/**
 * Sleeper Autopilot: sets Sleeper lineups and waiver claims from FantasyPros
 * Expert Consensus Rankings (ECR), following each league's own rules.
 *
 * Runs as a Google Apps Script web app inside your own Google account:
 *  - the dashboard (Index.html) is deployed with access "Only myself",
 *  - your Sleeper session token is kept in your private UserProperties
 *    (your password is never stored),
 *  - a 30-minute time trigger (tick) runs the autopilot.
 *
 * Sleeper reads use the public REST API. Logging in and saving changes use
 * the private GraphQL endpoint Sleeper's own web app calls: unofficial, may
 * change without notice, and automated use may conflict with Sleeper's terms.
 *
 * Functions ending in "_" are private; the others are called by the UI.
 */

var SLEEPER_REST = 'https://api.sleeper.app/v1';
var SLEEPER_GQL = 'https://api.sleeper.app/graphql';
var FP_BASE = 'https://www.fantasypros.com/nfl/rankings/';
var DP_IDS_URL = 'https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv';

var FP = {
  OP: { PPR: 'ppr-superflex', HALF: 'half-point-ppr-superflex', STD: 'superflex' },
  FLEX: { PPR: 'ppr-flex', HALF: 'half-point-ppr-flex', STD: 'flex' },
  QB: 'qb', K: 'k', DST: 'dst',
  ROS: { PPR: 'ros-ppr-overall', HALF: 'ros-half-point-ppr-overall', STD: 'ros-overall' },
};

var DEFAULTS = {
  auto_lineup: true,         // autopilot sets this league's lineup
  auto_waivers: false,       // autopilot submits waiver claims (Tuesday evening)
  superflex_qb_bonus: 10,    // in SUPER_FLEX a QB counts this many ECR spots better
  bench_statuses: ['Out', 'IR', 'PUP', 'Sus', 'Doubtful', 'NA', 'DNR', 'COV'],
  max_claims: 2,
  min_gain: 20,              // pickup must beat the dropped player by this many ROS spots
  faab_tiers: [[30, 0.25], [60, 0.15], [100, 0.08], [150, 0.04]],
  stream_k_def: true,
  stream_margin: 6,
  never_drop: [],
  min_roster: {},
};

var SLOT_ELIGIBILITY = {
  QB: ['QB'], RB: ['RB'], WR: ['WR'], TE: ['TE'], K: ['K'], DEF: ['DEF'],
  FLEX: ['RB', 'WR', 'TE'], WRRB_FLEX: ['WR', 'RB'], REC_FLEX: ['WR', 'TE'],
  SUPER_FLEX: ['QB', 'RB', 'WR', 'TE'],
};
var NON_STARTING = ['BN', 'IR', 'TAXI'];
var SKILL = ['QB', 'RB', 'WR', 'TE'];
var EMPTY = '0';
var UNRANKED = 999;      // player missing from the ECR list
var UNAVAILABLE = 5000;  // bye / injured: only start him if there is nobody else
var INELIGIBLE = 1e9;
var EMPTY_COST = 1e6;
var TEAM_ALIASES = { JAC: 'JAX', WSH: 'WAS', LVR: 'LV', OAK: 'LV', LA: 'LAR', STL: 'LAR', SD: 'LAC' };

// ===================================================================
// Web app + UI API
// ===================================================================

function doGet() {
  // The single-file build (dist/SleeperAutopilot.gs) carries the page as UI_HTML.
  var page = typeof UI_HTML !== 'undefined' ? HtmlService.createHtmlOutput(UI_HTML)
                                            : HtmlService.createHtmlOutputFromFile('Index');
  return page.setTitle('Sleeper Autopilot').addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** Everything the UI needs that doesn't require hitting Sleeper/FantasyPros. */
function getState() {
  var token = token_();
  var claims = token ? jwtClaims_(token) : {};
  return {
    connected: !!token,
    user: getJson_('user', null),
    mode: settings_().mode,
    tokenExpires: claims.exp || null,
    lastTick: getJson_('lastTick', null),
    autopilotScheduled: hasTrigger_(),
    log: getJson_('log', []),
    now: Date.now(),
  };
}

/** Live plan for every league (nothing is changed on Sleeper). */
function getDashboard() {
  var token = requireToken_();
  var ctx = new Ctx_(token);
  var s = settings_();
  var user = getJson_('user', {});
  var leagues = myLeagues_(ctx, user.user_id).map(function (data) {
    var lg = new League_(ctx, data, user.user_id, leagueCfg_(s, data.league_id));
    return lg.evaluate({ lineup: true, waivers: true });
  });
  return { state: getState(), week: ctx.state.week, season: ctx.state.league_season, leagues: leagues };
}

function setMode(mode) {
  var s = settings_();
  s.mode = mode === 'auto' ? 'auto' : 'suggest';
  putJson_('settings', s);
  ensureTrigger_();
  log_({ level: 'info', title: s.mode === 'auto' ? 'Autopilot turned on' : 'Autopilot paused (suggestions only)' });
  return getState();
}

function saveLeagueSettings(leagueId, patch) {
  var s = settings_();
  var cur = s.leagues[leagueId] || {};
  Object.keys(patch || {}).forEach(function (k) {
    if (k in DEFAULTS) cur[k] = patch[k];
  });
  s.leagues[leagueId] = cur;
  putJson_('settings', s);
  return leagueCfg_(s, leagueId);
}

function applyLineup(leagueId) {
  return withLeague_(leagueId, function (lg) {
    var res = lg.evaluate({ lineup: true });
    lg.applyLineup(res, 'manual');
    return res;
  });
}

function submitClaims(leagueId) {
  return withLeague_(leagueId, function (lg) {
    var res = lg.evaluate({ waivers: true });
    lg.applyClaims(res, 'manual');
    return res;
  });
}

/** Run the lineup part of the autopilot right now (ignores the time window). */
function runNow() {
  autopilot_({ force: true });
  return getState();
}

// ---- login ----------------------------------------------------------

var Q_LOGIN = 'query login($e: String!, $p: String!, $c: String) {' +
  ' login(email_or_phone_or_username: $e, password: $p, captcha: $c) { token } }';
var Q_LOGIN_CONTEXT = 'query login_context_by_email_or_phone_or_username($e: String!) {' +
  ' login_context_by_email_or_phone_or_username(email_or_phone_or_username: $e) }';
var M_SEND_CODE = 'mutation create_verification_code($e: String!, $c: String) {' +
  ' create_verification_code(email_or_phone: $e, captcha: $c) }';

function login(identifier, password) {
  identifier = String(identifier || '').trim();
  if (!identifier || !password) throw new Error('Enter your Sleeper email (or username) and password.');
  var data;
  try {
    data = gql_(Q_LOGIN, { e: identifier, p: String(password) });
  } catch (err) {
    if ((err.codes || []).indexOf('code_verification_required') >= 0) {
      gql_(M_SEND_CODE, { e: identifier });
      CacheService.getUserCache().put('pending_login', identifier, 900);
      var ctx = loginContext_(identifier) || {};
      return { needsCode: true, sentTo: ctx.masked_email || ctx.masked_phone || 'your email' };
    }
    if (/human|captcha/i.test(err.message)) throw new Error(CAPTCHA_MSG);
    throw new Error('Sleeper refused the login: ' + err.message);
  }
  if (!data || !data.login || !data.login.token) {
    throw new Error("Sleeper didn't accept that email/username and password.");
  }
  return finishLogin_(data.login.token, identifier);
}

function verifyCode(code) {
  var identifier = CacheService.getUserCache().get('pending_login');
  if (!identifier) throw new Error('The code request expired. Please log in again.');
  var data = gql_(Q_LOGIN, { e: identifier, p: String(code || '').trim() });
  if (!data || !data.login || !data.login.token) throw new Error("That code didn't work. Check the latest email from Sleeper.");
  return finishLogin_(data.login.token, identifier);
}

var CAPTCHA_MSG = 'Sleeper wants a captcha before it lets this login through. ' +
  'Wait a few minutes and try again, or use "Trouble logging in?" to connect via sleeper.com.';

/**
 * Save a Sleeper session obtained in the browser: either the page logged in
 * directly with Sleeper, or you pasted what the sleeper.com bookmarklet copied
 * ({"token": ..., "user_id": ...} or just the token).
 */
function connectWithToken(token, username, userId) {
  token = String(token || '').trim();
  if (token.charAt(0) === '{') {
    try {
      var o = JSON.parse(token);
      token = o.token || '';
      userId = userId || o.user_id;
    } catch (e) { /* fall through to the format check */ }
  }
  token = token.replace(/^"+|"+$/g, '');
  if (token.split('.').length !== 3) throw new Error("That doesn't look like a Sleeper login. Copy it again.");
  return finishLogin_(token, username, userId);
}

function logout() {
  store_().deleteProperty('token');
  store_().deleteProperty('waivers_done');
  log_({ level: 'info', title: 'Disconnected from Sleeper' });
  return getState();
}

function finishLogin_(token, identifier, userId) {
  var user = null;
  userId = userId || jwtClaims_(token).user_id;
  if (userId) user = sleeper_('/user/' + userId);
  if (!user && identifier && identifier.indexOf('@') < 0) user = sleeper_('/user/' + identifier);  // username
  if (!user && identifier) {
    var ctx = loginContext_(identifier);
    if (ctx && ctx.user_id) user = sleeper_('/user/' + ctx.user_id);
  }
  if (!user) throw new Error('Logged in, but could not work out which Sleeper user this is.');
  // Prove the token is accepted before saving it.
  var leagues = sleeper_('/user/' + user.user_id + '/leagues/nfl/' + sleeper_('/state/nfl').league_season) || [];
  if (leagues.length) {
    try {
      pendingWaivers_(token, leagues[0].league_id);
    } catch (e) {
      throw new Error(e.expired ? "Sleeper didn't accept that login. Please try again."
                                : 'Sleeper accepted the login but blocked this app from using it: ' + e.message);
    }
  }
  store_().setProperty('token', token);
  putJson_('user', { user_id: user.user_id, display_name: user.display_name, avatar: user.avatar });
  ensureTrigger_();
  log_({ level: 'info', title: 'Connected to Sleeper as ' + user.display_name });
  return getState();
}

function loginContext_(identifier) {
  try {
    return gql_(Q_LOGIN_CONTEXT, { e: identifier }).login_context_by_email_or_phone_or_username;
  } catch (e) {
    return null;
  }
}

// ===================================================================
// Autopilot (time trigger)
// ===================================================================

function tick() {
  var lock = LockService.getUserLock();
  if (!lock.tryLock(5000)) return;
  try {
    autopilot_({ force: false });
  } catch (e) {
    recordTick_('error', String(e.message || e));
  } finally {
    lock.releaseLock();
  }
}

function autopilot_(opts) {
  var token = token_();
  if (!token) return;
  var s = settings_();
  if (s.mode !== 'auto' && !opts.force) {
    recordTick_('idle', 'Suggestions only: autopilot is paused.');
    return;
  }
  var ctx = new Ctx_(token);
  var user = getJson_('user', {});
  var schedule = ctx.ranks(FP.OP.PPR);
  var nextKick = nextKickoff_(schedule, ctx.now);
  var lineupWindow = opts.force || (schedule.week === Number(ctx.state.week) && nextKick &&
                                    nextKick - ctx.now <= 30 * 3600);
  var done = getJson_('waivers_done', {});
  var summary = [];
  try {
    myLeagues_(ctx, user.user_id).forEach(function (data) {
      var cfg = leagueCfg_(s, data.league_id);
      var lg = new League_(ctx, data, user.user_id, cfg);
      if (!lg.roster || data.status !== 'in_season') return;
      if (cfg.auto_lineup && lineupWindow && !(lg.settings.best_ball)) {
        var res = lg.evaluate({ lineup: true });
        if (res.lineup && res.lineup.changes) {
          lg.applyLineup(res, 'autopilot');
          summary.push(lg.name + ': lineup updated');
        }
      }
      var win = waiverWindow_(lg, ctx.now);
      if (cfg.auto_waivers && !opts.force && win && !done[lg.id + ':' + win]) {
        var wres = lg.evaluate({ waivers: true });
        if (wres.waivers && wres.waivers.error) {
          log_({ level: 'error', league: lg.name, title: 'Waiver planning failed', lines: [wres.waivers.error] });
          return;  // try again on the next tick
        }
        lg.applyClaims(wres, 'autopilot');
        done[lg.id + ':' + win] = Date.now();
        putJson_('waivers_done', pruneDone_(done));
        summary.push(lg.name + ': ' + wres.waivers.claims.length + ' claim(s)');
      }
    });
  } catch (e) {
    if (e.expired) { recordTick_('error', EXPIRED_MSG); return; }
    throw e;
  }
  var idle = !lineupWindow ? 'No games in the next 30h; nothing to do.' : 'Checked lineups: all optimal.';
  recordTick_('ok', summary.length ? summary.join(' · ') : idle);
}

function nextKickoff_(list, now) {
  var next = null;
  Object.keys(list.teamKickoff).forEach(function (t) {
    var k = list.teamKickoff[t];
    if (k > now && (next === null || k < next)) next = k;
  });
  return next;
}

/** Claims go in the evening before the league's waiver day (UTC). Returns a window id or null. */
function waiverWindow_(lg, now) {
  if (lg.settings.daily_waivers) return null;
  var waiverDay = ((lg.settings.waiver_day_of_week || 2) + 1) % 7;  // Sleeper: 0=Mon; JS: 0=Sun
  var d = new Date(now * 1000);
  var day = d.getUTCDay(), hour = d.getUTCHours();
  var before = (waiverDay + 6) % 7;
  if ((day === before && hour >= 16) || (day === waiverDay && hour < 5)) {
    var start = new Date(d.getTime() - (day === waiverDay ? 86400000 : 0));
    return start.toISOString().slice(0, 10);
  }
  return null;
}

function pruneDone_(done) {
  var cutoff = Date.now() - 21 * 86400000;
  Object.keys(done).forEach(function (k) { if (done[k] < cutoff) delete done[k]; });
  return done;
}

function recordTick_(status, msg) {
  putJson_('lastTick', { ts: Date.now(), status: status, msg: msg });
}

function ensureTrigger_() {
  if (!hasTrigger_()) ScriptApp.newTrigger('tick').timeBased().everyMinutes(30).create();
}

function hasTrigger_() {
  return ScriptApp.getProjectTriggers().some(function (t) { return t.getHandlerFunction() === 'tick'; });
}

// ===================================================================
// Storage
// ===================================================================

function store_() { return PropertiesService.getUserProperties(); }
function token_() { return store_().getProperty('token'); }

function requireToken_() {
  var t = token_();
  if (!t) throw new Error('Not connected to Sleeper yet.');
  return t;
}

function settings_() {
  var s = getJson_('settings', null) || {};
  return { mode: s.mode || 'suggest', leagues: s.leagues || {} };
}

function leagueCfg_(s, leagueId) {
  var cfg = {};
  Object.keys(DEFAULTS).forEach(function (k) { cfg[k] = DEFAULTS[k]; });
  var o = s.leagues[leagueId] || {};
  Object.keys(o).forEach(function (k) { if (k in DEFAULTS) cfg[k] = o[k]; });
  return cfg;
}

function log_(entry) {
  var log = getJson_('log', []);
  entry.ts = Date.now();
  log.unshift(entry);
  putJson_('log', log.slice(0, 60));
}

// Property values are capped at 9 KB, so JSON is split across keys.
function getJson_(key, dflt) {
  var p = store_();
  var n = Number(p.getProperty(key + '#n') || 0);
  if (!n) return dflt;
  var s = '';
  for (var i = 0; i < n; i++) s += p.getProperty(key + '#' + i) || '';
  try { return JSON.parse(s); } catch (e) { return dflt; }
}

function putJson_(key, obj) {
  var p = store_();
  var s = JSON.stringify(obj), size = 6000;
  var n = Math.max(1, Math.ceil(s.length / size));
  var old = Number(p.getProperty(key + '#n') || 0);
  var map = {};
  for (var i = 0; i < n; i++) map[key + '#' + i] = s.substr(i * size, size);
  map[key + '#n'] = String(n);
  p.setProperties(map);
  for (var j = n; j < old; j++) p.deleteProperty(key + '#' + j);
}

// Cache values are capped at 100 KB, so big blobs are split too.
function cacheGet_(key) {
  var c = CacheService.getUserCache();
  var n = Number(c.get(key + '#n') || 0);
  if (!n) return null;
  var keys = [];
  for (var i = 0; i < n; i++) keys.push(key + '#' + i);
  var got = c.getAll(keys), s = '';
  for (var j = 0; j < n; j++) {
    if (got[keys[j]] == null) return null;
    s += got[keys[j]];
  }
  return JSON.parse(s);
}

function cachePut_(key, obj, seconds) {
  var s = JSON.stringify(obj), size = 80000;
  var n = Math.max(1, Math.ceil(s.length / size)), map = {};
  for (var i = 0; i < n; i++) map[key + '#' + i] = s.substr(i * size, size);
  map[key + '#n'] = String(n);
  CacheService.getUserCache().putAll(map, seconds);
}

function cached_(key, seconds, fn) {
  var v = cacheGet_(key);
  if (v !== null) return v;
  v = fn();
  try { cachePut_(key, v, seconds); } catch (e) { /* too big to cache: fine */ }
  return v;
}

// ===================================================================
// HTTP: Sleeper + FantasyPros
// ===================================================================

function fetch_(url, opt) {
  opt = opt || {};
  var params = { method: opt.payload ? 'post' : 'get', muteHttpExceptions: true,
                 headers: opt.headers || {}, followRedirects: true };
  if (opt.payload) {
    params.contentType = 'application/json';
    params.payload = JSON.stringify(opt.payload);
  }
  var tries = opt.retries || 3, resp, code;
  for (var attempt = 0; attempt < tries; attempt++) {
    resp = UrlFetchApp.fetch(url, params);
    code = resp.getResponseCode();
    if (code < 500) break;
    Utilities.sleep(1500 * (attempt + 1));
  }
  return { code: code, text: resp.getContentText() };
}

function sleeper_(path) {
  var r = fetch_(SLEEPER_REST + path);
  if (r.code !== 200) throw new Error('Sleeper API ' + path + ' failed (HTTP ' + r.code + ')');
  return JSON.parse(r.text);
}

function gql_(query, variables, token, retries) {
  var r = fetch_(SLEEPER_GQL, { payload: { query: query, variables: variables },
                                headers: token ? { Authorization: token } : {}, retries: retries });
  if (token && r.code === 401) throw sessionExpired_();
  var body;
  try { body = JSON.parse(r.text); } catch (e) { throw new Error('Sleeper returned HTTP ' + r.code); }
  if (body.errors && body.errors.length) {
    var err = new Error(body.errors.map(function (e) { return e.message; }).join('; '));
    err.codes = body.errors.map(function (e) { return e.code || (e.extensions && e.extensions.code) || ''; });
    err.status = r.code;
    throw err;
  }
  return body.data;
}

var EXPIRED_MSG = 'Your Sleeper session expired. Please log in again.';

/** Sleeper rejected our token: forget it (stops the autopilot) and say so once. */
function sessionExpired_() {
  if (token_()) {
    store_().deleteProperty('token');
    log_({ level: 'error', title: EXPIRED_MSG });
  }
  var e = new Error(EXPIRED_MSG);
  e.expired = true;
  return e;
}

function jwtClaims_(token) {
  try {
    var part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    while (part.length % 4) part += '=';
    return JSON.parse(Utilities.newBlob(Utilities.base64Decode(part)).getDataAsString());
  } catch (e) {
    return {};
  }
}

function pendingWaivers_(token, leagueId) {
  var q = 'query league_transactions_filtered($leagueId: String!, $rosterIdFilters: [Int], $typeFilters: [String],' +
    ' $legFilters: [Int], $statusFilters: [String], $limit: Int) { league_transactions_filtered(league_id: $leagueId,' +
    ' roster_id_filters: $rosterIdFilters, type_filters: $typeFilters, leg_filters: $legFilters,' +
    ' status_filters: $statusFilters, limit: $limit) { transaction_id type status roster_ids adds drops settings } }';
  return gql_(q, { leagueId: leagueId, rosterIdFilters: [], typeFilters: ['waiver'], legFilters: [],
                   statusFilters: ['pending'], limit: 100 }, token).league_transactions_filtered || [];
}

function setStarters_(token, leagueId, rosterId, starters) {
  var q = 'mutation roster_update_starters($leagueId: String!, $rosterId: Int!, $starters: [String]) {' +
    ' roster_update_starters(league_id: $leagueId, roster_id: $rosterId, starters: $starters) { roster_id starters } }';
  return gql_(q, { leagueId: leagueId, rosterId: rosterId, starters: starters }, token, 1);
}

function submitClaim_(token, leagueId, rosterId, add, drop, bid) {
  var q = 'mutation submit_waiver_claim($leagueId: String!, $k_adds: [String], $v_adds: [Int], $k_drops: [String],' +
    ' $v_drops: [Int], $k_settings: [String], $v_settings: [Int]) { submit_waiver_claim(league_id: $leagueId,' +
    ' k_adds: $k_adds, v_adds: $v_adds, k_drops: $k_drops, v_drops: $v_drops, k_settings: $k_settings,' +
    ' v_settings: $v_settings) { transaction_id type status leg adds drops roster_ids } }';
  var v = { leagueId: leagueId, k_adds: [add], v_adds: [rosterId],
            k_drops: drop ? [drop] : [], v_drops: drop ? [rosterId] : [] };
  if (bid !== null && bid !== undefined) {
    v.k_settings = ['waiver_bid'];
    v.v_settings = [Math.floor(bid)];
  }
  return gql_(q, v, token, 1);
}

/** Find the ``{...}`` that starts at ``start`` (string-aware). Returns end index. */
function matchBrace_(text, start) {
  var depth = 0, inStr = false;
  for (var j = start; j < text.length; j++) {
    var c = text.charCodeAt(j);
    if (inStr) {
      if (c === 92) j++;              // backslash
      else if (c === 34) inStr = false;
    } else if (c === 34) inStr = true;
    else if (c === 123) depth++;
    else if (c === 125 && --depth === 0) return j;
  }
  throw new Error('Unbalanced JSON');
}

function parseEcr_(html) {
  var m = /var\s+ecrData\s*=\s*/.exec(html);
  if (!m) throw new Error('FantasyPros page layout changed (no ecrData)');
  var start = m.index + m[0].length;
  return JSON.parse(html.substring(start, matchBrace_(html, start) + 1));
}

/** One FantasyPros ECR list, slimmed down for caching. */
function fpList_(slug) {
  return cached_('fp:' + slug, 30 * 60, function () {
    var r = fetch_(FP_BASE + slug + '.php');
    if (r.code !== 200) throw new Error('FantasyPros ' + slug + ' failed (HTTP ' + r.code + ')');
    var d = parseEcr_(r.text);
    return {
      week: Number(d.week || 0), label: d.type || slug,
      players: d.players.map(function (p) {
        return [p.player_id, p.player_name, p.player_position_id, p.player_team_id, Number(p.rank_ecr),
                p.pos_rank || '', p.player_bye_week, p.player_opponent, p.player_game_kickoff_ts || null,
                p.player_game_status || null];
      }),
    };
  });
}

/** fantasypros_id -> sleeper_id, from the DynastyProcess cross-site id table. */
function fpToSleeper_() {
  return cached_('dp_ids', 6 * 3600, function () {
    var rows = Utilities.parseCsv(fetch_(DP_IDS_URL).text);
    var head = rows[0], fi = head.indexOf('fantasypros_id'), si = head.indexOf('sleeper_id'), map = {};
    for (var i = 1; i < rows.length; i++) {
      var f = rows[i][fi], s = rows[i][si];
      if (f && s && f !== 'NA' && s !== 'NA') map[f] = s;
    }
    return map;
  });
}

/**
 * Sleeper's player db is ~14 MB; we keep only fantasy-relevant players as
 * [name, position, team, injury_status, fantasy_positions]. Refreshed more
 * often close to kickoff so game-day inactives are picked up.
 */
function playersSlim_(maxAgeSec) {
  var hit = cacheGet_('players');
  if (hit && Date.now() / 1000 - hit.at < maxAgeSec) return hit.players;
  var text = fetch_(SLEEPER_REST + '/players/nfl').text;
  var out = {}, i = text.indexOf('{') + 1;
  var keep = /"position":"(QB|RB|WR|TE|K|DEF)"/;
  while (true) {
    var ks = text.indexOf('"', i);
    if (ks < 0) break;
    var ke = text.indexOf('"', ks + 1);
    var os = text.indexOf('{', ke);
    if (os < 0) break;
    var oe = matchBrace_(text, os);
    var chunk = text.substring(os, oe + 1);
    if (keep.test(chunk)) {
      var p = JSON.parse(chunk);
      if (p.team || p.active) {
        var name = p.full_name || ((p.first_name || '') + ' ' + (p.last_name || '')).trim();
        var fpos = p.fantasy_positions && p.fantasy_positions.join(',') !== p.position ? p.fantasy_positions : null;
        out[text.substring(ks + 1, ke)] = [name, p.position, p.team || null, p.injury_status || null, fpos];
      }
    }
    i = oe + 1;
  }
  try { cachePut_('players', { at: Date.now() / 1000, players: out }, 6 * 3600); } catch (e) { /* ok */ }
  return out;
}

// ===================================================================
// Rankings: FantasyPros lists keyed by Sleeper id
// ===================================================================

function normTeam_(t) { t = String(t || '').toUpperCase(); return TEAM_ALIASES[t] || t; }

function normName_(n) {
  return String(n || '').toLowerCase().replace(/[.']/g, '').replace(/\b(jr|sr|ii|iii|iv|v)\b/g, '')
    .replace(/[^a-z]/g, '');
}

function IdMap_(players, fpToSleeper) {
  this.players = players;
  this.fp = fpToSleeper;
  this.byName = {};
  var self = this;
  Object.keys(players).forEach(function (pid) {
    var p = players[pid];
    (p[4] || [p[1]]).forEach(function (pos) {
      var k = normName_(p[0]) + '|' + pos;
      (self.byName[k] = self.byName[k] || []).push(pid);
    });
  });
}

IdMap_.prototype.sleeperId = function (fpId, name, pos, team) {
  if (pos === 'DST') return this.players[team] ? team : null;
  var sid = this.fp[String(fpId)];
  if (sid && this.players[sid]) return sid;
  var cands = this.byName[normName_(name) + '|' + pos] || [];
  if (cands.length > 1) {
    var players = this.players;
    var sameTeam = cands.filter(function (c) { return players[c][2] === team; });
    if (sameTeam.length) cands = sameTeam;
  }
  return cands.length === 1 ? cands[0] : null;
};

function RankList_(data, idmap, now) {
  this.week = data.week;
  this.label = data.label;
  this.byId = new Map();
  this.unmatched = [];
  this.teamKickoff = {};
  var self = this;
  data.players.forEach(function (row) {
    var name = row[1], pos = row[2], team = normTeam_(row[3]), bye = row[6], opp = row[7];
    var kickoff = row[8], status = row[9];
    if (kickoff) self.teamKickoff[team] = kickoff;
    var sid = idmap.sleeperId(row[0], name, pos, team);
    if (!sid) { self.unmatched.push(name); return; }
    if (self.byId.has(sid)) return;
    self.byId.set(sid, {
      rank: row[4], posRank: row[5], name: name, team: team, kickoff: kickoff,
      bye: !!self.week && (String(bye) === String(self.week) || (opp === '' && !kickoff)),
      started: !!(kickoff && kickoff <= now) || status === 'inprogress' || status === 'closed',
    });
  });
}

RankList_.prototype.get = function (sid) { return this.byId.get(sid) || null; };

RankList_.prototype.firstKickoff = function () {
  var ks = Object.keys(this.teamKickoff).map(function (t) { return this.teamKickoff[t]; }, this);
  return ks.length ? Math.min.apply(null, ks) : null;
};

function scoringFormat_(scoring) {
  var rec = Number(scoring.rec || 0);
  return rec >= 0.75 ? 'PPR' : rec >= 0.25 ? 'HALF' : 'STD';
}

/** Shared per-execution data: Sleeper state + players, cached ECR lists. */
function Ctx_(token) {
  this.token = token;
  this.now = Date.now() / 1000;
  this.state = cached_('sleeper_state', 600, function () { return sleeper_('/state/nfl'); });
  this.lists = {};
  var schedule = this.ranksRaw_(FP.OP.PPR);
  var soon = false, now = this.now;
  schedule.players.forEach(function (r) { if (r[8] && r[8] > now && r[8] - now < 3 * 3600) soon = true; });
  this.players = playersSlim_(soon ? 25 * 60 : 4 * 3600);
  this.idmap = new IdMap_(this.players, fpToSleeper_());
}

Ctx_.prototype.ranksRaw_ = function (slug) { return fpList_(slug); };

Ctx_.prototype.ranks = function (slug) {
  if (!this.lists[slug]) this.lists[slug] = new RankList_(fpList_(slug), this.idmap, this.now);
  return this.lists[slug];
};

function myLeagues_(ctx, userId) {
  return sleeper_('/user/' + userId + '/leagues/nfl/' + ctx.state.league_season) || [];
}

function withLeague_(leagueId, fn) {
  var token = requireToken_();
  var ctx = new Ctx_(token);
  var user = getJson_('user', {});
  var data = myLeagues_(ctx, user.user_id).filter(function (l) { return l.league_id === leagueId; })[0];
  if (!data) throw new Error('League not found');
  return fn(new League_(ctx, data, user.user_id, leagueCfg_(settings_(), leagueId)));
}

// ===================================================================
// Lineup optimizer
// ===================================================================

function starterSlots_(rosterPositions) {
  return rosterPositions.filter(function (s) { return NON_STARTING.indexOf(s) < 0; });
}

/** Min-cost assignment of every row to a distinct column (rows <= cols). */
function hungarian_(cost) {
  var n = cost.length, m = cost[0].length, INF = Infinity;
  var u = new Array(n + 1).fill(0), v = new Array(m + 1).fill(0);
  var p = new Array(m + 1).fill(0), way = new Array(m + 1).fill(0);
  for (var i = 1; i <= n; i++) {
    p[0] = i;
    var j0 = 0, minv = new Array(m + 1).fill(INF), used = new Array(m + 1).fill(false);
    do {
      used[j0] = true;
      var i0 = p[j0], delta = INF, j1 = 0;
      for (var j = 1; j <= m; j++) {
        if (used[j]) continue;
        var cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
        if (cur < minv[j]) { minv[j] = cur; way[j] = j0; }
        if (minv[j] < delta) { delta = minv[j]; j1 = j; }
      }
      for (var jj = 0; jj <= m; jj++) {
        if (used[jj]) { u[p[jj]] += delta; v[jj] -= delta; } else minv[jj] -= delta;
      }
      j0 = j1;
    } while (p[j0] !== 0);
    do { var jw = way[j0]; p[j0] = p[jw]; j0 = jw; } while (j0);
  }
  var assign = new Array(n);
  for (var c = 1; c <= m; c++) if (p[c]) assign[p[c] - 1] = c - 1;
  return assign;
}

/**
 * Best starters for ``slots``. ``cost(pid, slot)`` is lower-is-better or null
 * when ineligible. Locked players (game started) can't move; slots we don't
 * model (IDP...) stay exactly as they are.
 */
function optimize_(slots, current, roster, cost, locked) {
  locked = locked || {};
  current = current.slice();
  while (current.length < slots.length) current.push(EMPTY);
  var fixed = {}, taken = {};
  slots.forEach(function (slot, i) {
    var pid = current[i];
    if (!SLOT_ELIGIBILITY[slot] || (pid !== EMPTY && locked[pid])) { fixed[i] = true; taken[pid] = true; }
  });
  var pool = roster.filter(function (pid) { return !taken[pid] && !locked[pid]; });
  var openIdx = [];
  for (var i = 0; i < slots.length; i++) if (!fixed[i]) openIdx.push(i);
  var starters = current.slice();
  if (openIdx.length) {
    var cols = pool.concat(openIdx.map(function () { return EMPTY; }));
    var nowStarting = {};
    current.forEach(function (p) { nowStarting[p] = true; });
    var matrix = openIdx.map(function (si) {
      return cols.map(function (pid) {
        if (pid === EMPTY) return EMPTY_COST;
        var c = cost(pid, slots[si]);
        return c === null || c === undefined ? INELIGIBLE : c - (nowStarting[pid] ? 1e-3 : 0);
      });
    });
    hungarian_(matrix).forEach(function (col, r) {
      starters[openIdx[r]] = matrix[r][col] < INELIGIBLE ? cols[col] : EMPTY;
    });
    keepPositions_(slots, current, starters, openIdx);
  }
  var changes = [], keptLocked = [];
  slots.forEach(function (slot, i) {
    if (current[i] !== starters[i]) changes.push([i, slot, current[i], starters[i]]);
    if (fixed[i] && current[i] !== EMPTY && SLOT_ELIGIBILITY[slot]) keptLocked.push(current[i]);
  });
  return { starters: starters, changes: changes, locked: keptLocked };
}

/** Within identical slots (RB, RB...), keep players where they already sit. */
function keepPositions_(slots, current, starters, openIdx) {
  var groups = {};
  openIdx.forEach(function (i) { (groups[slots[i]] = groups[slots[i]] || []).push(i); });
  Object.keys(groups).forEach(function (g) {
    var idx = groups[g];
    var chosen = idx.map(function (i) { return starters[i]; });
    var stay = {}, stayed = {};
    idx.forEach(function (i) {
      if (current[i] !== EMPTY && chosen.indexOf(current[i]) >= 0) { stay[i] = current[i]; stayed[current[i]] = true; }
    });
    var rest = chosen.filter(function (p) { return !stayed[p]; });
    idx.forEach(function (i) { starters[i] = i in stay ? stay[i] : rest.shift(); });
  });
}

// ===================================================================
// Waivers
// ===================================================================

/** Best free agent first; each claim drops the weakest player it clearly beats. */
function planUpgrades_(o) {
  var counts = {};
  o.myPlayers.forEach(function (p) { var pos = o.position(p); counts[pos] = (counts[pos] || 0) + 1; });
  var openSpots = o.rosterLimit - o.myPlayers.length;
  var cands = o.myPlayers.filter(function (p) {
    return !o.protected[p] && !o.blockedDrops[p] && o.dropValue(p) !== null;
  }).sort(function (a, b) { return o.dropValue(b) - o.dropValue(a); });  // weakest first
  var fas = o.freeAgents.filter(function (p) { return o.value(p) !== null; })
    .sort(function (a, b) { return o.value(a) - o.value(b); });
  var claims = [];
  for (var f = 0; f < fas.length && claims.length < o.maxClaims; f++) {
    var fa = fas[f], fv = o.value(fa), fpos = o.position(fa);
    if (openSpots > 0) {
      claims.push({ add: fa, drop: null, addValue: fv, dropValue: null, kind: 'upgrade' });
      openSpots--;
      counts[fpos] = (counts[fpos] || 0) + 1;
      continue;
    }
    for (var c = 0; c < cands.length; c++) {
      var d = cands[c], dv = o.dropValue(d);
      if (dv - fv < o.minGain) break;
      var dpos = o.position(d);
      if (dpos !== fpos && (counts[dpos] || 0) - 1 < (o.minimums[dpos] || 0)) continue;
      claims.push({ add: fa, drop: d, addValue: fv, dropValue: dv, kind: 'upgrade' });
      cands.splice(c, 1);
      counts[dpos]--;
      counts[fpos] = (counts[fpos] || 0) + 1;
      break;
    }
  }
  return claims;
}

/** Swap a K or DEF for a free agent with a clearly better matchup this week. */
function planStream_(freeAgents, mine, value, margin, openSpot) {
  var fas = freeAgents.filter(function (p) { return value(p) !== null; })
    .sort(function (a, b) { return value(a) - value(b); });
  if (!fas.length) return null;
  var best = fas[0];
  if (!mine.length) return openSpot ? { add: best, drop: null, addValue: value(best), dropValue: null, kind: 'stream' } : null;
  var v = function (p) { return value(p) === null ? 1e9 : value(p); };
  var ranked = mine.slice().sort(function (a, b) { return v(a) - v(b); });
  if (v(ranked[0]) - value(best) < margin) return null;
  var drop = ranked[ranked.length - 1];
  return { add: best, drop: drop, addValue: value(best), dropValue: value(drop), kind: 'stream' };
}

function faabBid_(value, remaining, tiers, minBid) {
  if (remaining < minBid) return null;
  var frac = 0;
  for (var i = 0; i < tiers.length; i++) if (value <= tiers[i][0]) { frac = tiers[i][1]; break; }
  return Math.max(minBid, Math.min(remaining, Math.floor(frac * remaining)));
}

function superflexTemplate_(opList, players) {
  var byPos = { QB: [], RB: [], WR: [], TE: [] };
  opList.byId.forEach(function (r, sid) {
    var p = players[sid];
    if (p && byPos[p[1]] && !r.bye) byPos[p[1]].push(r.rank);
  });
  var out = {};
  Object.keys(byPos).forEach(function (k) {
    if (byPos[k].length) out[k] = byPos[k].sort(function (a, b) { return a - b; });
  });
  return out;
}

function templateValue_(template, pos, n) {
  var ranks = template[pos];
  if (!ranks || !n) return null;
  if (n <= ranks.length) return ranks[n - 1];
  var tail = ranks.slice(-10);
  var step = Math.max(1, (tail[tail.length - 1] - tail[0]) / Math.max(1, tail.length - 1));
  return ranks[ranks.length - 1] + step * (n - ranks.length);
}

// ===================================================================
// League: read its rules, plan (and maybe apply) moves
// ===================================================================

function League_(ctx, data, userId, cfg) {
  this.ctx = ctx;
  this.data = data;
  this.cfg = cfg;
  this.id = data.league_id;
  this.name = data.name || data.league_id;
  this.slots = starterSlots_(data.roster_positions || []);
  this.fmt = scoringFormat_(data.scoring_settings || {});
  this.qbPremium = this.slots.indexOf('SUPER_FLEX') >= 0 ||
    this.slots.filter(function (s) { return s === 'QB'; }).length >= 2;
  this.settings = data.settings || {};
  this.faab = this.settings.waiver_type === 2;
  this.rosters = sleeper_('/league/' + this.id + '/rosters');
  this.roster = this.rosters.filter(function (r) {
    return r.owner_id === userId || (r.co_owners || []).indexOf(userId) >= 0;
  })[0] || null;
}

League_.prototype.p = function (pid) { return this.ctx.players[pid] || null; };
League_.prototype.pos = function (pid) { var p = this.p(pid); return p ? p[1] : '?'; };
League_.prototype.positions = function (pid) { var p = this.p(pid); return p ? (p[4] || [p[1]]) : []; };
League_.prototype.team = function (pid) { return this.pos(pid) === 'DEF' ? pid : (this.p(pid) || [])[2] || null; };
League_.prototype.eligible = function (pid, slot) {
  var ok = SLOT_ELIGIBILITY[slot];
  return this.positions(pid).some(function (x) { return ok.indexOf(x) >= 0; });
};

League_.prototype.activePlayers = function () {
  var r = this.roster, hidden = {};
  (r.reserve || []).concat(r.taxi || []).forEach(function (p) { hidden[p] = true; });
  return (r.players || []).filter(function (p) { return !hidden[p]; });
};

League_.prototype.weeklyList = function (pos) {
  if (pos === 'K') return this.ctx.ranks(FP.K);
  if (pos === 'DEF') return this.ctx.ranks(FP.DST);
  if (SKILL.indexOf(pos) < 0) return null;
  if (this.qbPremium) return this.ctx.ranks(FP.OP[this.fmt]);   // QBs ranked against RB/WR/TE
  return this.ctx.ranks(pos === 'QB' ? FP.QB : FP.FLEX[this.fmt]);
};

League_.prototype.weeklyRank = function (pid) {
  var l = this.weeklyList(this.pos(pid));
  return l ? l.get(pid) : null;
};

League_.prototype.view = function (pid, rank, extra) {
  var p = this.p(pid) || [pid, '?', null];
  var v = { id: pid, name: pid === EMPTY ? '(empty)' : p[0], pos: p[1], team: this.team(pid),
            rank: rank && rank.rank !== undefined ? rank.rank : (typeof rank === 'number' ? Math.round(rank) : null),
            posRank: rank && rank.posRank ? rank.posRank : null };
  Object.keys(extra || {}).forEach(function (k) { v[k] = extra[k]; });
  return v;
};

League_.prototype.flags = function () {
  var f = [this.fmt === 'STD' ? 'Standard' : this.fmt === 'HALF' ? 'Half PPR' : 'PPR'];
  f.push(this.slots.indexOf('SUPER_FLEX') >= 0 ? 'Superflex' : this.qbPremium ? '2QB' : '1QB');
  f.push(this.faab ? 'FAAB' : 'Waiver priority');
  var sc = this.data.scoring_settings || {};
  if (sc.bonus_rec_te) f.push('TE premium');
  if ((sc.pass_td || 4) >= 6) f.push('6pt pass TD');
  if (this.settings.best_ball) f.push('Best ball');
  return f;
};

/** Plan this league (nothing is written). */
League_.prototype.evaluate = function (what) {
  var res = { id: this.id, name: this.name, flags: this.flags(), slots: this.slots,
              settings: this.cfg, superflex: this.slots.indexOf('SUPER_FLEX') >= 0,
              notes: [], lineup: null, waivers: null, status: this.data.status };
  if (!this.roster) { res.notes.push("You don't have a team in this league."); return res; }
  if (this.data.status !== 'in_season') { res.notes.push('League is ' + this.data.status + '.'); return res; }
  try {
    if (what.lineup) {
      res.lineup = this.settings.best_ball ? { skipped: 'Best ball: Sleeper sets the lineup.' } : this.planLineup();
    }
  } catch (e) {
    if (e.expired) throw e;
    res.lineup = { error: String(e.message || e) };
  }
  try {
    if (what.waivers) res.waivers = this.planWaivers();
  } catch (e) {
    if (e.expired) throw e;
    res.waivers = { error: String(e.message || e) };
  }
  return res;
};

League_.prototype.planLineup = function () {
  var self = this, ctx = this.ctx, cfg = this.cfg;
  var main = this.weeklyList(this.qbPremium ? 'QB' : 'RB');
  var week = Number(ctx.state.week);
  if (main.week !== week) {
    return { skipped: 'FantasyPros rankings are for week ' + main.week + '; Sleeper is on week ' + week + '.' };
  }
  var kickoff = {};
  this.slots.forEach(function (s) {
    (SLOT_ELIGIBILITY[s] || []).forEach(function (pos) {
      var l = self.weeklyList(pos);
      Object.keys(l.teamKickoff).forEach(function (t) { kickoff[t] = l.teamKickoff[t]; });
    });
  });
  var info = {};
  var everyone = this.activePlayers().concat(this.roster.starters || []);
  everyone.forEach(function (pid) {
    if (pid === EMPTY || info[pid]) return;
    var r = self.weeklyRank(pid), team = self.team(pid);
    var ko = (r && r.kickoff) || kickoff[team];
    var injury = (self.p(pid) || [])[3];
    var why = null;
    if (cfg.bench_statuses.indexOf(injury) >= 0) why = injury;
    else if ((r && r.bye) || !(team in kickoff)) why = 'bye';
    info[pid] = { r: r, locked: !!(r && r.started) || !!(ko && ko <= ctx.now), why: why };
  });
  var cost = function (pid, slot) {
    if (!self.eligible(pid, slot)) return null;
    var i = info[pid];
    var c = (i.r ? i.r.rank : UNRANKED) + (i.why ? UNAVAILABLE : 0);
    if (slot === 'SUPER_FLEX' && self.positions(pid).indexOf('QB') >= 0) c -= cfg.superflex_qb_bonus;
    return c;
  };
  var locked = {};
  Object.keys(info).forEach(function (pid) { if (info[pid].locked) locked[pid] = true; });
  var current = this.roster.starters || [];
  var out = optimize_(this.slots, current, this.activePlayers(), cost, locked);
  var vw = function (pid) {
    if (pid === EMPTY) return self.view(EMPTY);
    var i = info[pid];
    return self.view(pid, i.r, { why: i.why, locked: i.locked });
  };
  var after = {}, before = {};
  out.starters.forEach(function (p) { after[p] = true; });
  current.forEach(function (p) { before[p] = true; });
  return {
    week: week,
    changes: out.changes.length,
    starters: out.starters,
    lineup: out.starters.map(function (pid, i) {
      var v = vw(pid); v.slot = self.slots[i]; v.isNew = pid !== EMPTY && !before[pid]; return v;
    }),
    benched: current.filter(function (p) { return p !== EMPTY && !after[p]; }).map(vw),
    bench: this.activePlayers().filter(function (p) { return !after[p]; }).map(vw)
      .sort(function (a, b) { return (a.rank || 9999) - (b.rank || 9999); }),
    warnings: out.starters.filter(function (p) {
      return p !== EMPTY && info[p].why && !info[p].locked;
    }).map(function (p) { return vw(p).name + ' (' + info[p].why + ') starts: no healthy option left.'; }),
  };
};

League_.prototype.minimums = function () {
  var c = {};
  this.slots.forEach(function (s) { c[s] = (c[s] || 0) + 1; });
  var g = function (k) { return c[k] || 0; };
  var mins = { QB: g('QB') + g('SUPER_FLEX'), RB: g('RB'), WR: g('WR'), TE: g('TE'), K: g('K'), DEF: g('DEF') };
  if (this.qbPremium) mins.QB += 1;      // bye-week / injury cover when you start two QBs
  if (mins.RB) mins.RB += 1;
  if (mins.WR) mins.WR += 1;
  var o = this.cfg.min_roster || {};
  Object.keys(o).forEach(function (k) { mins[k] = o[k]; });
  return mins;
};

League_.prototype.planWaivers = function () {
  var self = this, ctx = this.ctx, cfg = this.cfg;
  var notes = [];
  var rostered = {};
  this.rosters.forEach(function (r) {
    (r.players || []).concat(r.reserve || [], r.taxi || []).forEach(function (p) { rostered[p] = true; });
  });
  var myRid = this.roster.roster_id, pending = [];
  try {
    pending = pendingWaivers_(ctx.token, this.id).filter(function (t) {
      return (t.roster_ids || []).indexOf(myRid) >= 0;
    });
  } catch (e) {
    if (e.expired) throw e;
    notes.push("Couldn't read your pending claims: " + e.message);
  }
  var pendingAdds = {}, pendingDrops = {};
  pending.forEach(function (t) {
    Object.keys(t.adds || {}).forEach(function (p) { pendingAdds[p] = true; });
    Object.keys(t.drops || {}).forEach(function (p) { pendingDrops[p] = true; });
  });
  var ros = ctx.ranks(FP.ROS[this.fmt]);
  var template = this.qbPremium ? superflexTemplate_(this.weeklyList('QB'), ctx.players) : null;
  var value = function (pid) {
    var pos = self.pos(pid), r = ros.get(pid);
    if (SKILL.indexOf(pos) < 0 || !r) return null;
    if (!template) return r.rank;
    var m = /(\d+)$/.exec(r.posRank || '');
    return templateValue_(template, pos, m ? Number(m[1]) : null);
  };
  var keep = this.neverDrop();
  var dropValue = function (pid) {
    if (keep[pid] || SKILL.indexOf(self.pos(pid)) < 0) return null;
    var v = value(pid);
    if (v === null && !ros.get(pid) && !self.weeklyRank(pid)) return UNRANKED;  // in no ECR list: cut-able
    return v;
  };
  var mine = this.activePlayers();
  var relevant = {};
  this.slots.forEach(function (s) {
    (SLOT_ELIGIBILITY[s] || []).forEach(function (p) { if (SKILL.indexOf(p) >= 0) relevant[p] = true; });
  });
  var fas = [];
  ros.byId.forEach(function (r, pid) {
    if (!rostered[pid] && !pendingAdds[pid] && relevant[self.pos(pid)] && (self.p(pid) || [])[2]) fas.push(pid);
  });
  var rosCost = function (pid, slot) {
    if (!self.eligible(pid, slot)) return null;
    var v = value(pid);
    return v === null ? UNRANKED : v;
  };
  var core = {};
  optimize_(this.slots, [], mine, rosCost).starters.forEach(function (p) { core[p] = true; });
  var limit = (this.data.roster_positions || []).filter(function (s) { return s !== 'IR' && s !== 'TAXI'; }).length;
  var claims = planUpgrades_({
    freeAgents: fas, myPlayers: mine, value: value, dropValue: dropValue,
    position: function (p) { return self.pos(p); }, protected: core, minimums: this.minimums(),
    rosterLimit: limit, maxClaims: cfg.max_claims, minGain: cfg.min_gain, blockedDrops: pendingDrops,
  });
  if (cfg.stream_k_def) {
    var openSpot = limit - mine.length - claims.filter(function (c) { return !c.drop; }).length > 0;
    [['K', FP.K], ['DEF', FP.DST]].forEach(function (pair) {
      var pos = pair[0];
      if (self.slots.indexOf(pos) < 0) return;
      var wl = ctx.ranks(pair[1]);
      var first = wl.firstKickoff();
      if (!first || first <= ctx.now) {
        notes.push(pos + " streaming waits for next week's rankings.");
        return;
      }
      var wv = function (pid) { var r = wl.get(pid); return !r || r.bye ? null : r.rank; };
      var faK = [];
      wl.byId.forEach(function (r, pid) { if (!rostered[pid] && !pendingAdds[pid]) faK.push(pid); });
      var my = mine.filter(function (p) { return self.pos(p) === pos && !pendingDrops[p] && !keep[p]; });
      var c = planStream_(faK, my, wv, cfg.stream_margin, openSpot);
      if (c) claims.push(c);
    });
  }
  if (this.faab) {
    var budget = (this.settings.waiver_budget || 0) - ((this.roster.settings || {}).waiver_budget_used || 0);
    var minBid = this.settings.waiver_bid_min || 0;
    claims.forEach(function (c) {
      c.bid = c.kind === 'upgrade' ? faabBid_(c.addValue, budget, cfg.faab_tiers, minBid)
                                   : (budget >= minBid ? minBid : null);
    });
    if (claims.some(function (c) { return c.bid === null; })) notes.push('Not enough FAAB left for some claims.');
    claims = claims.filter(function (c) { return c.bid !== null; });
  }
  return {
    pending: pending.length,
    faab: this.faab,
    basis: this.qbPremium ? 'rest-of-season ECR, superflex-adjusted' : 'rest-of-season ECR',
    notes: notes,
    claims: claims.map(function (c) {
      var vw = function (pid, value) {
        if (c.kind !== 'stream') return self.view(pid, value);
        var r = self.weeklyRank(pid), wl = self.weeklyList(self.pos(pid));
        return self.view(pid, r || value, { why: !(self.team(pid) in wl.teamKickoff) || (r && r.bye) ? 'bye' : null });
      };
      return { kind: c.kind, bid: c.bid === undefined ? null : c.bid,
               add: vw(c.add, c.addValue), drop: c.drop ? vw(c.drop, c.dropValue) : null };
    }),
  };
};

League_.prototype.neverDrop = function () {
  var self = this, wanted = {}, names = {};
  (this.cfg.never_drop || []).forEach(function (x) { wanted[String(x)] = true; names[normName_(x)] = true; });
  var out = {};
  (this.roster.players || []).forEach(function (pid) {
    if (wanted[pid] || names[normName_((self.p(pid) || [])[0])]) out[pid] = true;
  });
  return out;
};

League_.prototype.applyLineup = function (res, who) {
  var l = res.lineup;
  if (!l || l.error || l.skipped || !l.changes) return;
  try {
    setStarters_(this.ctx.token, this.id, this.roster.roster_id, l.starters);
    l.applied = true;
    log_({ level: 'change', league: this.name, title: 'Lineup updated (' + who + ')',
           lines: l.benched.map(function (p) { return 'OUT ' + p.name + (p.why ? ' (' + p.why + ')' : ''); })
             .concat(l.lineup.filter(function (p) { return p.isNew; })
               .map(function (p) { return 'IN  ' + p.name + ' → ' + p.slot; })) });
  } catch (e) {
    if (e.expired) throw e;
    l.applyError = String(e.message || e);
    log_({ level: 'error', league: this.name, title: 'Lineup update failed', lines: [l.applyError] });
  }
};

League_.prototype.applyClaims = function (res, who) {
  var w = res.waivers, self = this;
  if (!w || w.error || !w.claims.length) return;
  var lines = [];
  w.claims.forEach(function (c) {
    try {
      submitClaim_(self.ctx.token, self.id, self.roster.roster_id, c.add.id, c.drop && c.drop.id,
                   self.faab ? c.bid : null);
      c.submitted = true;
      lines.push('Claim ' + c.add.name + (c.drop ? ', drop ' + c.drop.name : '') + (self.faab ? ' ($' + c.bid + ')' : ''));
    } catch (e) {
      if (e.expired) throw e;
      c.error = String(e.message || e);
      lines.push('FAILED ' + c.add.name + ': ' + c.error);
    }
  });
  log_({ level: w.claims.some(function (c) { return c.error; }) ? 'error' : 'change', league: this.name,
         title: 'Waiver claims submitted (' + who + ')', lines: lines });
};
