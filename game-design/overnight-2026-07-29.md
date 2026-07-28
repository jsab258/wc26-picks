# The overnight run — 28/29 July 2026

Written as it happened. Everything here is on
`claude/game-dev-ai-automation-2h67ix` and verified by CoreTests, SimHarness
and the ShapeCheck/lint gates before each push; the in-engine column says
whether a green Windows CI run has confirmed it yet.

## What shipped

| | Work | In-engine |
|---|---|---|
| 1 | Wet-surface reflections, gated on distance travelled | **yes** — 167 refreshes over 1975 wet frames |
| 2 | Bodies: procedural mannequin + walk cycle | pending |
| 3 | Physique: a crowd that is not thirty of one person | pending |
| 4 | Idle: what a person does when they are doing nothing | pending |
| 5 | Gaze with the head rather than the whole body | pending |
| 6 | Ambient occlusion | pending |
| 7 | Confabs: the city talking to itself, visibly | pending |
| 8 | The hush — they stop talking when you walk up | pending |
| 9 | Perf: one silhouette per body, instancing, detail LOD | pending |
| 10 | A frame-time gate, which nothing had | pending |

Core checks went 2060 → 2135.

## The one that matters most

**Animation was blocked on a download that never came.** `Core/Rig` had a
gait, a lean, a breath, a limp, a look-split and two-bone IK — all of it
driving a capsule, waiting for a Mixamo import that is not mine to make. It
had been waiting for weeks.

So the skeleton is built from primitives instead: thirteen boxes and a sphere
in a real joint hierarchy, proportions and stride and idle phase and head
varied per person off their name. It will not be mistaken for a person. It is
unmistakably *a person walking*, which is the part that makes a street read
as populated, and a capsule never was.

**This does not replace the download — it de-risks it.** `CharacterRig`
prefers a Humanoid Avatar and falls back to the mannequin, so when the FBX
lands, tier one starts matching, tier two stops being instantiated, and
nothing downstream changes. The integration was the risk; it is now exercised
in CI on every build.

The general lesson is worth more than the animation: **when a dependency is
somebody else's to satisfy, build the thing behind it against a stand-in you
control.**

## The one that is most *this game*

Rumours have passed along the contact graph since the first week, and the
street showed none of it — a dozen people walking past each other in silence
while the thing the game is about happened underneath.

Now a pair stops, turns in, and stands at conversational distance. Not nose
to nose: squared-up is the posture of an argument, and a street staging every
conversation that way reads as one about to kick off. Shoulders angled
nineteen degrees — which makes the same number do the work twice, because a
*contradiction*, where somebody has just been caught lying, **is** square-on,
and the player reads a fight starting before anybody speaks.

And then the part that is not decoration: **they stop talking when you walk
up.** A pair who break off and look away have told the player they were
talking about him, that they know he can see them, and that they would rather
he had not heard — which no interface could say, and two people stopping
does. Conditional, or it is a proximity trigger rather than a signal: a pair
discussing the fish price keep talking while he walks straight through them,
which is exactly what makes the ones who *don't* mean something. And a close
pair holds its nerve and lets him watch, which is its own message and a worse
one.

## What the break runs found in my own work

Every claim here was proved by reintroducing the defect and watching the test
go red. Forty-eight deliberate breaks; four survived, and each one was a real
hole:

**The hash was correlated.** Salting last and multiplying once — under a
comment claiming it kept adjacent salts apart — leaves XOR-by-1 and XOR-by-2
differing in bits 24 and 25, which never reach the top bits the fraction is
read from. Height and breadth were one draw wearing a disguise, and the
triangular distribution built on averaging them collapsed to uniform: 49% of
the crowd near average where an independent pair gives 75%. **The range test
passed the whole time.** Caught by asserting the *shape* of the distribution.

Then the break run corrected the fix's explanation too: reintroducing the
weak salt *with* the avalanche still passes, so the byte-wise loop was never
what fixed it. A comment crediting it would have been the second wrong
explanation in one function.

**A threshold written twice.** The dry-road gate existed as both an early-out
constant and a curve origin, and each half silently covered for the other —
move one and the other still returns zero. The number deciding whether a
rained-on street looks wet was the only thing there no test could see change.

**Two tests written against the constants they were meant to pin**, hours
apart. `strangers <= Confab.FarMetres` moved with the number it constrained,
so pushing people out to social distance passed cleanly.

**A cull assertion that could not fail.** `solved <= rigs` is true of every
possible run including one that never culls.

## And the check that took three attempts

The idle motion needs people not to sway in unison — thirty people breathing
to one clock reads as a chorus line and cannot be unseen.

1. *Is the period ratio near a small rational?* A proxy. It did catch my
   original 4.3/2.9, which is three-halves to within a hair — two shifts and
   three sways re-aligning every nine seconds. But a proxy can be satisfied
   by constants that still lock.
2. *Does the phase difference visit the whole circle over a minute?* It
   always does. Two linear phases drift apart at a constant rate for any
   unequal periods. **That check passed for 3:2 as readily as for φ. It could
   not fail.**
3. *Does the combined motion ever return to a pose it held before, inside the
   twenty seconds anyone spends watching one idle figure?* Every simple ratio
   repeats **exactly** — 3:2 at 8.7s, 2:1 at 5.8s, 4:3 at 11.6s — where the
   golden ratio gets no nearer than half a unit.

Check the ruler before the reading. That is five times this session.

## What went wrong, and what it cost

Bodies roughly doubled the CI sim's wall clock — ten and a half minutes to
eighteen against a twenty-four minute timeout — and the run had to be
cancelled. On a runner with no GPU the shadow pass dominates, and thirteen
small shadow casters per walker across forty-six walkers was the whole of it.

Fixed by casting one silhouette per body rather than thirteen, dropping
shadows and detail past the solve distance, and enabling instancing. **But
the more useful finding is that nothing was measuring frame time at all** —
`perfOk` gated one subsystem, so a global regression could only surface as a
job timeout, which is a diagnosis-free failure on a twenty-minute loop. There
is a frame-time gate now.

## Still needing you

Two things, and that is the whole list:

- **Fifteen minutes of listening** to pick the bark voices (two commands).
- **A mocap licence**, $100–1000, if we want motion matching. Everything
  short of that is done.

Nothing has been bought, and nothing will be without you.
