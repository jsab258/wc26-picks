// Whole weeks against a fake Sleeper (test/world.js): the real app ticks every 30
// minutes from Tuesday to the next Tuesday, and every step is checked against
// Sleeper's rules, the app's safety rules and "was the lineup sensible at kickoff".
const test = require('node:test');
const assert = require('node:assert/strict');
const { makeWorld, T0, KICK, WAIVER_RUN, SLOT_POS } = require('./world');

const iso = (t) => new Date(t).toISOString().slice(5, 16);

/** Right before a kickoff: nobody out/on bye (or an empty slot) while a healthy bench player could play. */
function lineupProblems(world, k) {
  const out = [];
  const P = world.players, team = (p) => P[p][2];
  const canPlay = (p) => P[p][3] !== 'Out' && !!world.kickoffOf[team(p)] && world.kickoffOf[team(p)] >= k;
  const bench = world.me.players.filter((p) => !world.lineup.includes(p) && !world.started(p) && canPlay(p));
  world.lineup.forEach((p, i) => {
    if (p !== '0' && (world.started(p) || canPlay(p))) return;
    const alt = bench.find((b) => SLOT_POS[world.slots[i]].includes(P[b][1]));
    if (alt) out.push(`${iso(k)} kickoff: ${world.slots[i]} has ${p === '0' ? 'nobody' : p + ' (' + (P[p][3] || 'bye') + ')'} while ${alt} sits`);
  });
  return out;
}

/** What the page shows, judged by the world's own rules (not the app's safety check). */
function planProblems(world, d) {
  const out = [], when = iso(world.now);
  const rostered = (p) => world.rosters.some((ro) => ro.players.includes(p));
  d.leagues.forEach((lg) => {
    const seenDrops = {};
    const moves = [['pickup', lg.freeAgents], ['claim', lg.waivers]];
    moves.forEach(([how, plan]) => {
      if (!plan || plan.error || plan.waiting) return;
      plan.claims.forEach((c) => {
        if (rostered(c.add.id)) out.push(`${when} ${how} of ${c.add.id}, who is on a roster`);
        if (how === 'pickup' && !world.isFreeAgent(c.add.id)) out.push(`${when} pickup of ${c.add.id}, who isn't a free agent`);
        if (how === 'claim' && world.league.settings.leg === 8 && world.isFreeAgent(c.add.id)) {
          out.push(`${when} claim for ${c.add.id}, who is a free agent right now`);
        }
        if (c.drop) {
          if (!world.me.players.includes(c.drop.id)) out.push(`${when} drop of ${c.drop.id}, who isn't mine`);
          if (seenDrops[c.drop.id]) out.push(`${when} ${c.drop.id} dropped twice`);
          seenDrops[c.drop.id] = true;
        }
        [c.add, c.drop].filter(Boolean).forEach((v) => { if (v.rank >= 999) out.push(`${when} ${v.id} shown as #${v.rank}`); });
      });
    });
  });
  return out;
}

function runWeek(opts, script) {
  const world = makeWorld(opts);
  if (script) script(world);
  let gas = world.gas();
  gas.setMode('auto');
  gas.saveLeagueSettings('L1', Object.assign({ auto_waivers: true }, opts.cfg || {}));
  const problems = [];
  const kicks = Object.values(KICK).sort((a, b) => a - b);
  const end = Date.parse('2026-10-27T06:00:00Z');
  for (let t = world.now; t <= end; t += 30 * 60000) {
    kicks.filter((k) => k > world.now && k <= t).forEach((k) => {
      world.advance(k - 60000);
      problems.push(...lineupProblems(world, k));
    });
    world.advance(t);
    gas = world.gas();
    gas.tick();
    const last = gas.getJson_('lastTick');
    if (last && last.status === 'error') problems.push(`${iso(t)} check failed: ${last.msg}`);
    if ((t - T0) % (3 * 3600000) === 0) {   // someone opens the page every 3 hours
      const d = gas.getDashboard();
      problems.push(...planProblems(world, d));
      d.leagues.forEach((lg) => (lg.safety || []).forEach((x) => problems.push(`${iso(t)} safety: ${x}`)));
    }
  }
  problems.push(...world.errors.map((e) => 'Sleeper refused: ' + e));
  // Claims only in the evening before the waiver run, and nothing picked up then dropped again.
  world.log.filter((l) => l[0] === 'claim' && !(l[1] >= Date.parse('2026-10-20T16:00:00Z') && l[1] < WAIVER_RUN))
    .forEach((l) => problems.push(`claim for ${l[2]} at ${iso(l[1])}, outside the claim window`));
  const added = world.tx.filter((x) => x.roster_ids[0] === 1).flatMap((x) => Object.keys(x.adds || {}));
  world.tx.filter((x) => x.roster_ids[0] === 1).forEach((x) => Object.keys(x.drops || {}).forEach((d) => {
    if (added.includes(d)) problems.push(`${d} was picked up and dropped again the same week`);
  }));
  return { world, gas, problems };
}

/** Put the given players on my roster in place of others at the same position. */
function give(world, ids) {
  ids.forEach((id) => {
    const pos = world.players[id][1];
    world.rosters.forEach((ro) => { ro.players = ro.players.filter((p) => p !== id); });
    const mine = world.me.players;
    const out = mine.filter((p) => world.players[p][1] === pos);
    world.me.players = mine.filter((p) => !out.includes(p)).concat(id);
    world.lineup = world.lineup.map((p) => (out.includes(p) ? '0' : p));
    world.me.starters = world.lineup;
  });
}

test('a whole week in a superflex league with rolling waivers: byes, injuries, inactives, a rival', () => {
  const { world, problems } = runWeek({ seed: 7, superflex: true, rolling: true, passTd: 6, rivalClaims: [] }, (w) => {
    give(w, ['NYG_K', 'ARI_TE1']);   // kicker and only tight end on bye
    w.players.ARI_TE1[3] = null;
    // Saturday: a starting RB in a late game is ruled out; Sunday: a WR is inactive 80 minutes before kickoff.
    const lateRb = Object.keys(w.players).find((p) => w.players[p][1] === 'RB' && w.kickoffOf[w.players[p][2]] === KICK.LATE);
    w.rosters.forEach((ro) => { ro.players = ro.players.filter((p) => p !== lateRb); });
    w.me.players.push(lateRb);
    w.at(Date.parse('2026-10-24T12:00:00Z'), () => { w.players[lateRb][3] = 'Out'; });
    const earlyWr = w.me.players.find((p) => w.players[p][1] === 'WR' && w.kickoffOf[w.players[p][2]] === KICK.EARLY);
    if (earlyWr) w.at(KICK.EARLY - 80 * 60000, () => { w.players[earlyWr][3] = 'Out'; });
  });
  assert.deepEqual(problems, []);
  // The kicker's bye was covered: whoever started at K played this week.
  const k = world.lineup[world.slots.indexOf('K')];
  assert.ok(k !== '0' && world.kickoffOf[world.players[k][2]], 'K slot: ' + k);
});

test('a whole week in a 1QB league (W/R flex): claims Tuesday, free agents after the waiver run', () => {
  const { world, problems } = runWeek({ seed: 11, flex: 'WRRB_FLEX', rolling: false });
  assert.deepEqual(problems, []);
  assert.ok(world.log.some((l) => l[0] === 'lineup'), 'the lineup was saved at least once');
});

test('a whole week where a rival claims the players the app wanted', () => {
  const probe = makeWorld({ seed: 23, superflex: true });
  const fas = Object.keys(probe.players).filter((p) => !probe.rosters.some((r) => r.players.includes(p)) &&
    ['RB', 'WR', 'QB'].includes(probe.players[p][1])).sort((a, b) => probe.quality[a] - probe.quality[b]).slice(0, 4);
  const { problems } = runWeek({ seed: 23, superflex: true, rivalClaims: fas });
  assert.deepEqual(problems, []);
});

test('random leagues at random moments of the week: every plan passes the safety rules and Sleeper\'s rules', () => {
  const failures = [];
  for (let seed = 1; seed <= 300; seed++) {
    const r = ((x) => () => { x = (x * 16807) % 2147483647; return x / 2147483647; })(seed * 7919);
    const now = T0 + 8 * 3600000 + Math.floor(r() * 6.8 * 86400000);
    const world = makeWorld({ seed, now, superflex: r() < 0.5, flex: r() < 0.5 ? 'FLEX' : 'WRRB_FLEX', rolling: r() < 0.5,
                              waiversRan: now >= WAIVER_RUN, bench: 4 + Math.floor(r() * 4), injuries: 0.03 + r() * 0.1,
                              passTd: r() < 0.5 ? 6 : 4, priorityShift: Math.floor(r() * 10) });
    world.refreshStatus();
    Object.keys(world.players).forEach((p) => { if (r() < 0.04) world.clears[p] = Math.floor(now / 1000) + 86400; });
    let gas = world.gas();
    gas.setMode('auto');
    gas.saveLeagueSettings('L1', { auto_waivers: true, max_claims: 1 + Math.floor(r() * 3), min_gain: 10 + Math.floor(r() * 20) });
    try {
      const d = gas.getDashboard();
      planProblems(world, d).forEach((x) => failures.push(`seed ${seed}: ${x}`));
      d.leagues.forEach((lg) => (lg.safety || []).forEach((x) => failures.push(`seed ${seed} ${iso(now)}: ${x}`)));
      gas = world.gas();
      gas.tick();
      const last = gas.getJson_('lastTick');
      if (last && last.status === 'error') failures.push(`seed ${seed} ${iso(now)}: check failed: ${last.msg}`);
    } catch (e) {
      failures.push(`seed ${seed} ${iso(now)}: crashed: ${e.message}`);
    }
    world.errors.forEach((e) => failures.push(`seed ${seed}: Sleeper refused: ${e}`));
  }
  assert.deepEqual(failures, []);
});

test('random whole weeks: injuries, players coming back and rivals grabbing free agents at random times', () => {
  const failures = [];
  for (let seed = 101; seed <= 108; seed++) {
    const r = ((x) => () => { x = (x * 48271) % 2147483647; return x / 2147483647; })(seed * 104729);
    const { problems } = runWeek({ seed, superflex: r() < 0.5, flex: r() < 0.5 ? 'FLEX' : 'WRRB_FLEX', rolling: r() < 0.5,
                                   passTd: r() < 0.5 ? 6 : 4, bench: 4 + Math.floor(r() * 4), priorityShift: Math.floor(r() * 10),
                                   cfg: { max_claims: 1 + Math.floor(r() * 3) } }, (w) => {
      const ids = Object.keys(w.players).filter((p) => ['QB', 'RB', 'WR', 'TE'].includes(w.players[p][1]));
      for (let n = 0; n < 12; n++) {
        const when = Date.parse('2026-10-20T10:00:00Z') + Math.floor(r() * 6.5 * 86400000);
        const p = n % 3 === 0 ? w.me.players[Math.floor(r() * w.me.players.length)] : ids[Math.floor(r() * ids.length)];
        const kind = r();
        w.at(when, () => {
          if (kind < 0.5 && w.players[p][1] !== 'K' && w.players[p][1] !== 'DEF') w.players[p][3] = 'Out';
          else if (kind < 0.7) w.players[p][3] = null;   // back from injury
          else if (w.league.settings.leg === 8 && w.isFreeAgent(p)) w.rosters[1 + (n % (w.rosters.length - 1))].players.push(p);
        });
      }
    });
    problems.forEach((x) => failures.push(`seed ${seed}: ${x}`));
  }
  assert.deepEqual(failures, []);
});

test('control: the simulation does notice an unmanaged team (so a clean run means something)', () => {
  const { problems } = runWeek({ seed: 7, superflex: true, cfg: { auto_lineup: false, auto_waivers: false } }, (w) => {
    const rb = w.lineup.find((p) => p !== '0' && w.players[p][1] === 'RB');
    w.at(Date.parse('2026-10-24T12:00:00Z'), () => { w.players[rb][3] = 'Out'; });
  });
  assert.ok(problems.some((x) => /kickoff: .* \(Out\) while/.test(x)), problems.slice(0, 5).join(' | '));
});

module.exports = { runWeek, planProblems };
