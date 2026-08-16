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
        int _streetStills;
        /// Noon and night of one rest day, on top of the four. Two,
        /// because a Saturday needs the same pair of lighting
        /// conditions as a Tuesday to be comparable with one.
        const int MaxRestStills = 2;
        int _restStills;

        /// LAYER 3, and the thing it is actually for.
        ///
        /// Twenty frames are fingerprinted every run — mean and peak luminance,
        /// the bright fraction and its colour, the saturated fraction and its
        /// strength — and until now every one of those numbers went to
        /// `player.log` and the sim-out JSON, which are the two channels this
        /// environment cannot read. Twenty measurements taken, none reported.
        /// That is rule 12 exactly, and it is why four correct things were
        /// condemned off a 1280x720 JPEG: the picture was the only evidence
        /// available, and a picture is good evidence that something is wrong
        /// and poor evidence of what.
        ///
        /// One row per shot, committed to `game-design/sim-shots/frames.tsv`,
        /// which makes the NEXT run able to answer the question none of those
        /// four arguments could: not "does this look off" but "what moved".
        int _frameRows;
        readonly StringBuilder _frameLedger = new StringBuilder();
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

        /// THE NIGHT THE OUTFIT STOPPED CALLING, and the nights it never called
        /// after. Zero when it never happened.
        ///
        /// WHY THIS IS HERE AND NOT A BALANCE QUESTION. `verdictSane` requires
        /// that "while the campaign is live, most nights must actually post a
        /// job" — and `GameController` reads
        /// `InJobWindow(Now) && !Campaign.OutfitCutOff`, so once patience runs
        /// out the outfit posts NOTHING. That is the design working: three
        /// missed drops and they drop you. The clause was asking for job-nights
        /// the game had deliberately stopped providing.
        ///
        /// It is the same repair as `_frozenCloses`, whose comment already says
        /// it in as many words — *"the gates baseline on ACHIEVABLE counts, not
        /// ideal ones"* — for closes eaten by the frozen end screen. Second site
        /// of one idea, and the second site is the one nobody looked at.
        ///
        /// IT HAD BEEN PASSING FOR THE WRONG REASON. Across 64 kept runs the
        /// outfit cuts the player off on SEVEN, and on six of those the bot had
        /// scraped one drop in first, so `jobsDone=1` and the clause cleared its
        /// bound anyway. Only the seventh — a miss before any completion — made
        /// it visible. A gate that survives on luck is not a gate that works.
        int _cutOffDay;
        int _cutOffNights;
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
            // AND TWO MORE OF EXACTLY THE SAME SHAPE, found by pointing
            // `lint-unreached` at the Game layer rather than by noticing.
            //
            // `Audio.ResetSpeechCounters` clears the five speech counters and
            // the two distinct-asked sets — every one of which this file prints
            // on the done line. `Witnesses.ResetDeliveries` clears the
            // in-flight walk list and the delivery totals. Both existed, both
            // were written to be called here, and neither had a caller, which
            // is the sentence three lines above about two other methods.
            //
            // NOT A BUG BEING FIXED TODAY, and saying otherwise would be the
            // over-claim this file is full of warnings about: CI runs one sim
            // per process, so the statics start at zero anyway. It becomes one
            // the moment anything runs a second sim in a session or reloads
            // into one — and `RecordKilling` calls `SaveNow`, so a restore path
            // through this scene is not hypothetical. A reset that clears some
            // of a class's counters is worse than no reset at all, because the
            // ones it forgets look deliberate.
            Audio.ResetSpeechCounters();
            Witnesses.ResetDeliveries();
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
            SummonsHost.Reset();
            PressHost.Reset();
            ReliabilityHost.Reset();
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

        /// DOES A REST DAY LOOK DIFFERENT IN THE ENGINE, not just in a test.
        ///
        /// I said three times today — in a commit, in a doc and in the work
        /// order — that the rest days had never run because "the sim renders
        /// campaign days 1 and 2". Wrong. The STILLS are captured on days 1 and
        /// 2; the sim runs ELEVEN in-game days, so days 5 and 6 execute every
        /// build and always have. I read the screenshot filenames as if they
        /// were the run length.
        ///
        /// So the gap is narrower and real: the code runs, and nothing has ever
        /// LOOKED at it. Rule 6 is that a feature is done when something calls
        /// it and a gate proves the call happened — and CoreTests proving the
        /// curve differs is not the same as this city being different on a
        /// Saturday.
        ///
        /// Sampled at noon, which is where the two curves are furthest apart
        /// by construction: a working day is 0.18 outdoors at that hour and a
        /// rest day 0.22. Worst-case honest: if these come back equal, either
        /// the day is not reaching the population host or the difference is
        /// too small to see in a crowd this size, and both are worth knowing.
        void SampleDayShape()
        {
            // `PopulationHost.cs` is a PARTIAL GameController, not a separate
            // component — so the crowd count is on `_game` and there is no host
            // to find. Worth the line: I went looking for a type that does not
            // exist as a type.
            if (_game == null || _game.Now.Hour != 12) return;
            int day = _game.Now.Day;
            if (day == _lastShapeDay) return;
            _lastShapeDay = day;
            int outdoors = _game.CrowdWalkerCount;
            if (Ledger.Core.Population.IsRestDay(day))
            {
                _restDayNoonCrowd += outdoors;
                _restDaysSeen++;
            }
            else
            {
                _workDayNoonCrowd += outdoors;
                _workDaysSeen++;
            }
        }

        int _lastShapeDay = -1;
        int _restDayNoonCrowd, _workDayNoonCrowd, _restDaysSeen, _workDaysSeen;

        void Update()
        {
            SampleDayShape();
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
                // AFTER the walk, because the walk is what BUILDS the panels
                // that have never been opened — measuring first would read
                // contrast off three panels instead of six.
                _game.Ui.MeasureContrast();
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
                    // ASK FIRST WHETHER THEY COULD BE REACHED AT ALL, which
                    // is the question `Phones.ReachableNow` was written for and
                    // which nothing has ever put to it.
                    //
                    // Its own comment says it is "the answer the player most
                    // wants and the one they are never simply told — what makes
                    // an evening where somebody cannot be found feel like the
                    // city rather than like a locked door". That has been true
                    // and unwired since it was written.
                    //
                    // It changes what `rangOut` MEANS. Eleven calls ringing out
                    // reads as a failure; eleven calls to people who were not
                    // reachable at that hour reads as the schedule working. The
                    // two are the same number today and they are opposite
                    // findings, which is this project's most repeated fault in
                    // its smallest form.
                    _callsAttempted++;
                    // WITH THE SAME PREDICATE `RingLine` USES, and passing
                    // null was measuring something else entirely.
                    //
                    // `ReachableNow` treats a null `whoIsNear` as "do not
                    // check", so it returned true whenever a LINE was live at
                    // that hour — regardless of whether the person was
                    // anywhere near it. That is why the first reading was
                    // callsTried=22 callsReachable=22 with rangOut=12: not a
                    // contradiction between reachability and answering, just a
                    // number answering a weaker question than its name.
                    //
                    // `NearPhone` is what `RingLine` itself passes, so the
                    // probe and the thing it is measuring now ask the same
                    // question — the mistake rule 2 warns about when a gate
                    // measures its own opinion instead of the system's.
                    if (_game.Phones.ReachableNow(who, now, _game.NearPhone)) _callsReachable++;
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
                _harmTreated = _game.Harm.Inflict("Rocco", "Rocco", InjuryKind.Cut, now.Day,
                    "the same rail, the same night");
                _game.Harm.Treat(_harmTreated, null, now.Day);   // no wallet: the sim is proving the mechanism
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
                        _game.Empire.RecruitByNeed(sam, "Sam", 120, _game.Wallet, now, _game.Gossip?.Mill);
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
                    _game.Empire.RecruitByNeed(rocco, "Rocco", 100, _game.Wallet, now, _game.Gossip?.Mill);
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
                && _game.ActThree.Pp1Fired && now.Hour >= 14
                && now.Day > _handedTriedDay)
            {
                // Once per afternoon, not once per tick — the retry loop
                // this block became would otherwise ask hundreds of times
                // a day and count each one.
                _handedTriedDay = now.Day;
                var ready = _game.ReadySuccessor();
                // THE AUDIT STAYS OPEN UNTIL SOMEBODY QUALIFIES. The first
                // version closed it on this same pass — one attempt, one
                // chance, "the letter's date" — and the measured result was
                // a succession that has never completed in any recorded run:
                // `handedTried=True handedReady=[nobody]`, with Joey passing
                // `CouldHold` by the END of the run but not at the one hour
                // anybody asked, so `Ending.Quiet` was structurally
                // unreachable — the `inquiry=None` class of dead branch,
                // found by reading rather than by the constant-key tool.
                // Now each afternoon re-asks until someone is ready, and the
                // hard close at day 15 keeps every run ending SOME way:
                // nobody by then is the NoSuccessor ending honestly earned.
                //
                // The try fields are LAST-Wins across retries — says so
                // here, so nobody reads the retry count out of them — and
                // `handedRetries` carries how many afternoons asked.
                _handedTried = true;
                _handedRetries++;
                _handedReady = ready != null ? ready.Id : "nobody";
                _handedWhyAtTry = GameController.SuccessorWhy;
                if (ready != null && _game.ActThree.SuccessorId == null)
                    _actThreeHandedOver = _game.HandOver(ready.Id);
                if (ready != null || now.Day >= 15)
                    _game.ActThree.AuditClosesDay = now.Day;
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
            // THE HEAT'S DECAY, SAMPLED DAILY — 963248f's series held ONE
            // day because the first sampler lived inside the homicide
            // AUDIT, which runs once. This site runs every pass; the
            // day-latch keeps it to one token per day from the first
            // filed body onward, which is the whole span the fade crosses.
            if (_game != null && _game.Homicides != null
                && _game.Homicides.BodyCount > 0 && now.Day > _homWhyDay)
            {
                _homWhyDay = now.Day;
                _homWhySeries.Add("d" + now.Day + ":"
                    + _game.Homicides.PressureWhy(_game.Gossip?.Mill,
                                                  _game.IsAlive, now.Day));
                // AND WHETHER ELLIS IS ASKING, latched daily — the
                // provenance probe asks this ONCE, days before any body
                // can file, which is why ellisAsking has read False in
                // all 150 recorded runs: a moment probe on a condition
                // that starts later. This one answers "was she ever" and
                // says so in its name.
                _ellisEverAsked |= EvidenceHost.EllisIsAskingAboutYou(
                    _game.Homicides,
                    _game.Gossip != null ? _game.Gossip.Mill : null,
                    now.Day);
            }

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
            TraceJob(now);
            // PLANT THE MISSED DROPS, because nothing else ever has.
            //
            // `gates.py --constant` across a hundred and thirty-one kept runs
            // says `reliabilityFiled=0` and `reliabilityHeard=0` — every run
            // this project has ever kept. `Core/Reliability` turns missed drops
            // into talk at two misses and a reputation at four, it is tested,
            // it is wired through `ReliabilityHost`, and its condition has
            // never once been met: `reliabilityRead=[Fine after 1]`, because
            // the bot has never missed two drops without a delivery between.
            //
            // That is rule 5b's corollary — a probe needs a run in which the
            // thing it asserts CAN happen — and the fix it names is to PLANT
            // the condition, never to loosen the bound. Lowering
            // `TalkedAboutAt` to one would make the street comment on every
            // single lapse, which the constant's own comment argues against by
            // name.
            //
            // AFTER DAY TEN, AND ONLY TWO. The early windows are what
            // `jobRan` (`JobsDone >= 1`) and `takingsBanked` (`> 0`) live on,
            // and a stage that starved those would be a probe breaking the
            // gates it shares a run with — this project's most expensive shape
            // of guard. Three drops typically complete before day ten, so both
            // bounds are already met when this starts, and the windows after it
            // are left alone so the DELIVERY-CLEARS-IT path runs too.
            var jobPos = _game.ActiveJobPos;
            // STOP ON THE OUTCOME, NOT ON A COUNT — because two skips are not
            // two CONSECUTIVE skips, and only consecutive ones count.
            //
            // `MissedSinceLastDelivery` walks back from today and BREAKS at the
            // first completed night. So a skip on day 10 and a skip on day 12
            // with a delivery on day 11 returns 1, for ever, and the rule at
            // two never fires. Nothing here required the two days to be
            // adjacent, and whether they were depended on which days happened
            // to carry an active drop.
            //
            // That is why the series reads 0,1,1,2,1,1,1 and then 0 — measured,
            // not guessed: `reliabilityRead` says `[Slipping after 2]` for five
            // runs and `[Fine after 0]` for the newest, so the newest run
            // genuinely had nothing to file and the plant simply did not land
            // two in a row. A probe that fires on a lucky run is not a probe.
            //
            // Keep skipping until the rule ACTUALLY FIRES, then stop at once so
            // the delivery-clears-it path still runs afterwards. `SkipDropsMax`
            // is a backstop against a run where it can never fire, not a target
            // — and `dropsSkipped` beside `reliabilityFiled` says which
            // happened.
            bool stillNeeded = ReliabilityHost.Filed == 0 && _dropsSkipped < SkipDropsMax;
            if (jobPos.HasValue && now.Day >= SkipDropsFromDay && stillNeeded)
            {
                if (_skippingDropDay != now.Day)
                {
                    _skippingDropDay = now.Day;
                    _dropsSkipped++;
                    Debug.Log($"SimDirector: staging a missed drop on day {now.Day} "
                              + $"({_dropsSkipped}, up to {SkipDropsMax}) — nothing has ever "
                              + "let the reliability rule fire.");
                }
                jobPos = null;
            }
            var job = jobPos ?? _game.DayJobTargetPos; // night drops outrank; mornings go to parcels
            var target = beatSpot.HasValue
                ? new Vector3(beatSpot.Value.x, 0, beatSpot.Value.z)
                : job.HasValue ? new Vector3(job.Value.x, 0, job.Value.z) : Waypoints[_waypointIndex];
            // WHO IS DRIVING THE PLAYER THIS TICK. Set here at the first
            // assignment and overwritten by every later one, so the value at
            // the end of the tick is whoever actually won.
            _targetOwner = beatSpot.HasValue ? "beat"
                         : job.HasValue ? "job" : "waypoint";
            _player.AutoMoveTarget = target;
            if (!job.HasValue &&
                Vector3.Distance(new Vector3(_player.transform.position.x, 0, _player.transform.position.z), target) < 1.2f)
                _waypointIndex = (_waypointIndex + 1) % Waypoints.Length;

            StageConfrontation(now);
            StageThePlaces(now);
            StageCarryAndThreat(now);
            StageProvenance(now);
            StagePerception(now, ref target);
            StageTheCallbox(now, ref target);
            _player.AutoMoveTarget = target;
            NoteTargetOwner();

            // RUN FOR THE DROP, WHICH IS PLANTING THE CONDITION RATHER THAN
            // LOOSENING THE BOUND.
            //
            // The trace settled what `jobRan` has actually been measuring. Path
            // length comes within ~2m of straight-line distance on every drop —
            // the bot walks almost exactly at the marker, never wanders, is
            // never blocked. The window is 21 ticks and buys about 24 metres at
            // walking pace, so a drop posted beyond ~21m cannot complete
            // however well the bot walks. Two of five opened at 30m and 27m and
            // were unreachable before the bot took a step; the gate was
            // measuring where the marker happened to land.
            //
            // A PLAYER WOULD RUN. That is the whole justification: this is not
            // a special case bolted on to make a gate green, it is the obvious
            // behaviour of somebody with four hours to make a drop and a
            // distance to cover. `AutoMoveRun` already exists and the night-run
            // probe already uses it.
            //
            // ONLY WHEN THE JOB ACTUALLY OWNS THE TARGET. If a staged probe has
            // taken the bot, running would carry it away from the drop faster
            // rather than towards it, and `held:` is the field that knows which.
            //
            // AND IT CHANGES WHAT A NEIGHBOURING NUMBER ASKS, so it is counted.
            // `nightRunNotices` is a run total and means "people who noticed
            // the player running"; with this, some of them noticed a drop run
            // rather than the staged night run. `dropRuns` is how many ticks
            // that was, so the two can be told apart instead of one quietly
            // absorbing the other — the night-run probe's own reading is a
            // delta between its markers and is unaffected either way.
            bool runForDrop = _targetOwner == "job" && _nightRunUntil < 0;
            if (runForDrop) { _player.AutoMoveRun = true; _dropRuns++; }
            else if (_nightRunUntil < 0) _player.AutoMoveRun = false;

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
                    d => new Fact(AccusedId(d.WitnessId), "violence", "hook_street"),
                    d => $"{d.WitnessId} says it was {AccusedName(d.WitnessId)}, "
                         + "and came to say so");
                if (landed > 0)
                    Debug.Log($"SimDirector: {landed} witness account(s) arrived and "
                              + $"went indelible ({Witnesses.Arrived} total, "
                              + $"{Witnesses.Interceptions} intercepted)");
            }

            // WHO THIS WITNESS SAYS DID IT — one answer, because there were
            // two and they disagreed.
            //
            // FOUND BY READING THE LEDGER SCREEN BACK, which nothing had ever
            // done: `Zora — "Vera Mathis says it was , and came to say so"`.
            // An empty slot in a sentence shipped to the player, and repeated
            // for Rocco, Tomas, Tanja and Luka in the same run, so not rare.
            //
            // The two lambdas sat three lines apart. The one building the FACT
            // guarded `!string.IsNullOrEmpty` and fell back to "player"; the
            // one building the SENTENCE checked only `ContainsKey` and printed
            // whatever was there, including "". So the fact was right and the
            // words were wrong, which is the worst possible split — the
            // mechanics behaved and only the reader was lied to.
            //
            // Same shape as the two poach paths and the two wardrobe rules
            // repaired tonight: one idea, two implementations, and the one
            // nobody looks at is the one missing a line. This one also feeds
            // the model, so the hole was in a prompt as well as on a screen.
            // AND THE FIX FOR THAT SPLIT PUT THE ID INTO THE WORDS.
            //
            // Sharing one helper made the fact and the sentence agree, which
            // was the bug, and the value they now agree on is `"player"` —
            // right for a Fact, and a raw database key in a sentence a person
            // reads. The panel from 0eeee6d says it four times:
            //
            //     Rocco — "Mitch says it was player, and came to say so"
            //
            // So it is two helpers after all, and the reason is that the two
            // consumers want DIFFERENT THINGS from the same lookup — an id and
            // a name. What was wrong the first time was not having two, it was
            // having two that could disagree about who.
            //
            // The name comes from `GossipDirector.PlayerInTalk`, which is the
            // one place that knows whether the street has learned it yet. Not
            // a second copy of that rule: a district that says "Novak" in one
            // sentence and "the new owner" in the next, in the same panel, is
            // the same class of fault one layer up.
            string AccusedId(string witnessId) =>
                _deedAccused.TryGetValue(witnessId, out var w) && !string.IsNullOrEmpty(w)
                    ? w : "player";
            string AccusedName(string witnessId)
            {
                var id = AccusedId(witnessId);
                if (id != "player") return id;   // an NPC's id IS their display name here
                return _game != null && _game.Gossip != null
                    ? _game.Gossip.PlayerInTalk
                    : (_game != null && _game.Me != null ? _game.Me.Unplaced : "the new owner");
            }

            // One noon and one night shot per simulated day.
            if (now.Day != _shotDay) { _shotDay = now.Day; _tookDayShot = _tookNightShot = false; }
            SampleScore();
            SampleReflections();
            SampleBodies();
            SampleMix();
            SampleBubbles();
            SampleCrowding();
            if (!_tookDayShot && now.Hour == 12) { _tookDayShot = true; Shot($"day{now.Day}_noon"); }
            if (!_tookNightShot && now.Hour == 23)
            {
                _tookNightShot = true;
                // THE SHOT FIRST. Belt and braces on top of the immediate
                // restore in LightShaft.Enabled: the frame that gets saved
                // and gated is taken before any A/B has touched the scene,
                // so no future probe added here can quietly darken it.
                Shot($"day{now.Day}_night");
                // LATCHED AT THE SHOT, BECAUSE THE COUNTERS ARE LAST-WINS AND
                // THE STILL IS NOT.
                //
                // `windowsShopLit` came back 0 on a build whose night frame
                // plainly shows lit shopfronts, and I started to read that as
                // the rule being broken. It is not: `SetWindowsLit` rewrites on
                // every game hour, so the counters describe whatever hour the
                // RUN ended on — 0.70 home, which the occupancy curve puts
                // after midnight, when every shop is shut by design. The still
                // is taken at 23:00. Two moments, one pair of numbers, and the
                // number was right about a question nobody was asking.
                //
                // Same fault as the nameplate pair that cost an afternoon, and
                // the fifth site of it. The shot is the instant every visual
                // judgement is made at, so it is the instant these belong to.
                _windowsLitAtShot = WorldBuilder.WindowsLit;
                _windowsShopAtShot = WorldBuilder.WindowsShop;
                _windowsShopLitAtShot = WorldBuilder.WindowsShopLit;
                _windowsHourAtShot = now.Hour;
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

            // AND THE PLAYER'S OWN BODY, SEPARATELY, because the sweep above
            // cannot see it. That knee is COMPUTED from phase and speed rather
            // than read off a transform, and it is taken across every rig — so
            // fifty-five walking NPCs satisfy it while the protagonist stands
            // frozen in a T-pose, which after this week is the likeliest fault
            // left and nothing was watching for it.
            //
            // `PoseSignature` is read off the bones `CharacterRig` actually
            // WRITES. A rig that is posing produces a different number every
            // frame — breath alone moves the hips whether or not anybody is
            // walking. A rig that has stopped leaves it bit-identical, so the
            // test is that the value MOVED AT ALL rather than that it moved by
            // some tuned amount. Nothing in between exists: either something
            // wrote to the transform or nothing did.
            if (_player != null)
            {
                // The twin needs at least one Animator evaluation behind it, so
                // it is read here on the sampling pass rather than at staging —
                // reading it in the frame it was created would report the bind
                // pose and answer a question that already has an answer.
                RealBody.ReadNoClipTwin();
                var prig = _player.GetComponentInChildren<CharacterRig>();
                if (prig != null)
                {
                    float sig = prig.PoseSignature;
                    if (!_playerPoseSeen) { _playerPoseSeen = true; _playerPoseMin = _playerPoseMax = sig; }
                    else
                    {
                        if (sig < _playerPoseMin) _playerPoseMin = sig;
                        if (sig > _playerPoseMax) _playerPoseMax = sig;
                    }

                    // AND WHETHER THE SHAPE IS A PERSON, which is a different
                    // question from whether it MOVED and from which way the
                    // root faces. The build that forced this read
                    // `bodyUp=1.000` and `playerPose` non-zero while the still
                    // showed a splayed figure in the road: upright root,
                    // moving bones, and not a standing man.
                    //
                    // WORST OVER THE RUN, not the reading at the end. The
                    // question is "was the player ever assembled wrong", and a
                    // snapshot at the final frame answers a different one — the
                    // same reasoning that makes a maximum right for
                    // `NameTags.WorstUnplaced` and was wrong for the AO
                    // ceiling.
                    // THE BISECT'S OTHER HALF. Worst-over-run for both, so a
                    // single good frame cannot hide an inverted one.
                    if (prig.PrePoseRead)
                    {
                        if (!_prePostureSeen)
                        {
                            _prePostureSeen = true;
                            _worstPreHeadAboveHips = prig.PreHeadAboveHips;
                            _worstPreHipsAboveFeet = prig.PreHipsAboveFeet;
                        }
                        else
                        {
                            if (prig.PreHeadAboveHips < _worstPreHeadAboveHips)
                                _worstPreHeadAboveHips = prig.PreHeadAboveHips;
                            if (prig.PreHipsAboveFeet < _worstPreHipsAboveFeet)
                                _worstPreHipsAboveFeet = prig.PreHipsAboveFeet;
                        }
                    }
                    // THE AVATAR'S OWN ANSWER, kept at its most extreme swing.
                    // A pitch that reaches 180 once has inverted the body once,
                    // and an average over a run would hide exactly that — the
                    // same reasoning as the two worst-over-run pairs around it.
                    if (prig.AvatarProbeRead)
                    {
                        _avatarProbeSeen = true;
                        if (Mathf.Abs(prig.BodyPitch) > Mathf.Abs(_worstBodyPitch))
                            _worstBodyPitch = prig.BodyPitch;
                        if (Mathf.Abs(prig.BodyRoll) > Mathf.Abs(_worstBodyRoll))
                            _worstBodyRoll = prig.BodyRoll;
                        if (!string.IsNullOrEmpty(prig.ClipName)) _clipName = prig.ClipName;
                        _playerHasController = prig.HasController;
                    }
                    if (prig.PostureRead)
                    {
                        if (!_postureSeen)
                        {
                            _postureSeen = true;
                            _worstHeadAboveHips = prig.HeadAboveHips;
                            _worstHipsAboveFeet = prig.HipsAboveFeet;
                        }
                        else
                        {
                            if (prig.HeadAboveHips < _worstHeadAboveHips)
                                _worstHeadAboveHips = prig.HeadAboveHips;
                            if (prig.HipsAboveFeet < _worstHipsAboveFeet)
                            {
                                _worstHipsAboveFeet = prig.HipsAboveFeet;
                                // WHEN, AND WHAT THE BODY WAS DOING.
                                //
                                // All six `bodies` failures in sixty kept runs
                                // read `hipsOverFeet=-0.78`, identical to two
                                // decimals. A value that accumulates GROWS; a
                                // wrong absolute is CONSTANT, and this project
                                // has diagnosed a rig fault off exactly that
                                // signature before — a number sitting at
                                // -0.775 all run.
                                //
                                // So this is not noise and it is not drift: it
                                // is one specific state, entered on about one
                                // run in ten. A worst-over-run number cannot
                                // say WHICH state, so it now records the day,
                                // the hour and the clip that was playing when
                                // the worst reading was taken. If it is the
                                // Fall — the run stages one — the gate is
                                // over-specified and the fix is the assertion;
                                // if it is an ordinary walking hour, the rig
                                // inverts sometimes and the fix is the rig.
                                // Those are completely different searches and
                                // guessing between them costs a round trip.
                                _worstPoseDay = _game != null ? _game.Now.Day : -1;
                                _worstPoseHour = _game != null ? _game.Now.Hour : -1;
                                _worstPoseClip = prig.ClipName ?? "none";
                            }
                        }
                    }
                }
            }
        }

        bool _postureSeen;
        float _worstHeadAboveHips, _worstHipsAboveFeet;
        int _worstPoseDay = -1, _worstPoseHour = -1;
        string _worstPoseClip = "none";
        bool _prePostureSeen;
        float _worstPreHeadAboveHips, _worstPreHipsAboveFeet;
        float _worstBodyPitch, _worstBodyRoll;
        string _clipName = "";
        bool _avatarProbeSeen;
        bool _playerHasController;

        /// Per-frame cost of every `CharacterRig` in the scene, in milliseconds.
        /// Divided by the frame count rather than by the sample count: the
        /// question is what a FRAME pays, and rigs run once per character per
        /// frame, so dividing by samples would report the cost of one character
        /// and call it the cost of the crowd.
        static double RigsPerFrameMs()
        {
            var c = Perf.Get("rigs");
            if (c == null || Perf.FrameCount <= 0) return 0;
            return c.TotalMs / Perf.FrameCount;
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
            // THE STATE THE DESIGN CARES ABOUT, which the score has been able
            // to name since it was written and nothing has ever asked for.
            //
            // `RoomHasGoneQuiet` is pulse at the floor with unease above half
            // — its comment calls it "the moment the player should learn to
            // dread", and it is a STATE rather than a consequence of the
            // numbers, which is why it is a named function and not an
            // inequality somebody rewrites at each call site.
            //
            // Counted rather than acted on. Whether the room going quiet
            // should DO something is a design decision off a still and a
            // listen; whether it ever happens at all is a fact, and the fact
            // has never been available. If this reads zero over a nine-day
            // run the state is unreachable and the model is decorative.
            if (MusicModel.RoomHasGoneQuiet(mix)) _roomQuietSamples++;
            // AND THE TWO LAYERS THE CONDITION READS, so the 73% has an
            // explanation rather than a threshold guess attached to it.
            //
            // `roomQuiet` came back 1656 of 2267 samples. The model calls that
            // state "the moment the player should learn to dread" and it is
            // the DEFAULT condition of the game.
            //
            // THE DISTRIBUTION LANDED AND IT KILLED THE FORK THIS PARAGRAPH
            // SET UP. It said two completely different causes fit — the pulse
            // sits at its floor because the street is quiet, OR unease sits
            // high because the game is tense — and that they want opposite
            // fixes. `pulseMedian=0.000 uneaseMedian=1.000` came back, which
            // reads as both at once, and it is neither: those two layers are
            // not independent and never were.
            //
            // `MusicModel.Mix` computes ONE variable and derives both from it.
            // `Pulse = Clamp01(1 - exposure*1.5) * ...` is zero for any
            // exposure at or above 0.667; `Unease = Clamp01((exposure-0.2)/0.6)`
            // is one for any exposure at or above 0.8. So unease at its
            // ceiling FORCES pulse to its floor, arithmetically, and reading
            // them as two findings double-counts a single one.
            //
            // Which leaves exactly one question — why is exposure at 0.8 for
            // the median sample of a run — and exposure is
            // `max(heat, lead*0.9)`. So the heat series is the thing to print,
            // and it is the number that says whether this is the score being
            // wrong about a normal week or the SIM living at maximum heat
            // because a bot commits every crime in the game inside seventeen
            // days. Those are a music problem and a harness problem and they
            // have nothing in common but the symptom.
            //
            // NOTE THE SHAPE, because it is the one this project keeps
            // shipping: I wrote a fork into a comment, the run answered it,
            // and the answer was that the fork was false. Two numbers derived
            // from one variable are one number twice.
            //
            // Rule 2 still: print the distribution, look, THEN decide. Nothing
            // is re-tuned here.
            _pulseSamples.Add((float)mix[(int)MusicLayer.Pulse]);
            _uneaseSamples.Add((float)mix[(int)MusicLayer.Unease]);
            _heatSamples.Add((float)_game.CurrentHeat);
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
            _labelsColliding = CollidingNames();
            // AND AGAIN AT SHOT TIME, so the bubble peak has seen the frames
            // that actually get committed. One sample per audit could miss
            // every conversation in a seventeen-day run.
            _bubbleSampleWanted = true;
            // TWO MORE THINGS THE STILLS SHOWED AND NOTHING MEASURES.
            //
            // MIRRORED TEXT. `review_day2_noon` at fbb1865 has a caption
            // rendering back to front — "warehouse" reversed. World-space
            // TextMesh is only readable from the front, and the bark and
            // caption text is not billboarded, so from behind it is a mirror.
            // The count is of visible world text whose own forward points away
            // from the camera, which is exactly the population that reads
            // backwards.
            //
            // NAMEPLATE SIZE. `review_day2_night` has "Dusan" spanning a third
            // of the frame. `NameTags` resolves OVERLAP and has no opinion
            // about SIZE, so a label can pass the declutter and still be
            // absurd. The number is the tallest nameplate as a fraction of
            // viewport height.
            //
            // Both REPORTED, NOT GATED, on the first run. There is no bound
            // yet that has been measured, and inventing one is how
            // `nightNotDarker` came to fail on a thousandth.
            MeasureTextFaults();
            // THE SCENE AUDIT, at the same moment and for the same reason: this
            // is the point in the run where "what is on screen" is a settled
            // question. See `SceneAudit` for why it walks objects rather than
            // pixels.
            SceneAudit.Run(_player != null ? _player.gameObject : null);
            Debug.Log(SceneAudit.Report());

            Debug.Log($"SimDirector: glyphs labels={_labels} fontless={_labelsFontless} "
                      + $"blank={_labelsBlank} worldText={worldText} "
                      + $"depthTested={worldTextMaterialled} "
                      + $"adopted={WorldText.Adopted} refused={WorldText.Refused} "
                      + $"shader={WorldText.ShaderPresent} "
                      + $"collidingNames={_labelsColliding} collidingWorldText={_collidingWorldText}"
                      + $" worstWorldPair=[{_worstWorldPair}]"
                      + $" worstNamePair=[{_worstNamePair}]"
                      + $" namesTracked={_namesTracked}"
                      + $" namesAtWorstName={_namesAtWorstName}"
                      + $" worldTextTracked={_worldTextTracked}"
                      + $" bubblesTracked={_bubblesTracked}"
                      + $" textWalked={_textWalked}"
                      + $" textProjected={_textProjected}"

                      + $" textNoText={_textNoText}"
                      + $" textInvisible={_textInvisible}"
                      // THE SPLIT `namesTracked=0` HAS NEVER HAD. `seen` counts
                      // managed labels BEFORE the visibility cull and `culled`
                      // counts the ones that cull threw away. seen=0 means
                      // `Manages` does not know these objects; seen>0 with
                      // culled=seen means the frustum test is eating them and
                      // the declutter is fine.
                      + $" namesManagedSeen={_namesManagedSeen}"
                      + $" namesManagedCulled={_namesManagedCulled}"
                      + $" textPersonLabels={_textPersonLabels}"
                      + $" textWalkKinds=[{TextWalkKindsTop()}]"
                      + $" labelsOrphan={_labelsOrphan}"
                      + $" labelsManagedAtOrphan={_labelsManagedAtOrphan}"
                      + $" labelsManagedPeak={_labelsManagedPeak}"
                      + $" labelOrphanText=[{_labelOrphanText}]"
                      + $" textNoRect={_textNoRect}");
        }

        int _labelsColliding = -1;
        int _textMirrored = 0;

        /// How far out the billboards were at the instant a still was taken, and
        /// how many there were to correct. See the block in `Shot` — these are
        /// sampled BEFORE the aim, which is the only ordering that can measure
        /// the fault rather than the repair.
        /// Visible TextMeshes facing away from the camera, and visible
        /// TextMeshes in total. Half of every double-sided street plate faces
        /// away BY CONSTRUCTION, so this is a ratio to read, not a fault to
        /// count. See `MeasureTextFaults`.
        int _textFacingAway = 0, _textVisible = 0;
        /// Visible text at the instant the facing-away count peaked — the only
        /// denominator that one can honestly be divided by.
        int _textVisibleAtAway = 0;

        int _billboardsStale = 0;
        /// How many billboards existed at the instant the worst count was
        /// taken. The only denominator `billboardsStale` can honestly be
        /// divided by — same lesson, same shape, as `bubblesAtWorst`.
        int _billboardsAtWorst = 0;
        readonly List<float> _billboardStaleFrac = new List<float>();

        /// The typical share of billboards drifting, against the peak's worst
        /// moment. -1 for "never sampled", because a median of zero is a real
        /// and welcome reading and must not be confused with no reading.
        double BillboardStaleMedian
        {
            get
            {
                if (_billboardStaleFrac.Count == 0) return -1;
                var s = new List<float>(_billboardStaleFrac);
                s.Sort();
                return s[s.Count / 2];
            }
        }
        float _billboardWorstDeg = 0f;
        int _billboardsAimed = 0;

        /// Visible text plates lying face-up — captions painted on the road.
        /// The worst carries the OBJECT'S NAME, because which system laid it
        /// down is the question the still could not answer.
        int _textFlat;
        string _textFlatWorst = "none";

        /// Person-sized bare capsules visible in a shot — the white dummies
        /// review_day2_noon keeps showing while `walkersPrimitive=0` reads
        /// clean, because that counter's denominator is the CityWalker set
        /// and these bodies belong to some other population. The ROOT NAMES
        /// say which one; rule 3b, the denominator, worn by a mesh.
        int _capsulesLoose;
        string _capsulesLooseWho = "none";
        int _capsulesSeen, _capsulesAnim, _capsulesSized;
        string _capsulesAnimWho = "none";

        /// Visible bought bodies that were never tinted — `Tint` always
        /// leaves a property block behind, so a skinned renderer WITHOUT
        /// one has never met the wardrobe and draws in material white:
        /// the smooth pale figures the capsule census proved are not
        /// capsules. Named by root, counted once per shot sweep, run-worst.
        int _bodiesUndressed;
        string _bodiesUndressedWho = "none";

        void MeasureUndressedBodies()
        {
            int found = 0;
            var who = new List<string>();
            foreach (var smr in FindObjectsByType<SkinnedMeshRenderer>(
                         FindObjectsSortMode.None))
            {
                if (smr == null || !smr.isVisible) continue;
                if (smr.HasPropertyBlock()) continue;
                // The PAINT path colours a material INSTANCE rather than a
                // block, so no-block alone would count a painted body as
                // bare — the first sixteen may be exactly that. A body is
                // undressed only if its material is also still white (or
                // missing): both escape hatches closed, not one.
                var mat = smr.sharedMaterial;
                if (mat != null && mat.HasProperty("_Color"))
                {
                    var c = mat.color;
                    bool whiteish = c.r > 0.92f && c.g > 0.92f && c.b > 0.92f;
                    if (!whiteish) continue;
                }
                found++;
                if (who.Count < 4 && !who.Contains(smr.transform.root.name))
                    who.Add(smr.transform.root.name);
            }
            if (found > _bodiesUndressed)
            {
                _bodiesUndressed = found;
                _bodiesUndressedWho = who.Count > 0
                    ? string.Join("/", who.ToArray()) : "none";
            }
        }

        /// The census behind those two numbers: every visible renderer
        /// whose mesh is Unity's builtin Capsule, person-sized, standing
        /// free — not a limb of a rigged body, which parents its capsules
        /// under an armature with a controller.
        void MeasureLooseCapsules()
        {
            // FIRST OUTING: read 0 with a white capsule in the middle of
            // day1_noon at db605a4 — its own rule-3b fault. Every filter
            // below now counts what it discards, and the excluded sets
            // carry names too, because the leak is almost certainly one of
            // these buckets: a walker whose body swap failed still has an
            // Animator, and the old version silently excused it for that.
            int found = 0, seen = 0, animOut = 0, sizeOut = 0;
            var who = new List<string>();
            var animWho = new List<string>();
            foreach (var mf in FindObjectsByType<MeshFilter>(FindObjectsSortMode.None))
            {
                if (mf == null || mf.sharedMesh == null
                    || mf.sharedMesh.name != "Capsule") continue;
                var r = mf.GetComponent<Renderer>();
                if (r == null || !r.isVisible) continue;
                seen++;
                var s = mf.transform.lossyScale;
                float h = mf.sharedMesh.bounds.size.y * s.y;
                if (h < 1.2f || h > 2.6f) { sizeOut++; continue; }
                if (mf.GetComponentInParent<Animator>() != null)
                {
                    animOut++;
                    if (animWho.Count < 4
                        && !animWho.Contains(mf.transform.root.name))
                        animWho.Add(mf.transform.root.name);
                    continue;
                }
                found++;
                if (who.Count < 4 && !who.Contains(mf.transform.root.name))
                    who.Add(mf.transform.root.name);
            }
            if (seen > _capsulesSeen) _capsulesSeen = seen;
            if (animOut > _capsulesAnim)
            {
                _capsulesAnim = animOut;
                _capsulesAnimWho = animWho.Count > 0
                    ? string.Join("/", animWho.ToArray()) : "none";
            }
            if (sizeOut > _capsulesSized) _capsulesSized = sizeOut;
            if (found > _capsulesLoose)
            {
                _capsulesLoose = found;
                _capsulesLooseWho = who.Count > 0
                    ? string.Join("/", who.ToArray()) : "none";
            }
        }
        /// How many bubbles the SHOT re-pinned. Zero on a shot with speech in
        /// it means the re-pin is not running; zero with no speech is a quiet
        /// street, and only the count beside `bubblesOnScreen` separates them.
        int _bubblesPinnedAtShot;

        /// Bubbles moved by the shot-time de-overlap. Zero here with a non-zero
        /// `bubblesAtCeiling` means the pass ran and had nothing to do; zero
        /// with no denominator is what the birth-time version reported for its
        /// whole life.
        int _bubblesShotLifted;
        /// How many nameplates the SHOT re-pinned. Zero on a shot with people
        /// in it means the re-pin is not running; zero with nobody on screen
        /// is an empty street.
        int _namesPinnedAtShot;
        int _billboardsTracked = 0;

        /// See the note at the call site. Two numbers, each answering one
        /// question a still asked and no gate could.
        void MeasureTextFaults()
        {
            var cam = Camera.main;
            if (cam == null) return;
            int mirrored = 0, away = 0, seen = 0, flat = 0;
            float flatWorstDot = 0f;
            string flatWorstName = null;
            foreach (var tm in FindObjectsByType<TextMesh>(FindObjectsSortMode.None))
            {
                if (tm == null || string.IsNullOrEmpty(tm.text)) continue;
                var r = tm.GetComponent<Renderer>();
                if (r == null || !r.isVisible) continue;

                // FACING AWAY: the text's own forward against the direction
                // from the camera to it. `NpcWalker` billboards a label with
                // `LookRotation(labelPos - cam)`, so a correctly-facing plate
                // has its forward pointing AWAY from the camera and a negative
                // dot is the one we are behind.
                //
                // The comment that used to sit here said the opposite of the
                // line under it — "positive dot means we are behind the
                // glyphs" — and the line was right. A comment is a claim with
                // no test attached.
                var toText = tm.transform.position - cam.transform.position;
                bool facingAway = Vector3.Dot(tm.transform.forward, toText) < 0f;

                // AND THAT ALONE IS NOT A FAULT, which is what this metric got
                // wrong and what I was one report away from telling Jafar was a
                // regression.
                //
                // It read 46, then 58, and "mirrored world text is getting
                // worse" is exactly how it looks. Then `StreetFurniture.Label`:
                // every street plate is built TWICE, at `yaw` and `yaw + 180`,
                // deliberately — "a plate you can only read from one side is
                // worse than no plate, because you walk round it to find out."
                // So one of every pair is always facing away, by construction,
                // and `Hidden/LedgerText` culls its reverse face so it draws
                // nothing at all.
                //
                // The metric was counting the back of 58 correctly-built signs
                // and calling each one a defect. It went up because more signs
                // were in frustum, not because anything broke. `isVisible` is a
                // frustum test and never claimed otherwise; I read it as "can
                // be seen".
                //
                // So the question narrows to the one that has an answer: text
                // facing away that is NOT back-face culled, and therefore
                // really does render as a mirror image.
                // AND THE OTHER HALF OF THE COUNT, WHICH THIS COULD NEVER SEE.
                //
                // `mirrored` only rises for text that is facing away AND is not
                // on the culling shader. Every street plate IS on it — the whole
                // point of `WorldText.Adopt` — so no plate can ever contribute,
                // however it renders. The number is therefore a claim about
                // speech bubbles wearing the name of a claim about the city, and
                // `review_day5_night` at 4ac2f0f has what looks like a plate's
                // reverse face printed backwards over a lit window while this
                // reads 0. Both can be true, and only one of them is what a
                // player sees.
                //
                // So the raw population is counted too. `facingAway` alone is
                // NOT a fault — `StreetFurniture.Label` builds every plate twice,
                // at yaw and yaw+180, deliberately, so exactly half of them face
                // away by construction and `Cull Back` is what makes that
                // correct. The number to watch is the RATIO: if backs are being
                // culled, roughly half the plates in frustum face away and the
                // frame is clean. If the frame shows mirrored glyphs while this
                // sits at half, the cull is not working and the shader is the
                // suspect rather than the geometry.
                if (facingAway)
                {
                    away++;
                    var mat = r.sharedMaterial;
                    var sh = mat != null ? mat.shader : null;
                    if (sh == null || sh.name != "Hidden/LedgerText") mirrored++;
                }
                seen++;

                // LYING FLAT: a text plate's forward is its face normal, so
                // forward pointing at the SKY is a caption painted on the
                // road — what review_day2_noon at 57f91eb shows in van-sized
                // letters and nothing counted. Named, not just counted,
                // because the object's name says which SYSTEM laid it down
                // (a bubble, a nameplate, a street plate), and that is the
                // question one still could not answer. Zero degrees is
                // dead flat; the bound at 45 keeps a legitimately
                // downhill-tilted billboard out of the count.
                float skyward = Mathf.Abs(
                    Vector3.Dot(tm.transform.forward, Vector3.up));
                if (skyward > 0.707f)
                {
                    flat++;
                    if (skyward > flatWorstDot)
                    {
                        flatWorstDot = skyward;
                        flatWorstName = tm.gameObject.name + "/"
                            + Mathf.RoundToInt(Mathf.Acos(skyward)
                                               * Mathf.Rad2Deg)
                            + "degFromFlat";
                    }
                }

                // THE HEIGHT MEASUREMENT MOVED, and the comment that used to sit
                // here is why. It said "only the NPC nameplates are in question
                // here — street plates are meant to be large and near — so this
                // measures what `NameTags` manages." The loop it sat in walks
                // EVERY `TextMesh` in the scene, street plates included, so it
                // measured the opposite of what it claimed and reported 0.210
                // for what may well have been a sign the camera was standing
                // next to.
                //
                // It now lives in `NameTags.Resolve`, where the set really is
                // the offered NPC labels and the rects are already computed —
                // and where a suppressed label is excluded, because an invisible
                // name being large is not a fault. Read as
                // `NameTags.WorstNameFrac`.
            }
            // WORST OVER THE RUN, not the reading at one instant — and the
            // first run of this is exactly why. It came back
            // `worstTextHeightFrac=0.036`, a label 3.6% of screen height,
            // while the still that prompted the measurement shows a name
            // spanning a third of the frame. Both are true: the sample was
            // taken at a moment when no label was near, and the still caught a
            // moment when one was. A single sample cannot answer "does this
            // ever get absurd", which is the question.
            if (mirrored > _textMirrored) _textMirrored = mirrored;
            // Run-worst, same shape as the rest of the family — and the
            // NAME rides with the count it belongs to, same instant.
            if (flat > _textFlat)
            {
                _textFlat = flat;
                _textFlatWorst = flatWorstName ?? "none";
            }
            // PEAKS, like every other reading here, and the pair is the
            // point: `away` with no `seen` beside it cannot be read as a
            // ratio, and the ratio is the whole diagnosis.
            // AND THE DENOMINATOR IS TAKEN WITH THE NUMERATOR, because I wrote
            // "read the RATIO, not the count" onto the queue about these two and
            // then peaked them independently — the same fault found in
            // `collidingBubbles` twenty minutes ago and fixed there first.
            //
            // The frame with the most text facing away is not necessarily the
            // frame with the most text in it, so two independent maxima do not
            // divide. 70 over 149 read as 47%, which happened to support the
            // right conclusion for the wrong reason: the real evidence that
            // `Cull Back` works is `textMirrored=0`, not that fraction.
            if (away > _textFacingAway)
            {
                _textFacingAway = away;
                _textVisibleAtAway = seen;
            }
            if (seen > _textVisible) _textVisible = seen;
        }

        /// EVERY DROP THE OUTFIT POSTED, AND WHAT HAPPENED TO IT.
        ///
        /// WHY. `jobsDone=0 jobsMissed=3` came back on one run in 64 and reddened
        /// two gates, and the run could say nothing at all about WHY the bot
        /// missed three drops in a row — only that it had. The distribution says
        /// this is not noise: 49 runs finish 2/3, eight finish 3/3, six finish
        /// 1/4 with the outfit cutting them off, one finishes 0/3. So a quarter
        /// of the spread is the bot losing drops, and no number anywhere says
        /// what it lost them to.
        ///
        /// THE SUSPECT IS THE FRAME, NOT THE ROUTE. The bot heads straight for
        /// `ActiveJobPos` the moment one opens, and the window is four in-game
        /// hours. But `frameWorstMs=43666` — a single forty-three-second frame —
        /// and on a frame that long the clock crosses 02:00 while the walk gets
        /// one step. That is a hypothesis, which is exactly what this exists to
        /// settle: closest approach says whether the bot was walking and ran out
        /// of night, or never got near the thing at all. Rule 2, print the
        /// series before touching anything.
        ///
        /// OBSERVED, NOT INSTRUMENTED INTO THE GAME. Everything here is read off
        /// `ActiveJobPos` and the campaign's own counters, so the drop pipeline
        /// is measured without a probe inside it — the harness watches, and a
        /// watcher cannot alter the outcome it reports.
        /// AND THE TRACE SAID EVERYTHING EXCEPT THE ONE THING THAT MATTERED.
        ///
        /// Three runs in ninety-nine finish `jobsDone=0`, and reading the trace
        /// on two of them settles what the paragraph above suspected — and
        /// settles it AGAINST the frame. The failing run approached to 5.0m,
        /// 3.6m and 19.3m; the passing one to 2.8, 1.3, 4.2, 1.8 and 2.8. The
        /// completion radius is 2.5m flat, so this is a bot that walks most of
        /// the way and stops a few metres short — not one that runs out of
        /// night, because every one of those readings is timestamped inside the
        /// window.
        ///
        /// WHICH LEAVES ONE QUESTION AND THE TRACE COULD NOT ANSWER IT: the
        /// drop is not the only thing steering. `StagePerception` overwrites
        /// the target twice — `loiter-walk` sends the player somewhere else
        /// entirely, `loiter-hold` pins them where they stand — and the
        /// staging has no idea a drop is open. A probe that steals the bot for
        /// part of a four-hour window is exactly the shape that makes a gate
        /// fail three times in ninety-nine for a reason nobody has named.
        ///
        /// So the window now counts ticks by owner. Not a guess about which
        /// probe: the count, per drop, in the trace beside the approach. If
        /// `job` holds every tick and the bot still stops at 3.6m, the steering
        /// is innocent and the arrival is the fault; if a probe holds a third
        /// of them, the fix is priority and not locomotion. Those have nothing
        /// in common but the symptom, and no reading here has separated them.
        readonly List<string> _jobTrace = new List<string>();
        bool _jobOpen;
        int _jobOpenDay;
        double _jobOpenDist, _jobNearest;
        int _jobNearestHour = -1;
        int _jobDoneAtOpen, _jobMissedAtOpen;

        /// Whoever set `AutoMoveTarget` last this tick.
        string _targetOwner = "none";
        readonly Dictionary<string, int> _jobOwnerTicks = new Dictionary<string, int>();

        /// How many loiter holds ended early because a drop opened under them.
        int _loitersCutShort;
        /// Evenings the loiter probe had to give up and try again, because a
        /// drop opened under it before anybody looked. Non-zero is a finding
        /// about the schedule rather than a failure; four is the cap, and
        /// hitting it means the drop window and the loiter window overlap by
        /// design and one of them has to move.
        int _loiterRetries;
        /// Ticks the bot spent running because a drop was open and the job owned
        /// the target. Printed so `nightRunNotices` can still be read: it counts
        /// people who noticed the player RUNNING, and this adds a second reason
        /// to be running.
        int _dropRuns;

        /// GROUND COVERED DURING THE WINDOW, which is the number the owner
        /// tally could not supply and the second half of the answer.
        ///
        /// The tally split the misses cleanly in two. `d8` was a staged probe
        /// owning every tick — fixed above. But `d1` and `d13` read
        /// `held:job=20` and `held:job=19` and still finished 9.3m and 6.9m
        /// out, so the steering was right for every tick of those windows and
        /// the bot still did not arrive.
        ///
        /// Ownership cannot tell "steered at the drop and walking" from
        /// "steered at the drop and not moving" — a conversation, a knockdown
        /// or a blocked path all read as `job` holding the target. And the
        /// comparison the numbers invite is unreadable without this: `d2`
        /// covered 16.5m in 14 ticks and completed, `d13` covered 12.1m in 19.
        /// More time, less ground. That is not a distance problem and it is not
        /// a steering problem, and no reading in this trace can say which of
        /// the remaining ones it is.
        Vector3 _jobLastPos;
        double _jobMetresWalked;
        float _jobWorstSeverity;
        /// The longest run of consecutive ticks the bot did not move during a
        /// drop window, and the run in progress. See the note at the sample
        /// site: a total covers a slow walk and a dead stop identically.
        int _jobLongestStall, _jobStillRun;
        /// How many bodies were within two metres of the player AT THE
        /// INSTANT the longest stall was recorded, and where he stood. The
        /// pair separates "he was in the mob" from "he was alone and stuck
        /// on geometry", which are the only two things left once ownership
        /// and injury are ruled out — and `d13` ruled both out.
        int _jobStallCrowd;
        string _jobStallWhere = "nowhere";

        /// Called once per tick, after every stage has had its chance at the
        /// target. Only while a drop is open: outside the window the bot is
        /// free to be anywhere and counting it would drown the signal.
        void NoteTargetOwner()
        {
            if (!_jobOpen) return;
            _jobOwnerTicks.TryGetValue(_targetOwner, out int n);
            _jobOwnerTicks[_targetOwner] = n + 1;
        }

        /// `job=812 loiter-hold=310`, newest-largest first, or the words that
        /// say nothing was counted — because an empty string here would read as
        /// "the job held it all along", which is the opposite of what no data
        /// means.
        string OwnerTally()
        {
            if (_jobOwnerTicks.Count == 0) return "unwatched";
            var parts = new List<string>();
            foreach (var kv in _jobOwnerTicks) parts.Add($"{kv.Key}={kv.Value}");
            parts.Sort(System.StringComparer.Ordinal);
            return string.Join(",", parts);
        }

        void TraceJob(GameTime now)
        {
            if (_game == null || _player == null) return;

            // THE CUT-OFF, WATCHED RATHER THAN ASKED FOR. `Campaign` records the
            // flag but not the day it flipped, and the day is what turns "the
            // outfit went quiet" into a count of nights. Observing the edge here
            // needs no new Core field and no save-format change.
            if (_cutOffDay == 0 && _game.Campaign != null && _game.Campaign.OutfitCutOff)
            {
                _cutOffDay = now.Day;
                Debug.Log($"SimDirector: the outfit cut us off on day {_cutOffDay} — "
                          + $"no drop is posted after this, by design.");
            }
            if (_cutOffDay > 0) _cutOffNights = Mathf.Max(0, now.Day - _cutOffDay);

            var pos = _game.ActiveJobPos;
            if (pos.HasValue)
            {
                // MEASURED THE WAY THE GAME MEASURES IT, which the first version
                // was not. `GameController` completes a drop on
                // `Distance(new Vector3(p.x, 0, p.z), new Vector3(m.x, 0, m.z))
                // < 2.5f` — a FLAT distance — and this took the full 3D one. The
                // trace came back `d12:MISSED[nearest=1m]`, which under a 2.5m
                // radius reads as the completion check being broken, and the
                // first thing I nearly did was go and read it.
                //
                // A number that answers a slightly different question than the
                // one it is being compared against is the fault this project
                // finds most often, and here it was mine, in an instrument
                // written an hour ago to diagnose exactly this.
                var p0 = _player.transform.position;
                double d = Vector3.Distance(new Vector3(p0.x, 0, p0.z),
                                            new Vector3(pos.Value.x, 0, pos.Value.z));
                if (!_jobOpen)
                {
                    _jobOpen = true;
                    _jobOpenDay = now.Day;
                    _jobOpenDist = d;
                    _jobNearest = d;
                    _jobNearestHour = now.Hour;
                    _jobDoneAtOpen = _game.Campaign.JobsDone;
                    _jobMissedAtOpen = _game.Campaign.JobsMissed;
                    // PER DROP, NOT PER RUN. A run total would answer "did any
                    // probe ever hold the bot", which is yes and is useless;
                    // the question is whether one held it during THIS window.
                    _jobOwnerTicks.Clear();
                    _jobLastPos = p0;
                    _jobMetresWalked = 0;
                    _jobWorstSeverity = 0;
                    _jobLongestStall = 0;
                    _jobStallCrowd = 0; _jobStallWhere = "nowhere";
                    _jobStillRun = 0;
                }
                else
                {
                    if (d < _jobNearest) { _jobNearest = d; _jobNearestHour = now.Hour; }
                    // PATH LENGTH, NOT DISPLACEMENT. A bot that walks twenty
                    // metres in a circle and a bot that stands still both end
                    // the window the same distance out, and they are completely
                    // different faults. Flat, like every other distance here,
                    // because the completion test is flat.
                    var flatNow = new Vector3(p0.x, 0, p0.z);
                    var flatWas = new Vector3(_jobLastPos.x, 0, _jobLastPos.z);
                    float step = Vector3.Distance(flatNow, flatWas);
                    _jobMetresWalked += step;
                    _jobLastPos = p0;

                    // AND WHETHER HE WAS STANDING STILL, WHICH THE TOTAL CANNOT
                    // SAY AND IS THE LAST QUESTION THIS TRACE CANNOT ANSWER.
                    //
                    // `d13:MISSED[from=16m nearest=6.9m walked=10.0m
                    // held:job=19]` — ten of sixteen metres covered, the job
                    // steering for every tick of the window, stalled seven
                    // metres out. The first miss beside it turned out to be the
                    // waypoint's own collider; no obstacle explains this one.
                    //
                    // TEN METRES IN NINETEEN TICKS IS THE SAME TOTAL whether he
                    // walked slowly the whole time or walked briskly for eight
                    // ticks and stood still for eleven, and those are completely
                    // different faults: the first is a speed problem — a hurt
                    // man, a crowd — and the second is something taking him over
                    // that ownership cannot see, because a conversation holds
                    // his POSITION without ever touching the job's TARGET.
                    //
                    // LONGEST RUN, NOT A COUNT. Eleven still ticks scattered
                    // through a window is a man weaving through a crowd; eleven
                    // in a row is a man who stopped, and only the second is
                    // worth a mechanism. Five centimetres is not a design bound
                    // — a walking step is most of a metre — it is the line
                    // between "moved" and "float noise".
                    if (step < 0.05f)
                    {
                        _jobStillRun++;
                        if (_jobStillRun > _jobLongestStall)
                        {
                            _jobLongestStall = _jobStillRun;
                            // WHO WAS STANDING ON HIM AT THE WORST OF IT, taken
                            // at the instant the record is set rather than at
                            // the end of the window — the crowd moves, and a
                            // count from thirty seconds later describes a
                            // different street.
                            //
                            // `0720f52` says d13 is a different fault from d12
                            // and both looked like one. d12:
                            // `walked=24.5m stalled=0 held:job=7,waypoint=8` —
                            // never stopped, always moving, and a WAYPOINT took
                            // the target off the job for eight ticks. d13:
                            // `walked=10.1m stalled=13 hurt=0.00 held:job=19` —
                            // the job held the target for all nineteen ticks,
                            // he was not hurt, and he stood dead still for
                            // thirteen of them. Ownership is innocent and speed
                            // is innocent, so something was physically in the
                            // way, which is the case the paragraph above named
                            // and nothing could measure.
                            //
                            // AND THERE IS NOW A SUSPECT. The mob is 41 bodies
                            // inside two metres at `(-1,-3)`, in the road,
                            // outside the pub — a man walking a job through
                            // that would stop exactly like this. This says
                            // whether he was in it.
                            _jobStallCrowd = 0;
                            if (_npcs != null)
                                foreach (var n in _npcs)
                                {
                                    if (n == null || !n.isActiveAndEnabled) continue;
                                    if ((n.transform.position - _player.transform.position)
                                        .sqrMagnitude <= 4f) _jobStallCrowd++;
                                }
                            var p = _player.transform.position;
                            _jobStallWhere = $"{p.x:0}/{p.z:0}";
                        }
                    }
                    else _jobStillRun = 0;
                    // HOW HURT HE WAS, at his worst, during THIS window.
                    //
                    // `Gait.SpeedFactor` slows a hurt man, and one drop moved
                    // at a third of the rate of the other four with the job
                    // holding the target the whole time. Injury is the one
                    // candidate the code makes plausible; the alternative is
                    // crowd shoving, and these two numbers separate them
                    // without another round trip of guessing.
                    //
                    // Worst rather than mean, because the question is whether
                    // he was hurt AT ALL during a window that under-performed —
                    // an average over twenty-one ticks would dilute a bad
                    // stretch into nothing.
                    float sev = _player.SeverityNow;
                    if (sev > _jobWorstSeverity) _jobWorstSeverity = sev;
                }
                return;
            }

            if (!_jobOpen) return;
            _jobOpen = false;
            // WHICH COUNTER MOVED, not which one we hoped moved. A marker can
            // also vanish without either counter changing — the campaign ending
            // mid-window does exactly that — and calling every disappearance a
            // miss would invent a fault out of a legitimate ending.
            string how = _game.Campaign.JobsDone > _jobDoneAtOpen ? "done"
                       : _game.Campaign.JobsMissed > _jobMissedAtOpen ? "MISSED"
                       : "gone";
            _jobTrace.Add($"d{_jobOpenDay}:{how}[from={_jobOpenDist:0}m "
                          + $"nearest={_jobNearest:0.0}m@{_jobNearestHour:00}h "
                          + $"walked={_jobMetresWalked:0.0}m "
                          + $"hurt={_jobWorstSeverity:0.00} "
                          // The longest DEAD STOP in the window, which
                          // `walked` cannot show: ten metres in nineteen
                          // ticks reads the same for a slow walk and for
                          // a brisk one that stopped halfway.
                          + $"stalled={_jobLongestStall} "
                          + $"stalledWith={_jobStallCrowd}@{_jobStallWhere} "
                          + $"held:{OwnerTally()}]");
        }


        /// HOW THE PLAYER READS AGAINST THE CROWD, in rendered pixels.
        ///
        /// THE STANDING ITEM: turn a still into a number. `bodyCoat` came back
        /// `denim hsv=0.60/0.36/0.59 rgb=96,118,149` — a solid mid-blue — and
        /// the noon frame still shows a figure that reads as bare plastic. Both
        /// are true, and the gap between them is the only thing a player
        /// experiences. Every existing body metric asks about the MATERIAL:
        /// whether a coat reached every mesh, what colour it was, how much area
        /// it covers. None asks what the pixels come out as after the noir
        /// grade, the exposure and the fog.
        ///
        /// So: average the player's own pixels, average the crowd's, and print
        /// both. A player who reads as dressed is one whose colour sits in the
        /// same range as the clothed people around them; one who reads as a
        /// mannequin is paler and greyer than all of them. That is a
        /// comparison, not a threshold — rule 2 forbids inventing the bound
        /// before the series exists, and this is the run that produces it.
        ///
        /// SAMPLED AT SHOT TIME against the shot camera, because the question is
        /// about the committed frame and every metric tonight that sampled a
        /// different instant was answering a different question.
        void MeasureBodyRead(Camera cam)
        {
            if (cam == null || _game == null || _game.Player == null) return;
            var px = FramePixels(cam);
            if (px == null) return;
            const int W = 640, H = 360;

            bool Average(Renderer r, out double lum, out double sat, out int n)
            {
                lum = sat = 0; n = 0;
                if (r == null || !r.isVisible) return false;
                if (!NameTags.ScreenRect(cam, r.bounds, out var rect)) return false;
                int x0 = Mathf.Clamp((int)(rect.xMin * W / Screen.width), 0, W - 1);
                int x1 = Mathf.Clamp((int)(rect.xMax * W / Screen.width), 0, W - 1);
                int y0 = Mathf.Clamp((int)(rect.yMin * H / Screen.height), 0, H - 1);
                int y1 = Mathf.Clamp((int)(rect.yMax * H / Screen.height), 0, H - 1);
                for (int y = y0; y <= y1; y++)
                    for (int x = x0; x <= x1; x++)
                    {
                        var c = px[y * W + x];
                        double mx = Mathf.Max(c.r, Mathf.Max(c.g, c.b));
                        double mn = Mathf.Min(c.r, Mathf.Min(c.g, c.b));
                        lum += (c.r + c.g + c.b) / 3.0;
                        sat += mx <= 0 ? 0 : (mx - mn) / mx;
                        n++;
                    }
                return n > 0;
            }

            // THE RECT IS THE WHOLE BODY INCLUDING WHAT IS BEHIND IT, and that
            // is the honest limitation rather than a bug to hide: a bounding
            // box around a person contains pavement. It biases both readings
            // the same way, which is why they are only ever compared with each
            // other and never against an absolute.
            var body = _game.Player.GetComponentInChildren<SkinnedMeshRenderer>();
            if (Average(body, out double pl, out double ps, out int pn))
            {
                _playerLum = pl / pn; _playerSat = ps / pn; _playerPixels = pn;
                // WHICH FRAME THIS IS, because the answer depends entirely on
                // it and two runs were compared as if it did not.
                //
                // `0eeee6d` read `bodyReadLum=35.7`, `f06075e` read `10.8`, and
                // nothing about how the player is measured changed between
                // them. Both are correct: this runs on every shot and the last
                // one wins, so one run's number came off a noon frame and the
                // other's off a night frame. Comparing them across runs was
                // comparing noon with midnight.
                //
                // The player and the crowd are still read at the SAME instant,
                // which is the comparison this probe exists for and is
                // unaffected. What was missing is the label that says a
                // cross-run comparison is not on offer.
                _bodyReadWhen = _lastShotName;
            }
            // ONE PERSON IS NOT A CROWD, AND A PIXEL-WEIGHTED MEAN MAKES IT ONE.
            //
            // This summed every sampled NPC's pixels and divided by the TOTAL
            // pixel count, so a body near the camera — whose bounding box is
            // twenty times the area of one down the street — set the "crowd"
            // reading almost by itself. The first run read `crowdRead=3`, and
            // three bodies weighted like that is one body with two witnesses.
            //
            // That is the corpus diagnostic again: it read sixty consecutive
            // rows of a speaker-ordered set and reported on "the corpus",
            // having seen one person. Same instrument fault, different data.
            //
            // So each body contributes ONE reading, the readings are kept, and
            // the comparison is against their MEDIAN. A median because the
            // question is "does the player sit among the clothed people" and a
            // mean can be dragged out of the crowd by one bright shellsuit —
            // the same reason the AO ceiling stopped reading a maximum.
            //
            // AND THE SERIES IS PRINTED. Two collapsed numbers cannot say
            // whether a 0.19 saturation gap is the player being unusual or the
            // crowd being spread from 0.3 to 0.9; only the spread can, and no
            // bound goes anywhere near this until it has been read (rule 2).
            _crowdReadings.Clear();
            int considered = 0;
            if (_npcs != null)
                foreach (var n in _npcs)
                {
                    if (n == null) continue;
                    considered++;
                    if (_crowdReadings.Count >= 24) break;
                    var rr = n.GetComponentInChildren<Renderer>();
                    if (!Average(rr, out double l, out double sa, out int c)) continue;
                    _crowdReadings.Add(new Vector2((float)(l / c), (float)(sa / c)));
                }
            _crowdConsidered = considered;

            // HOW MANY DIFFERENT PEOPLE THE TWELVE FACES ACTUALLY ARE.
            //
            // The roadmap has said "ten models dress forty-three named people,
            // so at least two on screen always share one" for two days, and the
            // noon still shows it — two women in the same trousers with the
            // same hair, one of them the player. Nothing measured it.
            // `bodyChoices=10` counts models that EXIST, which is a different
            // question and has been standing in for this one.
            //
            // OVER THE BODIES THE LOD GRANTED, not over what is in shot. That
            // set is the nearest twelve by construction, so it is both the
            // people you can see and the people the sameness matters for — and
            // it needs no frustum test, which is the reading that has been
            // wrong twice in this file already.
            //
            // BOTH NUMBERS FROM ONE PASS. A distinct-model count taken on one
            // frame and a body count taken on another is the fault CLAUDE.md
            // lists four times over: the worst instant for the numerator is not
            // the worst instant for the denominator. They are appended as a
            // pair and read as a pair.
            if (_npcs != null)
            {
                var models = new HashSet<string>();
                int withBody = 0;
                foreach (var n in _npcs)
                {
                    if (n == null || !n.HasRealBody) continue;
                    withBody++;
                    models.Add(RealBody.ModelNameFor(n.DisplayName));
                }
                if (withBody > 0) _modelSamples.Add(new Vector2Int(withBody, models.Count));
            }
            if (_crowdReadings.Count > 0)
            {
                var lums = new List<float>();
                var sats = new List<float>();
                foreach (var v in _crowdReadings) { lums.Add(v.x); sats.Add(v.y); }
                lums.Sort(); sats.Sort();
                _crowdLum = lums[lums.Count / 2];
                _crowdSat = sats[sats.Count / 2];
                _crowdLumRange = $"{lums[0]:0.00}..{lums[lums.Count - 1]:0.00}";
                _crowdSatRange = $"{sats[0]:0.00}..{sats[sats.Count - 1]:0.00}";
                _crowdSampled = _crowdReadings.Count;

                // WHERE THE PLAYER SITS IN THE QUEUE, which is the only
                // reading that separates the two live hypotheses.
                //
                // At night the player reads 11.9 against a crowd MEDIAN of 2.8
                // — four times brighter, which looks damning. The crowd's own
                // range is 1.50 to 11.75, so the player is level with its
                // brightest member and not above it, and the range spans eight
                // times. That is a spread lighting POSITION can produce all by
                // itself: this camera follows the player, and the player is
                // usually the one standing under the lamp.
                //
                // The albedo difference is real and deliberate — `Wardrobe`
                // caps the crowd at value 0.46 and the coat lift takes the
                // player to 0.68, 1.48x — but 1.48 does not explain 4.25, so
                // something else is doing most of the work and a palette change
                // would be a fix aimed at the smaller term.
                //
                // A RANK ANSWERS IT AND A RATIO CANNOT. Top of eleven on every
                // night frame is a property of the player; bouncing around the
                // order is a property of where they happened to stand. One
                // number, and it needs no threshold — which is the point,
                // because inventing one here is what rule 2 forbids.
                // "6/6", NOT "7/6". The first version printed the player's
                // POSITION in a list they are not in, so being brighter than
                // all six bodies came out as `7/6` — a number that reads as an
                // off-by-one and would be dismissed as one. It was the correct
                // answer in a notation that cannot express it.
                //
                // How many of the crowd the player outshines, out of how many
                // there were. Unambiguous at both ends: 0/6 is the darkest
                // thing on the street, 6/6 is the brightest.
                int below = 0;
                foreach (var l in lums) if (l < _playerLum) below++;
                _bodyReadRank = $"{below}/{lums.Count}";

                // AND ACROSS EVERY SHOT, BECAUSE ONE FRAME IS NOT A SAMPLE.
                //
                // `crowdRead` has now come back as 24, 11 and 6 on three green
                // runs, and the median moved with it: 19.5, 2.8, 3.0. With six
                // bodies a median is barely a statistic, and I have twice drawn
                // a conclusion about the player's brightness from one — first
                // "comfortably inside the crowd's spread", then "the brightest
                // body on the street", and the second reversed the first.
                //
                // Both readings were honest arithmetic on a sample too small
                // and too variable to carry them. The instrument was answering
                // a question about ONE FRAME while being read as a question
                // about the game — which is the same fault as the bubble
                // series taking two samples in seventeen days, repaired here
                // the same way and one probe later.
                //
                // Each shot contributes its own outshone-fraction, so the run
                // reports how often the player is the brightest thing rather
                // than whether they were in one photograph.
                if (lums.Count > 0) _bodyOutshone.Add((float)below / lums.Count);
            }
        }

        /// The measured value of every distinct albedo the wash runs over,
        /// sorted, against the wardrobe's ceiling so the two are readable
        /// together rather than in two places.
        ///
        /// "not measured" and an empty list are different findings — the blit
        /// chain can fail on a runner with no GPU, and a silent empty would
        /// read as "the textures are black", which is the confusion that made
        /// `WashFromWhite` return -1 rather than 0.
        ///
        /// AND IF EVERY VALUE COMES BACK 0.00, SUSPECT THE INSTRUMENT FIRST.
        /// A `Graphics.Blit` chain on a device that is not really rendering
        /// produces black, and black albedos would send somebody at exactly the
        /// wrong conclusion — the noon still shows bright yellow trousers, so a
        /// city of value-zero textures is disproved by a picture before it is
        /// disproved by anything else. Rule 3, written down here because this
        /// reading's failure mode looks like a finding rather than an error.
        static string AlbedoRead()
        {
            var xs = RealBody.AlbedoValues;
            if (xs.Count == 0) return "not measured";
            var c = new List<float>(xs);
            c.Sort();
            var sb = new StringBuilder();
            for (int i = 0; i < c.Count && i < 16; i++)
            {
                if (i > 0) sb.Append(' ');
                sb.Append(c[i].ToString("0.00"));
            }
            if (c.Count > 16) sb.Append($" (+{c.Count - 16} more)");
            sb.Append($" vs wardrobe max {Ledger.Core.Wardrobe.MaxValue:0.00}");
            return sb.ToString();
        }

        /// HOW DEEP INTO THE ROAD THE STUCK CLUTTER'S OWN WALLS STAND.
        ///
        /// THE WHOLE SERIES, not a summary, and eight numbers is short enough
        /// to just print. This is the reading that decides whether the level
        /// fix is a kerb width or a street — and every summary of it answers a
        /// different question than the one being asked. A median would hide one
        /// facade standing in a lane; a maximum would make eight items look
        /// like a catastrophe when seven are a hand's width over a kerb.
        ///
        /// The words when it is empty say which empty it is: nothing stuck is
        /// the good outcome and no clutter measured is a broken probe, and
        /// `dressedInRoad` beside it is the denominator that tells them apart.
        static string RoadDepthRead()
        {
            var xs = WorldBuilder.DressedRoadDepth;
            if (xs.Count == 0) return "none stuck";
            var c = new List<float>(xs);
            c.Sort();
            var sb = new StringBuilder();
            for (int i = 0; i < c.Count && i < 24; i++)
            {
                if (i > 0) sb.Append(' ');
                sb.Append(c[i].ToString("0.00"));
            }
            if (c.Count > 24) sb.Append($" (+{c.Count - 24} more)");
            return sb.ToString();
        }

        /// -1 for "nothing sampled", never 0, because zero distinct models and
        /// no samples at all are opposite findings and they read identically.
        int ModelMedian(System.Func<Vector2Int, int> pick)
        {
            if (_modelSamples.Count == 0) return -1;
            var xs = new List<int>();
            foreach (var v in _modelSamples) xs.Add(pick(v));
            xs.Sort();
            return xs[xs.Count / 2];
        }

        /// The busiest sample's pair, printed together because they were taken
        /// together — `4/12` is four distinct models among twelve bodies.
        string ModelAtMost()
        {
            if (_modelSamples.Count == 0) return "nothing sampled";
            var best = _modelSamples[0];
            foreach (var v in _modelSamples) if (v.x > best.x) best = v;
            return $"{best.y}/{best.x}";
        }

        /// (bodies near, distinct models among them), one entry per sample.
        /// Kept rather than collapsed so the median and the busiest sample can
        /// both be read — a peak answers "did it ever get duplicated" and a
        /// median answers "is this how the street looks", and this needs the
        /// second one with the first beside it.
        readonly List<Vector2Int> _modelSamples = new List<Vector2Int>();

        /// The biggest group standing within conversation distance of one
        /// another, one entry per sample. MEDIAN and WORST both printed: a
        /// street that huddles once is a scene and a street that huddles always
        /// is a bug, and one number cannot tell those apart.
        readonly List<int> _huddles = new List<int>();
        /// What the worst huddle was DOING at the instant it was worst — see
        /// `SampleCrowding`. `_huddleWorstSeen` is the peak these were taken
        /// at, printed with them so a breakdown can never be read against a
        /// huddle it did not come from.
        int _huddleWorstSeen;
        int _huddleTalking, _huddleEscorting, _huddleDetour, _huddleWaiting;
        int _huddleStanding, _huddleMoving;
        /// Distinct scheduled place cells among the huddle's members. 1 means
        /// the ring is undersized; many means the rings overlap and the radius
        /// wants sizing from the neighbourhood rather than the cell.
        int _huddleCells;
        string _huddleWhere = "nowhere";

        int HuddleMedian()
        {
            if (_huddles.Count == 0) return -1;
            var c2 = new List<int>(_huddles);
            c2.Sort();
            return c2[c2.Count / 2];
        }

        int HuddleWorst()
        {
            int w = -1;
            foreach (var h in _huddles) if (h > w) w = h;
            return w;
        }

        /// The window counts as they stood when the NIGHT STILL was taken,
        /// with the hour beside them — because the live counters are rewritten
        /// every game hour and the picture is not.
        int _windowsLitAtShot = -1, _windowsShopAtShot = -1;
        int _windowsShopLitAtShot = -1, _windowsHourAtShot = -1;

        double _playerLum = -1, _playerSat = -1, _crowdLum = -1, _crowdSat = -1;
        int _playerPixels, _crowdSampled, _crowdConsidered;
        string _crowdLumRange = "none", _crowdSatRange = "none";
        /// Which committed frame the body/crowd reading came off. See the note
        /// where it is set: without it, two runs' numbers look comparable and
        /// are noon against midnight.
        string _bodyReadWhen = "none";
        /// The player's place in the crowd's brightness order at that instant,
        /// e.g. "11/11". A rank rather than a ratio, because a ratio against a
        /// median cannot tell "this body is bright" from "this body is standing
        /// under the only lamp".
        string _bodyReadRank = "none";
        /// The outshone-fraction from every shot, so the run answers "how often
        /// is the player the brightest body" rather than "were they in this
        /// one photograph".
        readonly List<float> _bodyOutshone = new List<float>();

        /// Typical share of the crowd the player outshines. -1 when never
        /// sampled — outshining nobody is a real and welcome reading.
        double BodyOutshoneMedian
        {
            get
            {
                if (_bodyOutshone.Count == 0) return -1;
                var v = new List<float>(_bodyOutshone);
                v.Sort();
                return v[v.Count / 2];
            }
        }
        /// One reading per body — x is luminance, y is saturation. Kept rather
        /// than folded so the spread can be printed beside the median.
        readonly List<Vector2> _crowdReadings = new List<Vector2>();

        /// The player's own pose, swept. See the note beside where it is read.
        bool _playerPoseSeen;
        float _playerPoseMin, _playerPoseMax;
        double PlayerPoseRange => _playerPoseSeen ? _playerPoseMax - _playerPoseMin : 0.0;

        /// How many pairs of world-space NAMES overlap on screen right now.
        ///
        /// FOUND IN A STILL, MEASURED HERE. `review_day1_night.jpg` has "Ivan
        /// Loveric" and "Katarina" printed across each other, and neither is
        /// readable. Every existing glyph check passed on that frame and all of
        /// them were right: the labels exist, have a font, and lay out a
        /// non-zero width. None of them asks whether two of them are in the same
        /// place — which is the difference between "text rendered" and "text you
        /// can read", and the second is the only one a player cares about.
        ///
        /// REPORTED, NOT GATED, and deliberately so. A crowd will sometimes put
        /// two people in a line from the camera, and there is no such thing as
        /// zero overlaps in a city — a gate at zero would be unsatisfiable and a
        /// gate at any other number is a threshold nobody has measured. So this
        /// prints the count and the count becomes the evidence, exactly as the
        /// AO round series did.
        ///
        /// Screen-space AABBs from the text's own bounds, not world distance:
        /// two names three metres apart in depth collide on screen and two names
        /// three metres apart across the view do not.
        /// IS THIS IN *THIS* CAMERA'S VIEW — which `Renderer.isVisible` does not
        /// answer, and the miss cost three readings of the name heap.
        ///
        /// `isVisible` is "was rendered by ANY camera during the last frame".
        /// A comment in this file called it a frustum test; it is not, and the
        /// difference is the whole fault. `CollidingNames` measures against the
        /// REVIEW camera at shot time, and the review camera has not rendered
        /// yet when the measurement is taken — so every label only IT can see
        /// reads as invisible, and the player camera cannot see them because it
        /// is somewhere else.
        ///
        /// MEASURED, and the numbers are not subtle: `textWalked=391
        /// textInvisible=260 textProjected=95 namesTracked=1`, taken on a run
        /// whose day-2 noon still has a dozen names piled illegibly in the
        /// bottom-right corner. Two thirds of the text in the frame was thrown
        /// away before anything looked at it, which is why three separate
        /// readings of this metric said the declutter had nothing to declutter.
        ///
        /// `TestPlanesAABB` asks the question that was meant: is this bounds
        /// inside the frustum of the camera I am measuring for. It needs no
        /// render to have happened and it cannot answer about a different
        /// camera.
        public static bool InView(Camera cam, Renderer r) =>
            cam != null && r != null
            && GeometryUtility.TestPlanesAABB(
                   GeometryUtility.CalculateFrustumPlanes(cam), r.bounds);

        int CollidingNames()
        {
            var cam = Camera.main;
            if (cam == null) return -1;
            var boxes = new List<Rect>();
            var other = new List<Rect>();
            var otherText = new List<string>();
            var boxText = new List<string>();
            var bubbles = new List<Rect>();
            // WHICH FILTER ATE THEM, because 392 walked and 92 projected leaves
            // three hundred unaccounted for and no way to tell which gate they
            // fell through.
            //
            // The night still shows PEOPLE'S NAMES — "Marla", "Sam" — rendered
            // large, while `namesTracked` peaks at 0 and says the declutter
            // tracked none of them. Those cannot both describe a working
            // instrument, and I have now spent three readings inferring which
            // one is wrong instead of asking. Every rejection is counted at the
            // line that makes it, so the next verdict names the gate rather
            // than leaving it to be deduced.
            int walked = 0, noText = 0, invisible = 0, noRect = 0;
            int managedSeen = 0, managedCulled = 0, personLabels = 0;
            int labelsManaged = 0, labelsOrphan = 0;
            foreach (var t in FindObjectsByType<TextMesh>(FindObjectsSortMode.None))
            {
                walked++;
                if (t == null || string.IsNullOrEmpty(t.text)) { noText++; continue; }
                // MANAGED, COUNTED BEFORE THE VISIBILITY CULL.
                //
                // `namesTracked=0` beside `worldTextTracked=102` says the
                // managed bucket was empty while a hundred and two world labels
                // were in shot, and `namesManagedEver=124 namesManagedDead=81`
                // says forty-three managed labels were alive at the time. Those
                // cannot all be true of a working instrument, and the two
                // explanations want opposite work: either `Manages` is asking
                // about a set that does not contain these objects — the
                // id-space mismatch this project has now found five times — or
                // the managed labels are simply being culled by `InView` and
                // are sitting inside `textInvisible=304`.
                //
                // The cull is three lines below, so every count taken after it
                // is blind to the difference. This one is taken before it.
                // `namesManagedSeen` against `namesTracked` is the whole split:
                // equal means the cull is innocent and the bucket is honestly
                // empty; much larger means the labels ARE managed and the
                // frustum test is throwing them away.
                //
                // It matters because `collidingNames=0` has been read three
                // times as "the declutter has nothing to declutter" while the
                // night stills show six people's names in a heap, and a gate
                // reading an empty bucket cannot go red however bad the frame.
                bool managed = NameTags.Manages(t);
                if (managed) managedSeen++;
                // AND WHETHER IT IS A PERSON'S LABEL AT ALL.
                //
                // `namesManagedSeen=0` across 405 walked meshes, with the cull
                // innocent at `namesManagedCulled=0` — so `Manages` recognised
                // nothing. Two readings survive that and they are miles apart:
                // either the managed set genuinely does not contain these
                // objects, or NO WALKER LABEL WAS PRESENT when this ran, in
                // which case the 405 are street plates and bubbles and the
                // measurement has simply never coincided with the frames that
                // show names in a heap.
                //
                // `FindObjectsByType` skips inactive objects and a walker
                // deactivates its label out of range, so the second reading is
                // entirely possible and nothing here could see it. Owned by an
                // `NpcWalker` is the test — the same discriminator the lean
                // owner uses — and `textPersonLabels=0` beside `walked=405`
                // means this loop and the still are looking at different
                // moments, which is a different fault from a broken set.
                if (t.GetComponentInParent<NpcWalker>() != null)
                {
                    personLabels++;
                    // THE REFERENCE-MISMATCH COUNTER: 8869d28 walked 15
                    // labels and `managedSeen` stayed 0, so either these
                    // exact TextMeshes were never Offered or the managed
                    // set holds different objects for the same people —
                    // recreation, the fork the heap item has carried for
                    // days. In/out counts plus one orphan's TEXT (a name
                    // a human can find in the cast list) settle it.
                    if (NameTags.Manages(t)) labelsManaged++;
                    else
                    {
                        labelsOrphan++;
                        if (_labelOrphanText == "none")
                            _labelOrphanText = t.text;
                    }
                }
                // AND WHAT THE WALKED MESHES ARE, BY NAME — because
                // `textPersonLabels=0` beside `nameTagsActive=43` in one
                // verdict means one of two moments is lying, and a census
                // of object names settles it in one build: if no "Label"
                // appears among the walked names, the walk really does run
                // in moments where every walker label is switched off, and
                // the heap in the stills belongs to some other object.
                // BY PREFIX, not full name — street plates are uniquely
                // named (NamePlate_j4_0_ew_text_180) and a per-name dict
                // put count 1 beside count 1 for four hundred of them,
                // which made the first census's top-4 nearly useless.
                var kind = t.gameObject.name;
                int cut = kind.IndexOf('_');
                if (cut > 0) kind = kind.Substring(0, cut);
                int have;
                _textWalkKinds.TryGetValue(kind, out have);
                _textWalkKinds[kind] = have + 1;
                var r = t.GetComponent<Renderer>();
                if (r == null || !InView(cam, r)) { invisible++; if (managed) managedCulled++; continue; }
                // THE SAME PROJECTION THE DECLUTTER USES. A gate and the thing
                // it gates must agree about what "overlapping" means, or the
                // gate measures its own opinion — which is how a control came to
                // assert behaviour the router had reasoned its way out of.
                if (!NameTags.ScreenRect(cam, r.bounds, out var rect)) { noRect++; continue; }
                // ONLY THE LABELS SOMETHING IS RESPONSIBLE FOR.
                //
                // This counted EVERY TextMesh in the scene and reported 182
                // overlapping pairs, which was quoted for hours as the
                // nameplate wall. The city is full of street plates, shop
                // fascias and bark bubbles, and two street plates overlapping
                // at a junction is what a junction looks like — nothing
                // declutters those and nothing should.
                //
                // It is the same fault as `worstTextHeightFrac=0.210`, which
                // was diagnosed in NameTags.cs and fixed there while this
                // identical loop sat one file away doing it again. Split
                // rather than filtered, so world text keeps being counted and
                // stops being blamed on the declutter.
                // THREE BUCKETS, BECAUSE A PICTURE FOUND A THIRD THING.
                //
                // `review_day1_night.jpg` has two speech bubbles drawn over
                // each other on the right-hand side — "Ask me agai…are.
                // Th…ear … the" — which is unreadable and is nobody's fault but
                // tonight's: the junction fix took confabs from 7 a run to 56,
                // and fifty-six conversations is fifty-six bubbles.
                //
                // `collidingWorldText` already counted it and could not say so,
                // because it lumps bubbles in with street plates and shop
                // fascias — and plates overlapping at a junction is a junction.
                // A number that cannot tell a fault from a feature is the
                // scope mistake this metric was split to fix, one level down.
                //
                // Counted before it is decluttered, deliberately. Rule 4: a
                // picture is excellent evidence that something is WRONG and
                // poor evidence of what — so the run reports how many bubbles
                // actually overlap, and the bound comes off that series rather
                // than off one JPEG at midnight.
                var bucket = NameTags.Manages(t) ? boxes
                           : t.GetComponentInParent<SpeechBubble>() != null ? bubbles
                           : other;
                bucket.Add(rect);
                // AND WHAT IT SAYS, for the world-text bucket only.
                //
                // `review_day5_night.jpg` has six PERSON names — Bruno, Dario,
                // Zora, Petra, Fabjan, Mitch — piled on top of each other in
                // the corner, illegible. `collidingNames` read 1, and it is a
                // peak sampled on the photographed frame, so it is not a
                // stale reading: those labels are not ones `NameTags` manages,
                // and they landed in this bucket alongside street plates.
                //
                // Which matters because the two have OPPOSITE verdicts. Street
                // plates overlapping at a junction is what a junction looks
                // like and nothing should declutter it; six people's names in
                // a heap is the declutter not being offered them at all. The
                // count cannot tell those apart and neither can I from here,
                // so the run says WHAT OVERLAPPED rather than how much.
                if (bucket == other) otherText.Add(t.text);
                else if (bucket == boxes) boxText.Add(t.text);
            }
            // THE MANAGED BUCKET GETS NAMED TOO, because three night stills in
            // a row show PEOPLE'S names in an illegible heap — Bruno/Dario/
            // Zora, then Ines/Tanja, then Iva/Marla/Kata — while
            // `collidingNames` reads 0 or 1 and `worstWorldPair` keeps coming
            // back street furniture.
            //
            // Two explanations survive and a count cannot separate them:
            // either those labels are not ones `NameTags` manages, so they sit
            // in the world-text bucket beside the shop fascias, or they are
            // managed and their projected rects genuinely do not overlap while
            // looking as though they do. Naming the worst pair on each side,
            // with how many labels are in each, settles it in one build.
            int pairs = 0;
            for (int i = 0; i < boxes.Count; i++)
                for (int j = i + 1; j < boxes.Count; j++)
                    if (boxes[i].Overlaps(boxes[j]))
                    {
                        pairs++;
                        var bl = Rect.MinMaxRect(
                            Mathf.Max(boxes[i].xMin, boxes[j].xMin),
                            Mathf.Max(boxes[i].yMin, boxes[j].yMin),
                            Mathf.Min(boxes[i].xMax, boxes[j].xMax),
                            Mathf.Min(boxes[i].yMax, boxes[j].yMax));
                        float ba = Mathf.Max(0f, bl.width) * Mathf.Max(0f, bl.height);
                        if (ba > _worstNameArea && i < boxText.Count && j < boxText.Count)
                        {
                            _worstNameArea = ba;
                            _worstNamePair = Trim(boxText[i]) + "|" + Trim(boxText[j]);
                            _namesAtWorstName = boxes.Count;
                        }
                    }
            // PEAKS, NOT LAST-WINS, and I published a conclusion off the
            // last-wins version within the hour.
            //
            // `CollidingNames` runs on EVERY shot, and these were assigned
            // fresh each call — so they described whichever shot happened to
            // run last, which is not the shot with the name heap in it. I read
            // `namesTracked=2 worldTextTracked=92` off one arbitrary frame and
            // wrote "the declutter manages two labels" into the queue as
            // DECISIVE. It was one instant, again, for the third time today.
            //
            // A peak answers "how many were ever on screen at once", which is
            // the question the heap poses. `namesAtWorstName` is the
            // same-instant denominator for the overlap pair above, which is
            // the other question and needs its own number.
            if (boxes.Count > _namesTracked) _namesTracked = boxes.Count;
            if (other.Count > _worldTextTracked) _worldTextTracked = other.Count;
            if (bubbles.Count > _bubblesTracked) _bubblesTracked = bubbles.Count;
            // AND THE DENOMINATOR, BECAUSE `namesTracked=0` IS A ZERO WITHOUT
            // ONE AND RULE 3b IS ABOUT EXACTLY THIS.
            //
            // The peak has now read 0 over a whole run while `nameTagsActive`
            // and `nameTagsOffered` both peaked at 43. Those cannot both
            // describe a working instrument, and the zero is consistent with
            // three different worlds: no TextMesh survived the visibility and
            // projection filters at all; they survived and none was one this
            // class manages; or none was ever offered in the first place.
            //
            // `textWalked` is what the scene walk saw, `textProjected` is what
            // got past both filters, and `namesManagedEver` is how many labels
            // have EVER been offered over the run — a lifetime figure against
            // three per-call ones, deliberately, because it is the only one
            // that can say whether the offer path runs at all. Between them
            // there is nothing left to infer.
            // PEAKS, LIKE THE BUCKET COUNTS THEY ARE PRINTED BESIDE.
            //
            // These were LAST-WINS while `namesTracked`, `worldTextTracked` and
            // `bubblesTracked` three lines up are peaks, so the verdict printed
            // a peak and four last-wins values side by side as if they described
            // one moment. Consecutive runs swung `textProjected` 111 to 48 and
            // `textInvisible` 277 to 346 — not because anything changed, but
            // because the last shot happened to be pointed somewhere else.
            //
            // That is the same fault as the cumulative-count-on-a-sparse-sampler
            // one fixed an hour ago, in the numbers printed immediately beside
            // it, which is rule 1's third corollary exactly: one idea, two
            // implementations, and the one nobody looked at is the one missing
            // a line.
            if (walked > _textWalked) _textWalked = walked;
            if (noText > _textNoText) _textNoText = noText;
            if (invisible > _textInvisible) _textInvisible = invisible;
            if (noRect > _textNoRect) _textNoRect = noRect;
            // TAKEN AT THE SAME CALL AS EACH OTHER, not as independent peaks.
            // Two maxima cannot be subtracted any more than they can be
            // divided, and `seen` minus `culled` is the number that matters —
            // so the pair is replaced together, on the call with the most
            // managed labels seen, or they would describe two different shots.
            if (managedSeen > _namesManagedSeen)
            {
                _namesManagedSeen = managedSeen;
                _namesManagedCulled = managedCulled;
            }
            if (personLabels > _textPersonLabels) _textPersonLabels = personLabels;
            if (labelsOrphan > _labelsOrphan)
            {
                _labelsOrphan = labelsOrphan;
                _labelsManagedAtOrphan = labelsManaged;
            }
            // The denominator on its own peak: orphan=0 alone cannot tell
            // "every walked label was managed" from "no label was walked",
            // and the first reading of this counter was ambiguous exactly
            // that way (459b940).
            if (labelsManaged > _labelsManagedPeak)
                _labelsManagedPeak = labelsManaged;
            int projected = boxes.Count + other.Count + bubbles.Count;
            if (projected > _textProjected) _textProjected = projected;
            // NOT CAPTURED HERE ANY MORE — see the done-line. This ran inside
            // `CollidingNames`, which fires only on shots, so it froze the
            // lifetime count at the LAST SHOT while `nameTagsOffered` kept
            // peaking over the whole run. The two then disagreed impossibly:
            // 44 labels offered in a single frame against 28 ever managed,
            // when every offer adds to the managed set.
            //
            // Two numbers taken at different instants and printed side by side,
            // in a field added this morning to stop exactly that — the rule
            // says the number most likely to be wrong is the one you wrote an
            // hour ago, and it was.
            // RESET WITH THE COUNT IT IS PRINTED BESIDE. `_collidingWorldText`
            // is per-call and the done-line shows the last call's value, so a
            // pair kept from an earlier call would describe a different frame
            // from the number next to it — the two-maxima fault in miniature.
            _collidingWorldText = 0;
            _worstWorldPair = "none";
            _worstWorldArea = 0f;
            _worstNamePair = "none";
            _worstNameArea = 0f;
            for (int i = 0; i < other.Count; i++)
                for (int j = i + 1; j < other.Count; j++)
                    if (other[i].Overlaps(other[j]))
                    {
                        _collidingWorldText++;
                        // THE WORST PAIR BY OVERLAP AREA, and the first
                        // version of this recorded the FIRST pair while being
                        // called `worstWorldPair`.
                        //
                        // That is rule 2's "a number keeps its name when the
                        // question it answers moves", committed three hours
                        // after I wrote the rule down — except here the name
                        // was wrong on arrival. It came back
                        // [Copper Row|Market Road], which is true, is two
                        // street plates, and settles nothing about the heap of
                        // PEOPLE'S names in the frame: first-found says
                        // nothing about worst-looking.
                        //
                        // Area, because that is what makes text unreadable. A
                        // pair clipping at the corner is a junction; a pair
                        // sitting on top of each other is the fault.
                        var lap = Rect.MinMaxRect(
                            Mathf.Max(other[i].xMin, other[j].xMin),
                            Mathf.Max(other[i].yMin, other[j].yMin),
                            Mathf.Min(other[i].xMax, other[j].xMax),
                            Mathf.Min(other[i].yMax, other[j].yMax));
                        float area = Mathf.Max(0f, lap.width) * Mathf.Max(0f, lap.height);
                        if (area > _worstWorldArea && i < otherText.Count && j < otherText.Count)
                        {
                            _worstWorldArea = area;
                            _worstWorldPair = Trim(otherText[i]) + "|" + Trim(otherText[j]);
                        }
                    }
            // PEAKS, BECAUSE THE FIRST READING WAS A MOMENT AND THE QUESTION
            // IS ABOUT THE RUN.
            //
            // It came back `bubblesOnScreen=0 collidingBubbles=0` while the
            // night still plainly shows two bubbles drawn through each other.
            // Both are true: this counter is sampled once, on a frame when
            // nobody happened to be talking, and a speech bubble lives for a
            // few seconds. So the instrument was answering a question about a
            // different instant from the one in the picture — which is exactly
            // how `nameTagsOffered=2` once printed beside a still with a dozen
            // names in it.
            //
            // A peak, like every other "how bad did it get" number on this
            // line. Zero now means it never happened, rather than that it was
            // not happening when somebody looked.
            int now = 0;
            for (int i = 0; i < bubbles.Count; i++)
                for (int j = i + 1; j < bubbles.Count; j++)
                    if (bubbles[i].Overlaps(bubbles[j])) now++;
            // TWO PEAKS FROM POSSIBLY DIFFERENT INSTANTS CANNOT BE DIVIDED,
            // and I tried to divide them.
            //
            // Before bubble stacking: `collidingBubbles=15 bubblesOnScreen=6` —
            // six bubbles have exactly fifteen pairs, so every pair overlapped.
            // After: `91` and `16`, which is 76% of 120 pairs and looks like an
            // improvement. It may be. It cannot be READ as one, because these
            // are independent maxima: the worst overlap instant and the busiest
            // instant need not be the same frame, so the denominator does not
            // belong to the numerator.
            //
            // That is the same fault as every "peak beside a peak" this file
            // has already fixed once, committed by me while fixing one of them.
            // The count at the moment of the WORST overlap is the only
            // denominator that means anything, so it is captured with it.
            if (now > _collidingBubbles)
            {
                _collidingBubbles = now;
                _bubblesAtWorst = bubbles.Count;
            }
            if (bubbles.Count > _bubblesOnScreen) _bubblesOnScreen = bubbles.Count;

            // AND THE PEAK CANNOT ANSWER THE QUESTION ANYWAY. THREE RUNS SAID
            // 91, 16 AND 116.
            //
            // Fixing the denominator was right and did not make the number
            // readable, because `collidingBubbles` is a MAXIMUM and the thing
            // it is being asked is "are speech bubbles legible on this street".
            // A maximum answers "did they ever pile up" — and it rises with
            // sampling, with the day's talkativeness, and with anything that
            // puts a crowd in shot. Sixteen on one run and a hundred and
            // sixteen on the next is not the declutter getting eight times
            // worse; it is a statistic that cannot tell those apart.
            //
            // That is the AO ceiling exactly: a bound placed on a maximum,
            // which maximises the quantity the bound exists to keep small, so
            // more rounds made it trip on itself. One run read 80% and the
            // round series read a median of 23.
            //
            // So the FRACTION, per sample, kept as a series — what share of
            // the pairs that COULD overlap actually do, at each instant where
            // there were at least two bubbles to overlap. The median of that
            // is the street as it typically reads, the peak beside it is still
            // the worst moment, and the two answer different questions on
            // purpose. No bound until the series exists (rule 2).
            if (bubbles.Count >= 2)
            {
                int couldPair = bubbles.Count * (bubbles.Count - 1) / 2;
                _bubbleOverlap.Add((float)now / couldPair);
            }
            return pairs;
        }

        int _collidingWorldText = -1;
        /// The first overlapping pair of world-text labels on a photographed
        /// frame, as "a|b". Says whether a heap of overlapping text is street
        /// furniture (a junction, and correct) or people's names (the
        /// declutter never being offered them) — see `CollidingNames`.
        string _worstWorldPair = "none";
        /// Overlap area of the pair above, so "worst" means worst.
        float _worstWorldArea;
        /// The worst overlapping pair among the labels NameTags MANAGES,
        /// and how many labels are in each bucket. Without the sizes, a
        /// zero here cannot be told from an empty bucket.
        string _worstNamePair = "none";
        float _worstNameArea;
        int _namesTracked = -1, _worldTextTracked = -1, _bubblesTracked = -1;
        /// The three denominators `namesTracked=0` needed and did not have —
        /// what the scene walk saw, what survived the filters, and how many
        /// labels have ever been offered to the declutter at all.
        int _textWalked = -1, _textProjected = -1;

        /// Managed labels seen by the text walk, and how many of those the
        /// visibility cull removed. Both from the SAME call — see where they
        /// are assigned. `-1` is "the walk never ran", which is a third answer
        /// neither zero can give.
        int _namesManagedSeen = -1, _namesManagedCulled = -1;

        /// Walked TextMeshes owned by a walker — a person's name rather than a
        /// street plate or a bubble. The denominator `namesManagedSeen` needs
        /// before a zero there can mean anything.
        int _textPersonLabels = -1;
        int _labelsOrphan;
        int _labelsManagedAtOrphan;
        int _labelsManagedPeak;
        string _labelOrphanText = "none";
        /// What the text walk's meshes ARE, by object name, accumulated
        /// over every walk — the census that says whether a walker label
        /// has EVER been walked, which two peak counters from different
        /// moments could not.
        readonly Dictionary<string, int> _textWalkKinds =
            new Dictionary<string, int>();
        string TextWalkKindsTop()
        {
            var pairs = new List<KeyValuePair<string, int>>(_textWalkKinds);
            pairs.Sort((x, y) => y.Value.CompareTo(x.Value));
            var top = new List<string>();
            for (int i = 0; i < pairs.Count && i < 4; i++)
                top.Add(pairs[i].Key + ":" + pairs[i].Value);
            return top.Count > 0 ? string.Join("/", top.ToArray()) : "none";
        }
        /// The three rejections, so `walked` and `projected` add up. A gap
        /// between two counts with nothing naming it is an invitation to guess,
        /// and the last three readings of this metric were guesses.
        int _textNoText = -1, _textInvisible = -1, _textNoRect = -1;
        /// How many managed labels were on screen AT the worst overlap —
        /// the denominator from the same instant as its numerator, which
        /// this file has now shipped wrong six times.
        int _namesAtWorstName = -1;

        /// Labels are free text and this goes on a single-line done-line, so
        /// commas, newlines and length all have to go.
        static string Trim(string s)
        {
            if (string.IsNullOrEmpty(s)) return "empty";
            s = s.Replace("\n", " ").Replace("\r", " ").Replace(",", ";").Trim();
            return s.Length <= 18 ? s : s.Substring(0, 18);
        }
        int _collidingBubbles = 0, _bubblesOnScreen = 0;
        /// How many bubbles were on screen at the instant of the worst overlap.
        /// The overlap fraction, taken on the sim's own tick rather than only
        /// when something else happens to look.
        ///
        /// The first version rode on `CollidingNames`, which walks every
        /// TextMesh in the scene and therefore runs twice: once per audit and
        /// once per shot. `f06075e` came back with `n=2`, both zero, one run
        /// after a peak of 116 overlapping pairs — a series of two cannot
        /// describe a street, and the emptiness was the probe's, not the
        /// game's.
        ///
        /// It reuses `_bubbleOverlap`, so the peak and the median stay two
        /// readings of ONE quantity rather than two quantities with similar
        /// names.
        void SampleBubbles()
        {
            var cam = Camera.main;
            if (cam == null) return;
            int n = SpeechBubble.Rects(cam, _bubbleRects);
            if (n < 2) return;
            int now = 0;
            for (int i = 0; i < n; i++)
                for (int j = i + 1; j < n; j++)
                    if (_bubbleRects[i].Overlaps(_bubbleRects[j])) now++;
            _bubbleOverlap.Add((float)now / (n * (n - 1) / 2));
            if (now > _collidingBubbles) { _collidingBubbles = now; _bubblesAtWorst = n; }
            if (n > _bubblesOnScreen) _bubblesOnScreen = n;
        }

        /// Reused across ticks so the per-tick sample allocates nothing.
        readonly List<Rect> _bubbleRects = new List<Rect>();

        /// ARE THE PEOPLE STANDING INSIDE EACH OTHER.
        ///
        /// `review_day1_night` from `bc4c689` shows the dockside crowd as a
        /// stack: six or seven figures occupying one body's worth of pavement,
        /// layered rather than gathered. Every gate on that frame was green,
        /// and correctly — they all ask whether a system ADDED something, and
        /// none of them asks what the frame LOOKS like, which is the third
        /// time that exact sentence has been true this week.
        ///
        /// A grep confirms the cause rather than a guess about it: `NpcWalker`
        /// has no separation, no avoidance and no personal space at all. Two
        /// walkers heading for the same doorway occupy the same metre and
        /// nothing anywhere objects.
        ///
        /// MEASURED, NOT FIXED, and in that order for the usual reason. A
        /// crowd that never touches is as wrong as one that interpenetrates —
        /// people in a queue stand close — so the repair is a distance and I do
        /// not have one. This prints the series and the series decides it.
        ///
        /// 0.45m IS A BODY, NOT A THRESHOLD I PICKED. `bodiesOk` already
        /// measures these figures at 1.58m to 1.91m tall; a person that tall is
        /// roughly 0.45m across the shoulders, so two centres closer than that
        /// are inside one another by construction. It is a fact about the
        /// meshes rather than a number chosen to make a reading look good.
        ///
        /// AND IT STOPPED BEING ONE FACT THE MOMENT BODIES GAINED BREADTH.
        /// `Physique.Breadth` runs 0.86 to 1.18 and, as of 4 Aug, reaches the
        /// bought meshes as well as the boxes — so the widest person on the
        /// street is 0.53 across and the narrowest 0.39, and a single 0.45 is
        /// now an average wearing a fact's clothes. `crowdGapMedian=0.42` was
        /// read against a world where everybody was the same width.
        ///
        /// DELIBERATELY NOT CHANGED TO A PER-PAIR WIDTH YET, and the reason is
        /// rule 2 rather than laziness: this counts pairs over a whole run and
        /// a per-pair bound would change what the median MEANS as well as what
        /// it reads, so the next value would be incomparable with every value
        /// in the kept verdicts. The range is printed beside it instead —
        /// `crowdBodyWidth` says what the constant assumes and what the extremes
        /// actually are, on the same log line, so the first person to read
        /// `0.42` can see immediately that it clears a narrow person and does
        /// not clear a broad one.
        const float BodyWidth = (float)Ledger.Core.Physique.ShoulderWidth;

        /// What the crowding bound assumes against what the street now is.
        /// On the gap's own line, because two numbers from two lines are two
        /// readings — the mistake that cost 4 August an afternoon.
        /// NO SPACES IN A VALUE. The verdict is space-separated `key=value`
        /// and everything that reads it — `verdict-read.py`, `verdict-keys.py`,
        /// every grep anybody has ever typed at it — assumes that. This first
        /// emitted `0.45(narrowest 0.39 broadest 0.53)` and the reader duly
        /// returned `0.45(narrowest`, silently, which is the whole class of
        /// fault that tool was written to stop happening one layer down.
        static string CrowdWidthRead() =>
            $"{BodyWidth:0.00}/{BodyWidth * 0.86f:0.00}..{BodyWidth * 1.18f:0.00}";

        void SampleCrowding()
        {
            var cam = Camera.main;
            if (cam == null || _npcs == null) return;
            _crowdSeen.Clear();

            // THE BIGGEST HUDDLE, WHICH THE GAP MEDIAN CANNOT SEE.
            //
            // `review_day2_night` shows about thirty people standing in a
            // packed rectangular block, shoulder to shoulder — a queue, not a
            // street. `crowdGapMedian=0.41` is perfectly healthy on that frame,
            // because a median over PAIRS is dominated by the sixty people who
            // are nowhere near each other, and the huddle is a handful of pairs.
            // A statistic answering "is the street crowded on average" cannot
            // answer "is anybody standing in a mob", and I have spent five
            // builds tuning the first while the second was what the picture
            // showed.
            //
            // WITHIN TWO METRES, which is not a threshold about crowding: it is
            // `Acoustics`-scale conversation distance, the range at which these
            // people are modelled as being AT the same place. Anybody closer
            // than that is at the same place by the game's own definition, so
            // the count is "how many are at one place" rather than a bound I
            // picked.
            //
            // NO GATE ON IT. Nobody has read the series, and a huddle of six is
            // a bus stop while a huddle of thirty is a fault — the number that
            // separates them has to come from the runs (rule 2).
            int worstHuddle = 0;
            NpcWalker worstAt = null;
            for (int i = 0; i < _npcs.Length; i++)
            {
                var a0 = _npcs[i];
                if (a0 == null || !a0.isActiveAndEnabled) continue;
                int near = 1;
                for (int j = 0; j < _npcs.Length; j++)
                {
                    if (i == j) continue;
                    var b0 = _npcs[j];
                    if (b0 == null || !b0.isActiveAndEnabled) continue;
                    if ((a0.transform.position - b0.transform.position).sqrMagnitude <= 4f) near++;
                }
                if (near > worstHuddle) { worstHuddle = near; worstAt = a0; }
            }
            _huddles.Add(worstHuddle);

            // AND WHAT THE HUDDLE IS DOING, AT THE INSTANT IT IS WORST.
            //
            // `busiestNear=12` equals `busiestPlace=12` on 7c87f38 while
            // `crowdHuddleWorst=38`. Those are all run maxima, so they compare
            // fairly, and the plan is exonerated: the schedules never put more
            // than twelve people within two metres of each other and
            // thirty-eight end up there. The cause is in the WALK, and nothing
            // measures which part of the walk.
            //
            // `review_day5_noon` shows the mob standing at a road junction —
            // which is the shape of a specific suspect. `confabs` read 1-13
            // under the old flat-road conversation rule and 29-74 under the
            // JUNCTION one; if the huddle is people who stopped to talk, this
            // is the conversation system gathering them and not the pathing.
            //
            // FOUR COUNTS RATHER THAN ONE, because they want opposite fixes: a
            // knot of talkers is a conversation-siting problem, a knot of
            // escorts is the companion rule, a knot on detour is an obstacle,
            // and a knot doing none of those is genuinely the route. The
            // denominator is the huddle itself, printed beside them.
            //
            // SAMPLED ON THE SAME PASS AS THE PEAK, not recomputed later. The
            // huddle moves every second, and a breakdown taken at a different
            // instant would describe a different crowd — which is the fault
            // that put four bad pairs on this file's done line.
            if (worstAt != null && worstHuddle > _huddleWorstSeen)
            {
                _huddleWorstSeen = worstHuddle;
                _huddleTalking = 0; _huddleEscorting = 0;
                _huddleDetour = 0; _huddleWaiting = 0;
                _huddleStanding = 0; _huddleMoving = 0;
                var cells = new HashSet<Vector3Int>();
                var at = worstAt.transform.position;
                foreach (var n in _npcs)
                {
                    if (n == null || !n.isActiveAndEnabled) continue;
                    if ((n.transform.position - at).sqrMagnitude > 4f) continue;
                    if (n.InConfab) _huddleTalking++;
                    if (n.Escorting) _huddleEscorting++;
                    if (n.OnDetour(_game.Now)) _huddleDetour++;
                    if (n.WaitingAsHost) _huddleWaiting++;
                    // AND WHICH PLACE CELL THEY BELONG TO, which is the one
                    // number that settles the spreading question.
                    //
                    // `Physique.SpreadRadius` sizes each person's ring from
                    // `CrowdAtPlace` — the count in their OWN metre cell. If
                    // this huddle is one cell, the ring is simply undersized
                    // and the fix is the radius. If it is seven, every ring is
                    // correctly sized for its own dozen and they overlap
                    // anyway, and the fix is to size it from the neighbourhood
                    // instead. Those are different edits and no landed number
                    // could tell them apart.
                    //
                    // The authored waypoints say seven — six metres across,
                    // seven distinct points — but that is a grep over literals
                    // and this is the live crowd, generated residents included.
                    var cell = GameController.PlaceKey(n.PlaceFor(_game.Now));
                    if (!cells.Contains(cell)) cells.Add(cell);

                    // AND ARE THEY STANDING WHERE THEY MEANT TO BE, OR STILL
                    // WALKING? This is the split that picks the fix, and every
                    // number taken so far has been blind to it.
                    //
                    // `busiestNear=12` counts TARGETS within two metres.
                    // `crowdHuddleWorst=41` counts BODIES within two metres.
                    // Those are different populations and they have been read as
                    // the same one — twice, in two different fixes I shipped
                    // saying they would work. If most of the forty-one are at
                    // their place, the rings genuinely are too small and
                    // `SpreadRadius` is the edit. If most are still en route,
                    // the rings are innocent and this is a jam: bodies piling up
                    // on a route with nothing separating them while they move,
                    // which is a different system entirely.
                    //
                    // Half a metre because the ring itself is 0.88m, so "at my
                    // place" has to be tighter than the ring or everyone counts
                    // as arrived by construction.
                    var want = n.PlaceFor(_game.Now);
                    var body = n.transform.position;
                    float ddx = want.x - body.x, ddz = want.z - body.z;
                    if (ddx * ddx + ddz * ddz <= 0.25f) _huddleStanding++;
                    else _huddleMoving++;
                }
                _huddleCells = cells.Count;
                _huddleWhere = $"{at.x:0}/{at.z:0}";
            }
            // GLANCED AT versus KNOWS WHO YOU ARE, counted in ONE pass so the
            // two describe the same instant. `deedWitnesses/deedEyesOpen` were
            // three separate maxima printed as one event's breakdown, and this
            // is the same shape of number one system over.
            int attending = 0, identified = 0;
            foreach (var n in _npcs)
            {
                if (n == null || !n.isActiveAndEnabled) continue;
                if (n.AttendingPlayer) attending++;
                if (n.HasIdentifiedPlayer)
                {
                    identified++;
                    // DisplayName, because that is the identifier a walker
                    // has — there is no Id on this type, which grepping for
                    // one before writing the line established rather than
                    // the compiler establishing it in half an hour.
                    if (!string.IsNullOrEmpty(n.DisplayName)) _identifiedEver.Add(n.DisplayName);
                }
                var v = cam.WorldToViewportPoint(n.transform.position);
                if (v.z <= 0 || v.x < 0 || v.x > 1 || v.y < 0 || v.y > 1) continue;
                _crowdSeen.Add(n.transform.position);
            }
            if (identified > _identifiedPeak)
            {
                _identifiedPeak = identified;
                _attendingAtIdentifiedPeak = attending;
            }
            if (_crowdSeen.Count < 2) return;
            int inside = 0;
            float tightest = float.MaxValue;
            for (int i = 0; i < _crowdSeen.Count; i++)
                for (int j = i + 1; j < _crowdSeen.Count; j++)
                {
                    // FLAT. Two people on a kerb and a step are not standing in
                    // each other, and a 3D distance would call them separate
                    // when they are side by side — the same 3D-against-flat
                    // mismatch that made `TightestGap` disagree with its own
                    // job trace.
                    var a = _crowdSeen[i]; var b = _crowdSeen[j];
                    float d = new Vector2(a.x - b.x, a.z - b.z).magnitude;
                    if (d < tightest) tightest = d;
                    if (d < BodyWidth) inside++;
                }
            // THE DENOMINATOR FROM THE SAME INSTANT. Twelve overlapping pairs
            // among fifty people and among thirteen are opposite findings, and
            // this file has now shipped that mistake four times.
            if (inside > _crowdInside)
            {
                _crowdInside = inside;
                _crowdSeenAtWorst = _crowdSeen.Count;
            }
            // AND WHEN, BECAUSE THIS IS A RUN MINIMUM AND I READ IT AS A
            // DESCRIPTION FOR THREE BUILDS.
            //
            // `_crowdTightest` is the worst instant in nine days. ONE frame
            // anywhere — two walkers spawned on the same waypoint and sampled
            // before either has taken a step — pins it at 0.00 for the rest of
            // the run, and no amount of separation working afterwards can move
            // it back. It answers "did it ever happen". I read it as "is this
            // how it looks", which is the fault CLAUDE.md names twice and
            // which I had quoted at myself the same morning.
            //
            // The median beside it was the real signal and it has moved every
            // build: 0.00, 0.20, 0.29, 0.33, 0.35. Note it is a median OF
            // per-frame tightest gaps, so it says "in a typical frame the
            // closest pair is this far apart" — the question worth asking.
            //
            // The peak keeps its job and gets a timestamp, the repair
            // `bodyReadWhen` got after one metric read 35.7 and 10.8 with no
            // code change between them. A zero stamped at day 1 is a spawn
            // artefact; one stamped mid-run is a real pile-up.
            if (tightest < _crowdTightest)
            {
                _crowdTightest = tightest;
                _crowdTightestWhen = _game != null
                    ? $"day{_game.Now.Day}h{_game.Now.Hour}n{_crowdSeen.Count}"
                    : "noworld";
            }
            _crowdGaps.Add(tightest);
        }

        readonly List<Vector3> _crowdSeen = new List<Vector3>();
        readonly List<float> _crowdGaps = new List<float>();
        int _crowdInside, _crowdSeenAtWorst;
        float _crowdTightest = float.MaxValue;
        /// When the run-minimum above was observed, and how many people
        /// were in frame at that instant. Without it a spawn artefact and
        /// a real pile-up print the same number.
        string _crowdTightestWhen = "never";

        /// The typical closest approach in frame, against the worst one. -1
        /// when nothing was ever sampled — a gap of zero is a real reading.
        double CrowdGapMedian
        {
            get
            {
                if (_crowdGaps.Count == 0) return -1;
                var s = new List<float>(_crowdGaps);
                s.Sort();
                return s[s.Count / 2];
            }
        }

        /// Every sampled instant's overlap FRACTION, for the median. Unbounded
        /// by design — it grows once per sample, and the sampler runs on the
        /// same cadence as the rest of this file's probes rather than per
        /// frame, so a seventeen-day run puts tens of entries in it, not
        /// thousands. If that ever stops being true this wants a reservoir,
        /// not a cap: dropping the tail would bias the median toward the
        /// quiet early days, which is the half of the run that has nobody
        /// talking in it.
        readonly List<float> _bubbleOverlap = new List<float>();

        /// The only denominator `collidingBubbles` can honestly be divided by.
        int _bubblesAtWorst = 0;

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

        /// STAGING THE ONE CONDITION THE RELIABILITY RULE NEEDS.
        ///
        /// Two consecutive missed drops, after the early windows have already
        /// satisfied `jobRan` and `takingsBanked`, so the street gets something
        /// to say about a man who does not turn up — and the windows after
        /// these are left alone, so a delivery clears it and that path runs
        /// too. `Reliability.TalkedAboutAt` is 2 and stays 2.
        const int SkipDropsFromDay = 10;

        /// A BACKSTOP, NOT A TARGET. The plant stops the moment the reliability
        /// rule files anything; this only bounds a run where it never can, so
        /// that a broken rule cannot starve every drop for the rest of the
        /// fifteen days. It was `SkipDropsCount = 2` and stopping at two was
        /// the bug — two skips separated by a delivery are not two consecutive
        /// missed nights, and only consecutive ones reach the bar.
        const int SkipDropsMax = 5;
        int _dropsSkipped;
        int _skippingDropDay = -1;

        /// M21: the run has to actually NAME somebody, or the informer verb is
        /// tested Core with no call site — which is the state it shipped in an
        /// hour ago and which `reach-check` refused.
        bool _denounceStaged;
        bool _pledged, _pledgeRefused, _brokeWith;
        bool _claimHeld, _claimCaught;
        bool _denounceIgnored, _denounceStuck, _poached, _claimStaged;

        /// Whether the one crew member who is not feuding was given something
        /// to run. False means `Establish` refused and the succession is still
        /// blocked for a reason `successorWhy` will name.
        bool _joeyRuns;

        /// The succession, sampled at the ONE pass that attempts it. The audit
        /// closes on that same pass, so there is no second try and an
        /// end-of-run reading describes a world that no longer matters.
        bool _handedTried;
        int _handedRetries;
        int _handedTriedDay;
        int _homWhyDay;
        readonly List<string> _homWhySeries = new List<string>();
        string _handedReady = "neverTried", _handedWhyAtTry = "neverTried";
        /// The one wound the harm probe treated, held so the gate can ask
        /// about THAT one rather than about Rocco in general.
        Injury _harmTreated;
        string _claimVia = "not reached";
        int _denounceWitnesses;
        /// Calls tried, and how many of those were to somebody the phone
        /// book says could be reached at that hour at all.
        int _callsAttempted, _callsReachable;
        /// Did an accusation ever come back at the player, and how hard the
        /// strongest contrary voice pushed. -1 means the probe never ran.
        bool _denounceBlewBack;
        double _blowbackContradiction = -1;
        /// How many score samples had the room gone quiet in — pulse at the
        /// floor with unease up. Its denominator is `scoreSamples`, printed
        /// beside it, because a bare count of a per-sample state says
        /// nothing without knowing how many samples there were.
        int _roomQuietSamples;
        readonly List<float> _pulseSamples = new List<float>();
        readonly List<float> _uneaseSamples = new List<float>();
        /// The variable BOTH of those are derived from. Without it the two
        /// medians look like two findings and are one, and there is no way to
        /// tell a score that misreads a normal week from a harness that runs
        /// the week at maximum heat.
        readonly List<float> _heatSamples = new List<float>();

        /// Median of a sampled series, or -1 when nothing was sampled — the
        /// same shape as `CrowdGapMedian`, which is the pattern this file
        /// already uses for exactly this question.
        static double MedianOf(List<float> xs)
        {
            if (xs == null || xs.Count == 0) return -1;
            var s = new List<float>(xs);
            s.Sort();
            return s[s.Count / 2];
        }
        /// How many people have worked out who the player is, at the worst
        /// instant, with the number merely LOOKING at that same instant — and
        /// the distinct count over the whole run, which is the one that says
        /// whether being careful is possible at all.
        int _identifiedPeak, _attendingAtIdentifiedPeak;
        readonly HashSet<string> _identifiedEver = new HashSet<string>();
        /// Nullable because "the cut never happened" and "it happened and
        /// nobody saw" are different facts, and a plain false would merge
        /// them — the denominator rule, in the smallest form it takes.
        bool? _cutMarkedYou;
        /// A COUNT, not a flag — ShapeCheck said so when I assumed
        /// otherwise. How many people perceived the cut, which is a
        /// better number than whether any did.
        int? _cutSawSomething;
        /// HOW MANY TIMES A REAL ACT CHARGED THE PLAYER'S REPUTATION.
        ///
        /// The denominator for `notoriety`, which is otherwise a zero that
        /// cannot tell "the street never learned anything" from "nothing ever
        /// called the model". `Violence.Notoriety` sat unit-tested and uncalled
        /// for weeks in exactly that state, so this is the number that would
        /// have said so.
        int _notorietyApplied;

        /// DOES BEING KNOWN CHANGE WHAT THE PLAYER CAN DO? Two doors, each
        /// tried twice — once at the notoriety this run actually built and once
        /// at nothing — and the answer is whether the two disagree.
        ///
        /// EVERY OTHER NUMBER ON THIS SUBJECT STOPS SHORT OF THE QUESTION.
        /// `notoriety` says a value exists, `notorietyApplied` and
        /// `notorietyFromLaw` say something charged it, and the roadmap's own
        /// note on this row is that none of it "yet CHANGES anything the player
        /// can do". A door that opens at 45 and a player who reached 62 are two
        /// facts that have never been put in the same sentence, because
        /// `CheckGates` returns immediately while the sim is running and the
        /// sim's own access probe builds a pauper with every field at zero.
        ///
        /// RULE 5b's TWIN, WHICH IS WHY THE SECOND READING IS HERE. A probe
        /// that only ever asks at the real value cannot tell "notoriety opened
        /// this" from "this door was open to anybody" — the laundry's other key
        /// is an introduction from Ada and the yard's are a crew of two or the
        /// hour being after nine, so both can open for reasons that have
        /// nothing to do with being known. Asking again at zero plants the
        /// condition: `differs` is the word that means notoriety did the work.
        string NotorietyDoorReading()
        {
            var host = _game;
            if (host == null || host.Gates == null) return "no gates";
            var sb = new System.Text.StringBuilder();
            int looked = 0;
            foreach (var gate in host.Gates)
            {
                if (gate == null || gate.Keys == null) continue;
                bool keyed = false;
                foreach (var k in gate.Keys)
                    if (k.Kind == KeyKind.Notorious || k.Kind == KeyKind.Quiet) keyed = true;
                if (!keyed) continue;
                looked++;

                var real = host.PeekAccessState(gate);
                bool openNow = Doors.Try(gate, real).Allowed;
                double had = real.Notoriety;
                real.Notoriety = 0;
                bool openUnknown = Doors.Try(gate, real).Allowed;

                if (sb.Length > 0) sb.Append(' ');
                sb.Append(gate.Id).Append(':').Append(openNow ? "open" : "shut")
                  .Append('@').Append(had.ToString("0.00"))
                  .Append(openNow == openUnknown ? " same" : " differs");
            }
            // THE DENOMINATOR. "No door answered" and "no door was asked" read
            // identically without it, and the second is what happens the moment
            // somebody removes the last notoriety key from `AccessSetup`.
            return looked == 0 ? "no notoriety-keyed gate in the world" : sb.ToString();
        }

        /// THE MOAT'S OWN NUMBERS, and until now they reached nobody.
        ///
        /// The log line that computes these says, in its own comment, that a
        /// run where every alibi checks out is indistinguishable from one
        /// where the contradiction branch is DEAD, and that the branch is the
        /// moat — an NPC cannot be talked out of what it knows. It then
        /// printed them on a conditional line that the verdict does not carry,
        /// so the distinction it exists to make has never been readable.
        /// `verdict-reach` lists all three as unreachable.
        double _denounceCorroboration = -1, _denounceContradiction = -1;
        string _denounceMark = "none";
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
        /// Peak over the run of the two structural blindnesses found on
        /// 3 August: how many witnesses had their eyes open at all, and how
        /// many knew the player well enough to name him. Both were zero by
        /// construction and no gate asked.
        int _deedEyesOpen, _deedKnowsYou;
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
        /// THE VISIBLY-ARMED WINDOW. `_batTook` is whether the swap succeeded
        /// and `_batCarried` is whether the street's flag agrees — two facts
        /// rather than one, because a `Carry` that returns true and a
        /// `ShowingWeapon` that stays false would be the interesting failure
        /// and one boolean cannot say which half went wrong.
        bool _batStaged, _batTook, _batCarried;
        Traces.Item _simRazor, _simBat;
        /// THE FIRST BODY TO REACH THE REGISTER. `_homSaw` and `_homKnew` are
        /// the two halves `RecordKilling` splits its witnesses into, printed
        /// separately because they price differently: seeing you costs
        /// `NamedWeight`, hearing it through a wall costs nothing at all, and a
        /// single total could not tell a quiet killing from a public one.
        bool _homicideStaged;
        string _homVictim = "";
        int _homBodies, _homSaw, _homKnew, _homWouldTalk, _homNamed;
        int _homSawStored, _homHoldsIt, _homHasAgent, _homAnyRumour;

        /// The key the register asks for, and the keys one witness actually
        /// carries. Both sides of a comparison that every count so far could
        /// only tell me had failed, never why.
        string _homWantKey = "none", _homTopics = "";
        int _homFileOffered = -1, _homFileDropped = -1;
        bool _homSameMill;
        double _homPressure;
        Inquiry _homInquiry = Inquiry.None;

        // M18 companionship. `_companionRung` is the companion's OWN rung on
        // the staged deed and `_companionStreetRung` is the best rung anybody
        // ELSE reached on the same deed — the pair, because the design claim is
        // comparative and a single number cannot carry it. See the gate.
        bool _companionStaged;
        float _companionDist = -1f;
        /// How far the escort was when she was recruited, and how many days the
        /// deed waited for her to arrive. Both exist so a red `companionSight`
        /// says which of the two possible causes it is.
        float _companionRecruitDist = -1f;
        int _deedWaitedDays;
        string _companionWith = "";
        int _companionRung = -1, _companionStreetRung = -1;
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
        bool _ellisEverAsked;
        /// How empty the emptiest place the run could find actually was. Zero
        /// is what the accident and disposal claims need; anything else is a
        /// fact about the world rather than about the code.
        int _emptyWatchers = -1;
        int _crowdedWatchers = -1;
        /// Did the staged "somebody can see you" spot actually satisfy the
        /// predicate the gate then tests? See where it is set. False means the
        /// run fell back to the fullest place it could find and the comparison
        /// below it is between two unwatched spots — which is a fact about the
        /// harness, not a finding about the game, and must not read as one.
        bool _crowdedIsWatched;
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
        /// How many ticks wanted to slam and could not, because a louder sound
        /// was still fresh or a ring already owned the ground. Without it, four
        /// slams landing reads identically whether the street is usually quiet
        /// or whether the gap was one tick in a thousand — and those have very
        /// different things to say about how often a player would hear anything.
        int _slamsDeferred;
        /// One entry per slam: the ring's skip reason and radius at that instant.
        /// See the note where it is filled.
        readonly List<string> _slamRingSkips = new List<string>();

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
            NpcWalker nearest = null;
            float nearestDist = float.MaxValue;
            void Consider(NpcWalker n)
            {
                if (n == null) return;
                float d = Vector3.Distance(n.transform.position, _player.transform.position);
                if (d < nearestDist) { nearestDist = d; nearest = n; }
                // The counting itself has moved to `NpcWalker.Tick`; this
                // pass now only wants the nearest body for staging a deed.
            }
            if (_npcs != null) foreach (var n in _npcs) Consider(n);
            if (_game != null && _game.CrowdBodies != null)
                foreach (var kv in _game.CrowdBodies) Consider(kv.Value);
            // NOT ASSIGNED HERE ANY MORE. This loop was the only writer of
            // `Perceivers.Attending` and `PresentNearby` in the project, and
            // this class runs in CI and nowhere else — so the hush, the crowd's
            // share of the ambient floor and the caption bar's attention
            // channel were all sim-only, behind a comment in `Perceivers`
            // claiming the walkers maintained them. The walkers do now.
            //
            // Read rather than recomputed, so the gate below measures the same
            // quantity the game does. A sim that computes its own copy of a
            // number is a sim that can pass while the game fails.
            int attending = Perceivers.Attending, present = Perceivers.PresentNearby;
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
            // AND NOT WHILE THE OUTFIT'S DROP IS OPEN. This probe walks the bot
            // to somebody and then HOLDS IT STILL for `LoiterSeconds`, and it
            // may start at any hour from 19:00 — which overlaps the 22:00-02:00
            // drop window on every day it can fire.
            //
            // The job trace is what caught it: `d8:MISSED[from=18m nearest=17m]`
            // — eighteen metres away when the drop opened, seventeen at its
            // closest, so the bot never went. Day 8 is the first day this probe
            // is allowed to stage, which is not a coincidence.
            //
            // "A probe that alters the outcome measured beside it is not a
            // probe" is already written in this file, about staging a
            // confrontation inside the campaign week. Same fault, second site.
            // The loiter has twenty other hours of the day and the drop has
            // four, so the drop wins and nothing is lost.
            bool dropOpen = _game.ActiveJobPos.HasValue;
            if (!_loiterStaged && !dropOpen && now.Day >= 8 && now.Hour >= 19 && nearest != null)
            {
                _loiterApproaching = true;
                _loiterTarget = nearest.transform.position;
            }

            // NAME SOMEBODY TO THE LAW, once, on a day when the street has had
            // time to accumulate something to say. Day 9 rather than day 1
            // because an accusation is weighed against what people have heard,
            // and on day one nobody has heard anything — the probe would
            // measure an empty mill and report Ignored for ever, which is a
            // true answer to a question nobody asked.
            //
            // The target is the rival, because that is the fiction: Sera Kest
            // is the person the player has a reason to point a detective at.
            // Whoever is standing nearest is who saw him go in.
            if (!_denounceStaged && now.Day >= 9 && _game != null && _game.Gossip != null
                && nearest != null)
            {
                _denounceStaged = true;

                // THE SEER MUST LIVE IN THE MILL, planted rather than hoped
                // for. A mark files only when the visit was SEEN — `saw`
                // requires `mill.Get(seenById)` — and `nearest` is whatever
                // body happens to stand closest, only ~180 of 700 of whom
                // carry gossip agents. One run in 150 drew three blanks and
                // the gate went red with every mechanic working (b052e3e).
                // Same family as disposal's crowded-spot-with-nobody-in-it:
                // the condition gets planted, the gate stays where it is.
                var seerMill = _game.Gossip != null ? _game.Gossip.Mill : null;
                string seer = nearest.DisplayName;
                if (seerMill != null && seerMill.Get(seer) == null)
                    foreach (var g in seerMill.Agents)
                    {
                        if (g == null || !Watched.WouldTalkToPolice(g)) continue;
                        seer = g.Id;
                        break;
                    }

                // THE ACCUSATION NOBODY WILL BACK, FIRST. This is the state the
                // street is in by default and it must be Ignored.
                var quiet = LawHost.Denounce(_game, seer, "kest",
                                             "handled", "the_warehouse_job");
                _denounceIgnored = quiet != null && quiet.Outcome == Accusation.Ignored;

                // AND THEN ONE THE STREET WILL BACK, because the first run of
                // this probe returned `Ignored (0 of 0, nobody will back it)`
                // and `lawOk=True`, and those two facts together prove only
                // that the method was called. Every branch that makes the verb
                // worth having — corroboration, the bar, the charge — went
                // unexercised behind a green gate. That is the shape rule 5b
                // exists for, found in my own probe within an hour of writing
                // the rule down again.
                //
                // The witnesses are PLANTED rather than hoped for: two people
                // who will talk to police and agree, so a charge is reachable
                // on every run instead of on the lucky ones. Nothing here
                // bypasses `Informing` — it still has to weigh them.
                var mill = _game.Gossip != null ? _game.Gossip.Mill : null;
                if (mill != null)
                {
                    int planted = 0;
                    foreach (var g in mill.Agents)
                    {
                        if (g == null || !Watched.WouldTalkToPolice(g)) continue;
                        mill.Witness(g.Id, new Fact("kest", "ran", "the_dockside_racket"),
                                     "I have seen who runs that.", sensitive: false,
                                     now: now, confidence: 0.6);
                        if (++planted >= 3) break;
                    }
                    _denounceWitnesses = planted;
                }
                var d = LawHost.Denounce(_game, seer, "kest",
                                         "ran", "the_dockside_racket");
                _denounceStuck = d != null && d.Outcome == Accusation.Charged;

                // AND THE BRANCH THAT MAKES THE VERB DANGEROUS, which has
                // never once run.
                //
                // `contradiction` landed on the done line this morning and read
                // 0.00, and the comment beside it says exactly why that is
                // ambiguous: a run where every alibi checks out and a run where
                // the branch is DEAD print the same number. It is the second.
                // The probe above plants three witnesses who all AGREE, so
                // nothing on this street has ever contradicted an accusation
                // and `BlewBack` has never been reached in a build.
                //
                // A contradiction is a witness on the SAME TOPIC with a
                // DIFFERENT VALUE, so it must be planted rather than hoped for
                // — rule 5b's corollary, which says a guard needs a run in
                // which the thing it asserts CAN happen.
                //
                // IT GETS ITS OWN TARGET, deliberately. Planting a contrary
                // voice into the accusation above would flip it from Charged
                // to BlewBack and take `denounceStuck` with it — a probe that
                // alters the outcome measured beside it is not a probe, which
                // is a sentence already written twice in this file. Nothing
                // bypasses `Informing`: it still weighs the voice, and with no
                // corroborators on a fresh claim any credible contrary one
                // wins, which is the rule rather than a rigged number.
                if (mill != null)
                {
                    foreach (var g in mill.Agents)
                    {
                        if (g == null || !Watched.WouldTalkToPolice(g)) continue;
                        mill.Witness(g.Id, new Fact("ferko", "ran", "nothing_at_all"),
                                     "That is not who runs it.", sensitive: false,
                                     now: now, confidence: 0.9);
                        break;
                    }
                }
                var back = LawHost.Denounce(_game, seer, "ferko",
                                            "ran", "the_dockside_racket");
                _denounceBlewBack = back != null && back.Outcome == Accusation.BlewBack;
                _blowbackContradiction = back != null ? back.Contradiction : -1;

                // AND ALLEGIANCE MOVES, BOTH WAYS, IN THE SAME RUN.
                //
                // Pledging and walking out are two halves of one claim — an
                // allegiance you cannot leave is a setting rather than a
                // choice — so staging only the pledge would leave the exit
                // exactly as unreached as it was this morning. Rule 5b in a
                // sim probe: exercise the case it must accept AND the case it
                // must refuse, which here is pledging to somebody who despises
                // you.
                var em = _game.Empire;
                var friendly = em.ArmOf("dockside");
                if (friendly != null)
                {
                    // The standing floor is a real precondition and the probe
                    // must not tunnel through it — it is SET here rather than
                    // bypassed, so the refusal below still means something.
                    friendly.Standing = System.Math.Max(friendly.Standing, em.PledgeStandingFloor);
                    _pledged = _game.Pledge("dockside");
                    var hostile = em.ArmOf("machine");
                    if (hostile != null)
                    {
                        hostile.Standing = -1.0;
                        _pledgeRefused = !_game.Pledge("machine");
                    }
                    _brokeWith = _game.WalkOutOn("dockside");

                    // AND TAKE ONE OF THEIR PEOPLE, which the run has never
                    // once done. `poachesHeard=0` failed this gate on its first
                    // build and was right to: the sim recruits Sam and Rocco,
                    // and neither answers to anybody — dockside is Joey and
                    // Ferko, machine is Tibor, newcrew is Rita. So the poach
                    // path was gated on an event the run cannot produce, which
                    // is the accept case going untested from the other
                    // direction.
                    //
                    // Joey, because he is dockside's and dockside is the arm
                    // this probe already deals with. Loyalty is SET to clear
                    // the recruit floor rather than hoped over it — the same
                    // reason the standing floor is set above and the witness is
                    // planted below. A probe that only fires on a lucky run is
                    // not a probe.
                    var joey = _game.Gossip?.Mill?.Get("Joey");
                    if (joey != null && em.CrewOf("Joey") == null)
                    {
                        joey.Loyalty = System.Math.Max(joey.Loyalty, 0.6);
                        _game.Wallet.EarnDirty(120);   // the probe must not fail for being skint
                        _poached = em.RecruitByNeed(joey, "Joey", 100, _game.Wallet, now,
                                                    _game.Gossip.Mill);

                        // AND GIVE HIM SOMETHING TO RUN, WHICH IS THE ONLY
                        // REASON THE GAME HAS NEVER BEEN ABLE TO END.
                        //
                        // `handed=False` in all 138 kept runs, and `successorWhy`
                        // finally said why on `a050815`:
                        // `Sam:feuding/c0.55l0.60, Rocco:feuding/c0.70l0.85,
                        // Joey:noAssignment/c0.65l0.70`. Every competence and
                        // loyalty bar is cleared. The blockers are a feud and a
                        // missing assignment, and BOTH are this sim's own doing:
                        // it establishes `collection` for Sam and `fencing` for
                        // Rocco, then flares a feud between exactly those two on
                        // day 4 to prove the injury layer — and `feuding` is
                        // true for anyone at war with ANY living crew member, so
                        // one staged feud disqualifies both runners at once.
                        // Joey, the one man left, was recruited and never given
                        // anything to run.
                        //
                        // So a probe for the harm system has been suppressing
                        // the ending of the game for a hundred and thirty-eight
                        // runs. "A probe that alters the outcome measured beside
                        // it is not a probe" is already written twice in this
                        // file, about smaller things than the ending.
                        //
                        // PLANTED, NOT LOOSENED. The feud stays exactly as it
                        // is and no bar moves: `protection` is the one racket
                        // nobody runs and the only one needing no front, so this
                        // adds a legitimate world state rather than editing the
                        // rule. `Establish` still refuses if he is already
                        // assigned or the racket is taken, so it cannot
                        // double-book him.
                        var joeyCrew = em.CrewOf("Joey");
                        if (joeyCrew != null)
                            _joeyRuns = em.Establish(em.RacketOf("protection"), joeyCrew, now);
                    }
                }

                // AND THE PLAYER OFFERS AN ALIBI — one that holds and one that
                // does not, to somebody who was there.
                //
                // Both, in the same run, because "a claim was processed" and "a
                // claim can be CAUGHT" are different facts. A run where every
                // alibi checks out is indistinguishable from one where the
                // contradiction branch is dead, and that branch is the moat:
                // an NPC cannot be talked out of what it knows.
                if (d != null)
                {
                    _denounceCorroboration = d.Corroboration;
                    _denounceContradiction = d.Contradiction;
                    // THE PREDICATE, WHICH IS THE WHOLE INFORMATION.
                    // `MarkOnYou` is a Fact, not a bool — it is
                    // (player, informer, no) when nothing stuck and
                    // (player, lied_to_police, <target>) when it did.
                    // ShapeCheck caught the bool assumption here rather
                    // than the Windows build catching it in half an hour,
                    // which is what that check is for.
                    _denounceMark = d.MarkOnYou != null
                        ? d.MarkOnYou.Predicate : "none";
                }
                if (d != null)
                    Debug.Log($"SimDirector: denounced kest -> {d.Outcome} "
                              + $"corroboration={d.Corroboration:0.00} "
                              + $"contradiction={d.Contradiction:0.00} "
                              + $"backers={d.Corroborators} mark={d.MarkOnYou}");
            }
            // THE ALIBI PROBE, OUTSIDE THE DENUNCIATION'S ONE-SHOT GUARD.
            //
            // It used to live inside it, and `claimsMade=0` came back from the
            // build for exactly that reason: `_denounceStaged` is set at the
            // TOP of that block, so if the conversation hosts were not built on
            // the single frame it ran, nothing ever tried again. A one-shot
            // probe that marks itself done BEFORE doing the work cannot tell
            // "did it" from "gave up", and reports the same zero either way.
            //
            // Its own latch, set only once a claim actually landed, and it
            // keeps trying until then. Both directions in the same run: an
            // alibi that holds and one that does not, because a run where every
            // alibi checks out is indistinguishable from one where the
            // contradiction branch is dead — and that branch is the moat.
            if (!_claimStaged && now.Day >= 9 && _game != null)
            {
                // WHY IT DID NOT EVEN TRY, because the last build said
                // `claimWhy=[not tried]` — the initial value, meaning
                // `LawHost.Claim` was never entered and every reason it can
                // report was therefore unreachable. The guard that stopped it
                // was HERE and it was silent, which is the same fault as the
                // three silent early returns I had just finished labelling one
                // layer down. A diagnostic that stops at the first door is a
                // diagnostic with a blind spot exactly where the problem is.
                //
                // AND IT NO LONGER DEPENDS ON ONE ACCESSOR. `_game.Hosts` is a
                // list something else has to have populated; the scene either
                // contains conversation hosts or it does not. Falling back to
                // the scene means the probe cannot be defeated by a list that
                // has not been filled yet, and the reason says which path
                // found one.
                var listener = _game.Hosts != null && _game.Hosts.Count > 0 ? _game.Hosts[0] : null;
                string via = listener != null ? "game.Hosts" : "";
                if (listener == null)
                {
                    var all = FindObjectsByType<ConversationHost>(FindObjectsSortMode.None);
                    foreach (var h in all)
                        if (h != null && h.Knowledge != null) { listener = h; via = $"scene({all.Length})"; break; }
                    if (listener == null && all.Length > 0) via = $"scene({all.Length}) none with knowledge";
                    if (all.Length == 0) via = "no hosts in the scene at all";
                }
                _claimVia = via;
                if (listener != null && listener.Knowledge != null)
                {
                    // The witness is GIVEN what he saw rather than hoped to
                    // have it, so the reject case is reachable on every run.
                    listener.Knowledge.Learn(new Fact("player", Claims.LocationKey(now), "docks"));

                    // AND SOMEBODY IS PUT WITHIN EARSHOT, because the first
                    // reading came back `claimOverheard=0` for the whole run.
                    //
                    // That is the failure this project has most of: a probe
                    // that only fires on a lucky world, reporting zero, and
                    // reading exactly like a mechanic that is not wired. The
                    // rule is to PLANT the condition and never to loosen the
                    // bound — set the standing before pledging, learn the fact
                    // into the witness before telling the lie, put a body at
                    // the crowded spot.
                    //
                    // Here the condition is a second person close enough to
                    // make out words. `Acoustics.SpeechCarry` is 14m and
                    // intelligibility has to clear `WordsThreshold`, so two
                    // metres is comfortably inside and is also a real distance
                    // for two people at the same bar — this stages a plausible
                    // world, not a degenerate one.
                    //
                    // MOVED, NOT TELEPORTED-AND-LEFT: the walker's own schedule
                    // takes it back, and a bystander that stayed welded to the
                    // speaker for the rest of the run would corrupt every other
                    // proximity reading in the sim.
                    ConversationHost bystander = null;
                    foreach (var h in _game.Hosts)
                        if (h != null && h != listener) { bystander = h; break; }
                    Vector3 stood = default;
                    if (bystander != null)
                    {
                        stood = bystander.transform.position;
                        bystander.transform.position =
                            listener.transform.position + new Vector3(2f, 0, 0);
                    }
                    _claimHeld = LawHost.Claim(_game, listener, "I was at the docks all evening")
                                 == ClaimResult.Consistent;
                    _claimCaught = LawHost.Claim(_game, listener, "I was at the Hook Street pub")
                                   == ClaimResult.Contradiction;
                    _claimStaged = LawHost.ClaimsMade > 0;
                    if (bystander != null) bystander.transform.position = stood;
                }
            }
            if (_loiterApproaching)
            {
                target = _loiterTarget;
                _targetOwner = "loiter-walk";
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
                // THE DROP WINS HERE TOO, AND THAT IS THE HALF THAT WAS MISSING.
                //
                // Twenty-three lines up, the loiter refuses to START while a
                // drop is open, with a comment explaining exactly why: "the
                // loiter has twenty other hours of the day and the drop has
                // four, so the drop wins and nothing is lost". The HOLD that
                // follows had no such guard, so a loiter begun at 19:00 pins
                // the bot in place straight through a window that opens at
                // 22:00 — and the owner tally caught it doing precisely that:
                //
                //   d8:MISSED[from=11m nearest=10.6m@22h held:loiter-hold=21]
                //
                // Twenty-one ticks, every one of them owned by the loiter, and
                // the bot moved less than half a metre. One idea, two
                // implementations, and the one nobody looked at is the one
                // missing a line — which is the fault this project has now
                // recorded four times in its own rules and walked into again.
                //
                // The measurement is taken rather than discarded: the loiter
                // has already done its work by this point (`loiterNotices` has
                // read 37 of 37) and what is lost is the tail of a hold, not
                // the probe. `loitersCutShort` counts it so the cost is a
                // number rather than a silence.
                bool dropWaiting = _game.ActiveJobPos.HasValue;
                if (Time.time < _loiterUntil && !dropWaiting)
                {
                    // Stand still. Holding the target AT the player is how the
                    // bot stops without touching the locomotion.
                    target = _player.transform.position;
                    _targetOwner = "loiter-hold";
                }
                else
                {
                    bool cutShort = dropWaiting && Time.time < _loiterUntil;
                    if (cutShort) _loitersCutShort++;
                    int looks = Perceivers.Looks - _looksBeforeLoiter;

                    // CUT SHORT WITH NOTHING TO SHOW IS NOT A MEASUREMENT, AND
                    // RECORDING IT AS ZERO IS HOW THE PERCEPTION GATE WENT RED
                    // FOR A REASON NOBODY HAD NAMED.
                    //
                    // The paragraph above says the loiter "has already done its
                    // work by this point (`loiterNotices` has read 37 of 37) and
                    // what is lost is the tail of a hold, not the probe". That
                    // was true of the run it was written from. On c101f35 it
                    // reads `loiterLooks=0 loiterNotices=0 loitersCutShort=1` —
                    // the drop was already open when the hold began, so the
                    // probe was cut before anybody could turn a head, and a
                    // comment claiming otherwise sat directly above the code
                    // that proved it wrong. Third decayed claim of the day.
                    //
                    // `perception` then failed on `loiter`, which is rule 5b's
                    // twin exactly: a guard asserting something the run never
                    // supplied the condition for. Ten of the last hundred and
                    // twenty-five runs have gone red here, and rare red with no
                    // named cause is what teaches everybody to read red as
                    // noise.
                    //
                    // SO THE CONDITION IS PLANTED AGAIN, NOT THE BOUND
                    // LOOSENED. A cut-short loiter that gathered nothing is
                    // un-staged and re-approached, so a twenty-day run gets
                    // another evening; the assertion stays at "somebody looked".
                    // Bounded, because a run whose drops are always open would
                    // otherwise retry for ever, and `loiterRetries` says how
                    // many evenings it took — a probe that needs five goes is a
                    // finding about the schedule, not a success.
                    if (cutShort && looks < 1 && _loiterRetries < 4)
                    {
                        _loiterRetries++;
                        _loiterStaged = false;
                        _loiterApproaching = false;
                    }
                    else _loiterLooks = looks;
                    _loiterUntil = -1f;
                    Debug.Log($"SimDirector: loiter over, {_loiterLooks} heads turned, "
                              + $"{Perceivers.LoiterNotices} of them for loitering"
                              + (dropWaiting ? " — CUT SHORT, a drop was open" : ""));
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
            // AND THE SLAM WAITS FOR A GAP, WHICH IS RULE 5b's TWIN.
            //
            // Four slams staged, four rings absent, and the honest per-slam line
            // read `noring` for every one of them. The cull was never the fault:
            // a slam carries 55 and the street talks at 58, so `Perceivers.Emit`
            // returns before drawing anything whenever a remark is inside its
            // six-second freshness window. The sim was spending all four of its
            // chances inside somebody else's sound and then failing itself for
            // the silence.
            //
            // PLANT THE CONDITION, NEVER LOOSEN THE BOUND. Both tests below ask
            // for exactly what the gate asserts — that a loud noise at 3am puts
            // a circle on the ground and pulls people toward it — and neither
            // touches a threshold. A slam is one instantaneous Emit inside a
            // four-hour window, so deferring it by a frame costs no game time
            // and it retries on the next tick of the same night.
            bool louderStillFresh =
                Time.time - Perceivers.LastSoundTime < Perceivers.SoundFreshSeconds
                && Perceivers.LastSoundLoudness > Perception.LoudDoorSlam;
            bool ringWouldBeShadowed =
                NoiseRing.WouldBeShadowed(Perception.LoudDoorSlam);
            if (louderStillFresh || ringWouldBeShadowed) _slamsDeferred++;

            if (_slams < SlamsWanted && now.Day != _lastSlamDay
                && now.Hour >= 1 && now.Hour <= 5
                && !louderStillFresh && !ringWouldBeShadowed
                && nearest != null && nearestDist <= Perceivers.NearBandMetres)
            {
                _slams++;
                _lastSlamDay = now.Day;
                _investigationsBeforeSlam = Perceivers.NoiseInvestigations;
                _ringsShownBeforeSlam = NoiseRing.Shown;
                int soundsBeforeSlam = Perceivers.SoundsEmitted;
                Perceivers.Emit(_player.transform.position, Perception.LoudDoorSlam, "slam");
                if (NoiseRing.Shown > _ringsShownBeforeSlam) _slamDrewRing = true;
                // WHY EACH SLAM'S RING DID OR DID NOT DRAW, kept per slam.
                //
                // `perception` has gone red once in 66 runs, on `ring-drawn`,
                // with `slams=4` and `ringsDrawn=109` in the same verdict — so
                // rings drew all night and not one of the four slams was among
                // them. The skip reason is already in the log line below and the
                // log is unreadable from here (rule 12), so the only channel that
                // works is the verdict, and it carried the outcome without the
                // reason.
                //
                // `ringSmall=151 ringShadowed=132` are run totals and cannot say
                // which cull caught a SLAM. This can. A slam at 3am carries 48
                // metres by `AudibleRadius`, which is not a small ring, so if the
                // answer comes back `small` the floor is being computed against
                // something other than the emission — and if it comes back
                // `shadowed` the cull is right and the gate is asserting
                // something the world does not owe it.
                // WHETHER A RING ACTUALLY APPEARED FOR THIS SLAM, not what a
                // global last-value happened to hold afterwards.
                //
                // The red run reported `#3:drawn@80m #4:drawn@81m` beside
                // `slamDrewRing=False`, which cannot both be true of the same
                // event. `LastSkip` and `LastRadius` are GLOBALS read after the
                // Emit — and `Perceivers.Emit` returns EARLY, before drawing
                // anything, when a louder sound is still fresh. So a swallowed
                // slam leaves the previous ring's verdict standing and the
                // diagnostic reports somebody else's "drawn".
                //
                // The same stale-global read this project keeps shipping: a
                // number taken at the wrong instant, next to one taken at the
                // right one. `shown` is the delta across THIS Emit, and
                // `swallowed` says the guard fired, so the two can no longer
                // disagree without saying which.
                // AND `noring` WAS STILL TWO ANSWERS WEARING ONE NAME, which is
                // rule 3b in the place rule 3b was written about. Swallowed by
                // the freshness guard and culled by the ring's own presentation
                // rule have opposite fixes — one is the sim staging into a
                // crowded moment, the other is the model saying the circle was
                // not worth drawing — and `noring(swallowed-or-culled)` could
                // not tell them apart, so it named the ambiguity rather than
                // resolving it.
                //
                // `SoundsEmitted` is the denominator. It moves once per Emit
                // that gets PAST the guard, and `sounds` equalled `ringsSized`
                // exactly in the last run, so a slam that reaches the sizing is
                // a slam that reaches the ring.
                bool drewThis = NoiseRing.Shown > _ringsShownBeforeSlam;
                bool heardThis = Perceivers.SoundsEmitted > soundsBeforeSlam;
                _slamRingSkips.Add(drewThis
                    ? $"#{_slams}:{NoiseRing.LastSkip}@{NoiseRing.LastRadius:0}m"
                    : heardThis
                        ? $"#{_slams}:culled({NoiseRing.LastSkip})@{NoiseRing.LastRadius:0}m"
                        : $"#{_slams}:swallowed(by {Perceivers.LastSoundKind}"
                          + $"@{Perceivers.LastSoundLoudness:0})");
                _slamAt = Time.time;
                Debug.Log($"SimDirector: slammed a door #{_slams}, {present} people nearby, "
                          + $"carries {Perception.AudibleRadius(Perception.LoudDoorSlam, Perception.AmbientNight3am):0.0}m"
                          // THE SAME STALE-GLOBAL READ, ELEVEN LINES UNDER THE
                          // PARAGRAPH ABOUT IT. The entry above stopped quoting
                          // `LastSkip` for a swallowed slam and this line went on
                          // doing it, so the log and the verdict would have
                          // disagreed about the same event — which is the exact
                          // shape of the fault that produced `#3:drawn@80m`
                          // beside `slamDrewRing=False`. One idea, two sites.
                          + $" — {_slamRingSkips[_slamRingSkips.Count - 1]}"
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
            // ---- M18: somebody comes out with you ----
            //
            // MOVED AHEAD OF THE DEED, and the distance probe is what found
            // it. The run reported `dist=-1.0m`, which is the untouched
            // initial value — so at the moment the deed resolved, the
            // companion had NO WALKER AT ALL, not a distant one. Proximity was
            // never the problem.
            //
            // The cause is ordering inside one tick: the deed block sits some
            // four hundred lines above this one, so on the day a deed fires
            // the escort has not been recruited yet. My first guess blamed the
            // victim selection, my second blamed proximity, and both were
            // stories about geometry when the fault was a line number. The
            // probe that settled it prints one float.
            //
            // STAGED BEFORE THE DEED, ON PURPOSE. The whole claim of the
            // feature is that a companion is a witness by STANDING THERE, and
            // the only way a run can prove that is for one to be at the
            // player's shoulder when the deed resolves — then read their
            // sighting out of the ordinary witness record. If this ran after,
            // the gate below would be measuring nothing.
            //
            // The loyalty is raised first because `Escort.WillWalk` requires
            // 0.55 and a cold walker sits below it. That is staging the
            // PRECONDITION, not staging the result: the run still has to make
            // them agree, put them there, and produce the sighting through
            // `Witnesses.Resolve` like anybody else.
            if (!_companionStaged && _game != null && _npcs != null
                && _game.Gossip != null && _game.Gossip.Mill != null)
            {
                // THE NEAREST ELIGIBLE WALKER, NOT THE FIRST IN THE LIST.
                //
                // `companionSight` came back red on a commit that changed no
                // code at all — a queue edit — which is the definition of a
                // gate measuring luck rather than the game. `dist=23.8m` is the
                // reason, and the comment at the distance probe below had
                // already named it as the leading hypothesis and asked for
                // exactly this number: *"if it comes back at forty metres the
                // explanation is settled; if it comes back at two, the fault is
                // somewhere else entirely."* Twenty-four metres settles it.
                //
                // `Ask` has no proximity requirement, and this loop took
                // whoever came first in `_npcs`, so the escort was recruited
                // wherever she happened to be standing in the city. Picking the
                // nearest costs one pass and starts her at the player's
                // shoulder instead of across the district.
                NpcWalker pick = null;
                Gossiper pickG = null;
                float pickDist = float.MaxValue;
                foreach (var n in _npcs)
                {
                    if (n == null || n.DisplayName == "Ellis") continue;
                    var gg = _game.Gossip.Mill.Get(n.GossipId);
                    if (gg == null) continue;
                    float d = Vector3.Distance(n.transform.position, _player.transform.position);
                    if (d < pickDist) { pickDist = d; pick = n; pickG = gg; }
                }
                for (int once = 0; once < 1 && pick != null; once++)
                {
                    var n = pick;
                    var g = pickG;
                    g.Loyalty = 0.8;
                    g.Nerve = 0.6;
                    if (!_game.Companion.Ask(g, n, now.Day, _game.Player != null ? _game.Player.transform : null)) continue;
                    _companionRecruitDist = pickDist;
                    _companionStaged = true;
                    _companionWith = n.DisplayName;
                    Debug.Log($"SimDirector: companion — {n.DisplayName} walks with you "
                              + $"(loyalty {g.Loyalty:0.00}, walks above {Escort.WalksWithYouAbove:0.00})");
                    break;
                }
            }

            // AND THE DEED WAITS FOR HER — BUT NOT FOR EVER.
            //
            // The gate asserts that a companion is a full sighting BECAUSE OF
            // WHERE THEY STAND. Staging the act while she is twenty-four metres
            // away tests whether she happened to arrive, which is why this gate
            // fails on identical code. Plant the condition, never loosen the
            // bound.
            //
            // THE TIMEOUT IS NOT A SOFTENING, IT IS THE 5b HALF. A deed that
            // waits indefinitely for an escort who wandered off would stage
            // nothing, and `deeds=0` fails four other gates for a reason none
            // of them could name — a guard that blocks the good case, which is
            // the exact failure this project keeps shipping. So it waits two
            // days, then stages anyway and RECORDS how far she was, so "she was
            // there and saw nothing" and "she never arrived" stay different
            // findings.
            bool companionClose = _game == null || _game.Companion.Walking == null
                || Vector3.Distance(_game.Companion.Walking.transform.position,
                                    _player.transform.position) <= Perceivers.NearBandMetres;
            if (!companionClose && _deedsStaged < DeedsWanted && now.Day != _lastDeedDay
                && nearest != null && nearestDist <= Perceivers.NearBandMetres)
                _deedWaitedDays++;
            if (_deedsStaged < DeedsWanted && now.Day != _lastDeedDay
                && (companionClose || _deedWaitedDays >= 2)
                && nearest != null && nearestDist <= Perceivers.NearBandMetres)
            {
                _deedsStaged++;
                _lastDeedDay = now.Day;
                var weapon = Arsenal.Get("cosh");
                // THE COMPANION CANNOT BE THE VICTIM, and the first run of this
                // gate is what showed why. It came back `companion[with=Tanja
                // rung=-1 ... noted=0]`: Tanja was recruited, was escorting,
                // and produced no observation at all.
                //
                // Because she was standing at the player's shoulder she was
                // ALWAYS the nearest walker, so the sim staged its deed
                // against her — and `Witnesses.Resolve` skips the victim by
                // design (`Reaction.AsVictim` owns the target's account; a dead
                // man is not a bystander). The escort was excluded from the
                // witness list by the very thing that made her a witness.
                //
                // A staging fault, not a design fault, and exactly the shape
                // rule 3 warns about: the instrument was standing in the way of
                // the measurement.
                var victim = nearest;
                if (_game != null && _game.Companion.Walking == victim)
                {
                    victim = null;
                    float best = float.MaxValue;
                    foreach (var n in _npcs)
                    {
                        if (n == null || n == _game.Companion.Walking) continue;
                        float d = Vector3.Distance(n.transform.position, _player.transform.position);
                        if (d < best) { best = d; victim = n; }
                    }
                    if (victim == null) victim = nearest;   // nobody else: stage it anyway
                }
                var deed = Observe.DeedFor(weapon, $"sim-deed-{_deedsStaged}",
                                           "player", victim.DisplayName,
                                           actorFled: false, hadPrecursor: true);
                // WITH THE FAMILIARITY FUNCTION, which nothing has ever
                // supplied. Without it every witness scores 0.0 and
                // `Perception.IdRung`'s top rung — the one that carries a
                // NAME, and therefore the only one the consequence engine can
                // act on — is unreachable by construction. That is what
                // `deedBestRung=1` has been reporting: not that the street got
                // a poor look, but that nobody in the city has ever met the
                // protagonist.
                Witnesses.Resolve(deed, _player.transform, victim.transform.position,
                                  _game != null ? _game.FamiliarityWithPlayer : null);
                // M18. AND WHOEVER WAS AT YOUR SHOULDER WHEN YOU DID IT.
                //
                // Read off the witness record that was just produced, not from
                // a distance test here — the companion's sighting is an
                // ordinary `Observation` resolved by the same pass as
                // everybody else's, which is the entire design. See
                // `CompanionHost.NoteDeed` for why a proximity check in this
                // spot would be a second opinion about who saw what.
                // WHERE THE COMPANION ACTUALLY WAS, measured at the moment
                // the deed resolves.
                //
                // Two builds have now reported `companionSight rung=-1`: the
                // escort recruited, escorting, and producing no observation at
                // all. My first explanation was that she was being staged as
                // the deed's own victim, and fixing that changed nothing — a
                // guess that cost a round trip. The leading explanation now is
                // that `CompanionHost.Ask` has NO PROXIMITY REQUIREMENT, so
                // the sim recruits the first walker with a gossiper wherever
                // they happen to be in the city, marks them escorting, and
                // stages the deed before they have walked anywhere near the
                // player's shoulder.
                //
                // That is a hypothesis and it is not getting another build on
                // trust. This prints the distance. If it comes back at forty
                // metres the explanation is settled; if it comes back at two,
                // the fault is somewhere else entirely and I would have
                // "fixed" proximity for nothing.
                if (_game != null && _game.Companion.Walking != null && _player != null)
                    _companionDist = Vector3.Distance(
                        _game.Companion.Walking.transform.position, _player.transform.position);
                if (_game != null) _game.Companion.NoteDeed(deed.EventId);
                // AND THE COMPARISON THAT TESTS THE CLAIM. The design says a
                // companion is a full sighting BECAUSE OF WHERE THEY STAND,
                // through the same resolver as everybody else. That is a
                // statement about two numbers, not one: their rung, and the
                // best rung the rest of the street managed on the same act.
                // Recording only theirs would let a run where the whole street
                // got a clean look read as proof of a companion effect.
                foreach (var o in Witnesses.Last)
                {
                    if (o == null) continue;
                    if (o.WitnessId == _companionWith)
                    { if (o.Rung > _companionRung) _companionRung = o.Rung; }
                    else if (o.Rung > _companionStreetRung) _companionStreetRung = o.Rung;
                }
                int distinct = Witnesses.DistinctSlotSets();
                if (distinct > _deedSlotSets) _deedSlotSets = distinct;
                // ONE DEED'S BREAKDOWN, NOT THREE SEPARATE MAXIMA.
                //
                // These print adjacent — `deedWitnesses=53 deedEyesOpen=50
                // deedKnowsYou=41` — and that reads unavoidably as "of the 53
                // who saw it, 50 had their eyes open and 41 knew you". Taken
                // independently the subset relationship is not guaranteed: the
                // deed with the most witnesses need not be the deed with the
                // most open eyes, and the trio could describe three different
                // events while looking like one.
                //
                // Fourth site of peaks-from-different-instants found tonight,
                // and the first that predates me. The sweep that found it was
                // mechanical — list every field assigned by a max, then ask
                // which of them are printed next to each other — which is the
                // only reason it turned up rather than being tripped over.
                //
                // Anchored on the widest-witnessed deed, because that is the
                // event the line is describing.
                if (Witnesses.Saw > _deedWitnesses)
                {
                    _deedWitnesses = Witnesses.Saw;
                    _deedEyesOpen = Witnesses.EyesOpen;
                    _deedKnowsYou = Witnesses.KnowsYou;
                }
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
                    // WHO *THIS* WITNESS WOULD THINK OF, not whoever is first
                    // in the walker list.
                    //
                    // `Observe.Misattribute`'s own line is "a long coat, at
                    // night, near the docks is Nikos to somebody who EXPECTS
                    // Nikos" — expectation belongs to the person doing the
                    // misidentifying. This loop handed every witness the same
                    // arbitrary walker, so eight misnamings in a run all pointed
                    // at one person chosen by list position, and the mechanic
                    // that makes the street WRONG about you in interesting ways
                    // was producing one uniform wrongness.
                    //
                    // Second site of the fault fixed in the companion recruit
                    // twenty minutes ago: list order standing in for a real
                    // criterion. Found by grepping for the shape rather than by
                    // tripping over it.
                    //
                    // The expectation comes from the mill, which is where this
                    // game keeps what people think about. Whoever they hold
                    // their strongest rumour about IS who comes to mind — no
                    // new state, no new number, and it makes the misnaming
                    // different per witness for the first time.
                    string expected = null;
                    var wg = _game != null && _game.Gossip != null && _game.Gossip.Mill != null
                        ? _game.Gossip.Mill.Get(o.WitnessId) : null;
                    if (wg != null)
                    {
                        double best = -1;
                        foreach (var r in wg.Rumors)
                        {
                            if (r == null || r.Content == null) continue;
                            string subj = r.Content.Subject;
                            if (string.IsNullOrEmpty(subj) || subj == "player"
                                || subj == o.WitnessId || subj == "Ellis") continue;
                            if (r.Confidence > best) { best = r.Confidence; expected = subj; }
                        }
                    }
                    // Nobody on their mind: fall back to the nearest walker, so
                    // a witness who holds nothing still has somebody plausible
                    // to be wrong about rather than nobody at all.
                    if (expected == null && _npcs != null)
                    {
                        float near2 = float.MaxValue;
                        foreach (var n in _npcs)
                        {
                            if (n == null || n.GossipId == o.WitnessId
                                || n.DisplayName == "Ellis") continue;
                            float d2 = Vector3.Distance(n.transform.position, _player.transform.position);
                            if (d2 < near2) { near2 = d2; expected = n.DisplayName; }
                        }
                    }
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
                var g0 = _game.Gossip.Mill.Get(n.GossipId);
                if (g0 == null || g0.Leashed) continue;
                float d = Vector3.Distance(n.transform.position, _player.transform.position);
                if (d < best) { best = d; nearest = n; }
            }
            if (nearest == null || best > 3.5f) return;

            var g = _game.Gossip.Mill.Get(nearest.GossipId);
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
            // AND THE CROWDED SPOT IS NOW CHOSEN WITH THE PREDICATE THAT WILL BE
            // ASKED ABOUT IT, which is the other half of the same repair.
            //
            // Counting neighbours within `Rung2MarkMetres` is not the question
            // `EvidenceHost.Dispose` asks. That one wants range AND an
            // unobstructed line AND the watcher facing within half the field of
            // view — so a knot of people all looking the other way maximises the
            // count and fails the test. The selection criterion and the test
            // criterion were different questions, which is how both gates came
            // back `seen=False` against `seen=False` on a street with forty-two
            // people in it.
            //
            // Ordered by crowd and then FILTERED by `Watched`, rather than
            // `Watched`-tested exhaustively: the predicate raycasts, and asking
            // it about every one of forty-two positions from every one of
            // forty-two people is a few thousand casts for an answer the first
            // candidate usually gives. Falls back to the fullest spot when
            // nobody in the city can see anywhere, and says so, because a
            // fallback that looks like a success is the thing this file exists
            // to stop.
            Vector3 crowded = _player.transform.position;
            int most = -1;
            _crowdedIsWatched = false;
            if (_npcs != null)
            {
                var byCrowd = new List<(int near, Vector3 pos)>();
                foreach (var n in _npcs)
                {
                    if (n == null) continue;
                    int near = 0;
                    foreach (var o in _npcs)
                        if (o != null && o != n
                            && Vector3.Distance(o.transform.position, n.transform.position)
                               < Perception.Rung2MarkMetres) near++;
                    byCrowd.Add((near, n.transform.position));
                    if (near > most) { most = near; crowded = n.transform.position; }
                }
                byCrowd.Sort((a, b) => b.near.CompareTo(a.near));
                foreach (var cand in byCrowd)
                {
                    if (!EvidenceHost.AnybodyWatching(cand.pos, _npcs)) continue;
                    crowded = cand.pos;
                    most = cand.near;
                    _crowdedIsWatched = true;
                    break;
                }
            }
            // HOW CROWDED THE CROWDED SPOT ACTUALLY WAS, which nothing has
            // ever asked. Both these gates compare a watched place against an
            // unwatched one, and both failed together on a run reading
            // `risk=0.30` against `risk=0.30` and an accident available in
            // company — all three of which are what you get when the crowded
            // spot has nobody at it. The quiet spot has printed its emptiness
            // since the day it was searched for rather than borrowed; its
            // opposite number never printed anything.
            _crowdedWatchers = most;
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
            // THE DAY, because without it a redirect is invisible here and the
            // sim would report Ellis asking about you on a run where she had
            // been pointed somewhere else that morning.
            _provEllisAsking = EvidenceHost.EllisIsAskingAboutYou(
                _game.Homicides, _game.Gossip != null ? _game.Gossip.Mill : null, _game.Now.Day);

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
            // the decision at the door is a real one, and the capacity rule
            // says so rather than this file deciding it.
            //
            // THIS COMMENT USED TO SAY "a razor is Damning, a cosh is
            // Concealable" AND THE RAZOR IS NOT. Measured against `Arsenal`
            // rather than remembered: cosh and razor are BOTH `Concealable` at
            // frisk cost 0.35, and the bat is `Impossible` at 1.00. The razor's
            // sharp edge is `MarksYou`, which is a different axis entirely and
            // is why it is the weapon the blood probe uses. Nothing downstream
            // was wrong — the reason written beside it was.
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
                // KEPT, because the bat is picked up again later in the run and
                // `Traces` has no lookup by id — `Acquire` mints one. Calling
                // it twice would have made a SECOND bat, left the first at
                // home, and printed a coat that reads correctly while
                // describing an object nobody is holding.
                _simRazor = razor; _simBat = bat;
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

            // ---- and then the player carries it where people can see ----
            //
            // RULE 5b's TWIN: A GUARD NEEDS A RUN IN WHICH THE THING IT ASSERTS
            // CAN HAPPEN. `Notice.What` learned to see a carried weapon tonight
            // and would have reported nothing for ever, because the coat probe
            // above asks for the bat THIRD and `Arsenal.Fits` refuses it: a
            // cosh and a razor are already on, and an `Impossible` weapon only
            // fits when it is one of at most two things. So `weaponVisible`
            // was wired to a flag that could not become true — the wiring would
            // have read exactly like the literal it replaced.
            //
            // NOT BY LOOSENING THE COAT RULE, which is the thing rule 2
            // forbids, and not by reordering the probe above — the choice gate
            // needs three objects that cannot all come, and its numbers are
            // captured at that instant. The player simply leaves the razor
            // behind and picks the bat up, which is a decision a player makes
            // and the one the file's own comment describes.
            //
            // AFTER THE FRISK, gated on `_friskStaged` rather than on merely
            // sitting lower in the method — the frisk block is skipped
            // entirely while `Gossip` is null, so source order is not the
            // guarantee it looks like.
            //
            // AND THE ORDER IS LOAD-BEARING, measured rather than assumed:
            // `Coat.WorstFind` is 0.35 with the cosh and the razor on and 1.00
            // once the bat replaces the razor, because an `Impossible`
            // concealment cannot be missed. Swapping first would have tripled
            // `_friskFound`, moved a landed gate number, and done it while
            // planting a condition that has nothing to do with frisking.
            // AND AFTER THE WASH, BECAUSE THE BAT SUPPRESSES THE BLOOD.
            //
            // `weaponNotices=157 bloodNotices=0` on `e7953a7`, and those two
            // are not independent readings of one street: `Notice.What` returns
            // `WeaponVisible` on its FIRST line and only reaches
            // `BloodOnClothes` if the weapon check fails. So from the instant
            // this swap runs, no walker in the game can ever classify the
            // player as bloodied again — and the zero is my own staging, not a
            // fact about blood.
            //
            // That is the two-numbers-from-one-variable trap: printing them
            // side by side reads as "the street sees weapons and not blood",
            // and the truth is that one is a gate in front of the other.
            //
            // `_washTried` is the natural boundary. The stain is taken by the
            // cut, offered to everybody near enough to see it, and washed
            // between two and four in the morning; gating on it gives blood the
            // whole of its own window and gives the bat every hour after. Both
            // numbers become readable and neither is invented.
            // AND A FALLBACK, BECAUSE I JUST GATED A PROBE ON SOMETHING THAT
            // MIGHT NEVER HAPPEN.
            //
            // `_washTried` is only set inside `if (PlayerStain != null)` and
            // only between two and four in the morning, and the stain only
            // exists if the staged cut found a walker near the player. No
            // walker, no cut, no stain, no wash — and the bat would never be
            // carried at all, silently killing `weaponNotices`, which is the
            // reading this whole staging exists for. That is rule 5b's twin
            // walked into within a minute of applying it: a probe that only
            // fires on a lucky run is not a probe.
            //
            // Two days is the whole blood window and more. The run reaches day
            // fifteen, so the bat is always carried and blood always gets first
            // refusal on its own hours.
            if (!_batStaged && _carryStaged && _friskStaged
                && (_washTried || now.Day > CarryStagesOnDay + 1))
            {
                _batStaged = true;
                if (_simRazor != null) CoatHost.Store(_simRazor);
                _batTook = _simBat != null && CoatHost.Carry(_simBat);
                // REFRESHED HERE RATHER THAN READ. `ShowingWeapon` is a cache
                // the population pass rebuilds once a second, so reading it in
                // the frame that changed the coat would report the previous
                // second's coat — and `batCarried=False` beside `batTook=True`
                // is exactly the self-contradicting pair that gets a number
                // deleted rather than explained.
                CoatHost.RefreshShowingWeapon();
                _batCarried = CoatHost.ShowingWeapon;
                Debug.Log($"SimDirector: the bat — took={_batTook} showing={_batCarried}, "
                          + $"on me {CoatHost.OnMe.Count}, at home {CoatHost.AtHome.Count}");
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
                // `familiarityWithActor` is the VICTIM's own — how well the
                // person being cut knows who cut them — and `familiarityOf` is
                // every bystander's. Two different people, two parameters, and
                // the second has never been passed by anything.
                var cut = ViolenceHost.Commit(razor, _player.transform, nearestForThreat,
                                              "sim-cut", lethal: false, now: now,
                                              harm: _game.Harm, familiarityWithActor: 0.2,
                                              familiarityOf: _game != null
                                                  ? _game.FamiliarityWithPlayer : null);
                // ONTO THE DONE LINE TOO. `marked` is whether cutting somebody
                // left a mark on YOU and `saw` is whether anybody perceived it
                // — the two facts that decide whether violence has a social
                // cost, which is the pillar this whole system serves. Both
                // printed only here, on a line the verdict does not carry, so
                // neither has ever been readable from a build.
                _cutMarkedYou = cut?.MarkedYou;
                _cutSawSomething = cut?.SawSomething;

                // AND THE STREET LEARNS WHO YOU ARE — the one place in the
                // project where a real act pays a reputation cost.
                //
                // APPLIED HERE AND NOT INSIDE `Commit`, which is where I put it
                // first. Two things are true at once: `ViolenceHost` is static
                // and has no game in scope (that cost a round trip, CS0118),
                // and the OTHER caller of `Commit` is `MeasurePlace`, which
                // commits the same killing three times to compare an alley with
                // a market. That is an instrument. Had the reputation been
                // charged inside `Commit`, every run would have made the player
                // notorious for three murders nobody committed, and the number
                // would have looked plausible.
                if (_game != null && cut != null)
                {
                    _game.Campaign.Noted(cut.Notoriety);
                    _notorietyApplied++;
                }
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
                // ONCE, and held. `HandAnchor` builds a GameObject the first
                // time it is asked, so calling it again for the log line would
                // be a second anchor on the same wrist.
                var hand = PlayerHand();
                // THREE OUTCOMES, NOT ONE, AND THE ORDER IS CHOSEN.
                //
                // `complied=0` and `called=0` across 136 kept runs — not
                // because the verbs are broken but because one staged threat at
                // one nerve value can only ever reach one branch of a
                // five-branch rule. Rule 5b's twin: the run has to supply the
                // condition.
                //
                // The inputs are swept off `Arsenal.Brandish` locally rather
                // than guessed, and every outcome is reachable with a cosh:
                //
                //   Comply         nerve 0.1, in private, reputation 0.7
                //   CallTheBluff   nerve 0.6, in public,  reputation 0.1
                //   FleeScreaming  nerve 0.2, in public,  reputation 0.7
                //
                // THE REAL ONE GOES LAST ON PURPOSE. `Brandish` writes the
                // target's stance — `Watches` for a complier, `Confronts` for
                // somebody calling the bluff, `Avoids` for a screamer — and a
                // confronting NPC blocks the player's path under §6.4. Running
                // the fiction's threat last leaves exactly the stance today's
                // runs leave, so two new readings cost nothing downstream.
                ViolenceHost.Brandish(cosh, nearestForThreat, _player.transform.position,
                                      inPublic: false, reputationForViolence: 0.7,
                                      targetNerve: 0.1, hand: hand);
                ViolenceHost.Brandish(cosh, nearestForThreat, _player.transform.position,
                                      inPublic: true, reputationForViolence: 0.1,
                                      targetNerve: 0.6, hand: hand);
                var t = ViolenceHost.Brandish(cosh, nearestForThreat,
                                              _player.transform.position,
                                              inPublic: true,
                                              reputationForViolence: 0.7,
                                              targetNerve: 0.2,
                                              // THE PLAYER'S OWN HAND, so the
                                              // object is drawn on the body the
                                              // camera can see rather than at a
                                              // world position nothing is at.
                                              hand: hand);
                // `hand=` is in the line because its absence is what a null hand
                // looks like from here — the threat resolves perfectly and
                // nothing is ever drawn, which is how M17.1's body swap took the
                // gate down without touching a line of violence code.
                Debug.Log($"SimDirector: brandished a cosh at {nearestForThreat.DisplayName} -> {t}"
                          + $" (canUndraw={ViolenceHost.CanUndraw()}, "
                          + $"hand={(hand != null ? hand.name : "NULL")}, "
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

            StageAKilling(now, nearestForThreat);
        }

        /// A BODY REACHES THE REGISTER, AND ONE NEVER HAS.
        ///
        /// `GameController.RecordKilling` is the only path into `HomicideBook`
        /// and it has no callers, so `Pressure` returns zero, `Stage` returns
        /// `None`, and `inquiry=None` sits on all 131 kept verdicts. Everything
        /// downstream of it has therefore never executed once: Ellis being
        /// summoned by a body rather than by heat, the suspicion floor, the
        /// rumour half-life changing, the paper naming you, and the redirect
        /// having anything to relieve. One missing call, a whole stage of the
        /// game, and no instrument was asking — `ReachCheck` covers public CORE
        /// APIs and this is Game-layer, which is why `lint-unreached.py` was
        /// written and why this was the largest thing it found.
        ///
        /// AFTER THE AUDIT HAS CLOSED, and that gate is the whole safety
        /// argument rather than a convenience:
        ///
        ///   `Police.ForcesActThree` opens Act III at `Investigation` and up.
        ///   `Police.BarsQuietExit` sets `LedgerState.Hunted` at `Manhunt`.
        ///
        /// Both are read while the act is being decided. `ActThree.Result` is a
        /// STORED field — checked, not assumed — set once when the audit
        /// closes, and `Opened` is already true by then. So a body filed after
        /// that instant cannot open an act that is open, cannot rewrite an
        /// ending that is written, and cannot turn `actThree` or `ending` red.
        /// Filing one EARLIER could do all three, which is why the first
        /// version of this note said "record two bodies, not three" and was
        /// reasoning about the wrong risk entirely.
        ///
        /// AND THE ARITHMETIC IS NOT THE ONE I WROTE DOWN. `PerBody` is 0.4, so
        /// bodies alone go 0.4 / 0.8 / 1.2 and two is the safe number. But
        /// `Pressure` adds `NamedWeight * bestConfidence` for any living
        /// witness who can name you, `FileWith` writes them in at
        /// `Violence.BodyConfidence`, and that constant is 1.0 — measured, not
        /// remembered. So ONE body seen by ONE person is 0.4 + 0.6 = exactly
        /// `ManhuntAt`. There is no number of bodies that is safe before the
        /// audit closes, and the day-count fix would not have helped.
        ///
        /// NOTHING IS GATED ON THE RESULT THIS BUILD. The reading comes first:
        /// `inquiry`, the body count, who saw and who only knew. A gate written
        /// before the number has landed is a threshold nobody measured.
        void StageAKilling(GameTime now, NpcWalker victim)
        {
            if (_homicideStaged || _game == null || _player == null) return;
            if (victim == null || !_game.ActThree.AuditClosed) return;
            // NOT THE CREW AND NOT THE SUCCESSOR. The nearest walker is
            // whoever the walk left standing there, and killing the person the
            // handover went to would break a gate for a reason that has nothing
            // to do with homicide.
            string id = victim.DisplayName;
            if (string.IsNullOrEmpty(id)) return;
            if (_game.Empire.CrewOf(id) != null) return;
            if (id == _game.ActThree.SuccessorId) return;

            _homicideStaged = true;
            var cosh = Arsenal.Get("cosh");
            var killed = ViolenceHost.Commit(cosh, _player.transform, victim,
                                             "sim-killing", lethal: true, now: now,
                                             harm: _game.Harm,
                                             familiarityWithActor: 0.0,
                                             familiarityOf: _game.FamiliarityWithPlayer);
            if (killed == null) return;

            // THE BRIDGE, and it is the reason the register was unreachable.
            // `RecordKilling` asks for the shape `Violence.Saw` returns, and
            // `lint-usings.py` fails the build if a Game-layer file calls that
            // function. `ViolenceHost.WitnessesOf` translates the observations
            // the modern path actually produces.
            var witnesses = ViolenceHost.WitnessesOf(killed.Seen);
            _homSaw = 0; _homKnew = 0;
            foreach (var w in witnesses) { if (w.Occluded) _homKnew++; else _homSaw++; }

            // WHAT THE MILL DID DURING THE FILING, MEASURED ACROSS THE CALL.
            //
            // `homSawStored=32 homHoldsIt=0` on `52037ba` located the break
            // between `FileWith` writing and `BestOfValue` reading — and then
            // every link in it checked out by reading, which is where this
            // project's rules say stop reading. A probe of the same sequence
            // against real Core (32 agents, `FileWith`, `BestOfValue`) returns
            // 32 of 32, so Core is innocent and the difference is here.
            //
            // `witnessDropped` is a LIFETIME total on the mill and it read 2,
            // which looks like proof that the 32 were accepted — but a lifetime
            // count cannot say what happened during one call, and reading it as
            // though it could is the frozen-cumulative fault of 4 August. These
            // two are the same counters sampled either side of `RecordKilling`,
            // so the delta belongs to the filing and nothing else.
            var millAt = _game.Gossip?.Mill;
            int offeredBefore = millAt != null ? millAt.WitnessesOffered : -1;
            int droppedBefore = millAt != null ? millAt.WitnessesDropped : -1;

            _game.RecordKilling(id, id, witnesses);

            var millAfter = _game.Gossip?.Mill;
            _homFileOffered = millAt != null && millAfter != null
                ? millAfter.WitnessesOffered - offeredBefore : -1;
            _homFileDropped = millAt != null && millAfter != null
                ? millAfter.WitnessesDropped - droppedBefore : -1;
            // AND WHETHER IT IS EVEN THE SAME MILL. The write goes through
            // `GameController._gossip.Mill` and the read through
            // `_game.Gossip?.Mill`; if a save, a load or a new day swaps the
            // object between them, every other number here is honest and the
            // belief is simply in a mill nobody asks. One reference comparison
            // settles a question three counters cannot.
            _homSameMill = millAt != null && ReferenceEquals(millAt, millAfter);
            _homVictim = id;
            _homBodies = _game.Homicides.BodyCount;
            _homPressure = _game.Homicides.Pressure(_game.Gossip?.Mill, _game.IsAlive, now.Day);
            _homInquiry = _game.PoliceInquiry;


            // AND WHICH OF THEM WOULD ACTUALLY GO TO THE POLICE, which is the
            // asymmetry the design turns on and a question nothing has ever
            // been able to ask.
            //
            // `EvidenceHost.WhoWouldTalk` had no caller for the same reason
            // `RecordKilling` had none: it takes the people who WATCHED, and
            // until this method existed nobody had ever watched anything the
            // register knew about. Rule 5b's twin — a guard needs a run in
            // which the thing it asserts can happen, and filing a body is what
            // supplies the condition.
            //
            // Its own comment is the claim being measured: "not the disloyal
            // ones — the ones with the least nerve AND the least to lose, and
            // that asymmetry is the interesting part: the man who likes you
            // least is not the man who talks." `homSaw` is the denominator and
            // sits beside it, so a zero says which kind of zero it is.
            var filed = _game.Homicides.Of(id);
            _homWouldTalk = filed != null
                ? EvidenceHost.WhoWouldTalk(_game.Gossip?.Mill, filed.SawYouDoIt).Count
                : 0;

            // AND HOW MANY OF THE WATCHERS CAN ACTUALLY NAME YOU, which the
            // first filed body in this project's history says is NONE.
            //
            // `0720f52`: `homSaw=29 homKnew=17 homPressure=0.40`. Twenty-nine
            // people watched a killing and the pressure is `PerBody` exactly —
            // bodies only, with no named term at all. `Pressure` adds
            // `NamedWeight * best` for any LIVING witness who can name you, and
            // `FileWith` writes each of them in at `Violence.BodyConfidence`,
            // which is 1.0, so one witness alone should have taken it to
            // `ManhuntAt`. It did not, so `LiveWitnesses` came back empty.
            //
            // `GossipMill.Witness` is why: `var w = Get(witnessId); if (w ==
            // null) return;` — a witness who is not a mill AGENT is dropped
            // silently, and `Get` never creates one. So a murder in front of a
            // crowd files exactly like a murder nobody saw.
            //
            // THE ARITHMETIC IS WHAT FOUND IT, and only because both numbers
            // were printed. `homPressure=0.40` on its own reads as a correct
            // low-pressure answer; beside `homSaw=29` it is impossible. This
            // makes it a stated fact rather than a subtraction: `homNamed` is
            // the count of watchers the register can actually hear from, and a
            // zero of it beside a large `homSaw` is the fault in one line.
            _homNamed = filed != null
                ? _game.Homicides.LiveWitnesses(_game.Gossip?.Mill, _game.IsAlive).Count
                : 0;

            // AND WHERE THE 32 BECOME 0, BECAUSE READING THE CODE HAS STOPPED
            // NARROWING IT.
            //
            // `e7953a7`: `witnessOffered=790 witnessDropped=2` — the mill takes
            // 788 of 790 now, so the id fix landed. `homSaw=32 homWouldTalk=5
            // homNamed=0 homPressure=0.40`. Those cannot all be true of the
            // same story by reading alone:
            //
            //   `homWouldTalk` walks `SawYouDoIt`, calls `mill.Get(id)` and
            //   asks `Watched.WouldTalkToPolice` — it found five, so the list
            //   is populated AND those ids have agents.
            //
            //   `LiveWitnesses` walks the same list, gets the same agents, and
            //   additionally asks `BestOfValue(TopicKey, "true")` for a
            //   confidence at or above `TestimonyGrade`. It found none.
            //
            // So the agents exist and the belief does not, while `FileWith`
            // writes exactly that belief at `Violence.BodyConfidence` = 1.0 and
            // only two witnesses were refused all run. Three readings that
            // cannot be reconciled by staring at them, which is the point at
            // which this project's own rules say stop staring.
            //
            // `homSawStored` is what the REGISTER kept, against `homSaw` which
            // is what the bridge offered; `homHoldsIt` is how many of those
            // agents hold the belief at ANY confidence. Between them they say
            // which of the three links is broken, and no combination of them is
            // ambiguous.
            _homSawStored = filed != null ? filed.SawYouDoIt.Count : 0;
            _homHoldsIt = 0;
            _homHasAgent = 0;
            _homAnyRumour = 0;
            var millNow = _game.Gossip?.Mill;
            if (filed != null && millNow != null)
                foreach (var wid in filed.SawYouDoIt)
                {
                    var g = millNow.Get(wid);
                    // THREE QUESTIONS, NOT ONE, because `homHoldsIt=0` is a zero
                    // with no denominator and cannot say which of them failed.
                    // `homHasAgent` is "the mill knows this id at all",
                    // `homAnyRumour` is "that agent carries anything whatever",
                    // and `homHoldsIt` is "it carries THIS belief". A run where
                    // the first is 0 is an id-space fault; where the second is 0
                    // the agents are empty shells; where only the third is 0 the
                    // topic key is wrong. Nothing else distinguishes them, and
                    // reading the code distinguished none of them.
                    if (g == null) continue;
                    _homHasAgent++;
                    if (g.Rumors.Count > 0) _homAnyRumour++;
                    if (g.BestOfValue(filed.TopicKey, "true") != null) _homHoldsIt++;

                    // AND WHAT THE FIRST WITNESS ACTUALLY HOLDS, SPELLED OUT.
                    //
                    // `a050815` closed every other branch: homSameMill=True,
                    // homFileOffered=49 homFileDropped=2 so the writes landed,
                    // homHasAgent=21 homAnyRumour=21 so the agents exist and
                    // carry rumours — and homHoldsIt=0. By the three-way split
                    // written here yesterday that means the topic key is wrong,
                    // and reading the code says it cannot be: `FileWith` writes
                    // `Fact("player", "killed_" + VictimId, "true")` and this
                    // asks `"player.killed_" + VictimId`, which are the same
                    // string, and a local probe of that pair against real Core
                    // returns 32 of 32.
                    //
                    // So stop deducing and print both sides. The key being
                    // asked for, and the keys one witness is actually holding.
                    // Whatever the mismatch is, it is visible in one line and
                    // invisible to every count taken so far.
                    //
                    // Bracketed and comma-joined because a verdict value may
                    // not contain a space, and the reader consumes a bracketed
                    // run whole.
                    if (_homTopics.Length == 0 && g.Rumors.Count > 0)
                    {
                        var sb = new System.Text.StringBuilder();
                        foreach (var r in g.Rumors)
                        {
                            if (r?.Content == null) continue;
                            if (sb.Length > 0) sb.Append(',');
                            sb.Append(r.Content.Subject).Append('.')
                              .Append(r.Content.Predicate).Append('=')
                              .Append(r.Content.Value);
                            if (sb.Length > 220) { sb.Append(",..."); break; }
                        }
                        _homTopics = sb.ToString().Replace(' ', '_');
                    }
                }
            _homWantKey = filed != null ? filed.TopicKey.Replace(' ', '_') : "none";
            Debug.Log($"SimDirector: killed {id} — filed {_homBodies} body(ies), "
                      + $"{_homSaw} saw it and {_homKnew} only knew of it, "
                      + $"{_homWouldTalk} of the watchers would talk, {_homNamed} can name you, "
                      + $"pressure {_homPressure:0.00}, inquiry {_homInquiry}, "
                      + $"Ellis={_game.EllisSpawned}");
        }

        /// The transform a held object hangs off — asked of the RIG, which is
        /// the one thing that knows which kind of body this person ended up
        /// with.
        ///
        /// THE PREVIOUS VERSION OF THIS METHOD WAS A REGRESSION I SHIPPED. It
        /// read `_player.GetComponent&lt;Mannequin&gt;()`, and its comment said the
        /// Humanoid hand would replace it "so nothing here changes" — which was
        /// exactly backwards. When `RealBody` gave the player a bought skeleton
        /// there was no `Mannequin` to find, this returned null, `Brandish` was
        /// handed a null hand, and the run failed with
        /// `threat[... drawn=0 object=none]`. The gate was right and the threat
        /// was right; the hand lookup had been written against one tier and
        /// asserted about the other.
        /// Is the player's spawn capsule still rendering on top of its body?
        ///
        /// Read live rather than latched at spawn, because the question is what
        /// the camera sees now, and a renderer re-added by anything later is the
        /// same fault arriving by a different door.
        bool PlayerPrimitiveShowing()
        {
            if (_player == null) return false;
            var mr = _player.GetComponent<MeshRenderer>();
            return mr != null && mr.enabled;
        }

        Transform PlayerHand()
        {
            if (_player == null) return null;
            var rig = _player.GetComponentInChildren<CharacterRig>();
            return rig != null ? rig.HandAnchor : null;
        }

        /// §4.7's headline claim, staged on the street the run actually built.
        ///
        /// The same act, three times, at three arrangements of people found by
        /// measurement rather than authored as coordinates. Every number the
        /// witnesses are judged on is the live world; only the act is
        /// synthetic, exactly as the Phase 2 deed staging is.
        /// STAND HIM AT A LIVE CALLBOX WHEN THE RIVAL RINGS.
        ///
        /// `summonsTaken=0` in every run that carries the key, and after the
        /// same-instant fix the reason is finally trustworthy: `summonsMissWhy`
        /// says a line WAS live and he was not near it, describing nine at
        /// night rather than the day close thirteen hours away. So the mechanic
        /// works and its condition has never occurred — and the rule for that
        /// is to plant the condition, never to loosen the bound.
        ///
        /// ONE HOUR, ONE DAY, AND ONLY AS A TARGET. It steers him toward a box
        /// on the ring hour of one day and does not teleport him — a harness
        /// that puts the player somewhere impossible proves nothing about a
        /// mechanic a real player has to reach on foot. If he does not make it,
        /// `summonsMissWhy` says so and that is a real answer about distance
        /// rather than a rigged pass.
        ///
        /// It runs LAST among the stagers and writes `target` by reference, so
        /// it overrides the day's job for that hour rather than fighting it —
        /// and only on `SummonsWalkDay`, so the other fourteen days keep
        /// exercising the routines this would otherwise trample.
        void StageTheCallbox(GameTime now, ref Vector3 target)
        {
            if (now.Day != SummonsWalkDay) return;
            if (now.Hour != Ledger.Core.Summoning.RingsAtHour) return;
            if (!_game.TryLiveLineSpot(now, out var box)) { _callboxWhy = "noLiveLine"; return; }
            target = new Vector3(box.x, 0, box.z);
            _callboxStaged = true;
            _callboxWhy = "steered";
        }

        /// Which day the sim walks the player to a telephone. Late enough that
        /// the drops, the frisk and the killing have all had their run, so this
        /// cannot starve a probe that came first.
        const int SummonsWalkDay = 12;
        bool _callboxStaged;
        string _callboxWhy = "hourNeverCame";

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
                                                familiarityWithActor: 0.0,
                                                familiarityOf: _game.FamiliarityWithPlayer);
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
            // ONCE, HERE, because this is the one place in the run that is
            // guaranteed to be night with the street built — which is the only
            // condition under which a window glow is a thing that exists. Six
            // extra 640x360 renders on top of the sampler's existing dozen.
            if (!_windowGlowMeasured) { _windowGlowMeasured = true; MeasureWindowGlow(); }
            // AND WHAT A SKINNED CROWD WOULD COST, once, in the same place —
            // the street is built and the camera is where the player is, which
            // is the only condition under which the answer means anything.
            if (!_crowdCostMeasured && _game != null && _game.Player != null)
            {
                _crowdCostMeasured = true;
                RealBody.MeasureCrowdCost(_game.Player.transform);
                Debug.Log($"SimDirector: [series] crowdCost {RealBody.CostSeries}");
                // AND THE LEDGER SCREEN, IN WORDS. Everything built tonight
                // ships into that panel and none of it has ever been read back.
                if (_game.Ui != null)
                    Debug.Log($"SimDirector: [panel] ledger — {_game.Ui.LedgerWords()}");
                // AND WHAT IS STANDING NEXT TO HIM. There is a glowing cube at
                // the player's chest in the night still and no way to tell what
                // it is from the picture.
                Debug.Log(SceneAudit.Near(_game.Player.transform.position + Vector3.up));
            }
        }

        bool _windowGlowMeasured;
        bool _crowdCostMeasured;

        /// Every noon/night pair from the run, so the next threshold can be
        /// chosen from data instead of from a guess.
        string _lumaSeries = "";
        double _aoSpread = -1, _grainSpread = -1;
        double _aoFraction = -1, _aoDrop = -1;
        /// Every round's fraction, not just the largest. See `aoOk`.
        readonly List<double> _aoFractions = new List<double>();

        /// The middle round, for the question a maximum cannot answer.
        double AoTypicalFraction
        {
            get
            {
                if (_aoFractions.Count == 0) return _aoFraction;
                var s = new List<double>(_aoFractions);
                s.Sort();
                return s[s.Count / 2];
            }
        }
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
        /// Printed once per run; null until then. A string rather than a bool,
        /// so the done line can carry the series itself and a run that skipped
        /// the probe says so instead of reporting zeros.
        string _ringGrowth;

        /// The same A/B at an arbitrary radius. `RingSeenWith` hardcoded
        /// `RingProbeRadius`, which is right for the "does it draw at all"
        /// question and cannot ask "does it still read as a ring at sixty-four
        /// metres".
        (double fraction, double rise) RingSeenAt(Camera cam, double radius) =>
            RingSeenWith(cam, NoiseRing.Paint.Ledger, NoiseRing.Lay.FlatBillboard, radius);

        (double fraction, double rise) RingSeenWith(Camera cam, NoiseRing.Paint paint,
                                                    NoiseRing.Lay lay = NoiseRing.Lay.FlatBillboard,
                                                    double radius = -1)
        {
            var probe = NoiseRing.ForVerification(_player.transform.position,
                                                  radius > 0 ? radius : RingProbeRadius,
                                                  paint, lay);
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
                // THE CAMERA'S OWN ROTATION, not a `LookRotation` along its
                // forward. Same result whenever it works, and it cannot fail.
                //
                // One-argument `LookRotation` takes world up as its hint, so a
                // camera looking steeply down gives a degenerate basis, returns
                // identity, and leaves this quad EDGE-ON — invisible. The
                // control would then read zero, which is exactly the
                // "the A/B itself is blind" verdict it exists to rule out, and
                // it would be believed because that is what a control reading
                // zero means. A false negative that is self-confirming.
                //
                // It works today (`ringControl=19.85`) and works only because
                // the review camera happens not to be steep enough. Found by
                // grepping every `LookRotation` in the project after fixing the
                // same degeneracy twice by accident — the nameplates and then
                // the speech bubbles — rather than a third time by luck.
                go.transform.rotation = cam.transform.rotation;
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

                // HOW A RING BEHAVES AS IT GROWS, PRINTED ONCE.
                //
                // `review_day1_night.jpg` is a white band edge to edge with the
                // city behind it: the ring at its true `ringMax=148.1` metre
                // radius, which seen from inside is a straight line rather than
                // a circle. Hiding it from the stills answered the screenshot;
                // it did not answer the game, because a player standing there
                // sees the same band.
                //
                // The geometric argument is that a circle stops reading as one
                // when its curvature falls below what the eye can pick out —
                // the sagitta of a chord L on radius R is about L squared over
                // 8R, so thirty metres of a 148-metre ring bows by 0.76m and is
                // a line. That says a fade is wanted; it does not say WHERE,
                // and picking a radius to fade over would be inventing a
                // threshold (rule 2).
                //
                // So this prints what each radius actually PUTS ON SCREEN,
                // through the same A/B the ring's own evidence already uses.
                //
                // AND THE ANSWER IS THAT THIS METRIC CANNOT TELL, which is
                // worth more than a number forced out of it. The series at
                // 6b64b40:
                //
                //     r=4  1.14%   r=16  2.04%   r=64  1.93%
                //     r=8  1.09%   r=32  1.27%   r=128 1.00%
                //
                // No trend. A 128-metre ring covers about as much screen as a
                // four-metre one, because a ring is a THIN LINE — its pixel
                // count is its length times its width, and as the radius grows
                // most of the circle leaves the frame entirely. Coverage was
                // the wrong quantity: the night still's band across the whole
                // image is only one or two percent of pixels, exactly like a
                // small ring nearby.
                //
                // Which leaves the geometric argument standing alone, and it is
                // a DERIVATION rather than a measurement — labelled as such
                // because rule 2 is about not dressing one up as the other. The
                // sagitta of a chord L on radius R is about L squared over 8R,
                // so a thirty-metre visible span bows by 0.76m at R=148 and by
                // 2.8m at R=40. Below roughly forty metres the curve is legible
                // as a curve; above it the shape stops carrying its meaning.
                //
                // Left unfaded for now, deliberately. Acting on a derivation
                // when the measurement said "cannot tell" is how thresholds get
                // defended instead of read, and the ring is already out of the
                // stills. The series stays so a better metric — arc curvature
                // in screen pixels, not coverage — can be compared against it.
                if (_ringGrowth == null)
                {
                    var g = new System.Text.StringBuilder("SimDirector: [series] ringGrowth");
                    foreach (double r in new[] { 4.0, 8.0, 16.0, 32.0, 64.0, 128.0 })
                    {
                        var (f2, _) = RingSeenAt(cam, r);
                        g.Append($" r={r:0}[seen={100 * f2:0.0000}%]");
                    }
                    _ringGrowth = g.ToString();
                    Debug.Log(_ringGrowth);
                }

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
            // less body detail — and since 15 Aug no bloom and no ambient
            // occlusion either (the post stack joined the preset). If that
            // renders the same frame, the whole preset is a label.
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
            // AND EVERY ROUND KEPT, because the gate asks two questions of this
            // number and a maximum can only answer one of them. See `aoOk`.
            _aoFractions.Add(aoFrac);
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
            // `[series]`, WHICH IS THE ONE WORD THAT GETS THIS HOME.
            //
            // These two lines are the A/B that decides whether a grade change
            // did anything at all — ambient occlusion, bloom, grain and the
            // vignette, each measured with the effect on and off. They have
            // never once been readable from the environment this project is
            // developed in: `aoD`, `bloomBright`, `grainLocal` and `vigEdge`
            // are four of the fifteen numbers `verdict-reach.py` reports as
            // reaching nothing, and the only four with no other route home.
            //
            // The allowlist already matches `[series]` as a FAMILY, precisely
            // so a new probe does not need anybody to remember the workflow
            // exists. This line is a series — an effect swept on and off — and
            // was simply never labelled as one.
            //
            // TAGGING THE LINE RATHER THAN WIDENING THE ALLOWLIST, and that is
            // not only tidiness: the build step is 65 characters under a hard
            // size limit that broke dispatch outright this morning, so a new
            // pattern there costs something real and a marker here costs
            // nothing.
            Debug.Log($"SimDirector: [series] post a/b [{sample}] aoD={aoD:0.00000} grainD={grainD:0.00000} "
                      + $"aoSpread={_aoSpread:0.00000} grainSpread={_grainSpread:0.00000}");
            Debug.Log($"SimDirector: [series] post a/b ao={all.Mean:0.0000}/{noAo.Mean:0.0000} "
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
        /// THE WINDOW GLOW, AS A SERIES RATHER THAN AN ARGUMENT.
        ///
        /// The frame ledger established the fault: night `brightRgb` reads
        /// (204,200,185), a channel ratio of 1.00:0.98:0.91 where the constant
        /// asks for 1.00:0.82:0.45. The windows are white, and a warm interior
        /// glow was the whole point of them.
        ///
        /// It did NOT establish the fix, and that is the distinction this
        /// project keeps paying for. "Lower it" is not a number. Blue clips
        /// above a 2.22 multiplier, ACES compresses and desaturates everything
        /// above it again, and the interaction of those two is not something to
        /// work out in my head — the AO ceiling was argued about across five
        /// runs and settled in one by printing the round series.
        ///
        /// So this renders the same night frame at six multipliers and prints
        /// what each one PRODUCES: how much of the frame is bright, and what
        /// colour those bright pixels actually are. The multiplier to ship is
        /// then read off the line — the largest one whose blue ratio is still
        /// near 0.45 — instead of guessed and defended.
        ///
        /// Restores 3.0 before returning. A probe that leaves the world in the
        /// state it was measuring is a probe that changes the build it reports
        /// on, and the stills are taken after this runs.
        void MeasureWindowGlow()
        {
            var cam = Camera.main;
            if (cam == null) return;
            // DARK FIRST, AS THE REFERENCE. Everything the windows are not —
            // lamps, neon, headlamps, the sky — is in this frame too, and the
            // first version of this probe averaged all of it and reported the
            // answer as if it were about windows. At k=1.0 the frame was still
            // 5.07% bright with the windows barely emitting, which is the number
            // that gave the instrument away.
            WorldBuilder.SetWindowGlow(0f);
            var dark = FramePixels(cam);

            var line = new StringBuilder("SimDirector: windowGlow");
            foreach (float k in new[] { 1.0f, 1.4f, 1.8f, 2.2f, 2.6f, 3.0f })
            {
                WorldBuilder.SetWindowGlow(k);
                var m = LitMinusDark(cam, dark);
                double blue = m.r > 0.01 ? m.b / m.r : 0.0;
                double blueTop = m.tr > 0.01 ? m.tb / m.tr : 0.0;
                line.Append($" k={k:0.0}[lit={m.pct:0.00}% all={(int)(m.r * 255)},")
                    .Append($"{(int)(m.g * 255)},{(int)(m.b * 255)} b/r={blue:0.00}")
                    .Append($" face={(int)(m.tr * 255)},{(int)(m.tg * 255)},{(int)(m.tb * 255)}")
                    .Append($" b/r={blueTop:0.00}]");
            }
            line.Append(" target b/r=0.45");
            Debug.Log(line.ToString());

            // AND THE AXIS THAT WAS NEVER SWEPT.
            //
            // The series above says brightness is not the lever: blue-over-red
            // runs 0.71 to 0.79 across a 3x multiplier and RISES with it, while
            // the target is 0.45. So there is no k that satisfies this probe's
            // own instruction — "ship the largest k whose blue ratio is still
            // near 0.45" — and there never was. A series can look informative
            // and still be a dead end, and this one printed every run for days.
            //
            // The source is ALREADY 0.45. Bloom spreads a near-white halo and
            // ACES desaturates highlights, and between them they pull it toward
            // white. What is wanted is therefore the SOURCE colour that comes
            // out at 0.45 on screen — a transfer, measured the same way the AO
            // ceiling was: print what each input produces and read the answer
            // off the line.
            //
            // Blue is swept and red is held, because the fault is entirely that
            // blue arrives too high; scaling green with it would change the hue
            // as well as the warmth and confound the two.
            var was = WorldBuilder.WindowEmissive;
            var warm = new StringBuilder("SimDirector: [series] windowWarmth");
            WorldBuilder.SetWindowGlow(0f);
            var dark2 = FramePixels(cam);
            // BLUE IS ANSWERED (0.16, read off the last run) so the sweep moves
            // to GREEN, which comes out at 0.97 against a target of 0.82 and is
            // the remaining half of the wash. Same shape, same discipline: six
            // inputs, print what each produces, read the answer off the line.
            // Blue held at its measured value so the two do not confound.
            foreach (float g in new[] { 0.82f, 0.70f, 0.58f, 0.46f, 0.34f, 0.20f })
            {
                WorldBuilder.WindowEmissive = new Color(1.0f, g, 0.16f);
                WorldBuilder.SetWindowGlow(1.4f);
                var m = LitMinusDark(cam, dark2);
                double gr = m.tr > 0.01 ? m.tg / m.tr : 0.0;
                double br = m.tr > 0.01 ? m.tb / m.tr : 0.0;
                warm.Append($" srcG={g:0.00}[face={(int)(m.tr * 255)},")
                    .Append($"{(int)(m.tg * 255)},{(int)(m.tb * 255)} g/r={gr:0.00} b/r={br:0.00}]");
            }
            warm.Append(" want g/r=0.82 b/r=0.45 at k=1.4");
            Debug.Log(warm.ToString());

            // RESTORED, BOTH OF THEM. A probe that leaves the world in the
            // state it was measuring changes the build it reports on, and the
            // four stills are taken after this runs — so a forgotten restore
            // here would put the wrong windows in every frame Jafar looks at.
            WorldBuilder.WindowEmissive = was;
            WorldBuilder.SetWindowGlow(3.0f);
        }

        /// The pixels the WINDOWS added, and their colour.
        ///
        /// Read exactly as occlusion and reflections are read: two renders, one
        /// quantity, the difference. A window that lights a wall is not a bright
        /// pixel anywhere near the window's own colour, so this counts only
        /// pixels that got MEANINGFULLY brighter and averages the ADDED light —
        /// `lit - dark` per channel — rather than the final pixel. Averaging the
        /// final pixel would fold in whatever the window is sitting on top of,
        /// which is the same mistake one level down.
        /// TWO POPULATIONS, BECAUSE THEY ANSWER DIFFERENT QUESTIONS, and the
        /// first two versions of this probe each measured one and reported it
        /// as the other.
        ///
        /// `all` is every pixel the windows brightened. That legitimately
        /// includes the light SPILLING onto walls, pavement and fog — and spill
        /// is emission times a grey surface, then fog-blended toward a blue
        /// night, so it is greyer and bluer than the source by physics rather
        /// than by fault. Measuring the windows' colour from it will always read
        /// too neutral, which is exactly what 0.70 against a target of 0.45
        /// looks like.
        ///
        /// `face` is the top decile by added luminance — the window rectangles
        /// themselves. THIS is what "are the windows the right colour" means.
        ///
        /// If `face` comes back near 0.45 the windows are correct at source and
        /// the complaint in the still is BRIGHTNESS, not hue: a blown-out pixel
        /// reads as white to the eye whatever its ratio. If `face` is also 0.70
        /// then the emission path itself is losing the colour and the search
        /// moves to the shader, not to the constant.
        (double pct, double r, double g, double b, double tr, double tg, double tb)
            LitMinusDark(Camera cam, Color32[] dark)
        {
            var lit = FramePixels(cam);
            if (lit == null || dark == null || lit.Length != dark.Length)
                return (-1, 0, 0, 0, 0, 0, 0);
            long n = 0; double sr = 0, sg = 0, sb = 0;
            var added = new List<(int sum, int r, int g, int b)>();
            for (int i = 0; i < lit.Length; i++)
            {
                int dr = lit[i].r - dark[i].r, dg = lit[i].g - dark[i].g, db = lit[i].b - dark[i].b;
                // Eight levels, so the rasteriser's own dither is not a finding.
                // Same reasoning as `ImageStats.QuantisationStep` on the other
                // A/B gates, in 0..255 rather than 0..1.
                if (dr + dg + db < 8 * 3) continue;
                n++; sr += dr; sg += dg; sb += db;
                added.Add((dr + dg + db, dr, dg, db));
            }
            if (n == 0) return (0, 0, 0, 0, 0, 0, 0);

            // HISTOGRAM, NOT A SORT, and this is my own regression being paid
            // back. The first version sorted every added pixel — up to 230,000
            // of them, six times a run — and `meanFrame` went 267ms to 329ms.
            // The probe made the thing it measures slower, which is the
            // instrument disturbing the subject in the most literal way
            // available.
            //
            // The decile does not need an ordering, only a cut: one pass to
            // bucket the added luminance, one walk down the buckets to find the
            // value the top tenth sits above, one pass to average them. O(n)
            // and three cheap passes instead of O(n log n) on a quarter of a
            // million items.
            var hist = new int[766];              // 0..765, the sum of three bytes
            foreach (var a2 in added) hist[a2.sum]++;
            int want = Mathf.Max(1, added.Count / 10), running = 0, cut = 765;
            for (int v = 765; v >= 0; v--)
            {
                running += hist[v];
                if (running >= want) { cut = v; break; }
            }
            double fr = 0, fg = 0, fb = 0; int top = 0;
            foreach (var a2 in added)
            {
                if (a2.sum < cut) continue;
                fr += a2.r; fg += a2.g; fb += a2.b; top++;
            }
            if (top == 0) top = 1;
            return (100.0 * n / lit.Length, sr / n / 255.0, sg / n / 255.0, sb / n / 255.0,
                    fr / top / 255.0, fg / top / 255.0, fb / top / 255.0);
        }

        /// One render, as raw pixels, for an A/B that needs the frame itself
        /// rather than a summary of it.
        Color32[] FramePixels(Camera cam)
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
                return tex.GetPixels32();
            }
            catch (Exception e) { _errors.Add("FramePixels: " + e.Message); return null; }
            finally
            {
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                if (tex != null) Destroy(tex);
                if (rt != null) { rt.Release(); Destroy(rt); }
            }
        }


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

        /// How many stills were taken with a live ring hidden. Zero over a
        /// whole run means either a silent street or a hide that never
        /// fired, and those want telling apart.
        int _shotsWithRingHidden;

        bool _bubbleSampleWanted;
        int _nearShots;

        /// The worst obstruction between the camera and the player across every
        /// shot, and how many shots had one at all.
        ///
        /// TWO NUMBERS, NOT ONE, and the pair is the point. "The closest thing
        /// ever to block the shot was 0.4m away" is a peak and says nothing
        /// about whether it happens; "eighteen of twenty shots were blocked"
        /// says it is the normal state of the camera and not a bad moment.
        /// Reporting a peak on its own is the fault this file has now found in
        /// four places tonight.
        float _shotBlockNearest = float.MaxValue;
        string _shotBlockWhat = "none";
        int _shotsBlocked, _shotsAimed;
        /// The worst fraction of a committed frame filled by geometry
        /// within two metres of the lens, and which shot it was.
        float _shotNearFracWorst;
        string _shotNearFracWhere = "none";
        int _restFrameSum, _restFrames, _workFrameSum, _workFrames;

        /// The frame the last shot-time probe read. Several probes run inside
        /// `Shot` and the last shot wins, so every one of them is a reading of
        /// a NAMED moment rather than of the run.
        string _lastShotName = "none";

        void Shot(string name)
        {
            _lastShotName = name;
            // SAMPLE THE TEXT COLLISIONS ON THE FRAME BEING PHOTOGRAPHED.
            // The audit's own sample is one moment a day; the picture is
            // another, and it is the one a human looks at. Cheap — it walks the
            // TextMeshes already in the scene — and it means the number and the
            // still describe the same instant.
            if (_bubbleSampleWanted) CollidingNames();
            // AND WHAT IS STANDING BY THE PLAYER IN THE FRAME BEING TAKEN,
            // which is the only instant the picture can be compared against.
            if (_game != null && _game.Player != null && _nearShots < 2)
            {
                _nearShots++;
                Debug.Log(SceneAudit.Near(_game.Player.transform.position + Vector3.up));
            }

            // AND WHAT IS STANDING BETWEEN THE CAMERA AND THE PLAYER, which is
            // a different question from what is standing NEAR them and is the
            // one three stills have raised.
            //
            // `SceneAudit.Near` is centred on the PLAYER. It answers "what is
            // around them", and it has been read as if it answered "what is in
            // the way" — the two agree only when the camera is behind the
            // player, which is exactly when nothing is in the way. Every still
            // with a pole across the middle of it, a black slab in the corner,
            // or a brown disc filling the bottom-left has been judged by eye
            // and never measured, and rule 4 says a visual judgement is a
            // hypothesis until a number settles it.
            //
            // A LINECAST, not a proximity test, because "close to the camera"
            // and "occluding the subject" are not the same thing: a lamp post
            // a metre to the left of the lens is in the frame and harmless,
            // and a sign four metres out on the sight line hides the player
            // completely. Named with its distance, so one round trip says
            // which object rather than that there is one.
            var blockCam = Camera.main;
            if (blockCam != null && _game != null && _game.Player != null)
            {
                var eye = blockCam.transform.position;
                var at = _game.Player.transform.position + Vector3.up * 1.2f;
                var hits = Physics.RaycastAll(eye, (at - eye).normalized,
                                              Vector3.Distance(eye, at));
                float nearest = float.MaxValue;
                string what = "clear";
                foreach (var h in hits)
                {
                    if (h.collider == null) continue;
                    // The player's own colliders are not an obstruction, and
                    // neither is anything parented under them.
                    if (h.collider.transform.IsChildOf(_game.Player.transform)) continue;
                    if (h.distance < nearest) { nearest = h.distance; what = h.collider.name; }
                }
                if (nearest < _shotBlockNearest)
                {
                    _shotBlockNearest = nearest;
                    _shotBlockWhat = $"{what}@{nearest:0.00}m in {name}";
                }
                if (nearest < float.MaxValue) _shotsBlocked++;
                _shotsAimed++;

                // AND HOW MUCH OF THE FRAME IS WALL AT ARM'S LENGTH, which
                // the sight-line test above cannot see: day1_night at
                // 57f91eb has its left 40% filled by one unlit corner the
                // camera stands against, the aim ray to the player was
                // CLEAR, and the framing is still bad. An 84-ray grid
                // across the frustum, counting hits within two metres —
                // the fraction is the number, the worst shot is named.
                int nearHits = 0, rays = 0;
                for (int gx = 0; gx < 12; gx++)
                    for (int gy = 0; gy < 7; gy++)
                    {
                        var vp = new Vector3((gx + 0.5f) / 12f,
                                             (gy + 0.5f) / 7f, 0f);
                        var ray = blockCam.ViewportPointToRay(vp);
                        rays++;
                        if (Physics.Raycast(ray, out var nh, 2f,
                                            ~0, QueryTriggerInteraction.Ignore)
                            && !nh.collider.transform.IsChildOf(
                                    _game.Player.transform))
                            nearHits++;
                    }
                float nearFrac = rays > 0 ? (float)nearHits / rays : 0f;
                if (nearFrac > _shotNearFracWorst)
                {
                    _shotNearFracWorst = nearFrac;
                    _shotNearFracWhere = name;
                }
            }

            // HOW MANY PEOPLE ARE ACTUALLY IN THE PICTURE.
            //
            // The first rest-day still ever taken shows two figures, and
            // `restNoonCrowd=12 workNoonCrowd=9` says a Saturday has MORE
            // people out than a Tuesday. Both are true and they are about
            // different things: that metric counts crowd walkers SPAWNED in the
            // simulated band, and the camera is looking at one street.
            //
            // So the design claim — the week has a shape you can SEE — has
            // never had a number attached to it. Spawned is not visible, and
            // the thing being promised is visible. Counted per shot, tagged
            // rest or work, so the two can finally be compared on the quantity
            // the promise is about.
            var shotCam = Camera.main;
            if (shotCam != null && _npcs != null)
            {
                int inFrame = 0;
                foreach (var n in _npcs)
                {
                    if (n == null) continue;
                    var v = shotCam.WorldToViewportPoint(n.transform.position);
                    if (v.z > 0 && v.x >= 0 && v.x <= 1 && v.y >= 0 && v.y <= 1) inFrame++;
                }
                bool rest = _game != null && Ledger.Core.Population.IsRestDay(_game.Now.Day);
                if (rest) { _restFrameSum += inFrame; _restFrames++; }
                else { _workFrameSum += inFrame; _workFrames++; }
            }
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

            // THE TEACHING OVERLAY IS NOT THE STREET. `review_day1_night.jpg`
            // is a white arc edge to edge across the frame with the city
            // barely visible behind it — the noise ring at its true
            // `ringMax=148.1` metre radius, which seen from inside is a band
            // rather than a circle. These four files exist to answer one
            // question and were answering it with a debug layer over the top.
            //
            // Nothing is weakened: the ring's own evidence is an A/B render
            // (`ringSeen` against `ringNone`) taken in its own frames, and it
            // does not read these files.
            //
            // Counted, because a still taken on a silent street looks exactly
            // like one where the hiding worked.
            if (NoiseRing.SetHiddenForCapture(true)) _shotsWithRingHidden++;

            // THE BILLBOARDS ARE AIMED AT LAST FRAME'S CAMERA UNTIL THIS LINE.
            //
            // `review_day5_night.jpg` prints two rumour lines across the frame
            // BACKWARDS, mirrored and skewed, while the nameplates beside them
            // read correctly. `SpeechBubble` aims in `LateUpdate` and
            // `NpcWalker` aims from `Tick`; this method runs in `Update` and
            // calls `cam.Render()` by hand — so every still ever committed was
            // drawn with the previous frame's aim, and at `meanFrame=334ms`
            // that is a third of a second of camera movement. On a bubble two
            // metres from the lens it is enough to swing past it, and the
            // built-in text shader is `Cull Off`, so the reverse face draws
            // instead of vanishing.
            //
            // MEASURED FIRST, THEN FIXED, and in that order deliberately.
            // After `AimAll` the count is zero by construction and would be a
            // gate certifying its own fix; taken before, it is the size of the
            // fault in the frame that is about to be written. Worst over the
            // run, because one still with a line printed backwards is the fault
            // — the same reason `bubblesOnScreen` became a peak the night it
            // read 0 beside a picture with two bubbles in it.
            int staleNow = Billboard.Misaimed(cam, 20f);
            int trackedNow = Billboard.Tracked;
            // THE DENOMINATOR FROM THE SAME INSTANT, and a series beside the
            // peak — the third probe tonight to need both, and the first to get
            // them without a wrong reading in between.
            //
            // `billboardsStale` went 5 -> 12 -> 27 across three green runs and
            // I nearly wrote that down as a regression. It is a run PEAK of a
            // count, and a count rises with how many billboards happen to be
            // visible: 27 of 55 and 27 of 500 are the same number and opposite
            // findings. The peak keeps its own denominator now, and the
            // fraction series says what the run typically looked like — which
            // is the reading a peak structurally cannot give, as sixteen
            // bubbles against a hundred and sixteen just demonstrated.
            if (staleNow > _billboardsStale)
            {
                _billboardsStale = staleNow;
                _billboardsAtWorst = trackedNow;
            }
            if (trackedNow > 0) _billboardStaleFrac.Add((float)staleNow / trackedNow);
            float staleDeg = Billboard.WorstDegrees(cam);
            if (staleDeg > _billboardWorstDeg) _billboardWorstDeg = staleDeg;
            _billboardsAimed = Billboard.AimAll(cam);
            _billboardsTracked = Billboard.Tracked;
            // AND RE-PIN THE SPEECH AT THE SAME MOMENT, for the same reason and
            // one line later. A bubble's SCALE is set against wherever the
            // camera was when its `LateUpdate` last ran, exactly as its rotation
            // was — so the still is committed with the previous frame's size.
            // The run said so before anybody looked: `bubbleFracPreCap=0.659`
            // against `worstBubbleFrac=1.245`, a post-cap reading larger than
            // its own pre-cap reading, which is only possible if the two are
            // describing different instants.
            _bubblesPinnedAtShot = SpeechBubble.PinAll(cam);
            // AND THE NAMEPLATES, for the identical reason one line up.
            // `nameShownWidthWorst=0.171` against a `PinFrac` of 0.120 is a
            // label that went through the clamp and came out wider than the
            // clamp allows, which is what a cap applied against last frame's
            // camera looks like.
            _namesPinnedAtShot = NameTags.PinAll(cam);
            // AND DE-OVERLAP THE BUBBLES, AFTER the pin — sizing changes the
            // screen rect, so testing overlap before it would test rectangles
            // that are about to move. Third site of one idea: anything that has
            // to be right in the committed frame is redone against the camera
            // that renders it.
            _bubblesShotLifted = SpeechBubble.LiftAtShot(cam);
            // AND THE MIRROR COUNT MOVES HERE TOO — AFTER the aim, on purpose,
            // because that is the frame that gets written. It used to run once,
            // at the audit moment, and reported 0 for a run whose committed
            // still has mirrored text in it: right scope, wrong instant, the
            // third metric this week with exactly that fault.
            //
            // SO THE TWO NUMBERS ASK DIFFERENT QUESTIONS AND BOTH ARE NEEDED.
            // `billboardsStale` is how wrong the aim was before this line —
            // the size of the bug, and it stays non-zero forever because
            // billboards genuinely drift for a frame. `textMirrored` is whether
            // any visible text is backwards, peaked over every instant it is
            // sampled at, and this call adds the twenty instants that matter
            // most: the ones that become files. The audit-moment call is kept,
            // because a frame the player sees is worth checking too. Reading
            // either number as the other is how a fix gets declared from the
            // wrong evidence.
            MeasureTextFaults();
            MeasureLooseCapsules();
            MeasureUndressedBodies();
            MeasureBodyRead(cam);

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
                //
                // AND ONE REST DAY, WHICH NO STILL HAS EVER SHOWN.
                //
                // The first-four rule fills its quota on campaign days 1 and 2,
                // and `Population.IsRestDay` is `day % 7 >= 5` — so both are
                // working days and every picture ever taken of this game is a
                // Tuesday. The week HAS a shape and the run measures it:
                // `workNoonCrowd=9` against `restNoonCrowd=12`, a third more
                // people out of doors at noon. Nobody has seen it.
                //
                // THE CAP WAS CHOSEN FOR A QUESTION THAT HAS BEEN ANSWERED. Its
                // own note says "four is enough to judge a surface: two
                // lighting conditions, twice" — and the texture pack landed and
                // was judged. The question now is whether the week reads, and
                // four stills of two identical weekdays cannot answer it. Same
                // drift as a metric keeping its name when the question moves.
                //
                // Added rather than swapped: the day numbers are in the file
                // names, and a dozen comments across this codebase cite
                // `review_day1_night` and `review_day2_noon` by name as the
                // evidence for a finding. Renaming them would falsify a dozen
                // true statements to save 300KB a build.
                bool restStill = Ledger.Core.Population.IsRestDay(_game != null ? _game.Now.Day : 0)
                                 && _restStills < MaxRestStills;
                if (_reviewStills < MaxReviewStills || restStill)
                {
                    if (restStill) _restStills++; else _reviewStills++;
                    System.IO.File.WriteAllBytes($"sim-out/review_{name}.jpg",
                                                 tex.EncodeToJPG(60));
                }

                // AND ONE FRAME FROM WHERE A PLAYER ACTUALLY STANDS. Every
                // committed still is the review camera's elevated vantage,
                // and at least one finding (the nameplate heap) may exist
                // ONLY from up there — plates from several junctions stack
                // in 2D at height and rarely can at eye level. One frame
                // per run, player eyes, player facing, through the same
                // aim-and-pin pipeline so text is honest in it.
                if (name == "day3_noon" && _streetStills < 1
                    && _game != null && _game.Player != null)
                {
                    _streetStills++;
                    var keepPos = cam.transform.position;
                    var keepRot = cam.transform.rotation;
                    cam.transform.position =
                        _game.Player.transform.position + Vector3.up * 1.65f;
                    cam.transform.rotation = Quaternion.LookRotation(
                        _game.Player.transform.forward, Vector3.up);
                    Billboard.AimAll(cam);
                    SpeechBubble.PinAll(cam);
                    NameTags.PinAll(cam);
                    cam.Render();
                    RenderTexture.active = rt;
                    tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
                    tex.Apply();
                    System.IO.File.WriteAllBytes("sim-out/review_street.jpg",
                                                 tex.EncodeToJPG(60));
                    cam.transform.position = keepPos;
                    cam.transform.rotation = keepRot;
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
                LedgerRow(name, fp);
            }
            catch (Exception e)
            {
                _errors.Add($"Shot({name}) failed: {e.Message}");
            }
            finally
            {
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                // Restored in `finally`, so a throw mid-render cannot
                // leave the ring invisible for the rest of the run and
                // turn a screenshot fix into a silent feature removal.
                NoiseRing.SetHiddenForCapture(false);
                if (tex != null) Destroy(tex);
                if (rt != null) { rt.Release(); Destroy(rt); }
            }
        }

        /// One shot, one row, written out immediately.
        ///
        /// APPENDED PER SHOT RATHER THAN BUFFERED TO THE END, because this
        /// project has watched a CI job report success while producing zero
        /// output for every character it was asked for. A run that dies on shot
        /// fourteen should leave thirteen readings behind, not nothing — a
        /// partial ledger is evidence and an absent one is a second mystery on
        /// top of the first.
        ///
        /// Tab-separated and invariant-culture, for the reason `ShotNum` gives
        /// below: a machine with a comma decimal separator turns 0.35 into 35
        /// and inverts every comparison made from it. `Fingerprint` has already
        /// formatted these invariantly, so they are passed through as text
        /// rather than re-parsed and re-printed.
        void LedgerRow(string name, (string luma, string rgb, string maxLuma, string brightPct,
                                     string brightRgb, string satPct, string satRgb) fp)
        {
            try
            {
                if (_frameRows == 0)
                    _frameLedger.Append("# frame ledger — one row per shot, written by the sim.\n")
                                .Append("# Compared against the previous run's committed copy by\n")
                                .Append("# tools/frame-drift.py, whose output goes into verdict.txt.\n")
                                .Append("shot\tmeanLuma\tmaxLuma\tbrightPct\tsatPct\t")
                                .Append("satStrength\tmeanRgb\tbrightRgb\n");
                _frameRows++;
                _frameLedger.Append(name).Append('\t')
                            .Append(fp.luma).Append('\t')
                            .Append(fp.maxLuma).Append('\t')
                            .Append(fp.brightPct).Append('\t')
                            .Append(fp.satPct).Append('\t')
                            .Append(fp.satRgb).Append('\t')
                            .Append(fp.rgb).Append('\t')
                            .Append(fp.brightRgb).Append('\n');
                System.IO.File.WriteAllText("sim-out/frames.tsv", _frameLedger.ToString());
            }
            catch (Exception e) { _errors.Add("LedgerRow: " + e.Message); }
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

            // EVERY DROP AND WHAT BECAME OF IT, printed before any gate reads a
            // job count. `jobsDone=0` was a number with no story attached; this
            // is the story. See `TraceJob` for why the frame is the suspect.
            Debug.Log("SimDirector: [series] jobs "
                      + (_jobTrace.Count == 0 ? "none posted" : string.Join(" ", _jobTrace)));

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
                // NOBODY INSIDE ANYBODY, ASKED OVER THE RUN INSTEAD OF AT AN
                // INSTANT. `tightest >= 0` was the clause and it could not
                // answer the question two different ways:
                //
                //   * the sentinel is 999, and 999 passes `>= 0`. Twenty of 68
                //     kept runs read `gap=not-measured` and every one of them
                //     cleared this clause on the strength of no data. The
                //     comment below has said so since it was written and the
                //     gate went on accepting it — reporting a hole is not
                //     closing it.
                //   * a RESOLVED overlap reads as exactly 0.00, because
                //     `Enforce` clamps the follower to nose-to-tail. Sixteen of
                //     the 48 measured runs read exactly 0.00, which is the clamp
                //     firing, and it passed `>= 0` alongside a genuinely clear
                //     road. "The planner kept the room" and "the clamp shoved
                //     them apart this frame" were the same reading.
                //
                // `OverlapsResolved` has neither problem: it counts every time
                // the clamp had to act, over the whole run, and it is always
                // measured. Bounded per METRE DRIVEN because the distance is a
                // property of the city and the frame count is a property of the
                // runner.
                //
                // THE BOUND IS MEASURED, from fifteen CoreTests configurations
                // covering ~460km: zero clamps everywhere except one, at 60
                // vehicles, which needed one. 2.0 per km is sixty times the
                // worst reading ever taken. `tightest` stays in the verdict as a
                // report, with `gapWhy` naming the pair.
                double perKm = traffic.TotalDistance > 0
                    ? 1000.0 * traffic.OverlapsResolved / traffic.TotalDistance : 0;
                trafficOk = trafficOk
                    && perKm < 2.0                       // nobody inside anybody, all run
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
            // `rigs` joins the named buckets rather than sitting in the residue.
            // Character work is the thing the cast tiering is about to trade
            // against, and until now every millisecond of it was pooled with
            // the software rasteriser under `render+rest` — where a doubling of
            // it would be invisible next to 297ms of GPU-less rendering.
            // `bodyLod` SPLIT OUT OF `population`, and it must be in this list
            // or the split would silently move four milliseconds of real game
            // work into `render+rest` and read as the gate improving. A
            // reattribution that changes the total is a fix that isn't one.
            // `mix` IS NEW AND IT USED TO BE PART OF `sun`. The whole audio
            // mix ran inside the sun's timer, so a line reading 3.15ms — a
            // quarter of the game budget — looked like a directional light
            // being expensive. Both are listed so the pair still sums to what
            // the old single number was, and the frame gate can finally say
            // which of the two it is complaining about.
            foreach (var name in new[] { "npcs", "population", "bodyLod", "sun", "mix", "checks",
                                         "traffic", "signals", "rigs" })
            {
                var c = Perf.Get(name);
                if (c == null || c.Samples == 0) { perFrame.Add($"{name}=none"); continue; }
                double perFrameMs = Perf.FrameCount > 0 ? c.TotalMs / Perf.FrameCount : 0;
                attributed += perFrameMs;
                perFrame.Add($"{name}={perFrameMs:0.00}ms");
            }
            double residueMs = Math.Max(0, meanFrameMs - attributed);
            perFrame.Add($"game={attributed:0.00}ms render+rest={residueMs:0.00}ms");
            // AND THE GAME'S SHARE, BECAUSE THE MILLISECONDS ARE MEASURING THE
            // RUNNER AS MUCH AS THE GAME.
            //
            // This gate was moved off the whole frame and onto `attributed` with
            // a comment promising that "runner noise lands in the residue". It
            // does not. `attributed` is wall-clock too, and eight consecutive
            // runs say so:
            //
            //     total 482.5  game 14.82  share 3.07%
            //     total 483.4  game 15.64  share 3.24%
            //     total 489.4  game 15.37  share 3.14%
            //     total 369.1  game 11.54  share 3.13%
            //     total 482.0  game 15.66  share 3.25%
            //     total 448.2  game 15.35  share 3.42%
            //     total 449.7  game 15.37  share 3.42%
            //     total 431.7  game 11.40  share 2.64%
            //
            // The absolute figure swings 11.4 to 15.7 — either side of the 12ms
            // ceiling — while the share sits between 2.6% and 3.4% throughout.
            // A 369ms run and a 489ms run are the same game on machines that
            // differ by a third, and the ms reading follows the machine almost
            // exactly. So a red here currently says "this runner was slow", and
            // that is the instrument being wrong rather than the subject.
            //
            // NOT GATED ON, AND THE GATE IS NOT MOVED. A share has its own
            // failure mode — make the renderer faster and it rises with nothing
            // changed — so swapping one unvalidated statistic for another is
            // the mistake this comment is about. Printed, with the series
            // accumulating in the kept verdicts, and the bound gets set when
            // there is something to set it from (rule 2). Leaving it red is
            // deliberate: moving a bound to make red go away is the thing
            // CLAUDE.md forbids by name.
            perFrame.Add($"gameShare={(meanFrameMs > 0 ? 100 * attributed / meanFrameMs : -1):0.00}%");
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
                // THE INJURY WE TREATED, NOT EVERY INJURY ROCCO HAS.
                //
                // This scanned `Harm.All` for any Rocco wound that went bad,
                // and the clause it was standing in means "while the treated
                // one did not". Those are different questions the moment Rocco
                // picks up a SECOND injury from anywhere else — and he does:
                // the collision layer hands out real wounds, `injuries=6` in a
                // typical run, and nothing treats those.
                //
                // So the gate went red on two runs while the thing it exists to
                // prove worked perfectly. `roccoUntreated=True` was the truth
                // about a wound this probe never staged.
                //
                // Third instance of this exact scope error found tonight, after
                // `collidingNames` counting every TextMesh in the city and
                // `worstTextHeightFrac` before it. A gate has to measure the
                // population its sentence is about.
                bool roccoFine = _harmTreated == null || !_harmTreated.WentBad;
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

            // AND THE WORDS ARE NOT DATABASE KEYS.
            //
            // Every check above asks whether the panel WORKS. None of them can
            // see what it says, and what it said on 0eeee6d was:
            //
            //     Rocco — "Mitch says it was player, and came to say so"
            //
            // four times, beside a sentence built ten lines away that got the
            // name right. Found by reading the dump, which is the third fault
            // a picture or a readback has caught that no gate was asking about
            // — so it becomes a number, the way `playerPrimitive` and `bodyUp`
            // did.
            //
            // IT NAMES THE SENTENCE, not just the count. A gate that can only
            // say its own name costs a round trip to learn why, and the whole
            // reason this one is possible is that the leak depends on world
            // state rather than on source a grep can reach.
            int idLeaks = 0;
            string idLeakSaid = "none";
            if (_game != null && _game.Gossip != null && _game.Gossip.Mill != null)
            {
                idLeaks = _game.Gossip.Mill.SummariesSaying("player");
                if (idLeaks > 0)
                    foreach (var g in _game.Gossip.Mill.Agents)
                    {
                        if (g == null) continue;
                        foreach (var r in g.Rumors)
                            if (r != null && GossipMill.SaysWord(r.Summary, "player"))
                            { idLeakSaid = $"{g.Id}: {r.Summary}"; break; }
                        if (idLeakSaid != "none") break;
                    }
            }

            // AND THE DOUBT TRAIL IS NOT ONE SENTENCE REPEATED.
            //
            // The panel shows three reasons. It used to show the last three
            // ENTRIES, and on 0eeee6d that was the same sentence three times
            // for two separate people — one repeated event had taken the whole
            // explanation, so every other reason those two had for distrusting
            // the player was off the screen.
            //
            // The number is the collapse doing its job: how many DISTINCT
            // lines the worst-doubting person's window resolves to, against
            // how many raw entries they are carrying. `shown` back at 1 with
            // `held` in double figures is the fault returning, and it is
            // exactly the reading nothing was taking when it shipped.
            //
            // REPORTED, NOT GATED. A person who has genuinely doubted you for
            // one reason once is a legitimate street state, and gating on it
            // would be a probe that only fires on a lucky run.
            int doubtShown = 0, doubtHeld = 0;
            string doubtWho = "nobody";
            if (_game != null && _game.Hosts != null)
                foreach (var h in _game.Hosts)
                {
                    if (h == null || h.Suspicion == null) continue;
                    if (h.Suspicion.Reasons.Count <= doubtHeld) continue;
                    doubtHeld = h.Suspicion.Reasons.Count;
                    doubtShown = h.Suspicion.RecentReasons(3).Count;
                    doubtWho = h.Card != null ? h.Card.Name : "somebody";
                }

            // WHOSE FACE BUILT THE CASE — the third competence brick, read off
            // the run rather than asserted from the fact it compiles.
            //
            // Rule 6 is the whole reason this is here: `Brandish`, `MayFrisk`,
            // `Acquire` and `Misattribute` were all built, tested and never
            // once called, and the only thing that would have said so is a
            // number from a run. `exposureDelegated` at 0 on a seventeen-day
            // open-mode campaign with two rackets running means the sentence
            // this brick exists to print never appears.
            int exYours = 0, exTheirs = 0;
            double exYoursW = 0, exTheirsW = 0;
            string exSays = "not measured";
            if (_game != null && _game.Gossip != null && _game.Gossip.Mill != null)
            {
                var ex = _game.Gossip.Mill.ExposureOf("player",
                    p => p != null && p.StartsWith("racket_"));
                exYours = ex.Yours; exTheirs = ex.Delegated;
                exYoursW = ex.YoursWeight; exTheirsW = ex.DelegatedWeight;
                exSays = ex.Sentence();
            }

            bool uiOk = _uiSmokeRun && panelsBad == 0 && panelsOk >= 7 && glyphsOk && idLeaks == 0;

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
                // While the campaign is live AND THE OUTFIT IS STILL CALLING,
                // most nights must actually post a job. The second half of that
                // sentence was missing and is not a softening: a cut-off outfit
                // posts nothing, because `GameController` asks
                // `InJobWindow(Now) && !Campaign.OutfitCutOff`, so those nights
                // could not have posted a job however well the run went. Same
                // subtraction as `_frozenCloses` immediately beside it, for the
                // same stated reason — achievable counts, not ideal ones.
                //
                // WHAT IT STILL CATCHES, because a bound nobody can fail is not
                // a gate (rule 5b): a live campaign with a calling outfit that
                // stops posting drops. That is the pipeline breaking, which is
                // the thing this clause exists for, and it is untouched.
                (camp.Verdict != Verdict.Ongoing ||
                 camp.JobsDone + camp.JobsMissed >= SimMode.Days - 2 - _frozenCloses - _cutOffNights);

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
            // M21: THE VERB RAN AND IT PAID FOR ITSELF.
            //
            // Two clauses, because two different things go wrong. Zero
            // denunciations is the failure this gate exists for — `Informing`
            // was tested Core with no caller, and a run that never names
            // anybody is that state wearing a green tick.
            //
            // And marks must equal denunciations. The mark on the player is the
            // whole design: an informer who pays nothing is a delete button with
            // extra steps. `Informing` hands the mark back as data so a caller
            // cannot drop it silently, and this is the check that says it did
            // not — the same shape as `deedDispatched` against `deedArrived`,
            // which is how a whole class of never-arriving deeds was found.
            // M21: ALLEGIANCE MOVED, BOTH WAYS, AND THE FLOOR STILL HELD.
            //
            // Four clauses because four different things were wrong this
            // morning and each could regress alone. Pledging works; pledging to
            // somebody who despises you does NOT (a probe that tunnels through
            // its own precondition proves nothing — rule 5b, the accept case
            // and the reject case both); walking out works; and the street
            // heard about a poach, which is the half that was silently missing
            // for as long as the recruit paths called a private twin that
            // skipped the gossip layer.
            // M19: THE PLAYER CAN MAKE A CLAIM, AND IT CAN BE CAUGHT.
            //
            // Both halves, because either alone is satisfiable by a broken
            // system: a run where every alibi is consistent proves nothing
            // about the contradiction branch.
            bool claimsOk = _claimHeld && _claimCaught && LawHost.ClaimsMade >= 2;

            bool allegianceOk = _pledged && _pledgeRefused && _brokeWith
                && GameController.AllegianceChanges >= 2
                // The poach must HAPPEN before the street can hear it, and the
                // first build failed here for the honest reason: nobody the sim
                // recruits answers to a rival, so the run never poached anyone
                // and a clause demanding the street hear about it could never
                // be satisfied. Both halves now, so a silent poach and an
                // absent poach stay distinguishable.
                && _poached
                && _game != null && _game.Empire != null && _game.Empire.PoachesHeard > 0;

            // FOUR CLAUSES, and the two new ones are why the first version of
            // this gate was worthless. It read `Denounced > 0 && Marks ==
            // Denounced` and went green on a run whose only accusation was
            // `Ignored (0 of 0)` — the method was called, nothing was weighed,
            // and every branch that gives the verb meaning sat untested.
            // AND THE REDIRECT, AS AN IMPLICATION RATHER THAN A COUNT.
            //
            // `LawHost.Redirected >= 1` is the clause I nearly wrote, and it is
            // the exact mistake this file learned about tonight: a redirect only
            // happens when a charge sticks WHILE the inquiry is below
            // `Investigation`, and a run with bodies and witnesses in it may
            // never be in that state. Asserting it would be a guard the world
            // does not owe — the same root as `allegiance` on a run that poached
            // nobody, and as `disposal` on a crowded spot with nobody in it.
            //
            // What the run DOES guarantee is consistency: if the counter moved,
            // the book must be pointed at somebody. That fails only when the
            // wiring is broken and passes on both branches — a run that
            // redirected and a run that never got the chance — which is the pair
            // rule 5b asks to have watched before shipping a guard.
            bool redirectSane = LawHost.Redirected == 0
                || !string.IsNullOrEmpty(_game.Homicides.PointedAt);
            bool lawOk = LawHost.Denounced >= 2
                && LawHost.MarksFiled == LawHost.Denounced
                && _denounceIgnored            // unbacked accusations do nothing
                && _denounceStuck              // and a corroborated one lands
                && redirectSane;               // and a redirect that fired landed somewhere

            bool bodiesOk = _bodySamples > 0 && _bodyRigs >= 2
                && _bodyMaxKnee - _bodyMinKnee > 10
                // Whenever somebody WAS out of range, somebody was culled.
                // Never "a cull happened", which is unsatisfiable in a city
                // where everybody is close by and would make this gate a
                // report on where the walkers wandered.
                && (_bodyCullable == 0 || _bodyCulled > _bodyCullable / 2)
                // 8cm apart at minimum: enough that the variation reached the
                // transforms rather than only the struct.
                && _bodyTallest - _bodyShortest > 0.08
                // AND NOTHING IS DRAWING THE SPAWN PRIMITIVE OVER THE TOP.
                //
                // Every clause above asks about the body that was ADDED. None
                // of them — none of the twenty gates in this file — asks what is
                // still being DRAWN, and for one build that gap hid the whole
                // point of M17.1: `realBody=1`, `bodiesOk=True`,
                // `height=1.58..1.90`, all true, and the player on screen was a
                // white capsule with two skin-coloured arms out of it, because
                // `RealBody` never removed the `CreatePrimitive` mesh that
                // `Mannequin.Build` has always removed. It was found by opening
                // the still, which is the only reason it was found at all.
                && !PlayerPrimitiveShowing()
                // AND IT IS STANDING UP. The bought body attached, scaled,
                // bound its avatar and passed every clause above while lying
                // flat on its back in the road — Jafar found it in the still,
                // after I had read `playerPrimitive=False` off this very line
                // and called the body confirmed without opening the frame.
                //
                // 0.9 is not a tuned number: `body.up` dotted with world up is
                // 1.0 standing and 0.0 flat, and 0.9 is ~25 degrees off
                // vertical, which is further than a person leans and nowhere
                // near a person lying down. Nothing in between is a pose this
                // game produces.
                && (RealBody.Attached == 0 || RealBody.Upright > 0.9)
                // AND IT HAS CLOTHES ON.
                //
                // The fifth fault found by opening a frame and the fourth this
                // list of clauses sailed past. Every one above asks about a
                // body that was ADDED — is it there, the right size, the right
                // way up, assembled like a man — and the figure in the middle
                // of the noon still was all four of those and stark naked,
                // because `name.Contains("face")` matched `Beta_Surface` and
                // painted the whole body flesh.
                //
                // The measurement was already here and already correct:
                // `bodyCoatArea=0.296`. Nothing read it, because nothing was
                // obliged to. `RealBody.Clothed` is that same number against
                // `BodyParts.MinDressedArea`, and it is exempt when the model
                // arrived with its own textures — see the property.
                && RealBody.Clothed
                // AND THE SKELETON HANGING OFF THAT ROOT IS A PERSON.
                //
                // `bodyUp` reads the ROOT's up vector. It read 1.000 — a
                // perfectly upright root — on the build whose player is a
                // splayed red figure lying across the road with its limbs out,
                // and the two facts are both true. Every clause above asks
                // about the body that was added, its size, its orientation and
                // whether the capsule is gone; not one of them can see the
                // POSE, which is the thing a person looking at the screen sees
                // first.
                //
                // Gated on the SIGN, so it is not a threshold: a head is above
                // its hips and hips are above their feet, or the figure is not
                // assembled like a man. The magnitudes are printed so a real
                // bound can be set from evidence next run rather than invented
                // here.
                && (!_postureSeen
                    || (_worstHeadAboveHips > 0f && _worstHipsAboveFeet > 0f))
                // AND SOMEBODY DRESSED HIM. The same build put the player on a
                // street reading `wardrobe=[navy:492 charcoal:549 olive:267
                // brown:449 oxblood:100]` while he himself was bare skin from
                // head to foot — because the material fallback painted every
                // renderer flesh, and a body painted entirely skin HAS a
                // material on every renderer. `SceneAudit`'s `noMaterial`
                // check, which exists for exactly this family of fault, was
                // right to pass. A naked man is not a missing material.
                // …OR THE MODEL CAME DRESSED, which is the case that turned this
                // clause red on the run that FIXED the bodies. See
                // `RealBody.WearsOwnSkin`: the exemption existed one clause up
                // on `Clothed` and this twin never got it, so a body whose
                // every renderer arrived with its own texture — the outcome the
                // whole extraction exists for — failed for not having been
                // painted over.
                && (RealBody.Attached == 0 || RealBody.Dressed > 0
                    || RealBody.WearsOwnSkin)
                // AND THE SCENE ITSELF IS SOUND. Missing materials, error
                // shaders, NaN transforms, hundredfold scales, buried geometry —
                // the classes that make a frame WRONG rather than merely
                // unusual, none of which any gate in this file has ever asked
                // about. `SceneAudit.Renderers` is printed beside it so a clean
                // report from an audit that walked nothing is not mistaken for
                // a clean scene.
                && SceneAudit.Clean
                // AND NO TWO NAMES IN THE SAME PLACE — among the names this
                // game puts over people's heads, which is not the same set as
                // "text on screen".
                // NOT `_labelsColliding`, which counts every TextMesh in the
                // scene — street plates, stop signs and lane signs on posts that
                // cluster at a junction by design. That number is reported
                // because a sudden jump in it means something moved, and it is
                // NOT a legibility failure. The build that proved it read
                // `collidingNames=144 nameTagsOffered=1`: a hundred and
                // forty-four overlaps among text this declutter never sees, and
                // one nameplate for it to place.
                //
                // TWO CLAUSES BECAUSE THERE ARE TWO QUESTIONS. `ResolvedFrames`
                // answers "did the pass ever run" — without it a declutter that
                // never executed reports a flawless zero. `WorstUnplaced`
                // answers "did it ever leave two names on top of each other",
                // and it is the maximum over the run rather than the reading at
                // this instant, because this line executes once and a collision
                // twenty frames ago is invisible to a snapshot.
                //
                // The first attempt at this fix was `Suppressed >= 0`, which is
                // true of every int that only counts up. An unsatisfiable gate
                // traded for a vacuous one is not a fix.
                && NameTags.ResolvedFrames > 0 && NameTags.WorstUnplaced == 0
                // AND THE PLAYER'S OWN BODY IS MOVING. Strictly greater than
                // zero, which is not a tuned threshold — it is the difference
                // between a transform something wrote to and one nothing did.
                && (!_playerPoseSeen || PlayerPoseRange > 0.0);

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
            // A MAXIMUM CANNOT ANSWER BOTH QUESTIONS, and it was being asked
            // both. `MeasureAoOnce` runs three rounds and keeps the LARGEST
            // fraction, which is right for "did the pass ever reach the frame"
            // and structurally wrong for "is the pass everywhere" — a maximum
            // maximises the very quantity the upper bound exists to keep small,
            // so adding rounds makes the ceiling more likely to trip on its own.
            //
            // The committed verdicts say it plainly. Across five runs the
            // number read 10.27, 31.22, 19.51, 24.88 and 80.49 percent, and
            // vehicle count does not predict it — fourteen vehicles produced
            // both 10 and 31. A 50% ceiling sits inside that spread, which is
            // the frame budget at 300ms all over again, and the third threshold
            // tonight found sitting inside its own instrument's noise.
            //
            // So the two questions get the two statistics they need: the peak
            // for the floor, the median for the ceiling. The series prints, so
            // the ceiling can be set from evidence rather than from the
            // geometric argument that the data has now contradicted.
            bool aoOk = FilmGrade.Applied > 0
                        && _aoFraction > 0.005
                        && AoTypicalFraction < 0.50
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
                // ITS OWN NUMBERS, LIKE EVERY OTHER GATE HERE. This one has
                // failed four times in sixty kept runs and said nothing but its
                // name each time, which is the exact thing this file's own
                // comment forbids: "a gate that can only say its own name costs
                // a twenty-minute round trip to learn WHY, which is what this
                // one cost the first time it fired."
                //
                // I called the most recent of those four a one-off two hours
                // ago. It is the fifth most common failure on the board, and
                // nobody has ever seen a reason for any of them — because
                // there was nothing to see.
                //
                // Five clauses, five readings: enough vehicles, nobody inside
                // anybody, nobody on the pavement, more than one kind of
                // vehicle, and it went somewhere.
                // AWAKE, BESIDE THE TOTAL, AND THE LEDGER SAID THIS WAS
                // ALREADY HERE. `TrafficSim.AwakeCount`'s entry reads "BY
                // DESIGN: an LOD measurement the sim's performance gate reads"
                // — and nothing in the Game layer referenced it at all. Third
                // decayed reason found on this ledger today, and the pattern in
                // all three is a reason describing the consumer somebody
                // intended rather than one that exists.
                //
                // It matters right now: the frame gate is red on the GAME's
                // half and traffic is 3.5ms of it. Fourteen vehicles at 3.5ms
                // and forty at 3.5ms are completely different findings, and
                // `vehicles` alone cannot separate them because the whole point
                // of the LOD is that most of them are asleep.
                ($"traffic[vehicles={(traffic != null ? traffic.Vehicles.Count : -1)} awake={(traffic != null ? traffic.AwakeCount() : -1)} kinds={kindsSeen} offRoad={offRoad} tightest={tightest:0.0} clamps={(traffic != null ? traffic.OverlapsResolved : -1)} metres={(traffic != null ? traffic.TotalDistance : -1):0} why={(traffic != null ? traffic.TightestGapWhy : "none")}]", trafficOk),
                ("perf", perfOk), ("witnessCar", witnessCarOk),
                // NAMED CLAUSE BY CLAUSE, because this gate went red as the
                // single word "harm".
                //
                // It is seven conditions and the verdict printed four numbers,
                // none of which moved: `injuries=6 feuds=1 samScars=1
                // samCap=1.00` was byte-identical to the previous run, which
                // passed. So the thing that flipped was one of the three
                // clauses nothing reported, and there was no way to tell which
                // without a twenty-eight-minute round trip per guess.
                //
                // `samCap` at two decimals is its own trap: the clause wants
                // `< 1.0` and 0.999 prints as 1.00, so the number that decides
                // it was rounded into looking like the number that fails it.
                // Four decimals here.
                ($"harm[staged={_harmStaged} sampled={_harmSampled} "
                 + $"stillHurt={_harmStillHurt} turned={_harmTurned} "
                 // `Harm.All` is an IReadOnlyList, which has no `.Exists` —
                 // the fully-qualified LINQ form is what the rest of this file
                 // uses, and it is also what the missing-usings linter accepts.
                 + $"treatedHeld={_harmTreated == null || !_harmTreated.WentBad} "
                 // AND WHAT ELSE HAPPENED TO HIM, printed but not
                 // gated. A collision wound going bad is the harm
                 // system WORKING; it is only noise in this gate.
                 + $"roccoOtherBad={System.Linq.Enumerable.Count(_game.Harm.All, i => i.PersonId == "Rocco" && i.WentBad && i != _harmTreated)} "
                 + $"samScars={_game.Harm.ScarsOf("Sam")} "
                 + $"samCap={_harmCapabilityAtInjury:0.0000} "
                 + $"feudLive={_harmFeudLive} feudBlocks={_harmFeudBlocks}]",
                 harmOk),
                ("phones", phonesOk),
                ($"ui[labels={_labels} fontless={_labelsFontless} blank={_labelsBlank} "
                 + $"idLeaks={idLeaks} said={idLeakSaid}]", uiOk),

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
                ($"law[denounced={LawHost.Denounced} marks={LawHost.MarksFiled} ignored={_denounceIgnored} stuck={_denounceStuck} backers={_denounceWitnesses} redirected={LawHost.Redirected} pointedAt={(string.IsNullOrEmpty(_game.Homicides.PointedAt) ? "nobody" : _game.Homicides.PointedAt)} {LawHost.LastVerdict}]", lawOk),
                ($"allegiance[pledged={_pledged} refused={_pledgeRefused} broke={_brokeWith} poached={_poached} moves={GameController.AllegianceChanges} poachHeard={(_game?.Empire != null ? _game.Empire.PoachesHeard : -1)}]", allegianceOk),
                ($"claims[made={LawHost.ClaimsMade} caught={LawHost.ClaimsCaught} held={_claimHeld}]", claimsOk),
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
                 $"h={_bodyShortest:0.00}..{_bodyTallest:0.00} primitive={PlayerPrimitiveShowing()} up={RealBody.Upright:0.00} "
                 + $"headOverHips={_worstHeadAboveHips:0.00} hipsOverFeet={_worstHipsAboveFeet:0.00} "
                 + $"worstAt=day{_worstPoseDay}h{_worstPoseHour}[{_worstPoseClip}] "
                 + $"dressed={RealBody.Dressed} skinned={RealBody.Skinned} "
                 + $"clothed={RealBody.Clothed} coat={RealBody.DressedAreaFraction:0.000} "
                 + $"parts=({RealBody.Parts})]", bodiesOk),
                ($"post[frames={FilmGrade.Frames}]", postOk),
                ($"framing[begun={FramedBeat.Begun} tightest={PlayerController.TightestFraming:0.0000}]", framingOk),
                ($"bloom[hit={100 * _bloomFraction:0.00}% rise={_bloomRise:0.0000} " +
                 $"lit={100 * _bloomHadHighlights:0.0}%]", bloomOk),
                ($"grain[local+{_grainDelta:0.0000000} floor={grainFloor:0.0000000} " +
                 $"spread={_grainSpread:0.0000000}]", grainOk),
                ($"vignette[edge {_vigOn:0.000} vs {_vigOff:0.000}]", vigOk),
                ($"ao[applied={FilmGrade.Applied} on={_aoOn:0.0000} " +
                 $"off={_aoOff:0.0000} delta={aoDelta:0.0000} " +
                 $"peak={100 * _aoFraction:0.00}% typical={100 * AoTypicalFraction:0.00}% " +
                 $"rounds=[{string.Join(" ", _aoFractions.ConvertAll(x => (100 * x).ToString("0.0")))}] " +
                 $"drop={_aoDrop:0.0000}]", aoOk),
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

                // M18 — THE HOUSEHOLD RAN AT ALL.
                //
                // ADDED ONE COMMIT LATE, and the omission is worth naming
                // because it is rule 6 in the shape it actually arrives in.
                // The household shipped wired, printing a household[...] line,
                // and I called it done — but a line in the verdict is a
                // REPORT, and this project's oldest failure is a system that
                // reports beautifully and is never called. `Brandish`,
                // `MayFrisk` and `Acquire` all printed zero for a month and
                // nobody read the zero.
                //
                // AND THE BOUND IS DELIBERATELY LOOSE, WITH THE EVIDENCE
                // PRINTED BESIDE IT. The clause I wrote first was `nights >=
                // SimMode.Days` — the arithmetic one, and it is the right gate
                // eventually. But whether a run closes `Days` nights or one
                // fewer depends on where the sim stops relative to the day
                // turn, and I have not measured that. Setting it from a guess
                // is `nightNotDarker` again: a gate that fails on an off-by-one
                // nobody has looked at, on a mechanism that is working.
                //
                // AND THE RUN THAT ANSWERED IT. 140f7a2 read `household[home=1
                // away=5 ...]` beside `daysClosed=6`, so the relationship is
                // exact and it is against `daysClosed` — the count of days the
                // game actually turned — and NOT `SimMode.Days`, which is the
                // requested length and was 17 on the same run because the sim
                // skips days. I would have gated on the wrong variable.
                //
                // Equality, now that it is a measurement rather than a guess. A
                // scorer that stops being called leaves the sum short, and no
                // amount of staring at `bond=0.49` would show it — the bond is
                // exactly what it would be if nothing had happened.
                ($"{(_game != null ? _game.Household.Report() : "household[absent]")}"
                 + $" nights={(_game != null ? _game.Household.NightsHome + _game.Household.NightsAway : -1)}"
                 + $"/daysClosed={(_game != null ? _game.Campaign.DaysClosed : -1)}",
                 _game != null
                 && _game.Household.NightsHome + _game.Household.NightsAway == _game.Campaign.DaysClosed
                 && _game.Household.Book.People.Count > 0),

                // M18 — AND THE COMPANION IS A WITNESS BY STANDING THERE.
                //
                // THE COMPARISON IS THE GATE, not the companion's rung alone.
                // The design claim is that somebody at your shoulder gets a
                // better sighting than the street DOES NOT BECAUSE THEY ARE A
                // COMPANION but because of where they are standing — resolved
                // by `Observe.Resolve` through the same pass, with no
                // companion branch anywhere in it. A gate reading only their
                // rung would pass on a run where everybody had a clean look at
                // a well-lit act, and would have proved nothing about the
                // mechanism.
                //
                // `>=` and not `>`. The street CAN produce another rung-4
                // witness — somebody standing close, lit, and facing the
                // right way is exactly what the model is for — and demanding
                // the companion beat them would be gating on the crowd's luck
                // rather than on the companion's position. What must never
                // happen is the companion coming out WORSE than the street
                // while stood at two metres in the player's own light.
                //
                // `noted>0` is the separate half: the sighting reached
                // `CompanionHost` through the witness record rather than
                // through a proximity test of its own.
                // The label wrapped `Companion.Report()` — which already opens
                // its own `companion[` — inside a second one, so the first run
                // printed `companion[with=Tanja rung=-1 street=1
                // companion[with=Tanja …]` with unbalanced brackets. Cosmetic,
                // and a verdict is the one channel out of CI this environment
                // can read, so it stays legible.
                ($"companionSight[with={(_companionWith == "" ? "none" : _companionWith)} "
                 + $"rung={_companionRung} street={_companionStreetRung} dist={_companionDist:0.0}m atRecruit={_companionRecruitDist:0.0}m waited={_deedWaitedDays}d] "
                 + $"{(_game != null ? _game.Companion.Report() : "companion[host=absent]")}",
                 _game != null && _companionStaged
                 && _game.Companion.Recruited > 0
                 && _game.Companion.Noted > 0
                 && _companionRung >= 4
                 && _companionRung >= _companionStreetRung),

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
                 + $"drawn={HeldObject.Drawn} object={HeldObject.LastDrawn ?? "none"} "
                 + $"hand={CharacterRig.HandTier}]",
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
                 + $"thread={_provThread}@{_provThreadRisk:0.00} ellisAsking={_provEllisAsking} " +
                 $"ellisEverAsked={_ellisEverAsked} "
                 + $"quietSpotWatchers={_emptyWatchers} crowdedWatchers={_crowdedWatchers} crowdedIsWatched={_crowdedIsWatched}]",
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
                 + $"quietSpotWatchers={_emptyWatchers} crowdedWatchers={_crowdedWatchers} crowdedIsWatched={_crowdedIsWatched}]",
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
                      $"beliefsShortened={Perceivers.BeliefsShortened} " +
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

            // THE BUBBLE OVERLAP SERIES, printed before any bound is put on it.
            // The peak said 91, 16 and 116 on three consecutive runs; this says
            // what the street typically looks like, and whether those three
            // disagree because the declutter changed or because the sampling
            // did.
            // AND THE TEXT-SIZE SERIES, folded here beside the overlap one so
            // both are closed at the same instant of the same run.
            NameTags.CloseTextStats();
            FootIk.Close();

            float bubbleMedian = -1f;
            if (_bubbleOverlap.Count > 0)
            {
                var sorted = new List<float>(_bubbleOverlap);
                sorted.Sort();
                bubbleMedian = sorted[sorted.Count / 2];
                var show = new System.Text.StringBuilder();
                // Evenly spaced through the run rather than the first twelve:
                // the first twelve samples are day one, when almost nobody is
                // out, and a series that only shows the quiet end is the
                // truncation fault this file fixed in the panel dump.
                int want = System.Math.Min(12, sorted.Count);
                for (int i = 0; i < want; i++)
                {
                    int at = _bubbleOverlap.Count * i / want;
                    show.Append($" {_bubbleOverlap[at]:0.00}");
                }
                // PREFIXED NAMES. `median=` and `worst=` were learned by
                // `verdict-keys` as required measurements the moment this line
                // first landed — generic words that any other series could
                // also use, so the manifest would demand "median" forever and
                // be satisfied by anybody's. Exactly what `S=` and `tail=` did
                // from the traffic sentence, caught this time before learning
                // rather than after.
                Debug.Log($"SimDirector: [series] bubbleOverlap n={_bubbleOverlap.Count} "
                          + $"bubbleMedian={bubbleMedian:0.00} "
                          + $"bubbleWorst={sorted[sorted.Count - 1]:0.00} "
                          + $"through the run:{show}");
            }

            // EVERY GATE'S LABEL, GREEN OR RED — and this is a repair to the
            // one channel out of CI this environment can read, so it outranks
            // whatever else was next (rule 12).
            //
            // `FAILING GATES:` prints the label of every gate that WENT RED,
            // and those labels are where most of this sim's diagnostics live.
            // So a measurement written to explain a failure is legible only on
            // the runs that fail, and the run where the fix WORKS reports
            // nothing about how.
            //
            // Found on `companionSight`. `atRecruit` and `waited` were added
            // an hour earlier for exactly one purpose — to tell "she was there
            // and saw nothing" from "she never arrived" — and both went inside
            // the gate label. It came back green and said neither, on a gate
            // whose whole problem is that it had been passing on LUCK for
            // twenty-two runs before going red on a commit that changed no
            // code. Green with no numbers cannot be told from lucky.
            //
            // Then the grep, because a fix without one is half a fix: 35 of
            // the 39 named quantities inside gate labels appear NOWHERE on a
            // green run. Not one instance — a whole channel that only opens
            // when something is already broken.
            //
            // ITS OWN LINE, and deliberately not merged into `done.`:
            // `verdict-keys` splits always-reported keys from gate-only ones
            // by looking for `FAILING GATES` in the line, and a key that moves
            // between the two classes is how that checker learned to cry wolf.
            // A distinct prefix keeps the old split intact and lets the tool
            // decide separately what to do with this one.
            Debug.Log($"SimDirector: ALL GATES: {string.Join(" | ", System.Array.ConvertAll(gates, g => (g.ok ? "ok " : "RED ") + g.name))}");
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
                      $"weekLostAs={_weekLostVerdict} frozenCloses={_frozenCloses} cutOffDay={_cutOffDay} cutOffNights={_cutOffNights} walkers={walkerCount} crowdWalkers={_game.CrowdWalkerCount} millAgents={millCount} crowdMill={crowdMill} strandedEmpty={strandedEmpty} heapMb={heapMb} frameAvgMs={avgMs:0.0} frameWorstMs={_frameWorst * 1000.0:0} " +
                      $"actTwoOpened={a2.Opened} actTwoOk={act2Ok} actTwoMissed=[{string.Join(",", act2Missed)}] " +
                      $"actThree={_actThreeStaged} opened={_game.ActThree.Opened} [{_actThreeWhy}] " +
                      $"ending={_actThreeEnding} handed={_actThreeHandedOver} " +
                      // WHY NOBODY COULD TAKE IT. `handed` has been false in
                      // all 137 kept runs and a conjunction of four
                      // conditions tells you none of them — the same
                      // argument `actThreeWhy` twelve lines up already won.
                      // DID THE PLANT TAKE. `handed` moving with `joeyRuns`
                      // false would mean something else fixed the succession;
                      // `joeyRuns` true with `handed` still false means the
                      // assignment was never the last blocker and
                      // `successorWhy` names the next one.
                      $"joeyRuns={_joeyRuns} " +
                      // AT THE ATTEMPT, not at the end of the run.
                      $"handedTried={_handedTried} handedRetries={_handedRetries} " +
                      $"handedReady=[{_handedReady}] " +
                      $"handedWhyAtTry={_handedWhyAtTry} " +
                      $"successorWhy={GameController.SuccessorWhy} " +
                      $"actThreeOk={actThreeOk} " +
                      $"npcs={(_npcs != null ? _npcs.Length : 0)} populationOk={populationOk} " +
                      $"shifts={_game.Job.ShiftsWorked} dayJobStaged={_dayJobStaged} dayJobOk={dayJobOk} " +
                      $"street={_game.Economy.Prosperity:0.00} prices={_game.Economy.PriceLevel:0.00} " +
                      $"takingsFactor={_game.Economy.TakingsFactor:0.00} economyOk={economyOk} " +
                      $"directorPending={_game.Directorate.Pending.Count} directorFired={_directorFired} directorOk={directorOk} " +
                      $"pop={(_game.Populace != null ? _game.Populace.Residents.Count : 0)} " +
                      $"gates={_game.Gates.Count} accessOk={accessOk} " +
                      $"targets={_game.Targets.Count} planRan={_planRan} opsOk={opsOk} " +
                      $"vehicles={(traffic != null ? traffic.Vehicles.Count : 0)} kinds={kindsSeen} " +
                      // BRAKE LIGHTS, and the count of vehicles drawn in
                      // the same pass beside it. A peak with no
                      // denominator cannot say whether four lit out of
                      // five is a jam or four out of twenty-eight is a
                      // rank.
                      // `GameController`, NOT `TrafficHost`. The statics live in
                      // `TrafficHost.cs` and that file declares
                      // `partial class GameController` — there is no type called
                      // `TrafficHost` anywhere in this project. I took a type
                      // name off a filename without opening the file, which is
                      // rule 1 with no excuse attached, and it cost a NO PLAYER
                      // LOG round trip. CS0103 is a name-RESOLUTION error, so
                      // ShapeCheck is structurally blind to it and CI was always
                      // going to be the first thing that could see it.
                      $"brakeLampsPeak={GameController.BrakeLampsPeak} " +
                      $"vehiclesDrawn={GameController.VehiclesDrawn} " +
                      // OFF THE ROAD, WITH THE COUNT DRAWN AT THAT SAME FRAME.
                      // Expected zero: `Traffic` steps vehicles along street
                      // edges, so anything above it means the stepper leaves
                      // the carriageway — most likely at a junction, where one
                      // edge ends and the next has not begun.
                      $"vehiclesOffRoad={GameController.VehiclesOffRoadPeak} " +
                      $"vehiclesAtOffRoadWorst={GameController.VehiclesAtOffRoadWorst} " +
                      $"trafficMetres={(traffic != null ? traffic.TotalDistance : 0):0} " +
                      $"gap={(gapMeasured ? tightest.ToString("0.00") : "not-measured")} " +
                      // THE CLAMP COUNT IS THE GATE NOW; the gap is the report.
                      // `gapWhy` names the pair, because four failures running
                      // said the word "traffic" and nothing else, and the run
                      // after that said "gap=-2.69" — which still cannot tell a
                      // bus inside a car from a car crossing a junction its
                      // leader had not cleared. Those need different work.
                      $"clamps={(traffic != null ? traffic.OverlapsResolved : -1)} " +
                      $"clampsPerKm={(traffic != null && traffic.TotalDistance > 0 ? 1000.0 * traffic.OverlapsResolved / traffic.TotalDistance : 0):0.00} " +
                      $"tailsBehindStart={(traffic != null ? traffic.TailsBehindStart : -1)} " +
                      $"gapWhy=[{(traffic != null ? traffic.TightestGapWhy : "no traffic")}] " +
                      $"offRoad={offRoad} yields={(traffic != null ? traffic.YieldsToPeople : 0)} trafficOk={trafficOk} " +
                      // `signs` answers "how much sign FURNITURE stands in the
                      // street" — under the town plan the name plates moved onto
                      // walls and out of this count, into wallPlates beside it.
                      $"signs={StreetFurniture.SignCount} wallPlates={StreetFurniture.WallPlateCount} " +
                      $"vehicleFact={vehicleFactSeen} witnessCarOk={witnessCarOk} " +
                      // THE BUILDINGS THAT STAND IN A CARRIAGEWAY, with how far.
                      // Two today, both the pub — Hook Street over its east
                      // face and Quay Street over its south, a metre and a half
                      // each. Reported rather than gated on zero, because zero
                      // is red on the shipped city for a level fault nobody is
                      // fixing tonight and a permanently red gate teaches
                      // everybody to read red as noise. It moves the day
                      // somebody nudges an avenue array, and it names the
                      // street when it does.
                      $"massInRoad=[{string.Join(" ", Ledger.Core.StreetMap.MassOverlaps())}] " +
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
                      // ON THE DONE LINE ONLY, and deliberately not on the
                      // gate string above. Both are run totals, and the gate
                      // string is emitted only when the gate is red — so a key
                      // living on both lines is a key `verdict-read.py` has to
                      // refuse, which is the fault that cost an afternoon.
                      // `loiterNotices` is on both for historical reasons; two
                      // more would be making the problem bigger on purpose.
                      $"bloodNotices={Perceivers.BloodNotices} " +
                      $"weaponNotices={Perceivers.WeaponNotices} " +
                      $"batCarried={_batCarried} batTook={_batTook} " +
                      $"sounds={Perceivers.SoundsEmitted} investigations={Perceivers.NoiseInvestigations} " +
                      $"beliefsShortened={Perceivers.BeliefsShortened} " +
                      $"clipsAsked={Audio.DistinctClipsAsked} voicesAsked={Audio.DistinctVoicesAsked} " +
                      // AND HOW MANY THE BANK OFFERS, which is the
                      // denominator `voicesAsked` has never had.
                      //
                      // `voicesAsked` alone cannot say whether the
                      // street sounds varied: twelve of twelve is a
                      // bank fully used and twelve of two hundred is
                      // a street drawing on a twentieth of what it
                      // has. `VoiceBank.PoolVoices` is the count and
                      // it has sat on the reach ledger under a reason
                      // that is now FALSE — it said the crowd pool is
                      // unwired, and `VoiceFor` falls through to the
                      // pools for anybody not in the cast, which is
                      // every street line `SpeechBubble` speaks. The
                      // POOL is wired; only its count had no reader.
                      $"voicePool={VoiceBank.PoolVoices} " +
                      $"{(_game != null ? _game.Household.Report() : "household[absent]")} " +
                      $"speechPlayed={Audio.SpeechPlayed} speechMissing={Audio.SpeechMissing} " +
                      $"speechNoClip={Audio.SpeechNoClip} " +
                      $"speechNoClipComposed={Audio.SpeechNoClipComposed} " +
                      $"speechPartsWorst={Audio.SpeechPartsWorst} " +
                      $"speechLinesMeasured={Audio.SpeechLinesMeasured} " +
                      $"speechOutOfRange={Audio.SpeechOutOfRange} " +
                      $"speechNoAudio={Audio.SpeechNoAudio} " +
                      // LIVE SPEECH, ON THE DONE LINE BECAUSE IT DESCRIBES THE
                      // WHOLE RUN. Its neighbours here are lifetime counts, so
                      // it belongs with them rather than on a screenshot line
                      // where every value is true only of one frame — which is
                      // the mistake that cost an afternoon and four published
                      // explanations of a number that was never wrong.
                      $"{Audio.Live.Verdict()} " +
                      // WHICH IT WAS, not just that live speech did nothing.
                      // "no vocabulary on disk" and "the vocabulary loaded and
                      // nothing asked" are different problems with different
                      // fixes, and a bare zero cannot tell them apart.
                      $"speechVocab={(Audio.Vocabulary != null ? Audio.Vocabulary.Count.ToString() : "none")} " +
                      $"speechVoices={Audio.Voices.Count} " +
                      // A ZERO NEEDS A DENOMINATOR, and this one cost a build.
                      // `speechVoices=0` was true and unreadable: nothing on
                      // disk, nothing parsed, or nothing staged all print the
                      // same. Bracketed because a verdict value may not carry
                      // a space and the reader takes a bracketed run whole.
                      $"speechVoicesWhy=[{Audio.VoicesWhy}] " +
                      $"speechVocabWhy=[{Audio.VocabularyWhy}] " +
                      $"speechBackendWhy=[{Audio.BackendWhy}] " +
                      // WHERE THE CACHE LIVED. "device" is the bound path the
                      // bench proved bit-exact at 17ms flat; anything else is
                      // the host path plus the reason it fell back. A
                      // residency that quietly stopped being resident reads
                      // as a slow card otherwise, and this is the number
                      // that tells those apart on a player's machine.
                      $"speechResidency=[{Audio.ResidencyWhy}] " +
                      $"{Audio.Pending.Verdict()} " +
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
                      // ON THE DONE-LINE, NOT ONLY IN THE GATE LABEL. A label
                      // prints when the gate FAILS, so a green run said nothing
                      // about whether the condition it needed had been staged —
                      // and "both spots were unwatched and the comparison came
                      // out equal" can satisfy a clause as easily as it can
                      // break one. That is the shape of a gate passing for the
                      // wrong reason, which is the half of flakiness nobody
                      // sees.
                      $"crowdedWatchers={_crowdedWatchers} crowdedIsWatched={_crowdedIsWatched} " +
                      $"quietSpotWatchers={_emptyWatchers} " +
                      $"deeds={_deedsStaged} deedWitnesses={_deedWitnesses} " +
                      $"deedEyesOpen={_deedEyesOpen} deedKnowsYou={_deedKnowsYou} " +
                      $"deedSlotSets={_deedSlotSets} deedBestRung={_deedBestRung} " +
                      // THE ESCORT'S DISTANCE BELONGS ON THE ALWAYS-PRINTED
                      // LINE, and putting it in the gate label was the third
                      // "suspect the instrument" of the week.
                      //
                      // `atRecruit` and `waited` were written to tell "she was
                      // there and saw nothing" apart from "she never arrived".
                      // They went into `companionSight[...]`, which a verdict
                      // prints ONLY for a FAILING gate — so the run where the
                      // fix works reports nothing about how it worked, and a
                      // green `companionSight` cannot be told from the green
                      // runs it produced by luck for twenty-two runs before
                      // going red on a commit that changed no code.
                      //
                      // That is the exact question the gate exists to answer,
                      // and the diagnostic was only readable when the answer
                      // was already known. A number that can only be seen on a
                      // bad run cannot show a fix HOLDING.
                      $"companionRung={_companionRung} companionStreet={_companionStreetRung} " +
                      $"companionDist={_companionDist:0.0} companionAtRecruit={_companionRecruitDist:0.0} " +
                      $"deedWaitedDays={_deedWaitedDays} " +
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
                      // THE LAST GENUINELY UNREACHABLE NUMBER, closed.
                      // Whether the noise ring's last draw was behind
                      // something was printed only on the door-slam line,
                      // which the verdict does not carry — so the one fact
                      // that says whether a sound was heard THROUGH a wall
                      // could not be read from a build at all.
                      $"ringLastOccluded={NoiseRing.LastOccluded} " +
                      $"ringLastRadius={NoiseRing.LastRadius:0.0} ringOk={_ringOk} " +
                      $"slamDrewRing={_slamDrewRing} " +
                      $"slamRings=[{(_slamRingSkips.Count == 0 ? "no slams staged" : string.Join(" ", _slamRingSkips))}] " +
                      $"slamsDeferred={_slamsDeferred} " +
                      $"loitersCutShort={_loitersCutShort} " +
                      $"dropRuns={_dropRuns} " +
                      $"ringSeen={100 * _ringSeenFraction:0.0000} ringRise={_ringSeenRise:0.0000} " +
                      $"ringLedger={100 * _ringSeenLedger:0.0000} " +
                      $"ringSprites={100 * _ringSeenSprites:0.0000} " +
                      $"ringParticles={100 * _ringSeenParticles:0.0000} " +
                      $"ringNone={100 * _ringSeenNone:0.0000} " +
                      $"ringTransformZ={100 * _ringSeenTransformZ:0.0000} " +
                      $"ringControl={100 * _controlSeen:0.0000} " +
                      $"ringPaintUsed={NoiseRing.PaintUsed} " +
                      $"ringHiddenShots={_shotsWithRingHidden} " +
                      $"aoRounds={_aoRounds} aoRan={_tookAoPair} " +
                      $"perceptionWhy={PerceptionWhy()} " +
                      $"perceptionOk={perceptionOk} " +
                      // PRINTED BECAUSE I GUESSED TWICE. Whether the probes
                      // fired depends on which days and hours the run actually
                      // reached, and neither was in the report — so two builds
                      // were spent inferring it from a -1.
                      $"lastDay={_lastSeenDay} endDayReached={_endDay} " +
                      $"loiterStaged={_loiterStaged} loiterRetries={_loiterRetries} "
                      + $"slams={_slams} " +
                      $"nightRunStaged={_nightRunStaged} " +
                      $"denounced={LawHost.Denounced} marksFiled={LawHost.MarksFiled} " +
                      $"denounceVerdict=[{LawHost.LastVerdict}] lawOk={lawOk} " +
                      // WHERE THE DETECTIVE IS LOOKING, and how many days
                      // of relief are left. `redirected` alone cannot say
                      // whether the redirect is still holding or has already
                      // decayed to nothing, and those are the two states the
                      // whole mechanism exists to move between.
                      $"redirected={LawHost.Redirected} " +
                      $"pointedAt={(string.IsNullOrEmpty(_game.Homicides.PointedAt) ? "nobody" : _game.Homicides.PointedAt)} " +
                      $"pointedOnDay={_game.Homicides.PointedOnDay} " +
                      $"redirectRelief={_game.Homicides.RedirectReliefOn(_game.Now.Day):0.00} " +
                      $"inquiry={_game.PoliceInquiry} " +
                      // THE ARITHMETIC BESIDE THE STAGE, ON THE SAME LINE.
                      //
                      // `Pressure` opens with `_killings.Count * PerBody`, and
                      // `PerBody` is 0.4 with `ManhuntAt` 1.0 — so three bodies
                      // is a manhunt on their own, whatever any witness says.
                      // `4e3eef3` printed `killings=4` on the gates line and
                      // `inquiry=Procedure` on this one, which is arithmetically
                      // impossible; but they are two lines, so they are two
                      // readings and the difference means nothing yet. That is
                      // the rule this project wrote after losing an afternoon
                      // to exactly this shape, so the fix is to put them side
                      // by side rather than to reason about the gap.
                      //
                      // `inquiryBodies` and `inquiryPressure` are read HERE, at
                      // the same instant as the stage above, off the same book.
                      $"inquiryBodies={_game.Homicides.BodyCount} " +
                      $"inquiryPressure={_game.Homicides.Pressure(_game.Gossip?.Mill, _game.IsAlive, _game.Now.Day):0.00} " +
                      // WHY `inquiry` IS WHATEVER IT IS, on the same line as
                      // the number itself. It has read `None` in every kept run
                      // and the reading could not say whether that was "no body
                      // was filed" or "a body was filed and priced at nothing"
                      // — rule 3b, a zero with no denominator. `homStaged` is
                      // the denominator: false means the staging never fired,
                      // which is a different fault from a body that filed
                      // cheaply. `homPressure` is the raw number the stage is
                      // cut from, so a stage sitting near a boundary is visible
                      // rather than inferred.
                      $"homStaged={_homicideStaged} homVictim=" +
                      $"{(string.IsNullOrEmpty(_homVictim) ? "nobody" : _homVictim)} " +
                      $"homBodies={_homBodies} homSaw={_homSaw} homKnew={_homKnew} " +
                      $"homWouldTalk={_homWouldTalk} " +
                      $"homNamed={_homNamed} " +
                      $"homSawStored={_homSawStored} homHoldsIt={_homHoldsIt} " +
                      // THE THREE-WAY SPLIT UNDER `homHoldsIt`, and the mill's
                      // own behaviour across the filing call. Read in this
                      // order: same mill, then offered/dropped for the call,
                      // then hasAgent, then anyRumour, then holdsIt. The first
                      // one that is zero names the broken link.
                      $"homSameMill={_homSameMill} " +
                      $"homFileOffered={_homFileOffered} homFileDropped={_homFileDropped} " +
                      $"homHasAgent={_homHasAgent} homAnyRumour={_homAnyRumour} " +
                      $"homWantKey=[{_homWantKey}] " +
                      $"homTopics=[{(_homTopics.Length == 0 ? "nothing" : _homTopics)}] " +
                      // AND WHETHER THE MILL REFUSED ANYBODY. A dropped
                      // witness was an early return with no trace until
                      // tonight, and it is what emptied the crowd's
                      // memory. `witnessOffered` is the denominator.
                      $"witnessOffered={(_game.Gossip?.Mill != null ? _game.Gossip.Mill.WitnessesOffered : -1)} " +
                      $"witnessDropped={(_game.Gossip?.Mill != null ? _game.Gossip.Mill.WitnessesDropped : -1)} " +
                      $"homPressure={_homPressure:0.00} " +
                      $"homPressureByDay=[{string.Join(",", _homWhySeries)}] homInquiry={_homInquiry} " +
                      $"marked={(_cutMarkedYou.HasValue ? _cutMarkedYou.Value.ToString() : "nocut")} " +
                      $"saw={(_cutSawSomething.HasValue ? _cutSawSomething.Value.ToString() : "nocut")} " +
                      // THREE NUMBERS, BECAUSE ONE CANNOT ANSWER IT. `notoriety`
                      // is what the campaign carries NOW, after decay;
                      // `notorietyPeak` is the loudest any single act offered;
                      // `notorietyApplied` is how many times anything charged
                      // it at all. A zero in the first is a quiet week, an
                      // unwired model, or a decayed reputation, and only the
                      // other two can say which.
                      $"notoriety={_game.Campaign.Notoriety:0.000} " +
                      $"notorietyPeak={ViolenceHost.PeakNotoriety:0.000} " +
                      $"notorietyApplied={_notorietyApplied} " +
                      // THE SECOND SOURCE, COUNTED SEPARATELY FROM THE FIRST.
                      // `notorietyApplied` is violence; this is informing. One
                      // combined counter could not tell a run where nobody
                      // informed from a run where that wiring broke, and both
                      // leave `notoriety` exactly where the cut put it.
                      $"notorietyFromLaw={LawHost.NotorietyFiled} " +
                      $"notorietyDoors=[{NotorietyDoorReading()}] " +
                      // M21: THE RIVAL RINGS YOU. `summonsPlaced` is the
                      // denominator — without it `summonsTaken=0` reads the
                      // same whether nobody answered or she never rang, and
                      // this is a system whose whole failure mode is looking
                      // like it ran quietly.
                      // DID THE HARNESS EVEN TRY. `summonsTaken=0` with
                      // `callboxStaged=False` is a plant that never ran;
                      // with True it is a plant that ran and he did not
                      // arrive, which is a fact about distance.
                      $"callboxStaged={_callboxStaged} callboxWhy=[{_callboxWhy}] " +
                      $"summonsPlaced={SummonsHost.Placed} " +
                      $"summonsTaken={SummonsHost.Taken} " +
                      // WHICH KIND OF MISS. "No line was live" is a world
                      // that never offered the choice; "a line was live and he
                      // was not near it" is the mechanic working. Zero taken
                      // means both until this says which.
                      $"summonsMissWhy=[{SummonsHost.MissWhy}] " +
                      $"summonsMissed={SummonsHost.MissedCalls} " +
                      $"summonsRead=[{SummonsHost.LastRead}] " +
                      // THE PAPER. `pressEditions` is the denominator:
                      // `pressNamed=0` reads the same whether the town never
                      // had a case against the player or the paper never ran,
                      // and this is exactly a system whose failure mode is
                      // being quietly absent.
                      $"pressEditions={PressHost.Editions} " +
                      $"pressNamed={PressHost.Named} " +
                      $"pressReaders={PressHost.Readers} " +
                      // MISSING DROPS COSTS SOMETHING NOW. `reliabilityFiled`
                      // is the denominator: `reliabilityHeard=0` reads the same
                      // whether the player never slipped or the filing is
                      // broken, and only the pair separates them.
                      $"dropsSkipped={_dropsSkipped} " +
                      $"reliabilityFiled={ReliabilityHost.Filed} " +
                      $"reliabilityHeard={ReliabilityHost.Heard} " +
                      $"reliabilityRead=[{ReliabilityHost.LastRead}] " +
                      $"pressHeadline=[{PressHost.LastHeadline}] " +
                      $"notorietyLastLaw={LawHost.LastNotoriety:0.000} " +
                      $"denounceIgnored={_denounceIgnored} denounceStuck={_denounceStuck} denounceWitnesses={_denounceWitnesses} " +
                      $"corroboration={_denounceCorroboration:0.00} " +
                      $"contradiction={_denounceContradiction:0.00} " +
                      $"denounceMark={_denounceMark} " +
                      $"denounceBlewBack={_denounceBlewBack} " +
                      $"blowbackContradiction={_blowbackContradiction:0.00} " +
                      $"pledged={_pledged} pledgeRefused={_pledgeRefused} brokeWith={_brokeWith} " +
                      $"allegianceMoves={GameController.AllegianceChanges} poachesHeard={(_game != null && _game.Empire != null ? _game.Empire.PoachesHeard : -1)} allegianceOk={allegianceOk} " +
                      $"claimsMade={LawHost.ClaimsMade} claimsCaught={LawHost.ClaimsCaught} " +
                      // WHO ELSE WAS STANDING THERE. Reported, not gated: a
                      // quiet street where nobody is within earshot is a
                      // legitimate world, and gating would be a probe that
                      // fires only on a lucky run — which is the single
                      // largest cause of red in this project. If it reads 0
                      // every run, the condition wants PLANTING, not a looser
                      // bound.
                      $"claimOverheard={LawHost.ClaimOverheard} " +
                      // THE CROWD AS A CROWD RATHER THAN A STACK. Reported, not
                      // gated — the bound does not exist until the series does,
                      // and a crowd that never touches is as wrong as one that
                      // interpenetrates.
                      $"crowdInside={_crowdInside} crowdSeenAtWorst={_crowdSeenAtWorst} " +
                      $"crowdTightest={(_crowdTightest == float.MaxValue ? -1f : _crowdTightest):0.00} " +
                      $"crowdTightestWhen={_crowdTightestWhen} " +
                      $"crowdGapMedian={CrowdGapMedian:0.00} crowdGapSamples={_crowdGaps.Count} " +
                      // WHETHER THE SEPARATION NUDGE IS STILL A NUDGE. `capped`
                      // against `calls` is the rate the pile case fires at, and
                      // `worst` is how far the uncapped push wanted to travel —
                      // anything over a metre is a body crossing the pavement in
                      // one frame, which is what the cap now prevents.
                      // WHICH ROUTE THE CROWD IS ACTUALLY TAKING. `direct` is
                      // the healthy case — a clear walk to the real
                      // destination. The others all share an aim point, and
                      // `junction` shares one across a whole neighbourhood,
                      // which is the shape a forty-one body knot has.
                      $"steerDirect={NpcWalker.SteerDirect} " +
                      $"steerTargetStreet={NpcWalker.SteerTargetStreet} " +
                      $"steerOwnStreet={NpcWalker.SteerOwnStreet} " +
                      $"steerJunction={NpcWalker.SteerJunction} " +
                      $"steerOrigin={NpcWalker.SteerOrigin} " +
                      $"crowdApartCapped={NpcWalker.ApartCapped} " +
                      $"crowdApartCalls={NpcWalker.ApartCalls} " +
                      $"crowdApartWorst={NpcWalker.ApartWorst:0.00} " +
                      $"crowdBodyWidth={CrowdWidthRead()} " +
                      // AND THE BIGGEST HUDDLE, because a median over pairs is
                      // dominated by the people who are nowhere near each other
                      // and cannot see thirty of them standing in a block.
                      $"crowdHuddle={HuddleMedian()} " +
                      $"crowdHuddleWorst={HuddleWorst()} " +
                      // THE BREAKDOWN AND THE HUDDLE IT CAME FROM, together.
                      // `huddleAt` is the peak these four were sampled at; if
                      // it disagrees with `crowdHuddleWorst` the sampler and
                      // the series have drifted apart and neither is readable.
                      $"huddleAt={_huddleWorstSeen} huddleTalking={_huddleTalking} " +
                      $"huddleEscorting={_huddleEscorting} huddleDetour={_huddleDetour} " +
                      $"huddleWaiting={_huddleWaiting} huddleCells={_huddleCells} " +
                      // STANDING versus MOVING at the huddle's worst instant.
                      // These two sum to `huddleAt` by construction, so a pair
                      // that does not is the sampler having moved on. Standing
                      // high means the rings are undersized; moving high means
                      // it is a jam on a route and the rings are innocent.
                      $"huddleStanding={_huddleStanding} huddleMoving={_huddleMoving} " +
                      $"huddleWhere={_huddleWhere} " +
                      $"crowdHuddleSamples={_huddles.Count} " +
                      // AND WHETHER THE MOB IS PEOPLE SENT TO ONE POINT.
                      // `busiestPlace` is how many walkers shared a scheduled
                      // spot; `crowdSpread` is the widest ring that had to be
                      // built for one. A huddle of forty with a busiest place of
                      // three is people who merely ended up near each other and
                      // wants a different fix entirely — and a spread stuck at
                      // 0.80 on a run with a busy place is the push not arriving.
                      $"busiestPlace={GameController.BusiestPlace} " +
                      $"busiestNear={GameController.BusiestNear} headingIntoRoad={GameController.WalkersHeadingIntoRoad} headingCounted={GameController.WalkersHeadingCounted} " +
                      // HOW MANY SPOTS, against `addressesLeftInRoad`.
                      // Sixteen walkers heading for nine corners the map
                      // deliberately left in a right of way is a busy
                      // morning; sixteen heading for sixteen patches of
                      // tarmac is sixteen people standing in traffic.
                      $"headingIntoRoadCells={GameController.WalkersHeadingIntoRoadCells} " +
                      $"crowdSpread={NpcWalker.WidestSpread:0.00} " +
                      $"claimHeld={_claimHeld} claimCaught={_claimCaught} claimsOk={claimsOk} " +
                      $"claimWhy=[{LawHost.ClaimWhy}] claimVia=[{_claimVia}] " +
                      $"lines={_game.Phones.All.Count} answered={_callsAnswered} " +
                      $"wrongPerson={_callsWrongPerson} rangOut={_callsRangOut} "
                      + $"callsTried={_callsAttempted} callsReachable={_callsReachable} "
                      + $"phonesOk={phonesOk} " +
                      $"panelsOk={panelsOk} panelsBad={panelsBad} idLeaks={idLeaks} " +
                      // CAN THE TEXT BE READ. Reported, not gated: some
                      // of these pairs are dimmed on purpose and a gate
                      // at AA would flatten the design before anybody
                      // decided that was wanted. The list comes first.
                      $"contrastChecked={DialogueUI.ContrastChecked} " +
                      $"contrastFailing={DialogueUI.ContrastFailing} " +
                      $"contrastWorst={DialogueUI.ContrastWorst:0.00} " +
                      $"contrastWorstWhere=[{DialogueUI.ContrastWorstWhere}] " +
                      $"contrastTightest={DialogueUI.ContrastTightest:0.00} " +
                      $"contrastTightestWhere=[{DialogueUI.ContrastTightestWhere}] " +
                      $"measureChecked={DialogueUI.MeasureChecked} " +
                      $"measureFailing={DialogueUI.MeasureFailing} " +
                      $"measureWorst={DialogueUI.MeasureWorst:0} " +
                      $"measureWorstWhere=[{DialogueUI.MeasureWorstWhere}] " +
                      $"measureFails=[{DialogueUI.MeasureFails}] " +
                      $"identifiedPeak={_identifiedPeak} " +
                      $"attendingAtIdentified={_attendingAtIdentifiedPeak} " +
                      $"identifiedEver={_identifiedEver.Count} " +
                      $"doubtShown={doubtShown} doubtHeld={doubtHeld} doubtWho={doubtWho} " +
                      // BOTH POPULATIONS AND BOTH WEIGHTS. Counts alone cannot
                      // show the mechanic: two racket rumours from a capable
                      // runner and two from a clumsy one are the same COUNT and
                      // a very different case against you.
                      $"exposureYours={exYours} exposureTheirs={exTheirs} " +
                      $"exposureYoursW={exYoursW:0.00} exposureTheirsW={exTheirsW:0.00} " +
                      $"exposureSays=[{exSays}] " +
                      // WHAT STOOD IN FRONT OF THE PLAYER, per shot and at
                      // worst. Reported, not gated: a city has street furniture
                      // in it and a camera that never passes behind anything is
                      // a camera in an empty world. The bound, if there is one,
                      // comes off this series (rule 2).
                      $"shotsAimed={_shotsAimed} shotsBlocked={_shotsBlocked} " +
                      $"shotBlocker=[{_shotBlockWhat}] " +
                      $"shotNearFracWorst={_shotNearFracWorst:0.00} " +
                      $"shotNearFracWhere=[{_shotNearFracWhere}] uiOk={uiOk} " +
                      $"labels={_labels} fontless={_labelsFontless} blankLabels={_labelsBlank} " +
                      $"collidingNames={_labelsColliding} collidingWorldText={_collidingWorldText} " +
                      $"collidingBubbles={_collidingBubbles} bubblesAtWorst={_bubblesAtWorst} bubblesOnScreen={_bubblesOnScreen} " +
                      // WHY THEY COLLIDE, if they do. `bubblesAtCeiling` are
                      // the ones the stack had no room left for and put on top
                      // of a neighbour anyway; `bubblesMade` is its denominator
                      // and is counted on the same event, so it is a fraction
                      // rather than two maxima divided.
                      $"bubblesMade={SpeechBubble.BubblesMade} " +
                      $"bubblesAtCeiling={SpeechBubble.BubblesAtCeiling} " +
                      // AND WHETHER THE SCREEN TEST RAN AT ALL.
                      // `bubblesNoBounds` is the one uncertainty in it: a
                      // TextMesh built this frame may have no renderer
                      // bounds yet, and without this a `screenLifted` of
                      // zero would read as "nothing overlapped" when it may
                      // mean "nothing could be measured".
                      $"bubblesScreenLifted={SpeechBubble.BubblesScreenLifted} " +
                      $"bubblesNoBounds={SpeechBubble.BubblesNoBounds} " +
                      // The peak and the typical, side by side and named as
                      // what they are. The peak is "how bad did one moment
                      // get"; the median is "how does this street read".
                      $"bubbleOverlapMedian={bubbleMedian:0.00} bubbleSamples={_bubbleOverlap.Count} " +
                      $"textMirrored={_textMirrored} " +
                      $"textFlat={_textFlat} textFlatWorst=[{_textFlatWorst}] " +
                      $"textFacingAway={_textFacingAway} textVisibleAtAway={_textVisibleAtAway} textVisible={_textVisible} " +
                      $"billboardsStale={_billboardsStale} billboardsAtWorst={_billboardsAtWorst} " +
                      $"billboardStaleMedian={BillboardStaleMedian:0.000} " +
                      $"billboardWorstDeg={_billboardWorstDeg:0.0} " +
                      $"billboardsAimed={_billboardsAimed} " +
                      $"billboardsTracked={_billboardsTracked} " +
                      $"worstNameFrac={NameTags.WorstNameFrac:0.000} " +
                      $"nameTagsTooNear={NameTags.TooNear} nameTagsRects={NameTags.RectCalls} " +
                      $"worstNameMetres={NameTags.WorstNameMetres:0.00} " +
                      $"worstNameBoundsY={NameTags.WorstNameBoundsY:0.00} " +
                      $"worstNameScale={NameTags.WorstNameScale:0.000} " +
                      $"worstNameCentreMetres={NameTags.WorstNameCentreMetres:0.00} " +
                      $"worstNamePixels={NameTags.WorstNamePixels:0} " +
                      // THE MEDIAN BESIDE THE PEAK, AND THE COUNT BESIDE BOTH.
                      // `worstNameFrac` is honest and it answers "did a name
                      // ever fill the frame". The night still asks "is this how
                      // the street looks", which no peak can answer, and the
                      // sample size is part of the statistic even though
                      // nothing about the number says so.
                      $"nameFracMedian={NameTags.NameFracMedian:0.000} " +
                      $"nameFracP90={NameTags.NameFracP90:0.000} " +
                      // THE OTHER AXIS. Every nameplate number in this
                      // project has been a HEIGHT, and the night still shows
                      // two labels each about a third of the frame wide with
                      // the second clipping off the edge — while every height
                      // reading says the plates are inside their bound. Both
                      // are true, which is what makes a one-axis bound on a
                      // two-axis object worth naming. The text comes with it,
                      // because a label's width is mostly a fact about its
                      // letters and the name says so in one reading.
                      $"nameWidthMedian={NameTags.NameWidthMedian:0.000} " +
                      $"nameWidthP90={NameTags.NameWidthP90:0.000} " +
                      $"nameShownWidth={NameTags.NameShownWidthMedian:0.000} " +
                      $"nameShownWidthP90={NameTags.NameShownWidthP90:0.000} " +
                      // AND THE POST-CAP WORST, WHICH WAS COMPUTED AND NEVER
                      // PRINTED. `nameWidthWorst=0.424` on "Wendell Dujmovic" is
                      // the label as the PROJECTION found it, before `Pin` runs;
                      // its post-cap twin is kept in the same pass, in a field
                      // beside it, and only the alarming half reached the
                      // verdict. So the reader gets a name at two fifths of the
                      // frame and no way to tell whether the cap already fixed
                      // it — which is the exact question a width bound would
                      // have to answer, and `NameTags`' own comment says no
                      // bound goes on until the series is read.
                      //
                      // The medians agree to three decimals (0.067 and 0.140
                      // both ways) because the cap bites 29 times in 2,226
                      // samples. The tail is the only place these two can
                      // differ, and the tail is what the still shows.
                      $"nameShownWidthWorst={NameTags.WorstNameWidthFrac:0.000} " +
                      $"nameShownWidthWorstText=[{NameTags.WorstNameWidthText}] " +
                      $"nameWidthWorst={NameTags.WorstNameWidthFrac:0.000} " +
                      $"nameWidthWorstText={NameTags.WorstNameWidthText} " +
                      $"nameFracSamples={NameTags.NameFracSamples} " +
                      $"worstBubbleFrac={NameTags.WorstBubbleFrac:0.000} " +
                      $"worstBubbleMetres={NameTags.WorstBubbleMetres:0.00} " +
                      $"bubbleFracMedian={NameTags.BubbleFracMedian:0.000} " +
                      $"bubbleFracP90={NameTags.BubbleFracP90:0.000} " +
                      // AND WHAT THE CAP DID. `worstBubbleFracPreCap` is what
                      // the bubble WOULD have taken; `worstBubbleFrac` beside it
                      // is what it actually took, so the clamp's effect is a
                      // subtraction rather than a claim. `bubblesPinned=0` with
                      // a pre-cap worst above 0.12 means the pin never ran,
                      // which is a different fault from it not being needed.
                      $"bubbleFracPreCap={NameTags.WorstBubbleFracPreCap:0.000} " +
                      $"bubblesPinned={NameTags.BubblesPinned} " +
                      $"bubblesPinnedAtShot={_bubblesPinnedAtShot} " +
                      $"bubblesShotLifted={_bubblesShotLifted} " +
                      $"namesPinnedAtShot={_namesPinnedAtShot} " +
                      $"bubblePinFloor={NameTags.BubblePinFloor:0.000} " +
                      $"bubbleFracSamples={NameTags.BubbleFracSamples} " +
                      // INPUT PARITY, AS A NUMBER. The claim is that a
                      // conversation can be carried without typing; it fails when
                      // the chip row runs dry, and no gate could see that because
                      // every gate asks whether the chips were BUILT. A zero here
                      // means somebody was left with nothing but a text field.
                      $"fewestChips={(DialogueUI.ChipRefreshes > 0 ? DialogueUI.FewestChipsOffered : -1)} " +
                      $"chipRefreshes={DialogueUI.ChipRefreshes} " +
                      $"nameTagsOffered={NameTags.OfferedPeak} nameTagsHidden={NameTags.SuppressedPeak} nameTagsUnresolved={NameTags.UnresolvedPeak} nameTagsOffScreen={NameTags.OffScreenPeak} nameTagsOffScreenCalls={NameTags.OffScreen} " +
                      $"nameTagsActive={NameTags.ActivePeak} " +
                      $"nameTagsUpDot={NameTags.WorstUpDot:0.000} " +
                      $"speechUpDot={SpeechBubble.WorstUpDot:0.000} " +
                      $"nameTagsFrames={NameTags.ResolvedFrames} " +
                      // THE SIZE CAP AND WHETHER IT BIT. `namePinCap` is the
                      // bound, printed beside the readings it was taken from so
                      // nobody has to go looking for where 0.12 came from;
                      // `namesPinned` is how many times a label was actually
                      // brought down, which is the denominator that stops
                      // `worstNameFrac` falling and reading as "the tail went
                      // away on its own". `namePinFloor` is the smallest scale
                      // ever applied — it is also the check on this code's one
                      // assumption, that a name's own scale starts at 1.
                      $"namePinCap={NameTags.PinFrac:0.000} " +
                      // THE WHOLE NAME FAMILY, ON ONE LINE, AT ONE INSTANT —
                      // AND THIS IS THE CORRECTION FOR EVERY WRONG ANSWER I
                      // GAVE ABOUT IT TODAY.
                      //
                      // These lived on the `glyphs` line, which is emitted on
                      // every SCREENSHOT. `nameTagsOffered` lives here, on the
                      // done line, at the end of the run. I spent the day
                      // comparing the two and calling the difference an
                      // arithmetic impossibility: 42 against 13, then 40
                      // against 9. Both were true. They are the same counter
                      // read at two different moments, and the peaks kept
                      // climbing after the last shot.
                      //
                      // FOUR PUBLISHED EXPLANATIONS, ALL WRONG, AND THE FIFTH
                      // WAS DELETING THE COUNTER. `OfferedPeak` was never
                      // broken; it is restored, and the thing that was broken
                      // was reading it off a different line from its own
                      // denominator. The rule this file already carries — a
                      // peak's denominator must come from the SAME INSTANT as
                      // its numerator — turns out to apply to the LOG LINE as
                      // well as to the frame, and nothing said so.
                      //
                      // So the family is together. Anything about the run as a
                      // whole belongs here; the shot line keeps only what is
                      // true of the shot.
                      //
                      // AND THE `+` AT THE START OF THIS LINE WAS THE SECOND
                      // ROUND TRIP. The line above ends with `+` already, so a
                      // leading `+` here is a UNARY plus applied to a string —
                      // CS0023, a semantic error rather than a syntax one, and
                      // therefore invisible to the syntax pass added an hour
                      // ago for the CS1003 at the other end of this same block.
                      // One paste, two compile errors, two builds, and the
                      // local checker's allow-list swallowed the second exactly
                      // as it had swallowed the first.
                      $" namesManagedEver={NameTags.ManagedEver}"
                      + $" namesOfferCalls={NameTags.Offers}"
                      + $" namesDistinctPeak={NameTags.OfferedDistinctPeak}"
                      + $" namesWorstOffered={NameTags.OfferedAtWorst}"
                      + $" namesWorstAlive={NameTags.AliveAtWorst}"
                      + $" namesWorstObjects={NameTags.DistinctObjectsAtWorst}"
                      + $" namesWorstIds={NameTags.DistinctIdsAtWorst}"
                      + $" namesManagedDead={NameTags.ManagedDead}"
                      + $" namesDupOffers={NameTags.DupOffers}"
                      + $" namesDupWorst={NameTags.DupWorst}"
                      + $" npcsListed={GameController.WalkersListed}"
                      + $" npcsDuplicated={GameController.WalkersDuplicated}"

                      // THE `+` THAT WAS MISSING HERE COST A ROUND TRIP, and
                      // the reason it got through is worth more than the fix:
                      // ShapeCheck reported zero errors on this file. A
                      // syntax error is not reference-dependent, so the one
                      // local check whose whole job is to catch what CI would
                      // catch should have seen it and did not.
                      + $"namesPinned={NameTags.NamesPinned} " +
                      $"namePinFloor={NameTags.NamePinFloor:0.000} " +
                      $"nameTagsUnplaced={NameTags.WorstUnplaced} " +
                      $"worldText={_worldText} depthTested={_worldTextDepth} " +
                      $"realBody={RealBody.Attached} realBodyWhy=[{RealBody.Why}] " +
                      $"bodyUp={RealBody.Upright:0.000} bodyRot=[{RealBody.Orientation}] " +
                      $"playerPose={PlayerPoseRange:0.00000} " +
                      $"headAboveHips={_worstHeadAboveHips:0.000} " +
                      $"hipsAboveFeet={_worstHipsAboveFeet:0.000} " +
                      $"postureRead={_postureSeen} " +
                      $"preHeadAboveHips={_worstPreHeadAboveHips:0.000} " +
                      $"preHipsAboveFeet={_worstPreHipsAboveFeet:0.000} " +
                      $"prePoseRead={_prePostureSeen} " +
                      $"bodyPitch={_worstBodyPitch:0.0} bodyRoll={_worstBodyRoll:0.0} " +
                      $"clip=[{_clipName}] avatarProbeRead={_avatarProbeSeen} " +
                      // THE FIRST FRAME, WHICH IS THE ONE SAMPLE THAT CANNOT
                      // CONTAIN OUR OWN SOLVE. Upright here with everything
                      // after it inverted means the pose is accumulating, not
                      // arriving inverted — and `playerHasController` says
                      // whether anything is rewriting it each frame.
                      $"firstPreHeadAboveHips={CharacterRig.FirstPreHeadAboveHips:0.000} " +
                      $"firstPreHipsAboveFeet={CharacterRig.FirstPreHipsAboveFeet:0.000} " +
                      $"firstPreRead={CharacterRig.FirstPreRead} " +
                      $"restArmDrop={CharacterRig.RestArmDropDegrees:0.0} " +
                      $"restArmRead={CharacterRig.RestArmRead} " +
                      $"liveArmDrop={CharacterRig.LiveArmDropDegrees:0.0} " +
                      // THE STREET, NOT THE PLAYER, AND A MEDIAN NOT A PEAK.
                      // liveArmDrop returns early unless it is the bought
                      // player body, so it has never described the crowd at
                      // all — and it is a worst-over-run, so it cannot tell
                      // one frozen scarecrow from everybody swinging through
                      // the top of a stride. These two are medians ACROSS
                      // BODIES — boxes as well as bought ones, because the
                      // question is what the STREET looks like: the typical
                      // frame, and the frame where it stood widest.
                      $"armStreet={CharacterRig.ArmDropStreetMedian:0.0} " +
                      $"tposeBodies={CharacterRig.TposeBodies} " +
                      $"tposeAtGrant={CharacterRig.TposeAtGrant} " +
                      $"tposeWhy=[{CharacterRig.TposeWhy}] " +
                      $"tposeWho={CharacterRig.TposeWho} " +
                      $"armStreetWorst={CharacterRig.ArmDropStreetWorst:0.0} " +
                      // AND THE WIDEST BODY, because both of the above are
                      // medians across bodies and the night frame plainly shows
                      // three people in a T-pose. A minority is invisible to a
                      // median; `armWidest` near ninety in a typical frame is a
                      // scarecrow standing there all run.
                      $"armWidest={CharacterRig.ArmWidestMedian:0.0} " +
                      $"armWidestWorst={CharacterRig.ArmWidestWorst:0.0} " +
                      $"armP90={CharacterRig.ArmP90Median:0.0} " +
                      // WITHOUT THE PLAYER. `armWidest=54.2` sits inside the
                      // band his own clip already holds him at (`preArmDrop=65.3`),
                      // so the widest body in a frame may simply be him — and
                      // the scarecrows in the night stills would then be a third
                      // fault nothing has yet measured. One branch splits them.
                      $"armCrowdWidest={CharacterRig.CrowdArmWidestMedian:0.0} " +
                      $"armCrowdWidestWorst={CharacterRig.CrowdArmWidestWorst:0.0} " +
                      // AND HOW FAR OUT TO THE SIDE, which the drop angle
                      // cannot tell you: a walk swings arms fore and aft and
                      // produces no lateral component at all, while a T-pose is
                      // entirely lateral. Near zero settles the retraction;
                      // near ninety un-settles it.
                      $"armSide={CharacterRig.ArmSideMedian:0.0} " +
                      $"armSideWorst={CharacterRig.ArmSideWorst:0.0} " +
                      // AND HOW FAR FORWARD THE TORSO IS PITCHED, because two
                      // bodies in review_day1_noon are leaning at the waist
                      // while walking and nothing in the project measures a
                      // spine. `leanBodies` is the denominator: every
                      // mannequin returns nothing, so a zero without it
                      // cannot tell "upright" from "never read".
                      $"lean={CharacterRig.LeanMedian:0.0} " +
                      $"leanWorst={CharacterRig.LeanWorst:0.0} " +
                      $"leanBodies={CharacterRig.LeanBodies} " +
                      $"leanDriven={CharacterRig.LeanDriven:0.0} " +
                      $"leanRest={CharacterRig.LeanRest:0.0} " +
                      $"leanDrivenFrames={CharacterRig.LeanDrivenFrames} " +
                      $"leanRestFrames={CharacterRig.LeanRestFrames} " +
                      // THE MIDDLE DRIVEN BODY, NOT THE WORST ONE IN THE FRAME.
                      // `leanDriven` is a median of frame MAXIMA — about a 92nd
                      // percentile with a dozen bodies in shot — and it was
                      // quoted as "a MEDIAN, so it is the whole street", which
                      // it structurally cannot be. This is that number.
                      $"leanTypical={CharacterRig.LeanDrivenTypical:0.0} " +
                      // AND THE SAME SPINE BEFORE THIS PROJECT WRITES IT.
                      // ANSWERED on 52037ba: preLeanDriven=41.6 against a
                      // leanWorst of 41.7, peak against peak, so the write adds
                      // a tenth of a degree and the bought clip arrives already
                      // leaning. Kept because it is the control for every later
                      // change to the pose code.
                      $"preLeanDriven={CharacterRig.PreLeanDriven:0.0} " +
                      $"preLeanRest={CharacterRig.PreLeanRest:0.0} " +
                      $"preLeanReads={CharacterRig.PreLeanReads} " +
                      // THE SPEED OF THE BODY AT THE WORST LEAN, SAME INSTANT.
                      // A walk blends at 1.4 m/s and a run at 4.0, so near 1.4
                      // the walk cycle itself is bent double and near 2.6 it is
                      // an escort hurrying and the animation is correct.
                      $"leanWorstSpeed={CharacterRig.LeanWorstSpeed:0.00} " +
                      $"leanWorstDriven={CharacterRig.LeanWorstDriven} " +
                      // FALSE MEANS THE PLAYER, and the player is in shot every
                      // frame at the closest distance in the game. A walker
                      // bent double in a crowd of fifty is nearly invisible;
                      // the player bent double is the whole screen.
                      $"leanWorstIsWalker={CharacterRig.LeanWorstIsWalker} " +
                      $"armSideMannequin={CharacterRig.ArmSideMannequin:0.0} " +
                      $"armSideSkinned={CharacterRig.ArmSideSkinned:0.0} " +
                      $"armSideMannequinFrames={CharacterRig.ArmSideMannequinFrames} " +
                      $"armSideSkinnedFrames={CharacterRig.ArmSideSkinnedFrames} " +
                      $"armBodies={CharacterRig.ArmBodiesMedian:0} " +
                      // AND WHETHER THE STREET'S BODIES ARE ANIMATING AT ALL.
                      // Every other animator reading in this verdict —
                      // `animCulling`, `animClipTime`, `animState` — is gated on
                      // `IsTheBoughtBody`, which is the player. Twelve crowd
                      // bodies are skinned at a time and 966 were granted last
                      // run, and none had ever been asked. `animDriven` minus
                      // `animAdvancing` is a body with a controller that is not
                      // moving, which is what a figure standing in its bind pose
                      // looks like from the inside.
                      $"animBodies={CharacterRig.AnimBodiesMedian:0} " +
                      $"animDriven={CharacterRig.AnimDrivenMedian:0} " +
                      $"animAdvancing={CharacterRig.AnimAdvancingMedian:0} " +
                      $"animStalledWorst={CharacterRig.AnimStalledWorst} " +
                      $"armFrames={CharacterRig.ArmFrames} " +
                      $"liveArmRead={CharacterRig.LiveArmRead} " +
                      $"preArmDrop={CharacterRig.PreArmDropDegrees:0.0} " +
                      $"preArmRead={CharacterRig.PreArmRead} " +
                      $"workNoonCrowd={(_workDaysSeen > 0 ? _workDayNoonCrowd / _workDaysSeen : -1)} " +
                      $"restNoonCrowd={(_restDaysSeen > 0 ? _restDayNoonCrowd / _restDaysSeen : -1)} " +
                      $"restDaysSeen={_restDaysSeen} workDaysSeen={_workDaysSeen} " +
                      $"restInFrame={(_restFrames > 0 ? _restFrameSum / _restFrames : -1)} workInFrame={(_workFrames > 0 ? _workFrameSum / _workFrames : -1)} framesRest={_restFrames} framesWork={_workFrames} " +
                      $"playerHasController={_playerHasController} " +
                      $"speedDriven={CharacterRig.SpeedDriven} " +
                      // HOW MANY BOUGHT BODIES GOT THEIR OWN LOOP PHASE. Zero
                      // beside a non-zero `walkerBodies` means everybody is
                      // still stepping in lockstep — the failure this seeds
                      // against, and one that only ever shows in a still.
                      $"phasesSeeded={CharacterRig.PhasesSeeded} " +
                      // The third shape trait, and zero beside a non-zero
                      // walkerBodies means the write never ran; uniform heads in
                      // a still WITH a non-zero count means it ran and lost.
                      $"headsScaled={CharacterRig.HeadsScaled} " +
                      // HOW MUCH OF THE CLIP'S HIP MOTION IS BEING THROWN AWAY.
                      // The rig assigns the hips from a rest position plus its
                      // own breath, dip and bob, on bodies whose Animator wrote
                      // a hip height that frame — while composing the pelvis
                      // ROTATION on the same bodies, under a comment giving the
                      // reason. Near zero means the clips barely move their
                      // hips and the assign is harmless; a few centimetres
                      // means the bought animation's vertical rhythm is being
                      // discarded and replaced by a phase it does not share.
                      // Read before touching it.
                      $"hipOverride={CharacterRig.HipOverrideMedian:0.000} " +
                      $"hipOverrideSamples={CharacterRig.HipOverrideSamples} " +
                      $"animCulling={CharacterRig.AnimCulling} " +
                      $"animClipTime={CharacterRig.AnimClipTime:0.00} " +
                      $"animState={CharacterRig.AnimStateHash} " +
                      $"crowdSpeed={NpcWalker.CrowdSpeedMean:0.00}/{NpcWalker.CrowdSpeedPeak:0.00} " +
                      $"crowdHip={Rig.LegSwing(0.25, NpcWalker.CrowdSpeedMean).hip:0.0} schedLag={NpcWalker.ScheduleLagMean:0.0}/{NpcWalker.ScheduleLagWorst:0.0} " +
                      $"armSplay={CharacterRig.ArmSplayDegrees:0.0} " +
                      // ON THE DONE-LINE, NOT ONLY IN THE GATE LABEL. The frame
                      // breakdown lives inside a gate, and a gate label prints
                      // when the gate FAILS — so on every green run the one
                      // number the cast tiering needs would be absent, and the
                      // run that most needs it is the one that passed. Same
                      // fault as the hand tier hiding in the threat gate.
                      $"rigsMs={RigsPerFrameMs():0.000} " +
                      $"bodySkinned={RealBody.Skinned} bodyDressed={RealBody.Dressed} " +
                      $"bodyKeptMats={RealBody.Kept} " +
                      $"bodyCoatArea={RealBody.DressedAreaFraction:0.000} " +
                      $"bodyCoatVerts={RealBody.DressedVertexFraction:0.000} " +
                      $"bodyCoverageRead={RealBody.CoverageRead} " +
                      $"bodyClothed={RealBody.Clothed} " +
                      $"bodyParts=[{RealBody.Parts}] " +
                      // BESIDE THE COVERAGE, because they contradict each other
                      // in the stills and only together do they say why. The
                      // coverage numbers ask whether a coat material reached
                      // every mesh and answer yes; the frame shows a figure that
                      // reads as bare plastic. `bodyCoat` is the missing third
                      // fact — what colour "coat" turned out to be.
                      $"bodyCoat=[{RealBody.CoatRead}] " +
                      $"bodyReadLum={_playerLum:0.0} bodyReadSat={_playerSat:0.000} bodyReadPx={_playerPixels} " +
                      $"bodyReadWhen={_bodyReadWhen} bodyReadRank={_bodyReadRank} " +
                      $"bodyOutshoneMedian={BodyOutshoneMedian:0.000} " +
                      $"bodyOutshoneShots={_bodyOutshone.Count} " +
                      // MEDIAN, and the SPREAD beside it. Two collapsed numbers
                      // cannot say whether the player's lower saturation is
                      // the player being unusual or the crowd being spread —
                      // and `crowdConsidered` against `crowdRead` says how many
                      // bodies were skipped for being off-screen, which is the
                      // difference between "the crowd reads like this" and
                      // "three bodies read like this".
                      $"crowdReadLum={_crowdLum:0.0} crowdReadSat={_crowdSat:0.000} crowdRead={_crowdSampled} " +
                      $"crowdConsidered={_crowdConsidered} crowdLumRange={_crowdLumRange} " +
                      $"crowdSatRange={_crowdSatRange} " +
                      $"bodyChoices={RealBody.BodyChoices} " +
                      // Kit-model props that actually reached the world.
                      // Zero with models committed means the prefab builder
                      // or the name candidates missed — the difference
                      // between a pipeline and a street (rule 6).
                      $"propsPlaced={AssetLibrary.PropsPlaced} " +
                      $"parkedCars={WorldBuilder.ParkedCars} shopNames={WorldBuilder.ShopNamesPainted} " +
                      $"smokeStacks={WorldBuilder.SmokeStacks} gulls={WorldBuilder.Gulls} " +
                      // THE WALKERS' BODIES, counted separately because
                      // `RealBody.Attached` is restored after each one and
                      // therefore cannot see them. A walker body that
                      // silently failed to attach would otherwise look
                      // exactly like one that was never asked for.
                      $"walkerBodies={RealBody.Extra} " +
                      $"walkerBodyCap={NpcWalker.RealBodyCap} " +
                      $"walkerBodiesFailed={RealBody.ExtraFailed} " +
                      $"walkerBodyWhy=[{RealBody.ExtraWhy}] " +
                      // BODY LOD, AND `walkerBodies` ABOVE IS NOW A LIFETIME
                      // COUNT RATHER THAN A HEADCOUNT. It was both while a
                      // walker chose its body once at spawn; with a budget that
                      // moves, attachments accumulate and the number of bodies
                      // currently worn is `walkerBodies - walkerBodiesOff`.
                      // Saying so here because the metric did not change its
                      // name when the question it answers moved, which is the
                      // drift that has already cost this project three wrong
                      // readings.
                      $"walkerBodiesOff={RealBody.Detached} " +
                      // THE WARDROBE, RECONNECTED. Ten body prefabs against a
                      // named cast of forty-three means at least two people on
                      // screen share a model at all times, and texture
                      // extraction silently stopped the wardrobe painting them
                      // — `bodyParts` has read "nothing to paint" since it
                      // landed. `bodyTinted=0` beside a non-zero `bodyKeptMats`
                      // is that regression coming back, and it is invisible in
                      // every other number here.
                      $"bodyTinted={RealBody.Tinted} " +
                      // AND WHETHER ANY OF IT ARRIVED, which `bodyTinted` on
                      // its own cannot say. A wash of pure white is applied as
                      // successfully as any other and changes no pixel, so
                      // 5,334 tints was a true number about a system doing
                      // nothing for a third of the city. `bodyWashWhite` is the
                      // MEDIAN distance of the applied wash from white on a
                      // 0..100 scale — zero is a wardrobe that renders as the
                      // model's own texture — with `bodyWashSampled` as its
                      // denominator and `bodyWashNone` counting the people
                      // whose coat came out under 5. Replicating the shipped
                      // rule over the roster put that last one at 39%.
                      $"bodyWashWhite={RealBody.WashFromWhite:0.0} " +
                      // AND WHAT IT IS MULTIPLYING, which is the number that
                      // decides whether the wash's ceiling is in the right
                      // place. The wardrobe caps a crowd garment at value 0.46;
                      // a wash whose top end is 1.0 leaves a bright albedo
                      // exactly as bright as it arrived. Whole series, one line
                      // per model, because ten numbers is short enough to show
                      // and the one loud sheet is the finding a median hides.
                      $"bodyAlbedo=[{AlbedoRead()}] " +
                      $"bodyWashSampled={RealBody.WashSampled} " +
                      $"bodyWashNone={RealBody.WashNearWhite} " +
                      // People whose sheet is darker than their band, so they
                      // render below the wardrobe rather than at it. The
                      // question bodyWashNone used to answer before the
                      // anchored rule made a white multiply the correct
                      // outcome for a dark sheet.
                      $"bodyWashUnreached={RealBody.WashUnreached} " +
                      // THE PAINT PATH OVER THE WHOLE RUN. `bodySkinned` and
                      // `bodyDressed` above are reset at every attach, so they
                      // describe the last body the LOD happened to grant. These
                      // three are lifetime, and they are what says whether the
                      // wash is the wardrobe's only route to the eye or merely
                      // was for one walker.
                      // THE SAMENESS, WITH A NUMBER ON IT AT LAST. `bodyFaces`
                      // is the median count of distinct models among the bodies
                      // the LOD granted, `bodyFacesOf` the median number of
                      // bodies those were chosen from, and `bodyFacesAtMost`
                      // the same pair taken from the busiest single sample —
                      // one instant, both halves, so the ratio means something.
                      // Ten models against forty-three named people bounds this
                      // at ten however good the wardrobe gets, which is exactly
                      // why the wash has to carry the rest.
                      $"bodyFaces={ModelMedian(v => v.y)} " +
                      $"bodyFacesOf={ModelMedian(v => v.x)} " +
                      $"bodyFacesAtMost={ModelAtMost()} " +
                      $"bodyFaceSamples={_modelSamples.Count} " +
                      // AND WHAT THE RULE DECIDED, over the run rather than for
                      // the last body. `bodyParts` reads "nothing to paint"
                      // whenever the final walker arrived fully textured, which
                      // is most runs, so it can never explain a lifetime zero.
                      $"bodyPartsEver=[{string.Join(" ", RealBody.PartsEver)}] " +
                      // BUILD, WHICH THE BOXES HAD AND THE BOUGHT BODIES THREW
                      // AWAY. `bodyBreadth` is the player's; `bodyBreadths` is
                      // every distinct one the street has worn, which is the
                      // half that answers "does the crowd vary" — one value
                      // cannot, and `crowdLum` already learned that lesson the
                      // expensive way.
                      $"bodyBreadth={RealBody.Breadth:0.00} " +
                      $"bodyBreadths=[{string.Join(" ", RealBody.BreadthsEver)}] " +
                      $"bodySkinnedEver={RealBody.SkinnedEver} " +
                      $"bodyDressedEver={RealBody.DressedEver} " +
                      $"bodyKeptEver={RealBody.KeptEver} " +
                      // WHO GOT THE CAST'S BRIGHTNESS LIFT — AND THE CROWD HALF
                      // OF THIS PAIR CANNOT CURRENTLY BE ANYTHING BUT ZERO.
                      //
                      // The split was built because every walker was being
                      // raised past the crowd's value ceiling, and
                      // `bodyLiftedCast=1036 bodyLiftedCrowd=0` reads as that
                      // fix working. It cannot read as anything else: the body
                      // LOD only grants to a walker with `WantsRealBody`, and
                      // the one place in the game that spawns crowd passes
                      // `realBody: false`. So no crowd walker ever holds a real
                      // body, `cast: !IsCrowd` is always `cast: true`, and this
                      // counter is structurally zero.
                      //
                      // A zero that could never have been anything else is not
                      // evidence. `bodyCrowdEligible` is the denominator that
                      // turns it back into evidence — zero there says the branch
                      // is unreachable today rather than untaken, and the day
                      // the crowd gets faces both counters start answering the
                      // question they were written for.
                      $"bodyLiftedCast={RealBody.LiftedCast} " +
                      $"bodyLiftedCrowd={RealBody.LiftedCrowd} " +
                      $"bodyLodPasses={GameController.BodyLodPasses} " +
                      $"bodyLodEligible={GameController.BodyLodEligible} " +
                      $"bodyCrowdEligible={GameController.BodyCrowdEligible} " +
                      $"walkersPrimitive={GameController.WalkersPrimitive} " +
                      $"capsulesLoose={_capsulesLoose} " +
                      $"capsulesLooseWho=[{_capsulesLooseWho}] " +
                      $"capsulesSeen={_capsulesSeen} " +
                      $"capsulesAnimOut={_capsulesAnim} " +
                      $"capsulesAnimWho=[{_capsulesAnimWho}] " +
                      $"capsulesSizeOut={_capsulesSized} " +
                      $"bodiesUndressed={_bodiesUndressed} " +
                      $"bodiesUndressedWho=[{_bodiesUndressedWho}] " +
                      $"walkersPrimitiveEver={GameController.WalkersPrimitiveEver} " +
                      $"walkersPrimitiveOf={GameController.WalkersPrimitiveOf} " +
                      $"walkersPrimitiveWho=[{string.Join(" ", GameController.WalkersPrimitiveWho)}] " +
                      $"bodyLodNear={GameController.BodyLodNear} " +
                      $"bodyLodSlack={GameController.BodyLodSlack} " +
                      // WHO IS LIMPING. `Rig.Limp` has had one writer since it
                      // was built — the player — so the city has never limped,
                      // whatever was done to it. `limpNames` is the half that
                      // matters: a zero count means nobody was hurt OR the
                      // lookup matched nobody, and only a name separates those.
                      // Printed against the tick list from the same pass, so
                      // the fraction is two numbers from one instant.
                      $"limpNow={GameController.WalkersHurtNow} " +
                      $"limpOf={GameController.WalkersListed} " +
                      $"limpWorst={GameController.WalkerCapabilityWorst:0.00} " +
                      $"limpNames=[{string.Join(",", GameController.WalkersHurtEver)}] " +
                      // THE THRASH READING. No dwell time has been invented to
                      // bound these — the band already carries six metres of
                      // hysteresis and whether that is enough is a measurement,
                      // not a guess. Grants roughly matching how many people
                      // walked past is the working case; thousands is thrash,
                      // and then a dwell time can come from the series.
                      $"bodyGrants={NpcWalker.BodyGrants} " +
                      $"bodyRevokes={NpcWalker.BodyRevokes} " +
                      $"bodyGrantsFailed={NpcWalker.BodyGrantsFailed} " +
                      // AND HOW LONG A BODY IS KEPT, which is what the counts
                      // above cannot say. 966 grants spread over a long run and
                      // 966 made by four people straddling one boundary read
                      // identically as a count and want opposite fixes. Seconds
                      // is a walker crossing the band; milliseconds is flicker,
                      // and only then does a dwell time have a number to be.
                      $"bodySpell={NpcWalker.BodySpellMedian:0.00} " +
                      $"bodySpellShortest={NpcWalker.BodySpellShortest:0.00} " +
                      $"bodySpells={NpcWalker.BodySpells} " +
                      $"bodyGrantWhy=[{NpcWalker.BodyGrantWhy}] " +
                      $"bindHeadAboveHips={RealBody.BindHeadAboveHips:0.000} " +
                      $"bindHipsAboveFeet={RealBody.BindHipsAboveFeet:0.000} " +
                      $"bindPoseRead={RealBody.BindPoseRead} " +
                      $"scaledHeadAboveHips={RealBody.ScaledHeadAboveHips:0.000} " +
                      $"scaledHipsAboveFeet={RealBody.ScaledHipsAboveFeet:0.000} " +
                      $"scaledPoseRead={RealBody.ScaledPoseRead} " +
                      $"twinHeadAboveHips={RealBody.TwinHeadAboveHips:0.000} " +
                      $"twinHipsAboveFeet={RealBody.TwinHipsAboveFeet:0.000} " +
                      $"twinRead={RealBody.TwinRead} twinHuman={RealBody.TwinHuman} " +
                      $"twinWhy=[{RealBody.TwinWhy}] " +
                      $"sceneClean={SceneAudit.Clean} sceneRenderers={SceneAudit.Renderers} " +
                      $"playerPrimitive={PlayerPrimitiveShowing()} " +
                      $"wardrobe=[{string.Join(" ", System.Linq.Enumerable.Select(GameController.WardrobeWorn, kv => kv.Key + ":" + kv.Value))}] " +
                      $"{(badPanels.Count > 0 ? "broken=[" + string.Join(",", badPanels) + "] " : "")}" +
                      $"{Perf.Summary()} trafficMs={(trafficCost != null ? trafficCost.MeanMs : 0):0.000} perfOk={perfOk} " +
                      // mean/median/peak bodies within 20m and within 8m,
                      // sampled every in-game hour across the whole run.
                      $"seen20={Dist(_within20)} seen8={Dist(_within8)} " +
                      $"near={(_game.Populace != null ? _game.Populace.CountIn(Lod.Near) : 0)} " +
                      $"mid={(_game.Populace != null ? _game.Populace.CountIn(Lod.Mid) : 0)} crowdOk={crowdOk} " +
                      $"beats=[{string.Join(",", beatStates)}] attended={beatsAttended} skipped={beatsSkipped} " +
                      $"shafts={LightShaft.Count} wet={SceneLighting.Wetness:0.00} " +
                      $"dressed={WorldBuilder.Dressed} dressedInRoad={WorldBuilder.DressedInRoad} dressedPulled={WorldBuilder.DressedPulled} dressedStuck={WorldBuilder.DressedStuckInRoad} dressedWorstPull={WorldBuilder.DressedWorstPull:0.00} dressedRoadWidth=[{RoadDepthRead()}] dressedStuckOn=[{string.Join(" ", WorldBuilder.DressedStuckOn)}] addressesSetBack={Ledger.Core.StreetMap.AddressesSetBack} addressesRefused={Ledger.Core.StreetMap.AddressesRefused} addressesLeftInRoad={Ledger.Core.StreetMap.AddressesLeftInRoad} addressDriftWorst={Ledger.Core.StreetMap.AddressDriftWorst:0.00} addressDriftMedian={Ledger.Core.StreetMap.AddressDriftMedian:0.00} placeStopsInRoad={WorldBuilder.PlaceStopsInRoad} placeFacesInRoad={WorldBuilder.PlaceFacesInRoad} placeFacesInLane={WorldBuilder.PlaceFacesInLane} placeFacesInRoadWho=[{string.Join(" ", WorldBuilder.PlaceFacesInRoadWho)}] doors={WorldBuilder.Doors} premises=[shop{WorldBuilder.PremisesBuilt[0]} house{WorldBuilder.PremisesBuilt[1]} tenement{WorldBuilder.PremisesBuilt[2]} shed{WorldBuilder.PremisesBuilt[3]}] perNear={perNear:0.00} perFar={perFar:0.00} " +
                      $"winPaned={WorldBuilder.WindowPanes} winBanded={WorldBuilder.WindowBands} " +
                      $"cables={StreetFurniture.CableCount} " +
                      // The back of a block has a shape now. Zero means the
                      // near-core test rejected everything, which is a finding
                      // about the density ramp rather than about fire escapes.
                      $"fireEscapes={WorldBuilder.FireEscapes} " +
                      $"leanTos={WorldBuilder.LeanTos} " +
                      $"mullions={WorldBuilder.Mullions} " +
                      // THE SKYLINE, AND ITS CAUSE ON THE SAME LINE. A third of
                      // the windows lit is right at nine in the evening and a
                      // fault at four in the morning, and only the fraction
                      // beside it can say which — two numbers from two lines
                      // would be two readings again. `windowsTotal=0` is a
                      // build that drew no windows, which every other number
                      // here would report as a dark city.
                      $"windowsLit={WorldBuilder.WindowsLit} " +
                      $"windowsTotal={WorldBuilder.WindowsTotal} " +
                      $"windowsHome={WorldBuilder.WindowsHomeFraction:0.00} " +
                      // Shopfronts counted apart from flats, because "a third of
                      // the windows are lit" is a different finding depending on
                      // which third — and zero shops at noon is a fault while zero
                      // at four in the morning is the point.
                      $"windowsShop={WorldBuilder.WindowsShop} " +
                      // AND `windowsShopLit=0` IS NOT THE FAULT IT LOOKS LIKE.
                      // It has read zero in all 131 kept runs — `gates.py
                      // --constant` — and that is the LAST-WINS value, written
                      // at whatever hour the run happened to end, which is
                      // after midnight every time. The reading that describes a
                      // picture is `windowsShopLitAtShot`, latched when the
                      // night still was taken, with `windowsHourAtShot` beside
                      // it: 154 of 517 at 23:00 on the last build. Read those.
                      $"windowsShopLit={WorldBuilder.WindowsShopLit} " +
                      // AND THE SAME THREE AT THE MOMENT THE NIGHT FRAME WAS
                      // TAKEN, which is the only instant any of this is ever
                      // judged at. The live ones describe whatever hour the run
                      // ended on, and after midnight every shop is shut by
                      // design — a zero that reads as a broken rule.
                      $"windowsLitAtShot={_windowsLitAtShot} " +
                      $"windowsShopAtShot={_windowsShopAtShot} " +
                      $"windowsShopLitAtShot={_windowsShopLitAtShot} " +
                      $"windowsHourAtShot={_windowsHourAtShot} " +
                      // BUS STOPS AND CAB RANKS DRAWN. Counted for the reason
                      // `cables` is: "the bus route reads as a route" has to be
                      // a number, and zero here means the sim's own loop came
                      // back empty — which would be a map fault reported as
                      // scenery rather than found six builds later.
                      $"transit={StreetFurniture.TransitCount} " +
                      $"reflWet={_reflWetFrames} reflDry={_reflDryFrames} " +
                      $"reflRefresh={ReflRefreshes} reflMax={_reflMaxStrength:0.00} reflOk={reflOk} " +
                      $"postFrames={FilmGrade.Frames} postOk={postOk} " +
                      $"framedBeats={FramedBeat.Begun} framingPush={PlayerController.TightestFraming:0.0000} framingOk={framingOk} " +
                      // THE WIND THE RUN ACTUALLY SAW. Both at 1.0000
                      // means the player never ran far enough to spend
                      // any, which is a finding about the sim rather
                      // than about the model.
                      $"staminaLow={PlayerController.LowestStamina:0.000} " +
                      $"staminaHigh={PlayerController.HighestStamina:0.000} " +
                      // THE 180-DEGREE RULE, MEASURED AND NOT YET ENFORCED.
                      // Both from the same beat, so they can honestly be
                      // divided — `lineWatched` counts only beats that HAD a
                      // line to keep, and `lineCrossed` counts the ones where
                      // the follow rig walked over it. If this comes back at
                      // zero over a run of framed beats, enforcement would be
                      // dead code that looks like a feature.
                      $"lineWatched={FramedBeat.LineWatched} lineCrossed={FramedBeat.LineCrossed} " +
                      // AND HOW MANY OF THOSE WERE THE RIG RATHER THAN
                      // THE PLAYER. `lineCrossed` alone cannot say, and
                      // the two want opposite responses — one is a
                      // composed shot reversing itself, the other is the
                      // camera correctly getting out of the way.
                      $"lineCrossedLive={FramedBeat.LineCrossedLive} " +
                      // AND HOW MANY OF THOSE THE BEAT ACTED ON. If this
                      // ever drifts below `lineCrossedLive`, a crossing
                      // was detected and not acted on — a guard that
                      // reports and does not guard.
                      $"lineYielded={FramedBeat.LineYielded} " +
                      $"beatTried={_beatBotTried ?? "none"} beatClosest={_beatClosestApproach:0.0}m " +
                      $"beatChaseSecs={_beatChaseSeconds:0} beatMarker={_beatMarkerSeen} " +
                      $"nightFull={_nightFull:0.0000} nightNoShafts={_nightNoShafts:0.0000} " +
                      $"nightNoBloom={_nightNoBloom:0.0000} nightUngraded={_nightRaw:0.0000} " +
                      $"bloomD={_bloomDelta:0.0000} bloomHit={100 * _bloomFraction:0.00} " +
                      $"bloomRise={_bloomRise:0.0000} bloomLit={100 * _bloomHadHighlights:0.0} " +
                      $"grainD={_grainDelta:0.00000} vig={_vigOn:0.000}/{_vigOff:0.000} " +
                      // THE TEMPERATURE NUDGE, PROVEN TO BE MOVING. Both
                      // at exactly 1.000 means `LitAmount` never changes
                      // or the call never runs, and those look identical
                      // from here — which is how this model spent weeks
                      // written, tested and connected to nothing.
                      $"tempR={FilmGrade.LastTempR:0.0000} tempB={FilmGrade.LastTempB:0.0000} " +
                      $"tempLit={FilmGrade.LitAmount:0.000} " +
                      $"aoApplied={FilmGrade.Applied} aoDelta={aoDelta:0.0000} aoOk={aoOk} " +
                      $"aoTypical={100 * AoTypicalFraction:0.00} " +
                      $"aoRounds2=[{string.Join(" ", _aoFractions.ConvertAll(x => (100 * x).ToString("0.0")))}] " +
                      $"aoHit={100 * _aoFraction:0.00} aoDrop={_aoDrop:0.0000} " +
                      $"reflHit={100 * _reflFraction:0.00} reflRise={_reflRise:0.0000} " +
                      $"reflSeen={reflSeen} reflWetAtAb={SceneLighting.Wetness:0.00} " +
                      $"specHit={100 * _specFraction:0.00} specRise={_specRise:0.0000} " +
                      $"presetHit={100 * _presetFraction:0.00} presetOk={presetOk} " +
                      $"aoSpread={_aoSpread:0.00000} grainSpread={_grainSpread:0.00000} " +
                      $"aoRange={_aoDeltaMin:0.00000}..{_aoDeltaMax:0.00000} " +
                      $"grainRange={_grainDeltaMin:0.00000}..{_grainDeltaMax:0.00000} " +
                      $"confabCand={GossipDirector.ConfabCandidates} confabKerbMean={(GossipDirector.ConfabKerbSamples > 0 ? GossipDirector.ConfabKerbSum / GossipDirector.ConfabKerbSamples : -1):0.00} confabKerbWorst={GossipDirector.ConfabKerbWorst:0.00} confabKerbN={GossipDirector.ConfabKerbSamples} confabOffRoad={GossipDirector.ConfabOffRoad} confabInJunction={GossipDirector.ConfabInJunction} confabTooFar={GossipDirector.ConfabTooFar} confabWidest={GossipDirector.ConfabWidestSeen:0.0} confabs={(_game.Gossip != null ? _game.Gossip.Confabs : -1)} confabOk={confabOk} " +
                      $"hushWalkBys={hushBy} hushes={hushed} " +
                      $"duck={_mixDuckMin:0.00}..{_mixDuckMax:0.00} mixOk={mixOk} " +
                      $"stemVolMax={_stemVolumeMax:0.000} stemsUnbound={_stemsUnbound} " +
                      // THE VOICE BUDGET, PROVEN TO BE REFUSING THINGS.
                      // `dropped=0` over a whole run means either the
                      // street never gets busy enough to need a budget or
                      // the gate is not in the path — and those look
                      // identical from here, which is the state this
                      // system was in for as long as it has existed.
                      // AND WHETHER A SOUND COULD HAVE BEEN PLAYED AT ALL.
                      //
                      // `soundsOffered=0` came back and I read it as the
                      // budget never being reached, which is true and is not
                      // a fault: `PlayerController.Footsteps` has
                      // `audible = SimMode.Days == 0`, so the sim skips
                      // PLAYING a step while still emitting it as something
                      // the city can hear. Deliberate, and its comment says so.
                      //
                      // So the denominator I added an hour ago to stop a zero
                      // being ambiguous was itself ambiguous, for the reason
                      // rule 5b's corollary names: the run cannot produce the
                      // condition the number asks about. This says so on the
                      // line, so nobody chases it — including me, twice.
                      $"simAudible={SimMode.Days == 0} " +
                      $"soundsOffered={Audio.SoundsOffered} " +
                      $"soundsNoClip={Audio.SoundsNoClip} " +
                      $"soundsAdmitted={Audio.SoundsAdmitted} " +
                      $"soundsDropped={Audio.SoundsDropped} " +
                      $"soundsStolen={Audio.SoundsStolen} " +
                      $"soundsPeak={Audio.SoundsPeak} soundsPeakBus={Audio.SoundsPeakBus} " +
                      $"stemRatio={_stemRatioMin:0.000}..{_stemRatioMax:0.000} " +
                      $"scoreAudible={scoreAudible} " +
                      $"busMusic={_busMusicMin:0.000}..{_busMusicMax:0.000} " +
                      $"rigs={_bodyRigs} rigSolved={_bodyMaxSolved} " +
                      // FOOT IK, AND WHETHER IT RAN BEFORE WHETHER IT WORKED.
                      // `ikFrames=0` with `ikUndriven` large means no body ever
                      // bound a controller; `ikFrames=0` with `ikUndriven` zero
                      // means the IK pass is off and `OnAnimatorIK` is never
                      // delivered. Those look identical in a still and have
                      // different fixes, which is why both are printed.
                      $"ikFrames={FootIk.Frames} ikUndriven={FootIk.FramesUndriven} " +
                      $"ikGoals={FootIk.Goals} ikClamped={FootIk.Clamped} " +
                      $"ikCorrectionWorst={FootIk.CorrectionWorst:0.000} " +
                      $"ikCorrectionMedian={FootIk.CorrectionMedian:0.000} " +
                      $"ikCorrectionSamples={FootIk.CorrectionSamples} " +
                      $"ikGroundMissed={FootIk.GroundMissed} " +
                      $"ikWorstDrop={FootIk.WorstDrop:0.000} " +
                      $"ikWorstHit=[{FootIk.WorstHit}] " +
                      $"ikPlantedGoals={FootIk.PlantedGoals} " +
                      $"ikPlantedMedian={FootIk.PlantedMedian:0.000} " +
                      // THE PAIR THAT CAN ACTUALLY ACCUSE THE BLEND. The two
                      // correction medians above cannot: `correction` is
                      // derived from `blend`, so a swinging foot contributes an
                      // arithmetic zero and the overall median is the planted
                      // one diluted. These are the raw foot-above-road, which
                      // the blend does not touch, so both outcomes are
                      // reachable. Signed, and with counts, because a drop can
                      // legitimately be negative and -1 is the empty sentinel.
                      $"ikDropMedian={FootIk.DropMedian:0.000} " +
                      $"ikPlantedDropMedian={FootIk.PlantedDropMedian:0.000} " +
                      $"ikDropSamples={FootIk.DropSamples} " +
                      $"ikPlantedDropSamples={FootIk.PlantedDropSamples} " +
                      // HOW WRONG THE OLD CLOCK WAS, reported rather than
                      // asserted. Frames where the procedural gait phase said
                      // "planted" and the feet disagreed; a zero would mean the
                      // two clocks happened to agree and the change bought
                      // nothing. The two drop medians beside it are now the
                      // test of the NEW answer: they should come apart.
                      $"ikPlantDisagreed={FootIk.PlantDisagreed} " +
                      // AND THE LEG THE CORRECTION IS MEASURED AGAINST,
                      // because eighteen centimetres means nothing until
                      // you know whether the leg is 0.88m or 0.38m. It was
                      // the mannequin default on every bought body until
                      // this run.
                      $"ikLegLength={FootIk.LegLengthSeen:0.000} " +
                      $"knee={_bodyMinKnee:0.0}..{_bodyMaxKnee:0.0} cull={_bodyCulled}/{_bodyCullable} " +
                      $"height={_bodyShortest:0.00}..{_bodyTallest:0.00} bodiesOk={bodiesOk} " +
                      $"roomQuiet={_roomQuietSamples} " +
                      $"pulseMedian={MedianOf(_pulseSamples):0.000} " +
                      $"uneaseMedian={MedianOf(_uneaseSamples):0.000} " +
                      $"heatMedian={MedianOf(_heatSamples):0.000} " +
                      $"heatSamples={_heatSamples.Count} " +
                      $"musicFloor={MusicModel.Floor:0.000} " +
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
