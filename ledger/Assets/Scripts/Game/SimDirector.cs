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
        public static int Days
        {
            get
            {
                var args = Environment.GetCommandLineArgs();
                for (int i = 0; i < args.Length - 1; i++)
                    if (args[i] == "-simdays" && int.TryParse(args[i + 1], out var d))
                        return d;
                return 0;
            }
        }
    }

    public class SimDirector : MonoBehaviour
    {
        const float SimMinutesPerRealSecond = 20f; // 1 game day = 72 real seconds

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
        bool _planStaged, _planRan;
        bool _actThreeStaged;
        bool _actThreeHandedOver;
        Ending _actThreeEnding = Ending.None;
        bool _secretEverReachedDay;
        int _lastSampledHour = -1;
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
            // Ossei's spawn path gets exercised) and careful from day 3 (coated, so
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

            // Act I PP4 in CI: the trust path needs live conversation, so on day 6
            // the bot learns the hiding place the other way a player can — from
            // Rocco — and the authored moment must fire off the real transition.
            if (!_forcedLedgerLearn && now.Day >= 6)
            {
                _forcedLedgerLearn = true;
                var s = _game.HooksBook.ById("lena_ledger");
                if (s != null && !s.KnownToPlayer) s.Learn("Rocco", now);
            }

            // Empire v1 in CI: the moment the city opens, the bot plays one
            // beat of empire — recruit Sam by need (loyalty staged past the
            // floor), put him on the collection round, buy Viktor's marker and
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
                    _game.Empire.Squeeze(shop, m.Get("Viktor"), m, now);
                }
            }

            // The Director's firing path in CI (roadmap M8). No API key on the
            // build machine means the nightly pass never authors anything, so
            // the code that actually RUNS a pressure would never be exercised.
            // Stage two by hand on day 9 — a demand from Rocco, then answered,
            // and a rumor through Sam — so scheduling, firing through the real
            // primitives, and settling all run in-engine every build.
            if (!_directorStaged && _game.Campaign.OpenMode && now.Day >= 9 && now.Hour >= 11)
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
            if (!_planStaged && _game.CanPlan && now.Day >= 9 && now.Hour >= 12)
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
            if (!_actThreeStaged && _game.Campaign.OpenMode && now.Day >= 9 && now.Hour >= 13)
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
            if (!_tookDayShot && now.Hour == 12) { _tookDayShot = true; Shot($"day{now.Day}_noon"); }
            if (!_tookNightShot && now.Hour == 23) { _tookNightShot = true; Shot($"day{now.Day}_night"); }

            if (now.Day >= _endDay) Finish();
        }

        /// Renders through an explicit RenderTexture rather than ScreenCapture:
        /// the build machine has no GPU/display, and ScreenCapture silently
        /// produces nothing there. This path works on a software device and
        /// writes the file synchronously so we know immediately if it failed.
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

        /// Downsample a captured frame to a small ASCII art thumbnail (logged so it
        /// is visible in CI, where the PNG artifact host is unreachable) plus mean
        /// luminance and RGB for the JSON report.
        static (string luma, string rgb, string maxLuma, string brightPct) Fingerprint(Texture2D tex, string name)
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
            for (int i = 0; i < px.Length; i++)
            {
                var c = px[i];
                double l = (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) / 255.0;
                if (l > maxLuma) maxLuma = l;
                if (l > 0.60) brightCount++;
            }
            double brightPct = 100.0 * brightCount / px.Length;
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
            art.Append($"render[{name}] meanLuma={luma:0.000} maxLuma={maxLuma:0.000} bright(>0.6)%={brightPct:0.00}\n");
            Debug.Log(art.ToString());
            return (
                luma.ToString("0.000", inv),
                $"{(int)mr},{(int)mg},{(int)mb}",
                maxLuma.ToString("0.000", inv),
                brightPct.ToString("0.00", inv));
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
            bool discreditWorks = true;
            if (mill != null && secretReachedDay)
            {
                string topic = null; string value = null; double before = 0;
                foreach (var a in mill.Agents)
                    if (a.Circle == "day")
                        foreach (var r in a.Rumors)
                            if (r.Sensitive && r.Confidence > before)
                            { before = r.Confidence; topic = r.TopicKey; value = r.Content.Value; }
                if (topic != null)
                {
                    mill.Discredit(topic, value, _game.Now);
                    double after = 0;
                    foreach (var a in mill.Agents)
                        if (a.Circle == "day")
                            foreach (var r in a.Rumors)
                                if (r.TopicKey == topic && r.Confidence > after) after = r.Confidence;
                    discreditWorks = after < before;
                }
            }

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

            // Ossei must appear iff the street ever ran hot enough (same sampling
            // cadence as the spawn check, so the comparison cannot race).
            bool osseiOk = _game.OsseiSpawned == (_game.ObservedPeakHeat >= OsseiSetup.SpawnHeatThreshold);

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
                _game.SaveNow(quiet: true);
                if (!System.IO.File.Exists(_game.SavePath)) saveLoadOk = false;
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
            // Viktor plus the generated batch must actually be walking.
            bool populationOk = _npcs != null && _npcs.Length >= 20;

            // The day job (§6.6): in the open city the bot must have walked at
            // least one courier round — clean pay through the honest channel.
            bool dayJobOk = !_game.Campaign.OpenMode || SimMode.Days < 9 || _game.Job.ShiftsWorked >= 1;

            // The living economy (roadmap M7). Three things must be true after
            // nine days: the district has actually been paying its suppliers
            // (Mirek comes weekly and takes real money), the street's own state
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

            // Frame cost, measured rather than assumed. Traffic is the first
            // system here that does work every frame for every visible object,
            // so its budget is a gate: if the per-frame cost of driving the whole
            // district ever crosses a few milliseconds, that is a regression
            // worth failing a build over, and it should be found in CI rather
            // than in a stutter on the player's machine.
            var trafficCost = Perf.Get("traffic");
            bool perfOk = trafficCost == null || trafficCost.MeanMs < 4.0;

            // The vehicle description (spec §4). Only meaningful if the bot was
            // seen at all; when it was, somebody must be able to describe the car.
            bool vehicleFactSeen = false;
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
                var samHurts = _game.Harm.Hurts("Sam", _game.Now.Day);
                bool stillHurt = samHurts.Count > 0;
                bool turned = false;
                foreach (var i in samHurts) if (i.WentBad) turned = true;
                bool roccoFine = true;
                foreach (var i in _game.Harm.All)
                    if (i.PersonId == "Rocco" && i.WentBad) roccoFine = false;
                var feud = _game.Harm.FeudBetween("Sam", "Rocco");

                harmOk = _harmStaged
                    && stillHurt                                        // days later, still carrying it
                    && turned                                           // and it got worse for being ignored
                    && roccoFine                                        // while the treated one did not
                    && _game.Harm.ScarsOf("Sam") >= 1                   // the count does not heal
                    && _harmCapabilityAtInjury < 1.0                    // it cost him something
                    && feud != null                                     // and the feud is still standing
                    && !_game.Harm.WillWorkTogether("Sam", "Rocco");    // which is a scheduling problem
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
            bool uiOk = _uiSmokeRun && panelsBad == 0 && panelsOk >= 5;

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

            bool verdictSane = camp.Verdict != Verdict.LostCastOut &&
                // While the campaign is live, most nights must actually post a job.
                (camp.Verdict != Verdict.Ongoing || camp.JobsDone + camp.JobsMissed >= SimMode.Days - 2);

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
            bool openModeOk = !_game.Campaign.OpenMode || _game.Campaign.DaysClosed >= 8;
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
                { "actThreeClosesDay", _game.ActThree.AuditClosesDay },
                { "actThreeStaged", _actThreeStaged },
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
                { "osseiSpawned", _game.OsseiSpawned },
                { "peakHeat", _game.ObservedPeakHeat },
                { "confrontations", _game.TotalConfrontations },
                { "checksRun", _game.Gossip != null ? _game.Gossip.ChecksRun : 0 },
                { "overheard", _game.Gossip != null ? _game.Gossip.Overheard : 0 },
                { "osseiInterviews", _game.OsseiInterviews.Count },
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
                { "tightestGap", System.Math.Round(tightest, 2) },
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

            bool pass = _errors.Count == 0 && npcsMoved && WorldBuilder.LampToggleCount >= 2
                        && _screenshots.Count > 0 && secretReachedDay && discreditWorks
                        && jobRan && takingsBanked && verdictSane && knowledgeWorks && launderWorks
                        && disguiseWorks && beatsResolved && osseiOk && saveLoadOk && actOneOk
                        && openModeOk && fallOk && empireOk && populationOk && dayJobOk && economyOk
                        && directorOk && crowdOk && accessOk && opsOk && trafficOk && perfOk && witnessCarOk && harmOk && phonesOk && uiOk
                        && actThreeOk;
            Debug.Log($"SimDirector: done. errors={_errors.Count} npcsMoved={npcsMoved} " +
                      $"lampToggles={WorldBuilder.LampToggleCount} screenshots={_screenshots.Count} " +
                      $"gossipHeat={gossipHeat:0.00} secretReachedDay={secretReachedDay} " +
                      $"discreditWorks={discreditWorks} jobsDone={camp.JobsDone} jobsMissed={camp.JobsMissed} " +
                      $"patience={camp.OutfitPatience:0.00} takings={_game.TotalTakings} " +
                      $"witnesses={_game.NightWitnesses} knownLeads={_game.Knowledge.Count} " +
                      $"clean={_game.Wallet.Clean} dirty={_game.Wallet.Dirty} washed={_game.Wallet.TotalWashed} " +
                      $"coatConf={_game.MaxCoatedWitnessConf:0.00} ossei={_game.OsseiSpawned} peakHeat={_game.ObservedPeakHeat:0.00} " +
                      $"checks={(_game.Gossip != null ? _game.Gossip.ChecksRun : 0)} confronts={_game.TotalConfrontations} " +
                      $"saveLoad={saveLoadOk} actOne={actOneOk} pp4={_game.ActOne.Pp4Fired} posture={_game.ActOne.Posture} " +
                      $"openMode={_game.Campaign.OpenMode} falls={_game.Campaign.Falls} cutOff={_game.Campaign.OutfitCutOff} " +
                      $"daysClosed={_game.Campaign.DaysClosed} openModeOk={openModeOk} fallOk={fallOk} verdictSane={verdictSane} " +
                      $"empireOk={empireOk} racketIncome={_game.Empire.TotalRacketIncome} rivalStage={_game.Empire.Rival.Stage} " +
                      $"actThree={_actThreeStaged} ending={_actThreeEnding} handed={_actThreeHandedOver} actThreeOk={actThreeOk} " +
                      $"npcs={(_npcs != null ? _npcs.Length : 0)} populationOk={populationOk} " +
                      $"shifts={_game.Job.ShiftsWorked} dayJobOk={dayJobOk} " +
                      $"street={_game.Economy.Prosperity:0.00} prices={_game.Economy.PriceLevel:0.00} " +
                      $"takingsFactor={_game.Economy.TakingsFactor:0.00} economyOk={economyOk} " +
                      $"directorPending={_game.Directorate.Pending.Count} directorFired={_directorFired} directorOk={directorOk} " +
                      $"pop={(_game.Populace != null ? _game.Populace.Residents.Count : 0)} " +
                      $"gates={_game.Gates.Count} accessOk={accessOk} " +
                      $"targets={_game.Targets.Count} planRan={_planRan} opsOk={opsOk} " +
                      $"vehicles={(traffic != null ? traffic.Vehicles.Count : 0)} kinds={kindsSeen} " +
                      $"trafficMetres={(traffic != null ? traffic.TotalDistance : 0):0} gap={tightest:0.00} " +
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
                      $"near={(_game.Populace != null ? _game.Populace.CountIn(Lod.Near) : 0)} " +
                      $"mid={(_game.Populace != null ? _game.Populace.CountIn(Lod.Mid) : 0)} crowdOk={crowdOk} " +
                      $"beats=[{string.Join(",", beatStates)}] " +
                      $"verdict={camp.Verdict} pass={pass}");
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
    }
}
