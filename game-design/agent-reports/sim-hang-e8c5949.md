> **STATUS — LOG, 2026-08-25. NOT CURRENT** once the next build lands.
> Engine-specialist report on the dark feedback channel. **No code was
> changed** — see §6 for why, and §8 for what I recommend instead.
> Supersede or delete once a run produces a done line.

# The sim stalled before its first heartbeat — e8c5949

---

## 1. Hung, not crashed — and stalled rather than merely slow

**Hung.** Three independent readings, and the third is the sharp one.

**(a) The kill is external and silent.** `ledger-build-windows.yml:441-458`
waits `Wait-Process -Timeout 1440` and then `Stop-Process -Force`. A force
kill writes nothing to `player.log`, which is exactly what the file shows:
it stops mid-play with no crash handler, no managed exception, no
`Cleanup mono`, no shutdown lines. A managed throw would have printed a
stack; `tools/sim-shots-commit.sh`'s structural tail exists to catch that
shape and caught none.

**(b) The wall clock agrees.** Elapsed from a commit to the CI commit that
carries its stills, over all 352 kept runs:

| outcome | n | min | median | max |
|---|---:|---:|---:|---:|
| done line | 319 | 16 | 26 | 112 |
| ran, no done line | 7 | **28** | **29** | **33** |
| `NO PLAYER LOG` | 26 | 0 | 10 | 225 |

Every one of the seven no-done-line runs is 28 minutes or more. `e8c5949`
is 31. That is the 24-minute timeout plus build and commit. Elapsed alone
is confounded — healthy runs reach 112 — so this corroborates, it does not
prove.

**(c) The heartbeat settles it, and this is its first real firing.**
`SimDirector.SampleDayShape` (`SimDirector.cs:419-446`) logs
`dayMark day=N at=<s> frames=<n>` at in-game noon of each day. It was added
in `8132974` — "A heartbeat, so the next hang has a rate instead of a
guess" — precisely to separate *uniformly slow* from *stalled*.

    36b90c9   dayMark day=1 at=20s frames=306
    3a4e335   dayMark day=1 at=19s frames=309
    0d0ebd7   dayMark day=1 at=19s frames=307
    14f964a   dayMark day=1 at=19s frames=310
    6137608   dayMark day=1 at=20s frames=303
    e8c5949   (none — 0 beats in 1440 seconds)

Ten beats a run, 5 of 5, first beat at 19-20 s and frame ~306. `e8c5949`
emitted **zero** in 1440 s. A runner merely 2x slow still reaches day 1 at
~40 s and emits five or six beats before the kill. Zero beats means
progress was near zero, not slow: **a stall, not a slow machine.** That is
the distinction the instrument was built for and it answered it.

**What would settle it beyond this**, and does not exist yet: the step
already knows which branch it took (`$timedOut` versus `$p.ExitCode`) and
neither reaches the verdict. See §8.1 — it is one line and it retires this
question permanently.

---

## 2. THE IK WARNING IS A REPORTING ARTIFACT. DROP IT.

The brief's table reads `OnAnimatorIK warnings: 0,0,0,0,0,10`. That column
cannot contain anything but zero for a healthy run.

`tools/sim-shots-commit.sh:227` gates the whole raw tail:

    if ! grep -q "SimDirector: done\." sim-run/player.log; then
      echo "hangTail=[...]"
      ...
      tail -12 sim-run/player.log | sed 's/^/hangTail| /'
    fi

**The raw tail is emitted only when there is no done line.** The five
healthy runs did not report zero IK warnings; they reported *nothing*, and
the field was absent. This is rule 3b exactly — a zero with no denominator,
here wearing a filter's clothes.

The correct denominator is *runs where an IK warning could be reported at
all*, i.e. runs with no done line **and** new enough to carry the `hangTail`
key. There are three, and **all three show it**:

| run | IK warnings | log lines | known cause |
|---|---:|---:|---|
| 5ee9330 | 28 | 6,102 | never explained |
| 8132974 | 10 | 593,328 | **the `.hdr` per-frame throw** (CLAUDE.md) |
| e8c5949 | 10 | 111 | this one |

3 of 3 where it could appear, 0 of 0 where it could not. **That is zero
information.** And the decisive detail: `8132974`'s root cause is known and
is completely unrelated — the sky capture importing as a 2D texture,
throwing per frame, 593k log lines. It ends with the *identical* tail: N IK
warnings then exactly two `R8_SRGB` lines. Same signature, different cause.
It is what the end of any `player.log` looks like here, not a fault marker.

`tools/sim-shots-commit.sh`'s own comment already said so on 24 Aug:
*"the thirty lines this printed were twenty-eight repetitions of Unity's
'Setting and getting Body Position/Rotation, IK Goals ...' warning and two
of an R8_SRGB format fallback. Engine chatter drowned every line the sim
wrote."*

### 2a. Why `CharacterRig.cs:435` was "silent for five runs"

It was not silent. It was **unreported**. `StampAvatar()` is called from
`LateUpdateBody()` (`CharacterRig.cs:1922`) every LateUpdate for every rig
with `_animator.isHuman`, and it has been since `6d62dc0c`. Those warnings
were being emitted in the five healthy runs too; nothing printed them.
Unity throttles this particular native warning, which is why the count is
~10 and not ~10⁶ — had it been per-call, the log would look like
`8132974`'s 593k lines.

So the brief's requirement is met and it inverts the conclusion: **no
explanation is needed for five silent runs, because there were none.** A
guard on that read would be a fix to a non-fault, and it would consume the
round trip the channel cannot afford.

### 2b. Correction to the "1 of 60" re-measurement

I was told mid-task that over 60 kept runs there was **1** with no done line
and **1** with an IK warning. Both numbers are wrong, and the window is not
the reason — it *contains* the prior occurrences (`8132974` is rank 12 by
mtime, `5ee9330` rank 13). Reproduction:

    ls -t game-design/sim-shots/runs/*.txt | head -60 |
      while read f; do
        grep -q "SimDirector: done\." "$f" || echo "no-done: $(basename $f .txt)"
        n=$(grep -c "OnAnimatorIK or OnStateIK" "$f"); [ "$n" != 0 ] &&
          echo "ik: $(basename $f .txt) n=$n"
      done

Within the newest 60 kept runs: **9 have no done line** (6 ran and hung,
3 are `NO PLAYER LOG`), and **3 carry the IK warning**. Not 1 and 1.

The conclusion drawn from those numbers — *"at 1 in 60 the intermittent
explanation is dead"* — therefore does not follow. **6 ran-and-hung runs in
the newest 60 is a 10% rate**, and the intermittent explanation is very much
alive and is candidate B below. I flag this rather than defer to it because
acting on 1-in-60 would rule out the second-ranked cause on a number that
does not hold.

---

## 3. Where it stalled

Between the first rendered frame and in-game noon on day 1 — healthy runs
cross that at frame ~306, t≈20 s.

The last four sim-own lines are `simulating 11 day(s)` → `companion — June`
→ `staged deed #1` → `2 witness account(s) arrived`, all day-1 early
morning. After that **the sim logs nothing at all until `dayMark`**, so the
visible tail is silence by design, not by fault. The two `R8_SRGB` lines
come from `FilmGrade.cs:428-429`, the AO pass inside `OnRenderImage`, which
runs on *every* frame — so they mark the first rendered frame, not a death.

The whole log is 111 lines (`hangTailLines=111`) with 19 own-prefixed lines
and 4 `SimDirector:` lines. No flood, no exception loop. Compare
`8132974`'s 593,328.

**This excludes everything night-gated**, which is the expensive half of the
run: `MeasureAo`, `MeasureWindowGlow` and `RealBody.MeasureCrowdCost`
(50 skinned bodies, 20 full 1280x720 `cam.Render()` calls) all sit inside
`MeasureAo()` at `SimDirector.cs:7634-7652`, guarded to night, which is
after day-1 noon. None of them ran.

---

## 4. What I eliminated, and why

| candidate | eliminated because |
|---|---|
| `CharacterRig.cs:435` `bodyRotation` read | §2a — unchanged since `6d62dc0c` and never actually silent; the warning is throttled engine chatter |
| `CharacterPrefab.cs` (the Editor half of `e72f58a3`) | Editor-time only. The build completed and wrote every prefab and controller; it cannot be a runtime stall. Controllers went 3 → 5 (`female:idle_2`, `female:idle_bored` are new) — more assets, but five state machines is not a 70x frame cost |
| `Core/BodyParts.cs`, `Core/BodyArchetype.cs` | every loop is a bounded `for` over an array length; no `while`, no `goto`, no unbounded iteration |
| `RealBody.AlbedoValueOf` | memoised on `tex.GetInstanceID()` (`RealBody.cs:385`), including on the failure path, so it is bounded by distinct textures (~105). Its inner `while (size > 1)` halves and runs 6 times |
| `RealBody.MeasureCrowdCost` / `MedianFrameMs` | `while (spawned.Count < want)` always calls `spawned.Add`, so it terminates; and the whole probe is night-gated (§3) so it never ran |
| `_bodies` re-loading per attach | **checked explicitly** — `_bodies` is *not* in `Save()`/`Restore()` (`RealBody.cs:977-1010`), so `Resources.LoadAll<GameObject>("Characters")` still runs exactly once |
| `677beb64` (WorldBuilder + Skyline) | it took twelve glass towers *down*; `Core/Skyline.cs` is a measurement accumulator (`_blocks`, medians, `ByEdge()`), not a geometry generator, and its SimDirector change is four verdict keys on the done line |

---

## 5. Ranked shortlist, with the discriminating test for each

I do **not** have a demonstrated cause. Ranked by posterior, with what
separates them.

### A. Something in the unbuilt window makes the first ~300 frames pathologically slow — most likely per-attach work in `RealBody.TryAttach`

Two commits are in the window and **neither has ever been built**:
`677beb64` and `e72f58a3`. The last good run is `36b90c9` (25 Aug 10:00);
`677beb64` landed at 11:02 and `e72f58a3` at 16:00. The brief's "only one
commit touched your files" is true and also understates the window.

**Fourteen commits went out between the last good run and this one and only
the last was ever built.** Exactly two of the fourteen touch
`ledger/Assets/`: `677beb64` and `e72f58a3`. So the bisect is two-wide, not
one-wide, and this is the CLAUDE.md pattern repeating — one fault riding a
stack of commits, each dispatched against a channel nobody had confirmed
was still answering.

Against it: I read the whole `TryAttach` diff and found no unbounded loop,
no repeated load, no new per-frame work. Everything added is once-per-attach
with array-bounded loops. I cannot name a 70x mechanism.

**Discriminating test — costs nothing and is the one I would run first:**
dispatch `e8c5949` **unchanged, a second time**. If it produces a done line,
candidate A is dead and B is confirmed. If it stalls again at frame <306,
A is confirmed and the window bisects to two commits. One round trip either
way, and it is the *only* test that distinguishes A from B without guessing.

### B. The pre-existing intermittent stall, recurring

**6 ran-and-hung runs in the newest 60 (§2b); 7 in 352 overall.** Six of the
seven cluster on 24 Aug and exactly one of those was ever explained
(`8132974`, the `.hdr` throw, fixed by `daaf947`). `5ee9330`, `6b3ab53`,
`7c983e0`, `3e3cdc2` and `e17e91e` were never given a cause. A mode that has
bitten seven times and been explained once is not a mode you can assume is
retired.

**Discriminating test:** the same re-dispatch as A. Additionally, `--flaky`
over the hang set: if the stall recurs on commits *without* `e72f58a3`, B is
proved outright.

### C. A runner-side stall — a hung GPU/driver call on the software rasteriser

The last thing in the log is a render (`R8_SRGB` from the AO pass), and
`-force-d3d11` on a headless runner is a software path. A wedged present or
a driver reset would look precisely like this: rendering starts, the process
stops advancing, nothing is logged, the harness kills it at 24 minutes.

**Discriminating test:** it is currently untestable from here, which is its
main weakness as a hypothesis. §8.1 makes it testable — an in-process
watchdog that prints a frame count and a stack from a *different* thread
distinguishes "the main thread is inside a render call" from "the main
thread is looping in managed code".

---

## 6. What I changed

**Nothing.** No file was edited. `git status` for my five owned files is
clean.

This is a deliberate call against the brief's preference order, and the
reason is the brief's own standing rule. Option 1 was "a guard that makes
the offending read or write safe" — but §2 and §2a show the offending read
is not offending: it is unchanged code whose warnings were never absent,
only unreported. Shipping that guard would spend the round trip the channel
cannot afford on a non-fault, and it would come back stalled again with the
lead now falsely eliminated. Option 3, reverting `e72f58a3`, throws away the
first visible change in days to fix something I cannot show it caused, and
would not touch `677beb64`, which is equally unbuilt and equally unproven.

**A visual or textual symptom is a hypothesis.** Ten warnings correlated
with one failure, in a field that cannot be non-zero on a success, is not
evidence, and four correct things were once condemned here off exactly this
kind of reading.

---

## 7. Two real findings in my files, neither a hang — for the queue, not for this build

Found while reading; both are measurement faults introduced by `e72f58a3`.

1. **`ArchetypeRead`, `ControllerRead` and `TrouserRead` are last-wins
   strings outside the save/restore set** (`RealBody.cs`, assigned in
   `TryAttach`; `Save()` at `:977` does not carry them). `TryAttachExtra`
   restores the player's readings after every walker, but these three are not
   restored — so they describe **whichever walker attached last**, not the
   player, while sitting on a line whose neighbours are about the player.
   That is the `namesTracked=2` fault again: a last-wins field read as a
   summary. The counters (`PartsUpper`, `OwnEver`, `SplitBodies`, ...) are
   correctly *outside* the set, per the documented rule at `RealBody.cs:562`.
2. **`bodyTinted` and the `bodyWash*` family change population at this
   commit** — from every textured renderer to cloth only. The commit message
   declares this, which is right, but nothing in the verdict says it, so the
   next series-reader sees an unexplained fall. It wants a note at the emit.

---

## 8. The smallest change that restores the channel

**The channel is not dark because of a bad read. It is dark because a
stalled sim writes nothing, and nothing in the pipeline can say why.** Two
changes, both outside my ownership, both cheap. I am naming them precisely
rather than editing files another agent holds.

### 8.1 Make the sim step say which branch it took — one line, retires §1 forever

`.github/workflows/ledger-build-windows.yml:451-468` already computes the
answer and throws it away. `$timedOut` and `$p.ExitCode` distinguish "killed
at 24 minutes" from "crashed with an exit code", and neither reaches the
verdict. Write them to a file next to `player.log` and have
`tools/sim-shots-commit.sh` emit them as verdict keys:

    simExit=<code|killed>  simTimedOut=<yes|no>  simWaitSeconds=<n>

Every future occurrence then arrives already classified. This is rule 12:
the blocked channel is the highest-leverage bug on the board, and I spent
this whole task inferring from commit timestamps what one key would have
stated.

### 8.2 An in-sim watchdog that beats the external kill

The external kill at 24 minutes destroys the evidence. A watchdog inside
`SimDirector` that fires at ~20 minutes of wall clock and logs frame count,
in-game time, and the last completed phase — then quits cleanly — converts
every future stall from "no answer" into "stalled at frame N on day D".
`SimDirector.cs` is another agent's file this cycle; this belongs on the
queue with 8.1.

### 8.3 And the cheapest thing available right now

**Re-dispatch `e8c5949` unchanged.** It is the discriminating test for both
A and B (§5), it costs exactly one round trip — the same as any speculative
fix — and unlike a speculative fix it cannot be wrong. If it comes back
green, the street-dressing batch ships behind it and candidate A is dead. If
it stalls again, the window bisects to `677beb64` vs `e72f58a3` and the next
dispatch is `677beb64` alone.

---

## 9. What the next run's tail looks like

**If I am right that this is not the IK read** (whatever the true cause):

- a re-dispatch of `e8c5949` unchanged either produces a full done line —
  in which case candidate B is confirmed and nothing needed fixing — or it
  stalls again with **zero `dayMark` lines** and the same 111-line log.
- either way the IK warnings appear again in any stalled run and never in a
  green one, because that is a property of the reporting gate, not the code.

**If I am wrong and the IK read is implicated**, the tell is specific and
falsifiable: a stalled run would show `dayMark` lines *present but sparse*
(a slowdown, since a warning per LateUpdate per rig is a cost, not a
deadlock) rather than absent entirely, and the log would be very long rather
than 111 lines — the shape `8132974` had. Zero beats and a 111-line log is
the opposite shape, which is why I rank it out.

**The single number to read first on the next run:** `dayMark day=1 at=`. If
it is present at ~20 s, the sim is healthy. If present at 200 s, the runner
is slow and the timeout wants raising. If absent, it stalled again and §8.1
tells you whether it was killed or died.

---

## 10. verify.py

**`ledger/.verify-footer` DOES NOT EXIST ON DISK.** Checked before the run
and after it. That is the correct state and it is the answer to the brief's
question: `verify.py` exits 1, and a red run deletes the footer, so **there
is no footer to paste and nothing here may be used in a commit message.**
The tool prints `NOT GREEN — do not paste this into a commit message as if
it were` in place of one.

    $ ls -l ledger/.verify-footer
    ls: cannot access 'ledger/.verify-footer': No such file or directory
    $ python3 ledger/verify.py ; echo $?
    1

**Two causes, and one of them was mine.**

1. **Not mine.** `CoreTests did not report a count (build failure?)`, and
   with it `save chaos did not report`, `soak did not report`, `adversary
   did not report`. `ledger/CoreTests/Program.cs` is modified in the working
   tree by another agent this cycle, along with the new untracked
   `Core/KitDressing.cs` and `Game/StreetDressing.cs`. The Core test binary
   does not build, so the four checks that depend on it cannot report. I did
   not touch it and did not attempt to fix it.
2. **Mine, and fixed.** The first run flagged
   `DOCS: sim-hang-e8c5949.md declares a status in its first 8 lines — no
   STATUS banner` — this report's own header. It now carries the standard
   `> **STATUS — LOG, 2026-08-25. NOT CURRENT**` block and
   `python3 tools/docs-check.py` reports it clean on all three of its
   checks. The one remaining docs failure is `queue.md` at 404 lines
   against a 400-line bound, which is not mine either.

Everything that does not depend on the Core test binary passed, including
the five name-shape lints that cover ShapeCheck's blind spots:

    0 lint errors; 0 shape errors (189 files); 0 shadowed Core types;
    0 nested-type errors (253 Core types); 0 static/instance errors
    (75 members, 556 bodies); 0 filename-as-type errors (189 files,
    13 filenames that are not types); 0 namespace-as-value errors
    (189 files, 4 segments in scope); 0 stale anchors;
    Game layer compiles (183 files)

Those are green against a tree containing **no changes of mine**, so they
say nothing about a fix — there is no fix to check. They are recorded
because the brief asked what I saw.
