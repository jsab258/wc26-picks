using System;
using System.Collections.Generic;
using System.Text;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Headless-ish self-test: launched with "-simdays N", the game plays itself —
    /// accelerated clock, the player walks a waypoint loop, NPC positions are
    /// sampled, runtime errors are captured, screenshots are taken day and night —
    /// then writes sim-out/sim-report.json and exits with a pass/fail code.
    public static class SimMode
    {
        // Parsed once (it cannot change after process start — and the old
        // per-read GetCommandLineArgs() allocated a fresh array six times a
        // frame on the normal-play hot path), and clamped at zero (a negative
        // -simdays used to produce a normal-looking game with driving, audio
        // and the key prompt all silently disabled). Audit 2026-07-27.
        static int? _days;
        public static int Days
        {
            get
            {
                if (_days.HasValue) return _days.Value;
                int parsed = 0;
                var args = Environment.GetCommandLineArgs();
                for (int i = 0; i < args.Length - 1; i++)
                    if (args[i] == "-simdays" && int.TryParse(args[i + 1], out var d))
                        parsed = Math.Max(0, d);
                _days = parsed;
                return parsed;
            }
        }
    }

    public class SimDirector : MonoBehaviour
    {
        const float SimMinutesPerRealSecond = 20f; // 1 game day = 72 real seconds
        /// Ceiling on days given back to the sim after the clock jumps. See the
        /// reclaim in Update: uncapped, repeated falls make the run unbounded.
        const int MaxReclaimedDays = 4;
        /// Consecutive hourly samples an Act II beat may stay due-and-unfired
        /// before the build fails. Two, so a beat has a clear game-hour to
        /// fire — enough that the last hour of the run cannot manufacture a
        /// failure, small enough that a beat which never fires still does.
        // Three, not two: beat firing runs on a 30-frame cadence, and on a
        // runner sustaining under ~10 fps one game-hour can span fewer frames
        // than the cadence — two samples could red a healthy build for being
        // slow (audit 2026-07-27).
        const int ActTwoGraceSamples = 3;

        GameController _game;
        PlayerController _player;
        NpcWalker[] _npcs;

        readonly List<string> _errors = new List<string>();
        readonly List<object> _samples = new List<object>();
        readonly List<object> _screenshots = new List<object>();
        readonly Dictionary<string, Vector3> _startPositions = new Dictionary<string, Vector3>();

        int _endDay;
        bool _finished;
        bool _forcedLedgerLearn;
        bool _forcedFall;
        bool _empireScripted;
        bool _directorStaged, _directorFired;
        bool _harmStaged;
        bool _uiSmokeRun;
        List<DialogueUI.PanelReport> _uiPanels;
        int _lastRungDay = -1, _callsAnswered, _callsWrongPerson, _callsRangOut;
        /// Night witnesses at the moment the car started following the bot. The
        /// vehicle gate only means anything if a drop was SEEN after that.
        int _witnessesWhenCarArrived = -1;
        double _harmCapabilityAtInjury = 1.0;
        // Sampled at the day-8 close, BEFORE the fall: the wound's still-there
        // and gone-bad claims are about days 4-8, and the fall's jump now
        // heals through days 10-12 as designed (the world-day fix), so
        // asserting "still hurting" at day 13 red a healthy build.
        bool _harmSampled, _harmStillHurt, _harmTurned, _harmFeudLive, _harmFeudBlocks;
        bool _planStaged, _planRan;
        bool _dayJobStaged;
        bool _openModeForced;
        int _lastSeenDay = -1, _daysSkipped;
        /// Latched the moment a witness can describe the car. Read once per
        /// in-game hour rather than at the end, because the Fall clears the mill.
        bool _vehicleFactLatched;
        int _vehicleScanHour = -1;
        /// Per Act II pressure point: how many consecutive hourly samples its
        /// condition has held while its flag stayed unset. See ActTwoSample.
        readonly Dictionary<string, int> _act2Owed = new Dictionary<string, int>();
        int _act2SampleHour = -1;
        bool _endScreenDismissed;
        Verdict _weekLostVerdict = Verdict.Ongoing;
        bool _discreditExercised;
        bool? _discreditWorked;   // null = the secret never reached the day circle
        int _frozenCloses;   // closes the lost-week end screen ate before the day-8 reopen
        // P5 budgets: frame times accumulated every Update, reported at Finish.
        int _frames; double _frameSum; double _frameWorst;
        bool _actThreeStaged;
        string _actThreeWhy = "not staged";
        bool _actThreeHandedOver;
        Ending _actThreeEnding = Ending.None;
        bool _secretEverReachedDay;
        int _lastSampledHour = -1;

        // HOW BUSY THE STREET ACTUALLY FEELS (Jafar, 2026-07-28: "is 700 NPC
        // the right number? density vs kcd2?").
        //
        // The end-of-run near-band count was the only number we had and it is
        // a single snapshot of one moment: two consecutive runs reported 3 and
        // then 12, which says nothing except that the sim player happened to
        // be somewhere quiet. Sampling hourly across nine days gives a
        // distribution instead — and the useful question is not "how many
        // people exist" but "how many can you see from where you are
        // standing", which is a different number and a different knob.
        readonly List<int> _within20 = new List<int>();
        readonly List<int> _within8 = new List<int>();

        void SampleDensity()
        {
            if (_player == null) return;
            var p = _player.transform.position;
            int near20 = 0, near8 = 0;
            foreach (var npc in _npcs)
            {
                if (npc == null) continue;
                var q = npc.transform.position;
                float d2 = (p.x - q.x) * (p.x - q.x) + (p.z - q.z) * (p.z - q.z);
                if (d2 <= 400f) near20++;
                if (d2 <= 64f) near8++;
            }
            if (_game != null && _game.CrowdBodies != null)
                foreach (var kv in _game.CrowdBodies)
                {
                    if (kv.Value == null) continue;
                    var q = kv.Value.transform.position;
                    float d2 = (p.x - q.x) * (p.x - q.x) + (p.z - q.z) * (p.z - q.z);
                    if (d2 <= 400f) near20++;
                    if (d2 <= 64f) near8++;
                }
            _within20.Add(near20);
            _within8.Add(near8);
        }

        static string Dist(List<int> xs)
        {
            if (xs.Count == 0) return "n/a";
            var sorted = new List<int>(xs); sorted.Sort();
            double mean = 0; foreach (var v in xs) mean += v;
            mean /= xs.Count;
            return $"{mean:0.0}/{sorted[sorted.Count / 2]}/{sorted[sorted.Count - 1]}";
        }

        bool _tookDayShot, _tookNightShot;
        int _shotDay = -1;
        int _waypointIndex;
        static readonly Vector3[] Waypoints =
        {
            new Vector3(0, 0, -8), WorldBuilder.BarDoor, new Vector3(8, 0, 8), new Vector3(0, 0, -8),
        };

        public void Begin(GameController game, PlayerController player)
        {
            _game = game;
            _player = player;
            _endDay = _game.Now.Day + SimMode.Days;
            _game.MinutesPerRealSecond = SimMinutesPerRealSecond;
            System.IO.Directory.CreateDirectory("sim-out");
            Application.logMessageReceived += OnLog;
            _npcs = UnityEngine.Object.FindObjectsByType<NpcWalker>(FindObjectsSortMode.None);
            foreach (var npc in _npcs) _startPositions[npc.DisplayName] = npc.transform.position;
            Debug.Log($"SimDirector: simulating {SimMode.Days} day(s)");
        }

        void OnLog(string condition, string stackTrace, LogType type)
        {
            if ((type == LogType.Error || type == LogType.Exception) && _errors.Count < 30)
                _errors.Add($"{type}: {condition}");
        }

        void Update()
        {
            if (_game == null) return;
            var now = _game.Now;

            // The sim bot is careless early (bare-faced drops, so heat climbs and
            // Ellis's spawn path gets exercised) and careful from day 3 (coated, so
            // the disguise path is exercised too). Both halves get CI coverage.
            // Careless on the first night only, careful from the second.
            //
            // This was "careless until day 3", and it was tuned when gossip was
            // quietly under-running on slow CI machines. With talk spreading at
            // its designed rate the bot now loses the week on day three, which
            // costs CI every gate that only exists in the open city — empire,
            // the Fall, the Director. One bare-faced night still exercises the
            // witness path; three of them just ended the run early.
            _game.WearingCoat = now.Day >= 2 && (now.Hour >= 21 || now.Hour < 3);

            // The car in CI (roadmap M12 step 7). The bot cannot press a key, so
            // from day 5 it simply keeps the car with it — the same world state
            // as having driven there. What this exercises is the part that
            // matters: a night drop made with a vehicle standing in the street
            // must leave a vehicle FACT in a witness's head, and must leave it
            // whether or not the bot was wearing the coat.
            if (now.Day >= 5 && PlayerCar.Instance != null && _player != null)
            {
                if (_witnessesWhenCarArrived < 0) _witnessesWhenCarArrived = _game.NightWitnesses;
                var pp = _player.transform.position;
                PlayerCar.Instance.transform.position = new Vector3(pp.x + 2.2f, 0.05f, pp.z + 1.4f);
            }

            ActTwoSample(now);

            // Catch the car description while it is still in somebody's head.
            // Once an hour is often enough — a rumor lives for days — and cheap
            // enough that scanning the mill does not show up in the frame time.
            if (!_vehicleFactLatched && now.Hour != _vehicleScanHour
                && _game.Gossip != null && _game.Gossip.Mill != null)
            {
                _vehicleScanHour = now.Hour;
                foreach (var lead in _game.Gossip.Mill.Leads("player"))
                    if (lead.TopicKey != null && lead.TopicKey.StartsWith("player.vehicle_d"))
                    { _vehicleFactLatched = true; break; }
            }

            // The panels, once, on day two — after the world has some state in it
            // so the ledger and the plan have something to say, and early enough
            // that a panel which strands the player fails the build rather than
            // fails the player.
            if (!_uiSmokeRun && now.Day >= 2 && _game.Ui != null)
            {
                _uiSmokeRun = true;
                _uiPanels = _game.Ui.SmokeTestPanels();
                foreach (var r in _uiPanels)
                    if (!r.Ok) Debug.LogWarning($"UI smoke: {r}");
            }

            // The exchange in CI (roadmap M10). Once a day the bot rings two
            // lines it has no special claim on. What this proves in-engine is
            // the thing the whole design rests on: that whether somebody
            // answers depends on where they actually ARE, so over nine days the
            // same call gets a different person, or nobody, or the person you
            // wanted. If every ring came back identical the system would be a
            // menu wearing a telephone.
            if (_lastRungDay != now.Day && now.Hour >= 11)
            {
                _lastRungDay = now.Day;
                foreach (var (place, who) in new[] { ("bar", "Lena"), ("boarding_house", "Ada") })
                {
                    var call = _game.RingLine(place, who);
                    if (call.Result == CallResult.Answered) _callsAnswered++;
                    else if (call.Result == CallResult.SomebodyElse) _callsWrongPerson++;
                    else if (call.Result == CallResult.NoAnswer) _callsRangOut++;
                }
            }

            // Harm in CI (roadmap M11). The bot cannot get into a fight, so the
            // consequence layer is staged directly: one wound left alone and one
            // seen to, on day 4, plus a feud between two of the crew. What this
            // proves is the part that only shows up over TIME — that an injury
            // is still there days later, that neglect turns it into something
            // worse, and that treatment prevents exactly that.
            if (!_harmStaged && now.Day >= 4 && now.Hour >= 10)
            {
                _harmStaged = true;
                _game.Harm.Inflict("Sam", "Sam", InjuryKind.Cut, now.Day,
                    "opened his arm on the ferry rail and would not go and get it seen to");
                var seen = _game.Harm.Inflict("Rocco", "Rocco", InjuryKind.Cut, now.Day,
                    "the same rail, the same night");
                _game.Harm.Treat(seen, null, now.Day);   // no wallet: the sim is proving the mechanism
                _game.Harm.Flare("Sam", "Sam", "Rocco", "Rocco", now.Day, heat: 0.7);
                _harmCapabilityAtInjury = _game.Harm.Capability("Sam", now.Day);
            }

            if (_harmStaged && !_harmSampled && now.Day >= 8 && now.Hour >= 9)
            {
                _harmSampled = true;
                var hurts8 = _game.Harm.Hurts("Sam", now.Day);
                _harmStillHurt = hurts8.Count > 0;
                foreach (var i in hurts8) if (i.WentBad) _harmTurned = true;
                _harmFeudLive = _game.Harm.FeudBetween("Sam", "Rocco") != null;
                _harmFeudBlocks = !_game.Harm.WillWorkTogether("Sam", "Rocco");
            }

            // THE CLOCK CAN JUMP, AND THE SIM MUST NOT PAY FOR IT. The Fall puts
            // the player away for three days by moving the calendar, not by
            // simulating them — so a fall on day 8 lands the world on day 11 and
            // a nine-day run ends having simulated six. Those three days are
            // world time, not sim time, and counting them as coverage is how
            // "nine simulated days" quietly became "however many the bot had
            // left". Give them back.
            _frames++;
            _frameSum += Time.unscaledDeltaTime;
            if (Time.unscaledDeltaTime > _frameWorst && _frames > 30) _frameWorst = Time.unscaledDeltaTime;

            if (_lastSeenDay < 0) _lastSeenDay = now.Day;
            if (now.Day > _lastSeenDay)
            {
                int skipped = now.Day - _lastSeenDay - 1;
                // Capped, because the Fall can happen more than once in the open
                // city and an uncapped reclaim is a run that never ends — each
                // fall buying the days that let the bot earn the next one. Four
                // is two falls' worth, which is all the coverage this is for.
                if (skipped > 0 && _daysSkipped < MaxReclaimedDays)
                {
                    // The arithmetic lives in Core (SimClock) because the first
                    // inline version extended every run exactly to its own
                    // landing day — a reclaim that had never reclaimed anything
                    // (audit 2026-07-27). CoreTests pin it now.
                    int before = _endDay;
                    _endDay = SimClock.EndDayAfterJump(_endDay, _lastSeenDay, now.Day,
                        MaxReclaimedDays - _daysSkipped);
                    _daysSkipped += _endDay - before;
                }
                _lastSeenDay = now.Day;
            }

            // Damage control in CI, staged BEFORE the fall: the fall deletes
            // every player rumor, so running this at Finish measured an empty
            // mill and defaulted true — permanently vacuous in every 9-day run
            // (audit 2026-07-27). Day 8, open city, pre-fall: the staged
            // warehouse story and the night jobs' witnesses are all still
            // alive, so the exercise is deterministic.
            if (!_discreditExercised && _secretEverReachedDay && now.Day >= 8 && now.Hour >= 9)
            {
                _discreditExercised = true;
                var mill8 = _game.Gossip != null ? _game.Gossip.Mill : null;
                if (mill8 != null)
                {
                    string topic = null; string value = null; double before = 0;
                    foreach (var a8 in mill8.Agents)
                        if (a8.Circle == "day")
                            foreach (var r8 in a8.Rumors)
                                if (r8.Sensitive && r8.Confidence > before)
                                { before = r8.Confidence; topic = r8.TopicKey; value = r8.Content.Value; }
                    if (topic == null) _discreditWorked = false;   // nothing to deny = the gate is lying
                    else
                    {
                        mill8.Discredit(topic, value, _game.Now);
                        double after8 = 0;
                        foreach (var a8 in mill8.Agents)
                            if (a8.Circle == "day")
                                foreach (var r8 in a8.Rumors)
                                    if (r8.TopicKey == topic && r8.Confidence > after8) after8 = r8.Confidence;
                        _discreditWorked = after8 < before;
                    }
                }
            }

            // Act I PP4 in CI: the trust path needs live conversation, so on day 6
            // the bot learns the hiding place the other way a player can — from
            // Rocco — and the authored moment must fire off the real transition.
            if (!_forcedLedgerLearn && now.Day >= 6)
            {
                _forcedLedgerLearn = true;
                var s = _game.HooksBook.ById("lena_ledger");
                if (s != null && !s.KnownToPlayer) s.Learn("Rocco", now);
            }

            // THE COVERAGE FLOOR. If day eight has arrived and the city has not
            // opened, open it anyway.
            //
            // Run 30248511085 went green having tested almost nothing: the bot
            // lost the week on day six, so OpenMode stayed false, so the empire
            // gate, the Director gate, the operations gate and BOTH act gates
            // passed vacuously on their own preconditions. Nine simulated days,
            // and the second half of the game was never touched.
            //
            // A conditional gate is only honest if something asserts the
            // condition was met. This is that something — and losing the week is
            // still reported, because whether a careful player can survive it is
            // a real balance question and papering over it here would be the
            // second mistake.
            if (!_openModeForced && !_game.Campaign.OpenMode && now.Day >= 8 && now.Hour >= 8)
            {
                _openModeForced = true;
                _weekLostVerdict = _game.Campaign.Verdict;
                // How many closes the frozen end-screen span ate: a live week
                // has closed 7 times by the day-8 morning. The gates baseline
                // on ACHIEVABLE counts, not ideal ones — a legitimately lost
                // week used to red the build under two misleading gate names
                // (openModeOk, verdictSane) for closes and job postings that
                // structurally could not have happened (audit 2026-07-27).
                _frozenCloses = Mathf.Max(0, 7 - _game.Campaign.DaysClosed);
                _game.Campaign.ForceOpenMode();
                // AND take the end screen down. Losing the week raises a panel
                // and sets InputLocked permanently — the won-week path has a sim
                // bypass and the lost one never did, because nothing after a
                // loss was ever exercised. Forcing open mode while the player is
                // frozen behind "the week is settled" is not a test of the open
                // city, it is a test of a paused game.
                _endScreenDismissed = _game.Ui != null && _game.Ui.DismissEndScreen();
                if (_player != null) _player.InputLocked = false;
                Debug.Log($"SimDirector: week ended {_weekLostVerdict} — forcing open mode so the " +
                          $"second half of the game is actually exercised (endScreen={_endScreenDismissed}).");
            }

            // The day job in CI. Staged for the same reason everything else in
            // the open city is: the accelerated clock gives the dispatch board a
            // four-hour window that is twelve real seconds, and the bot cannot
            // cross three districts in that. The ROUND is not staged — it still
            // walks all three stops and back to Zlata to be paid, which is the
            // half that can break.
            if (!_dayJobStaged && _game.Campaign.OpenMode && now.Hour >= 8 && now.Hour < 11)
            {
                _dayJobStaged = _game.StageDayJobShift();
            }

            // Empire v1 in CI: the moment the city opens, the bot plays one
            // beat of empire — recruit Sam by need (loyalty staged past the
            // floor), put him on the collection round, buy Victor's marker and
            // turn the key (nerve 0.4 folds). Day 9's close then pays the
            // racket, seeds witnesses, and wakes the rival — all on real paths.
            if (!_empireScripted && _game.Campaign.OpenMode && now.Hour >= 9)
            {
                _empireScripted = true;
                var m = _game.Gossip != null ? _game.Gossip.Mill : null;
                if (m != null)
                {
                    var sam = m.Get("Sam");
                    if (sam != null)
                    {
                        sam.Loyalty = 0.5; // the week's favors, staged
                        _game.Empire.RecruitByNeed(sam, "Sam", 120, _game.Wallet, now);
                        _game.Empire.Establish(_game.Empire.RacketOf("collection"), _game.Empire.CrewOf("Sam"), now);
                    }
                    var shop = _game.Empire.BusinessOf("pawnshop");
                    _game.Wallet.EarnDirty(300); // the bot funds the marker
                    _game.Empire.BuyDebt(shop, _game.Wallet);
                    _game.Empire.Squeeze(shop, m.Get("Victor"), m, now);
                }
            }

            // The Director's firing path in CI (roadmap M8). No API key on the
            // build machine means the nightly pass never authors anything, so
            // the code that actually RUNS a pressure would never be exercised.
            // Stage two by hand on day 9 — a demand from Rocco, then answered,
            // and a rumor through Sam — so scheduling, firing through the real
            // primitives, and settling all run in-engine every build.
            // Staged on the open city EXISTING, not on a date. It used to say
            // "day 9", and day 9 turned out to be unreachable: the Fall moves
            // the clock three days forward, so a fall late on day 8 lands the
            // world on day 11 and Finish() runs before hour 11 ever comes round
            // again. Every gate keyed to day 9 was therefore unsatisfiable, and
            // the only reason four builds did not say so is that they were also
            // vacuous — OpenMode was false, so each gate passed on its own
            // precondition being unmet. Closing the vacuum exposed the trap.
            if (!_directorStaged && _game.Campaign.OpenMode && now.Day >= 8 && now.Hour >= 11)
            {
                _directorStaged = true;
                bool demand = _game.StagePressure(new Pressure
                {
                    Kind = Pressures.Demand, Who = "Rocco", FireDay = now.Day, Amount = 150,
                    Line = "Rocco asked for a hundred and fifty, and did not say what for.",
                    Because = "staged in CI",
                });
                bool rumor = _game.StagePressure(new Pressure
                {
                    Kind = Pressures.Rumor, Who = "Sam", FireDay = now.Day,
                    Line = "Sam has been telling people the new owner keeps odd hours.",
                    Because = "staged in CI",
                });
                _game.Wallet.EarnDirty(200);   // so the demand can actually be answered
                bool paid = _game.SettleDemand("Rocco", out _);
                _directorFired = demand && rumor && paid && _game.DemandFrom("Rocco") == null;
            }

            // Operations in CI (roadmap M7.5). The bot cannot click a panel, so
            // the plan is assembled and run through the SAME path the panel
            // uses — which is the half most likely to break, because it is the
            // half that pushes witnesses into the mill and writes into crew
            // memory. Forced, at noon, bare-faced: chosen to guarantee somebody
            // sees it, so the witness wiring is actually exercised.
            if (!_planStaged && _game.CanPlan && now.Day >= 8 && now.Hour >= 12)
            {
                _planStaged = true;
                var mark = System.Linq.Enumerable.FirstOrDefault(_game.OpenTargets);
                if (mark != null)
                {
                    int dirtyBefore = _game.Wallet.Dirty;
                    _game.Plan = new OperationPlan(mark.Id)
                    { Approach = Approach.Forced, Hour = 12, Tools = true };
                    foreach (var c in _game.Empire.ActiveCrew) _game.Plan.Crew.Add(c.Name);
                    var read = _game.ReadPlan();
                    var outcome = _game.RunPlan();
                    _planRan = outcome != null
                        && read != null && read.Line.Length > 0
                        && !System.Linq.Enumerable.Any(read.Line, char.IsDigit)   // odds stay words
                        && mark.Done == (outcome.Success || outcome.Partial)
                        && _game.Wallet.Dirty == dirtyBefore + outcome.Take
                        && _game.Plan == null;                                    // a plan is spent
                }
            }

            // Act III in CI (act3-draft.md). The act's own trigger wants the
            // Table answered and an operation too big to deny, and its clock
            // wants six days the nine-day sim does not have. So the sim stages
            // the PRECONDITIONS by hand and then lets the act run itself: the
            // opening, the letter, the succession judgement, the handover and
            // the close all go through the real paths, on the real state.
            //
            // Every ending in this game is a description of the world, so what
            // this gate proves is not that a particular ending happens — it is
            // that the world always resolves to SOMETHING. An audit that closed
            // on Ending.None would be a player left standing in a finished game.
            if (!_actThreeStaged && _game.Campaign.OpenMode && now.Day >= 8 && now.Hour >= 13)
            {
                _actThreeStaged = true;
                var m = _game.Gossip != null ? _game.Gossip.Mill : null;

                // A second racket and a second pair of hands: the act opens on
                // an operation the bar cannot explain, and it needs somebody
                // who could be handed it.
                var rocco = m != null ? m.Get("Rocco") : null;
                if (rocco != null && _game.Empire.CrewOf("Rocco") == null)
                {
                    rocco.Loyalty = 0.75;                       // the week's favours, staged
                    _game.Empire.RecruitByNeed(rocco, "Rocco", 100, _game.Wallet, now);
                    _game.Empire.Establish(_game.Empire.RacketOf("fencing"), _game.Empire.CrewOf("Rocco"), now);
                }

                // The Table, answered. Somebody at a summit wanted a room and
                // got an answer; which answer does not matter to Act III.
                if (!_game.ActTwo.TableFired)
                {
                    if (_game.ActTwo.TableArmId == null) _game.ActTwo.TableArmId = "dockside";
                    _game.AnswerTable("defy");
                }

                // WHY the act did or did not open, recorded at the moment the
                // preconditions were set. `ShouldOpen` is a conjunction of three
                // things and a gate that only says "actThree failed" cannot tell
                // which of them was missing — the recruit may have been
                // unaffordable, the racket may have wanted a front nobody owns,
                // the Table may not have had an arm to answer. One line here
                // saves a twenty-minute build to find out.
                _actThreeWhy =
                    $"table={_game.ActTwo.TableFired} " +
                    $"biz={_game.Empire.Businesses.FindAll(b => b.Owned).Count} " +
                    $"rax={_game.Empire.Rackets.FindAll(r => r.Established).Count} " +
                    $"crew={_game.Empire.Crew.FindAll(c => !c.Departed).Count} " +
                    $"clean={_game.Wallet.Clean} dirty={_game.Wallet.Dirty}";
            }

            // One pass later, so the act has actually opened through its own
            // check rather than being constructed here: judge the successor,
            // hand it over, and bring the named day forward to today so the
            // close runs in-engine instead of six days after the sim ends.
            if (_actThreeStaged && _game.ActThree.Opened && !_game.ActThree.AuditClosed
                && _game.ActThree.Pp1Fired && now.Hour >= 14)
            {
                var ready = _game.ReadySuccessor();
                if (ready != null && _game.ActThree.SuccessorId == null)
                    _actThreeHandedOver = _game.HandOver(ready.Id);
                _game.ActThree.AuditClosesDay = now.Day;   // the letter's date, brought forward
            }

            if (_game.ActThree.AuditClosed) _actThreeEnding = _game.ActThree.Result;

            // Open-mode Fall in CI: if week two arrived without the fuse ever
            // blowing organically, stage one on day 9 so the whole Fall path
            // (seizure, time skip, the street knowing) runs in-engine every build.
            // AFTER the morning close (hour >= 10): the Fall's 3-day skip must
            // not swallow day 9's close, or DaysClosed never reaches 8 and the
            // openMode criterion reads as a regression (run 30199175088).
            //
            // `day >= 9` IS SAFE HERE, and it is the only place left in this
            // file where an exact day still appears — everything else was moved
            // off dates after three gates turned out to be unsatisfiable for
            // exactly that reason. It survives on `Falls == 0`: the only thing
            // that moves the clock is a Fall, so if none has happened the clock
            // has not jumped and day 9 arrives normally. If one HAS happened
            // this block is not wanted anyway. Do not "fix" it to day 8 — that
            // would stage a fall before the open city has had a day to be one.
            if (!_forcedFall && now.Day >= 9 && now.Hour >= 10 && _game.Campaign.OpenMode
                && _game.Campaign.Falls == 0 && !_game.Campaign.FallPending)
            {
                _forcedFall = true;
                _game.Campaign.ForcePendingFall();
            }

            // Drive the player around the block to exercise movement and camera —
            // except when the outfit's drop is open: then head straight for it, so the
            // night-job completion path (pay, witnesses, patience) runs in-engine.
            var job = _game.ActiveJobPos ?? _game.DayJobTargetPos; // night drops outrank; mornings go to parcels
            var target = job.HasValue ? new Vector3(job.Value.x, 0, job.Value.z) : Waypoints[_waypointIndex];
            _player.AutoMoveTarget = target;
            if (!job.HasValue &&
                Vector3.Distance(new Vector3(_player.transform.position.x, 0, _player.transform.position.z), target) < 1.2f)
                _waypointIndex = (_waypointIndex + 1) % Waypoints.Length;

            // Hourly NPC sample.
            if (now.Hour != _lastSampledHour)
            {
                _lastSampledHour = now.Hour;
                SampleDensity();
                // Transport check must be "did talk EVER reach the day circle", not an
                // end-of-week snapshot: disguised (0.6) sightings hop weakly and decay
                // below the carry threshold within days — by design, not by breakage.
                if (_game.Gossip != null && _game.Gossip.Mill != null &&
                    _game.Gossip.Mill.DayCircleHeat() > 0.05)
                    _secretEverReachedDay = true;
                foreach (var npc in _npcs)
                {
                    var p = npc.transform.position;
                    _samples.Add(new Dictionary<string, object>
                    {
                        { "time", now.ToString() }, { "npc", npc.DisplayName },
                        { "x", Math.Round(p.x, 1) }, { "z", Math.Round(p.z, 1) },
                    });
                }
            }

            // One noon and one night shot per simulated day.
            if (now.Day != _shotDay) { _shotDay = now.Day; _tookDayShot = _tookNightShot = false; }
            SampleScore();
            SampleReflections();
            SampleBodies();
            if (!_tookDayShot && now.Hour == 12) { _tookDayShot = true; Shot($"day{now.Day}_noon"); }
            if (!_tookNightShot && now.Hour == 23) { _tookNightShot = true; Shot($"day{now.Day}_night"); }
            // ONE A/B, ONCE. The only way to prove an image effect reaches
            // pixels is to render the same frame without it and compare —
            // everything else proves the code ran, which is not the same
            // claim and is exactly the gap every "verified in a test, absent
            // in the game" defect in this project has lived in.
            if (!_tookAoPair && now.Day >= 3 && now.Hour == 21) MeasureAo();

            if (now.Day >= _endDay) Finish();
        }

        /// Act II's standing conditions, in ONE place so the sampler below and
        /// the gate cannot drift apart. Each entry is (name, the condition that
        /// makes this beat due, whether it has fired).
        ///
        /// PP4 is absent on purpose rather than by oversight: it is the
        /// collision, it fires off an ATTENDED beat rather than off empire
        /// state, and so it has no standing condition to check.
        List<KeyValuePair<string, bool>> ActTwoOwed()
        {
            var owed = new List<KeyValuePair<string, bool>>();
            var a2 = _game.ActTwo;
            if (!a2.Opened) return owed;
            var e = _game.Empire;
            void Due(string name, bool condition, bool fired)
            {
                if (condition && !fired) owed.Add(new KeyValuePair<string, bool>(name, true));
            }
            Due("pp1", e.Arms.FindAll(a => a.Attention >= 0.25).Count >= 2, a2.Pp1Fired);
            Due("pp2", e.ArmOf("machine").Attention >= 0.5, a2.Pp2Fired);
            Due("pp3", e.ArmOf("newcrew").Attention >= 0.5 || e.CrewOf("Rita") != null, a2.Pp3Fired);
            Due("pp5", e.Arms.FindAll(a => a.Attention >= 0.5).Count >= 2, a2.Pp5Fired);
            Due("pp6", _game.EllisSpawned && _game.EllisInterviews.Count > 0
                       && e.TotalRacketIncome > 0, a2.Pp6Fired);
            Due("pp7", e.Arms.Exists(a => a.Stage >= 4), a2.TableArmId != null);
            return owed;
        }

        /// Once an in-game hour, ask which beats are DUE AND UNFIRED, and count
        /// how many samples in a row that has been true of each.
        ///
        /// The gate used to ask the same question once, at the end of the run,
        /// and that is a race it loses: the world's last hour can make a
        /// condition true, and `CheckActTwo` runs on a 30-frame cadence, so the
        /// beat is reported missing before the game was ever given a tick in
        /// which to fire it. Requiring the debt to SURVIVE a sample is the
        /// difference between "this beat never fires" — worth failing a build —
        /// and "this beat fired a moment after we looked", which is not a bug.
        ///
        /// It is the car gate's lesson pointed the other way: there, the world
        /// moved on and erased the evidence; here, the world had not yet caught
        /// up. Both are end-of-run reads of a thing that was still moving.
        void ActTwoSample(GameTime now)
        {
            if (now.Hour == _act2SampleHour) return;
            _act2SampleHour = now.Hour;
            var owed = ActTwoOwed();
            var stillOwed = new HashSet<string>();
            foreach (var kv in owed) stillOwed.Add(kv.Key);
            // Anything that has been settled since the last look drops back to
            // zero: a beat that fired late is a beat that fired.
            var keys = new List<string>(_act2Owed.Keys);
            foreach (var k in keys) if (!stillOwed.Contains(k)) _act2Owed[k] = 0;
            foreach (var k in stillOwed)
                _act2Owed[k] = (_act2Owed.TryGetValue(k, out var n) ? n : 0) + 1;
        }

        /// Renders through an explicit RenderTexture rather than ScreenCapture:
        /// the build machine has no GPU/display, and ScreenCapture silently
        /// produces nothing there. This path works on a software device and
        /// writes the file synchronously so we know immediately if it failed.
        // The live score, sampled hourly. Two things are recorded: whether
        // the mix MOVED at all across the run, and whether the calmest and
        // hottest moments came out the right way round — which is the one
        // property the whole adaptive-score design rests on.
        int _scoreSamples;
        double _scoreEnergyRange;
        double _scoreCalmUnease = -1, _scoreCalmestHeat, _scoreHotUnease = -1, _scoreHottestHeat = -1;
        double _scoreMinE = double.MaxValue, _scoreMaxE = double.MinValue;

        // ---- BODIES ----
        //
        // `Core/Rig` computed a gait for months while every person in the
        // city was a capsule. Three separate things can be wrong here and
        // only the first shows up in a screenshot:
        //
        //   nobody has a body   — Mannequin is wired to nothing;
        //   nobody's legs move  — the rig binds but never drives the joints;
        //   everybody solves    — the distance cull is not culling, and the
        //                         frame budget goes on people whose legs
        //                         cannot be seen from where the camera is.
        int _bodySamples, _bodyMaxSolved;
        double _bodyMaxKnee, _bodyMinKnee = 999;
        int _bodyRigs;
        /// Samples where at least one rig was outside the solve radius — the
        /// only samples at which a cull COULD have happened.
        double _bodyTallest, _bodyShortest = 99;
        int _bodyCullable;
        /// ...and samples where one actually did. The gate compares the two
        /// rather than asserting a cull outright, because a city whose people
        /// all happen to be nearby has nothing to cull and must not fail for
        /// it. My first version asserted `solved <= rigs`, which is true of
        /// every possible run including a cull that never fires.
        int _bodyCulled;
        int _bodyTick;

        void SampleBodies()
        {
            // Throttled: this is a scene-wide object scan, and running one
            // every frame of a nine-day simulation to check a gate is the
            // measurement costing more than the thing measured.
            if (++_bodyTick % 30 != 0) return;
            var rigs = UnityEngine.Object.FindObjectsByType<CharacterRig>(
                FindObjectsSortMode.None);
            if (rigs == null || rigs.Length == 0) return;
            _bodySamples++;
            _bodyRigs = Math.Max(_bodyRigs, rigs.Length);
            int solved = CharacterRig.SolvedLastFrame;
            _bodyMaxSolved = Math.Max(_bodyMaxSolved, solved);

            // The crowd must be a crowd. A body model that generates thirty
            // heights and builds thirty identical bodies passes every Core
            // test about the distribution — the failure is entirely in the
            // wiring, which is where every "verified in a test, absent in the
            // game" defect this project has found has lived.
            foreach (var r in rigs)
            {
                var man = r != null ? r.GetComponent<Mannequin>() : null;
                if (man == null) continue;
                _bodyTallest = Math.Max(_bodyTallest, man.Shape.Height);
                _bodyShortest = Math.Min(_bodyShortest, man.Shape.Height);
            }

            var cam = Camera.main;
            if (cam != null)
            {
                bool anyFar = false;
                foreach (var r in rigs)
                {
                    if (r == null) continue;
                    if (Vector3.Distance(r.transform.position, cam.transform.position)
                        > CharacterRig.SolveWithinMetres) { anyFar = true; break; }
                }
                if (anyFar)
                {
                    _bodyCullable++;
                    if (solved < rigs.Length) _bodyCulled++;
                }
            }
            // Read the KNEE the rig would be producing rather than a joint
            // angle off a transform: a transform tells you where a limb ended
            // up after four other systems touched it, and would pass this
            // gate on a body that is merely being pushed around.
            foreach (var r in rigs)
            {
                if (r == null || r.Speed < 0.4) continue;
                double knee = Rig.LegSwing(r.Phase, r.Speed).knee;
                if (knee > _bodyMaxKnee) _bodyMaxKnee = knee;
                if (knee < _bodyMinKnee) _bodyMinKnee = knee;
            }
        }

        // ---- WET REFLECTIONS ----
        //
        // The model is tested; what is NOT testable in Core is whether the
        // probe ever ran, and — the part that actually costs frame time —
        // whether it ran far LESS often than every frame. A refresh-gating
        // bug is invisible in a screenshot and invisible in a correctness
        // test: the picture looks right either way and the only symptom is
        // six extra camera passes a frame. So the gate counts.
        int _reflWetFrames, _reflDryFrames;
        float _reflMaxStrength;
        int _reflStartRefreshes = -1;

        void SampleReflections()
        {
            if (_reflStartRefreshes < 0) _reflStartRefreshes = WetReflections.Refreshes;
            if (WetReflections.Strength > 0)
            {
                _reflWetFrames++;
                if (WetReflections.Strength > _reflMaxStrength)
                    _reflMaxStrength = WetReflections.Strength;
            }
            else _reflDryFrames++;
        }

        int ReflRefreshes => Math.Max(0, WetReflections.Refreshes - Math.Max(0, _reflStartRefreshes));

        void SampleScore()
        {
            if (!Audio.ScoreRunning) return;
            var mix = new double[MusicModel.Layers];
            for (int i = 0; i < mix.Length; i++) mix[i] = Audio.StemGain((MusicLayer)i);
            double e = MusicModel.Energy(mix);
            double heat = _game.CurrentHeat;
            _scoreSamples++;
            if (e < _scoreMinE) _scoreMinE = e;
            if (e > _scoreMaxE) _scoreMaxE = e;
            _scoreEnergyRange = _scoreMaxE - _scoreMinE;
            // Tracked against the HEAT that produced them rather than against
            // the extremes of energy, or the comparison is circular.
            // UNEASE, not total energy. Energy also moves with the hour —
            // the pulse is damped at night — so the hottest-heat sample and
            // the calmest-heat sample can land on opposite sides of dusk and
            // the comparison says nothing about heat at all. Unease answers
            // to exposure and to nothing else, which makes it the one layer
            // this gate can read cleanly.
            //
            // Caught before the gate ever reported, by asking what ELSE moves
            // the number being compared. The same question the fog test
            // needed and did not get.
            double unease = Audio.StemGain(MusicLayer.Unease);
            if (_scoreCalmUnease < 0 || heat < _scoreCalmestHeat)
            { _scoreCalmestHeat = heat; _scoreCalmUnease = unease; }
            if (_scoreHotUnease < 0 || heat > _scoreHottestHeat)
            { _scoreHottestHeat = heat; _scoreHotUnease = unease; }
        }

        // ---- ambient occlusion, measured against its own absence ----
        bool _tookAoPair;
        double _aoOn = -1, _aoOff = -1;

        void MeasureAo()
        {
            _tookAoPair = true;
            var cam = Camera.main;
            if (cam == null) return;
            // Night, and a frame with geometry in it: occlusion on an empty
            // street is correctly almost nothing, and measuring THAT would
            // give a difference of zero and a gate that fails for being
            // pointed somewhere honest.
            double on = FrameLuma(cam);
            FilmGrade.AmbientOcclusion = false;
            double off = FrameLuma(cam);
            FilmGrade.AmbientOcclusion = true;
            _aoOn = on;
            _aoOff = off;
            Debug.Log($"SimDirector: ao a/b on={on:0.0000} off={off:0.0000} "
                      + $"delta={off - on:0.0000} applied={FilmGrade.Applied}");
        }

        /// Mean luminance of one rendered frame, without writing a file.
        double FrameLuma(Camera cam)
        {
            RenderTexture rt = null;
            Texture2D tex = null;
            var prevTarget = cam.targetTexture;
            var prevActive = RenderTexture.active;
            try
            {
                rt = new RenderTexture(640, 360, 24, RenderTextureFormat.ARGB32);
                cam.targetTexture = rt;
                cam.Render();
                RenderTexture.active = rt;
                tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
                tex.Apply();
                var px = tex.GetPixels();
                double sum = 0;
                foreach (var c in px) sum += 0.299 * c.r + 0.587 * c.g + 0.114 * c.b;
                return px.Length > 0 ? sum / px.Length : 0;
            }
            catch (Exception e) { _errors.Add("FrameLuma: " + e.Message); return -1; }
            finally
            {
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                if (tex != null) UnityEngine.Object.Destroy(tex);
                if (rt != null) rt.Release();
            }
        }

        void Shot(string name)
        {
            var path = $"sim-out/shot_{name}.png";
            var cam = Camera.main;
            if (cam == null) { _errors.Add("Shot: no main camera"); return; }

            RenderTexture rt = null;
            Texture2D tex = null;
            var prevTarget = cam.targetTexture;
            var prevActive = RenderTexture.active;
            try
            {
                rt = new RenderTexture(1280, 720, 24, RenderTextureFormat.ARGB32);
                cam.targetTexture = rt;
                cam.Render();

                RenderTexture.active = rt;
                tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
                tex.Apply();

                System.IO.File.WriteAllBytes(path, tex.EncodeToPNG());
                var info = new System.IO.FileInfo(path);

                // Emit a coarse ASCII luminance thumbnail + mean colour to the log.
                // The PNG artifact lives on a host our review environment can't reach,
                // but the job LOG is readable — so this is how the render gets "seen"
                // for blind iteration on visuals.
                var fp = Fingerprint(tex, name);
                _screenshots.Add(new Dictionary<string, object>
                {
                    { "path", path }, { "bytes", info.Exists ? info.Length : 0 },
                    { "meanLuma", fp.luma }, { "meanRgb", fp.rgb },
                    { "maxLuma", fp.maxLuma }, { "brightPct", fp.brightPct },
                    // The bright pixels' own colour. A magenta error shader
                    // reads as high-red/high-blue with green near zero.
                    { "brightRgb", fp.brightRgb },
                    { "satPct", fp.satPct }, { "satStrength", fp.satRgb },
                });
            }
            catch (Exception e)
            {
                _errors.Add($"Shot({name}) failed: {e.Message}");
            }
            finally
            {
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                if (tex != null) Destroy(tex);
                if (rt != null) { rt.Release(); Destroy(rt); }
            }
        }

        /// The fingerprint stores its numbers as invariant-culture STRINGS so
        /// the JSON report is stable across locales. Reading them back needs
        /// the same culture, or a machine with a comma decimal separator
        /// parses 0.35 as 35 and every gate here inverts.
        static double ShotNum(Dictionary<string, object> shot, string key)
        {
            if (shot == null || !shot.TryGetValue(key, out var v)) return -1;
            if (v is double d) return d;
            return double.TryParse(v as string, System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out var parsed) ? parsed : -1;
        }

        /// Downsample a captured frame to a small ASCII art thumbnail (logged so it
        /// is visible in CI, where the PNG artifact host is unreachable) plus mean
        /// luminance and RGB for the JSON report.
        static (string luma, string rgb, string maxLuma, string brightPct, string brightRgb,
                string satPct, string satRgb) Fingerprint(Texture2D tex, string name)
        {
            const int cols = 64, rows = 24;
            const string ramp = " .:-=+*#%@"; // dark -> bright
            var px = tex.GetPixels32();
            int w = tex.width, h = tex.height;
            long tr = 0, tg = 0, tb = 0;

            // Full-resolution brightness scan. Small, bright features (glowing windows,
            // a lamp pool) get averaged away in the 64x24 ASCII, so track the peak luma
            // and the fraction of genuinely bright pixels — these survive downsampling and
            // are how emissive/lighting work is verified blind from the CI log.
            double maxLuma = 0; long brightCount = 0;
            // THE COLOUR OF THE BRIGHT PIXELS, not just how many there are.
            //
            // Luminance alone cannot tell coloured neon from a shader that
            // failed to resolve, because Unity's error shader is magenta and
            // magenta is moderately bright. That is a real risk here: neon
            // uses Shader.Find("Standard"), which can return null in a
            // stripped player build, and a green log would have said nothing
            // about it. Magenta has a signature no real light in this game
            // has — high red, high blue, GREEN NEAR ZERO — so averaging the
            // colour of only the bright pixels makes the failure legible from
            // a text log, which is the only channel CI actually gives us.
            long br = 0, bg = 0, bb = 0;
            // AND THE SATURATED PIXELS, SEPARATELY. Averaging the colour of
            // merely BRIGHT pixels answers the magenta question and nothing
            // else, because any white in the mix drags the mean to grey — the
            // night frame came back at 247,249,244 and that could equally have
            // meant "no coloured light" or "coloured light plus a white UI".
            // Measuring the saturated pixels on their own says whether there
            // is real colour on screen, which is the actual art question.
            // MEAN SATURATION, NOT MEAN COLOUR. Averaging the colour of the
            // saturated pixels makes the same mistake one level down: eight
            // neon hues spread round the wheel average to a muddy khaki
            // (88,87,70 in the first run that measured it) even though every
            // one of them is strongly coloured. Opposing hues cancel; their
            // SATURATIONS cannot. So the honest statistic is how much of the
            // frame is coloured and how coloured it is — two scalars, neither
            // of which can be washed out by mixing.
            long sc = 0; double satSum = 0;
            for (int i = 0; i < px.Length; i++)
            {
                var c = px[i];
                double l = (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) / 255.0;
                if (l > maxLuma) maxLuma = l;
                if (l > 0.60) { brightCount++; br += c.r; bg += c.g; bb += c.b; }
                int mx = Math.Max(c.r, Math.Max(c.g, c.b));
                if (mx >= 40)
                {
                    int mn = Math.Min(c.r, Math.Min(c.g, c.b));
                    double sv = (mx - mn) / (double)mx;
                    if (sv >= 0.35) { sc++; satSum += sv; }
                }
            }
            double brightPct = 100.0 * brightCount / px.Length;
            long bn = brightCount > 0 ? brightCount : 1;
            string brightRgb = $"{br / bn},{bg / bn},{bb / bn}";
            double satPct = 100.0 * sc / px.Length;
            string satRgb = (sc > 0 ? satSum / sc : 0.0).ToString("0.00",
                System.Globalization.CultureInfo.InvariantCulture);
            var art = new StringBuilder(cols * rows + rows + 64);
            art.Append($"\n--- render[{name}] {cols}x{rows} ascii-luma ---\n");
            for (int ry = 0; ry < rows; ry++)
            {
                // ascii row 0 = top of image; GetPixels32 is bottom-up, so flip.
                int yHi = h - 1 - (ry * h) / rows;
                int yLo = h - 1 - ((ry + 1) * h) / rows;
                for (int rx = 0; rx < cols; rx++)
                {
                    int xLo = (rx * w) / cols, xHi = ((rx + 1) * w) / cols;
                    long r = 0, g = 0, b = 0; int n = 0;
                    for (int y = yLo + 1; y <= yHi; y++)
                        for (int x = xLo; x < xHi; x++)
                        {
                            var c = px[y * w + x];
                            r += c.r; g += c.g; b += c.b; n++;
                        }
                    if (n == 0) n = 1;
                    int ar = (int)(r / n), ag = (int)(g / n), ab = (int)(b / n);
                    tr += ar; tg += ag; tb += ab;
                    double lum = (0.299 * ar + 0.587 * ag + 0.114 * ab) / 255.0;
                    int idx = Mathf.Clamp((int)(lum * (ramp.Length - 1) + 0.5), 0, ramp.Length - 1);
                    art.Append(ramp[idx]);
                }
                art.Append('\n');
            }
            int cells = cols * rows;
            double mr = tr / (double)cells, mg = tg / (double)cells, mb = tb / (double)cells;
            double luma = (0.299 * mr + 0.587 * mg + 0.114 * mb) / 255.0;
            var inv = System.Globalization.CultureInfo.InvariantCulture;
            art.Append($"render[{name}] meanLuma={luma:0.000} maxLuma={maxLuma:0.000} " +
                       $"bright(>0.6)%={brightPct:0.00} meanRgb={(int)mr},{(int)mg},{(int)mb} " +
                       $"brightRgb={brightRgb} sat(>0.35)%={satPct:0.00} satStrength={satRgb}\n");
            Debug.Log(art.ToString());
            return (
                luma.ToString("0.000", inv),
                $"{(int)mr},{(int)mg},{(int)mb}",
                maxLuma.ToString("0.000", inv),
                brightPct.ToString("0.00", inv),
                brightRgb,
                satPct.ToString("0.00", inv),
                satRgb);
        }

        void Finish()
        {
            // Application.Quit is asynchronous (and a no-op in the Editor), so Update()
            // keeps calling Finish() every frame after _endDay. Guard so the report is
            // written and the process exit is requested exactly once.
            if (_finished) return;
            _finished = true;

            Application.logMessageReceived -= OnLog;

            bool npcsMoved = false;
            foreach (var npc in _npcs)
                if (Vector3.Distance(npc.transform.position, _startPositions[npc.DisplayName]) > 2f)
                    npcsMoved = true;

            // Gossip self-test: over the simulated days, night-life talk must have
            // physically reached the day circle at some point as NPCs crossed paths.
            var mill = _game.Gossip != null ? _game.Gossip.Mill : null;
            bool secretReachedDay = _secretEverReachedDay;
            double gossipHeat = mill != null ? mill.DayCircleHeat() : 0.0;

            // Exercise the damage-control path the dialogue buttons use, in-engine.
            // Discredit whichever sensitive story is currently strongest in the day
            // circle and verify THAT story loses confidence — the night jobs the sim
            // completes seed fresh witnessed rumors, so the original warehouse story
            // is not necessarily the one dominating the heat reading anymore.
            // Measured on day 8, pre-fall, when the stories provably existed
            // (audit 2026-07-27) — measuring here at Finish read the post-fall
            // wiped mill and defaulted true.
            bool discreditWorks = _discreditWorked ?? !secretReachedDay;

            // Campaign self-test. The sim bot does every drop and NO damage control,
            // so over a full week any verdict except cast-out is legitimate play —
            // per the balance lab, a careless week gets exposed about a third of the
            // time. Cast-out, though, would mean the job pipeline itself broke.
            var camp = _game.Campaign;
            bool jobRan = camp.JobsDone >= 1;
            bool takingsBanked = _game.TotalTakings > 0;
            // Belief-state channel: every witnessed drop is also SEEN by the player,
            // so witnesses must have produced known leads (design-doc §6.2 ledger).
            bool knowledgeWorks = _game.NightWitnesses == 0 || _game.Knowledge.Count >= 1;
            // Dirty night pay must actually cycle through the till into clean money.
            bool launderWorks = camp.JobsDone == 0 || _game.Wallet.TotalWashed > 0;

            // Any coated drop that was witnessed must have seeded its rumors at the
            // coat's reduced confidence — read back from the mill at creation time
            // by GameController (end-to-end proof the doubt landed).
            bool disguiseWorks = !_game.AnyCoatedWitnessed ||
                _game.MaxCoatedWitnessConf <= GameController.CoatWitnessConfidence + 0.01;

            // Ellis must appear iff the street ever ran hot enough (same sampling
            // cadence as the spawn check, so the comparison cannot race).
            bool osseiOk = _game.EllisSpawned == (_game.ObservedPeakHeat >= EllisSetup.SpawnHeatThreshold);

            // P5 in-engine proof: capture the lived week, overlay it onto fresh
            // authored objects, and the city must match — plus the real file writes.
            bool saveLoadOk = true;
            try
            {
                var json = _game.CaptureSave();
                var w2 = new Wallet(0);
                var c2 = new Campaign();
                var pk2 = new PlayerKnowledge();
                var sec2 = SecretsSetup.Build();
                var bb2 = new BeatBook();
                foreach (var b in _game.Beats.All)
                    bb2.Add(new Beat { Id = b.Id, HostId = b.HostId, Title = b.Title, Day = b.Day, StartHour = b.StartHour, EndHour = b.EndHour });
                var m2 = new GossipMill(new SocialGraph());
                if (mill != null)
                    foreach (var a in mill.Agents)
                        m2.Add(new Gossiper(a.Id, a.DisplayName, new MemoryStore(a.Id.ToLowerInvariant()),
                            new KnowledgeBase(), new SuspicionTracker(), a.Circle));
                var db2 = new DebtBook();
                foreach (var d in _game.Debts.All) db2.Add(new Debtor { Id = d.Id, Name = d.Name, Amount = d.Amount, Note = d.Note });
                var t2 = SaveCodec.Restore(json, w2, c2, pk2, sec2, bb2, m2, db2, out _);
                saveLoadOk = t2.TotalMinutes == _game.Now.TotalMinutes
                    && w2.Clean == _game.Wallet.Clean && w2.Dirty == _game.Wallet.Dirty
                    && System.Math.Abs(c2.OutfitPatience - camp.OutfitPatience) < 1e-9
                    && c2.Verdict == camp.Verdict
                    && c2.OpenMode == camp.OpenMode && c2.Falls == camp.Falls
                    && pk2.Count == _game.Knowledge.Count;
                if (mill != null)
                    foreach (var a in mill.Agents)
                    {
                        var twin = m2.Get(a.Id);
                        if (twin == null || twin.Rumors.Count != a.Rumors.Count || twin.Leashed != a.Leashed)
                            saveLoadOk = false;
                    }
                // THE SAVE MUST CARRY THE WHOLE WORLD. Injuries, purses and
                // Ellis's interview record all existed, all round-tripped in
                // CoreTests — and none was in the save, because nothing ever
                // asserted the game-layer wiring (audit 2026-07-27). This does:
                // a subsystem with live state whose key is missing from the
                // save is a red build, not a surprise on reload.
                var extraKeys = MiniJson.AsObject(MiniJson.Deserialize(json));
                var flags = extraKeys != null ? MiniJson.AsObject(extraKeys.TryGetValue("extra", out var ex) ? ex : null) : null;
                foreach (var mustCarry in new[] { "harm", "purses", "osseiInterviews", "interviewed", "empire", "economy", "acttwo", "actthree" })
                    if (flags == null || !flags.ContainsKey(mustCarry))
                    { _errors.Add("save missing key: " + mustCarry); saveLoadOk = false; }
                _game.SaveNow(quiet: true);
                if (!System.IO.File.Exists(_game.SavePath)) saveLoadOk = false;
                // P2: the second write must leave the previous good file as
                // .bak — the corruption-recovery line the load path falls to.
                _game.SaveNow(quiet: true);
                if (!System.IO.File.Exists(_game.SavePath + ".bak"))
                { _errors.Add("save backup missing after second write"); saveLoadOk = false; }
            }
            catch (Exception e) { _errors.Add("saveLoad: " + e.Message); saveLoadOk = false; }

            // Authored beats must resolve — the sim bot prioritizes drops, so passed
            // windows should read Skipped (with the loyalty cost applied), never
            // linger Pending. A beat still in the future may legitimately be Pending.
            bool beatsResolved = true;
            var beatStates = new List<object>();
            foreach (var b in _game.Beats.All)
            {
                beatStates.Add($"{b.Id}:{b.State}");
                if (b.WindowPassed(_game.Now) && b.State == BeatState.Pending) beatsResolved = false;
            }
            // The district population (open-city-spec §3): the founding cast plus
            // Victor plus the generated batch must actually be walking.
            bool populationOk = _npcs != null && _npcs.Length >= 20;

            // The day job (§6.6): in the open city the bot must have walked at
            // least one courier round — clean pay through the honest channel.
            bool dayJobOk = !_game.Campaign.OpenMode || SimMode.Days < 9 || _game.Job.ShiftsWorked >= 1;

            // The living economy (roadmap M7). Three things must be true after
            // nine days: the district has actually been paying its suppliers
            // (Mitch comes weekly and takes real money), the street's own state
            // is inside its designed band rather than having inflated away or
            // collapsed, and the whole thing survives its own codec. A campaign
            // that never squeezes should still be sitting near the neutral 1.0,
            // which is what makes this system safe to have shipped.
            var econ = _game.Economy;
            var econSnap = MiniJson.Serialize(econ.Capture());
            var econTwin = EconomySetup.Build();
            econTwin.Restore(MiniJson.AsObject(MiniJson.Deserialize(econSnap)));
            bool economyOk =
                econ.Suppliers.Exists(s => s.LastPaidDay >= 0)              // deliveries happened
                && econ.Prosperity > 0.05 && econ.Prosperity < 0.95         // no collapse, no runaway
                && econ.PriceLevel >= 0.9 && econ.PriceLevel <= 2.0         // no inflation spiral
                && econ.TakingsFactor >= econ.MinTakingsFactor
                && econ.TakingsFactor <= econ.MaxTakingsFactor
                && System.Math.Abs(econTwin.Prosperity - econ.Prosperity) < 1e-6
                && System.Math.Abs(econTwin.PriceLevel - econ.PriceLevel) < 1e-6;

            // The crowd (roadmap M9). Three thousand residents exist; almost none
            // of them are simulated, and the ones that are must be the ones near
            // the player. The gate is that the bands are populated, that the caps
            // held over nine days of the bot walking around, that the crowd
            // actually entered the gossip mill, and that the whole city still
            // saves as a seed rather than as three thousand records.
            var pop = _game.Populace;
            var popSnap = MiniJson.Serialize(_game.CapturePopulationForSim());
            bool crowdOk = pop != null
                && pop.Residents.Count == _game.PopulationCount
                && pop.CountIn(Lod.Near) <= pop.NearCap
                // Fully qualified, like everything else in this file: SimDirector
                // deliberately does not import System.Linq, and extension-method
                // syntax on List<T>.Count silently means the COUNT PROPERTY to a
                // reader and a compile error to Unity. It cost a red build.
                && pop.CountIn(Lod.Mid) <= pop.MidCap
                    + System.Linq.Enumerable.Count(pop.Residents, r => r.Known)
                && pop.CountIn(Lod.Near) > 0                      // somebody is always nearby
                && pop.CountIn(Lod.Far) > pop.Residents.Count / 2 // and almost everybody is not
                && popSnap.Length < 20000                         // a seed, not a census
                && (_game.Gossip == null || _game.Gossip.Mill == null
                    || System.Linq.Enumerable.Any(_game.Gossip.Mill.Agents,
                           a => a.Id.StartsWith("r")));

            // Access (roadmap M7.5). CI cannot walk the bot to every door, so
            // the gate is on the RULES rather than on the walking: every gate
            // must be openable by somebody, every one must have a doorman and a
            // refusal, and the evaluator must produce a legible answer for a
            // player who has nothing. A gate nobody can ever open is a wall,
            // and walls are the one thing this system exists to not build.
            // Operations (roadmap M7.5): the board must be real, and the plan
            // staged above must have gone all the way through the wiring.
            bool opsOk = _game.Targets.Count >= 3
                && (!_game.CanPlan || SimMode.Days < 9 || _planRan);

            // Traffic (roadmap M12). CoreTests already proves the rules; what
            // this proves is that the rules are still true after nine game-days
            // of the ENGINE driving them, with the player and thirty walkers
            // wandering into the road. The failure that would actually ruin an
            // evening is not a crash, it is a grid wedged solid.
            var traffic = _game.Traffic;
            bool trafficOk = traffic != null && traffic.Vehicles.Count >= 10;
            double tightest = traffic != null ? traffic.TightestGap() : 0;
            int offRoad = 0, kindsSeen = 0;
            if (traffic != null)
            {
                var kinds = new HashSet<string>();
                foreach (var v in traffic.Vehicles)
                {
                    kinds.Add(v.Kind.Id);
                    if (!v.Kind.UsesLanes && !StreetMap.OnRoad(v.X, v.Z, margin: 1.5)) offRoad++;
                }
                kindsSeen = kinds.Count;
                trafficOk = trafficOk
                    && tightest >= 0                     // nobody inside anybody
                    && offRoad == 0                      // nobody on the pavement
                    && kindsSeen >= 3                    // it is traffic, not a fleet of one car
                    && traffic.TotalDistance > 500;      // and it went somewhere
            }
            // TightestGap returns its sentinel when no two vehicles shared a
            // road in the same direction at the sampled instant — which after
            // the local-destination fix is common, because the traffic spreads
            // out instead of queueing. That is a good thing about the city and a
            // bad thing about this check: "999" passing `>= 0` reads like proven
            // clearance and is actually no measurement at all. Reported as such,
            // and the real following-distance property is covered properly in
            // CoreTests, which samples every step of a three-minute run.
            bool gapMeasured = tightest < 900;

            // Frame cost, measured rather than assumed. Traffic is the first
            // system here that does work every frame for every visible object,
            // so its budget is a gate: if the per-frame cost of driving the whole
            // district ever crosses a few milliseconds, that is a regression
            // worth failing a build over, and it should be found in CI rather
            // than in a stutter on the player's machine.
            //
            // AND IT HAS TO HAVE MEASURED SOMETHING. This read
            // "trafficCost == null || MeanMs < 4.0", which passes when the
            // profiler recorded nothing at all — so a build where the timing
            // scope stopped being entered would go green on the strength of
            // having no data. Same disease as the coverage hole below, one
            // system down: an absent measurement is not a passing one. Traffic
            // demonstrably runs (the gate above requires ten vehicles), so no
            // samples means the instrumentation broke.
            var trafficCost = Perf.Get("traffic");
            bool perfOk = trafficCost != null && trafficCost.Samples > 0 && trafficCost.MeanMs < 4.0;

            // The vehicle description (spec §4). Only meaningful if the bot was
            // seen at all; when it was, somebody must be able to describe the car.
            //
            // LATCHED WHILE THE RUN HAPPENS, not read out of the mill at the
            // end, and the difference is not academic: the Fall deliberately
            // wipes every rumor about the player — three days inside and the
            // street stops guessing, which is the whole point of that beat. So
            // an end-of-run read asks "can anybody still describe the car" and
            // gets a truthful no, having actually asked a question about the
            // Fall rather than about the car. The gate wants to know the fact
            // was FILED. It was; something erased it afterwards, on purpose.
            bool vehicleFactSeen = _vehicleFactLatched;
            var millV = _game.Gossip != null ? _game.Gossip.Mill : null;
            if (millV != null)
                foreach (var lead in millV.Leads("player"))
                    if (lead.TopicKey != null && lead.TopicKey.StartsWith("player.vehicle_d"))
                        vehicleFactSeen = true;
            // Only meaningful if a drop was witnessed AFTER the car turned up.
            //
            // The first version of this gate said "if there were any night
            // witnesses at all, somebody must be able to describe the car", and
            // it went red the first time the bot lost the week on day three —
            // the campaign ended before day five, the car never arrived, and the
            // gate failed the build for something that had not happened yet. A
            // test that assumes the campaign gets as far as it did last time is
            // not testing the game, it is testing the runner.
            bool sawADropWithTheCar = _witnessesWhenCarArrived >= 0
                && _game.NightWitnesses > _witnessesWhenCarArrived;
            bool witnessCarOk = !sawADropWithTheCar || vehicleFactSeen;

            // The consequence layer (roadmap M11). Four things, and every one of
            // them is about persistence rather than about the moment: the wound
            // outlived the day it happened, neglect made it worse, treatment
            // stopped exactly that, and a feud is still standing between two
            // people who have to work together.
            bool harmOk = true;
            if (SimMode.Days >= 6)
            {
                bool stillHurt = _harmSampled && _harmStillHurt;
                bool turned = _harmSampled && _harmTurned;
                bool roccoFine = true;
                foreach (var i in _game.Harm.All)
                    if (i.PersonId == "Rocco" && i.WentBad) roccoFine = false;
                harmOk = _harmStaged
                    && stillHurt                                        // days later, still carrying it (sampled day 8)
                    && turned                                           // and it got worse for being ignored (sampled day 8)
                    && roccoFine                                        // while the treated one did not
                    && _game.Harm.ScarsOf("Sam") >= 1                   // the count does not heal
                    && _harmCapabilityAtInjury < 1.0                    // it cost him something
                    && _harmFeudLive                                    // the feud stood while both were around (sampled day 8)
                    && _harmFeudBlocks;                                 // and it was a scheduling problem (sampled day 8)
            }

            // The exchange is real if it is not always the same answer. Over
            // eighteen calls across nine days the bot must have got through at
            // least once AND missed at least once — a phone that always works
            // is a menu, and one that never does is a wall.
            int rings = _callsAnswered + _callsWrongPerson + _callsRangOut;
            bool phonesOk = _game.Phones.All.Count >= 4
                && (SimMode.Days < 4 || (rings > 0 && _callsAnswered + _callsWrongPerson > 0
                                          && _callsAnswered < rings));

            // Every panel opened, said something, closed, and gave the player
            // back their controls. The last of those is the one that matters:
            // a panel that cannot be closed leaves the player standing in a city
            // they can no longer move around in, which is the worst bug this
            // game can have and was invisible to every test we owned.
            int panelsOk = 0, panelsBad = 0;
            var badPanels = new List<string>();
            if (_uiPanels != null)
                foreach (var r in _uiPanels)
                {
                    if (r.Ok) panelsOk++;
                    else { panelsBad++; badPanels.Add(r.ToString()); }
                }
            // Seven now: six panels plus the rebind screen — and the floor
            // asserts the COUNT so a silently missing report reds the build
            // rather than shrinking the walk (audit 2026-07-27 pattern).
            bool uiOk = _uiSmokeRun && panelsBad == 0 && panelsOk >= 7;

            // P5 BUDGETS. The deterministic ones gate (caps are design
            // numbers, so exceeding them is a leak, not a slow machine); the
            // timing ones report, because CI hardware is weather.
            int walkerCount = 0;
            foreach (var w in FindObjectsByType<NpcWalker>(FindObjectsSortMode.None)) walkerCount++;
            int millCount = 0, crowdMill = 0, strandedEmpty = 0;
            if (mill != null)
                foreach (var a in mill.Agents)
                {
                    millCount++;
                    if (a.Id == null || a.Id.Length < 2 || a.Id[0] != 'r' || !char.IsDigit(a.Id[1])) continue;
                    crowdMill++;
                    // The leak signal is an EMPTY crowd agent stranded outside
                    // the band: carrying nothing, Forget would take them, and
                    // the LOD should have called it. Carriers above the band
                    // cap are pillar P5 working (run 30339120018: 132 crowd
                    // agents, 110 in band + 22 rumor-carriers — healthy).
                    bool empty = a.Rumors.Count == 0 && a.Memory.Events.Count == 0
                        && a.Suppressed.Count == 0 && !a.Leashed;
                    var res = _game.Populace != null ? _game.Populace.ById(a.Id) : null;
                    // In-band is anything not Far: the NEAR band's 22 walkers
                    // are in the mill too (a walker you can talk to needs a
                    // gossip brain), and counting them as stranded red a
                    // healthy build (run 30340665815: strandedEmpty=22, the
                    // walker cap to the digit).
                    bool inBand = res != null && res.Band != Lod.Far;
                    if (empty && !inBand) strandedEmpty++;
                }
            long heapMb = System.GC.GetTotalMemory(false) / (1024 * 1024);
            double avgMs = _frames > 0 ? _frameSum / _frames * 1000.0 : 0;
            // Gate on the DESIGN CAPS directly: the crowd's walkers and the
            // crowd's mill agents against their own ceilings. Totals are
            // reported, never gated — the authored cast grows by design (heads
            // spawn at PP7, the inspector at the audit), and a guessed
            // total-ceiling red a healthy build (run 30335994335: 42 authored
            // walkers against my invented "+40 headroom").
            bool budgetsOk = _game.CrowdWalkerCount <= GameController.CrowdWalkerCap
                && strandedEmpty == 0;

            bool accessOk = _game.Gates.Count > 0;
            foreach (var gate in _game.Gates)
            {
                if (gate.Keys.Count == 0 || string.IsNullOrEmpty(gate.Doorman)
                    || string.IsNullOrEmpty(gate.Refusal)) { accessOk = false; break; }
                var pauper = new AccessState { Hour = 3, Dress = "coat", Money = 0 };
                var turned = Doors.Try(gate, pauper);
                if (turned.Allowed) continue;                 // openable even with nothing
                if (turned.Nearest == null || string.IsNullOrEmpty(turned.Hint))
                { accessOk = false; break; }                  // refused without teaching
            }

            // The Director (roadmap M8). CI has no API key, so the nightly pass
            // never authors anything — which is exactly the property worth
            // gating: a game with no model available must run a completely
            // ordinary week. So the assertions are that it stayed silent, that
            // its book survives its own codec, and — the part that would
            // actually break — that a pressure fired by hand goes through the
            // real primitives and lands. That last one is scripted below.
            var dirSnap = MiniJson.Serialize(_game.Directorate.Capture());
            var dirTwin = new DirectorBook();
            dirTwin.Restore(MiniJson.AsObject(MiniJson.Deserialize(dirSnap)));
            bool directorOk =
                dirTwin.Pending.Count == _game.Directorate.Pending.Count
                && dirTwin.LastRunDay == _game.Directorate.LastRunDay
                && dirTwin.History.Count == _game.Directorate.History.Count
                // Whatever it did or did not schedule, nothing may be in flight
                // that names a pressure kind the game cannot run.
                && _game.Directorate.Pending.TrueForAll(p => Pressures.Known(p.Kind))
                // And the hand-fired pressure below must have landed.
                && (!_game.Campaign.OpenMode || SimMode.Days < 9 || _directorFired);

            // _weekLostVerdict too: ForceOpenMode rewrites any pre-open verdict
            // to Ongoing at day 8, which made the cast-out clause unfalsifiable
            // (audit 2026-07-27) — the sampled copy is the honest record.
            bool verdictSane = camp.Verdict != Verdict.LostCastOut && _weekLostVerdict != Verdict.LostCastOut &&
                // While the campaign is live, most nights must actually post a job.
                (camp.Verdict != Verdict.Ongoing || camp.JobsDone + camp.JobsMissed >= SimMode.Days - 2 - _frozenCloses);

            // Act I in-engine proof (act1-draft.md): PP1/PP2 fired on their days,
            // PP4 tracked the lena_ledger transition exactly, Noor is in the mill,
            // and the PP7 posture answer plants a Fact in every cast brain — the
            // sim answers here if the week ended before the verdict screen could.
            if (_game.ActOne.Posture == null) _game.AnswerPosture("takeover");
            bool postureFact = false;
            var lenaG = mill != null ? mill.Get("Lena") : null;
            if (lenaG != null)
                postureFact = lenaG.Knowledge.CheckClaim(new Fact("player", "posture", "takeover")) == ClaimResult.Consistent;
            bool ledgerKnown = _game.HooksBook.ById("lena_ledger") != null && _game.HooksBook.ById("lena_ledger").KnownToPlayer;
            bool actOneOk = _game.ActOne.Pp1Fired && _game.ActOne.Pp2Fired
                && _game.ActOne.Pp4Fired == ledgerKnown
                && (mill == null || mill.Get("Noor") != null)
                && postureFact;

            // Open mode (open-city-spec.md): if the bot won the week, the city must
            // have opened and kept closing days past seven; and one Fall (organic
            // or the day-9 staged one) must have run — proven by the street holding
            // player.did_time as hard fact, an invariant later play can't erase.
            bool openModeOk = !_game.Campaign.OpenMode || _game.Campaign.DaysClosed >= 8 - _frozenCloses;
            bool fallOk = true;
            if (_game.Campaign.OpenMode && SimMode.Days >= 9)
            {
                var adaG = mill != null ? mill.Get("Ada") : null;
                fallOk = _game.Campaign.Falls >= 1 && adaG != null
                    && adaG.Knowledge.CheckClaim(new Fact("player", "did_time", "true")) == ClaimResult.Consistent;
            }

            // Empire v1 (open-city-spec §2): the scripted day-8 beat must leave a
            // squeezed shop, a crewed racket that has actually paid, an awake
            // rival — and the whole book must survive its own codec.
            bool empireOk = true;
            if (_game.Campaign.OpenMode && SimMode.Days >= 9)
            {
                var shop = _game.Empire.BusinessOf("pawnshop");
                var snap = MiniJson.Serialize(_game.Empire.Capture());
                var twin = EmpireSetup.Build();
                twin.Restore(MiniJson.AsObject(MiniJson.Deserialize(snap)));
                empireOk = shop != null && shop.Owned && shop.AcquiredVia == "debt"
                    && _game.Empire.CrewOf("Sam") != null
                    && (_game.Empire.RacketOf("collection")?.Established ?? false)
                    && _game.Empire.TotalRacketIncome > 0
                    && _game.Empire.Rival.Stage >= 1
                    && MiniJson.Serialize(twin.Capture()) == snap;
            }

            // THE GATE THAT WOULD HAVE CAUGHT ALL OF THIS. Every conditional
            // check below is only worth its green tick if its precondition was
            // actually reached, and on run 30248511085 none of them were: nine
            // simulated days, the week lost on day six, and the entire open
            // city — empire, Director, operations, Acts II and III — skipped
            // while the build reported success.
            //
            // So the run now has to prove it got there. Not "the open city
            // behaved", which the individual gates say; just "the open city
            // HAPPENED", which nothing said.
            bool coverageOk = SimMode.Days < 8 ||
                (_game.Campaign.OpenMode
                 && _game.Empire.Businesses.Exists(b => b.Owned)      // the empire beat ran
                 && _actThreeStaged                                    // Act III was reached
                 && _planRan                                           // an operation went through
                 && _directorFired);                                   // and the Director fired one

            // Act II (act2-draft.md). All seven pressure points are wired; none
            // of them was ever PROVEN, which is a different thing and the reason
            // this exists — Act I and Act III both have gates and the middle of
            // the spine had none.
            //
            // A nine-day sim cannot reach most of these preconditions honestly
            // (PP7 wants an organization at its summit), and staging all seven
            // would only prove that the staging works. So this asserts the
            // IMPLICATION instead: wherever a pressure point's condition is
            // true, its flag must be set. That catches the failure that actually
            // matters — a beat that can never fire, or one whose condition
            // drifted away from its firing site — without pretending the bot
            // played a longer campaign than it did.
            var a2 = _game.ActTwo;
            bool act2Ok = true;
            var act2Missed = new List<object>();
            if (a2.Opened)
            {
                // A beat counts as MISSED only if it stayed due and unfired
                // across consecutive hourly samples — see ActTwoSample for why
                // one end-of-run look is a race the gate loses rather than a
                // test it passes. The conditions themselves live in ActTwoOwed,
                // so this and the sampler cannot drift apart.
                ActTwoSample(_game.Now);
                foreach (var kv in _act2Owed)
                    if (kv.Value >= ActTwoGraceSamples) { act2Ok = false; act2Missed.Add(kv.Key); }
                act2Ok &= MiniJson.Serialize(a2.Capture()) ==
                          MiniJson.Serialize(RoundTripActTwo(a2).Capture());
            }

            // Act III (act3-draft.md). Only asserted when the sim actually got
            // far enough to stage it — the gate must never assume the bot
            // reaches day 9, which is exactly the brittleness that made the
            // car gate lie on a short run.
            bool actThreeOk = true;
            if (_actThreeStaged)
            {
                var a3 = _game.ActThree;
                actThreeOk = a3.Opened && a3.Pp1Fired && a3.AuditClosed
                    && _actThreeEnding != Ending.None
                    // Handing over is the only ending you reach for, so if the
                    // bot reached for it, it must be the one it got.
                    && (!_actThreeHandedOver || _actThreeEnding == Ending.Quiet)
                    // And the act must survive its own codec, like everything else.
                    && MiniJson.Serialize(a3.Capture()) ==
                       MiniJson.Serialize(RoundTrip(a3).Capture());
            }

            var report = new Dictionary<string, object>
            {
                { "simDays", SimMode.Days },
                { "coverageOk", coverageOk },
                { "daysSkipped", _daysSkipped },
                { "openModeForced", _openModeForced },
                { "endScreenDismissed", _endScreenDismissed },
                { "weekLostAs", _weekLostVerdict.ToString() },
                { "dayJobStaged", _dayJobStaged },
                { "actTwoOpened", _game.ActTwo.Opened },
                { "actTwoFired", $"{(_game.ActTwo.Pp1Fired ? 1 : 0)}{(_game.ActTwo.Pp2Fired ? 1 : 0)}" +
                                 $"{(_game.ActTwo.Pp3Fired ? 1 : 0)}{(_game.ActTwo.Pp4Fired ? 1 : 0)}" +
                                 $"{(_game.ActTwo.Pp5Fired ? 1 : 0)}{(_game.ActTwo.Pp6Fired ? 1 : 0)}" +
                                 $"{(_game.ActTwo.TableFired ? 1 : 0)}" },
                { "actTwoMissed", act2Missed },
                { "actTwoOk", act2Ok },
                { "actThreeClosesDay", _game.ActThree.AuditClosesDay },
                { "actThreeStaged", _actThreeStaged },
                { "actThreeWhy", _actThreeWhy },
                { "actThreeOpened", _game.ActThree.Opened },
                { "actThreeEnding", _actThreeEnding.ToString() },
                { "actThreeHandedOver", _actThreeHandedOver },
                { "actThreeOk", actThreeOk },
                { "finalTime", _game.Now.ToString() },
                { "errorCount", _errors.Count },
                { "errors", new List<object>(_errors.ToArray()) },
                { "npcsMoved", npcsMoved },
                { "lampToggles", WorldBuilder.LampToggleCount },
                { "gossipHeat", gossipHeat },
                { "secretReachedDay", secretReachedDay },
                { "discreditWorks", discreditWorks },
                { "jobsDone", camp.JobsDone },
                { "jobsMissed", camp.JobsMissed },
                { "outfitPatience", camp.OutfitPatience },
                { "totalTakings", _game.TotalTakings },
                { "nightWitnesses", _game.NightWitnesses },
                { "knownLeads", _game.Knowledge.Count },
                { "verdict", camp.Verdict.ToString() },
                { "playerCash", _game.PlayerCash },
                { "cleanCash", _game.Wallet.Clean },
                { "dirtyCash", _game.Wallet.Dirty },
                { "washed", _game.Wallet.TotalWashed },
                { "maxCoatedWitnessConf", _game.MaxCoatedWitnessConf },
                { "osseiSpawned", _game.EllisSpawned },
                { "peakHeat", _game.ObservedPeakHeat },
                { "confrontations", _game.TotalConfrontations },
                { "checksRun", _game.Gossip != null ? _game.Gossip.ChecksRun : 0 },
                { "overheard", _game.Gossip != null ? _game.Gossip.Overheard : 0 },
                { "osseiInterviews", _game.EllisInterviews.Count },
                { "debtsOutstanding", System.Linq.Enumerable.Count(System.Linq.Enumerable.Where(_game.Debts.All, d => d.Outstanding)) },
                { "saveLoadOk", saveLoadOk },
                { "beats", beatStates },
                { "secretsKnown", System.Linq.Enumerable.Count(_game.HooksBook.Known) },
                { "pp1", _game.ActOne.Pp1Fired }, { "pp2", _game.ActOne.Pp2Fired },
                { "pp4", _game.ActOne.Pp4Fired }, { "ledgerSecretKnown", ledgerKnown },
                { "noorInMill", mill != null && mill.Get("Noor") != null },
                { "posture", _game.ActOne.Posture ?? "" }, { "postureFactPlanted", postureFact },
                { "openMode", _game.Campaign.OpenMode }, { "outfitCutOff", _game.Campaign.OutfitCutOff },
                { "falls", _game.Campaign.Falls }, { "daysClosed", _game.Campaign.DaysClosed },
                { "npcCount", _npcs != null ? _npcs.Length : 0 },
                // Informational (nondeterministic): did a racket witness surface to
                // the player through the normal channels (warning/overheard)?
                { "racketLeadKnown", System.Linq.Enumerable.Any(_game.Knowledge.Entries,
                    k => k.TopicKey != null && k.TopicKey.StartsWith("player.racket")) },
                { "empireOwned", _game.Empire.Businesses.FindAll(b => b.Owned).Count },
                { "empireCrew", _game.Empire.Crew.Count }, { "racketIncome", _game.Empire.TotalRacketIncome },
                { "rivalStage", _game.Empire.Rival.Stage },
                { "machineStage", _game.Empire.ArmOf("machine").Stage },
                { "newcrewStage", _game.Empire.ArmOf("newcrew").Stage },
                { "shiftsWorked", _game.Job.ShiftsWorked },
                { "llmCalls", _game.Cost.TotalCalls },
                { "llmCostUsd", _game.Cost.EstimateUsd() },
                // Diagnostics for the next time the campaign ends somewhere
                // unexpected: which day it closed on, and whether the staged
                // beats got the chance to run at all.
                { "panelsOk", panelsOk },
                { "panelsBad", panelsBad },
                { "panelsBroken", new List<object>(badPanels.ToArray()) },
                { "phoneLines", _game.Phones.All.Count },
                { "callsAnswered", _callsAnswered },
                { "callsWrongPerson", _callsWrongPerson },
                { "callsRangOut", _callsRangOut },
                { "lostOnDay", _game.Campaign.DaysClosed },
                { "carArrived", _witnessesWhenCarArrived >= 0 },
                { "dropSeenWithCar", sawADropWithTheCar },
                { "harmInjuries", _game.Harm.All.Count },
                { "harmFeuds", _game.Harm.Feuds.Count },
                { "samScars", _game.Harm.ScarsOf("Sam") },
                { "samCapability", System.Math.Round(_game.Harm.Capability("Sam", _game.Now.Day), 3) },
                { "playerName", _game.Me.Full },
                { "vehicleFactSeen", vehicleFactSeen },
                { "signsBuilt", StreetFurniture.SignCount },
                { "vehicles", traffic != null ? traffic.Vehicles.Count : 0 },
                { "vehicleKinds", kindsSeen },
                { "trafficMetres", traffic != null ? System.Math.Round(traffic.TotalDistance, 0) : 0 },
                { "tightestGap", gapMeasured ? (object)System.Math.Round(tightest, 2) : "not-measured" },
                { "vehiclesOffRoad", offRoad },
                { "trafficYields", traffic != null ? traffic.YieldsToPeople : 0 },
                { "frames", Perf.FrameCount },
                { "meanFrameMs", System.Math.Round(Perf.MeanFrameMs, 3) },
                { "p95FrameMs", System.Math.Round(Perf.FramePercentileMs(0.95), 3) },
                { "worstFrameMs", System.Math.Round(Perf.WorstFrameMs, 1) },
                { "perf", Perf.Report() },
                { "hourlySamples", _samples.Count },
                { "samples", _samples },
                { "screenshotCount", _screenshots.Count },
                { "screenshots", _screenshots },
            };
            System.IO.File.WriteAllText("sim-out/sim-report.json", MiniJson.Serialize(report));

            // THE RENDER, GATED (the-gap.md §3a). The fingerprint has been
            // diagnostic-only since it was written — it caught the neon
            // clipping defect because a human read the numbers, not because
            // anything failed. Lighting is now driven per frame from
            // LightModel, and a driven rig can break in ways a static one
            // could not: a curve that returns zero is a black street, a
            // runaway exposure is a white one, and either would ship.
            bool lightingOk = true;
            var lightingWhy = new List<string>();
            {
                double dayLuma = -1, nightLuma = -1, nightSat = -1;
                foreach (var entry in _screenshots)
                {
                    // _screenshots is List<object> because MiniJson wants it
                    // that way. Iterating it as a dictionary compiles fine in
                    // a syntax-only check and fails in Unity, which is where
                    // this cost twenty minutes.
                    var shot = entry as Dictionary<string, object>;
                    if (shot == null) continue;
                    string nm = shot.TryGetValue("path", out var pv) ? (pv as string ?? "") : "";
                    double luma = ShotNum(shot, "meanLuma");
                    // NEVER A BLACK FRAME and NEVER A BLOWN ONE. These two
                    // catch the whole family at once, whatever caused it.
                    if (luma < 0.012) { lightingOk = false; lightingWhy.Add($"black:{nm}:{luma:0.000}"); }
                    if (luma > 0.85) { lightingOk = false; lightingWhy.Add($"blown:{nm}:{luma:0.000}"); }
                    if (nm.Contains("noon")) dayLuma = luma;
                    if (nm.Contains("night")) { nightLuma = luma; nightSat = ShotNum(shot, "satPct"); }
                }
                // Night must actually be darker than noon. This is the one
                // that proves the day/night curves reach the RENDER rather
                // than merely being computed correctly in a test.
                if (dayLuma >= 0 && nightLuma >= 0 && nightLuma >= dayLuma)
                { lightingOk = false; lightingWhy.Add($"nightNotDarker:{nightLuma:0.000}>={dayLuma:0.000}"); }
                // And a night street must have COLOUR in it — lamps and neon.
                // A grey night is the failure mode the fog work exists to
                // prevent, and it is invisible to a luminance check.
                if (nightSat >= 0 && nightSat < 0.20)
                { lightingOk = false; lightingWhy.Add($"greyNight:{nightSat:0.00}%"); }
            }

            // THE SCORE, GATED. Computing the right mix in a test proves the
            // curves; it does not prove the audio graph ever heard about it.
            // What is asserted is that the stems exist, that they MOVED
            // across the run, and that the mix obeyed the rule the whole
            // design rests on — quieter under pressure, not louder.
            bool scoreOk = Audio.ScoreRunning && _scoreSamples >= 2
                && _scoreEnergyRange > 0.05
                && (_scoreHotUnease < 0 || _scoreHotUnease >= _scoreCalmUnease - 1e-6);

            // THE REFLECTIONS, GATED on all three things that can be wrong
            // independently of each other:
            //
            //   it never ran          — the probe is wired to nothing;
            //   it never stopped      — a dry street is paying for a mirror;
            //   it ran every frame    — the distance gate is not gating.
            //
            // The last one is the reason this gate exists at all. The first
            // two show up in a picture; a probe re-rendering on every one of
            // several thousand wet frames looks EXACTLY like a correctly
            // gated one and costs six extra camera passes a frame to do it.
            bool reflOk = _reflWetFrames > 0 && _reflDryFrames > 0
                && ReflRefreshes > 0
                && ReflRefreshes < _reflWetFrames / 4;

            // Bodies exist, their legs move through a real cycle, and the
            // rig does NOT solve for everyone at once. The knee spread is
            // the load-bearing part: a rig bound to a body it never drives
            // reports a constant, and a constant knee is a mannequin being
            // dragged rather than a person walking.
            bool bodiesOk = _bodySamples > 0 && _bodyRigs >= 2
                && _bodyMaxKnee - _bodyMinKnee > 10
                // Whenever somebody WAS out of range, somebody was culled.
                // Never "a cull happened", which is unsatisfiable in a city
                // where everybody is close by and would make this gate a
                // report on where the walkers wandered.
                && (_bodyCullable == 0 || _bodyCulled > _bodyCullable / 2)
                // 8cm apart at minimum: enough that the variation reached the
                // transforms rather than only the struct.
                && _bodyTallest - _bodyShortest > 0.08;

            // OCCLUSION, gated on the A/B rather than on the counter.
            //
            // `Applied > 0` proves three Blits happened. It does not prove
            // the shader compiled, that DepthNormals was requested, that the
            // AO texture was bound, or that the composite multiplied by it —
            // and every one of those failures leaves the counter climbing and
            // the picture unchanged. The frame rendered without it has to
            // come out BRIGHTER, and by enough to be a real effect rather
            // than dither.
            //
            // Both directions matter. Too little and it is doing nothing;
            // too much and it is grime rather than contact, which is the
            // characteristic failure of screen-space occlusion and the reason
            // this has an upper bound at all.
            double aoDelta = (_aoOn >= 0 && _aoOff >= 0) ? _aoOff - _aoOn : -1;
            bool aoOk = FilmGrade.Applied > 0 && aoDelta > 0.002 && aoDelta < 0.09;

            // THE STREET TALKS TO ITSELF. Rumours have passed along the
            // contact graph since the first week and the city has shown none
            // of it — a dozen people walking past each other in silence while
            // the thing the game is about happens underneath.
            //
            // Gated at all because the staging has three ways to silently
            // never fire: both parties already talking, nowhere off-road to
            // stand, or a pair the mill likes that never happens to be near
            // each other. Any of those leaves a street that looks exactly
            // like the old one, and the only difference between "the feature
            // is subtle" and "the feature is absent" is a number.
            bool confabOk = _game.Gossip == null || _game.Gossip.Confabs > 0;

            // Every gate, by name, so a failure says WHICH one.
            //
            // Getting this out of CI used to mean reading a job log that the
            // API truncates and the two ASCII screenshots fill, or downloading
            // an artifact from a host the sandbox cannot reach. The one line
            // worth having was the one that never survived. Now it is printed
            // last, alone, and only when something is wrong.
            var gates = new (string name, bool ok)[]
            {
                ("noErrors", _errors.Count == 0), ("npcsMoved", npcsMoved),
                ("lamps", WorldBuilder.LampToggleCount >= 2), ("screenshots", _screenshots.Count > 0),
                ("secretReachedDay", secretReachedDay), ("discredit", discreditWorks),
                ("jobRan", jobRan), ("takingsBanked", takingsBanked), ("verdictSane", verdictSane),
                ("knowledge", knowledgeWorks), ("launder", launderWorks), ("disguise", disguiseWorks),
                ("beats", beatsResolved), ("ossei", osseiOk), ("saveLoad", saveLoadOk),
                ("actOne", actOneOk), ("openMode", openModeOk), ("fall", fallOk), ("empire", empireOk),
                ("population", populationOk), ("dayJob", dayJobOk), ("economy", economyOk),
                ("director", directorOk), ("crowd", crowdOk), ("access", accessOk), ("ops", opsOk),
                ("traffic", trafficOk), ("perf", perfOk), ("witnessCar", witnessCarOk),
                ("harm", harmOk), ("phones", phonesOk), ("ui", uiOk), ("budgets", budgetsOk),
                ("actTwo", act2Ok), ("actThree", actThreeOk), ("coverage", coverageOk),
                ($"lighting[{string.Join("|", lightingWhy)}]", lightingOk),
                // The streets must actually be dressed. A model that computes
                // beautiful placements nothing ever builds is the exact shape
                // of every other "verified in a test, absent in the game"
                // defect this project has found.
                ($"dressing[{WorldBuilder.Dressed}]", WorldBuilder.Dressed >= 150),
                // THE GATE NAME CARRIES ITS OWN NUMBERS. The FAILING GATES
                // line is the only channel that reliably survives out of CI —
                // the log tail is a fixed window that post-job cleanup fills,
                // the artifacts are on a host this environment cannot reach,
                // and the check-run summary came back empty when it was
                // needed. A gate that can only say its own name costs a
                // twenty-minute round trip to learn WHY, which is what this
                // one cost the first time it fired.
                ($"score[running={Audio.ScoreRunning} n={_scoreSamples} " +
                 $"range={_scoreEnergyRange:0.000} calm={_scoreCalmUnease:0.00}@{_scoreCalmestHeat:0.00} " +
                 $"hot={_scoreHotUnease:0.00}@{_scoreHottestHeat:0.00}]", scoreOk),
                ($"reflect[wet={_reflWetFrames} dry={_reflDryFrames} " +
                 $"refresh={ReflRefreshes} max={_reflMaxStrength:0.00}]", reflOk),
                ($"bodies[rigs={_bodyRigs} solved={_bodyMaxSolved} " +
                 $"knee={_bodyMinKnee:0.0}..{_bodyMaxKnee:0.0} cull={_bodyCulled}/{_bodyCullable} " +
                 $"h={_bodyShortest:0.00}..{_bodyTallest:0.00}]", bodiesOk),
                ($"ao[applied={FilmGrade.Applied} on={_aoOn:0.0000} " +
                 $"off={_aoOff:0.0000} delta={aoDelta:0.0000}]", aoOk),
                ($"confab[{(_game.Gossip != null ? _game.Gossip.Confabs : -1)}]", confabOk),
            };
            var failed = new List<string>();
            foreach (var g in gates) if (!g.ok) failed.Add(g.name);
            bool pass = failed.Count == 0;
            Debug.Log($"SimDirector: done. errors={_errors.Count} npcsMoved={npcsMoved} " +
                      $"lampToggles={WorldBuilder.LampToggleCount} screenshots={_screenshots.Count} " +
                      $"gossipHeat={gossipHeat:0.00} secretReachedDay={secretReachedDay} " +
                      $"discreditWorks={discreditWorks} jobsDone={camp.JobsDone} jobsMissed={camp.JobsMissed} " +
                      $"patience={camp.OutfitPatience:0.00} takings={_game.TotalTakings} " +
                      $"witnesses={_game.NightWitnesses} knownLeads={_game.Knowledge.Count} " +
                      $"clean={_game.Wallet.Clean} dirty={_game.Wallet.Dirty} washed={_game.Wallet.TotalWashed} " +
                      $"coatConf={_game.MaxCoatedWitnessConf:0.00} ossei={_game.EllisSpawned} peakHeat={_game.ObservedPeakHeat:0.00} " +
                      $"checks={(_game.Gossip != null ? _game.Gossip.ChecksRun : 0)} confronts={_game.TotalConfrontations} " +
                      $"saveLoad={saveLoadOk} actOne={actOneOk} pp4={_game.ActOne.Pp4Fired} posture={_game.ActOne.Posture} " +
                      $"openMode={_game.Campaign.OpenMode} falls={_game.Campaign.Falls} cutOff={_game.Campaign.OutfitCutOff} " +
                      $"daysClosed={_game.Campaign.DaysClosed} openModeOk={openModeOk} fallOk={fallOk} verdictSane={verdictSane} " +
                      $"empireOk={empireOk} racketIncome={_game.Empire.TotalRacketIncome} rivalStage={_game.Empire.Rival.Stage} " +
                      $"coverageOk={coverageOk} openModeForced={_openModeForced} endScreen={_endScreenDismissed} " +
                      $"daysSkipped={_daysSkipped} endDay={_endDay} " +
                      $"weekLostAs={_weekLostVerdict} frozenCloses={_frozenCloses} walkers={walkerCount} crowdWalkers={_game.CrowdWalkerCount} millAgents={millCount} crowdMill={crowdMill} strandedEmpty={strandedEmpty} heapMb={heapMb} frameAvgMs={avgMs:0.0} frameWorstMs={_frameWorst * 1000.0:0} " +
                      $"actTwoOpened={a2.Opened} actTwoOk={act2Ok} actTwoMissed=[{string.Join(",", act2Missed)}] " +
                      $"actThree={_actThreeStaged} opened={_game.ActThree.Opened} [{_actThreeWhy}] " +
                      $"ending={_actThreeEnding} handed={_actThreeHandedOver} actThreeOk={actThreeOk} " +
                      $"npcs={(_npcs != null ? _npcs.Length : 0)} populationOk={populationOk} " +
                      $"shifts={_game.Job.ShiftsWorked} dayJobStaged={_dayJobStaged} dayJobOk={dayJobOk} " +
                      $"street={_game.Economy.Prosperity:0.00} prices={_game.Economy.PriceLevel:0.00} " +
                      $"takingsFactor={_game.Economy.TakingsFactor:0.00} economyOk={economyOk} " +
                      $"directorPending={_game.Directorate.Pending.Count} directorFired={_directorFired} directorOk={directorOk} " +
                      $"pop={(_game.Populace != null ? _game.Populace.Residents.Count : 0)} " +
                      $"gates={_game.Gates.Count} accessOk={accessOk} " +
                      $"targets={_game.Targets.Count} planRan={_planRan} opsOk={opsOk} " +
                      $"vehicles={(traffic != null ? traffic.Vehicles.Count : 0)} kinds={kindsSeen} " +
                      $"trafficMetres={(traffic != null ? traffic.TotalDistance : 0):0} " +
                      $"gap={(gapMeasured ? tightest.ToString("0.00") : "not-measured")} " +
                      $"offRoad={offRoad} yields={(traffic != null ? traffic.YieldsToPeople : 0)} trafficOk={trafficOk} " +
                      $"signs={StreetFurniture.SignCount} vehicleFact={vehicleFactSeen} witnessCarOk={witnessCarOk} " +
                      $"carArrived={_witnessesWhenCarArrived >= 0} dropWithCar={sawADropWithTheCar} " +
                      $"injuries={_game.Harm.All.Count} feuds={_game.Harm.Feuds.Count} " +
                      $"samScars={_game.Harm.ScarsOf("Sam")} samCap={_game.Harm.Capability("Sam", _game.Now.Day):0.00} " +
                      $"harmOk={harmOk} name={_game.Me.Full} " +
                      $"lines={_game.Phones.All.Count} answered={_callsAnswered} " +
                      $"wrongPerson={_callsWrongPerson} rangOut={_callsRangOut} phonesOk={phonesOk} " +
                      $"panelsOk={panelsOk} panelsBad={panelsBad} uiOk={uiOk} " +
                      $"{(badPanels.Count > 0 ? "broken=[" + string.Join(",", badPanels) + "] " : "")}" +
                      $"{Perf.Summary()} trafficMs={(trafficCost != null ? trafficCost.MeanMs : 0):0.000} perfOk={perfOk} " +
                      // mean/median/peak bodies within 20m and within 8m,
                      // sampled every in-game hour across the whole run.
                      $"seen20={Dist(_within20)} seen8={Dist(_within8)} " +
                      $"near={(_game.Populace != null ? _game.Populace.CountIn(Lod.Near) : 0)} " +
                      $"mid={(_game.Populace != null ? _game.Populace.CountIn(Lod.Mid) : 0)} crowdOk={crowdOk} " +
                      $"beats=[{string.Join(",", beatStates)}] " +
                      $"shafts={LightShaft.Count} wet={SceneLighting.Wetness:0.00} " +
                      $"dressed={WorldBuilder.Dressed} " +
                      $"reflWet={_reflWetFrames} reflDry={_reflDryFrames} " +
                      $"reflRefresh={ReflRefreshes} reflMax={_reflMaxStrength:0.00} reflOk={reflOk} " +
                      $"aoApplied={FilmGrade.Applied} aoDelta={aoDelta:0.0000} aoOk={aoOk} " +
                      $"confabs={(_game.Gossip != null ? _game.Gossip.Confabs : -1)} confabOk={confabOk} " +
                      $"rigs={_bodyRigs} rigSolved={_bodyMaxSolved} " +
                      $"knee={_bodyMinKnee:0.0}..{_bodyMaxKnee:0.0} cull={_bodyCulled}/{_bodyCullable} " +
                      $"height={_bodyShortest:0.00}..{_bodyTallest:0.00} bodiesOk={bodiesOk} " +
                      $"scoreSamples={_scoreSamples} scoreRange={_scoreEnergyRange:0.000} " +
                      $"calmUnease={_scoreCalmUnease:0.00}@heat{_scoreCalmestHeat:0.00} " +
                      $"hotUnease={_scoreHotUnease:0.00}@heat{_scoreHottestHeat:0.00} scoreOk={scoreOk} " +
                      $"lightingOk={lightingOk}{(lightingWhy.Count > 0 ? " [" + string.Join(",", lightingWhy) + "]" : "")} " +
                      $"verdict={camp.Verdict} pass={pass}");
            // Last line in the log, on purpose: whatever else scrolls past, this
            // is what a person reading a red build needs.
            if (!pass) Debug.LogError($"SimDirector: FAILING GATES: {string.Join(", ", failed)}");
            Application.Quit(pass ? 0 : 1);
        }

        /// A save-and-reload of the act, for the gate that proves an ending
        /// cannot be lost between one session and the next.
        static ActThreeState RoundTrip(ActThreeState a)
        {
            var twin = new ActThreeState();
            twin.Restore(MiniJson.AsObject(MiniJson.Deserialize(MiniJson.Serialize(a.Capture()))));
            return twin;
        }

        static ActTwoState RoundTripActTwo(ActTwoState a)
        {
            var twin = new ActTwoState();
            twin.Restore(MiniJson.AsObject(MiniJson.Deserialize(MiniJson.Serialize(a.Capture()))));
            return twin;
        }
    }
}
