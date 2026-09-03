# The gap — LEDGER against KCD2 and GTA5

> **STATUS: LOG, 2026-07-28. NOT CURRENT.** A record of what was true on the
> day, kept because the reasoning is worth having. **Do not read it as the
> present state** — for that, `roadmap.md`. Items called "open" here have
> very likely been closed since.

**Written 2026-07-28**, answering Jafar directly: *"how far away are we from
top tier games like kcd2 and gta5? how do we close the gap? goal is to get as
close as possible to those."*

This is the strategy document. It is deliberately blunt in both directions —
about what is out of reach, and about what is more reachable than it looks.

---

## 1. The measurement

Scored 0–10 on what a player would perceive, not on what is technically
present.

| Dimension | LEDGER | KCD2 | GTA5 | Gap |
|---|---|---|---|---|
| **Social simulation** | **9** | 4 | 2 | **we lead** |
| **Non-repeating dialogue** | **8** | 5 | 4 | **we lead** |
| **Consequence systems** | **8** | 6 | 3 | **we lead** |
| Systems robustness / verification | 8 | ? | ? | unusual for the stage |
| Writing quality | ? | 8 | 8 | unproven — no playtest |
| Moment-to-moment feel | 5 | 7 | 9 | closing |
| Audio | 4 | 8 | 9 | closable |
| Music / cinematics | 3 | 8 | 9 | partly closable |
| Content volume | 3 | 9 | 10 | **not closable — rescope** |
| Environment art | 2 | 9 | 9 | expensive |
| **Lighting / render** | **2** | 9 | 8 | **cheapest big win** |
| **Animation** | **1 → 4** | 8 | 9 | **still the biggest gap** |

**The resourcing reality.** KCD2 is roughly 250 people for five years. GTA5
was around a thousand people and about a quarter of a billion dollars. Almost
all of that money bought **art production volume, animation, audio
production, and QA** — not systems. Their design documents are shorter than
ours.

**So: you cannot out-produce them, and the plan must not try.** Every hour
spent chasing their content mass is an hour not spent on the three rows where
we already lead.

## 2. The moat, stated plainly

Look at the top three rows again.

GTA5's pedestrians are set dressing — they have no memory of the player and
no model of each other. KCD2's reputation is a number per region, moved by
scripted events. **Neither has anything resembling a per-person belief
network with confidence, hop decay, suppression, contradiction against things
the player has said to their face, and a class of fact that cannot be
discredited.**

That is not "close to" them. It is a category they do not compete in, and it
is already built and tested.

The commercial precedent for this position is **Disco Elysium against
Baldur's Gate 3.** DE did not win by getting close on production values. It
won by being incomparable on one axis and honest about the rest.

**That is the target: unmistakably worse-looking than KCD2, unmistakably
deeper than either.**

## 3. Where the gap actually is — and why it is cheaper than it looks

Perceived production value in this genre is dominated by three things, and
polygon count is not one of them.

### 3a. LIGHTING — the best ratio in the entire project

KCD2 looks like KCD2 mostly because of **light and materials**, not geometry.
A proper lighting setup transforms perceived value more than any other single
change, and it **costs no art at all**.

What it means concretely:
- Linear colour, HDR, and a real filmic tonemapper rather than a clamp
- Time-of-day driven ambient (sky/equator/ground), not a flat grey
- Exponential-squared fog whose colour tracks the hour and the weather
- **Volumetric light** — raymarched cones from the street lamps and neon
- **Wet PBR asphalt**, so the lamps actually reflect in the road
- Shadow distance and cascades tuned for a street rather than a landscape

A rainy night street with volumetric lamp cones on wet asphalt reads as AAA
over box geometry. **That is literally LEDGER's setting.** This is the single
highest-value thing not yet started, it is nearly all code, and it is the
work beginning now.

### 3b. ANIMATION — the biggest gap, and the most honest limit

> **Updated 2026-07-29 — this section was written assuming a download that
> had not happened, and then the download stayed un-happened for weeks while
> everything it blocked sat still.** That was the wrong shape for a
> dependency. `Core/Rig` had a gait, a lean, a breath, a limp, a look-split
> and two-bone IK, all of it driving a capsule, waiting for a skeleton.
>
> The skeleton is now built from primitives (`Game/Mannequin`): thirteen
> boxes and a sphere in a real joint hierarchy, with proportions, stride,
> idle phase and head varied per person off their name. It will not be
> mistaken for a person. It is unmistakably **a person walking**, which is
> the part that makes a street read as populated, and the capsules never
> were.
>
> **This does not replace the Mixamo download — it de-risks it.** The bones
> are the contract: `CharacterRig` prefers a Humanoid Avatar and falls back
> to the mannequin, so when the FBX lands, tier one starts matching, tier two
> stops being instantiated, and nothing downstream changes. The integration
> was the risk; it is now already exercised, in CI, every build. Score moves
> 1 → 4: the gap to KCD2 is still motion matching over a mocap corpus, and
> that is still a purchase.
>
> The general lesson is worth more than the animation: **when a dependency is
> somebody else's to satisfy, build the thing behind it against a stand-in
> you control.** Three other items on this list were parked behind
> acquisitions and at least one of them deserves the same treatment.

Mixamo plus procedural layers — foot IK, look-at, additive breathing, the
limp already driven by real capability, ragdoll-blended hit reactions — gets
to **good indie**. It does not get to KCD2.

Real KCD2-grade locomotion is **motion matching** over a dense mocap corpus,
and this is where honesty matters: the good free research datasets (AMASS,
LAFAN1, 100STYLE) are largely **non-commercial licences**. That is a
purchasing decision, not something clever code routes around.

Commercially licensed libraries do exist in the **$100–1000** range, which is
affordable and worth doing.

> **Updated 2026-07-29 — the matcher is built, and the corpus is now the
> only part that is a purchase.** `Core/MotionMatch` is the whole runtime:
> feature layout, per-dimension normalisation, trajectory-over-pose cost
> weighting, the search cadence, the jump margin, the clip-boundary rule and
> the inertial blend. `IMotionCorpus` is the seam. `SyntheticCorpus`
> implements it today out of `Rig`'s analytic walk.
>
> **What that does not buy.** Matching against motion `Rig` generated cannot
> produce motion better than `Rig`. There is no version of this where search
> invents mocap. The animation score does not move.
>
> **What it does buy** is that the day the licence is bought, the work is
> writing one class that samples the clips — not meeting seven integration
> bugs at once in a system with no working baseline. Four of those bugs are
> already found and fixed: a query that left the foot-velocity channels at
> zero, a per-clip frame with the feature vector of a body standing still,
> playback that ran a 30fps corpus at double speed, and a continuation cost
> measured at the wrong point. None of them needed mocap to find.
>
> That is the §3b lesson applied a second time, and it now has two data
> points: **when a dependency is somebody else's to satisfy, build the thing
> behind it against a stand-in you control.**

### 3c. AUDIO — where AI gives a genuine 100× advantage

GTA5 spent millions in voice studios. A **3,000-line voiced bark bank is
about five hours of GPU time here, once.** Plus live LLM dialogue, which
neither of them can do at all.

This is the one production axis where the economics are not merely favourable
but inverted. It should be pushed hard.

## 4. THE SCOPE CALL — and I would push hard for this

**Cut from seven districts to two or three, and make those dense.**

This is not a concession, it is a design improvement. The gossip system is
*better* in a small world where everyone knows everyone: rumours reach people
who matter, the same faces recur, and the player learns the street rather
than a map. Seven graybox districts is the **weaker** game as well as the
more expensive one.

Depth over breadth, every time, for a team this size.

## 5. The plan, ranked by perceived quality per unit of effort

| # | Work | Read | Cost | Who |
|---|---|---|---|---|
| 1 | **Lighting + volumetrics + wet materials** | huge | low | me |
| 2 | **Voiced bark bank** (chatterbox, one overnight run) | huge | low | me + one listening pass |
| 3 | ~~Characters +~~ **procedural animation layers** | huge | low-med | **done without the download** — bodies, walk cycle, idle, gaze |
| 4 | Set dressing density on 2–3 districts | big | med | asset packs |
| 5 | Music — adaptive layers off real state | med | low | me |
| 6 | Motion matching on a licensed corpus | big | med | **runtime done** — the corpus is the purchase |
| 7 | UI typography and iconography pass | med | v.low | me |
| 8 | Cinematic framing for the authored beats | med | low | me |

Items 1, 5, 7 and 8 need nothing from anybody and are **done**. Item 4 is
done procedurally (`Core/Dressing`) without the asset packs. Item 3 is done
to the limit of what code can do, and the Mixamo download now **upgrades** it
rather than unblocking it.

**What is actually left needing you:** item 2's fifteen-minute listening pass,
and item 6's mocap licence. That is the whole list — and item 6 is now a
purchase with a working system behind it rather than a purchase that starts
a project.

## 6. Rough budget

| | |
|---|---|
| Characters + animations (Mixamo) | **free** |
| Environment/prop packs for 2–3 dense districts | $100–400 |
| Licensed mocap library (motion matching) | $100–1000 |
| Audio libraries (impacts, foley, room tones) | $0–150 |
| **Total** | **$200–1550** |

Against a quarter of a billion dollars. The asymmetry is the whole strategy.

## 7. Timeline, honestly

- **Now → ~3 months:** lighting, voice, characters, animation layers, density
  on Hook Street. End state: *looks like a competent indie, plays like
  nothing else.*
- **~3 → 9 months:** motion matching, second and third district, music,
  cinematic beats, the long playtest that has never happened.
- **~9 → 12 months:** the polish tail, which is always longer than anyone
  plans for.

**Presentation parity with KCD2 is not reachable without a team, and I would
rather say that now than let it be discovered in a year.** What *is* reachable
is a game that no reviewer can describe without using the word "unlike
anything else", which is worth more than a comparison it would lose.

## 8. What I cannot do, listed so it is never a surprise

- **Make art.** Models, textures, animations — I can integrate, generate
  procedurally, and write every shader, but I cannot author assets.
- **Judge aesthetics.** I can measure a render fingerprint and catch a
  clipped channel. I cannot tell you whether the street looks *good*.
- **Buy anything.** Every purchase and every account is yours.
- **Playtest.** Pacing across a twenty-one day campaign has never been felt
  by a human being, and no amount of simulation substitutes for that.

The bottleneck on this project has never been code. It is asset acquisition
and your eyes.
