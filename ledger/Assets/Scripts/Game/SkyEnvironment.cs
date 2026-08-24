using UnityEngine;
using UnityEngine.Rendering;

namespace Ledger.Game
{
    /// WHAT A DRY WINDOW REFLECTS — the four Poly Haven captures, wired to the
    /// environment cubemap and to nothing else (M17.10 V6).
    ///
    /// THE DECISION THIS IMPLEMENTS, 24 Aug, and it was made on numbers rather
    /// than on taste. Glass is smoothness 0.90 and Window 0.85 in `SurfaceSpec`,
    /// on every facade in town, so the largest reflective area in the game is
    /// its windows. What they reflected until now was a 64px cubemap baked off
    /// `Hidden/LedgerSky` — a three-colour gradient with no structure at all.
    /// The near-black windows in every landed still are dark BECAUSE there is
    /// nothing to reflect, not because anybody authored them dark.
    ///
    /// THE VISIBLE DOME IS NOT TOUCHED, on purpose. Swapping `RenderSettings.
    /// skybox` for a capture would trade a CONTINUOUS day — dusk warmth, night
    /// sodium, a per-day cloud deck the ambient fill reads from — for four fixed
    /// photographs it would pop between. Reflection is additive and cannot
    /// regress any of that: `ambientMode` stays Trilight and is written from
    /// `LightModel` every frame, so this changes reflections and nothing else.
    ///
    /// WHICH CAPTURE, AND WHY EACH ONE HAS A RULE. Four captures with three
    /// conditions between them would leave one sitting unused, which is the
    /// state this whole class exists to end:
    ///
    ///   belfast_open_field      day, dry, ordinary cloud — a British sky for a
    ///                           British port town, and named for one
    ///   kloppenheim_04          day, dry, LOW cloud deck — the clear-day
    ///                           alternate, picked off the per-day `deck` value
    ///                           SceneLighting already computes for the fill
    ///   misty_farm_road         day, wet — the overcast/mist case
    ///   industrial_sunset       through the crossover, where `Dusk` is up
    ///
    /// NIGHT KEEPS THE PROCEDURAL CUBEMAP, because there is no night capture.
    /// The handover sits at `night >= 0.5`, which is NOT a number invented here
    /// — it is the crossover the lighting model already turns on, the peak of
    /// `LightModel.Dusk` and the point either side of which the sun or the lamps
    /// dominate. If the handover shows in a still, the series below says so and
    /// the next value comes from evidence rather than from this sentence.
    ///
    /// WHY THERE IS NO PIXEL READBACK IN THE MEASUREMENT. An imported `.hdr` is
    /// not readable, and this project ships no `.meta` files — every import
    /// setting is Unity's default, decided on the CI machine — so `GetPixels`
    /// would throw rather than measure. What is checkable from here is the WIRE,
    /// and it is checked completely: how many captures were found against how
    /// many were asked for, what each loaded AS, which one is bound, and whether
    /// the binding is still live at the instant a frame is taken. The visual
    /// effect is then read off the pinned frames — the seven district shots and
    /// day1_noon/day1_night are the only rows `frame-drift` calls comparable,
    /// and windows are in all of them.
    public static class SkyEnvironment
    {
        /// Under `Assets/Resources`, which is why the captures moved there:
        /// `Resources.Load` cannot reach `Assets/Sky`, and `LoadImage` does not
        /// decode Radiance, so there is no route that leaves them where the
        /// fetch first put them.
        const string LoadRoot = "Sky/polyhaven/";

        const string DayName = "belfast_open_field_2k";
        const string ClearName = "kloppenheim_04_2k";
        const string WetName = "misty_farm_road_2k";
        const string DuskName = "industrial_sunset_puresky_2k";

        /// The crossover, from `LightModel.Dusk`'s own peak. Above it the lamps
        /// are the street's light and there is no capture to hand over TO.
        const float NightHandover = 0.5f;

        /// A LOW deck is a clear day. `SceneLighting` builds `deck` from the
        /// day's hash in the same range every day (0.35..0.75 dry), so this
        /// splits it near the middle of that band rather than at a round number.
        const float ClearDeck = 0.50f;

        static Texture _day, _clear, _wet, _dusk;
        static Texture _bound;
        static bool _loaded;

        /// THE DENOMINATOR, and rule 3b is the whole reason it is a pair. Four
        /// asked for, four found is a wire; four asked for, ZERO found reads
        /// identically to "the sky never changed" unless the count is printed
        /// beside it — and a `Resources.Load` that misses returns null quietly.
        public static int Asked, Found;
        /// Names that did not load, so one round trip says WHICH rather than
        /// that there was one.
        public static string MissingNames = "";
        /// What the first capture loaded as. An `.hdr` is expected to import as
        /// a Cube; if Unity's default gives a 2D texture instead, the binding
        /// still succeeds and reflects garbage, so the dimension is the tell.
        public static string LoadedAs = "not tried";
        /// Which capture is the environment right now, or `procedural`.
        public static string Bound = "none";
        /// How many times that changed. A source that never once changed across
        /// a thirteen-day run is a rule that is not running.
        public static int Binds;
        /// How many times the setting was actually WRITTEN, against `Binds`
        /// which counts how many times the chosen capture changed. They should
        /// be close: a `Rebinds` far above `Binds` means something is taking
        /// the environment away every frame and this class is fighting it,
        /// which is the failure the first version could not have detected
        /// because it wrote unconditionally and so never noticed.
        public static int Rebinds;
        /// True when `RenderSettings.customReflectionTexture` is still the
        /// object this class put there. `WetReflections` legitimately takes it
        /// over on a wet street; anything ELSE taking it is a fault, and
        /// without this the two are indistinguishable.
        public static bool Live;
        /// True only while a CAPTURE is bound. Night and the A/B both leave
        /// `Live` false legitimately, so a reader asking "did anything steal the
        /// binding" needs to know whether this class was claiming it at all —
        /// without that, every night frame counts as a theft.
        public static bool Owning;

        /// Load once. Safe to call every frame.
        public static void Ensure()
        {
            if (_loaded) return;
            _loaded = true;
            var missing = new System.Collections.Generic.List<string>();
            _day = Take(DayName, missing);
            _clear = Take(ClearName, missing);
            _wet = Take(WetName, missing);
            _dusk = Take(DuskName, missing);
            MissingNames = missing.Count == 0 ? "none" : string.Join("/", missing);
            var first = _day ?? _clear ?? _wet ?? _dusk;
            // After the shape gate above, a non-null here IS a cube, so this
            // reads `Cube` on success and `all rejected — see skyMissing` when
            // the importer regressed; the per-name entries carry the shapes.
            LoadedAs = first == null
                ? (Asked > 0 && missing.Count == Asked ? "all-rejected-see-skyMissing"
                                                       : "nothing-loaded")
                : first.dimension.ToString();
        }

        static Texture Take(string name, System.Collections.Generic.List<string> missing)
        {
            Asked++;
            var tex = Resources.Load<Texture>(LoadRoot + name);
            if (tex == null)
            {
                missing.Add(name);
                return null;
            }
            // FAIL CLOSED ON SHAPE, AND THIS LINE IS WHY THE 24 AUG STALL
            // CANNOT RECUR. `customReflectionTexture` accepts only a cube;
            // a capture that imported as 2D — which is Unity's DEFAULT for
            // an .hdr, and what every capture was before `SkyImport`
            // existed — throws at BIND time, once per frame, and one run
            // wrote 593,328 log lines and died at its kill cap having
            // taken one screenshot. A wrong-shaped texture is treated as
            // missing and NAMED with its shape, so the verdict says
            // `skyMissing=belfast_open_field_2k(2D)` instead of the log
            // saying nothing legible at all. The procedural cubemap is the
            // fallback either way, which is the pre-sky behaviour: worse
            // reflections, working game.
            if (tex.dimension != UnityEngine.Rendering.TextureDimension.Cube)
            {
                missing.Add(name + "(" + tex.dimension + ")");
                return null;
            }
            Found++;
            return tex;
        }

        /// Bind the source that matches the hour and the weather.
        ///
        /// NOT CALLED WHILE THE STREET IS WET. `WetReflections` publishes a real
        /// capture of the scene then, which beats any photograph of a sky, and
        /// two writers on one setting is how the fog calibration was lost for a
        /// week — so there is exactly one owner of the dry state and it is this,
        /// and one owner of the wet state and it is that.
        public static void Apply(float night, float rain, float deck)
        {
            Ensure();
            if (_suspended) return;
            Texture want;
            if (night >= NightHandover) want = null;                 // no capture exists
            else if (rain > 0.5f) want = _wet ?? _day;
            else if (LightModelDusk(night) > 0.5f) want = _dusk ?? _day;
            else if (deck < ClearDeck) want = _clear ?? _day;
            else want = _day;

            // WRITTEN ONLY WHEN IT CHANGES, WHICH IS TWICE A DAY.
            //
            // The first version of this function assigned all three settings on
            // EVERY dry frame, and `RenderSettings.customReflectionTexture` is
            // not a field — assigning it asks the engine to re-establish the
            // environment, so a value that moves at dawn and dusk was being
            // republished sixty times a second. That is wrong on its own terms
            // whatever it costs.
            //
            // IT IS ALSO THE OBVIOUS SUSPECT FOR `5ee9330`, AND THE EVIDENCE
            // DOES NOT SUPPORT SAYING SO. That run reached one shot in
            // twenty-four minutes where a healthy run takes twenty in twelve —
            // but two runs BEFORE this code existed were killed at four shots,
            // so the truncation is a pre-existing intermittent and one landing
            // cannot separate "made it worse" from "landed on a bad one".
            // Recorded as unproven rather than as a cause; `hangOwn` is what
            // will answer it, and this gets fixed either way.
            //
            // The re-assert is what makes "only on change" safe: `WetReflections`
            // legitimately takes the setting over on a wet street, so after a
            // handover the binding is stale and nothing would ever rewrite it.
            // `Stolen()` is that test, and it reads the setting rather than
            // trusting a flag.
            if (want == null)
            {
                if (_bound != null || Bound != "procedural")
                {
                    Binds++;
                    _bound = null;
                    Bound = "procedural";
                    RenderSettings.defaultReflectionMode = DefaultReflectionMode.Skybox;
                    RenderSettings.reflectionIntensity = 1f;
                }
                Live = false;
                Owning = false;
                return;
            }

            bool changed = !ReferenceEquals(want, _bound);
            if (changed)
            {
                Binds++;
                _bound = want;
                Bound = want.name;
            }
            Owning = true;
            if (changed || !ReferenceEquals(RenderSettings.customReflectionTexture, want))
            {
                RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
                RenderSettings.customReflectionTexture = want;
                RenderSettings.reflectionIntensity = 1f;
                Rebinds++;
            }
            Live = ReferenceEquals(RenderSettings.customReflectionTexture, _bound);
        }

        /// `LightModel.Dusk` without reaching across the assembly for one curve.
        /// Kept identical to it deliberately, and it is four lines: a wrapper
        /// that DRIFTS from the model it names is worse than an honest copy,
        /// and `CoreTests` owns the original.
        static float LightModelDusk(float night)
        {
            night = Mathf.Clamp01(night);
            float d = 4f * night * (1f - night);
            return d * d * d;
        }

        static bool _suspended;

        /// The A/B's off side. `SimDirector` turns reflections off to measure
        /// what they contribute, and that question includes this class — an
        /// "off" that quietly left a sky capture under every window would
        /// measure a photograph against a photograph and report it as the
        /// feature's contribution, which is the inert-A/B fault this file's own
        /// comments already name twice.
        public static void Suspend()
        {
            _suspended = true;
            _bound = null;
            Bound = "suspended";
            Live = false;
            Owning = false;
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Skybox;
            RenderSettings.reflectionIntensity = 0f;
        }

        public static void Resume()
        {
            _suspended = false;
        }

        /// Called by `WetReflections` when the street dries out, so the handover
        /// has no gap. Restoring `Skybox` there instead — which is what it used
        /// to do — would put the gradient back under every window for as long as
        /// it took the next `Apply` to run, and component order is undefined.
        public static void Restore(float night, float rain, float deck)
        {
            Apply(night, rain, deck);
        }

        /// Re-read on demand, because `Live` is a claim about NOW and the sim
        /// reads it long after `Apply` last ran. Returns true when this class
        /// believes it owns the environment and does NOT: the theft case, which
        /// is the only one worth counting.
        public static bool Stolen()
        {
            if (!Owning) return false;
            Live = _bound != null
                   && ReferenceEquals(RenderSettings.customReflectionTexture, _bound);
            return !Live;
        }
    }
}
