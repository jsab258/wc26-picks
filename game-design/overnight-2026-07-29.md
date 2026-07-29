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
| 11 | The mix: ducking that does not pump, voice budgets, crowd summing | pending |
| 12 | AO split into its own shader so it cannot break the grade | pending |
| 13 | **The post stack had never run at all** — found and fixed | pending |
| 14 | Exposure tied to the night it compensates for | n/a (Core) |
| 15 | The cinematic camera had never run in a verified build | pending |
| 16 | Motion matching, built against a corpus we do not own | n/a (Core) |
| 17 | A break-run harness, after losing work to two ad-hoc ones | n/a (tooling) |

Core checks went 2060 → 2239.

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

## The biggest thing found tonight, and it was found by accident

`FilmGrade` — grain, vignette, bloom, exposure, the ACES tonemap — was
attached to a **child GameObject parented under the camera**. `OnRenderImage`
is only delivered to a component on the GameObject that *has* the Camera. So
the entire post stack has never executed a single frame since it was written.
The component sat in the scene, correctly built, doing nothing.

**Nothing caught it because every check was of the model.** The curves are
tested in `Core/LightModel`. The shader compiled. The material was built. The
component existed. Every one of those was true, and not one of them was the
claim being made.

The check that found it was the ambient-occlusion A/B — written four features
later, for a completely different purpose: proving that a *subtle* effect was
not invisible, by rendering one frame with it and one without. It reported
`ao[applied=0 on=0.1827 off=0.1827]` on its first run and the cause turned out
to have nothing to do with occlusion.

That is the argument for A/B gates over presence gates, made by accident and
at some cost: **an effect existing is not an effect running, and a screenshot
of a scene that looks plausible cannot tell you which.** There is now a frame
counter on `OnRenderImage` so this exact class of failure fails loudly.

It also surfaced a second defect that could not have existed before: exposure
lifts night by 1.55× to keep the street legible, and nothing tied that to how
much the ambient bands darken at night. If the lift ever exceeds the
darkening, the tonemap sees more light at midnight than at midday and the
night is simply gone. The two curves are now checked against each other.

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

## The mix

The bark bank is blocked on your listening pass. **The mix is not blocked on
anything**, and it is most of why an independent game sounds independent.

What was there: `DuckMusic(true/false)`, which snapped the score to 35% and
back. Symmetric, so the bed swells into every gap between syllables and
collapses again — the most recognisable sound of an amateur mix, and audible
to people who could not name it. It is an envelope now, 80ms down and 750ms
back, and the depth is per-bus because ducking everything equally takes the
street out from behind the speaker and sounds like a fault rather than
emphasis.

**Overhearing is a different duck**, and it is the one this game needs. Two
people discussing the player six metres away is the moment the whole gossip
network exists for, and until tonight it competed on equal terms with rain and
traffic. The street now leans out of the way harder for something he was not
meant to hear than for a conversation he is having.

Plus a budget on how many sounds may speak at once — stealing from the
*quietest*, never from an authored line — and summing that matches hearing:
ten incoherent sources at 0.3 make about 0.95, not 3.0, and adding them
linearly is why crowds clip.

## The second thing that had never run

`FilmGrade` was the first. The cinematic framing layer was the second, and
it was hiding in plain sight for the same reason: **the sim is the only
thing that runs this game end to end, and the trigger carried
`SimMode.Days > 0` in its guard.** Push, hold, authority, shot sizes, the
180-degree rule — `Core/Framing` is fully tested and none of the wiring to
it had ever executed.

The stated reason was sound. A push-in part-way through a measured
screenshot moves the luminance the lighting gates read. But that is an
argument for suppressing framing *around a screenshot*, not for the whole
run, and the smaller exclusion costs one method: `Abort()` — stop on this
tick, no yield — called immediately before each render.

The gate needed two numbers. `Begun > 0` proves a beat started and nothing
more; a beat that starts and is never ticked satisfies it. The second is
the smallest fraction the camera was actually pulled to, which stays at
exactly 1 if the push never reached it.

## Motion matching, and the second use of the §3b lesson

The animation section closes with a note that three items were parked
behind acquisitions and at least one deserved the same treatment. The mocap
licence was that item.

`Core/MotionMatch` is the whole runtime and `IMotionCorpus` is the seam;
`SyntheticCorpus` implements it out of `Rig` today. **It does not improve
the animation** — matching against motion `Rig` generated cannot produce
motion better than `Rig`, and no amount of search invents mocap. What it
does is find the integration bugs now. Four of them, none needing a single
mocap frame:

- The query left the foot-velocity channels at zero. They carry the
  heaviest weight in the feature, so every search came back pointing at a
  body that had stopped moving.
- Frame 0 of each clip differenced backwards into nothing, giving one frame
  per clip the exact feature vector of a person standing still. A query with
  a planted foot found those holes irresistible.
- Playback advanced one frame per tick, running a 30fps corpus at 2x.
- Continuation was costed at the integer frame index while playback sits
  *between* frames, so the matcher paid for its own stepping error, jumped
  to correct it, and landed between two frames again.

## And the ruler was wrong twice more

**Jump count is not a quality measure.** The first chatter check asserted
"at most two jumps" and saw nine. All nine were harmless: a corpus holds
many frames at the same point in the stride and hopping between them
changes nothing on screen. A twitch is a jump that lands on a *different*
pose. Chasing the wrong number did find two of the four defects above, so
it was not wasted — it just could not say when it was finished.

Then the replacement threshold was a number invented out of nothing, in
weighted-normalised units nobody has an intuition for. It is calibrated
against the corpus's own scale now: one frame of ordinary playback is by
definition invisible, two frames from different clips is by definition a
cut, and they are three orders of magnitude apart.

That is eight times this session.

## The harness, and why it is committed now

Two ad-hoc break scripts cost real work — one took SIGPIPE before its
restore and left a deliberate break in the tree, and one restored with
`shutil.copy2`, which preserves mtime, so the restored file looked older
than the objects built from the broken one and MSBuild handed the next run
the **broken binary against correct-looking source**. Twenty minutes of
staring at code that was already right.

`ledger/breakrun.py` restores on every exit path and never preserves mtime.
It also refuses to run against a red baseline, because if the tests are
already failing then every break "goes red" and none of it is evidence.

Sixteen breaks across tonight's two features. Five survived the first pass
and every survivor was a check that could not fail — **three of them
covering defects fixed an hour earlier.** Fixing a bug is not the same as
preventing it.

## Three gates that were measuring the wrong thing

Found by asking, of every render gate, *would this still pass with the
effect switched off?* — the only useful generalisation from the two dead
layers above. It turned up something worse than gates that could not fail:
gates that could not tell which way the effect went.

**The grain gate said "local spread" in its own comment and computed
global variance.** Global variance of a night street is the sky against the
lamps. Grain's contribution is a rounding error on it — and then the
reading went *negative*, which is the part that gives it away. Additive
noise cannot reduce spread. Grain clamped at black can: half the pixels in
a night frame sit near zero, negative grain on them is cut off and positive
grain is not, so the noise lifts the blacks toward the middle and reduces
the variance it was meant to raise. Not a shrunken effect. A ruler reading
the sign backwards, for months, while passing.

The replacement is the statistic the comment always described: the mean
squared difference between horizontally adjacent pixels. Smooth things have
almost none of it however bright they are; per-pixel noise has a great deal
by definition. The decisive test is one image, one grain pass, two rulers —
global variance falls, local spread rises.

**The occlusion gate diluted a local effect across a global average.**
Occlusion darkens creases: a few percent of a street. A very visible 0.03
drop over 6% of a frame moves the mean of the whole frame by 0.0018. CI
reported 0.0014 against a floor of 0.002 and called it a failure — and that
reading is what a *correct* pass looks like through a statistic that
divides its result by the ninety-odd parts of the image it was never
supposed to touch. Worse, the floor was tuned on a scene with a particular
amount of geometry in shot, so it needed retuning every time the camera
moved.

Now: what fraction of the frame the pass reached, and how hard it hit
there. Both halves catch a different failure — near-zero fraction means it
never ran; near-total means it is not occlusion but an exposure change
wearing its coat.

**And the probe I wrote to diagnose the third one measured nothing.**
`LightShaft.Enabled` was a plain field read by `LateUpdate`, and the probe
set it false and true again inside a single `Update` — so `LateUpdate` never
saw the false and not one shaft was ever switched off. `nightNoShafts` was
a second copy of `nightFull`. An instrument that cannot affect what it
measures is useless; one that can, invisibly, is worse, because it also
looks like good news.

**Thresholds are derived now, not tuned.** Uniform noise of amplitude *a*
has standard deviation *a*/√3 and adds 2σ² to the neighbour difference, so
the grain floor follows from the amount the shader was asked for. The
occlusion bounds are geometric: a street is comfortably more than half a
percent creases and nothing like half. A floor nobody can derive gets
lowered when it starts failing, which is how a gate stops being one.

## The cleanest example of the whole pattern

Saved for last because it is the tidiest. The wet-road reflection probe
woke on schedule, refreshed 142 times over 1280 wet frames, obeyed its
rate limit exactly, and reported healthy numbers to a gate that checked
every one of those things. It contributed **zero pixels to the image.**

The gate was not weak. It proved everything it claimed. It simply never
claimed the one thing that mattered.

Finding out which end was broken needed two toggles rather than one,
because "switching the probe off changes nothing" has two very different
explanations — the probe is not reaching the shading, or wet specular is
worth nothing anyway — and each guess costs a twenty-five minute build. So
one run measured both: the probe (0.00% of the frame) and a positive
control that flattens the wet surfaces' smoothness by a route with no
probe mechanics in it at all (33.22%, by 0.26).

Unambiguous. Wet specular was doing a great deal and none of it came from
the probe. The shine on the road was direct lamp specular; the actual
reflections — the point of the entire feature — were absent.

**The mechanism is worth writing down.** A renderer only samples a
reflection probe when its BOUNDS sit inside the probe's box, and the road
is a small number of very large meshes. Their bounds dwarf a 48-metre box,
so Unity blended them to the skybox instead. Publishing the capture as the
scene's reflection removes the containment question; and the strength has
to travel through `RenderSettings.reflectionIntensity`, because a custom
reflection texture does not carry the probe's own intensity with it.

## And the trap that appeared five times

Every one of these was an A/B that measured its own inertness:

1. `LightShaft.Enabled` — a plain field read by `LateUpdate`, set false and
   true again inside one `Update`, so nothing was ever switched off.
2. The reflection probe — `enabled = false` stops a realtime probe
   UPDATING; the renderers keep sampling the cubemap it last produced.
3. The graphics preset — read inside `LateUpdate` for the same reason as 1,
   caught before it shipped rather than after.
4. `StemGain` — returned the number the mixer computed, not the one on the
   AudioSource.
5. The panel smoke test — a panel opens, speaks and closes whether or not a
   single glyph rendered.

The generalisation, and it is worth more than any of the five: **an A/B is
only a measurement if the thing it switches is switched by the time the
frame is drawn.** Everything that reads its state one frame later, or
holds a cached copy, or lives on the far side of an engine boundary, will
quietly report that the effect does nothing — which is indistinguishable
from good news.

## One reading that is not a bug, so nobody chases it

`hotUnease` read 0.11 at heat 0.92 in one run and 1.00 at heat 0.97 in the
next, which looks like a near-vertical knee in the music. It is not. The
unease layer is a smoothed gain and the sim samples it at the instant of
peak heat, so a heat spike that has only just happened reads low while a
sustained one reads settled. The curve is linear from 0.2 to 0.8 exposure
and does exactly what it says. The pairing in the log is a weak label, not
a defect.

## Still needing you

Two things, and that is the whole list:

- **Fifteen minutes of listening** to pick the bark voices (two commands).
- **A mocap licence**, $100–1000, if we want motion matching. The matcher
  itself is now built and tested, so this is a purchase with a working
  system waiting behind it rather than one that starts a project.

Nothing has been bought, and nothing will be without you.
