using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Schedule-driven background character: walks toward wherever their daily
    /// schedule says they should be right now. The sim heart of "the city has
    /// routines you can learn".
    public class NpcWalker : MonoBehaviour
    {
        /// HOW FAST A PERSON WALKS, and this was 2.6 with no comment on it —
        /// the only bare constant in the file, which is usually what a
        /// placeholder looks like after everybody stops noticing it.
        ///
        /// 2.6 m/s is 9.4 km/h. That is a jog, and the noon still shows
        /// exactly that: a crowd in deep lunging strides with the arms thrown
        /// back, which reads as a street full of people running late.
        ///
        /// THE GAIT MODEL WAS INNOCENT — `Rig.LegSwing` is driven by MEASURED
        /// displacement, not by this constant, so it was faithfully drawing
        /// the run it was being handed. Printed off the real Core rather than
        /// guessed:
        ///
        ///     speed  peakHip  peakKnee  peakArm
        ///       1.2     23.7      39.9     11.6
        ///       1.4     26.2      43.7     12.8
        ///       2.0     32.1      52.5     15.7
        ///       2.6     36.1      58.6     17.7   <- what the street was doing
        ///       3.5     40.0      64.4     19.5
        ///
        /// 1.4 is not invented either. This project already asserts twice that
        /// a walking person moves at 1.4 m/s — `Witnesses.Resolve` passes it to
        /// `Perception.InSight` as `subjectSpeed` for somebody walking, and the
        /// locomotion blend tree uses it as the walk threshold. Three places
        /// now agree instead of two agreeing and one contradicting them.
        ///
        /// THE RISK, STATED: game time is compressed, so a slower crowd may
        /// fall behind its schedule. `crowdSpeed` and `crowdHip` are on the
        /// done line for that reason — if the street stops keeping its
        /// routine, that is the number that will say so, and the fix is to
        /// hurry the ones who are late rather than to make everybody run.
        const float MoveSpeed = 1.4f;

        /// What somebody moves at when they are catching you up. The old
        /// crowd-wide speed — a jog, wrong as a walk, and exactly right for a
        /// person hurrying to fall in beside you.
        const float CatchUpSpeed = 2.6f;

        /// What the crowd is actually doing, over the run. A constant can be
        /// read off the source; whether the bodies MOVE at it cannot.
        ///
        /// WHAT IT MEANS CHANGED WHEN ESCORTS LEARNED TO HURRY, and the number
        /// stays while the question it answers moves — the same trap
        /// `liveArmDrop` fell into the moment the body started animating. The
        /// mean now mixes walkers at 1.4 with escorts closing at 2.6, so it
        /// will read ABOVE 1.4 and that is the feature working rather than the
        /// walk being wrong. Read the peak as "somebody was hurrying", not as
        /// "the crowd is jogging again".
        public static double CrowdSpeedPeak, CrowdSpeedSum;
        public static int CrowdSpeedSamples;
        public static double CrowdSpeedMean =>
            CrowdSpeedSamples > 0 ? CrowdSpeedSum / CrowdSpeedSamples : -1;

        /// How far walkers are from where their schedule says they should be.
        /// Escorts, talkers and waiting hosts are excluded: all three are
        /// deliberately off-schedule and counting them would bury the signal
        /// under the features.
        public static double ScheduleLagSum, ScheduleLagWorst;
        public static int ScheduleLagSamples;
        public static double ScheduleLagMean =>
            ScheduleLagSamples > 0 ? ScheduleLagSum / ScheduleLagSamples : -1;

        struct Entry { public int MinuteOfDay; public Vector3 Position; }

        readonly List<Entry> _schedule = new List<Entry>();
        TextMesh _label;
        /// Fully legible this close; gone by the far one. Recognition, not HUD.
        // TIED TO THE RANGE YOU CAN ACTUALLY SPEAK AT, rather than to two
        // numbers that happened to be there.
        //
        // The rule beside the fade below says a name "resolves as you get close
        // enough to speak to somebody, and it is not there at all across the
        // road". `ConversationHost.TalkRange` is 3 metres. These were 4 and 11
        // — fully legible a metre beyond speaking distance and still on screen
        // eleven metres away, which IS across the road. The sentence and the
        // numbers had never agreed, and the tuning pass on 2026-07-28 that was
        // supposed to stop "a street of a dozen people reading as a wall of
        // text" moved the numbers without checking them against the rule.
        //
        // A night still from the first build that could commit one shows five
        // names at once, two of them larger than the people wearing them. That
        // is the wall of text, still standing, with a picture of it.
        //
        // So: full exactly at talking distance, gone by twice that. Derived
        // from the constant that defines the interaction rather than picked, so
        // the two cannot drift apart again.
        const float LabelFullAt = ConversationHost.TalkRange;
        const float LabelFadeOut = ConversationHost.TalkRange * 2f;

        public string DisplayName { get; private set; }

        /// WHO THIS BODY IS TO THE GOSSIP MILL, WHICH IS NOT ALWAYS WHAT IS ON
        /// ITS NAMEPLATE — and the gap has silently emptied the crowd's memory
        /// since the crowd existed.
        ///
        /// `PopulationHost` registers a crowd resident's mill agent under
        /// `r.Id`, which `Population.Generate` sets to `r0000`, `r0001`, …, and
        /// spawns their body with `r.Name`, which is a person's name. Every
        /// lookup in the Game layer then asked `Mill.Get(walker.DisplayName)`
        /// and got null for all seven hundred of them.
        ///
        /// THE CONSEQUENCE IS THE WHOLE MOAT. `GossipMill.Witness` opens with
        /// `var w = Get(witnessId); if (w == null) return;` — silently — so a
        /// crowd member could witness anything at all and carry none of it. The
        /// first body ever filed measured it: `homSaw=29 homPressure=0.40`,
        /// twenty-nine people watching a killing and a police pressure of
        /// exactly `PerBody`, because not one of the twenty-nine was somebody
        /// the mill had ever heard of. `GossipDirector` has the fault in a
        /// single line — it iterates `CrowdBodies`, whose KEY is the resident
        /// id, and looks the value up by `DisplayName`.
        ///
        /// This is the id-versus-name fault that `RecordKilling` had six hours
        /// earlier with `n.name` against `DisplayName`, one system over. The
        /// grep that was supposed to find the twin looked for `.name ==` and
        /// could not: this one is spelled `r.Id` against `r.Name`, in a
        /// different file, at a spawn rather than at a comparison.
        ///
        /// `DisplayName` stays what a nameplate shows and a bark says. This is
        /// what the mill, the register and the observation model are asked.
        public string GossipId { get; private set; }

        /// Set once by the crowd spawner, which is the only caller that has an
        /// identity different from the name over the head.
        public void SetGossipId(string id)
        {
            if (!string.IsNullOrEmpty(id)) GossipId = id;
        }

        /// One of the seven hundred rather than one of the cast. Decides
        /// whether the wardrobe may lift this person's coat above the crowd's
        /// value ceiling.
        public bool IsCrowd { get; private set; }

        /// HOW MUCH OF THEMSELVES THIS PERSON CURRENTLY IS, 0..1, pushed in by
        /// the population pass — and until now nobody in this city has ever
        /// limped.
        ///
        /// `CharacterRig.Capability` drives `Rig.Limp`, which is a whole
        /// authored asymmetry with its own Core function, its own tests and a
        /// footstep rhythm built to match it so that "a limp you can hear but
        /// not see is worse than neither". It had exactly ONE writer:
        /// `PlayerController`. Every one of the sixty-odd walkers sat at the
        /// default 1.0, `Rig.Limp` took its `hurt < 0.05` early return, and the
        /// street walked perfectly evenly no matter what had been done to it.
        ///
        /// The world already knows better. `HarmBook` records the injury, the
        /// sim's own verdict prints `samCap=0.70` for a man it beat on day one,
        /// `Perception` offers "the one with the limp" as a way to describe
        /// somebody — and the body it belonged to walked like everybody else.
        /// That is rule 6 exactly: built, tested, and never once running.
        ///
        /// KEYED ON `DisplayName` because that is what harm is FILED under for
        /// a person on the street — `TrafficHost.GatherHazards` registers each
        /// walker as `Id = npc.DisplayName` and the strike is inflicted on that
        /// same string, and the named cast are their own ids. Keying on a
        /// resident's `rNNNN` would have been a lookup that never matched for
        /// anybody the player can actually see, which is this fault again one
        /// layer down.
        public double Capability
        {
            get => _capability;
            set
            {
                _capability = value;
                if (_body != null) _body.Capability = value;
            }
        }
        double _capability = 1.0;

        /// Every walker currently in the scene, so one can see what it is
        /// about to stand inside.
        ///
        /// Registered on spawn and swept lazily on read — a destroyed Unity
        /// object compares equal to null and a list of them would otherwise
        /// grow for the life of the process, which is the same lifetime bug
        /// `SpeechBubble._live` documents and avoids the same way.
        static readonly List<NpcWalker> _live = new List<NpcWalker>();

        public static IEnumerable<NpcWalker> Live
        {
            get
            {
                for (int i = _live.Count - 1; i >= 0; i--)
                    if (_live[i] == null) _live.RemoveAt(i);
                return _live;
            }
        }

        /// Shoulder width, from `Core/Physique` — which is where it lives now,
        /// because this file and `SimDirector` each carried their own copy of
        /// the same 0.45 with near-identical paragraphs underneath. One fact,
        /// two implementations, in the two files that PLACE and MEASURE the
        /// same people.
        const float BodyWidth = (float)Ledger.Core.Physique.ShoulderWidth;

        /// The most `StepApart` may move a body in one frame. A resolved pair
        /// needs 0.225m — half the overlap of two coincident bodies — so half a
        /// body width is four times the ordinary case and bites only in a pile.
        const float MaxApartStep = BodyWidth * 0.5f;

        /// How often the cap bit, how far the uncapped push wanted to go, and
        /// the denominator that says the pass ran at all. A zero `ApartCapped`
        /// beside a zero `ApartCalls` is "separation never executed" and beside
        /// a large one is "no pile ever needed it" — rule 3b, and the two look
        /// identical without the second number.
        public static int ApartCapped, ApartCalls;
        /// How many PAIRS actually came close enough to be measured, against
        /// `ApartCalls` walkers swept. The broad-phase reject above is
        /// behaviour-neutral, so nothing can go red if it stops working — this
        /// is the only thing that would say so. A ratio near the crowd size
        /// means the reject is doing nothing; near zero means almost every
        /// pair is being dropped before the square root, which is the point.
        public static int ApartPairs;
        public static float ApartWorst;

        /// Which branch of `Steer` each walker took. Four counters because the
        /// four have completely different consequences: `Direct` is a clear
        /// walk to the real destination and is the healthy case, the two street
        /// branches share a point per street, `Junction` shares one point
        /// across a whole neighbourhood, and `Origin` sends everybody to
        /// (0,0) — and only a count can say which of them the crowd is
        /// actually using.
        public static int SteerDirect, SteerTargetStreet, SteerOwnStreet,
                          SteerJunction, SteerOrigin;

        /// How far sideways a walker may be shifted off a shared WAYPOINT.
        /// Half the footway `NearestStreetPoint` leaves around the point it
        /// aims at, so a walker fanned out across a junction cannot be pushed
        /// into the carriageway or through a shopfront. Not the destination
        /// ring — see `Steer` for why a waypoint wants a different bound.
        const float LaneMetres = 0.55f;

        /// How far from a scheduled point somebody actually stands. Two
        /// shoulders: far enough that two people sent to one place are clear of
        /// each other, near enough that they are still at the place and still
        /// inside talking range of it. See `Spread`.
        const float SpreadMetres = 0.8f;

        /// How many walkers may carry a skinned body at once, and how many do.
        ///
        /// Twelve rather than forty-four, and the number is chosen rather than
        /// derived: it is `CrowdWalkerCap`'s value, which was itself set from a
        /// measurement of how many people are out of doors within earshot at
        /// midday. A dozen skinned bodies is roughly 280k vertices, which is
        /// the order the rest of this scene is built at.
        // Follows `CrowdWalkerCap` up, 12 -> 28, and for the same measured
        // reason: the render ladder's `noBodies` rung came back 0.9ms
        // SLOWER than the full frame, so skinned bodies were not costing
        // what the vertex arithmetic above assumed. That estimate — "a
        // dozen skinned bodies is roughly 280k vertices, the order the
        // rest of this scene is built at" — was reasoning about the right
        // quantity and never checked against a timed frame; the frame is
        // held by shadows and per-pixel lights instead.
        //
        // It stays EQUAL to `CrowdWalkerCap` on purpose. The two numbers
        // have always been the same value for the same reason, and a
        // crowd where most of the visible people are mannequins is the
        // thing `streetBodiesSkinned=2 of 12` was reporting.
        public const int RealBodyCap = 28;
        public static int RealBodies;

        /// SWAPS, BOTH WAYS, AND THE FAILURES. A body budget spent on the
        /// nearest twelve can thrash: two walkers a centimetre apart at the cap
        /// boundary would trade a skinned mesh back and forth every pass, which
        /// costs a prefab instantiate each time and would show up as frame cost
        /// rather than as anything visibly wrong.
        ///
        /// NO COOLDOWN CONSTANT, DELIBERATELY. The obvious fix is a minimum
        /// dwell time, and picking one now would be inventing a threshold
        /// before measuring the thing it bounds — rule 2, exactly. The band
        /// already carries `Population.BandSlack` of hysteresis, which may well
        /// be enough. These counters are how the next run says whether it is:
        /// swaps roughly equal to the number of people who walked past is
        /// normal, swaps in the thousands is thrash and then a dwell time can
        /// be chosen from the series rather than guessed.
        public static int BodyGrants, BodyRevokes, BodyGrantsFailed;
        public static string BodyGrantWhy = "none asked for";

        /// AND THE ANSWER CAME BACK 966 GRANTS AND 952 REVOKES, so this is the
        /// series the paragraph above says to choose a dwell time from.
        ///
        /// A thousand prefab instantiates for a budget of twelve is the thrash
        /// case by that paragraph's own criterion, but the COUNT still cannot
        /// name a cooldown: 966 swaps spread evenly over a long run and 966
        /// swaps made by four people flickering on one boundary want completely
        /// different fixes, and the count reads identically for both.
        ///
        /// HOW LONG A BODY IS KEPT is what separates them, so that is what is
        /// recorded — seconds from grant to revoke, one entry per completed
        /// spell. A median in seconds is a walker crossing the band; a median
        /// in tens of milliseconds is a boundary being straddled, and a dwell
        /// time chosen to be a little above that median is a number taken from
        /// the run rather than from taste.
        ///
        /// SPELLS STILL OPEN AT THE END ARE NOT COUNTED, which biases the
        /// median DOWNWARD — the bodies still standing there are the ones that
        /// were kept longest. That is the safe direction for this question: it
        /// cannot manufacture thrash that is not there.
        static readonly List<float> _bodySpells = new List<float>();
        float _bodyGrantedAt = -1f;

        public static double BodySpellMedian
        {
            get
            {
                if (_bodySpells.Count == 0) return -1;
                var c = new List<float>(_bodySpells);
                c.Sort();
                return c[c.Count / 2];
            }
        }

        public static double BodySpellShortest
        {
            get
            {
                double s = -1;
                foreach (var v in _bodySpells) if (s < 0 || v < s) s = v;
                return s;
            }
        }

        public static int BodySpells => _bodySpells.Count;

        /// WHERE THIS PERSON STANDS when the schedule says "the market corner",
        /// as a fixed offset — computed once and kept.
        ///
        /// The angle comes from the display name rather than the instance id:
        /// an id is a session detail and would put the same person in a
        /// different spot after a reload, which is the quiet non-determinism
        /// the separation nudge in this same file was already bitten by.
        ///
        /// CACHED, AND THE FIRST VERSION WAS NOT. It hashed the name on every
        /// walker on every frame — fifty-odd string hashes sixty times a second
        /// for an answer that cannot change, sitting inside the scope the frame
        /// gate is currently red against. The value is deterministic by
        /// construction, so computing it twice is pure waste and computing it
        /// per frame is the kind of waste that hides inside a plausible number.
        Vector3 SpreadOffset
        {
            get
            {
                // A RING OF FIXED RADIUS CANNOT HOLD A CROWD, AND THE RUN SAYS
                // BY HOW MUCH. `crowdHuddleWorst=41` — forty-one people within
                // two metres of one person — on a street `crowdGapMedian=0.44`
                // calls comfortable, and `review_day5_noon` shows the block of
                // them, overlapping, arms through each other.
                //
                // 0.8m of radius gives forty-one people 2*pi*0.8/41 = TWELVE
                // CENTIMETRES of arc each, against a body 45cm across. The
                // constant was not wrong when it was written — it is right for
                // about ten people, which is exactly the measured MEDIAN huddle
                // — it simply never asked how many were coming. Rule 2's other
                // drift: a number that kept its name when the world moved.
                //
                // THE RADIUS IS PACKING, NOT TASTE. N bodies of width w need
                // N*w^2 of floor; a disc of radius R has pi*R^2, so
                // R = w * sqrt(N/pi) is the radius at which everybody has a body
                // width to stand in. Forty-one gives 1.63m, six gives 0.62m, and
                // ten — the median huddle — gives 0.80m, which is the constant
                // that is already here. So this does not move the typical case
                // at all; it only stops the tail piling up.
                //
                // FLOORED AT THE OLD VALUE so nobody is ever placed tighter than
                // they are today, and the whole thing collapses to the old
                // behaviour when nothing is crowded.
                //
                // AND FILLED AS A DISC RATHER THAN A RING. `sqrt(u)` is the
                // standard uniform-disc radius: taking `u` raw would bunch
                // everybody toward the middle, which is the fault again in a
                // smaller radius. The angle is unchanged and still comes from
                // the display name, so a person stands in the same spot every
                // run and every reload.
                // BACK TO THE CELL, BECAUSE THE NEIGHBOURHOOD VERSION DID
                // NOTHING AND I SHIPPED IT SAYING IT WOULD.
                //
                // The reasoning was sound and the arithmetic refuted it.
                // `huddleCells=21` at a huddle of 41 says the bodies come from
                // twenty-one different cells, so sizing each ring from its own
                // cell cannot separate them — true. The fix sized it from
                // `CrowdNearPlace`, the count of targets within TWO metres,
                // which the `busiestNear` pass was already computing.
                //
                // `c7e841b` says that changed nothing: `crowdSpread=0.88`, the
                // widest ring ever issued, IDENTICAL to the build before. And
                // the reason was on the same line the whole time —
                // `busiestNear=12` equals `busiestPlace=12`, so a two-metre
                // neighbourhood holds no more people than a one-metre cell, and
                // `SpreadRadius(12)` is 0.88 either way. I read that pair as
                // "the plan is innocent" hours earlier and did not read it as
                // "these two counts are the same number".
                //
                // A 19-cell knot needs a radius sized from the KNOT — 19 gives
                // 1.11m and 41 gives 1.63m — and neither a 1m cell nor a 2m
                // disc can see one. That is a real fix and it needs a count at
                // the scale of the thing being separated, not another guess at
                // which small radius to use.
                //
                // Reverted rather than left in: it added a cache key that moves
                // more often for no behaviour change, and the median huddle
                // went 11 to 20 in the same build, which I cannot attribute to
                // it and will not leave a suspect standing in.
                if (!_spreadKnown || _spreadFor != CrowdAtPlace)
                {
                    float radius = (float)Ledger.Core.Physique.SpreadRadius(
                        CrowdAtPlace, SpreadMetres);
                    float a = (float)(Ledger.Core.Physique.Fraction(DisplayName, 97)
                                      * System.Math.PI * 2.0);
                    float u = (float)Ledger.Core.Physique.Fraction(DisplayName, 61);
                    _spread = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a))
                              * (radius * Mathf.Sqrt(u));
                    _spreadKnown = true;
                    _spreadFor = CrowdAtPlace;
                    if (radius > WidestSpread) WidestSpread = radius;
                }
                return _spread;
            }
        }
        Vector3 _spread;
        bool _spreadKnown;
        int _spreadFor = -1;

        /// How many walkers are heading for the same place as this one, pushed
        /// in by the population pass once a second — because a walker cannot
        /// count its neighbours without walking the whole list every frame, and
        /// that pass already walks it.
        ///
        /// ONE, NOT ZERO, when nobody has said otherwise: an unset crowd must
        /// behave exactly as this file did before, and a zero would collapse the
        /// radius rather than leave it alone.
        public int CrowdAtPlace = 1;
        /// How many people are heading for a point within two metres of this
        /// one — the NEIGHBOURHOOD rather than the cell. Pushed in by the same
        /// once-a-second pass that computes `busiestNear`, which was already
        /// counting it and keeping only the maximum.
        public int CrowdNearPlace = 1;

        /// The widest ring any place has needed. Read beside `crowdHuddle`: a
        /// spread that never grows past 0.80 on a run whose worst huddle is
        /// forty is a push that is not arriving.
        public static float WidestSpread;

        bool _wantsRealBody;
        Color _skin, _cloth;

        /// Is this walker eligible for a skinned body at all? The anonymous
        /// crowd is not, by choice rather than by budget — mannequins read
        /// perfectly well at the distance the crowd is ever seen, and bounding
        /// the skinned set to the named cast means the cost is a number
        /// somebody chose rather than whatever the population happened to be.
        public bool WantsRealBody => _wantsRealBody;

        /// Whether this walker MAY wear a skinned body at all, as opposed to
        /// whether it asks for one everywhere. The cast asks everywhere; the
        /// crowd is allowed one only when `PopulationHost` ranks it close
        /// enough to read as a box, which is a decision about the CAMERA and
        /// therefore belongs where the distances are. The paragraph above is
        /// the old rule and stands corrected: it reasoned from an elevated
        /// review camera, and the street camera stands among these people.
        public bool CanWearBody => true;
        public bool HasRealBody => RealBody.Wearing(gameObject);

        /// Swap this walker between a skinned body and a mannequin.
        ///
        /// RETURNS WHETHER THE STATE CHANGED, not whether it is now what was
        /// asked for. A grant that fails leaves a working mannequin and must
        /// not be counted as a grant, or the next pass reads the budget as
        /// spent and the nearest person stays a box for ever while a counter
        /// says twelve bodies are out.
        ///
        /// The rig is rebound rather than kept: `CharacterRig` holds bone
        /// transforms from whichever body it bound to, and those are about to
        /// be destroyed. Dropping `_body` makes `DriveBody` rebuild it on the
        /// next tick, against the body that is actually there.
        public bool SetRealBody(bool want)
        {
            // The rank decides WHO, this decides WHETHER IT IS POSSIBLE —
            // and since the crowd may now hold a body when it is close, the
            // guard reads `CanWearBody` rather than the cast-only flag. A
            // grant still only ever arrives from `PopulationHost`'s ranking,
            // which is where the budget and the distance both live.
            if (!CanWearBody && want) return false;
            bool has = HasRealBody;
            if (has == want) return false;

            if (want)
            {
                Mannequin.Teardown(gameObject);
                bool ok = RealBody.TryAttachExtra(
                    gameObject, (float)Physique.For(DisplayName).Height, DisplayName,
                    cast: !IsCrowd);
                if (!ok)
                {
                    // BACK TO A MANNEQUIN IN THE SAME BREATH. A failed attach
                    // used to be harmless because the caller built a mannequin
                    // instead; here the mannequin has already been taken off,
                    // so returning early would leave a walker with no body at
                    // all — invisible, and nothing in this project measures
                    // invisibility.
                    Mannequin.Build(gameObject, _skin, _cloth, DisplayName);
                    BodyGrantsFailed++;
                    BodyGrantWhy = RealBody.ExtraWhy;
                    _body = null;
                    return false;
                }
                RealBodies++;
                BodyGrants++;
                _bodyGrantedAt = Time.time;
            }
            else
            {
                RealBody.DetachExtra(gameObject);
                Mannequin.Build(gameObject, _skin, _cloth, DisplayName);
                if (RealBodies > 0) RealBodies--;
                BodyRevokes++;
                // ONLY A SPELL THAT BEGAN WITH A GRANT WE SAW. A walker that
                // spawned holding a body has no start time, and stamping one
                // here would record a spell of zero for the longest-held body
                // in the run — the exact wrong direction for a number whose job
                // is to detect flicker.
                if (_bodyGrantedAt >= 0f && _bodySpells.Count < 20000)
                    _bodySpells.Add(Time.time - _bodyGrantedAt);
                _bodyGrantedAt = -1f;
            }
            _body = null;
            return true;
        }

        /// `realBody` is false for the anonymous crowd. See the note at the
        /// `Mannequin.Build` call below for why the split is where it is.
        /// `crowd` DECIDES WHETHER THIS PERSON MAY OUTSHINE THE CAST, and the
        /// call path is the only thing that honestly knows.
        ///
        /// `RealBody.TryAttach` lifts a coat's value to 0.68 under a comment
        /// saying "the player is a named character", and `TryAttachExtra` calls
        /// straight through it — so every walker in the city was being lifted
        /// past `Wardrobe.MaxValue` 0.46, the constant whose entire job is that
        /// nobody in the crowd outshines a cast authored at 0.65-0.75.
        ///
        /// I looked for a roster to tell them apart and there is not one worth
        /// using: `VoiceBank.Cast`'s own comment says its ids do not all match
        /// the game's, so a named character under the wrong id would silently
        /// get crowd brightness. But the CALLERS know perfectly well —
        /// `GameController` and `ActThreeHost` spawn the cast by name,
        /// `PopulationHost` spawns residents in a loop. Defaulting to cast
        /// means a new authored character is bright unless somebody says
        /// otherwise, which is the safer direction: a cast member accidentally
        /// dimmed is a lead the eye slides off.
        public static NpcWalker Spawn(string name, Color color, (GameTime at, Vector3 pos)[] schedule,
                                      bool realBody = true, bool crowd = false)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            go.name = $"NPC_{name}";
            // Was 1.0 — half a capsule. A body's ground contact is its
            // SOLE, and the two numbers are 10cm apart.
            go.transform.position = schedule[0].pos + Vector3.up * Mannequin.SoleBelowOrigin;
            // A BODY, not a capsule. Ten boxes and a sphere articulated by
            // Core/Rig — which will not be mistaken for a person and is
            // unmistakably a person WALKING, and that is the whole difference
            // between a populated street and objects sliding along one.
            //
            // The name colour becomes the clothes; skin is a warm neutral off
            // the same hue, so a crowd is varied without anybody being
            // pillar-box red from the neck up.
            var skin = new Color(Mathf.Lerp(color.r, 0.72f, 0.65f),
                                 Mathf.Lerp(color.g, 0.58f, 0.65f),
                                 Mathf.Lerp(color.b, 0.47f, 0.65f));
            // A REAL BODY IF THERE IS ONE, AND THIS IS THE LINE THAT MADE THE
            // WHOLE TOWN BOXES.
            //
            // `RealBody.TryAttach` had exactly one caller — `PlayerController`
            // — so the player was a person and all sixty-seven walkers were
            // articulated boxes. The roadmap has called that the largest single
            // immersion gap for weeks and it was one call site wide.
            //
            // NAMED CAST ONLY, and the split is deliberate rather than
            // budgetary. The people you talk to and remember are the ones worth
            // a skinned mesh; the anonymous crowd reads perfectly well as
            // mannequins at the distance you ever see them, and bounding it to
            // a known set means the cost is a number somebody chose rather than
            // whatever the population happened to be that run.
            //
            // THE HEIGHT COMES FROM `Physique`, so a street of real bodies
            // keeps the variety the mannequins had. `Physique.For` is
            // deterministic per name — the same person is the same size every
            // run, which is the rule `RealBody.PickBody` already follows for
            // WHICH body they get.
            //
            // `TryAttachExtra` rather than `TryAttach`, and that is the whole
            // reason this could not simply be switched on: `TryAttach`
            // publishes statics that five clauses of the `bodies` gate read as
            // THE PLAYER's. See its comment — the extra path runs the identical
            // attach and puts the player's readings back.
            // AND BOUNDED, because forty-four of them broke the frame budget and
            // the geometry says the cost is real rather than a runner artefact:
            // skinned vertices went 16,338 to 1,037,694 — sixty-three-fold,
            // about 23k a body, which is what a Mixamo character costs. That is
            // work on any machine, GPU or not.
            //
            // SPAWN ORDER IS THE PRINCIPALS, which is why this crude bound is
            // defensible rather than arbitrary. `GameController` spawns the
            // named cast first — Rocco, Ada, Sam, Marla, Joey — so the cap
            // lands on exactly the people the player talks to most and the
            // later, thinner cast falls back to mannequins.
            //
            // THE CAP IS NOW A BUDGET RATHER THAN A RACE. It used to be spent
            // in spawn order, which meant the twelve skinned bodies went to
            // whoever `GameController` happened to create first and stayed
            // there for the run — so the woman standing in front of you could
            // be a box while a mannequin's worth of detail was being drawn on
            // somebody four districts away.
            //
            // `PopulationHost.TickBodyDetail` now spends it on the twelve
            // NEAREST, every second, and this line only decides who is ELIGIBLE.
            // Spawning as a mannequin is deliberate: a walker created far away
            // should not pay for a skinned mesh it is about to lose, and the
            // first LOD pass grants one within a second if it really is close.
            var npc = go.AddComponent<NpcWalker>();
            npc.DisplayName = name;
            // WHO THIS PERSON IS TO THE MILL, which for the cast is their name
            // and for the crowd is NOT. See `GossipId`. Defaulted here so no
            // existing caller changes and the crowd spawn overrides it.
            npc.GossipId = name;
            npc.IsCrowd = crowd;
            npc._wantsRealBody = realBody;
            npc._skin = skin;
            npc._cloth = color;
            Mannequin.Build(go, skin, color, name);
            foreach (var (at, pos) in schedule)
                npc._schedule.Add(new Entry { MinuteOfDay = at.Hour * 60 + at.Minute, Position = pos });

            // Floating name label (billboarded toward the camera each frame).
            var labelGo = new GameObject("Label");
            labelGo.transform.SetParent(go.transform, false);
            labelGo.transform.localPosition = new Vector3(0, 1.4f, 0);
            npc._label = labelGo.AddComponent<TextMesh>();
            npc._label.text = name;
            // DERIVED FROM THE PROJECT'S OWN STATED ORDER, NOT PICKED.
            //
            // `NameTags.Pin` says it in as many words: one cap for names and
            // bubbles, and "a bubble is allowed to be the bigger of the two
            // because it is content and a name is not". Measured, the order is
            // the wrong way round — `nameFracMedian=0.064` against
            // `bubbleFracMedian=0.041`, so the label that is not content is
            // more than half again the size of the label that is.
            //
            // AND THE CAP CANNOT FIX IT, which is the part worth writing down
            // because it is where the obvious edit goes wrong. `PinFrac` is
            // 0.12 and the name P90 is 0.113, so the cap barely engages;
            // lowering it would clamp the top decile and leave the median —
            // the thing that makes the frame read as captions — untouched.
            // The size is set here, by the base character size, and nowhere
            // else.
            //
            // 0.033 is 0.055 scaled by 0.038/0.064. Screen fraction is world
            // height over distance, so it is linear in this number at a fixed
            // distance distribution, and the median lands just under the
            // bubble median instead of half again over it. The series is the
            // check: `nameFracMedian` has read 0.060 to 0.072 across all 39
            // runs that carry it — structural, not noise — so a step to about
            // 0.038 is unmistakable and a step to anything else means this
            // arithmetic was wrong.
            //
            // Somebody already halved this once, from 0.12, with the note
            // "legible, not a banner". That was right and it was not enough,
            // and there was no series to say so at the time.
            npc._label.characterSize = 0.033f;
            npc._label.fontSize = 48;
            npc._label.anchor = TextAnchor.MiddleCenter;
            npc._label.color = new Color(1f, 1f, 1f, 0f);   // fades in on approach
            // A NAME BELONGS TO SOMEBODY STANDING SOMEWHERE, so it goes behind
            // what they are standing behind. The built-in text shader is
            // ZTest Always, and a screenshot caught "Lucille Salas" lying
            // across the rooftops at noon.
            WorldText.Adopt(npc._label);
            // AND THE SHOT HAS TO BE ABLE TO RE-AIM IT. The aim below happens in
            // `Tick`; `SimDirector.Shot` renders by hand from `Update`, so the
            // committed frame is drawn with whatever rotation the last tick left
            // behind. Registering here is what lets the shot correct that.
            Billboard.Register(labelGo.transform);
            labelGo.SetActive(false);

            // On the same register-on-create, sweep-on-read discipline as the
            // billboard above and `SpeechBubble._live`: three lists of Unity
            // objects in this project, one lifetime rule.
            _live.Add(npc);
            return npc;
        }

        // A temporary detour from the ordinary routine (roadmap M8). The
        // Director schedules people into unusual places; a routine you can learn
        // is only interesting if it can also be broken for a reason.
        Vector3 _detour;
        int _detourFromDay = -1, _detourToDay = -1, _detourFromHour, _detourToHour;

        /// Puts this character somewhere they would not normally be, between two
        /// hours, for a run of days. Replaces any detour already set — one reason
        /// to be out of place at a time.
        public void SetDetour(Vector3 where, int fromDay, int days, int fromHour, int toHour)
        {
            _detour = where;
            _detourFromDay = fromDay;
            _detourToDay = fromDay + Mathf.Max(0, days - 1);
            _detourFromHour = Mathf.Clamp(fromHour, 0, 23);
            _detourToHour = Mathf.Clamp(toHour, _detourFromHour + 1, 24);
        }

        public void ClearDetour() => _detourFromDay = _detourToDay = -1;

        public bool OnDetour(GameTime now) =>
            _detourFromDay >= 0 && now.Day >= _detourFromDay && now.Day <= _detourToDay
            && now.Hour >= _detourFromHour && now.Hour < _detourToHour;

        /// Where the schedule says this NPC should be at the given time — unless
        /// something has taken them out of their routine.
        /// The place this walker is heading for right now, without the
        /// personal offset — so the population pass can group people by where
        /// they are ALL going rather than by where each of them ends up, which
        /// is the offset's own input and would be circular.
        public Vector3 PlaceFor(GameTime now) => TargetFor(now);

        Vector3 TargetFor(GameTime now)
        {
            if (OnDetour(now)) return _detour;
            int minute = now.Hour * 60 + now.Minute;
            Vector3 target = _schedule[_schedule.Count - 1].Position; // before first entry: last night's spot
            foreach (var e in _schedule)
                if (minute >= e.MinuteOfDay) target = e.Position;
            return target;
        }

        /// Where this character's routine would put them at a given time,
        /// ignoring any detour — so a meeting can be arranged AT somebody rather
        /// than at a coordinate nobody visits.
        public Vector3 RoutinePosition(GameTime now)
        {
            int minute = now.Hour * 60 + now.Minute;
            Vector3 target = _schedule[_schedule.Count - 1].Position;
            foreach (var e in _schedule)
                if (minute >= e.MinuteOfDay) target = e.Position;
            return target;
        }

        // ---- M15.2: being perceived ----
        //
        // The stance is computed in Core from state the player could only read
        // in a panel; here it becomes something they can WATCH. A body that
        // turns to follow you across a street says "they have heard about the
        // warehouse" better than any readout, and it says it while you are
        // busy doing something else.
        public StanceKind Stance = StanceKind.Indifferent;
        Transform _player;
        float _nextAvoidStep;
        float _nextConfrontPoint;

        public void SetPlayer(Transform player) => _player = player;

        /// M18. WALKING WITH THE PLAYER INSTEAD OF TO A SCHEDULE.
        ///
        /// A flag and not a subclass, because a companion is an ordinary
        /// person who happens to be next to you — that is the entire design.
        /// `Witnesses.Resolve` iterates `NpcWalker`, so an escort is a witness
        /// to everything the player does WITHOUT ONE LINE OF SPECIAL CASING:
        /// they are at two metres, in the same light, and already watching, so
        /// `Observe.Resolve` hands them a full-rung sighting the same way it
        /// hands the man across the road a poor one. See `Core/Companionship`
        /// for why that is the whole feature.
        ///
        /// **That paragraph was false for as long as it existed, and the build
        /// said so: `companionSight[with=Goran rung=0 street=1 dist=1.7m]`.**
        /// The escort geometry was right — she really was at 1.7 metres — but
        /// `Witnesses.Resolve` read "already watching" off the SUSPICION
        /// ladder, which loyalty deliberately pulls down, so the resolver
        /// scored the one guaranteed witness in the city as not looking. Fixed
        /// by reading `SecondsAttendingPlayer`, which was already being
        /// measured. Note the deleted clause: she is NOT "facing you" — she
        /// walks half a metre behind the shoulder, so the actor's face is not
        /// toward her and rung 3 is unreachable by design. Rung 4 is the one
        /// she should get, and that needs familiarity, which is the other half.
        ///
        /// `WaitingAsHost` is the precedent for a state that outranks the
        /// schedule, and it is also the warning: that one exists because a
        /// character who promised to wait walked her patrol route instead and
        /// four fixes went at the pathfinding before anybody read the text.
        public bool Escorting { get; set; }

        /// Which side they walk on, so two escorts do not stand in one place.
        /// Metres, and not a tuned number: `ConversationHost.TalkRange` is 3.0
        /// and is what this game already calls "near enough to be with
        /// somebody", so half of it is inside that and outside the body.
        public float EscortSide = ConversationHost.TalkRange * 0.5f;

        /// SOMEBODY WALKED INTO YOU (game-feel-spec.md §5).
        ///
        /// Until now the player passed through a crowd like a ghost, which
        /// quietly tells them none of it is real — the most damaging
        /// impression in the whole document, because it makes the simulation
        /// underneath get disbelieved on the strength of the contact layer.
        ///
        /// A shove is also a FACT in a game about being noticed, so a real
        /// knock buys real attention and the stance system reads it.
        Vector3 _stagger;
        float _staredUntil;

        // ---- perception (spec §17.1: ~6Hz, staggered, Near band only) ----
        Perception.Attention _attention;
        float _nextPerceptionAt;
        float _lastPerceptionAt;
        float _stationaryFor;
        /// What this walker last read the player AS, while watching. Reset
        /// when they look away, so looking back is a fresh reading.
        Notable _lastNotableSeen = Notable.None;
        bool _attendingNow;
        /// Set once per walker so the whole crowd does not evaluate on the
        /// same frame. Without it the cost is a spike every sixth of a second
        /// rather than a flat line, which is the same amount of work and a
        /// much worse frame time.
        float _phase = -1f;

        /// Returns whether this walker's attention is currently on the player.
        ///
        /// Every accrual is multiplied by the real elapsed time rather than
        /// counted per evaluation, because this runs at 6Hz and the notice
        /// threshold is in seconds. Counting ticks would make being spotted
        /// depend on the tick rate — the FrameRate bug, one system over.
        bool TickPerception(Vector3 current)
        {
            if (_phase < 0f) _phase = Random.value / Perceivers.VisionHz;
            if (Time.time < _nextPerceptionAt) return _attendingNow;
            float dt = _lastPerceptionAt <= 0 ? 1f / Perceivers.VisionHz
                                              : Time.time - _lastPerceptionAt;
            _lastPerceptionAt = Time.time;
            _nextPerceptionAt = Time.time + 1f / Perceivers.VisionHz + _phase * 0.1f;

            var to = _player.position - current; to.y = 0;
            float metres = to.magnitude;
            if (metres > Perceivers.NearBandMetres)
            {
                _attention.Tick(dt, false, 0, 0, 0);
                return _attendingNow = false;
            }

            // The cached per-frame value, not a fresh sweep of every lamp in
            // the city for a number twenty-one other walkers just computed.
            double light = Perceivers.PlayerLight;
            double offAxis = Perceivers.OffAxis(transform, _player.position);
            float speed = PlayerController.CurrentSpeed;

            // Cone, range and light first; the ray only if all three pass.
            bool inSight = Perception.InSight(metres, offAxis, light,
                                              occluded: false, subjectSpeed: speed);
            if (inSight && Perceivers.Occluded(current, _player.position)) inSight = false;

            HearLastSound(current, dt);

            _stationaryFor = speed < 0.1f ? _stationaryFor + dt : 0f;
            // BLOOD ON YOU IS NOTABLE, AND THIS SAID `false`.
            //
            // `ViolenceHost.PlayerStain` is a modelled thing with a noticeable
            // range, a social cost and a wash — the run reports
            // `blood[taken=1 noticed=5 washed=1]` — and the street's ordinary
            // attention ladder was told, in a literal, that there was never any
            // blood and never any mark. So a man walking home covered in it was
            // placed exactly as fast as a man who was not, by every stranger he
            // passed.
            //
            // `StainIsAMark` is the function for the second half and had no
            // callers at all; `lint-unreached.py` found it forty minutes after
            // being written. Its own comment says what it is for: "a stain is a
            // distinguishing mark, exactly like a limp: it feeds the
            // identification ladder rather than the case file." The ladder is
            // right here and was passing a constant.
            //
            // THE OTHER SITE WAS ALREADY CORRECT, which is what makes this the
            // usual shape. `Observation` asks the same question through
            // `v.ActorHasMark`, properly wired, because a deed's witnesses were
            // built with care. The street's everyday noticing is the copy
            // nobody looked at.
            //
            // NOT THE LIMP, YET. The player's own capability is knowable here
            // too and would belong in the same two arguments, but a limp is
            // common where a stain is rare — one run in one, briefly — and
            // changing how fast the whole street places the player on every
            // ordinary day is a decision to make at the top of a turn against
            // the perception numbers, not at the end of one.
            // AND THE FIRST VERSION OF THIS LINE WAS `PlayerStain != null`,
            // WHICH IS THE SAME FAULT ONE LAYER IN. The literal `false` was
            // wrong because the street could never see blood; a bare null check
            // is wrong because the street can now see it from forty-five
            // metres. `Notice.BloodNoticeMetres` is 4.5 and this band is 45 —
            // a factor of ten, and every one of the nine walkers in between
            // would have read a man as bloodied across a dark road.
            //
            // `Traces.Noticeable` is the model: range scaled by light and by
            // how strong the stain still is. The distance is the horizontal one
            // this tick already computed for `InSight`, so the stain is judged
            // at the range the rest of the perception judges everything else at
            // — one sensor per tick rather than two that can disagree.
            bool bloodOnMe = ViolenceHost.StainNoticeableAt(metres, light);
            // AND A CARRIED WEAPON HAS NO SHORTER RANGE THAN THE PERSON. There
            // is no `WeaponNoticeMetres` and inventing one here is exactly what
            // rule 2 forbids: a bat is a silhouette rather than a stain, so it
            // is visible for as long as its owner is, and `inSight` below is
            // the range test. If that turns out to be too generous it wants a
            // measured constant in `Notice`, not a number picked in a walker.
            var notable = Notice.What(_stationaryFor, speed, GameController.NightAmount,
                                      whereTheyShouldNotBe: false,
                                      bloodVisible: bloodOnMe,
                                      weaponVisible: CoatHost.ShowingWeapon);
            // A noteworthy person is noticed FASTER through the same
            // accumulator rather than through a second code path.
            double pull = 1.0 + Notice.Interest(notable, GameController.NightAmount);

            int rung = Perception.IdRung(metres, light, familiarity: 0.5,
                                         hasDistinguishingMark: ViolenceHost.StainIsAMark());
            bool wasAttending = _attendingNow;
            _attention.Tick(dt, inSight, Perception.ConeWeight(offAxis),
                            Perception.MotionFactor(speed) * pull, rung);
            _attendingNow = _attention.Noticed;

            // MUTUAL AWARENESS. Costs one predicate on top of a record that
            // already exists, and it is the difference between a witness you
            // know about and one you do not — which §4.4 calls the quiet horror
            // case and deliberately gives the player nothing for.
            // ONLY WHEN THEY ARE ACTUALLY LOOKING. The standoff needs both
            // halves, and `_attendingNow` is the cheap one — checking the
            // player's side first would spend a raycast per walker per tick on
            // the overwhelming majority who have not noticed anything. Same
            // ordering principle as putting the ray last inside `InSight`.
            if (_attendingNow)
                Standoff.Consider(DisplayName, true,
                                  Standoff.PlayerCanRead(_player, transform, light));

            if (_attendingNow && !wasAttending)
            {
                Perceivers.Looks++;
                if (Notice.WorthRemarking(notable, Nerve, GameController.NightAmount))
                    Perceivers.Remarks++;
            }

            // THE STREET COULD ONLY EVER CLASSIFY YOU AT THE INSTANT IT FIRST
            // LOOKED, and that is why `loiterNotices` reads 0 beside
            // `loiterLooks=35`.
            //
            // Both notice counters used to sit inside the rising-edge block
            // above, so a walker who began watching you at second five of a
            // loiter fired that edge with `notable == None` and never got
            // another. `Notice.LoiterSeconds` is 30 and the probe freezes the
            // player for thirty REAL seconds, so the classification can only
            // become Loitering at the very end of the window — by which time
            // every watcher's one and only edge is long spent. Thirty-five
            // people looked and the answer was structurally always going to
            // be zero.
            //
            // It is not only the probe. A person already watching you when
            // you START behaving oddly never re-reads you, which is wrong
            // about people and wrong for a game whose moat is what the street
            // knows. So a notice now fires when the CLASSIFICATION changes
            // for somebody who is watching, of which first-look is one case.
            //
            // `Remarks` deliberately stays on the original edge. It has a
            // landed history (`remarks=4`) and moving two numbers at once
            // would leave neither comparable — whether a remark should also
            // re-fire is the same question and it gets its own change.
            bool reclassified = _attendingNow && notable != _lastNotableSeen;
            if (reclassified)
            {
                if (notable == Notable.Loitering) Perceivers.LoiterNotices++;
                if (notable == Notable.RunningAtNight) Perceivers.NightRunNotices++;
                // THE TWO CLASSIFICATIONS THAT COULD NOT HAPPEN UNTIL TONIGHT,
                // counted here rather than trusted: both arguments were
                // literals until today, so `Notable.BloodOnClothes` and
                // `Notable.WeaponVisible` have never been returned by this call
                // in the recorded history of the project. A wiring nobody can
                // see fire is rule 6's "built is not running".
                if (notable == Notable.BloodOnClothes) Perceivers.BloodNotices++;
                if (notable == Notable.WeaponVisible) Perceivers.WeaponNotices++;
                // AND THE NOTICE SHOWS. Realising the man beside you carries
                // a knife is a recoil; clocking a loiterer is a look. These
                // ride the same edge the counters do, so a notice that fires
                // is a notice a bystander could SEE fire — which is what the
                // whole perception ladder has lacked on screen.
                if (notable == Notable.BloodOnClothes || notable == Notable.WeaponVisible)
                    React("flinch", 1.5f);
                else if (notable == Notable.Loitering || notable == Notable.RunningAtNight)
                    React("glance", 1.6f);
            }
            // KEPT ACROSS A LOOK-AWAY, and resetting it was an over-count.
            //
            // "Looking back is a fresh reading" sounded right and measured
            // wrong: `nightRunNotices` went from 4 to 139 in one build. A
            // walker who glances away and back re-read the player as new, and
            // in a milling crowd that happens constantly — so it counted
            // glances rather than realisations.
            //
            // `loiterNotices` did not show it, because a loiter is one flip
            // inside a two-second window and nobody had time to look away and
            // back. One number confirming a fix while another one silently
            // inflates is exactly the shape worth grepping for, and this time
            // both were in the same three lines.
            //
            // So the reading persists: a person who looks back at the SAME
            // behaviour has not noticed anything new, and one who looks back
            // at a DIFFERENT one has.
            if (_attendingNow) _lastNotableSeen = notable;
            return _attendingNow;
        }

        Vector3 _investigateAt;
        float _investigateUntil = -1f;
        float _lastSoundHeardAt = -999f;
        /// Rises when something is heard and decays, which is what makes an
        /// already-nervous person hear more — `Perception.EffectiveFloor`
        /// takes it and drops their floor. Escalation with no state machine.
        float _alertness;

        public bool Investigating => _investigateUntil > Time.time;

        /// Did this walker hear the last thing that happened, and does it care?
        ///
        /// Called on the vision tick rather than on a timer of its own, so
        /// hearing genuinely costs nothing until something makes a sound.
        void HearLastSound(Vector3 current, double dt)
        {
            _alertness = Mathf.Max(0f, _alertness - (float)dt * 0.08f);
            if (!Perceivers.SoundIsFresh || Perceivers.LastSoundTime <= _lastSoundHeardAt) return;

            float metres = Vector3.Distance(current, Perceivers.LastSoundAt);
            double floor = Perceivers.AmbientFloorAt(current, Perceivers.PresentNearby);
            // CHEAP TEST FIRST. If it would not reach even through open air,
            // there is nothing a wall can change and the raycast is wasted —
            // and most sounds do not reach most people, so this is the common
            // case rather than a corner of it.
            if (!Perception.Heard(metres, Perceivers.LastSoundLoudness, floor,
                                  occluded: false, alertness: _alertness))
                return;
            bool occluded = Perceivers.Occluded(current, Perceivers.LastSoundAt);
            if (!Perception.Heard(metres, Perceivers.LastSoundLoudness, floor, occluded, _alertness))
                return;

            _lastSoundHeardAt = Perceivers.LastSoundTime;
            _alertness = Mathf.Min(1f, _alertness + 0.35f);

            // What they DO about it is the reaction ladder's decision, not
            // this file's. Hearing something is not the same as caring, and a
            // timid person walking toward a gunshot would be wrong.
            double severity = Feel.Clamp01(Perceivers.LastSoundLoudness / 100.0);
            var what = Reaction.Decide(severity, Nerve, dutiful: 0.4,
                                       willingness: 0.7, sawABody: false,
                                       alreadyAlarmed: false);
            if (what == Reacted.Investigate)
            {
                // WHERE THEY THINK IT WAS, WHICH IS NOT WHERE IT WAS.
                //
                // This used to be `_investigateAt = Perceivers.LastSoundAt` —
                // the exact position of the sound, walked to precisely.
                // Hearing cannot tell anybody that, and it is why
                // `Perception.HeardAs` is a function rather than a comment:
                // what a listener gets is a bearing and a range and never an
                // identity or a point.
                //
                // Through a wall you localise to the wall. `BelievedAt` is
                // not an error term with a magnitude I picked — that would be
                // rule 2, since nothing here has ever measured how well a
                // person places a bang. It is the geometry they actually
                // have: the sound arrived through the nearest surface between
                // them, so that surface is as far as they can tell.
                //
                // The occlusion raycast was already run above, so this is one
                // more cast on the rare path where somebody actually decides
                // to go and look, not on the common one.
                Vector3 toSound = Perceivers.LastSoundAt - current;
                float wall = occluded
                    ? Perceivers.OccluderDistance(current, Perceivers.LastSoundAt)
                    : -1f;
                var believed = Perception.BelievedAt(
                    Mathf.Atan2(toSound.x, toSound.z) * Mathf.Rad2Deg, metres,
                    occluded, wall);
                Vector3 dir = toSound.sqrMagnitude > 1e-6f
                    ? toSound.normalized : transform.forward;
                _investigateAt = current + dir * (float)believed.metres;
                _investigateUntil = Time.time + 8f;
                Perceivers.NoiseInvestigations++;
                if (believed.metres < metres - 0.01) Perceivers.BeliefsShortened++;
                // Heard it, TURNED, went — the glance halts them a beat
                // before the walk toward the sound begins, which is the
                // order a person does it in.
                React("glance", 1.2f);
            }
            else if (what == Reacted.Alarm)
            {
                // An alarm is a shout, so it makes the same kind of event it
                // came from. Panic propagates through the hearing model rather
                // than through a system built for it.
                Perceivers.Emit(current, Reaction.LoudnessOf(Reacted.Alarm), "alarm");
                // And the body does what the voice does: the Scared clip is
                // the shout made visible.
                React("flinch", 1.5f);
            }
        }

        /// Whether this walker's attention is currently on the player. Read by
        /// the hush, which needs a count of attending people per frame and
        /// must not re-run anybody's perception to get it.
        public bool AttendingPlayer => _attendingNow;

        /// HOW LONG THIS WALKER HAS HAD ITS EYES ON THE PLAYER, in seconds.
        ///
        /// `Perception.NoticeSeconds` is documented as *"seconds of continuous
        /// presence in the acuity band before a glance becomes a look"* — a
        /// quantity about geometry, light and time. `Witnesses.Resolve` needs
        /// exactly that and had no way to ask for it, so it substituted a
        /// two-valued guess off the SUSPICION ladder: 3.0 for anybody already
        /// in `Watches`, 0.0 for everybody else. Those are different
        /// quantities, and the run says so — forty people in clear line of
        /// sight in a market produced zero sightings, and the one person
        /// walking at the player's shoulder produced a worse account of a
        /// stabbing than a stranger across the road.
        ///
        /// The number was already here. `_attention` accrues real dt-weighted
        /// seconds at 6Hz for every walker in the near band, through cone,
        /// light and occlusion, and nothing outside this class had ever read
        /// it. Rule 3, from the other side: the instrument was fine and the
        /// consumer was measuring something else.
        public double SecondsAttendingPlayer => _attention.Seconds;

        /// The rung this walker's own accumulator reached, for the same
        /// reason: it exists, it is real, and the witness path recomputed a
        /// worse one from scratch.
        ///
        /// `Reached()` RATHER THAN `Rung`, and the difference is the whole
        /// point of the accumulator. `Rung` is the best identification the
        /// geometry ever ALLOWED; `Reached()` is what this person would say if
        /// asked, and it returns 0 unless they actually NOTICED — the two come
        /// apart for somebody who was in the right light at the right distance
        /// and never looked long enough for it to register.
        ///
        /// Handing the raw rung to the witness path would let a man who walked
        /// past without a glance carry a floor into a deed he did not attend,
        /// which is the same shape as naming somebody through a wall and was
        /// one field away from shipping.
        public int AttentionRung => _attention.Reached();

        /// HAS THIS PERSON WORKED OUT WHO YOU ARE, as distinct from having
        /// looked at you. `Noticed` is a glance that stuck; `Identified` is
        /// long enough in the acuity band to put a name to a face, and the
        /// gap between them is most of what being careful in this city
        /// means. Core has drawn the distinction since it was written and
        /// nothing in the game has ever asked for it — `Reached()` folds it
        /// into a rung, which is not the same as being able to COUNT the
        /// people who got there.
        public bool HasIdentifiedPlayer => _attention.Identified;

        /// Nerve, for whether they say something rather than only look. The
        /// crowd's walkers do not all have a `Gossiper` behind them, so this
        /// defaults to the middle of the range rather than pretending.
        public float Nerve = 0.5f;

        public void Bumped(Vector3 fromPlayer, float relativeSpeed)
        {
            var kind = Bumps.Classify(relativeSpeed);
            var away = fromPlayer; away.y = 0;
            if (away.sqrMagnitude > 0.001f)
                _stagger = away.normalized * (float)Bumps.Stagger(relativeSpeed);
            _staredUntil = Time.time + (float)Bumps.AttentionSeconds(kind);
            if (Bumps.WorthRemembering(kind))
            {
                BumpsWorthRemembering++;
                // A knock is the one contact everybody agrees deserves a
                // visible startle. The flinch starts as the stagger decays,
                // which reads as impact first, recoil after.
                React("flinch", 1.2f);
            }
        }

        /// Knocks and shoves only. Read by the sim so "you barge through this
        /// city" is something the world can know about you.
        public int BumpsWorthRemembering { get; private set; }

        CharacterRig _body;
        Vector3 _lastBodyPos;
        double _gaitPhase;

        // ---- momentary reactions (M17.4 T3: the street answers back) ------
        //
        // Six clips sat on disk since 18 August with no consumer — flinch,
        // glance, greet, wave, point, head_no — while the perception events
        // they belong to fired invisibly. This is the wire: a REACTION is a
        // timed activity override. It outranks the standing repertoire for a
        // second or two, halts the walk so it can actually be seen (an
        // activity only plays while the body is still), and then everything
        // resumes as if it had not happened.
        string _reaction;
        float _reactionUntil;
        float _reactionCooldownUntil;
        int _headNoWindow = -1;

        /// Played and refused, run-cumulative, read on the done line. The
        /// refusals matter for the same reason `ActivityRefused` exists: a
        /// street that never reacts and a controller that cannot are
        /// different faults with identical screenshots (rule 3b).
        ///
        /// REFUSED IS THE SUM OF ITS REASONS NOW (22 Aug). The cooldown
        /// return used to exit without touching any counter, so on V the
        /// arithmetic did not close: 466 asks, 63 played, 337 refused, 66
        /// vanished. `ReactionsRefused` therefore CHANGED MEANING — it was
        /// "no capability" only and is now every ask that did not play —
        /// and the two reasons print separately, because a street kept
        /// quiet by its own cooldown and one whose rigs lack the state
        /// want opposite fixes (a tuning constant against clip wiring).
        public static int ReactionsPlayed, ReactionsRefused;
        public static int ReactRefusedCooldown, ReactRefusedNoState;
        public static readonly Dictionary<string, int> ReactByKind =
            new Dictionary<string, int>();
        /// Asks per kind, tallied before any gate — d3aafab printed
        /// `greet:0` and `head_no:0` and the play counts alone cannot say
        /// whether those kinds were never asked for or always refused,
        /// which are different faults in different systems (the bark
        /// gesture wiring against the rig's slot table). Rule 3b again:
        /// a zero ships with its denominator.
        public static readonly Dictionary<string, int> ReactAsksByKind =
            new Dictionary<string, int>();

        /// Play a momentary clip: flinch, glance, greet, wave, point,
        /// head_no. Capability is checked HERE, at the ask, so a slot the
        /// controller cannot serve is one counted refusal rather than a
        /// refusal per frame inside `DriveActivity` — and the cooldown keeps
        /// a walker from chaining reactions into a fit.
        public void React(string slot, float seconds)
        {
            int a; ReactAsksByKind.TryGetValue(slot, out a);
            ReactAsksByKind[slot] = a + 1;
            if (Time.time < _reactionCooldownUntil)
            {
                ReactionsRefused++;
                ReactRefusedCooldown++;
                return;
            }
            if (_body == null || !_body.HasActivityState(slot))
            {
                ReactionsRefused++;
                ReactRefusedNoState++;
                return;
            }
            _reaction = slot;
            _reactionUntil = Time.time + seconds;
            _reactionCooldownUntil = Time.time + 6f;
            ReactionsPlayed++;
            int c; ReactByKind.TryGetValue(slot, out c);
            ReactByKind[slot] = c + 1;
        }

        /// The gait, from distance actually covered rather than from whether
        /// the walk state says "walking". Somebody shoved sideways, steering
        /// round a bin or stopped by a red light all move at speeds their
        /// state machine does not know about, and a stride that ignores that
        /// is the foot-sliding every graybox crowd has.
        void DriveBody()
        {
            if (_body == null)
            {
                _body = CharacterRig.Attach(gameObject);
                _lastBodyPos = transform.position;
                if (_body == null) return;
                // THIS PERSON'S OWN WALK, WHICH THE REAL-BODY PATH LOSES.
                //
                // `CharacterRig.Bind` reads gait bias, bad leg and idle phase
                // off `Mannequin.Shape` — and a bought body has no Mannequin,
                // so every one of the named cast would take the defaults and
                // the street would walk in perfect unison. A crowd where
                // everybody has the same stride is the thing the per-person
                // physique exists to prevent, and it would have read as the
                // real bodies looking WORSE than the boxes they replaced.
                //
                // `Physique.For` is the same deterministic source `Mannequin`
                // uses, keyed on the same name, so the two tiers cannot
                // disagree about who walks how. Set unconditionally rather than
                // only for real bodies: on a mannequin it writes the identical
                // values `Bind` already read, which is a no-op that cannot
                // drift from them.
                var shape = Physique.For(DisplayName);
                _body.GaitBias = shape.Gait;
                _body.BadLegIsLeft = shape.BadLegIsLeft;
                _body.IdleOffset = shape.IdlePhase;
                _body.HeadScale = shape.HeadScale;
                // The rig binds LAZILY, several passes after the population
                // pass first pushed a capability in, so the setter's write had
                // nowhere to go. Anybody already hurt when their body arrives
                // would otherwise walk evenly until the next push — which for a
                // body granted and dropped by the LOD band is most of a run.
                _body.Capability = _capability;
            }
            float dt = Time.deltaTime;
            if (dt <= 0) return;
            var here = transform.position;
            float moved = Vector3.Distance(new Vector3(here.x, 0, here.z),
                                           new Vector3(_lastBodyPos.x, 0, _lastBodyPos.z));
            _lastBodyPos = here;
            double speed = moved / dt;
            _body.Speed = speed;

            // WHAT THIS PERSON IS DOING, not merely how fast (town-plan T3).
            //
            // Only while genuinely stopped: a clip of somebody leaning on a
            // wall played by somebody crossing a road is worse than no clip.
            // The choice is deterministic per person — a body that reshuffles
            // its activity every frame reads as a glitch, and a stable one
            // reads as a character trait.
            //
            // TALK AND ARGUE ARE THE BIG ONES because conversation is this
            // game's whole moat and it has been performed, until now, by two
            // people standing perfectly still facing each other. `argue` for
            // the sourer quarter of confabs, by a hash of the pair, so the
            // street has both registers in it.
            if (speed > Ledger.Core.Rig.StillBelowMetresPerSec)
            {
                _body.Activity = null;
            }
            else if (_reaction != null && Time.time < _reactionUntil)
            {
                // A reaction outranks the standing repertoire for its moment
                // — somebody mid-lean who flinches at a shout should flinch,
                // and the lean resumes by itself when the window closes.
                _body.Activity = _reaction;
            }
            else if (InConfab)
            {
                _body.Activity = (ActivityHash() & 3) == 0 ? "argue" : "talk";
                // AND THE ODD SHAKE OF THE HEAD. Two people who talk for a
                // minute without one disagreement read as a mime act. Once
                // per window, a quarter of windows, deterministic per person
                // — rare enough to stay a character beat rather than a tic.
                int w = (int)(Time.time / 24f);
                if (w != _headNoWindow)
                {
                    _headNoWindow = w;
                    if (((ActivityHash() ^ w) & 3) == 0) React("head_no", 1.4f);
                }
            }
            else if (WaitingAsHost)
            {
                // Somebody who promised to wait looks like somebody waiting
                // — against a wall, against a post, or just standing. Three
                // ways, per person, so two hosts on one corner differ.
                int hw = ActivityHash() % 3;
                _body.Activity = hw == 0 ? "lean_wall"
                               : hw == 1 ? "idle_bored" : "lean";
            }
            else
            {
                // AND WHAT THE PLACE THEY ARE STANDING AT IS FOR. Somebody
                // stopped outside a bar is having a cigarette; somebody
                // behind a counter is working it; somebody at a phone is on
                // the phone — and until now all three stood to attention,
                // which is the social sim being invisible while it runs.
                //
                // The place is looked up once and CACHED per stop, not per
                // frame: `HookMap.Places` is sixty-one entries and this is
                // every walker on every tick, which is exactly the shape of
                // cost this project has paid for before.
                if (_activityStopAt != Vector3.zero
                    && (here - _activityStopAt).sqrMagnitude > 4f)
                    _activityAtPlace = null;   // moved on; ask again
                if (_activityAtPlace == null)
                {
                    _activityStopAt = here;
                    _activityAtPlace = BenchSeatNear(here)
                                     ?? ActivityForPlaceNear(here) ?? "";
                }
                _body.Activity = _activityAtPlace.Length > 0 ? _activityAtPlace : null;
            }
            // SAMPLED WHERE IT IS MEASURED, not where it is configured. A
            // constant says what the walker was ASKED to do; this says what
            // the body was actually handed, which is the number the gait
            // draws and therefore the number the frame shows. Only while
            // genuinely moving, or a crowd standing at its stops would drag
            // the mean toward zero and hide a street of joggers.
            if (speed > Ledger.Core.Rig.StillBelowMetresPerSec)
            {
                if (speed > CrowdSpeedPeak) CrowdSpeedPeak = speed;
                CrowdSpeedSum += speed;
                CrowdSpeedSamples++;
            }
            // Cadence rises with speed, so a hurrying person takes faster
            // steps rather than longer ones.
            _gaitPhase = (_gaitPhase + speed * dt * 0.62) % 1.0;
            _body.Phase = _gaitPhase;
        }

        // ---- standing and talking to somebody ----------------------------
        //
        // The game's whole thesis is that the antagonist is gossip, and the
        // street has always shown none of it: rumours pass along the contact
        // graph every tick while a dozen people walk past each other in
        // silence. Now that there are bodies, the exchange can be a thing you
        // WATCH — two strangers stopping, turning in, leaning toward each
        // other. That is the central mechanic taught without a line of UI.
        //
        // Every number comes from Core/Confab, which is where they are
        // tested. This holds the state.
        NpcWalker _talkingTo;
        float _confabUntil, _confabStarted, _confabTotal;
        double _confabDistance = Confab.NearMetres;
        double _confabOffAxis = Confab.OffAxisDegrees;

        public bool InConfab => _talkingTo != null && Time.time < _confabUntil;

        /// Set by GameController while this walker is the host of an open
        /// beat. Cleared the moment the window closes, so a host who was
        /// stood up goes back to their evening.
        public bool WaitingAsHost { get; set; }

        string _activityAtPlace;
        Vector3 _activityStopAt;

        /// What somebody standing HERE would plausibly be doing, from the
        /// nearest authored place and its kind — or null for "just standing",
        /// which is a perfectly good thing to be doing on a pavement.
        ///
        /// The vocabulary is the harvest's clip slots, so a name that reaches
        /// here is a name the rig can already play. Deterministic per person:
        /// two people outside the same pub should not both light up in the
        /// same frame like a chorus line.
        string ActivityForPlaceNear(Vector3 here)
        {
            Ledger.Core.HookPlace best = null;
            double bestD2 = 7.0 * 7.0;      // arm's length of a doorway
            foreach (var p in Ledger.Core.HookMap.Places)
            {
                double dx = p.X - here.x, dz = p.Z - here.z;
                double d2 = dx * dx + dz * dz;
                if (d2 < bestD2) { bestD2 = d2; best = p; }
            }
            if (best == null) return null;
            int h = ActivityHash();
            // TWO PLACES ARE MORE SPECIFIC THAN THEIR KIND, and both came out
            // of the reach sweep (clip-reach.py): `phone_box` and `drink`
            // were states built into every controller that no writer had
            // ever asked for. The letter stall is where the town's one
            // outdoor line stands — WorldBuilder puts the box there — so
            // somebody stopped at the stall is sometimes ON it; and the pub
            // door is where people drink standing up.
            if (best.Id == "letter_stall" && (h & 3) == 0) return "phone_box";
            if (best.Id == "bar_door")
                return (h & 3) == 0 ? "drink"
                     : (h & 3) == 1 ? "lean_wall" : null;
            switch (best.Kind)
            {
                case "business":
                    // Behind the counter, waiting to be served, or carrying
                    // stock in — the split is per person, so a shop has all
                    // three in it.
                    return (h & 3) == 0 ? "work_counter"
                         : (h & 3) == 1 ? "carry_bag"
                         : (h & 3) == 2 ? "carry" : null;
                case "landmark":
                    return (h & 3) == 0 ? "look_around" : null;
                case "corner":
                    // A shelter is where people wait, smoke and lean. The
                    // smoke slice stands even though the harvest hole means
                    // the ask is refused today: when the clip lands, the
                    // corners light up with no further wiring.
                    return (h & 3) == 0 ? "smoke"
                         : (h & 3) == 1 ? "lean_wall"
                         : (h & 3) == 2 ? "idle_bored" : null;
                case "home":
                    return (h & 7) == 0 ? "smoke" : null;
                default:
                    return null;
            }
        }

        /// A BENCH IS AN INVITATION. `Furniture` records every park bench it
        /// places; somebody who stops within a couple of metres of one takes
        /// the seat — which is the whole social reason benches exist, and
        /// the `sit` clip's first consumer (it was STATE-ONLY in the reach
        /// sweep: built into every controller, never once entered).
        string BenchSeatNear(Vector3 here)
        {
            foreach (var seat in Furniture.BenchSeats)
            {
                double dx = seat.x - here.x, dz = seat.z - here.z;
                if (dx * dx + dz * dz < 2.0 * 2.0) return "sit";
            }
            return null;
        }

        /// A stable number per person, for choosing WHICH activity they do.
        /// From the gossip id when there is one and the object name
        /// otherwise, so the same body makes the same choice every frame of
        /// every run — a walker that reshuffles its activity per frame reads
        /// as a glitch, and one that keeps it reads as a character.
        int ActivityHash()
        {
            var key = GossipId ?? DisplayName ?? name;
            int h = 17;
            foreach (var c in key) h = h * 31 + c;
            return h & 0x7fffffff;
        }

        /// Begin one. Called on both halves of a pair, by whoever noticed the
        /// exchange — the walkers do not decide this, the gossip does.
        /// `aboutPlayer` is a parameter rather than a property set beforehand
        /// because it is the one input that decides whether this pair breaks
        /// off when he walks up, and a flag the caller can forget to set is a
        /// feature that silently never fires.
        public void BeginConfab(NpcWalker other, double tie, bool sensitive, bool hostile,
                                bool aboutPlayer)
        {
            if (other == null || other == this) return;
            if (Time.time < _confabBlockedUntil) return;
            _talkingTo = other;
            _confabTie = tie;
            _confabAboutPlayer = aboutPlayer;
            _confabTotal = (float)Confab.Seconds(tie, sensitive);
            _confabStarted = Time.time;
            _confabUntil = Time.time + _confabTotal;
            _confabDistance = Confab.Distance(tie, sensitive);
            _confabOffAxis = Confab.OffAxis(hostile);
            _hushing = false;
        }

        bool _confabAboutPlayer;
        double _confabTie;
        bool _hushing;
        float _confabBlockedUntil;

        /// THE MOMENT THE WHOLE THING IS FOR. A pair who break off as he
        /// walks up have told him they were talking about him, that they know
        /// he can see them, and that they would rather he had not heard —
        /// which no interface could say, and two people stopping does.
        /// Counted for the sim gate, and counted in PAIRS of numbers because
        /// the claim is conditional. "Some pairs hushed" is not the design —
        /// the design is that a pair discussing the fish price keeps talking
        /// while he walks straight through them, which is exactly what makes
        /// the ones who DON'T mean something. A run where every pair hushed
        /// is a proximity trigger, and a proximity trigger is what this is
        /// not; both failures need a number to be visible.
        public static int HushWalkBys { get; private set; }
        public static int Hushes { get; private set; }

        void CheckHush()
        {
            if (_hushing || _talkingTo == null || _player == null) return;
            float d = Vector3.Distance(transform.position, _player.position);
            if (d <= (float)Confab.HushRadiusMetres) HushWalkBys++;
            if (!Confab.ShouldHush(_confabAboutPlayer, d, _confabTie)) return;
            _hushing = true;
            Hushes++;
            // They finish the word. A pair that cuts out the frame he crosses
            // a line is a trigger, and a trigger is what this is not.
            _confabUntil = Mathf.Min(_confabUntil, Time.time + (float)Confab.HushSeconds);
            _confabTotal = Mathf.Max(0.01f, _confabUntil - _confabStarted);
            // And they do not pick it back up when he leaves. Somebody caught
            // talking about you moves off, and the street is quieter behind
            // you.
            _confabBlockedUntil = Time.time + (float)Confab.HushCooldownSeconds;
        }

        /// Where this walker wants to stand and face while talking, or false
        /// if they are not. Returns the target the ordinary steering should
        /// be overridden with.
        bool ConfabTarget(Vector3 current, out Vector3 stand, out Vector3 face)
        {
            stand = current; face = transform.forward;
            if (!InConfab) { _talkingTo = null; return false; }
            var them = _talkingTo.transform.position;
            var toThem = them - current; toThem.y = 0;
            if (toThem.sqrMagnitude < 0.0001f) return false;

            float commitment = (float)Confab.Commitment(Time.time - _confabStarted, _confabTotal);

            // THE LISTENER WALKS OVER, not both. Two people converging on a
            // point neither occupied reads as choreography, because that is
            // something that only happens when somebody arranged it.
            // Somebody with news stands still; somebody who wants it comes.
            var dir = toThem.normalized;
            stand = _approachesInConfab
                ? them - dir * (float)_confabDistance
                : current;
            // Ease in, so the walk over is a walk rather than a snap.
            stand = Vector3.Lerp(current, stand, commitment);

            // Shoulders angled off the line between them, not squared up:
            // face-on is the posture of an argument, and a street staging
            // every conversation that way reads as one about to kick off.
            face = Quaternion.Euler(0, (float)(_confabOffAxis * _offAxisSide), 0) * dir;
            return true;
        }

        bool _approachesInConfab;
        float _offAxisSide = 1f;

        /// Which of the pair goes to the other, and which way each angles
        /// off. Set once when the pair is formed so the two halves cannot
        /// disagree — both leaning the same way puts them shoulder to
        /// shoulder facing a wall.
        public void SetConfabRole(bool approaches, bool leansLeft)
        {
            _approachesInConfab = approaches;
            _offAxisSide = leansLeft ? -1f : 1f;
        }

        public void Tick(GameTime now)
        {
            var target = TargetFor(now);
            var current = transform.position;

            // WHO IS NEAR THE PLAYER, AND WHO IS LOOKING — reported before
            // anything can return early.
            //
            // `Perceivers` has always said these were "maintained by
            // NpcWalker". They were not: the only writer was `SimDirector`,
            // which runs in CI and nowhere else, so in a real play session the
            // hush never fell, the crowd never raised the ambient floor, and
            // the caption bar's attention channel could not fire. Three
            // systems doing nothing behind one true-sounding sentence.
            //
            // ABOVE `WaitingAsHost`, deliberately. Somebody standing still
            // because they promised to wait for you is emphatically present,
            // and the early return below would have made the room go quiet
            // whenever the only people in it were the ones waiting for you.
            if (_player != null)
                Perceivers.Report(Vector3.Distance(current, _player.position), _attendingNow);

            // A HOST WAITS. Ada's invitation says "I'll wait up"; Rocco says
            // "my front step". They then walked their patrol route all
            // evening, and the player — who moves at about the same speed —
            // spent ninety in-game minutes in a tail chase that closed to
            // nine and a half metres and never any nearer. Four fixes went
            // at the marker, the radius and the bot's budget before it became
            // clear the invitation was walking away from whoever accepted it.
            //
            // This is a writing bug wearing a pathfinding costume: the text
            // promises somebody standing still, and only the text was doing
            // that.
            if (WaitingAsHost) return;

            // A conversation outranks a schedule. Somebody who walks off
            // mid-sentence because it is nine o'clock is the exact failure
            // this is meant to fix.
            CheckHush();
            if (ConfabTarget(current, out var standAt, out var faceDir))
            {
                // AT A WALK, NOT AT HALF ONE. This was `MoveSpeed * 0.55f`,
                // and the 0.55 was calibrated when `MoveSpeed` was 2.6 — it
                // existed to make somebody crossing to talk approach at 1.43
                // rather than at a jog, which was right.
                //
                // Against a real 1.4 m/s walk the same factor produces 0.77:
                // a shuffle, for a person who has decided to go and speak to
                // somebody. Nobody chose that. It is the constant left behind
                // when the thing it was a fraction OF changed underneath it,
                // which is the same shape as a comment going stale and just as
                // invisible in a diff that does not touch the line.
                //
                // A person walking over to say something walks. `MoveSpeed` is
                // now the walk, so the fraction has nothing left to do.
                var step = Vector3.MoveTowards(current, new Vector3(standAt.x, current.y, standAt.z),
                                               MoveSpeed * Time.deltaTime);
                transform.position = step;
                if (faceDir.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation,
                        Quaternion.LookRotation(faceDir), 5f * Time.deltaTime);
                // The head goes to the person they are talking to, which is
                // what the off-axis stance leaves room for: the body is
                // angled and the face is not.
                // AND THEY LOOK AWAY. Breaking off while still staring at
                // each other is two people pausing; breaking off and finding
                // somewhere else to look is two people who have been caught,
                // and the second is the one worth the whole feature.
                if (_body != null) _body.LookAt = _hushing ? null : _talkingTo.transform;
                DriveBody();
                return;
            }

            // The stumble resolves over a moment rather than teleporting them
            // sideways: displacement first, recovery after.
            if (_stagger.sqrMagnitude > 0.0001f)
            {
                var step = Vector3.ClampMagnitude(_stagger, 2.2f * Time.deltaTime);
                transform.position = current + step;
                _stagger -= step;
                current = transform.position;
            }

            // Somebody who wants nothing to do with you puts distance between
            // you — the ladder's "avoids" rung, expressed as walking away
            // rather than as a word in a book.
            if (_player != null && Stance >= StanceKind.Avoids && Stance < StanceKind.Confronts)
            {
                float toPlayer = Vector3.Distance(current, _player.position);
                if (toPlayer < 7f && Time.time > _nextAvoidStep)
                {
                    _nextAvoidStep = Time.time + 2.5f;
                    var away = (current - _player.position); away.y = 0;
                    if (away.sqrMagnitude > 0.01f)
                        target = current + away.normalized * 9f;
                }
            }

            // AND THE TOP OF THE LADDER MAKES IT PERSONAL. `Confronts` has
            // always been a word in the stance enum and a line of dialogue;
            // now the body stops, comes round, and POINTS — the accusation
            // made visible from across a street, no interface at all. Long
            // per-person cooldown so it lands as an event, not a loop.
            if (_player != null && Stance == StanceKind.Confronts
                && Time.time > _nextConfrontPoint
                && Vector3.Distance(current, _player.position) < 8f)
            {
                _nextConfrontPoint = Time.time + 25f;
                _staredUntil = Mathf.Max(_staredUntil, Time.time + 2f);
                React("point", 1.8f);
            }

            // WALKING TOWARD A NOISE, which spec §8 calls the highest-value
            // behaviour in the whole system — it turns one sound into a moving
            // problem, and it explains itself to the player with no interface
            // at all. A man coming toward the thing you just did is the
            // clearest statement this game can make.
            if (_investigateUntil > Time.time) target = _investigateAt;

            // AND A COMPANION STAYS WITH YOU — last, so it outranks both the
            // schedule and the noise.
            //
            // OUTRANKING THE NOISE IS THE DELIBERATE PART. Investigating is
            // the best behaviour in the walker and this overrides it, because
            // an escort who walks forty metres off to look at a scream has
            // stopped being an escort, and the player would experience the
            // feature as a follower that keeps losing them. They hold the
            // shoulder; what they SAW is settled by `Witnesses.Resolve` from
            // where they are standing, which is beside you, which is the
            // point.
            if (Escorting && _player != null)
            {
                var beside = _player.right * EscortSide;
                target = _player.position - _player.forward * (EscortSide * 0.5f) + beside;
            }

            // AN ESCORT WHO IS NOT AT YOUR SHOULDER YET HURRIES TO IT.
            //
            // `companionSight[with=Filip rung=0 street=4 dist=31.0m]`. At
            // thirty-one metres rung 0 is CORRECT — she genuinely could not see
            // it — so the perception model is right and the FOLLOWING is wrong,
            // which is the opposite of where two earlier rounds looked.
            //
            // `CompanionHost.Ask` has no proximity requirement, so the sim
            // recruits the first willing gossiper wherever they happen to be.
            // That was survivable at 2.6 m/s. Dropping the crowd to a real
            // walking 1.4 halved the closing speed, and against a player who is
            // also moving it can mean never arriving — a regression I caused
            // tonight that surfaced as a perception failure two systems away.
            //
            // Hurrying is the fix already argued for: the walk-speed note said
            // that if anything fell behind, hurry the ones who are late rather
            // than make everybody run. Somebody half a street away catching up
            // to walk with you is also what a person does.
            //
            // `TalkRange`, not a new number — it is what this project already
            // calls "near enough to be with somebody".
            float moveAt = MoveSpeed;
            if (Escorting && _player != null
                && Vector3.Distance(current, _player.position) > ConversationHost.TalkRange)
                moveAt = CatchUpSpeed;

            // A PLACE IS NOT A POINT, AND UNTIL NOW IT WAS.
            //
            // THE SEPARATION NUDGE WAS FIGHTING THE SCHEDULE TO A DRAW, and the
            // series says so more clearly than any argument: `crowdGapMedian`
            // went 0.00, 0.20, 0.29, 0.33, 0.29 and stopped, against a body
            // width of 0.45 that the nudge is trying to open up. A fix that
            // moves a number a third of the way and then plateaus is a fix
            // pulling against something.
            //
            // Here is the something, and it is arithmetic rather than
            // suspicion. `moving` is false within 0.2m of the target, so
            // everybody converges to within 0.2m of their scheduled point —
            // and two people whose schedules name the SAME point therefore
            // settle within 0.4m of each other, inside the 0.45m the nudge is
            // trying to keep clear. Every frame the schedule pulls them back
            // in and the nudge pushes them out, and the standoff lands at
            // about 0.3m, which is exactly what has been printed for four
            // builds.
            //
            // So a scheduled place stops meaning one metre of ground. Each
            // person stands at their own spot AROUND it — deterministic from
            // their name, so the same person takes the same place every run and
            // the crowd does not shimmer, and the same source `Physique` and
            // `RealBody.PickBody` already use for per-person variation.
            //
            // 0.8m IS TWO SHOULDERS, not a number I liked: two people on
            // opposite sides of a 0.8m ring are 1.6m apart at worst and 0.8m
            // apart at the tightest useful angle, both comfortably clear of a
            // body width, and both comfortably inside the 3m people talk at —
            // so this cannot break a confab, which is the thing the nudge's own
            // note was careful about too.
            //
            // NOT APPLIED TO AN ESCORT: their target is your shoulder, computed
            // above from your facing, and standing a metre off it deterministically
            // is exactly the fault the escort work spent two rounds fixing.
            var spot = Escorting ? target : Spread(target);
            var flatTarget = new Vector3(spot.x, current.y, spot.z);

            // HOW FAR BEHIND ITS OWN SCHEDULE THIS BODY IS, which nothing has
            // ever asked. `npcsMoved=True` proves the walkers MOVE; it says
            // nothing about whether they ARRIVE.
            //
            // That distinction is the leading explanation for two regressions
            // from one constant tonight. `Confab.StartWithinMetres` is 6.5 and
            // is purely a distance test, so slowing the crowd cannot make a
            // pair "too far apart" at any given instant — unless people stop
            // reaching the places their schedules send them, in which case
            // socially-connected characters simply stop co-locating and the
            // rumour graph fires exchanges between two people who are nowhere
            // near each other. The escort stranded at thirty-one metres is the
            // same fact seen from the other end.
            //
            // Mean and worst, because a crowd where everybody is four metres
            // adrift is a completely different world from one where two people
            // are two hundred metres adrift and everybody else is fine.
            if (!Escorting && !InConfab && !WaitingAsHost)
            {
                float lag = Vector3.Distance(current, flatTarget);
                ScheduleLagSum += lag;
                ScheduleLagSamples++;
                if (lag > ScheduleLagWorst) ScheduleLagWorst = lag;
            }

            bool moving = (flatTarget - current).sqrMagnitude > 0.04f;
            // A REACTION HALTS THE WALK for its second or two — the activity
            // layer only plays on a still body, so without this a flinch on
            // somebody mid-stride would simply never appear (rule 6 at the
            // scale of one clip). The stagger above still displaces them: a
            // shove pushes you WHILE you flinch, which is the right order.
            if (Time.time < _reactionUntil) moving = false;
            if (moving)
            {
                var waypoint = Steer(current, flatTarget);
                var next = Vector3.MoveTowards(current, waypoint, moveAt * Time.deltaTime);
                next = StepApart(next);
                transform.position = next;
                var dir = waypoint - current; dir.y = 0;
                if (dir.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), 8f * Time.deltaTime);
            }
            else
            {
                // STANDING STILL IS WHEN PEOPLE BUNCH UP, and the first version
                // of the separation could not see that case at all.
                //
                // `StepApart` sat inside the `moving` branch, so it only ever
                // applied to walkers on their way somewhere. The reading says
                // exactly that: `crowdGapMedian` rose from 0.00 to 0.20, which
                // is the moving crowd coming apart, while `crowdTightest`
                // stayed at 0.00 and 284 pairs were still inside one another.
                // A median that moves and a worst case that does not is the
                // signature of a fix applied on the wrong path.
                //
                // And it is the wrong path in the specific way that matters:
                // people interpenetrate when they STOP. A confab is two people
                // standing to talk, a queue is people standing, and the day-5
                // noon still is eight figures bunched at a corner, none of them
                // going anywhere. The one branch that skipped the nudge is the
                // one where the whole crowd ends up.
                //
                // IT CANNOT BREAK A CONFAB. The nudge stops at 0.45m, a body's
                // width, and people talk at up to 3m — so a pair pushed out of
                // interpenetration is still comfortably inside talking range.
                // `confabs` is the number that would say otherwise.
                var apart = StepApart(current);
                if ((apart - current).sqrMagnitude > 1e-8f) transform.position = apart;
            }

            // PEOPLE DO NOT STAND INSIDE EACH OTHER, and until now they did.
            //
            // MEASURED FIRST: `crowdGapMedian=0.00` over 2087 sampled frames,
            // with 780 of the 820 possible pairs among 41 visible people closer
            // than a body width and a tightest gap of exactly zero. Not a peak
            // artefact — the MEDIAN says two people at the same point is the
            // normal state of this street. The night stills have shown it as a
            // stack of figures for as long as there have been night stills, and
            // every gate on those frames was green because they all ask what a
            // system ADDED.
            //
            // A grep found the cause rather than a guess about it: `NpcWalker`
            // had no separation, no avoidance and no personal space at all.
            //
            // A NUDGE, NOT A COLLISION. Two things this deliberately is not:
            //
            //   - it is not a physics solve. One pass, no iteration, no
            //     resolution guarantee. A crowd that guarantees clearance is a
            //     crowd that cannot huddle, and the confabs — two people
            //     standing close enough to talk — are the thing this game is
            //     about. Overlap gets rarer, not impossible.
            //   - it is not applied to the target. Steering away from a
            //     neighbour would make people walk around each other on
            //     approach, which is a different and much bigger feature; this
            //     only stops the last few centimetres of interpenetration.
            //
            // HALF THE OVERLAP EACH, because the neighbour is running the same
            // code on the same frame and will push back the other way. Pushing
            // the whole distance would double-correct and make pairs jitter
            // apart — the classic symptom of a separation step that forgot it
            // was symmetric.
            //
            // 0.45m IS A BODY, NOT A NUMBER I PICKED. `bodiesOk` measures these
            // figures at 1.58m to 1.91m tall; a person that tall is about 0.45m
            // across the shoulders, so two centres closer than that are inside
            // one another by construction.
            /// Where THIS person stands when the schedule says "the market
            /// corner". A fixed offset on a ring, from the name, so it is the
            /// same every run and every reload.
            Vector3 Spread(Vector3 place) => place + SpreadOffset;

            Vector3 StepApart(Vector3 at)
            {
                // TIMED, BECAUSE I ALREADY GUESSED WRONG ABOUT THIS ONCE.
                //
                // Removing the square root from this sweep was committed as
                // "why the street is empty" and `npcs` did not move: 9.36 ->
                // 8.43 -> 8.63, while `crowdApartPairs` proved the rejection
                // was dropping 99.8% of pairs before the arithmetic. So the
                // separation is either not the cost, or the cost is the
                // ITERATION rather than the work inside it, and no number
                // anywhere can currently tell those apart.
                //
                // A spatial bucket is the obvious next move and it is a real
                // piece of work. Writing it before knowing whether this loop
                // is 1ms of the 8.63 or 6ms of it would be making the same
                // mistake a second time, one build later.
                //
                // NOT IN THE BUDGET SUM. `attributed` adds a fixed whitelist
                // of scope names and "apart" is not on it, so this nests
                // inside `npcs` as a diagnostic without double-counting the
                // gate. `Perf.Scope` is a struct over two Stopwatch reads, so
                // 63k calls cost a few milliseconds across a ten-minute run.
                using var _apart = Perf.Time("apart");
                var push = Vector3.zero;
                foreach (var other in Live)
                {
                    if (other == null || other == this) continue;
                    var d = other.transform.position - at;
                    d.y = 0;
                    // REJECTED ON AN AXIS, THEN ON THE SQUARE, AND ONLY THEN
                    // MEASURED. This took `d.magnitude` — a square root — for
                    // EVERY other walker in the city before comparing it, and
                    // it runs per walker per frame, so it is O(n^2) square
                    // roots: about three thousand a frame at 55 walkers, of
                    // which a handful are ever within touching distance.
                    //
                    // That is not a micro-optimisation here, it is the reason
                    // the street cannot be busier. `npcs` is the largest game
                    // cost (9.36ms of a 12ms budget) and this term grows with
                    // the SQUARE of the crowd, so doubling the walkers to fill
                    // an empty street quadruples it while everything else
                    // about adding a person is linear.
                    //
                    // BEHAVIOUR IS UNCHANGED BY CONSTRUCTION, which is the
                    // point — no threshold is introduced and none needs
                    // measuring. |dx| >= BodyWidth implies dist >= BodyWidth,
                    // and so does dx*dx + dz*dz >= BodyWidth^2, so both
                    // rejects drop exactly the pairs the old comparison
                    // dropped; the survivors take the same square root and the
                    // same push as before.
                    if (d.x >= BodyWidth || d.x <= -BodyWidth
                        || d.z >= BodyWidth || d.z <= -BodyWidth) continue;
                    float sq = d.x * d.x + d.z * d.z;
                    if (sq >= BodyWidth * BodyWidth) continue;
                    ApartPairs++;
                    float dist = Mathf.Sqrt(sq);
                    // EXACTLY COINCIDENT NEEDS A DIRECTION FROM SOMEWHERE, and
                    // `d/0` is not one. Two walkers spawned on the same metre is
                    // not hypothetical — `crowdTightest=0.00` says it happened —
                    // so they get a deterministic sideways shove derived from
                    // their identity rather than a random one, which would make
                    // the crowd shimmer.
                    // ...AND IT HAS TO BE ANTISYMMETRIC, OR THEY WALK OFF
                    // TOGETHER. This derived the escape direction from the
                    // walker's OWN instance id, so two people standing on the
                    // same point each picked a direction independently — and
                    // nothing stopped those being the same direction. Two
                    // walkers travelling identically stay exactly coincident
                    // for ever, which is why `crowdTightest` read 0.00 through
                    // three builds while `crowdGapMedian` climbed 0.00 -> 0.20
                    // -> 0.29 -> 0.33 around it. The median moving while the
                    // worst case does not, twice over, from two different
                    // causes.
                    //
                    // The direction now comes from the PAIR and the sign from
                    // which id is lower, so A gets exactly the opposite of
                    // what B gets. Still deterministic, so no shimmer.
                    //
                    // The angle is also bounded now. `Mathf.Cos(GetInstanceID())`
                    // takes the cosine of a large int: the float carries almost
                    // none of that argument, so the "spread" of directions it
                    // produced was never as varied as it looks.
                    Vector3 away;
                    if (dist > 0.001f) away = d / dist;
                    else
                    {
                        int mine = GetInstanceID(), theirs = other.GetInstanceID();
                        float ang = ((mine ^ theirs) & 1023) * (Mathf.PI * 2f / 1024f);
                        float sign = mine < theirs ? 1f : -1f;
                        away = new Vector3(Mathf.Cos(ang) * sign, 0, Mathf.Sin(ang) * sign);
                    }
                    push -= away * (BodyWidth - dist) * 0.5f;
                }
                ApartCalls++;
                // A NUDGE HAS TO STAY A NUDGE, AND IN A PILE THIS ONE STOPPED
                // BEING ONE.
                //
                // The sum is over EVERY neighbour inside a body width with no
                // bound on the total. Two people overlapping give at most
                // 0.225m, which is the nudge this function's comment describes
                // and defends. Thirty people in a knot — which the day-2 noon
                // still shows and `crowdHuddleWorst=41` measures — can sum to
                // several metres in a single frame, and the one place that
                // happens is the one place it must not: a dense huddle, where
                // it reads as a body flicking across the street rather than
                // easing out of a crowd.
                //
                // Capped at half a body width per frame. That is still four
                // times what a resolved pair needs, so nothing about the
                // ordinary two-person case changes — checked against the
                // arithmetic above rather than assumed — and the pile now
                // relaxes over several frames instead of exploding in one.
                //
                // `crowdApartCapped` says how often the cap bit. If it is zero
                // the pile was never the problem and this comment is wrong;
                // that is the point of counting it rather than asserting it.
                // The last build shipped a screen-space bubble pass whose own
                // "did it fire" counter read 2, and without that counter I
                // would have credited it with a change it did not make.
                float far = push.magnitude;
                if (far > MaxApartStep)
                {
                    push *= MaxApartStep / far;
                    ApartCapped++;
                    if (far > ApartWorst) ApartWorst = far;
                }
                return at + push;
            }

            // GAZE. How far off somebody picks you out is how much they have
            // heard — and standing still to look at you is the cheapest, most
            // legible signal in the game.
            // Just been walked into? Then they are looking at you, whatever
            // their stance would otherwise have them do. Nobody ignores being
            // shoved, and a stance ladder that let them is a ladder the
            // player would immediately catch out.
            // WITH THE HEAD, NOT THE FEET, now that there is a head.
            //
            // Every version of this until now turned the whole body to face
            // you, because a capsule has no other way to look at anything.
            // That reads as squaring up: it is the posture of somebody about
            // to start something, applied to a stranger who has merely
            // clocked you. In a game whose antagonist is gossip that is
            // precisely the wrong signal — being NOTICED and being CONFRONTED
            // are different rungs of the same ladder and were rendering
            // identically.
            //
            // `Rig.LookSplit` distributes the turn down chest, neck and head,
            // and `MustTurnBody` decides when somebody has to come round
            // because their neck cannot get there. So the body turns when a
            // person would actually turn, and otherwise they just look.
            bool wantsToLook = false;
            if (_player != null && Time.time < _staredUntil) wantsToLook = true;
            else if (_player != null && !moving)
            {
                float gaze = (float)StreetVoice.GazeMetres(Stance);
                var toYou = _player.position - current; toYou.y = 0;
                wantsToLook = gaze > 0.5f && toYou.sqrMagnitude > 0.04f
                              && toYou.magnitude <= gaze;
            }

            // PERCEPTION, and it is deliberately OR-ed with the stance gaze
            // above rather than replacing it. The stance ladder answers "how
            // does this person feel about you", which is a social question and
            // still the right one; this answers "can they physically see you
            // from there, in this light, at this hour", which nothing in the
            // project has ever asked. A man under a lamp is looked at from
            // across the street and the same man in a doorway is not.
            if (_player != null && TickPerception(current)) wantsToLook = true;

            if (_body != null) _body.LookAt = wantsToLook ? _player : null;

            // The body still comes round for the two cases where a person
            // would: when their neck has run out, and when they are staring
            // at you rather than glancing.
            if (wantsToLook && (_body == null || _body.MustTurn
                                || Time.time < _staredUntil))
            {
                var at = _player.position - transform.position; at.y = 0;
                if (at.sqrMagnitude > 0.01f)
                    transform.rotation = Quaternion.Slerp(transform.rotation,
                        Quaternion.LookRotation(at),
                        (Time.time < _staredUntil ? 9f : 3.5f) * Time.deltaTime);
            }

            // A NAME IS NOT A NAMEPLATE. Every walker used to carry its name in
            // white, at full size, at every distance — which is why a street of
            // a dozen people read as a wall of text (playtest 2026-07-28). A
            // name now behaves like recognition does: it resolves as you get
            // close enough to speak to somebody, and it is not there at all
            // across the road.
            if (_label != null && Camera.main != null)
            {
                var cam = Camera.main.transform.position;
                float d = Vector3.Distance(transform.position, cam);
                float alpha = Mathf.Clamp01((LabelFadeOut - d) / (LabelFadeOut - LabelFullAt));
                if (alpha <= 0.01f)
                {
                    if (_label.gameObject.activeSelf) _label.gameObject.SetActive(false);
                }
                else
                {
                    if (!_label.gameObject.activeSelf) _label.gameObject.SetActive(true);
                    var c = _label.color; c.a = alpha; _label.color = c;
                    // YAW ONLY, and the paragraph explaining why moved to
                    // `Billboard` along with the maths — it was written twice,
                    // here and in `SpeechBubble`, and only one copy ever got the
                    // fix. One implementation now, and the shot path calls the
                    // same one so a committed frame cannot be drawn with a
                    // stale aim.
                    Billboard.Aim(_label.transform, Camera.main);
                    NameTags.Offer(_label, d);
                    // COUNTED WHERE IT IS SWITCHED ON, not where it is offered.
                    // A label the declutter never sees is still a label on the
                    // screen, and the whole reason the frame and the counters
                    // disagreed is that only the offered ones were counted.
                    NameTags.NoteActive(_label.transform);
                }
            }

            // Last, and after every branch above that can move them: the
            // stagger, the avoid step and the walk are all displacement this
            // frame, and a gait measured before any of them is a gait that
            // disagrees with where the body went.
            DriveBody();
        }

        /// Street-wise steering. Walk straight when the line is clear of
        /// buildings; otherwise get to the nearest STREET and follow it.
        ///
        /// This used to fall back to "the nearest point on the founding cross",
        /// which was true when the city had two roads and became nonsense the
        /// moment it had forty. It now uses the real network, so people walk
        /// down streets to get places instead of cutting diagonally across the
        /// blocks between them — which is most of what makes a crowd read as a
        /// crowd rather than as particles.
        ///
        /// Stateless and re-evaluated every tick, so a schedule change mid-walk
        /// just bends the route, and the accelerated CI sim stays deterministic.
        /// AN INTERMEDIATE WAYPOINT IS A SHARED AIM POINT, AND THAT IS THE MOB.
        ///
        /// `a050815`: `huddleStanding=0 huddleMoving=41` — every body in the
        /// worst huddle was in transit and not one was standing at its place,
        /// with `huddleCells=22`, so forty-one people bound for twenty-two
        /// different destinations were inside two metres of each other. Two
        /// builds were spent widening `SpreadRadius`, which spreads people
        /// around a DESTINATION and can do nothing about that.
        ///
        /// This function is why. Three of its four returns are a single point
        /// that many walkers share — the same junction node, the same nearest
        /// street point — and `Spread` is applied to the destination only, so
        /// everybody funnelling through a junction aims at its exact
        /// coordinates. `huddleWhere` has read -1/-1, -1/-3, -1/-5, 1/1 and
        /// 2/2 across runs: a few metres from the origin every time, which is
        /// what a shared node looks like when it is plotted.
        ///
        /// So the per-person offset that already exists for standing at a
        /// place is applied to the waypoint too. It is deterministic from the
        /// name, so nobody shimmers and everybody takes the same line every
        /// run; it is the same vector the destination uses, so there is no
        /// second constant to drift; and the FIRST return is left alone —
        /// a clear path to the real target must stay exact or people stop
        /// arriving, which is the regression `scheduleLag` exists to catch.
        ///
        /// `steerVia` counts which branch each walker took. Without it the
        /// claim above is a guess about a four-way if, and the last two guesses
        /// about this mob were both wrong.
        Vector3 Steer(Vector3 cur, Vector3 target)
        {
            // A ROAD IS NOT AN OBSTACLE, WHICH IS WHY EVERYONE WAS IN IT.
            //
            // This branch asks only whether anything SOLID stands between
            // here and there, and tarmac does not, so any walker with line
            // of sight to its destination walked straight at it — across
            // the carriageway, and diagonally ALONG it whenever the
            // destination sat up the street. `steerDirect` is the biggest
            // branch in the tally by far, the pavement logic below it only
            // ever ran when something was in the way, and the day-2 noon
            // still shows the result: thirteen people in convoy down the
            // middle of the road, `headingIntoRoad=13`, `huddleMoving=13`
            // with nobody talking or standing. Not a gathering — a shared
            // desire line nothing was pulling off the tarmac.
            //
            // People DO cross roads, so the test is not "any road". It is
            // how far the line RUNS ON one: a perpendicular crossing of
            // the widest street here is 8m of tarmac (avenue width, from
            // StreetMap), and anything much past that is walking along the
            // carriageway rather than over it. 12m allows the widest
            // crossing with margin and refuses the diagonal.
            //
            // Refusal falls through to the pavement branches below, which
            // already know how to route — this adds no new path, it just
            // stops the shortcut from pre-empting them. Counted, because a
            // guard that never fires and a guard that fixed the street
            // read identically from the still alone.
            if (WorldBuilder.SegmentClear(cur, target) && !RunsAlongRoad(cur, target))
            { SteerDirect++; return target; }

            // BOUNDED BY THE PAVEMENT, NOT BY `SpreadOffset`'S OWN SIZE.
            //
            // The destination ring runs from 0.8m to about 1.6m, sized for how
            // many people are standing at a place. A waypoint is not a place:
            // `NearestStreetPoint` puts walkers `edge.Width/2 + 1.1` from the
            // road centre, so there is roughly 1.1m of footway around the point
            // being aimed at, and a 1.6m sideways shove would put somebody in
            // the carriageway or through a shopfront. Half that band cannot
            // reach either, which is where 0.55 comes from — the same number
            // `NearestStreetPoint` already uses, halved, rather than a new one.
            var lane = SpreadOffset;
            float wide = lane.magnitude;
            if (wide > LaneMetres) lane *= LaneMetres / wide;

            // Aim for the street outside the destination first.
            var targetStreet = NearestStreetPoint(target);
            if (WorldBuilder.SegmentClear(cur, targetStreet))
            { SteerTargetStreet++; return targetStreet + lane; }

            // Otherwise get onto our own street and follow it round.
            var myStreet = NearestStreetPoint(cur);
            if ((myStreet - cur).sqrMagnitude > 0.04f && WorldBuilder.SegmentClear(cur, myStreet))
            { SteerOwnStreet++; return myStreet + lane; }

            // Last resort: the nearest junction, which is always on tarmac and
            // always connected to everywhere else.
            var j = Ledger.Core.StreetMap.NearestNode(cur.x, cur.z, junctionsOnly: true);
            if (j == null) { SteerOrigin++; return new Vector3(0, cur.y, 0) + lane; }
            SteerJunction++;
            return new Vector3((float)j.X, cur.y, (float)j.Z) + lane;
        }

        /// How much of a straight walk lies on tarmac, against the bound a
        /// legitimate crossing needs. Sampled at half-metre steps: finer
        /// buys nothing against an 8m street and this runs per walker per
        /// steer.
        ///
        /// `SteerDirectOnRoad` counts the refusals. A zero there means the
        /// direct branch was never the reason people were in the road and
        /// this whole change is wrong — which is the point of counting it
        /// rather than asserting it.
        public static int SteerDirectOnRoad;
        const float RoadRunMetres = 12f;

        static bool RunsAlongRoad(Vector3 a, Vector3 b)
        {
            var d = b - a; d.y = 0;
            float len = d.magnitude;
            if (len < RoadRunMetres) return false;
            d /= len;
            float onRoad = 0f;
            for (float t = 0f; t <= len; t += 0.5f)
            {
                var p = a + d * t;
                if (Ledger.Core.StreetMap.OnRoad(p.x, p.z))
                {
                    onRoad += 0.5f;
                    if (onRoad > RoadRunMetres) { SteerDirectOnRoad++; return true; }
                }
            }
            return false;
        }

        /// Closest point on any street, pulled a little toward the pavement so
        /// people walk beside the traffic rather than down the middle of it.
        static Vector3 NearestStreetPoint(Vector3 p)
        {
            if (!Ledger.Core.StreetMap.NearestOnStreet(p.x, p.z, out var sx, out var sz, out var edge))
                return p;
            var onRoad = new Vector3((float)sx, p.y, (float)sz);
            var toWalker = new Vector3(p.x - onRoad.x, 0, p.z - onRoad.z);
            float pavement = (float)edge.Width / 2f + 1.1f;
            return toWalker.sqrMagnitude < 0.01f
                ? onRoad
                : onRoad + toWalker.normalized * pavement;
        }
    }
}
