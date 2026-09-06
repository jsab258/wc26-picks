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
    /// QUEUE 119: CAN THREE STRANGERS TELL THE DIFFERENCE.
    ///
    /// One crime and its aftermath, played twice by the same person over two
    /// runs, with one thing changed between them and nothing else. The reading
    /// is what the person says afterwards, not anything this program measures,
    /// so nothing here scores the session and nothing is printed to the player
    /// that names a system.
    ///
    /// WHAT IS NEW HERE AND WHAT IS NOT. Nothing in this file decides anything
    /// about the world. The crime is `OperationSetup.Build()` and
    /// `Operations.Read` / `Operations.Run`; who saw it and who tells whom is
    /// `GossipMill`; every sentence anybody speaks comes out of
    /// `StreetVoice`'s banks; the lie is caught by `Claims.Process`; the cast
    /// are `LenaSetup` and `CastSetup`. This file is the console, the order of
    /// the beats, and the ONE switch the experiment turns.
    ///
    /// THE SWITCH. `--arm real` runs the paragraph above. `--arm canned`
    /// replaces the state those systems read with a fixed script: nobody
    /// perceives, nobody remembers, nobody passes anything to anybody, and
    /// what the player says is not checked against anything. Every renderer,
    /// every bank, every prompt and every beat is the same object in both, so
    /// the two runs cannot differ in shape, only in whether the world had a
    /// reason for what it said.
    ///
    /// THE CANNED ARM IS NOT A STRAW ARM AND THAT IS THE WHOLE DESIGN. It gets
    /// mission-level knowledge, which is what a scripted game has: it knows
    /// which job the player took and how it went, and it fires a pointed line
    /// about it. What it does not have is perception (it does not know whether
    /// anybody was there to see), memory (it does not know what the player
    /// said an hour ago), or propagation (nobody tells anybody anything). A
    /// careful player who was seen by nobody will hear the canned street talk
    /// about them and the real street say nothing, and that is left in.
    ///
    /// THE OTHER HALF OF THIS CLASS IS `Sweep.cs`, added 2026-09-06 when Jafar
    /// ruled that the evening waits for a visual build and the studio runs the
    /// comparison itself. It plays this session over the whole answer space and
    /// counts what is countable; it reports no preference, because a preference
    /// is the one reading only a person can give. Everything it touches here is
    /// a record: `Log.Said`, `Log.Trace` and the accessibility to reach `Play`.
    /// The beat-identity selftest is the guard that the record changed nothing.
    static partial class Program
    {
        // ---------------------------------------------------------------
        // the two arms
        // ---------------------------------------------------------------

        internal enum Arm { Real, Canned }

        /// WHICH ARM EACH PARTICIPANT GETS FIRST. Order varies because
        /// whichever run comes second benefits from already knowing the
        /// controls, and with three people that benefit cannot be split
        /// evenly. It falls 2:1 toward CANNED being second, which is the
        /// direction that works against the result this project would prefer.
        static readonly Arm[][] Assignment =
        {
            new[] { Arm.Real, Arm.Canned },     // participant 1
            new[] { Arm.Canned, Arm.Real },     // participant 2
            new[] { Arm.Real, Arm.Canned },     // participant 3
        };

        // ---------------------------------------------------------------
        // the console, behind an interface so the selftest can drive it
        // ---------------------------------------------------------------

        /// Everything the session can do to a person. Two implementations: the
        /// real console, and a scripted one that answers from a list and keeps
        /// the transcript, so both arms can be played headlessly and compared.
        internal interface IUi
        {
            void Show(string block);
            int Ask(string question, string[] options);
            void Pause();
        }

        class ConsoleUi : IUi
        {
            public void Show(string block)
            {
                Console.WriteLine();
                Console.WriteLine(block);
            }

            public int Ask(string question, string[] options)
            {
                Console.WriteLine();
                Console.WriteLine(question);
                Console.WriteLine();
                for (int i = 0; i < options.Length; i++)
                    Console.WriteLine("  " + (i + 1) + ")  " + options[i]);
                while (true)
                {
                    Console.WriteLine();
                    Console.Write("  > ");
                    var typed = Console.ReadLine();
                    if (typed == null) return 0;           // a closed pipe is not an answer
                    int n;
                    if (int.TryParse(typed.Trim(), out n) && n >= 1 && n <= options.Length)
                        return n - 1;
                    // NO SYSTEM WORDS ON A MISTYPE. A stranger who types "y"
                    // must not be told about parsing.
                    Console.WriteLine("  (a number from the list)");
                }
            }

            public void Pause()
            {
                Console.WriteLine();
                Console.Write("  press return ");
                Console.ReadLine();
                Console.WriteLine();
            }
        }

        /// The selftest's player. Answers from a fixed list and records every
        /// call, so the shape of a run is a value that can be compared.
        internal class ScriptedUi : IUi
        {
            readonly int[] _answers;
            int _next;
            public readonly List<string> Shape = new List<string>();
            public readonly List<string> Text = new List<string>();

            public ScriptedUi(int[] answers) { _answers = answers; }

            public void Show(string block) { Shape.Add("show"); Text.Add(block); }

            public int Ask(string question, string[] options)
            {
                // THE QUESTION AND THE OPTIONS ARE PART OF THE SHAPE, not of
                // the text: if one arm ever offers a different choice, the two
                // runs stop being the same game and the comparison is
                // measuring the menu.
                Shape.Add("ask:" + question + "|" + string.Join("|", options));
                int a = _next < _answers.Length ? _answers[_next] : 0;
                _next++;
                return a >= 0 && a < options.Length ? a : 0;
            }

            public void Pause() { Shape.Add("pause"); }
        }

        // ---------------------------------------------------------------
        // the world, built the same way in both arms
        // ---------------------------------------------------------------

        /// One person's social side. The same four objects the game gives a
        /// character: what they remember, what they know, how they feel about
        /// the player, and their place in the mill.
        internal class Person
        {
            public string Name;
            public MemoryStore Memory;
            public KnowledgeBase Knowledge;
            public SuspicionTracker Suspicion;
            public Gossiper G;
        }

        static Person Cast(string name, string circle, double greed, double nerve, double loyalty)
        {
            var p = new Person
            {
                Name = name,
                Memory = new MemoryStore(name),
                Knowledge = new KnowledgeBase(),
                Suspicion = new SuspicionTracker(),
            };
            p.G = new Gossiper(name, name, p.Memory, p.Knowledge, p.Suspicion, circle, greed, nerve, loyalty);
            return p;
        }

        internal class World
        {
            public GossipMill Mill;
            public Person Lena, Rocco, Ada, Sam;
        }

        internal static World BuildWorld()
        {
            var w = new World();
            // Lena's dispositions are quoted from GossipDirector.cs, which
            // builds her the same way for the live game: "the guarded
            // bookkeeper, near-unbuyable, hard to rattle".
            w.Lena = Cast("Lena", "day", 0.25, 0.75, 0.5);
            LenaSetup.SeedMemories(w.Lena.Memory);
            LenaSetup.SeedKnowledge(w.Lena.Knowledge);

            foreach (var name in new[] { "Rocco", "Ada", "Sam" })
            {
                var m = CastSetup.Get(name);
                var p = Cast(name, m.Circle, m.Greed, m.Nerve, m.Loyalty);
                if (name == "Rocco") w.Rocco = p;
                else if (name == "Ada") w.Ada = p;
                else w.Sam = p;
            }

            // The five ties between these four, weights quoted from
            // GossipDirector.cs:125-129 rather than chosen here. Rocco and
            // Sam are the strongest pair on the street and Rocco is the one
            // who is out at night, which is why a night job reaches the
            // daytime world through him.
            var graph = new SocialGraph();
            graph.Link("Rocco", "Lena", 0.7);
            graph.Link("Rocco", "Sam", 0.8);
            graph.Link("Sam", "Lena", 0.6);
            graph.Link("Ada", "Lena", 0.6);
            graph.Link("Ada", "Sam", 0.5);

            w.Mill = new GossipMill(graph);
            w.Mill.Add(w.Lena.G);
            w.Mill.Add(w.Rocco.G);
            w.Mill.Add(w.Ada.G);
            w.Mill.Add(w.Sam.G);
            return w;
        }

        // ---------------------------------------------------------------
        // presentation, identical in both arms
        // ---------------------------------------------------------------

        const string Rule = "  ------------------------------------------------------------";

        static string Speech(string who, string line) =>
            "  " + who.ToUpperInvariant() + "\n  \"" + line + "\"";

        static string Wrap(string s, int width = 68)
        {
            var outp = new StringBuilder();
            foreach (var para in s.Split('\n'))
            {
                if (para.Length == 0) { outp.AppendLine(); continue; }
                int col = 0;
                outp.Append("  ");
                foreach (var word in para.Split(' '))
                {
                    if (col > 0 && col + word.Length + 1 > width)
                    {
                        outp.Append("\n  ");
                        col = 0;
                    }
                    if (col > 0) { outp.Append(' '); col++; }
                    outp.Append(word);
                    col += word.Length;
                }
                outp.AppendLine();
            }
            return outp.ToString().TrimEnd('\n');
        }

        // ---------------------------------------------------------------
        // the session
        // ---------------------------------------------------------------

        /// What the run wrote down for the operator. Never shown to the player
        /// and never a score: it is the transcript and the one line that lets
        /// a later session prove this ran at all.
        internal class Log
        {
            public readonly List<string> Lines = new List<string>();
            public string Choices = "";
            public int Spoken;
            public void Add(string s) { Lines.Add(s); }

            /// EVERY SPOKEN LINE WITH THE STATE THAT JUSTIFIED IT, and the
            /// per-run causal record underneath it. Added for the queue 119
            /// study (Sweep.cs), which had to answer "what did the real arm
            /// know that the canned arm could not" and could not answer it
            /// from `Spoken`, which is a count.
            ///
            /// NOTHING HERE CHANGES WHAT THE PLAYER SEES. The beat-identity
            /// selftest is the guard on that claim: it compares the two arms'
            /// beats and it still passes.
            public readonly List<Said> Said = new List<Said>();
            public readonly Trace Trace = new Trace();
        }

        /// One spoken line, and the reason it was that line rather than another.
        ///
        /// `Kind` is taken from the `SpokenLine` StreetVoice actually produced
        /// (`AboutPlayer`), never re-derived here, so it cannot drift from the
        /// banks. `ambient` is the one thing the flag cannot say on its own:
        /// `StreetVoice.Ambient` is the street's own life and its lines are not
        /// about the player by construction.
        internal class Said
        {
            public string Beat;         // which of the five moments
            public string Speaker;
            public string Text;
            public string Kind;         // pointed | chatter | ambient
            public double Suspicion, Loyalty, Strongest;
            public StanceKind Stance;
            public int Hops = -1;       // -1 when no rumour stands behind the line
            /// WOULD THE LIVE GAME HAVE SAID ANYTHING AT ALL HERE.
            ///
            /// `GossipDirector.TickStances` does `if (stance < StanceKind.Comments)
            /// continue;`, so below the Comments rung the street is SILENT in the
            /// game. This session substitutes the plain neighbourly band instead,
            /// deliberately, so the two arms never differ by a line being present
            /// or absent. That substitution makes the harness more talkative than
            /// the build, and a study that did not count it would report a line
            /// the game would never speak.
            public bool LiveWouldSpeak = true;
        }

        /// The causal chain of one run, as numbers rather than as the prose the
        /// operator transcript already carries. Same events, same order; this
        /// half is the one a sweep can count.
        internal class Trace
        {
            public int Witnesses, Awake, Filed;
            public double FiledConfidence;
            public string ClaimValue = "none", Verdict = "none";
            public int Tick1Events, Tick1Mine, Tick1Contra, Tick2Events, Tick2Contra;
            public string Heard = "none";
            public double HeardConfidence;
            public int HeardHops = -1;
            public double LenaSuspicion;
        }

        internal static void Play(IUi ui, Arm arm, int seed, Log log)
        {
            var w = BuildWorld();
            var targets = OperationSetup.Build();
            var night = new GameTime(2, 22, 0);

            ui.Show(Wrap(
                "MERIDIAN, a port town in the north of England, some time around 1990.\n" +
                "\n" +
                "Three weeks ago your uncle Mickey died and left you his pub on Hook " +
                "Street. It came with a cellar full of empties, a doorman nobody has " +
                "paid since the funeral, and a bookkeeper called Lena who has kept the " +
                "books here for thirty-one years and has not decided about you yet.\n" +
                "\n" +
                "It also came with the other thing Mickey did, which nobody has said " +
                "out loud to you.\n" +
                "\n" +
                "You choose by typing a number and pressing return. That is all there " +
                "is to it. It takes about ten minutes."));
            ui.Pause();

            // ---- the evening, and the four decisions ----
            ui.Show(Rule + "\n" + Wrap(
                "TUESDAY, TEN AT NIGHT. The bar is empty. Lena is counting the till " +
                "and not looking at you.") + "\n\n" +
                Speech("Lena", "There's money in this town for a man who doesn't mind the hour. Mickey minded it less than he let on.") + "\n\n" +
                Wrap("She names three places, the way you would name three kinds of weather."));

            var targetOptions = targets.Select(t => Cap(t.Name) + ".").ToArray();
            int ti = ui.Ask("  Which one?", targetOptions);
            var target = targets[ti];

            var plan = new OperationPlan(target.Id);
            int hourIndex = 0, approachIndex = 0, coatIndex = 0;

            // The plan loop. The read is a character's estimate and never a
            // number, per the approved decision quoted in Operations.RiskWord,
            // so the player is being told what somebody thinks rather than
            // shown odds.
            while (true)
            {
                hourIndex = ui.Ask("  What time do you go?", new[]
                {
                    "Eleven at night. The street is still awake.",
                    "One in the morning. The last of the pubs are turning out.",
                    "Three in the morning. Nobody is out at three who is not up to something.",
                });
                plan.Hour = new[] { 23, 1, 3 }[hourIndex];

                approachIndex = ui.Ask("  How do you go in?", new[]
                {
                    "Quietly. Take your time and touch nothing you do not have to.",
                    "Straight through the door. Fast, and be gone before anybody decides what they heard.",
                });
                plan.Approach = approachIndex == 0 ? Approach.Quiet : Approach.Forced;

                coatIndex = ui.Ask("  There is a long coat on the hook by the cellar door. It was Mickey's.", new[]
                {
                    "Wear it. Nobody needs to know the shape of you.",
                    "Leave it. It is a warm night and a man in a coat looks like a man in a coat.",
                });

                var state = new OperationState
                {
                    // Quoted from OperationHost.BuildOperationState: a player
                    // who has done no jobs and taken no falls starts at 0.35,
                    // and heat is what the street already says about you,
                    // which on a first night is nothing.
                    Nerve = 0.35,
                    Heat = 0.0,
                    Coated = coatIndex == 0,
                };
                var read = Operations.Read(plan, target, state);

                ui.Show(Rule + "\n" + Wrap("You put it to Lena the way you have it in your head. She listens to the end, which is not nothing.") + "\n\n" +
                        Speech("Lena", read.Line + " " + read.Worry));

                if (ui.Ask("  Well?", new[] { "Go tonight.", "Think about it again." }) == 0) break;
            }

            bool coated = coatIndex == 0;
            var opState = new OperationState { Nerve = 0.35, Heat = 0.0, Coated = coated };
            log.Choices = target.Id + "/h" + plan.Hour.ToString("00", CultureInfo.InvariantCulture)
                + "/" + (plan.Approach == Approach.Quiet ? "quiet" : "forced")
                + "/" + (coated ? "coat" : "nocoat");

            // ---- doing it ----
            // Seed quoted from OperationHost.RunPlan so the same plan resolves
            // the same way it would in the game.
            var rng = new Random(night.Day * 7919 + plan.Hour * 31 + target.Id.Length);
            var outcome = Operations.Run(plan, target, opState, () => rng.NextDouble());

            ui.Show(Rule + "\n" + Wrap(outcome.Line) + "\n\n" + Wrap(
                outcome.Take > 0
                    ? "You count it in the cellar with the light off. " + Money(outcome.Take) + "."
                    : "You come home with nothing but the walk."));
            ui.Pause();

            // ---- who saw, and what the street does with it ----
            //
            // THE ONE PLACE THE TWO ARMS DIFFER. In REAL this is the game's own
            // wiring, mirrored from OperationHost.RunPlan: the witnesses
            // Operations.Run produced are drawn from whoever was actually out
            // at that hour, they enter the mill as ordinary sightings at the
            // confidence the coat leaves them, and the mill moves it around
            // afterwards. In CANNED nobody is asked and nothing is filed; the
            // street gets one fixed story about the job and never changes it.
            var jobFact = new Fact("player", "job_d" + night.Day + "_" + target.Id, "seen");
            // The witness's own words, quoted verbatim from OperationHost.
            string summary = "somebody was at " + target.Name + " in the small hours, and it was not nothing";

            Rumor canned = null;
            if (arm == Arm.Real)
            {
                var awake = w.Mill.Agents
                    .Where(a => a.Circle != "day" || plan.Hour >= 8 && plan.Hour < 20).ToList();
                var pool = awake.Take(outcome.Witnesses).ToList();
                foreach (var a in pool)
                    w.Mill.Witness(a.Id, jobFact, summary, sensitive: true, now: night,
                        confidence: coated ? 0.55 : 0.9);
                // THREE NUMBERS AND NOT ONE, because a zero here has two very
                // different causes: nobody was awake to see, or the plan was
                // good enough that the job produced no witnesses at all. A
                // single count cannot tell them apart and the first draft of
                // this line could not either.
                log.Add("real: Operations.Run produced " + outcome.Witnesses + " witness(es); "
                        + awake.Count + " of 4 agent(s) were out at hour " + plan.Hour + "; "
                        + pool.Count + " actually filed, at confidence "
                        + (coated ? "0.55(coat)" : "0.90(nocoat)"));
                log.Trace.Witnesses = outcome.Witnesses;
                log.Trace.Awake = awake.Count;
                log.Trace.Filed = pool.Count;
                log.Trace.FiledConfidence = coated ? 0.55 : 0.9;
            }
            else
            {
                // A scripted game knows which mission you did and fires a line
                // about it. It does not know whether anybody saw you, so this
                // rumour is nobody's: it has no origin, it never moves, and it
                // never gets stronger or weaker.
                //
                // Confidence 0.6 is the MIDDLE of the three bands
                // StreetVoice.Exchange selects on (below 0.5, 0.5 to 0.8, 0.8
                // and up). It is a band choice and not a measurement: the
                // middle is the only one that is neither the weakest nor the
                // strongest phrasing the bank can produce, so the canned arm
                // cannot be accused of having been handed either.
                canned = new Rumor
                {
                    Content = jobFact, OriginId = "", Summary = summary,
                    Confidence = 0.6, Hops = 1, Sensitive = true,
                };
                log.Add("canned: one fixed story, confidence 0.60, no origin, never moves");
            }

            // ---- the morning after, and what you tell her ----
            //
            // THE ORDER OF THESE THREE SCENES IS THE EXPERIMENT'S ONLY REAL
            // STAGING DECISION AND IT IS MADE FOR THE REAL ARM'S BENEFIT, so
            // it is written down here and in the report. A lie is only ever
            // caught in this build when a rumour ARRIVES at somebody who was
            // already told otherwise (GossipMill.Tick's contradiction branch),
            // so the claim has to be on the record before the street moves.
            // She asks first thing; the street talks afterwards. Both arms get
            // the same order.
            var morning = new GameTime(3, 9, 0);
            ui.Show(Rule + "\n" + Wrap(
                "WEDNESDAY MORNING. Lena has the ledger open on the counter and does " +
                "not look up when you come down.") + "\n\n" +
                Speech("Lena", "You were out late.") + "\n\n" +
                Wrap("It is not a question, exactly."));

            int said = ui.Ask("  What do you tell her?", new[]
            {
                "The truth. You were where you were, and she can make of it what she likes.",
                "You were home. Early night, nothing to report.",
                "Nothing. Let her ask properly if she wants to know.",
            });

            if (arm == Arm.Real && said != 2)
            {
                // Both halves, in the order LawHost.cs:234-240 does it in the
                // live game: check it against what she knows and move her
                // suspicion, THEN put it on the record so a rumour arriving
                // later has something to collide with. The other way round she
                // checks the claim against the claim and it always agrees.
                var claim = new Fact("player", jobFact.Predicate, said == 0 ? "seen" : "home");
                var verdict = Claims.Process(w.Lena.Knowledge, w.Lena.Suspicion, w.Lena.Memory, claim, morning);
                w.Mill.PlayerClaims("Lena", claim, morning);
                log.Add("real: claim " + claim + " -> " + verdict
                        + ", Lena suspicion " + w.Lena.Suspicion.Value.ToString("0.00", CultureInfo.InvariantCulture));
                log.Trace.ClaimValue = claim.Value;
                log.Trace.Verdict = verdict.ToString();
            }

            ui.Show(Speech("Lena", Passing(w, w.Lena, arm, canned, seed, "morning/lena", log)));
            log.Spoken++;
            ui.Pause();

            // ---- out on the street, where it moves ----
            // In REAL, one round of the mill: whoever saw it tells whoever they
            // drink with. In CANNED nothing is ticked, because nothing is held.
            GossipEvent heard = null;
            if (arm == Arm.Real)
            {
                var events = w.Mill.Tick(morning.AddMinutes(90));
                var mine = events.Where(e => e.Rumor != null && e.Rumor.Content.Subject == "player").ToList();
                // Staged where the people actually are. Lena is behind her own
                // bar all day, so an exchange with her in it is not something
                // you walk past on the pavement; if the only talk that moved
                // was hers, it still happened and she carries it, it is simply
                // not the conversation this scene shows.
                heard = mine.FirstOrDefault(e => e.FromId != "Lena" && e.ToId != "Lena")
                        ?? mine.FirstOrDefault();
                int contra = events.Count(e => e.Contradiction);
                log.Add("real: tick 1 produced " + events.Count + " event(s), " + mine.Count
                        + " about the player, " + contra + " collided with what the player had said; "
                        + (heard == null ? "nothing to overhear" : heard.FromId + "->" + heard.ToId));
                log.Trace.Tick1Events = events.Count;
                log.Trace.Tick1Mine = mine.Count;
                log.Trace.Tick1Contra = contra;
                if (heard != null)
                {
                    log.Trace.Heard = heard.FromId + "->" + heard.ToId;
                    log.Trace.HeardConfidence = heard.Rumor.Confidence;
                    log.Trace.HeardHops = heard.Rumor.Hops;
                }
            }

            ui.Show(Rule + "\n" + Wrap(
                "LATER. Hook Street smells of the fish quay and last night's rain. " +
                "There are two of them stood by the bookmaker's with their backs to " +
                "the wind, and they do not stop talking as you go by."));

            // The overheard pair. Same renderer, same bank, same two lines.
            // REAL: whatever the mill actually moved, in the words of the
            // people who moved it. CANNED: the fixed story, told by the same
            // two people. If in REAL nobody saw anything, the street has
            // nothing to say about you and talks about itself instead, which
            // is StreetVoice.Ambient and is the honest answer rather than a
            // silence.
            List<SpokenLine> pair;
            if (arm == Arm.Real && heard != null)
                pair = StreetVoice.Exchange(heard.Rumor, w.Mill.Get(heard.FromId), w.Mill.Get(heard.ToId), seed);
            else if (arm == Arm.Canned)
                pair = StreetVoice.Exchange(canned, w.Rocco.G, w.Sam.G, seed);
            else
                pair = StreetVoice.Ambient(w.Rocco.G, w.Sam.G, morning, 0.4, 0.5, false, false, seed);

            ui.Show(string.Join("\n\n", pair.Select(l => Speech(l.SpeakerId, l.Text))));
            log.Spoken += pair.Count;
            // AMBIENT IS THE ONE KIND THE FLAG CANNOT NAME. `AboutPlayer` is
            // false both for the street's own life and for a neighbour's plain
            // hello, and the study has to tell those apart, so the caller says
            // which function it just called.
            bool ambient = arm == Arm.Real && heard == null;
            foreach (var l in pair)
                log.Said.Add(new Said
                {
                    Beat = "street/pair", Speaker = l.SpeakerId, Text = l.Text,
                    Kind = ambient ? "ambient" : l.AboutPlayer ? "pointed" : "chatter",
                    Strongest = l.Source != null ? l.Source.Confidence : 0.0,
                    Hops = l.Source != null ? l.Source.Hops : -1,
                });

            // Somebody clocks you as you pass. StreetVoice.Recognition, from
            // the stance ladder. In REAL the stance is computed from what that
            // person actually carries and how they actually feel; in CANNED it
            // is pinned at Comments, which is the lowest rung that speaks and
            // the one a scripted game's pointed line lives on. Pinning it
            // higher would have somebody refuse to deal with a player they
            // have no reason to refuse, which is a worse scripted game rather
            // than a better one.
            //
            // WHOEVER WAS NOT JUST OVERHEARD. Otherwise the same person is
            // stood in two places in the same minute, which reads as the game
            // being broken and would read that way in one arm more often than
            // the other. The three staging sentences are the only prose in
            // this file that describes a member of the cast, and all three are
            // used by both arms.
            var spoke = new HashSet<string>(pair.Select(l => l.SpeakerId));
            var passer = new[] { w.Ada, w.Rocco, w.Sam }.First(p => !spoke.Contains(p.Name));
            ui.Show(Rule + "\n" + Wrap(Where(passer.Name)));
            ui.Show(Speech(passer.Name, Passing(w, passer, arm, canned, seed + 1, "passing/" + passer.Name.ToLowerInvariant(), log)));
            log.Spoken++;
            ui.Pause();

            // ---- the afternoon, when it catches up or does not ----
            var afternoon = new GameTime(3, 17, 0);
            if (arm == Arm.Real)
            {
                var events = w.Mill.Tick(afternoon);
                int contra = events.Count(e => e.Contradiction);
                log.Add("real: tick 2 produced " + events.Count + " event(s), "
                        + contra + " collided with what the player had claimed; Lena suspicion "
                        + w.Lena.Suspicion.Value.ToString("0.00", CultureInfo.InvariantCulture)
                        + " (" + w.Lena.Suspicion.Level + ")");
                log.Trace.Tick2Events = events.Count;
                log.Trace.Tick2Contra = contra;
            }
            log.Trace.LenaSuspicion = w.Lena.Suspicion.Value;

            ui.Show(Rule + "\n" + Wrap(
                "LATE AFTERNOON. The light is going. Lena is on the step of the pub " +
                "with her coat on, which she does not usually have on at five."));
            ui.Show(Speech("Lena", Passing(w, w.Lena, arm, canned, seed + 2, "evening/lena", log)));
            log.Spoken++;

            ui.Show("\n" + Rule + "\n" + Wrap(
                "You go in and put the lights on. The street carries on outside " +
                "the window, doing whatever it does.\n" +
                "\n" +
                "That is the end of this one. Thank you.") + "\n" + Rule);
        }

        /// One line from somebody who has clocked you, through the ladder.
        ///
        /// The SAME call in both arms. REAL asks the person what they are
        /// actually carrying and how they actually feel; CANNED hands the same
        /// function a fixed story and a fixed stance. Below the rung where the
        /// ladder speaks, the function is asked for the plain band instead of
        /// nothing, so a person with no reason to say anything pointed still
        /// says the ordinary thing a neighbour says, and the two arms never
        /// differ by a line being present or absent.
        static string Passing(World w, Person p, Arm arm, Rumor canned, int seed, string beat, Log log)
        {
            var said = new Said { Beat = beat, Speaker = p.Name, Loyalty = p.G.Loyalty };
            SpokenLine line;
            if (arm == Arm.Canned)
            {
                said.Stance = StanceKind.Comments;
                said.Strongest = canned != null ? canned.Confidence : 0.0;
                said.Hops = canned != null ? canned.Hops : -1;
                line = StreetVoice.Recognition(p.G, canned, StanceKind.Comments, seed);
            }
            else
            {
                var about = p.G.Rumors
                    .Where(r => r.Content.Subject == "player")
                    .OrderByDescending(r => r.Confidence).FirstOrDefault();
                double strongest = about != null ? about.Confidence : 0.0;
                var stance = StreetVoice.Stance(p.Suspicion.Value, p.G.Loyalty, strongest,
                    leashed: false, wearingCoat: false);
                said.Suspicion = p.Suspicion.Value;
                said.Strongest = strongest;
                said.Stance = stance;
                said.Hops = about != null ? about.Hops : -1;
                line = StreetVoice.Recognition(p.G, about, stance, seed);
                // NULL IS THE LADDER DECLINING TO SPEAK, and it is the one
                // thing this session does that the live game does not: below
                // Comments, `GossipDirector.TickStances` stays silent and this
                // falls through to the plain band so the two arms cannot differ
                // by a line being missing. Recorded rather than smoothed over.
                said.LiveWouldSpeak = line != null;
                if (line == null) line = StreetVoice.Recognition(p.G, null, StanceKind.Comments, seed);
            }
            said.Text = line.Text;
            said.Kind = line.AboutPlayer ? "pointed" : "chatter";
            if (log != null) log.Said.Add(said);
            return line.Text;
        }

        /// Where each of the three is when you come past them, from their own
        /// card: Ada is a retired teacher in the flats opposite, Rocco has
        /// stood on that door for twenty years, Sam walks the block at all
        /// hours selling nothing anybody can name.
        static string Where(string name) =>
            name == "Ada"
                ? "Ada from the flats is on her step with the milk. She taught half this street and she watches you the whole way past."
            : name == "Rocco"
                ? "Rocco is on the pub door with his hands in his coat, where he has stood since before you were anybody's nephew."
                : "Sam falls into step beside you for half the pavement, the way he does with everybody.";

        static string Cap(string s) =>
            string.IsNullOrEmpty(s) || !char.IsLower(s[0]) ? s : char.ToUpperInvariant(s[0]) + s.Substring(1);

        /// Late-analog money, in the words the period uses. Nothing here is a
        /// score: it is what the player is holding.
        static string Money(int pounds) =>
            pounds == 1 ? "One pound" : pounds + " pounds, in fives and tens";

        // ---------------------------------------------------------------
        // the selftest: the two arms are the same game
        // ---------------------------------------------------------------

        /// THE ACCEPTING CASE FIRST. Plays both arms with the same answers and
        /// asserts they are the same shape, because if they ever are not, the
        /// evening measures formatting instead of the town.
        ///
        /// The rejecting case is a transcript with one beat added: the
        /// comparison has to be able to SEE a difference, or a green here is
        /// a ratchet that would pass two arms that had drifted apart.
        static int Selftest()
        {
            int passed = 0, failed = 0;

            // Four answer scripts, chosen to walk different branches: the
            // careful plan, the loud one, the one that changes its mind, and
            // the one that says nothing to Lena at the end.
            var scripts = new Dictionary<string, int[]>
            {
                { "careful/truth", new[] { 0, 2, 0, 0, 0, 0 } },
                { "loud/lie", new[] { 1, 0, 1, 1, 0, 1 } },
                { "changes-mind/silent", new[] { 2, 1, 0, 0, 1, 1, 1, 0, 0, 2 } },
                { "warehouse/lie", new[] { 2, 2, 0, 1, 0, 1 } },
            };

            foreach (var kv in scripts)
            {
                var real = new ScriptedUi(kv.Value);
                var cann = new ScriptedUi(kv.Value);
                Play(real, Arm.Real, 7, new Log());
                Play(cann, Arm.Canned, 7, new Log());

                if (Same(real.Shape, cann.Shape, out string why))
                {
                    passed++;
                    Console.WriteLine("  PASS  " + kv.Key + ": both arms " + real.Shape.Count
                        + " beat(s), " + real.Shape.Count(s => s.StartsWith("ask:")) + " question(s), identical");
                }
                else
                {
                    failed++;
                    Console.WriteLine("  FAIL  " + kv.Key + ": " + why);
                }

                // Every spoken line has to have words in it. An empty band pick
                // reads to a player as the game breaking, and it would only
                // ever happen in one arm.
                foreach (var ui in new[] { real, cann })
                    foreach (var block in ui.Text)
                        if (block == null || block.Trim().Length == 0)
                        {
                            failed++;
                            Console.WriteLine("  FAIL  " + kv.Key + ": an empty block reached the player");
                        }
            }

            // THE REJECTING CASE. A planted extra beat must be caught, or the
            // comparison above is not a comparison.
            var a = new List<string> { "show", "ask:x|1", "pause" };
            var b = new List<string> { "show", "ask:x|1", "pause", "show" };
            if (!Same(a, b, out string _))
            {
                passed++;
                Console.WriteLine("  PASS  planted difference: caught (4 beats against 3)");
            }
            else
            {
                failed++;
                Console.WriteLine("  FAIL  planted difference: NOT caught, the comparison is blind");
            }
            var c = new List<string> { "show", "ask:x|1|2", "pause" };
            if (!Same(a, c, out string _))
            {
                passed++;
                Console.WriteLine("  PASS  planted option change: caught (one arm offered a choice the other did not)");
            }
            else
            {
                failed++;
                Console.WriteLine("  FAIL  planted option change: NOT caught");
            }

            Console.WriteLine("stranger-test selftest: " + passed + " passed, " + failed + " failed ("
                + scripts.Count + " answer script(s) played through both arms, 2 planted difference(s))");
            return failed == 0 ? 0 : 1;
        }

        static bool Same(List<string> a, List<string> b, out string why)
        {
            if (a.Count != b.Count)
            {
                why = "one arm has " + a.Count + " beat(s) and the other " + b.Count;
                return false;
            }
            for (int i = 0; i < a.Count; i++)
                if (a[i] != b[i])
                {
                    why = "beat " + (i + 1) + " differs: real=" + a[i] + " canned=" + b[i];
                    return false;
                }
            why = "";
            return true;
        }

        // ---------------------------------------------------------------

        static int Main(string[] args)
        {
            // The transcript is committed and read by people; its numbers must
            // not depend on the machine's locale. Copied from SimHarness for
            // the same reason it is there.
            CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;

            // THE STUDY'S MODES. `--sweep` and `--curve` are the queue 119
            // comparison run by the studio instead of by three people, ruled by
            // Jafar on 2026-09-06 because there is no playable build to put in
            // front of anybody yet. Neither prints a preference; see Sweep.cs.
            if (Array.IndexOf(args, "--selftest") >= 0)
            {
                int core = Selftest();
                int study = StudySelftest();
                return core != 0 || study != 0 ? 1 : 0;
            }
            if (Array.IndexOf(args, "--sweep") >= 0) return Sweep();
            if (Array.IndexOf(args, "--curve") >= 0) return Curve();

            int participant = IntArg(args, "--participant", 0);
            int run = IntArg(args, "--run", 0);
            string armArg = StrArg(args, "--arm", null);

            Arm arm;
            if (armArg != null)
            {
                if (armArg != "real" && armArg != "canned")
                {
                    Console.WriteLine("--arm takes real or canned");
                    return 2;
                }
                arm = armArg == "real" ? Arm.Real : Arm.Canned;
            }
            else if (participant >= 1 && participant <= Assignment.Length && (run == 1 || run == 2))
            {
                arm = Assignment[participant - 1][run - 1];
            }
            else
            {
                Console.WriteLine("Give a participant (1, 2 or 3) and a run (1 or 2):");
                Console.WriteLine("    dotnet run --project ledger/StrangerTest -- --participant 1 --run 1");
                Console.WriteLine("Or run the studio's own comparison, which needs nobody:");
                Console.WriteLine("    dotnet run --project ledger/StrangerTest -- --sweep");
                Console.WriteLine("    dotnet run --project ledger/StrangerTest -- --curve");
                return 2;
            }

            // The seed varies per participant and per run so nobody hears the
            // same sentence twice. The bands are fourteen lines wide, so the
            // same beat picks a different line each time even when the state
            // behind it is the same.
            int seed = participant * 100 + run * 7;

            var log = new Log();
            log.Add("participant=" + participant + " run=" + run + " arm=" + arm.ToString().ToLowerInvariant()
                    + " seed=" + seed);
            int code = 0;
            try
            {
                Play(new ConsoleUi(), arm, seed, log);
            }
            catch (Exception ex)
            {
                // A crash in front of a stranger is not data. Say one plain
                // sentence and let the operator read the reason in the file.
                Console.WriteLine();
                Console.WriteLine("  Something has gone wrong and this run has stopped. Nothing you did caused it.");
                log.Add("ENDED EARLY: " + ex);
                code = 1;
            }

            WriteRecord(participant, run, arm, seed, log, code);
            return code;
        }

        /// THE INSTRUMENT. Not a score and never shown to the player: one
        /// key=value row per run so a later session can prove the evening
        /// happened and how far each run got, plus the transcript of what the
        /// harness did underneath.
        ///
        /// No spaces inside a value, per the instrument conventions, so every
        /// reader that splits on whitespace gets whole fields.
        static void WriteRecord(int participant, int run, Arm arm, int seed, Log log, int code)
        {
            try
            {
                var root = RepoRoot();
                if (root == null) return;
                var dir = Path.Combine(root, "production", "stranger-test", "sessions");
                Directory.CreateDirectory(dir);
                string stamp = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture);
                string armName = arm.ToString().ToLowerInvariant();

                File.WriteAllText(
                    Path.Combine(dir, "p" + participant + "-run" + run + "-" + stamp + ".txt"),
                    string.Join("\n", log.Lines) + "\n");

                // One row, appended. `spoken` is a COUNT OF LINES SPOKEN IN
                // THIS RUN, not a rate and not a total across runs; `ended` is
                // last-wins for the run and is the only thing that says whether
                // a person got to the end.
                var row = "strangerTest participant=" + participant + " run=" + run
                    + " arm=" + armName + " seed=" + seed
                    + " choices=" + (log.Choices.Length == 0 ? "none-yet" : log.Choices)
                    + " spoken=" + log.Spoken
                    + " ended=" + (code == 0 ? "complete" : "early")
                    + " atUtc=" + stamp + "\n";
                File.AppendAllText(Path.Combine(root, "production", "stranger-test", "runs.txt"), row);
            }
            catch (IOException)
            {
                // A locked disk must not take the evening down. The run
                // already happened; the reading is what the person says.
            }
        }

        static string RepoRoot()
        {
            var d = new DirectoryInfo(Directory.GetCurrentDirectory());
            while (d != null)
            {
                if (File.Exists(Path.Combine(d.FullName, "CLAUDE.md"))) return d.FullName;
                d = d.Parent;
            }
            return null;
        }

        static int IntArg(string[] args, string name, int fallback)
        {
            var s = StrArg(args, name, null);
            int v;
            return s != null && int.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out v) ? v : fallback;
        }

        static string StrArg(string[] args, string name, string fallback)
        {
            int i = Array.IndexOf(args, name);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : fallback;
        }
    }
}
