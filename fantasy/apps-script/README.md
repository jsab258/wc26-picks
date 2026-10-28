# Sleeper Autopilot web app (Google Apps Script)

A dashboard you log in to with your Sleeper account. It sets your lineups and
waiver claims from FantasyPros consensus rankings (ECR), following each
league's own rules.

It runs inside **your own Google account** as an Apps Script web app:
- Only your Google login can open the page.
- Your Sleeper session is kept in your private script storage. Your password
  is never saved.
- It checks every 30 minutes, even when your computer is off.

## Setup (once, about 3 minutes, on a computer)

1. Open [script.new](https://script.new) to create a new Apps Script project.
   Name it *Sleeper Autopilot*.
2. Open `Code.gs` and replace it with
   [`dist/SleeperAutopilot.gs`](dist/SleeperAutopilot.gs) (use the **Raw**
   button, then select all and copy). Save.
3. Click **Deploy → New deployment**, then the gear icon → **Web app**:
   - *Execute as*: **Me**
   - *Who has access*: **Only myself**
   - Click **Deploy**.
4. Authorise it. Google warns *"Google hasn't verified this app"* because you
   just wrote it yourself. Click **Advanced → Go to Sleeper Autopilot**. Then
   tick **Select all**, because every permission has its own checkbox and an
   unticked one isn't granted, and click **Continue**. It asks for:
   - **Connect to an external service:** Sleeper, FantasyPros, GitHub.
   - **Run when you are not present:** the 30-minute checks.
5. Open the **Web app URL** it shows. Bookmark it, or add it to your phone's
   home screen. Then connect your Sleeper account. Log in on sleeper.com
   itself, where Sleeper shows its captcha, and copy your session over:
   - **Computer:** one line in the browser console.
   - **Phone:** a small helper bookmark.

   The steps are on that screen. Sleeper blocks password logins from other
   sites with a captcha that only works on sleeper.com, so the app's
   password form (*Log in with password instead*) rarely gets through.

It starts in **suggestions only** mode. Look over the plan, then flip the
switch to turn the autopilot on. In suggestions-only mode nothing changes on
Sleeper unless you tap **Apply now** or **Submit claims now**; **Check lineups
now** only reports what it would change.

`appsscript.json` is optional: Google works out the same two permissions from
the code.

### Updates

When a newer version is on GitHub, the app shows **Update available** with
the release notes. Tap **Install update**, then reload, and that's it. No
redeploying, no extra Google permissions.
- **How it works:** the app stores the new version in its private script
  storage and loads it on top of the code you pasted, on every run (page,
  buttons, 30-minute checks).
- **Where updates come from:** this repo's `main` branch once it has the app
  (the development branch until then), and only when you tap the button.
- **If something goes wrong:** if an installed update fails to load, the app
  runs the pasted version and offers **Remove the update**.
- **Pasting a version by hand:** the pasted code always wins over a stored
  update. Paste the new `SleeperAutopilot.gs`, save, then
  **Deploy → Manage deployments → ✏️ → Version: New version → Deploy**.

## What you see

- **Status:** autopilot on/off, the last background check and what it did.
- **A tab per league** (a dot marks one that needs you), and an **Activity** tab.
- **Each league:** detected rules (PPR/half/standard, 1QB/superflex/2QB,
  FAAB, TE premium, 6-pt pass TD), plus:
  - this week's matchup: every player's projected points for you and your
    opponent, both totals and your chance of winning, for the lineups as set
    or the best ones. During games it shows live points plus the projection
    for the time left, refreshing every 2 minutes while the page is open;
  - this week's best lineup, with injured or bye starters flagged and new
    starters marked **IN**, and an **Apply now** button;
  - the waiver plan (add / drop / FAAB bid) with **Submit claims now**;
  - after Wednesday's waiver run, the free agents to pick up now, with
    **Add now**;
  - a ☆ next to each player: tap it to never let the waiver plan drop him
    (or trade him);
  - trade ideas with every other team (**Find trades**), and **Offer on
    Sleeper** to send one;
  - settings: auto lineup, auto claims and free agents, K/DEF streaming,
    bye/injury fill-ins, superflex QB lean, upgrades per week, minimum upgrade.
- **Safety check:** if a plan ever breaks one of the app's safety rules (a bug),
  the league card says so in red and nothing in that league is changed until it's fixed.
- **Activity:** every change the autopilot or you made, any errors, and the
  background check schedule.

## How it decides

- **Lineups:** an exact assignment over the league's slots, using the weekly
  ECR list for its scoring. In superflex it uses FantasyPros' superflex list,
  plus the QB lean (bigger with 6-point passing TDs, which ECR doesn't assume).
  - It never starts players who are Out, on IR, Doubtful or on bye.
  - It never moves a player whose game has started.
  - A Questionable player has to rank 2 spots better than a healthy one.
  - Of two close starters, the later game goes in the flex, so he can still
    be swapped for almost anyone if he's ruled out late.
- **Waivers:** rest-of-season ECR, with QBs re-valued for superflex and 2QB
  and for 6-point passing TDs.
  - It keeps your best starters, position minimums and starred players.
  - When a starter can't play this week and the bench can't fill in, it
    picks up a one-week fill-in, giving up an easy-to-replace bench player.
  - With rolling waivers, a high priority is only spent on a clear upgrade or
    a fill-in, not on a kicker/defense matchup swap.
  - After the waiver run, upgrades to free agents and starters who can't
    play (byes, injuries, kickers and defenses) are handled with free agents
    right away, which costs no waiver priority; the waiver plan then only
    lists players who are on waivers. Only true free agents count, as on
    Sleeper: not on a roster, not just dropped, and their game not started
    (bye-week players until the week's first game). Pickups work like
    sleeper.com's Add button.
  - A player picked up in the last 7 days needs twice the usual gain to be
    dropped again.
  - FAAB bids scale with player value.
  - Claims go in the evening before your waiver day: for your leagues,
    Tuesday from 16:00 UTC, ahead of Sleeper's Wednesday ~07:10 UTC run. They are
    never repeated.
- **Matchup projections:** Sleeper's own weekly projections, scored with
  the league's scoring settings (so 6-point passing TDs count), and Sleeper's
  live points. The win chance assumes a typical weekly swing that shrinks as
  the games are played.
- **Trades:** each player is worth rough points per game from the same
  rest-of-season values the waiver plan uses. A trade's worth to a team is how
  much it raises that team's best lineup in every remaining week (bye weeks
  included, the best free agent filling any gap, playoff weeks counting half).
  The finder tries one-for-one, two-for-one and one-for-two trades with every
  team and keeps those where both teams gain and you gain more. Starred players
  are never offered, it never takes you over the roster limit, and it marks
  teams in a playoff spot and your opponent this week. Offers go out only when
  you tap the button, the way sleeper.com sends them; the autopilot never trades.
- **Background checks:** every 30 minutes, but they only do something when
  games are less than 30 hours away or claims are due; otherwise they don't
  download anything. Sleeper's player list (injury news) refreshes every 6
  hours and again once each game's inactives are announced, so game-day
  inactives get benched.

## Caveats

- Logging in and saving changes use Sleeper's **private** web API, the same
  calls sleeper.com makes. It's unofficial: it can break without notice, and
  automated use may go against Sleeper's terms.
- If Sleeper ever rejects the saved session, the app forgets it, logs it once
  and shows the login again. Nothing changes on Sleeper until you log back
  in.
- Sleeper puts a captcha in front of password logins. The app never tries to
  get around that. You log in on sleeper.com and bring the session over
  instead.

## Development

```
node --test fantasy/apps-script/test/*.test.js      # offline tests
node fantasy/apps-script/dev/bundle.js              # rebuild dist/ after editing Code.gs / Index.html
DEMO_USER_ID=<sleeper user id> node fantasy/apps-script/dev/server.js [--fake-update]
node fantasy/apps-script/dev/canary.js              # plan the leagues from live data, writing nothing
```

To ship a change:
1. Edit `Code.gs` / `Index.html`.
2. Add an entry at the top of `CHANGES.md`. Those are the release notes, and
   the entry count is the version number.
3. Run the bundler, commit and push.

The app then offers the update once the change is in `main`. GitHub runs the
tests and the bundle check on every push
(`.github/workflows/sleeper-autopilot-tests.yml`), so a stale `dist/` file
shows up as a failed check.

How bugs are kept out:
- **Safety rules** (`checkPlans_` in `Code.gs`): plain rules every plan must
  pass, checked separately from the planning code (no claim for a free agent,
  no player dropped twice, no starred or just-picked-up player dropped for a
  small gain, nothing that breaks Sleeper's rules, no internal values on screen,
  roster size and weekly limit respected, no move that leaves this week's lineup
  with a spot nobody can play in, a sensible lineup). A plan that breaks one is
  never carried out, by the autopilot or the buttons.
- **Week simulation** (`test/simulation.test.js`, `test/world.js`): a fake
  Sleeper league that runs the real app every 30 minutes for whole weeks (claims,
  the waiver run, free agency, kickoffs, byes, injury news, inactives, rivals
  taking players), enforcing Sleeper's rules on every write and checking the
  plans and the lineup at every kickoff. It also checks hundreds of random leagues
  at random moments of the week, and a control run proves it notices problems.
  `test/fuzz.test.js` adds hundreds of random leagues with claims pending on
  Sleeper, starred players, fresh pickups, open roster spots and Sunday locks
  (`FUZZ_N=4000` for more). New features get covered here before they ship.
- **Independent review**: before a bigger change ships, a reviewer that didn't
  write it hunts for bugs with runnable repros. Every confirmed finding becomes a
  test in `test/plans.test.js` (built on the small configurable league in
  `test/fixture.js`), checked to fail on the code before the fix:
  `GAS_CODE=<old Code.gs> node --test test/plans.test.js` runs the tests (and the
  simulation) against another copy of `Code.gs`.
- **Daily canary** (`.github/workflows/sleeper-autopilot-canary.yml`): plans your
  real leagues from live data every day, writing nothing, and applies the safety
  rules. A failure (a bug, or FantasyPros or Sleeper changing something) fails
  the run, and GitHub emails you.

The preview server at http://localhost:8080 runs `Code.gs` on Apps Script
stand-ins (`dev/gas-stub.js`). It reads real data but fakes logins and never
sends writes: log in with password `demo` and code `1234`. Even the page's
own browser-side Sleeper calls are rerouted to local fakes, so the preview
can't send a real login.
