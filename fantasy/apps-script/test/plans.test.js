// Targeted plan tests from an independent review: each one is a situation the planner or the
// safety check once got wrong. The base league (test/fixture.js) is a 1QB team on a
// Thursday after the waiver run whose only TE (te1) is Out; rb3 and wr3 are the cheap bench.
const test = require('node:test');
const assert = require('node:assert/strict');
const { build, claims, plain, base } = require('./fixture');

const TUESDAY = Date.parse('2026-10-20T17:00:00Z');  // claim window, before the waiver run (leg 6)
const page = (s) => build(s).gas.getDashboard().leagues[0];
const shownOf = (plan) => plan.claims.map((c) => [c.add.id, c.drop ? c.drop.id : null, c.bid == null ? null : c.bid]);
const ids = (plan) => plan.claims.map((c) => c.add.id);
const drops = (plan) => plan.claims.filter((c) => c.drop).map((c) => c.drop.id);
const tuesday = (s) => { s.now = TUESDAY; s.leg = 6; return s; };
const auto = (gas, cfg) => { gas.setMode('auto'); gas.saveLeagueSettings('L', Object.assign({ auto_waivers: true }, cfg || {})); };
test('claims pending on Sleeper leave room for a fill-in: no false safety alarm, the TE gets picked up', () => {
  const s = base();
  s.others = [[]];
  s.clears = { p1: s.now / 1000 + 86400, p2: s.now / 1000 + 86400, p3: s.now / 1000 + 86400 };
  s.pending = [{ adds: { p1: 1 }, drops: { wr3: 1 } }, { adds: { p2: 1 }, drops: { wr3: 1 } }, { adds: { p3: 1 }, drops: { wr3: 1 } }];
  const lg = page(s);
  assert.deepEqual(claims(lg.freeAgents), [['cover', 'te_fa', 'rb3']]);
  assert.deepEqual(plain(lg.safety), []);
  const { gas, writes } = build(s);
  auto(gas, { max_claims: 2 });
  gas.tick();
  assert.deepEqual(writes, [['fa', 'te_fa', 'rb3']]);
});

test('after the autopilot submits its claims, the page shows no safety alarm', () => {
  const s = tuesday(base());
  s.others = [[]];
  s.cfg = { max_claims: 1 };
  const { gas, writes } = build(s);
  auto(gas, { max_claims: 1 });
  gas.tick();
  assert.deepEqual(writes, [['claim', 'te_fa', 'wr3', null]]);
  s.pending = [{ adds: { te_fa: 1 }, drops: { wr3: 1 } }];
  s.now += 3600e3;
  const lg = page(s);
  assert.deepEqual(claims(lg.waivers), []);
  assert.deepEqual(plain(lg.safety), []);
});

test('free-agent upgrades and fill-ins share the bench: nothing just picked up gets dropped', () => {
  const s = base();
  s.mutate = true;
  auto(build(s).gas, { max_claims: 2 });
  const all = [];
  for (const t of ['2026-10-22T12:30:00Z', '2026-10-24T12:00:00Z', '2026-10-24T12:30:00Z']) {
    s.now = Date.parse(t);
    const b = build(s);
    b.gas.tick();
    all.push(...b.writes);
  }
  const added = all.filter((w) => w[0] === 'fa').map((w) => w[1]);
  const dropped = all.filter((w) => w[0] === 'fa').map((w) => w[2]);
  assert.deepEqual(added.sort(), ['te_fa', 'wr_fa']);
  assert.ok(!dropped.some((d) => added.includes(d)), JSON.stringify(all));
  assert.ok(s._roster.starters.includes('te_fa'));  // and he starts at TE
});

test('a drop never leaves this week\'s lineup with a hole', () => {
  // te1 (TE1, kept for the rest of the season) is on bye; te2 starts in his place.
  const mk = (faPlays) => {
    const s = base();
    s.players.te1[3] = null;
    s.players.te2 = ['te2', 'TE', 'DAL', null, null];
    s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'te2', 'rb3'];
    s.starters = ['qb1', 'rb1', 'wr1', 'te2', 'rb2', 'k1', 'DET'];
    s.weekly['ppr-flex'] = s.weekly['ppr-flex'].filter((r) => r[0] !== 'te1' && r[0] !== 'te_fa')
      .concat([['te1', 40, 'TE5', null, true], ['te2', 80, 'TE15'], ['te_fa', 70, 'TE12', undefined, !faPlays]]);
    s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].filter((r) => r[0] !== 'rb3').concat([['te2', 300, 'TE30'], ['rb3', 120, 'RB40']]);
    s.cfg = { max_claims: 2 };
    return s;
  };
  // te_fa is better for the rest of the season but also on bye: te2 must stay this week.
  let lg = page(mk(false));
  assert.ok(!drops(lg.freeAgents).includes('te2'), JSON.stringify(claims(lg.freeAgents)));
  assert.deepEqual(plain(lg.safety), []);
  // te_fa plays: swapping te2 for him is fine, and he starts.
  const s = mk(true);
  s.mutate = true;
  lg = page(s);
  assert.deepEqual(claims(lg.freeAgents), [['upgrade', 'te_fa', 'te2']]);
  const { gas } = build(s);
  auto(gas, { max_claims: 2 });
  s.now = Date.parse('2026-10-24T12:00:00Z');
  build(s).gas.tick();
  assert.equal(s._roster.starters[3], 'te_fa');
});

test('an upgrade that fills the empty spot is not followed by a second fill-in', () => {
  const s = base();
  s.players.te_up = ['te_up', 'TE', 'GB', null, null];
  s.weekly['ppr-flex'].push(['te_up', 50, 'TE8']);
  s.ros['ros-ppr-overall'].push(['te_up', 100, 'TE9']);
  s.cfg = { max_claims: 1 };
  const lg = page(s);
  assert.deepEqual(claims(lg.freeAgents), [['upgrade', 'te_up', 'wr3']]);
  assert.match(lg.freeAgents.notes.join(' '), /te_up is an upgrade and also fills the TE spot/);
});

test('a kicker on bye who is not top-12 is swapped for the fill-in, not a bench player', () => {
  const mk = (now, leg) => {
    const s = base();
    s.now = Date.parse(now); s.leg = leg;
    s.players.te1[3] = null;
    s.weekly.k = [['k1', 30, 'K30', null, true], ['k_fa', 2, 'K2']];
    s.ros['ros-k'] = [['k1', 25, 'K25'], ['k_fa', 20, 'K20']];
    s.cfg = { max_claims: 0 };
    return s;
  };
  assert.deepEqual(claims(page(mk('2026-10-20T17:00:00Z', 6)).waivers), [['cover', 'k_fa', 'k1']]);
  assert.deepEqual(claims(page(mk('2026-10-22T12:00:00Z', 7)).freeAgents), [['cover', 'k_fa', 'k1']]);
});

test('a top kicker on bye already covered: a better streamer replaces the cover, never a third kicker', () => {
  for (const [now, leg, plan] of [['2026-10-20T17:00:00Z', 6, 'waivers'], ['2026-10-22T12:00:00Z', 7, 'freeAgents']]) {
    const s = base();
    s.now = Date.parse(now); s.leg = leg;
    s.players.te1[3] = null;
    s.players.k2 = ['k2', 'K', 'DAL', null, null];
    s.mine = s.mine.filter((p) => p !== 'wr3').concat('k2');
    s.weekly.k = [['k1', 1, 'K1', null, true], ['k2', 15, 'K15'], ['k_fa', 2, 'K2']];
    s.ros['ros-k'] = [['k1', 3, 'K3'], ['k2', 25, 'K25'], ['k_fa', 20, 'K20']];
    s.cfg = { max_claims: 0 };
    assert.deepEqual(claims(page(s)[plan]), [['stream', 'k_fa', 'k2']]);
  }
});

test('a kicker who plays (starred or not) is never joined by a worse one in an open spot', () => {
  const mk = (star) => {
    const s = tuesday(base());
    s.players.te1[3] = null;
    s.positions = s.positions.concat('BN');
    s.weekly.k = [['k1', 1, 'K1'], ['k_fa', 9, 'K9']];
    s.cfg = { max_claims: 0, never_drop: star ? ['k1'] : [] };
    return s;
  };
  assert.deepEqual(claims(page(mk(false)).waivers), []);
  assert.deepEqual(claims(page(mk(true)).waivers), []);
  const s = mk(true);
  s.now = Date.parse('2026-10-22T12:00:00Z'); s.leg = 7;
  assert.deepEqual(claims(page(s).freeAgents), []);
});

test('if Sleeper can\'t say who is on waivers, no claims are planned or sent', () => {
  const s = base();
  s.players.te1[3] = null;
  const { gas, writes } = build(s);
  gas.waiverClears_ = () => { throw new Error('Cannot query field "league_players"'); };
  const lg = gas.getDashboard().leagues[0];
  assert.match(lg.freeAgents.error, /league_players/);
  assert.deepEqual(claims(lg.waivers), []);
  assert.match(lg.waivers.notes.join(' '), /Couldn't read who's on waivers/);
  gas.submitClaims('L', []);
  assert.deepEqual(writes, []);
  // And the safety check refuses claims it can't verify.
  const safety = gas.withLeague_('L', (l) => {
    const res = l.evaluate({ waivers: true });
    res.waivers.claims = [{ kind: 'upgrade', add: { id: 'wr_fa', name: 'wr_fa', rank: 170 }, drop: { id: 'wr3', name: 'wr3', rank: 260 } }];
    return plain(gas.checkPlans_(l, res));
  });
  assert.ok(safety.some((x) => /Can't check on Sleeper whether wr_fa is still on waivers/.test(x)), JSON.stringify(safety));
});

test('a failed claim submission is retried on the next check', () => {
  const s = tuesday(base());
  s.now = Date.parse('2026-10-20T16:30:00Z');
  s.players.te1[3] = null;
  let b = build(s);
  auto(b.gas);
  b.gas.submitClaim_ = () => { throw new Error('Sleeper returned HTTP 502'); };
  b.gas.tick();
  assert.equal(b.gas.getJson_('lastTick').status, 'error');
  assert.match(b.gas.getJson_('lastTick').msg, /2 failed \(retrying\)/);
  const sent = [];
  for (const t of ['2026-10-20T17:00:00Z', '2026-10-20T17:30:00Z']) {
    s.now = Date.parse(t);
    b = build(s);
    b.gas.submitClaim_ = (...a) => { sent.push(a.slice(3)); s.pending = (s.pending || []).concat({ adds: { [a[3]]: 1 }, drops: a[4] ? { [a[4]]: 1 } : {} }); };
    b.gas.tick();
  }
  assert.deepEqual(plain(sent), [['wr_fa', 'wr3', null], ['rb_fa', 'rb3', null]]);  // once each
});

test('Submit claims accepts the waiver plan the page showed (made after the free-agent plan)', () => {
  const s = base();
  s.players.te1[3] = null;
  s.players.wr4 = ['wr4', 'WR', 'DAL', null, null];
  s.positions = s.positions.concat('BN');
  s.mine = s.mine.concat('wr4');
  s.weekly['ppr-flex'].push(['wr4', 99, 'WR50']);
  s.ros['ros-ppr-overall'].push(['wr4', 280, 'WR95']);
  s.others = [['p2', 'p3']];
  s.clears = { p1: s.now / 1000 + 86400 };
  s.cfg = { max_claims: 3 };
  s.ros['ros-ppr-overall'].find((r) => r[0] === 'te_fa')[1] = 225;
  const { gas, writes } = build(s);
  const lg = gas.getDashboard().leagues[0];
  assert.equal(lg.freeAgents.claims.length, 2);
  assert.deepEqual(plain(ids(lg.waivers)), ['p1']);
  assert.ok(!drops(lg.waivers).some((d) => drops(lg.freeAgents).includes(d)));
  const res = gas.submitClaims('L', shownOf(lg.waivers));
  assert.ok(!res.waivers.changed);
  assert.deepEqual(writes.map((w) => w[1]), ['p1']);
});

test('rolling waivers near the front of the line: no marginal claim just because a spot is open', () => {
  const s = tuesday(base());
  s.players.te1[3] = null;
  s.settings = { waiver_type: 0 }; s.rosterSettings = { waiver_position: 1 };
  s.mine = s.mine.filter((p) => p !== 'wr3');   // one open bench spot
  s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].filter((r) => !['wr_fa', 'rb_fa', 'te_fa'].includes(r[0])).concat([['wr_fa', 240, 'WR85']]);
  s.cfg = { max_claims: 2, stream_k_def: false };
  assert.deepEqual(claims(page(s).waivers), []);
});

test('position minimums count the claims already pending', () => {
  // WR minimum is 2 (one WR slot + 1). Pending claims drop wr3 and rb3 for running backs,
  // so wr1 and wr2 must both stay.
  const s = tuesday(base());
  s.players.te1[3] = null;
  s.players.te_up = ['te_up', 'TE', 'GB', null, null];
  s.weekly['ppr-flex'].push(['te_up', 45, 'TE7']);
  s.ros['ros-ppr-overall'].push(['te_up', 35, 'TE3']);
  s.others = [['p2', 'p3', 'wr_fa', 'te_fa']];
  s.pending = [{ adds: { p1: 1 }, drops: { wr3: 1 } }, { adds: { rb_fa: 1 }, drops: { rb3: 1 } }];
  s.cfg = { max_claims: 3, stream_k_def: false };
  const lg = page(s);
  assert.ok(!drops(lg.waivers).includes('wr2'), JSON.stringify(claims(lg.waivers)));
  assert.ok(!drops(lg.waivers).includes('wr1'));
});

test('free-agent moves and pending claims together never overfill the roster', () => {
  const s = base();
  s.players.te1[3] = null;
  s.positions = s.positions.concat('BN');           // 11 spots, 10 players, one no-drop claim pending
  s.others = [['p3']];
  s.clears = { p1: s.now / 1000 + 86400, p2: s.now / 1000 + 86400 };
  s.pending = [{ adds: { p1: 1 }, drops: {} }];
  s.ros['ros-ppr-overall'].find((r) => r[0] === 'rb_fa')[1] = 225;
  s.ros['ros-ppr-overall'].find((r) => r[0] === 'te_fa')[1] = 255;
  s.cfg = { max_claims: 3 };
  const lg = page(s);
  assert.ok(lg.freeAgents.claims.every((c) => c.drop) && lg.waivers.claims.every((c) => c.drop));
  assert.deepEqual(plain(lg.safety), []);
});

// ---- The safety check on its own: plans the planner should never make get blocked ----------

const bad = (s, edit) => {
  const { gas } = build(s);
  return gas.withLeague_('L', (l) => {
    const res = l.evaluate({ lineup: true, freeAgents: true, waivers: true });
    const v = (pid, rank) => ({ id: pid, name: pid, rank: rank || null });
    edit(res, (kind, add, drop) => ({ kind, add: v(add), drop: drop ? v(drop) : null }));
    return plain(gas.checkPlans_(l, res));
  });
};

test('safety: a fill-in may not drop someone just picked up', () => {
  const s = base();
  s.tx = { 7: [{ status: 'complete', status_updated: s.now - 3600e3, adds: { wr3: 1 }, drops: null }] };
  const out = bad(s, (res, c) => { res.freeAgents.claims = [c('cover', 'te_fa', 'wr3')]; res.waivers.claims = []; });
  assert.ok(out.some((x) => /wr3 was just picked up and would be dropped for a one-week pickup/.test(x)), JSON.stringify(out));
});

test('safety: moves that leave a starting spot with nobody who can play are blocked', () => {
  const s = base();
  s.players.te1[3] = null;
  s.players.te2 = ['te2', 'TE', 'DAL', null, null];
  s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'te2', 'rb3'];
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].filter((r) => r[0] !== 'te1').concat([['te1', 40, 'TE5', null, true], ['te2', 80, 'TE15']]);
  const out = bad(s, (res, c) => { res.freeAgents.claims = [c('upgrade', 'wr_fa', 'te2')]; res.waivers.claims = []; });
  assert.ok(out.some((x) => /starting spot this week with nobody who can play/.test(x)), JSON.stringify(out));
});

test('safety: the weekly limit counts upgrades against the room pending claims leave, not fill-ins', () => {
  const s = base();
  s.others = [[]];
  s.clears = { p1: s.now / 1000 + 86400 };
  s.pending = [{ adds: { p1: 1 }, drops: { wr3: 1 } }];
  s.cfg = { max_claims: 2 };
  let out = bad(s, (res, c) => { res.freeAgents.claims = [c('upgrade', 'wr_fa', 'rb3'), c('upgrade', 'rb_fa', 'wr2')]; res.waivers.claims = []; });
  assert.ok(out.some((x) => /More upgrades than your limit of 2/.test(x)), JSON.stringify(out));
  out = bad(s, (res, c) => { res.freeAgents.claims = [c('upgrade', 'wr_fa', 'rb3'), c('cover', 'te_fa', 'wr2')]; res.waivers.claims = []; });
  assert.ok(!out.some((x) => /More upgrades/.test(x)), JSON.stringify(out));
});
