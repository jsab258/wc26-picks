using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// TWO NAMES IN THE SAME PLACE ARE WORSE THAN ONE NAME — and the street
    /// never had 185 such pairs, which took until 4 August to establish.
    ///
    /// THE NUMBER IN THIS SENTENCE WAS NEVER ABOUT NAMEPLATES. It came from
    /// `collidingNames`, which counted every `TextMesh` in the scene: street
    /// plates, shop fascias, stop signs, speech bubbles. Split by what this
    /// class actually manages, the same run reads `collidingNames=0` and
    /// `collidingWorldText=155`. Every one of those overlaps was furniture, and
    /// furniture clustering at a junction is a junction.
    ///
    /// The declutter below is still right and still worth having — six people
    /// inside talking range really do produce six labels wanting one patch of
    /// screen. What was wrong was the evidence, and it stayed wrong for as long
    /// as it sat at the top of this file being quoted.
    ///
    /// The distance rule was already right — a name resolves as you get close
    /// enough to speak to somebody and is not there across the road — and it is
    /// not sufficient. Six people standing at a junction are all inside talking
    /// range, so six names arrive at once, overlap, and none of them can be
    /// read. Recognition does not work like that: you pick out the person you
    /// are looking at, not the crowd behind them.
    ///
    /// So the nearest label wins its patch of screen and anything farther that
    /// collides with it stands down. That is a real declutter rather than a cap
    /// on the count — a cap would hide the sixth person on an empty street,
    /// where there was nothing wrong with showing them.
    ///
    /// AND IT MAKES A MEASUREMENT GATEABLE — BUT NOT THE ONE THIS COMMENT
    /// ORIGINALLY NAMED. It said `collidingNames` had been printed for three
    /// builds and gated on nothing, and that a working declutter finally made
    /// zero reachable there. Wrong: `collidingNames` counts every `TextMesh` in
    /// the scene, and the scene is full of street plates, stop signs and lane
    /// signs on posts that cluster at junctions by design. The build settled it
    /// at `collidingNames=144 nameTagsOffered=1` — a hundred and forty-four
    /// overlaps among text this class never touches, and one nameplate to
    /// place. Zero was never reachable there and never should have been.
    ///
    /// What became gateable is `WorstUnplaced`, below: the labels this class
    /// owns, after it has finished with them. `collidingNames` stays printed
    /// and ungated, because a jump in it means the street furniture moved and
    /// that is worth seeing without being a legibility failure.
    public static class NameTags
    {
        struct Candidate
        {
            public TextMesh Label;
            public float Distance;
            /// How many times this label was offered in the frame this
            /// candidate belongs to. One is the healthy value.
            public int Times;
        }

        static readonly List<Candidate> _offered = new List<Candidate>();
        static readonly HashSet<TextMesh> _managed = new HashSet<TextMesh>();
        /// Reused rather than allocated per frame — this runs inside the frame
        /// budget the `frame` gate is red against.
        static readonly HashSet<TextMesh> _distinct = new HashSet<TextMesh>();
        /// The same set counted a way Unity's equality cannot reach. See the
        /// note in `Resolve`: this exists to test the container, not the data.
        static readonly HashSet<int> _distinctIds = new HashSet<int>();
        static int _frame = -1;

        /// How many labels stood down on the last resolved frame, and how many
        /// were offered. Printed so a declutter that quietly stopped running
        /// looks different from a street with nothing to declutter.
        public static int Suppressed { get; private set; }
        /// PEAK OVER THE RUN, not the reading on the last frame.
        ///
        /// This was instantaneous, and it produced a straight contradiction:
        /// `nameTagsOffered=2` printed beside a night still with a dozen names
        /// in it. Neither was wrong — the counter described the final frame and
        /// the picture described a different one — but a number that answers
        /// "how many right now" while sitting on a done line that everything
        /// else reads as "how bad did it get" is a number that will be misread
        /// every time, and I misread it within a minute of printing it.
        ///
        /// `WorstUnplaced` next door is already a maximum, for exactly this
        /// reason and with a comment saying so. Two counters about the same
        /// system disagreeing on what a run-level number means is the drift
        /// worth removing.
        public static int Offered { get; private set; }

        /// `OfferedPeak` WAS DELETED THIS AFTERNOON AND IS RESTORED, BECAUSE
        /// IT WAS NEVER WRONG.
        ///
        /// It read 42 where a probe built to describe one frame read 13, and I
        /// called that arithmetically impossible four times, published four
        /// explanations, and finally deleted the counter under the standing
        /// rule that a measurement contradicting itself twice gets deleted
        /// rather than explained.
        ///
        /// The rule is right and it was applied to the wrong thing. The two
        /// numbers were printed on DIFFERENT LOG LINES: this one on the done
        /// line at the end of the run, the probe on the `glyphs` line which is
        /// emitted on every screenshot. Same counter, two moments, and the
        /// peaks kept climbing after the last shot. Nothing contradicted
        /// anything.
        ///
        /// The rule this project already carries — a peak's denominator must
        /// come from the SAME INSTANT as its numerator — turns out to govern
        /// which LOG LINE a number is printed on, not only which frame it is
        /// sampled from. Five sites had been fixed for the frame version of
        /// that fault and none of us noticed the line version.
        ///
        /// The whole family is on the done line now.
        public static int OfferedPeak { get; private set; }

        /// PEAKS, FOR THE SAME REASON `Offered` NEEDED ONE — third instance of
        /// this drift in one file, and I wrote the rule about it an hour before
        /// finding this one.
        ///
        /// `Suppressed` is reset at the top of every `Resolve`, so
        /// `nameTagsHidden=0` means "nothing was hidden on whichever frame
        /// swept last", not "nothing is ever hidden". Printed beside a peak it
        /// reads as the declutter doing nothing, which may well be true and
        /// which this cannot currently tell you.
        ///
        /// `Unresolved` is the outcome that had no name at all: a label whose
        /// screen rect could not be computed is skipped by the placement loop
        /// and stays visible, counted by neither side.
        public static int SuppressedPeak { get; private set; }
        public static int Unresolved { get; private set; }
        public static int UnresolvedPeak { get; private set; }

        /// Labels the camera could not see, this pass and at worst. Kept apart
        /// from `Unresolved` because they are the opposite finding: nothing is
        /// wrong, there is simply nothing on screen to place. Printed rather
        /// than dropped so the two can be told apart next time — the whole
        /// reason `Unresolved` was ambiguous is that it silently held both.
        public static int OffScreenNow { get; private set; }
        public static int OffScreenPeak { get; private set; }

        /// Every rect request anywhere that fell outside the viewport. A
        /// lifetime total, alongside `TooNear` and `RectCalls`.
        public static int OffScreen { get; private set; }

        /// Pairs of STILL-VISIBLE managed labels that overlap once the pass has
        /// finished — the postcondition, not the workload.
        ///
        /// THE GATE HAS TO MEASURE WHAT THE DECLUTTER CONTROLS. The first
        /// version gated on `collidingNames`, which counts every `TextMesh` in
        /// the scene — and the scene is full of street furniture: name plates,
        /// stop signs, lane signs, neon words, all on posts that legitimately
        /// cluster at a junction. The build came back `collidingNames=144
        /// nameTagsOffered=1`: a hundred and forty-four overlaps among text this
        /// class never sees, and one nameplate to declutter. The gate was
        /// unsatisfiable and it was measuring somebody else's population.
        ///
        /// AND THEN THE FIX WAS WRONG TWICE MORE, both worth writing down
        /// because they are the failure modes this repo keeps producing:
        ///
        ///   - the replacement incremented this counter in the same `blocked`
        ///     branch as `Suppressed`, so it was that number with a second name
        ///     while its comment claimed it was what remained AFTERWARDS. Every
        ///     one of those collisions was then successfully hidden — they are
        ///     the declutter WORKING, and gating on zero of them would have
        ///     demanded an empty street.
        ///   - the gate clause became `Suppressed >= 0`, which is true of any
        ///     int that only counts up. Swapping an unsatisfiable gate for a
        ///     vacuous one is moving the bound to make red go away.
        ///
        /// So this is computed as a genuine postcondition: after the pass, take
        /// the labels still showing and ask whether any two of them are in the
        /// same place. Zero by construction — which is the point. A gate on a
        /// constructed invariant costs nothing while the construction holds and
        /// fires the moment somebody changes the resolver to nudge instead of
        /// hide, or reorders it so a rect is compared before it is final.
        public static int UnplacedNow { get; private set; }

        /// The worst that got past the resolver on ANY frame of the run, and
        /// how many frames actually resolved something.
        ///
        /// MAXIMUM, BECAUSE OF THE QUESTION IT ANSWERS. The sim reads these once
        /// at the end of a day; `UnplacedNow` at that instant describes one
        /// frame out of thousands and a collision two seconds earlier would be
        /// invisible. "Did this ever fail" is answered by the maximum — the same
        /// reasoning that made the maximum WRONG for the AO ceiling, where the
        /// question was "is the pass everywhere" and a maximum maximised the
        /// very quantity the bound existed to keep small. Same statistic, and it
        /// is right here for precisely the reason it was wrong there.
        ///
        /// `ResolvedFrames` is the other half and it is a count, not a maximum,
        /// because it answers "did this run at all" — without it, a declutter
        /// that never executed reports a perfect zero and gates green.
        public static int WorstUnplaced { get; private set; }
        public static int ResolvedFrames { get; private set; }

        /// The tallest a SHOWING nameplate has been over the run, as a fraction
        /// of screen height. Worst-over-run rather than a sample, for the reason
        /// the first version of this measurement failed: it read 0.036 while the
        /// still that prompted it showed a name spanning a third of the frame.
        /// Both were true — the sample happened at a moment with no label near.
        public static float WorstNameFrac { get; private set; }

        /// AND THE MIDDLE OF IT, BECAUSE A PEAK CANNOT DESCRIBE A STREET.
        ///
        /// `worstNameFrac=0.306` with `worstNameCentreMetres=1.21` and
        /// `worstNameBoundsY=0.29` is the projection working: a label genuinely
        /// 1.2 metres from the camera IS a third of the screen tall, and the
        /// arithmetic checks out at this camera's field of view. So the peak is
        /// honest and it answers "did a name ever fill the frame", which is not
        /// the question the night still poses. That question is "is this how
        /// the street looks", and only a distribution can answer it.
        ///
        /// NO THRESHOLD YET, DELIBERATELY. Rule 2: make the system report the
        /// value, run it, look, then bound it. A clamp picked now would be a
        /// number invented to make a picture I disliked go away, and this
        /// project has a table of those.
        ///
        /// Every SHOWING label contributes one sample per resolve, so this is a
        /// statistic over label-instants rather than over frames — a frame with
        /// twelve names counts twelve times, which is right, because the
        /// question is what a name typically looks like and not what a frame
        /// typically contains.
        public static double NameFracMedian { get; private set; }
        public static int NameFracSamples => _nameFracs.Count;
        static readonly List<float> _nameFracs = new List<float>();

        /// THE WIDTH FAMILY, and it exists because a still disagreed with every
        /// number in this file at once.
        ///
        /// `WorstNameWidthText` carries the NAME, not just the number, because
        /// the width of a label is mostly a fact about its text — and "the
        /// widest label was 0.34 of the screen" sends you looking at the
        /// projection while "the widest label was 0.34 of the screen and it
        /// said Katarina" sends you at the right thing in one reading.
        public static double NameWidthMedian { get; private set; }
        public static double NameWidthP90 { get; private set; }
        public static float WorstNameWidthFrac { get; private set; }
        public static string WorstNameWidthText { get; private set; } = "none";
        public static int NameWidthSamples => _nameWidths.Count;
        static readonly List<float> _nameWidths = new List<float>();
        /// The same widths AFTER the cap — what the player actually sees.
        /// Kept apart from the pre-cap series because 0.610 shrinking to 0.12
        /// is the system working and 0.610 staying put is a label the cap never
        /// reached, and one list cannot say which happened.
        static readonly List<float> _nameShownWidths = new List<float>();
        public static double NameShownWidthMedian { get; private set; }
        public static double NameShownWidthP90 { get; private set; }

        /// The same for a bubble, and it is the SHARPER half of the still.
        ///
        /// `review_day1_night.jpg` has overheard speech running edge to edge
        /// across the right of the frame, plainly larger than any nameplate in
        /// it, and nothing in this codebase has ever measured how big a bubble
        /// gets. `textVisible=144` counts them and `textFacingAway=70` says
        /// which way they point; neither can see a size.
        public static float WorstBubbleFrac { get; private set; }
        public static float WorstBubbleMetres { get; private set; }
        public static double BubbleFracMedian { get; private set; }
        public static int BubbleFracSamples => _bubbleFracs.Count;
        static readonly List<float> _bubbleFracs = new List<float>();

        /// Called by `SpeechBubble.Rects` for each bubble it has already
        /// projected. It takes the RECT rather than the renderer on purpose:
        /// that method walks the live bubbles and computes the screen rect every
        /// tick anyway, so projecting a second time here would be a second
        /// implementation of one idea — the shape of fault this project keeps
        /// finding in pairs, and the cheapest place to not create one is before
        /// it exists.
        public static void NoteBubbleRect(Camera cam, Rect rect, Vector3 centre)
        {
            if (cam == null) return;
            float frac = rect.height / Mathf.Max(1f, cam.pixelHeight);
            _bubbleFracs.Add(frac);
            if (frac > WorstBubbleFrac)
            {
                WorstBubbleFrac = frac;
                WorstBubbleMetres = Vector3.Distance(cam.transform.position, centre);
            }
        }

        /// AND THE TAIL, WHICH IS THE ONE THING THE MEDIAN STRUCTURALLY CANNOT
        /// SHOW — and on this metric the tail is the entire finding.
        ///
        /// First reading: `bubbleFracMedian=0.041` over 1,325 samples and
        /// `worstBubbleFrac=1.900` at 1.98 metres. A typical bubble is four per
        /// cent of the screen and is fine; one of them was NEARLY TWICE THE
        /// SCREEN TALL. Read either number alone and you get a different game.
        ///
        /// A ninth decile is what separates "one freak frame" from "a fifth of
        /// the speech in this game is unreadable", and those want completely
        /// different fixes — the first is a clamp on a corner case, the second
        /// is the bubble being sized wrong. No bound goes on this until that
        /// number lands, which is rule 2 and is why there is no clamp in this
        /// commit.
        public static double NameFracP90 { get; private set; }
        public static double BubbleFracP90 { get; private set; }

        /// The middle value of a list, by the same rule everywhere: with an even
        /// count take the lower of the two middles rather than their mean, so
        /// the answer is always a value the system actually produced.
        static double MedianOf(List<float> xs) => QuantileOf(xs, 0.5);

        /// Nearest-rank, so the answer is always a value that was measured
        /// rather than an interpolation between two that were not.
        static double QuantileOf(List<float> xs, double q)
        {
            if (xs.Count == 0) return -1;
            var copy = new List<float>(xs);
            copy.Sort();
            int i = (int)System.Math.Ceiling(q * copy.Count) - 1;
            if (i < 0) i = 0;
            if (i >= copy.Count) i = copy.Count - 1;
            return copy[i];
        }

        /// Folded once, at the end of the run, because sorting thousands of
        /// samples every resolve would show up in `frameWorstMs` and the
        /// medians are only ever read from the done-line.
        public static void CloseTextStats()
        {
            // HOW MANY OF THE "MANAGED" LABELS NO LONGER EXIST.
            //
            // `_managed` is never pruned and `PopulationHost` destroys crowd
            // walkers all run, so this set holds a dead reference for every
            // label that has ever left the street. Counting them is a
            // MEASUREMENT and not a repair on purpose: pruning would change
            // what `ManagedEver` means in the same build that is finally
            // testing what it means, and this metric has already produced three
            // wrong answers from readings taken at cross purposes.
            //
            // Unity's `==` is true for a destroyed object, which is what makes
            // this countable at all.
            ManagedDead = 0;
            foreach (var l in _managed) if (l == null) ManagedDead++;

            NameFracMedian = MedianOf(_nameFracs);
            NameWidthMedian = MedianOf(_nameWidths);
            NameShownWidthMedian = MedianOf(_nameShownWidths);
            BubbleFracMedian = MedianOf(_bubbleFracs);
            NameFracP90 = QuantileOf(_nameFracs, 0.90);
            NameWidthP90 = QuantileOf(_nameWidths, 0.90);
            NameShownWidthP90 = QuantileOf(_nameShownWidths, 0.90);
            BubbleFracP90 = QuantileOf(_bubbleFracs, 0.90);
        }

        /// Labels rejected for sitting at or inside the camera's near plane.
        /// Counted rather than silently dropped: if this is large, bodies are
        /// walking through the camera, which is a placement problem wearing a
        /// nameplate problem's clothes — and the old code answered it with a
        /// rect thousands of screens tall instead of a number.
        public static int TooNear { get; private set; }

        /// IS THE NAME STANDING UP, AND HOW MANY ARE THERE.
        ///
        /// `review_day1_night.jpg` at eea92fd is a wall of names, several of
        /// them skewed across the pavement — the exact "lying in the road"
        /// failure a comment in `NpcWalker` says was fixed by flattening the
        /// billboard direction. The comment may be right and something else may
        /// be tilting them; it may be wrong. Nothing measures it either way,
        /// which is why the frame is the only place it shows.
        ///
        /// `UpDot` is the label's own up-vector dotted with world up: 1.0 is
        /// standing, 0.0 is flat on the ground. WORST over the run, because one
        /// plate lying down is the fault and an average would hide it behind
        /// forty that are fine.
        ///
        /// `Active` is how many labels are switched on at once. The declutter
        /// reported `nameTagsOffered=2` against `labels=42`, which reads as "the
        /// street is nearly empty of names" — and the frame shows a dozen. One
        /// of those two numbers is about something other than what I think, and
        /// counting the live ones is how to find out which.
        public static double WorstUpDot { get; private set; } = 2.0;
        public static int Active { get; private set; }
        public static int ActivePeak { get; private set; }

        /// Called by each walker for every label it leaves switched on.
        public static void NoteActive(Transform label)
        {
            Active++;
            if (Active > ActivePeak) ActivePeak = Active;
            if (label == null) return;
            double up = Vector3.Dot(label.up, Vector3.up);
            if (up < WorstUpDot) WorstUpDot = up;
        }

        /// Cleared where the per-frame offer list is, so the two cannot drift
        /// into describing different frames.
        public static void ClearActive() => Active = 0;

        /// How many rects were asked for at all — the denominator `TooNear`
        /// needs and did not have. 3,739 rejections is unreadable on its own:
        /// over a two-day run with dozens of labels a frame it could be a
        /// rounding or it could be most of them, and rule 2 is that a count
        /// without its denominator is not a measurement.
        public static int RectCalls { get; private set; }

        /// How far from the camera the tallest label was, in metres.
        ///
        /// `worstNameFrac` fell from 2,119 to 4.4 when the near plane was
        /// enforced, which is a fix and not a cure — 4.4 screens tall is still
        /// absurd. The obvious next move is to guess at another bound, and
        /// guessing at bounds on this metric has already been wrong twice
        /// today. The distance says whether this is a label pressed against the
        /// camera (a placement problem) or an ordinary label whose world bounds
        /// are far larger than the glyphs (a bounds problem), and those have
        /// nothing in common but the symptom.
        public static float WorstNameMetres { get; private set; }

        /// The world-space height of the tallest label's renderer bounds, and
        /// the scale of the transform it hangs on.
        ///
        /// The distance reading settled what this is NOT. The tallest label was
        /// 5.48m away — ordinary street distance, nowhere near the camera — so
        /// it is not a placement problem, and 4,107 of 11,026 rect requests
        /// being rejected as "too near" from that distance can only mean the
        /// BOUNDS are large enough to straddle the camera plane from five
        /// metres out. One cause, both symptoms.
        ///
        /// Which leaves two candidates with different fixes: a mesh whose
        /// bounds are genuinely enormous, or an ordinary mesh on a transform
        /// with a large scale. Printing both rather than picking one, because
        /// this metric has been guessed at twice today and been wrong twice.
        public static float WorstNameBoundsY { get; private set; }
        public static float WorstNameScale { get; private set; }

        /// Distance to the bounds the rect is actually projected from, and the
        /// rect's raw height in pixels. The pair that settles it.
        public static float WorstNameCentreMetres { get; private set; }
        public static float WorstNamePixels { get; private set; }

        /// A walker offers its label each frame it wants one shown.
        ///
        /// OFFERED, NOT SHOWN. The walker has already decided the label is close
        /// enough and faded it in; this decides whether it survives contact with
        /// the labels in front of it. Splitting it that way keeps the distance
        /// rule where the person is and the screen rule where the screen is.
        public static void Offer(TextMesh label, float distance)
        {
            if (label == null) return;
            Sweep();
            Offers++;
            _managed.Add(label);

            // ONE ENTRY PER LABEL PER FRAME, AND THE MEASUREMENT SAID SO.
            //
            // `nameTagsOffered=42` against `namesDistinctPeak=7` on the same
            // frame: forty-two entries from at most seven labels. That is not
            // the declutter being busy, it is the same name arriving six times,
            // and it did real harm rather than only inflating a number — the
            // resolve loop below sorts the list, keeps the first, and then
            // finds the SECOND COPY OF THE SAME LABEL overlapping the rect it
            // just kept. Identical rect, so it always overlaps. It marks it
            // blocked and sets its alpha to zero, and because both entries are
            // the same object that zero lands on the label itself. Every
            // duplicated name hid itself, which is what `nameTagsHidden=34`
            // beside legible names in the frames has been reporting.
            //
            // NEAREST WINS, not first, because the ordering is the whole point
            // of this class: a label's distance decides who beats whom for a
            // patch of screen, and taking whichever copy happened to arrive
            // first would make that depend on iteration order again.
            //
            // THE CAUSE IS NOT FIXED HERE, AND SAYING SO MATTERS. Something
            // ticks a walker more than once per rendered frame; this makes the
            // symptom harmless and counts the repeats so the next run can name
            // it. `namesDupOffers` is the count and `namesDupWorst` is the most
            // any single label managed in one frame.
            for (int i = 0; i < _offered.Count; i++)
            {
                if (_offered[i].Label != label) continue;
                DupOffers++;
                var c = _offered[i];
                // COUNTED ON THE CANDIDATE, not in a field beside the loop. The
                // first version kept a running counter reset whenever a new
                // label arrived, which counts CONSECUTIVE repeats — so offers
                // arriving A, B, A, B would have reported a worst of one while
                // every label was being doubled. The count belongs to the
                // label, so it lives on the label's entry.
                c.Times++;
                if (c.Times > DupWorst) DupWorst = c.Times;
                if (distance < c.Distance) c.Distance = distance;
                _offered[i] = c;
                return;
            }
            _offered.Add(new Candidate { Label = label, Distance = distance, Times = 1 });
        }

        /// How often a label was offered twice in one frame, and the worst run
        /// of repeats for a single label. Both lifetime, both printed, because
        /// `namesDupOffers=0` after the dedupe would otherwise be
        /// indistinguishable from the offer path having stopped running.
        public static int DupOffers { get; private set; }
        public static int DupWorst { get; private set; }

        /// HOW MANY TIMES ANYTHING HAS OFFERED A LABEL, EVER. A plain integer
        /// with no object identity in it, which is the entire point.
        ///
        /// `ManagedEver` was supposed to be this number and cannot be trusted
        /// to be: it is the size of a `HashSet<TextMesh>`, and this counter
        /// exists because that set has now produced an arithmetic
        /// impossibility three readings running — `nameTagsOffered=42` in a
        /// single frame against `namesManagedEver=24` for the whole run, when
        /// every offer adds to the set. Three explanations have been published
        /// for that and all three were wrong, so this one is built to be
        /// unfalsifiable in the useful direction: it counts CALLS, and nothing
        /// about a destroyed object, a recycled instance id or a duplicate can
        /// touch it.
        public static int Offers { get; private set; }

        /// DISTINCT LABELS IN A SINGLE FRAME'S OFFER LIST, AT THE WORST FRAME.
        ///
        /// THE DISCRIMINATOR, and it is the only new number here that can name
        /// the fault rather than route around it. Two explanations survive
        /// reading the code:
        ///
        ///   - `_offered` collects DUPLICATES within one frame, so the peak
        ///     counts one walker twice. Then this comes back below
        ///     `OfferedPeak`, and the resolve loop has been comparing labels
        ///     against themselves, marking them blocked and setting their alpha
        ///     to zero — which would also explain `nameTagsHidden=33` beside
        ///     names still legible in the frames.
        ///
        ///   - `_managed` is failing to GROW for genuinely distinct labels.
        ///     `PopulationHost` destroys crowd walkers constantly and their
        ///     labels go with them; the set is never pruned, so it holds
        ///     hundreds of dead references, and Unity does not promise an
        ///     instance id is unique for the life of a session. Then this comes
        ///     back EQUAL to `OfferedPeak` and the lifetime set is the broken
        ///     thing.
        ///
        /// Both are reachable and they disagree, which is what the last three
        /// readings could not manage between them.
        public static int OfferedDistinctPeak { get; private set; }

        /// The worst offering frame, described by four numbers taken from IT
        /// rather than from four different frames. See the note in `Resolve`.
        public static int OfferedAtWorst { get; private set; }
        public static int AliveAtWorst { get; private set; }
        public static int DistinctObjectsAtWorst { get; private set; }
        public static int DistinctIdsAtWorst { get; private set; }

        /// Is this one of the labels this class is responsible for?
        ///
        /// WHY ANYTHING NEEDS TO ASK. `SimDirector.CollidingNames` reported 182
        /// overlapping pairs and was quoted as "the nameplate wall" — while
        /// looping over EVERY TextMesh in the scene. This city is full of
        /// street plates, shop fascias and bark bubbles, and two street plates
        /// overlapping at a junction is a junction, not a fault.
        ///
        /// It is the same misreading that made `worstTextHeightFrac=0.210`
        /// meaningless, diagnosed in this very file forty lines below and then
        /// left in place one file over. A metric whose scope is "everything"
        /// answers a question nobody asked.
        public static bool Manages(TextMesh label) =>
            label != null && _managed.Contains(label);

        /// How many distinct labels have EVER been offered. A lifetime figure
        /// beside three per-call ones, and the only one that can distinguish
        /// "the offer path never ran" from "it ran and nothing was in shot" —
        /// which is the fork `namesTracked=0` beside `nameTagsOffered=43` left
        /// open, because a peak of zero is consistent with both.
        public static int ManagedEver => _managed.Count;

        /// Entries in that set whose label has since been destroyed. The
        /// denominator `ManagedEver` never had: a set of 24 that is 20 corpses
        /// is describing four live labels, and reads identically to a set of 24
        /// live ones.
        public static int ManagedDead { get; private set; }

        /// Resolve the previous frame's offers once, at the start of the next.
        ///
        /// DEFERRED BY A FRAME ON PURPOSE. Walkers update in an order nobody
        /// controls, so resolving as they arrive would let the first one win by
        /// being first rather than by being nearest. Waiting until the set is
        /// complete costs one frame of latency on a label appearing, which is
        /// invisible, and buys a decision that does not depend on iteration
        /// order — the same reasoning as `CharacterRig.SolvedLastFrame`.
        static void Sweep()
        {
            if (Time.frameCount == _frame) return;
            _frame = Time.frameCount;
            Resolve();
            _offered.Clear();
            // The live count is per FRAME, like the offer list, and cleared in
            // the same place so the two can never describe different frames —
            // which is exactly how `nameTagsOffered=2` came to sit beside a
            // screenshot with a dozen names in it without anybody noticing.
            ClearActive();
        }

        /// A NAME STOPS GROWING ONCE IT IS BIG ENOUGH TO READ.
        ///
        /// THE FAULT, AND IT IS THE ONE THE NIGHT STILLS KEPT SHOWING. World
        /// text is a fixed size in METRES, so its share of the screen goes as
        /// 1/distance and has no ceiling. A label 1.27m from the camera came
        /// out 202 pixels tall — 28% of a 720-line frame for one person's
        /// name — and that is what "the text heap" has been every time it was
        /// photographed. It was never a declutter failure: `collidingNames=0`
        /// and `nameTagsUnplaced=0` on the same run.
        ///
        /// THE BOUND CAME FROM THE SERIES, NOT FROM TASTE, and the series had
        /// to land first — the queue item for this said so and refused a
        /// number for three runs. Four runs now agree: the median name is
        /// 0.060 / 0.062 / 0.066 / 0.068 of the screen and the P90 is 0.098 /
        /// 0.100 / 0.102 / 0.121, against worsts of 0.320 / 0.306 / 0.281. So
        /// 0.12 sits at or above every measured P90 and clamps strictly the
        /// tail: nine labels in ten are untouched, and the one that was taking
        /// a third of the frame is brought to an eighth.
        ///
        /// MEASURED RATHER THAN DERIVED, which is why there is no field of
        /// view or text-height arithmetic here. The rect is already projected
        /// two lines above, so the correction is the ratio of what it is to
        /// what it may be, applied to the scale that produced it. It converges
        /// in one frame and unwinds itself when the label is far again,
        /// because a frac below the cap asks for a scale ABOVE the current one
        /// and the clamp at 1 stops it there.
        ///
        /// ONE, AND THE CODE SAYS WHY IT MAY ASSUME THAT. Nothing else scales
        /// a name — `NpcWalker` sets `characterSize` and a colour and
        /// `Billboard.Aim` sets rotation only — and the verdict has read
        /// `worstNameScale=1.000` on every run that printed it. If that ever
        /// stops being true this pins to the wrong baseline, so it is measured
        /// rather than trusted: `NamePinFloor` is the smallest scale ever
        /// applied, and a floor that keeps falling is this assumption breaking.
        public const float PinFrac = 0.12f;
        public static int NamesPinned { get; private set; }
        public static float NamePinFloor { get; private set; } = 1f;

        /// Returns the scale RELATIVE to what the rect was measured at, or
        /// -1 when nothing could be pinned — so a caller can turn a pre-cap
        /// measurement into the post-cap one without projecting twice.
        static float Pin(TextMesh label, float frac)
        {
            if (label == null || frac <= 0f) return -1f;
            var t = label.transform;
            float now = t.localScale.y;
            if (now <= 0f) return -1f;
            float want = Mathf.Clamp(now * PinFrac / frac, 0.05f, 1f);
            // A DEAD BAND, because a scale write every frame on every label is
            // a transform dirty flag every frame on every label, and this runs
            // inside the budget the `frame` gate is red against. One per cent
            // is well below anything visible and well above float noise.
            // THE RATIO IS RETURNED EVEN INSIDE THE DEAD BAND. `want / now` is
            // what the caller needs to convert its pre-cap measurement, and a
            // dead band that skipped the WRITE must not also skip the ANSWER —
            // that would report a label as unscaled on exactly the frames where
            // it was already the right size, which is the majority of them.
            if (Mathf.Abs(want - now) < 0.01f) return want / now;
            t.localScale = new Vector3(want, want, want);
            if (want < now) NamesPinned++;
            if (want < NamePinFloor) NamePinFloor = want;
            return want / now;
        }

        static void Resolve()
        {
            Offered = _offered.Count;
            if (Offered > OfferedPeak) OfferedPeak = Offered;
            // COUNTED WITHIN THE FRAME, where every label is still alive and
            // its identity cannot be in question — which is exactly what makes
            // this comparable with `OfferedPeak` when the lifetime set is not.
            if (_offered.Count > 0)
            {
                _distinct.Clear();
                _distinctIds.Clear();
                int alive = 0;
                foreach (var c in _offered)
                {
                    if (c.Label == null) continue;
                    alive++;
                    _distinct.Add(c.Label);
                    _distinctIds.Add(c.Label.GetInstanceID());
                }
                if (_distinct.Count > OfferedDistinctPeak)
                    OfferedDistinctPeak = _distinct.Count;

                // ALL FOUR TAKEN AT THE SAME INSTANT, AND THAT IS THE POINT.
                //
                // The last build produced a reading I could not explain and
                // spent twenty minutes failing to: 42 offered in one frame
                // against a distinct peak of 17, with `namesDupOffers=0` (so no
                // duplicates reached the list) and `namesManagedDead=0` (so no
                // label had been destroyed). Those three cannot all be true.
                //
                // AND THE FIRST THING TO SUSPECT IS THAT THEY ARE NOT ABOUT THE
                // SAME FRAME. `OfferedPeak` and `OfferedDistinctPeak` are two
                // independent maxima over frames, and I wrote the rule about
                // dividing two maxima into this project's notes this morning
                // before doing it here by lunchtime. So the four numbers below
                // are captured together, at whichever frame offered most:
                // the raw count, how many were still alive, how many distinct
                // OBJECTS that came to, and how many distinct INSTANCE IDS.
                //
                // Those last two are the discriminator and they are different
                // types on purpose. `_distinct` is a `HashSet<TextMesh>`, so it
                // dedupes through Unity's own equality; `_distinctIds` is a
                // `HashSet<int>`, which cannot be influenced by any of it. If
                // the object set comes out smaller than the id set, Unity is
                // merging live objects the game considers different, and every
                // count in this file built on a `HashSet<TextMesh>` — including
                // `namesManagedEver`, which has produced three wrong answers —
                // has been under-reporting from the day it was written.
                if (_offered.Count > OfferedAtWorst)
                {
                    OfferedAtWorst = _offered.Count;
                    AliveAtWorst = alive;
                    DistinctObjectsAtWorst = _distinct.Count;
                    DistinctIdsAtWorst = _distinctIds.Count;
                }
            }
            Suppressed = 0;
            Unresolved = 0;
            OffScreenNow = 0;
            UnplacedNow = 0;
            var cam = Camera.main;
            if (cam == null || _offered.Count == 0) return;
            ResolvedFrames++;

            // Nearest first, so the winner of any overlap is the person the
            // player is closest to — which is the one they are most likely to
            // be looking at and the only one they can speak to.
            _offered.Sort((a, b) => a.Distance.CompareTo(b.Distance));

            var kept = new List<Rect>(_offered.Count);
            foreach (var c in _offered)
            {
                if (c.Label == null) continue;
                var r = c.Label.GetComponent<Renderer>();
                if (r == null) continue;
                if (!ScreenRect(cam, r.bounds, out var rect, out var why))
                {
                    // OFF SCREEN IS NOT UNMANAGED. A label the camera cannot
                    // see is not drawn, cannot collide with anything, and needs
                    // no decision — counting it as a failure of the declutter
                    // is how `nameTagsUnresolved=42` of 43 came to read as
                    // "two-fifths of labels never reach the placement loop"
                    // when most of them were simply behind the player.
                    if (why == RectFail.OffScreen) { OffScreenNow++; continue; }

                    // NEITHER KEPT NOR SUPPRESSED — AND STILL ON SCREEN.
                    //
                    // A label whose rect cannot be computed falls out of this
                    // loop entirely: it is not placed, it is not hidden, and
                    // nothing counts it. It just draws. `nameTagsTooNear` has
                    // read as high as 5,049 of 12,664 rect requests, so this is
                    // not a corner — it is two labels in five going unmanaged
                    // while `nameTagsHidden` reports the declutter working.
                    Unresolved++;
                    continue;
                }

                bool blocked = false;
                foreach (var k in kept)
                    if (k.Overlaps(rect)) { blocked = true; break; }

                if (blocked)
                {
                    // Hidden, not moved. Nudging a colliding label somewhere
                    // free would put a name over the wrong person's head, which
                    // is a worse failure than not naming them — this game is
                    // about who saw whom, and a misattributed name is a lie.
                    var col = c.Label.color;
                    col.a = 0f;
                    c.Label.color = col;
                    Suppressed++;
                }
                else
                {
                    kept.Add(rect);
                    // HOW BIG A NAME EVER GETS, MEASURED WHERE THE NAMES ARE.
                    //
                    // `SimDirector.MeasureTextFaults` reported
                    // `worstTextHeightFrac=0.210` — a label a fifth of the
                    // screen tall — under a comment claiming it measured "what
                    // NameTags manages". It did not: it looped over every
                    // `TextMesh` in the scene, and this city is full of street
                    // plates that are SUPPOSED to be large when you stand next
                    // to one. The same reading that made the mirrored-text
                    // count meaningless.
                    //
                    // Here the set is exactly the offered NPC labels, the rects
                    // are already computed, and a suppressed label is excluded
                    // because it is invisible and its size is not a fault. The
                    // number this produces is answerable: no threshold on it
                    // yet, because rule 2 — print the series first, then bound
                    // it from the evidence.
                    float frac = rect.height / Mathf.Max(1f, cam.pixelHeight);
                    // THE SAMPLE GOES IN BEFORE EITHER BRANCH, so the series
                    // and the peak describe the same population. Recording it
                    // inside the `if` would have collected only the record
                    // holders — a median of the maxima, which is a statistic
                    // about nothing.
                    _nameFracs.Add(frac);
                    // AND THE OTHER AXIS, WHICH NOTHING HAS EVER MEASURED.
                    //
                    // Every reading in this file is `rect.height` — the cap,
                    // the worst, the series. `review_day1_night` shows two
                    // labels each spanning about a third of the frame with the
                    // second one clipping off the right edge, and every number
                    // here says the nameplates are inside their bound. Both are
                    // true: `PinFrac` caps HEIGHT, and at a legal height an
                    // eight-letter name is enormously wide. A bound on one axis
                    // of a two-axis object is not a bound.
                    //
                    // NOT REOPENING THE PINNING RULE, which is closed and works
                    // — this adds the axis it was never asked about. From the
                    // SAME rect as the height, so the two cannot come from two
                    // instants, and no threshold until the series has been read
                    // (rule 2), which is the same discipline the height had.
                    float wfrac = rect.width / Mathf.Max(1f, cam.pixelWidth);
                    _nameWidths.Add(wfrac);

                    // AND THE WIDTH AFTER THE CAP, WHICH IS THE ONE ON SCREEN.
                    //
                    // The first reading of this measured 0.610 on a label
                    // saying "Carl" — four letters at three fifths of the
                    // frame — and I nearly wrote that up as a long-name
                    // problem. It is not: this sample is taken BEFORE `Pin`
                    // runs, so it describes the label's size as the projection
                    // found it, not as the player sees it. So does the height
                    // series beside it, and has since it was written.
                    //
                    // `Pin` scales uniformly, so the post-cap width is the
                    // pre-cap width times the scale it settles on. That is what
                    // the eye gets, and it is the number a bound would ever be
                    // set from.
                    //
                    // BOTH KEPT. The pre-cap value says how hard the cap is
                    // working; the post-cap one says whether it is enough, and
                    // they are different questions — 0.610 shrinking to 0.12
                    // is the system doing its job, and 0.610 staying at 0.610
                    // is a label the cap never reached.
                    float scale = Pin(c.Label, frac);
                    if (scale > 0f)
                    {
                        float shown = wfrac * scale;
                        _nameShownWidths.Add(shown);
                        if (shown > WorstNameWidthFrac)
                        {
                            WorstNameWidthFrac = shown;
                            WorstNameWidthText = c.Label.text ?? "";
                        }
                    }
                    if (frac > WorstNameFrac)
                    {
                        WorstNameFrac = frac;
                        WorstNameMetres = Vector3.Distance(cam.transform.position,
                                                          c.Label.transform.position);
                        WorstNameBoundsY = r.bounds.size.y;
                        WorstNameScale = c.Label.transform.lossyScale.y;
                        // THE NUMBERS CONTRADICT EACH OTHER, SO MEASURE THE
                        // THING THE RECT IS ACTUALLY BUILT FROM.
                        //
                        // Last run: bounds 0.29m tall, scale 1.0, label 6.45m
                        // away — and a rect 4.5 SCREENS high. At that distance
                        // the frame is about seven metres, so 0.29m is four per
                        // cent of it. Those readings cannot all describe the
                        // same object, and the one I trust least is the
                        // distance, because it is measured to the TRANSFORM
                        // while the rect is projected from the BOUNDS. If the
                        // mesh sits far from its own transform, both the
                        // enormous rect and a third of all rect requests being
                        // rejected as too-near follow immediately.
                        //
                        // So: the distance to the bounds, and the raw pixel
                        // height. Between them there is nothing left to infer —
                        // either the box is somewhere the transform is not, or
                        // the projection is wrong, and no third reading is
                        // needed to tell those apart.
                        WorstNameCentreMetres = Vector3.Distance(cam.transform.position,
                                                                r.bounds.center);
                        WorstNamePixels = rect.height;
                    }
                }
            }

            // THE POSTCONDITION, ASKED SEPARATELY FROM THE WORK.
            //
            // Everything above is what the pass DID. This is what it LEFT: of
            // the labels still showing, is any pair in the same place. It is
            // deliberately not the `blocked` tally — those are the collisions
            // the declutter resolved, and requiring zero of THEM would be
            // requiring an empty street.
            //
            // Redundant while the loop above is correct, and that is the whole
            // value of it. It re-derives the claim from the result instead of
            // restating the loop, so it survives the rewrite that breaks the
            // loop — which is the failure a gate exists to catch and the one a
            // counter incremented inside the loop cannot.
            for (int i = 0; i < kept.Count; i++)
                for (int j = i + 1; j < kept.Count; j++)
                    if (kept[i].Overlaps(kept[j])) UnplacedNow++;
            if (UnplacedNow > WorstUnplaced) WorstUnplaced = UnplacedNow;
            // Taken here, at the end of a resolve, so all three describe the
            // same pass — the mismatch that made `offered` unreadable was
            // exactly two counters sampled at different moments.
            if (Suppressed > SuppressedPeak) SuppressedPeak = Suppressed;
            if (Unresolved > UnresolvedPeak) UnresolvedPeak = Unresolved;
            if (OffScreenNow > OffScreenPeak) OffScreenPeak = OffScreenNow;
        }

        /// A world-space bounds as a screen rectangle, or false if it is behind
        /// the camera — where the projection is meaningless and every rect
        /// would appear to collide with every other.
        /// Why a rect could not be had. `OffScreen` is not a fault — see the
        /// note where it is returned.
        public enum RectFail { None, TooNear, OffScreen }

        public static bool ScreenRect(Camera cam, Bounds b, out Rect rect) =>
            ScreenRect(cam, b, out rect, out _);

        public static bool ScreenRect(Camera cam, Bounds b, out Rect rect, out RectFail why)
        {
            why = RectFail.None;
            rect = default;
            // NOT MERELY IN FRONT — IN FRONT OF THE NEAR PLANE.
            //
            // `z <= 0` catches behind the camera, where the projection is
            // meaningless. It does not catch a label ALMOST AT the camera, where
            // the projection is finite and absurd: screen size goes as 1/z, so a
            // label at a millimetre produces a rect thousands of screens tall.
            // The run that found this reported a nameplate 2,119 times the
            // height of the frame.
            //
            // That is not only a bad number. This same function feeds the
            // declutter, and a rect that size overlaps EVERY other label — so
            // one NPC brushing the camera would suppress every name on screen,
            // silently, and the "collisions resolved" counter would call it a
            // good day's work.
            //
            // Bounded by `nearClipPlane` rather than by a figure of mine. It is
            // the camera's own statement of what it draws: nearer than that and
            // there is nothing on screen to label, so there is no rect to want.
            RectCalls++;
            // PROJECTED FROM THE CENTRE, NOT FROM TWO DIAGONAL CORNERS.
            //
            // The numbers finally cornered this. A box 0.29m tall, whose centre
            // and whose transform are BOTH 3.08m from the camera, produced a
            // rect 3,816 pixels high on a 720-pixel screen. At that distance
            // the frame is about 3.6m, so 0.29m is roughly 59 pixels. The
            // inputs were right and the projection was wrong by a factor of
            // sixty-five, which is why three previous attempts at this metric —
            // wrong scope, wrong near-plane, wrong distance — all failed: they
            // were looking for a bad input to a good algorithm.
            //
            // `b.min` and `b.max` are OPPOSITE CORNERS of the box, at different
            // depths. Projecting exactly those two and taking their screen-space
            // bounding box is not an approximation of the right answer, it is a
            // different quantity: as either corner approaches the camera its
            // projected position runs away, and the "height" becomes a fact
            // about perspective rather than about the label. Two of eight
            // corners cannot bound a box in general.
            //
            // A nameplate is small and faces the camera, so the honest and
            // stable construction is its centre, sized by its extents at the
            // centre's depth. It cannot run away, because nothing near the
            // camera plane enters the arithmetic.
            var centre = cam.WorldToScreenPoint(b.center);
            float near = Mathf.Max(cam.nearClipPlane, 0.001f);
            if (centre.z <= near)
            {
                // BEHIND THE CAMERA IS OFF SCREEN, NOT A FAULT — and the run
                // that landed says so plainly: `nameTagsUnresolved=42` with
                // `nameTagsOffScreen=42`. Forty-two labels at once with a depth
                // at or behind the near plane is not forty-two broken labels,
                // it is a camera standing in a crowd with people behind it.
                // None of them is drawn — the near clip sees to that — so none
                // of them needs placing.
                //
                // Left in the fault bucket, `Unresolved` would stay pinned at
                // the crowd size for ever and the counter built to discriminate
                // would go back to meaning nothing. Moved here it becomes what
                // it was for: the ONLY way to be unresolved now is a degenerate
                // frustum, so a non-zero reading is a real alarm rather than a
                // census of who is standing behind you.
                TooNear++;
                OffScreen++;
                why = RectFail.OffScreen;
                return false;
            }

            // Pixels per world metre at this depth, from the camera's own
            // vertical field of view. No invented constant: this is the same
            // relationship the projection matrix uses.
            float halfFov = cam.fieldOfView * 0.5f * Mathf.Deg2Rad;
            float visibleHeight = 2f * centre.z * Mathf.Tan(halfFov);
            if (visibleHeight <= 0.0001f) { why = RectFail.TooNear; return false; }
            float pxPerMetre = cam.pixelHeight / visibleHeight;

            float w = b.size.x * pxPerMetre;
            float h = b.size.y * pxPerMetre;
            rect = new Rect(centre.x - w * 0.5f, centre.y - h * 0.5f, w, h);

            // AND IT HAS TO BE ON THE SCREEN, which `z > near` does not say.
            //
            // THE ARITHMETIC THAT FOUND THIS, from one landed run and nothing
            // else. The worst-offending label reported `worstNameBoundsY=0.29`,
            // `worstNameCentreMetres=3.37` and `worstNamePixels=566`. At 3.37m
            // through a 60-degree lens the frame is 3.89m tall, so 0.29m is 54
            // pixels — and 566 is ten and a half times that. The only free term
            // is the depth the projection actually used, and solving for it
            // gives z = 0.32m against a straight-line distance of 3.37m. That
            // is a label EIGHTY-FOUR DEGREES off the camera axis: over the
            // player's shoulder, behind the frame edge, not drawn at all.
            //
            // `centre.z` is depth ALONG THE VIEW AXIS, and `pxPerMetre` goes as
            // 1/z, so anything out to the side is magnified by the cosine of a
            // large angle. Off-axis is the same blow-up as up-close and the
            // near-plane test cannot see it: the label was 3.4m away, which is
            // nowhere near the camera.
            //
            // The damage ran both ways. Such a rect overlaps most of the
            // screen, so an unseen label suppressed real ones; and
            // `SimDirector.CollidingNames` was pairing these off against each
            // other and calling the total a wall of text.
            //
            // Reported as OffScreen and NOT as a fault, because it is not one.
            // A label the camera cannot see needs no rect and takes no part in
            // decluttering — the correct handling is to leave it out, which is
            // what the callers now do.
            if (rect.xMax < 0 || rect.yMax < 0
                || rect.xMin > cam.pixelWidth || rect.yMin > cam.pixelHeight)
            {
                OffScreen++;
                why = RectFail.OffScreen;
                rect = default;
                return false;
            }
            return true;
        }
    }
}
