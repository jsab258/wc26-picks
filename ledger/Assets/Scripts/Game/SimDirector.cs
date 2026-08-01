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

        /// How many stills get committed for review. Four: noon and night on
        /// the first two days the sim shoots. See `Shot`.
        const int MaxReviewStills = 4;
        int _reviewStills;
        readonly Dictionary<string, Vector3> _startPositions = new Dictionary<string, Vector3>();

        int _endDay;
        bool _finished;
        bool _forcedLedgerLearn;
        bool _forcedFall;
        bool _botAttendedABeat;
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
            // Counters are per-run or they are meaningless. Both of these
            // reset methods existed and neither had a caller, which is the
            // dead-field smell one file over from where PeakHush had it.
            Perceivers.ResetCounters();
            Standoff.Reset();
            // CAPTIONS ON FOR THE RUN. They are off by default and should be
            // — but a channel nobody exercises is a channel nobody finds out
            // is broken, and this one exists precisely for the players least
            // likely to be in the room when it fails. The self-test is the
            // only pass with the sound off that anybody is going to make
            // every build.
            GameSettings.Current.Captions = (int)CaptionLevel.SpeechAndSound;
            CaptionBar.ResetCounters();
            CaptionBar.Ensure();
            _npcs = UnityEngine.Object.FindObjectsByType<NpcWalker>(FindObjectsSortMode.None);
            foreach (var npc in _npcs) _startPositions[npc.DisplayName] = npc.transform.position;
            // Phase 3 reports witnesses by id, and turning an id back into the
            // person who has to react to blood on your coat needs the list.
            ViolenceHost.Reset();
            ViolenceHost.BindWalkers(_npcs);
            CoatHost.Reset();
            EvidenceHost.Reset();
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
                MeasureGlyphs();
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
                    // AND IT HAS TO BE A DENIABLE STORY.
                    //
                    // This took the strongest sensitive rumour in the day
                    // circle, full stop — and once the open city had produced
                    // four killings, the strongest sensitive rumour in the day
                    // circle was a BODY. `Discredit` refuses those, on purpose
                    // and loudly: "There is a body. No amount of denying makes
                    // it not be there." So the gate denied the one story the
                    // design guarantees cannot be denied, measured no change,
                    // and reported the design working as a failure.
                    //
                    // Third time this month the instrument was the thing at
                    // fault. The fix is not to weaken the rule; it is to test
                    // BOTH rules, since the run now reliably produces one of
                    // each: a deniable story must lose weight, and an
                    // indelible one must be refused by name.
                    string topic = null, value = null; double before = 0;
                    string hardTopic = null, hardValue = null;
                    foreach (var a8 in mill8.Agents)
                        if (a8.Circle == "day")
                            foreach (var r8 in a8.Rumors)
                            {
                                if (!r8.Sensitive) continue;
                                if (r8.Indelible)
                                {
                                    if (hardTopic == null)
                                    { hardTopic = r8.TopicKey; hardValue = r8.Content.Value; }
                                    continue;
                                }
                                if (r8.Confidence > before)
                                { before = r8.Confidence; topic = r8.TopicKey; value = r8.Content.Value; }
                            }

                    bool deniableOk;
                    if (topic == null)
                    {
                        // Nothing deniable to deny. That is a finding about the
                        // run, not a pass — the same "an absent measurement is
                        // not a passing one" the frame gate learned.
                        deniableOk = false;
                        Debug.Log("SimDirector: discredit had no deniable sensitive story in the day circle");
                    }
                    else
                    {
                        var res = mill8.Discredit(topic, value, _game.Now);
                        double after8 = 0;
                        foreach (var a8 in mill8.Agents)
                            if (a8.Circle == "day")
                                foreach (var r8 in a8.Rumors)
                                    if (r8.TopicKey == topic && r8.Confidence > after8) after8 = r8.Confidence;
                        deniableOk = after8 < before && res.Affected > 0;
                        Debug.Log($"SimDirector: discredit {topic}={value} {before:0.00}->{after8:0.00} "
                                  + $"({res.Outcome}, {res.Affected} telling(s))");
                    }

                    // The body, if the run made one. Reported either way so the
                    // next run says whether this half was exercised at all.
                    bool bodyRefused = true;
                    if (hardTopic != null)
                    {
                        var hard = mill8.Discredit(hardTopic, hardValue, _game.Now);
                        bodyRefused = hard.Outcome == DcOutcome.Indelible;
                        Debug.Log($"SimDirector: discredit on a body -> {hard.Outcome} "
                                  + $"({hard.Affected} affected), refused={bodyRefused}");
                    }
                    else
                    {
                        Debug.Log("SimDirector: no indelible story in the day circle to refuse");
                    }

                    _discreditWorked = deniableOk && bodyRefused;
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
            // AN OPEN BEAT OUTRANKS THE ERRAND, and this is a behaviour
            // change to the bot rather than a gate change.
            //
            // Every run reported beats=[tea:Skipped,toast:Skipped,...] and
            // passed, because the gate asked only that nothing was left
            // Pending and a Skipped beat is resolved. The bot prioritised
            // drops and never once walked to a porch, so four authored scenes
            // — and `Core/Framing`, the whole cinematic layer built on top of
            // them — had never run in-engine. Nothing was broken; nothing was
            // being executed.
            //
            // Attending is proximity to the marker, so the fix is to send the
            // bot there rather than to call Attend directly: calling it would
            // exercise the beat and skip the marker, the distance test and the
            // collision that fires off the back of it, which is most of what
            // there is to get wrong.
            //
            // Beats are an evening window and drops are night; the design note
            // on Beat says a determined player can thread both. This bot is
            // now determined.
            // ONE BEAT, THEN BACK TO WORK.
            //
            // Diverting whenever a beat was open cost the run its
            // `verdictSane` gate: the bot stood on a porch through the
            // evening instead of returning to the bar, so nights stopped
            // being closed and JobsDone+JobsMissed never reached the count
            // that gate requires. The gate was right and my change was
            // greedy.
            //
            // One is all the beats gate asks for and all the authored path
            // needs exercised. After that the errand outranks the invitation
            // again, which is also what a player with a business to run
            // would do.
            // BOUNDED BY THE WINDOW, NOT BY SUCCESS. The previous version
            // stopped diverting once a beat was Attended — a condition that
            // never became true, so the bot walked to a porch every evening
            // for nine days and never went back to work. `beats` and
            // `verdictSane` both failed, and they were one bug: an escape
            // hatch that only opens if the thing you are trying works is not
            // an escape hatch.
            //
            // Now it commits to the FIRST open beat it sees and gives up when
            // that beat's window closes, whatever happened. One evening is
            // what the beats gate asks for; the other eight go to the job.
            // AND IT LEAVES EARLY. The invitation goes out in the morning; a
            // player who only starts walking when the window opens has six
            // real seconds to get there. Three hours of lead is what somebody
            // who meant to go would give themselves.
            var openBeat = _game.Beats.Soon(_game.Now, 3);
            // One beat at a time, and a fresh attempt once that one's window
            // has closed. Committing to the first beat forever meant that if
            // `tea` happened to be unreachable the bot never tried `toast`,
            // `evening_d8` or `evening_d12` either — four skipped beats out
            // of one bad spot. Bounded by "until one is attended", not by
            // "until the first attempt".
            //
            // AND ONLY WHEN THERE IS NO WORK OUTSTANDING. Retrying every
            // window cost the run its jobs — 4 done fell to 2, missed rose to
            // 4, and the campaign lost outright — because the invitation kept
            // outranking the errand. That is the same greedy mistake as the
            // first version, one level up: bounding the number of ATTEMPTS
            // does not bound the time they take.
            //
            // The errand always wins now, and the porch gets whatever is
            // left. Which is also what somebody with a business to run would
            // do, and it makes the beat something the player chooses at a
            // cost rather than something the bot does instead of working.
            // BOUNDED BY A BUDGET, which is the third shape of this and the
            // one that works.
            //
            // "Until it succeeds" never opened, so the bot loitered for nine
            // days. "One window then give up" cost all four beats to one bad
            // spot. "Only when no work is outstanding" never fired at all —
            // there is ALWAYS a job or a parcel, so beatTried came back
            // `none` and the authored path still never ran.
            //
            // A time budget cannot fail in any of those ways. Ninety in-game
            // minutes across nine days is an hour and a half the errand can
            // afford, it is spent on whichever beat is open when the bot has
            // it, and when it runs out the job has the bot back for good.
            // THE BUDGET IS IN REAL SECONDS, and the previous one was in game
            // minutes, which is why none of the four earlier fixes worked.
            //
            // The sim runs at twenty game-minutes per real second. Ninety
            // game minutes of "budget" is FOUR AND A HALF REAL SECONDS of
            // walking. The beat's own window — two game hours — is six. The
            // bot was never failing to path; it was being given six seconds
            // to cross a district, and every fix I aimed at radius, marker
            // and host position was aimed at geometry when the problem was
            // arithmetic.
            //
            // Walking takes real time whatever the clock is doing. Forty
            // seconds is roughly a hundred and fifty metres at walking pace,
            // and it costs thirteen game hours out of nine days.
            const double BeatBudgetRealSeconds = 40;
            if (openBeat == null) _beatBotTried = null;
            else if (_beatBotTried == null && _beatChaseSeconds < BeatBudgetRealSeconds)
                _beatBotTried = openBeat.Id;
            foreach (var b in _game.Beats.All)
                if (b.State == BeatState.Attended) { _botAttendedABeat = true; break; }
            bool chasing = !_botAttendedABeat && _beatChaseSeconds < BeatBudgetRealSeconds
                           && openBeat != null && openBeat.Id == _beatBotTried;
            if (chasing) _beatChaseSeconds += Time.deltaTime;
            var beatSpot = chasing ? _game.OpenBeatSpot : null;

            // AND SAY WHY IF IT MISSES. Attendance needs the player within
            // 2.5m of the marker; a run that reports "no beat attended" and
            // nothing else cannot distinguish "never went" from "went and
            // stood two and a half metres away".
            // EVERY FRAME, NOT EVERY HOUR. The hourly sample reported a
            // closest approach of ten metres for three runs running, and an
            // hourly sample simply cannot see a bot that walks past the spot
            // between two ticks of the clock. Three fixes have now been aimed
            // at a number that was never measuring what it claimed — the
            // ruler again, and this time it cost three build cycles.
            if (chasing && beatSpot.HasValue)
            {
                var here = _player.transform.position;
                float d = Vector2.Distance(new Vector2(here.x, here.z),
                                           new Vector2(beatSpot.Value.x, beatSpot.Value.z));
                if (d < _beatClosestApproach) _beatClosestApproach = d;
                // Separately: is there a marker to attend at all? Attendance
                // is gated on the marker existing, so "never got close" and
                // "got close to a beat with no marker" are different failures
                // that have been reading identically.
                if (_game.HasBeatMarker) _beatMarkerSeen = true;
                if (now.Hour != _lastBeatChaseHour)
                {
                    _lastBeatChaseHour = now.Hour;
                    Debug.Log($"SimDirector: chasing beat {openBeat.Id} at {now.Hour:00}:00, "
                              + $"{d:0.0}m away, marker={_game.HasBeatMarker}");
                }
            }
            var job = _game.ActiveJobPos ?? _game.DayJobTargetPos; // night drops outrank; mornings go to parcels
            var target = beatSpot.HasValue
                ? new Vector3(beatSpot.Value.x, 0, beatSpot.Value.z)
                : job.HasValue ? new Vector3(job.Value.x, 0, job.Value.z) : Waypoints[_waypointIndex];
            _player.AutoMoveTarget = target;
            if (!job.HasValue &&
                Vector3.Distance(new Vector3(_player.transform.position.x, 0, _player.transform.position.z), target) < 1.2f)
                _waypointIndex = (_waypointIndex + 1) % Waypoints.Length;

            StageConfrontation(now);
            StageThePlaces(now);
            StageCarryAndThreat(now);
            StageProvenance(now);
            StagePerception(now, ref target);
            _player.AutoMoveTarget = target;

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

            // THE WITNESSES ARE WALKING, so somebody has to move them. Without
            // this the delivery window is a list that fills and never empties:
            // dispatched, never arriving, and the mill never learning a thing.
            //
            // Indelible on arrival — Core's rule, not this file's. What is
            // decided here is only what the fact SAYS, because the map and the
            // words belong to the game.
            // ONE READING OF THE CLOCK PER FRAME, and it has to be taken
            // unconditionally.
            //
            // This used to be taken inside the `InFlight.Count > 0` guard
            // below, which works for deliveries by luck: with nothing in
            // flight, nothing needs the delta. Blood ages on the same clock,
            // and with the reading still inside the guard a stain taken on a
            // quiet night would have sat un-aged until the next delivery and
            // then been handed three days in one step.
            double gameMinutes = ElapsedGameMinutes(now);
            // Blood does not fade usefully on its own — it dulls to a floor and
            // stays there, which is the design: dealing with it is a decision
            // rather than a timer you wait out.
            ViolenceHost.AgeStain(gameMinutes);

            // A WITNESS LEFT ALONE GETS MORE DANGEROUS. Once a game-hour, so a
            // retelling is a conversation rather than a frame; four of them
            // climb a rung, which is `Observe.RetellingsPerRung`. The expected
            // name is the same misattribution source the delivery window uses,
            // because a certainty that outruns the evidence has to borrow a
            // name from somewhere and what it borrows is what they believed.
            _retellMinutes += gameMinutes;
            if (_retellMinutes >= 60 && Witnesses.Last.Count > 0)
            {
                _retellMinutes = 0;
                int hardened = Witnesses.RetellRound(o =>
                    _deedAccused.ContainsKey(o.WitnessId) ? _deedAccused[o.WitnessId] : null);
                _assemblingPairs = Witnesses.PairsThatAssembleMore();
                if (hardened > 0)
                    Debug.Log($"SimDirector: {hardened} witness(es) hardened into a name "
                              + $"without seeing anything new ({Witnesses.NamingWitnesses()} naming, "
                              + $"{_assemblingPairs} pair(s) would assemble more)");
            }

            if (_game != null && _game.Gossip != null && Witnesses.InFlight.Count > 0)
            {
                int landed = Witnesses.Tick(
                    gameMinutes,
                    _game.Gossip.Mill, now,
                    d =>
                    {
                        string who = "player";
                        if (_deedAccused.ContainsKey(d.WitnessId)
                            && !string.IsNullOrEmpty(_deedAccused[d.WitnessId]))
                            who = _deedAccused[d.WitnessId];
                        return new Fact(who, "violence", "hook_street");
                    },
                    d =>
                    {
                        string who = _deedAccused.ContainsKey(d.WitnessId)
                            ? _deedAccused[d.WitnessId] : "player";
                        return $"{d.WitnessId} says it was {who}, and came to say so";
                    });
                if (landed > 0)
                    Debug.Log($"SimDirector: {landed} witness account(s) arrived and "
                              + $"went indelible ({Witnesses.Arrived} total, "
                              + $"{Witnesses.Interceptions} intercepted)");
            }

            // One noon and one night shot per simulated day.
            if (now.Day != _shotDay) { _shotDay = now.Day; _tookDayShot = _tookNightShot = false; }
            SampleScore();
            SampleReflections();
            SampleBodies();
            SampleMix();
            if (!_tookDayShot && now.Hour == 12) { _tookDayShot = true; Shot($"day{now.Day}_noon"); }
            if (!_tookNightShot && now.Hour == 23)
            {
                _tookNightShot = true;
                // THE SHOT FIRST. Belt and braces on top of the immediate
                // restore in LightShaft.Enabled: the frame that gets saved
                // and gated is taken before any A/B has touched the scene,
                // so no future probe added here can quietly darken it.
                Shot($"day{now.Day}_night");
                MeasureNightLight();
            }
            // ONE A/B, ONCE. The only way to prove an image effect reaches
            // pixels is to render the same frame without it and compare —
            // everything else proves the code ran, which is not the same
            // claim and is exactly the gap every "verified in a test, absent
            // in the game" defect in this project has lived in.
            // ON MORE THAN ONE NIGHT, and that is the fix for the last red gate
            // rather than a tweak to it.
            //
            // `AoSamples = 3` looked like three samples and was one: the loop
            // runs three times inside a SINGLE frame, so all three see the same
            // camera in the same place looking at the same street. The comment
            // below it promises to "keep the BEST-EVIDENCED sample rather than
            // the last" and there was only ever one to choose from.
            //
            // That is why `preset` has been red at 0.0%, 2.5% and 3.2% and green
            // at 6.9% across four otherwise identical builds: whether switching
            // the graphics preset moves 5% of the frame depends entirely on
            // whether the camera happened to be facing a street with shafts and
            // wet road in it at 21:00 on day three. One instant of one evening
            // was deciding four render gates.
            if (_aoRounds < AoRounds && now.Day >= 3 && now.Hour == 21
                && now.Day != _lastAoDay)
            {
                _aoRounds++;
                _lastAoDay = now.Day;
                MeasureAo();
            }

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

        // ---- THE MIX ----
        //
        // A duck envelope is invisible in a screenshot and inaudible in CI.
        // What CAN be checked is that it MOVED and that it moved BOTH WAYS:
        // an envelope stuck at zero is the old boolean with extra steps, and
        // one stuck at one is a game that ducked the music at the title
        // screen and never brought it back.
        double _mixDuckMin = 9, _mixDuckMax = -1;

        void SampleMix()
        {
            if (!Audio.Ready) return;
            double d = Audio.DuckAmount;
            if (d < _mixDuckMin) _mixDuckMin = d;
            if (d > _mixDuckMax) _mixDuckMax = d;
        }

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

            // AND WHAT UNITY IS ACTUALLY PLAYING. `StemGain` is the number
            // this game computed; `StemVolume` is the one on the AudioSource.
            // Delete the assignment between them and every score check still
            // passes, over silence — the same way every FilmGrade check
            // passed while the post stack was detached from the camera.
            for (int i = 0; i < mix.Length; i++)
            {
                float v = Audio.StemVolume((MusicLayer)i);
                if (v < 0) { _stemsUnbound++; continue; }
                if (v > _stemVolumeMax) _stemVolumeMax = v;

                // PROPORTIONALITY, NOT EQUALITY, and the first version got
                // this wrong in the most instructive way.
                //
                // It divided the engine volume by MasterVolume * MusicVolume
                // and expected the model gain back. But `Audio` scales by
                // `0.30f * MasterVolume * MusicVolume` — the score's own bed
                // level — so the gate reported a drift of 0.7 and failed a
                // score that was working perfectly. I had guessed at the
                // scaling instead of reading it.
                //
                // Copying the 0.30 here would be the OTHER mistake this
                // project keeps making: a check written against the constant
                // it is meant to pin, which moves the day somebody retunes
                // the music bed. What the gate actually cares about is that
                // the engine tracks the model — so measure the ratio and
                // require it to be the SAME ratio for every layer and every
                // sample. That holds for any bed level and breaks the moment
                // one stem stops following its gain.
                if (mix[i] > 0.05)
                {
                    double ratio = v / mix[i];
                    if (ratio < _stemRatioMin) _stemRatioMin = ratio;
                    if (ratio > _stemRatioMax) _stemRatioMax = ratio;
                }
            }
            float busMusic = Audio.BusVolume(Bus.Music);
            if (busMusic >= 0)
            {
                if (busMusic > _busMusicMax) _busMusicMax = busMusic;
                if (busMusic < _busMusicMin) _busMusicMin = busMusic;
            }
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
        /// Whether the render A/B ever ran at all. Now only a fact about the
        /// run rather than the thing gating it — `_aoRounds` does that — but kept
        /// because "the probe never fired" and "the probe fired and found
        /// nothing" are the two readings this project most often confuses.
        bool _tookAoPair;
        /// How many separate EVENINGS the render A/B has run on. Three, because
        /// the thing being averaged out is where the camera was standing, and
        /// one more night is far cheaper than one more red build.
        const int AoRounds = 3;
        int _aoRounds;
        int _lastAoDay = -99;
        bool _spreadSeeded;
        double _aoOn = -1, _aoOff = -1;
        double _bloomDelta = -1, _grainDelta = -1, _vigOn = -1, _vigOff = -1;
        double _aoDeltaMin, _aoDeltaMax, _grainDeltaMin, _grainDeltaMax;

        double _nightFull = -1, _nightNoShafts = -1, _nightRaw = -1, _nightNoBloom = -1;
        string _beatBotTried;
        double _beatChaseSeconds;
        int _lastBeatChaseHour = -1;
        float _beatClosestApproach = 9999f;
        bool _beatMarkerSeen;

        /// WHERE IS THE NIGHT LIGHT COMING FROM. Asked once, in-engine,
        /// instead of guessed at across twenty-five-minute build cycles.
        ///
        /// `nightNotDarker` says the 23:00 frame is twice as bright as noon,
        /// and there are at least four candidates: the ambient bands, three
        /// hundred and sixty additive volumetric cones, the bloom pass, and
        /// the exposure lift the grade applies for night legibility. A single
        /// mean luminance cannot separate them, and a screenshot of a scene
        /// that has all four cannot either — which is the same lesson the
        /// ambient-occlusion A/B taught at the cost of a dead post stack.
        ///
        /// So: render the same frame four ways and log the decomposition.
        void MeasureNightLight()
        {
            var cam = Camera.main;
            if (cam == null) return;
            _nightFull = FrameShot(cam).Mean;

            LightShaft.Enabled = false;
            // A frame, so LateUpdate has run and the renderers are actually off.
            _nightNoShafts = FrameShot(cam).Mean;
            LightShaft.Enabled = true;

            FilmGrade.Bloom = false;
            _nightNoBloom = FrameShot(cam).Mean;
            FilmGrade.Bloom = true;

            FilmGrade.Bypass = true;
            _nightRaw = FrameShot(cam).Mean;
            FilmGrade.Bypass = false;

            Debug.Log($"SimDirector: night light full={_nightFull:0.0000} "
                      + $"noShafts={_nightNoShafts:0.0000} noBloom={_nightNoBloom:0.0000} "
                      + $"ungraded={_nightRaw:0.0000} "
                      + $"(shafts contribute {_nightFull - _nightNoShafts:0.0000}, "
                      + $"bloom {_nightFull - _nightNoBloom:0.0000}, "
                      + $"the grade {_nightFull - _nightRaw:0.0000})");
        }

        int _labels = -1, _labelsBlank = -1, _labelsFontless = -1;

        /// DID A SINGLE GLYPH ACTUALLY DRAW.
        ///
        /// The panel smoke test proves every panel opens, says something and
        /// gives the controls back. All three are true of a panel whose font
        /// failed to resolve and which therefore renders as an empty
        /// rectangle — the text is in the component, the component is in the
        /// scene, and nothing is on screen. That is the exact shape of the
        /// post stack sitting dead for months under checks that were all
        /// individually true.
        ///
        /// It matters more here than it looks. `UiTheme.LoadFont` asks the OS
        /// for Segoe UI, falls back to Arial, then to Unity's built-in — so
        /// the font that resolves depends on the MACHINE, and CI is a machine
        /// nobody has looked at the screen of.
        ///
        /// `preferredWidth` is the ruler because it is computed from the
        /// glyphs the font actually produced. A label with text and a
        /// preferred width of zero laid out nothing.
        void MeasureGlyphs()
        {
            _labels = 0; _labelsBlank = 0; _labelsFontless = 0;
            foreach (var t in FindObjectsByType<UnityEngine.UI.Text>(FindObjectsSortMode.None))
            {
                if (t == null || string.IsNullOrEmpty(t.text)) continue;
                _labels++;
                if (t.font == null) { _labelsFontless++; continue; }
                if (t.preferredWidth <= 0.01f) _labelsBlank++;
            }
            // AND THE WORLD TEXT, which is a different population from the UI
            // labels above — TextMesh in the street rather than UGUI on the
            // canvas. Counted because the screenshots that started this showed
            // names lying across the skyline, and a shader assignment that
            // quietly did nothing would look exactly like one that worked.
            int worldText = 0, worldTextMaterialled = 0;
            foreach (var t in FindObjectsByType<TextMesh>(FindObjectsSortMode.None))
            {
                if (t == null) continue;
                worldText++;
                var r = t.GetComponent<MeshRenderer>();
                var sh = r != null && r.sharedMaterial != null ? r.sharedMaterial.shader : null;
                if (sh != null && sh.name == "Hidden/LedgerText") worldTextMaterialled++;
            }
            _worldText = worldText;
            _worldTextDepth = worldTextMaterialled;

            Debug.Log($"SimDirector: glyphs labels={_labels} fontless={_labelsFontless} "
                      + $"blank={_labelsBlank} worldText={worldText} "
                      + $"depthTested={worldTextMaterialled} "
                      + $"adopted={WorldText.Adopted} refused={WorldText.Refused} "
                      + $"shader={WorldText.ShaderPresent}");
        }

        int _worldText = -1, _worldTextDepth = -1;

        /// REPEATED, because a single A/B pair cannot tell a small effect
        /// from a noisy ruler.
        ///
        /// Grain came back with a NEGATIVE variance delta — additive noise
        /// that reduced local spread, which is not a thing that can happen —
        /// and occlusion came in at 0.0014 against a floor of 0.002. Both are
        /// small signals sitting near a hard threshold, and one sample of
        /// each cannot say whether the effect shrank or the measurement is
        /// jittering. Three pairs, reported with their spread, can.
        ///
        /// If the spread turns out to be wider than the signal, the answer is
        /// not a lower threshold. It is that the frame pair is not controlled
        /// and the gate has been passing by luck.
        const int AoSamples = 3;

        /// The first day the ambush probe may stage. Named rather than
        /// inlined so the report can print it next to the day the run actually
        /// reached, which is the comparison that would have made this obvious.
        public const int ConfrontStagesOnDay = 10;
        bool _confrontStaged;
        /// Set when staging was refused only because the run had not got that
        /// far. Distinguishes "the game never confronted anybody" from "the
        /// harness stopped before the probe was allowed to start".
        bool _confrontUnreached;
        float _confrontOpenedAt = -1f;
        string _confrontTarget;

        /// THE SOCIAL SIMULATION'S LAST UNRUN BRANCH.
        ///
        /// Every run reported `checks=0 confronts=0`. Suspicion becoming
        /// BEHAVIOUR — somebody comparing notes about you with a neighbour,
        /// somebody stepping into your path — needs a tracker above 0.50 and
        /// 0.80 respectively, and nine days of a bot doing careful drops
        /// never gets anybody there. So the two things this game is most
        /// about had never once executed in a verified build, for the same
        /// reason the beats hadn't: nothing in the sim ever produced the
        /// precondition.
        ///
        /// WHAT IS STAGED AND WHAT IS NOT. The precondition is staged — one
        /// person's suspicion is raised through the real `Raise` API, with a
        /// real reason, on the person who already believes the most. What is
        /// NOT staged is the response: whether the ladder reads as
        /// Confronting, whether the ambush fires, whether they compare notes
        /// with somebody standing near them, whether a conversation opens.
        /// That is the code under test and none of it is touched here.
        ///
        /// It is the same split the empire, Director, operations and Act III
        /// staging already use, and the reason is the same — the accumulation
        /// is tested in Core against a clock we control, and the sim exists to
        /// prove the wiring downstream of it.
        // ---- PHASE 1 BEHAVIOUR PROBE (weapons-spec.md §10) ----------------
        //
        // THE MACHINERY GATE IS NOT THE POINT. "A lit walker is detected
        // further than a shadowed one" can be green in a city that computes
        // perfectly and reacts to nothing, which is exactly the failure this
        // project keeps producing — a post stack that never executed a frame,
        // a cinematic camera behind a guard, five systems built and not
        // running. So this stages the two behaviours §3.3 actually promises
        // and counts what happened to the player.
        bool _loiterStaged, _nightRunStaged;
        float _slamAt = -1f;
        bool _loiterApproaching;
        Vector3 _loiterTarget;
        int _investigationsBeforeSlam, _slamInvestigations = -1;
        bool? _ringOk;

        /// THE SLAM IS NO LONGER A ONE-SHOT, and the reason is the whole of last
        /// night's remaining bug. One slam in thirteen days meant one chance for
        /// the ring to draw, and the ring's cooldown gave that one chance a coin
        /// flip. A probe that fires once and can be silently robbed is not
        /// evidence; four on four separate nights costs nothing (a slam is one
        /// instantaneous Emit) and turns the ring claim from luck into a fact.
        int _slams;
        int _lastSlamDay = -99;

        /// PHASE 2. How many evenings stage a deed, and what the witnesses
        /// made of it. Four, on four separate days, for the same reason the
        /// ambient-occlusion probe needed three: one sample of one street is
        /// one arrangement of people, and "four witnesses produce four slot
        /// sets" is a claim about arrangements.
        int _deedsStaged, _lastDeedDay = -99;
        const int DeedsWanted = 4;
        int _deedSlotSets, _deedWitnesses, _deedBestRung;
        /// The delivery window, measured: how many witnesses started walking,
        /// whether an interception landed, and how many got there anyway.
        int _deedDispatched;
        bool _deedInterceptTried, _deedIntercepted;
        /// Who each witness will name when they get there — the player, or,
        /// on a partial identification, somebody they merely expected.
        readonly Dictionary<string, string> _deedAccused = new Dictionary<string, string>();
        /// How many named the wrong man. §4.7 claim 5.
        int _deedMisnamed;
        /// A person crossing a street, in metres per game-minute. Walk speed
        /// is 1.4 m/s, and a sim minute is a minute.
        const double WitnessWalkMetresPerMinute = 84.0;

        int _minuteClock = -1;

        /// Game-minutes since the last call, read off the CLOCK rather than
        /// off the frame.
        ///
        /// The delivery window is measured in game minutes and the sim runs
        /// days in seconds, so scaling a frame delta would have made a witness
        /// walk for a real-time minute — a number with no relationship to the
        /// distance they were given. `now` is the only honest source, and a
        /// day rollover is a forward step rather than a jump backwards.
        double ElapsedGameMinutes(GameTime now)
        {
            int stamp = now.Day * 1440 + now.Hour * 60 + now.Minute;
            if (_minuteClock < 0) { _minuteClock = stamp; return 0; }
            int delta = stamp - _minuteClock;
            _minuteClock = stamp;
            return delta > 0 ? delta : 0;
        }

        /// The walker with this display name, or null. A loop rather than
        /// Linq because this file does not import it, and a `using` added for
        /// one call site is how a lint rule starts being ignored.
        NpcWalker NamedWalker(string displayName)
        {
            if (_npcs == null || string.IsNullOrEmpty(displayName)) return null;
            foreach (var n in _npcs)
                if (n != null && n.DisplayName == displayName) return n;
            return null;
        }
        // ---- §4.7's HEADLINE CLAIM, which nothing has ever tested ----------
        //
        // *The same killing leaves no witness in an empty alley, several in a
        // market, and none in the back room of a busy pub.* That is the done-
        // condition for Phase 3 and it is a claim about the WORLD, not about
        // the resolver: CoreTests can prove `Observe.Resolve` distinguishes
        // vantages it is handed, and only a running street can prove the
        // street produces vantages that differ this way.
        //
        // NO TELEPORTING, and no authored coordinates. The three places are
        // found by measuring the street the run actually built: for every
        // walker, how many OTHER walkers stand within sight range with a clear
        // line, and how many stand within range with a wall between. That
        // gives the three cases their honest definitions —
        //
        //   the empty alley       fewest people who can see it
        //   the market            most people who can see it
        //   the pub's back room   people are close, and every one is blocked
        //
        // — and if the world contains no such arrangement, the gate says so
        // rather than inventing one. A world with no enclosed busy place is a
        // finding about the world.
        const int PlacesStageOnDay = 12;
        bool _placesStaged;
        PlaceReading _placesAlley = PlaceReading.None,
                     _placesMarket = PlaceReading.None,
                     _placesEnclosed = PlaceReading.None;
        string _placesWhy = "not reached";

        /// PHASE 3's other verbs — carry, the frisk, the threat, the blood.
        /// Day nine: the open city, after the campaign week has been decided,
        /// for exactly the reason the confrontation waits until day ten. A
        /// probe that alters the outcome measured beside it is not a probe.
        const int CarryStagesOnDay = 9;
        bool _carryStaged, _friskStaged, _threatStaged, _washTried;
        int _carryTook;
        bool _carryIsAChoice, _carryCanTakeAll;
        Coat.Refusal _friskRefusalCost = Coat.Refusal.Allowed;
        double _friskFound, _friskCost;
        /// Somebody with no grounds must NOT get to search you. The negative
        /// case, because a gate that only checks the positive one is testing
        /// half a rule.
        bool _friskGroundlessHappened = true;
        bool _washFailedInPublic, _washWorkedAtHome;

        /// PHASE 4 — provenance, disposal, accidents. Day ten, after the coat
        /// and the frisk have run, so a run that dies early still gets Phase 3.
        const int ProvenanceStagesOnDay = 10;
        bool _provenanceStaged;
        double _provBought, _provStolen, _provTaken, _provInherited, _provOrdinary;
        bool _provOrdinaryStayedOrdinary, _provUsedShowsInHistory;
        bool _provDisposalSeen, _provDisposalUnseen;
        double _provRiskSeen, _provRiskUnseen;
        bool _accidentInCompany, _accidentAlone;
        string _provThread = "none";
        double _provThreadRisk;
        bool _provEllisAsking;
        /// How empty the emptiest place the run could find actually was. Zero
        /// is what the accident and disposal claims need; anything else is a
        /// fact about the world rather than about the code.
        int _emptyWatchers = -1;
        bool _bloodStaged;

        /// PHASE 2's REMAINDER — the ghost, retelling, comparing notes.
        double _retellMinutes;
        int _assemblingPairs;

        const int SlamsWanted = 4;
        /// Did a slam actually put a circle on the ground? Checked in the same
        /// frame as the Emit, because `Show` is synchronous — so this is the
        /// drawn ring itself answering, not an inference from a counter.
        bool _slamDrewRing;
        int _ringsShownBeforeSlam;

        /// Which perception sub-claims are failing, by name. Empty when green.
        string PerceptionWhy()
        {
            var why = new List<string>();
            if (Perceivers.Looks < 1) why.Add("no-looks");
            if (_loiterLooks < 1) why.Add("loiter");
            if (!(_litRange > _darkRange)) why.Add("light");
            if (Perceivers.SoundsEmitted < 1) why.Add("no-sounds");
            if (_slamInvestigations < 1) why.Add("slam");
            if (_ringOk != true) why.Add("ring-radius");
            // AND THAT IT DREW. The old gate asserted the ring's arithmetic and
            // called that "the ring", so a build in which the circle never once
            // appeared on screen passed it. Verified-and-invisible is the exact
            // failure this project keeps shipping, and the only cure is a gate
            // that reads the drawing rather than the maths behind it.
            if (!_slamDrewRing) why.Add("ring-drawn");
            // AND THE PIXELS. "Drawn" means a GameObject exists; this means the
            // player can see it. They are not the same claim and the difference
            // between them was a circle standing on its edge.
            if (!(_ringSeenFraction >= RingSeenFloor)) why.Add("ring-onscreen");
            // The same events in words. Three of §6.2's four channels are
            // audio; captions are how any of them reach a player with the
            // sound off, and the spec's own honesty test is that pass.
            if (_captionsShown < 1) why.Add("captions-silent");
            return why.Count == 0 ? "ok" : string.Join("+", why);
        }
        float _loiterUntil = -1f, _nightRunUntil = -1f;
        int _looksBeforeLoiter, _looksBeforeRun;
        int _loiterLooks = -1, _nightRunLooks = -1, _nightWalkLooks = -1;
        double _hushPeak;
        double _litRange = -1, _darkRange = -1;

        /// How many caption lines the run put on screen, and how many of them
        /// were the hush — the channel with no sound to hang itself on, which
        /// is the one most likely to be silently dead.
        int _captionsShown, _captionHushes;

        void StagePerception(GameTime now, ref Vector3 target)
        {
            // The hush is read every tick because its PEAK is the interesting
            // value — a street that went quiet for two seconds and recovered
            // is the whole effect, and a sample at the end of the run would
            // find it back at nothing.
            // THE CROWD COUNTS TOO. `_npcs` is the named cast, and counting only
            // them made "how many people are near you" an answer about the story
            // rather than about the street — which is wrong for a hush, whose
            // whole subject is how much noise a crowd was making.
            int attending = 0, present = 0;
            NpcWalker nearest = null;
            float nearestDist = float.MaxValue;
            void Consider(NpcWalker n)
            {
                if (n == null) return;
                float d = Vector3.Distance(n.transform.position, _player.transform.position);
                if (d < nearestDist) { nearestDist = d; nearest = n; }
                if (d > Perceivers.NearBandMetres) return;
                present++;
                if (n.AttendingPlayer) attending++;
            }
            if (_npcs != null) foreach (var n in _npcs) Consider(n);
            if (_game != null && _game.CrowdBodies != null)
                foreach (var kv in _game.CrowdBodies) Consider(kv.Value);
            Perceivers.Attending = attending;
            Perceivers.PresentNearby = present;
            double hush = Notice.HushFraction(attending, present);
            if (hush > _hushPeak) _hushPeak = hush;
            // Read the caption channel from the same place the hush is read,
            // so the two can never disagree about whether the street went
            // quiet and whether anybody was told.
            _captionsShown = CaptionBar.Shown;
            _captionHushes = CaptionBar.Hushes;
            // One owner for the peak. `Perceivers.PeakHush` existed and nothing
            // wrote to it, which is the exact shape of the five systems this
            // project found built and not running — a public field with no
            // writer is a bug waiting to be discovered by somebody reading it.
            if (hush > Perceivers.PeakHush) Perceivers.PeakHush = hush;

            // LIGHT ATTRIBUTION, measured in the real scene rather than
            // asserted in a unit test: how far a person is detectable standing
            // where the player is standing, at the brightest and darkest spots
            // the probe can find within a few metres.
            // PROBE THE LAMPS, NOT A CIRCLE AROUND THE BOT. The first version
            // sampled twelve points on a six-metre ring around wherever the
            // player happened to be, and reported lit=4.8m dark=4.8m — identical,
            // because at that moment there was no lamp within six metres of the
            // bot and it was measuring darkness against darkness. A ruler that
            // can return the same number for both ends of what it is comparing
            // is not measuring the thing.
            //
            // So: find a real lamp and stand next to it, and find a point as far
            // from every lamp as the street allows. Deterministic, and it fails
            // loudly if the city genuinely has no lamps rather than quietly
            // reporting a null result as a pass.
            if (_litRange < 0 && now.Hour >= 21)
            {
                // FORCE THE LAMP LIST FIRST. Without this the probe finds a live
                // lamp with its own fresh query and then asks `LevelAt` — which
                // answers from a cache that may predate the lamp switching on —
                // producing lit=4.8m dark=4.8m, darkness measured against
                // darkness. Two views of one set is the bug; one view is the fix.
                Perceivers.RefreshLamps();
                Vector3 here = _player.transform.position;
                Light lamp = null;
                float lampDist = float.MaxValue;
                foreach (var l in UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
                {
                    if (l == null || !l.isActiveAndEnabled || l.type == LightType.Directional) continue;
                    float d = Vector3.Distance(l.transform.position, here);
                    if (d < lampDist) { lampDist = d; lamp = l; }
                }
                if (lamp != null)
                {
                    // A metre from the lamp is as lit as this street gets; the
                    // far side of its own range is as dark as the same street
                    // gets, which keeps the comparison local and honest.
                    Vector3 lit = lamp.transform.position + Vector3.right * 1.0f;
                    Vector3 dark = lamp.transform.position
                                   + Vector3.right * (lamp.range * 2.5f + 10f);
                    double bestLight = Perceivers.LevelAt(lit);
                    double worstLight = Perceivers.LevelAt(dark);
                    _litRange = Perception.DetectRangeMetres * Perception.LightFactor(bestLight);
                    _darkRange = Perception.DetectRangeMetres * Perception.LightFactor(worstLight);
                    Debug.Log($"SimDirector: light attribution off {lamp.name} "
                              + $"(range {lamp.range:0.0}) — lit {bestLight:0.00} reaches "
                              + $"{_litRange:0.0}m, dark {worstLight:0.00} reaches "
                              + $"{_darkRange:0.0}m");
                }
            }

            // ---- the loiter ----
            //
            // Thirty real seconds of standing still, once, in an eleven-minute
            // run. It costs about five percent of the sim and it is the only
            // way to prove the claim rather than assert it: `Notice.What` needs
            // real accumulated stationary time, and shortening the threshold
            // for the test would be testing a different game.
            // DAY TEN, IN THE OPEN CITY — and this is the same lesson
            // `StageConfrontation` already carries, learned again the hard way.
            //
            // The loiter freezes the player for thirty REAL seconds, and at
            // twenty game-minutes per real second that is ten game-hours of
            // standing still. Staged inside the campaign week it cost the bot
            // three days of jobs, which tipped the week to LostCastOut and made
            // `verdictSane` go red — the only failing gate in an otherwise green
            // run. A probe that alters the outcome measured beside it is not a
            // probe, and I wrote that sentence into this file yesterday.
            //
            // After day eight the week is already decided, so the same thirty
            // seconds proves the same thing and votes on nothing.
            // A WINDOW, NOT AN HOUR. The Fall skips days in the open city and
            // the sim reclaims them by extending the end day, so a probe pinned
            // to one hour of one day can be jumped over entirely and never fire
            // — which would make this gate flaky rather than strict, and a
            // flaky gate is worse than no gate because it teaches people to
            // re-run.
            // GO AND FIND AN AUDIENCE. The first version waited for somebody to
            // already be within forty-five metres at those hours and it never
            // fired once in a nine-day run — the bot's evening waypoints and the
            // cast's evening schedules simply do not coincide. A probe that has
            // to be lucky is not a probe, so this one WALKS to the nearest
            // person and then stands still.
            if (!_loiterStaged && now.Day >= 8 && now.Hour >= 19 && nearest != null)
            {
                _loiterApproaching = true;
                _loiterTarget = nearest.transform.position;
            }
            if (_loiterApproaching)
            {
                target = _loiterTarget;
                if (nearestDist <= 8f)
                {
                    _loiterApproaching = false;
                    _loiterStaged = true;
                    // CAST, and the reason is worth a line: Core is double
                    // throughout and the Unity layer is float throughout, so
                    // every constant crossing that boundary needs one. Nothing
                    // local catches it — ShapeCheck is a shape pass, not a
                    // compile — so CI is the only compiler this half has.
                    _loiterUntil = Time.time + (float)Notice.LoiterSeconds + 2f;
                    _looksBeforeLoiter = Perceivers.Looks;
                    Debug.Log($"SimDirector: staging a loiter beside "
                              + $"{nearest.DisplayName} at {nearestDist:0.0}m, "
                              + $"{present} people within the near band");
                }
            }
            if (_loiterUntil > 0)
            {
                if (Time.time < _loiterUntil)
                {
                    // Stand still. Holding the target AT the player is how the
                    // bot stops without touching the locomotion.
                    target = _player.transform.position;
                }
                else
                {
                    _loiterLooks = Perceivers.Looks - _looksBeforeLoiter;
                    _loiterUntil = -1f;
                    Debug.Log($"SimDirector: loiter over, {_loiterLooks} heads turned, "
                              + $"{Perceivers.LoiterNotices} of them for loitering");
                }
            }

            // ---- a noise, and whether anybody walks toward it ----
            //
            // §8 calls investigating the highest-value behaviour in the design
            // and the Phase 1 gate did not test it, so it went in the same
            // night rather than the next one. A door slam at 3am carries about
            // forty-eight metres in a silent street, which is the arithmetic
            // rather than a hope.
            // NO DAY GATE. A slam is one instantaneous Emit — it costs no game
            // time at all and cannot move the week's outcome, so gating it on
            // day ten was copy-paste from the loiter rather than reasoning, and
            // it cost two builds' worth of evidence about hearing.
            if (_slams < SlamsWanted && now.Day != _lastSlamDay
                && now.Hour >= 1 && now.Hour <= 5
                && nearest != null && nearestDist <= Perceivers.NearBandMetres)
            {
                _slams++;
                _lastSlamDay = now.Day;
                _investigationsBeforeSlam = Perceivers.NoiseInvestigations;
                _ringsShownBeforeSlam = NoiseRing.Shown;
                Perceivers.Emit(_player.transform.position, Perception.LoudDoorSlam, "slam");
                if (NoiseRing.Shown > _ringsShownBeforeSlam) _slamDrewRing = true;
                _slamAt = Time.time;
                Debug.Log($"SimDirector: slammed a door #{_slams}, {present} people nearby, "
                          + $"carries {Perception.AudibleRadius(Perception.LoudDoorSlam, Perception.AmbientNight3am):0.0}m"
                          + $" — ring {NoiseRing.LastSkip} at {NoiseRing.LastRadius:0.0}m"
                          + $" (floor {NoiseRing.LastFloor:0.0}, occluded={NoiseRing.LastOccluded})");
            }
            // A DEED, STAGED, so `Witnesses` is exercised rather than merely
            // written. §4.7's five claims are all about witnessing a violent
            // act, and Phase 3 is what puts a weapon on a button — so until
            // then the only way to find out whether the geometry produces
            // different vantages on a real street is for the run to stage one.
            //
            // This is not a fake result standing in for a real one. The deed
            // is synthetic; every number the witnesses are judged on —
            // position, facing, light on the actor, light on the victim, walls
            // — is the live world. What it measures is exactly the half
            // CoreTests cannot: whether the street produces varied vantages,
            // or whether four people in a city all resolve identically because
            // something upstream is handing them the same geometry.
            if (_deedsStaged < DeedsWanted && now.Day != _lastDeedDay
                && nearest != null && nearestDist <= Perceivers.NearBandMetres)
            {
                _deedsStaged++;
                _lastDeedDay = now.Day;
                var weapon = Arsenal.Get("cosh");
                var deed = Observe.DeedFor(weapon, $"sim-deed-{_deedsStaged}",
                                           "player", nearest.DisplayName,
                                           actorFled: false, hadPrecursor: true);
                Witnesses.Resolve(deed, _player.transform, nearest.transform.position);
                int distinct = Witnesses.DistinctSlotSets();
                if (distinct > _deedSlotSets) _deedSlotSets = distinct;
                if (Witnesses.Saw > _deedWitnesses) _deedWitnesses = Witnesses.Saw;
                if (Witnesses.BestRung() > _deedBestRung) _deedBestRung = Witnesses.BestRung();
                Debug.Log($"SimDirector: staged deed #{_deedsStaged} "
                          + $"({Witnesses.Considered} considered, {Witnesses.Saw} got something, "
                          + $"{distinct} distinct slot sets, best rung {Witnesses.BestRung()})");

                // THE DELIVERY WINDOW, ACTUALLY OPENED. `Witnesses.Dispatch`,
                // `Tick` and `Intercept` were written, tested in Core and
                // never once called by the game — the minutes between seeing
                // and the street knowing, which §4.5 calls the best pressure
                // in the design, did not exist at runtime.
                //
                // Real distance, not a constant: the witness walks from where
                // they are standing to where they are taking it, at the walk
                // speed the rest of the sim uses. That is the whole reason
                // `Dispatch` takes a callback instead of a number.
                NpcWalker goTo = NamedWalker("Ellis");
                Vector3 dest = goTo != null ? goTo.transform.position
                                            : WorldBuilder.BarDoor;
                // WHO EACH WITNESS WILL NAME, decided before anybody walks.
                //
                // §4.7 claim 5: a rung-1 or rung-2 identification plus an
                // expectation produces a named accusation of the WRONG man,
                // and the mill has to carry it as an ordinary fact at ordinary
                // confidence — being wrong is content, not an error path.
                // `Observe.Misattribute` was written for this and had no
                // caller, so the street could only ever be right.
                //
                // The expectation is the nearest OTHER walker: the person this
                // witness would think of first. A long coat at night near the
                // docks is Nikos to somebody who expects Nikos.
                _deedAccused.Clear();
                foreach (var o in Witnesses.Last)
                {
                    if (o == null || o.Empty) continue;
                    string expected = null;
                    if (_npcs != null)
                        foreach (var n in _npcs)
                            if (n != null && n.DisplayName != o.WitnessId
                                && n.DisplayName != "Ellis") { expected = n.DisplayName; break; }
                    string named = Observe.Misattribute(o, expected, _deedsStaged * 31 + 7);
                    _deedAccused[o.WitnessId] = named;
                    if (!string.IsNullOrEmpty(named) && named == expected
                        && named != "player") _deedMisnamed++;
                }

                int walking = Witnesses.Dispatch(
                    Witnesses.Last, goTo != null ? "Ellis" : "Lena",
                    o =>
                    {
                        var w = NamedWalker(o.WitnessId);
                        double metres = w != null
                            ? Vector3.Distance(w.transform.position, dest) : 60.0;
                        return Math.Max(1.0, metres / WitnessWalkMetresPerMinute);
                    },
                    o => 0.5);
                _deedDispatched += walking;

                // AND ONE OF THEM GETS STOPPED, so claim 4 is exercised rather
                // than merely available: intercepted before arrival leaves the
                // mill untouched, and the same witness a minute later leaves
                // something nothing takes back.
                if (walking > 0 && !_deedInterceptTried)
                {
                    _deedInterceptTried = true;
                    var first = Witnesses.InFlight.Count > 0
                        ? Witnesses.InFlight[0].WitnessId : null;
                    if (first != null) _deedIntercepted = Witnesses.Intercept(first);
                }
            }

            // THE RING IS THE MODEL, asserted rather than assumed. Comparing
            // the drawn radius against `AudibleRadius` recomputed from the same
            // inputs catches the whole class of bug where a visual quietly
            // drifts from the system it is supposed to be showing — which is
            // exactly what `scoreAudible` caught in the mix a day ago.
            if (_ringOk == null && NoiseRing.Sized > 0)
            {
                double expect = Perception.AudibleRadius(NoiseRing.LastLoudness,
                                                         NoiseRing.LastFloor,
                                                         NoiseRing.LastOccluded);
                _ringOk = Math.Abs(NoiseRing.LastRadius - expect) < 1e-9;
                Debug.Log($"SimDirector: noise ring {NoiseRing.LastRadius:0.00}m vs "
                          + $"model {expect:0.00}m — matches={_ringOk}");
            }

            if (_slamAt > 0 && Time.time - _slamAt > 4f)
            {
                // THE BEST OF THE FOUR, not the last of them. Overwriting would
                // let a slam on an empty street erase the evidence from one on a
                // busy one, which is a probe that gets weaker the more often it
                // runs — the opposite of the point.
                int walked = Perceivers.NoiseInvestigations - _investigationsBeforeSlam;
                _slamInvestigations = Math.Max(_slamInvestigations, walked);
                _slamAt = -1f;
                Debug.Log($"SimDirector: {walked} people walked toward the slam "
                          + $"(best so far {_slamInvestigations})");
            }

            // ---- running at night ----
            //
            // The same action at two different hours has to read differently
            // or the clock is decoration. A walk sample is taken first so the
            // comparison is against this run's own baseline rather than a
            // number I picked.
            if (!_nightRunStaged && now.Day >= 8 && now.Hour <= 4 && _loiterUntil < 0)
            {
                _nightRunStaged = true;
                _nightWalkLooks = Perceivers.Looks;
                _nightRunUntil = Time.time + 12f;
                _looksBeforeRun = Perceivers.Looks;
                _player.AutoMoveRun = true;
                Debug.Log("SimDirector: staging a night run");
            }
            if (_nightRunUntil > 0 && Time.time >= _nightRunUntil)
            {
                _nightRunLooks = Perceivers.Looks - _looksBeforeRun;
                _nightRunUntil = -1f;
                _player.AutoMoveRun = false;
                Debug.Log($"SimDirector: night run over, {_nightRunLooks} heads turned, "
                          + $"{Perceivers.NightRunNotices} of them for running");
            }
        }

        void StageConfrontation(GameTime now)
        {
            // Close a forced conversation a moment after it opens. A panel
            // left up would sit over every screenshot for the rest of the run.
            if (_confrontOpenedAt > 0 && Time.time - _confrontOpenedAt > 1.5f)
            {
                _game.Ui?.CloseConversation();
                _confrontOpenedAt = -1f;
            }
            if (_confrontStaged || _game.Gossip == null || _game.Gossip.Mill == null) return;
            // Day six: late enough that the mill has real content and the
            // player has a history, early enough to leave room for the
            // consequences to travel.
            // DAY TEN, IN THE OPEN CITY — not day six.
            //
            // Staging it inside the campaign week changed the week. Raising
            // one person to 0.85 suspicion on day six is a real event with
            // real consequences, and it tipped the verdict: verdictSane went
            // red on the very run that first fired a confrontation. A probe
            // that alters the outcome measured beside it is not a probe.
            //
            // After day eight the week is already decided, so the ambush
            // proves the wiring without voting on the ending.
            // AND THE RUN MUST REACH DAY TEN FOR THIS LINE TO BE ANYTHING BUT
            // A RETURN. It did not. CI runs `-simdays 9`, so day 10 never
            // arrived, staging never ran, `TotalConfrontations` stayed 0, and
            // `suspicionActs` — which requires it to be above zero — could not
            // go green on any run, ever. The gate was not failing. It was
            // unsatisfiable, and it had been reporting `confronts=0` as though
            // that were a finding about the game rather than about the harness.
            //
            // The harness is what was wrong, so the harness is what changed:
            // the run is eleven days now, which leaves days ten and eleven for
            // the nearest walker to be near enough. The day-ten rule itself is
            // deliberate and stays — staging inside the campaign week tipped
            // `verdictSane` red once already, and a probe that alters the
            // outcome measured beside it is not a probe.
            if (now.Day < ConfrontStagesOnDay) { _confrontUnreached = true; return; }
            if (_npcs == null) return;

            // The nearest walker who is not Ellis — the confrontation needs
            // them within four metres, and picking somebody already standing
            // there tests the ambush without needing a second navigation
            // system to get the bot to them.
            NpcWalker nearest = null;
            float best = float.MaxValue;
            foreach (var n in _npcs)
            {
                if (n == null || n.DisplayName == "Ellis") continue;
                var g0 = _game.Gossip.Mill.Get(n.DisplayName);
                if (g0 == null || g0.Leashed) continue;
                float d = Vector3.Distance(n.transform.position, _player.transform.position);
                if (d < best) { best = d; nearest = n; }
            }
            if (nearest == null || best > 3.5f) return;

            var g = _game.Gossip.Mill.Get(nearest.DisplayName);
            double need = 0.85 - g.Suspicion.Value;
            if (need > 0)
                g.Suspicion.Raise(need,
                    "counted the takings twice and the second number was the one that left");
            _confrontStaged = true;
            _confrontTarget = nearest.DisplayName;
            _confrontOpenedAt = Time.time;
            Debug.Log($"SimDirector: staged a confrontation with {_confrontTarget} at "
                      + $"{best:0.0}m, suspicion now {g.Suspicion.Value:0.00}");
        }

        /// PHASE 4 — the object's life, and the claim the phase is done by.
        ///
        /// *A weapon acquired by each of the four routes carries a different
        /// traceability, and disposal seen by a witness produces a different
        /// residual risk from disposal unseen.* Both are numbers `Core/Traces`
        /// has computed since Phase 1 and nothing has ever called.
        ///
        /// FOUR OBJECTS, ONE PER ROUTE, and the fifth is the deliberate
        /// collision: a kitchen knife BOUGHT from a named seller must still
        /// come out Ordinary, because ordinariness is a property of the object
        /// rather than of the transaction, and that is the one place the two
        /// disagree and the object wins.
        void StageProvenance(GameTime now)
        {
            if (_provenanceStaged || now.Day < ProvenanceStagesOnDay || _player == null) return;
            _provenanceStaged = true;

            var bought = EvidenceHost.Acquire("p-bought", "switchblade",
                                              Traces.Origin.Bought, "Kass");
            var stolen = EvidenceHost.Acquire("p-stolen", "tyreiron",
                                              Traces.Origin.Stolen, "the garage on Copper Row");
            var taken = EvidenceHost.Acquire("p-taken", "cosh",
                                             Traces.Origin.Taken, "a man who is not carrying it now");
            var inherited = EvidenceHost.Acquire("p-inherited", "razor",
                                                 Traces.Origin.Inherited, "Mickey");
            var ordinary = EvidenceHost.Acquire("p-ordinary", "kitchenknife",
                                                Traces.Origin.Bought, "Kass");

            _provBought = EvidenceHost.Traceability(bought);
            _provStolen = EvidenceHost.Traceability(stolen);
            _provTaken = EvidenceHost.Traceability(taken);
            _provInherited = EvidenceHost.Traceability(inherited);
            _provOrdinary = EvidenceHost.Traceability(ordinary);
            _provOrdinaryStayedOrdinary = ordinary != null
                                          && ordinary.Origin == Traces.Origin.Ordinary;

            // THE SAME OBJECT, USED, THEN DISPOSED OF TWICE OVER — once where
            // people can see and once where they cannot. Two items rather than
            // one, because disposal is once-only and the comparison needs both
            // answers from the same starting position.
            var seenBlade = EvidenceHost.Acquire("p-seen", "switchblade",
                                                 Traces.Origin.Bought, "Kass");
            var unseenBlade = EvidenceHost.Acquire("p-unseen", "switchblade",
                                                   Traces.Origin.Bought, "Kass");
            EvidenceHost.Used(seenBlade, "killed", "a man on Copper Row");
            EvidenceHost.Used(unseenBlade, "killed", "a man on Copper Row");
            _provUsedShowsInHistory = seenBlade != null && seenBlade.UsedInAKilling;

            // WHERE PEOPLE ARE, AND WHERE THEY GENUINELY ARE NOT.
            //
            // The first version took the emptiest WALKER'S POSITION as the
            // unwatched spot, and both disposals came back `seen=True`. Of
            // course they did: somebody is standing at a walker's position —
            // the walker. `SomebodyWatching` iterates every npc and that one is
            // at distance zero with a clear line.
            //
            // Exactly the fault `Witnesses.Resolve` had with the victim, twelve
            // hours apart and in a different file: a position derived FROM a
            // person, then tested against everybody INCLUDING that person. The
            // accident gate failed for the same reason, and worse — it uses the
            // 40m detect range rather than disposal's 18m, so an empty spot has
            // to be genuinely empty rather than merely quiet.
            //
            // So the quiet spot is now searched for and MEASURED rather than
            // borrowed, and the run prints how empty it managed to get.
            Vector3 crowded = _player.transform.position;
            int most = -1;
            if (_npcs != null)
                foreach (var n in _npcs)
                {
                    if (n == null) continue;
                    int near = 0;
                    foreach (var o in _npcs)
                        if (o != null && o != n
                            && Vector3.Distance(o.transform.position, n.transform.position)
                               < Perception.Rung2MarkMetres) near++;
                    if (near > most) { most = near; crowded = n.transform.position; }
                }
            int emptyWatchers;
            Vector3 empty = QuietSpot(out emptyWatchers);

            bool seenA = EvidenceHost.Dispose(seenBlade, "the canal", crowded, _npcs);
            bool seenB = EvidenceHost.Dispose(unseenBlade, "the canal", empty, _npcs);
            _provDisposalSeen = seenA;
            _provDisposalUnseen = seenB;
            _provRiskSeen = EvidenceHost.ResidualRisk(seenBlade);
            _provRiskUnseen = EvidenceHost.ResidualRisk(unseenBlade);

            // AND THE ACCIDENT, which must be refused in company. Same spot,
            // same weapon, and the only thing that differs is who can see it.
            var stairs = Arsenal.Get("stairs");
            _accidentInCompany = EvidenceHost.AccidentAvailable(stairs, crowded, true, _npcs);
            _accidentAlone = EvidenceHost.AccidentAvailable(stairs, empty, true, _npcs);

            // Ellis follows the object rather than the man.
            double threadRisk;
            var thread = EvidenceHost.StrongestThread(out threadRisk);
            _provThread = thread != null ? thread.InstanceId : "none";
            _provThreadRisk = threadRisk;
            _provEllisAsking = EvidenceHost.EllisIsAskingAboutYou(
                _game.Homicides, _game.Gossip != null ? _game.Gossip.Mill : null);

            _emptyWatchers = emptyWatchers;
            Debug.Log($"SimDirector: quiet spot has {emptyWatchers} watcher(s) within "
                      + $"{Perception.DetectRangeMetres:0}m — {(emptyWatchers == 0 ? "genuinely empty" : "the world had nowhere emptier")}");
            Debug.Log($"SimDirector: provenance — bought {_provBought:0.00} stolen {_provStolen:0.00} "
                      + $"taken {_provTaken:0.00} inherited {_provInherited:0.00} "
                      + $"ordinary {_provOrdinary:0.00} (stayed ordinary={_provOrdinaryStayedOrdinary}); "
                      + $"disposal seen={seenA} risk {_provRiskSeen:0.00} vs unseen={seenB} "
                      + $"risk {_provRiskUnseen:0.00}; accident inCompany={_accidentInCompany} "
                      + $"alone={_accidentAlone}; thread {_provThread} at {_provThreadRisk:0.00}, "
                      + $"Ellis asking={_provEllisAsking}");
        }

        /// THE REST OF PHASE 3 — the threat, the coat, the frisk, the blood.
        ///
        /// Not one of these had a call site. The player cannot press a button
        /// for any of them yet, so the same argument that justifies staging a
        /// deed applies: the only way to find out whether the verbs work
        /// against a live street is for the run to perform them. Every input
        /// they take comes from the world; only the decision to act is staged.
        void StageCarryAndThreat(GameTime now)
        {
            if (_player == null || now.Day < CarryStagesOnDay) return;
            // The nearest walker, found here rather than threaded in: this runs
            // from a different place in Update than the deed staging does, and
            // a `nearest` computed three hundred lines away is a variable that
            // silently means something else the day somebody moves a call.
            NpcWalker nearestForThreat = null;
            if (_npcs != null)
            {
                float best = float.MaxValue;
                foreach (var n in _npcs)
                {
                    if (n == null) continue;
                    float d = Vector3.Distance(n.transform.position, _player.transform.position);
                    if (d < best) { best = d; nearestForThreat = n; }
                }
                if (best > Perceivers.NearBandMetres) nearestForThreat = null;
            }

            // ---- what is in the coat, once ----
            //
            // Two objects that will not both fit, so `IsAChoice` is TRUE and
            // the decision at the door is a real one. A razor is Damning, a
            // cosh is Concealable, and the capacity rule says so rather than
            // this file deciding it.
            if (!_carryStaged)
            {
                _carryStaged = true;
                var razor = Traces.Acquire("sim-razor", "razor", Traces.Origin.Ordinary, "a drawer");
                var cosh = Traces.Acquire("sim-cosh", "cosh", Traces.Origin.Inherited, "Mickey");
                // A bat is `Concealment.Impossible` — not carried under a coat
                // at all, but carried VISIBLY, which is a different decision.
                // Three objects that cannot all come is what makes `IsAChoice`
                // true, and a run where everything fits proves nothing.
                var bat = Traces.Acquire("sim-bat", "bat", Traces.Origin.Ordinary, "the yard");
                CoatHost.Store(razor); CoatHost.Store(cosh); CoatHost.Store(bat);
                _carryTook = 0;
                if (CoatHost.Carry(cosh)) _carryTook++;
                if (CoatHost.Carry(razor)) _carryTook++;
                if (CoatHost.Carry(bat)) _carryTook++;
                _carryIsAChoice = CoatHost.IsAChoice;
                _carryCanTakeAll = CoatHost.CanTakeEverything;
                Debug.Log($"SimDirector: coat — took {_carryTook} of 3, on me {CoatHost.OnMe.Count}, "
                          + $"at home {CoatHost.AtHome.Count}, isAChoice={_carryIsAChoice}, "
                          + $"canTakeEverything={_carryCanTakeAll}");
            }

            // ---- the frisk, both answers ----
            //
            // Refused once and allowed once, because refusing is an answer and
            // costs something different depending on who asked. Both branches
            // or the gate only proves half the verb.
            if (!_friskStaged && _game.Gossip != null)
            {
                _friskStaged = true;
                double heat = Feel.Clamp01(_game.CurrentHeat);
                var refused = CoatHost.Frisk(Coat.Frisker.Doorman, 0.2,
                                             placeHasARule: true, makingAPoint: false,
                                             streetHeat: heat, playerRefuses: true);
                var searched = CoatHost.Frisk(Coat.Frisker.Constable, 0.7,
                                              placeHasARule: false, makingAPoint: false,
                                              streetHeat: heat, playerRefuses: false);
                // AND THE ONE THAT MUST NOT HAPPEN: nobody with no grounds gets
                // to search you. A frisk is never at random, and a gate that
                // never checks the negative case is testing half a rule.
                var groundless = CoatHost.Frisk(Coat.Frisker.Constable, 0.05,
                                                placeHasARule: false, makingAPoint: false,
                                                streetHeat: heat, playerRefuses: false);
                _friskRefusalCost = refused.IfRefused;
                _friskFound = searched.WorstFind;
                _friskCost = searched.Cost;
                _friskGroundlessHappened = groundless.Happened;
                Debug.Log($"SimDirector: frisk — refusing a doorman is {_friskRefusalCost}; "
                          + $"a constable found {_friskFound:0.00} costing {_friskCost:0.00} "
                          + $"at heat {heat:0.00}; groundless search happened={_friskGroundlessHappened}");
            }

            // ---- and one act that actually bleeds ----
            //
            // THE BLOOD GATE FAILED WITH `taken=0` AND THE WEAPON IS WHY.
            // Every staged act used a cosh, and `cosh.MarksYou` is FALSE —
            // "firearms, the cosh and an accident do not mark you, which is
            // most of the reason to choose them", says the file that defines
            // it. So the gate asserted blood from the one object picked
            // precisely because it leaves none, and it could never have passed.
            //
            // A razor instead, and NON-LETHAL, which is the more interesting
            // half anyway: the target survives, so `Reaction.AsVictim` returns
            // a real account and `IsFleeingVictim` fires — the most dangerous
            // witness in the game, walking somewhere with a story. The §4.7
            // places staging keeps the cosh, because those three have to be
            // the same act as each other and that gate passes.
            if (!_bloodStaged && nearestForThreat != null)
            {
                _bloodStaged = true;
                var razor = Arsenal.Get("razor");
                var cut = ViolenceHost.Commit(razor, _player.transform, nearestForThreat,
                                              "sim-cut", lethal: false, now: now,
                                              harm: _game.Harm, familiarityWithActor: 0.2);
                Debug.Log($"SimDirector: cut {nearestForThreat.DisplayName} with a razor — "
                          + $"marked={cut?.MarkedYou} fleeing={cut?.VictimIsFleeing} "
                          + $"saw={cut?.SawSomething} looksLike="
                          + $"{ViolenceHost.VictimLooksLike(_game.Harm, nearestForThreat.DisplayName, now.Day)}");
            }

            // ---- the threat ----
            if (!_threatStaged && nearestForThreat != null)
            {
                _threatStaged = true;
                var cosh = Arsenal.Get("cosh");
                var t = ViolenceHost.Brandish(cosh, nearestForThreat,
                                              _player.transform.position,
                                              inPublic: true,
                                              reputationForViolence: 0.7,
                                              targetNerve: 0.2,
                                              // THE PLAYER'S OWN FOREARM, so the
                                              // object is drawn on the body the
                                              // camera can see rather than at a
                                              // world position nothing is at.
                                              hand: PlayerForearm());
                Debug.Log($"SimDirector: brandished a cosh at {nearestForThreat.DisplayName} -> {t}"
                          + $" (canUndraw={ViolenceHost.CanUndraw()}, "
                          + $"drawn={HeldObject.Drawn} {HeldObject.LastDrawn})");
            }

            // ---- and the blood, which is the part that costs time ----
            //
            // Aged on the game clock so it dulls to the floor rather than
            // vanishing, offered to everybody near enough to see it, and then
            // washed — which needs water, privacy and twenty-five minutes, and
            // fails without any one of them.
            if (ViolenceHost.PlayerStain != null)
            {
                // Ageing happens once a frame on the hoisted clock reading, up
                // in the delivery block. This is only who can see it.
                ViolenceHost.NoticeStain(_player.transform.position, _npcs, null);
                if (!_washTried && now.Hour >= 2 && now.Hour <= 4)
                {
                    _washTried = true;
                    // The failing attempt first, and it must fail: no privacy
                    // in the street, whatever the clock says.
                    _washFailedInPublic = !ViolenceHost.WashStain(Traces.WashMinutes,
                                                                  hasWaterAndPrivacy: false);
                    _washWorkedAtHome = ViolenceHost.WashStain(Traces.WashMinutes,
                                                               hasWaterAndPrivacy: true);
                    Debug.Log($"SimDirector: blood — failed in public={_washFailedInPublic}, "
                              + $"washed at home={_washWorkedAtHome}, "
                              + $"noticed by {ViolenceHost.StainsNoticed}, "
                              + $"worst social cost {ViolenceHost.WorstStainCost:0.00}");
                }
            }
        }

        /// The transform a held object hangs off. `Mannequin` builds the body
        /// today and the Humanoid right hand replaces it at M17.1; the offset
        /// is measured from the wrist either way, so nothing here changes.
        Transform PlayerForearm()
        {
            if (_player == null) return null;
            var body = _player.GetComponent<Mannequin>();
            return body != null ? body.RForearm : null;
        }

        /// §4.7's headline claim, staged on the street the run actually built.
        ///
        /// The same act, three times, at three arrangements of people found by
        /// measurement rather than authored as coordinates. Every number the
        /// witnesses are judged on is the live world; only the act is
        /// synthetic, exactly as the Phase 2 deed staging is.
        void StageThePlaces(GameTime now)
        {
            if (_placesStaged || now.Day < PlacesStageOnDay) return;
            if (_npcs == null || _npcs.Length < 3 || _player == null) return;

            // For each walker: who else could see something happening to them.
            NpcWalker alley = null, market = null, enclosed = null;
            int alleyOpen = int.MaxValue, marketOpen = -1, enclosedBlocked = -1;
            foreach (var subject in _npcs)
            {
                if (subject == null) continue;
                Vector3 at = subject.transform.position;
                int open = 0, blocked = 0;
                foreach (var other in _npcs)
                {
                    if (other == null || other == subject) continue;
                    float d = Vector3.Distance(other.transform.position, at);
                    if (d > Perception.DetectRangeMetres) continue;
                    if (Perceivers.Occluded(other.transform.position + Vector3.up * 1.6f,
                                            at + Vector3.up * 1.6f)) blocked++;
                    else open++;
                }
                if (open < alleyOpen) { alleyOpen = open; alley = subject; }
                if (open > marketOpen) { marketOpen = open; market = subject; }
                // The back room: people are near, and a wall is between every
                // one of them and the act. `open == 0` is the whole point —
                // an enclosed place with a sightline is just a room.
                if (open == 0 && blocked > enclosedBlocked)
                { enclosedBlocked = blocked; enclosed = subject; }
            }

            if (alley == null || market == null)
            {
                _placesWhy = "the street produced no arrangement to measure";
                return;
            }
            // NOT A FAILURE, A FINDING. If the world has no place where people
            // are close and all of them are blocked, then it has no back room,
            // and that is a fact about the world worth printing rather than a
            // reason to fake a third case.
            if (enclosed == null) _placesWhy = "no enclosed busy place exists in this world";
            else _placesWhy = "ok";

            _placesStaged = true;
            _placesAlley = WitnessesToAKillingAt(alley, "places-alley");
            _placesMarket = WitnessesToAKillingAt(market, "places-market");
            _placesEnclosed = enclosed != null
                ? WitnessesToAKillingAt(enclosed, "places-enclosed") : PlaceReading.None;

            // THE OPEN/BLOCKED COUNTS BESIDE THE RESULT, because they are what
            // chose these three walkers. If eyes and open ever disagree — an
            // alley with nobody in line of sight producing sighted witnesses —
            // the disagreement is between the staging and the resolver, and
            // this line is the only place it would be visible.
            Debug.Log($"SimDirector: §4.7 places — "
                      + $"alley eyes={_placesAlley.Eyes} noticed={_placesAlley.Noticed} "
                      + $"named={_placesAlley.Named} considered={_placesAlley.Considered} (open {alleyOpen}) | "
                      + $"market eyes={_placesMarket.Eyes} noticed={_placesMarket.Noticed} "
                      + $"named={_placesMarket.Named} considered={_placesMarket.Considered} (open {marketOpen}) | "
                      + $"enclosed eyes={_placesEnclosed.Eyes} noticed={_placesEnclosed.Noticed} "
                      + $"named={_placesEnclosed.Named} (blocked {enclosedBlocked}) — {_placesWhy}");
        }

        /// A place nobody can see, found by looking rather than assumed.
        ///
        /// Walks outward from the crowd's centre and returns the first point
        /// with NOBODY inside `Perception.DetectRangeMetres` with a clear line
        /// — the wider of the two radii this is used for, so a spot that passes
        /// here also passes the disposal test at eighteen metres.
        ///
        /// Reports how many watchers the best candidate had. A world too small
        /// or too busy to contain an empty spot is a finding about the world,
        /// and the gate should say so rather than quietly asserting the design.
        Vector3 QuietSpot(out int watchers)
        {
            watchers = int.MaxValue;
            Vector3 best = _player != null ? _player.transform.position : Vector3.zero;
            if (_npcs == null || _npcs.Length == 0) { watchers = 0; return best; }

            Vector3 centre = Vector3.zero;
            int n = 0;
            foreach (var w in _npcs) { if (w != null) { centre += w.transform.position; n++; } }
            if (n == 0) { watchers = 0; return best; }
            centre /= n;

            // Eight bearings, three distances. Cheap, and it beats one offset in
            // a direction that might walk into the next street.
            foreach (float radius in new[] { 45f, 80f, 130f })
                for (int i = 0; i < 8; i++)
                {
                    float a = i * Mathf.PI * 2f / 8f;
                    var at = centre + new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * radius;
                    int seen = 0;
                    foreach (var w in _npcs)
                    {
                        if (w == null) continue;
                        if (Vector3.Distance(w.transform.position, at)
                            > Perception.DetectRangeMetres) continue;
                        if (Perceivers.Occluded(w.transform.position + Vector3.up * 1.6f,
                                                at + Vector3.up * 1.0f)) continue;
                        seen++;
                    }
                    if (seen < watchers) { watchers = seen; best = at; }
                    if (watchers == 0) return best;
                }
            return best;
        }

        /// One killing, at this person, with the player standing beside them.
        ///
        /// The actor needs a transform with a position and a facing, and the
        /// player is somewhere else entirely — so a throwaway one is placed a
        /// metre off and turned to face the victim. That is the geometry of
        /// somebody standing over somebody, and it is the only synthetic part.
        /// What one staged killing produced, in four columns rather than one.
        ///
        /// THE GATE READ THE WRONG NUMBER AND COULD NOT HAVE KNOWN. It used
        /// `SawSomething`, which counts every observation that is not empty —
        /// and `Observe.Resolve` fills `Slot.Act` on `seesVictim || heardAct ||
        /// heardCry`. A killing is loud and `Witnesses.ConsiderMetres` is 80m,
        /// so everybody in an eighty-metre circle hears it through whatever
        /// walls are in the way and lands a non-empty observation. The alley
        /// and the market both returned 53, which is not two places measuring
        /// the same and is not a coincidence: it is one number saturating.
        ///
        /// That is right about the world and wrong for the claim. §4.7 says the
        /// same killing "leaves no witness in an empty alley, several in a
        /// market, and none in the back room of a busy pub" — and a man who
        /// heard a noise seventy metres away through a wall is not a witness to
        /// a killing in any sense that sentence means. What distinguishes the
        /// three places is SIGHT, which is exactly why sound does not: a scream
        /// carries into the back room and out of the alley alike.
        ///
        /// So all four are measured and all four are printed, and the gate
        /// reads `Eyes`. If a later run shows `Eyes` cannot separate them
        /// either, the run itself will say which column can — the deedSlotSets
        /// resolution, which was to make the thing print its series rather than
        /// to keep guessing at a threshold.
        struct PlaceReading
        {
            public int Considered;   // within 80m of it at all
            public int Noticed;      // got anything, hearing included
            public int Eyes;         // SAW the victim go down, or saw who did it
            public int Named;        // rung 4 — could give a name
            public static PlaceReading None =>
                new PlaceReading { Considered = -1, Noticed = -1, Eyes = -1, Named = -1 };
            public override string ToString() =>
                $"{Eyes}(noticed {Noticed}/{Considered}, named {Named})";
        }

        PlaceReading WitnessesToAKillingAt(NpcWalker victim, string eventId)
        {
            if (victim == null) return PlaceReading.None;
            Vector3 victimAt = victim.transform.position;
            var stand = new GameObject("sim-actor");
            try
            {
                Vector3 offset = victim.transform.forward * -1f;
                if (offset.sqrMagnitude < 0.01f) offset = Vector3.forward;
                stand.transform.position = victimAt + offset;
                stand.transform.LookAt(new Vector3(victimAt.x, stand.transform.position.y, victimAt.z));

                // THE SAME KILLING, all three times. Same weapon, same lethality,
                // same everything — if the three numbers differ it is because
                // the places differ, which is the entire claim.
                var weapon = Arsenal.Get("cosh");
                var after = ViolenceHost.Commit(weapon, stand.transform, victim, eventId,
                                                lethal: true, now: _game.Now,
                                                harm: _game.Harm,
                                                familiarityWithActor: 0.0);
                if (after == null || after.Seen == null) return PlaceReading.None;

                var r = new PlaceReading { Considered = Witnesses.Considered };
                foreach (var o in after.Seen)
                {
                    if (o == null || o.Empty) continue;
                    r.Noticed++;
                    // SIGHT, WHICH IS WHAT THE CLAIM IS ABOUT. `Victim` is set
                    // by `seesVictim` and `Actor` by `seesActor`; neither can be
                    // filled by hearing, which is the whole reason they are
                    // separate slots from `Act`.
                    if (o.Has(Slot.Victim) || o.Has(Slot.Actor)) r.Eyes++;
                    if (o.NamesSomebody) r.Named++;
                }
                return r;
            }
            finally
            {
                Destroy(stand);
            }
        }

        void MeasureAo()
        {
            _tookAoPair = true;
            var cam = Camera.main;
            if (cam == null) return;
            for (int i = 0; i < AoSamples; i++) MeasureAoOnce(i);
        }

        /// Every noon/night pair from the run, so the next threshold can be
        /// chosen from data instead of from a guess.
        string _lumaSeries = "";
        double _aoSpread = -1, _grainSpread = -1;
        double _aoFraction = -1, _aoDrop = -1;
        double _reflFraction = -1, _reflRise = -1;
        double _specFraction = -1, _specRise = -1;
        double _presetFraction = -1;
        double _bloomFraction = -1, _bloomRise = -1, _bloomHadHighlights = -1;
        float _stemVolumeMax = -1f, _busMusicMax = -1f, _busMusicMin = 9f;
        int _stemsUnbound;
        double _stemRatioMin = double.MaxValue, _stemRatioMax = 0;
        double StemRatioSpread =>
            _stemRatioMax > 0 && _stemRatioMin < double.MaxValue
                ? _stemRatioMax / _stemRatioMin : -1;

        /// Twelve metres: big enough that its near arc is unmistakably in frame
        /// and small enough that the line is several pixels wide at that
        /// distance. A district-sized circle would be a hairline forty metres
        /// away and a room-sized one would be under the camera.
        const double RingProbeRadius = 12.0;

        /// Fraction of the frame the ring CHANGED — brightened plus darkened,
        /// because a pale line can be darker than the lamp behind it and reading
        /// only one direction is how the occlusion gate measured its own
        /// blind spot. Negative until measured: a gate that cannot tell "not
        /// measured" from "measured zero" is the trap the loiter probe fell into.
        double _ringSeenFraction = -1, _ringSeenRise = -1;

        /// The same measurement for each candidate material, and for a positive
        /// control that has nothing to do with the ring at all.
        ///
        /// THE CONTROL IS THE POINT. Last run said zero changed pixels, and that
        /// has two completely different explanations: the ring does not render,
        /// or this A/B cannot see anything render. A plain quad three metres in
        /// front of the camera distinguishes them in the same run, and without it
        /// I would be back to guessing at half an hour a guess.
        double _ringSeenLedger = -1, _ringSeenSprites = -1, _ringSeenParticles = -1;
        double _ringSeenNone = -1;
        double _ringSeenTransformZ = -1;
        double _controlSeen = -1;
        bool _ringSweptOnce;

        /// FORTY-SIX PIXELS OF A 640x360 FRAME. Set to catch "nothing at all"
        /// rather than to grade the drawing: a twelve-metre ring should come in
        /// an order of magnitude above this, and if it lands just over the line
        /// that is itself worth knowing.
        const double RingSeenFloor = 0.0002;

        /// How much of the frame a ring drawn with this material changes.
        ///
        /// BOTH DIRECTIONS. A pale line over dark asphalt brightens and the same
        /// line across a lamp's glare darkens, and counting only one of those is
        /// how a gate ends up measuring its own blind spot.
        (double fraction, double rise) RingSeenWith(Camera cam, NoiseRing.Paint paint,
                                                    NoiseRing.Lay lay = NoiseRing.Lay.FlatBillboard)
        {
            var probe = NoiseRing.ForVerification(_player.transform.position,
                                                  RingProbeRadius, paint, lay);
            if (probe == null) return (-1, -1);
            try
            {
                probe.LineEnabled = false;
                var off = FrameShot(cam);
                probe.LineEnabled = true;
                var on = FrameShot(cam);
                // `FrameShot` returns an empty struct if the render failed, and
                // comparing two nulls would throw inside a gate rather than fail it.
                if (on.Luma == null || off.Luma == null) return (-1, -1);
                var up = ImageStats.Brightened(on.Luma, off.Luma, ImageStats.QuantisationStep);
                var down = ImageStats.Darkened(on.Luma, off.Luma, ImageStats.QuantisationStep);
                return (up.fraction + down.fraction, up.meanRise);
            }
            finally
            {
                // SWITCHED OFF BEFORE IT IS DESTROYED, and this is a real bug
                // rather than tidiness. `Destroy` is DEFERRED to the end of the
                // frame, so a probe that has been destroyed is still in the
                // scene for every later render in that same frame — including
                // the next arm of this sweep, which draws its circle in the very
                // same place. The second arm then toggles a line over pixels the
                // first arm has already lit and measures almost nothing.
                //
                // That is exactly what the numbers showed: `None` measured
                // 0.7279% when it ran first and 0.0000% when it ran fourth, for
                // identical code. The first arm of each frame was clean and
                // every arm after it was reading through the previous one.
                probe.LineEnabled = false;
                UnityEngine.Object.Destroy(probe.gameObject);
            }
        }

        /// THE POSITIVE CONTROL: a plain quad three metres in front of the
        /// camera, with nothing of the ring in it. If this reads zero too then
        /// the A/B itself is blind and every ring number above is meaningless —
        /// which is a completely different repair from "the line does not draw",
        /// and telling them apart is worth one quad.
        double ControlSeen(Camera cam)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
            try
            {
                var col = go.GetComponent<Collider>();
                // Disabled rather than destroyed: `Destroy` is deferred to the
                // end of the frame and a two-metre wall in front of the player
                // for even one physics step is a shove nobody asked for.
                if (col != null) col.enabled = false;
                go.transform.position = cam.transform.position + cam.transform.forward * 3f;
                go.transform.rotation = Quaternion.LookRotation(cam.transform.forward);
                go.transform.localScale = new Vector3(2f, 2f, 1f);
                var mr = go.GetComponent<MeshRenderer>();
                if (mr == null) return -1;
                mr.enabled = false;
                var off = FrameShot(cam);
                mr.enabled = true;
                var on = FrameShot(cam);
                if (on.Luma == null || off.Luma == null) return -1;
                var up = ImageStats.Brightened(on.Luma, off.Luma, ImageStats.QuantisationStep);
                var down = ImageStats.Darkened(on.Luma, off.Luma, ImageStats.QuantisationStep);
                return up.fraction + down.fraction;
            }
            finally
            {
                // Hidden before it is destroyed, for the reason above: a
                // deferred `Destroy` leaves a two-metre quad in front of the
                // camera for the rest of the frame, and everything measured
                // after it in this function would have been looking at a wall.
                var mr2 = go.GetComponent<MeshRenderer>();
                if (mr2 != null) mr2.enabled = false;
                UnityEngine.Object.Destroy(go);
            }
        }

        void MeasureAoOnce(int sample)
        {
            var cam = Camera.main;
            if (cam == null) return;
            // Night, and a frame with geometry in it: occlusion on an empty
            // street is correctly almost nothing, and measuring THAT would
            // give a difference of zero and a gate that fails for being
            // pointed somewhere honest.
            var all = FrameShot(cam);

            // ---- THE NOISE RING, ON SCREEN OR NOT ----
            //
            // The one thing the last build could not tell me. `ringsDrawn` counts
            // circles CONSTRUCTED, and a `LineRenderer` standing upright with its
            // ribbon aimed at the road constructs perfectly and draws nothing a
            // player can see. So: render this frame with the ring's renderer off,
            // render it again with the renderer on, and count the pixels that got
            // brighter. Same ruler as occlusion and reflections.
            //
            // Rendered IMMEDIATELY on either side of the toggle rather than
            // across two game frames, because "an A/B is only a measurement if
            // the thing it switches is switched by the time the frame is drawn"
            // — which this project has now paid for twice.
            // MEASURED EVERY SAMPLE AND THE BEST ONE KEPT, not latched on the
            // first. One render could catch the player in a doorway with the
            // circle behind a wall, and a single unlucky sample latching zero
            // would fail a gate about the ring for a reason that is about the
            // street. Same policy as the occlusion sampler above.
            if (_player != null)
            {
                var (frac, rise) = RingSeenWith(cam, NoiseRing.Paint.Ledger);
                if (frac > _ringSeenFraction) { _ringSeenFraction = frac; _ringSeenRise = rise; }
                if (frac > _ringSeenLedger) _ringSeenLedger = frac;

                // The two rejected candidates and the control, once. They exist
                // to tell me WHY a zero is a zero, and once is enough for that —
                // paying for six extra renders on every sample would be buying
                // the same fact three times.
                if (!_ringSweptOnce)
                {
                    _ringSweptOnce = true;
                    _ringSeenSprites = RingSeenWith(cam, NoiseRing.Paint.SpritesDefault).fraction;
                    _ringSeenParticles =
                        RingSeenWith(cam, NoiseRing.Paint.ParticlesAlphaBlended).fraction;
                    _ringSeenNone = RingSeenWith(cam, NoiseRing.Paint.None).fraction;
                    _ringSeenTransformZ = RingSeenWith(cam, NoiseRing.Paint.Ledger,
                                                       NoiseRing.Lay.FlatTransformZ).fraction;
                    _controlSeen = ControlSeen(cam);
                    Debug.Log($"SimDirector: ring materials — ledger={100 * _ringSeenLedger:0.0000}% "
                              + $"sprites={100 * _ringSeenSprites:0.0000}% "
                              + $"particles={100 * _ringSeenParticles:0.0000}% "
                              + $"none={100 * _ringSeenNone:0.0000}% "
                              + $"transformZ={100 * _ringSeenTransformZ:0.0000}% "
                              + $"control={100 * _controlSeen:0.0000}%");
                }
            }

            FilmGrade.AmbientOcclusion = false;
            var noAo = FrameShot(cam);
            FilmGrade.AmbientOcclusion = true;

            FilmGrade.Bloom = false;
            var noBloom = FrameShot(cam);
            FilmGrade.Bloom = true;

            FilmGrade.Grain = false;
            var noGrain = FrameShot(cam);
            FilmGrade.Grain = true;

            FilmGrade.Vignette = false;
            var noVig = FrameShot(cam);
            FilmGrade.Vignette = true;

            // REFLECTIONS, and this was the last render gate that could pass
            // with the effect switched off. `reflOk` proved the probe woke
            // up, refreshed, and was rate-limited — all true of a probe whose
            // contribution to the image is nothing. A reflection ADDS light
            // to wet ground, so it is read exactly as occlusion is, upside
            // down.
            WetReflections.Enabled = false;
            var noRefl = FrameShot(cam);
            WetReflections.Enabled = true;
            var (rFrac, rRise) = ImageStats.Brightened(all.Luma, noRefl.Luma,
                                                       ImageStats.QuantisationStep);
            // THE BEST OF THE ROUNDS, NOT THE LAST — which is what the comment
            // at the bottom of this function has always claimed and what only
            // the occlusion and grain numbers actually did.
            //
            // This is not a weakened gate. The claim is "toggling this changes
            // the image", and a night where it moved seven percent of the pixels
            // PROVES that; a later night with the camera facing a plain wall does
            // not unprove it. Taking the maximum is the correct estimator for
            // "does this effect ever do anything", and taking the last was
            // simply a bug wearing the clothes of a measurement.
            if (rFrac > _reflFraction) { _reflFraction = rFrac; _reflRise = rRise; }

            // THE POSITIVE CONTROL. Flattening the smoothness of every wet
            // surface removes the specular term by a route with no probe
            // mechanics in it. If this moves the frame and the probe toggle
            // above does not, the probe is not what is lighting the road —
            // and if NEITHER moves it, wet specular is contributing nothing
            // and the whole effect is decorative.
            //
            // Two toggles because one cannot distinguish those, and each
            // guess costs a twenty-five minute build.
            // DOES THE GRAPHICS PRESET DO ANYTHING. A performance setting
            // that changes no pixels is the same failure as an effect that
            // never runs, wearing the opposite coat — and it is worse in one
            // way, because a player turns it down, sees nothing improve, and
            // concludes the game is simply slow.
            //
            // Low against High: no shafts, short shadows, no reflections,
            // less body detail. If that renders the same frame, the whole
            // preset is a label.
            int wasDetail = GameSettings.Current.Detail;
            GameSettings.Current.Detail = (int)DetailLevel.Low;
            SceneLighting.ApplyQuality();
            var lowFrame = FrameShot(cam);
            GameSettings.Current.Detail = wasDetail;
            SceneLighting.ApplyQuality();
            var (dDark, _) = ImageStats.Darkened(lowFrame.Luma, all.Luma,
                                                 ImageStats.QuantisationStep);
            var (dBright, _) = ImageStats.Brightened(lowFrame.Luma, all.Luma,
                                                     ImageStats.QuantisationStep);
            _presetFraction = Math.Max(_presetFraction, dDark + dBright);

            AssetLibrary.DefeatWetSpecular(true);
            var noSpec = FrameShot(cam);
            AssetLibrary.DefeatWetSpecular(false);
            var (sFrac, sChange) = ImageStats.Brightened(all.Luma, noSpec.Luma,
                                                         ImageStats.QuantisationStep);
            var (sDarker, _) = ImageStats.Darkened(all.Luma, noSpec.Luma,
                                                   ImageStats.QuantisationStep);
            if (sFrac + sDarker > _specFraction)
            { _specFraction = sFrac + sDarker; _specRise = sChange; }

            // Keep the BEST-EVIDENCED sample rather than the last, and
            // record how far the samples disagreed. A gate reading the last
            // of three is still reading one sample; the spread is the number
            // that says whether any of them mean anything.
            // MEASURED WHERE IT LANDED, not averaged over the frame it
            // correctly did not touch. Occlusion darkens creases — a few
            // percent of a street — so the global mean divides its result by
            // the twenty parts of the image that were never in shadow, and a
            // working pass reads as 0.0014 against a floor of 0.002.
            var (aoFrac, aoDrop) = ImageStats.Darkened(all.Luma, noAo.Luma,
                                                       ImageStats.QuantisationStep);
            if (aoFrac > _aoFraction) { _aoFraction = aoFrac; _aoDrop = aoDrop; }
            double aoD = noAo.Mean - all.Mean;
            double grainD = all.LocalSpread - noGrain.LocalSpread;
            // THE FIRST SAMPLE EVER, not the first of each round — which is a
            // bug I introduced an hour ago by adding rounds. `sample` is the
            // INNER loop index, so it is 0 once per evening and the range reset
            // itself every time, leaving a "spread" that described only the last
            // round. The run reported aoRange=0.00124..0.00124 from nine samples
            // across three separate nights, which is not a number anybody should
            // believe.
            //
            // Nothing gates on the spread, which is exactly why it was worth
            // fixing immediately: an ungated number that looks like evidence is
            // the kind of thing that gets quoted later.
            if (!_spreadSeeded)
            {
                _spreadSeeded = true;
                _aoDeltaMin = _aoDeltaMax = aoD;
                _grainDeltaMin = _grainDeltaMax = grainD;
            }
            else
            {
                if (aoD < _aoDeltaMin) _aoDeltaMin = aoD;
                if (aoD > _aoDeltaMax) _aoDeltaMax = aoD;
                if (grainD < _grainDeltaMin) _grainDeltaMin = grainD;
                if (grainD > _grainDeltaMax) _grainDeltaMax = grainD;
            }
            _aoSpread = _aoDeltaMax - _aoDeltaMin;
            _grainSpread = _grainDeltaMax - _grainDeltaMin;

            _aoOn = all.Mean;
            _aoOff = noAo.Mean;
            _bloomDelta = all.Bright - noBloom.Bright;
            // WHERE IT ACTS, like the occlusion pass. Bloom spreads
            // highlights, so the pixels it touches are the ones beside
            // something bright — a small and very specific part of the frame.
            // The bright-pixel FRACTION is a global count and collapses to
            // nothing whenever the camera happens not to be looking at a
            // lamp, which is how a working bloom came back at +0.0002.
            var (bFrac, bRise) = ImageStats.Brightened(all.Luma, noBloom.Luma,
                                                       ImageStats.QuantisationStep);
            _bloomFraction = bFrac;
            _bloomRise = bRise;
            _bloomHadHighlights = all.Bright;
            _grainDelta = grainD;
            // A vignette makes the corners darker RELATIVE to the centre, so
            // the ratio must FALL when it is on. Comparing absolute corner
            // brightness would have been fooled by anything that changed the
            // whole frame.
            _vigOn = all.EdgeRatio;
            _vigOff = noVig.EdgeRatio;
            Debug.Log($"SimDirector: post a/b [{sample}] aoD={aoD:0.00000} grainD={grainD:0.00000} "
                      + $"aoSpread={_aoSpread:0.00000} grainSpread={_grainSpread:0.00000}");
            Debug.Log($"SimDirector: post a/b ao={all.Mean:0.0000}/{noAo.Mean:0.0000} "
                      + $"bloomBright={all.Bright:0.0000}/{noBloom.Bright:0.0000} "
                      + $"grainLocal={all.LocalSpread:0.0000000}/{noGrain.LocalSpread:0.0000000} "
                      + $"vigEdge={all.EdgeRatio:0.000}/{noVig.EdgeRatio:0.000}");
        }

        /// One rendered frame, reduced to the three numbers the post gates
        /// need. THREE, because the three effects do different things and a
        /// single ruler cannot see all of them:
        ///
        ///   mean       — occlusion darkens, so this is its ruler.
        ///   bright     — bloom SPREADS highlights without moving the mean
        ///                much, so the fraction of bright pixels is its ruler.
        ///   variance   — grain is signed noise. It barely moves the mean at
        ///                all, by construction; local spread is the only
        ///                thing that changes.
        ///   edgeRatio  — corner brightness over centre brightness, which is
        ///                precisely and only what a vignette does.
        ///
        /// Reaching for mean luminance for all four would have found the
        /// occlusion and quietly passed the other three, which is the same
        /// mistake as measuring total energy for the score gate and the fog
        /// ratio against the wrong colour. Check the ruler.
        struct FrameStats
        {
            public double Mean, Bright, Variance, EdgeRatio, LocalSpread;
            /// The frame itself, kept so two renders can be compared pixel by
            /// pixel. A local effect cannot be measured by any single number
            /// summarising the whole image — that was the occlusion gate's
            /// mistake, and no choice of summary statistic fixes it.
            public double[] Luma;
        }

        FrameStats FrameShot(Camera cam)
        {
            // A COMPOSED FRAME IS NOT THE FRAME WE MEASURE. Framing runs
            // in the sim now — it never used to, which is why the whole
            // cinematic layer went months without executing in a verified
            // build — but a push-in part-way through a measured render moves
            // the luminance the lighting gate reads. Aborting is a smaller
            // exclusion than switching the layer off for the run.
            if (_game != null && _game.Player != null) _game.Player.Beat.Abort();
            var st = new FrameStats();
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
                if (px.Length == 0) return st;

                double sum = 0, sumSq = 0, bright = 0;
                double centre = 0, corner = 0;
                int centreN = 0, cornerN = 0;
                int w = tex.width, h = tex.height;
                var luma = new double[px.Length];
                for (int i = 0; i < px.Length; i++)
                {
                    var c = px[i];
                    double l = ImageStats.Luma(c.r, c.g, c.b);
                    luma[i] = l;
                    sum += l; sumSq += l * l;
                    if (l > 0.6) bright++;
                    // Where in the frame, for the vignette ruler.
                    double x = (i % w) / (double)w - 0.5;
                    double y = (i / w) / (double)h - 0.5;
                    double dd = x * x + y * y;
                    if (dd < 0.02) { centre += l; centreN++; }
                    else if (dd > 0.36) { corner += l; cornerN++; }
                }
                st.Mean = sum / px.Length;
                st.Variance = sumSq / px.Length - st.Mean * st.Mean;
                // THE RULER THE GRAIN GATE ALWAYS CLAIMED TO USE. Its own
                // comment said "local spread is the only thing that changes"
                // and then it read global variance, which is dominated by sky
                // against lamps and which clamping at black can drive the
                // wrong way outright. Proved in CoreTests on one image where
                // the two statistics disagree about the sign.
                st.LocalSpread = ImageStats.LocalSpread(luma, w);
                st.Luma = luma;
                st.Bright = bright / px.Length;
                st.EdgeRatio = (centreN > 0 && cornerN > 0 && centre > 1e-6)
                    ? (corner / cornerN) / (centre / centreN) : 1.0;
                return st;
            }
            catch (Exception e) { _errors.Add("FrameShot: " + e.Message); return st; }
            finally
            {
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                if (tex != null) UnityEngine.Object.Destroy(tex);
                if (rt != null) rt.Release();
            }
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
            // A COMPOSED FRAME IS NOT THE FRAME WE MEASURE. Framing runs
            // in the sim now — it never used to, which is why the whole
            // cinematic layer went months without executing in a verified
            // build — but a push-in part-way through a measured render moves
            // the luminance the lighting gate reads. Aborting is a smaller
            // exclusion than switching the layer off for the run.
            if (_game != null && _game.Player != null) _game.Player.Beat.Abort();
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

                // AND A SMALL JPEG THE BUILD CAN COMMIT, so the render can be
                // LOOKED AT rather than inferred.
                //
                // The PNG below goes to an artifact host this project's review
                // environment is denied outright, which is why the ASCII
                // thumbnail underneath exists at all — a coarse luminance grid
                // standing in for the picture. It caught a magenta error shader
                // once and it cannot tell moss from cobble.
                //
                // That stopped being an acceptable trade the moment a real
                // texture pack landed. Three of the first three albedos
                // inspected were off-brief — red rust through the asphalt,
                // bright green moss through the paving, ochre rubble where red
                // brick was asked for — and whether `SurfaceSpec`'s noir tint
                // rescues them is not answerable from the source images or from
                // a luminance mean. It is answerable by looking at the street.
                //
                // Quality 60 at 1280x720 is ~150KB, which a run can commit
                // without the repository growing the way a PNG per shot would.
                // The same file name every run, so it overwrites rather than
                // accumulates.
                //
                // AND ONLY THE FIRST FEW. The sim shoots noon and night on every
                // in-game day, so a seventeen-day run is thirty-four stills —
                // five megabytes committed per build, every build, all night.
                // Four is enough to judge a surface: two lighting conditions,
                // twice, and the day numbers are stable across runs so they
                // overwrite rather than pile up.
                if (_reviewStills < MaxReviewStills)
                {
                    _reviewStills++;
                    System.IO.File.WriteAllBytes($"sim-out/review_{name}.jpg",
                                                 tex.EncodeToJPG(60));
                }

                // Emit a coarse ASCII luminance thumbnail + mean colour to the log.
                // The PNG artifact lives on a host our review environment can't reach,
                // but the job LOG is readable — so this is how the render gets "seen"
                // for blind iteration on visuals.
                // WHAT THE SKY ACTUALLY WAS, recorded beside the frame.
                //
                // The noon stills come back flat, with the sky near white, and
                // every explanation for that is a guess until the run says
                // which value produced it — the fog colour, the camera
                // background, the density, or the grade on top. Two separate
                // systems write `RenderSettings.fogColor` and the ambient
                // trilight every frame (`SceneLighting` and `GameController`),
                // so which one is winning is not answerable by reading either.
                //
                // Cheap, and it is the `deedSlotSets` move again: make the run
                // print the series rather than argue about the number.
                var bg = cam.backgroundColor;
                var fc = RenderSettings.fogColor;
                Debug.Log($"SimDirector: sky {name} fogMode={RenderSettings.fogMode} "
                          + $"fogOn={RenderSettings.fog} "
                          + $"density={RenderSettings.fogDensity:0.0000} "
                          + $"fogRGB=({fc.r:0.000},{fc.g:0.000},{fc.b:0.000}) "
                          + $"bgRGB=({bg.r:0.000},{bg.g:0.000},{bg.b:0.000}) "
                          + $"clear={cam.clearFlags} "
                          + $"ambSky={RenderSettings.ambientSkyColor.r:0.000},"
                          + $"{RenderSettings.ambientSkyColor.g:0.000},"
                          + $"{RenderSettings.ambientSkyColor.b:0.000}");

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
            int beatsAttended = 0, beatsSkipped = 0;
            var beatStates = new List<object>();
            foreach (var b in _game.Beats.All)
            {
                beatStates.Add($"{b.Id}:{b.State}");
                if (b.WindowPassed(_game.Now) && b.State == BeatState.Pending) beatsResolved = false;
                if (b.State == BeatState.Attended) beatsAttended++;
                else if (b.State == BeatState.Skipped) beatsSkipped++;
            }
            // AND AT LEAST ONE MUST ACTUALLY HAPPEN.
            //
            // "Nothing left Pending" was the whole test, and a Skipped beat
            // satisfies it — so a run in which the player attended nothing,
            // ever, was indistinguishable from one in which the authored
            // content worked. Every CI run for months read
            // [tea:Skipped,toast:Skipped,evening_d8:Skipped,evening_d12:Skipped]
            // and passed.
            //
            // Skipping still has to be POSSIBLE — standing someone up is a
            // real choice with a real loyalty cost, and a gate demanding every
            // beat be attended would be asserting the player has no options.
            // One is the claim: the path exists and runs.
            beatsResolved = beatsResolved && beatsAttended >= 1;
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

            // FRAME TIME, WHICH NOTHING WAS MEASURING.
            //
            // `perfOk` above gates ONE SUBSYSTEM — the traffic update — and
            // has done since it was written. A global regression could not
            // fail it, and in fact one did not: the day bodies landed the sim
            // went from ten and a half minutes to eighteen, and the only
            // thing that noticed was the job's twenty-four minute wall clock.
            // That is a diagnosis-free failure on a twenty-minute loop.
            //
            // THE NUMBER IS A REGRESSION DETECTOR, NOT A TARGET. This runner
            // has no GPU and software-rasterises everything, so 187ms is a
            // healthy frame here and would be catastrophic anywhere else.
            // What it catches is the frame time DOUBLING, which is what
            // happened and what a per-subsystem gate structurally cannot see.
            double meanFrameMs = Perf.MeanFrameMs;

            // WHERE IT WENT, measured first, because the gate is now set on a
            // part of it rather than on the whole.
            //
            // `render+rest` is a residue rather than a scope: this runner has no
            // GPU and software-rasterises 1280x720 with bloom, AO, reflections
            // and grain, so most of the frame is expected to land there.
            var perFrame = new List<string>();
            double attributed = 0;
            foreach (var name in new[] { "npcs", "population", "sun", "checks", "traffic", "signals" })
            {
                var c = Perf.Get(name);
                if (c == null || c.Samples == 0) { perFrame.Add($"{name}=none"); continue; }
                double perFrameMs = Perf.FrameCount > 0 ? c.TotalMs / Perf.FrameCount : 0;
                attributed += perFrameMs;
                perFrame.Add($"{name}={perFrameMs:0.00}ms");
            }
            double residueMs = Math.Max(0, meanFrameMs - attributed);
            perFrame.Add($"game={attributed:0.00}ms render+rest={residueMs:0.00}ms");
            string frameWhere = string.Join(" ", perFrame);

            // AND THE GATE IS ON THE GAME'S HALF, NOW THAT A RUN HAS SPLIT THEM.
            //
            // The previous budget was the whole frame against 300ms, with a
            // comment promising it would stay there "until a run has actually
            // attributed the growth". A run has:
            //
            //     npcs 2.05  population 1.05  sun 1.74
            //     checks 0.09  traffic 1.03  signals 0.04   = 6.00ms
            //     render+rest                               = 297.25ms
            //
            // 98% of the frame is a software rasteriser on a machine with no
            // GPU. Two consecutive runs put the total at 293.29ms and 303.26ms
            // with nothing between them that touches rendering, so a gate at 300
            // sits inside the runner's own noise — it fails on which agent
            // picked the job up. That is `nightNotDarker` failing at 0.136
            // against 0.135 all over again: a rounding wearing a threshold's
            // clothes.
            //
            // Moving 300 to 310 would be the easy repair and the wrong one, for
            // the reason the old comment gave. The right one is to gate the
            // quantity the game controls. 6.00ms of game systems against a
            // 16.67ms frame at 60fps is the real budget, and 12ms — under three
            // quarters of that frame, twice what was measured — is a ceiling a
            // genuine regression crosses and runner noise does not, because
            // runner noise lands in the residue.
            //
            // The residue is still printed every run. When enough runs have
            // reported it, it can have a gate of its own, set from the series
            // rather than from two points.
            const double GameFrameBudgetMs = 12.0;
            bool frameOk = meanFrameMs <= 0 || attributed < GameFrameBudgetMs;


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
            // AND THE TEXT RENDERED. Opening, speaking and closing are all
            // true of a panel whose font did not resolve and which draws an
            // empty rectangle — and the font this game gets depends on which
            // machine it is running on.
            bool glyphsOk = _labels > 0 && _labelsFontless == 0 && _labelsBlank == 0;
            bool uiOk = _uiSmokeRun && panelsBad == 0 && panelsOk >= 7 && glyphsOk;

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
                // EVERY DAY, NOT THE LAST ONE. `dayLuma` and `nightLuma` were
                // each overwritten by whichever shot came last, so an
                // eleven-day run was gated on a single pair of frames — and it
                // failed at 0.136 against 0.135, which is not a measurement,
                // it is a rounding. Weather, district and the open-city switch
                // all move a single frame by more than that.
                var noonLumas = new List<double>();
                var nightLumas = new List<double>();
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
                    if (nm.Contains("noon")) { dayLuma = luma; noonLumas.Add(luma); }
                    if (nm.Contains("night"))
                    {
                        nightLuma = luma; nightSat = ShotNum(shot, "satPct");
                        nightLumas.Add(luma);
                    }
                }
                // Night must actually be darker than noon. This is the one
                // that proves the day/night curves reach the RENDER rather
                // than merely being computed correctly in a test.
                //
                // ACROSS THE RUN, AND ON MOST DAYS. Two conditions, because
                // either alone is weak: the MEANS must separate (a broken
                // curve makes them equal, and no amount of weather fixes
                // that), and night must win on MOST PAIRED DAYS (a mean can
                // be carried by one freak frame). One pair of frames, which
                // is what this used to be, proves neither.
                if (noonLumas.Count > 0 && nightLumas.Count > 0)
                {
                    double noonMean = 0, nightMean = 0;
                    for (int i = 0; i < noonLumas.Count; i++) noonMean += noonLumas[i];
                    for (int i = 0; i < nightLumas.Count; i++) nightMean += nightLumas[i];
                    noonMean /= noonLumas.Count; nightMean /= nightLumas.Count;
                    int pairs = Math.Min(noonLumas.Count, nightLumas.Count), darker = 0;
                    for (int i = 0; i < pairs; i++) if (nightLumas[i] < noonLumas[i]) darker++;
                    // PRINT THE SERIES. A threshold set without looking at the
                    // numbers is the mistake this project keeps making, and
                    // there is no way to look at these without asking for
                    // them: they live inside one frame of one CI run. With
                    // the pairs in the log, a margin can be chosen from
                    // evidence rather than invented here.
                    var series = new System.Text.StringBuilder();
                    for (int i = 0; i < pairs; i++)
                        series.Append(i == 0 ? "" : " ")
                              .Append($"{noonLumas[i]:0.000}/{nightLumas[i]:0.000}");
                    _lumaSeries = $"noon{noonMean:0.000} night{nightMean:0.000} " +
                                  $"darker{darker}of{pairs} [{series}]";
                    if (nightMean >= noonMean)
                    {
                        lightingOk = false;
                        lightingWhy.Add($"nightNotDarkerMean:{nightMean:0.000}>={noonMean:0.000}");
                    }
                    if (pairs > 0 && darker * 2 <= pairs)
                    {
                        lightingOk = false;
                        lightingWhy.Add($"nightDarkerOn:{darker}/{pairs}days");
                    }
                }
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

            // AND SOMETHING IS ACTUALLY REFLECTED. Everything above is true
            // of a probe that woke, refreshed on schedule, obeyed its rate
            // limit and contributed not one pixel to the image.
            //
            // Reported rather than gated on this run. The A/B is taken at
            // 21:00 and the road is only wet when it has been raining, so a
            // dry evening would fail a gate for being pointed somewhere
            // honest — the same trap the occlusion measurement was written to
            // avoid. What the run reports is whether it was wet at the time
            // and what the probe was worth if so; one reading turns it into a
            // gate conditioned on wetness.
            bool reflSeen = _reflFraction > 0.002 && _reflRise > 0.004;

            // THE GRAPHICS PRESET IS NOT A LABEL. Low turns off the shafts,
            // shortens the shadows, drops the reflections and thins the
            // bodies — if the frame comes back identical, none of that
            // reached the renderer and the slider is a lie told to somebody
            // whose machine is struggling.
            //
            // A twentieth of the frame is a deliberately low bar. It is
            // asking "did anything happen", not grading the saving.
            bool presetOk = _presetFraction > 0.05;

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
            // THE PAIR, NOT THE MEAN. `fraction` is how much of the frame the
            // pass reached and `drop` is how hard it hit there, and both
            // failures need a number to be visible: near-zero fraction means
            // it never ran, near-total means it is not occlusion at all but
            // an exposure change wearing its coat.
            //
            // The bounds are geometric rather than tuned. A street frame is
            // creases, contacts and doorways — comfortably over half a
            // percent of the image and nothing like half of it — and unlike
            // the old global-mean floor these do not need retuning every time
            // the amount of geometry in shot changes.
            bool aoOk = FilmGrade.Applied > 0
                        && _aoFraction > 0.005 && _aoFraction < 0.50
                        && _aoDrop > 0.004;

            // AND THAT THE GRADE RAN AT ALL, which is a different claim and
            // the one that actually mattered.
            //
            // The A/B above reported ao[applied=0 on=0.1827 off=0.1827] and
            // the cause was not ambient occlusion: `FilmGrade` was attached
            // to a CHILD of the camera, and `OnRenderImage` is only delivered
            // to a component on the GameObject that has the Camera. Grain,
            // vignette, bloom, exposure and the ACES tonemap had never
            // executed a single frame.
            //
            // Nothing caught it for months because every check was of the
            // MODEL — the curves are tested in Core, the shader compiled, the
            // material built, the component existed in the scene. The first
            // check that rendered one frame with an effect and one without
            // found it in a single run. This counter is the cheap version of
            // that lesson: an effect existing is not an effect running.
            bool postOk = FilmGrade.Frames > 0;

            // AND EACH EFFECT ON ITS OWN RULER. `postOk` proves the stack
            // runs; these prove each effect inside it reaches pixels, which
            // is a separate claim and the one that has already gone wrong.
            //
            // Every threshold here is a FLOOR ON BEING PRESENT, not a tuning
            // target. They say "this did something measurable", not "this did
            // the right amount" — nobody can judge the right amount from a
            // number, and a gate that pretends otherwise becomes an argument
            // with the art direction every time it is touched.
            // AND ONLY WHEN THERE IS SOMETHING TO BLOOM. A frame with no
            // highlights has nothing for the pass to spread, and failing the
            // gate for that is failing it for being pointed somewhere honest
            // — the trap the occlusion measurement was written to avoid.
            bool bloomMeasurable = _bloomHadHighlights > 0.01;
            bool bloomOk = !bloomMeasurable
                           || (_bloomFraction > 0.005 && _bloomRise > 0.004);
            // THE FLOOR IS DERIVED, not tuned until it went green.
            //
            // Grain is uniform noise of amplitude `a`, so its standard
            // deviation is a/sqrt(3) and it adds 2*sigma^2 to the mean
            // squared difference between neighbours. The shader asks for
            // roughly 0.02 by day rising to 0.065 at night and in rain; the
            // A/B runs at 21:00, so take the day figure and keep a wide
            // margin for the clamping at black that eats part of it.
            //
            // A threshold that follows from the amount the shader was asked
            // for can be defended the day it starts failing. A constant
            // nobody can derive gets lowered instead, which is how a gate
            // stops being one.
            const double GrainAmplitude = 0.020;
            double grainFloor = ImageStats.SpreadFromNoise(GrainAmplitude / Math.Sqrt(3.0)) * 0.25;
            bool grainOk = _grainDelta > grainFloor;
            // The ratio must FALL when the vignette is on: corners darker
            // relative to centre. Comparing absolute corner brightness would
            // be fooled by anything that changed the whole frame — including
            // the exposure change that shipped alongside this.
            bool vigOk = _vigOn >= 0 && _vigOff >= 0 && _vigOn < _vigOff * 0.95;


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

            // SUSPICION BECOMES BEHAVIOUR. `checks` is somebody comparing
            // notes about you with a neighbour; `confronts` is somebody
            // stepping into your path. Both read zero on every run this
            // project has ever produced, because nothing ever pushed a
            // tracker past the levels they need — so the two things the game
            // is most about were as unrun as the beats were.
            bool suspicionActs = _game.Gossip != null
                                 && _game.Gossip.ChecksRun > 0
                                 && _game.TotalConfrontations > 0;

            // AND THE HUSH, WHICH IS THE PART THAT IS ACTUALLY THIS GAME.
            // `Confabs > 0` says the street talks to itself. It says nothing
            // about the moment the whole system exists for: a pair breaking
            // off as he walks up, which tells him they were talking about
            // him, that they know he can see them, and that they would rather
            // he had not heard.
            //
            // Reported rather than gated, for now. The hush needs a rumour
            // ABOUT THE PLAYER to be live in a pair standing within four and
            // a half metres of a bot that is walking a fixed errand route,
            // and I do not yet know how often nine days produces that. A gate
            // I cannot predict the value of is a gate that fails for being
            // pointed somewhere honest — the mistake the ambient-occlusion
            // measurement was written to avoid. One run tells me; then it
            // gates.
            int hushBy = NpcWalker.HushWalkBys, hushed = NpcWalker.Hushes;

            // The duck has to have gone down AND come back. Either
            // extreme alone is a mix that is broken in a way nobody would
            // notice until they played it.
            bool mixOk = _mixDuckMax > 0.25 && _mixDuckMin < 0.05
                // AND THE DUCK REACHED THE ENGINE. Everything above is the
                // control signal — the number the mixer decided on. The music
                // bus's own volume has to have moved with it, or the mix is a
                // simulation of a mix.
                && _busMusicMax > 0 && _busMusicMax - _busMusicMin > 0.01;

            // THE SCORE IS AUDIBLE, not merely computed. `_stemsUnbound`
            // counts samples where a layer had no AudioSource at all, and the
            // ratio spread is how much the engine-to-model ratio varied
            // across every layer and every sample. One ratio for all of them
            // means Unity is playing the mix the tests describe, whatever bed
            // level the score is scaled to.
            bool scoreAudible = _stemVolumeMax > 0.001f && _stemsUnbound == 0
                                && StemRatioSpread > 0 && StemRatioSpread < 1.02;

            // DRESSING, and the measurement changed with the scope call.
            //
            // A floor on the TOTAL was right while every district got the
            // same detail. Concentrating it into two dense cores lowers the
            // total by design, so that floor would now fail for the feature
            // working — the classic way a gate outlives the thing it was
            // measuring and starts arguing with it.
            //
            // What concentration actually claims is that a wall in Hook
            // carries more than an identical wall at the edge of the map. So:
            // pieces PER FACADE on each side of the ramp, plus a much lower
            // floor on the total that still catches "nothing was placed".
            double perNear = WorldBuilder.FacadesNear > 0
                ? (double)WorldBuilder.DressedNear / WorldBuilder.FacadesNear : 0;
            double perFar = WorldBuilder.FacadesFar > 0
                ? (double)WorldBuilder.DressedFar / WorldBuilder.FacadesFar : 0;
            bool dressingOk = WorldBuilder.Dressed >= 90
                && WorldBuilder.FacadesNear > 0 && WorldBuilder.FacadesFar > 0
                && perNear > perFar * 1.25
                // ...and the far city is still dressed. Concentrating is not
                // stripping, and a bare street is worse than a sparse one.
                && perFar > 0.2;

            // THE CINEMATIC LAYER RAN. `Core/Framing` is push, hold,
            // authority, shot size and the 180-degree rule, and until tonight
            // none of it had ever executed in a verified build: the trigger
            // carried `SimMode.Days > 0` in its guard, so the sim — the only
            // thing that runs this game end to end — was the one context
            // where framing was off.
            //
            // Same shape as the beats gate it sits next to. A layer that
            // never runs is indistinguishable from one with nothing to frame,
            // and only a count can tell them apart.
            // AND IT REACHED THE CAMERA. `Begun > 0` on its own is a
            // presence check wearing a counter's clothes: a beat can start,
            // never be ticked, and satisfy it. `TightestFraming` is the
            // smallest fraction the camera was actually pulled to and sits at
            // exactly 1 if the push branch never executed, so the two
            // together say the layer ran AND did something.
            //
            // The bot is walking for most of the sim, so nearly every beat is
            // cancelled on its first tick and yields over 0.28s — the push
            // that survives that is a couple of percent, not the full 14. The
            // threshold is set to catch "never moved", not to grade the move.
            bool framingOk = FramedBeat.Begun > 0 && PlayerController.TightestFraming < 0.999f;

            // Every gate, by name, so a failure says WHICH one.
            //
            // Getting this out of CI used to mean reading a job log that the
            // API truncates and the two ASCII screenshots fill, or downloading
            // an artifact from a host the sandbox cannot reach. The one line
            // worth having was the one that never survived. Now it is printed
            // last, alone, and only when something is wrong.
            // NAME THE CLAUSE THAT FAILED. A composite boolean tells you a gate
            // is red and nothing else, and I have now spent three builds
            // inferring WHICH half from the fields around it. One string, listed
            // in the report, and the guessing stops.
            bool perceptionOk = Perceivers.Looks >= 1 && _loiterLooks >= 1
                                && _litRange > _darkRange
                                && Perceivers.SoundsEmitted >= 1
                                && _slamInvestigations >= 1
                                // The ring must have been drawn AND must have
                                // been drawn at the model's radius. A ring
                                // nobody drew and a ring drawn at the wrong size
                                // read identically from a distance.
                                //
                                // THIS COMMENT WAS TRUE OF THE INTENTION AND
                                // FALSE OF THE CODE for one whole build: only
                                // `_ringOk` was here, and it compares a radius
                                // against the model without asking whether
                                // anything was ever put on screen. It passed
                                // green with `ringsDrawn=0`. Both halves now.
                                && _ringOk == true && _slamDrewRing
                                && _ringSeenFraction >= RingSeenFloor
                                // AND THE SAME EVENTS IN WORDS. §6.2's
                                // redundancy claim is only true for a deaf
                                // player if the caption channel actually
                                // carries — and a channel that is built and
                                // silent reads identically to one that works
                                // until somebody plays with the sound off.
                                && _captionsShown >= 1;

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
                ("harm", harmOk), ("phones", phonesOk),
                ($"ui[labels={_labels} fontless={_labelsFontless} blank={_labelsBlank}]", uiOk),

                // WORLD TEXT SITS IN THE WORLD. Unity's built-in text shader
                // is ZTest Always, and the first screenshot this project ever
                // committed caught what that means: a walker's name lying
                // across the rooftops, and every street sign reading as
                // forward and backward glyphs superimposed because the
                // double-sided plate's far copy drew straight through the
                // board.
                //
                // Gated on the SHADER ACTUALLY BEING ON THEM rather than on
                // having called the helper. `Shader.Find` returns null in a
                // player for anything not in `Resources` — the noise ring
                // spent three CI runs proving that — and `WorldText.Adopt`
                // deliberately leaves the built-in material in place when the
                // lookup fails, because an invisible sign is worse than a
                // mirrored one. That fallback is safe and silent, which is
                // exactly the combination that needs a gate over it.
                ($"worldText[n={_worldText} depthTested={_worldTextDepth} "
                 + $"adopted={WorldText.Adopted} refused={WorldText.Refused} "
                 + $"shader={WorldText.ShaderPresent}]",
                 _worldText <= 0 || (WorldText.ShaderPresent && _worldTextDepth > 0
                                     && WorldText.Refused == 0)),
                ("budgets", budgetsOk),
                ("actTwo", act2Ok), ("actThree", actThreeOk), ("coverage", coverageOk),
                ($"lighting[{string.Join("|", lightingWhy)}]", lightingOk),
                // The streets must actually be dressed. A model that computes
                // beautiful placements nothing ever builds is the exact shape
                // of every other "verified in a test, absent in the game"
                // defect this project has found.
                ($"dressing[{WorldBuilder.Dressed} near={WorldBuilder.DressedNear}/"
                 + $"{WorldBuilder.FacadesNear} far={WorldBuilder.DressedFar}/"
                 + $"{WorldBuilder.FacadesFar}]", dressingOk),
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
                ($"post[frames={FilmGrade.Frames}]", postOk),
                ($"framing[begun={FramedBeat.Begun} tightest={PlayerController.TightestFraming:0.0000}]", framingOk),
                ($"bloom[hit={100 * _bloomFraction:0.00}% rise={_bloomRise:0.0000} " +
                 $"lit={100 * _bloomHadHighlights:0.0}%]", bloomOk),
                ($"grain[local+{_grainDelta:0.0000000} floor={grainFloor:0.0000000} " +
                 $"spread={_grainSpread:0.0000000}]", grainOk),
                ($"vignette[edge {_vigOn:0.000} vs {_vigOff:0.000}]", vigOk),
                ($"ao[applied={FilmGrade.Applied} on={_aoOn:0.0000} " +
                 $"off={_aoOff:0.0000} delta={aoDelta:0.0000} " +
                 $"hit={100 * _aoFraction:0.00}% drop={_aoDrop:0.0000}]", aoOk),
                ($"confab[{(_game.Gossip != null ? _game.Gossip.Confabs : -1)}]", confabOk),
                // §4.7 CLAIM 1 AND CLAIM 4, GATED AT LAST.
                //
                // `deedSlotSets` has been reported and not asserted since it
                // was written, deliberately: a threshold set without a
                // measured value is how this project keeps hurting itself.
                // The claim is not a number anyway, it is "more than one" —
                // one means every witness in the city resolved identically,
                // which says something upstream handed them the same geometry.
                //
                // The delivery half is stronger than a count: somebody started
                // walking, and somebody was stopped before arriving. A window
                // nobody walks is a list.
                ($"deedClaims[slotSets={_deedSlotSets} dispatched={_deedDispatched} " +
                 $"intercepted={Witnesses.Interceptions} arrived={Witnesses.Arrived}]",
                 _deedsStaged == 0
                     || (_deedSlotSets > 1 && _deedDispatched > 0
                         && Witnesses.Interceptions > 0)),
                ($"suspicionActs[checks={(_game.Gossip != null ? _game.Gossip.ChecksRun : 0)} " +
                 $"confronts={_game.TotalConfrontations} staged={_confrontTarget ?? "none"} " +
                 $"stagesOnDay={ConfrontStagesOnDay} lastDay={_lastSeenDay}" +
                 (_confrontUnreached && _confrontTarget == null
                      ? " NEVER-REACHED-THE-STAGING-DAY" : "") + "]",
                 suspicionActs),
                ($"frame[mean={meanFrameMs:0.0}ms gameBudget={GameFrameBudgetMs:0}ms "
                 + $"{frameWhere}]", frameOk),

                // §4.7's HEADLINE CLAIM, AND IT IS GATED ON THE ORDER RATHER
                // THAN ON A NUMBER.
                //
                // "The same killing leaves no witness in an empty alley,
                // several in a market, and none in the back room of a busy
                // pub." What "several" means is not knowable until a run has
                // said so, and inventing a figure for it is how `nightNotDarker`
                // came to fail on a thousandth. The claim itself is ordinal —
                // fewest where nobody is, most where everybody is, none behind
                // a wall — so that is what this asserts, and the three raw
                // counts are printed beside it so an absolute gate can be set
                // from evidence on a later run.
                //
                // The enclosed case is skipped when the world contains no
                // place where people are near and every one of them is
                // blocked. That is a finding about the world, and `placesWhy`
                // says so rather than the gate quietly passing.
                //
                // ON `Any`, AND I MOVED IT OFF `Any` FOR A BAD REASON.
                //
                // One run reported alley=53 market=53 and I called the count
                // saturated by hearing, then re-gated on `Eyes`. That was a
                // conclusion from a single sample — the exact mistake the
                // threshold rule exists to prevent — and I made it while
                // fixing a different single-sample mistake. In that run the
                // alley pick simply happened to stand in the open.
                //
                // The first run that printed all four columns settles it:
                //
                //     alley    any  3/54   (open 0)
                //     market   any 53/54   (open 40)
                //     enclosed any  3/54   (blocked 41)
                //
                // That IS the claim — fewest where nobody is, most where
                // everybody is, fewest again behind a wall — and it falls out
                // of occlusion attenuating the sound, which is the mechanism
                // the design wanted.
                //
                // `Eyes` was 0 in all three, and that is not a fact about the
                // places. `Witnesses.Resolve` sets `SecondsWatching` to 3.0
                // only for a walker already in `Watches` stance and 0 for
                // everybody else, and `Observe.Resolve` gates BOTH `seesActor`
                // and `seesVictim` behind `NoticeSeconds`. So nobody can
                // visually witness anything unless they were already staring —
                // forty people in clear line of sight in a market produced
                // zero sightings. That is a real finding about the perception
                // model rather than about this gate, it is printed every run,
                // and gating on it would be gating on a constant.
                ($"places[alley={_placesAlley} market={_placesMarket} "
                 + $"enclosed={_placesEnclosed} why={_placesWhy}]",
                 _placesStaged
                 && _placesMarket.Noticed > _placesAlley.Noticed
                 && (_placesEnclosed.Noticed < 0
                     || _placesMarket.Noticed > _placesEnclosed.Noticed)),

                // THE REST OF PHASE 3, and every clause is a rule that had no
                // caller before tonight rather than a number somebody picked.
                //
                //   the coat is a decision   three objects, two fit
                //   refusing has a price     and it differs by who asked
                //   a frisk is never random  nobody with no grounds searches you
                //   blood needs a place      the same wash fails in the street
                //                            and works at home
                ($"carry[took={_carryTook}/3 choice={_carryIsAChoice} all={_carryCanTakeAll} "
                 + $"refuse={_friskRefusalCost} found={_friskFound:0.00} cost={_friskCost:0.00} "
                 + $"groundless={_friskGroundlessHappened} frisks={CoatHost.Frisks} "
                 + $"refused={CoatHost.FrisksRefused}]",
                 _carryStaged && _friskStaged
                 && _carryTook > 0 && !_carryCanTakeAll && _carryIsAChoice
                 && _friskRefusalCost == Coat.Refusal.NotGoingIn
                 && _friskFound > 0 && _friskCost > 0
                 && !_friskGroundlessHappened
                 && CoatHost.Frisks == 1 && CoatHost.FrisksRefused == 1),

                ($"blood[taken={ViolenceHost.StainsTaken} noticed={ViolenceHost.StainsNoticed} "
                 + $"washed={ViolenceHost.StainsWashed} publicFailed={_washFailedInPublic} "
                 + $"atHome={_washWorkedAtHome} worstCost={ViolenceHost.WorstStainCost:0.00}]",
                 ViolenceHost.StainsTaken > 0
                 && (!_washTried || (_washFailedInPublic && _washWorkedAtHome))),

                // M17.9 — REPORTED, NOT GATED, and the distinction is the
                // point. The font cannot land until a CI fetch brings one
                // (`fonts.google.com` answers 000 from the dev container), so
                // gating on it would paint the build red for work that has not
                // started, and a check that is red for a known reason is a
                // check people learn to skip. What it must never do is go
                // QUIET: a silent OS fallback is exactly how the project ended
                // up not knowing it had no font of its own.
                ($"font[shipped={UiTheme.UsingShippedFont} face={UiTheme.ShippedFont}]", true),

                ($"threat[brandishes={ViolenceHost.Brandishes} last={ViolenceHost.LastThreat} "
                 + $"fled={ViolenceHost.ThreatsThatFled} called={ViolenceHost.ThreatsCalled} "
                 + $"complied={ViolenceHost.ThreatsComplied} undraw={ViolenceHost.CanUndraw()} "
                 + $"drawn={HeldObject.Drawn} object={HeldObject.LastDrawn ?? "none"}]",
                 ViolenceHost.Brandishes > 0 && !ViolenceHost.CanUndraw()
                 // AND SOMETHING WAS ACTUALLY PUT IN THE HAND. M17.8: the
                 // threat is the most legible act in a game about being seen,
                 // and until tonight the object being threatened with had no
                 // mesh anywhere in the project.
                 && HeldObject.Drawn > 0),

                // PHASE 4's DONE-CONDITION, stated as the spec states it.
                //
                // *A weapon acquired by each of the four routes carries a
                // different traceability, and disposal seen by a witness
                // produces a different residual risk from disposal unseen.*
                //
                // Every clause is a relationship rather than a number: the four
                // routes must be four distinct values in the design's order,
                // seen must cost more than unseen, and a kitchen knife bought
                // from a named seller must still come out Ordinary — the one
                // place the object and the transaction disagree.
                ($"provenance[bought={_provBought:0.00} stolen={_provStolen:0.00} "
                 + $"taken={_provTaken:0.00} inherited={_provInherited:0.00} "
                 + $"ordinary={_provOrdinary:0.00} stayedOrdinary={_provOrdinaryStayedOrdinary} "
                 + $"usedLogged={_provUsedShowsInHistory}]",
                 _provenanceStaged
                 && _provBought > _provStolen && _provStolen > _provInherited
                 && _provInherited > _provTaken && _provTaken > _provOrdinary
                 && _provOrdinaryStayedOrdinary && _provUsedShowsInHistory),

                ($"disposal[seen={_provDisposalSeen} risk={_provRiskSeen:0.00} "
                 + $"unseen={_provDisposalUnseen} risk={_provRiskUnseen:0.00} "
                 + $"disposals={EvidenceHost.Disposed} watched={EvidenceHost.DisposalsSeen} "
                 + $"thread={_provThread}@{_provThreadRisk:0.00} ellisAsking={_provEllisAsking} "
                 + $"quietSpotWatchers={_emptyWatchers}]",
                 _provenanceStaged && EvidenceHost.Disposed >= 2
                 && !_provDisposalUnseen && _provRiskSeen > _provRiskUnseen),

                // AND THE ACCIDENT, which is only an accident when nobody is
                // there. Same spot, same weapon, and the only thing that
                // differs is who can see it — so this is one claim, not two.
                // PHASE 2's REMAINDER. The ghost only where the awareness was
                // mutual — reported rather than gated, because a run whose bot
                // never happens to lock eyes with anybody is a legitimate run
                // and gating on it would make the gate a dice roll. What IS
                // gated is that when a ghost appeared, the awareness that
                // earned it was one `GhostAllowed` permits, which is the rule
                // rather than the frequency.
                ($"ghost[shown={Standoff.Ghosts} awareness={Standoff.GhostAwareness} "
                 + $"standoffs={Standoff.Beats}]",
                 Standoff.Ghosts == 0
                 || Observe.GhostAllowed(Standoff.GhostAwareness)),

                // AND WAITING IS NOT FREE. A witness left alone retells, and
                // certainty climbs while accuracy does not — so a hesitant
                // description hardens into a name nobody ever verified.
                ($"retelling[rounds={Witnesses.Retellings} hardened={Witnesses.HardenedToAName} "
                 + $"naming={Witnesses.NamingWitnesses()} assembles={_assemblingPairs}]",
                 Witnesses.Retellings > 0),

                ($"accident[inCompany={_accidentInCompany} alone={_accidentAlone} "
                 + $"quietSpotWatchers={_emptyWatchers}]",
                 _provenanceStaged && !_accidentInCompany && _accidentAlone),

                ($"killings[acts={ViolenceHost.Acts} killings={ViolenceHost.Killings} "
                 + $"confidence={ViolenceHost.PeakKillingConfidence:0.00} "
                 + $"fleeing={ViolenceHost.FleeingVictims}]",
                 ViolenceHost.Killings > 0 && ViolenceHost.PeakKillingConfidence > 0),
                ($"mix[duck={_mixDuckMin:0.00}..{_mixDuckMax:0.00} " +
                 $"bus={_busMusicMin:0.000}..{_busMusicMax:0.000}]", mixOk),
                ($"preset[low vs high changes {100 * _presetFraction:0.0}% of the frame]", presetOk),
                ($"scoreAudible[peak={_stemVolumeMax:0.000} unbound={_stemsUnbound} " +
                 $"ratio={_stemRatioMin:0.000}..{_stemRatioMax:0.000}]", scoreAudible),
                // PHASE 1 IS NOT DONE UNTIL THE CITY REACTS. Three claims,
                // each of which a city that computes perfectly and reacts to
                // nothing would fail: somebody actually turned their head at
                // the player during the run, the staged loiter drew at least
                // one of them, and a lit spot is detectable further than a
                // dark one MEASURED IN THE SCENE rather than in a unit test.
                ($"perception[looks={Perceivers.Looks} remarks={Perceivers.Remarks} " +
                 $"loiterLooks={_loiterLooks} loiterNotices={Perceivers.LoiterNotices} " +
                 $"nightRunLooks={_nightRunLooks} nightRunNotices={Perceivers.NightRunNotices} " +
                 $"sounds={Perceivers.SoundsEmitted} investigations={Perceivers.NoiseInvestigations} " +
                 $"slamInvestigations={_slamInvestigations} " +
                 $"standoffs={Standoff.Beats} awareness={Standoff.LastAwareness} " +
                 $"ringsSized={NoiseRing.Sized} ringsDrawn={NoiseRing.Shown} " +
                 $"ringSmall={NoiseRing.SkippedSmall} ringShadowed={NoiseRing.SkippedShadowed} " +
                 $"ringNoMaterial={NoiseRing.SkippedNoMaterial} ringMax={NoiseRing.MaxRadius:0.0} " +
                 $"slamDrewRing={_slamDrewRing} slams={_slams} " +
                 $"ringSeen={100 * _ringSeenFraction:0.0000}% rise={_ringSeenRise:0.0000} " +
                 $"ringPaint[ledger={100 * _ringSeenLedger:0.0000} " +
                 $"sprites={100 * _ringSeenSprites:0.0000} " +
                 $"particles={100 * _ringSeenParticles:0.0000} " +
                 $"none={100 * _ringSeenNone:0.0000} " +
                 $"transformZ={100 * _ringSeenTransformZ:0.0000} " +
                 $"control={100 * _controlSeen:0.0000}] paint={NoiseRing.PaintUsed} " +
                 $"ringOk={_ringOk} why={PerceptionWhy()} " +
                 $"hushPeak={_hushPeak:0.00} lit={_litRange:0.0}m dark={_darkRange:0.0}m]",
                 perceptionOk),
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
                      $"confrontTarget={_confrontTarget ?? "none"} suspicionActs={suspicionActs} " +
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
                      // ALWAYS PRINTED, not only on failure. The gate's own
                      // string only reaches the log when the gate is red, so a
                      // green run told me nothing about how many heads turned —
                      // and "it passed" is not a measurement.
                      $"looks={Perceivers.Looks} remarks={Perceivers.Remarks} " +
                      $"loiterLooks={_loiterLooks} loiterNotices={Perceivers.LoiterNotices} " +
                      $"nightRunLooks={_nightRunLooks} nightRunNotices={Perceivers.NightRunNotices} " +
                      $"sounds={Perceivers.SoundsEmitted} investigations={Perceivers.NoiseInvestigations} " +
                      $"slamInvestigations={_slamInvestigations} standoffs={Standoff.Beats} " +
                      $"hushPeak={_hushPeak:0.00} litRange={_litRange:0.0} darkRange={_darkRange:0.0} " +
                      $"lumaPairs=[{_lumaSeries}] " +
                      // ITEMISED for the same reason the ring is: "captions=0"
                      // has more than one cause, and the hush is the one that
                      // dies quietly because it is polled rather than pushed.
                      $"captions={_captionsShown} captionHushes={_captionHushes} " +
                      // PHASE 2. `deedSlotSets` is the §4.7 claim that only a
                      // running street can answer: one event, witnesses at
                      // different positions, DIFFERENT slot sets. One means
                      // everybody resolved identically, which would say
                      // something upstream is handing them the same geometry.
                      $"deeds={_deedsStaged} deedWitnesses={_deedWitnesses} " +
                      $"deedSlotSets={_deedSlotSets} deedBestRung={_deedBestRung} " +
                      // THE DELIVERY WINDOW, §4.5, measured rather than assumed
                      // to run. Dispatched is how many started walking;
                      // arrived is how many made it and went indelible;
                      // intercepted is claim 4 actually exercised.
                      $"deedDispatched={_deedDispatched} " +
                      $"deedArrived={Witnesses.Arrived} " +
                      $"deedIntercepted={Witnesses.Interceptions} " +
                      $"deedInFlight={Witnesses.InFlight.Count} " +
                      $"deedMisnamed={_deedMisnamed} " +
                      $"ringsSized={NoiseRing.Sized} ringsDrawn={NoiseRing.Shown} " +
                      // ITEMISED, because `drawn=0` had three possible causes
                      // and I picked the wrong one out loud. `small` is the
                      // model working, `shadowed` is the presentation rule, and
                      // `noMaterial` is the only one that means the build is
                      // broken. `ringMax` says whether anything loud enough to
                      // draw ever happened at all.
                      $"ringSmall={NoiseRing.SkippedSmall} ringShadowed={NoiseRing.SkippedShadowed} " +
                      $"ringNoMaterial={NoiseRing.SkippedNoMaterial} " +
                      $"ringMax={NoiseRing.MaxRadius:0.0} ringLastSkip={NoiseRing.LastSkip} " +
                      $"ringRadius={NoiseRing.LastRadius:0.0} ringOk={_ringOk} " +
                      $"slamDrewRing={_slamDrewRing} " +
                      $"ringSeen={100 * _ringSeenFraction:0.0000} ringRise={_ringSeenRise:0.0000} " +
                      $"ringLedger={100 * _ringSeenLedger:0.0000} " +
                      $"ringSprites={100 * _ringSeenSprites:0.0000} " +
                      $"ringParticles={100 * _ringSeenParticles:0.0000} " +
                      $"ringNone={100 * _ringSeenNone:0.0000} " +
                      $"ringTransformZ={100 * _ringSeenTransformZ:0.0000} " +
                      $"ringControl={100 * _controlSeen:0.0000} " +
                      $"ringPaintUsed={NoiseRing.PaintUsed} " +
                      $"aoRounds={_aoRounds} aoRan={_tookAoPair} " +
                      $"perceptionWhy={PerceptionWhy()} " +
                      $"perceptionOk={perceptionOk} " +
                      // PRINTED BECAUSE I GUESSED TWICE. Whether the probes
                      // fired depends on which days and hours the run actually
                      // reached, and neither was in the report — so two builds
                      // were spent inferring it from a -1.
                      $"lastDay={_lastSeenDay} endDayReached={_endDay} " +
                      $"loiterStaged={_loiterStaged} slams={_slams} " +
                      $"nightRunStaged={_nightRunStaged} " +
                      $"lines={_game.Phones.All.Count} answered={_callsAnswered} " +
                      $"wrongPerson={_callsWrongPerson} rangOut={_callsRangOut} phonesOk={phonesOk} " +
                      $"panelsOk={panelsOk} panelsBad={panelsBad} uiOk={uiOk} " +
                      $"labels={_labels} fontless={_labelsFontless} blankLabels={_labelsBlank} " +
                      $"worldText={_worldText} depthTested={_worldTextDepth} " +
                      $"{(badPanels.Count > 0 ? "broken=[" + string.Join(",", badPanels) + "] " : "")}" +
                      $"{Perf.Summary()} trafficMs={(trafficCost != null ? trafficCost.MeanMs : 0):0.000} perfOk={perfOk} " +
                      // mean/median/peak bodies within 20m and within 8m,
                      // sampled every in-game hour across the whole run.
                      $"seen20={Dist(_within20)} seen8={Dist(_within8)} " +
                      $"near={(_game.Populace != null ? _game.Populace.CountIn(Lod.Near) : 0)} " +
                      $"mid={(_game.Populace != null ? _game.Populace.CountIn(Lod.Mid) : 0)} crowdOk={crowdOk} " +
                      $"beats=[{string.Join(",", beatStates)}] attended={beatsAttended} skipped={beatsSkipped} " +
                      $"shafts={LightShaft.Count} wet={SceneLighting.Wetness:0.00} " +
                      $"dressed={WorldBuilder.Dressed} perNear={perNear:0.00} perFar={perFar:0.00} " +
                      $"reflWet={_reflWetFrames} reflDry={_reflDryFrames} " +
                      $"reflRefresh={ReflRefreshes} reflMax={_reflMaxStrength:0.00} reflOk={reflOk} " +
                      $"postFrames={FilmGrade.Frames} postOk={postOk} " +
                      $"framedBeats={FramedBeat.Begun} framingPush={PlayerController.TightestFraming:0.0000} framingOk={framingOk} " +
                      $"beatTried={_beatBotTried ?? "none"} beatClosest={_beatClosestApproach:0.0}m " +
                      $"beatChaseSecs={_beatChaseSeconds:0} beatMarker={_beatMarkerSeen} " +
                      $"nightFull={_nightFull:0.0000} nightNoShafts={_nightNoShafts:0.0000} " +
                      $"nightNoBloom={_nightNoBloom:0.0000} nightUngraded={_nightRaw:0.0000} " +
                      $"bloomD={_bloomDelta:0.0000} bloomHit={100 * _bloomFraction:0.00} " +
                      $"bloomRise={_bloomRise:0.0000} bloomLit={100 * _bloomHadHighlights:0.0} " +
                      $"grainD={_grainDelta:0.00000} vig={_vigOn:0.000}/{_vigOff:0.000} " +
                      $"aoApplied={FilmGrade.Applied} aoDelta={aoDelta:0.0000} aoOk={aoOk} " +
                      $"aoHit={100 * _aoFraction:0.00} aoDrop={_aoDrop:0.0000} " +
                      $"reflHit={100 * _reflFraction:0.00} reflRise={_reflRise:0.0000} " +
                      $"reflSeen={reflSeen} reflWetAtAb={SceneLighting.Wetness:0.00} " +
                      $"specHit={100 * _specFraction:0.00} specRise={_specRise:0.0000} " +
                      $"presetHit={100 * _presetFraction:0.00} presetOk={presetOk} " +
                      $"aoSpread={_aoSpread:0.00000} grainSpread={_grainSpread:0.00000} " +
                      $"aoRange={_aoDeltaMin:0.00000}..{_aoDeltaMax:0.00000} " +
                      $"grainRange={_grainDeltaMin:0.00000}..{_grainDeltaMax:0.00000} " +
                      $"confabs={(_game.Gossip != null ? _game.Gossip.Confabs : -1)} confabOk={confabOk} " +
                      $"hushWalkBys={hushBy} hushes={hushed} " +
                      $"duck={_mixDuckMin:0.00}..{_mixDuckMax:0.00} mixOk={mixOk} " +
                      $"stemVolMax={_stemVolumeMax:0.000} stemsUnbound={_stemsUnbound} " +
                      $"stemRatio={_stemRatioMin:0.000}..{_stemRatioMax:0.000} " +
                      $"scoreAudible={scoreAudible} " +
                      $"busMusic={_busMusicMin:0.000}..{_busMusicMax:0.000} " +
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
