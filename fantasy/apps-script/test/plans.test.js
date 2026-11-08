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

// ---- Second review: pending claims after the waiver run, which spot a move empties, locks --

test('after the waiver run, a pending claim neither hides this week\'s hole nor invents one', () => {
  // A TE claim pending for next week's run: this week's TE spot still needs a fill-in now.
  let s = base();
  s.players.te_w = ['te_w', 'TE', 'GB', null, null];
  s.weekly['ppr-flex'].push(['te_w', 50, 'TE8']);
  s.ros['ros-ppr-overall'].push(['te_w', 100, 'TE9']);
  s.clears = { te_w: s.now / 1000 + 6 * 86400 };
  s.pending = [{ adds: { te_w: 1 }, drops: { wr3: 1 } }];
  let lg = page(s);
  assert.ok(lg.freeAgents.claims.some((c) => c.add.id === 'te_fa'), JSON.stringify(claims(lg.freeAgents)));
  assert.ok(!drops(lg.freeAgents).includes('wr3'));  // the pending claim drops him
  // A kicker claim pending (that kicker is on bye this week, k1 still plays): nothing to fill.
  s = base();
  s.players.te1[3] = null;
  s.players.k_w = ['k_w', 'K', 'GB', null, null];
  s.weekly.k = [['k1', 10, 'K10'], ['k_fa', 8, 'K8'], ['k_w', 1, 'K1', null, true]];
  s.ros['ros-k'] = [['k1', 12, 'K12'], ['k_fa', 20, 'K20'], ['k_w', 2, 'K2']];
  s.clears = { k_w: s.now / 1000 + 6 * 86400 };
  s.pending = [{ adds: { k_w: 1 }, drops: { k1: 1 } }];
  s.cfg = { max_claims: 0 };
  lg = page(s);
  assert.deepEqual(claims(lg.freeAgents), []);
});

test('an upgrade never trades one empty spot for a harder one (drops the only QB who plays to fill FLEX)', () => {
  const mk = (cfg) => {
    const s = base();
    s.players.te1[3] = null;
    s.players.qb1[2] = 'NYG';                         // on bye
    s.players.qb2 = ['qb2', 'QB', 'DAL', null, null];
    s.players.rb2[3] = 'Out'; s.players.wr2[3] = 'Out'; s.players.wr3[3] = 'Out';
    s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'qb2', 'wr3'];
    s.starters = ['qb1', 'rb1', 'wr1', 'te1', 'rb2', 'k1', 'DET'];
    s.weekly.qb = [['qb1', 5, 'QB5', null, true], ['qb2', 20, 'QB20']];
    s.ros['ros-ppr-overall'].push(['qb2', 300, 'QB32']);
    s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].map((r) => (r[0] === 'wr3' ? ['wr3', 300, 'WR99'] : r));
    s.cfg = Object.assign({ max_claims: 2, stream_k_def: false }, cfg);
    return s;
  };
  for (const cfg of [{ never_drop: ['wr3'] }, { cover_byes: false }]) {
    const lg = page(mk(cfg));
    assert.ok(!drops(lg.freeAgents).includes('qb2'), JSON.stringify(claims(lg.freeAgents)));
    assert.deepEqual(plain(lg.safety), []);
  }
});

test('before the waiver run, no claim relies on an earlier claim going through', () => {
  // rb2 is the only RB who can play; dropping him is only safe if the rb_fa claim wins.
  const s = tuesday(base());
  s.players.te1[3] = null;
  s.players.rb1[3] = 'Out'; s.players.rb3[3] = 'Out';
  s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].map((r) => (r[0] === 'rb2' ? ['rb2', 280, 'RB80']
    : r[0] === 'wr3' ? ['wr3', 300, 'WR99'] : r[0] === 'rb_fa' ? ['rb_fa', 165, 'RB58'] : r));
  s.others = [['p1', 'p2', 'p3', 'te_fa']];
  s.cfg = { max_claims: 2, stream_k_def: false, min_roster: { RB: 1 } };
  const lg = page(s);
  assert.ok(lg.waivers.claims.length > 0);
  assert.ok(!drops(lg.waivers).includes('rb2'), JSON.stringify(claims(lg.waivers)));
});

test('safety: a bench player whose game has started can\'t fill an empty spot', () => {
  // Sunday after the early games: te2 (late game) is the only TE who can still play; te3
  // already played on the bench. Dropping te2 leaves TE empty.
  const LATE = Date.parse('2026-10-25T20:25:00Z') / 1000;
  const s = base();
  s.now = Date.parse('2026-10-25T17:30:00Z');
  s.players.te2 = ['te2', 'TE', 'DAL', null, null];
  s.players.te3 = ['te3', 'TE', 'CHI', null, null];
  s.players.te1[2] = 'DAL';
  s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'te2', 'te3'];
  s.starters = ['qb1', 'rb1', 'wr1', 'te2', 'rb2', 'k1', 'DET'];
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].filter((r) => r[0] !== 'te1')
    .map((r) => (['rb_fa', 'wr_fa', 'te_fa'].includes(r[0]) ? [r[0], r[1], r[2], LATE] : r))
    .concat([['te1', 40, 'TE5', LATE], ['te2', 80, 'TE15', LATE], ['te3', 85, 'TE16']]);
  s.ros['ros-ppr-overall'].push(['te2', 300, 'TE30'], ['te3', 120, 'TE12']);
  const out = bad(s, (res, c) => { res.freeAgents.claims = [c('upgrade', 'wr_fa', 'te2')]; res.waivers.claims = []; });
  assert.ok(out.some((x) => /starting spot this week with nobody who can play/.test(x)), JSON.stringify(out));
  // The planner may swap te2 only for a TE who still plays (te_fa, late game).
  const swap = page(s).freeAgents.claims.find((c) => c.drop && c.drop.id === 'te2');
  assert.ok(!swap || swap.add.id === 'te_fa', JSON.stringify(swap && swap.add.id));
});

test('safety: no false alarm when a locked bench player could have filled the spot earlier', () => {
  // Sunday: FLEX is empty and the bench players who could fill it already played. The plan
  // must neither drop qb2 (the only QB who plays) nor get blocked for a hole it didn't open.
  const LATE = Date.parse('2026-10-25T20:25:00Z') / 1000;
  const s = base();
  s.now = Date.parse('2026-10-25T17:30:00Z');
  s.players.te1[3] = null;
  s.players.qb2 = ['qb2', 'QB', 'DAL', null, null];
  s.players.qb1[2] = 'NYG';
  s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'qb2', 'wr3'];
  s.players.rb2[3] = 'Out'; s.players.wr2[3] = 'Out';
  s.starters = ['qb1', 'rb1', 'wr1', 'te1', '0', 'k1', 'DET'];
  s.weekly.qb = [['qb1', 5, 'QB5', null, true], ['qb2', 20, 'QB20', LATE]];
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].map((r) => (['rb_fa', 'wr_fa', 'te_fa'].includes(r[0]) ? [r[0], r[1], r[2], LATE] : r));
  s.ros['ros-ppr-overall'].push(['qb2', 250, 'QB30']);
  s.cfg = { max_claims: 2, stream_k_def: false };
  const lg = page(s);
  assert.ok(!drops(lg.freeAgents).includes('qb2'), JSON.stringify(claims(lg.freeAgents)));
  assert.deepEqual(plain(lg.safety), []);
});

// ---- Third review: ties between equal lineups, claims already pending before the run ------

test('the verdict on a move doesn\'t depend on lineup layout or roster order (no false safety block)', () => {
  // mx (RB/WR) is the only player who can take the second RB or the second WR spot this week,
  // so either one is "the empty spot". Claims Tuesday, before the waiver run.
  const spec = (mxAt, order, fa) => {
    const s = tuesday(base());
    Object.assign(s.players, { mx: ['mx', 'WR', 'BUF', null, ['RB', 'WR']], te2: ['te2', 'TE', 'GB', null, null], qb2: ['qb2', 'QB', 'SF', null, null] });
    s.players.te1[3] = null;
    s.players.rb2[3] = 'Out';
    s.players.wr2[2] = 'BYE1'; s.players.rb3[2] = 'BYE1'; s.players.wr3[2] = 'BYE1';
    s.positions = ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'K', 'DEF', 'BN', 'BN', 'BN', 'BN'];
    s.mine = order || ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'rb3', 'wr3', 'qb2', 'te2', 'mx'];
    s.starters = ['qb1', 'rb1', mxAt === 'RB' ? 'mx' : 'rb2', 'wr1', mxAt === 'WR' ? 'mx' : 'wr2', 'te1', 'te2', 'k1', 'DET'];
    s.others = [['p1', 'p2', 'p3', fa === 'wr' ? 'rb_fa' : 'wr_fa', 'te_fa']];
    s.weekly['ppr-flex'] = s.weekly['ppr-flex'].map((r) => (['wr2', 'rb3', 'wr3'].includes(r[0]) ? [r[0], r[1], r[2], null, true] : r))
      .concat([['mx', 80, 'WR40'], ['te2', 60, 'TE10']]);
    s.weekly.qb.push(['qb2', 20, 'QB20']);
    s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].map((r) => (r[0] === 'rb3' ? ['rb3', 150, 'RB50'] : r[0] === 'wr3' ? ['wr3', 120, 'WR45'] : r))
      .concat([['mx', 280, 'WR95'], ['te2', 200, 'TE16'], ['qb2', 100, 'QB14']]);
    s.cfg = { max_claims: 2, stream_k_def: false };
    return s;
  };
  const reversed = ['mx', 'qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'rb3', 'wr3', 'qb2', 'te2'];
  for (const fa of ['rb', 'wr']) {
    const seen = new Set();
    for (const order of [null, reversed]) {
      for (const at of ['RB', 'WR']) {
        const lg = page(spec(at, order, fa));
        assert.deepEqual(plain(lg.safety), [], `${fa} ${at} ${order ? 'reversed' : ''}`);
        seen.add(JSON.stringify(claims(lg.waivers)));
        const { gas } = build(spec(at, order, fa));
        auto(gas, { max_claims: 2, stream_k_def: false });
        gas.tick();
        assert.notEqual(gas.getJson_('lastTick').status, 'error', gas.getJson_('lastTick').msg);
      }
    }
    assert.equal(seen.size, 1, [...seen].join(' vs '));
  }
});

test('before the waiver run, a new claim doesn\'t rely on a claim already pending on Sleeper', () => {
  // te1 is Out and te2 is the only other TE who plays. A claim for te_fa is pending: if a
  // rival wins it, dropping te2 would leave TE empty this week.
  const s = tuesday(base());
  s.players.te2 = ['te2', 'TE', 'GB', null, null];
  s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'rb3', 'te2'];
  s.weekly['ppr-flex'].push(['te2', 85, 'TE20']);
  s.ros['ros-ppr-overall'].push(['te2', 300, 'TE40']);
  s.others = [['p1', 'p2', 'p3']];
  s.pending = [{ adds: { te_fa: 1 }, drops: { rb3: 1 } }];
  s.cfg = { max_claims: 2, stream_k_def: false };
  const lg = page(s);
  assert.ok(!drops(lg.waivers).includes('te2'), JSON.stringify(claims(lg.waivers)));
  assert.deepEqual(plain(lg.safety), []);
  const out = bad(s, (res, c) => { res.waivers.claims = [c('upgrade', 'wr_fa', 'te2')]; });
  assert.ok(out.some((x) => /starting spot this week with nobody who can play/.test(x)), JSON.stringify(out));
});

test('claims pending on Sleeper are listed with who comes in, who goes and the bid', () => {
  const s = tuesday(base());
  s.others = [[]];
  s.pending = [{ adds: { te_fa: 1 }, drops: { wr3: 1 }, settings: { waiver_bid: 7 } }, { adds: { rb_fa: 1 }, drops: {} }];
  const view = (W) => plain(W.pendingClaims).map((c) => [c.add && c.add.name, c.add && c.add.posRank, c.drop && c.drop.name, c.bid]);
  const W = page(s).waivers;
  assert.equal(W.pending, 2);
  assert.deepEqual(view(W), [['te_fa', 'TE14', 'wr3', null], ['rb_fa', 'RB60', null, null]]);   // no bids without FAAB
  s.settings = { waiver_type: 2, waiver_budget: 100 };
  s.pending[1].settings = '{"waiver_bid":3}';   // Sleeper may send settings as JSON text
  assert.deepEqual(view(page(s).waivers), [['te_fa', 'TE14', 'wr3', 7], ['rb_fa', 'RB60', null, 3]]);
});

// IR spots. wr3 is the cheap bench receiver; here he's injured with a collapsed rank (Lamar after his surgery).
const injured = (status) => {
  const s = tuesday(base());
  s.players.wr3 = ['wr3', 'WR', 'MIN', status, null];
  s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].map((r) => (r[0] === 'wr3' ? ['wr3', 400, 'WR120'] : r));
  return s;
};

test('an injured player is never dropped while an IR spot is open; without one he can be', () => {
  assert.ok(drops(page(injured('Out')).waivers).includes('wr3'));
  const s = injured('Out');
  s.settings = { reserve_slots: 1 };
  const lg = page(s);
  assert.ok(!drops(lg.waivers).includes('wr3'), JSON.stringify(claims(lg.waivers)));
  assert.deepEqual(plain(lg.reserve.moves), []);   // only Out: he isn't moved to IR by himself
  const full = injured('Out');
  full.settings = { reserve_slots: 1 };
  full.mine.push('p_ir'); full.reserve = ['p_ir']; full.players.p_ir = ['p_ir', 'RB', 'KC', 'IR', null];
  assert.ok(drops(page(full).waivers).includes('wr3'));   // the IR spot is taken
});

test('the autopilot moves a player listed as IR to an open IR spot first, then uses the roster spot', () => {
  const s = base();
  s.players.wr3 = ['wr3', 'WR', 'MIN', 'IR', null];
  s.settings = { reserve_slots: 1 };
  s.mutate = true;
  const lg = page(s);
  assert.deepEqual(lg.reserve.moves.map((v) => v.id), ['wr3']);
  const { gas, writes } = build(s);
  auto(gas);
  gas.tick();
  assert.deepEqual(writes[0], ['reserve', ['wr3']]);
  assert.deepEqual(writes.slice(1).filter((w) => w[1] === 'te_fa'), [['fa', 'te_fa', null]]);   // no drop needed now
  assert.deepEqual(s._roster.reserve, ['wr3']);
  const after = page(s);
  assert.deepEqual(after.reserve.players.map((v) => v.id), ['wr3']);
  assert.deepEqual(plain(after.reserve.moves), []);
  // Suggestions only: nothing moves by itself, but the page's button does it.
  const t = base();
  t.players.wr3 = ['wr3', 'WR', 'MIN', 'IR', null];
  t.settings = { reserve_slots: 1 };
  const b = build(t);
  b.gas.tick();
  assert.deepEqual(b.writes, []);
  assert.equal(b.gas.updateReserve('L').reserve.applied, true);
  assert.deepEqual(b.writes, [['reserve', ['wr3']]]);
});

test('a healthy player still in an IR spot goes back to the roster when there is room, and is flagged when not', () => {
  const s = base();
  s.settings = { reserve_slots: 1 };
  s.reserve = ['wr3'];
  const lg = page(s);
  assert.deepEqual([lg.reserve.back.map((v) => v.id), lg.reserve.stuck.map((v) => v.id)], [['wr3'], []]);
  const { gas, writes } = build(s);
  auto(gas);
  gas.tick();
  assert.deepEqual(writes[0], ['reserve', []]);
  const full = base();
  full.settings = { reserve_slots: 1 };
  full.reserve = ['wr3'];
  full.mine.push('p_x'); full.players.p_x = ['p_x', 'RB', 'KC', null, null];
  const f = page(full);
  assert.deepEqual([f.reserve.back.map((v) => v.id), f.reserve.stuck.map((v) => v.id)], [[], ['wr3']]);
  const b = build(full);
  auto(b.gas);
  b.gas.tick();
  assert.ok(!b.writes.some((w) => w[0] === 'reserve'));
  assert.match(b.gas.getJson_('lastTick').msg, /wr3 must come off IR/);
});

// Backups. A Wolfpack-shaped team: two RB spots and a flex; rb2 is questionable and plays first;
// no RB on the bench (wr3 only) and one roster spot open. rb_fa is a free agent who plays later.
const shaky = (status) => {
  const s = base();
  s.positions = ['QB', 'RB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF', 'BN', 'BN'];
  s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'wr3'];
  s.starters = ['qb1', 'rb2', 'rb1', 'wr1', 'te1', 'wr2', 'k1', 'DET'];
  s.players.te1 = ['te1', 'TE', 'LV', null, null];
  s.players.rb2 = ['rb2', 'RB', 'NYJ', status === undefined ? 'Questionable' : status, null];
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].map((r) => (r[0] === 'rb2' ? ['rb2', 20, 'RB10', s.kick - 2 * 86400] : r));
  s.now = (s.kick - 3 * 86400) * 1000;   // the day before his game, free agency open
  return s;
};

test('a questionable starter nobody could replace gets a backup, picked up in the daytime', () => {
  const lg = page(shaky());
  assert.deepEqual(claims(lg.freeAgents).filter((c) => c[0] === 'backup'), [['backup', 'rb_fa', null]]);
  assert.ok(lg.freeAgents.notes.some((n) => /rb2 \(RB, questionable\).*picks up rb_fa as a backup/.test(n)), lg.freeAgents.notes.join(' | '));
  // A healthy RB on the bench who plays at the same time or later is a backup already...
  const covered = shaky();
  covered.mine.push('rb3'); covered.positions.push('BN');
  assert.deepEqual(claims(page(covered).freeAgents).filter((c) => c[0] === 'backup'), []);
  // ...but not one whose game is over by the time the starter's inactives are out.
  const early = shaky();
  early.mine.push('rb3'); early.positions.push('BN');
  early.weekly['ppr-flex'] = early.weekly['ppr-flex'].map((r) => (r[0] === 'rb3' ? ['rb3', 90, 'RB40', early.kick - 2 * 86400 - 3 * 3600] : r));
  assert.deepEqual(claims(page(early).freeAgents).filter((c) => c[0] === 'backup').map((c) => c[1]), ['rb_fa']);
  // Healthy starters need no backup, and "Cover byes and injuries" off means none.
  assert.deepEqual(claims(page(shaky(null)).freeAgents).filter((c) => c[0] === 'backup'), []);
  const off = shaky();
  off.cfg = { cover_byes: false };
  const b = build(off);
  b.gas.saveLeagueSettings('L', { cover_byes: false });
  assert.deepEqual(claims(b.gas.getDashboard().leagues[0].freeAgents).filter((c) => c[0] === 'backup'), []);
});

test('the autopilot picks up the backup ahead of time and swaps him in once the starter is ruled out', () => {
  const s = shaky();
  s.mutate = true;
  let b = build(s);
  auto(b.gas, { max_claims: 0 });   // no upgrades: only the backup
  b.gas.tick();
  assert.deepEqual(b.writes.filter((w) => w[0] === 'fa'), [['fa', 'rb_fa', null]]);
  assert.ok(s._roster.starters.includes('rb2'));   // the better player still starts while questionable
  // Game day: Sleeper marks him out an hour before his game; the next check swaps the backup in.
  s.players.rb2 = ['rb2', 'RB', 'NYJ', 'Out', null];
  s.now = (s.kick - 2 * 86400 - 3600) * 1000;
  b = build(s);
  b.gas.tick();
  assert.ok(!s._roster.starters.includes('rb2'));
  assert.ok(s._roster.starters.includes('rb_fa'), JSON.stringify(s._roster.starters));
});

test('no upgrade, fill-in or stream drops the backup a questionable starter has', () => {
  // rb3 (a cheap RB who plays later) is rb2's only backup; an upgrade at WR would otherwise drop him.
  const s = shaky();
  s.mine.push('rb3');
  s.positions = ['QB', 'RB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF', 'BN'];   // roster full: an upgrade needs a drop
  s.others = [['p1', 'p2', 'p3', 'rb_fa']];   // the free agents worth adding are receivers (an RB could take over as backup)
  s.cfg = { max_claims: 2, never_drop: ['wr3'], min_roster: { RB: 2 } };   // rb3 is the only cheap bench player, and not needed for depth
  const lg = page(s);
  assert.ok(!drops(lg.freeAgents).includes('rb3'), JSON.stringify(claims(lg.freeAgents)));
  assert.deepEqual(claims(lg.freeAgents).filter((c) => c[0] === 'backup'), []);   // he's covered
  s.players.rb2 = ['rb2', 'RB', 'NYJ', null, null];   // once rb2 is healthy, rb3 is just a cheap bench player again
  assert.ok(drops(page(s).freeAgents).includes('rb3'), JSON.stringify(claims(page(s).freeAgents)));
});

test('no move weakens this week\'s lineup: a rest-of-season upgrade that drops a starter waits until after his game', () => {
  // wr2 is the worst player for the rest of the season but starts in the flex this week; wr_fa is far
  // better for the rest of the season but on bye this week.
  const spec = () => {
    const s = base();
    s.players.te1 = ['te1', 'TE', 'LV', null, null];
    s.weekly['ppr-flex'] = s.weekly['ppr-flex'].map((r) => (r[0] === 'wr2' ? ['wr2', 15, 'WR8'] : r[0] === 'wr_fa' ? ['wr_fa', 60, 'WR30', null, true] : r));
    s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].map((r) => (r[0] === 'wr2' ? ['wr2', 300, 'WR95'] : r[0] === 'wr_fa' ? ['wr_fa', 100, 'WR40'] : r));
    return s;
  };
  const lg = page(spec());
  assert.ok(lg.lineup.starters.includes('wr2'));
  assert.ok(!drops(lg.freeAgents).includes('wr2'), JSON.stringify(claims(lg.freeAgents)));
  assert.ok(claims(lg.freeAgents).some((c) => c[1] === 'wr_fa'), JSON.stringify(claims(lg.freeAgents)));   // made with another drop
  // With nobody else to give up (a full roster without the cheap bench players), the upgrade waits and the page says why.
  const full = spec();
  full.mine = full.mine.filter((p) => p !== 'wr3' && p !== 'rb3');
  full.positions = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF', 'BN'];
  const held = page(full).freeAgents;
  assert.deepEqual(claims(held).filter((c) => c[1] === 'wr_fa'), []);
  assert.ok(held.notes.some((n) => /wr_fa would be an upgrade over wr2, but wr2 helps your lineup this week/.test(n)), held.notes.join(' | '));
});

test('the safety check blocks a plan that weakens this week\'s lineup or takes a backup, however it was made', () => {
  const s = base();
  s.players.te1 = ['te1', 'TE', 'LV', null, null];
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].map((r) => (r[0] === 'wr2' ? ['wr2', 15, 'WR8'] : r));
  const { gas } = build(s);
  gas.withLeague_('L', (lg) => {
    const res = lg.evaluate({ lineup: true, freeAgents: true });
    assert.deepEqual(plain(res.safety), []);
    // A planner bug that drops this week's flex starter for a free agent who is worse this week:
    res.freeAgents.claims = [{ kind: 'upgrade', add: lg.rosView_('rb_fa'), drop: lg.rosView_('wr2') }];
    assert.ok(gas.checkPlans_(lg, res).some((x) => /Dropping wr2 for rb_fa would weaken this week's lineup/.test(x)));
  });
  const q = shaky();
  q.mine.push('rb3'); q.positions.push('BN');
  const b = build(q);
  b.gas.withLeague_('L', (lg) => {
    const res = lg.evaluate({ lineup: true, freeAgents: true });
    res.freeAgents.claims = [{ kind: 'upgrade', add: lg.rosView_('wr_fa'), drop: lg.rosView_('rb3') }];
    assert.ok(b.gas.checkPlans_(lg, res).some((x) => /Dropping rb3 would leave rb2 \(questionable\) without a backup/.test(x)),
              JSON.stringify(b.gas.checkPlans_(lg, res)));
  });
});

// ---- From the independent audit: each was a confirmed wrong decision -------------------------------

test('audit: a player in an IR spot whose status the league doesn\'t allow there must come off it (and claims wait)', () => {
  for (const st of ['Doubtful', 'Out', 'NA', 'DNR', 'COV', 'Sus', 'Questionable', null]) {
    const s = base();
    s.players.ir1 = ['ir1', 'WR', 'BUF', st, null];
    s.reserve = ['ir1']; s.mine = s.mine.concat(['ir1']); s.positions = s.positions.concat(['IR']);
    s.settings = { reserve_slots: 1, reserve_allow_out: 0, reserve_allow_doubtful: 0 };
    const lg = page(s);
    const off = lg.reserve.stuck.concat(lg.reserve.back).map((v) => v.id);
    assert.deepEqual(off, ['ir1'], String(st));
    assert.deepEqual(claims(lg.freeAgents), [], String(st) + ' ' + JSON.stringify(claims(lg.freeAgents)));
  }
  // A league that allows Out players on IR keeps him there; IR and PUP are always fine.
  for (const [st, allow] of [['Out', { reserve_allow_out: 1 }], ['IR', {}], ['PUP', {}]]) {
    const s = base();
    s.players.ir1 = ['ir1', 'WR', 'BUF', st, null];
    s.reserve = ['ir1']; s.mine = s.mine.concat(['ir1']); s.positions = s.positions.concat(['IR']);
    s.settings = Object.assign({ reserve_slots: 1 }, allow);
    const lg = page(s);
    assert.deepEqual(lg.reserve.stuck.concat(lg.reserve.back), [], st);
  }
});

test('audit: stuck in an IR spot with a full roster: the page and the log say exactly whom to drop', () => {
  const s = base();
  s.players.ir1 = ['ir1', 'WR', 'BUF', null, null];   // a good receiver, healthy again
  s.ros['ros-ppr-overall'].push(['ir1', 30, 'WR10']);
  s.reserve = ['ir1']; s.mine = s.mine.concat(['ir1']);
  s.settings = { reserve_slots: 1 };
  const lg = page(s);
  assert.deepEqual(lg.reserve.stuck.map((v) => v.id), ['ir1']);
  assert.equal(lg.reserve.makeRoom.id, 'wr3');   // the least valuable bench player
  const { gas } = build(s);
  auto(gas);
  gas.tick();
  gas.tick();
  const logged = gas.getState().log.filter((e) => /ir1 must come off IR/.test(e.title));
  assert.equal(logged.length, 1);
  assert.match(logged[0].lines.join(' '), /Drop wr3 on Sleeper \(your least valuable player\), then move ir1 back/);
});

test('audit: keeper and dynasty leagues never cut a stashed player missing from the redraft lists, or one on IR', () => {
  const run = (type) => {
    const s = base();
    s.players.rookie = ['rookie', 'QB', 'NYG', null, null];
    s.players.acl = ['acl', 'WR', 'CIN', 'IR', null];
    s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'rookie', 'acl'];
    s.players.te1 = ['te1', 'TE', 'LV', null, null];
    s.settings = { type };
    return drops(page(s).freeAgents);
  };
  assert.ok(run(0).includes('rookie'));   // redraft: unranked is cut-able
  const d = run(2);
  assert.ok(!d.includes('rookie') && !d.includes('acl'), JSON.stringify(d));
  assert.ok(!run(1).includes('rookie'));
});

test('audit: players in an open trade offer are never dropped', () => {
  const s = base();
  s.trades = [{ transaction_id: 't1', type: 'trade', status: 'proposed', roster_ids: [1, 2], creator: 'me',
                adds: { rb3: 2, wr3: 2, p1: 1 }, drops: { rb3: 1, wr3: 1, p1: 2 } }];
  const lg = page(s);
  assert.ok(!drops(lg.freeAgents).some((d) => d === 'rb3' || d === 'wr3'), JSON.stringify(claims(lg.freeAgents)));
  assert.deepEqual(plain(lg.safety), []);
});

test('audit: a game with no kickoff time yet is a game, not a bye', () => {
  const s = base();
  s.players.te1[3] = null;
  for (const slug of Object.keys(s.weekly)) s.weekly[slug] = s.weekly[slug].map((r) => (s.players[r[0]][2] === 'DET' ? [r[0], r[1], r[2], null] : r));
  const lg = page(s);
  assert.ok(!lg.lineup.benched.some((v) => v.why === 'bye'), JSON.stringify(lg.lineup.benched));
  assert.ok(lg.lineup.starters.includes('rb1'));   // DET's RB still starts
});

test('audit: a pickup Sleeper keeps refusing is logged once, not on every 30-minute check', () => {
  const s = base();
  const first = build(s);
  auto(first.gas, { max_claims: 2 });
  let attempts = 0;
  for (let i = 0; i < 6; i++) {
    s.now = Date.parse('2026-10-24T18:00:00Z') + i * 30 * 60e3;
    const b = build(s);
    b.gas.addFreeAgent_ = () => { attempts++; throw new Error('Sleeper refused the pickup'); };
    b.gas.tick();
  }
  assert.ok(attempts >= 6);   // still retried every check
  const log = build(s).gas.getState().log;
  assert.equal(log.filter((e) => e.title === 'A free-agent pickup failed').length, 1, JSON.stringify(log.map((e) => e.title)));
  assert.equal(log.filter((e) => /Free agents picked up/.test(e.title)).length, 0);
});

// ---- From the second review (each was a confirmed defect in the first round of fixes) ---------------

test('review: a kicker/defense ranking page that stays down is tried once per check, and the plans still work', () => {
  for (const tuesday of [false, true]) {
    const s = base();
    if (tuesday) { s.now = TUESDAY; s.leg = 6; }
    const b = build(s);
    const orig = b.gas.fpList_, counts = {};
    b.gas.fpList_ = (slug) => { counts[slug] = (counts[slug] || 0) + 1; if (slug === 'k' || slug === 'dst') throw new Error('FantasyPros ' + slug + ' failed (HTTP 503)'); return orig(slug); };
    const lg = b.gas.getDashboard().leagues[0];
    assert.ok(!lg.lineup.error && !(lg.freeAgents && lg.freeAgents.error) && !(lg.waivers && lg.waivers.error), JSON.stringify([lg.lineup.error, lg.freeAgents, lg.waivers.error]));
    assert.ok((counts.k || 0) <= 1 && (counts.dst || 0) <= 1, JSON.stringify(counts));
  }
});

test('review: claims held for a player who must come off IR wait (the window isn\'t used up), with or without Auto lineup', () => {
  for (const autoLineup of [true, false]) {
    const s = tuesday(base());
    s.players.ir1 = ['ir1', 'WR', 'BUF', 'Doubtful', null];
    s.ros['ros-ppr-overall'].push(['ir1', 30, 'WR10']);
    s.reserve = ['ir1']; s.mine = s.mine.concat(['ir1']);
    s.settings = { reserve_slots: 1 };
    let b = build(s);
    auto(b.gas, { auto_lineup: autoLineup });
    b.gas.tick();
    assert.deepEqual(b.writes, []);
    assert.deepEqual(b.gas.getJson_('waivers_done', {}), {});
    assert.ok(b.gas.getState().log.some((e) => e.title === 'Waiver claims are waiting'), String(autoLineup));
    // The manager follows the advice (drops wr3, moves ir1 back); the next check sends the claims.
    s._roster.players = s._roster.players.filter((p) => p !== 'wr3'); s._roster.reserve = [];
    s.now += 3600e3;
    b = build(s);
    b.gas.tick();
    assert.ok(b.writes.some((w) => w[0] === 'claim'), JSON.stringify(b.writes));
  }
});

test('review: "no weaker lineup this week" also holds if an earlier claim in the plan is lost', () => {
  const s = tuesday(base());
  s.players.te1 = ['te1', 'TE', 'LV', null, null];
  s.mine = s.mine.filter((p) => p !== 'wr3');   // one open roster spot
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].map((r) => (r[0] === 'wr_fa' ? ['wr_fa', 10, 'WR5'] : r[0] === 'rb_fa' ? ['rb_fa', 65, 'RB30', null, true] : r));
  s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].map((r) => (r[0] === 'rb2' ? ['rb2', 300, 'RB90'] : r[0] === 'rb3' ? ['rb3', 200, 'RB70']
    : r[0] === 'wr_fa' ? ['wr_fa', 100, 'WR40'] : r[0] === 'rb_fa' ? ['rb_fa', 110, 'RB45'] : r));
  const lg = page(s);
  assert.ok(lg.lineup.starters.includes('rb2'));
  assert.ok(!drops(lg.waivers).includes('rb2'), JSON.stringify(claims(lg.waivers)));
  assert.deepEqual(plain(lg.safety), []);
});

test('review: if open trade offers can\'t be read, nobody is dropped and the plan says why', () => {
  const s = base();
  s.trades = [{ transaction_id: 't1', type: 'trade', status: 'proposed', roster_ids: [1, 2], adds: { rb3: 2, wr3: 2, p1: 1 }, drops: { rb3: 1, wr3: 1, p1: 2 } }];
  const b = build(s);
  b.gas.pendingTrades_ = () => { throw new Error('Sleeper API timeout'); };
  const f = b.gas.getDashboard().leagues[0].freeAgents;
  assert.equal(drops(f).length, 0, JSON.stringify(claims(f)));
  assert.ok(f.notes.some((n) => /Couldn't read your open trade offers/.test(n)));
});

test('review: in a dynasty league the "make room" advice never names a stashed player', () => {
  const s = base();
  s.settings = { type: 2, reserve_slots: 1 };
  s.players.ir1 = ['ir1', 'WR', 'BUF', null, null];
  s.ros['ros-ppr-overall'].push(['ir1', 30, 'WR10']);
  s.players.rookie = ['rookie', 'QB', 'NYG', null, null];
  s.mine = ['qb1', 'rb1', 'rb2', 'wr1', 'wr2', 'te1', 'k1', 'DET', 'rookie', 'wr3', 'ir1'];
  s.reserve = ['ir1'];
  s.players.te1 = ['te1', 'TE', 'LV', null, null];
  assert.equal(page(s).reserve.makeRoom.id, 'wr3');
});

test('review: the safety check refuses claims planned while a player must come off IR', () => {
  const s = base();
  s.players.ir1 = ['ir1', 'WR', 'BUF', 'Doubtful', null];
  s.reserve = ['ir1']; s.mine = s.mine.concat(['ir1']);
  s.settings = { reserve_slots: 1 };
  const { gas } = build(s);
  gas.withLeague_('L', (lg) => {
    const res = lg.evaluate({ lineup: true, freeAgents: true });
    res.freeAgents.claims = [{ kind: 'cover', add: lg.rosView_('te_fa'), drop: null }];
    assert.ok(gas.checkPlans_(lg, res).some((x) => /while a player must come off IR/.test(x)));
  });
});

// ---- From the third review --------------------------------------------------------------------------

test('review 3: a one-off failure fetching the main ranking list doesn\'t sink the whole check', () => {
  const s = base();
  s.starters = ['qb1', 'rb1', 'wr1', 'te1', 'wr3', 'k1', 'DET'];   // wr3 in the flex: the lineup step should fix it
  s.settings = { reserve_slots: 1 };
  s.players.irx = ['irx', 'WR', 'BUF', 'IR', null]; s.reserve = ['irx']; s.mine = s.mine.concat(['irx']);
  s.now = (s.kick - 3 * 3600) * 1000;
  const b = build(s);
  b.gas.setMode('auto');
  const orig = b.gas.fpList_;
  let n = 0;
  b.gas.fpList_ = (slug) => { if (slug === 'ppr-flex' && n++ === 0) throw new Error('Address unavailable: fantasypros'); return orig(slug); };
  b.gas.tick();
  assert.ok(b.writes.some((w) => w[0] === 'starters'), b.gas.getJson_('lastTick').msg);
});

test('review 3: with Auto lineup off, a player who can come back from IR is reported (pickups wait for him)', () => {
  const s = base();
  s.settings = { reserve_slots: 1 };
  s.players.ir1 = ['ir1', 'WR', 'BUF', null, null];
  s.ros['ros-ppr-overall'].push(['ir1', 30, 'WR10']);
  s.mine = s.mine.filter((p) => p !== 'wr3').concat(['ir1']); s.reserve = ['ir1'];
  const b = build(s);
  auto(b.gas, { auto_lineup: false });
  b.gas.tick();
  assert.ok(b.gas.getState().log.some((e) => e.title === 'ir1 must come off IR' && /Move back to roster/.test(e.lines.join(' '))));
  assert.deepEqual(b.writes, []);
});

test('review 3: no "claims are waiting" when there was nothing to claim; the window is used up as usual', () => {
  const s = tuesday(base());
  s.players.te1 = ['te1', 'TE', 'LV', null, null];
  for (const k of Object.keys(s.weekly)) s.weekly[k] = s.weekly[k].filter((r) => !/_fa$/.test(r[0]));
  for (const k of Object.keys(s.ros)) s.ros[k] = s.ros[k].filter((r) => !/_fa$/.test(r[0]));
  s.players.ir1 = ['ir1', 'WR', 'BUF', 'Doubtful', null];
  s.ros['ros-ppr-overall'].push(['ir1', 30, 'WR10']);
  s.mine = s.mine.concat(['ir1']); s.reserve = ['ir1'];
  s.settings = { reserve_slots: 1 };
  const b = build(s);
  auto(b.gas);
  b.gas.tick();
  assert.ok(!b.gas.getState().log.some((e) => e.title === 'Waiver claims are waiting'));
  assert.notDeepEqual(b.gas.getJson_('waivers_done', {}), {});
});

test('review 3: no "drop X" advice while open trade offers can\'t be read', () => {
  const s = base();
  s.settings = { reserve_slots: 1 };
  s.players.ir1 = ['ir1', 'WR', 'BUF', null, null];
  s.ros['ros-ppr-overall'].push(['ir1', 30, 'WR10']);
  s.reserve = ['ir1']; s.mine = s.mine.concat(['ir1']);
  const b = build(s);
  b.gas.pendingTrades_ = () => { throw new Error('Sleeper API timeout'); };
  const r = b.gas.getDashboard().leagues[0].reserve;
  assert.deepEqual(r.stuck.map((v) => v.id), ['ir1']);
  assert.equal(r.makeRoom, null);
});

test('review 3: kicker rankings that didn\'t load are said as such, never shown as a rank', () => {
  const s = base();
  s.players.te1 = ['te1', 'TE', 'LV', null, null];
  s.weekly.k = s.weekly.k.map((r) => (r[0] === 'k1' ? ['k1', 10, 'K10', null, true] : r));   // k1 on bye: a fill-in is needed
  const b = build(s);
  const orig = b.gas.fpList_;
  b.gas.fpList_ = (slug) => { if (slug === 'ros-k') throw new Error('FantasyPros ros-k failed (HTTP 503)'); return orig(slug); };
  const f = b.gas.getDashboard().leagues[0].freeAgents;
  assert.ok(!f.error, f.error);
  const said = f.notes.filter((n) => /k1/.test(n)).join(' | ');
  assert.ok(/no K rankings loaded/.test(said) && !/K1 rest of season/.test(said), said);
});

// ---- Depth: an injured pickup doesn't get past the useful-depth cap ---------------------------------

// Two TEs already (te1 Out, te2 healthy); the cap for a 1-TE league is 2. te_out is a strong TE who is Out.
const twoTes = (outFa) => {
  const s = base();
  s.positions = s.positions.concat(['BN']);
  s.players.te2 = ['te2', 'TE', 'GB', null, null];
  s.players.te_out = ['te_out', 'TE', 'BAL', outFa ? 'Out' : null, null];
  s.mine = s.mine.concat(['te2']);
  s.starters = s.starters.map((p) => (p === 'te1' ? 'te2' : p));
  s.others = [['p1', 'p2', 'p3', 'te_fa', 'wr_fa', 'rb_fa']];
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].concat([['te2', 45, 'TE8'], ['te_out', 30, 'TE4']]);
  s.ros['ros-ppr-overall'] = s.ros['ros-ppr-overall'].concat([['te2', 150, 'TE12'], ['te_out', 30, 'TE3']]);
  return s;
};

test('depth: an injured free agent is not added as a 3rd TE for a player at another position', () => {
  const s = twoTes(true);
  s.weekly['ppr-flex'] = s.weekly['ppr-flex'].map((r) => (r[0] === 'wr3' ? ['wr3', 10, 'WR4'] : r));  // wr3 starts this week
  const lg = page(s);
  assert.ok(!ids(lg.freeAgents).includes('te_out'), JSON.stringify(claims(lg.freeAgents)));
  // ...and no note promises him for after this week's games either
  assert.ok(!lg.freeAgents.notes.some((n) => /te_out/.test(n)), JSON.stringify(lg.freeAgents.notes));
  assert.deepEqual(plain(lg.safety), []);
});

test('depth: a healthy TE is still added while one of the two is out', () => {
  const lg = page(twoTes(false));
  assert.ok(ids(lg.freeAgents).includes('te_out'), JSON.stringify(claims(lg.freeAgents)));
  assert.deepEqual(plain(lg.safety), []);
});

test('depth: the safety check refuses a pickup past useful depth that replaces another position', () => {
  const { gas } = build(twoTes(true));
  gas.withLeague_('L', (lg) => {
    const res = lg.evaluate({ lineup: true, freeAgents: true });
    res.freeAgents.claims = [{ kind: 'upgrade', add: lg.rosView_('te_out'), drop: lg.rosView_('wr3') }];
    const out = gas.checkPlans_(lg, res);
    assert.ok(out.some((x) => /te_out would be TE number 3 \(past useful depth\)/.test(x)), JSON.stringify(out));
  });
});
