# LEDGER — the Mixamo drop

## Never done this before? Download **`SETUP.bat`** and double-click it.

That is the only file you need. It puts the project on your PC, then hands
straight over to the harvest. If git or Python are missing it stops and tells
you which one and where to get it, rather than failing halfway through.

## Already have the project on your PC?

Double-click `tools\mixamo-pick\GO.bat` from inside it.

> It needs the two Python files that sit beside it. A copy run on its own —
> from Downloads, say — will now look in the usual places a clone lands and
> tell you what to do if it cannot find one, rather than failing four steps
> later with a path error the way the first version did.

It opens Mixamo, tells you how to get a token, opens Notepad for you to paste
it, and then does everything else unattended. Come back in a couple of hours
and the clips will be in the repo.

**What you actually do:** log in, press F12, paste one line into the console
(it is already on your clipboard), copy the result, paste into Notepad, save,
close. Maybe ninety seconds.

---

## What it does while you are away

| | |
|---|---|
| 1 | clones MixamoHarvester to `%USERPROFILE%\ledger-mixamo` — **outside the repo**, because the harvest is about a gigabyte and none of it belongs in git |
| 2 | builds a Python environment and installs the dependencies |
| 3 | sets the thread count (2 by default, or whatever `threads.txt` says) |
| 4 | **pins the character list to two bodies** |
| 5 | runs the harvest — resumable, so closing the window costs nothing |
| 6 | picks the ~30 clips the game needs, then hands to `PUSH.bat` to commit and push |

### Step 4 is the one that matters

MixamoHarvester's `main()` is:

```python
characters = get_character_list(bearer_token)
for character_id in characters:
    process_animations_for_character(...)
```

There is no way to limit it — it fetches **every** character in the catalogue,
around a hundred, and runs all ~2,500 animations against each. A quarter of a
million exports, hundreds of gigabytes, days of running, for a game that needs
thirty clips on two bodies.

But `get_character_list` reads `characters.json` from disk when it exists and
only calls the API when it does not. So `choose_characters.py` writes that file
first — one small request — and the whole run is pinned. Two hours instead of a
week, and a great deal politer to Adobe's servers.

It prefers X Bot and Y Bot (neutral bodies: no armour, no capes, no stylised
proportions, because the silhouette gate is about reading a person rather than
a costume). If those are not on your account it says so and prints what it took
instead, rather than quietly harvesting two characters nobody chose.

---

## After the first harvest: `REPICK.bat`

The first pick ran against clip names guessed from memory. The harvest
produced `_catalogue.txt` — the real 2,589 — and the wants list was rebuilt
from it. `REPICK.bat` applies that against the harvest already on your disk:
no downloads, no token, seconds not hours. It pulls, re-picks, commits and
pushes.

Against the real catalogue it fills **41 slots with none missing**, including
a full block start/hold/end/broken set, the fight-idle transitions, `Drawing
Gun`, and stairs up/down — none of which I knew existed while guessing.

## One thing the harvest does NOT get you

It downloads animations **without skin** — motion only, no body. The two
character meshes are still two manual downloads from Mixamo: search **X Bot**
and **Y Bot**, download each as *FBX for Unity*, **T-pose**, **with skin**, and
drop them in `ledger/Assets/Characters/`. Two clicks each, and without them
there is motion data and nothing to move.

## What comes back

Under `ledger/Assets/Characters/`:

| | |
|---|---|
| `A/` `B/` `C/` | the clips, by tier. **A is the twelve that unblock combat** |
| `_catalogue.txt` | **every animation name in the harvest** — worth more than the clips on the first run, because every name I have used so far was guessed from memory and this ends that |
| `_picks.json` | matched / **substituted** / missing, kept apart, because "found something" and "found the right thing" are different claims |

**Do not go hunting by hand for anything listed as missing.** The catalogue is
there so I can pick real names out of it instead of guessing at more.

---

## If something goes wrong

**"Could not pin the characters"** — almost always an expired token. They last
hours, not days. Delete `%USERPROFILE%\ledger-mixamo\MixamoHarvester\mixamo_token.txt`
and run `GO.bat` again.

**It stopped halfway** — just run `GO.bat` again. The harvester keeps a
`state.json`, skips what it already has, and the token check will reuse the one
you pasted.

**"I cannot find choose_characters.py"** — you are running a lone copy of
`GO.bat`. Run it from `tools\mixamo-pick\` inside your clone.

**It is going to take all night** — measured on the real thing: about 6.7
seconds a clip at 2 threads, so two characters is roughly 9 hours. Close the
window, double-click `FASTER.bat`, then `GO.bat` again: one character instead
of two and 5 threads instead of 2 brings it to under two hours, and nothing
already downloaded is repeated.

**"Author identity unknown"** — git will not make a commit until it knows who
you are. `PUSH.bat` now asks once, sets it globally, and never asks again.

**The push was rejected: "fetch first"** — your copy is behind the remote.
`PUSH.bat` rebases before pushing, so just run it again. The harvest does not
need repeating; that is why pushing is its own file.

**Everything else** — send me the last twenty lines of the window.

## An honest caveat

I could not test steps 1–5 end to end: this sandbox's network policy blocks
mixamo.com outright, and it is Linux rather than Windows. The first run proved
that immediately — two bugs, a PowerShell parameter that does not exist on
Windows PowerShell 5.1, and an assumption that the file would be run from the
repo. The thread-limit step now VERIFIES its own patch instead of printing an
error and carrying on regardless, which is the same lesson the noise ring
taught this morning at greater expense. What **is** tested is
`pick_animations.py`, against a simulated harvest, which caught two real bugs
before you ever saw it. The rest is written from the harvester's actual source
rather than from assumptions about it — but the first run is the first run, and
if it falls over I would rather you send me the output than fight it.
