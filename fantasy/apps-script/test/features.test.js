// Matchup projections, the trade finder and trade offers, on the configurable league in
// test/fixture.js. Nothing here reaches Sleeper: projections, game states and offers are stubbed.
const test = require('node:test');
const assert = require('node:assert/strict');
const { build, plain, base, KICK } = require('./fixture');
const { loadGas } = require('../dev/gas-stub');

const gasOnly = loadGas();

test('projections are scored with the league\'s own rules', () => {
  const stats = { pass_yd: 250, pass_td: 2, pass_int: 1, rush_yd: 20, rec: 0, pts_ppr: 99, gp: 1 };
  assert.equal(gasOnly.scorePoints_(stats, { pass_yd: 0.04, pass_td: 4, pass_int: -2, rush_yd: 0.1 }), 10 + 8 - 2 + 2);
  assert.equal(gasOnly.scorePoints_(stats, { pass_yd: 0.04, pass_td: 6, pass_int: -2, rush_yd: 0.1 }), 22);  // 6-pt TDs
  assert.equal(gasOnly.scorePoints_({ def_td: 0.1, pts_allow_21_27: 1, sack: 2 }, { def_td: 6, pts_allow_21_27: 0, sack: 1 }), 2.6);
});

test('kicker projections count long field goals and misses the way the league scores them', () => {
  const proj = { fgm: 2, fgm_30_39: 1, fgm_40_49: 0.6, fgm_50p: 0.4, fgmiss_30_39: 0.1, fgmiss_50p: 0.2, xpm: 3 };
  const s = gasOnly.completeKicking_(proj);
  assert.equal(s.fgm_50_59, 0.4);
  assert.ok(Math.abs(s.fgmiss - 0.3) < 1e-9);
  // A league scoring fgm_50_59 / fgm_60p / fgmiss (not fgm_50p), like Wolfpack:
  const wolf = { fgm_30_39: 3, fgm_40_49: 4, fgm_50_59: 5, fgm_60p: 6, fgmiss: -1, xpm: 1 };
  assert.ok(Math.abs(gasOnly.scorePoints_(s, wolf) - (3 + 2.4 + 2 - 0.3 + 3)) < 1e-9);
  // A league scoring both forms, like SG Bears: Sleeper adds both on a real 50+ yard kick.
  const bears = { fgm_30_39: 3, fgm_40_49: 3, fgm_50p: 5, fgm_50_59: 5, xpm: 1 };
  assert.ok(Math.abs(gasOnly.scorePoints_(s, bears) - (3 + 1.8 + 4 + 3)) < 1e-9);
  // Stat lines that already carry every form are left as they are.
  const full = { fgm_50p: 1, fgm_50_59: 1, fgmiss: 0.5, fgmiss_40_49: 0.5 };
  assert.deepEqual(plain(gasOnly.completeKicking_(full)), full);
});

test('game clock: share of the game still to play', () => {
  assert.equal(gasOnly.gameLeft_(1, '15:00'), 1);
  assert.equal(gasOnly.gameLeft_(2, '0:00'), 0.5);
  assert.equal(gasOnly.gameLeft_(3, '7:30'), 0.375);
  assert.equal(gasOnly.gameLeft_(4, '0:00'), 0);
  assert.equal(gasOnly.gameLeft_(5, '10:00'), 0.02);   // overtime
  assert.equal(gasOnly.gameLeft_(null, null), 1);
});

test('win chance: even when level, certain when the games are over', () => {
  assert.ok(Math.abs(gasOnly.winChance_(100, 100, 100, 100) - 0.5) < 1e-6);
  assert.ok(gasOnly.winChance_(130, 130, 100, 100) > 0.75);
  assert.ok(gasOnly.winChance_(100, 100, 130, 130) < 0.25);
  assert.equal(gasOnly.winChance_(101, 0, 100, 0), 1);
  assert.equal(gasOnly.winChance_(99, 0, 100, 0), 0);
  for (let x = -4; x <= 4; x += 0.5) assert.ok(Math.abs(gasOnly.normCdf_(x) + gasOnly.normCdf_(-x) - 1) < 1e-7);
});

// ---- matchup -------------------------------------------------------------------------

const TEAMS = ['KC', 'DET', 'NYJ', 'MIA', 'SEA', 'LV', 'CHI', 'MIN', 'CLE', 'PIT', 'IND', 'TB', 'NO', 'ATL'];
const matchupSpec = () => {
  const s = base();   // te1 is Out
  s.matchups = [
    { roster_id: 1, matchup_id: 3, starters: ['qb1', 'rb1', 'wr1', 'te1', 'rb2', 'k1', 'DET'], players_points: {} },
    { roster_id: 2, matchup_id: 3, starters: ['0', 'p1', 'p2', '0', 'p3', '0', '0'], players_points: {} },
    { roster_id: 9, matchup_id: 4, starters: [], players_points: {} },
  ];
  s.users = [{ user_id: 'me', display_name: 'me' }, { user_id: 'x0', display_name: 'rival' }];
  s.proj = { qb1: 20, rb1: 15, wr1: 14, te1: 9, rb2: 10, k1: 8, DET: 6, wr2: 11, rb3: 5, wr3: 4, p1: 12, p2: 10, p3: 9 };
  return s;
};

test('matchup before kickoff: projections per player, totals, the best lineup, win chance', () => {
  const lg = build(matchupSpec()).gas.getDashboard().leagues[0];
  const M = lg.matchup;
  assert.equal(M.me.name, 'me');
  assert.equal(M.opp.name, 'rival');
  const rows = (side) => plain(side.rows.map((x) => [x.id, x.exp]));
  assert.deepEqual(rows(M.me.current), [['qb1', 20], ['rb1', 15], ['wr1', 14], ['te1', 0], ['rb2', 10], ['k1', 8], ['DET', 6]]);
  assert.equal(M.me.current.rows[3].why, 'Out');           // an Out player is expected to score nothing
  assert.equal(M.me.current.total, 73);
  assert.equal(M.opp.current.total, 31);                    // their empty spots score nothing
  assert.ok(M.me.best && M.opp.best);
  assert.ok(M.win.current > 85 && M.win.current <= 100);
  assert.equal(M.live, false);
  assert.equal(M.started, false);
  assert.equal(M.nextKick, KICK);
});

test('matchup during games: live points plus the projection for the time left; final points once over', () => {
  const s = matchupSpec();
  s.games = Object.fromEntries(TEAMS.map((t) => [t, { status: 'pre', left: 1, clock: null }]));
  s.games.KC = { status: 'post', left: 0, clock: null };
  s.games.DET = { status: 'in', left: 0.5, clock: 'Q3 7:30' };
  s.matchups[0].players_points = { qb1: 25.5, k1: 9, rb1: 6, DET: 2 };
  const M = build(s).gas.getDashboard().leagues[0].matchup;
  const byId = Object.fromEntries(M.me.current.rows.map((x) => [x.id, x]));
  assert.deepEqual([byId.qb1.status, byId.qb1.pts, byId.qb1.exp], ['post', 25.5, 25.5]);
  assert.deepEqual([byId.rb1.status, byId.rb1.pts, byId.rb1.exp, byId.rb1.clock], ['in', 6, 13.5, 'Q3 7:30']);
  assert.deepEqual([byId.wr1.status, byId.wr1.pts, byId.wr1.exp], ['pre', null, 14]);
  assert.equal(M.me.current.total, 25.5 + 13.5 + 14 + 0 + 10 + 9 + 5);
  assert.equal(M.live, true);
  assert.equal(M.started, true);
  // A team with no game this week is on bye: nothing expected.
  delete s.games.MIA;
  const M2 = build(s).gas.getDashboard().leagues[0].matchup;
  assert.deepEqual(plain([M2.me.current.rows[2].status, M2.me.current.rows[2].exp]), ['bye', 0]);
});

test('matchup: no opponent this week, or the matchup failing, never breaks the page', () => {
  let s = matchupSpec();
  s.matchups = [];
  let lg = build(s).gas.getDashboard().leagues[0];
  assert.equal(lg.matchup.none, 'No matchup this week.');
  assert.ok(lg.lineup.starters);
  s = matchupSpec();
  const { gas } = build(s);
  gas.projectedPoints_ = () => { throw new Error('Sleeper projections failed (HTTP 500)'); };
  lg = gas.getDashboard().leagues[0];
  assert.match(lg.matchup.error, /projections failed/);
  assert.ok(lg.lineup.starters);
  // The page's 2-minute refresh returns the same matchup.
  const again = build(matchupSpec()).gas.getMatchups();
  assert.equal(again[0].matchup.me.current.total, 73);
});

test('matchup: players the app does not track (IDP) count with Sleeper\'s own points', () => {
  const s = matchupSpec();
  s.positions = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF', 'DL', 'BN', 'BN', 'BN'];
  s.mine = s.mine.concat('idp1');
  s.matchups[0].starters = s.matchups[0].starters.concat('idp1');
  s.matchups[0].players_points = { idp1: 7.5 };
  s.matchups[1].starters = s.matchups[1].starters.concat('0');
  const M = build(s).gas.getDashboard().leagues[0].matchup;
  const row = M.me.current.rows.find((x) => x.id === 'idp1');
  assert.deepEqual(plain([row.status, row.pts, row.exp]), ['other', 7.5, 7.5]);
  assert.equal(M.me.current.total, 73 + 7.5);
});

test('matchup refresh: one league failing to load still refreshes the others', () => {
  const s = matchupSpec();
  const { gas, league } = build(s);
  const L2 = Object.assign({}, league, { league_id: 'L2', name: 'Second' });
  const orig = gas.sleeper_;
  gas.sleeper_ = (p, fresh) => {
    if (p.includes('/leagues/')) return [league, L2];
    if (p === '/league/L2/rosters') throw new Error('Sleeper API /league/L2/rosters failed (HTTP 500)');
    return orig(p, fresh);
  };
  const got = gas.getMatchups();
  assert.equal(got[0].matchup.me.current.total, 73);
  assert.match(got[1].matchup.error, /HTTP 500/);
});

// ---- trade finder ----------------------------------------------------------------------

/** I have a spare good RB and a weak WR2; they have a spare good WR and a weak RB2. */
const tradeSpec = () => {
  const P = {}, add = (id, pos, team) => { P[id] = [id, pos, team, null, null]; };
  [['m_qb', 'QB', 'KC'], ['m_rb1', 'RB', 'DET'], ['m_rb2', 'RB', 'NYJ'], ['m_rb3', 'RB', 'CHI'], ['m_rb4', 'RB', 'ATL'],
   ['m_wr1', 'WR', 'MIA'], ['m_wr2', 'WR', 'SEA'], ['m_te', 'TE', 'LV'], ['m_k', 'K', 'KC'], ['DET', 'DEF', 'DET'],
   ['t_qb', 'QB', 'BUF'], ['t_rb1', 'RB', 'CLE'], ['t_rb2', 'RB', 'PIT'], ['t_wr1', 'WR', 'IND'], ['t_wr2', 'WR', 'TB'],
   ['t_wr3', 'WR', 'NO'], ['t_wr4', 'WR', 'GB'], ['t_te', 'TE', 'DAL'], ['t_k', 'K', 'BUF'], ['MIN', 'DEF', 'MIN']]
    .forEach(([id, pos, team]) => add(id, pos, team));
  P.DET[0] = 'Detroit'; P.MIN[0] = 'Minnesota';
  const ros = [['m_qb', 40, 'QB5'], ['m_rb1', 5, 'RB2'], ['m_rb2', 15, 'RB6'], ['m_rb3', 20, 'RB8'], ['m_rb4', 25, 'RB10'],
    ['m_wr1', 10, 'WR4'], ['m_wr2', 150, 'WR60'], ['m_te', 60, 'TE5'], ['t_qb', 45, 'QB6'], ['t_rb1', 12, 'RB5'],
    ['t_rb2', 160, 'RB60'], ['t_wr1', 8, 'WR3'], ['t_wr2', 18, 'WR7'], ['t_wr3', 22, 'WR9'], ['t_wr4', 30, 'WR12'],
    ['t_te', 70, 'TE7']];
  return {
    now: Date.parse('2026-10-22T12:00:00Z'), kick: KICK, week: 7, leg: 7, players: P,
    positions: ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'K', 'DEF', 'BN', 'BN', 'BN', 'BN'],
    mine: ['m_qb', 'm_rb1', 'm_rb2', 'm_rb3', 'm_rb4', 'm_wr1', 'm_wr2', 'm_te', 'm_k', 'DET'],
    starters: ['m_qb', 'm_rb1', 'm_rb2', 'm_wr1', 'm_wr2', 'm_te', 'm_rb3', 'm_k', 'DET'],
    others: [['t_qb', 't_rb1', 't_rb2', 't_wr1', 't_wr2', 't_wr3', 't_wr4', 't_te', 't_k', 'MIN']],
    weekly: {
      qb: [['m_qb', 5, 'QB5'], ['t_qb', 6, 'QB6']],
      'ppr-flex': ros.filter((r) => P[r[0]][1] !== 'QB'),
      k: [['m_k', 5, 'K5'], ['t_k', 6, 'K6']],
      dst: [['DET', 3, 'DST3'], ['MIN', 4, 'DST4']],
    },
    ros: { 'ros-ppr-overall': ros, 'ros-k': [['m_k', 5, 'K5'], ['t_k', 6, 'K6']], 'ros-dst': [['DET', 3, 'DST3'], ['MIN', 4, 'DST4']] },
    users: [{ user_id: 'me', display_name: 'me' }, { user_id: 'x0', display_name: 'rival' }],
    settings: { playoff_week_start: 15, playoff_teams: 6, playoff_round_type: 0 },   // playoffs weeks 15-17
    cfg: { max_claims: 0 },
  };
};
const ids = (ps) => plain(ps.map((p) => p.id));

test('trade finder: finds the trade that fixes both teams\' weak spots, you gaining more', () => {
  const { gas } = build(tradeSpec());
  const T = gas.findTrades('L', {});
  assert.ok(T.trades.length > 0, JSON.stringify(T));
  const top = T.trades[0];
  assert.deepEqual(ids(top.give), ['m_rb4']);                   // the spare RB...
  assert.deepEqual(plain(top.get.map((p) => p.pos)), ['WR']);   // ...for one of their WRs
  assert.equal(top.partner.name, 'rival');
  T.trades.forEach((t) => {
    assert.ok(t.me >= t.them && t.them > 0, JSON.stringify(t));
    assert.ok(10 - t.give.length + t.get.length <= 13);   // never over the roster limit
  });
  assert.equal(T.from, 7);
  assert.equal(T.weeks, 11);
});

test('playoff weeks: one round a week, a two-week final, or two weeks a round', () => {
  assert.equal(gasOnly.lastPlayoffWeek_({ playoff_week_start: 15, playoff_teams: 6, playoff_round_type: 0 }), 17);  // Wolfpack
  assert.equal(gasOnly.lastPlayoffWeek_({ playoff_week_start: 16, playoff_teams: 4, playoff_round_type: 1 }), 18);  // SG Bears
  assert.equal(gasOnly.lastPlayoffWeek_({ playoff_week_start: 15, playoff_teams: 4, playoff_round_type: 2 }), 18);
  assert.equal(gasOnly.lastPlayoffWeek_({ playoff_week_start: 14, playoff_teams: 8, playoff_round_type: 0 }), 16);
});

test('trade finder: starred players are never offered; focus and the trade deadline are respected', () => {
  let s = tradeSpec();
  s.cfg = { never_drop: ['m_rb4'] };
  let T = build(s).gas.findTrades('L', {});
  assert.ok(!T.trades.some((t) => t.give.some((p) => p.id === 'm_rb4')));
  T = build(tradeSpec()).gas.findTrades('L', { focus: 'WR' });
  assert.ok(T.trades.length && T.trades.every((t) => t.get.some((p) => p.pos === 'WR')));
  T = build(tradeSpec()).gas.findTrades('L', { focus: 'TE' });
  assert.ok(T.trades.every((t) => t.get.some((p) => p.pos === 'TE')));
  s = tradeSpec();
  s.settings = Object.assign(s.settings, { trade_deadline: 6 });
  T = build(s).gas.findTrades('L', {});
  assert.match(T.closed, /deadline \(week 6\) has passed/);
  s = tradeSpec();
  s.settings.disable_trades = 1;
  T = build(s).gas.findTrades('L', {});
  assert.match(T.closed, /turned off/);
  s = tradeSpec();
  s.settings = Object.assign(s.settings, { trade_deadline: 6 });
  T = build(s).gas.findTrades('L', {});
  assert.match(T.closed, /deadline \(week 6\) has passed/);
  assert.deepEqual(plain(T.trades), []);
});

test('trade finder: open offers on Sleeper are listed and valued', () => {
  const s = tradeSpec();
  s.trades = [{ transaction_id: 'tx1', roster_ids: [1, 2], creator: 'x0', adds: { t_wr3: 1, m_rb4: 2 }, drops: { t_wr3: 2, m_rb4: 1 } }];
  const T = build(s).gas.findTrades('L', {});
  assert.equal(T.offers.length, 1);
  const o = T.offers[0];
  assert.deepEqual([o.sent, ids(o.give), ids(o.get), o.partner.name], [false, ['m_rb4'], ['t_wr3'], 'rival']);
  assert.ok(o.me > 0);
});

test('lineup scoring for trades equals the full assignment, for any slots and multi-position players', () => {
  const sets = [['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'K', 'DEF'], ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'WRRB_FLEX', 'K', 'DEF'],
    ['QB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'FLEX', 'SUPER_FLEX', 'K', 'DEF'], ['QB', 'QB', 'RB', 'WR', 'TE', 'REC_FLEX'],
    ['QB', 'RB', 'WR', 'TE', 'WRRB_FLEX', 'REC_FLEX', 'SUPER_FLEX']];
  // Reference: the app's lineup optimizer (Hungarian assignment) on the same players.
  const exact = (slots, items) => {
    const ids = items.map((x, i) => 'i' + i);
    const cost = (id, slot) => (items[+id.slice(1)].pos.some((p) => gasOnly.SLOT_ELIGIBILITY[slot].includes(p)) ? 100 - items[+id.slice(1)].v : null);
    return gasOnly.optimize_(slots, [], ids, cost).starters.reduce((t, id) => t + (id === '0' ? 0 : items[+id.slice(1)].v), 0);
  };
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const POS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'];
  for (const slots of sets) {
    for (let i = 0; i < 200; i++) {
      const items = Array.from({ length: 4 + Math.floor(rnd() * 14) }, () => {
        const pos = [POS[Math.floor(rnd() * 6)]];
        if (rnd() < 0.2) pos.push(POS[1 + Math.floor(rnd() * 3)]);   // some RB/WR/TE hybrids
        return { pos, v: Math.round(rnd() * 250) / 10 };
      });
      assert.ok(Math.abs(gasOnly.lineupPoints_(slots, items) - exact(slots, items)) < 1e-9, JSON.stringify([slots, items]));
    }
  }
});

// ---- trade offers ----------------------------------------------------------------------

const offerGas = (s) => {
  const b = build(s || tradeSpec()), sent = [];
  b.gas.gql_ = (q, v) => {
    if (/propose_trade/.test(q)) { sent.push({ q, v }); return { propose_trade: { transaction_id: 'tx9', status: 'proposed' } }; }
    throw new Error('unexpected Sleeper call: ' + q.slice(0, 40));
  };
  return Object.assign(b, { sent });
};

test('trade offer: sent the way sleeper.com sends it, and logged', () => {
  const { gas, sent } = offerGas();
  const r = gas.proposeTrade('L', { rosterId: 2, give: ['m_rb4'], get: ['t_wr2'] });
  assert.deepEqual(plain(r), { sent: true, to: 'rival', transactionId: 'tx9' });
  assert.equal(sent.length, 1);
  assert.match(sent[0].q, /^mutation propose_trade/);
  assert.deepEqual(plain(sent[0].v), { k_adds: ['t_wr2', 'm_rb4'], v_adds: [1, 2], k_drops: ['t_wr2', 'm_rb4'], v_drops: [2, 1] });
  const log = gas.getJson_('log')[0];
  assert.match(log.title, /Trade offered to rival/);
  assert.deepEqual(plain(log.lines), ['You give: m_rb4', 'You get: t_wr2']);
});

test('trade offer: refused for starred players, players who moved, past the deadline, over the limit, or a repeat', () => {
  const tries = [
    [(s) => { s.cfg = { never_drop: ['m_rb4'] }; }, { give: ['m_rb4'], get: ['t_wr2'] }, /starred/],
    [() => {}, { give: ['m_rb4'], get: ['t_wr9'] }, /no longer on that roster/],
    [() => {}, { give: ['t_wr1'], get: ['t_wr2'] }, /no longer on your roster/],
    [(s) => { s.settings.trade_deadline = 6; }, { give: ['m_rb4'], get: ['t_wr2'] }, /deadline/],
    [(s) => { s.settings.disable_trades = 1; }, { give: ['m_rb4'], get: ['t_wr2'] }, /turned off/],
    [() => {}, { give: ['m_rb4', 'm_rb4'], get: ['t_wr2'] }, /only be in a trade once/],
    // An IR player frees no active spot: 13 active of 13, giving him and getting one would make 14.
    [(s) => { s.mine.push('m_x1', 'm_x2', 'm_x3'); s.reserve = ['m_rb4']; Object.assign(s.players, { m_x1: ['m_x1', 'WR', 'KC', null, null],
      m_x2: ['m_x2', 'WR', 'KC', null, null], m_x3: ['m_x3', 'WR', 'KC', null, null], m_x4: ['m_x4', 'WR', 'KC', null, null] });
      s.mine.push('m_x4'); s.positions.push('IR'); }, { give: ['m_rb4'], get: ['t_wr2'] }, /roster limit/],
    [(s) => { s.positions = s.positions.slice(0, 10); }, { give: ['m_rb4'], get: ['t_wr2', 't_wr3'] }, /roster limit/],
    [(s) => { s.trades = [{ roster_ids: [1, 2], adds: { t_wr2: 1, m_rb4: 2 } }]; }, { give: ['m_rb4'], get: ['t_wr2'] }, /already open/],
    [() => {}, { give: [], get: ['t_wr2'] }, /both sides/],
    [() => {}, { rosterId: 1, give: ['m_rb4'], get: ['t_wr2'] }, /not in this league/],
  ];
  for (const [edit, offer, err] of tries) {
    const s = tradeSpec();
    edit(s);
    const { gas, sent } = offerGas(s);
    assert.throws(() => gas.proposeTrade('L', Object.assign({ rosterId: 2 }, offer)), err);
    assert.equal(sent.length, 0);
  }
});

test('the autopilot never offers trades', () => {
  const s = tradeSpec();
  const { gas, sent } = offerGas(s);
  gas.setMode('auto');
  gas.saveLeagueSettings('L', { auto_waivers: true });
  gas.tick();
  assert.equal(sent.length, 0);
});

// ---- injury badges ------------------------------------------------------------------------

test('the player list keeps the injury and body part (only for injured players)', () => {
  const text = JSON.stringify({
    1: { full_name: 'Hurt Guy', position: 'WR', team: 'KC', injury_status: 'Questionable', injury_body_part: 'Hamstring', fantasy_positions: ['WR'] },
    2: { full_name: 'Fine Guy', position: 'RB', team: 'KC', injury_status: null, injury_body_part: 'Ankle', fantasy_positions: ['RB'] },
  });
  const out = plain(gasOnly.parsePlayers_(text));
  assert.deepEqual(out['1'], ['Hurt Guy', 'WR', 'KC', 'Questionable', null, 'Hamstring']);
  assert.deepEqual(out['2'], ['Fine Guy', 'RB', 'KC', null, null, null]);
});

test('every player view carries Sleeper\'s injury status: lineup, bench, matchup, pickups', () => {
  const s = matchupSpec();
  s.players.rb2 = ['rb2', 'RB', 'NYJ', 'Questionable', null, 'Hamstring'];
  s.players.te1[5] = 'Knee';
  const lg = build(s).gas.getDashboard().leagues[0];
  const view = (list, id) => list.find((p) => p.id === id);
  const rb2 = view(lg.lineup.lineup.concat(lg.lineup.bench), 'rb2');
  assert.deepEqual(plain([rb2.injury, rb2.injuryDetail, rb2.why]), ['Questionable', 'Hamstring', null]);  // Q plays, but shows
  const te1 = view(lg.lineup.lineup.concat(lg.lineup.bench), 'te1');
  assert.deepEqual(plain([te1.injury, te1.injuryDetail, te1.why]), ['Out', 'Knee', 'Out']);
  const row = lg.matchup.me.current.rows.find((x) => x.id === 'rb2');
  assert.equal(row.injury, 'Questionable');
  const healthy = lg.lineup.lineup.find((p) => p.id === 'qb1');
  assert.equal(healthy.injury, null);
  const claims = (lg.freeAgents.claims || []).concat(lg.waivers.claims || []);
  claims.forEach((c) => { assert.ok('injury' in c.add); if (c.drop) assert.ok('injury' in c.drop); });
});

// ---- superflex: QB lean from projections ----------------------------------------------------

/**
 * Superflex league (6-pt pass TD); qb2 and wr2 compete for SUPER_FLEX. 40 RB/WR set the points-per-rank
 * scale; 8 other QBs (ECR 33-61) are projected like a RB/WR ranked ``boost`` spots better.
 */
const sfSpec = (qb2Rank, boost) => {
  const s = base();
  s.scoring = { rec: 1, pass_td: 6 };
  s.positions = ['QB', 'RB', 'WR', 'SUPER_FLEX', 'BN', 'BN', 'BN'];
  s.players.qb2 = ['qb2', 'QB', 'BUF', null, null];
  s.mine = ['qb1', 'rb1', 'wr1', 'qb2', 'wr2', 'rb2'];
  s.starters = ['qb1', 'rb1', 'wr1', 'wr2'];
  s.others = [[]];
  const at = (rank) => 22 - (rank / 2 - 1) * 0.35;   // a RB/WR ranked ``rank`` projects this
  const rows = [['qb1', 1, 'QB1'], ['rb1', 3, 'RB2'], ['wr1', 5, 'WR3'], ['qb2', qb2Rank, 'QB20'], ['wr2', 35, 'WR20'], ['rb2', 60, 'RB30']];
  s.proj = { qb1: 26, rb1: 21, wr1: 20, qb2: 15, wr2: 13, rb2: 10 };
  for (let i = 1; i <= 40; i++) {
    const id = 'f' + i;
    s.players[id] = [id, i % 2 ? 'RB' : 'WR', 'TB', null, null];
    rows.push([id, i * 2, (i % 2 ? 'RB' : 'WR') + i]);
    s.proj[id] = at(i * 2);
  }
  [32, 36, 40, 44, 48, 52, 56, 59].forEach((r, i) => {
    const id = 'q' + i;
    s.players[id] = [id, 'QB', 'NO', null, null];
    rows.push([id, r + 1, 'QB' + (i + 3)]);
    s.proj[id] = at(r + 1 - boost);
  });
  s.weekly['ppr-superflex'] = rows;
  s.cfg = { max_claims: 0, stream_k_def: false, min_roster: { WR: 1, RB: 1 } };
  return s;
};
const sf = (s) => build(s).gas.getDashboard().leagues[0].lineup.starters[3];

test('superflex lean: the gap between QBs and RB/WR/TE projected for the same points', () => {
  for (const boost of [0, 12, 30]) {
    const lean = build(sfSpec(60, boost)).gas.withLeague_('L', (lg) => lg.superflexLean_());
    assert.ok(Math.abs(lean - boost) < 3, `boost ${boost}: lean ${lean}`);   // the fixture's own RB/WR shift the scale a little
  }
});

test('superflex: when QBs project well above their ECR, a lower-ranked QB starts over the WR', () => {
  // QBs project 30 spots better than ECR says: qb2 (ECR 60) counts as 30, ahead of wr2 (35).
  // The old fixed lean of 20 would have made him 40 and started wr2.
  assert.equal(sf(sfSpec(60, 30)), 'qb2');
});

test('superflex: when QBs project no better than their ECR, the WR starts', () => {
  // No gap this week: qb2 (ECR 45) stays 45, behind wr2 (35). The old fixed lean (25) would have started him.
  assert.equal(sf(sfSpec(45, 0)), 'wr2');
});

test('superflex: without projections the fixed lean still applies', () => {
  const { gas } = build(sfSpec(45, 0));
  gas.projectedPoints_ = () => { throw new Error('Sleeper projections failed (HTTP 500)'); };
  assert.equal(gas.getDashboard().leagues[0].lineup.starters[3], 'qb2');   // 45 - 20 = 25 beats wr2's 35
});

test('superflex: two starting QBs are not swapped between QB and SUPER_FLEX for nothing', () => {
  const s = sfSpec(20, 12);
  s.starters = ['qb2', 'rb1', 'wr1', 'qb1'];   // the better QB already sits in SUPER_FLEX
  const L = build(s).gas.getDashboard().leagues[0].lineup;
  assert.deepEqual([L.starters[0], L.starters[3], L.changes], ['qb2', 'qb1', 0]);
});
