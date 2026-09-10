# The move to its own repo: the plan, the measurements, and the one card

STATUS: LIVE, verified 2026-09-10. Ruling 2 of Jafar's cleanup batch of
2026-09-10: LEDGER gets its own repo named `ledger`, this branch becomes main,
LFS for files over 2MB, `wc26-picks` stays as the archive, the BTC branch is not
carried, and the move happens LAST. The three steps only Jafar can do arrive as
ONE card, which is section 4.

## 1. What is actually being moved, measured 2026-09-10

- tracked files: 5026, totalling 1727.0 MB
- tracked files over 2MB: 101, totalling 1113.2 MB
- those 101 by kind: 56 jpg, 22 png, 18 fbx, 4 hdr, 1 gif
- largest five, all Mixamo character bodies: Adam.fbx 83.2 MB, Pete.fbx 62.2 MB,
  Martha.fbx 54.1 MB, Elizabeth.fbx 53.6 MB, James.fbx 52.1 MB
- the `.git` directory on this machine: 2.6 GB
- `.gitattributes`: DOES NOT EXIST. There is no LFS anywhere in this repo today,
  so every one of those 1113.2 MB is a plain git object.
- workflows: 18, of which 9 run on the self-hosted Windows runner.

## 2. The fact that decides the shape of the move

LFS applied to a new repo catches NEW commits. It does not reach back into
history. If the new `ledger` repo is created by pushing this branch's existing
history, the 1113.2 MB of large blobs arrive as ordinary git objects exactly as
they are today, and LFS only helps files added from that point on. Getting the
existing blobs into LFS means rewriting history, which changes every commit sha
in the project.

So there are two shapes, and they differ in what the new repo's first commit is:

- **CLEAN START.** The new repo's main begins as one initial commit holding this
  branch's tree. LFS is in force from commit 1, so the big files are in LFS and
  the repo clones small. The history of how the project got here lives in
  `wc26-picks`, which ruling 2 already keeps as the archive. Commit shas do not
  carry over, so every sha cited in a decision record points at the archive.
- **CARRY THE HISTORY.** The new repo gets the full history, shas keep meaning,
  and the clone is about 2.6 GB with LFS helping only future files.

The ruling's own words point at the clean start: `wc26-picks` stays as the
archive, which is where a history belongs, and LFS for files over 2MB only
actually happens under the clean start. RECOMMENDED: clean start. This is in
section 4's card because it is not mine to decide: it makes every commit sha in
170 decision records an archive reference.

## 3. What I have NOT verified, and will not assert

GitHub's included LFS storage and bandwidth allowance, and the price of
additional capacity. `docs.github.com` is blocked by this container's egress
proxy, so I could not read the figures, and I am not going to state numbers I
could not check. What matters is the comparison, so the card asks Jafar to read
the allowance off his own billing page and weigh it against the measured
1113.2 MB in section 1. If that payload exceeds the included allowance, LFS
capacity is a PURCHASE, and every purchase is his.

There is a cheaper path if it does: the 18 fbx bodies are 305.2 MB of the
1113.2 MB and they are Mixamo downloads, refetchable with his account and token.
They could stay out of the repo behind a fetch script rather than occupy paid
LFS. This is not proposed, only costed, and it waits on the open question about
which bodies are v1.

## 4. THE CARD: the three things only Jafar can do

One card, delivered by the Producer, nothing started until it is answered.

1. **Create the repo and let this session reach it.** Create an empty repo named
   `ledger` under his account, and grant the Claude GitHub App access to it.
   Without the second half, sessions cannot push and the move cannot be proven.
   This session's GitHub access is scoped to `jsab258/wc26-picks` and creating a
   repo uses his account, so both halves are his.
2. **Re-register the self-hosted Windows runner against the new repo.** 9 of 18
   workflows run on it, and it is registered to `wc26-picks`. It needs its
   config script run again on his machine against `ledger`. THIS IS THE STEP
   THAT MATTERS MOST: CI is the only feedback channel this project has, so a
   move that leaves the runner behind blinds the studio until it is done.
3. **Decide the two questions in sections 2 and 3.** Clean start or carry the
   history. And whether the measured 1113.2 MB sits inside his included LFS
   allowance, read off his own billing page, because if it does not then LFS is
   a purchase.

## 5. The order, once the card is answered

Nothing here starts before section 4 is answered.

1. Write `.gitattributes` with the LFS patterns covering the five extensions
   measured in section 1, and prove the patterns match all 101 files by name
   before any push.
2. Push to `ledger` in the agreed shape, with main as the default branch. The
   BTC branch is not carried.
3. ONE ROUND TRIP, PROVEN, BEFORE ANYTHING IS FROZEN: dispatch a job on the new
   repo and verify its EFFECTS, not its exit code. A committed evidence file
   under `game-design/sim-shots/` naming the new repo's commit on line 1 is the
   proof. Ancestry alone does not prove a payload: queue 229 exists because a
   landed run was read as a produced one.
4. Only after that round trip lands: `wc26-picks` becomes the archive, and this
   branch stops being pushed to.
