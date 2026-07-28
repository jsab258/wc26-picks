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

        static AudioSource _ambience, _ui, _foot, _traffic, _music;
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
            _music = Make("Music", loop: true);
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
            if (_ambience != null)
                _ambience.volume = (0.28f + 0.34f * _chatter) * s.MasterVolume * s.MusicVolume;
            if (_music != null) _music.volume = 0.22f * s.MasterVolume * s.MusicVolume * (_ducked ? 0.35f : 1f);
            if (_ui != null) _ui.volume = 0.6f * s.MasterVolume * s.SfxVolume;
            if (_foot != null) _foot.volume = 0.35f * s.MasterVolume * s.SfxVolume;
            // The traffic bed's own volume is driven per-frame by proximity; the
            // settings only scale the ceiling it is allowed to reach.
            _trafficCeiling = 0.30f * s.MasterVolume * s.SfxVolume;
        }

        static float _trafficCeiling = 0.30f;

        /// RAIN, which the art pass shipped without. A downpour you can see
        /// and cannot hear is worse than no rain at all, because the eye and
        /// the ear disagree and the ear wins — the scene reads as a video
        /// playing behind glass.
        ///
        /// Two layers, because rain is two sounds. A broad hiss that is the
        /// sum of a million drops too far away to resolve, and a sparser
        /// patter of the ones landing near you. Crossfading between them with
        /// intensity is what makes a drizzle sound like a drizzle rather than
        /// like a quiet downpour.
        static AudioSource _rain, _rainNear;

        public static void Rain(float intensity, float indoors = 0f)
        {
            if (_root == null) return;
            intensity = Mathf.Clamp01(intensity);
            if (_rain == null)
            {
                _rain = Make("Rain", loop: true);
                _rainNear = Make("RainNear", loop: true);
            }
            if (intensity <= 0.01f)
            {
                if (_rain.isPlaying) _rain.Stop();
                if (_rainNear.isPlaying) _rainNear.Stop();
                return;
            }
            if (_rain.clip == null) _rain.clip = Clip("rain_bed", () => RainBed(false));
            if (_rainNear.clip == null) _rainNear.clip = Clip("rain_near", () => RainBed(true));
            if (!_rain.isPlaying) _rain.Play();
            if (!_rainNear.isPlaying) _rainNear.Play();

            var s = GameSettings.Current;
            float gain = (1f - 0.72f * Mathf.Clamp01(indoors)) * s.MasterVolume * s.SfxVolume;
            // The bed comes up fast and saturates; the near patter only
            // arrives once it is really raining. A shower and a storm differ
            // mostly in how much of the near layer you get.
            _rain.volume = Mathf.Sqrt(intensity) * 0.34f * gain;
            _rainNear.volume = Mathf.Clamp01((intensity - 0.25f) / 0.75f) * 0.28f * gain;
            _rain.pitch = 0.94f + 0.12f * intensity;
        }

        /// `near` gives the sparse, bright, individual drops; otherwise the
        /// broad hiss. Both are noise, but shaped completely differently —
        /// which is the whole point, because one noise source at two volumes
        /// is what makes fake rain sound like static.
        static AudioClip RainBed(bool near)
        {
            int len = SampleRate * 4;                    // loops seamlessly below
            var data = new float[len];
            var rng = new System.Random(near ? 7717 : 313);
            float lp = 0, hp = 0;
            for (int i = 0; i < len; i++)
            {
                float n = (float)(rng.NextDouble() * 2 - 1);
                if (near)
                {
                    // Sparse impulses: most samples are silent, a few are
                    // sharp. That sparseness is what the ear hears as
                    // individual drops rather than as hiss.
                    float drop = rng.NextDouble() < 0.0016 ? n * 1.6f : 0f;
                    lp += (drop - lp) * 0.55f;
                    hp = lp - hp * 0.25f;
                    data[i] = hp * 0.9f;
                }
                else
                {
                    // Broadband, slightly darkened. Real rain is not white
                    // noise; the high end is eaten by air and by distance.
                    lp += (n - lp) * 0.38f;
                    data[i] = lp * 0.5f;
                }
            }
            CrossfadeEnds(data, SampleRate / 4);
            return Make(near ? "rain_near" : "rain_bed", data);
        }

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
            if (_music != null)
            {
                _music.clip = Clip(night ? "music_night" : "music_day", () => Score(night));
                _music.Play();
            }
        }

        /// The score steps back while people talk — dialogue is the game's
        /// instrument and the music knows it (P3).
        static bool _ducked;
        public static void DuckMusic(bool talking)
        {
            if (_ducked == talking) return;
            _ducked = talking;
            ApplyVolumes();
        }

        /// P3's missing half: a score, synthesised once and cached — and like
        /// every clip here, a drop-in wav with the same name simply wins.
        ///
        /// Composition, not wallpaper: a slow aeolian progression
        /// (i – VI – III – VII in A minor) under a sparse pentatonic line, all
        /// sines with slow attacks, quiet enough to sit UNDER the ambience
        /// rather than on top of it. Night is the same music with the lights
        /// off: down an octave, half the melody, longer chords — the day's
        /// tune remembered rather than played. Deterministic seed, so the
        /// city always hums the same few bars; familiarity is the point.
        static AudioClip Score(bool night)
        {
            // LATE 1980s / EARLY 90s, and deliberately NOT mournful (Jafar:
            // "can't be too depressing, has to make the player come back").
            // A synth score with a PULSE: detuned saw pad, a sixteenth-note
            // arpeggio that keeps the blood moving, and a sub bass on the
            // root. Night drops the arpeggio to half time and takes the top
            // off — the same tune after hours, not a sadder one.
            int barSeconds = night ? 8 : 6;
            int[][] chords =
            {
                new[] { 0, 3, 7, 10 },    // Am7
                new[] { -4, 0, 3, 7 },    // Fmaj7
                new[] { -2, 2, 5, 9 },    // Gmaj-ish
                new[] { 3, 7, 10, 14 },   // Cmaj add9
            };
            int len = SampleRate * barSeconds * chords.Length;
            var data = new float[len];
            var rng = new System.Random(night ? 5150 : 808);
            float root = night ? 55f : 110f;                   // A1 / A2
            float[] arpSteps = { 0, 3, 7, 10, 12, 10, 7, 3 };

            for (int c = 0; c < chords.Length; c++)
            {
                int start = c * barSeconds * SampleRate;
                int clen = barSeconds * SampleRate;

                // Sub bass: the root, square-ish, the thing you feel.
                float bassHz = root * Mathf.Pow(2f, chords[c][0] / 12f);
                for (int i = 0; i < clen; i++)
                {
                    float t = i / (float)SampleRate;
                    float env = Mathf.Min(1f, t / 0.05f) * Mathf.Min(1f, (barSeconds - t) / 0.6f);
                    float saw = Mathf.Repeat(bassHz * t, 1f) * 2f - 1f;
                    data[start + i] += saw * 0.045f * env;
                }

                // Detuned saw pad: two oscillators a few cents apart is the
                // whole sound of the decade.
                foreach (var semi in chords[c])
                {
                    float hz = root * 4f * Mathf.Pow(2f, semi / 12f);
                    float amp = 0.028f / chords[c].Length;
                    for (int i = 0; i < clen; i++)
                    {
                        float t = i / (float)SampleRate;
                        float env = Mathf.Min(1f, t / 1.2f) * Mathf.Min(1f, (barSeconds - t) / 1.2f);
                        float a1 = Mathf.Repeat(hz * t, 1f) * 2f - 1f;
                        float a2 = Mathf.Repeat(hz * 1.006f * t, 1f) * 2f - 1f;
                        data[start + i] += (a1 + a2) * 0.5f * amp * env;
                    }
                }

                // The arpeggio. This is the part that makes it move.
                int steps = night ? 8 : 16;
                float stepLen = barSeconds / (float)steps;
                for (int stp = 0; stp < steps; stp++)
                {
                    float semi = chords[c][0] + arpSteps[stp % arpSteps.Length];
                    float hz = root * 8f * Mathf.Pow(2f, semi / 12f);
                    int at = start + (int)(stp * stepLen * SampleRate);
                    int nlen = (int)(stepLen * SampleRate * 0.9f);
                    float vel = (stp % 4 == 0 ? 1f : 0.62f) * (night ? 0.5f : 1f);
                    for (int i = 0; i < nlen && at + i < len; i++)
                    {
                        float t = i / (float)SampleRate;
                        float env = Mathf.Min(1f, t / 0.008f) * Mathf.Exp(-t * 9f);
                        float sq = Mathf.Sin(2 * Mathf.PI * hz * t) > 0 ? 1f : -1f;
                        data[at + i] += sq * 0.016f * vel * env;
                    }
                }
            }

            // A touch of noise, so it sounds like a machine in a room.
            for (int i = 0; i < len; i++) data[i] += (float)(rng.NextDouble() * 2 - 1) * 0.0012f;

            CrossfadeEnds(data, SampleRate / 2);
            return Make(night ? "music_night" : "music_day", data);
        }

        /// M15.1 — THE STREET'S VOLUME IS ITS TEMPERATURE. A hot street is a
        /// talkative one, and the player should learn to read the noise rather
        /// than a word in a status line. Rides on top of the ambience bed so
        /// it costs nothing but a gain change.
        static float _chatter;

        /// How loud the street is, 0..1. Read by the acoustics model, so a
        /// busy street genuinely makes eavesdropping harder rather than only
        /// sounding as though it does.
        public static float ChatterLevel => _chatter;

        public static void SetChatter(float level)
        {
            _chatter = Mathf.Clamp01(level);
            ApplyVolumes();
        }

        /// GAME FEEL §4: footsteps by surface × gait × several variants, so it
        /// never sounds looped. One clip with a random pitch — which is what
        /// this was — is the sound every player has learned to stop hearing.
        ///
        /// `weight` comes from the gait: a limping step lands harder on the
        /// good leg, which is what actually sells an injury through
        /// headphones, before any model exists to show it.
        static int _stepVariant;
        public static void Footstep(float weight = 1f, float wet = 0f)
        {
            if (_root == null || _foot == null) return;
            // Cycle rather than randomise, so the same variant cannot land
            // twice running — the thing that makes randomness sound cheap.
            _stepVariant = (_stepVariant + 1 + Random.Range(0, 3)) % StepVariants;
            int v = _stepVariant;
            bool splash = wet > 0.35f && Random.value < wet;
            string name = (splash ? "step_wet" : "step") + v;
            _foot.pitch = Random.Range(0.94f, 1.06f) / Mathf.Max(0.6f, weight);
            _foot.PlayOneShot(Clip(name, () => Step(v, splash)),
                              Mathf.Clamp(weight, 0.4f, 1.4f));
        }

        /// FOLEY (game-feel-spec.md §4): clothing rustle, keys, the coat
        /// going on and coming off.
        ///
        /// Foley is the sound of a body existing. Its absence is never
        /// noticed and its presence is never noticed either — which is
        /// exactly why it works, and exactly why it gets cut. A coat that
        /// goes on in silence is a boolean; a coat that rustles is a
        /// garment, and in this game the coat is a MECHANIC, so it had
        /// better feel like a thing you put on.
        public static void Foley(string kind, float volume = 1f)
        {
            if (_root == null || _foot == null) return;
            _foot.pitch = Random.Range(0.95f, 1.05f);
            switch (kind)
            {
                case "coat_on":
                    _foot.PlayOneShot(Clip("cloth_long", () => Cloth(0.55f, 0.30f)), 0.9f * volume);
                    break;
                case "coat_off":
                    _foot.PlayOneShot(Clip("cloth_short", () => Cloth(0.38f, 0.45f)), 0.8f * volume);
                    break;
                case "keys":
                    _foot.PlayOneShot(Clip("keys", Keys), 0.7f * volume);
                    break;
                default:
                    _foot.PlayOneShot(Clip("cloth_short", () => Cloth(0.38f, 0.45f)), 0.35f * volume);
                    break;
            }
        }

        /// Something was knocked, brushed or dropped. `force` 0..1.
        ///
        /// Matched to material, because a bin and a bottle are not the same
        /// event and a single generic "thud" is how a world announces that
        /// nothing in it is really there.
        public static void Impact(string material, float force = 0.6f)
        {
            if (_root == null || _ui == null) return;
            force = Mathf.Clamp01(force);
            _ui.pitch = Random.Range(0.9f, 1.1f) * (1.15f - 0.3f * force);
            string name = material == "metal" ? "hit_metal"
                        : material == "glass" ? "hit_glass"
                        : material == "wood" ? "hit_wood"
                        : "hit_soft";
            _ui.PlayOneShot(Clip(name, () => Hit(material)), 0.25f + 0.55f * force);
            _ui.pitch = 1f;
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

        /// Cloth: band-passed noise with a soft attack and a long-ish tail.
        /// The soft attack is the whole difference between fabric and a
        /// snare — a rustle has no transient, which is why noise with a
        /// hard envelope always sounds like percussion instead.
        static AudioClip Cloth(float seconds, float brightness)
        {
            int len = (int)(SampleRate * seconds);
            var data = new float[len];
            var rng = new System.Random(97);
            float lp = 0, prev = 0;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)len;
                float env = Mathf.Min(1f, t / 0.18f) * Mathf.Exp(-3.2f * t);
                float n = (float)(rng.NextDouble() * 2 - 1);
                lp += (n - lp) * brightness;
                float bp = lp - prev; prev = lp;         // crude band-pass
                data[i] = bp * env * 0.45f;
            }
            return Make("cloth", data);
        }

        static AudioClip Keys()
        {
            int len = SampleRate / 3;
            var data = new float[len];
            var rng = new System.Random(431);
            // Four bright transients, unevenly spaced — evenly spaced reads
            // as a machine rather than as a bunch of keys moving.
            int[] at = { 0, SampleRate / 26, SampleRate / 11, SampleRate / 7 };
            foreach (var start in at)
                for (int i = start; i < Mathf.Min(len, start + SampleRate / 22); i++)
                {
                    float t = (i - start) / (float)(SampleRate / 22);
                    data[i] += (float)(rng.NextDouble() * 2 - 1) * Mathf.Exp(-26f * t) * 0.32f;
                }
            return Make("keys", data);
        }

        /// One impact, coloured by what it hit. Metal rings, glass is bright
        /// and short, wood is a dull knock, soft is barely anything.
        static AudioClip Hit(string material)
        {
            float decay = material == "metal" ? 5f : material == "glass" ? 14f
                        : material == "wood" ? 22f : 34f;
            float tone = material == "metal" ? 210f : material == "glass" ? 900f
                       : material == "wood" ? 150f : 90f;
            int len = (int)(SampleRate * (material == "metal" ? 0.55f : 0.22f));
            var data = new float[len];
            var rng = new System.Random(material.Length * 17 + 3);
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)SampleRate;
                float env = Mathf.Exp(-decay * t);
                float body = Mathf.Sin(2f * Mathf.PI * tone * t);
                float grit = (float)(rng.NextDouble() * 2 - 1) * Mathf.Exp(-90f * t);
                data[i] = (body * 0.55f + grit * 0.45f) * env * 0.5f;
            }
            return Make("hit_" + material, data);
        }

        public const int StepVariants = 5;

        /// Each variant is a different seed AND a slightly different decay, so
        /// they differ in shape rather than only in noise. A wet step keeps
        /// ringing after the heel lands — that tail is the whole difference
        /// between "asphalt" and "asphalt in the rain", and it costs a filter.
        static AudioClip Step(int variant, bool wet)
        {
            int len = wet ? SampleRate / 7 : SampleRate / 12;
            var data = new float[len];
            var rng = new System.Random(5 + variant * 31 + (wet ? 977 : 0));
            float decay = (wet ? 8.5f : 14f) + variant * 0.7f;
            float lp = 0, hp = 0;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)len;
                float env = Mathf.Exp(-decay * t);
                float n = (float)(rng.NextDouble() * 2 - 1);
                if (wet)
                {
                    // Band-passed noise with a longer tail reads as a splash;
                    // broadband with a hard decay reads as a dry heel.
                    lp += (n - lp) * 0.45f;
                    hp = lp - hp * 0.15f;
                    data[i] = hp * env * 0.55f;
                }
                else data[i] = n * env * 0.5f;
            }
            return Make(wet ? "step_wet" + variant : "step" + variant, data);
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
