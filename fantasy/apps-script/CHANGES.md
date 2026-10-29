# Changes

Newest first. Each `##` entry becomes the release notes shown by the app's
"Install update" button. Add one with every change to Code.gs / Index.html.

## Injury badges
- Players now show Sleeper's injury status as a badge, like on Sleeper: Q (questionable), D (doubtful), O / IR / SUS (out), and BYE. They appear in the lineup, the bench, both sides of the matchup, the waiver and free-agent lists, trade ideas and open offers.
- Tap a badge (or hover on a computer) to see the injury, e.g. "Questionable (Ankle)".

## League tabs, matchup projections, trade finder
- Each league has its own tab, and Activity (the history) has one too, so the page is much shorter. A dot on a tab means that league needs you.
- This week's matchup at the top of each league: every player's projected points for you and your opponent, the totals and your chance of winning, for the lineups as set or the best ones. During games it shows live points plus what's still to come, refreshing every 2 minutes while the page is open.
- Trade finder: Find trades checks every team for trades where both lineups get better for the rest of the season and yours gets better by more, with Offer on Sleeper to send one. Nothing is ever sent without your tap, and starred players are never offered.
- Open trade offers (sent and received) are listed with what they're worth to you.

## Safety checks
- Every plan is now checked against plain safety rules before anything changes. If a plan breaks one (that would be a bug), nothing happens in that league, automatically or with the buttons, and the league card says why.
- Fixed: a free-agent upgrade could choose to drop a player whose game had already started, which Sleeper doesn't allow.
- The free-agent and waiver plans now make their moves one at a time on the roster as it will be, so they no longer get in each other's way. No move leaves this week's lineup with a spot nobody can play in, swaps one empty spot for a harder one to fill (like the only QB who plays for a flex), or relies on another claim winning (including claims already pending on Sleeper).
- Claims still pending after the waiver run only go through next week, so they no longer hide (or invent) an empty spot this week.
- An upgrade that also fills an empty starting spot does both jobs (no second fill-in for the same spot). Fill-ins get first pick of the cheap bench players, and a player just picked up is never dropped for a one-week fill-in.
- A kicker or defense on bye who isn't top-12 is swapped for the fill-in instead of dropping a bench player. A top one already covered for his bye gets a better streamer in place of the cover, never a third kicker. A kicker who plays is never joined by a worse one just because a roster spot is open.
- Fixed: claims already pending on Sleeper (made on sleeper.com or by the app) could block a needed fill-in or show a false safety alarm after submitting.
- "Submit claims now" no longer reports a changed plan when free-agent pickups are also on screen.
- If Sleeper can't say who is still on waivers, no claims are planned, since they could be for free agents.
- If sending a claim fails, the autopilot tries again on its next check instead of giving up for the week.
- Position minimums count the claims already pending, and with a high rolling waiver priority an open roster spot no longer invites a marginal claim.
- The phone alerts card is gone.
- Behind the scenes, every update is now tested on simulated whole weeks and hundreds of random leagues, and a daily check runs the safety rules on your real leagues. An independent review's findings are kept as tests.

## Waiver plan after the waiver run
- After Wednesday's waiver run, players nobody claimed are free agents, so upgrades to them now show up under "Free agents now" (Add now, or the autopilot with auto claims on) instead of as claims that wouldn't process until next week. The waiver plan only lists players who are actually on waivers.
- Players on a bye week count as free agents until the week's first game, like on Sleeper.
- A player you picked up in the last 7 days needs twice the usual gain to be dropped again, so a fresh pickup isn't dropped the next day.
- A spare kicker/defense shows its real rest-of-season rank instead of "#999".
- The waiver plan and the free-agent plan never drop the same player, and free-agent upgrades count toward "Upgrades per week".

## Free-agent pickups
- After Wednesday's waiver run, starters who can't play (byes, injuries, kickers and defenses) are covered with free agents right away, without spending waiver priority.
- The autopilot does this in leagues with "Auto waiver claims and free agents" on; otherwise the league card shows the pickups with an "Add now" button (and an alert, if alerts are on).
- Only real free agents are picked up: not on a roster, not just dropped, and their game hasn't started. Pickups work exactly like sleeper.com's Add button.
- With a high rolling waiver priority, kicker/defense matchup swaps now come from free agency after waivers instead of being skipped.

## Phone alerts, bye-week fill-ins, smarter lineups
- Phone alerts (optional, through the free ntfy app): when something needs you, when the autopilot changes something, and when an update is out. In suggestions-only mode they tell you what to change.
- When a starter at any position is on bye or out and your bench can't fill in, the waiver plan picks up a one-week fill-in (until now only kickers and defenses got one).
- Tap ☆ next to a player to keep him: the waiver plan will never drop him.
- 6-point passing TDs (both your leagues) now count: QBs get a bigger superflex lean and higher waiver values.
- Rolling waivers (Wolfpack): with a high priority, upgrades must gain twice as much, and kicker/defense matchup swaps are skipped so the priority isn't wasted.
- Of two close starters, the later game goes in the flex, so a late scratch can still be swapped; a Questionable player needs to rank clearly better than a healthy one.
- Lighter on Sleeper: quiet checks download nothing, and the player list is fetched every 6 hours plus once after each game's inactives are announced.
- The buttons wait for a running background check, so two saves never overlap.

## Safety fixes from a full review
- If Sleeper's player list fails to download, the app keeps using its last copy, and it never takes a player out of your lineup without putting someone in.
- "Check lineups now" no longer changes anything in suggestions-only mode; it only tells you what it would change.
- "Submit claims now" sends exactly the claims on screen. If the plan changed since the page loaded, nothing is sent and you see the new plan.
- Waiver plans no longer drop the same player twice, treat a pending no-drop claim's roster spot as free, or let an injured pickup replace a healthy player you need.
- If your pending claims can't be read, no claims are submitted (they could repeat yours); the autopilot tries again later.
- Leagues with Monday waivers get their claims on Sunday evening instead of almost a week late.
- Failed checks now show as errors under "Last check" and are logged once, and a problem in one league no longer stops the other.
- Smaller fixes: no false bye warnings for defensive (IDP) players, text you're typing survives the update check, toggles update the page right away, and updates come from main once the app is merged there.

## Waiver fixes: weekly limit, kicker byes
- Claims already pending on Sleeper now count toward your weekly limit, so no surprise extra suggestions.
- When your top kicker/defense is on bye, it adds a one-week replacement by dropping an easy-to-replace bench player instead of leaving the spot empty.
- After the bye, the spare kicker/defense is the first player dropped for the next pickup.

## Lineups actually save
- "Apply now" (and the autopilot) now save the lineup for the right week: Sleeper keeps one lineup per week, and the old call only covered the league's current week, which lags a day behind. Sleeper quietly ignored it.
- After saving, the app checks what Sleeper stored and shows an error if it didn't take.
- No more pointless slot swaps (e.g. two RBs trading the RB and flex spots).

## Smarter waiver claims
- Won't drop a top-12 kicker or defense just to stream one week (e.g. during his bye).
- Won't stack extra QBs/TEs beyond useful depth at the cost of other positions; a 4th QB can only replace a QB.
- Injured (Out/IR) players no longer count toward position minimums, so it keeps enough healthy starters.

## Fix garbled "On a computer" steps
- Google cut off everything after "//" in the sleeper.com links, which scrambled the connect steps (and would have broken your profile picture). Links are now written so nothing gets cut.

## Updates without Google's script API
- "Install update" now stores the new version inside the app, so it no longer needs Google's Apps Script API, a Cloud project or extra permissions.
- If an installed update ever fails to load, the app runs the version you pasted and offers to remove the update.

## Connect via sleeper.com first
- Fixes "Invalid argument …/user/\"…\"": the user id copied from sleeper.com comes wrapped in quotes.
- The app now opens on "Connect via sleeper.com", since Sleeper blocks password logins from other sites with a captcha.
- Checks which Google permissions you actually granted (Google's screen has a checkbox for each) and shows an "Approve in Google" button for any that are missing.

## Easier "connect via sleeper.com"
- When Sleeper asks for a captcha, a "Connect via sleeper.com" button appears right under the message.
- Clearer phone steps, and a copy-paste console line for computers.
- If an update can't install, the message links straight to your script editor and quotes Google's reason.

## Install updates from the app
- New "Install update" button: future versions install from GitHub with one tap, no more pasting.
- The app shows which version it is running.

## Log in from your browser
- The login goes straight from your browser to Sleeper, which fixes "unable to confirm you're human".
- Clearer message when Sleeper wants a captcha, plus a phone-friendly sleeper.com fallback.

## First version
- Dashboard with Sleeper login, autopilot lineups and waiver claims.
