# LEDGER — the Mixamo harvest, and picking the clips out of it

**Your part is a token and one command. Everything downstream is handled here.**

## Why it is split this way

The harvest has to run in your own session, under your own login, because it
needs a bearer token from a logged-in Mixamo page. That token is yours and
stays on your machine — it is not something to paste into a chat, and it is not
something I should be holding.

What I *can* do is everything either side of it: the pick list, the matcher,
the report of what is missing, and the Unity import. That is what this folder is.

## Step 1 — the token

1. Log into [mixamo.com](https://mixamo.com) in Chrome.
2. Press **F12** for developer tools, click **Console**.
3. Paste this and press enter:

   ```js
   localStorage.getItem('access_token')
   ```

4. Copy the string it prints, **without the surrounding quotes**.

## Step 2 — the harvest

```bat
git clone https://github.com/paulpierre/MixamoHarvester.git
cd MixamoHarvester
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

Paste the token into a file called `mixamo_token.txt` in that folder, then run
the script per its README.

**Three things worth knowing before you start it:**

- **Turn the thread count DOWN, to 2.** It defaults to 5. This is not about
  speed — a slower, quieter run is less likely to trip a rate limit, and the
  whole thing is unattended anyway.
- **It is resumable.** There is a `state.json`; if it dies or you stop it, it
  picks up where it left off and skips files it already has.
- **Budget the disk.** Roughly 2,500 animations per character, on the order of
  a gigabyte. This does *not* go into the repository — step 3 is what picks the
  ~30 clips that do.

If it only gets partway through, that is fine. Run step 3 on whatever you have;
the report will say what is missing and I will work with the rest.

## Step 3 — the pick

Double-click **`1 PICK.bat`**, or:

```bat
python pick_animations.py --harvest "C:\path\to\MixamoHarvester\animations"
```

It walks the harvest, copies the best match for each clip the game needs into
`ledger/Assets/Characters/A|B|C/`, and writes two files that matter as much as
the FBX:

| file | why |
|---|---|
| `_catalogue.txt` | **every animation name in the harvest.** Worth more than the clips on the first run — every name I have used so far was guessed from memory, and this replaces the guessing |
| `_picks.json` | what matched, what was a substitute rather than an exact hit, and what is missing |

`--tiers A` copies only the twelve clips that unblock combat, if you want to
push something small first.

## Step 4 — push

Commit and push the `ledger/Assets/Characters/` folder — FBX files, catalogue
and picks report together. **Do not go hunting by hand for anything the report
lists as missing.** Send the catalogue and I will pick the real names out of it;
that is exactly the job the catalogue exists to make possible.

## Settings, if you end up downloading anything manually

FBX for Unity · **Without Skin** for animations · T-pose **With Skin** for the
two characters · 30fps · no keyframe reduction.
