using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// MOTION MATCHING — the-gap.md item 6, the last thing on the plan still
    /// parked behind a purchase.
    ///
    /// §3b already learned this lesson once, expensively: `Core/Rig` had a
    /// gait, a lean, a breath, a limp and two-bone IK sitting behind a Mixamo
    /// download that stayed un-happened for weeks. The fix was to build the
    /// thing behind the dependency against a stand-in we control. That
    /// section closes with "three other items on this list were parked behind
    /// acquisitions and at least one of them deserves the same treatment."
    ///
    /// This is that treatment, applied to the mocap licence.
    ///
    /// WHAT MOTION MATCHING IS. Instead of a state machine of clips and
    /// transitions — walk, walk_turn_left, walk_to_run, and the combinatorial
    /// misery of authoring every edge — you keep a flat pile of animation
    /// frames and, several times a second, ask: *given where the player is
    /// asking to go, and where my body is right now, which single frame in the
    /// whole corpus is the best next frame?* Then you go there and blend.
    /// There are no transitions to author because there are no states.
    ///
    /// It is the technique behind KCD2-grade locomotion and it is not
    /// difficult. **What is expensive is the corpus** — hours of clean mocap
    /// covering every speed, turn rate, start, stop and pivot, because the
    /// matcher can only ever play back motion it was given. The good research
    /// sets (AMASS, LAFAN1, 100STYLE) are non-commercial; a commercial one is
    /// $100–1000 and is Jafar's to buy, not mine.
    ///
    /// SO THE CORPUS IS AN INTERFACE, and `SyntheticCorpus` implements it
    /// today out of `Rig`'s analytic walk. To be honest about what that buys:
    /// matching against motion this file generated cannot produce motion
    /// better than that motion. The synthetic corpus is not a substitute for
    /// mocap and no amount of search makes it one.
    ///
    /// What it IS, is everything around the corpus built and proved before
    /// the money is spent: the feature layout, the normalisation, the cost
    /// weighting, the hysteresis, the clip-boundary rule, the blend. Those are
    /// where motion matching is actually got wrong, they are all testable
    /// without a single mocap frame, and every one of them is a bug that
    /// would otherwise be discovered *after* the purchase, in a system with
    /// no working baseline to compare against.
    ///
    /// NOT WIRED TO THE GAME YET, and deliberately so — see the note at the
    /// bottom of this file for exactly what wiring it needs.
    public static class MotionFeature
    {
        /// How far into the future the trajectory is compared, in seconds.
        ///
        /// THE SPAN MATTERS MORE THAN THE COUNT. Too short and the matcher
        /// cannot see a turn coming, so it commits to a straight-ahead frame
        /// and has to correct violently. Too long and it refuses to start
        /// walking because it can see you stopping in two seconds. A second
        /// of lookahead is about one stride, which is the horizon a person
        /// actually plans over.
        public static readonly double[] HorizonSeconds = { 0.33, 0.66, 1.0 };

        // Layout of the feature vector. Flat doubles rather than a struct of
        // named fields, because normalisation and weighting are per-dimension
        // and a struct turns both into thirty lines of copy-paste.
        public const int Horizons = 3;
        public const int TrajPos = 0;                        // (x,z) per horizon
        public const int TrajDir = TrajPos + Horizons * 2;   // (x,z) facing per horizon
        public const int FootPos = TrajDir + Horizons * 2;   // (x,y,z) per foot
        public const int FootVel = FootPos + 6;              // (x,y,z) per foot
        public const int HipVel = FootVel + 6;               // (y)
        public const int Length = HipVel + 1;

        /// WHY THE FEATURE IS SPLIT IN TWO AT ALL, and it is the decision the
        /// whole technique rests on.
        ///
        /// The trajectory half is what the player ASKED FOR. The pose half is
        /// where the body ALREADY IS. Weight the pose too heavily and you get
        /// a character who moves beautifully and ignores the stick — every
        /// frame it picks is a lovely continuation of the last one and none of
        /// them go where you pointed. Weight the trajectory too heavily and it
        /// snaps to whatever frame happens to face the right way, mid-stride,
        /// with the wrong foot down.
        ///
        /// Responsiveness wins, because a player forgives an ugly step and
        /// does not forgive a character that will not turn.
        public const double TrajectoryWeight = 1.0;
        public const double PoseWeight = 0.42;

        /// The foot terms carry most of the pose weight, and specifically the
        /// foot VELOCITIES.
        ///
        /// Foot sliding is the artefact that makes procedural locomotion look
        /// procedural, and it comes from cutting to a frame whose foot is
        /// travelling when the current foot is planted. Matching velocity is
        /// what stops that — a planted foot finds another planted foot — and
        /// it is why the velocity terms are weighted above the positions they
        /// are derived from.
        public const double FootVelocityWeight = 1.6;

        public static double GroupWeight(int dimension)
        {
            if (dimension < FootPos) return TrajectoryWeight;
            if (dimension >= FootVel && dimension < HipVel) return PoseWeight * FootVelocityWeight;
            return PoseWeight;
        }
    }

    /// What a corpus has to be able to answer. A licensed mocap library
    /// implements this by sampling its clips; `SyntheticCorpus` implements it
    /// out of `Rig`. Nothing downstream knows or cares which.
    public interface IMotionCorpus
    {
        int ClipCount { get; }
        /// Sampled frames per second. 30 is the usual mocap rate and is
        /// plenty: the matcher blends between frames, it does not step to them.
        double SampleRate { get; }
        int FrameCount(int clip);
        /// The searchable feature for one frame, written into `into`.
        void Feature(int clip, int frame, double[] into);
    }

    /// The flat pile of frames, normalised and searchable.
    public class MotionDatabase
    {
        readonly List<double[]> _features = new List<double[]>();
        readonly List<int> _clip = new List<int>();
        readonly List<int> _frame = new List<int>();
        double[] _scale;

        public int Count => _features.Count;
        public int ClipOf(int i) => _clip[i];
        public int FrameOf(int i) => _frame[i];

        public static MotionDatabase Build(IMotionCorpus corpus)
        {
            var db = new MotionDatabase();
            for (int c = 0; c < corpus.ClipCount; c++)
            {
                int n = corpus.FrameCount(c);
                for (int f = 0; f < n; f++)
                {
                    var v = new double[MotionFeature.Length];
                    corpus.Feature(c, f, v);
                    db._features.Add(v);
                    db._clip.Add(c);
                    db._frame.Add(f);
                }
            }
            db.Normalise();
            return db;
        }

        /// PER-DIMENSION NORMALISATION, and skipping it is the classic way to
        /// build a matcher that does not work and cannot be debugged.
        ///
        /// The feature mixes trajectory positions in metres (spread of
        /// several), facing vectors (spread of about one) and foot velocities
        /// in metres per second (spread of a few). A plain squared distance
        /// over that is not a distance between motions, it is a distance
        /// dominated by whichever channel happens to have the largest units —
        /// and the authored weights above are then multiplying numbers that
        /// were already a hundred to one apart, which makes them read as
        /// tuning when they are noise.
        ///
        /// Dividing each dimension by its standard deviation across the whole
        /// corpus puts every channel on equal terms first, so the weights mean
        /// what they say.
        void Normalise()
        {
            _scale = new double[MotionFeature.Length];
            if (_features.Count == 0)
            {
                for (int d = 0; d < _scale.Length; d++) _scale[d] = 1;
                return;
            }
            for (int d = 0; d < MotionFeature.Length; d++)
            {
                double mean = 0;
                for (int i = 0; i < _features.Count; i++) mean += _features[i][d];
                mean /= _features.Count;
                double var = 0;
                for (int i = 0; i < _features.Count; i++)
                {
                    double x = _features[i][d] - mean;
                    var += x * x;
                }
                var /= _features.Count;
                double sd = Math.Sqrt(var);
                // A dimension that never varies carries no information, and
                // dividing by its zero standard deviation would turn every
                // query into a NaN. Leave it at unit scale; the weighted
                // difference across it is zero for every candidate anyway.
                _scale[d] = sd > 1e-6 ? 1.0 / sd : 1.0;
            }
        }

        public double Scale(int dimension) => _scale[dimension];

        public double Cost(int index, double[] query)
        {
            var f = _features[index];
            double sum = 0;
            for (int d = 0; d < MotionFeature.Length; d++)
            {
                double diff = (f[d] - query[d]) * _scale[d];
                sum += MotionFeature.GroupWeight(d) * diff * diff;
            }
            return sum;
        }

        /// How far apart two frames are IN POSE ALONE — the trajectory
        /// channels excluded.
        ///
        /// This is the number that says whether a jump is visible. A matcher
        /// on a corpus of any real length has many frames at the same point
        /// in the stride, and hopping between them is free: same pose, no pop,
        /// nothing on screen changes. Counting raw jumps calls that a twitch
        /// and it is not one — the twitch is a jump that lands on a DIFFERENT
        /// pose, and only a pose-space distance can tell the two apart.
        public double PoseDistance(int a, int b)
        {
            if (a < 0 || b < 0) return 0;
            var fa = _features[a];
            var fb = _features[b];
            double sum = 0;
            for (int d = MotionFeature.FootPos; d < MotionFeature.Length; d++)
            {
                double diff = (fa[d] - fb[d]) * _scale[d];
                sum += MotionFeature.GroupWeight(d) * diff * diff;
            }
            return sum;
        }

        /// The cost of where playback ACTUALLY IS, which is between two
        /// frames rather than on one.
        ///
        /// Judging "should I stay here?" at the integer frame index charges
        /// the matcher for up to a full frame of phase error that it created
        /// itself by stepping in integers — so it jumps to fix it, lands
        /// between two frames again, and jumps again. A self-inflicted error
        /// that the correction re-creates is a loop, and it presents as
        /// chatter on a perfectly good clip.
        public double CostBetween(int index, double fraction, double[] query)
        {
            if (index < 0) return double.MaxValue;
            int next = Next(index);
            if (next < 0 || fraction <= 0) return Cost(index, query);
            double f = fraction > 1 ? 1 : fraction;
            var a = _features[index];
            var b = _features[next];
            double sum = 0;
            for (int d = 0; d < MotionFeature.Length; d++)
            {
                double here = a[d] + (b[d] - a[d]) * f;
                double diff = (here - query[d]) * _scale[d];
                sum += MotionFeature.GroupWeight(d) * diff * diff;
            }
            return sum;
        }

        public int Nearest(double[] query, out double cost)
        {
            cost = double.MaxValue;
            int best = -1;
            for (int i = 0; i < _features.Count; i++)
            {
                double c = Cost(i, query);
                if (c < cost) { cost = c; best = i; }
            }
            return best;
        }

        /// The index of the frame that naturally follows `index`, or -1 at the
        /// end of a clip.
        ///
        /// CLIPS DO NOT RUN INTO EACH OTHER. The database is one flat array
        /// and the last frame of clip 3 sits immediately before the first
        /// frame of clip 4, but those two frames are unrelated motion — a
        /// runner mid-stride and a person standing still, recorded an hour
        /// apart. Letting playback fall off the end of one into the start of
        /// the next is a one-character bug that produces a character who
        /// teleports between poses at clip boundaries, and it is invisible in
        /// code review because the array index is perfectly valid.
        public int Next(int index)
        {
            if (index < 0 || index + 1 >= _features.Count) return -1;
            return _clip[index + 1] == _clip[index] ? index + 1 : -1;
        }
    }

    /// The runtime. Holds where in the corpus we are, searches on a cadence,
    /// and refuses to jump for a trivial improvement.
    public class MotionMatcher
    {
        readonly MotionDatabase _db;
        readonly double _sampleRate;

        /// How often a search runs, in seconds. NOT every frame.
        ///
        /// Ten times a second is the standard figure and it is not a
        /// performance compromise — searching every frame is what makes a
        /// matcher chatter, because the best frame for this instant is a
        /// different one every instant and none of them get to play. The
        /// cadence IS the commitment.
        public const double SearchIntervalSeconds = 0.1;

        /// A candidate must beat continuing where we are by this fraction
        /// before we jump.
        ///
        /// Hysteresis, and it does the same job as the cadence from the other
        /// side. Without it the matcher leaves a perfectly good clip for one
        /// that is a hundredth of a percent better, every single search, and
        /// the result is a body that twitches while walking in a straight
        /// line — the single most recognisable failure of a naive
        /// implementation.
        public const double JumpMargin = 0.12;

        /// Settable so a test can run the same walk with and without it and
        /// compare, rather than asserting the constant back at itself. A
        /// check that only says "the margin is not zero" moves with the
        /// number it is meant to pin, which is a mistake this project has
        /// made twice and caught both times by break run.
        public double Margin = JumpMargin;

        double _sinceSearch;
        double _playhead;

        public int Index { get; private set; } = -1;
        public int Searches { get; private set; }
        public int Jumps { get; private set; }
        /// Set on the frame a jump happened, so the caller knows to blend
        /// rather than cut.
        public bool Jumped { get; private set; }
        public double LastCost { get; private set; }
        /// The biggest pose discontinuity any jump has caused. The number a
        /// gate should read: jump COUNT is not a quality measure, and a
        /// matcher hopping between identical poses is doing nothing wrong.
        public double WorstJumpPop { get; private set; }
        /// What continuing was judged to cost at the last search. Exposed
        /// because the ONLY thing that pins the use site is a number read
        /// from it: `CostBetween` having the right property is not the same
        /// claim as the matcher calling it.
        public double LastStayCost { get; private set; }
        /// How far past `Index` playback has got, 0..1, for interpolating
        /// towards the next frame.
        public double Fraction => _playhead;

        public MotionMatcher(MotionDatabase db, double sampleRate)
        {
            _db = db;
            _sampleRate = sampleRate > 0 ? sampleRate : 30.0;
        }

        public void Tick(double dt, double[] query)
        {
            Jumped = false;
            if (_db == null || _db.Count == 0 || dt <= 0) return;

            _sinceSearch += dt;

            // PLAY FORWARD IN SECONDS, NOT IN TICKS. The first version
            // advanced one corpus frame per call, which quietly plays a 30fps
            // corpus at double speed on a 60fps frame and at eight times on a
            // 240fps one. It surfaced as the matcher jumping nine times while
            // walking in a straight line: playback outran the query's stride
            // phase, so staying put got worse every frame and the hysteresis
            // was right to give way. The chatter was the symptom; the clock
            // was the fault.
            if (Index >= 0)
            {
                _playhead += dt * _sampleRate;
                while (_playhead >= 1.0)
                {
                    int next = _db.Next(Index);
                    // Off the end of a clip: force a search whatever the
                    // cadence says, because there is nothing left to play.
                    if (next < 0) { _sinceSearch = SearchIntervalSeconds; _playhead = 0; break; }
                    Index = next;
                    _playhead -= 1.0;
                }
            }

            if (Index >= 0 && _sinceSearch < SearchIntervalSeconds) return;
            _sinceSearch = 0;
            Searches++;

            int best = _db.Nearest(query, out double bestCost);
            LastCost = bestCost;
            if (best < 0) return;

            if (Index >= 0)
            {
                double staying = _db.CostBetween(Index, _playhead, query);
                LastStayCost = staying;
                if (bestCost > staying * (1.0 - Margin)) { LastCost = staying; return; }
            }

            if (best != Index)
            {
                Jumps++;
                Jumped = true;
                double pop = _db.PoseDistance(Index, best);
                if (pop > WorstJumpPop) WorstJumpPop = pop;
            }
            Index = best;
            _playhead = 0;
        }

        /// How far to blend out of the pose we were in, 0..1, `since` seconds
        /// after a jump.
        ///
        /// INERTIAL BLEND RATHER THAN A CROSS-FADE. A cross-fade averages two
        /// poses, and the average of two legs in opposite positions is a leg
        /// in neither — for a quarter of a second the character wades. An
        /// inertial blend plays only the NEW pose and decays the OFFSET
        /// between where the body was and where the new frame starts, so
        /// there is never a moment of averaged nonsense on screen.
        public const double BlendSeconds = 0.22;

        public static double BlendOut(double since)
        {
            if (since <= 0) return 1.0;
            double p = Feel.Clamp01(since / BlendSeconds);
            // Smoothstep: zero velocity at both ends, so the correction
            // neither starts with a snap nor stops with one.
            return 1.0 - p * p * (3 - 2 * p);
        }
    }

    /// The stand-in corpus: `Rig`'s analytic walk, sampled across a grid of
    /// speeds and turn rates.
    ///
    /// Read the honest limit again — motion matched over this can only ever
    /// be as good as `Rig`, and `Rig` is a sine wave with opinions. The point
    /// is not the motion. The point is that the feature layout, the
    /// normalisation, the weights, the cadence, the margin and the clip
    /// boundaries are all exercised now, so a licensed corpus is a class that
    /// implements one interface rather than a system meeting reality for the
    /// first time on the day it is paid for.
    public class SyntheticCorpus : IMotionCorpus
    {
        /// One clip per (speed, turn rate). Real corpora are organised the
        /// same way — a shoot is a list of "walk this fast, turning this
        /// hard" takes — so the shape the matcher sees is right even though
        /// the motion in it is not real.
        public static readonly double[] Speeds = { 0.0, 0.8, 1.4, 2.2, 3.6, 5.2 };
        public static readonly double[] TurnRatesDegPerSec = { -90, -35, 0, 35, 90 };

        public const double ClipSeconds = 2.0;
        public double SampleRate => 30.0;
        public int ClipCount => Speeds.Length * TurnRatesDegPerSec.Length;
        public int FrameCount(int clip) => (int)(ClipSeconds * SampleRate);

        public double SpeedOf(int clip) => Speeds[clip / TurnRatesDegPerSec.Length];
        public double TurnOf(int clip) => TurnRatesDegPerSec[clip % TurnRatesDegPerSec.Length];

        /// Seconds per stride at a given speed. Shared with `Query` on
        /// purpose: the query and the corpus entries have to be built by the
        /// same arithmetic or the distance between them measures the
        /// disagreement between two formulas rather than the difference
        /// between two motions.
        public static double StridePeriod(double speed) => 0.62 - 0.05 * speed;

        static double Phase(double speed, double t) =>
            speed < Rig.StillBelowMetresPerSec ? 0 : t / StridePeriod(speed);

        public void Feature(int clip, int frame, double[] into)
        {
            Array.Clear(into, 0, into.Length);
            double speed = SpeedOf(clip);
            double turn = TurnOf(clip) * Math.PI / 180.0;
            double t = frame / SampleRate;
            // Stride phase. A stride is roughly 0.55s at a walk and shortens
            // with speed; below the standstill threshold there is no cycle at
            // all and every frame of the clip is the same standing pose.
            double stride = Phase(speed, t);

            // ---- trajectory, in this frame's own space ----
            for (int h = 0; h < MotionFeature.Horizons; h++)
            {
                double dt = MotionFeature.HorizonSeconds[h];
                double heading = turn * dt;
                // Constant-curvature arc: the path a body actually takes at a
                // steady speed and turn rate, not a straight line rotated at
                // the end.
                double x, z;
                if (Math.Abs(turn) < 1e-6) { x = 0; z = speed * dt; }
                else
                {
                    double r = speed / turn;
                    x = r * (1 - Math.Cos(heading));
                    z = r * Math.Sin(heading);
                }
                into[MotionFeature.TrajPos + h * 2] = x;
                into[MotionFeature.TrajPos + h * 2 + 1] = z;
                into[MotionFeature.TrajDir + h * 2] = Math.Sin(heading);
                into[MotionFeature.TrajDir + h * 2 + 1] = Math.Cos(heading);
            }

            // ---- pose: the two feet, from the walk cycle ----
            var (lHip, lKnee) = Rig.LegSwing(stride, speed);
            var (rHip, rKnee) = Rig.LegSwing(stride + 0.5, speed);
            Foot(lHip, lKnee, -0.09, into, MotionFeature.FootPos);
            Foot(rHip, rKnee, 0.09, into, MotionFeature.FootPos + 3);

            // Velocities by finite difference, which is how a real corpus
            // derives them too — mocap gives positions and the velocity
            // channel is computed at bake time.
            //
            // FRAME 0 DIFFERENCES FORWARDS. The obvious `if (frame > 0)`
            // leaves the first frame of every clip with zero velocity
            // everywhere, and zero is not missing data — it is the feature
            // vector of a body standing perfectly still. A query with any
            // planted foot then finds those holes irresistible, and the
            // matcher jumps to the start of a clip over and over. It showed
            // up here as nine jumps in a straight line, all of them landing
            // on frame 0.
            double before = frame > 0 ? (frame - 1) / SampleRate : t;
            double after = frame > 0 ? t : (frame + 1) / SampleRate;
            Velocities(speed, before, after, into);
        }

        void Velocities(double speed, double t0, double t1, double[] into)
        {
            double dt = t1 - t0;
            if (dt <= 0) return;
            var a = new double[6];
            var b = new double[6];
            PoseAt(speed, t0, a);
            PoseAt(speed, t1, b);
            for (int i = 0; i < 6; i++)
                into[MotionFeature.FootVel + i] = (b[i] - a[i]) / dt;
            into[MotionFeature.HipVel] =
                (Rig.Bob(Phase(speed, t1), speed) - Rig.Bob(Phase(speed, t0), speed)) / dt;
        }

        void PoseAt(double speed, double t, double[] into)
        {
            double p = Phase(speed, t);
            var (lHip, lKnee) = Rig.LegSwing(p, speed);
            var (rHip, rKnee) = Rig.LegSwing(p + 0.5, speed);
            Foot(lHip, lKnee, -0.09, into, 0);
            Foot(rHip, rKnee, 0.09, into, 3);
        }

        /// Foot position relative to the hip, from the two joint angles.
        /// Thigh and shin lengths are the reference physique's; the matcher
        /// works in the corpus's own proportions and the retarget to a
        /// particular body happens downstream, exactly as it would for mocap.
        static void Foot(double hipDeg, double kneeDeg, double side, double[] into, int at)
        {
            const double Thigh = 0.44, Shin = 0.42;
            double hip = hipDeg * Math.PI / 180.0;
            double knee = kneeDeg * Math.PI / 180.0;
            double kneeZ = Thigh * Math.Sin(hip);
            double kneeY = -Thigh * Math.Cos(hip);
            double shinAngle = hip - knee;
            into[at] = side;
            into[at + 1] = kneeY - Shin * Math.Cos(shinAngle);
            into[at + 2] = kneeZ + Shin * Math.Sin(shinAngle);
        }

        /// Build the query a live character issues: where it is being asked to
        /// go, and where its feet are now. Same layout as a corpus frame, and
        /// that is not an accident — the query and the entries have to be the
        /// same kind of thing or the distance between them is meaningless.
        public static double[] Query(double desiredSpeed, double desiredTurnDegPerSec,
                                     double currentStridePhase, double currentSpeed)
        {
            var q = new double[MotionFeature.Length];
            double turn = desiredTurnDegPerSec * Math.PI / 180.0;
            for (int h = 0; h < MotionFeature.Horizons; h++)
            {
                double dt = MotionFeature.HorizonSeconds[h];
                double heading = turn * dt;
                double x, z;
                if (Math.Abs(turn) < 1e-6) { x = 0; z = desiredSpeed * dt; }
                else
                {
                    double r = desiredSpeed / turn;
                    x = r * (1 - Math.Cos(heading));
                    z = r * Math.Sin(heading);
                }
                q[MotionFeature.TrajPos + h * 2] = x;
                q[MotionFeature.TrajPos + h * 2 + 1] = z;
                q[MotionFeature.TrajDir + h * 2] = Math.Sin(heading);
                q[MotionFeature.TrajDir + h * 2 + 1] = Math.Cos(heading);
            }
            var (lHip, lKnee) = Rig.LegSwing(currentStridePhase, currentSpeed);
            var (rHip, rKnee) = Rig.LegSwing(currentStridePhase + 0.5, currentSpeed);
            Foot(lHip, lKnee, -0.09, q, MotionFeature.FootPos);
            Foot(rHip, rKnee, 0.09, q, MotionFeature.FootPos + 3);

            // AND THE VELOCITY CHANNELS, which the first version of this left
            // at zero. They carry the heaviest weight in the whole feature —
            // they are what stops foot sliding — so a query that cannot
            // express them is not asking a weaker question, it is asking the
            // matcher to find a body that has stopped moving. Every search
            // came back pointing at a standing pose.
            //
            // Differenced over the corpus's own sample interval rather than
            // some other small number: the corpus bakes its velocities across
            // 1/30s of motion, and a query differenced across 1/240s of the
            // same curve is a slightly different quantity in the same units,
            // which is the sort of mismatch that reads as a mysteriously
            // biased cost function.
            double period = StridePeriod(currentSpeed);
            double step = (1.0 / 30.0) / Math.Max(1e-6, period);
            var prevL = Rig.LegSwing(currentStridePhase - step, currentSpeed);
            var prevR = Rig.LegSwing(currentStridePhase - step + 0.5, currentSpeed);
            var prev = new double[6];
            Foot(prevL.hip, prevL.knee, -0.09, prev, 0);
            Foot(prevR.hip, prevR.knee, 0.09, prev, 3);
            for (int i = 0; i < 6; i++)
                q[MotionFeature.FootVel + i] = (q[MotionFeature.FootPos + i] - prev[i]) * 30.0;
            q[MotionFeature.HipVel] =
                (Rig.Bob(currentStridePhase, currentSpeed)
                 - Rig.Bob(currentStridePhase - step, currentSpeed)) * 30.0;
            return q;
        }
    }

    // ---- WHAT WIRING THIS NEEDS, written down so it is not rediscovered ----
    //
    // Unwired on purpose, and for a different reason than `Core/Combat`:
    // combat is dormant by a DESIGN decision, this is dormant because the
    // thing it exists to play back has not been bought. Both are decisions;
    // neither is a bug; and an unwired system that does not say which it is
    // becomes one.
    //
    // The order, when the corpus lands:
    //
    //   1. A `MocapCorpus : IMotionCorpus` that samples the licensed clips.
    //      This file changes not at all — that is the entire point of it.
    //   2. `Game/CharacterRig` gains a tier above the Avatar path: matched
    //      frame -> retargeted joint rotations. The three-tier bind built for
    //      the mannequin already has the shape.
    //   3. A sim gate on `Searches` AND on jump rate. Searches alone is a
    //      presence check — a matcher pinned to one frame searches happily
    //      forever. The pair that means something is "it searched, and it
    //      moved between clips when the query changed".
    //
    // Until then the mannequin plays `Rig` directly, which is what it does
    // now and is not worse for this file existing.
}
