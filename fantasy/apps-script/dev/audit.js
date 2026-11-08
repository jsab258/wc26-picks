// Real-league audit: plans the waiver and free-agent moves of many owners in real Sleeper
// leagues (found through SLEEPER_USERNAME's league-mates) with this repo's Code.gs, and flags
// moves that look wrong. Roster rates across the sampled leagues are the independent check:
// they come from real managers, not from the rankings the planner uses. It never logs in and
// writes nothing to Sleeper. It found the backup-QB bug in 1 of 5 upgrades in 1-QB leagues.
//
//   node fantasy/apps-script/dev/audit.js [--leagues 340] [--per 6] [--workers 4] [--min-gain 20]
//
// Prints counts and examples per flag; the full records go to audit-out/ (git-ignored). Flags
// are leads, not verdicts: look at each pattern (the roster, the values) before changing code.
// About 15 minutes for the defaults. Stay near 4 workers: Sleeper allows ~1000 calls a minute.
const fs = require('fs');
const path = require('path');
const { fork } = require('child_process');
const { loadGas } = require('./gas-stub');

const arg = (name, def) => {
  const i = process.argv.indexOf('--' + name);
  return i > 0 ? Number(process.argv[i + 1]) : def;
};
const OUT = path.join(__dirname, '..', 'audit-out');
const LEAGUES = arg('leagues', 340), PER = arg('per', 6), WORKERS = arg('workers', 4), MIN_GAIN = arg('min-gain', 0);
const SLOTS = new Set(['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'FLEX', 'WRRB_FLEX', 'REC_FLEX', 'SUPER_FLEX', 'BN', 'IR', 'TAXI']);
const INJURED = new Set(['Out', 'IR', 'Doubtful', 'Sus', 'PUP', 'NA']);
const superflex = (positions) => positions.includes('SUPER_FLEX') || positions.filter((s) => s === 'QB').length > 1;

const newGas = () => {
  const gas = loadGas({ gql: (b) => {
    if (/^\s*query league_players\(/.test(b.query)) return undefined;  // public: who's on waivers
    throw new Error('the audit never talks to Sleeper GraphQL beyond league_players');
  } });
  gas.pendingWaivers_ = () => [];
  gas.pendingTrades_ = () => [];
  const clears = gas.waiverClears_;
  gas.waiverClears_ = (token, id) => clears(null, id);
  gas.setStarters_ = gas.submitClaim_ = gas.addFreeAgent_ = gas.proposeTrade_ = gas.setReserve_ = () => {
    throw new Error('the audit never writes');
  };
  gas.__props.setProperty('token', 'audit.audit.audit');
  return gas;
};

// ---- Worker: plan as up to PER owners in every WORKERS-th league ----
if (process.env.AUDIT_WORKER) {
  const I = Number(process.env.AUDIT_WORKER) - 1;
  const gas = newGas();
  const leagues = JSON.parse(fs.readFileSync(path.join(OUT, 'leagues.json'))).filter((l, i) => i % WORKERS === I);
  const lines = [];
  for (const data of leagues) {
    let ctx, rosters;
    try {
      ctx = new gas.Ctx_('audit');
      rosters = gas.sleeper_('/league/' + data.league_id + '/rosters', true) || [];
    } catch (e) {
      lines.push({ league: data.league_id, name: data.name, crash: String(e.message || e) });
      continue;
    }
    const owners = rosters.filter((r) => r.owner_id).map((r) => r.owner_id).sort().slice(0, PER);
    for (const owner of owners) {
      const rec = { league: data.league_id, name: data.name, owner, positions: data.roster_positions };
      try {
        const cfg = gas.leagueCfg_(gas.settings_(), data.league_id);
        if (MIN_GAIN) cfg.min_gain = MIN_GAIN;
        const lg = new gas.League_(ctx, data, owner, cfg);
        const view = (p) => { const x = lg.p(p) || [p]; return { id: p, name: x[0], pos: x[1], st: x[3] || null }; };
        const res = lg.evaluate({ lineup: true, freeAgents: true, waivers: true });
        const moves = (P) => (P && P.claims ? P.claims.map((c) => ({
          kind: c.kind, add: view(c.add.id), drop: c.drop ? view(c.drop.id) : null })) : []);
        rec.fa = moves(res.freeAgents);
        rec.w = moves(res.waivers);
        rec.errors = ['lineup', 'freeAgents', 'waivers', 'reserve'].map((k) => res[k] && res[k].error).filter(Boolean);
        rec.safety = res.safety || [];
        rec.roster = lg.activePlayers().map(view);
        rec.maxDepth = lg.maxDepth();
      } catch (e) {
        rec.crash = String(e.stack || e).split('\n').slice(0, 3).join(' | ');
      }
      lines.push(rec);
    }
  }
  fs.writeFileSync(path.join(OUT, 'plans-' + I + '.json'), JSON.stringify(lines));
  process.exit(0);
}

// ---- Main: find leagues, roster rates, run the workers, report ----
fs.mkdirSync(OUT, { recursive: true });
const gas = newGas();
const season = gas.sleeper_('/state/nfl').league_season;
const me = gas.sleeper_('/user/' + (process.env.SLEEPER_USERNAME || 'jsab258'));
const leagues = new Map(), seenUsers = new Set(), queue = [];
const addUser = (uid) => {
  if (seenUsers.has(uid)) return;
  seenUsers.add(uid);
  let ls = [];
  try { ls = gas.sleeper_('/user/' + uid + '/leagues/nfl/' + season) || []; } catch (e) { return; }
  ls.forEach((l) => {
    if (leagues.has(l.league_id) || l.status !== 'in_season' || (l.settings || {}).best_ball) return;
    if (![0, 1, 2].includes(Number((l.settings || {}).type || 0))) return;  // redraft, keeper, dynasty
    if (!(l.roster_positions || []).every((s) => SLOTS.has(s))) return;   // no IDP
    leagues.set(l.league_id, l);
    queue.push(l.league_id);
  });
};
addUser(me.user_id);
while (queue.length && leagues.size < LEAGUES && seenUsers.size < 3000) {
  let users = [];
  try { users = gas.sleeper_('/league/' + queue.shift() + '/users') || []; } catch (e) { continue; }
  for (const u of users) { addUser(u.user_id); if (leagues.size >= LEAGUES) break; }
}
const list = [...leagues.values()].slice(0, LEAGUES);
fs.writeFileSync(path.join(OUT, 'leagues.json'), JSON.stringify(list));

// Roster rate of every player, in 1-QB and superflex leagues separately.
const own = { SF: {}, '1QB': {} }, count = { SF: 0, '1QB': 0 };
for (const l of list) {
  let rs;
  try { rs = gas.sleeper_('/league/' + l.league_id + '/rosters', true) || []; } catch (e) { continue; }
  const b = superflex(l.roster_positions) ? 'SF' : '1QB', seen = new Set();
  count[b]++;
  rs.forEach((r) => (r.players || []).concat(r.reserve || [], r.taxi || []).forEach((p) => seen.add(p)));
  seen.forEach((p) => { own[b][p] = (own[b][p] || 0) + 1; });
}
console.log(`${list.length} leagues (${count['1QB']} 1-QB, ${count.SF} superflex), ${PER} owners each, ${WORKERS} workers`);

Promise.all(Array.from({ length: WORKERS }, (_, i) => new Promise((resolve) => {
  fork(__filename, process.argv.slice(2), { env: Object.assign({}, process.env, { AUDIT_WORKER: String(i + 1) }) })
    .on('exit', resolve);
}))).then(() => {
  const recs = [];
  for (let i = 0; i < WORKERS; i++) {
    const f = path.join(OUT, 'plans-' + i + '.json');
    if (fs.existsSync(f)) recs.push(...JSON.parse(fs.readFileSync(f)));
  }
  const flags = {};
  const flag = (k, s) => { (flags[k] = flags[k] || []).push(s); };
  let moves = 0;
  for (const r of recs) {
    if (r.crash) { flag('crash', r.name + ': ' + r.crash); continue; }
    r.errors.forEach((e) => flag('plan error', r.name + ': ' + e));
    r.safety.forEach((s) => flag('safety alarm', r.name + ': ' + s));
    const b = superflex(r.positions) ? 'SF' : '1QB';
    const rate = (x) => (own[b][x.id] || 0) / count[b];
    const who = (x) => `${x.name} ${x.pos}${x.st ? ' [' + x.st + ']' : ''} (${Math.round(100 * rate(x))}%)`;
    for (const [plan, ms] of [['FA', r.fa], ['W', r.w]]) {
      let roster = r.roster.slice();
      for (const m of ms) {
        moves++;
        const s = `${r.name.slice(0, 28)} | ${plan} ${m.kind}: +${who(m.add)} -${m.drop ? who(m.drop) : '(open spot)'}`;
        const other = !m.drop || m.drop.pos !== m.add.pos;
        if (m.kind === 'upgrade' && b === '1QB' && m.add.pos === 'QB' && other) flag('1-QB league: QB added for a non-QB (must start)', s);
        if (m.kind === 'upgrade' && INJURED.has(m.add.st)) flag('injured player added as an upgrade', s);
        if (m.drop && !['K', 'DEF'].includes(m.drop.pos) && rate(m.drop) - rate(m.add) >= 0.3) {
          flag('drops a player rostered in 30+ points more leagues', s);
        }
        if (m.drop) roster = roster.filter((x) => x.id !== m.drop.id);
        roster.push(m.add);
        const n = roster.filter((x) => x.pos === m.add.pos).length;
        if (m.kind === 'upgrade' && other && r.maxDepth[m.add.pos] !== undefined && n > r.maxDepth[m.add.pos]) {
          flag(`more ${m.add.pos}s than useful depth (injured ones counted)`, s);
        }
      }
    }
  }
  console.log(`${recs.length} plans, ${moves} moves`);
  Object.entries(flags).sort((a, b) => b[1].length - a[1].length).forEach(([k, v]) => {
    console.log(`\n== ${k}: ${v.length}`);
    [...new Set(v)].slice(0, 15).forEach((s) => console.log('  ' + s));
  });
  const bad = (flags.crash || []).length + (flags['plan error'] || []).length + (flags['safety alarm'] || []).length;
  process.exit(bad ? 1 : 0);
});
