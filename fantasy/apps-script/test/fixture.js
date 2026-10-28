// A small configurable league for targeted plan tests (test/plans.test.js): one roster of
// mine, rankings and Sleeper state given per test. Network functions are replaced; with
// ``spec.mutate`` free-agent adds and lineup saves change the fake roster.
const { loadGas } = require('../dev/gas-stub');

const plain = (x) => JSON.parse(JSON.stringify(x));
// spec: { now (ms), week, leg, players: {id: [name,pos,team,inj,fpos]}, weekly: {slug: [[id, rank, posRank, kickoffSec|null, byeWeek?]]},
//         ros: {slug: [[id, rank, posRank]]}, positions, mine: [...], starters: [...], others: [[...]], settings, rosterSettings,
//         pending: [{adds, drops}], clears: {}, tx: {leg: [...]}, cfg: {},
//         matchups: [...], users: [...], proj: {id: points}, games: {team: {status, left, clock}}, trades: [pending offers] }
function build(spec) {
  const writes = [];
  const P = spec.players;
  const row = (week) => ([id, rank, pr, ko, bye]) => {
    const pos = P[id][1] === 'DEF' ? 'DST' : P[id][1];
    const isBye = bye === true;
    return [id, id, pos, P[id][2], rank, pr, isBye ? String(week) : '14', isBye ? '' : 'vs. X',
            isBye ? null : (ko === undefined ? spec.kick : ko), (ko || spec.kick) * 1000 <= spec.now && !isBye ? 'inprogress' : 'created'];
  };
  const lists = {};
  Object.entries(spec.weekly).forEach(([slug, rows]) => { lists[slug] = { week: spec.week, label: slug, players: rows.map(row(spec.week)) }; });
  Object.entries(spec.ros).forEach(([slug, rows]) => { lists[slug] = { week: 0, label: slug, players: rows.map(([id, r, pr]) => row(0)([id, r, pr, null])).map((x) => { x[8] = null; x[9] = null; x[7] = 'vs. X'; x[6] = '14'; return x; }) }; });
  if (!lists['ppr-superflex']) lists['ppr-superflex'] = { week: spec.week, label: 'sf', players: [].concat((lists.qb || {}).players || [], (lists['ppr-flex'] || {}).players || []) };
  const league = { league_id: 'L', name: 'Test', status: 'in_season', roster_positions: spec.positions,
                   scoring_settings: spec.scoring || { rec: 1 }, settings: Object.assign({ waiver_type: 1, waiver_day_of_week: 2, leg: spec.leg }, spec.settings || {}) };
  const roster = spec._roster || { roster_id: 1, owner_id: 'me', settings: spec.rosterSettings || { waiver_position: 5 }, players: spec.mine.slice(),
                   starters: spec.starters.slice(), reserve: spec.reserve || [], taxi: [] };
  spec._roster = roster;
  const others = spec._others || (spec.others || [[]]).map((pl, i) => ({ roster_id: i + 2, owner_id: 'x' + i, players: pl, starters: [], settings: {} }));
  spec._others = others;
  const gas = loadGas({ now: () => spec.now, props: spec.props, file: process.env.GAS_CODE });  // GAS_CODE: test another Code.gs
  spec.props = gas.__props._data;
  gas.fpList_ = (slug) => { if (!lists[slug]) throw new Error('no list ' + slug); return lists[slug]; };
  gas.playersSlim_ = () => P;
  gas.fpToSleeper_ = () => Object.fromEntries(Object.keys(P).map((k) => [k, k]));
  gas.sleeper_ = (p) => {
    if (p === '/state/nfl') return { week: spec.week, league_season: '2026' };
    if (p.includes('/leagues/')) return [league];
    if (p.endsWith('/rosters')) return plain([roster, ...others]);
    const m = /\/matchups\/(\d+)$/.exec(p);
    if (m) return spec.matchups ? plain(spec.matchups) : [{ roster_id: 1, starters: roster.starters.slice() }];
    if (p.endsWith('/users')) return spec.users || [];
    const t = /\/transactions\/(\d+)$/.exec(p);
    if (t) return (spec.tx || {})[t[1]] || [];
    return null;
  };
  gas.pendingWaivers_ = () => (spec.pending || []).map((x) => Object.assign({ roster_ids: [1] }, x));
  gas.pendingTrades_ = () => plain(spec.trades || []);
  gas.projectedPoints_ = () => Object.assign({}, spec.proj || {});   // Sleeper projections, already scored
  gas.gameStates_ = () => Object.assign({}, spec.games || {});
  gas.latestBuild_ = () => null;
  gas.waiverClears_ = () => Object.assign({}, spec.clears || {});
  gas.addFreeAgent_ = (...a) => {
    const add = a[3], drop = a[4];
    writes.push(['fa', add, drop]);
    if (spec.mutate) {
      if (drop) { roster.players = roster.players.filter((x) => x !== drop); roster.starters = roster.starters.map((x) => (x === drop ? '0' : x)); spec.clears = Object.assign(spec.clears || {}, { [drop]: spec.now / 1000 + 2 * 86400 }); }
      others.forEach((o) => { o.players = o.players.filter((x) => x !== add); });
      roster.players.push(add);
      spec.tx = spec.tx || {}; (spec.tx[spec.leg] = spec.tx[spec.leg] || []).push({ status: 'complete', status_updated: spec.now, adds: { [add]: 1 }, drops: drop ? { [drop]: 1 } : null });
    }
    return { adds: { [add]: 1 }, status: 'complete' };
  };
  gas.setStarters_ = (...a) => { writes.push(['starters', ...a.slice(3)]); if (spec.mutate) roster.starters = Array.from(a[3]); };
  gas.submitClaim_ = (...a) => writes.push(['claim', ...a.slice(3)]);
  if (!gas.__props.getProperty('token')) {
    gas.__props.setProperty('token', 'a.b.c');
    gas.putJson_('user', { user_id: 'me', display_name: 'me' });
    if (spec.cfg) gas.saveLeagueSettings('L', spec.cfg);
  }
  return { gas, writes, league, roster, lists };
}
const claims = (plan) => (plan ? plain(plan.claims.map((c) => [c.kind, c.add.id, c.drop && c.drop.id])) : null);

// A 1QB league base spec used by several repros.
const NOW = Date.parse('2026-10-22T12:00:00Z');       // Thursday, after Wednesday's waiver run
const KICK = Date.parse('2026-10-25T17:00:00Z') / 1000; // Sunday
function base() {
  const players = {
    qb1: ['qb1', 'QB', 'KC', null, null], rb1: ['rb1', 'RB', 'DET', null, null], rb2: ['rb2', 'RB', 'NYJ', null, null],
    wr1: ['wr1', 'WR', 'MIA', null, null], wr2: ['wr2', 'WR', 'SEA', null, null], te1: ['te1', 'TE', 'LV', 'Out', null],
    k1: ['k1', 'K', 'KC', null, null], DET: ['Detroit', 'DEF', 'DET', null, null], rb3: ['rb3', 'RB', 'CHI', null, null],
    wr3: ['wr3', 'WR', 'MIN', null, null],
    te_fa: ['te_fa', 'TE', 'ATL', null, null], wr_fa: ['wr_fa', 'WR', 'TB', null, null], rb_fa: ['rb_fa', 'RB', 'NO', null, null],
    p1: ['p1', 'RB', 'CLE', null, null], p2: ['p2', 'WR', 'PIT', null, null], p3: ['p3', 'WR', 'IND', null, null],
    k_fa: ['k_fa', 'K', 'TB', null, null],
  };
  return {
    now: NOW, kick: KICK, week: 7, leg: 7, players,
    positions: ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF', 'BN', 'BN', 'BN'],
    mine: ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'rb3', 'wr3'],
    starters: ['qb1', 'rb1', 'wr1', 'te1', 'rb2', 'k1', 'DET'],
    others: [['p1', 'p2', 'p3']],
    weekly: {
      qb: [['qb1', 5, 'QB5']],
      'ppr-flex': [['rb1', 3, 'RB2'], ['wr1', 6, 'WR3'], ['rb2', 20, 'RB10'], ['wr2', 25, 'WR12'], ['te1', 40, 'TE5'],
                   ['te_fa', 70, 'TE12'], ['wr_fa', 60, 'WR30'], ['rb_fa', 65, 'RB30'], ['rb3', 90, 'RB40'], ['wr3', 95, 'WR45'],
                   ['p1', 30, 'RB15'], ['p2', 35, 'WR18'], ['p3', 36, 'WR19']],
      k: [['k1', 10, 'K10'], ['k_fa', 2, 'K2']],
      dst: [['DET', 3, 'DST3']],
    },
    ros: {
      'ros-ppr-overall': [['rb1', 5, 'RB2'], ['wr1', 9, 'WR3'], ['qb1', 40, 'QB4'], ['rb2', 50, 'RB18'], ['wr2', 60, 'WR25'],
                          ['te1', 80, 'TE6'], ['p1', 70, 'RB25'], ['p2', 75, 'WR30'], ['p3', 76, 'WR31'],
                          ['wr_fa', 170, 'WR60'], ['rb_fa', 175, 'RB60'], ['te_fa', 190, 'TE14'], ['rb3', 230, 'RB75'], ['wr3', 260, 'WR90']],
      'ros-k': [['k1', 12, 'K12'], ['k_fa', 20, 'K20']],
      'ros-dst': [['DET', 3, 'DST3']],
    },
    cfg: { max_claims: 2 },
  };
}
module.exports = { build, claims, plain, base, NOW, KICK };
