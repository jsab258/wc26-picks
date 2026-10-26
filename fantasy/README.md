# Sleeper autopilot (FantasyPros ECR)

Sets your Sleeper lineups and waiver claims from FantasyPros Expert Consensus
Rankings, following each league's own rules. Runs on a schedule in GitHub
Actions. **Dry run by default:** nothing changes on Sleeper until you turn it on.

## What it does

**Lineups** (Thu, Sun ×4, Mon): for every league, it reads the roster slots and
scoring, pulls the matching weekly ECR and saves the best legal lineup.
- It benches players who are Out, IR, Doubtful, suspended or on bye.
- It never touches a player whose game has started. Sleeper locks those
  players, so the bot leaves them where they are.
- Players stay in their current slot when only the order would change, so
  there are no pointless edits.

**Superflex:** the bot uses FantasyPros' weekly *superflex* ECR, which ranks
QBs against RB/WR/TE. On top of that, `superflex_qb_bonus` makes a QB look N
ECR spots better in the SUPER_FLEX slot, so close calls go to the 2nd QB.

**Waivers** (Tue evening):
- Uses rest-of-season ECR to find free agents who clearly beat your weakest
  bench player.
- In superflex and 2QB leagues, QBs are re-valued to superflex worth.
  FantasyPros has no ROS superflex list, so ROS positional ranks are mapped
  through this week's superflex ECR.
- Always keeps your ROS-best starting lineup, plus a minimum per position
  (3 QBs in superflex).
- Sizes FAAB bids to the player's value and your remaining budget.
- Streams K/DEF when next week's ECR shows a clearly better option.
- Skips claims you already have pending.

### How league rules are respected

| League setting | Effect |
|---|---|
| Points per reception | PPR / Half / Standard ECR (nearest match) |
| `SUPER_FLEX` or 2 QB slots | Superflex ECR, QB-valued waivers, keeps 3 QBs |
| `FLEX`, `WRRB_FLEX`, `REC_FLEX` | Correct eligibility per slot |
| K / DEF slots | Only ranked and streamed if the league has them |
| FAAB vs. rolling waivers | Bids only in FAAB leagues |
| IR / taxi | Never started, don't count against roster size |
| Best ball | Lineups skipped |
| IDP slots | Left exactly as you set them |

TE premium and 6-pt passing TDs are flagged in the report. ECR is per format,
not per custom scoring, so it's only an approximation there.

## Setup

1. Put your Sleeper username in `config.toml`.
2. Dry run locally (Python 3.11+, no dependencies):
   ```
   cd fantasy
   python3 -m autopilot all
   ```
3. Get your Sleeper token. Sign in at sleeper.com in a desktop browser and
   open DevTools (F12):
   - **Network** tab: click any `graphql` request and copy the
     `authorization` request header. Or:
   - **Console**: run `localStorage.getItem("token")`.

   Treat the token like your password.
4. In GitHub, open **Settings → Secrets and variables → Actions**:
   - Add the secret `SLEEPER_TOKEN`.
   - Run the **Sleeper autopilot** workflow manually with *apply* unchecked,
     then read the job summary.
   - When you trust it, add the **variable** `AUTOPILOT_APPLY` = `true`. That
     enables lineups. Set `auto_waivers = true` in `config.toml` to also let it
     submit claims.
5. Scheduled runs only fire from the default branch, so merge this to `main`.

Manual runs: `python3 -m autopilot lineup --apply` (needs `SLEEPER_TOKEN` in the
environment). Use `--league <id>` to target one league.

### Privacy

This repo is public, so Actions logs are too. Lineup moves are visible on
Sleeper anyway, but your pending claims and FAAB bids are not. The workflow
therefore hides claim details unless you set the variable
`SHOW_WAIVER_DETAILS=true`. Only do that in a private repo. Moving `fantasy/`
and the workflow into a private repo is the cleanest option, and private repos
get 2,000 free Actions minutes a month (this uses roughly 30).

### FantasyPros account

The consensus rankings pages work without logging in. To fetch them as your
paid account instead (e.g. if you customised which experts count), put your
browser's `Cookie` header for fantasypros.com in the secret
`FANTASYPROS_COOKIE`. This is untested.

## Config knobs (`config.toml`)

| Key | Default | Meaning |
|---|---|---|
| `superflex_qb_bonus` | 10 | ECR spots a QB gains in SUPER_FLEX |
| `bench_statuses` | Out, IR, PUP, Sus, Doubtful, NA, DNR, COV | Never start these |
| `max_claims` | 2 | Claims per league per run |
| `min_gain` | 20 | Pickup must beat the drop by this many ROS ECR spots |
| `faab_tiers` | see file | `[value, share of remaining budget]` |
| `stream_k_def`, `stream_margin` | true, 6 | K/DEF streaming threshold |
| `never_drop` | [] | Names or Sleeper ids |
| `min_roster` | derived | e.g. `{ QB = 3, TE = 2 }` |

Any key can be overridden per league under `[league."<league id>"]`.

## Caveats

- **Sleeper's write API is unofficial.** Reads use the public API. Saving
  lineups and claims uses the private GraphQL calls the Sleeper web app makes
  with your token. They can change without notice, and automated use may go
  against Sleeper's terms. You decide whether that risk is acceptable.
  Scraping FantasyPros pages has the same caveat.
- When the token expires or is revoked (e.g. logging out everywhere), the
  workflow fails and GitHub emails you. Paste a fresh token into the secret.
- Claims go in Tuesday evening, ahead of Sleeper's default Wednesday
  processing. If a league clears waivers on another day, change the cron.
  Free-agent pickups after waivers clear are not automated.
- GitHub pauses scheduled workflows in repos with no commits for 60 days.

## Tests

```
python3 -m unittest discover -s tests -t .
```
