# The playtest runbook — getting LEDGER onto the MacBook and keeping it there

> **STATUS: LIVE**, verified 2026-08-15. Everything needed to run the
> Wednesday 19 Aug playtest on the MacBook Air, written to be followed
> at a kitchen table, not at a desk. The final build link lands here
> Tuesday; every other step is already true.

## Getting the build (5 minutes, needs your GitHub login)

1. Open the repository's **Actions** tab → **LEDGER macOS build** →
   the newest green run → scroll to **Artifacts** → download
   **LEDGER-macOS**.
2. That download is a zip CONTAINING a zip (GitHub wraps what the
   build made). Unzip twice: the download gives `LEDGER-mac.zip`,
   and THAT gives `LEDGER.app`. Use the Finder's own double-click —
   Archive Utility restores the app's permissions from the inner zip.
3. Drag `LEDGER.app` somewhere real (Desktop is fine). Do not run it
   from inside the Downloads zip window.

Artifacts expire after 14 days. If the link is dead, any newer green
run of the same workflow carries the same artifact name.

## First launch (the Gatekeeper dance, once per machine)

The app is not signed or notarised (an Apple Developer ID is a
purchase, and we do not purchase). macOS will refuse a plain
double-click the first time.

1. **Right-click `LEDGER.app` → Open → Open.** That is usually the
   whole dance on a fresh download.
2. If macOS still refuses ("cannot be opened" with no Open button),
   open Terminal, then:

       xattr -dr com.apple.quarantine ~/Desktop/LEDGER.app

   (adjust the path to wherever the app is), then double-click again.
3. If the app bounces once and dies, the executable bit was lost —
   only possible if step 2 of "Getting the build" was skipped and the
   inner zip was extracted by something other than Archive Utility:

       chmod +x ~/Desktop/LEDGER.app/Contents/MacOS/LEDGER

Once it has opened once, it opens normally forever.

## Conversations need the key (2 minutes, once)

Characters answer as themselves through a language model. Without a
key every character says "(no API key configured)" — the street still
talks, barks still play, the game is playable but conversations are
mute.

1. Start a game, press **F2**, paste the Anthropic API key, confirm.
2. The key is stored on the laptop only (`secrets.json` in the app's
   own data folder). It never enters the repository.
3. **F1** shows live spend. A heavy evening of typed conversation
   measures under a dollar; three days stays well under ten.

**If the café wifi dies mid-conversation:** the reply fails inside
about half a minute and the game carries on — recorded voices, street
talk and everything mechanical keep working. It recovers by itself
when the network does.

## The Air runs best one notch down

Options (from the title screen or Escape in game):

- **Graphics: Medium** — the first-run default. High is there if the
  frame rate holds.
- **Render scale: Balanced** — half the pixels of the Retina panel,
  hard to spot in motion, and the single biggest frame-rate lever on
  this machine. Drop to Fast if it still stutters.

## Three players, one laptop

- **New game** wipes the previous run completely — the autosave AND
  every character's memory of the last player. A fresh start is
  genuinely fresh; nobody inherits anybody's reputation.
- To KEEP a run while somebody else plays: pause → **Keep a copy**
  (a numbered slot). Slots survive New game. But the street's memory
  is shared — reopening a kept slot after somebody else's run keeps
  the money and progress, while the people remember the town's most
  recent history. One live run at a time is the honest mode; slots
  are snapshots, not parallel lives.
- **Cmd-Q saves on the way out.** So does the pause menu's "Save and
  quit".

## The controls card (defaults — all rebindable under Options → Controls)

| key | does |
|---|---|
| WASD | walk |
| Shift | run |
| E | talk to whoever you are facing |
| L | your ledger — what the street knows about you |
| J | plan a job |
| C | the runner's coat |
| F | drive / stop driving |
| T | use a telephone box |
| F5 | save |
| Escape | close panel / pause |

In conversation: type anything and press Return, or click a chip.
"leave it" actually leaves. The game teaches the first four of these
in its first morning.

## Known limits, so nobody debugs the intended

- **Voices are the recorded bank.** Live per-line speech generation
  needs a GPU this laptop does not have; it is parked, not missing.
  Named characters speak their recorded lines; novel sentences appear
  as text.
- Gossip tellings (a rumour retold in someone's words) are text-only
  by nature — they are composed fresh every time.
- The frame-time budget on this machine is the render-scale option's
  job, not a bug report.

## If it all goes wrong

The Windows tower build (same game, same save format) is the fallback
venue; the artifact lives under **LEDGER build (Windows)** in the same
Actions tab. Say so in the group chat and play on.
