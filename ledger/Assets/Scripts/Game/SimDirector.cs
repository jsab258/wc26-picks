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
            _game.WearingCoat = now.Day >= 3 && (now.Hour >= 21 || now.Hour < 3);

            // Act I PP4 in CI: the trust path needs live conversation, so on day 6
            // the bot learns the hiding place the other way a player can — from
            // Rocco — and the authored moment must fire off the real transition.
            if (!_forcedLedgerLearn && now.Day >= 6)
            {
                _forcedLedgerLearn = true;
                var s = _game.HooksBook.ById("lena_ledger");
                if (s != null && !s.KnownToPlayer) s.Learn("Rocco", now);
            }

            // Open-mode Fall in CI: if week two arrived without the fuse ever
            // blowing organically, stage one on day 9 so the whole Fall path
            // (seizure, time skip, the street knowing) runs in-engine every build.
            if (!_forcedFall && now.Day >= 9 && _game.Campaign.OpenMode
                && _game.Campaign.Falls == 0 && !_game.Campaign.FallPending)
            {
                _forcedFall = true;
                _game.Campaign.ForcePendingFall();
            }

            // Drive the player around the block to exercise movement and camera —
            // except when the outfit's drop is open: then head straight for it, so the
            // night-job completion path (pay, witnesses, patience) runs in-engine.
            var job = _game.ActiveJobPos;
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

            var report = new Dictionary<string, object>
            {
                { "simDays", SimMode.Days },
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
                { "llmCalls", _game.Cost.TotalCalls },
                { "llmCostUsd", _game.Cost.EstimateUsd() },
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
                        && openModeOk && fallOk;
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
                      $"beats=[{string.Join(",", beatStates)}] " +
                      $"verdict={camp.Verdict} pass={pass}");
            Application.Quit(pass ? 0 : 1);
        }
    }
}
