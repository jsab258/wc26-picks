using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// Sound (production track P3). The game was completely silent. This
    /// follows the AssetLibrary pattern exactly: a drop-in pack at
    /// StreamingAssets/Audio/ wins if present, otherwise every sound is
    /// SYNTHESISED at runtime — so the build has audio today, with no
    /// licensing, no downloads, and no code change when recorded assets
    /// arrive later.
    ///
    /// The palette is deliberately spare and diegetic: a room tone that
    /// changes between day and night, footsteps that follow your own pace,
    /// a door, a coin, a page turning for the books, a low pulse when the
    /// street turns against you. No score yet — an authored score is a real
    /// composer's job and is on the roadmap, not faked here.
    public static class Audio
    {
        public const int SampleRate = 44100;

        static AudioSource _ambience, _ui, _foot, _traffic;
        static readonly Dictionary<string, AudioClip> Cache = new Dictionary<string, AudioClip>();
        static GameObject _root;
        static bool _night;

        public static bool Ready => _root != null;

        public static void Initialize()
        {
            if (_root != null) return;
            _root = new GameObject("Audio");
            Object.DontDestroyOnLoad(_root);
            _ambience = Make("Ambience", loop: true);
            _ui = Make("UI", loop: false);
            _foot = Make("Foot", loop: false);
            _traffic = Make("Traffic", loop: true);
            ApplyVolumes();
            SetNight(false);
        }

        static AudioSource Make(string name, bool loop)
        {
            var go = new GameObject(name);
            go.transform.SetParent(_root.transform, false);
            var src = go.AddComponent<AudioSource>();
            src.loop = loop;
            src.playOnAwake = false;
            src.spatialBlend = 0f; // the street is stereo, not positional, for now
            return src;
        }

        public static void ApplyVolumes()
        {
            if (_root == null) return;
            var s = GameSettings.Current;
            if (_ambience != null) _ambience.volume = 0.35f * s.MasterVolume * s.MusicVolume;
            if (_ui != null) _ui.volume = 0.6f * s.MasterVolume * s.SfxVolume;
            if (_foot != null) _foot.volume = 0.35f * s.MasterVolume * s.SfxVolume;
            // The traffic bed's own volume is driven per-frame by proximity; the
            // settings only scale the ceiling it is allowed to reach.
            _trafficCeiling = 0.30f * s.MasterVolume * s.SfxVolume;
        }

        static float _trafficCeiling = 0.30f;

        /// The nearest engine, as heard from where the player is standing.
        /// `loudness` is 0..1 by proximity and speed; 0 stops the bed entirely.
        ///
        /// One source for the whole district rather than one per vehicle. A dozen
        /// looping AudioSources would be a dozen voices mixing to roughly this,
        /// and the thing that actually sells a street is that SOMETHING is
        /// running nearby — not stereo placement of each individual car.
        public static void Traffic(float loudness, float pitch)
        {
            if (_root == null || _traffic == null) return;
            loudness = Mathf.Clamp01(loudness);
            if (loudness <= 0.01f)
            {
                if (_traffic.isPlaying) _traffic.Stop();
                return;
            }
            if (_traffic.clip == null) _traffic.clip = Clip("engine", Engine);
            if (!_traffic.isPlaying) _traffic.Play();
            _traffic.volume = loudness * _trafficCeiling;
            _traffic.pitch = Mathf.Clamp(pitch, 0.6f, 1.7f);
        }

        /// Day and night have different rooms. Night is quieter, lower, and
        /// has the harbour in it.
        public static void SetNight(bool night)
        {
            if (_root == null || (night == _night && _ambience.isPlaying)) return;
            _night = night;
            _ambience.clip = Clip(night ? "ambience_night" : "ambience_day", () => Ambience(night));
            _ambience.Play();
        }

        public static void Footstep()
        {
            if (_root == null || _foot == null) return;
            _foot.pitch = Random.Range(0.92f, 1.08f);
            _foot.PlayOneShot(Clip("step", Step));
        }

        public static void Ui(string kind)
        {
            if (_root == null || _ui == null) return;
            switch (kind)
            {
                case "page": _ui.PlayOneShot(Clip("page", Page)); break;
                case "coin": _ui.PlayOneShot(Clip("coin", Coin)); break;
                case "door": _ui.PlayOneShot(Clip("door", Door)); break;
                case "dread": _ui.PlayOneShot(Clip("dread", Dread)); break;
                default: _ui.PlayOneShot(Clip("tick", Tick)); break;
            }
        }

        /// A drop-in pack wins; otherwise synthesise once and cache.
        static AudioClip Clip(string name, System.Func<AudioClip> synth)
        {
            if (Cache.TryGetValue(name, out var cached)) return cached;
            AudioClip clip = null;
            try
            {
                var path = System.IO.Path.Combine(Application.streamingAssetsPath, "Audio", name + ".wav");
                if (System.IO.File.Exists(path)) clip = LoadWav(path, name);
            }
            catch (System.Exception) { /* fall through to synthesis */ }
            if (clip == null) clip = synth();
            Cache[name] = clip;
            return clip;
        }

        // ---- synthesis ----

        /// Layered noise beds: a low hum, a filtered hiss for air, and (at
        /// night) a slow harbour swell. Seeded, so a build always sounds
        /// identical — the sim's screenshots stay comparable.
        static AudioClip Ambience(bool night)
        {
            int len = SampleRate * 8;                    // an 8-second loop
            var data = new float[len];
            var rng = new System.Random(night ? 71 : 17);
            float hum = night ? 54f : 78f;
            float lp = 0f;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)SampleRate;
                float noise = (float)(rng.NextDouble() * 2 - 1);
                lp += (noise - lp) * (night ? 0.02f : 0.05f);   // one-pole low pass
                float tone = Mathf.Sin(2 * Mathf.PI * hum * t) * (night ? 0.05f : 0.035f);
                float swell = night ? Mathf.Sin(2 * Mathf.PI * 0.11f * t) * 0.4f + 0.6f : 1f;
                data[i] = (lp * (night ? 0.5f : 0.35f) + tone) * swell;
            }
            CrossfadeEnds(data, SampleRate / 4);
            return Make("ambience", data);
        }

        /// An engine at idle-to-cruise: a low sawtooth with its second and
        /// third harmonics, roughened with a little filtered noise so it does
        /// not read as a test tone. Pitch-shifted at playback by road speed,
        /// which is why the loop itself is deliberately flat.
        static AudioClip Engine()
        {
            int len = SampleRate * 2;
            var data = new float[len];
            var rng = new System.Random(41);
            float lp = 0f;
            const float f = 46f;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)SampleRate;
                float saw = 2f * (t * f - Mathf.Floor(t * f + 0.5f));
                float h2 = Mathf.Sin(2 * Mathf.PI * f * 2f * t) * 0.35f;
                float h3 = Mathf.Sin(2 * Mathf.PI * f * 3f * t) * 0.18f;
                lp += ((float)(rng.NextDouble() * 2 - 1) - lp) * 0.08f;
                data[i] = (saw * 0.35f + h2 + h3) * 0.28f + lp * 0.10f;
            }
            CrossfadeEnds(data, SampleRate / 8);
            return Make("engine", data);
        }

        static AudioClip Step()
        {
            int len = SampleRate / 12;
            var data = new float[len];
            var rng = new System.Random(5);
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)len;
                float env = Mathf.Exp(-14f * t);
                data[i] = (float)(rng.NextDouble() * 2 - 1) * env * 0.5f;
            }
            return Make("step", data);
        }

        static AudioClip Page()
        {
            int len = SampleRate / 5;
            var data = new float[len];
            var rng = new System.Random(23);
            float lp = 0;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)len;
                float env = Mathf.Sin(Mathf.PI * t) * Mathf.Exp(-2f * t);
                lp += ((float)(rng.NextDouble() * 2 - 1) - lp) * 0.35f;
                data[i] = lp * env * 0.5f;
            }
            return Make("page", data);
        }

        static AudioClip Coin()
        {
            int len = SampleRate / 3;
            var data = new float[len];
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)SampleRate;
                float env = Mathf.Exp(-9f * t);
                data[i] = (Mathf.Sin(2 * Mathf.PI * 2100f * t) * 0.6f
                         + Mathf.Sin(2 * Mathf.PI * 3170f * t) * 0.4f) * env * 0.28f;
            }
            return Make("coin", data);
        }

        static AudioClip Door()
        {
            int len = SampleRate / 2;
            var data = new float[len];
            var rng = new System.Random(41);
            float lp = 0;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)len;
                float env = Mathf.Exp(-5f * t);
                lp += ((float)(rng.NextDouble() * 2 - 1) - lp) * 0.08f;
                float creak = Mathf.Sin(2 * Mathf.PI * (180f + 60f * t) * (i / (float)SampleRate));
                data[i] = (lp * 0.6f + creak * 0.25f) * env * 0.5f;
            }
            return Make("door", data);
        }

        /// The street turning against you: a low descending pulse. Used for
        /// exposure, confrontations, and the Fall.
        static AudioClip Dread()
        {
            int len = (int)(SampleRate * 1.6f);
            var data = new float[len];
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)SampleRate;
                float env = Mathf.Exp(-1.4f * t);
                float f = Mathf.Lerp(96f, 47f, t / 1.6f);
                data[i] = Mathf.Sin(2 * Mathf.PI * f * t) * env * 0.5f;
            }
            return Make("dread", data);
        }

        static AudioClip Tick()
        {
            int len = SampleRate / 30;
            var data = new float[len];
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)len;
                data[i] = Mathf.Sin(2 * Mathf.PI * 1400f * (i / (float)SampleRate)) * Mathf.Exp(-18f * t) * 0.22f;
            }
            return Make("tick", data);
        }

        static void CrossfadeEnds(float[] data, int fade)
        {
            for (int i = 0; i < fade && i < data.Length / 2; i++)
            {
                float k = i / (float)fade;
                int j = data.Length - 1 - i;
                float a = data[i], b = data[j];
                data[i] = Mathf.Lerp(b, a, k);
                data[j] = Mathf.Lerp(a, b, k);
            }
        }

        static AudioClip Make(string name, float[] data)
        {
            var clip = AudioClip.Create(name, data.Length, 1, SampleRate, false);
            clip.SetData(data, 0);
            return clip;
        }

        /// Minimal 16-bit PCM WAV reader for drop-in packs.
        static AudioClip LoadWav(string path, string name)
        {
            var bytes = System.IO.File.ReadAllBytes(path);
            if (bytes.Length < 44) return null;
            int channels = System.BitConverter.ToInt16(bytes, 22);
            int rate = System.BitConverter.ToInt32(bytes, 24);
            int samples = (bytes.Length - 44) / 2;
            var data = new float[samples];
            for (int i = 0; i < samples; i++)
                data[i] = System.BitConverter.ToInt16(bytes, 44 + i * 2) / 32768f;
            var clip = AudioClip.Create(name, samples / Mathf.Max(1, channels), Mathf.Max(1, channels), rate, false);
            clip.SetData(data, 0);
            return clip;
        }
    }
}
