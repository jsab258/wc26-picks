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
2. Open [`dist/SleeperAutopilot.gs`](dist/SleeperAutopilot.gs) (use the
   **Raw** button), select all and copy. In the editor, replace the sample
   code with it and press **Ctrl/Cmd + S**.
3. Click **Deploy → New deployment**, then the gear icon → **Web app**:
   - *Execute as*: **Me**
   - *Who has access*: **Only myself**
   - Click **Deploy**.
4. Authorise it. Google warns *"Google hasn't verified this app"* because you
   just wrote it yourself. Click **Advanced → Go to Sleeper Autopilot**, then
   **Allow**. It asks for two permissions:
   - **Connect to an external service:** Sleeper and FantasyPros.
   - **Run when you are not present:** the 30-minute checks.
5. Open the **Web app URL** it shows. Bookmark it, or add it to your phone's
   home screen. Then log in with your Sleeper email and password. If Sleeper
   emails you a 4-digit code, enter it there.

It starts in **suggestions only** mode. Look over the plan, then flip the
switch to turn the autopilot on.

### Updating to a newer version

Paste the new `SleeperAutopilot.gs` over the old code and save. Then go to
**Deploy → Manage deployments → ✏️ → Version: New version → Deploy**. The URL
and your login stay the same.

## What you see

- **Status:** autopilot on/off, the last background check and what it did,
  and when your Sleeper session expires.
- **Each league:** detected rules (PPR/half/standard, 1QB/superflex/2QB,
  FAAB, TE premium, 6-pt pass TD), plus:
  - this week's best lineup, with injured or bye starters flagged and new
    starters marked **IN**, and an **Apply now** button;
  - the waiver plan (add / drop / FAAB bid) with **Submit claims now**;
  - settings: auto lineup, auto claims, K/DEF streaming, superflex QB lean,
    claims per week, minimum upgrade.
- **Activity:** every change the autopilot or you made, and any errors.

## How it decides

The logic is the same as the Python CLI in `../autopilot` (see `../README.md`).
- **Lineups:** an exact assignment over the league's slots, using the weekly
  ECR list for its scoring. In superflex it uses FantasyPros' superflex list,
  plus the QB lean.
  - It never starts players who are Out, on IR, Doubtful or on bye.
  - It never moves a player whose game has started.
- **Waivers:** rest-of-season ECR, with QBs re-valued for superflex and 2QB.
  - It keeps your best starters and position minimums.
  - FAAB bids scale with player value.
  - Claims go in the evening before your waiver day: for your leagues,
    Tuesday ~18:00 UTC, ahead of Sleeper's Wednesday ~07:10 UTC run. They are
    never repeated.
- **Background checks:** every 30 minutes, but they only touch lineups when
  games are less than 30 hours away. Player injury data refreshes every 25
  minutes close to kickoff, so game-day inactives get benched.

## Caveats

- Logging in and saving changes use Sleeper's **private** web API, the same
  calls sleeper.com makes. It's unofficial: it can break without notice, and
  automated use may go against Sleeper's terms.
- If Sleeper ever rejects the saved session, the app forgets it, logs it once
  and shows the login again. Nothing changes on Sleeper until you log back
  in.
- If the password login stops working (e.g. Sleeper starts requiring a
  captcha), use **Trouble logging in?** to paste your session from
  sleeper.com instead.

## Development

```
node --test fantasy/apps-script/test/*.test.js      # offline tests
node fantasy/apps-script/dev/bundle.js              # rebuild dist/ after editing Code.gs / Index.html
DEMO_USER_ID=<sleeper user id> node fantasy/apps-script/dev/server.js
```

The preview server at http://localhost:8080 runs `Code.gs` on Apps Script
stand-ins (`dev/gas-stub.js`). It reads real data but fakes logins and never
sends writes: log in with password `demo` and code `1234`.
