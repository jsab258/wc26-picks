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
  ROS_K: 'ros-k', ROS_DST: 'ros-dst',
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
  cover_byes: true,          // one-week pickup when a starter can't play and the bench can't fill in
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
var SPARE_MIN = 150;     // ROS value past which a bench player is easy to replace
var LATE_FLEX = 0.4;     // flex slots: up to this many ECR spots for a later kickoff (keeps a swap open)
var QUESTIONABLE = 2;    // a Questionable player must rank this many spots better than a healthy one
var TD6_QB_LEAN = 10;    // 6-pt passing TDs (ECR assumes 4): extra superflex QB lean, in ECR spots
var TD6_QB_VALUE = 0.85; // ...and QB waiver values count this much of their ECR rank (lower is better)
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
    build: buildInfo_(),
    update: { installed: !!RUNNING_INSTALLED_, error: LOAD_ERROR_ || null,
              pasted: PASTED_BUILD_ ? PASTED_BUILD_.title : null },
    permissions: missingScopes_(CORE_SCOPES),
    alerts: alertsView_(),
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
    var cfg = leagueCfg_(s, data.league_id);
    try {
      return new League_(ctx, data, user.user_id, cfg).evaluate({ lineup: true, waivers: true, freeAgents: true });
    } catch (e) {
      if (e.expired) throw e;
      // One league failing to load (e.g. Sleeper erroring on its rosters) mustn't hide the others.
      return { id: data.league_id, name: data.name || data.league_id, flags: [], slots: [], settings: cfg,
               notes: ["Couldn't load this league: " + (e.message || e)], lineup: null, waivers: null,
               status: data.status };
    }
  });
  return { state: getState(), week: ctx.state.week, season: ctx.state.league_season, leagues: leagues };
}

function setMode(mode) {
  var s = settings_();
  s.mode = mode === 'auto' ? 'auto' : 'suggest';
  putJson_('settings', s);
  deleteJson_('idle_until');
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
  deleteJson_('idle_until');
  return leagueCfg_(s, leagueId);
}

function applyLineup(leagueId) {
  return withLock_(function () {
    return withLeague_(leagueId, function (lg) {
      var res = lg.evaluate({ lineup: true });
      if (!blocked_(res)) lg.applyLineup(res, 'manual');
      return res;
    });
  });
}

/**
 * Submit the claims the page showed: ``shown`` is [[add id, drop id, bid], ...]. The plan
 * is made again first, and if it changed in the meantime (new rankings, a player got
 * picked up) nothing is sent and the page shows the new plan to check instead.
 */
function submitClaims(leagueId, shown) {
  if (!shown) throw new Error('Reload the page and try again.');
  return withLock_(function () {
    return withLeague_(leagueId, function (lg) {
      var res = lg.evaluate({ freeAgents: true, waivers: true });  // as on the page: claims come after free agents
      var w = res.waivers;
      if (w && !w.error && claimKeys_(w.claims) !== shown.map(function (c) { return c.join('|'); }).join(',')) {
        w.changed = true;
        return res;
      }
      if (!blocked_(res)) lg.applyClaims(res, 'manual');
      return res;
    });
  });
}

/** Pick up the free agents the page showed (same check as submitClaims). */
function addFreeAgents(leagueId, shown) {
  if (!shown) throw new Error('Reload the page and try again.');
  return withLock_(function () {
    return withLeague_(leagueId, function (lg) {
      var res = lg.evaluate({ freeAgents: true });
      var f = res.freeAgents;
      if (f && !f.error && !f.waiting && claimKeys_(f.claims) !== shown.map(function (c) { return c.join('|'); }).join(',')) {
        f.changed = true;
        return res;
      }
      if (!blocked_(res)) lg.applyFreeAgents(res, 'manual');
      return res;
    });
  });
}

/** A plan that fails the safety check is never carried out (the page shows why). */
function blocked_(res) {
  return !!(res.safety && res.safety.length);
}

function claimKeys_(claims) {
  return claims.map(function (c) {
    return [c.add.id, c.drop ? c.drop.id : null, c.bid === undefined ? null : c.bid].join('|');
  }).join(',');
}

/**
 * Check lineups right now, ignoring the 30-hour window. They're only saved when the
 * autopilot is on; in suggestions-only mode this just reports what it would change.
 */
function runNow() {
  withLock_(function () { autopilot_({ force: true }); });
  return getState();
}

/** One writer at a time: the buttons wait for a background check that's running. */
function withLock_(fn) {
  var lock = LockService.getUserLock();
  if (!lock.tryLock(30000)) throw new Error('The autopilot is busy right now. Try again in a minute.');
  try { return fn(); } finally { lock.releaseLock(); }
}

// ---- phone alerts ---------------------------------------------------------
// Push notifications through ntfy (https://ntfy.sh): free, no account, and it only
// needs the "connect to an external service" permission the app already has.
var NTFY_URL = 'https://ntfy.sh';

function alertsView_() {
  var a = settings_().alerts;
  return { on: !!a.topic, topic: a.topic || null, changes: a.changes !== false };
}

/** UI: turn alerts on (creates a private random topic), off, or choose whether changes are sent too. */
function saveAlerts(patch) {
  patch = patch || {};
  var s = settings_(), a = s.alerts;
  if (patch.on === true && !a.topic) a.topic = 'sleeper-autopilot-' + Utilities.getUuid().replace(/-/g, '').slice(0, 20);
  if (patch.on === false) a = {};
  if ('changes' in patch && a.topic) a.changes = !!patch.changes;
  s.alerts = a;
  putJson_('settings', s);
  deleteJson_('idle_until');
  return getState();
}

function testAlert() {
  var a = settings_().alerts;
  if (!a.topic) throw new Error('Turn alerts on first.');
  var r = sendAlert_(a.topic, { title: 'Sleeper Autopilot', message: 'Test alert: alerts reach this phone.',
                               tags: ['white_check_mark'] });
  if (r.code !== 200) throw new Error('ntfy refused the alert (HTTP ' + r.code + ').');
  return true;
}

function sendAlert_(topic, n) {
  return fetch_(NTFY_URL, { retries: 1, payload: { topic: topic, title: n.title, message: n.message,
                                                   priority: n.priority || 3, tags: n.tags || [],
                                                   click: appUrl_() || undefined } });
}

var ALERT_KINDS = {
  action: { priority: 4, tags: ['warning'] },         // needs you: always sent
  change: { priority: 3, tags: ['white_check_mark'] },  // the autopilot did something: optional
  info: { priority: 2, tags: ['arrow_up'] },            // e.g. a new version: always sent, quietly
};

/** Send a phone alert if they're on. With ``key``, the same alert goes out only once. */
function notify_(kind, title, message, key) {
  var a = settings_().alerts;
  if (!a.topic || (kind === 'change' && a.changes === false)) return;
  if (key) {
    var sent = getJson_('alerts_sent', {});
    if (sent[key]) return;
    sent[key] = Date.now();
    putJson_('alerts_sent', pruneDone_(sent));
  }
  try {
    sendAlert_(a.topic, { title: title, message: message, priority: ALERT_KINDS[kind].priority,
                          tags: ALERT_KINDS[kind].tags });
  } catch (e) { /* alerts are best effort */ }
}

/** Once a day, with alerts on: tell the phone when a new version is out. */
function checkUpdateDaily_() {
  if (!settings_().alerts.topic) return;
  var last = getJson_('update_checked', 0);
  if (Date.now() - last < 20 * 3600 * 1000) return;
  putJson_('update_checked', Date.now());
  try {
    var u = checkForUpdate();
    if (u.available) {
      notify_('info', 'Update available: ' + u.latest.title, 'Open Sleeper Autopilot and tap Install update.',
              'update:' + u.latest.id);
    }
  } catch (e) { /* try again tomorrow */ }
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

var CAPTCHA_MSG = 'Sleeper wants a captcha before it lets this login through (via Google). ' +
  'Connect via sleeper.com instead.';

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
  // sleeper.com keeps these JSON-encoded, so they can arrive wrapped in quotes.
  token = token.replace(/^"+|"+$/g, '');
  userId = String(userId || '').replace(/\D/g, '') || null;
  if (token.split('.').length !== 3) throw new Error("That doesn't look like a Sleeper login. Copy it again.");
  return finishLogin_(token, username, userId);
}

function logout() {
  store_().deleteProperty('token');
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
  deleteJson_('idle_until');
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
    checkUpdateDaily_();
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
  var auto = s.mode === 'auto';  // only then does anything get saved to Sleeper
  var alerting = !!s.alerts.topic && !opts.force;  // in suggestions-only mode, alerts say what to do
  if (!auto && !opts.force && !alerting) {
    recordTick_('idle', 'Suggestions only: autopilot is paused.');
    return;
  }
  // Nothing can need doing before this (no games within 30h, no waiver window): skip all downloads.
  if (!opts.force && Date.now() / 1000 < getJson_('idle_until', 0)) {
    recordTick_('ok', 'No games in the next 30h; nothing to do.');
    return;
  }
  var ctx = new Ctx_(token);
  var user = getJson_('user', {});
  var schedule = ctx.ranks(FP.OP.PPR);
  var nextKick = nextKickoff_(schedule, ctx.now);
  var lineupWindow = opts.force || (schedule.week === Number(ctx.state.week) && nextKick &&
                                    nextKick - ctx.now <= 30 * 3600);
  var done = getJson_('waivers_done', {});
  var summary = [], failed = false, wake = nextKick ? nextKick - 30 * 3600 : ctx.now + 3 * 3600;
  // A problem that persists is logged (and sent to the phone) once, not on every 30-minute check.
  var seen = getJson_('tick_errors', {}), errors = {};
  var fail = function (key, league, title, msg, logged) {
    failed = true;
    errors[key] = msg;
    if (seen[key] === msg) return;
    if (!logged) log_({ level: 'error', league: league, title: title, lines: [msg] });
    notify_('action', league + ': ' + title.toLowerCase(), msg);
  };
  try {
    myLeagues_(ctx, user.user_id).forEach(function (data) {
      var name = data.name || data.league_id;
      try {
        var cfg = leagueCfg_(s, data.league_id);
        var lg = new League_(ctx, data, user.user_id, cfg);
        if (!lg.roster || data.status !== 'in_season') return;
        // After this week's waivers: fill holes with free agents (no waiver priority spent).
        if (cfg.auto_waivers && !opts.force && Number(lg.settings.leg) === Number(ctx.state.week)) {
          var fres = lg.evaluate({ freeAgents: true }), f = fres.freeAgents || {};
          if (f.error) {
            summary.push(name + ": couldn't check free agents");
            fail(lg.id + ':fa', name, 'Free-agent check failed', f.error);
          } else if (blocked_(fres)) {
            summary.push(name + ': free agents held back by a safety check');
            fail(lg.id + ':fa-safety', name, 'Safety check stopped free-agent pickups', fres.safety.join(' '));
          } else if (f.claims && f.claims.length && !f.pendingUnknown) {
            if (auto) {
              lg.applyFreeAgents(fres, 'autopilot');
              var added = f.claims.filter(function (c) { return c.submitted; }).length;
              var failedFa = f.claims.some(function (c) { return c.error; });
              summary.push(name + ': ' + added + ' free agent' + (added === 1 ? '' : 's') + ' added');
              notify_(failedFa ? 'action' : 'change', name + (failedFa ? ': a free-agent pickup failed' : ': free agents picked up'),
                      claimLines_(f, false).join('\n'));
              if (added) lg = new League_(ctx, data, user.user_id, cfg);  // fresh roster for the lineup below
            } else if (alerting) {
              notify_('action', name + ': free agents to add', claimLines_(f, false).join('\n') +
                      '\nOpen Sleeper Autopilot and tap Add now.', 'fa:' + lg.id + ':' + claimKeys_(f.claims));
            }
          }
        }
        if (lineupWindow && !lg.settings.best_ball && (cfg.auto_lineup || !auto)) {
          var res = lg.evaluate({ lineup: true }), l = res.lineup || {};
          if (l.error) {
            summary.push(name + ": couldn't check the lineup");
            fail(lg.id + ':lineup', name, 'Lineup check failed', l.error);
          } else if (blocked_(res)) {
            summary.push(name + ': lineup held back by a safety check');
            fail(lg.id + ':lineup-safety', name, 'Safety check stopped the lineup', res.safety.join(' '));
          } else if (l.changes && auto) {
            lg.applyLineup(res, 'autopilot');
            if (l.applied) {
              summary.push(name + ': lineup updated');
              notify_('change', name + ': lineup updated', lineupLines_(l).join('\n'));
            } else {
              summary.push(name + ': saving the lineup failed');
              fail(lg.id + ':save', name, 'Saving the lineup failed', l.applyError, true);
            }
          } else if (l.changes) {
            summary.push(name + ': ' + l.changes + ' lineup change' + (l.changes > 1 ? 's' : '') + ' suggested');
            if (alerting) {
              notify_('action', name + ': lineup changes to make', lineupLines_(l).join('\n') +
                      '\nOpen Sleeper Autopilot and tap Apply now.', 'suggest:' + lg.id + ':' + l.starters.join(','));
            }
          }
          if (alerting && l.warnings) {
            l.warnings.forEach(function (w) {
              notify_('action', name + ": a starter can't play", w, 'warn:' + lg.id + ':' + l.week + ':' + w);
            });
          }
        }
        var win = waiverWindow_(lg, ctx.now);
        if (cfg.auto_waivers) {
          var next = nextWaiverWindow_(lg, ctx.now);
          if (next) wake = Math.min(wake, next);
          // Waivers run the next morning (~03:05 New York time); free agents open up after that.
          var faOpen = next && next - 7 * 86400 + 17 * 3600;
          if (faOpen && faOpen > ctx.now) wake = Math.min(wake, faOpen);
        }
        if (cfg.auto_waivers && !opts.force && win && !done[lg.id + ':' + win]) {
          var wres = lg.evaluate({ waivers: true }), w = wres.waivers || {};
          if (w.error || w.pendingUnknown) {
            summary.push(name + ": couldn't plan waiver claims");
            fail(lg.id + ':waivers', name, 'Waiver planning failed', w.error || PENDING_UNKNOWN_MSG);
            return;  // try again on the next tick
          }
          if (blocked_(wres)) {
            summary.push(name + ': claims held back by a safety check');
            fail(lg.id + ':waivers-safety', name, 'Safety check stopped the waiver claims', wres.safety.join(' '));
            return;
          }
          if (!auto) {
            if (w.claims.length) {
              notify_('action', name + ': waiver claims to make', claimLines_(w, lg.faab).join('\n') +
                      '\nOpen Sleeper Autopilot and tap Submit claims now.', 'claims:' + lg.id + ':' + win);
            }
            return;
          }
          lg.applyClaims(wres, 'autopilot');
          var bad = w.claims.filter(function (c) { return c.error; });
          var sent = w.claims.length - bad.length;
          if (bad.length) {
            // Not marked done: the next check plans again (the claims that went through are pending
            // on Sleeper by then) and retries the rest while the window is open.
            summary.push(name + ': ' + sent + ' claim(s), ' + bad.length + ' failed (retrying)');
            fail(lg.id + ':claims', name, 'Some waiver claims failed', bad.map(function (c) {
              return c.add.name + ': ' + c.error;
            }).join(' '), true);
            return;
          }
          done[lg.id + ':' + win] = Date.now();
          putJson_('waivers_done', pruneDone_(done));
          summary.push(name + ': ' + w.claims.length + ' claim(s)');
          if (w.claims.length) notify_('change', name + ': waiver claims submitted', claimLines_(w, lg.faab).join('\n'));
        }
      } catch (e) {
        if (e.expired) throw e;
        summary.push(name + ': error');
        fail(data.league_id + ':league', name, "Couldn't check this league", String(e.message || e));
      }
    });
  } catch (e) {
    if (e.expired) { recordTick_('error', EXPIRED_MSG); return; }
    throw e;
  }
  putJson_('tick_errors', errors);
  if (!opts.force && !lineupWindow && !failed) putJson_('idle_until', Math.min(wake, ctx.now + 12 * 3600));
  var idle = !lineupWindow ? 'No games in the next 30h; nothing to do.' : 'Checked lineups: all optimal.';
  recordTick_(failed ? 'error' : 'ok', summary.length ? summary.join(' · ') : idle);
}

function lineupLines_(l) {
  var lines = l.benched.map(function (p) { return 'OUT ' + p.name + (p.why ? ' (' + p.why + ')' : ''); })
    .concat(l.lineup.filter(function (p) { return p.isNew; }).map(function (p) { return 'IN  ' + p.name + ' → ' + p.slot; }));
  return lines.length ? lines : ['Same players, new spots (a later game goes in the flex).'];
}

function claimLines_(w, faab) {
  return w.claims.map(function (c) {
    return (c.error ? 'FAILED ' : '') + '+ ' + c.add.name + (c.drop ? ', drop ' + c.drop.name : '') +
      (faab && c.bid !== null ? ' ($' + c.bid + ')' : '') + (c.error ? ': ' + c.error : '');
  });
}

function nextKickoff_(list, now) {
  var next = null;
  Object.keys(list.teamKickoff).forEach(function (t) {
    var k = list.teamKickoff[t];
    if (k > now && (next === null || k < next)) next = k;
  });
  return next;
}

/** The league's waiver day as a JS weekday (0 = Sunday), or null with daily waivers. */
function waiverDay_(lg) {
  if (lg.settings.daily_waivers) return null;
  var wd = lg.settings.waiver_day_of_week;
  if (wd === undefined || wd === null) wd = 2;  // Sleeper's default, Wednesday
  return (Number(wd) + 1) % 7;  // Sleeper: 0=Mon; JS: 0=Sun
}

/** Claims go in the evening before the league's waiver day (UTC). Returns a window id or null. */
function waiverWindow_(lg, now) {
  var waiverDay = waiverDay_(lg);
  if (waiverDay === null) return null;
  var d = new Date(now * 1000);
  var day = d.getUTCDay(), hour = d.getUTCHours();
  var before = (waiverDay + 6) % 7;
  if ((day === before && hour >= 16) || (day === waiverDay && hour < 5)) {
    var start = new Date(d.getTime() - (day === waiverDay ? 86400000 : 0));
    return start.toISOString().slice(0, 10);
  }
  return null;
}

/** When the next claim window opens (epoch seconds), or null. */
function nextWaiverWindow_(lg, now) {
  var waiverDay = waiverDay_(lg);
  if (waiverDay === null) return null;
  var d = new Date(now * 1000), day0 = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) / 1000;
  for (var i = 0; i < 8; i++) {
    var t = day0 + i * 86400 + 16 * 3600;
    if (new Date(t * 1000).getUTCDay() === (waiverDay + 6) % 7 && t > now) return t;
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
// Self-update from GitHub
// ===================================================================

// The single-file build carries BUILD_INFO (id, version, release notes) and ends
// by calling loadInstalledUpdate_(). Installing an update stores the newer build's
// full text in this user's script storage; every execution (page, button, timer)
// then evaluates it on top of the pasted code, replacing every function. No Google
// API or extra permission is involved, and the pasted code stays as the fallback.
var UPDATE_URLS = [
  'https://raw.githubusercontent.com/jsab258/wc26-picks/main/fantasy/apps-script/dist/SleeperAutopilot.gs',
  'https://raw.githubusercontent.com/jsab258/wc26-picks/ccr-23b89428-f20cvp/fantasy/apps-script/dist/SleeperAutopilot.gs',
];
// No initializers on purpose: the installed code re-declares these while it loads,
// and a "var x = ..." there would reset them mid-load.
var INSTALLING_, PASTED_BUILD_, RUNNING_INSTALLED_, LOAD_ERROR_;
var GLOBAL_ = this;

function buildInfo_() {
  return typeof BUILD_INFO !== 'undefined' ? BUILD_INFO : { id: 'dev', version: 0, title: 'development copy', notes: [] };
}

function readBuildInfo_(text) {
  var m = /\nvar BUILD_INFO = (\{.*\});\n/.exec(text);
  return m ? JSON.parse(m[1]) : { id: 'legacy', version: 0, title: 'older build', notes: [] };
}

/**
 * The build published on GitHub: main's once main has one, the development branch's
 * until then. Main being unreachable is not a reason to fall back to the branch.
 */
function latestBuild_() {
  for (var i = 0; i < UPDATE_URLS.length; i++) {
    var r = fetch_(UPDATE_URLS[i], { retries: 1 });
    if (r.code === 404) continue;
    if (r.code !== 200) return null;
    return { info: readBuildInfo_(r.text), text: r.text };
  }
  return null;
}

/**
 * Runs at the end of the pasted file. An installed update only applies on top of
 * the exact paste it was installed on, so pasting a different build by hand
 * always wins.
 */
function loadInstalledUpdate_() {
  if (INSTALLING_) return;  // this is the installed code itself loading
  PASTED_BUILD_ = buildInfo_();
  var pkg = getJson_('engine', null);
  if (!pkg || pkg.base !== PASTED_BUILD_.id) return;
  INSTALLING_ = true;
  try {
    // Global eval: redefines every function and setting. It parses the whole text
    // before running any of it, so a damaged copy fails without half-loading.
    (0, eval)(pkg.code);
    RUNNING_INSTALLED_ = true;
  } catch (e) {
    LOAD_ERROR_ = String(e.message || e);
  } finally {
    INSTALLING_ = false;
  }
}

// Google's consent screen has a checkbox per permission (granular consent), and an
// unticked one is simply not granted: the script still runs and isn't asked again.
var CORE_SCOPES = ['https://www.googleapis.com/auth/script.external_request',
                   'https://www.googleapis.com/auth/script.scriptapp'];

/** {scopes: [...not granted], url: Google's approval page} or null when all are granted. */
function missingScopes_(scopes) {
  try {
    var mode = ScriptApp.AuthMode.FULL, required = ScriptApp.AuthorizationStatus.REQUIRED;
    var missing = scopes.filter(function (sc) {
      return ScriptApp.getAuthorizationInfo(mode, [sc]).getAuthorizationStatus() === required;
    });
    if (!missing.length) return null;
    return { scopes: missing, url: ScriptApp.getAuthorizationInfo(mode, scopes).getAuthorizationUrl() };
  } catch (e) {
    return null;  // runtime without per-scope checks: nothing we can tell
  }
}

/** UI: is there a newer build than the one running? */
function checkForUpdate() {
  var cur = buildInfo_();
  var latest = latestBuild_();
  if (!latest) return { current: cur, error: "Couldn't reach GitHub to check for updates." };
  var available = latest.info.id !== cur.id && latest.info.version >= cur.version;
  return { current: cur, latest: latest.info, available: available,
           notes: available ? latest.info.notes.slice(0, Math.max(1, latest.info.version - cur.version)) : [] };
}

/** UI: download the newest build and store it; it takes over from the next run on. */
function installUpdate(expectedId) {
  var latest = latestBuild_();
  if (!latest) throw new Error("Couldn't download the update from GitHub.");
  if (expectedId && latest.info.id !== expectedId) throw new Error('An even newer update just appeared. Check again.');
  var text = latest.text;
  var complete = text.indexOf('function doGet(') >= 0 && text.indexOf('\nvar UI_HTML = ') >= 0 &&
    /\nloadInstalledUpdate_\(\);\n$/.test(text);
  try {
    if (complete) new Function(text);
  } catch (e) {
    complete = false;
  }
  if (!complete) throw new Error('The downloaded update looks incomplete, so it was not installed.');
  putJson_('engine', { base: (PASTED_BUILD_ || buildInfo_()).id, info: latest.info, code: text, at: Date.now() });
  log_({ level: 'info', title: 'Installed update "' + latest.info.title + '"' });
  return { info: latest.info, url: appUrl_() };
}

/** UI: forget the installed update and run the pasted code again. */
function removeUpdate() {
  deleteJson_('engine');
  log_({ level: 'info', title: 'Removed the installed update; back to the pasted version' });
  return getState();
}

/**
 * UI entry point for every server call, so an installed update can add server
 * functions the pasted code never had.
 */
var PUBLIC_API = ['getState', 'getDashboard', 'setMode', 'saveLeagueSettings', 'applyLineup', 'submitClaims',
                  'runNow', 'login', 'verifyCode', 'connectWithToken', 'logout', 'checkForUpdate',
                  'installUpdate', 'removeUpdate', 'saveAlerts', 'testAlert', 'addFreeAgents'];

function call(name, args) {
  if (PUBLIC_API.indexOf(name) < 0 || typeof GLOBAL_[name] !== 'function') throw new Error('Unknown action: ' + name);
  return GLOBAL_[name].apply(null, args || []);
}

function appUrl_() {
  try { return ScriptApp.getService().getUrl(); } catch (e) { return null; }
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
  return { mode: s.mode || 'suggest', leagues: s.leagues || {}, alerts: s.alerts || {} };
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
  if (n === 1) {
    s = p.getProperty(key + '#0') || '';
  } else {
    var all = p.getProperties();  // one call for big values: an installed update spans ~17
    for (var i = 0; i < n; i++) s += all[key + '#' + i] || '';
  }
  try { return JSON.parse(s); } catch (e) { return dflt; }
}

function deleteJson_(key) {
  var p = store_();
  var n = Number(p.getProperty(key + '#n') || 0);
  for (var i = 0; i < n; i++) p.deleteProperty(key + '#' + i);
  p.deleteProperty(key + '#n');
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

/**
 * Like cached_, but refreshed once older than ``maxAgeSec``; if the refresh fails, the
 * older copy (kept up to 6h) is used rather than nothing.
 */
function cachedFresh_(key, maxAgeSec, fn) {
  var hit = cacheGet_(key);
  if (hit && Date.now() / 1000 - hit.at < maxAgeSec) return hit.v;
  var v;
  try {
    v = fn();
  } catch (e) {
    if (hit) return hit.v;
    throw e;
  }
  try { cachePut_(key, { at: Date.now() / 1000, v: v }, 6 * 3600); } catch (e) { /* too big to cache: fine */ }
  return v;
}

// ===================================================================
// HTTP: Sleeper + FantasyPros
// ===================================================================

function fetch_(url, opt) {
  opt = opt || {};
  var params = { method: opt.method || (opt.payload ? 'post' : 'get'), muteHttpExceptions: true,
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

/** Sleeper REST. fresh: bypass Sleeper's CDN cache (rosters/lineups can be minutes stale). */
function sleeper_(path, fresh) {
  var r = fetch_(SLEEPER_REST + path + (fresh ? (path.indexOf('?') < 0 ? '?' : '&') + '_=' + Date.now() : ''));
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
var PENDING_UNKNOWN_MSG = "Couldn't read your pending claims on Sleeper, so no claims were submitted: " +
  'the plan could repeat ones you already have.';

/** Sleeper rejected our token: forget it (stops the autopilot) and say so once. */
function sessionExpired_() {
  if (token_()) {
    store_().deleteProperty('token');
    log_({ level: 'error', title: EXPIRED_MSG });
    notify_('action', 'Sleeper session expired', 'Open Sleeper Autopilot and connect again. Until then nothing is ' +
            'checked or changed.');
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

/**
 * Save the lineup for NFL week ``week``. Sleeper keeps a lineup per week
 * ("matchup leg"); roster_update_starters only covers the league's current leg,
 * which lags a day behind (it advances when waivers run), and silently keeps the
 * old lineup otherwise. So we write the week's leg, also update the roster when
 * the league is already on that week, and check what Sleeper sends back.
 */
function setStarters_(token, leagueId, rosterId, starters, week, leagueLeg) {
  var same = function (got) { return got && got.join(',') === starters.join(','); };
  var q = 'mutation update_matchup_leg($leagueId: String!, $rosterId: Int!, $round: Int!, $leg: Int!,' +
    ' $starters: [String]) { update_matchup_leg(league_id: $leagueId, roster_id: $rosterId, round: $round,' +
    ' leg: $leg, starters: $starters) { leg round starters } }';
  var leg = gql_(q, { leagueId: leagueId, rosterId: rosterId, round: week, leg: week, starters: starters },
                 token, 1).update_matchup_leg;
  if (!leg || !same(leg.starters)) throw new Error("Sleeper didn't accept the week " + week + ' lineup.');
  if (Number(leagueLeg) === Number(week)) {
    var rq = 'mutation roster_update_starters($leagueId: String!, $rosterId: Int!, $starters: [String]) {' +
      ' roster_update_starters(league_id: $leagueId, roster_id: $rosterId, starters: $starters) { roster_id starters } }';
    var roster = gql_(rq, { leagueId: leagueId, rosterId: rosterId, starters: starters }, token, 1).roster_update_starters;
    if (!roster || !same(roster.starters)) throw new Error("Sleeper didn't accept the lineup.");
  }
  return leg;
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

/**
 * Pick up a free agent right away (dropping ``drop``, if any), exactly as sleeper.com's
 * Add button does. Players still on waivers need submit_waiver_claim instead.
 */
function addFreeAgent_(token, leagueId, rosterId, add, drop) {
  var q = 'mutation league_create_transaction($k_adds: [String], $v_adds: [Int], $k_drops: [String], $v_drops: [Int]) {' +
    ' league_create_transaction(league_id: "' + String(leagueId).replace(/\D/g, '') + '", type: "free_agent",' +
    ' k_adds: $k_adds, v_adds: $v_adds, k_drops: $k_drops, v_drops: $v_drops) {' +
    ' adds drops leg roster_ids status transaction_id type } }';
  var t = gql_(q, { k_adds: [add], v_adds: [rosterId], k_drops: drop ? [drop] : [], v_drops: drop ? [rosterId] : [] },
               token, 1).league_create_transaction;
  if (!t || !t.adds || !(add in t.adds) || (t.status && t.status !== 'complete')) {
    throw new Error("Sleeper didn't complete the pickup" + (t && t.status ? ' (' + t.status + ')' : '') + '.');
  }
  return t;
}

/** Recently dropped players are on waivers until waiver_clears_at: player id -> epoch seconds. */
function waiverClears_(token, leagueId) {
  var q = 'query league_players($league_id: String!) { league_players(league_id: $league_id) { player_id settings } }';
  var out = {};
  (gql_(q, { league_id: leagueId }, token).league_players || []).forEach(function (p) {
    var t = p.settings && p.settings.waiver_clears_at;
    if (t) out[p.player_id] = Number(t);
  });
  return out;
}

/** Players this roster picked up in the last 7 days (claims or free agents): id -> epoch ms. */
function recentAdds_(leagueId, rosterId, leg, nowMs) {
  var out = {};
  [leg, leg - 1].forEach(function (l) {
    if (!(l >= 1)) return;
    (sleeper_('/league/' + leagueId + '/transactions/' + l, true) || []).forEach(function (t) {
      if (t.status !== 'complete' || nowMs - t.status_updated > 7 * 86400000) return;
      Object.keys(t.adds || {}).forEach(function (p) { if (t.adds[p] === rosterId) out[p] = t.status_updated; });
    });
  });
  return out;
}

/** Upgrades the app made as free-agent pickups during a league's current leg (waiver cycle). */
function upgradesDone_(leagueId, leg) {
  var d = getJson_('upgrades_done', {})[leagueId];
  return d && d.leg === leg ? d.n : 0;
}

function countUpgrade_(leagueId, leg) {
  var all = getJson_('upgrades_done', {});
  all[leagueId] = { leg: leg, n: upgradesDone_(leagueId, leg) + 1 };
  putJson_('upgrades_done', all);
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
  return cachedFresh_('dp_ids2', 3 * 3600, function () {
    var r = fetch_(DP_IDS_URL);
    if (r.code !== 200) throw new Error("Couldn't download the player id table (HTTP " + r.code + ')');
    var rows = Utilities.parseCsv(r.text);
    var head = rows[0] || [], fi = head.indexOf('fantasypros_id'), si = head.indexOf('sleeper_id'), map = {};
    if (fi < 0 || si < 0) throw new Error('The player id table changed its format');
    for (var i = 1; i < rows.length; i++) {
      var f = rows[i][fi], s = rows[i][si];
      if (f && s && f !== 'NA' && s !== 'NA') map[f] = s;
    }
    return map;
  });
}

/**
 * How old Sleeper's player list (injury news) may be. Sleeper asks apps to fetch it
 * rarely, so it's refreshed every 6 hours, plus once after each kickoff slot's
 * inactives are announced (about 90 minutes before the games).
 */
function playersMaxAge_(kickoffs, now) {
  var since = null;
  kickoffs.forEach(function (k) {
    var out = k - 80 * 60;
    if (out <= now && now < k && (since === null || out > since)) since = out;
  });
  return since === null ? 6 * 3600 : Math.max(60, now - since);
}

/**
 * Sleeper's player db is ~14 MB; we keep only fantasy-relevant players as
 * [name, position, team, injury_status, fantasy_positions]. Refreshed more
 * often close to kickoff so game-day inactives are picked up.
 */
function playersSlim_(maxAgeSec) {
  return cachedFresh_('players2', maxAgeSec, function () {
    var r = fetch_(SLEEPER_REST + '/players/nfl');
    if (r.code !== 200) throw new Error("Couldn't download Sleeper's player list (HTTP " + r.code + ')');
    var out = parsePlayers_(r.text);
    if (!Object.keys(out).length) throw new Error("Sleeper's player list came back empty");
    return out;
  });
}

function parsePlayers_(text) {
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
  var kickoffs = {};
  this.ranksRaw_(FP.OP.PPR).players.forEach(function (r) { if (r[8]) kickoffs[r[8]] = true; });
  this.players = playersSlim_(playersMaxAge_(Object.keys(kickoffs).map(Number), this.now));
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
        if (c === null || c === undefined) return INELIGIBLE;
        // Tiny nudges so ties keep players where they are (no pointless slot swaps).
        return c - (current[si] === pid ? 2e-3 : nowStarting[pid] ? 1e-3 : 0);
      });
    });
    hungarian_(matrix).forEach(function (col, r) {
      starters[openIdx[r]] = matrix[r][col] < INELIGIBLE ? cols[col] : EMPTY;
    });
    // Never take out a player who is still on the roster without putting someone in:
    // an empty slot there means data didn't load (e.g. the player list), not a better lineup.
    var onRoster = {}, inLineup = {};
    roster.forEach(function (p) { onRoster[p] = true; });
    starters.forEach(function (p) { inLineup[p] = true; });
    openIdx.forEach(function (i) {
      var p = current[i];
      if (starters[i] === EMPTY && p !== EMPTY && onRoster[p] && !inLineup[p]) { starters[i] = p; inLineup[p] = true; }
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

/**
 * Best free agent first; each claim drops the weakest player it clearly beats.
 * Position minimums count healthy players only (an Out WR doesn't fill a WR spot),
 * and past o.maxDepth (e.g. a 4th QB in superflex) a pickup may only replace a
 * player at its own position.
 */
function planUpgrades_(o) {
  var counts = {};
  var healthy = o.healthy || function () { return true; };
  var maxDepth = o.maxDepth || {};
  (o.countFrom || o.myPlayers).forEach(function (p) {  // the roster as it will be (pending moves included)
    var pos = o.position(p);
    if (healthy(p)) counts[pos] = (counts[pos] || 0) + 1;
  });
  var openSpots = o.rosterLimit - o.myPlayers.length;
  var allow = o.allow || function () { return true; };  // e.g. "doesn't open a hole in this week's lineup"
  var cands = o.myPlayers.filter(function (p) {
    return !o.protected[p] && !o.blockedDrops[p] && o.dropValue(p) !== null;
  }).sort(function (a, b) { return o.dropValue(b) - o.dropValue(a); });  // weakest first
  var fas = o.freeAgents.filter(function (p) { return o.value(p) !== null; })
    .sort(function (a, b) { return o.value(a) - o.value(b); });
  var claims = [];
  for (var f = 0; f < fas.length && claims.length < o.maxClaims; f++) {
    var fa = fas[f], fv = o.value(fa), fpos = o.position(fa);
    var deep = maxDepth[fpos] !== undefined && (counts[fpos] || 0) >= maxDepth[fpos];
    // An open spot needs no drop, but with o.openSpotGain the pickup must still beat your weakest player.
    var weakest = cands.length ? o.dropValue(cands[0]) : Infinity;
    if (openSpots > 0 && !deep && (!o.openSpotGain || weakest - fv >= o.openSpotGain) && allow(fa, null, claims)) {
      claims.push({ add: fa, drop: null, addValue: fv, dropValue: null, kind: 'upgrade' });
      openSpots--;
      if (healthy(fa)) counts[fpos] = (counts[fpos] || 0) + 1;
      continue;
    }
    for (var c = 0; c < cands.length; c++) {
      var d = cands[c], dv = o.dropValue(d);
      if (dv - fv < o.minGain) break;
      if (o.extraGain && dv - fv < o.minGain + o.extraGain(d)) continue;
      if (!allow(fa, d, claims)) continue;
      var dpos = o.position(d);
      if (dpos !== fpos && deep) continue;
      // Healthy players left at the drop's position (an injured pickup doesn't replace a healthy one).
      var have = counts[dpos] || 0;
      var left = have - (healthy(d) ? 1 : 0) + (dpos === fpos && healthy(fa) ? 1 : 0);
      if (left < have && left < (o.minimums[dpos] || 0)) continue;
      claims.push({ add: fa, drop: d, addValue: fv, dropValue: dv, kind: 'upgrade' });
      cands.splice(c, 1);
      if (healthy(d)) counts[dpos]--;
      if (healthy(fa)) counts[fpos] = (counts[fpos] || 0) + 1;
      break;
    }
  }
  return claims;
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
  this.rolling = this.settings.waiver_type === 0;  // a successful claim sends you to the back of the line
  this.passTd6 = Number((data.scoring_settings || {}).pass_td || 4) >= 6;
  this.rosters = sleeper_('/league/' + this.id + '/rosters', true);
  this.roster = this.rosters.filter(function (r) {
    return r.owner_id === userId || (r.co_owners || []).indexOf(userId) >= 0;
  })[0] || null;
}

League_.prototype.p = function (pid) { return this.ctx.players[pid] || null; };

// League data fetched at most once per run (the planner and the safety check share it).
League_.prototype.pending_ = function () {
  if (this._pending === undefined) {
    var rid = this.roster.roster_id;
    this._pending = pendingWaivers_(this.ctx.token, this.id).filter(function (t) {
      return (t.roster_ids || []).indexOf(rid) >= 0;
    });
  }
  return this._pending;
};
League_.prototype.clears_ = function () {
  if (this._clears === undefined) this._clears = waiverClears_(this.ctx.token, this.id);
  return this._clears;
};
League_.prototype.recent_ = function () {
  if (this._recent === undefined) {
    try {
      this._recent = recentAdds_(this.id, this.roster.roster_id, Number(this.settings.leg) || Number(this.ctx.state.week),
                                 Date.now());
    } catch (e) {
      if (e.expired) throw e;
      this._recent = {};
    }
  }
  return this._recent;
};

/** When a player's game kicks off this week (0: no game). */
League_.prototype.kickoffOf = function (pid, kickoff) {
  var r = this.weeklyRank(pid);
  return (r && r.kickoff) || kickoff[this.team(pid)] || 0;
};

/**
 * Sleeper's own rule, once the week's waivers have run: a free agent is on nobody's roster,
 * wasn't just dropped (waiver_clears_at), and his game hasn't started (a team on bye:
 * until the week's first game kicks off).
 */
League_.prototype.isFreeAgent = function (pid, clears, kickoff) {
  var first = Math.min.apply(null, Object.keys(kickoff).map(function (t) { return kickoff[t]; }));
  return !(clears[pid] > this.ctx.now) && (this.kickoffOf(pid, kickoff) || first) > this.ctx.now;
};
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
  var p = this.p(pid) || ['Player ' + pid, '', null];  // not tracked (e.g. IDP): left as you set it
  var v = { id: pid, name: pid === EMPTY ? '(empty)' : p[0], pos: p[1], team: this.team(pid),
            rank: rank && rank.rank !== undefined ? rank.rank
              : (typeof rank === 'number' && rank < UNRANKED ? Math.round(rank) : null),
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
  // Free agents first: they're added now, and the waiver plan covers what's left.
  try {
    if (what.freeAgents) res.freeAgents = this.planWaivers({ freeAgents: true });
  } catch (e) {
    if (e.expired) throw e;
    res.freeAgents = { error: String(e.message || e) };
  }
  try {
    var f = res.freeAgents;
    if (what.waivers) res.waivers = this.planWaivers({ after: f && !f.error && !f.waiting ? f : null });
  } catch (e) {
    if (e.expired) throw e;
    res.waivers = { error: String(e.message || e) };
  }
  try {
    res.safety = checkPlans_(this, res);
  } catch (e) {
    if (e.expired) throw e;
    res.safety = ['The safety check itself failed: ' + (e.message || e)];
  }
  return res;
};

/**
 * This roster's lineup for NFL ``week`` as Sleeper will score it: the week's
 * matchup entry. roster.starters is the league's current week, which lags a day.
 */
League_.prototype.weekStarters = function (week) {
  var rid = this.roster.roster_id, mine = null;
  try {
    mine = (sleeper_('/league/' + this.id + '/matchups/' + week, true) || [])
      .filter(function (m) { return m.roster_id === rid; })[0];
  } catch (e) { /* no matchups for this week (bye/offseason): fall back */ }
  return (mine && mine.starters && mine.starters.length ? mine.starters : this.roster.starters) || [];
};

/** Kickoff time per NFL team this week, from the weekly lists this league uses. */
League_.prototype.weekKickoffs = function () {
  var self = this, kickoff = {};
  this.slots.forEach(function (s) {
    (SLOT_ELIGIBILITY[s] || []).forEach(function (pos) {
      var l = self.weeklyList(pos);
      Object.keys(l.teamKickoff).forEach(function (t) { kickoff[t] = l.teamKickoff[t]; });
    });
  });
  return kickoff;
};

/** Why a player can't play this week ('Out', 'bye'...), or null. */
League_.prototype.whyOut = function (pid, kickoff) {
  var injury = (this.p(pid) || [])[3], r = this.weeklyRank(pid);
  if (this.cfg.bench_statuses.indexOf(injury) >= 0) return injury;
  if ((r && r.bye) || !(this.team(pid) in kickoff)) return 'bye';
  return null;
};

League_.prototype.planLineup = function () {
  var self = this, ctx = this.ctx, cfg = this.cfg;
  var main = this.weeklyList(this.qbPremium ? 'QB' : 'RB');
  var week = Number(ctx.state.week);
  if (main.week !== week) {
    return { skipped: 'FantasyPros rankings are for week ' + main.week + '; Sleeper is on week ' + week + '.' };
  }
  var kickoff = this.weekKickoffs();
  var info = {};
  var current = this.weekStarters(week);
  var everyone = this.activePlayers().concat(current);
  var keep = this.neverDrop();
  everyone.forEach(function (pid) {
    if (pid === EMPTY || info[pid]) return;
    if (!self.p(pid)) { info[pid] = { r: null, locked: false, why: null }; return; }  // IDP etc.: not ours to judge
    var r = self.weeklyRank(pid);
    var ko = (r && r.kickoff) || kickoff[self.team(pid)];
    info[pid] = { r: r, ko: ko, locked: !!(r && r.started) || !!(ko && ko <= ctx.now), why: self.whyOut(pid, kickoff),
                  questionable: (self.p(pid) || [])[3] === 'Questionable' };
  });
  var times = Object.keys(info).map(function (pid) { return info[pid].ko; }).filter(Boolean);
  var first = Math.min.apply(null, times), last = Math.max.apply(null, times);
  var qbLean = cfg.superflex_qb_bonus + (this.passTd6 ? TD6_QB_LEAN : 0);
  var cost = function (pid, slot) {
    if (!self.eligible(pid, slot)) return null;
    var i = info[pid];
    var c = (i.r ? i.r.rank : UNRANKED) + (i.why ? UNAVAILABLE : 0) + (i.questionable ? QUESTIONABLE : 0);
    if (slot === 'SUPER_FLEX' && self.positions(pid).indexOf('QB') >= 0) c -= qbLean;
    // In a flex slot, a later game keeps a swap open if he's ruled out late. Never worth a whole rank spot.
    if (SLOT_ELIGIBILITY[slot].length > 1 && i.ko && last > first) c -= LATE_FLEX * (i.ko - first) / (last - first);
    return c;
  };
  var locked = {};
  Object.keys(info).forEach(function (pid) { if (info[pid].locked) locked[pid] = true; });
  var out = optimize_(this.slots, current, this.activePlayers(), cost, locked);
  var vw = function (pid) {
    if (pid === EMPTY) return self.view(EMPTY);
    var i = info[pid];
    return self.view(pid, i.r, { why: i.why, locked: i.locked, keep: !!keep[pid], tracked: !!self.p(pid) });
  };
  var after = {}, before = {};
  out.starters.forEach(function (p) { after[p] = true; });
  current.forEach(function (p) { before[p] = true; });
  return {
    week: week,
    changes: out.changes.length,
    starters: out.starters,
    current: current,
    lineup: out.starters.map(function (pid, i) {
      var v = vw(pid); v.slot = self.slots[i]; v.isNew = pid !== EMPTY && !before[pid]; return v;
    }),
    benched: current.filter(function (p) { return p !== EMPTY && !after[p]; }).map(vw),
    bench: this.activePlayers().filter(function (p) { return !after[p]; }).map(vw)
      .sort(function (a, b) { return (a.rank || 9999) - (b.rank || 9999); }),
    // Starting spots nobody healthy can fill this week (and not locked yet).
    holes: out.starters.map(function (p, i) {
      var slot = self.slots[i];
      if (!SLOT_ELIGIBILITY[slot] || (p !== EMPTY && (!info[p].why || info[p].locked))) return null;
      return { slot: slot, out: p };
    }).filter(Boolean),
    lockedIds: Object.keys(locked),
    warnings: out.starters.filter(function (p) {
      return p !== EMPTY && info[p].why && !info[p].locked;
    }).map(function (p) {
      return vw(p).name + ' (' + info[p].why + ') starts: you have no healthy ' + self.pos(p) +
        ' to replace him. Check the waiver plan or add a free agent.';
    }),
  };
};

/**
 * The starting spots this week that nobody on ``roster`` can play in, as [{slot, out}] (out:
 * who'd sit there, or EMPTY). Players who can play take the narrowest spots first, so the
 * empty ones are the easiest to fill and the answer doesn't depend on which of two equal
 * lineups gets picked. Locked players stay where they are in ``current`` (or on the bench).
 */
League_.prototype.weekHoles = function (roster, current, locked, kickoff) {
  var self = this;
  locked = locked || {};
  var width = function (slot) { return SLOT_ELIGIBILITY[slot].length; };
  var cost = function (p, slot) {
    if (!self.eligible(p, slot)) return null;
    return self.whyOut(p, kickoff) ? 100 - width(slot) : width(slot);
  };
  var cur = (current || []).map(function (p) { return roster.indexOf(p) >= 0 ? p : EMPTY; });
  var out = [];
  optimize_(this.slots, cur, roster, cost, locked).starters.forEach(function (p, i) {
    var slot = self.slots[i];
    if (!SLOT_ELIGIBILITY[slot] || (p !== EMPTY && locked[p])) return;
    if (p === EMPTY || self.whyOut(p, kickoff)) out.push({ slot: slot, out: p });
  });
  return out;
};

/**
 * True if ``after`` fills this week's starting spots at least as well as ``before`` (with
 * ``fills``: better): it fills as many, and still as many once up to three players of any
 * positions are added, so trading the only QB who plays for a flex player counts as worse.
 * It counts spots that can be filled rather than looking at which one ends up empty, so it
 * doesn't depend on which of two equal lineups is picked. Locked players stay put.
 */
League_.prototype.noWorseWeek = function (before, after, current, locked, kickoff, fills) {
  var self = this;
  locked = locked || {};
  current = current || [];
  var slots = this.slots.filter(function (slot) { return !!SLOT_ELIGIBILITY[slot]; });
  var positions = [];
  slots.forEach(function (slot) {
    SLOT_ELIGIBILITY[slot].forEach(function (pos) { if (positions.indexOf(pos) < 0) positions.push(pos); });
  });
  var shape = function (roster) {
    var on = {}, open = [], filled = 0;
    roster.forEach(function (p) { on[p] = true; });
    self.slots.forEach(function (slot, i) {
      if (!SLOT_ELIGIBILITY[slot]) return;
      var p = current[i];
      if (p && p !== EMPTY && locked[p] && on[p]) filled++; else open.push(slot);
    });
    var players = roster.filter(function (p) { return !locked[p] && !self.whyOut(p, kickoff); }).map(function (p) {
      return open.map(function (slot, j) { return self.eligible(p, slot) ? j : -1; }).filter(function (j) { return j >= 0; });
    });
    return { open: open, filled: filled, players: players };
  };
  var count = function (sh, extra) {  // most spots filled, with extra players of these positions
    var players = sh.players.concat(extra.map(function (pos) {
      return sh.open.map(function (slot, j) { return SLOT_ELIGIBILITY[slot].indexOf(pos) >= 0 ? j : -1; })
        .filter(function (j) { return j >= 0; });
    }));
    var match = {};  // open spot -> player (augmenting paths)
    var assign = function (pi, seen) {
      return players[pi].some(function (j) {
        if (seen[j]) return false;
        seen[j] = true;
        if (match[j] === undefined || assign(match[j], seen)) { match[j] = pi; return true; }
        return false;
      });
    };
    var n = sh.filled;
    for (var i = 0; i < players.length; i++) if (assign(i, {})) n++;
    return n;
  };
  var b = shape(before), a = shape(after), nb = count(b, []), na = count(a, []);  // b/a: before/after
  if (fills ? na <= nb : na < nb) return false;
  var holes = slots.length - nb;
  if (!holes) return true;
  // Every mix of up to three added players (as many as there are empty spots).
  var extras = [[]];
  for (var k = 0; k < Math.min(holes, 3); k++) {
    extras = extras.concat(extras.filter(function (x) { return x.length === k; }).reduce(function (all, x) {
      var from = x.length ? positions.indexOf(x[x.length - 1]) : 0;
      return all.concat(positions.slice(from).map(function (p) { return x.concat([p]); }));
    }, []));
  }
  return extras.every(function (x) { return !x.length || count(a, x) >= count(b, x); });
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

/** Past this many healthy players at a position, extra ones barely help (a 4th QB). */
League_.prototype.maxDepth = function () {
  var c = {};
  this.slots.forEach(function (s) { c[s] = (c[s] || 0) + 1; });
  return { QB: (c.QB || 0) + (c.SUPER_FLEX || 0) + 1, TE: (c.TE || 0) + 1 };
};

/**
 * The waiver plan, or with ``opts.freeAgents`` the free-agent plan: after this week's
 * waivers have run, unrostered players whose game is still ahead (and who weren't just
 * dropped) can be added right away, which fills holes without spending waiver priority.
 */
League_.prototype.planWaivers = function (opts) {
  var self = this, ctx = this.ctx, cfg = this.cfg;
  var fa = !!(opts && opts.freeAgents);
  var faOpen = fa || Number(this.settings.leg) === Number(ctx.state.week);  // this week's waivers have run
  var notes = [], lp = null, clears = {};
  if (fa) {
    if (Number(this.settings.leg) !== Number(ctx.state.week)) {
      return { freeAgents: true, waiting: "Free agents open up once this week's waivers have run.", claims: [], notes: [] };
    }
    lp = this.planLineup();
    if (lp.skipped) return { freeAgents: true, waiting: lp.skipped, claims: [], notes: [] };
    clears = this.clears_();
  }
  // Free agency happens now: players whose game has started can't be dropped, and this week's
  // starters aren't given up for a one-week pickup.
  var locked = {}, starting = {};
  if (fa) {
    lp.lockedIds.forEach(function (p) { locked[p] = true; });
    lp.starters.forEach(function (p) { starting[p] = true; });
  }
  var rostered = {};
  this.rosters.forEach(function (r) {
    (r.players || []).concat(r.reserve || [], r.taxi || []).forEach(function (p) { rostered[p] = true; });
  });
  var pending = [], pendingUnknown = false;
  try {
    pending = this.pending_();
  } catch (e) {
    if (e.expired) throw e;
    // Without them the plan could repeat claims you already have: show it, but don't submit it.
    pendingUnknown = true;
    notes.push("Couldn't read your pending claims on Sleeper (" + e.message + '), so this plan may repeat ' +
               "them and won't be submitted until that works again.");
  }
  var pendingAdds = {}, pendingDrops = {};
  pending.forEach(function (t) {
    Object.keys(t.adds || {}).forEach(function (p) { pendingAdds[p] = true; });
    Object.keys(t.drops || {}).forEach(function (p) { pendingDrops[p] = true; });
  });
  // Planned free-agent pickups happen first; this waiver plan is for what's left.
  var after = (opts && opts.after) || null, afterAdds = {}, afterDrops = {}, afterUpgrades = 0;
  if (after) {
    after.claims.forEach(function (c) {
      afterAdds[c.add.id] = true;
      if (c.drop) afterDrops[c.drop.id] = true;
      if (c.kind === 'upgrade') afterUpgrades++;
    });
  }
  if (faOpen && !fa) {
    try {
      clears = this.clears_();
    } catch (e) {
      if (e.expired) throw e;
      clears = null;  // can't tell who's a free agent, so no claims (they could be for free agents)
      notes.push("Couldn't read who's on waivers on Sleeper, so no claims are planned until that works again.");
    }
  }
  var kickoffNow = faOpen ? this.weekKickoffs() : {};
  var freeNow = function (pid) { return !!clears && self.isFreeAgent(pid, clears, kickoffNow); };
  // Players you just picked up need twice the usual gain to be dropped again.
  var recent = this.recent_();
  var ros = ctx.ranks(FP.ROS[this.fmt]);
  var template = this.qbPremium ? superflexTemplate_(this.weeklyList('QB'), ctx.players) : null;
  var value = function (pid) {
    var pos = self.pos(pid), r = ros.get(pid);
    if (SKILL.indexOf(pos) < 0 || !r) return null;
    var v = r.rank;
    if (template) {
      var m = /(\d+)$/.exec(r.posRank || '');
      v = templateValue_(template, pos, m ? Number(m[1]) : null);
    }
    return v !== null && pos === 'QB' && self.passTd6 ? v * TD6_QB_VALUE : v;
  };
  var keep = this.neverDrop();
  var mine = this.activePlayers();
  var slotCount = {};
  this.slots.forEach(function (s) { slotCount[s] = (slotCount[s] || 0) + 1; });
  // Rest-of-season K/DEF rank (1 = best); 999 when unranked.
  var kdNum = function (pid) {
    var list = ctx.ranks(self.pos(pid) === 'K' ? FP.ROS_K : FP.ROS_DST);
    var r = list.get(pid), m = r && /(\d+)$/.exec(r.posRank || '');
    return m ? Number(m[1]) : 999;
  };
  // More K/DEF than slots (e.g. last week's bye-week streamer): an extra can go if
  // he's outside the rest-of-season top 12 and not needed for the coming week.
  var excessKD = {};
  ['K', 'DEF'].forEach(function (pos) {
    var at = mine.filter(function (p) { return self.pos(p) === pos; });
    var n = slotCount[pos] || 0;
    if (!n || at.length <= n) return;
    var weekly = ctx.ranks(pos === 'K' ? FP.K : FP.DST);
    var thisWeek = function (p) { var r = weekly.get(p); return r && !r.bye ? r.rank : 999; };
    var needed = {};
    at.slice().sort(function (a, b) { return kdNum(a) - kdNum(b); }).slice(0, n).forEach(function (p) { needed[p] = true; });
    at.slice().sort(function (a, b) { return thisWeek(a) - thisWeek(b); }).slice(0, n).forEach(function (p) { needed[p] = true; });
    at.forEach(function (p) { if (!needed[p] && kdNum(p) > 12) excessKD[p] = true; });
  });
  var healthy = function (p) { return cfg.bench_statuses.indexOf((self.p(p) || [])[3]) < 0; };
  var dropValue = function (pid) {
    if (keep[pid]) return null;
    if (excessKD[pid]) return UNRANKED;
    if (SKILL.indexOf(self.pos(pid)) < 0) return null;
    var v = value(pid);
    if (v === null && !ros.get(pid) && !self.weeklyRank(pid)) return UNRANKED;  // in no ECR list: cut-able
    return v;
  };
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
    if (slot === 'K' || slot === 'DEF') return kdNum(pid);
    var v = value(pid);
    return v === null ? UNRANKED : v;
  };
  var core = {};
  optimize_(this.slots, [], mine, rosCost).starters.forEach(function (p) { core[p] = true; });
  var limit = (this.data.roster_positions || []).filter(function (s) { return s !== 'IR' && s !== 'TAXI'; }).length;
  // The weekly limit covers claims already pending on Sleeper, free-agent upgrades made
  // since this week's waivers ran and the ones planned above (fill-ins and streams don't count).
  var pendingUpgrades = Object.keys(pendingAdds).filter(function (p) { return SKILL.indexOf(self.pos(p)) >= 0; }).length;
  var used = pendingUpgrades + upgradesDone_(this.id, Number(this.settings.leg)) + afterUpgrades;
  var room = Math.max(0, cfg.max_claims - used);
  if (used && !room) {
    notes.push('Your limit of ' + cfg.max_claims + ' upgrades a week is used up (pending claims and this week\'s pickups).');
  }
  // Rolling waivers: a successful claim sends you to the back of the line, so a high
  // priority is only spent on a clear upgrade or to fill a starting spot.
  var prio = Number((this.roster.settings || {}).waiver_position) || null, teams = this.rosters.length;
  var guard = !fa && this.rolling && prio && prio <= Math.ceil(teams / 2);
  var minGain = cfg.min_gain * (guard ? 2 : 1);
  if (guard) {
    notes.push('Your waiver priority is #' + prio + ' of ' + teams + ' and a claim sends you to the back of the line, ' +
               'so upgrades must gain ' + minGain + ' spots instead of ' + cfg.min_gain + ', and kicker/defense ' +
               'matchup swaps wait until waivers have run, then come from free agency (no priority cost).');
  }
  var name = function (pid) { return (self.p(pid) || [pid])[0]; };
  var hardMin = { QB: slotCount.QB || 0, RB: slotCount.RB || 0, WR: slotCount.WR || 0, TE: slotCount.TE || 0 };

  // ---- Moves, one at a time, each on the roster as it will be after the ones before -------
  // Free agents are picked up now; claims go through at the waiver run. Pending claims and
  // (for the waiver plan) the free-agent plan come first. A move may not open a hole in
  // this week's lineup while this week can still be helped.
  var claims = [], usedDrops = {}, adding = {};
  var blocked = Object.assign({}, pendingDrops, afterDrops, locked);  // this plan can't drop them
  var withMoves = function (roster, moves) {
    var r = roster.slice();
    moves.forEach(function (c) {
      if (c.drop) r = r.filter(function (p) { return p !== c.drop; });
      if (r.indexOf(c.add) < 0) r.push(c.add);
    });
    return r;
  };
  // The roster once everything planned has gone through (for roster spots and depth)...
  var base = mine.filter(function (p) { return !pendingDrops[p] && !afterDrops[p]; });
  Object.keys(pendingAdds).concat(Object.keys(afterAdds)).forEach(function (p) { if (base.indexOf(p) < 0) base.push(p); });
  var rosterNow = function () { return withMoves(base, claims); };
  // ...and the one that plays this week: in free agency, claims still pending only go through
  // at next week's waiver run; before the run, pending claims go through with this plan's.
  var weekBase = fa ? mine.slice() : base;
  var weekRoster = function (moves) { return withMoves(weekBase, moves || claims); };
  var available = function (pid) {
    if (rostered[pid] || pendingAdds[pid] || afterAdds[pid] || adding[pid]) return false;
    if (fa) return freeNow(pid);
    // After the waiver run, claims are only for players still on waivers (and none if we can't tell).
    return !faOpen || (clears !== null && !freeNow(pid));
  };
  // This week's games, if a move can still help them (claims go through before Thursday).
  var mainList = this.weeklyList(this.qbPremium ? 'QB' : 'RB');
  var weekMatters = fa || (!faOpen && mainList.week === Number(ctx.state.week) && mainList.firstKickoff() > ctx.now);
  var kickoff = weekMatters || faOpen ? this.weekKickoffs() : {};
  var weekCost = function (pid, slot) {
    if (!self.eligible(pid, slot)) return null;
    var r = self.weeklyRank(pid);
    return (r ? r.rank : UNRANKED) + (self.whyOut(pid, kickoff) ? UNAVAILABLE : 0);
  };
  /** This week's best lineup for a roster (in free agency, locked players stay where they are). */
  var weekLineup = function (roster) {
    if (!fa) return optimize_(self.slots, [], roster, weekCost).starters;
    var current = lp.current.map(function (p) { return roster.indexOf(p) >= 0 ? p : EMPTY; });
    return optimize_(self.slots, current, roster, weekCost, locked).starters;
  };
  /** Starting spots nobody on this roster can fill this week. */
  var holesOf = function (roster) {
    return weekMatters ? self.weekHoles(roster, fa ? lp.current : [], locked, kickoff) : [];
  };
  var openSpots = function () { return limit - rosterNow().length; };
  var droppable = function (p) {
    return mine.indexOf(p) >= 0 && rosterNow().indexOf(p) >= 0 && !blocked[p] && !usedDrops[p] && !keep[p];
  };
  /** A bench player to give up for a one-week pickup: cheap, not needed this week, not just picked up. */
  var spare = function () {
    var need = {}, rosters = [rosterNow(), weekRoster()];
    if (weekMatters) weekLineup(weekRoster()).forEach(function (p) { need[p] = true; });
    var healthyAt = function (pos) {
      return Math.min.apply(null, rosters.map(function (r) {
        return r.filter(function (p) { return self.pos(p) === pos && healthy(p); }).length;
      }));
    };
    return mine.filter(function (p) {
      var v = dropValue(p), pos = self.pos(p);
      if (!droppable(p) || core[p] || need[p] || starting[p] || v === null || v < SPARE_MIN) return false;
      if (recent[p] && !excessKD[p]) return false;
      return !healthy(p) || !(pos in hardMin) || healthyAt(pos) - 1 >= hardMin[pos];
    }).sort(function (a, b) { return dropValue(b) - dropValue(a); })[0] || null;
  };
  /** Who goes for a pickup that fills ``hole``: a kicker/defense swaps with one of yours if possible. */
  var dropFor = function (hole) {
    if (hole.slot === 'K' || hole.slot === 'DEF') {
      var kds = mine.filter(function (p) { return self.pos(p) === hole.slot && droppable(p) && kdNum(p) > 12; });
      kds.sort(function (a, b) {
        return (self.whyOut(b, kickoff) ? 1 : 0) - (self.whyOut(a, kickoff) ? 1 : 0) || kdNum(b) - kdNum(a);
      });
      if (kds.length) return kds[0];
    }
    return spare();
  };
  /**
   * A move may not leave a starting spot this week that nobody can play in, whether or not the
   * moves before it go through (a rival can win a claim; a pickup can fail). With ``fills`` it
   * must also fill one of the empty spots.
   */
  var noNewHoles = function (fills) {
    var noWorse = function (before, after, better) {
      return self.noWorseWeek(before, after, fa ? lp.current : [], locked, kickoff, better);
    };
    return function (add, drop, inner) {
      if (!weekMatters) return true;
      var move = [{ add: add, drop: drop }], prior = claims.concat(inner || []);
      if (!noWorse(weekRoster(prior), weekRoster(prior.concat(move)), fills)) return false;
      // And on its own: the moves before it, and claims pending on Sleeper, may not go through.
      return noWorse(mine, withMoves(mine, move), false);
    };
  };
  var upgrade = function (cands, max, mustFill) {
    if (max <= 0 || !cands.length) return [];
    var roster = rosterNow();
    var made = planUpgrades_({
      freeAgents: cands, myPlayers: roster, countFrom: roster, value: value, dropValue: dropValue,
      position: function (p) { return self.pos(p); }, protected: core, minimums: self.minimums(),
      maxDepth: self.maxDepth(), healthy: healthy, extraGain: function (p) { return recent[p] ? cfg.min_gain : 0; },
      rosterLimit: limit, maxClaims: max, minGain: minGain, openSpotGain: guard ? minGain : 0,
      blockedDrops: Object.assign({}, blocked, usedDrops, roster.reduce(function (m, p) {
        if (mine.indexOf(p) < 0) m[p] = true;
        return m;
      }, {})),
      allow: noNewHoles(mustFill),
    });
    made.forEach(function (c) { claims.push(c); adding[c.add] = true; if (c.drop) usedDrops[c.drop] = true; });
    return made;
  };
  var label = function (p) {
    var pos = self.pos(p);
    return name(p) + (pos === 'K' || pos === 'DEF' ? ' (' + pos + kdNum(p) + ' rest of season)' : '');
  };
  var fill = function (hole) {
    var best = null, bestRank = Infinity;
    SLOT_ELIGIBILITY[hole.slot].forEach(function (pos) {
      self.weeklyList(pos).byId.forEach(function (r, pid) {
        if (self.eligible(pid, hole.slot) && !self.whyOut(pid, kickoff) && available(pid) && r.rank < bestRank) {
          best = pid; bestRank = r.rank;
        }
      });
    });
    var kd = hole.slot === 'K' || hole.slot === 'DEF';
    var star = hole.out !== EMPTY && kd && (keep[hole.out] || kdNum(hole.out) <= 12);
    var who = hole.out === EMPTY ? 'Your ' + hole.slot + ' spot is empty this week'
      : name(hole.out) + ' (' + self.pos(hole.out) + ', ' + self.whyOut(hole.out, kickoff) +
        (kd ? ', ' + self.pos(hole.out) + kdNum(hole.out) + ' rest of season' : '') + ") can't play this week" +
        (star ? ' and is too good to drop' : '');
    var drop = openSpots() > 0 ? null : dropFor(hole);
    if (best && drop && !noNewHoles(false)(best, drop)) drop = null;  // he'd be needed if an earlier move fails
    if (!best || (openSpots() <= 0 && !drop)) {
      notes.push(who + (star ? ', but ' : ' and nobody on your bench can fill in, but ') +
                 (best ? 'no bench player is cheap enough to give up' : 'no free agent is available') +
                 (fa ? '. Add one yourself if you can.' : ' right now. The free-agent plan tries again once waivers have run.'));
      return;
    }
    claims.push({ add: best, drop: drop, addValue: bestRank, dropValue: drop ? dropValue(drop) : null, kind: 'cover' });
    adding[best] = true;
    if (drop) usedDrops[drop] = true;
    notes.push(who + (star ? ', so this ' : ' and nobody on your bench can fill in, so this ') +
               (fa ? 'picks up ' : 'adds ') + name(best) + (fa ? ' as a free agent' : ' for the week') +
               (drop ? ' and drops ' + name(drop) + (kd && self.pos(drop) === hole.slot ? '.' : ', who is easy to replace.') : '.'));
  };
  var fas = [];
  ros.byId.forEach(function (r, pid) { if (relevant[self.pos(pid)] && (self.p(pid) || [])[2] && available(pid)) fas.push(pid); });
  var wanted = function (hole) { return (hole.slot === 'K' || hole.slot === 'DEF') ? cfg.stream_k_def : cfg.cover_byes; };
  // 1. An upgrade that also fills an empty starting spot does both jobs.
  holesOf(weekRoster()).forEach(function (hole) {
    if (!wanted(hole) || hole.slot === 'K' || hole.slot === 'DEF') return;
    var fits = fas.filter(function (p) {
      return !adding[p] && self.eligible(p, hole.slot) && !self.whyOut(p, kickoff);
    });
    var made = upgrade(fits, Math.min(1, room), true);
    room -= made.length;
    made.forEach(function (c) { notes.push(name(c.add) + ' is an upgrade and also fills the ' + hole.slot + ' spot this week.'); });
  });
  // 2. Fill-ins for the spots still empty: they get first pick of the cheap bench players.
  holesOf(weekRoster()).forEach(function (hole) { if (wanted(hole)) fill(hole); });
  // 3. Rest-of-season upgrades with whatever room is left.
  room -= upgrade(fas.filter(function (p) { return !adding[p]; }), room, false).length;
  // 4. Kicker/defense swaps for a clearly better matchup this week.
  if (cfg.stream_k_def && (fa || !faOpen)) {
    [['K', FP.K], ['DEF', FP.DST]].forEach(function (pair) {
      var pos = pair[0];
      if (self.slots.indexOf(pos) < 0) return;
      var wl = ctx.ranks(pair[1]);
      var first = wl.firstKickoff();
      if (!fa && (!first || first <= ctx.now)) {
        notes.push(pos + " streaming waits for next week's rankings.");
        return;
      }
      var at = function (p) { return self.pos(p) === pos; };
      if (Object.keys(pendingAdds).some(at) || Object.keys(adding).some(at)) return;  // already streaming
      var mineAt = weekRoster().filter(at);
      if (fa && mineAt.some(function (p) { return locked[p]; })) return;            // his game already started
      var wv = function (pid) { var r = wl.get(pid); return !r || r.bye || self.whyOut(pid, kickoff) ? null : r.rank; };
      var playing = mineAt.filter(function (p) { return wv(p) !== null; });
      if (!playing.length || guard) return;  // nobody plays: a hole (handled above); top waiver priority: not for this
      var myBest = Math.min.apply(null, playing.map(wv));
      var best = null;
      wl.byId.forEach(function (r, pid) { if (available(pid) && wv(pid) !== null && (!best || r.rank < wv(best))) best = pid; });
      if (!best || myBest - wv(best) < cfg.stream_margin) return;
      var keepers = mineAt.filter(function (p) {
        return !droppable(p) || (kdNum(p) <= 12 && kdNum(best) >= kdNum(p));  // a top-12 one stays unless the streamer is better for good
      });
      var drop = mineAt.filter(function (p) { return keepers.indexOf(p) < 0; })
        .sort(function (a, b) { return (wv(b) === null ? 1e9 : wv(b)) - (wv(a) === null ? 1e9 : wv(a)); })[0] || null;
      if (drop && !noNewHoles(false)(best, drop)) return;
      if (!drop && openSpots() <= 0) {
        keepers.forEach(function (p) {
          if (kdNum(p) <= 12) notes.push('Keeping ' + label(p) + ' rather than dropping him for a one-week ' + pos + ' stream.');
        });
        return;
      }
      claims.push({ add: best, drop: drop, addValue: wv(best), dropValue: drop ? dropValue(drop) : null, kind: 'stream' });
      adding[best] = true;
      if (drop) usedDrops[drop] = true;
    });
  }
  if (this.faab && !fa) {
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
    freeAgents: fa,
    pending: pending.length,
    pendingUnknown: pendingUnknown,
    faab: this.faab,
    priority: prio ? { position: prio, teams: teams, rolling: this.rolling } : null,
    basis: (this.qbPremium ? 'rest-of-season ECR, superflex-adjusted' : 'rest-of-season ECR') +
      (this.passTd6 ? ', QBs boosted for 6-pt passing TDs' : ''),
    notes: notes,
    claims: claims.map(function (c) {
      var vw = function (pid, value) {
        if (c.kind === 'upgrade') {
          var pos = self.pos(pid);  // a spare K/DEF: show his real rest-of-season rank
          var kd = pos === 'K' || pos === 'DEF' ? ctx.ranks(pos === 'K' ? FP.ROS_K : FP.ROS_DST).get(pid) : null;
          return self.view(pid, kd || value);
        }
        var r = self.weeklyRank(pid), wl = self.weeklyList(self.pos(pid));
        return self.view(pid, r || value, { why: !(self.team(pid) in wl.teamKickoff) || (r && r.bye) ? 'bye' : null });
      };
      return { kind: c.kind, bid: c.bid === undefined ? null : c.bid,
               add: vw(c.add, c.addValue), drop: c.drop ? vw(c.drop, c.dropValue) : null };
    }),
  };
};

/**
 * Plain rules every plan must pass, checked separately from how the plan was made: a
 * violation means a bug in the planner. Nothing is then done automatically (or by the
 * buttons) for that league, and the page shows the problem. Returns the problems found.
 */
function checkPlans_(lg, res) {
  var out = [];
  if (!lg.roster || res.status !== 'in_season') return out;
  var ctx = lg.ctx, cfg = lg.cfg;
  var name = function (p) { return (lg.p(p) || ['player ' + p])[0]; };
  var shown = [];
  var kickoff = lg.weekKickoffs();
  var locked = function (p) {
    var r = lg.weeklyRank(p), ko = lg.kickoffOf(p, kickoff);
    return !!(r && r.started) || !!(ko && ko <= ctx.now);
  };
  // Lineup: valid, no locked player moved, nobody out while a healthy bench player could play.
  var L = res.lineup;
  if (L && L.starters) {
    var seen = {};
    L.starters.forEach(function (p, i) {
      var slot = lg.slots[i];
      if (p === EMPTY) return;
      if (seen[p]) out.push(name(p) + ' is in the lineup twice.');
      seen[p] = true;
      var stays = L.current && L.current[i] === p && locked(p);  // already there and his game started
      if (SLOT_ELIGIBILITY[slot] && lg.p(p) && !lg.eligible(p, slot) && !stays) out.push(name(p) + " can't play " + slot + '.');
      if (L.current && L.current[i] !== p) {
        if (L.current[i] !== EMPTY && locked(L.current[i])) out.push(name(L.current[i]) + "'s game has started, but he'd be moved.");
        if (locked(p) && L.current.indexOf(p) !== i) out.push(name(p) + "'s game has started, but he'd be moved in.");
      }
    });
    var free = (L.bench || []).filter(function (b) { return b.tracked && !b.why && !b.locked; });
    (L.lineup || []).forEach(function (v) {
      if (!v.why || v.locked || !SLOT_ELIGIBILITY[v.slot]) return;
      var alt = free.filter(function (b) { return lg.eligible(b.id, v.slot); })[0];
      if (alt) out.push(v.name + ' (' + v.why + ') would start at ' + v.slot + ' while ' + alt.name + ' sits.');
    });
    shown = shown.concat(L.lineup || [], L.bench || []);
  }
  // Moves: free-agent pickups happen first, then the waiver claims.
  var F = res.freeAgents && !res.freeAgents.error && !res.freeAgents.waiting ? res.freeAgents : null;
  var W = res.waivers && !res.waivers.error ? res.waivers : null;
  if (F || W) {
    var rostered = {}, mine = {}, keep = lg.neverDrop(), recent = lg.recent_();
    lg.rosters.forEach(function (r) {
      (r.players || []).concat(r.reserve || [], r.taxi || []).forEach(function (p) { rostered[p] = true; });
    });
    lg.activePlayers().forEach(function (p) { mine[p] = true; });
    var faOpen = Number(lg.settings.leg) === Number(ctx.state.week), clears = null;
    try { clears = faOpen ? lg.clears_() : null; } catch (e) { if (e.expired) throw e; }
    var pending = [];
    try { pending = lg.pending_(); } catch (e) { if (e.expired) throw e; }
    var size = Object.keys(mine).length, added = {}, dropped = {}, upgrades = 0, pendingSkill = 0;
    pending.forEach(function (t) {
      size += Object.keys(t.adds || {}).length - Object.keys(t.drops || {}).filter(function (p) { return mine[p]; }).length;
    });
    var before = size;  // after the claims already pending: the plan mustn't make it worse
    pending.forEach(function (t) {
      Object.keys(t.adds || {}).forEach(function (p) { if (SKILL.indexOf(lg.pos(p)) >= 0) pendingSkill++; });
      Object.keys(t.drops || {}).forEach(function (p) { dropped[p] = true; });
    });
    [[F, 'pickup'], [W, 'claim']].forEach(function (pair) {
      var plan = pair[0], how = pair[1];
      if (!plan) return;
      plan.claims.forEach(function (c) {
        var a = c.add.id, d = c.drop && c.drop.id;
        shown.push(c.add);
        if (rostered[a]) out.push(name(a) + ' is already on a roster.');
        if (added[a]) out.push(name(a) + ' would be added twice.');
        added[a] = true;
        size++;
        if (c.kind === 'upgrade') upgrades++;
        if (c.kind !== 'upgrade' && lg.whyOut(a, kickoff)) out.push(name(a) + " can't play this week but is picked up for it.");
        if (clears && how === 'pickup' && !lg.isFreeAgent(a, clears, kickoff)) out.push(name(a) + " isn't a free agent right now.");
        if (clears && how === 'claim' && lg.isFreeAgent(a, clears, kickoff)) {
          out.push(name(a) + ' is a free agent right now: he should be picked up, not claimed for next week.');
        }
        if (!clears && faOpen) out.push("Can't check on Sleeper whether " + name(a) + ' is still on waivers.');
        if (!d) return;
        shown.push(c.drop);
        size--;
        if (!mine[d]) out.push(name(d) + " isn't on your roster.");
        if (dropped[d]) out.push(name(d) + ' would be dropped twice.');
        dropped[d] = true;
        if (keep[d]) out.push(name(d) + ' is starred (kept) but would be dropped.');
        if (how === 'pickup' && locked(d)) out.push(name(d) + "'s game has started, so he can't be dropped now.");
        var kd = lg.pos(d) === 'K' || lg.pos(d) === 'DEF';
        if (c.kind !== 'upgrade' && recent[d] && !kd) out.push(name(d) + ' was just picked up and would be dropped for a one-week pickup.');
        if (c.kind === 'upgrade' && !kd && c.add.rank && c.drop.rank) {
          var need = cfg.min_gain * (recent[d] ? 2 : 1);
          if (c.drop.rank - c.add.rank < need) {
            out.push(name(a) + ' for ' + name(d) + ' gains ' + (c.drop.rank - c.add.rank) + ' spots, less than ' + need +
                     (recent[d] ? ' (he was just picked up).' : '.'));
          }
        }
      });
    });
    var limit = (lg.data.roster_positions || []).filter(function (s) { return s !== 'IR' && s !== 'TAXI'; }).length;
    if (size > Math.max(limit, before)) {
      out.push('After these moves your roster would have ' + size + ' players; the limit is ' + limit + '.');
    }
    // The weekly limit: claims already pending and this week's upgrades leave this much room.
    var room = Math.max(0, cfg.max_claims - pendingSkill - upgradesDone_(lg.id, Number(lg.settings.leg)));
    if (upgrades > room) out.push('More upgrades than your limit of ' + cfg.max_claims + ' a week.');
    // No move may leave a starting spot this week with nobody who can play in it. Free agents
    // join now; claims made before the waiver run join before this week's games.
    var weekList = lg.weeklyList(lg.qbPremium ? 'QB' : 'RB'), first = weekList.firstKickoff();
    var moves = F ? F.claims : W && !faOpen && weekList.week === Number(ctx.state.week) && first > ctx.now ? W.claims : [];
    if (moves.length) {
      // Players whose game has started stay where they are: in the lineup or on the bench.
      var lockedNow = {}, startersNow = (L && L.current) || (lg.roster.starters || []).slice();
      Object.keys(mine).forEach(function (p) { if (locked(p)) lockedNow[p] = true; });
      var noWorse = function (before, after) { return lg.noWorseWeek(before, after, startersNow, lockedNow, kickoff, false); };
      var week0 = Object.keys(mine), week = week0;
      if (!F) {  // before the waiver run, pending claims go through with the plan's
        pending.forEach(function (t) {
          week = week.filter(function (p) { return !(t.drops || {})[p]; }).concat(Object.keys(t.adds || {}));
        });
      }
      var apply = function (roster, c) {
        return roster.filter(function (p) { return !c.drop || p !== c.drop.id; }).concat([c.add.id]);
      };
      // Each move after the ones before it, and on its own (they and pending claims can fail).
      var sofar = week, opens = false;
      moves.forEach(function (c) {
        var next = apply(sofar, c);
        if (!noWorse(sofar, next) || !noWorse(week0, apply(week0, c))) opens = true;
        sofar = next;
      });
      if (opens) out.push('These moves would leave a starting spot this week with nobody who can play.');
    }
  }
  shown.forEach(function (v) {
    if (v.rank >= UNRANKED) out.push(v.name + ' shows an internal value (' + v.rank + ') as his rank.');
  });
  return out;
}

League_.prototype.neverDrop = function () {
  var self = this, wanted = {}, names = {};
  (this.cfg.never_drop || []).forEach(function (x) {
    wanted[String(x)] = true;
    if (normName_(x)) names[normName_(x)] = true;  // an id like "4034" has no name part
  });
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
    setStarters_(this.ctx.token, this.id, this.roster.roster_id, l.starters, l.week, this.settings.leg);
    l.applied = true;
    log_({ level: 'change', league: this.name, title: 'Lineup updated (' + who + ')', lines: lineupLines_(l) });
  } catch (e) {
    if (e.expired) throw e;
    l.applyError = String(e.message || e);
    log_({ level: 'error', league: this.name, title: 'Lineup update failed', lines: [l.applyError] });
  }
};

League_.prototype.applyFreeAgents = function (res, who) {
  var f = res.freeAgents, self = this;
  if (!f || f.error || f.waiting || !f.claims.length) return;
  if (f.pendingUnknown) {
    f.submitError = PENDING_UNKNOWN_MSG;
    return;
  }
  var lines = [];
  f.claims.forEach(function (c) {
    try {
      addFreeAgent_(self.ctx.token, self.id, self.roster.roster_id, c.add.id, c.drop && c.drop.id);
      c.submitted = true;
      if (c.kind === 'upgrade') countUpgrade_(self.id, Number(self.settings.leg));
      lines.push('Added ' + c.add.name + (c.drop ? ', dropped ' + c.drop.name : ''));
    } catch (e) {
      if (e.expired) throw e;
      c.error = String(e.message || e);
      lines.push('FAILED ' + c.add.name + ': ' + c.error);
    }
  });
  log_({ level: f.claims.some(function (c) { return c.error; }) ? 'error' : 'change', league: this.name,
         title: 'Free agents picked up (' + who + ')', lines: lines });
};

League_.prototype.applyClaims = function (res, who) {
  var w = res.waivers, self = this;
  if (!w || w.error || !w.claims.length) return;
  if (w.pendingUnknown) {
    w.submitError = PENDING_UNKNOWN_MSG;
    return;
  }
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
