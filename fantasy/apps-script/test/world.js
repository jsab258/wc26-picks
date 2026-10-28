/**
 * A small fake Sleeper + FantasyPros world for whole-week simulations and random
 * leagues. It enforces Sleeper's rules on every write the app makes (locked players
 * can't move, only real free agents can be added, claims are processed at the waiver
 * run...) and records every rule the app breaks in `world.errors`.
 */
const { loadGas } = require('../dev/gas-stub');

const DAY = 86400000;
const T0 = Date.parse('2026-10-20T00:00:00Z');   // a Tuesday; NFL week 8 runs Thu-Mon
const WEEK = 8;
const KICK = {
  TNF: Date.parse('2026-10-23T00:15:00Z'), EARLY: Date.parse('2026-10-25T17:00:00Z'),
  LATE: Date.parse('2026-10-25T20:25:00Z'), SNF: Date.parse('2026-10-26T00:20:00Z'),
  MNF: Date.parse('2026-10-27T00:15:00Z'),
};
const SCHEDULE = {
  TNF: ['KC', 'BUF'], EARLY: ['DET', 'NYJ', 'MIA', 'SEA', 'LV', 'CHI', 'MIN', 'TB', 'ATL', 'NO', 'CLE', 'PIT', 'IND', 'TEN', 'JAX', 'CAR'],
  LATE: ['LAR', 'SF', 'DAL', 'PHI', 'DEN', 'LAC'], SNF: ['GB', 'CIN'], MNF: ['HOU', 'BAL'], BYE: ['NYG', 'ARI', 'NE', 'WAS'],
};
const WAIVER_RUN = Date.parse('2026-10-21T07:05:00Z');   // Wednesday ~03:05 New York time
const SLOT_POS = { QB: ['QB'], RB: ['RB'], WR: ['WR'], TE: ['TE'], K: ['K'], DEF: ['DEF'],
                   FLEX: ['RB', 'WR', 'TE'], WRRB_FLEX: ['WR', 'RB'], REC_FLEX: ['WR', 'TE'], SUPER_FLEX: ['QB', 'RB', 'WR', 'TE'] };

function rng(seed) {
  let s = (seed * 2654435761) >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

/**
 * opts: seed, superflex, flex ('FLEX' | 'WRRB_FLEX'), rolling (waiver type), teams,
 * bench, passTd, now (ms), waiversRan (league leg already = week), injuries (share).
 */
function makeWorld(opts = {}) {
  const r = rng(opts.seed || 1);
  const pick = (a) => a[Math.floor(r() * a.length)];
  const world = { now: opts.now || T0 + 8 * 3600000, errors: [], tx: [], pending: [], clears: {}, log: [] };
  const kickoffOf = {};
  Object.keys(SCHEDULE).forEach((slot) => SCHEDULE[slot].forEach((t) => { kickoffOf[t] = KICK[slot] || null; }));
  world.kickoffOf = kickoffOf;
  const firstKick = KICK.TNF;

  // Players: a QB, 2 RBs, 3 WRs, a TE, a K and the defense for every team.
  const players = {}, quality = {};
  Object.keys(kickoffOf).forEach((team) => {
    const add = (id, name, pos, q) => { players[id] = [name, pos, team, null, null]; quality[id] = q + r() * 0.6; };
    add(team + '_QB1', team + ' QB', 'QB', r());
    [1, 2].forEach((n) => add(team + '_RB' + n, team + ' RB' + n, 'RB', r() * (n === 1 ? 1 : 1.6)));
    [1, 2, 3].forEach((n) => add(team + '_WR' + n, team + ' WR' + n, 'WR', r() * (1 + (n - 1) * 0.5)));
    add(team + '_TE1', team + ' TE', 'TE', r() * 1.3);
    add(team + '_K', team + ' K', 'K', r());
    add(team, team + ' D/ST', 'DEF', r());
  });
  Object.keys(players).forEach((p) => {
    if (players[p][1] === 'K' || players[p][1] === 'DEF') return;
    const x = r();
    if (x < (opts.injuries ?? 0.06)) players[p][3] = 'Out';
    else if (x < (opts.injuries ?? 0.06) * 2.5) players[p][3] = 'Questionable';
  });
  world.players = players;
  world.quality = quality;

  // League and rosters (a draft by quality, with position caps).
  const sf = !!opts.superflex;
  const slots = ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', opts.flex || 'FLEX'].concat(sf ? ['SUPER_FLEX'] : [], ['K', 'DEF']);
  const benchN = opts.bench ?? 6;
  const positions = slots.concat(Array(benchN).fill('BN'));
  const nTeams = opts.teams || 10;
  const caps = { QB: sf ? 3 : 2, RB: 5, WR: 5, TE: 2, K: 1, DEF: 1 };
  const order = Object.keys(players).sort((a, b) => quality[a] - quality[b]);
  const rosters = [];
  for (let i = 0; i < nTeams; i++) {
    rosters.push({ roster_id: i + 1, owner_id: i === 0 ? 'me' : 'u' + i, players: [], starters: [], reserve: [], taxi: [],
                   settings: { waiver_position: 1 + ((i + (opts.priorityShift || 0)) % nTeams), waiver_budget_used: 0 } });
  }
  const need = slots.length + benchN;
  for (let round = 0; round < need; round++) {
    for (let k = 0; k < nTeams; k++) {
      const ro = rosters[round % 2 ? nTeams - 1 - k : k];
      const count = (pos) => ro.players.filter((p) => players[p][1] === pos).length;
      const minimal = { K: 1, DEF: 1, QB: sf ? 2 : 1, TE: 1 };
      const left = need - ro.players.length;
      const missing = Object.keys(minimal).filter((pos) => count(pos) < minimal[pos]);
      const p = order.find((id) => !rosters.some((x) => x.players.includes(id)) && count(players[id][1]) < caps[players[id][1]] &&
        (left > missing.length || missing.includes(players[id][1])) && (r() > 0.25 || !opts.seed));
      if (p) ro.players.push(p);
    }
  }
  // Like a real season: rivals have let some good players go (a few were dropped only
  // a day ago and are still on waivers), so there are upgrades to find.
  const others = rosters.slice(1).flatMap((ro) => ro.players.map((p) => [ro, p]))
    .filter(([, p]) => ['QB', 'RB', 'WR', 'TE'].includes(players[p][1]));
  for (let n = 0; n < (opts.released ?? 10) && others.length; n++) {
    const [ro, p] = others.splice(Math.floor(r() * Math.min(others.length, 60)), 1)[0];
    ro.players = ro.players.filter((x) => x !== p);
    if (r() < 0.3) world.clears[p] = Math.floor((opts.now || T0 + 8 * 3600000) / 1000) + 86400;
  }
  world.rosters = rosters;
  world.me = rosters[0];
  world.league = {
    league_id: 'L1', name: 'Sim League', status: 'in_season', roster_positions: positions,
    scoring_settings: { rec: 1, pass_td: opts.passTd || 4 },
    settings: { waiver_type: opts.rolling ? 0 : 1, waiver_day_of_week: 2, daily_waivers: 0, leg: opts.waiversRan ? WEEK : WEEK - 1,
                waiver_budget: 100, waiver_bid_min: 0 },
  };
  world.slots = slots;
  world.limit = positions.length;
  // A deliberately poor starting lineup: roster order, whoever fits.
  world.lineup = slots.map((slot) => world.me.players.find((id) => SLOT_POS[slot].includes(players[id][1])) || '0');
  dedupe(world.lineup);
  world.me.starters = world.lineup;

  // ---- FantasyPros lists -------------------------------------------------------------
  const isBye = (team) => !kickoffOf[team];
  const row = (id, rank, posRank, weekly) => {
    const team = players[id][2], pos = players[id][1] === 'DEF' ? 'DST' : players[id][1];
    return [id, players[id][0], pos, team, rank, posRank, isBye(team) ? String(WEEK) : '14',
            weekly && !isBye(team) ? 'vs. X' : '', weekly ? kickoffOf[team] / 1000 || null : null,
            weekly && kickoffOf[team] && kickoffOf[team] <= world.now ? 'inprogress' : 'created'];
  };
  const listOf = (ids, weekly, noise) => {
    const scored = ids.map((id) => [id, quality[id] + (noise ? (r() - 0.5) * noise : 0)]).sort((a, b) => a[1] - b[1]);
    const seen = {};
    return scored.map(([id], i) => {
      const pos = players[id][1] === 'DEF' ? 'DST' : players[id][1];
      seen[pos] = (seen[pos] || 0) + 1;
      return row(id, i + 1, pos + seen[pos], weekly);
    });
  };
  const skill = Object.keys(players).filter((p) => ['QB', 'RB', 'WR', 'TE'].includes(players[p][1]));
  const playing = (ids) => ids.filter((p) => !isBye(players[p][2]));
  const ofPos = (pos) => Object.keys(players).filter((p) => players[p][1] === pos);
  world.lists = {
    'ppr-superflex': { week: WEEK, label: 'sf', players: listOf(playing(skill), true, 0.3) },
    'ppr-flex': { week: WEEK, label: 'flex', players: listOf(playing(skill.filter((p) => players[p][1] !== 'QB')), true, 0.3) },
    qb: { week: WEEK, label: 'qb', players: listOf(playing(ofPos('QB')), true, 0.3) },
    k: { week: WEEK, label: 'k', players: listOf(playing(ofPos('K')), true, 0.4) },
    dst: { week: WEEK, label: 'dst', players: listOf(playing(ofPos('DEF')), true, 0.4) },
    'ros-ppr-overall': { week: 0, label: 'ros', players: listOf(skill, false, 0) },
    'ros-k': { week: 0, label: 'ros-k', players: listOf(ofPos('K'), false, 0) },
    'ros-dst': { week: 0, label: 'ros-dst', players: listOf(ofPos('DEF'), false, 0) },
  };
  // RankList marks a game as started from these timestamps; keep "status" in step with the clock.
  world.refreshStatus = () => Object.values(world.lists).forEach((l) => l.players.forEach((x) => {
    x[9] = x[8] && x[8] * 1000 <= world.now ? 'inprogress' : 'created';
  }));

  // ---- Sleeper's rules ------------------------------------------------------------------
  const rostered = (p) => world.rosters.some((ro) => ro.players.includes(p));
  const started = (p) => { const k = kickoffOf[players[p][2]]; return !!k && k <= world.now; };
  const isFreeAgent = (p) => !rostered(p) && !(world.clears[p] > world.now / 1000) &&
    (kickoffOf[players[p][2]] || firstKick) > world.now;
  world.isFreeAgent = isFreeAgent;
  world.started = started;
  const err = (msg) => { world.errors.push(new Date(world.now).toISOString().slice(5, 16) + ' ' + msg); throw new Error(msg); };
  const drop = (ro, p) => {
    ro.players = ro.players.filter((x) => x !== p);
    if (ro === world.me) world.lineup = world.lineup.map((x) => (x === p ? '0' : x));
    world.me.starters = world.lineup;
    world.clears[p] = Math.floor(world.now / 1000) + 2 * 86400;
  };

  world.setStarters = (starters) => {
    if (starters.length !== slots.length) err('lineup has the wrong number of slots');
    const seen = {};
    starters.forEach((p, i) => {
      if (p === '0') return;
      if (seen[p]) err(p + ' starts twice');
      seen[p] = true;
      if (!world.me.players.includes(p)) err(p + ' is not on the roster');
      if (!SLOT_POS[slots[i]].includes(players[p][1])) err(p + ' cannot play ' + slots[i]);
      if (started(p) && world.lineup[i] !== p) err(p + ' is locked but was moved in');
    });
    world.lineup.forEach((p, i) => { if (p !== '0' && started(p) && starters[i] !== p) err(p + ' is locked but was moved out'); });
    world.lineup = starters.slice();
    world.me.starters = world.lineup;
    world.log.push(['lineup', world.now]);
  };
  world.submitClaim = (add, dropId) => {
    if (rostered(add)) err('claim for ' + add + ', who is on a roster');
    if (world.league.settings.leg === WEEK && isFreeAgent(add)) err('claim for ' + add + ', who is a free agent right now');
    if (dropId && !world.me.players.includes(dropId)) err('claim drops ' + dropId + ', who is not on the roster');
    if (world.pending.some((t) => t.add === add)) err('second claim for ' + add);
    world.pending.push({ add, drop: dropId || null, rid: 1 });
    world.log.push(['claim', world.now, add, dropId]);
  };
  world.addFreeAgent = (add, dropId) => {
    if (world.league.settings.leg !== WEEK) err('free-agent add before the waiver run: ' + add);
    if (!isFreeAgent(add)) err(add + ' is not a free agent');
    if (dropId && !world.me.players.includes(dropId)) err('drops ' + dropId + ', who is not on the roster');
    if (dropId && started(dropId)) err('drops ' + dropId + ', whose game has started');
    if (world.me.players.length + 1 - (dropId ? 1 : 0) > world.limit) err('roster too big after adding ' + add);
    if (dropId) drop(world.me, dropId);
    world.me.players.push(add);
    world.tx.push({ type: 'free_agent', status: 'complete', leg: world.league.settings.leg, roster_ids: [1],
                    adds: { [add]: 1 }, drops: dropId ? { [dropId]: 1 } : null, status_updated: world.now });
    world.log.push(['fa', world.now, add, dropId]);
    return { adds: { [add]: 1 }, status: 'complete' };
  };

  // ---- events ---------------------------------------------------------------------------
  world.events = [];
  world.at = (time, fn) => world.events.push({ time, fn });
  world.at(WAIVER_RUN, () => {
    const claims = (opts.rivalClaims || []).map((add) => ({ add, drop: null, rid: 2 })).concat(world.pending);
    claims.forEach((c) => {
      const ro = world.rosters.find((x) => x.roster_id === c.rid);
      const ok = !rostered(c.add) && (!c.drop || ro.players.includes(c.drop)) &&
        ro.players.length + 1 - (c.drop ? 1 : 0) <= world.limit;
      if (ok) {
        if (c.drop) drop(ro, c.drop);
        ro.players.push(c.add);
        world.tx.push({ type: 'waiver', status: 'complete', leg: WEEK - 1, roster_ids: [c.rid], adds: { [c.add]: c.rid },
                        drops: c.drop ? { [c.drop]: c.rid } : null, status_updated: world.now });
      }
    });
    world.pending = [];
    world.league.settings.leg = WEEK;
  });

  world.advance = (to) => {
    world.events.sort((a, b) => a.time - b.time);
    while (world.events.length && world.events[0].time <= to) {
      const e = world.events.shift();
      world.now = e.time;
      e.fn();
    }
    world.now = to;
    world.refreshStatus();
  };

  // ---- this week's matchup: me against roster 2, games 3 hours long ----------------------
  const GAME = 3 * 3600000;
  world.proj = (p) => 4 + (seededHash(p) % 160) / 10;   // a stable projection per player
  world.elapsed = (p) => {
    const k = kickoffOf[players[p][2]];
    return !k ? 0 : Math.max(0, Math.min(1, (world.now - k) / GAME));   // kickoffs are in ms
  };
  world.games = () => {
    const out = {};
    Object.keys(kickoffOf).forEach((t) => {
      const e = Math.max(0, Math.min(1, (world.now - kickoffOf[t]) / GAME));
      out[t] = e <= 0 ? { status: 'pre', left: 1, clock: null } : e >= 1 ? { status: 'post', left: 0, clock: null }
        : { status: 'in', left: 1 - e, clock: 'Q' + (1 + Math.floor(e * 4)) + ' 7:30' };
    });
    return out;
  };
  world.matchups = () => {
    const opp = world.rosters[1], used = {};
    const oppLineup = world.slots.map((slot) => {
      const p = opp.players.find((x) => !used[x] && SLOT_POS[slot].includes(players[x][1]));
      if (p) used[p] = true;
      return p || '0';
    });
    const points = (list) => Object.fromEntries(list.filter((p) => p !== '0').map((p) => [p, Math.round(world.proj(p) * world.elapsed(p) * 10) / 10]));
    return [{ roster_id: 1, matchup_id: 1, starters: world.lineup.slice(), players_points: points(world.me.players) },
            { roster_id: 2, matchup_id: 1, starters: oppLineup, players_points: points(opp.players) }];
  };

  // ---- the app, wired to this world ---------------------------------------------------
  world.gas = () => {
    const gas = loadGas({ now: () => world.now, props: world.props, file: process.env.GAS_CODE });  // GAS_CODE: test another Code.gs
    world.props = gas.__props._data;
    gas.fpList_ = (slug) => world.lists[slug];
    gas.playersSlim_ = () => world.players;
    gas.fpToSleeper_ = () => Object.fromEntries(Object.keys(world.players).map((k) => [k, k]));
    gas.latestBuild_ = () => null;
    gas.sleeper_ = (path) => {
      if (path === '/state/nfl') return { week: WEEK, league_season: '2026' };
      if (path.includes('/leagues/nfl/')) return [JSON.parse(JSON.stringify(world.league))];
      if (/\/rosters$/.test(path)) return JSON.parse(JSON.stringify(world.rosters));
      const m = /\/matchups\/(\d+)$/.exec(path);
      if (m) return Number(m[1]) === WEEK ? world.matchups() : [];
      const t = /\/transactions\/(\d+)$/.exec(path);
      if (t) return world.tx.filter((x) => x.leg === Number(t[1]));
      if (path.endsWith('/users')) return [];
      return null;
    };
    gas.pendingWaivers_ = () => world.pending.map((c) => ({ roster_ids: [1], adds: { [c.add]: 1 }, drops: c.drop ? { [c.drop]: 1 } : {} }));
    gas.pendingTrades_ = () => [];
    gas.projectedPoints_ = () => Object.fromEntries(Object.keys(world.players).map((p) => [p, world.proj(p)]));
    gas.gameStates_ = () => world.games();
    gas.waiverClears_ = () => Object.assign({}, world.clears);
    gas.setStarters_ = (token, lid, rid, starters) => world.setStarters(Array.from(starters));
    gas.submitClaim_ = (token, lid, rid, add, d) => world.submitClaim(add, d);
    gas.addFreeAgent_ = (token, lid, rid, add, d) => world.addFreeAgent(add, d);
    if (!world.props || !gas.__props.getProperty('token')) {
      gas.__props.setProperty('token', 'a.b.c');
      gas.putJson_('user', { user_id: 'me', display_name: 'me' });
    }
    return gas;
  };
  return world;
}

function seededHash(s) {
  let h = 7;
  for (const c of String(s)) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return h;
}

function dedupe(lineup) {
  const seen = {};
  lineup.forEach((p, i) => { if (p !== '0' && seen[p]) lineup[i] = '0'; seen[p] = true; });
}

/**
 * How many starting spots ``roster`` can fill this week with players who can still play
 * (players whose game started keep their spot or stay benched). With ``ignoreStarted``, as if
 * no game had started (for claims that go through before the week's games).
 */
function fillable(world, roster, ignoreStarted) {
  const P = world.players;
  const started = (p) => !ignoreStarted && world.started(p);
  const canPlay = (p) => P[p][3] !== 'Out' && !!world.kickoffOf[P[p][2]] && !started(p);
  let n = 0;
  const open = [], held = new Set();
  world.slots.forEach((slot, i) => {
    const p = world.lineup[i];
    if (p !== '0' && started(p) && roster.includes(p)) { held.add(p); n++; } else open.push(slot);
  });
  const pool = roster.filter((p) => !held.has(p) && canPlay(p));
  const match = {};  // player -> index into open (augmenting paths)
  const assign = (si, seen) => pool.some((p) => {
    if (seen.has(p) || !SLOT_POS[open[si]].includes(P[p][1])) return false;
    seen.add(p);
    if (match[p] === undefined || assign(match[p], seen)) { match[p] = si; return true; }
    return false;
  });
  open.forEach((_, si) => { if (assign(si, new Set())) n++; });
  return n;
}

module.exports = { makeWorld, T0, WEEK, KICK, WAIVER_RUN, DAY, SLOT_POS, fillable };
