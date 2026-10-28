// Early warning, run every day by .github/workflows/sleeper-autopilot-canary.yml:
// plans every league of SLEEPER_USERNAME with this repo's Code.gs against live data
// and fails if anything errors or the data looks broken (FantasyPros or Sleeper
// changed their format). It never logs in, writes nothing, and prints no lineups
// or claims, because the repo's Actions logs are public.
//   SLEEPER_USERNAME=jsab258 node fantasy/apps-script/dev/canary.js
const { loadGas } = require('./gas-stub');

const username = process.env.SLEEPER_USERNAME || 'jsab258';
const problems = [];
// Only the public league_players read (who's still on waivers) may reach Sleeper's GraphQL.
const gas = loadGas({ gql: (body) => {
  if (/^\s*query league_players\(/.test(body.query)) return undefined;  // sent for real, without a login
  throw new Error('the canary never talks to Sleeper GraphQL beyond league_players');
} });
gas.pendingWaivers_ = () => [];  // private (needs a login); the plan just assumes none
gas.pendingTrades_ = () => [];   // the same for open trade offers
const clears = gas.waiverClears_;
gas.waiverClears_ = (token, leagueId) => clears(null, leagueId);
gas.setStarters_ = gas.submitClaim_ = gas.addFreeAgent_ = gas.proposeTrade_ = () => { throw new Error('the canary never writes'); };

const user = gas.sleeper_('/user/' + username);
if (!user) throw new Error('Sleeper user not found: ' + username);
gas.__props.setProperty('token', 'canary.canary.canary');
gas.putJson_('user', { user_id: user.user_id, display_name: user.display_name });

// The data the plans are built from.
const ctx = new gas.Ctx_('canary');
const players = Object.keys(ctx.players).length;
console.log(`Sleeper players: ${players}, week ${ctx.state.week}`);
if (players < 1500) problems.push(`only ${players} players in Sleeper's player list`);
const slugs = [gas.FP.OP.PPR, gas.FP.FLEX.PPR, gas.FP.QB, gas.FP.K, gas.FP.DST, gas.FP.ROS.PPR, gas.FP.ROS_K, gas.FP.ROS_DST];
for (const slug of slugs) {
  const list = ctx.ranks(slug);
  const total = list.byId.size + list.unmatched.length;
  const share = total ? list.byId.size / total : 0;
  console.log(`FantasyPros ${slug}: week ${list.week}, ${list.byId.size}/${total} players matched`);
  if (total < 20 || share < 0.85) problems.push(`FantasyPros ${slug}: ${list.byId.size}/${total} players matched`);
}

// Every league plans without errors.
const dash = gas.getDashboard();
for (const lg of dash.leagues) {
  const parts = [];
  if (lg.status !== 'in_season') { console.log(`${lg.name}: ${lg.status}, skipped`); continue; }
  if (lg.notes.some((n) => /Couldn't load/.test(n))) problems.push(`${lg.name}: ${lg.notes.join(' ')}`);
  if (lg.lineup) {
    if (lg.lineup.error) problems.push(`${lg.name} lineup: ${lg.lineup.error}`);
    parts.push('lineup ' + (lg.lineup.error ? 'FAILED' : lg.lineup.skipped ? 'skipped (' + lg.lineup.skipped + ')' : 'ok'));
  }
  if (lg.waivers) {
    if (lg.waivers.error) problems.push(`${lg.name} waivers: ${lg.waivers.error}`);
    parts.push('waivers ' + (lg.waivers.error ? 'FAILED' : 'ok'));
  }
  if (lg.freeAgents) {
    if (lg.freeAgents.error) problems.push(`${lg.name} free agents: ${lg.freeAgents.error}`);
    parts.push('free agents ' + (lg.freeAgents.error ? 'FAILED' : lg.freeAgents.waiting ? 'waiting for waivers' : 'ok'));
  }
  const M = lg.matchup;
  if (M) {
    if (M.error) problems.push(`${lg.name} matchup: ${M.error}`);
    else if (!M.none && !(M.me && M.me.current.total > 0)) problems.push(`${lg.name} matchup: no projected points`);
    parts.push('matchup ' + (M.error ? 'FAILED' : M.none ? 'none this week' : 'ok'));
  }
  try {
    const T = gas.findTrades(lg.id, {});
    parts.push('trades ' + (T.closed ? 'closed' : 'ok'));
  } catch (e) {
    problems.push(`${lg.name} trade finder: ${e.message}`);
    parts.push('trades FAILED');
  }
  // The same safety rules the app applies before changing anything.
  (lg.safety || []).forEach((x) => problems.push(`${lg.name} safety check: ${x}`));
  parts.push('safety ' + ((lg.safety || []).length ? 'FAILED' : 'ok'));
  console.log(`${lg.name}: ${parts.join(', ')}`);
}
if (!dash.leagues.length) problems.push('no leagues found for ' + username);

if (problems.length) {
  console.error('\nPROBLEMS:\n- ' + problems.join('\n- '));
  process.exit(1);
}
console.log('\nAll good.');
