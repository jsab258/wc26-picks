using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Owns the game clock, day/night cycle, and world orchestration for the
    /// M0 tech spike: one graybox block, a player, three scheduled NPCs, and
    /// Lena (the full conversational character).
    public class GameController : MonoBehaviour
    {
        public float MinutesPerRealSecond = 2f; // 1 game day = 12 real minutes (sim mode overrides)

        public GameTime Now { get; private set; } = new GameTime(1, 9, 0);
        public CostTracker Cost { get; } = new CostTracker();

        float _minuteAccumulator;
        Light _sun;
        readonly List<NpcWalker> _npcs = new List<NpcWalker>();
        ConversationHost _lena;
        int _lastReflectedDay;

        void Start()
        {
            WorldBuilder.BuildBlock();
            _sun = WorldBuilder.BuildSun();

            var player = PlayerController.Spawn(new Vector3(0, 1.2f, -8));

            _npcs.Add(NpcWalker.Spawn("Rocco", new Color(0.75f, 0.3f, 0.25f), new[]
            {
                (new GameTime(0, 7, 0), new Vector3(18, 0, 14)),   // docks
                (new GameTime(0, 12, 0), WorldBuilder.BarDoor + new Vector3(2, 0, 1)),
                (new GameTime(0, 19, 0), new Vector3(-16, 0, -12)), // home
            }));
            _npcs.Add(NpcWalker.Spawn("Ada", new Color(0.3f, 0.5f, 0.75f), new[]
            {
                (new GameTime(0, 8, 0), new Vector3(-14, 0, 12)),  // apartment steps
                (new GameTime(0, 10, 0), new Vector3(10, 0, -14)), // market corner
                (new GameTime(0, 17, 0), new Vector3(-14, 0, 12)),
            }));
            _npcs.Add(NpcWalker.Spawn("Sam", new Color(0.4f, 0.65f, 0.35f), new[]
            {
                (new GameTime(0, 9, 0), new Vector3(14, 0, -12)),
                (new GameTime(0, 13, 0), new Vector3(14, 0, 12)),
                (new GameTime(0, 16, 0), new Vector3(-12, 0, 14)),
                (new GameTime(0, 21, 0), new Vector3(-12, 0, -14)),
            }));

            var lenaWalker = NpcWalker.Spawn("Lena", new Color(0.55f, 0.4f, 0.6f), new[]
            {
                (new GameTime(0, 8, 0), WorldBuilder.BarCounter),
                (new GameTime(0, 23, 30), WorldBuilder.BarDoor + new Vector3(-1, 0, -1)),
            });
            _npcs.Add(lenaWalker);
            _lena = lenaWalker.gameObject.AddComponent<ConversationHost>();
            _lena.Initialize(this, LenaSetup.CardMarkdown, LenaSetup.SeedKnowledge, LenaSetup.SeedMemories);

            DialogueUI.Create(this, player, _lena);

            if (SimMode.Days > 0)
                gameObject.AddComponent<SimDirector>().Begin(this, player);
        }

        void Update()
        {
            _minuteAccumulator += Time.deltaTime * MinutesPerRealSecond;
            while (_minuteAccumulator >= 1f)
            {
                _minuteAccumulator -= 1f;
                Now = Now.AddMinutes(1);
            }

            UpdateSun();
            foreach (var npc in _npcs) npc.Tick(Now);

            // Nightly reflection: distill the day's memories into beliefs once, from 23:00.
            // Use >= 23, not == 23: under the accelerated sim clock a single frame can
            // step across the exact hour, and the per-day guard already limits it to once.
            if (Now.Hour >= 23 && Now.Day > _lastReflectedDay && _lena != null && _lena.Ready)
            {
                _lastReflectedDay = Now.Day;
                _ = _lena.RunReflectionAsync(Now);
            }
        }

        void UpdateSun()
        {
            if (_sun == null) return;
            // 06:00 sunrise, 18:00 sunset mapped across a full rotation.
            float dayFraction = (Now.Hour * 60 + Now.Minute) / 1440f;
            float sunAngle = dayFraction * 360f - 90f;
            _sun.transform.rotation = Quaternion.Euler(sunAngle, 35f, 0);

            float daylight = Mathf.Clamp01(Mathf.Sin(dayFraction * Mathf.PI * 2f - Mathf.PI / 2f) + 0.15f);
            _sun.intensity = Mathf.Lerp(0.02f, 1.15f, daylight);
            _sun.color = Color.Lerp(new Color(1f, 0.55f, 0.35f), Color.white, daylight);
            RenderSettings.ambientLight = Color.Lerp(new Color(0.06f, 0.07f, 0.12f), new Color(0.55f, 0.57f, 0.62f), daylight);
            WorldBuilder.SetLampsEnabled(daylight < 0.25f);
        }
    }
}
