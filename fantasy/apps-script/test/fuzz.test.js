// Random leagues with what the other random tests don't vary: claims pending on Sleeper (before
// and after the waiver run), starred players, fresh pickups, open roster spots, FAAB, Sunday
// locks. Every plan is judged by the fake world's own rules, not the app's safety check.
// FUZZ_N=4000 node --test test/fuzz.test.js runs more leagues.
const test = require('node:test');
const assert = require('node:assert/strict');
const { makeWorld, KICK, WAIVER_RUN, SLOT_POS, fillable } = require('./world');

const iso = (t) => new Date(t).toISOString().slice(5, 16);
const N = Number(process.env.FUZZ_N || 400);

/** One random league at a random moment; returns what went wrong. */
function league(seed) {
  const r = ((x) => () => { x = (x * 16807) % 2147483647; return x / 2147483647; })(seed * 7919 + 13);
  const moments = [
    Date.parse('2026-10-20T16:00:00Z') + Math.floor(r() * 12.5 * 3600000),    // claim window, before the run
    Date.parse('2026-10-21T08:00:00Z') + Math.floor(r() * 40 * 3600000),      // Wednesday-Thursday after the run
    KICK.EARLY + 60000 + Math.floor(r() * (KICK.LATE - KICK.EARLY - 120000)), // Sunday, early games locked
    KICK.TNF + 3600000 + Math.floor(r() * 50 * 3600000),                       // Friday/Saturday after TNF
  ];
  const now = moments[Math.floor(r() * moments.length)];
  const waiversRan = now >= WAIVER_RUN;
  const world = makeWorld({ seed, now, superflex: r() < 0.4, flex: r() < 0.5 ? 'FLEX' : 'WRRB_FLEX', rolling: r() < 0.4,
                            waiversRan, bench: 3 + Math.floor(r() * 5), injuries: 0.03 + r() * 0.15, passTd: r() < 0.3 ? 6 : 4,
                            priorityShift: Math.floor(r() * 10) });
  if (r() < 0.25) world.league.settings.waiver_type = 2;  // FAAB
  world.refreshStatus();
  Object.keys(world.players).forEach((p) => { if (r() < 0.04) world.clears[p] = Math.floor(now / 1000) + 86400; });
  const P = world.players;
  const rostered = (p) => world.rosters.some((ro) => ro.players.includes(p));
  const bench = () => world.me.players.filter((p) => !world.lineup.includes(p));
  const nOpen = r() < 0.3 ? 1 + Math.floor(r() * 2) : 0;
  for (let i = 0; i < nOpen; i++) {
    const b = bench();
    if (b.length) { const p = b[Math.floor(r() * b.length)]; world.me.players = world.me.players.filter((x) => x !== p); }
  }
  if (r() < 0.5) {
    const n = 1 + Math.floor(r() * 3);
    const pool = Object.keys(P).filter((p) => !rostered(p) && ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'].includes(P[p][1]));
    for (let i = 0; i < n && pool.length; i++) {
      const add = pool.splice(Math.floor(r() * pool.length), 1)[0];
      if (waiversRan) world.clears[add] = Math.floor(now / 1000) + 5 * 86400;  // still on waivers: next run
      const b = bench().filter((p) => !world.pending.some((t) => t.drop === p));
      const drop = r() < 0.75 && b.length ? b[Math.floor(r() * b.length)] : null;
      world.pending.push({ add, drop, rid: 1 });
    }
  }
  const recent = [];
  if (r() < 0.4) {
    const n = 1 + Math.floor(r() * 2);
    for (let i = 0; i < n; i++) {
      const p = world.me.players[Math.floor(r() * world.me.players.length)];
      recent.push(p);
      world.tx.push({ type: 'free_agent', status: 'complete', leg: world.league.settings.leg, roster_ids: [1], adds: { [p]: 1 },
                      drops: null, status_updated: now - Math.floor(r() * 5 * 86400000) });
    }
  }
  const stars = [];
  if (r() < 0.4) {
    const n = 1 + Math.floor(r() * 3);
    for (let i = 0; i < n; i++) stars.push(world.me.players[Math.floor(r() * world.me.players.length)]);
  }
  let gas = world.gas();
  gas.setMode('auto');
  gas.saveLeagueSettings('L1', { auto_waivers: true, max_claims: 1 + Math.floor(r() * 3), min_gain: 10 + Math.floor(r() * 20),
                                 never_drop: stars });
  const out = [];
  const moves = (plan) => JSON.stringify(plan.claims.map((c) => [c.kind, c.add.id, c.drop && c.drop.id]));
  try {
    const lg = gas.getDashboard().leagues[0];
    const F = lg.freeAgents && !lg.freeAgents.error && !lg.freeAgents.waiting ? lg.freeAgents : null;
    const W = lg.waivers && !lg.waivers.error ? lg.waivers : null;
    (lg.safety || []).forEach((x) => out.push('safety: ' + x));
    const dropped = {};
    world.pending.forEach((t) => { if (t.drop) dropped[t.drop] = 'pending'; });
    [['F', F], ['W', W]].forEach(([how, plan]) => {
      if (!plan) return;
      plan.claims.forEach((c) => {
        const a = c.add.id, d = c.drop && c.drop.id;
        if (rostered(a)) out.push(`${how} adds ${a}, who is on a roster`);
        if (how === 'F' && !world.isFreeAgent(a)) out.push(`F adds ${a}, who isn't a free agent`);
        if (how === 'W' && waiversRan && world.isFreeAgent(a)) out.push(`W claims ${a}, who is a free agent`);
        if (world.pending.some((t) => t.add === a)) out.push(`${how} adds ${a} again (claim pending)`);
        if (!d) return;
        if (!world.me.players.includes(d)) out.push(`${how} drops ${d}, who isn't mine`);
        if (dropped[d]) out.push(`${how} drops ${d} twice (${dropped[d]})`);
        dropped[d] = how;
        if (stars.includes(d)) out.push(`${how} drops starred ${d}`);
        if (how === 'F' && world.started(d)) out.push(`F drops ${d}, whose game started`);
        const kd = P[d][1] === 'K' || P[d][1] === 'DEF';
        if (c.kind !== 'upgrade' && recent.includes(d) && !kd) out.push(`${how} ${c.kind} drops fresh pickup ${d}`);
      });
    });
    const withMoves = (roster, plan) => {
      let after = roster.slice();
      plan.claims.forEach((c) => { if (c.drop) after = after.filter((p) => p !== c.drop.id); after.push(c.add.id); });
      return after;
    };
    if (F && F.claims.length) {
      const b = fillable(world, world.me.players), a = fillable(world, withMoves(world.me.players, F));
      if (a < b) out.push(`F opens a hole (${b}->${a}) ${moves(F)}`);
      // A drop nobody else can replace this week, for a player who can't take any of his spots.
      let R = world.me.players.slice();
      F.claims.forEach((c) => {
        const a2 = c.add.id, d = c.drop && c.drop.id;
        if (d) {
          const needed = fillable(world, R.filter((p) => p !== d)) < fillable(world, R);
          const sameSlot = world.slots.some((sl) => SLOT_POS[sl].includes(P[a2][1]) && SLOT_POS[sl].includes(P[d][1]));
          if (needed && !sameSlot) out.push(`F trades needed ${d} (${P[d][1]}) for ${c.kind} ${a2} (${P[a2][1]})`);
          R = R.filter((p) => p !== d);
        }
        R.push(a2);
      });
      const size = world.me.players.length + F.claims.reduce((s, c) => s + 1 - (c.drop ? 1 : 0), 0);
      if (size > world.limit && size > world.me.players.length) out.push(`F overfills the roster ${size}/${world.limit}`);
    }
    if (W && !waiversRan && W.claims.length && now < KICK.TNF) {
      let week = world.me.players.slice();
      world.pending.forEach((t) => { if (t.drop) week = week.filter((p) => p !== t.drop); if (!week.includes(t.add)) week.push(t.add); });
      const b = fillable(world, week, true), a = fillable(world, withMoves(week, W), true);
      if (a < b) out.push(`W opens a hole (${b}->${a}) ${moves(W)}`);
    }
    // A fillable spot left empty without a word about it.
    if (F && lg.settings.cover_byes) {
      const after = withMoves(world.me.players, F), a = fillable(world, after);
      const cand = Object.keys(P).filter((p) => world.isFreeAgent(p) && P[p][3] !== 'Out' && world.kickoffOf[P[p][2]] && !world.started(p));
      const fixable = a < world.slots.length && cand.some((p) => fillable(world, after.concat(p)) > a);
      if (fixable && !F.notes.some((n) => /can't play this week|spot is empty/.test(n))) out.push(`F silently leaves a fillable spot ${moves(F)}`);
    }
    gas = world.gas();
    gas.tick();
    const last = gas.getJson_('lastTick');
    if (last && last.status === 'error') out.push('check failed: ' + last.msg);
  } catch (e) {
    out.push('crashed: ' + e.stack);
  }
  world.errors.forEach((e) => out.push('Sleeper refused: ' + e));
  return out.map((x) => `seed ${seed} ${iso(now)}: ${x}`);
}

test(`${N} random leagues with pending claims, stars, fresh pickups, open spots and Sunday locks`, () => {
  const failures = [];
  for (let seed = 1; seed <= N; seed++) failures.push(...league(seed));
  assert.deepEqual(failures, []);
});
