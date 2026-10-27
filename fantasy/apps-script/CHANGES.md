# Changes

Newest first. Each `##` entry becomes the release notes shown by the app's
"Install update" button. Add one with every change to Code.gs / Index.html.

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
