using System;
using System.Collections.Generic;
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

            // Drive the player around the block to exercise movement and camera.
            var target = Waypoints[_waypointIndex];
            _player.AutoMoveTarget = target;
            if (Vector3.Distance(new Vector3(_player.transform.position.x, 0, _player.transform.position.z), target) < 1.2f)
                _waypointIndex = (_waypointIndex + 1) % Waypoints.Length;

            // Hourly NPC sample.
            if (now.Hour != _lastSampledHour)
            {
                _lastSampledHour = now.Hour;
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
                _screenshots.Add(new Dictionary<string, object>
                {
                    { "path", path }, { "bytes", info.Exists ? info.Length : 0 },
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

        void Finish()
        {
            Application.logMessageReceived -= OnLog;

            bool npcsMoved = false;
            foreach (var npc in _npcs)
                if (Vector3.Distance(npc.transform.position, _startPositions[npc.DisplayName]) > 2f)
                    npcsMoved = true;

            var report = new Dictionary<string, object>
            {
                { "simDays", SimMode.Days },
                { "finalTime", _game.Now.ToString() },
                { "errorCount", _errors.Count },
                { "errors", new List<object>(_errors.ToArray()) },
                { "npcsMoved", npcsMoved },
                { "lampToggles", WorldBuilder.LampToggleCount },
                { "hourlySamples", _samples.Count },
                { "samples", _samples },
                { "screenshotCount", _screenshots.Count },
                { "screenshots", _screenshots },
            };
            System.IO.File.WriteAllText("sim-out/sim-report.json", MiniJson.Serialize(report));

            bool pass = _errors.Count == 0 && npcsMoved && WorldBuilder.LampToggleCount >= 2 && _screenshots.Count > 0;
            Debug.Log($"SimDirector: done. errors={_errors.Count} npcsMoved={npcsMoved} " +
                      $"lampToggles={WorldBuilder.LampToggleCount} screenshots={_screenshots.Count} pass={pass}");
            Application.Quit(pass ? 0 : 1);
        }
    }
}
