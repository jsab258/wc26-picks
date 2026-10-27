// Run: node --test fantasy/apps-script/test/
// Offline tests of Code.gs on the Apps Script stubs (network functions are replaced).
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadGas } = require('../dev/gas-stub');

// Values created inside the sandbox have their own Array prototype; compare plain copies.
const plain = (x) => JSON.parse(JSON.stringify(x));

const POS = { qb1: 'QB', qb2: 'QB', qb3: 'QB', rb1: 'RB', rb2: 'RB', rb3: 'RB', wr1: 'WR', wr2: 'WR', wr3: 'WR',
              te1: 'TE', te2: 'TE', k1: 'K', d1: 'DEF' };
const RANKS = { qb1: 6, qb2: 30, qb3: 90, rb1: 2, rb2: 15, rb3: 45, wr1: 3, wr2: 12, wr3: 40, te1: 28, te2: 120, k1: 1, d1: 1 };
const SLOTS = ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'SUPER_FLEX', 'K', 'DEF'];

function ranked(gas, ranks, bonus = 0) {
  return (pid, slot) => {
    if (!gas.SLOT_ELIGIBILITY[slot].includes(POS[pid])) return null;
    return slot === 'SUPER_FLEX' && POS[pid] === 'QB' ? ranks[pid] - bonus : ranks[pid];
  };
}

test('optimizer: superflex starts the 2nd QB; QB lean tips close calls', () => {
  const gas = loadGas();
  const roster = Object.keys(POS);
  let r = gas.optimize_(SLOTS, [], roster, ranked(gas, RANKS));
  assert.equal(r.starters[SLOTS.indexOf('SUPER_FLEX')], 'qb2');
  assert.equal(r.starters[SLOTS.indexOf('FLEX')], 'wr3');
  const close = { ...RANKS, qb2: 50 };
  r = gas.optimize_(SLOTS, [], roster, ranked(gas, close));
  assert.equal(r.starters[SLOTS.indexOf('SUPER_FLEX')], 'rb3');
  r = gas.optimize_(SLOTS, [], roster, ranked(gas, close, 10));
  assert.equal(r.starters[SLOTS.indexOf('SUPER_FLEX')], 'qb2');
});

test('optimizer: locked players stay, order-only differences are not changes', () => {
  const gas = loadGas();
  const roster = Object.keys(POS);
  const current = ['qb1', 'rb1', 'rb3', 'wr1', 'wr2', 'te1', 'wr3', 'qb2', 'k1', 'd1'];
  const r = gas.optimize_(SLOTS, current, roster, ranked(gas, RANKS), { rb3: true, wr3: true });
  assert.deepEqual(Array.from(r.starters), [...current.slice(0, 7), 'rb2', 'k1', 'd1']);
  const benchLocked = gas.optimize_(SLOTS, current, roster, ranked(gas, RANKS), { rb2: true });
  assert.ok(!benchLocked.starters.includes('rb2'));
  const swapped = ['qb1', 'rb2', 'rb1', 'wr2', 'wr1', 'te1', 'wr3', 'qb2', 'k1', 'd1'];
  assert.equal(gas.optimize_(SLOTS, swapped, roster, ranked(gas, RANKS)).changes.length, 0);
  const idp = gas.optimize_(['QB', 'RB', 'DL'], ['0', 'rb2', 'idp9'], ['qb1', 'rb1', 'rb2', 'idp9'],
                            (p, s) => (p === 'idp9' ? null : ranked(gas, RANKS)(p, s)));
  assert.deepEqual(Array.from(idp.starters), ['qb1', 'rb1', 'idp9']);
});

test('waivers: upgrades, minimums, open spots, streaming, FAAB', () => {
  const gas = loadGas();
  const pos = { fa_rb: 'RB', fa_wr: 'WR', my_rb: 'RB', my_wr: 'WR', my_qb: 'QB', my_qb2: 'QB' };
  const plan = (values, mine, fas, extra = {}) => gas.planUpgrades_(Object.assign({
    freeAgents: fas, myPlayers: mine, value: (p) => values[p] ?? null, dropValue: (p) => values[p] ?? null,
    position: (p) => pos[p], protected: {}, minimums: {}, rosterLimit: mine.length, maxClaims: 5, minGain: 10,
    blockedDrops: {} }, extra)).map((c) => [c.add, c.drop]);
  const eq = (a, b) => assert.deepEqual(plain(a), b);
  eq(plan({ fa_rb: 80, my_rb: 150, my_wr: 120 }, ['my_rb', 'my_wr'], ['fa_rb']), [['fa_rb', 'my_rb']]);
  eq(plan({ fa_rb: 145, my_rb: 150 }, ['my_rb'], ['fa_rb']), []);
  eq(plan({ fa_wr: 50, my_qb: 200, my_qb2: 210, my_rb: 100 }, ['my_qb', 'my_qb2', 'my_rb'], ['fa_wr'],
          { minimums: { QB: 2 } }), [['fa_wr', 'my_rb']]);
  eq(plan({ fa_rb: 140, my_rb: 150 }, ['my_rb'], ['fa_rb'], { rosterLimit: 2 }), [['fa_rb', null]]);
  const s = gas.planStream_(['fa_k'], ['my_k'], (p) => ({ fa_k: 4, my_k: null }[p]), 6, false);
  assert.deepEqual([s.add, s.drop], ['fa_k', 'my_k']);
  assert.equal(gas.planStream_(['fa_k'], ['my_k'], (p) => ({ fa_k: 4, my_k: 8 }[p]), 6, false), null);
  const tiers = [[30, 0.25], [60, 0.15], [100, 0.08], [150, 0.04]];
  assert.equal(gas.faabBid_(20, 100, tiers, 0), 25);
  assert.equal(gas.faabBid_(400, 100, tiers, 1), 1);
  assert.equal(gas.faabBid_(20, 0, tiers, 1), null);
});

test('parsing: ecrData blob and slim player db', () => {
  const gas = loadGas();
  const html = 'x<script>var ecrData = {"week":"7","players":[{"note":"a {tricky} \\"}\\" str"}]};\nvar y={};</script>';
  assert.equal(gas.parseEcr_(html).players[0].note, 'a {tricky} "}" str');
  const db = { 9221: { full_name: 'Jahmyr Gibbs', position: 'RB', team: 'DET', injury_status: 'Questionable',
                       fantasy_positions: ['RB'], metadata: { x: '{' } },
               1: { full_name: 'Some Lineman', position: 'OL', team: 'DET' },
               DET: { first_name: 'Detroit', last_name: 'Lions', position: 'DEF', team: 'DET', fantasy_positions: ['DEF'] },
               77: { full_name: 'Taysom Hill', position: 'TE', team: 'NO', fantasy_positions: ['QB', 'TE'] } };
  gas.fetch_ = () => ({ code: 200, text: JSON.stringify(db) });
  const slim = gas.playersSlim_(0);
  assert.deepEqual(Object.keys(slim).sort(), ['77', '9221', 'DET']);
  assert.deepEqual(Array.from(slim['9221']), ['Jahmyr Gibbs', 'RB', 'DET', 'Questionable', null]);
  assert.deepEqual(Array.from(slim['77'][4]), ['QB', 'TE']);
  assert.equal(slim.DET[0], 'Detroit Lions');
});

test('storage: JSON larger than one property value is chunked', () => {
  const gas = loadGas();
  const big = Array.from({ length: 400 }, (_, i) => ({ ts: i, title: 'Lineup updated '.repeat(4) + i }));
  gas.putJson_('log', big);
  assert.ok(Number(gas.__props.getProperty('log#n')) > 1);
  assert.equal(gas.getJson_('log', []).length, 400);
  gas.putJson_('log', [1]);
  assert.equal(gas.__props.getProperty('log#1'), null);  // stale chunks removed
});

test('waiver window: evening before Sleeper waiver day (Wed), once', () => {
  const gas = loadGas();
  const lg = { settings: { waiver_day_of_week: 2 } };
  const at = (iso) => gas.waiverWindow_(lg, Date.parse(iso) / 1000);
  assert.equal(at('2026-10-27T20:00:00Z'), '2026-10-27');
  assert.equal(at('2026-10-28T03:00:00Z'), '2026-10-27');
  assert.equal(at('2026-10-28T12:00:00Z'), null);
  assert.equal(at('2026-10-27T10:00:00Z'), null);
  assert.equal(gas.waiverWindow_({ settings: { daily_waivers: 1 } }, Date.parse('2026-10-27T20:00:00Z') / 1000), null);
});

test('login: password, emailed code, wrong password', () => {
  let step = 0;
  const gas = loadGas({
    gql(body) {
      if (body.query.includes('login(')) {
        if (body.variables.p === 'right') return { errors: [{ message: 'verify', code: 'code_verification_required' }] };
        if (body.variables.p === '1234') return { data: { login: { token: 'h.' + Buffer.from('{"user_id":"42"}').toString('base64url') + '.s' } } };
        return { data: { login: null } };
      }
      if (body.query.includes('create_verification_code')) { step++; return { data: { create_verification_code: true } }; }
      if (body.query.includes('login_context')) return { data: { login_context_by_email_or_phone_or_username: { user_id: '42', masked_email: 'j***@x.ch' } } };
      if (body.query.includes('league_transactions_filtered')) return { data: { league_transactions_filtered: [] } };
    },
  });
  gas.sleeper_ = (p) => (p === '/state/nfl' ? { league_season: '2026' } : p.startsWith('/user/42/leagues') ? [{ league_id: 'L' }]
                         : { user_id: '42', display_name: 'tester', avatar: null });
  assert.throws(() => gas.login('tester', 'nope'), /didn't accept/);
  const r = gas.login('tester', 'right');
  assert.deepEqual([r.needsCode, r.sentTo, step], [true, 'j***@x.ch', 1]);
  const st = gas.verifyCode('1234');
  assert.equal(st.connected, true);
  assert.equal(st.user.display_name, 'tester');
  assert.equal(gas.__triggers.length, 1);  // background checks scheduled on connect
});

// ---- whole league against fixtures ---------------------------------------
const PLAYERS = {
  qb_a: ['qb_a', 'QB', 'KC', null, null], qb_b: ['qb_b', 'QB', 'BUF', null, null], rb_c: ['rb_c', 'RB', 'DET', null, null],
  rb_d: ['rb_d', 'RB', 'NYJ', null, null], wr_e: ['wr_e', 'WR', 'MIA', null, null], wr_f: ['wr_f', 'WR', 'SEA', 'Out', null],
  te_g: ['te_g', 'TE', 'LV', null, null], k_1: ['k_1', 'K', 'KC', null, null], qb_fa: ['qb_fa', 'QB', 'TB', null, null],
  wr_fa: ['wr_fa', 'WR', 'CHI', null, null], k_fa: ['k_fa', 'K', 'MIN', null, null], DET: ['Detroit Lions', 'DEF', 'DET', null, null],
};
const NOW = Date.parse('2026-10-22T12:00:00Z'), KICK = NOW / 1000 + 6 * 3600;
const list = (week, rows) => ({ week, label: 't', players: rows.map(([id, rank, pr]) =>
  [id, id, id === 'DET' ? 'DST' : PLAYERS[id][1], PLAYERS[id][2], rank, pr, '14', 'vs. X', KICK, 'created']) });
const LISTS = {
  'ppr-superflex': list(7, [['qb_a', 5, 'QB1'], ['rb_c', 8, 'RB1'], ['wr_e', 10, 'WR1'], ['qb_fa', 20, 'QB2'], ['qb_b', 30, 'QB3'],
                            ['rb_d', 45, 'RB2'], ['te_g', 60, 'TE1'], ['wr_fa', 70, 'WR2'], ['wr_f', 80, 'WR3']]),
  k: list(7, [['k_fa', 1, 'K1'], ['k_1', 12, 'K2']]),
  dst: list(7, [['DET', 3, 'DST1']]),
  'ros-ppr-overall': list(0, [['rb_c', 5, 'RB1'], ['wr_e', 9, 'WR1'], ['rb_d', 60, 'RB2'], ['qb_a', 70, 'QB1'], ['te_g', 90, 'TE1'],
                              ['qb_fa', 100, 'QB2'], ['wr_fa', 150, 'WR2'], ['qb_b', 200, 'QB3'], ['wr_f', 300, 'WR3']]),
};
const LEAGUE = { league_id: 'L', name: 'Test', status: 'in_season',
  roster_positions: ['QB', 'RB', 'WR', 'TE', 'SUPER_FLEX', 'K', 'DEF', 'BN', 'BN'],
  scoring_settings: { rec: 1 }, settings: { waiver_type: 2, waiver_budget: 100, waiver_day_of_week: 2 } };
const ROSTER = { roster_id: 1, owner_id: 'me', settings: { waiver_budget_used: 0 },
  players: ['qb_a', 'qb_b', 'rb_c', 'rb_d', 'wr_e', 'wr_f', 'te_g', 'k_1', 'DET'],
  starters: ['qb_a', 'rb_c', 'wr_f', 'te_g', 'rb_d', 'k_1', 'DET'] };

function fixtureGas(nowMs) {
  const writes = [];
  const gas = loadGas({ now: () => nowMs });
  gas.fpList_ = (slug) => LISTS[slug];
  gas.playersSlim_ = () => PLAYERS;
  gas.fpToSleeper_ = () => Object.fromEntries(Object.keys(PLAYERS).map((k) => [k, k]));
  gas.sleeper_ = (p) => (p === '/state/nfl' ? { week: 7, league_season: '2026' }
    : p.includes('/leagues/') ? [LEAGUE] : p.endsWith('/rosters') ? [ROSTER, { roster_id: 2, owner_id: 'x', players: ['wr_x'] }] : null);
  gas.pendingWaivers_ = () => [];
  gas.setStarters_ = (...a) => writes.push(['starters', ...a.slice(1)]);
  gas.submitClaim_ = (...a) => writes.push(['claim', ...a.slice(1)]);
  gas.__props.setProperty('token', 'a.b.c');
  gas.putJson_('user', { user_id: 'me', display_name: 'me' });
  return { gas, writes };
}

test('dashboard plans a league without writing anything', () => {
  const { gas, writes } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
  const lg = gas.getDashboard().leagues[0];
  assert.deepEqual(Array.from(lg.lineup.starters), ['qb_a', 'rb_c', 'wr_e', 'te_g', 'qb_b', 'k_1', 'DET']);
  assert.deepEqual(plain(lg.lineup.benched.map((p) => [p.id, p.why])), [['wr_f', 'Out'], ['rb_d', null]]);
  assert.deepEqual(plain(lg.waivers.claims.map((c) => [c.add.id, c.drop && c.drop.id, c.bid])),
                   [['qb_fa', 'wr_f', 25], ['k_fa', 'k_1', 0]]);
  assert.deepEqual(Array.from(lg.flags).slice(0, 3), ['PPR', 'Superflex', 'FAAB']);
  assert.equal(writes.length, 0);
});

test('autopilot: off by default; on = lineup now, claims only in the waiver window, once', () => {
  let now = NOW;
  const { gas, writes } = fixtureGas(now);
  gas.tick();
  assert.equal(writes.length, 0);
  assert.equal(gas.getJson_('lastTick').status, 'idle');
  gas.setMode('auto');
  gas.saveLeagueSettings('L', { auto_waivers: true, min_roster: { WR: 1 } });
  gas.tick();
  assert.deepEqual(writes.map((w) => w[0]), ['starters']);
  assert.match(gas.getJson_('log')[0].title, /Lineup updated \(autopilot\)/);
});

test('autopilot: claims go in Tuesday evening exactly once', () => {
  const tue = Date.parse('2026-10-20T20:00:00Z');
  const { gas, writes } = fixtureGas(tue);
  gas.setMode('auto');
  gas.saveLeagueSettings('L', { auto_waivers: true, auto_lineup: false, min_roster: { WR: 1 } });
  gas.tick();
  gas.tick();
  assert.deepEqual(plain(writes.map((w) => [w[0], w[3], w[4], w[5]])),
                   [['claim', 'qb_fa', 'wr_f', 25], ['claim', 'k_fa', 'k_1', 0]]);
});

test('a 401 from Sleeper drops the saved session', () => {
  const gas = loadGas({ gql: () => ({ __status: 401, errors: [{ message: 'Your token is invalid.' }] }) });
  gas.__props.setProperty('token', 'a.b.c');
  assert.throws(() => gas.gql_('query x { y }', {}, 'a.b.c'), /session expired/);
  assert.equal(gas.getState().connected, false);
});

test('autopilot: expired Sleeper session is reported once, not every 30 minutes', () => {
  const { gas, writes } = fixtureGas(NOW);
  gas.setMode('auto');
  gas.setStarters_ = () => { throw gas.sessionExpired_(); };
  gas.tick();
  gas.tick();
  const titles = gas.getJson_('log').map((e) => e.title);
  assert.equal(titles.filter((t) => /session expired/.test(t)).length, 1);
  assert.ok(!titles.some((t) => /Lineup update failed/.test(t)));
  assert.equal(gas.getJson_('lastTick').status, 'error');
  assert.equal(gas.getState().connected, false);
  assert.equal(writes.length, 0);
});

test('single-file build is current and serves the dashboard by itself', () => {
  const { execFileSync } = require('child_process');
  const path = require('path');
  execFileSync('node', [path.join(__dirname, '..', 'dev', 'bundle.js'), '--check']);
  const dist = loadGas({ file: path.join(__dirname, '..', 'dist', 'SleeperAutopilot.gs') });
  assert.match(dist.doGet().getContent(), /<title>Sleeper Autopilot<\/title>/);
  assert.equal(typeof dist.tick, 'function');
});

test('login: captcha wall gets a clear message; pasted sessions accept JSON or a bare token', () => {
  const gas = loadGas({
    gql(body) {
      if (body.query.includes('login(')) return { errors: [{ message: "Sorry, we're unable to confirm you're human." }] };
      if (body.query.includes('league_transactions_filtered')) return { data: { league_transactions_filtered: [] } };
    },
  });
  const users = [];
  gas.sleeper_ = (p) => {
    if (p === '/state/nfl') return { league_season: '2026' };
    if (p.includes('/leagues/')) return [{ league_id: 'L' }];
    users.push(p);
    return { user_id: p.split('/')[2] === 'jsab258' ? '7' : p.split('/')[2], display_name: 'jsab258' };
  };
  assert.throws(() => gas.login('jsab258', 'pw'), /wants a captcha/);
  const st = gas.connectWithToken(JSON.stringify({ token: 'h.e.s', user_id: '7' }), null, null);
  assert.equal(st.connected, true);
  assert.equal(users[0], '/user/7');
  gas.logout();
  assert.equal(gas.connectWithToken('"h.e.s"', 'jsab258', null).connected, true);  // username fallback
  assert.equal(users[1], '/user/jsab258');
  assert.throws(() => gas.connectWithToken('not a token', null, null), /doesn't look like/);
  gas.logout();
  // Exactly what the sleeper.com console line copies: both values JSON-encoded in localStorage.
  const copied = JSON.stringify({ token: '"h.e.s"', user_id: '"1393509836200624128"' });
  assert.equal(gas.connectWithToken(copied, null, null).connected, true);
  assert.equal(users[users.length - 1], '/user/1393509836200624128');
});

// ---- self-update ----------------------------------------------------------
const fs = require('fs');
const os = require('os');
const path = require('path');
const DIST = path.join(__dirname, '..', 'dist', 'SleeperAutopilot.gs');
const distText = () => fs.readFileSync(DIST, 'utf8');

function remoteBuild(version, id) {
  // A "newer" build: the real dist with a new BUILD_INFO, a visible UI change and
  // an extra server function, so tests can tell which code is running.
  return distText()
    .replace(/\nvar BUILD_INFO = .*;\n/, '\nvar BUILD_INFO = ' + JSON.stringify({ id, version, title: 'v' + version,
      notes: [{ title: 'v' + version, items: ['newest'] }, { title: 'v' + (version - 1), items: ['older'] }] }) + ';\n')
    .replace('Sleeper Autopilot</div>\\n', 'Sleeper Autopilot v' + version + '</div>\\n')
    .replace(/\nloadInstalledUpdate_\(\);\n$/, "\nfunction whoAmI_() { return 'installed v" + version + "'; }\nloadInstalledUpdate_();\n");
}

function updaterGas(remote, opts = {}) {
  return loadGas(Object.assign({ file: DIST, fetch(url) {
    if (url.includes('raw.githubusercontent.com')) {
      return url.includes('/main/') ? { code: 404, body: '404' } : { code: 200, body: remote };
    }
  } }, opts));
}

test('update check: newer build on GitHub is offered with its release notes', () => {
  const cur = loadGas({ file: DIST }).buildInfo_();
  const r = plain(updaterGas(remoteBuild(cur.version + 1, 'newer')).checkForUpdate());
  assert.equal(r.available, true);
  assert.deepEqual(r.notes.map((n) => n.title), ['v' + (cur.version + 1)]);
  assert.equal(updaterGas(distText()).checkForUpdate().available, false);
});

test('install: stored update takes over from the next run (server code and page), and can update again', () => {
  const v = loadGas({ file: DIST }).buildInfo_().version;
  const first = updaterGas(remoteBuild(v + 1, 'n1'));
  const r = first.installUpdate('n1');
  assert.equal(r.info.title, 'v' + (v + 1));
  assert.match(first.getJson_('log')[0].title, /Installed update "v/);
  assert.equal(typeof first.whoAmI_, 'undefined');       // this run keeps the old code

  const next = loadGas({ file: DIST, props: first.__props._data });  // a fresh execution, like Google's
  assert.equal(next.whoAmI_(), 'installed v' + (v + 1));
  assert.equal(next.buildInfo_().version, v + 1);
  assert.match(next.doGet().getContent(), /Sleeper Autopilot v\d+<\/div>/);
  const st = plain(next.call('getState', []));
  assert.deepEqual([st.update.installed, st.update.error], [true, null]);

  // Installing again from the installed code still stacks on the same paste.
  const again = updaterGas(remoteBuild(v + 2, 'n2'), { props: next.__props._data });
  again.installUpdate('n2');
  const third = loadGas({ file: DIST, props: again.__props._data });
  assert.equal(third.whoAmI_(), 'installed v' + (v + 2));
});

test('install: a different build pasted by hand always wins over a stored update', () => {
  const v = loadGas({ file: DIST }).buildInfo_().version;
  const gas = updaterGas(remoteBuild(v + 1, 'n1'));
  gas.installUpdate();
  const pasted = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'sa-')), 'pasted.gs');
  fs.writeFileSync(pasted, distText().replace(/"id":"[0-9a-f]+"/, '"id":"hand-pasted"'));
  const run = loadGas({ file: pasted, props: gas.__props._data });
  assert.equal(typeof run.whoAmI_, 'undefined');
  assert.equal(run.buildInfo_().id, 'hand-pasted');
  assert.equal(run.getState().update.installed, false);
});

test('install: damaged stored update falls back to the pasted code and can be removed', () => {
  const base = loadGas({ file: DIST });
  base.putJson_('engine', { base: base.buildInfo_().id, info: { title: 'bad' }, code: 'function broken( {' });
  const run = loadGas({ file: DIST, props: base.__props._data });
  const st = plain(run.getState());
  assert.equal(st.update.installed, false);
  assert.ok(st.update.error);
  assert.equal(run.buildInfo_().id, base.buildInfo_().id);
  run.removeUpdate();
  assert.equal(loadGas({ file: DIST, props: run.__props._data }).getState().update.error, null);
});

test('install: refuses incomplete downloads; dispatcher only runs listed actions', () => {
  assert.throws(() => updaterGas('garbage').installUpdate(), /incomplete/);
  const truncated = remoteBuild(99, 'x').replace(/\nloadInstalledUpdate_\(\);\n$/, '\n');
  assert.throws(() => updaterGas(truncated).installUpdate(), /incomplete/);
  const gas = loadGas({ file: DIST });
  assert.throws(() => gas.call('fetch_', ['https://example.com']), /Unknown action/);
  assert.throws(() => gas.call('eval', ['1']), /Unknown action/);
  assert.equal(gas.call('getState', []).connected, false);
});

test('granular consent: an unticked core permission shows up with an Approve link', () => {
  assert.equal(loadGas().getState().permissions, null);
  const core = loadGas({ deniedScopes: ['https://www.googleapis.com/auth/script.scriptapp'] });
  const p = plain(core.getState().permissions);
  assert.deepEqual(p.scopes, ['https://www.googleapis.com/auth/script.scriptapp']);
  assert.match(p.url, /approve/);
});

test('page source has no "://": Google cuts text after // inside the page\'s template strings', () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'Index.html'), 'utf8');
  const bad = html.split('\n').map((l, i) => [i + 1, l]).filter(([, l]) => l.includes('://'));
  assert.deepEqual(bad, [], 'write URLs as https:\\/\\/... in a quoted constant');
});
