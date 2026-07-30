# LEDGER — the Mixamo drop

## Double-click `GO.bat`. That is the whole thing.

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
| 3 | drops the thread count from 5 to 2 |
| 4 | **pins the character list to two bodies** |
| 5 | runs the harvest — resumable, so closing the window costs nothing |
| 6 | picks the ~30 clips the game needs, commits them, pushes to the branch |

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

**Everything else** — send me the last twenty lines of the window.

## An honest caveat

I could not test steps 1–5 end to end: this sandbox's network policy blocks
mixamo.com outright, and it is Linux rather than Windows. What **is** tested is
`pick_animations.py`, against a simulated harvest, which caught two real bugs
before you ever saw it. The rest is written from the harvester's actual source
rather than from assumptions about it — but the first run is the first run, and
if it falls over I would rather you send me the output than fight it.
