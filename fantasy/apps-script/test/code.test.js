// Run: node --test fantasy/apps-script/test/*.test.js
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
  'ros-k': list(0, [['k_fa', 20, 'K20'], ['k_1', 15, 'K15']]),
  'ros-dst': list(0, [['DET', 3, 'DST3']]),
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
  gas.latestBuild_ = () => null;   // no GitHub from the fixtures
  gas.waiverClears_ = () => ({});
  gas.addFreeAgent_ = (...a) => writes.push(['fa', ...a.slice(3)]);
  gas.setStarters_ = (...a) => writes.push(['starters', ...a.slice(1)]);
  gas.submitClaim_ = (...a) => writes.push(['claim', ...a.slice(1)]);
  gas.__props.setProperty('token', 'a.b.c');
  gas.putJson_('user', { user_id: 'me', display_name: 'me' });
  // Every plan any test looks at must pass the safety rules.
  const dashboard = gas.getDashboard;
  gas.getDashboard = () => {
    const d = dashboard();
    d.leagues.forEach((lg) => assert.deepEqual(plain(lg.safety || []), [], 'safety check failed for ' + lg.name));
    return d;
  };
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

test('waivers: injured players do not fill minimums; a QB past useful depth must replace a QB', () => {
  const gas = loadGas();
  const pos = { fa_rb: 'RB', fa_qb: 'QB', my_wr: 'WR', my_wr_out: 'WR', q1: 'QB', q2: 'QB', q3: 'QB' };
  const plan = (values, mine, fas, extra) => plain(gas.planUpgrades_(Object.assign({
    freeAgents: fas, myPlayers: mine, value: (p) => values[p] ?? null, dropValue: (p) => values[p] ?? null,
    position: (p) => pos[p], protected: {}, minimums: {}, rosterLimit: mine.length, maxClaims: 5, minGain: 10,
    blockedDrops: {} }, extra)).map((c) => [c.add, c.drop]));
  assert.deepEqual(plan({ fa_rb: 50, my_wr: 200, my_wr_out: 150 }, ['my_wr', 'my_wr_out'], ['fa_rb'],
    { minimums: { WR: 1 }, healthy: (p) => p !== 'my_wr_out' }), [['fa_rb', 'my_wr_out']]);
  const qbs = { fa_qb: 65, q1: 10, q2: 20, q3: 70, my_wr: 300 };
  assert.deepEqual(plan(qbs, ['q1', 'q2', 'q3', 'my_wr'], ['fa_qb'], { maxDepth: { QB: 3 } }), []);
  assert.deepEqual(plan(Object.assign({}, qbs, { fa_qb: 40 }), ['q1', 'q2', 'q3', 'my_wr'], ['fa_qb'],
    { maxDepth: { QB: 3 } }), [['fa_qb', 'q3']]);
});

test('waivers: keeps a top-12 kicker instead of dropping him for a one-week stream', () => {
  LISTS['ros-k'].players[1][5] = 'K2';  // k_1 becomes an elite kicker
  try {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
    const w = gas.getDashboard().leagues[0].waivers;
    assert.ok(!w.claims.some((c) => c.add.id === 'k_fa'));
    assert.match(w.notes.join(' '), /Keeping k_1 \(K2 rest of season\)/);
  } finally {
    LISTS['ros-k'].players[1][5] = 'K15';
  }
});

test('lineup save: writes the week\'s leg, the roster only when the league is on that week, and verifies', () => {
  const sent = [];
  let echo = true;
  const gas = loadGas({ gql(body) {
    const name = body.query.split('(')[0].split(' ').pop();
    sent.push([name, body.variables.round, body.variables.leg]);
    const starters = echo ? body.variables.starters : ['old'];
    return name === 'update_matchup_leg' ? { data: { update_matchup_leg: { leg: 8, round: 8, starters } } }
                                         : { data: { roster_update_starters: { roster_id: 1, starters } } };
  } });
  gas.setStarters_('t', 'L', 1, ['a', 'b'], 8, 7);   // Tuesday: league still on week 7
  assert.deepEqual(sent, [['update_matchup_leg', 8, 8]]);
  sent.length = 0;
  gas.setStarters_('t', 'L', 1, ['a', 'b'], 8, 8);   // game days: league on week 8
  assert.deepEqual(sent.map((x) => x[0]), ['update_matchup_leg', 'roster_update_starters']);
  echo = false;
  assert.throws(() => gas.setStarters_('t', 'L', 1, ['a', 'b'], 8, 7), /didn't accept the week 8 lineup/);
});

test('optimizer: no pointless swap between RB and flex', () => {
  const gas = loadGas();
  const r = gas.optimize_(['RB', 'FLEX'], ['rb2', 'rb1'], ['rb1', 'rb2', 'rb3'], ranked(gas, RANKS));
  assert.equal(r.changes.length, 0);
});

test('lineup plan compares against the week\'s matchup lineup, not the lagging roster lineup', () => {
  const { gas } = fixtureGas(NOW);
  const base = gas.sleeper_;
  // roster.starters was already updated (league still on last week), but week 7's matchup has the old lineup.
  const oldWeek = ['qb_a', 'rb_c', 'wr_f', 'te_g', 'rb_d', 'k_1', 'DET'];
  ROSTER.starters = ['qb_a', 'rb_c', 'wr_e', 'te_g', 'qb_b', 'k_1', 'DET'];
  gas.sleeper_ = (p, fresh) => (p.endsWith('/matchups/7') ? [{ roster_id: 1, starters: oldWeek }] : base(p, fresh));
  try {
    const l = gas.getDashboard().leagues[0].lineup;
    assert.equal(l.changes, 2);
    assert.deepEqual(plain(l.benched.map((p) => p.id)).sort(), ['rb_d', 'wr_f']);
  } finally {
    ROSTER.starters = oldWeek;
  }
});

test('waivers: claims already pending on Sleeper count toward the weekly limit', () => {
  const { gas } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
  gas.pendingWaivers_ = () => [{ roster_ids: [1], adds: { wr_fa: 1 }, drops: {} },
                               { roster_ids: [1], adds: { qb_fa: 1 }, drops: {} }];
  const w = gas.getDashboard().leagues[0].waivers;
  assert.ok(!w.claims.some((c) => c.kind === 'upgrade'));
  assert.match(w.notes.join(' '), /limit of 2 upgrades a week is used up/);
});

test('waivers: top kicker on bye gets a one-week replacement by dropping a spare bench player', () => {
  const kRow = LISTS.k.players.find((r) => r[0] === 'k_1');
  const wrRow = LISTS['ros-ppr-overall'].players.find((r) => r[0] === 'wr_f');
  LISTS['ros-k'].players[1][5] = 'K2';   // k_1 is an elite kicker...
  kRow[6] = '7';                          // ...on bye this week
  wrRow[5] = 'WR40';                      // and the injured wr_f is easy to replace
  try {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { min_roster: { WR: 1 }, max_claims: 0 });
    let w = gas.getDashboard().leagues[0].waivers;
    const k = w.claims.find((c) => c.add.id === 'k_fa');
    assert.deepEqual([k.kind, k.drop && k.drop.id], ['cover', 'wr_f']);  // injured, easy-to-replace WR goes
    assert.match(w.notes.join(' '), /can't play this week and is too good to drop/);
    gas.saveLeagueSettings('L', { max_claims: 2 });  // the fill-in gets first pick of the spare players
    w = gas.getDashboard().leagues[0].waivers;
    assert.equal(w.claims.find((c) => c.add.id === 'k_fa').drop.id, 'wr_f');
    assert.equal(w.claims.filter((c) => c.drop && c.drop.id === 'wr_f').length, 1);
    gas.saveLeagueSettings('L', { never_drop: ['wr_f'] });  // nobody else is cheap enough
    w = gas.getDashboard().leagues[0].waivers;
    assert.ok(!w.claims.some((c) => c.add.id === 'k_fa'));
    assert.match(w.notes.join(' '), /no bench player is cheap enough/);
  } finally {
    LISTS['ros-k'].players[1][5] = 'K15';
    kRow[6] = '14';
    wrRow[5] = 'WR3';
  }
});

test('waivers: a spare K outside the top 12 is dropped first, an elite or needed one is kept', () => {
  PLAYERS.k_x = ['k_x', 'K', 'NO', null, null];
  LISTS['ros-k'].players.push(['k_x', 'k_x', 'K', 'NO', 30, 'K30', '14', 'vs. X', KICK, 'created']);
  LISTS.k.players.push(['k_x', 'k_x', 'K', 'NO', 20, 'K20', '14', 'vs. X', KICK, 'created']);
  ROSTER.players.push('k_x');
  LEAGUE.roster_positions.push('BN');
  try {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { stream_k_def: false, min_roster: { WR: 1 } });
    let claims = gas.getDashboard().leagues[0].waivers.claims;
    assert.equal(claims[0].drop.id, 'k_x');               // spare K30 goes before anyone else
    LISTS['ros-k'].players[LISTS['ros-k'].players.length - 1][5] = 'K9';
    claims = loadGasFresh(gas).getDashboard().leagues[0].waivers.claims;
    assert.ok(!claims.some((c) => c.drop && c.drop.id === 'k_x'));   // two top-12 kickers: your call
  } finally {
    delete PLAYERS.k_x;
    LISTS['ros-k'].players.pop();
    LISTS.k.players.pop();
    ROSTER.players.pop();
    LEAGUE.roster_positions.pop();
  }
});

function loadGasFresh(prev) {
  const { gas } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { stream_k_def: false, min_roster: { WR: 1 } });
  return gas;
}

// ---- audit fixes ------------------------------------------------------------
const claimsOf = (w) => plain(w.claims.map((c) => [c.kind, c.add.id, c.drop && c.drop.id]));

test('player list: an HTTP error is never parsed as an empty list; an older copy is used instead', () => {
  const gas = loadGas();
  gas.fetch_ = () => ({ code: 429, text: 'Too Many Requests' });
  assert.throws(() => gas.playersSlim_(0), /player list \(HTTP 429\)/);
  gas.fetch_ = () => ({ code: 200, text: JSON.stringify({ 9221: { full_name: 'Jahmyr Gibbs', position: 'RB', team: 'DET' } }) });
  gas.playersSlim_(0);
  gas.fetch_ = () => ({ code: 429, text: 'Too Many Requests' });
  assert.deepEqual(Object.keys(gas.playersSlim_(0)), ['9221']);
  gas.fetch_ = () => ({ code: 200, text: '{}' });
  assert.deepEqual(Object.keys(gas.playersSlim_(0)), ['9221']);  // an empty list is a failure too
});

test('player id table: an HTTP error is never cached as an empty map', () => {
  const gas = loadGas();
  gas.fetch_ = () => ({ code: 429, text: '429: Too Many Requests' });
  assert.throws(() => gas.fpToSleeper_(), /id table \(HTTP 429\)/);
  gas.fetch_ = () => ({ code: 200, text: 'name,fantasypros_id,sleeper_id\nA,1,11\nB,NA,12\n' });
  assert.deepEqual(plain(gas.fpToSleeper_()), { 1: '11' });
});

test('lineup: nobody is taken out without a replacement, so missing player data saves nothing', () => {
  const gas = loadGas();
  const r = gas.optimize_(['QB', 'RB'], ['qb1', 'rb1'], ['qb1', 'rb1', 'rb2'], () => null);
  assert.deepEqual([Array.from(r.starters), r.changes.length], [['qb1', 'rb1'], 0]);
  const { gas: g, writes } = fixtureGas(NOW);
  g.playersSlim_ = () => ({});  // e.g. Sleeper's player list failed and nothing was cached
  g.setMode('auto');
  g.tick();
  assert.equal(writes.length, 0);
});

test('"Check lineups now" in suggestions-only mode reports but never saves', () => {
  const { gas, writes } = fixtureGas(NOW);
  gas.runNow();
  assert.equal(writes.length, 0);
  assert.match(gas.getJson_('lastTick').msg, /Test: 2 lineup changes suggested/);
  gas.setMode('auto');
  gas.runNow();
  assert.deepEqual(writes.map((w) => w[0]), ['starters']);
});

test('autopilot: a failed lineup check or save is reported as such, and logged once', () => {
  const { gas, writes } = fixtureGas(NOW);
  const lists = gas.fpList_;
  gas.fpList_ = (slug) => { if (slug === 'k') throw new Error('FantasyPros k failed (HTTP 503)'); return lists(slug); };
  gas.setMode('auto');
  gas.tick();
  gas.tick();
  assert.equal(gas.getJson_('lastTick').status, 'error');
  assert.match(gas.getJson_('lastTick').msg, /couldn't check the lineup/);
  assert.equal(gas.getJson_('log').filter((e) => e.title === 'Lineup check failed').length, 1);
  assert.equal(writes.length, 0);
  gas.fpList_ = lists;
  gas.setStarters_ = () => { throw new Error("Sleeper didn't accept the lineup."); };
  gas.tick();
  assert.deepEqual([gas.getJson_('lastTick').status, gas.getJson_('lastTick').msg], ['error', 'Test: saving the lineup failed']);
});

test('waivers: a pending claim with no drop fills the open roster spot', () => {
  const saved = ROSTER.players;
  ROSTER.players = saved.filter((p) => p !== 'wr_f');  // 8 players, 9 spots
  try {
    const { gas } = fixtureGas(NOW);
    gas.pendingWaivers_ = () => [{ roster_ids: [1], adds: { wr_fa: 1 }, drops: {} }];
    const w = gas.getDashboard().leagues[0].waivers;
    assert.ok(!w.claims.some((c) => !c.drop), JSON.stringify(claimsOf(w)));
  } finally {
    ROSTER.players = saved;
  }
});

test('waivers: when pending claims can\'t be read, nothing is submitted and the window stays open', () => {
  const tue = Date.parse('2026-10-20T20:00:00Z');
  const { gas, writes } = fixtureGas(tue);
  gas.pendingWaivers_ = () => { throw new Error('Sleeper returned HTTP 502'); };
  gas.setMode('auto');
  gas.saveLeagueSettings('L', { auto_waivers: true, auto_lineup: false, min_roster: { WR: 1 } });
  const w = gas.getDashboard().leagues[0].waivers;
  assert.equal(w.pendingUnknown, true);
  assert.match(w.notes.join(' '), /won't be submitted/);
  gas.tick();
  gas.tick();
  assert.equal(writes.length, 0);
  assert.deepEqual(plain(gas.getJson_('waivers_done', {})), {});
  assert.equal(gas.getJson_('log').filter((e) => e.title === 'Waiver planning failed').length, 1);
  const res = gas.submitClaims('L', w.claims.map((c) => [c.add.id, c.drop && c.drop.id, c.bid]));
  assert.match(res.waivers.submitError, /no claims were submitted/);
  assert.equal(writes.length, 0);
});

test('waiver window: Monday waivers (day 0) open Sunday evening', () => {
  const gas = loadGas();
  const lg = { settings: { waiver_day_of_week: 0 } };
  assert.equal(gas.waiverWindow_(lg, Date.parse('2026-10-25T20:00:00Z') / 1000), '2026-10-25');
  assert.equal(gas.waiverWindow_(lg, Date.parse('2026-10-27T20:00:00Z') / 1000), null);
});

test('waivers: an injured pickup can\'t replace a healthy player below the position minimum', () => {
  const gas = loadGas();
  const pos = { fa_rb_ir: 'RB', rb1: 'RB', rb2: 'RB' };
  const values = { fa_rb_ir: 60, rb1: 150, rb2: 140 };
  const claims = gas.planUpgrades_({ freeAgents: ['fa_rb_ir'], myPlayers: ['rb1', 'rb2'], value: (p) => values[p],
    dropValue: (p) => values[p], position: (p) => pos[p], protected: {}, minimums: { RB: 2 }, rosterLimit: 2,
    maxClaims: 5, minGain: 10, blockedDrops: {}, healthy: (p) => p !== 'fa_rb_ir' });
  assert.equal(claims.length, 0);
});

test('waivers: the K/DEF stream never drops a player an upgrade already drops', () => {
  PLAYERS.NYJ = ['New York Jets', 'DEF', 'NYJ', null, null];
  PLAYERS.MIA = ['Miami Dolphins', 'DEF', 'MIA', null, null];
  const dst = LISTS.dst, rosDst = LISTS['ros-dst'];
  LISTS.dst = list(7, [['MIA', 2, 'DST1'], ['DET', 10, 'DST5'], ['NYJ', 20, 'DST20']]);
  LISTS['ros-dst'] = list(0, [['DET', 3, 'DST3'], ['MIA', 15, 'DST15'], ['NYJ', 20, 'DST20']]);
  LISTS.dst.players.concat(LISTS['ros-dst'].players).forEach((r) => { r[2] = 'DST'; });
  ROSTER.players.push('NYJ');
  try {
    const { gas } = fixtureGas(NOW);
    const w = gas.getDashboard().leagues[0].waivers;
    const drops = claimsOf(w).map((c) => c[2]).filter(Boolean);
    assert.ok(drops.includes('NYJ'));
    assert.equal(drops.length, new Set(drops).size, JSON.stringify(claimsOf(w)));
  } finally {
    delete PLAYERS.NYJ; delete PLAYERS.MIA;
    LISTS.dst = dst; LISTS['ros-dst'] = rosDst;
    ROSTER.players.pop();
  }
});

test('submit claims: sends what the page showed, or nothing if the plan has changed since', () => {
  const { gas, writes } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
  const shown = gas.getDashboard().leagues[0].waivers.claims.map((c) => [c.add.id, c.drop && c.drop.id, c.bid]);
  const stale = gas.submitClaims('L', [['wr_fa', 'wr_f', 9]]);
  assert.equal(stale.waivers.changed, true);
  assert.equal(writes.length, 0);
  gas.submitClaims('L', shown);
  assert.deepEqual(plain(writes.map((w) => w.slice(3, 6))), plain(shown));
  assert.throws(() => gas.submitClaims('L'), /Reload the page/);
});

test('one league failing to load doesn\'t hide or stop the others', () => {
  const { gas, writes } = fixtureGas(NOW);
  const base = gas.sleeper_;
  const broken = Object.assign({}, LEAGUE, { league_id: 'B', name: 'Broken' });
  gas.sleeper_ = (p, fresh) => {
    if (p.includes('/leagues/')) return [broken, LEAGUE];
    if (p.startsWith('/league/B/')) throw new Error('Sleeper API /league/B/rosters failed (HTTP 503)');
    return base(p, fresh);
  };
  const leagues = gas.getDashboard().leagues;
  assert.deepEqual(plain(leagues.map((l) => [l.name, !!l.lineup])), [['Broken', false], ['Test', true]]);
  assert.match(leagues[0].notes[0], /Couldn't load this league/);
  gas.setMode('auto');
  gas.tick();
  assert.deepEqual(writes.map((w) => w[0]), ['starters']);
  assert.match(gas.getJson_('lastTick').msg, /Broken: error · Test: lineup updated/);
});

test('lineup: untracked IDP starters are left alone without bogus warnings', () => {
  LEAGUE.roster_positions.splice(7, 0, 'DL');
  ROSTER.players.push('idp1');
  ROSTER.starters.push('idp1');
  try {
    const { gas } = fixtureGas(NOW);
    const l = gas.getDashboard().leagues[0].lineup;
    assert.deepEqual(plain(l.warnings), []);
    const dl = l.lineup.find((p) => p.slot === 'DL');
    assert.deepEqual([dl.id, dl.why, dl.pos], ['idp1', null, '']);
  } finally {
    LEAGUE.roster_positions.splice(7, 1);
    ROSTER.players.pop();
    ROSTER.starters.pop();
  }
});

test('never_drop: a Sleeper id doesn\'t protect every defense', () => {
  const { gas } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { never_drop: ['4034', 'qb_b'] });
  assert.deepEqual(Object.keys(gas.withLeague_('L', (lg) => lg.neverDrop())), ['qb_b']);
});

test('updates come from main once main has a build, never from the branch next to it', () => {
  const v = loadGas({ file: DIST }).buildInfo_().version;
  const gas = loadGas({ file: DIST, fetch(url) {
    if (url.includes('raw.githubusercontent.com')) {
      return url.includes('/main/') ? { body: remoteBuild(v + 1, 'main') } : { body: remoteBuild(v + 5, 'branch') };
    }
  } });
  assert.equal(gas.checkForUpdate().latest.id, 'main');
  const down = loadGas({ file: DIST, fetch(url) {
    if (url.includes('raw.githubusercontent.com')) {
      return url.includes('/main/') ? { code: 503, body: '' } : { body: remoteBuild(v + 5, 'branch') };
    }
  } });
  assert.match(down.checkForUpdate().error, /Couldn't reach GitHub/);
});

test('removing an update frees its storage', () => {
  const v = loadGas({ file: DIST }).buildInfo_().version;
  const gas = updaterGas(remoteBuild(v + 1, 'n1'));
  gas.installUpdate('n1');
  assert.ok(gas.__props.getProperty('engine#3'));
  gas.removeUpdate();
  assert.deepEqual(Object.keys(gas.__props._data).filter((k) => k.startsWith('engine#')), []);
});

// ---- improvements: lineups ------------------------------------------------------
const opRow = (id) => LISTS['ppr-superflex'].players.find((r) => r[0] === id);
function withChanges(apply, fn) {
  const undo = [];
  try {
    apply((obj, key, val) => { undo.push([obj, key, obj[key], key in obj]); obj[key] = val; });
    return fn();
  } finally {
    undo.reverse().forEach(([obj, key, old, had]) => { if (had) obj[key] = old; else delete obj[key]; });
  }
}

test('lineup: of two close starters, the later game goes in the flex', () => {
  withChanges((set) => {
    set(LEAGUE, 'roster_positions', ['QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPER_FLEX', 'K', 'DEF', 'BN', 'BN']);
    set(ROSTER, 'starters', ['qb_a', 'rb_c', 'wr_e', 'te_g', 'rb_d', 'qb_b', 'k_1', 'DET']);
    set(opRow('rb_c'), 8, KICK + 3 * 86400);   // Monday night
  }, () => {
    const { gas } = fixtureGas(NOW);
    const l = gas.getDashboard().leagues[0].lineup;
    assert.deepEqual(plain(l.lineup.map((p) => [p.slot, p.id])).slice(1, 5),
                     [['RB', 'rb_d'], ['WR', 'wr_e'], ['TE', 'te_g'], ['FLEX', 'rb_c']]);
    assert.equal(l.changes, 2);
  });
});

test('lineup: a Questionable player needs to rank clearly better than a healthy one', () => {
  withChanges((set) => {
    set(PLAYERS, 'wr_y', ['wr_y', 'WR', 'CHI', null, null]);
    set(PLAYERS, 'wr_e', ['wr_e', 'WR', 'MIA', 'Questionable', null]);
    set(ROSTER, 'players', ROSTER.players.concat('wr_y'));
    set(LISTS['ppr-superflex'], 'players', LISTS['ppr-superflex'].players.concat(
      [['wr_y', 'wr_y', 'WR', 'CHI', 11, 'WR2', '14', 'vs. X', KICK, 'created']]));
    set(LEAGUE, 'roster_positions', LEAGUE.roster_positions.concat('BN'));
  }, () => {
    const { gas } = fixtureGas(NOW);
    const l = gas.getDashboard().leagues[0].lineup;
    assert.equal(l.lineup.find((p) => p.slot === 'WR').id, 'wr_y');   // 10 + 2 > 11
  });
});

test('lineup: 6-point passing TDs tip the superflex towards the QB', () => {
  withChanges((set) => set(opRow('qb_b'), 4, 58), () => {
    const sf = (gas) => gas.getDashboard().leagues[0].lineup.lineup.find((p) => p.slot === 'SUPER_FLEX').id;
    assert.equal(sf(fixtureGas(NOW).gas), 'rb_d');                         // 58 - 10 > 45
    withChanges((set) => set(LEAGUE, 'scoring_settings', { rec: 1, pass_td: 6 }), () => {
      assert.equal(sf(fixtureGas(NOW).gas), 'qb_b');                       // 58 - 20 < 45
    });
  });
});

// ---- improvements: waivers -------------------------------------------------------
test('waivers: a starter on bye with nobody to fill in gets a one-week fill-in', () => {
  withChanges((set) => {
    set(PLAYERS, 'te_fa', ['te_fa', 'TE', 'ATL', null, null]);
    set(opRow('te_g'), 6, '7');   // te_g, the only TE, is on bye
    set(LISTS['ppr-superflex'], 'players', LISTS['ppr-superflex'].players.concat(
      [['te_fa', 'te_fa', 'TE', 'ATL', 65, 'TE2', '14', 'vs. X', KICK, 'created']]));
    set(LISTS['ros-ppr-overall'].players.find((r) => r[0] === 'wr_f'), 5, 'WR40');   // easy to replace
  }, () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { max_claims: 0 });
    const w = gas.getDashboard().leagues[0].waivers;
    assert.deepEqual(claimsOf(w).filter((c) => c[0] === 'cover'), [['cover', 'te_fa', 'wr_f']]);
    assert.match(w.notes.join(' '), /te_g \(TE, bye\) can't play this week and nobody on your bench can fill in, so this adds te_fa/);
    gas.saveLeagueSettings('L', { cover_byes: false });
    assert.ok(!claimsOf(gas.getDashboard().leagues[0].waivers).some((c) => c[0] === 'cover'));
  });
});

test('waivers: with a top rolling waiver priority, matchup streams are skipped and upgrades must gain double', () => {
  withChanges((set) => {
    set(LEAGUE, 'settings', Object.assign({}, LEAGUE.settings, { waiver_type: 0 }));
    set(ROSTER, 'settings', { waiver_budget_used: 0, waiver_position: 1 });
  }, () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
    let w = gas.getDashboard().leagues[0].waivers;
    assert.ok(!w.claims.some((c) => c.kind === 'stream'), JSON.stringify(claimsOf(w)));
    assert.match(w.notes.join(' '), /waiver priority is #1 of 2 .* upgrades must gain 40 spots instead of 20/);
    assert.deepEqual(plain(w.priority), { position: 1, teams: 2, rolling: true });
    ROSTER.settings.waiver_position = 2;   // back half: claims cost little
    w = gas.getDashboard().leagues[0].waivers;
    assert.ok(w.claims.some((c) => c.kind === 'stream'));
  });
});

test('waivers: a kept (starred) player is never dropped, and the lineup shows the star', () => {
  const { gas } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { min_roster: { WR: 1 }, never_drop: ['wr_f'] });
  const lg = gas.getDashboard().leagues[0];
  assert.ok(!lg.waivers.claims.some((c) => c.drop && c.drop.id === 'wr_f'));
  assert.equal(lg.lineup.bench.find((p) => p.id === 'wr_f').keep, true);
});

// ---- improvements: alerts, lock, lighter Sleeper use ------------------------------
function withAlerts(gas) {
  const sent = [];
  gas.sendAlert_ = (topic, n) => { sent.push([n.title, n.message, n.priority]); return { code: 200 }; };
  gas.saveAlerts({ on: true });
  return sent;
}

test('alerts: turning on makes a private topic; the request goes to ntfy with it', () => {
  const calls = [];
  const gas = loadGas({ fetch(url, params) { if (url === 'https://ntfy.sh') { calls.push(JSON.parse(params.payload)); return { body: '{}' }; } } });
  const st = gas.saveAlerts({ on: true });
  assert.match(st.alerts.topic, /^sleeper-autopilot-[0-9a-f]{20}$/);
  assert.equal(gas.testAlert(), true);
  assert.deepEqual([calls[0].topic, calls[0].title], [st.alerts.topic, 'Sleeper Autopilot']);
  assert.match(calls[0].click, /script\.google\.com/);
  gas.saveAlerts({ changes: false });
  assert.equal(gas.getState().alerts.changes, false);
  assert.equal(gas.saveAlerts({ on: false }).alerts.on, false);
  assert.throws(() => gas.testAlert(), /Turn alerts on first/);
});

test('alerts: lineup changes are sent (unless turned off); a lasting problem is sent once', () => {
  const { gas } = fixtureGas(NOW);
  const sent = withAlerts(gas);
  gas.setMode('auto');
  gas.tick();
  assert.deepEqual(sent.map((a) => a[0]), ['Test: lineup updated']);
  assert.match(sent[0][1], /OUT wr_f \(Out\)/);
  const lists = gas.fpList_;
  gas.fpList_ = (slug) => { if (slug === 'k') throw new Error('FantasyPros k failed (HTTP 503)'); return lists(slug); };
  gas.tick();
  gas.tick();
  assert.deepEqual(sent.slice(1).map((a) => [a[0], a[2]]), [['Test: lineup check failed', 4]]);
});

test('alerts: in suggestions-only mode they say what to change, once per suggestion; nothing is saved', () => {
  const { gas, writes } = fixtureGas(NOW);
  const sent = withAlerts(gas);
  gas.tick();
  gas.tick();
  assert.equal(writes.length, 0);
  assert.deepEqual(sent.map((a) => a[0]), ['Test: lineup changes to make']);
  assert.match(sent[0][1], /tap Apply now/);
});

test('alerts: an expired session and a new version reach the phone', () => {
  const { gas } = fixtureGas(NOW);
  const sent = withAlerts(gas);
  gas.sessionExpired_();
  assert.equal(sent[0][0], 'Sleeper session expired');
  gas.checkForUpdate = () => ({ available: true, latest: { id: 'x', title: 'Newer' } });
  gas.checkUpdateDaily_();
  gas.checkUpdateDaily_();
  assert.deepEqual(sent.slice(1).map((a) => a[0]), ['Update available: Newer']);
});

test('buttons wait for a running background check instead of writing at the same time', () => {
  const { gas } = fixtureGas(NOW);
  gas.LockService = { getUserLock: () => ({ tryLock: () => false, releaseLock() {} }) };
  assert.throws(() => gas.applyLineup('L'), /busy/);
  assert.throws(() => gas.submitClaims('L', []), /busy/);
});

test('idle checks (no games within 30h, no waiver window) download nothing', () => {
  const sat = Date.parse('2026-10-17T12:00:00Z');   // games on the 22nd, waivers on the 21st
  const { gas } = fixtureGas(sat);
  let calls = 0;
  const fp = gas.fpList_, sl = gas.sleeper_;
  gas.fpList_ = (x) => { calls++; return fp(x); };
  gas.sleeper_ = (p, f) => { calls++; return sl(p, f); };
  gas.setMode('auto');
  gas.saveLeagueSettings('L', { auto_waivers: true });
  gas.tick();
  assert.ok(calls > 0);
  const before = calls;
  gas.tick();
  assert.equal(calls, before);
  assert.equal(gas.getJson_('lastTick').msg, 'No games in the next 30h; nothing to do.');
  assert.ok(gas.getJson_('idle_until') <= Date.parse('2026-10-18T00:00:00Z') / 1000);   // capped at 12h
  gas.saveLeagueSettings('L', { min_gain: 25 });   // any settings change re-checks right away
  gas.tick();
  assert.ok(calls > before);
});

test('Sleeper\'s player list: every 6 hours, plus once after each kickoff slot\'s inactives are out', () => {
  const gas = loadGas();
  const k = 1_800_000_000;
  assert.equal(gas.playersMaxAge_([k], k - 3 * 3600), 6 * 3600);
  assert.equal(gas.playersMaxAge_([k], k - 60 * 60), 20 * 60);   // inactives at k-80min
  assert.equal(gas.playersMaxAge_([k], k + 60), 6 * 3600);       // game started
});

test('waiver windows: the next one opens the evening before waiver day', () => {
  const gas = loadGas();
  const next = gas.nextWaiverWindow_({ settings: { waiver_day_of_week: 2 } }, Date.parse('2026-10-25T10:00:00Z') / 1000);
  assert.equal(new Date(next * 1000).toISOString(), '2026-10-27T16:00:00.000Z');
});

// ---- rankings (ported from the retired Python tests) ------------------------------
test('rankings: id table first, name fallback, team aliases, byes and locks', () => {
  const gas = loadGas();
  const players = { 9221: ['Jahmyr Gibbs', 'RB', 'DET', null, null], 6804: ['Jordan Love', 'QB', 'GB', null, null],
                    4984: ['Josh Allen', 'QB', 'BUF', null, null], 777: ['Marvin Harrison Jr.', 'WR', 'ARI', null, null],
                    JAX: ['Jacksonville Jaguars', 'DEF', 'JAX', null, null] };
  const row = (id, name, pos, team, rank, kickoff, bye = '9', opp = 'vs. X', status = 'created') =>
    [id, name, pos, team, rank, pos + rank, bye, opp, kickoff, status];
  const data = { week: 7, label: 't', players: [
    row(22968, 'Jahmyr Gibbs', 'RB', 'DET', 1, 1000, '9', 'vs. X', 'closed'),
    row(19246, 'Jordan Love', 'QB', 'GB', 2, 5000),
    row(1, 'Marvin Harrison', 'WR', 'ARI', 3, 5000),        // no id table entry: matched by name
    row(2, 'Josh Allen', 'QB', 'BUF', 50, null, '7', ''),   // on bye
    row(3, 'Jacksonville Jaguars', 'DST', 'JAC', 4, 6000),  // FantasyPros team code
  ] };
  const r = new gas.RankList_(data, new gas.IdMap_(players, { 22968: '9221', 19246: '6804' }), 2000);
  assert.deepEqual([r.get('9221').started, r.get('6804').started], [true, false]);
  assert.equal(r.get('777').rank, 3);
  assert.equal(r.get('4984').bye, true);
  assert.equal(r.get('JAX').rank, 4);
  assert.deepEqual(plain(r.unmatched), []);
  assert.ok(!('BUF' in r.teamKickoff));
  const tmpl = gas.superflexTemplate_(r, players);
  assert.deepEqual(plain(tmpl.QB), [2]);   // Allen on bye isn't "QB2" this week
  assert.equal(gas.templateValue_(tmpl, 'QB', 1), 2);
  assert.ok(gas.templateValue_(tmpl, 'QB', 3) > 2);
  assert.deepEqual([gas.scoringFormat_({ rec: 1 }), gas.scoringFormat_({ rec: 0.5 }), gas.scoringFormat_({})],
                   ['PPR', 'HALF', 'STD']);
});


// ---- free agents ------------------------------------------------------------------
test('free agents: added exactly like sleeper.com\'s Add button, and a non-completed pickup is an error', () => {
  const sent = [];
  let status = 'complete';
  const gas = loadGas({ gql(body) {
    sent.push(body);
    if (body.query.includes('league_players(')) {
      return { data: { league_players: [{ player_id: 'a', settings: { waiver_clears_at: 99 } }, { player_id: 'b', settings: null }] } };
    }
    return { data: { league_create_transaction: { adds: { p1: 3 }, drops: { p2: 3 }, status, type: 'free_agent' } } };
  } });
  gas.addFreeAgent_('t', '1393366794277765120', 3, 'p1', 'p2');
  assert.match(sent[0].query, /league_create_transaction\(league_id: "1393366794277765120", type: "free_agent", k_adds: \$k_adds/);
  assert.deepEqual(plain(sent[0].variables), { k_adds: ['p1'], v_adds: [3], k_drops: ['p2'], v_drops: [3] });
  status = 'failed';
  assert.throws(() => gas.addFreeAgent_('t', '1', 3, 'p1', null), /didn't complete the pickup \(failed\)/);
  assert.deepEqual(plain(gas.waiverClears_('t', '1')), { a: 99 });
  assert.match(sent[sent.length - 1].query, /query league_players\(\$league_id: String!\)/);
});

function teBye(set) {
  set(PLAYERS, 'te_fa', ['te_fa', 'TE', 'ATL', null, null]);
  set(opRow('te_g'), 6, '7');   // te_g, the only TE, is on bye
  set(LISTS['ppr-superflex'], 'players', LISTS['ppr-superflex'].players.concat(
    [['te_fa', 'te_fa', 'TE', 'ATL', 65, 'TE2', '14', 'vs. X', KICK, 'created']]));
  set(LISTS['ros-ppr-overall'].players.find((r) => r[0] === 'wr_f'), 5, 'WR40');   // easy to replace
  set(LEAGUE, 'settings', Object.assign({}, LEAGUE.settings, { leg: 7 }));         // this week's waivers have run
}

test('free agents: after waivers, a hole is filled right away; players on waivers or already playing are skipped', () => {
  withChanges(teBye, () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { max_claims: 0 });   // just the hole here, no upgrades
    let f = gas.getDashboard().leagues[0].freeAgents;
    assert.deepEqual(claimsOf(f).find((c) => c[0] === 'cover'), ['cover', 'te_fa', 'wr_f']);
    assert.match(f.notes.join(' '), /picks up te_fa as a free agent and drops wr_f/);
    gas.waiverClears_ = () => ({ te_fa: NOW / 1000 + 3600 });   // just dropped: still on waivers
    f = gas.getDashboard().leagues[0].freeAgents;
    assert.ok(!claimsOf(f).some((c) => c[1] === 'te_fa'));
    assert.match(f.notes.join(' '), /no free agent is available/);
    gas.waiverClears_ = () => ({});
    opRow('te_fa')[8] = NOW / 1000 - 60;   // his game already started: on waivers until Wednesday
    f = gas.getDashboard().leagues[0].freeAgents;
    opRow('te_fa')[8] = KICK;
    assert.ok(!claimsOf(f).some((c) => c[1] === 'te_fa'));
  });
  withChanges((set) => { teBye(set); set(LEAGUE, 'settings', Object.assign({}, LEAGUE.settings, { leg: 6 })); }, () => {
    const f = fixtureGas(NOW).gas.getDashboard().leagues[0].freeAgents;
    assert.match(f.waiting, /once this week's waivers have run/);
  });
});

test('free agents: the autopilot picks them up before setting the lineup, and says so', () => {
  withChanges(teBye, () => {
    const { gas, writes } = fixtureGas(NOW);
    const sent = withAlerts(gas);
    gas.setMode('auto');
    gas.saveLeagueSettings('L', { auto_waivers: true, max_claims: 0 });
    gas.tick();
    const kinds = writes.map((w) => w[0]);
    assert.ok(kinds.indexOf('fa') >= 0 && kinds.indexOf('fa') < kinds.indexOf('starters'), JSON.stringify(writes));
    assert.deepEqual(plain(writes.find((w) => w[0] === 'fa').slice(1)), ['te_fa', 'wr_f']);
    assert.ok(sent.some((a) => a[0] === 'Test: free agents picked up'));
    assert.match(gas.getJson_('lastTick').msg, /free agents? added/);
  });
});

test('free agents: in suggestions-only mode an alert says which to add; "Add now" adds what the page showed', () => {
  withChanges(teBye, () => {
    const { gas, writes } = fixtureGas(NOW);
    const sent = withAlerts(gas);
    gas.saveLeagueSettings('L', { auto_waivers: true });
    gas.tick();
    gas.tick();
    assert.equal(writes.filter((w) => w[0] === 'fa').length, 0);
    assert.equal(sent.filter((a) => a[0] === 'Test: free agents to add').length, 1);
    const f = gas.getDashboard().leagues[0].freeAgents;
    const shown = f.claims.map((c) => [c.add.id, c.drop && c.drop.id, null]);
    assert.equal(gas.addFreeAgents('L', [['nobody', null, null]]).freeAgents.changed, true);
    gas.addFreeAgents('L', shown);
    assert.deepEqual(plain(writes.filter((w) => w[0] === 'fa').map((w) => w.slice(1))), plain(shown.map((c) => c.slice(0, 2))));
  });
});

test('idle checks wake up shortly after the waiver run, when free agents open up', () => {
  const tue = Date.parse('2026-10-20T22:00:00Z');
  const { gas } = fixtureGas(tue);
  gas.setMode('auto');
  gas.saveLeagueSettings('L', { auto_waivers: true, auto_lineup: false, min_roster: { WR: 1 } });
  gas.tick();
  assert.equal(new Date(gas.getJson_('idle_until') * 1000).toISOString(), '2026-10-21T09:00:00.000Z');
});


test('after waivers: upgrades to free agents are picked up now; the waiver plan keeps only players on waivers', () => {
  withChanges((set) => set(LEAGUE, 'settings', Object.assign({}, LEAGUE.settings, { leg: 7 })), () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
    let lg = gas.getDashboard().leagues[0];
    assert.deepEqual(claimsOf(lg.freeAgents).find((c) => c[0] === 'upgrade'), ['upgrade', 'qb_fa', 'wr_f']);
    assert.ok(!lg.waivers.claims.some((c) => c.add.id === 'qb_fa'));
    assert.ok(!lg.waivers.claims.some((c) => c.drop && c.drop.id === 'wr_f'));   // not dropped twice
    gas.waiverClears_ = () => ({ qb_fa: NOW / 1000 + 86400 });   // just dropped by someone: still on waivers
    lg = gas.getDashboard().leagues[0];
    assert.ok(!lg.freeAgents.claims.some((c) => c.add.id === 'qb_fa'));
    assert.deepEqual(claimsOf(lg.waivers).find((c) => c[1] === 'qb_fa'), ['upgrade', 'qb_fa', 'wr_f']);
  });
});

test('upgrades picked up as free agents count toward the weekly limit', () => {
  withChanges((set) => set(LEAGUE, 'settings', Object.assign({}, LEAGUE.settings, { leg: 7 })), () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { min_roster: { WR: 1 }, max_claims: 1 });
    const f = gas.getDashboard().leagues[0].freeAgents;
    gas.addFreeAgents('L', f.claims.map((c) => [c.add.id, c.drop && c.drop.id, null]));
    assert.equal(gas.upgradesDone_('L', 7), 1);
    const lg = gas.getDashboard().leagues[0];
    assert.ok(!lg.freeAgents.claims.some((c) => c.kind === 'upgrade'));
    assert.match(lg.waivers.notes.join(' '), /limit of 1 upgrades a week is used up/);
  });
});

test('a player picked up in the last week needs twice the usual gain to be dropped again', () => {
  const { gas } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { never_drop: ['wr_f'], min_roster: { RB: 1, WR: 1 } });
  const qbClaim = () => claimsOf(gas.getDashboard().leagues[0].waivers).find((c) => c[1] === 'qb_fa');
  assert.deepEqual(qbClaim(), ['upgrade', 'qb_fa', 'rb_d']);   // QB2 (20) for RB2 (45): +25
  const base = gas.sleeper_;
  gas.sleeper_ = (p, fresh) => (p.includes('/transactions/')
    ? [{ status: 'complete', status_updated: NOW - 86400000, adds: { rb_d: 1 }, drops: null }] : base(p, fresh));
  assert.equal(qbClaim(), undefined);                         // rb_d was just picked up: +25 < 40
});

test('a spare defense shows its real rest-of-season rank, never "999"', () => {
  withChanges((set) => {
    set(PLAYERS, 'NYJ', ['New York Jets', 'DEF', 'NYJ', null, null]);
    set(LISTS, 'ros-dst', list(0, [['DET', 3, 'DST3'], ['NYJ', 14, 'DST14']]));
    LISTS['ros-dst'].players.forEach((r) => { r[2] = 'DST'; });
    set(ROSTER, 'players', ROSTER.players.concat('NYJ'));
  }, () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { stream_k_def: false, min_roster: { WR: 1 } });
    const c = gas.getDashboard().leagues[0].waivers.claims.find((x) => x.drop && x.drop.id === 'NYJ');
    assert.deepEqual([c.drop.rank, c.drop.posRank], [14, 'DST14']);
  });
});


test('after waivers: a player whose team is on bye is a free agent until the week\'s first game', () => {
  withChanges((set) => {
    set(LEAGUE, 'settings', Object.assign({}, LEAGUE.settings, { leg: 7 }));
    set(opRow('qb_fa'), 6, '7');   // qb_fa's team is on bye this week
    set(opRow('qb_fa'), 8, null);
  }, () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
    assert.ok(gas.getDashboard().leagues[0].freeAgents.claims.some((c) => c.add.id === 'qb_fa'));
    const late = fixtureGas(KICK * 1000 + 60000).gas;   // the week's first game has started
    late.saveLeagueSettings('L', { min_roster: { WR: 1 } });
    const lg = late.getDashboard().leagues[0];
    assert.ok(!lg.freeAgents.claims.some((c) => c.add.id === 'qb_fa'));
    assert.ok(lg.waivers.claims.some((c) => c.add.id === 'qb_fa'));   // claimable for the next run instead
  });
});

// ---- safety rules -------------------------------------------------------------------
function planWith(gas, mutate) {
  return gas.withLeague_('L', (lg) => {
    const res = lg.evaluate({ lineup: true, waivers: true, freeAgents: true });
    mutate(res, lg);
    return plain(gas.checkPlans_(lg, res));
  });
}

test('safety rules catch yesterday\'s bug: a claim for a player who is a free agent right now', () => {
  withChanges((set) => set(LEAGUE, 'settings', Object.assign({}, LEAGUE.settings, { leg: 7 })), () => {
    const { gas } = fixtureGas(NOW);
    gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
    const problems = planWith(gas, (res) => {   // what v13 did: the free agent sat in the waiver plan
      res.waivers.claims.push(...res.freeAgents.claims.filter((c) => c.kind === 'upgrade'));
      res.freeAgents.claims = res.freeAgents.claims.filter((c) => c.kind !== 'upgrade');
    });
    assert.ok(problems.some((x) => /qb_fa is a free agent right now/.test(x)), problems.join(' | '));
  });
});

test('safety rules: double drops, starred players, internal values, fresh pickups, roster size', () => {
  const { gas } = fixtureGas(NOW);
  gas.saveLeagueSettings('L', { min_roster: { WR: 1 } });
  const dup = planWith(gas, (res) => { res.waivers.claims.push(Object.assign({}, res.waivers.claims[0], { add: { id: 'wr_fa', name: 'wr_fa' } })); });
  assert.ok(dup.some((x) => /wr_f would be dropped twice/.test(x)), dup.join(' | '));
  gas.saveLeagueSettings('L', { never_drop: ['wr_f'] });
  const kept = planWith(gas, (res) => { res.waivers.claims[0].drop = { id: 'wr_f', name: 'wr_f', rank: 300 }; });
  assert.ok(kept.some((x) => /wr_f is starred/.test(x)), kept.join(' | '));
  gas.saveLeagueSettings('L', { never_drop: [] });
  const internal = planWith(gas, (res) => { res.waivers.claims[0].drop.rank = 999; });
  assert.ok(internal.some((x) => /internal value \(999\)/.test(x)), internal.join(' | '));
  const base = gas.sleeper_;
  gas.sleeper_ = (p, f) => (p.includes('/transactions/') ? [{ status: 'complete', status_updated: NOW - 3600000, adds: { wr_f: 1 } }] : base(p, f));
  const fresh = planWith(gas, (res) => { res.waivers.claims[0].add.rank = res.waivers.claims[0].drop.rank - 25; });
  assert.ok(fresh.some((x) => /just picked up/.test(x)), fresh.join(' | '));
  gas.sleeper_ = base;
  const big = planWith(gas, (res) => { res.waivers.claims.push({ kind: 'upgrade', add: { id: 'te_fa', name: 'te_fa' }, drop: null }, { kind: 'upgrade', add: { id: 'zz', name: 'zz' }, drop: null }); });
  assert.ok(big.some((x) => /roster would have/.test(x)), big.join(' | '));
});

test('safety rules: lineups may not move a locked player or start an injured one over a healthy bench player', () => {
  const { gas } = fixtureGas(NOW);
  const benched = planWith(gas, (res) => {
    const i = res.lineup.starters.indexOf('wr_e');
    res.lineup.starters[i] = 'wr_f';
    res.lineup.lineup[i] = Object.assign({}, res.lineup.lineup[i], { id: 'wr_f', name: 'wr_f', why: 'Out' });
    res.lineup.bench.push({ id: 'wr_e', name: 'wr_e', tracked: true, why: null, locked: false });
  });
  assert.ok(benched.some((x) => /wr_f \(Out\) would start at WR while wr_e sits/.test(x)), benched.join(' | '));
  const late = fixtureGas(KICK * 1000 + 60000).gas;   // every game has started
  const moved = planWith(late, (res) => { res.lineup.starters[1] = 'rb_d'; });
  assert.ok(moved.some((x) => /game has started/.test(x)), moved.join(' | '));
});

test('a plan that fails the safety rules is never carried out', () => {
  const { gas, writes } = fixtureGas(NOW);
  gas.checkPlans_ = () => ['something looks wrong'];
  gas.setMode('auto');
  gas.saveLeagueSettings('L', { auto_waivers: true });
  gas.tick();
  assert.equal(writes.length, 0);
  assert.match(gas.getJson_('lastTick').msg, /held back by a safety check/);
  assert.ok(gas.getJson_('log').some((e) => /Safety check stopped the lineup/.test(e.title)));
  const res = gas.applyLineup('L');
  assert.deepEqual(plain(res.safety), ['something looks wrong']);
  assert.equal(writes.length, 0);
});
