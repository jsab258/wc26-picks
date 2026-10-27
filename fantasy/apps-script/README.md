# Sleeper Autopilot web app (Google Apps Script)

A dashboard you log in to with your Sleeper account. It sets your lineups and
waiver claims from FantasyPros consensus rankings (ECR), following each
league's own rules.

It runs inside **your own Google account** as an Apps Script web app:
- Only your Google login can open the page.
- Your Sleeper session is kept in your private script storage. Your password
  is never saved.
- It checks every 30 minutes, even when your computer is off.

## Setup (once, about 5 minutes, on a computer)

1. Turn on the **Google Apps Script API** at
   [script.google.com/home/usersettings](https://script.google.com/home/usersettings).
   This lets the app install its own updates.
2. Open [script.new](https://script.new) to create a new Apps Script project.
   Name it *Sleeper Autopilot*.
3. Click **⚙️ Project Settings** and tick *Show "appsscript.json" manifest
   file in editor*. Back in the editor, open `appsscript.json` and replace its
   contents with [`appsscript.json`](appsscript.json). Save.
4. Open `Code.gs` and replace it with
   [`dist/SleeperAutopilot.gs`](dist/SleeperAutopilot.gs) (use the **Raw**
   button, then select all and copy). Save.
5. Click **Deploy → New deployment**, then the gear icon → **Web app**:
   - *Execute as*: **Me**
   - *Who has access*: **Only myself**
   - Click **Deploy**.
6. Authorise it. Google warns *"Google hasn't verified this app"* because you
   just wrote it yourself. Click **Advanced → Go to Sleeper Autopilot**, then
   **Allow**. It asks for:
   - **Connect to an external service:** Sleeper, FantasyPros, GitHub.
   - **Run when you are not present:** the 30-minute checks.
   - **Create and update Apps Script projects and deployments:** installing
     updates.
7. Open the **Web app URL** it shows. Bookmark it, or add it to your phone's
   home screen. Then connect your Sleeper account. Log in on sleeper.com
   itself, where Sleeper shows its captcha, and copy your session over:
   - **Computer:** one line in the browser console.
   - **Phone:** a small helper bookmark.

   The steps are on that screen. Sleeper blocks password logins from other
   sites with a captcha that only works on sleeper.com, so the app's
   password form (*Log in with password instead*) rarely gets through.

It starts in **suggestions only** mode. Look over the plan, then flip the
switch to turn the autopilot on.

### Updates

When a newer version is on GitHub, the app shows **Update available** with
the release notes. Tap **Install update**, then reload, and that's it. Updates
come from this repo's `main` branch (or the development branch until it's
merged), and only when you tap the button. The update permission technically
lets the app edit your Apps Script projects. It only ever rewrites itself.

If an update can't install (e.g. the Apps Script API is off), it says why.
The manual way still works: paste the new `SleeperAutopilot.gs`, save, then
**Deploy → Manage deployments → ✏️ → Version: New version → Deploy**.

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
- Sleeper puts a captcha in front of password logins. The app never tries to
  get around that. You log in on sleeper.com and bring the session over
  instead.

## Development

```
node --test fantasy/apps-script/test/*.test.js      # offline tests
node fantasy/apps-script/dev/bundle.js              # rebuild dist/ after editing Code.gs / Index.html
DEMO_USER_ID=<sleeper user id> node fantasy/apps-script/dev/server.js [--fake-update]
```

To ship a change:
1. Edit `Code.gs` / `Index.html`.
2. Add an entry at the top of `CHANGES.md`. Those are the release notes, and
   the entry count is the version number.
3. Run the bundler, commit and push.

The app then offers the update.

The preview server at http://localhost:8080 runs `Code.gs` on Apps Script
stand-ins (`dev/gas-stub.js`). It reads real data but fakes logins and never
sends writes: log in with password `demo` and code `1234`. Even the page's
own browser-side Sleeper calls are rerouted to local fakes, so the preview
can't send a real login.
