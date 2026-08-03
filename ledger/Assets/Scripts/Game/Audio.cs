// NO `using System;` HERE, deliberately. This file uses bare `Object.`
// and `Random.`, which resolve to UnityEngine's — and importing System
// makes both ambiguous with System.Object and System.Random (CS0104).
// Adding it cost a build; `System.Math` is spelled out below instead.
using System.Collections.Generic;
using Ledger.Core;
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
        /// The voice bus, and the two halves of the telephone: `_phone` is the
        /// speech that arrives down the wire, `_line` is the wire itself.
        static AudioSource _voice, _phone, _line;
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
            // SPEECH GETS ITS OWN SOURCES. Everything above ducks for the
            // voice bus and there was no voice bus — `Core/Mixing` has had a
            // reach, a budget, a duck depth and a protection rule for
            // `Bus.Voice` since the day it was written, and nothing in the
            // game was ever on it.
            _voice = Make("Voice", loop: false);
            _phone = Make("Phone", loop: false);
            _line = Make("Line", loop: true);
            BuildTelephoneFilters();
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
            // PER-BUS DUCK DEPTH, from Core/Mixing. Ducking everything by the
            // same amount is the classic over-correction: it takes the street
            // out from behind the speaker, which sounds like a fault rather
            // than like emphasis. Music gets out of the way hard, the bed a
            // little, footsteps barely — dialogue over nothing sounds like a
            // vacuum — and the interface not at all, because it is not in the
            // world.
            float dAmb = (float)Mixing.Gain(Bus.Ambience, _duck, _overhearing);
            float dMus = (float)Mixing.Gain(Bus.Music, _duck, _overhearing);
            float dFol = (float)Mixing.Gain(Bus.Foley, _duck, _overhearing);
            if (_ambience != null)
                _ambience.volume = (0.28f + 0.34f * _chatter) * s.MasterVolume * s.MusicVolume * dAmb;
            if (_music != null) _music.volume = 0.22f * s.MasterVolume * s.MusicVolume * dMus;
            if (_ui != null) _ui.volume = 0.6f * s.MasterVolume * s.SfxVolume;
            if (_foot != null) _foot.volume = 0.35f * s.MasterVolume * s.SfxVolume * dFol;
            // VOICE DOES NOT DUCK FOR ITSELF — `Mixing.DuckDepth(Bus.Voice)`
            // is zero, and multiplying by it is here so the shape of this
            // block stays honest rather than because the number does work.
            float dVox = (float)Mixing.Gain(Bus.Voice, _duck, _overhearing);
            if (_voice != null) _voice.volume = 0.85f * s.MasterVolume * s.VoiceVolume * dVox;
            // The wire is quieter than the person on it, always. A line bed
            // that competes with the speech is the mistake this whole
            // treatment exists to avoid.
            if (_phone != null) _phone.volume = 0.85f * s.MasterVolume * s.VoiceVolume * dVox;
            if (_line != null)
                _line.volume = _lineBedGain * 0.30f * s.MasterVolume * s.VoiceVolume;
            // The traffic bed's own volume is driven per-frame by proximity; the
            // settings only scale the ceiling it is allowed to reach.
            _trafficCeiling = 0.30f * s.MasterVolume * s.SfxVolume * dAmb;
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

        /// CONTINUOUS DAY AND NIGHT (game-feel-spec.md §8, "continuous
        /// day/night lighting, not stepped").
        ///
        /// The light has always lerped smoothly and the SOUND did not: the
        /// room swapped on an hour boundary, so at 20:00 exactly the street
        /// changed character in one frame. That is the one hard cut left in
        /// the game, and it is the more noticeable half, because a picture
        /// that fades while its soundtrack jumps reads as a bug rather than
        /// as dusk.
        ///
        /// Both beds now play at once and crossfade on the SAME daylight
        /// number the sun uses, so light and sound cannot disagree about what
        /// time it is.
        static AudioSource _ambienceNight;

        public static void SetDaylight(float night)
        {
            if (_root == null || _ambience == null) return;
            night = Mathf.Clamp01(night);
            if (_ambienceNight == null)
            {
                _ambienceNight = Make("AmbienceNight", loop: true);
                _ambienceNight.clip = Clip("ambience_night", () => Ambience(true));
                _ambienceNight.Play();
            }
            if (_ambience.clip == null)
            {
                _ambience.clip = Clip("ambience_day", () => Ambience(false));
                _ambience.Play();
            }
            var s = GameSettings.Current;
            float bed = (0.28f + 0.34f * _chatter) * s.MasterVolume * s.MusicVolume;
            // Equal-power rather than linear, or the crossfade dips in the
            // middle and dusk sounds like a hole in the audio.
            _ambience.volume = bed * Mathf.Cos(night * Mathf.PI * 0.5f);
            _ambienceNight.volume = bed * Mathf.Sin(night * Mathf.PI * 0.5f);
        }

        // ---- ADAPTIVE SCORE (Core/MusicModel) ------------------------------
        //
        // Four stems, playing at once, SAMPLE-ALIGNED, each faded
        // independently. The fixed day/night pair was wallpaper; this is the
        // score doing the one job nothing else can — telling a player who is
        // looking somewhere else that the street has turned.
        //
        // The rule, from MusicModel and worth repeating where the audio
        // actually happens: AS EXPOSURE RISES THE SCORE LOSES INSTRUMENTS.
        // The arpeggio dropping out is the signal. A stinger says "something
        // dramatic is happening"; a room going quiet says "everybody here
        // already knows".
        static AudioSource[] _stems;
        static readonly double[] _stemGain = new double[MusicModel.Layers];

        public static void SetScore(ScoreState state, float dt)
        {
            if (_root == null || state == null) return;
            if (_stems == null)
            {
                _stems = new AudioSource[MusicModel.Layers];
                // Started on the SAME frame from the same length of audio, so
                // the stems stay in phase for the whole session. Starting them
                // lazily as they are first needed would drift them apart and
                // the chords would smear.
                for (int i = 0; i < MusicModel.Layers; i++)
                {
                    var layer = (MusicLayer)i;
                    _stems[i] = Make("Stem_" + layer, loop: true);
                    _stems[i].clip = Clip("music_stem_" + layer, () => Stem(layer));
                    _stems[i].volume = 0f;
                    _stems[i].Play();
                }
                // The single fixed track is retired the moment stems exist —
                // two scores playing over each other is the worst possible
                // outcome and would be nearly impossible to diagnose by ear.
                if (_music != null) { _music.Stop(); _music.clip = null; }
            }

            var target = MusicModel.Mix(state);
            MusicModel.Settle(_stemGain, target, dt);

            var s = GameSettings.Current;
            float master = 0.30f * s.MasterVolume * s.MusicVolume;
            for (int i = 0; i < _stems.Length; i++)
                if (_stems[i] != null) _stems[i].volume = (float)_stemGain[i] * master;
        }

        /// Live mix, for the sim to assert against.
        public static double StemGain(MusicLayer l) =>
            _stems == null ? 0 : _stemGain[(int)l];

        /// WHAT UNITY IS ACTUALLY PLAYING, which is a different claim.
        ///
        /// `StemGain` returns the number this file computed. Delete the line
        /// that pushes it onto the AudioSource and it keeps returning exactly
        /// the same numbers, the score gate keeps passing, and the game is
        /// silent. That is the shape that let the entire post stack sit dead
        /// for months — every check was of the model, and the model was fine.
        ///
        /// Reading the volume back off the engine is the audio equivalent of
        /// asking a label for its laid-out width instead of its text.
        public static float StemVolume(MusicLayer l) =>
            _stems == null || _stems[(int)l] == null ? -1f : _stems[(int)l].volume;

        /// The same question for the buses the duck actually moves.
        public static float BusVolume(Bus b)
        {
            switch (b)
            {
                case Bus.Music: return _music != null ? _music.volume : -1f;
                case Bus.Ambience: return _ambience != null ? _ambience.volume : -1f;
                case Bus.Foley: return _foot != null ? _foot.volume : -1f;
                case Bus.Ui: return _ui != null ? _ui.volume : -1f;
                default: return -1f;
            }
        }
        public static bool ScoreRunning => _stems != null;

        /// One stem. Every layer is the SAME four bars at the same tempo and
        /// in the same key, so any subset of them is a coherent piece of
        /// music — which is the entire discipline of writing stems, and the
        /// reason a layer can drop out mid-bar without it sounding broken.
        static AudioClip Stem(MusicLayer layer)
        {
            const int barSeconds = 6;
            int[][] chords =
            {
                new[] { 0, 3, 7, 10 },    // Am7
                new[] { -4, 0, 3, 7 },    // Fmaj7
                new[] { -2, 2, 5, 9 },    // Gmaj-ish
                new[] { 3, 7, 10, 14 },   // Cmaj add9
            };
            int len = SampleRate * barSeconds * chords.Length;
            var data = new float[len];
            const float root = 110f;
            float[] arpSteps = { 0, 3, 7, 10, 12, 10, 7, 3 };
            var rng = new System.Random(1988 + (int)layer);

            for (int c = 0; c < chords.Length; c++)
            {
                int start = c * barSeconds * SampleRate;
                int clen = barSeconds * SampleRate;

                if (layer == MusicLayer.Bed)
                {
                    // Detuned saw pad: two oscillators a few cents apart is
                    // the whole sound of the decade.
                    foreach (var semi in chords[c])
                    {
                        float hz = root * 4f * Mathf.Pow(2f, semi / 12f);
                        float amp = 0.055f / chords[c].Length;
                        for (int i = 0; i < clen; i++)
                        {
                            float t = i / (float)SampleRate;
                            float env = Mathf.Min(1f, t / 1.2f) * Mathf.Min(1f, (barSeconds - t) / 1.2f);
                            float a1 = Mathf.Repeat(hz * t, 1f) * 2f - 1f;
                            float a2 = Mathf.Repeat(hz * 1.006f * t, 1f) * 2f - 1f;
                            data[start + i] += (a1 + a2) * 0.5f * amp * env;
                        }
                    }
                }
                else if (layer == MusicLayer.Pulse)
                {
                    // Sub bass — the thing you feel rather than hear.
                    float bassHz = root * Mathf.Pow(2f, chords[c][0] / 12f);
                    for (int i = 0; i < clen; i++)
                    {
                        float t = i / (float)SampleRate;
                        float env = Mathf.Min(1f, t / 0.05f) * Mathf.Min(1f, (barSeconds - t) / 0.6f);
                        data[start + i] += (Mathf.Repeat(bassHz * t, 1f) * 2f - 1f) * 0.085f * env;
                    }
                    // And the arpeggio that keeps the blood moving.
                    const int steps = 16;
                    float stepLen = barSeconds / (float)steps;
                    for (int stp = 0; stp < steps; stp++)
                    {
                        float semi = chords[c][0] + arpSteps[stp % arpSteps.Length];
                        float hz = root * 8f * Mathf.Pow(2f, semi / 12f);
                        int at = start + (int)(stp * stepLen * SampleRate);
                        int nlen = (int)(stepLen * SampleRate * 0.9f);
                        float vel = stp % 4 == 0 ? 1f : 0.62f;
                        for (int i = 0; i < nlen && at + i < len; i++)
                        {
                            float t = i / (float)SampleRate;
                            float env = Mathf.Min(1f, t / 0.008f) * Mathf.Exp(-t * 9f);
                            float sq = Mathf.Sin(2 * Mathf.PI * hz * t) > 0 ? 1f : -1f;
                            data[at + i] += sq * 0.030f * vel * env;
                        }
                    }
                }
                else if (layer == MusicLayer.Unease)
                {
                    // A high detuned drone on the MINOR SECOND above the
                    // root. It is in the key and it does not belong, which is
                    // exactly what being talked about feels like — nothing you
                    // can point at, and you cannot stop hearing it.
                    float hz = root * 8f * Mathf.Pow(2f, (chords[c][0] + 1) / 12f);
                    for (int i = 0; i < clen; i++)
                    {
                        float t = i / (float)SampleRate;
                        float env = Mathf.Min(1f, t / 2.4f) * Mathf.Min(1f, (barSeconds - t) / 2.4f);
                        // Slow beating between the two, so it breathes rather
                        // than sitting there as a test tone.
                        float a1 = Mathf.Sin(2 * Mathf.PI * hz * t);
                        float a2 = Mathf.Sin(2 * Mathf.PI * hz * 1.004f * t);
                        data[start + i] += (a1 + a2) * 0.5f * 0.030f * env;
                    }
                }
                else // Dread
                {
                    // A sub swell an octave under the bass, rising through
                    // the bar. Felt more than heard, and it does not resolve.
                    float hz = root * 0.5f * Mathf.Pow(2f, chords[c][0] / 12f);
                    for (int i = 0; i < clen; i++)
                    {
                        float t = i / (float)SampleRate;
                        float swell = t / barSeconds;
                        float env = swell * swell * Mathf.Min(1f, (barSeconds - t) / 0.8f);
                        data[start + i] += Mathf.Sin(2 * Mathf.PI * hz * t) * 0.095f * env;
                        // A breath of noise on top, filtered by being tiny.
                        data[start + i] += (float)(rng.NextDouble() * 2 - 1) * 0.004f * env;
                    }
                }
            }

            CrossfadeEnds(data, SampleRate / 2);
            return Make("music_stem_" + layer, data);
        }

        /// THE DUCK, which was a boolean and is now an envelope.
        ///
        /// `DuckMusic(true/false)` snapped the score to 35% and back, which
        /// makes the mix breathe on every line — the bed swelling into each
        /// gap and collapsing again. It is the most recognisable sound of an
        /// amateur mix and audible to people who could not name it.
        ///
        /// Every number is `Core/Mixing`, where they are tested. This holds
        /// one float and calls into it.
        static bool _talking, _overhearing;
        static double _duck;

        public static double DuckAmount => _duck;

        public static void DuckMusic(bool talking)
        {
            _talking = talking;
        }

        /// OVERHEARING IS A DIFFERENT DUCK. Two people discussing the player
        /// six metres away is the moment the whole gossip system exists for,
        /// and it competes with rain, traffic, and a street bed authored to
        /// sit comfortably for walking around in. So the bed gets out of the
        /// way HARDER for something he was not meant to hear.
        public static void DuckForOverheard(bool overhearing)
        {
            _overhearing = overhearing;
        }

        /// Advance the envelope. Called once a frame from the same place
        /// that drives the score.
        public static void StepMix(float dt)
        {
            double before = _duck;
            _duck = Mixing.StepDuck(_duck, (_talking || _overhearing) ? 1 : 0, dt);
            // Only push to the sources when it actually moved enough to
            // hear. ApplyVolumes touches every AudioSource in the game and
            // running it every frame for a change of 0.0001 is a cost for
            // nothing.
            if (System.Math.Abs(_duck - before) > 0.002) ApplyVolumes();
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

        // ---- THE VOICE BUS -------------------------------------------------
        //
        // Audit item 7. `Core/Mixing` has described `Bus.Voice` since it was
        // written — a reach of fourteen metres, a budget of four, a duck
        // depth of zero because it is the thing everything else ducks FOR,
        // and a protection rule so an authored line never loses its slot to a
        // footstep. None of it was connected to an AudioSource. Speech in
        // this game was text in a bubble.

        static AudioLowPassFilter _voiceLp, _phoneLp, _lineLp;
        static AudioHighPassFilter _phoneHp, _lineHp;
        static float _lineBedGain;

        /// How many `Speak` calls found no clip in the bank. Zero is not the
        /// goal — the bank does not exist yet — but a number that never moves
        /// while the game is talking means the wire is not connected, and
        /// that is the failure this whole session has been about.
        public static int SpeechPlayed { get; private set; }
        public static int SpeechMissing { get; private set; }

        /// WHY IT WAS MISSING, AND THERE ARE THREE ANSWERS.
        ///
        /// `speechMissing=358` was one number covering causes that want
        /// completely different responses: a line nobody could have heard from
        /// where they stood, a line whose recording does not exist yet, and a
        /// line the audio system was never up to play at all. The first is the
        /// mix working. The second is a milestone. The third is a fault.
        ///
        /// I was about to quote that number as the size of the voice gap. It
        /// is not: it is an upper bound on it, and until tonight nothing said
        /// by how much. The same shape as `EyesOpen` and `KnowsYou` — a count
        /// that answers two questions answers neither.
        public static int SpeechOutOfRange { get; private set; }
        public static int SpeechNoClip { get; private set; }
        public static int SpeechNoAudio { get; private set; }

        /// WHAT THE BANK WOULD ACTUALLY HAVE TO CONTAIN — the number that
        /// decides M17.2's scope, and it is not the one I was about to ask
        /// Jafar to rule on.
        ///
        /// The arithmetic said 2,604 authored bark lines times six crowd voices
        /// is 15,624 clips and roughly forty-three hours of runner time, so I
        /// wrote it up as a decision he had to take. That is the THEORETICAL
        /// cross product. What a bank has to hold is the pairs the game
        /// actually ASKS FOR, and nobody had counted those.
        ///
        /// `ClipName` keys a recording by (voice, exact text), which also
        /// settles the other half: LLM-generated conversation is novel every
        /// time, so it can never have a pre-generated clip and is not part of
        /// this number at all. Only authored text can be banked.
        ///
        /// So: every distinct clip name the run requests, counted, and the
        /// distinct VOICES among them. A seventeen-day run exercises the real
        /// distribution — who stands near whom, which slots fire, how often a
        /// line repeats — and turns a scope argument into a measurement.
        static readonly System.Collections.Generic.HashSet<string> _asked =
            new System.Collections.Generic.HashSet<string>();
        static readonly System.Collections.Generic.HashSet<string> _askedVoices =
            new System.Collections.Generic.HashSet<string>();

        public static int DistinctClipsAsked => _asked.Count;
        public static int DistinctVoicesAsked => _askedVoices.Count;

        public static void ResetSpeechCounters()
        {
            SpeechPlayed = 0; SpeechMissing = 0;
            SpeechOutOfRange = 0; SpeechNoClip = 0; SpeechNoAudio = 0;
            _asked.Clear(); _askedVoices.Clear();
        }

        /// Recorded on the way in, before any reason to give up on the clip —
        /// out of range, missing from the bank, no audio root. The question is
        /// what the bank WOULD need, so a request that could not be served is
        /// exactly the request that matters most.
        static void NoteAsked(string clipName)
        {
            if (string.IsNullOrEmpty(clipName)) return;
            _asked.Add(clipName);
            int slash = clipName.IndexOf('/');
            if (slash > 0) _askedVoices.Add(clipName.Substring(0, slash));
        }

        static void BuildTelephoneFilters()
        {
            if (_voice != null)
                _voiceLp = _voice.gameObject.AddComponent<AudioLowPassFilter>();
            if (_phone != null)
            {
                _phoneLp = _phone.gameObject.AddComponent<AudioLowPassFilter>();
                _phoneHp = _phone.gameObject.AddComponent<AudioHighPassFilter>();
            }
            if (_line != null)
            {
                _lineLp = _line.gameObject.AddComponent<AudioLowPassFilter>();
                _lineHp = _line.gameObject.AddComponent<AudioHighPassFilter>();
            }
            // The band is the same one Core states, applied in one place.
            SetBand(_phoneLp, _phoneHp);
            SetBand(_lineLp, _lineHp);
            if (_voiceLp != null) _voiceLp.cutoffFrequency = 22000f;
        }

        static void SetBand(AudioLowPassFilter lp, AudioHighPassFilter hp)
        {
            if (lp != null) lp.cutoffFrequency = (float)Acoustics.TelephoneHighHz;
            if (hp != null) hp.cutoffFrequency = (float)Acoustics.TelephoneLowHz;
        }

        /// Somebody said something out loud, in the room, at `metres`.
        ///
        /// Returns false when the bank has no clip for that line — which is
        /// today's normal answer and is reported rather than swallowed. The
        /// duck still happens either way: the mix should behave the same
        /// whether or not the recording exists, or the day the bank lands the
        /// whole street will change balance for reasons nobody can trace.
        public static bool Speak(string clipName, float metres = 0f,
                                 bool occluded = false, float streetNoise = 0f)
        {
            NoteAsked(clipName);
            // COUNTED, NOT SILENTLY DROPPED. This returned false without
            // touching either counter, so on a runner with no audio device
            // every request vanished and `speechMissing` UNDERSTATED the
            // demand — a bank sized off that number would have been short.
            if (_root == null || _voice == null) { SpeechNoAudio++; return false; }
            double reach = Mixing.Reach(Bus.Voice);
            if (metres > reach) { SpeechMissing++; SpeechOutOfRange++; return false; }

            // The distance IS the filter. A quiet sound that is still bright
            // reads as a small sound nearby, not a loud one far away.
            if (_voiceLp != null)
                _voiceLp.cutoffFrequency = (float)Acoustics.LowPassHz(metres, occluded);

            var clip = VoiceClip(clipName);
            if (clip == null) { SpeechMissing++; SpeechNoClip++; return false; }

            float gain = (float)Mixing.Attenuate(Bus.Voice, metres);
            gain *= 1f - 0.35f * Mathf.Clamp01(streetNoise);
            _voice.PlayOneShot(clip, Mathf.Clamp01(gain));
            SpeechPlayed++;
            return true;
        }

        /// Speech that arrives down a wire. Same bank, different treatment,
        /// and the treatment is the mechanic.
        public static bool SpeakOnTheLine(string clipName, Acoustics.LineKind kind)
        {
            // THE PHONE DRAWS FROM THE SAME BANK, so its requests are part of
            // the same demand. Counting only the in-room path would understate
            // what has to be generated by every line anybody ever says down a
            // wire — and the phone layer is a whole milestone's worth of them.
            NoteAsked(clipName);
            if (_root == null || _phone == null) { SpeechNoAudio++; return false; }
            var clip = VoiceClip(clipName);
            if (clip == null) { SpeechMissing++; SpeechNoClip++; return false; }
            // DISTANCE DOES NOT APPLY. A caller two hundred miles away and a
            // caller in the next street arrive at the same level; that is
            // what a telephone is, and it is stated in `Acoustics` so nobody
            // reaches for the metres model here by reflex.
            _phone.PlayOneShot(clip, (float)Acoustics.LineClarity(kind));
            SpeechPlayed++;
            return true;
        }

        /// The bank lives under its own folder because it is the one set of
        /// assets that will be produced by a generator rather than by hand,
        /// and mixing it in with the foley makes both harder to replace.
        static AudioClip VoiceClip(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            if (Cache.TryGetValue("voice/" + name, out var cached)) return cached;
            AudioClip clip = null;
            try
            {
                var path = System.IO.Path.Combine(Application.streamingAssetsPath,
                                                  "Audio", "Voice", name + ".wav");
                if (System.IO.File.Exists(path)) clip = LoadWav(path, name);
            }
            catch (System.Exception) { /* no bank yet is the normal case */ }
            // NO SYNTHESISED PLACEHOLDER. A generated mouth-noise stand-in is
            // a design decision nobody has made, and a bad one taken by
            // default is exactly the shape of mistake this audit was written
            // about. Silence, counted, until the bank exists.
            Cache["voice/" + name] = clip;
            return clip;
        }

        // ---- THE SECOND CHANNEL --------------------------------------------
        //
        // Audit item 2. The phone had a social model — `PhoneBook` damps what
        // you learn down a wire — and no sound of its own at all. A voice on
        // the telephone was sample-identical to the same voice standing in
        // the room, which throws away the identity of a mechanic that has its
        // own milestone.

        static bool _lineOpen;

        public static bool LineIsOpen => _lineOpen;

        /// Pick the handset up. `callerSpace` is the room the OTHER person is
        /// standing in, and it is the best detail available to a game about
        /// knowing where people are: a hall behind Ellis tells you which
        /// building he is in and nobody wrote a line of dialogue for it.
        public static void OpenLine(Acoustics.LineKind kind,
                                    SpaceKind callerSpace = SpaceKind.Room)
        {
            if (_root == null || _line == null) return;
            _lineOpen = true;
            _lineBedGain = (float)(Acoustics.LineNoise(kind) +
                                   0.6 * Acoustics.Bleed(callerSpace, kind));
            _line.clip = Clip("line_" + kind + "_" + callerSpace,
                              () => LineBed(kind, callerSpace));
            _line.loop = true;
            _line.Play();
            ApplyVolumes();
        }

        public static void CloseLine()
        {
            _lineOpen = false;
            _lineBedGain = 0f;
            if (_line != null) _line.Stop();
            ApplyVolumes();
        }

        /// The wire itself: hiss inside the voice band, the caller's room
        /// arriving as a dulled wash of it, and mains hum underneath.
        ///
        /// The hum is the one part deliberately OUTSIDE the 300–3400 band,
        /// because it is not coming down the line — it is induced in the
        /// earpiece against your head, and a phone bed built entirely inside
        /// the passband sounds like a filter rather than like a telephone.
        static AudioClip LineBed(Acoustics.LineKind kind, SpaceKind callerSpace)
        {
            int len = SampleRate * 4;                       // a 4-second loop
            var data = new float[len];
            // Seeded per line kind and room, so the same call always sounds
            // the same — determinism is audit item 5 and it starts here.
            var rng = new System.Random(((int)kind + 1) * 977 + (int)callerSpace * 31);
            float noise = (float)Acoustics.LineNoise(kind);
            float bleed = (float)Acoustics.Bleed(callerSpace, kind);

            // Two one-pole filters make a crude band-pass, which is exactly
            // what a carbon mouthpiece is.
            float lp = 0f, hp = 0f;
            // Cutoffs as one-pole coefficients at this sample rate.
            float kLow = 1f - Mathf.Exp(-2f * Mathf.PI * (float)Acoustics.TelephoneHighHz / SampleRate);
            float kHigh = 1f - Mathf.Exp(-2f * Mathf.PI * (float)Acoustics.TelephoneLowHz / SampleRate);

            // The handset's ring, as a resonator the noise is fed through.
            // Unity's built-in filters have no peaking EQ, so the peak that
            // makes a band-passed voice read as a TELEPHONE rather than as a
            // voice through a wall is baked in here, at the sample level,
            // where we own every number.
            float r = Mathf.Exp(-Mathf.PI * (float)Acoustics.HandsetResonanceHz
                                / ((float)Acoustics.HandsetResonanceQ * SampleRate));
            float theta = 2f * Mathf.PI * (float)Acoustics.HandsetResonanceHz / SampleRate;
            float a1 = -2f * r * Mathf.Cos(theta), a2 = r * r;
            float y1 = 0f, y2 = 0f;

            // SETTLED, 2026-07-31. This was flagged as the one number in the
            // audio layer that said which side of an ocean the city is on,
            // with nobody having decided. The city is British — see
            // `setting-britain-2026-07-31.md` — so 50 is now the answer
            // rather than the default that happened to be typed.
            const float MainsHz = 50f;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)SampleRate;
                float n = (float)(rng.NextDouble() * 2 - 1);
                lp += (n - lp) * kLow;
                hp += (lp - hp) * kHigh;
                float banded = lp - hp;                    // 300..3400

                float res = banded - a1 * y1 - a2 * y2;
                y2 = y1; y1 = res;
                banded += res * 0.28f * (1f - r);

                // The caller's room: the same noise, slower, which is what a
                // reverberant space sounds like once the wire has taken the
                // top off it.
                float wash = Mathf.Sin(2f * Mathf.PI * 0.37f * t)
                           * Mathf.Sin(2f * Mathf.PI * 0.11f * t);

                float hum = Mathf.Sin(2f * Mathf.PI * MainsHz * t) * 0.35f
                          + Mathf.Sin(2f * Mathf.PI * MainsHz * 2f * t) * 0.12f;

                data[i] = banded * (0.55f + 0.45f * bleed * (0.5f + 0.5f * wash)) * noise
                        + hum * noise * 0.20f;
            }
            CrossfadeEnds(data, SampleRate / 4);
            return Make("line_" + kind + "_" + callerSpace, data);
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
