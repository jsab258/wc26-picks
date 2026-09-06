using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Ledger.Core;
using Ledger.Game;

namespace Ledger.StrangerTest
{
    /// QUEUE 119 AT SCALE, BECAUSE THE EVENING IS NOT AVAILABLE.
    ///
    /// Jafar, 2026-09-06: "I am not spending my evenings on a text harness
    /// while the game has no playable build. Run the comparison yourself, at
    /// whatever scale your own tooling supports, and report the result with its
    /// confidence and its biases."
    ///
    /// WHAT THIS IS NOT. It is not the reading queue 119 asked for. That
    /// reading is what a person says, unprompted, about which arm felt more
    /// alive, and no program can produce it. Nothing here scores an arm,
    /// prefers an arm, or reports a preference. It counts what is countable:
    /// how often the two arms say different words, what state stood behind the
    /// difference, and how many of the real arm's lines are answers to
    /// something the player did rather than remarks about the weather.
    ///
    /// IT DRIVES THE SHIPPED SESSION. Every number below comes out of
    /// `Program.Play`, through the same `IUi` the console uses, with the same
    /// cast, the same banks and the same beat sheet a stranger would have got.
    /// A study that re-implemented the session would be measuring its own copy,
    /// which is the fault this project has found in four different systems.
    static partial class Program
    {
        // ---------------------------------------------------------------
        // the answer space
        // ---------------------------------------------------------------

        /// THE WHOLE SINGLE-PASS ANSWER SPACE, AND WHY IT IS THE WHOLE SPACE.
        ///
        /// `Play` asks six questions: which job (3), what hour (3), how you go
        /// in (2), the coat (2), go-or-think-again (2), and what you tell Lena
        /// (3). Answering "think again" reopens the plan loop, so the space of
        /// TRANSCRIPTS is unbounded. The space of WORLDS is not: the loop
        /// overwrites hour, approach and coat and touches nothing else, and the
        /// operation's seed is `day*7919 + hour*31 + id.Length`, which has no
        /// term for how many times the player changed their mind. So a re-plan
        /// that ends on the same plan produces the same night, and 3*3*2*2*3 is
        /// the whole of it.
        ///
        /// THAT IS A CLAIM AND IT IS TESTED, not asserted: `StudySelftest`
        /// plays a two-pass script and its single-pass twin and requires every
        /// spoken line to match.
        internal const int PathCount = 108;

        internal static IEnumerable<int[]> AllPaths()
        {
            for (int t = 0; t < 3; t++)
                for (int h = 0; h < 3; h++)
                    for (int a = 0; a < 2; a++)
                        for (int c = 0; c < 2; c++)
                            for (int s = 0; s < 3; s++)
                                yield return new[] { t, h, a, c, 0, s };
        }

        /// The path in the words of the choices, for a report a person reads.
        /// No spaces, per the instrument conventions, so a reader that splits
        /// on whitespace gets the whole field.
        internal static string PathName(int[] p) =>
            new[] { "customs", "safe", "warehouse" }[p[0]]
            + "/h" + new[] { "23", "01", "03" }[p[1]]
            + "/" + (p[2] == 0 ? "quiet" : "forced")
            + "/" + (p[3] == 0 ? "coat" : "nocoat")
            + "/" + new[] { "truth", "lie", "silent" }[p[5]];

        /// THE SIX SEEDS THE EVENING WOULD HAVE USED, and not six of my own.
        /// `Main` computes `participant*100 + run*7` for participants 1..3 over
        /// runs 1..2, so these are the only seeds a participant could ever have
        /// heard. Picking arbitrary seeds would sweep a line space the
        /// experiment does not use.
        internal static readonly int[] Seeds = { 107, 114, 207, 214, 307, 314 };

        // ---------------------------------------------------------------
        // the arithmetic, kept beside the ladder it mirrors
        // ---------------------------------------------------------------

        /// THE PRESSURE NUMBER `StreetVoice.Stance` COMPUTES AND DOES NOT
        /// RETURN, mirrored here so the study can print a curve instead of a
        /// staircase of band names.
        ///
        /// A MIRROR IS A SECOND IMPLEMENTATION AND THEREFORE A LIABILITY, so it
        /// is checked against the original on every single sample the sweep and
        /// the curve take: `Band(Pressure(...))` must equal
        /// `StreetVoice.Stance(...)`, and a mismatch is reported as an
        /// instrument failure rather than as a finding. Lines quoted from
        /// StreetVoice.cs:94-109.
        internal static double Pressure(double suspicion, double loyalty,
            double strongestAboutPlayer, bool wearingCoat)
        {
            double pressure = Clamp01(0.55 * Clamp01(suspicion) + 0.45 * Clamp01(strongestAboutPlayer));
            pressure -= 0.35 * Clamp01(loyalty - 0.5) * 2.0 * (pressure < 0.85 ? 1.0 : 0.4);
            if (wearingCoat && pressure < 0.7) pressure -= 0.12;
            return Clamp01(pressure);
        }

        internal static StanceKind Band(double pressure, bool leashed)
        {
            if (pressure >= 0.86 && !leashed) return StanceKind.Confronts;
            if (pressure >= 0.72) return StanceKind.Refuses;
            if (pressure >= 0.58) return StanceKind.Avoids;
            if (pressure >= 0.42) return leashed ? StanceKind.Watches : StanceKind.Comments;
            if (pressure >= 0.26) return StanceKind.Watches;
            if (pressure >= 0.12) return StanceKind.Notices;
            return StanceKind.Indifferent;
        }

        /// The rung at which somebody speaks about the player at all, quoted
        /// from the ladder rather than typed as 0.42 in six places.
        internal const double CommentsAt = 0.42;

        /// THIRTY REAL MINUTES IN GAME MINUTES, derived and not chosen:
        /// `GameController.MinutesPerRealSecond` is 2, so 30 * 60 * 2 = 3600.
        /// Meridian clause 2 is written in minutes at the controls and every
        /// other number in this file is in game time, so the conversion is
        /// stated once, here, with the constant it comes from.
        internal const int PlayWindowGameMinutes = 3600;

        static double Clamp01(double v) => v < 0 ? 0 : v > 1 ? 1 : v;

        /// Separators for the joined line tuples. Control characters, because
        /// every printable candidate appears inside the banks: the tell band
        /// interpolates whole sentences and the reply band is full of commas
        /// and full stops, so a visible delimiter would eventually cut a line
        /// in half and report two arms as differing when they had not.
        const char Sep = '\u001f';
        const char Split = '\u001e';

        static string F(double v) => v.ToString("0.000", CultureInfo.InvariantCulture);
        static string F2(double v) => v.ToString("0.00", CultureInfo.InvariantCulture);

        /// A count with the denominator it is a fraction OF, always, and a
        /// never-ran that says so in words rather than printing 0/0.
        internal static string Frac(int n, int of) =>
            of <= 0 ? "nothing-measured" : n + "/" + of;

        // ---------------------------------------------------------------
        // one session, played headlessly
        // ---------------------------------------------------------------

        internal class Run
        {
            public Log Log;
            public ScriptedUi Ui;
            public List<Said> Said => Log.Said;
        }

        internal static Run PlayScript(int[] answers, Arm arm, int seed)
        {
            var ui = new ScriptedUi(answers);
            var log = new Log();
            Play(ui, arm, seed, log);
            return new Run { Log = log, Ui = ui };
        }

        // ---------------------------------------------------------------
        // PART ONE: the comparison at scale
        // ---------------------------------------------------------------

        class Tally
        {
            public int Lines, Differ;
            public int RealPointed, RealChatter, RealAmbient;
            public int CannedPointed, CannedChatter, CannedAmbient;
            public int RealRecognitionBeats, RealMuted;
            public int Paths, PathsWithWitness, PathsWithContradiction, PathsWithHeard;
            public int BandMismatch, BandChecked;
            /// Real beats that were pointed while the canned beat at the same
            /// moment was pointed too: both on topic, so the difference is not
            /// visible as topic. Counted because it is the case that works
            /// AGAINST the mechanism and it must not be hidden in a total.
            public int BothPointed, CannedPointedRealNot, RealPointedCannedNot;
            /// SIGHTINGS THE ROSTER COULD NOT HOLD. `Operations.Run` returns a
            /// witness COUNT and the harness draws that many people out of a
            /// four-person street, so a job seen by three produces two
            /// witnesses and one that never existed. Counted because it is a
            /// bias of this study that works in the canned arm's favour and
            /// would otherwise be invisible.
            public int WitnessesWanted, WitnessesFiled;
            /// The lie caught, and the street saying nothing different about
            /// it. The sharpest number in the sweep and it needs both halves.
            public int PathsLieCaught, PathsLieCaughtAndAudible;
        }

        internal static int Sweep()
        {
            var report = new StringBuilder();
            void Say(string s) { Console.WriteLine(s); report.AppendLine(s); }

            Say("QUEUE 119 SWEEP: both arms over the whole single-pass answer space.");
            Say("Every line below is a count with its denominator. No line is a preference.");
            Say("");

            var t = new Tally();
            // distinct spoken tuples per arm per seed, and distinct texts per
            // beat position: this is the responsiveness measure, and it is the
            // one the canned arm cannot move by being retuned.
            var realTuples = new Dictionary<int, HashSet<string>>();
            var cannedTuples = new Dictionary<int, HashSet<string>>();
            var realByBeat = new Dictionary<string, HashSet<string>>();
            var cannedByBeat = new Dictionary<string, HashSet<string>>();
            // one-factor-at-a-time: how often does changing exactly one
            // decision change what the street says.
            string[] dims = { "job", "hour", "approach", "coat", "answer" };
            var flipTotal = new int[5];
            var flipReal = new int[5];
            var flipCanned = new int[5];
            var chains = new List<string>();
            var pathTuples = new Dictionary<int, Dictionary<string, string>>();
            var beatSeen = new Dictionary<string, int>();
            var beatDiffer = new Dictionary<string, int>();

            foreach (int seed in Seeds)
            {
                realTuples[seed] = new HashSet<string>();
                cannedTuples[seed] = new HashSet<string>();
                pathTuples[seed] = new Dictionary<string, string>();

                foreach (var path in AllPaths())
                {
                    var real = PlayScript(path, Arm.Real, seed);
                    var cann = PlayScript(path, Arm.Canned, seed);
                    t.Paths++;

                    if (real.Said.Count != cann.Said.Count)
                    {
                        Say("  INSTRUMENT FAILURE: " + PathName(path) + " spoke "
                            + real.Said.Count + " line(s) real and " + cann.Said.Count + " canned.");
                        return 1;
                    }

                    var tr = real.Log.Trace;
                    t.WitnessesWanted += tr.Witnesses;
                    t.WitnessesFiled += tr.Filed;
                    if (tr.Filed > 0) t.PathsWithWitness++;
                    if (tr.Tick1Contra + tr.Tick2Contra > 0) t.PathsWithContradiction++;
                    if (tr.Heard != "none") t.PathsWithHeard++;

                    var rt = new StringBuilder();
                    var ct = new StringBuilder();
                    for (int i = 0; i < real.Said.Count; i++)
                    {
                        var r = real.Said[i];
                        var c = cann.Said[i];
                        t.Lines++;
                        if (r.Text != c.Text) t.Differ++;
                        Count(r, ref t.RealPointed, ref t.RealChatter, ref t.RealAmbient);
                        Count(c, ref t.CannedPointed, ref t.CannedChatter, ref t.CannedAmbient);
                        if (r.Kind == "pointed" && c.Kind == "pointed") t.BothPointed++;
                        else if (c.Kind == "pointed") t.CannedPointedRealNot++;
                        else if (r.Kind == "pointed") t.RealPointedCannedNot++;

                        if (r.Beat.StartsWith("morning") || r.Beat.StartsWith("passing")
                            || r.Beat.StartsWith("evening"))
                        {
                            t.RealRecognitionBeats++;
                            if (!r.LiveWouldSpeak) t.RealMuted++;
                            // THE MIRROR, CHECKED AGAINST THE LADDER, on every
                            // sample rather than once in a test.
                            t.BandChecked++;
                            var mine = Band(Pressure(r.Suspicion, r.Loyalty, r.Strongest, false), false);
                            var theirs = StreetVoice.Stance(r.Suspicion, r.Loyalty, r.Strongest, false, false);
                            if (mine != theirs) t.BandMismatch++;
                        }

                        string key = i + ":" + r.Beat;
                        Add(realByBeat, key, r.Text);
                        Add(cannedByBeat, key, c.Text);
                        Bump(beatSeen, key);
                        if (r.Text != c.Text) Bump(beatDiffer, key);
                        rt.Append(r.Text).Append(Sep);
                        ct.Append(c.Text).Append(Sep);
                    }
                    realTuples[seed].Add(rt.ToString());
                    cannedTuples[seed].Add(ct.ToString());
                    pathTuples[seed][string.Join(",", path)] = rt.ToString() + Split + ct.ToString();

                    // THE LIE, AND WHETHER IT COST ANYTHING OUT LOUD. Same
                    // path with the truth told instead, same seed: if the two
                    // sessions speak the same five sentences, the lie was
                    // caught in the ledger and nowhere a player can hear.
                    if (path[5] == 1)
                    {
                        t.PathsLieCaught += tr.Tick1Contra + tr.Tick2Contra > 0 ? 1 : 0;
                        var honest = PlayScript(new[] { path[0], path[1], path[2], path[3], 0, 0 }, Arm.Real, seed);
                        string a1 = string.Join("|", real.Said.Select(x => x.Text));
                        string b1 = string.Join("|", honest.Said.Select(x => x.Text));
                        if (tr.Tick1Contra + tr.Tick2Contra > 0 && a1 != b1) t.PathsLieCaughtAndAudible++;
                    }

                    if (seed == Seeds[0]) chains.Add(Chain(path, real));
                }
            }

            // One-factor flips, over every pair of paths differing in exactly
            // one decision. Denominator printed beside every count.
            foreach (int seed in Seeds)
            {
                var all = AllPaths().ToList();
                for (int i = 0; i < all.Count; i++)
                    for (int j = i + 1; j < all.Count; j++)
                    {
                        int d = -1, diffs = 0;
                        for (int k = 0; k < 6; k++)
                            if (all[i][k] != all[j][k]) { diffs++; d = k == 5 ? 4 : k; }
                        if (diffs != 1 || d < 0 || d > 4) continue;
                        var a = pathTuples[seed][string.Join(",", all[i])].Split(Split);
                        var b = pathTuples[seed][string.Join(",", all[j])].Split(Split);
                        flipTotal[d]++;
                        if (a[0] != b[0]) flipReal[d]++;
                        if (a[1] != b[1]) flipCanned[d]++;
                    }
            }

            Say("COVERAGE");
            Say("  paths swept       " + Frac(t.Paths / Seeds.Length, PathCount)
                + " distinct single-pass player paths (3 jobs x 3 hours x 2 approaches x 2 coats x 3 answers)");
            Say("  seeds             " + Seeds.Length + " of " + Seeds.Length
                + " the evening could use (participant*100+run*7, participants 1..3, runs 1..2)");
            Say("  sessions played   " + (t.Paths * 2) + " (" + t.Paths + " per arm)");
            Say("  spoken lines      " + t.Lines + " per-arm-pairs compared, 5 a session");
            Say("  re-plan loop      not a separate world: proven by StudySelftest, not assumed");
            Say("");

            Say("WHERE THE TWO ARMS SAY DIFFERENT WORDS (same seed, so the RNG is held still)");
            Say("  differ            " + Frac(t.Differ, t.Lines) + " spoken lines ("
                + F(100.0 * t.Differ / Math.Max(1, t.Lines)) + " percent, pooled over all seeds)");
            foreach (var k in realByBeat.Keys.OrderBy(x => x))
                Say("    beat " + k.PadRight(22) + " differ " + Frac(Got(beatDiffer, k), Got(beatSeen, k)).PadRight(9)
                    + " real said " + realByBeat[k].Count.ToString().PadLeft(3)
                    + " distinct sentence(s), canned said " + cannedByBeat[k].Count);
            Say("");

            Say("WHAT THE REAL ARM'S LINES ARE ABOUT (denominator " + t.Lines + " lines per arm)");
            Say("  real   pointed    " + Frac(t.RealPointed, t.Lines) + " (a response to something the player did)");
            Say("  real   chatter    " + Frac(t.RealChatter, t.Lines) + " (the plain neighbourly band: weather, the pub, Mickey)");
            Say("  real   ambient    " + Frac(t.RealAmbient, t.Lines) + " (the street's own life, nothing to do with the player)");
            Say("  canned pointed    " + Frac(t.CannedPointed, t.Lines) + " (fixed: it is always on topic, by construction)");
            Say("  canned chatter    " + Frac(t.CannedChatter, t.Lines));
            Say("  canned ambient    " + Frac(t.CannedAmbient, t.Lines));
            Say("  both pointed      " + Frac(t.BothPointed, t.Lines) + " (both on topic at the same moment)");
            Say("  canned on topic, real not  " + Frac(t.CannedPointedRealNot, t.Lines));
            Say("  real on topic, canned not  " + Frac(t.RealPointedCannedNot, t.Lines));
            Say("");

            Say("WHAT THE LIVE GAME WOULD HAVE DONE AT THOSE BEATS");
            Say("  recognition beats " + t.RealRecognitionBeats + " (three a session: Lena twice, one passer-by)");
            Say("  below Comments    " + Frac(t.RealMuted, t.RealRecognitionBeats)
                + " would be SILENT in the build (GossipDirector.TickStances returns before speaking);");
            Say("                    this session substitutes the plain band so the two arms cannot differ by a missing line.");
            Say("");

            Say("HOW MUCH OF WHAT IS SAID DEPENDS ON WHAT THE PLAYER CHOSE");
            for (int d = 0; d < 5; d++)
                Say("  change only the " + dims[d].PadRight(9) + " real " + Frac(flipReal[d], flipTotal[d])
                    + " pair(s) of paths changed what the street says; canned " + Frac(flipCanned[d], flipTotal[d]));
            int rt2 = realTuples.Values.Sum(x => x.Count) / Seeds.Length;
            int ct2 = cannedTuples.Values.Sum(x => x.Count) / Seeds.Length;
            Say("  distinct sessions real " + rt2 + " of " + PathCount + " paths (mean over " + Seeds.Length + " seeds)");
            Say("  distinct sessions canned " + ct2 + " of " + PathCount + " paths (mean over " + Seeds.Length + " seeds)");
            Say("");

            Say("THE CAUSAL CHAIN, PER PATH, SEED " + Seeds[0] + " (real arm; canned has no chain to print)");
            foreach (var c in chains) Say("  " + c);
            Say("");

            Say("INSTRUMENT SELF-CHECK");
            Say("  pressure mirror   " + Frac(t.BandChecked - t.BandMismatch, t.BandChecked)
                + " sample(s) where this file's pressure lands in the band StreetVoice.Stance returned");
            Say("  roster loss       " + Frac(t.WitnessesFiled, t.WitnessesWanted)
                + " of the sightings Operations.Run produced could be given to a real person;"
                + " the rest fell off a four-person street");
            Say("  lie caught, and heard  " + Frac(t.PathsLieCaughtAndAudible, t.PathsLieCaught)
                + " path-seed(s) where the contradiction fired AND the session's five spoken lines"
                + " differ from the same path told truthfully");
            Say("  witness accounting " + Frac(t.PathsWithWitness, t.Paths) + " path-seed(s) filed at least one sighting; "
                + Frac(t.PathsWithHeard, t.Paths) + " had something to overhear; "
                + Frac(t.PathsWithContradiction, t.Paths) + " caught the player in a lie");

            var verdict = "strangerSweep paths=" + (t.Paths / Seeds.Length) + "/" + PathCount
                + " seeds=" + Seeds.Length
                + " lines=" + t.Lines
                + " differ=" + t.Differ + "/" + t.Lines
                + " realPointed=" + t.RealPointed + "/" + t.Lines
                + " realChatter=" + t.RealChatter + "/" + t.Lines
                + " realAmbient=" + t.RealAmbient + "/" + t.Lines
                + " cannedPointed=" + t.CannedPointed + "/" + t.Lines
                + " liveSilent=" + t.RealMuted + "/" + t.RealRecognitionBeats
                + " filedAtLeastOne=" + t.PathsWithWitness + "/" + t.Paths
                + " lieCaught=" + t.PathsWithContradiction + "/" + t.Paths
                + " mirrorOk=" + (t.BandChecked - t.BandMismatch) + "/" + t.BandChecked
                + " rosterKept=" + t.WitnessesFiled + "/" + t.WitnessesWanted
                + " lieHeard=" + t.PathsLieCaughtAndAudible + "/" + t.PathsLieCaught
                + " atUtc=" + Stamp();
            Say("");
            Say(verdict);

            Write("study-sweep.txt", report.ToString());
            Append("study.txt", verdict + "\n");
            return t.BandMismatch == 0 ? 0 : 1;
        }

        static void Count(Said s, ref int pointed, ref int chatter, ref int ambient)
        {
            if (s.Kind == "pointed") pointed++;
            else if (s.Kind == "ambient") ambient++;
            else chatter++;
        }

        static void Bump(Dictionary<string, int> d, string k) =>
            d[k] = d.TryGetValue(k, out var n) ? n + 1 : 1;

        static int Got(Dictionary<string, int> d, string k) => d.TryGetValue(k, out var n) ? n : 0;

        static void Add(Dictionary<string, HashSet<string>> d, string k, string v)
        {
            if (!d.TryGetValue(k, out var set)) d[k] = set = new HashSet<string>();
            set.Add(v);
        }

        /// One path's chain in one line: what was seen, who filed it, where it
        /// went, what it collided with, and what that left Lena standing at.
        /// Everything here is a number the run produced, not a re-derivation.
        static string Chain(int[] path, Run real)
        {
            var tr = real.Log.Trace;
            var lena = real.Said.LastOrDefault(s => s.Speaker == "Lena");
            double p = lena != null ? Pressure(lena.Suspicion, lena.Loyalty, lena.Strongest, false) : 0;
            return PathName(path).PadRight(34)
                + " saw=" + tr.Witnesses + " awake=" + tr.Awake + "/4 filed=" + tr.Filed
                + "@" + F2(tr.FiledConfidence)
                + " claim=" + tr.ClaimValue + "/" + tr.Verdict
                + " moved=" + tr.Heard + "@" + F(tr.HeardConfidence) + "/hop" + tr.HeardHops
                + " contra=" + (tr.Tick1Contra + tr.Tick2Contra)
                + " susp=" + F(tr.LenaSuspicion)
                + " pressure=" + F(p)
                + " stance=" + (lena != null ? lena.Stance.ToString() : "none")
                + " lastLine=" + (lena != null ? lena.Kind : "none");
        }

        // ---------------------------------------------------------------
        // PART TWO: the pressure curve, and the three comparisons
        // ---------------------------------------------------------------

        /// A multi-day scenario the one-crime session cannot express.
        ///
        /// THIS IS THE ONE PLACE THE STUDY RE-IMPLEMENTS ANYTHING, and it is
        /// unavoidable: `Play` is a fixed beat sheet with one crime in it. Every
        /// call below is the same Core call `Play` makes, in the same order,
        /// with the constants quoted from it. The guard on the copy is that its
        /// FIRST DAY must reproduce the swept session's numbers exactly for the
        /// same path, checked in `StudySelftest`; if the copy drifts, that check
        /// goes red before any curve is believed.
        internal class Days
        {
            public World W;
            public bool Aging;          // call GossipMill.Age hourly, as GameController does
            public GameTime Clock;
            public int Crimes;
            /// Game minutes from the first sighting to the first mill event that
            /// carried a rumour about the player between two people. This is the
            /// gossip channel's time-to-audible, and it does not use the ladder.
            public double MinutesToFirstTalk = -1;
            public GameTime FirstSighting;
            public bool Sighted;
            public readonly List<string> Rows = new List<string>();

            public Days(bool aging)
            {
                W = BuildWorld();
                Aging = aging;
                Clock = new GameTime(2, 8, 0);
                if (aging) W.Mill.Age(Clock);   // the baseline call; it moves nothing
            }

            /// Advance to a stamp, ageing ONCE PER GAME HOUR AT THE HOUR
            /// BOUNDARY, which is what `GameController.Update` does:
            ///
            ///     if (Now.Hour != _lastAgedHour) { _lastAgedHour = Now.Hour; _gossip?.Mill?.Age(Now); }
            ///
            /// The first draft of this method aged on every call, which is
            /// every gossip round, and that is 10 times the build's rate. It
            /// mattered: `Age` is the only thing that moves a stored rumour, and
            /// the number of times it moves is the number of chances the
            /// re-tell guard gets to open. An instrument that ages faster than
            /// the game reports a street that talks faster than the game.
            public void To(GameTime when)
            {
                if (!Aging) { Clock = when; return; }
                long next = (Clock.TotalMinutes / 60 + 1) * 60;
                while (next <= when.TotalMinutes)
                {
                    W.Mill.Age(GameTime.FromTotalMinutes(next));
                    next += 60;
                }
                Clock = when;
            }

            /// One night's work, wired exactly as `Play` and `OperationHost.RunPlan`
            /// wire it. `hour`, `forced` and `coat` are the player's behaviour and
            /// are held constant across the curve.
            public OperationOutcome Night(int day, string targetId, int hour, bool forced, bool coat)
            {
                var when = new GameTime(day, hour, 0);
                To(when);
                // A FRESH TARGET EACH NIGHT, and it is an assumption with a
                // cost. `Operations.Run` sets `Done` on any job that pays, so
                // the shipped board holds exactly three crimes; a curve over ten
                // needs a supply of comparable work the current build does not
                // have. Rebuilding the list models "another job of the same
                // kind" and removes both the exhaustion and the +0.08 difficulty
                // a failure leaves behind. Named here and in the report.
                var target = OperationSetup.Build().First(x => x.Id == targetId);
                var plan = new OperationPlan(target.Id) { Hour = hour, Approach = forced ? Approach.Forced : Approach.Quiet };
                // Quoted from Play: a player who has done no jobs starts at 0.35
                // and heat is what the street says, which this harness never
                // raises. The live `OperationHost.BuildOperationState` would
                // raise Nerve by 0.05 a job and Heat with the talk, both of which
                // this curve holds still.
                var state = new OperationState { Nerve = 0.35, Heat = 0.0, Coated = coat };
                var rng = new Random(day * 7919 + hour * 31 + target.Id.Length);
                var outcome = Operations.Run(plan, target, state, () => rng.NextDouble());

                var fact = new Fact("player", "job_d" + day + "_" + target.Id, "seen");
                string summary = "somebody was at " + target.Name + " in the small hours, and it was not nothing";
                var awake = W.Mill.Agents.Where(a => a.Circle != "day" || hour >= 8 && hour < 20).ToList();
                var pool = awake.Take(outcome.Witnesses).ToList();
                foreach (var a in pool)
                    W.Mill.Witness(a.Id, fact, summary, sensitive: true, now: when,
                        confidence: coat ? 0.55 : 0.9);
                if (pool.Count > 0 && !Sighted) { Sighted = true; FirstSighting = when; }
                Crimes++;
                LastFact = fact;
                return outcome;
            }

            public Fact LastFact;

            /// The morning after: she asks, the player answers, and the answer
            /// goes on the record before the street moves. Same order as
            /// `Play` and `LawHost`.
            public void Morning(int day, int said)
            {
                var when = new GameTime(day, 9, 0);
                To(when);
                if (said == 2 || LastFact == null) return;   // silence files nothing
                var claim = new Fact("player", LastFact.Predicate, said == 0 ? "seen" : "home");
                Claims.Process(W.Lena.Knowledge, W.Lena.Suspicion, W.Lena.Memory, claim, when);
                W.Mill.PlayerClaims("Lena", claim, when);
            }

            /// One gossip round at a stamp, with the same unrestricted
            /// `together` the harness uses. Records the first moment a rumour
            /// about the player passed between two people.
            public List<GossipEvent> Tick(GameTime when)
            {
                To(when);
                var events = W.Mill.Tick(when);
                if (MinutesToFirstTalk < 0 && Sighted)
                {
                    var mine = events.FirstOrDefault(e => e.Rumor != null && e.Rumor.Content.Subject == "player");
                    if (mine != null) MinutesToFirstTalk = when.TotalMinutes - FirstSighting.TotalMinutes;
                }
                return events;
            }

            /// Where Lena stands right now, read the way `Passing` reads it.
            public (double susp, double strongest, double pressure, StanceKind stance) Lena()
            {
                var about = W.Lena.G.Rumors.Where(r => r.Content.Subject == "player")
                    .OrderByDescending(r => r.Confidence).FirstOrDefault();
                double strongest = about != null ? about.Confidence : 0.0;
                double susp = W.Lena.Suspicion.Value;
                return (susp, strongest, Pressure(susp, W.Lena.G.Loyalty, strongest, false),
                    StreetVoice.Stance(susp, W.Lena.G.Loyalty, strongest, false, false));
            }
        }

        internal static int Curve()
        {
            var report = new StringBuilder();
            void Say(string s) { Console.WriteLine(s); report.AppendLine(s); }

            Say("QUEUE 119 PART TWO: what pressure does over crimes and over days.");
            Say("Player behaviour held constant: the customs shed, eleven at night, straight through the door,");
            Say("no coat, and a lie the next morning. That is the loudest single night the session offers.");
            Say("Lena's loyalty is 0.5, so the ladder's loyalty discount is exactly zero for her.");
            Say("");

            int mismatches = 0, checks = 0;
            // Carried out of the blocks below so the verdict row is built from
            // the same numbers the prose printed, not from a second pass.
            int crossNoDecay = -1, crossWithDecay = -1, liveContra = 0, livePlayerEvents = 0;
            double oneCrimeLie = 0, firstTalkMinutes = -1;
            string Row(Days d, string label)
            {
                var l = d.Lena();
                checks++;
                if (Band(l.pressure, false) != l.stance) mismatches++;
                return "  " + label.PadRight(30)
                    + " crimes=" + d.Crimes
                    + " susp=" + F(l.susp)
                    + " strongest=" + F(l.strongest)
                    + " pressure=" + F(l.pressure)
                    + " (" + (l.pressure >= CommentsAt ? "AT-OR-OVER" : "under") + " " + F2(CommentsAt) + ")"
                    + " stance=" + l.stance;
            }

            // ---- A: one crime, the session's own span ----
            Say("A. ONE CRIME, the span the shipped session covers (night of day 2 to the evening of day 3).");
            foreach (bool aging in new[] { false, true })
            {
                var d = new Days(aging);
                var oc = d.Night(2, "customs_run", 23, forced: true, coat: false);
                Say("  " + (aging ? "with decay   " : "no decay     ")
                    + " Operations.Run: success=" + oc.Success + " partial=" + oc.Partial
                    + " witnesses=" + oc.Witnesses + " filed=" + Math.Min(oc.Witnesses, 2) + "/2-awake");
                d.Morning(3, 1);
                d.Tick(new GameTime(3, 10, 30));
                Say(Row(d, (aging ? "with decay" : "no decay") + ", after tick 1"));
                d.Tick(new GameTime(3, 17, 0));
                Say(Row(d, (aging ? "with decay" : "no decay") + ", after tick 2"));
                Say("  " + (aging ? "with decay" : "no decay") + ", first talk about the player: "
                    + (d.MinutesToFirstTalk < 0 ? "never (nothing propagated)"
                       : F(d.MinutesToFirstTalk) + " game minutes after the sighting, at the harness's 2-ticks-a-day cadence"));
            }
            Say("");

            // ---- B: one crime, then time ----
            Say("B. ONE CRIME, THEN TIME. No further crimes. Ten days, decay on, ticking twice a day.");
            Say("   RumorHalfLifeHours is 96, so this is the 'lie low' path and it is meant to go quiet.");
            {
                var d = new Days(aging: true);
                d.Night(2, "customs_run", 23, forced: true, coat: false);
                d.Morning(3, 1);
                for (int day = 3; day <= 12; day++)
                {
                    d.Tick(new GameTime(day, 10, 30));
                    d.Tick(new GameTime(day, 17, 0));
                    Say(Row(d, "day " + day));
                }
            }
            Say("");

            // ---- C: many crimes over days ----
            Say("C. MANY CRIMES OVER DAYS. One a night, same behaviour, lying every morning.");
            foreach (bool aging in new[] { false, true })
            {
                Say("  " + (aging ? "WITH decay (as GameController ages the mill hourly)" : "NO decay (as the shipped session does: it never calls Age)"));
                var d = new Days(aging);
                int crossed = -1;
                for (int n = 1; n <= 10; n++)
                {
                    int night = 1 + n;
                    d.Night(night, "customs_run", 23, forced: true, coat: false);
                    d.Morning(night + 1, 1);
                    d.Tick(new GameTime(night + 1, 10, 30));
                    d.Tick(new GameTime(night + 1, 17, 0));
                    var l = d.Lena();
                    Say(Row(d, "crime " + n + " (night of day " + night + ")"));
                    if (crossed < 0 && l.pressure >= CommentsAt) crossed = n;
                    if (n == 1 && !aging) oneCrimeLie = l.pressure;
                }
                if (aging) crossWithDecay = crossed; else crossNoDecay = crossed;
                Say("  " + (aging ? "with decay" : "no decay") + ": crossed " + F2(CommentsAt)
                    + (crossed < 0 ? " never, over 10 crime(s)"
                       : " on crime " + crossed + " of 10, which is the morning of day " + (2 + crossed)));
            }
            Say("");

            // ---- D: the clock the game actually runs on ----
            //
            // GAME TIME IS NOT PLAY TIME AND THE DIFFERENCE IS THE WHOLE OF
            // MERIDIAN CLAUSE 2. `GameController.MinutesPerRealSecond` is 2, so
            // one game day is twelve real minutes and thirty real minutes at the
            // controls is 3600 game minutes, two and a half game days.
            // `GossipDirector.TickIntervalGameMinutes` is 6, so the mill runs
            // 600 times in that window rather than the twice a day the session
            // schedules. This is the same one crime, ticked at the build's own
            // cadence.
            Say("D. THE BUILD'S OWN CLOCK. MinutesPerRealSecond=2 and TickIntervalGameMinutes=6,");
            Say("   so thirty real minutes of play is " + PlayWindowGameMinutes + " game minutes ("
                + F(PlayWindowGameMinutes / 1440.0) + " game days) and " + (PlayWindowGameMinutes / 6) + " gossip rounds.");
            // BOTH WAYS, BECAUSE THE FIRST RUN OF THIS BLOCK WAS A SURPRISE.
            // One crime drove Lena to suspicion 1.000 inside the window, which
            // no reading of the code predicts: the re-tell guard in
            // `GossipMill.Tick` is supposed to refuse a story the listener
            // already holds at least as strongly. Decay is the only thing that
            // separates this from comparison A, so it is the variable, and the
            // run with it off is the control.
            foreach (bool aging in new[] { true, false })
            {
                var d = new Days(aging);
                d.Night(2, "customs_run", 23, forced: true, coat: false);
                var start = new GameTime(2, 23, 0);
                int playerEvents = 0, rounds = 0;
                double firstAt = -1, lastAt = -1;
                var when = start;
                bool claimed = false;
                var trail = new List<string>();
                int contradictions = 0;
                for (int m = 6; m <= PlayWindowGameMinutes; m += 6)
                {
                    when = start.AddMinutes(m);
                    // She asks the morning after, at nine, wherever that falls
                    // in the window. The lie has to be on the record before the
                    // street moves or there is nothing for it to collide with.
                    if (!claimed && when.Hour >= 9 && when.Day > 2) { d.Morning(when.Day, 1); claimed = true; }
                    var ev = d.Tick(when);
                    rounds++;
                    int mine = ev.Count(e => e.Rumor != null && e.Rumor.Content.Subject == "player");
                    contradictions += ev.Count(e => e.Contradiction);
                    if (mine > 0)
                    {
                        playerEvents += mine;
                        if (firstAt < 0) firstAt = when.TotalMinutes - start.TotalMinutes;
                        lastAt = when.TotalMinutes - start.TotalMinutes;
                        // THE SERIES, PRINTED, because the first run of this
                        // block reported one crime driving Lena to suspicion
                        // 1.000 and a total is not an explanation. Every event
                        // that carried the player's name, with who told whom, at
                        // what confidence, and what it did to her.
                        foreach (var e in ev.Where(x => x.Rumor != null && x.Rumor.Content.Subject == "player"))
                            trail.Add("    " + when + " " + e.FromId + "->" + e.ToId
                                + " conf=" + F(e.Rumor.Confidence) + " hop=" + e.Rumor.Hops
                                + (e.Contradiction ? " CONTRADICTION" : e.Exposure ? " exposure" : "")
                                + " lenaSusp=" + F(d.W.Lena.Suspicion.Value));
                    }
                }
                Say("  " + (aging ? "WITH decay" : "NO decay") + ":");
                Say("  rounds ticked     " + rounds + " of " + (PlayWindowGameMinutes / 6) + " in the window");
                Say("  talk about the player " + playerEvents + " event(s) in " + rounds + " round(s)");
                Say("  first at          " + (firstAt < 0 ? "never" : F(firstAt) + " game minutes after the sighting = "
                    + F(firstAt / 120.0) + " real minutes at MinutesPerRealSecond=2"));
                Say("  last at           " + (lastAt < 0 ? "never" : F(lastAt) + " game minutes = "
                    + F(lastAt / 120.0) + " real minutes; after that every listener already holds it and the re-tell guard blocks"));
                // THE LIE, AT THE BUILD'S OWN CADENCE. `GossipMill.Tick` raises
                // suspicion for a contradiction only when a rumour ARRIVES at
                // somebody who was already told otherwise, and a heard rumour
                // never enters `KnowledgeBase` (only `Witness` at 0.95 and up
                // does that), so `Claims.Process` at the moment of the lie sees
                // Unknown. If the street moves before she asks, there is no
                // second arrival and the lie is never caught by anything.
                if (aging) { liveContra = contradictions; livePlayerEvents = playerEvents; firstTalkMinutes = firstAt; }
                Say("  contradictions    " + Frac(contradictions, playerEvents)
                    + " of the player-events collided with the lie the player told at nine");
                Say("  every event that carried the player's name, in order:");
                foreach (var line in trail) Say(line);
                if (trail.Count == 0) Say("    none in " + rounds + " round(s)");
                Say(Row(d, "end of the 30-real-minute window"));
            }
            Say("");

            // ---- why D and A disagree, isolated to arithmetic ----
            //
            // THIS IS A DEFECT IN THE MILL AND NOT A PROPERTY OF THE DESIGN, so
            // it is named here rather than folded into a curve. `Tick` refuses
            // to re-tell when `existing.Confidence >= passed`, and `passed` is
            // `r.Confidence * tie * HopDecay`. After `Age` has multiplied both
            // the teller's copy and the listener's copy by the same factor, the
            // two sides of that comparison are the same real number reached by
            // different multiplication orders, so they differ in the last bit.
            // Whenever the new one lands one bit HIGH the guard opens, the same
            // story is filed again, and if it contradicts a claim the listener
            // takes another 0.35 * confidence of suspicion.
            //
            // NOTHING IS CHANGED HERE. The brief forbids tuning and this is
            // somebody else's fix; it goes to the queue with a name.
            Say("WHY D AND A DISAGREE: the re-tell guard against floating point, in isolation.");
            // EVERY TIE IN THE GRAPH AND NOT ONE, because the first version of
            // this probe modelled Rocco-to-Lena at 0.7, found nothing, and sat
            // beside a live run in which three re-tells had plainly happened on
            // a different edge. Which pair leaks is a property of where the two
            // roundings fall, so the probe has to walk the same weights
            // `BuildWorld` links.
            {
                double[] ties = { 0.5, 0.6, 0.7, 0.8 };
                int steps = 10 * PlayWindowGameMinutes / 60;   // ten days of hourly ageing
                double f = Math.Pow(0.5, 1.0 / 96.0);
                foreach (var tie in ties)
                {
                    double held = 0.9 * tie * 0.8, src = 0.9;
                    int leaks = 0;
                    for (int i = 0; i < steps; i++)
                    {
                        src *= f; held *= f;
                        double passed = src * tie * 0.8;
                        if (passed > held) { leaks++; held = passed; }
                    }
                    Say("  tie " + F2(tie) + "          guard opened " + Frac(leaks, steps)
                        + " hourly Age step(s), on two numbers equal in exact arithmetic");
                }
                Say("  the gap is one bit: 2.22e-16 at these magnitudes, and the guard is a >= on doubles.");
            }
            Say("");

            Say("INSTRUMENT SELF-CHECK");
            Say("  pressure mirror   " + Frac(checks - mismatches, checks)
                + " row(s) where this file's pressure lands in the band StreetVoice.Stance returned");

            // ONE ROW, so a later session can see this ran without reading the
            // prose. `crossAt` is the crime number at which Lena's pressure
            // first reached the Comments rung, out of the ten crimes walked;
            // `firstTalk` is game minutes from the sighting to the first mill
            // event carrying the player's name at the build's own tick rate.
            var verdict = "strangerCurve crimesWalked=10"
                + " crossNoDecay=" + (crossNoDecay < 0 ? "never" : crossNoDecay.ToString(CultureInfo.InvariantCulture)) + "/10"
                + " crossWithDecay=" + (crossWithDecay < 0 ? "never" : crossWithDecay.ToString(CultureInfo.InvariantCulture)) + "/10"
                + " oneCrimePressureLie=" + F(oneCrimeLie)
                + " commentsAt=" + F2(CommentsAt)
                + " firstTalkGameMinutes=" + F(firstTalkMinutes)
                + " playWindowGameMinutes=" + PlayWindowGameMinutes
                + " lieCaughtAtLiveCadence=" + liveContra + "/" + livePlayerEvents
                + " mirrorOk=" + (checks - mismatches) + "/" + checks
                + " atUtc=" + Stamp();
            Say("");
            Say(verdict);

            Write("study-curve.txt", report.ToString());
            Append("study.txt", verdict + "\n");
            return mismatches == 0 ? 0 : 1;
        }

        // ---------------------------------------------------------------
        // the study's own selftest, accepting case first
        // ---------------------------------------------------------------

        /// THE THREE THINGS THE STUDY WOULD BE WRONG ABOUT IF THEY WERE WRONG.
        ///
        /// One: the pressure mirror agrees with the shipped ladder, including
        /// at the rung boundaries, and DISAGREES when the ladder is fed a
        /// different number, so the check can fail.
        /// Two: a re-plan produces the same world as its single-pass twin, which
        /// is what makes 108 the whole space rather than a sample of it.
        /// Three: the multi-day copy reproduces the shipped session's first day.
        internal static int StudySelftest()
        {
            int passed = 0, failed = 0;
            void Ok(string s) { passed++; Console.WriteLine("  PASS  " + s); }
            void No(string s) { failed++; Console.WriteLine("  FAIL  " + s); }

            // 1. the mirror, on every rung boundary and just under each.
            double[] probes = { 0.0, 0.119, 0.12, 0.259, 0.26, 0.419, 0.42, 0.579, 0.58, 0.719, 0.72, 0.859, 0.86, 1.0 };
            int agree = 0;
            foreach (var p in probes)
            {
                // Fed straight in as `strongest` with suspicion 0 and loyalty
                // 0.5, so pressure is 0.45*p and the ladder is exercised through
                // its own arithmetic rather than around it.
                double mine = Pressure(0.0, 0.5, p, false);
                if (Band(mine, false) == StreetVoice.Stance(0.0, 0.5, p, false, false)) agree++;
            }
            if (agree == probes.Length) Ok("pressure mirror agrees with StreetVoice.Stance on " + agree + "/" + probes.Length + " rung probes");
            else No("pressure mirror disagrees on " + (probes.Length - agree) + "/" + probes.Length + " rung probes");

            // THE REJECTING CASE. A mirror that cannot fail is a ratchet, so
            // shift it by one band and require the comparison to catch it.
            if (Band(Pressure(0.0, 0.5, 1.0, false) - 0.5, false) != StreetVoice.Stance(0.0, 0.5, 1.0, false, false))
                Ok("planted mirror error: caught (a pressure shifted half a scale changes band)");
            else No("planted mirror error: NOT caught, the mirror check is blind");

            // 2. the re-plan claim: 108 is the whole world space.
            //    Single pass: warehouse / 3am / quiet / coat / silent.
            //    Two passes: the first plan is loud and coatless and is thrown
            //    away, the second is identical to the single pass.
            var once = PlayScript(new[] { 2, 2, 0, 0, 0, 2 }, Arm.Real, 107);
            var twice = PlayScript(new[] { 2, 0, 1, 1, 1, 2, 2, 0, 0, 2 }, Arm.Real, 107);
            var a = string.Join("|", once.Said.Select(s => s.Speaker + ":" + s.Text));
            var b = string.Join("|", twice.Said.Select(s => s.Speaker + ":" + s.Text));
            if (a == b && once.Said.Count == 5)
                Ok("a re-plan is not a different world: " + once.Said.Count + " spoken line(s), identical to the single-pass twin");
            else
                No("a re-plan changed the world: " + once.Said.Count + " line(s) against " + twice.Said.Count + ", texts " + (a == b ? "same" : "differ"));

            // 3. the multi-day copy against the shipped session, same path.
            //    loud/nocoat/lie on the customs shed at eleven, which is
            //    path {0,0,1,1,0,1} in the session's own answer numbering.
            var session = PlayScript(new[] { 0, 0, 1, 1, 0, 1 }, Arm.Real, 107);
            var days = new Days(aging: false);
            days.Night(2, "customs_run", 23, forced: true, coat: false);
            days.Morning(3, 1);
            days.Tick(new GameTime(3, 10, 30));
            days.Tick(new GameTime(3, 17, 0));
            var l = days.Lena();
            var lastLena = session.Said.Last(s => s.Speaker == "Lena");
            bool same = Math.Abs(l.susp - lastLena.Suspicion) < 1e-9
                        && Math.Abs(l.strongest - lastLena.Strongest) < 1e-9;
            if (same)
                Ok("the multi-day copy reproduces the shipped session's day one: suspicion " + F(l.susp)
                   + ", strongest rumour " + F(l.strongest));
            else
                No("the multi-day copy DRIFTED from the shipped session: copy susp=" + F(l.susp)
                   + " strongest=" + F(l.strongest) + "; session susp=" + F(lastLena.Suspicion)
                   + " strongest=" + F(lastLena.Strongest));

            // 4. the arithmetic the report quotes, against the code, so the
            //    author's stated numbers are checked rather than repeated.
            //    0.9 witnessed, tie 0.7 to Lena, HopDecay 0.8.
            double arrival = 0.9 * 0.7 * 0.8, arrivalCoat = 0.55 * 0.7 * 0.8;
            double lie = Pressure(0.35 * arrival, 0.5, arrival, false);
            double truth = Pressure(0.12 * arrival, 0.5, arrival, false);
            Console.WriteLine("  NOTE  arrival " + F(arrival) + " nocoat / " + F(arrivalCoat) + " coat;"
                + " one-crime pressure lie " + F(lie) + " truth " + F(truth)
                + "; the file's 0.326 uses the DISPLAYED suspicion 0.18 and not the stored "
                + (0.35 * arrival).ToString("0.0000", CultureInfo.InvariantCulture));

            // 5. no spaces inside a key=value value, which every reader splits on.
            var probe = Frac(3, 108) + "|" + PathName(new[] { 0, 1, 1, 0, 0, 2 });
            if (!probe.Contains(" ")) Ok("instrument values carry no spaces (" + probe + ")");
            else No("an instrument value contains a space: " + probe);

            Console.WriteLine("study selftest: " + passed + " passed, " + failed + " failed ("
                + probes.Length + " rung probe(s), 1 planted error, 1 re-plan twin, 1 day-one cross-check)");
            return failed == 0 ? 0 : 1;
        }

        // ---------------------------------------------------------------

        /// The same stamp format the session's own `WriteRecord` uses, so a
        /// reader can put a study row and a session row in one sort. Rows
        /// accumulate; without this a re-run of the tool appends a second row
        /// under the same key and nothing says which is the newer.
        static string Stamp() =>
            DateTime.UtcNow.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture);

        static void Write(string name, string body)
        {
            var root = RepoRoot();
            if (root == null) return;
            var dir = Path.Combine(root, "production", "stranger-test");
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, name), body);
        }

        static void Append(string name, string body)
        {
            var root = RepoRoot();
            if (root == null) return;
            var dir = Path.Combine(root, "production", "stranger-test");
            Directory.CreateDirectory(dir);
            File.AppendAllText(Path.Combine(dir, name), body);
        }
    }
}
