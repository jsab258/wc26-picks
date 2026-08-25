using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// M17.1. The bought body, when there is one.
    ///
    /// `CharacterRig.Bind` has had three tiers since it was written — a Humanoid
    /// Avatar, the procedural `Mannequin`, then a leaning capsule — with a note
    /// saying tier two could be deleted "when the FBX arrives". The FBX have
    /// been in the repository for days and nothing instantiated them, so tier
    /// one had never once matched.
    ///
    /// It is answered now rather than assumed: the build reports
    /// `models=44 humanoid=44 validHumanAvatar=44 clips=44`, so every FBX yields
    /// a valid human Avatar under `CharacterImport`'s settings.
    ///
    /// WHY THE PLAYER ONLY, AND NOT THE STREET. A Mixamo body is a skinned mesh
    /// of several thousand triangles; `Mannequin` is thirteen boxes. CI has no
    /// GPU and software-rasterises every frame, and the sim already spends
    /// ~297ms of a ~300ms frame in the rasteriser with the crowd it has. Putting
    /// fifty-five skinned meshes on that runner is a change whose cost I cannot
    /// predict and whose failure mode is a twenty-five-minute step timing out.
    ///
    /// So: one body, on the character in shot in every still, where it can
    /// actually be judged. The crowd keeps its boxes until there is a measured
    /// reason to change that — which is what `perFrame` and the sim's own
    /// timings will say once this has run.
    public static class RealBody
    {
        /// Whether a real body was instantiated, and why not when it was not.
        /// Read by the sim verdict — a fallback that is silent is a fallback
        /// nobody discovers, and this one is designed to be invisible.
        public static int Attached { get; private set; }
        public static string Why { get; private set; } = "not tried";

        /// `body.up` dotted with world up: 1 is standing, 0 is lying down.
        ///
        /// THE GATE THAT DID NOT EXIST. Five checks called the first bought body
        /// fine — attached, scaled, in the height range, primitive gone — while
        /// it lay on its back in the road, because every one of them asks about
        /// the body that was ADDED and none asks what it looks like. Jafar found
        /// it in the still. This is the number that would have.
        public static double Upright { get; private set; }
        public static string Orientation { get; private set; } = "not tried";

        /// HOW THE BODY IS PAINTED, counted so a run can tell the three cases
        /// apart. `Kept` is renderers that arrived with their own material,
        /// `Skinned` is head/hands/eyes, `Dressed` is everything the wardrobe
        /// covered. The build that made these necessary read `Skinned` = every
        /// renderer and `Dressed` = 0 — a naked player on a dressed street —
        /// and reported nothing at all, because a body painted entirely skin
        /// has a material on every renderer and passes every check that asks
        /// whether a material exists.
        public static int Skinned { get; private set; }
        public static int Dressed { get; private set; }
        public static int Kept { get; private set; }

        /// AND THE SAME THREE OVER THE WHOLE RUN, because the three above are
        /// RESET AT EVERY ATTACH and therefore describe whichever body was
        /// attached last.
        ///
        /// `bodySkinned=0 bodyDressed=0` is a last-wins reading. I was one
        /// sentence away from writing "nothing in this city is ever painted"
        /// off it, which it cannot support — it says the LAST body was not,
        /// and the last body is whichever walker the LOD happened to grant as
        /// the run ended. The distinction matters here because the paint path
        /// carrying zero for the whole run is what makes the wash the only
        /// route the wardrobe has, and that claim is load-bearing on the
        /// change beside it.
        ///
        /// Same fault as `namesManagedEver`, from the opposite side: there a
        /// cumulative number was sampled somewhere sparse, here a per-event
        /// number was read as a lifetime one.
        public static int SkinnedEver { get; private set; }
        public static int DressedEver { get; private set; }
        public static int KeptEver { get; private set; }

        /// The breadth applied to the last body attached — a statement ABOUT
        /// THE PLAYER when a gate reads it, so it goes in the save-and-restore
        /// set with `Why`, unlike the lifetime counters below it.
        public static float Breadth { get; private set; } = -1;

        /// AND THE SPREAD ACROSS THE CROWD, which is the half that matters.
        ///
        /// One breadth says the player is 1.04 wide. It cannot say whether the
        /// street varies, and "the street varies" is the entire claim — the
        /// same distinction `crowdLum` had to learn when one body near the
        /// camera was setting the crowd's reading by itself. Distinct values,
        /// because breadth is a function of the name and repeating a walker
        /// would weight it by how often the LOD happened to grant them a body.
        public static readonly SortedSet<string> BreadthsEver = new SortedSet<string>();

        /// Every distinct `renderer->material` the wardrobe has decided, over
        /// the whole run. Bounded, because a name that is not distinct after
        /// ten models is a name that never will be — and this exists to be
        /// READ, so an unbounded list would defeat it by being unreadable.
        public static readonly SortedSet<string> PartsEver = new SortedSet<string>();

        /// AND HOW MUCH OF THE BODY EACH OF THOSE ACTUALLY COVERS.
        ///
        /// The counts above are of RENDERERS, and a count cannot see
        /// proportion. `bodyDressed=1 bodySkinned=1` is the same reading
        /// whether the coat covers the torso and the skin covers the hands, or
        /// the skin covers the whole figure and the coat covers a waistband —
        /// and the noon still on 3 August shows the second one, a bare
        /// mannequin, while every number in the run said dressed. Three faults
        /// have now been found by a human opening a frame and none by a gate
        /// (rule 4); this is the one that would have caught this one.
        ///
        /// TRIANGLE AREA RATHER THAN VERTEX COUNT, because vertex share only
        /// equals surface share if the mesh is uniformly tessellated, and
        /// heads never are — a face carries a large share of a character's
        /// vertices and a small share of its skin. Area is the quantity the
        /// eye is actually judging, so it is the one to measure rather than a
        /// proxy that happens to be easier to get. Both are printed: if they
        /// disagree, the disagreement is itself the finding.
        public static double DressedAreaFraction { get; private set; }
        public static double DressedVertexFraction { get; private set; }
        public static bool CoverageRead { get; private set; }

        /// Every paintable mesh, its share of the body's surface, and which
        /// material it got — `Beta_Surface:70.4%->skin Beta_Joints:29.6%->coat`.
        /// The naked player was visible in three separate numbers and legible
        /// in none of them; this is the line that says it in words.
        public static string Parts { get; private set; } = "not tried";

        /// Is the body actually clothed? False only when coverage was READ and
        /// came back under the bound — a model whose materials all arrived
        /// textured is never measured and must not fail for it (rule 5b: the
        /// guard has to pass the case it should pass, and a bought character
        /// with its own textures is that case).
        public static bool Clothed =>
            !CoverageRead || DressedAreaFraction >= BodyParts.MinDressedArea;

        /// THE MODEL BROUGHT ITS OWN CLOTHES, so the wardrobe stood down.
        ///
        /// The exemption above was written for `Clothed` and the gate has a
        /// SECOND clause one line down — `RealBody.Dressed > 0` — that never
        /// got it. The moment the texture extraction started working, that
        /// clause turned red: `dressed=0 skinned=0 clothed=True coat=-1.000
        /// parts=()` with `bodyKeptMats=1`, which is the whole system doing
        /// exactly what it was built to do. Every renderer arrived with a
        /// texture, so `Kept` took all of them, nothing needed painting, and
        /// the gate demanded paint.
        ///
        /// That is rule 5's ratchet in its purest form: a guard that cannot
        /// tell a regression from an improvement, failing the run that fixed
        /// the thing. And it is rule 1's third corollary again — one idea, two
        /// implementations, and the one nobody looked at is the one missing a
        /// line. The exemption is named here so there is one of it rather than
        /// three.
        ///
        /// It is not a loosened bound. `Kept` only counts a renderer whose
        /// material carries a real texture, which is a stronger statement about
        /// the figure being clothed than the coat-area fraction is — the coat
        /// area asks whether OUR paint covered enough of him, and this asks
        /// whether the artist's did.
        public static bool WearsOwnSkin => Kept > 0;

        /// The skeleton as IMPORTED, before anything animates it. See the note
        /// where these are measured: this is what tells a bad import apart from
        /// a bad animation without spending a CI round trip on each guess.
        public static float BindHeadAboveHips { get; private set; }
        public static float BindHipsAboveFeet { get; private set; }
        public static bool BindPoseRead { get; private set; }

        /// The same span AFTER the body is scaled to its target height. See the
        /// note where it is taken: the bind sample alone left the scaling step
        /// unmeasured, which is precisely where a bisect must not have a gap.
        public static float ScaledHeadAboveHips { get; private set; }
        public static float ScaledHipsAboveFeet { get; private set; }
        public static bool ScaledPoseRead { get; private set; }

        /// WHICH BODY THIS PERSON HAS, and it must never change.
        ///
        /// Every `Body_*.prefab` in Resources is one bought mesh.
        /// `CharacterPrefab` writes one per FBX sitting directly in
        /// `Assets/Characters`, so the moment more than one lands the town
        /// stops being sixty people wearing one face.
        ///
        /// Chosen through `Physique.Fraction`, which is the function this
        /// project already uses to make a name mean a body — "the same name is
        /// the same body, always; a city that reshuffles its people on reload
        /// is broken in a way nobody can unsee". A different salt from the
        /// wardrobe's, or everybody in a navy coat would also share a face.
        ///
        /// SORTED, because `Resources.LoadAll` does not promise an order and
        /// an unsorted list would give the same name a different body whenever
        /// a new mesh was added — which is the reshuffle that rule forbids,
        /// arriving through the back door.
        static GameObject[] _bodies;
        public static int BodyChoices { get; private set; }

        /// WHAT COLOUR THE PLAYER'S COAT ACTUALLY CAME OUT, and which band chose
        /// it. Printed rather than argued about.
        ///
        /// WHY. `review_day2_noon` and `review_day5_noon` show the player as a
        /// pale blue-white figure that reads as an undressed mannequin, while
        /// every number in the same run says it is dressed —
        /// `bodyCoatArea=1.000 bodyClothed=True bodyParts=[...->coat ...->coat]`.
        /// Both can be true at once: the meshes ARE painted, and painted a
        /// near-neutral that looks like bare plastic. The coverage metric asks
        /// "is a coat material on every mesh" and answers it correctly; nothing
        /// asks "is that colour a coat".
        ///
        /// So this is a hypothesis being turned into a reading before anything
        /// is changed, which is rule 4: a picture is good evidence something is
        /// wrong and poor evidence of what. Three textures, a bench and a set of
        /// wheels were nearly "fixed" off a JPEG in this project already.
        ///
        /// The street calls the player "someone in a runner's coat" in its own
        /// rumours — the coat is how they are identified — so a protagonist who
        /// rolls stone-grey is a writing problem as much as a rendering one.
        /// That decision waits on this number.
        public static string CoatRead { get; private set; } = "not tried";

        /// WHAT A CROWD OF SKINNED BODIES WOULD COST, measured on the runner
        /// that has to draw it.
        ///
        /// WHY THIS IS THE NEXT THING AND NOT THE CROWD ITSELF. `CharacterRig`
        /// states the blocker in its own words: *"Tier two is still what the
        /// crowd is made of and is not going anywhere until a skinned mesh has
        /// been costed on a GPU-less runner."* That is a measurement nobody had
        /// taken, and swapping fifty walkers over without it is precisely the
        /// "set a threshold you have not measured" habit — with a 28-minute
        /// round trip per guess and a software rasteriser to be wrong on.
        ///
        /// The player is currently the ONLY skinned figure in the city:
        /// `SceneAudit` reads `renderers=9073 skinned=2`, and the bought body
        /// has exactly two meshes. Every one of the fifty walkers is ten boxes
        /// and a sphere, which is what the noon still shows standing next to a
        /// skinned player.
        ///
        /// A SERIES AND NOT A SINGLE READING, for two reasons this project has
        /// paid for. One value cannot separate "skinning is expensive" from
        /// "the runner was busy" — the AO ceiling sat inside its own
        /// instrument's noise for five runs on exactly that mistake. And the
        /// question is not "is it affordable" but "how many", which only a
        /// curve answers.
        ///
        /// THE MEDIAN OF THE ROUNDS, never the max. The AO probe kept a maximum
        /// while its gate bounded a fraction from above, so adding rounds made
        /// it trip on itself. Frame times here are long-tailed on a software
        /// rasteriser — this run reports `meanFrame=266ms` with
        /// `worstFrame=2000ms` — so a mean is a report on the worst hitch and a
        /// median is a report on the frame.
        public static string CostSeries { get; private set; } = "not measured";

        public static void MeasureCrowdCost(Transform near)
        {
            if (near == null) return;
            var prefab = PickBody("player");
            if (prefab == null) { CostSeries = "no body to cost"; return; }

            var line = new System.Text.StringBuilder();
            var spawned = new List<GameObject>();
            int[] counts = { 0, 8, 24, 50 };
            foreach (int want in counts)
            {
                // Bodies accumulate rather than being rebuilt each step, so the
                // instantiate cost lands once per step instead of being charged
                // to every reading after it.
                while (spawned.Count < want)
                {
                    // IN FRONT OF THE CAMERA, WHICH THE FIRST VERSION WAS NOT.
                    //
                    // It spread them on a golden-angle spiral all the way round
                    // the player, and the run showed the instrument up rather
                    // than the subject: n=8 cost 10.5ms, n=24 cost 10.0 and
                    // n=50 cost 10.2 — flat, because most of them were behind
                    // the camera and frustum-culled before anything skinned
                    // them. A cost curve that does not rise with the count is
                    // measuring culling.
                    //
                    // Fanned across the view direction instead, inside roughly
                    // the horizontal field of view, at the distances people are
                    // actually seen at. Now every body added is a body drawn,
                    // which is the number the decision needs.
                    var cam = Camera.main;
                    Vector3 fwd = cam != null ? cam.transform.forward : Vector3.forward;
                    fwd.y = 0f;
                    if (fwd.sqrMagnitude < 1e-4f) fwd = Vector3.forward;
                    fwd.Normalize();
                    var side = new Vector3(fwd.z, 0f, -fwd.x);
                    // Rows of six across, stepping back — a queue at a stall
                    // rather than a wall, and it fills the frame from 4m out.
                    int col = spawned.Count % 6, row = spawned.Count / 6;
                    var at = near.position + fwd * (4f + 2.2f * row)
                                           + side * ((col - 2.5f) * 1.1f);
                    var g = Object.Instantiate(prefab, at, Quaternion.identity);
                    g.name = $"CostBody_{spawned.Count}";
                    spawned.Add(g);
                }

                double ms = MedianFrameMs(5);
                line.Append(line.Length == 0 ? "" : " ")
                    .Append($"n={want}[ms={ms:0.0}]");
            }
            foreach (var g in spawned) if (g != null) Object.Destroy(g);
            CostSeries = line.ToString();
        }

        /// Render `rounds` frames and return the median wall time of one.
        /// `Time.deltaTime` is the frame the ENGINE last completed, which on a
        /// batchmode runner is the honest number — it includes the rasteriser,
        /// which is the whole point of costing skinning here rather than
        /// counting vertices in a spreadsheet.
        static double MedianFrameMs(int rounds)
        {
            var cam = Camera.main;
            if (cam == null) return -1;
            var ms = new List<double>();
            RenderTexture rt = null;
            var prevTarget = cam.targetTexture;
            var prevActive = RenderTexture.active;
            try
            {
                // 1280x720 because that is the size the stills are taken at and
                // therefore the size every judgement about this game is made
                // at. Costing skinning at 640x360 would answer a question
                // nobody asks.
                rt = new RenderTexture(1280, 720, 24, RenderTextureFormat.ARGB32);
                cam.targetTexture = rt;
                for (int i = 0; i < rounds; i++)
                {
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    cam.Render();
                    sw.Stop();
                    ms.Add(sw.Elapsed.TotalMilliseconds);
                }
            }
            catch (System.Exception e) { CostSeries = "render failed: " + e.Message; return -1; }
            finally
            {
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                if (rt != null) { rt.Release(); Object.Destroy(rt); }
            }
            ms.Sort();
            return ms.Count == 0 ? -1 : ms[ms.Count / 2];
        }

        /// HOW BRIGHT THE TEXTURE THE WASH IS MULTIPLYING ACTUALLY IS.
        ///
        /// THE QUESTION THE WASH FIX LEFT OPEN, and it is the only one that
        /// decides whether the anchor is right. `Wardrobe.MaxValue` is 0.46 and
        /// exists so no crowd garment outshines a cast authored at 0.65-0.75.
        /// The wash maps the wardrobe's whole value range onto [0.45, 1.0], so
        /// the BRIGHTEST coat leaves the texture untouched — which is correct
        /// if the texture is a neutral mid-grey and wrong if it is a bright
        /// yellow. The noon still says it is the second: after the wash landed
        /// and measurably worked (near-white cases 39% to 7.7%, median distance
        /// from white 19.1), the two women in front are still in loud yellow
        /// trousers, and no multiply capped at 1.0 can bring a value-0.9 albedo
        /// under a 0.46 ceiling.
        ///
        /// Which means the ceiling of the wash's range is the thing to change,
        /// and it must not be guessed. Rule 2: make the run report the value,
        /// read it, then set it — the same sequence `deedSlotSets` sat ungated
        /// for days waiting for, correctly.
        ///
        /// SUCCESSIVE HALVING RATHER THAN `GetPixels`. Mixamo's textures are
        /// imported non-readable, so reading them on the CPU throws; and a
        /// single blit to a 1x1 target is one bilinear TAP at the centre, not
        /// an average — it would report whatever pixel happens to be in the
        /// middle of the sheet, which for a character atlas is usually a seam.
        /// Halving repeatedly makes each step a 2x2 box filter, so the last one
        /// is a true mean of the whole sheet.
        ///
        /// ONCE PER MATERIAL, cached, because body LOD grants and revokes
        /// bodies continuously and this is a chain of eight blits.
        static readonly Dictionary<int, float> _albedo = new Dictionary<int, float>();

        /// The measured mean value (HSV V, i.e. max channel) of every distinct
        /// albedo the wash has been applied over, and how many there were.
        /// Printed as the series: ten models is short enough to just show, and
        /// a median would hide the one bright sheet that is doing the damage.
        public static readonly List<float> AlbedoValues = new List<float>();

        static float AlbedoValueOf(Texture tex)
        {
            if (tex == null) return -1;
            int key = tex.GetInstanceID();
            if (_albedo.TryGetValue(key, out float cached)) return cached;

            float v = -1;
            RenderTexture a = null, b = null;
            var prevActive = RenderTexture.active;
            try
            {
                int size = 64;
                a = RenderTexture.GetTemporary(size, size, 0, RenderTextureFormat.ARGB32);
                Graphics.Blit(tex, a);
                while (size > 1)
                {
                    size /= 2;
                    b = RenderTexture.GetTemporary(size, size, 0, RenderTextureFormat.ARGB32);
                    Graphics.Blit(a, b);
                    RenderTexture.ReleaseTemporary(a);
                    a = b;
                    b = null;
                }
                RenderTexture.active = a;
                var one = new Texture2D(1, 1, TextureFormat.RGBA32, false);
                one.ReadPixels(new Rect(0, 0, 1, 1), 0, 0);
                one.Apply();
                var c = one.GetPixel(0, 0);
                Object.Destroy(one);
                // VALUE, not luminance. The wash is an HSV rule and
                // `Wardrobe.MaxValue` is an HSV V, so the albedo has to be read
                // on the same axis or the comparison is two scales again — the
                // fault `Press.Print` shipped with a testimony grade against a
                // pressure aggregate.
                v = Mathf.Max(c.r, Mathf.Max(c.g, c.b));
            }
            catch (System.Exception) { v = -1; }
            finally
            {
                RenderTexture.active = prevActive;
                if (a != null) RenderTexture.ReleaseTemporary(a);
                if (b != null) RenderTexture.ReleaseTemporary(b);
            }
            _albedo[key] = v;
            if (v >= 0) AlbedoValues.Add(v);
            return v;
        }

        /// WHICH MODEL A NAME WEARS, ASKABLE WITHOUT ATTACHING ONE.
        ///
        /// Eight prefabs against forty-three named people is the sameness
        /// problem in one sentence (ten minus the two rig mannequins, since
        /// 15 Aug), and it has never had a number — `bodyChoices` says how
        /// many models EXIST, which is not the question. The question
        /// is how many DISTINCT ones are in the frame, and answering it needs
        /// the pick for a walker the reader is not attaching.
        ///
        /// A FUNCTION OF THE NAME AND NOTHING ELSE, going through the same
        /// `PickBody` the attach uses. The alternative — recording the pick on
        /// a static as bodies attach — walks straight into the save-and-restore
        /// set that puts the player's readings back after every walker, and
        /// would answer with the player's model at unpredictable moments. It is
        /// also rule 1's third corollary waiting to happen: one idea, two
        /// implementations, and the drift is invisible because both return a
        /// plausible model name.
        public static string ModelNameFor(string wearer)
        {
            var p = PickBody(wearer);
            return p != null ? p.name : "none";
        }

        /// THE RIG MANNEQUINS ARE NOT PEOPLE, and until 15 Aug a fifth of the
        /// street was them: `X Bot` and `Y Bot` are Mixamo's grey untextured
        /// stand-ins, they ride along in `Assets/Characters` because the
        /// animation clips were retargeted through them, and nothing anywhere
        /// excluded them from being WORN. Two of ten pool slots, so with
        /// twelve bodies on screen at once, two greys in frame was the
        /// expected case, not the unlucky one.
        ///
        /// ONE IMPLEMENTATION, TWO CALLERS, on purpose: `CharacterPrefab`
        /// (Editor) asks this before writing a prefab, and `PickBody` asks it
        /// again before pooling one — so a mannequin prefab left behind by an
        /// older build still cannot reach the street. Accepts either spelling
        /// ("X Bot" the model, "Body_XBot" the prefab) so the two callers
        /// cannot drift apart on normalisation.
        public static bool IsMannequin(string modelOrPrefabName)
        {
            if (string.IsNullOrEmpty(modelOrPrefabName)) return false;
            var n = modelOrPrefabName.Replace(" ", "");
            if (n.StartsWith("Body_")) n = n.Substring("Body_".Length);
            return string.Equals(n, "XBot", System.StringComparison.OrdinalIgnoreCase)
                || string.Equals(n, "YBot", System.StringComparison.OrdinalIgnoreCase);
        }

        static GameObject PickBody(string wearer)
        {
            if (_bodies == null)
            {
                var all = Resources.LoadAll<GameObject>("Characters");
                var list = new System.Collections.Generic.List<GameObject>();
                foreach (var g in all)
                    if (g != null && g.name.StartsWith("Body_") && !IsMannequin(g.name))
                        list.Add(g);
                list.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
                _bodies = list.ToArray();
                BodyChoices = _bodies.Length;
                // EVERY MODEL AND THE GAIT IT DREW, once, here — this block
                // runs exactly on the first pick. A run that reports
                // `walkFemale=0/0` cannot say whether the pool holds no women
                // or whether six women were classified as men, and those want
                // opposite next actions; the roster is the denominator that
                // separates them.
                var stems = new string[_bodies.Length];
                for (int b = 0; b < _bodies.Length; b++)
                    stems[b] = StemOf(_bodies[b].name);
                ArchetypeRead = Ledger.Core.BodyArchetype.Roster(stems);
            }
            if (_bodies.Length == 0)
                return Resources.Load<GameObject>("Characters/Body");
            double f = Ledger.Core.Physique.Fraction(wearer ?? "player", 23);
            int i = Mathf.Clamp((int)(f * _bodies.Length), 0, _bodies.Length - 1);
            return _bodies[i];
        }

        /// EIGHT MODELS, FORTY-THREE NAMED PEOPLE — SO THEY MUST NOT BE THE
        /// ONLY THING THAT TELLS THEM APART.
        ///
        /// COUNTED, NOT JUDGED FROM THE STILL. There are eight body prefabs
        /// (ten FBX minus the two rig mannequins) and the cast is forty-three,
        /// with twelve worn at once, so by pigeonhole at least two people on
        /// screen share a model at all times. The noon
        /// frame shows it plainly: two women in the same yellow trousers with
        /// the same hair, one of them the player.
        ///
        /// AND THE CAUSE IS A CHANGE THAT LANDED THIS MORNING. Before texture
        /// extraction, every renderer arrived untextured, so the wardrobe
        /// painted all of them and the street was varied — flat, but varied.
        /// Extraction gave the models their own textures, `Kept` took them, and
        /// the paint loop below stopped running at all: `bodyParts=[nothing to
        /// paint — all 1 renderer(s) came textured]`. The wardrobe was
        /// disconnected by a fix to something else, which is rule 1's second
        /// corollary happening to a SYSTEM rather than to a comment.
        ///
        /// SO THE TEXTURE STAYS AND THE WARDROBE COMES BACK AS A WASH.
        ///
        /// AND THE FIRST VERSION OF THAT SENTENCE WAS WRONG FOR A THIRD OF THE
        /// CITY. It read: "the band's own hue at half saturation and full
        /// value: multiplying an albedo by that shifts its colour clearly and
        /// darkens it barely". The second clause is true. The first is true of
        /// denim and false of black and grey, which share a hue range, both sit
        /// at saturation 0.02-0.10, and are told apart by VALUE — the one axis
        /// `1f` threw away. Over the real roster, 39% of people washed to
        /// within 5% of white, and a multiply by white is the identity.
        ///
        /// That is a comment being a claim with no test attached, and the claim
        /// decayed the moment somebody asked it about a band it was not written
        /// for. The rule now lives in `Core/Wardrobe.Wash`, with the measured
        /// series beside it and a CoreTest holding both ends — the darkest coat
        /// separating from the brightest, and the brightest not being dimmed.
        ///
        /// NO NEW COLOUR. `ch`, `cs` and `cv` are what `Wardrobe` already chose
        /// for this person, deterministic per name, and the same triple the
        /// coat material is built from twenty lines above — which is the point:
        /// the two paths were reading different parts of one decision.
        ///
        /// AND SINCE THE GARMENT SPLIT LANDED IT IS TWO DRAWS FROM THAT SAME
        /// TABLE, NOT A SECOND PALETTE. The upper garment takes the coat's
        /// triple and the lower garment takes `Wardrobe.Dress` again under its
        /// own salt — same eight authored bands, same `MaxValue` ceiling, same
        /// `Mix` fold. Nothing here invents a colour, and the sentence above
        /// stays true of each draw separately; what changed is HOW MANY of them
        /// reach one body.
        ///
        /// A PROPERTY BLOCK RATHER THAN `r.material`. Touching `.material`
        /// instantiates a copy per renderer that Unity never reclaims, and body
        /// LOD grants and revokes bodies continuously — the last run made 1,486
        /// grants, so that is a leak with a multiplier on it rather than a
        /// tidiness preference.
        static readonly int TintId = Shader.PropertyToID("_Color");
        static MaterialPropertyBlock _tint;
        /// NOT IN THE SAVE-AND-RESTORE SET, AND IT WAS, WHICH IS WHY IT READ 1.
        ///
        /// `TryAttachExtra` snapshots every static this class publishes and puts
        /// them back, so that attaching a walker's body cannot rewrite the five
        /// gate clauses that describe THE PLAYER. I added this counter to that
        /// set by reflex and the build said what it costs: `bodyTinted=1`
        /// against 1,586 body attachments. Every walker's tint was restored
        /// away the instant it happened, so the number described the player and
        /// only the player.
        ///
        /// It does not belong there, because it is not a statement ABOUT a
        /// body — it is a lifetime count of how many renderers have been
        /// washed. The rule for that set is "does a gate read this as being
        /// about the player", and nothing reads this at all except the verdict.
        ///
        /// AND THE POPULATION IT COUNTS CHANGED UNDER IT, WHICH THE NAME DOES
        /// NOT SAY AND A SERIES-READER CANNOT SEE. Until the garment split,
        /// `Tint` was called on every kept textured renderer on the body —
        /// face, hair, shoes and all. It is now called only on the meshes the
        /// wardrobe dresses: upper garment, lower garment, welded whole body.
        /// The rest are counted by `OwnEver`. So `bodyTinted` and the whole
        /// `bodyWash*` family below describe CLOTH from `e72f58a3` onward, and
        /// the fall in their landed series is the fix rather than a regression.
        /// `WashPopulation` below is that sentence in a form the done line can
        /// carry; this paragraph is for whoever is reading the code instead.
        ///
        /// CUMULATIVE OVER THE RUN, and over renderer-washes rather than over
        /// people: body LOD grants and revokes continuously, so one walker
        /// washed four times is four here.
        public static int Tinted { get; private set; }

        /// WHICH POPULATION THE WASH NUMBERS ARE ABOUT, AS A VALUE RATHER THAN
        /// A COMMENT — because a commit message is not on the done line, and
        /// the next person reading the series will not be reading it.
        ///
        /// `bodyTinted`, `bodyWashWhite`, `bodyWashSampled`, `bodyWashNone` and
        /// `bodyWashUnreached` all changed population at `e72f58a3` and not one
        /// of them changed name. That is the drift `liveArmDrop`,
        /// `nameTagsOffered` and `crowdSpeed` each paid for: the instrument does
        /// not move when the system does, so a working fix reads as a regression
        /// and the number that would have said so reads as agreement.
        ///
        /// THE SERIES IT IS ABOUT TO BREAK, PRINTED BEFORE THE CLAIM WAS MADE.
        /// Over the newest 20 landed runs, min / median / max:
        ///
        ///     bodyTinted     2739 / 3054 / 3219   (bodyKeptEver: identical)
        ///     bodyWashNone    258 /  308 /  339
        ///
        /// All-time over 200 landed runs is 1 / 2699 / 6497 and describes no
        /// single regime — the model pool itself went 2, 5, 6, 8, 10, 14 — so
        /// the recent window is the honest baseline here and the all-time
        /// median is not.
        ///
        /// AND THE TWO SCHEMAS ARE BRIDGED, not merely incomparable, which is
        /// worth more than a warning. Every kept textured renderer goes to
        /// exactly one of four branches in the paint loop; three of them wash
        /// and the fourth is `OwnEver`. So schema 2 satisfies
        /// `bodyTinted + bodyPartsOwn == bodyKeptEver`, and schema 1 satisfied
        /// `bodyTinted == bodyKeptEver` — which holds in 196 of the 196 landed
        /// runs carrying both keys, checked rather than assumed. A reader
        /// crossing the boundary adds `bodyPartsOwn` back on and has one series
        /// again.
        ///
        /// NO SPACES, `/` AND `..` FOR STRUCTURE, AND NO `=` INSIDE THE VALUE:
        /// `tools/verdict-keys.py` harvests key names with `([A-Za-z]\w*)=`
        /// over the bracket-stripped line, so an `=` in a value invents a key
        /// that exists nowhere and the inventory check goes off on it.
        ///
        /// NOTHING EMITS THIS YET, WHICH IS RULE 6 AND IS SAID RATHER THAN
        /// LEFT TO BE FOUND. `SimDirector` owns the done line and is another
        /// agent's file this cycle; the single line it needs is named in
        /// `game-design/agent-reports/body-readings-fix.md`. Until it lands,
        /// the boundary is documented in code and invisible in the verdict.
        public const string WashPopulation =
            "schema2/cloth-only..schema1/all-kept-textured/bridge-tinted+partsOwn-is-keptEver";

        /// HOW MUCH WARDROBE ACTUALLY ARRIVES, and it is the reading that was
        /// missing rather than a decoration.
        ///
        /// `Tinted=5334` was true and meant nothing. It counts renderers the
        /// wash was APPLIED to, and a wash of pure white is applied just as
        /// successfully as any other — so the counter proving the system ran
        /// could not distinguish it running from it doing nothing, which is
        /// rule 3b with the denominator present and the wrong quantity counted.
        ///
        /// This is the distance of each applied wash from white, 0..100, where
        /// zero means that person's coat changed no pixel. Kept as a list so
        /// the MEDIAN is available: a peak would answer "did anybody's wardrobe
        /// ever show", which is not the question the noon still asks, and a
        /// mean would let one shellsuit carry two hundred people in black.
        ///
        /// CAPPED, AND THE CAP SAYS WHEN IT BITES. Body LOD grants and revokes
        /// continuously, so this would otherwise grow with the run rather than
        /// with the city. Past the cap it stops sampling and `WashSampled`
        /// stays below `Tinted`, which is the difference between "measured
        /// everything" and "measured the first twenty thousand" being legible
        /// instead of assumed.
        const int WashCap = 20000;
        static readonly List<float> _washes = new List<float>();
        public static int WashSampled => _washes.Count;

        /// The median distance from white, or -1 when nothing was washed —
        /// which must not read as "the wash is perfectly white", the exact
        /// confusion `ContrastWorst` shipped with.
        public static double WashFromWhite
        {
            get
            {
                if (_washes.Count == 0) return -1;
                var c = new List<float>(_washes);
                c.Sort();
                return c[c.Count / 2];
            }
        }

        /// How many people's wardrobe reaches the eye as nothing at all.
        ///
        /// AND THE QUESTION THIS ANSWERS MOVED UNDER IT WITHIN THE HOUR, which
        /// is the fault CLAUDE.md lists three separate instances of and I have
        /// now shipped the change that causes a fourth.
        ///
        /// Under the old rule a wash near white meant the wardrobe had failed
        /// to arrive, and 39% of the roster was that. Under the anchored rule a
        /// wash of exactly 1.0 is the CORRECT answer for a sheet already darker
        /// than the band wants — a multiply cannot lift it, so leaving it alone
        /// is right. The count duly went 303 to 446 on the build that fixed the
        /// thing it was measuring, and read as a regression.
        ///
        /// Kept, because "how much colour is imposed" is still worth knowing,
        /// and paired with the number that answers the question the old one
        /// used to: `WashUnreached` counts the people whose sheet is too dark
        /// for their band, so they render below the wardrobe rather than at it.
        /// That is the honest residue of the anchored rule and it is a
        /// different fault from the one this used to catch.
        public static int WashNearWhite { get; private set; }

        /// People rendering DARKER than the band the wardrobe chose, because
        /// the sheet they are painted on is darker than the band and a multiply
        /// only subtracts. Not a bug in the wash — the wash did the only thing
        /// available — but a real limit on how much of the palette can reach
        /// the street, and the number that says whether it matters.
        public static int WashUnreached { get; private set; }

        /// How many bodies got the cast's brightness lift and how many did not.
        /// Lifetime, and NOT in the save-and-restore set: these are counts of
        /// what happened to the city, not statements about the player.
        ///
        /// `LiftedCrowd` COUNTS THE CROWD BODIES THAT WERE **NOT** LIFTED, and
        /// the comment here said the opposite until 2026-08-18: *"non-zero is
        /// the fault this pair was added to prove was fixed"*. That was true
        /// while `TryAttachExtra` lifted everybody. The `cast` flag below fixed
        /// it, and the moment it did, non-zero became the CORRECT reading —
        /// `bodyLiftedCrowd=161` says a hundred and sixty-one crowd bodies were
        /// properly left under `Wardrobe.MaxValue`, not that a hundred and
        /// sixty-one are illegally bright.
        ///
        /// So the pair reads: `LiftedCast` bodies got the cast's brightness
        /// lift, `LiftedCrowd` bodies correctly did not. Zero of BOTH still
        /// means no body was dressed at all, which is what the original
        /// sentence was reaching for and is the only part of it that survived.
        ///
        /// THE NAME IS KEPT DESPITE BEING WRONG, and that is a deliberate
        /// trade rather than laziness: `bodyLiftedCrowd` is a landed verdict
        /// key with a history behind it, and this project has already paid for
        /// losing a measurement's series. The name is wrong; this paragraph is
        /// the fix, and it is the same fault CLAUDE.md files under "a number
        /// keeps its name when the question it answers moves".
        public static int LiftedCast { get; private set; }
        public static int LiftedCrowd { get; private set; }

        /// HOW MANY MESHES ON THE LAST BODY WENT WHICH WAY. Per body,
        /// LAST-WINS — they are reset at the top of every attach and describe
        /// whichever body attached most recently, exactly like `Skinned` and
        /// `Dressed` beside them. Do not read them as a description of the
        /// city; `SplitBodies` and its family below are the cumulative pair.
        public static int PartsUpper { get; private set; }
        public static int PartsLower { get; private set; }
        public static int PartsWhole { get; private set; }
        public static int PartsOwn { get; private set; }

        /// THE NUMBER THAT PROVES THE SPLIT REACHED THE STREET.
        ///
        /// `SplitBodies` counts bodies that got an upper garment draw AND a
        /// lower garment draw — a navy coat over stone trousers, which is the
        /// thing that could not happen before this wire. `DressedBodies` is its
        /// denominator: bodies on which the wardrobe washed anything at all.
        /// The two off-diagonal cases are named rather than summed away, so a
        /// fall in the split reads as WHICH kind of model turned up rather than
        /// as a mystery:
        ///
        ///   `WeldedBodies`    one mesh carrying clothes and skin together —
        ///                     James, Michelle, Big Vegas, Sporty Granny. They
        ///                     take the coat draw over the whole figure, which
        ///                     is what every body did before the split, so
        ///                     these are correct rather than missed.
        ///   `UpperOnlyBodies` a garment mesh for the top and none for the
        ///                     bottom — Sophie's `Ch02_Cloth` is the only one
        ///                     on today's roster.
        ///
        /// SplitBodies + WeldedBodies + UpperOnlyBodies == DressedBodies, by
        /// construction, so a reader can check the arithmetic on the done line.
        ///
        /// CUMULATIVE over the whole run, counted per ATTACH rather than per
        /// person: body LOD grants and revokes continuously, so a walker who is
        /// granted a body four times is counted four times. That makes this a
        /// count of dressing EVENTS, not of citizens — the same statistic
        /// `Tinted` is, and named here because a lifetime count read as a
        /// population is a mistake this file has already made once.
        ///
        /// NOT in the save-and-restore set, for `Tinted`'s reason.
        public static int SplitBodies { get; private set; }
        public static int WeldedBodies { get; private set; }
        public static int UpperOnlyBodies { get; private set; }
        public static int DressedBodies { get; private set; }

        /// Renderers left carrying the artist's own texture — faces, hair,
        /// shoes, props. Cumulative. The denominator for "the split left
        /// something alone" as against "the split never ran": zero of these
        /// beside a non-zero `Tinted` means every mesh got washed, which is
        /// the state this change exists to end.
        public static int OwnEver { get; private set; }

        /// Renderer names no word list recognised, DISTINCT and capped.
        ///
        /// Rule 3b, pointed at a vocabulary rather than a count. A Mixamo drop
        /// whose garments are called something nobody has listed renders
        /// exactly like a welded model — one colour over the whole figure —
        /// and nothing about the frame or the split count says which happened.
        /// This is the line that tells them apart, and it is why the word lists
        /// in `BodyParts` contain no invented synonyms: the next drop's
        /// vocabulary arrives here as a reading.
        ///
        /// `Ch03` and `Ch06` are expected members — Michelle and James ship one
        /// unnamed welded mesh each, and their names genuinely carry no
        /// information. Anything else in this list is a model whose garments
        /// are not being split.
        const int UnknownCap = 24;
        static readonly List<string> _unknownParts = new List<string>();
        public static int UnknownParts => _unknownParts.Count;
        public static string UnknownRead
        {
            get
            {
                if (_unknownParts.Count == 0)
                    return $"none of {KeptEver} textured renderer(s)";
                var b = new System.Text.StringBuilder();
                for (int i = 0; i < _unknownParts.Count && i < UnknownCap; i++)
                    b.Append(i == 0 ? "" : " ").Append(_unknownParts[i]);
                if (_unknownParts.Count > UnknownCap)
                    b.Append($" (+{_unknownParts.Count - UnknownCap} more not shown)");
                return b.ToString();
            }
        }

        /// THE MODEL NAME UNDERNEATH A PREFAB NAME. `CharacterPrefab` writes
        /// `Body_{stem}` with the FBX's spaces stripped, so `Sporty Granny`
        /// arrives as `Body_SportyGranny` and the archetype rule has to split
        /// the camel hump back out — which is exactly what `BodyParts.Words`
        /// does. The bare `Body` fallback prefab has no stem and returns empty,
        /// which classifies as `default`: correct, since that prefab is a copy
        /// of whichever model was marked default.
        static string StemOf(string prefabName)
        {
            if (string.IsNullOrEmpty(prefabName)) return "";
            const string pre = "Body_";
            return prefabName.StartsWith(pre) ? prefabName.Substring(pre.Length) : "";
        }

        /// HOW MANY WOMEN ARE ON THE FEMALE WALK CYCLE, and out of how many.
        ///
        /// `FemaleWalkers` counts body attachments whose model is a woman AND
        /// whose Animator arrived holding a `female` controller.
        /// `FemaleBodies` is the denominator: attachments whose model is a
        /// woman, whatever controller turned up. Both CUMULATIVE over the run
        /// and read on the done line, never inside a screenshot hook — a
        /// lifetime count sampled by a sparse sampler freezes at the last
        /// sample, which this project has already paid for once.
        ///
        /// `FemaleWalkers` BELOW `FemaleBodies` is the interesting state and it
        /// is the one the silent fallback produces: `BuildLocomotion` falls
        /// back to `walk` when `walk_f` cannot be found, and a body walking the
        /// male cycle looks completely normal. Equality is the wire holding.
        /// Both zero means the pool has no women in it, which `ArchetypeRead`
        /// is there to confirm or deny.
        ///
        /// NOT in the save-and-restore set, for `Tinted`'s reason: they are
        /// counts of what happened to the city, not statements about the
        /// player.
        public static int FemaleBodies { get; private set; }
        public static int FemaleWalkers { get; private set; }

        /// Every model in the pool and the archetype it drew, slash-separated.
        ///
        /// WRITE-ONCE OVER THE POOL. Not last-wins, and not a reading about any
        /// body: it is assigned inside `PickBody`'s `_bodies == null` block,
        /// which runs exactly once per process for the whole pool, so whichever
        /// attach happened to trigger the load cannot change what it says. An
        /// FBX nobody classified shows up here as a `default` beside a name a
        /// reader can recognise, and the initialiser `no pick yet` is the
        /// never-ran case — which must stay distinguishable from a pool that
        /// loaded empty, and is: `Roster` answers that one `no models offered`.
        ///
        /// DELIBERATELY NOT IN THE SAVE-AND-RESTORE SET, AND THAT IS NOT THE
        /// SAME DECISION AS `TrouserRead`'s BELOW. Restoring this would break
        /// it rather than repair it. `TryAttachExtra` snapshots BEFORE the
        /// attach, so if the first body ever picked belongs to a walker, the
        /// snapshot holds the initialiser, the roster is written during the
        /// attach, and the restore puts the initialiser back — permanently,
        /// because the load block never runs a second time. `BodyChoices` IS in
        /// that set and carries exactly that latent order-dependency today; it
        /// reads 14 across the newest 20 landed runs, so the player is in fact
        /// attaching first, which is an ordering rather than a guarantee.
        /// The subject of this key is the POOL, and the pool is not the player.
        public static string ArchetypeRead { get; private set; } = "no pick yet";

        /// The three fields `ControllerRead` is folded from, all cumulative
        /// over attachments and none of them read anywhere else. Private,
        /// because a denominator that can be quoted away from its numerator
        /// eventually is.
        static int _controllerReads, _controllerMissed;
        static string _controllerWitness = "";

        /// WHICH CONTROLLER ASSET TURNED UP ON A BODY WHOSE ARCHETYPE IT DOES
        /// NOT CARRY, AND HOW MANY ATTACHMENTS WERE LIKE THAT.
        ///
        /// WHAT IT WAS: a LAST-WINS string, assigned on every attach and not in
        /// the save-and-restore set, so it described whichever walker the LOD
        /// happened to dress last while sitting on the done line between
        /// `bodyKinds` (the pool) and `bodyCoat` (the player), describing
        /// neither. That is `namesTracked=2` again — a last-wins field read as
        /// a summary — and it has never landed, so no series is being moved.
        ///
        /// THE SUBJECT IS THE POPULATION, SO THE REPAIR IS A SHAPE AND NOT A
        /// RESTORE. Its job, by its own previous comment, is the qualitative
        /// half of `walkFemale=n/total`: the count is wrong, which asset turned
        /// up. No single string can answer that about a population however it is
        /// captured, and "is ANYBODY on the wrong cycle" is never a last-wins
        /// question — it is a witness plus a count plus the denominator both
        /// were taken over.
        ///
        /// SO IT IS THREE FACTS IN ONE VALUE, CUMULATIVE OVER EVERY ATTACHMENT
        /// AND COMPUTED WHERE THE RUN ENDS rather than assigned during it. A
        /// getter cannot be last-wins by construction; a cumulative number
        /// captured inside whatever function was convenient is how
        /// `namesManagedEver` froze at the last screenshot.
        ///
        ///   nothing-measured           no attachment has reached the read at
        ///                              all — the never-ran case, and it may
        ///                              not read as "all fine"
        ///   allCarried/0of1586         every attachment's controller carried
        ///                              its archetype, with the denominator
        ///                              beside the zero on the same key at the
        ///                              same instant
        ///   Kate:female->Body/3of1586  the FIRST mismatching attachment —
        ///                              model, archetype, and the asset the
        ///                              Animator actually held — then how many
        ///                              attachments mismatched, over how many
        ///                              were read
        ///
        /// FIRST-WINS FOR THE WITNESS, deliberately: once set it never moves,
        /// so the qualitative half stops depending on LOD ordering, and the
        /// COUNT beside it is what says how widespread the fault is. Both
        /// halves and their denominator come off the same three fields at the
        /// same moment, so they cannot be two instants read as one.
        ///
        /// NOT IN THE SAVE-AND-RESTORE SET, for `Tinted`'s reason: a count of
        /// what happened to the city is not a statement about the player, and
        /// restoring one after every walker is what made `bodyTinted` read 1
        /// against 1,586 attachments.
        public static string ControllerRead =>
            _controllerReads == 0 ? "nothing-measured"
            : _controllerMissed == 0 ? $"allCarried/0of{_controllerReads}"
            : $"{_controllerWitness}/{_controllerMissed}of{_controllerReads}";

        /// WHAT THE PLAYER'S LOWER GARMENT CAME OUT, band and HSV — `CoatRead`'s
        /// twin for the second wardrobe draw, and the same subject as it.
        ///
        /// LAST-WINS WITHIN ONE ATTACH, SAVED AND RESTORED ACROSS WALKERS, so
        /// what survives to the done line is the PLAYER's trousers, exactly as
        /// `bodyCoat` two keys along is the player's coat. It shipped outside
        /// the save-and-restore set and therefore described whichever walker
        /// the LOD dressed last, among neighbours that are about the player —
        /// which is the precise fault `TryAttachExtra` exists to prevent,
        /// reappearing in a field added after it was written. Never landed, so
        /// nothing in the history is being reinterpreted.
        ///
        /// THE POPULATION QUESTION IS NOT THIS KEY'S. "What is the street
        /// wearing" is answered by `bodyPartsDistinct` and the `bodyWash*`
        /// family, which are cumulative and correctly OUTSIDE the set. This is
        /// the third fact that settles a still showing one hue per figure
        /// against a number saying two draws happened.
        ///
        /// SLASHED RATHER THAN SPACED, unlike `CoatRead`, and the divergence is
        /// deliberate: a verdict value may not contain a space, `bodyCoat` has
        /// carried one since it landed, and reformatting it now would put a
        /// silent boundary through a series with 196 landed runs behind it for
        /// a cosmetic gain. The new key gets the rule; the old one gets a note
        /// in the report. `nothing-measured` is the never-ran case and is the
        /// same state `bodyCoat` spells `not tried`.
        public static string TrouserRead { get; private set; } = "nothing-measured";

        /// The last wash actually written to a renderer, with the albedo it
        /// was anchored against. Appended to `CoatRead` after the paint loop,
        /// because the wash is not knowable before it.
        ///
        /// ITS POPULATION MOVED AT `e72f58a3` TOO, and `bodyCoat` carries it
        /// without saying so. `Tint` used to run on every kept textured
        /// renderer, so this was the last of those — a face or a shoe as often
        /// as a garment. `Tint` now has exactly three callers, all inside the
        /// garment switch, so it is the last GARMENT wash. That is the reading
        /// `bodyCoat` always wanted and it is still a change of subject under
        /// an unchanged name; recorded here because the value is qualitative
        /// and has no series a gate could trip on, which is the only reason it
        /// is a comment rather than a mark on the line.
        static string _lastWash = "none applied";

        static void Tint(Renderer r, double hue, double saturation, double value,
                         double albedo)
        {
            if (r == null) return;
            if (_tint == null) _tint = new MaterialPropertyBlock();
            Ledger.Core.Wardrobe.Wash(hue, saturation, value, albedo,
                                      out double wh, out double ws, out double wv);
            var c = Color.HSVToRGB((float)wh, (float)ws, (float)wv);
            r.GetPropertyBlock(_tint);
            // CONVERTED BY HAND IN LINEAR, because a MaterialPropertyBlock
            // colour skips the gamma->linear conversion Material.SetColor
            // performs — a known Unity asymmetry, and the V1.5 flip turned
            // it into a live fault: every wash multiplier the wardrobe
            // computes in display terms was being applied raw in linear,
            // so a 0.46 wash darkened to ~0.63 on screen and the whole
            // wardrobe quietly weakened. The palest-body catcher reading
            // real bodies at 213-223 luma against a crowd median of ~20 is
            // this asymmetry plus a near-white sheet the wash is anchored
            // not to touch.
            _tint.SetColor(TintId,
                QualitySettings.activeColorSpace == ColorSpace.Linear ? c.linear : c);
            r.SetPropertyBlock(_tint);
            Tinted++;

            // A MULTIPLY BY WHITE IS THE IDENTITY, so distance from white is
            // exactly how much of the wardrobe survives to the frame. Plain RGB
            // rather than a perceptual space, because the multiply itself
            // happens in RGB and the question is what the shader does.
            float d = Mathf.Sqrt(((1f - c.r) * (1f - c.r)
                                  + (1f - c.g) * (1f - c.g)
                                  + (1f - c.b) * (1f - c.b)) / 3f) * 100f;
            if (d < 5f) WashNearWhite++;
            // The sheet was already darker than the band asked for, so the
            // garment lands below the wardrobe rather than on it.
            if (albedo > 0 && albedo < value) WashUnreached++;
            _lastWash = $"{(int)(c.r * 255)},{(int)(c.g * 255)},{(int)(c.b * 255)}"
                        + $" on albedo {albedo:0.00}";
            if (_washes.Count < WashCap) _washes.Add(d);
        }

        /// The mesh a renderer draws, whether it is skinned or not. One reader,
        /// because the body has both kinds and two lookups would eventually
        /// disagree about which meshes count.
        static Mesh MeshOf(Renderer r)
        {
            if (r is SkinnedMeshRenderer smr) return smr.sharedMesh;
            var mf = r != null ? r.GetComponent<MeshFilter>() : null;
            return mf != null ? mf.sharedMesh : null;
        }

        static int VertexCount(Renderer r)
        {
            var m = MeshOf(r);
            return m != null ? m.vertexCount : 0;
        }

        /// Total triangle area of a renderer's mesh, in the mesh's own units.
        ///
        /// Local space deliberately, and not world: every renderer on this body
        /// shares one root scale, so a uniform factor cancels in the FRACTION
        /// that is the only thing anybody reads. Doing it in world space would
        /// add a per-vertex transform to a loop over fifty thousand triangles
        /// for a number that comes out identical.
        static double SurfaceArea(Renderer r)
        {
            var mesh = MeshOf(r);
            if (mesh == null) return 0;
            var verts = mesh.vertices;
            var tris = mesh.triangles;
            if (verts == null || tris == null) return 0;
            double sum = 0;
            for (int i = 0; i + 2 < tris.Length; i += 3)
            {
                int a = tris[i], b = tris[i + 1], c = tris[i + 2];
                if (a >= verts.Length || b >= verts.Length || c >= verts.Length) continue;
                // Half the cross product's magnitude — the triangle's area, and
                // the only definition of "how much of this person" that does
                // not depend on how finely somebody chose to tessellate a face.
                sum += Vector3.Cross(verts[b] - verts[a], verts[c] - verts[a]).magnitude * 0.5;
            }
            return sum;
        }

        /// One reader for both samples, so the two cannot measure subtly
        /// different things. A bisect whose arms disagree proves nothing.
        static bool ReadBoneSpan(GameObject body, out float headAboveHips, out float hipsAboveFeet)
        {
            headAboveHips = hipsAboveFeet = 0f;
            var anim = body != null ? body.GetComponentInChildren<Animator>() : null;
            if (anim == null || !anim.isHuman) return false;
            var hips = anim.GetBoneTransform(HumanBodyBones.Hips);
            var head = anim.GetBoneTransform(HumanBodyBones.Head);
            var lf = anim.GetBoneTransform(HumanBodyBones.LeftFoot);
            var rf = anim.GetBoneTransform(HumanBodyBones.RightFoot);
            if (hips == null || head == null || (lf == null && rf == null)) return false;
            float sole = lf != null && rf != null
                ? Mathf.Min(lf.position.y, rf.position.y)
                : (lf != null ? lf.position.y : rf.position.y);
            headAboveHips = head.position.y - hips.position.y;
            hipsAboveFeet = hips.position.y - sole;
            return true;
        }

        public static void ResetCounters()
        {
            Attached = 0;
            Why = "not tried";
        }

        /// Put a skinned body under `host`, or return false and leave the caller
        /// to build a `Mannequin`.
        ///
        /// The prefab is written by `Editor/CharacterPrefab` at build time and
        /// carries an `Animator` whose avatar is the model's own — which is
        /// precisely what `CharacterRig.Bind` looks for.
        /// EVERY STATIC THIS CLASS PUBLISHES, saved and put back — so a body
        /// that is not the player's can be attached without rewriting the
        /// player's readings.
        ///
        /// WHY THIS HAS TO EXIST BEFORE A SINGLE WALKER GETS A REAL BODY.
        /// `TryAttach` writes `Attached`, `Why`, `Upright`, `Skinned`,
        /// `Dressed`, `Kept`, `Parts`, the two garment reads `CoatRead` and
        /// `TrouserRead`, the coverage fractions and the bind and scaled pose
        /// readings. FIVE clauses of the sim's `bodies` gate read those, and
        /// the entire point of every one of them is that it describes THE
        /// PLAYER — is HE upright, is HE dressed, is HE not still a capsule.
        /// Attach fifty-five walkers and all five quietly become about
        /// whichever walker attached last, with nothing anywhere saying so. A
        /// corrupted gate reads exactly like a passing one.
        ///
        /// THE MEMBERSHIP RULE, BECAUSE THE LIST HAS BEEN GOT WRONG IN BOTH
        /// DIRECTIONS AND THE TWO FAULTS LOOK NOTHING ALIKE. In goes anything
        /// that is a STATEMENT ABOUT ONE BODY, because the body the done line
        /// means is the player's: the pose readings, the coverage fractions,
        /// `CoatRead`, and `TrouserRead` — which was added a cycle after this
        /// comment and left out, so it described whichever walker was dressed
        /// last. Out stays anything CUMULATIVE OVER THE CITY — `Tinted`,
        /// `KeptEver`, `OwnEver`, `PartsUpper` and the rest — because restoring
        /// a lifetime count after every walker is what made `bodyTinted` read 1
        /// against 1,586 attachments. And out stays anything WRITE-ONCE about
        /// the POOL: `ArchetypeRead` is written on the first pick only, so a
        /// snapshot taken before that pick would restore the initialiser
        /// permanently. `BodyChoices` is in the set and has that hazard live.
        ///
        /// SNAPSHOT AND RESTORE RATHER THAN A GUARD AT EACH WRITE. The writes
        /// are scattered through the body of `TryAttach` rather than gathered
        /// behind helper calls, so guarding them one by one is wide and easy to
        /// do four-fifths of. This is one place to read and one place to review,
        /// and the field list is the same either way.
        ///
        /// `Attached` is restored too, deliberately. The gate reads
        /// `Attached == 0 || Upright > 0.9` — "if a body attached it must be
        /// upright" — and it means the PLAYER's body. Letting walkers increment
        /// it would keep the clause true while changing which body it is about.
        struct Published
        {
            public int Attached, Skinned, Dressed, Kept, BodyChoices;
            public float Breadth;
            public string Why, Orientation, Parts, CoatRead, TrouserRead, CostSeries, TwinWhy;
            public double Upright, DressedAreaFraction, DressedVertexFraction;
            public bool CoverageRead, BindPoseRead, ScaledPoseRead, TwinRead, TwinHuman;
            public float BindHeadAboveHips, BindHipsAboveFeet;
            public float ScaledHeadAboveHips, ScaledHipsAboveFeet;
            public float TwinHeadAboveHips, TwinHipsAboveFeet;
        }

        static Published Save() => new Published
        {
            Attached = Attached, Skinned = Skinned, Dressed = Dressed, Kept = Kept,
            BodyChoices = BodyChoices, Breadth = Breadth,
            Why = Why, Orientation = Orientation,
            Parts = Parts, CoatRead = CoatRead, TrouserRead = TrouserRead,
            CostSeries = CostSeries, TwinWhy = TwinWhy,
            Upright = Upright, DressedAreaFraction = DressedAreaFraction,
            DressedVertexFraction = DressedVertexFraction, CoverageRead = CoverageRead,
            BindPoseRead = BindPoseRead, ScaledPoseRead = ScaledPoseRead,
            TwinRead = TwinRead, TwinHuman = TwinHuman,
            BindHeadAboveHips = BindHeadAboveHips, BindHipsAboveFeet = BindHipsAboveFeet,
            ScaledHeadAboveHips = ScaledHeadAboveHips, ScaledHipsAboveFeet = ScaledHipsAboveFeet,
            TwinHeadAboveHips = TwinHeadAboveHips, TwinHipsAboveFeet = TwinHipsAboveFeet,
        };

        static void Restore(Published p)
        {
            Attached = p.Attached; Skinned = p.Skinned; Dressed = p.Dressed; Kept = p.Kept;
            BodyChoices = p.BodyChoices; Breadth = p.Breadth;
            Why = p.Why; Orientation = p.Orientation;
            Parts = p.Parts; CoatRead = p.CoatRead; TrouserRead = p.TrouserRead;
            CostSeries = p.CostSeries;
            TwinWhy = p.TwinWhy; Upright = p.Upright;
            DressedAreaFraction = p.DressedAreaFraction;
            DressedVertexFraction = p.DressedVertexFraction;
            CoverageRead = p.CoverageRead; BindPoseRead = p.BindPoseRead;
            ScaledPoseRead = p.ScaledPoseRead; TwinRead = p.TwinRead; TwinHuman = p.TwinHuman;
            BindHeadAboveHips = p.BindHeadAboveHips; BindHipsAboveFeet = p.BindHipsAboveFeet;
            ScaledHeadAboveHips = p.ScaledHeadAboveHips;
            ScaledHipsAboveFeet = p.ScaledHipsAboveFeet;
            TwinHeadAboveHips = p.TwinHeadAboveHips; TwinHipsAboveFeet = p.TwinHipsAboveFeet;
        }

        /// How many bodies were attached to somebody who is NOT the player, and
        /// how many of those failed. Counted here because `Attached` is
        /// restored and therefore cannot see them — a walker body that silently
        /// failed to attach would otherwise look identical to one that was
        /// never asked for.
        public static int Extra, ExtraFailed;
        public static string ExtraWhy = "none asked for";

        /// THE NAME OF THE CHILD, IN ONE PLACE. A detach that looks for a
        /// different string is a leak that reads as a working swap: the old
        /// skinned mesh stays in the scene, still costing its 23,000 vertices,
        /// while a mannequin is built on top of it and every counter says the
        /// body came off. One idea, one spelling.
        public const string ChildName = "RealBody";

        /// Is this host currently wearing one? Asked rather than remembered,
        /// because the walker's own flag and the scene are two records of one
        /// fact and they drift the moment anything else destroys the child.
        public static bool Wearing(GameObject host) =>
            host != null && host.transform.Find(ChildName) != null;

        /// How many skinned bodies have been taken off again. `Extra` counts
        /// attachments over the whole run and keeps doing so, because a
        /// lifetime count and a live one answer different questions and this
        /// project has merged them before. Live is `Extra - Detached`.
        public static int Detached;

        /// Take the skinned body off and leave the host ready for a mannequin.
        ///
        /// DEACTIVATED BEFORE BEING DESTROYED, and that is not belt and braces.
        /// Unity defers `Destroy` to the end of the frame, so a body torn down
        /// and replaced in the same frame is still rendering when the
        /// replacement is built — two bodies in one silhouette for a frame,
        /// which on a swap that happens as somebody walks toward you is exactly
        /// when it would be seen.
        public static bool DetachExtra(GameObject host)
        {
            if (host == null) return false;
            var child = host.transform.Find(ChildName);
            if (child == null) return false;
            child.gameObject.SetActive(false);
            Object.Destroy(child.gameObject);
            Detached++;
            return true;
        }

        /// A body for somebody other than the player. Same path, same dressing,
        /// same scaling — and none of the readings.
        public static bool TryAttachExtra(GameObject host, float targetHeightMetres,
                                          string wearer, bool cast = true)
        {
            var saved = Save();
            bool ok = false;
            string why;
            try
            {
                ok = TryAttach(host, targetHeightMetres, wearer, cast);
            }
            finally
            {
                // READ THE REASON BEFORE PUTTING THE PLAYER'S BACK, or the
                // failure reason reported for a walker is the player's "ok".
                why = Why;
                // In a `finally` so a throw mid-attach cannot leave the
                // player's readings describing a walker — the state this whole
                // method exists to protect is exactly the state an exception
                // would corrupt.
                Restore(saved);
            }
            if (ok) Extra++;
            else { ExtraFailed++; ExtraWhy = why; }
            return ok;
        }

        public static bool TryAttach(GameObject host, float targetHeightMetres = 1.8f,
                                     string wearer = "player", bool cast = true)
        {
            if (host == null) { Why = "no host"; return false; }

            var prefab = PickBody(wearer);
            if (prefab == null)
            {
                // The likeliest cause is that the Editor step did not run, not
                // that the model is bad — and saying which saves a build.
                Why = "Resources/Characters/Body not in the build";
                return false;
            }

            var body = Object.Instantiate(prefab, host.transform);
            if (body == null) { Why = "instantiate returned null"; return false; }
            body.name = ChildName;

            // DID THE FEMALE WALK ACTUALLY ARRIVE ON THIS BODY?
            //
            // Rule 6's proof for the `walk_f` wire, and it reads the Animator
            // rather than re-asking the classifier. `BodyArchetype.Of` decides
            // which controller the EDITOR should have written; asking it again
            // here would print a perfect score on a build where that step never
            // ran — two numbers derived from one variable are one number twice.
            // `ControllerCarries` compares the archetype segment of the asset
            // name the Animator is actually holding.
            //
            // Counted per ATTACH, cumulatively: body LOD grants and revokes
            // continuously, so a woman granted a body four times counts four
            // times. It is a count of attachments, not of citizens.
            //
            // ASKED ONCE AND READ TWICE. `carries` feeds both `walkFemale` and
            // `bodyController`, so the two cannot disagree about the same
            // attachment — calling `ControllerCarries` a second time for the
            // second reader is how one idea becomes two implementations and one
            // of them gets fixed.
            var stem = StemOf(prefab.name);
            var arch = Ledger.Core.BodyArchetype.Of(stem);
            var anim0 = body.GetComponent<Animator>();
            var held = anim0 != null && anim0.runtimeAnimatorController != null
                ? anim0.runtimeAnimatorController.name : "";
            bool carries = Ledger.Core.BodyArchetype.ControllerCarries(held, arch);
            // THE DENOMINATOR FOR `bodyController`, INCREMENTED BEFORE THE
            // TEST, so a run that attached bodies and matched every one of them
            // cannot print the same thing as a run that attached none.
            _controllerReads++;
            if (!carries)
            {
                _controllerMissed++;
                // FIRST-WINS: the witness is fixed by the first mismatch and
                // never overwritten, so it does not depend on LOD ordering.
                //
                // RAW NAME TO CORE, ESCAPED ONCE FOR THE CHANNEL.
                // `ControllerCarries` owns the rule — including that Unity
                // appends " (Instance)" in some load paths — so Core gets the
                // name Unity gave us. The copy that rides on a verdict line may
                // not contain a space, so the whole assembled witness has its
                // spaces REPLACED rather than trimmed, in one place: this is
                // escaping, not a second implementation of Core's stem rule,
                // and the full asset name survives it.
                //
                // `no-stem` is the fallback body — `Characters/Body`, which
                // does not carry the `Body_` prefix `StemOf` reads — and it
                // says so rather than printing an empty field that reads as a
                // formatting fault.
                if (_controllerWitness.Length == 0)
                    _controllerWitness =
                        ((stem.Length > 0 ? stem : "no-stem") + ":" + arch + "->"
                         + (held.Length > 0 ? held : "none")).Replace(' ', '-');
            }
            if (arch == Ledger.Core.BodyArchetype.Female)
            {
                FemaleBodies++;
                if (carries) FemaleWalkers++;
            }

            // AND THE CAPSULE GOES, which this did not do and `Mannequin.Build`
            // has always done.
            //
            // THE STILL IS HOW IT WAS FOUND, and every gate in the run said the
            // body was fine: `realBody=1`, `realBodyWhy=[ok (raw 1.90m scaled
            // x0.949)]`, `bodiesOk=True`, `height=1.58..1.90`. All true. The
            // player was still a two-metre white capsule with a pair of skin-
            // coloured arms poking out of it, because `PlayerController.Spawn`
            // builds the host from `CreatePrimitive(Capsule)` and nothing here
            // removed the mesh that came with it. The bought body was inside,
            // at exactly the same height, hidden by the thing it replaced.
            //
            // Not one gate could have caught it. Every one of them asks about
            // the body that was ADDED and none asks what is still being DRAWN —
            // so `PlayerController` now reports `playerPrimitive`, and the sim
            // gates on it.
            //
            // The instruction was eleven lines long in `Mannequin.Build`, with
            // its reasoning attached, and I wrote the parallel path without
            // reading it. That is the `persist-credentials: false` incident
            // again: the comment that would have prevented it was sitting just
            // above the code I was copying the shape of.
            //
            // The renderer, not the object — anything holding the transform
            // still holds it. And DISABLED first: Destroy is end-of-frame,
            // so a host handed over in the frame a screenshot lands would
            // draw its bare capsule into that frame — the fault the
            // `capsulesLoose` catcher caught on the mannequin path, whose
            // removal block is this block's other implementation.
            var mesh = host.GetComponent<MeshRenderer>();
            if (mesh != null) { mesh.enabled = false; Object.Destroy(mesh); }
            var filter = host.GetComponent<MeshFilter>();
            if (filter != null) Object.Destroy(filter);
            // DOWN, NOT UP, AND THE SIGN IS THE WHOLE THING. The host's origin
            // sits at hip height — `Mannequin.HipY = -SoleBelowOrigin`, and
            // callers spawn at `ground + up * SoleBelowOrigin`. A Mixamo rig's
            // origin is at the FEET. So the body hangs 0.9m BELOW the host to
            // put its soles on the pavement; positive would float it a hip's
            // height above the street, which is precisely the kind of fault a
            // still would show and a gate would not.
            body.transform.localPosition = new Vector3(0f, -Mannequin.SoleBelowOrigin, 0f);
            body.transform.localRotation = Quaternion.identity;

            // A MATERIAL, because the model ships without one and Unity's
            // stand-in for that is bright pink. The first body on the street was
            // magenta and lying down, and the magenta is the easier half.
            // Skin-toned and flat, matching what `Mannequin` dresses its own
            // bodies in, so the two tiers do not read as different species.
            // AND THEN THE STILL SHOWED WHY THAT COMMENT WAS ONLY HALF A FIX.
            //
            // The fallback fired on EVERY renderer — the model ships with no
            // materials at all — so the player walked the street as a
            // uniformly skin-coloured figure while `wardrobe=[navy:492
            // charcoal:549 olive:267 brown:449 oxblood:100]` said the crowd was
            // dressed. Nothing was broken by the measure any gate took:
            // `realBody=1`, `playerPrimitive=False`, `bodyUp=1.000`,
            // `SceneAudit` clean with no `noMaterial` finding — because there
            // WAS a material, and it was skin.
            //
            // A person with no clothes is not a missing-material bug, which is
            // why every check built to catch missing materials passed. It is a
            // MISSING WARDROBE, and the player was the only body in the city
            // nothing dressed.
            //
            // So: skin stays the fallback for anything unpainted, and the body
            // is then DRESSED from `Core/Wardrobe` like everybody else — at a
            // named character's value rather than the crowd's, since
            // `Wardrobe.MaxValue` exists precisely so the cast stay brighter
            // than the street. `Skinned` and `Dressed` are counted so a run can
            // tell "the fallback painted everything" from "the model arrived
            // with its own materials", which the last one could not.
            var skin = AssetLibrary.Opaque(new Color(0.72f, 0.58f, 0.47f));
            // FULLY QUALIFIED, AND THE REASON THIS COMMENT GAVE WAS FALSE. It
            // said the file "deliberately has no `using Ledger.Core;`" because
            // that import would collide with `UnityEngine.Object` and make the
            // bare `Object.Destroy` above a CS0104. Line 2 of this file is
            // `using Ledger.Core;` and has been since f8ef52b, and it compiles
            // — Core declares no type called `Object`, so there was never a
            // collision to avoid. A worked-out reason is the most convincing
            // kind of wrong comment, and this one survived because nobody
            // rereads a paragraph that is not in their diff.
            //
            // The qualification stays because every neighbour has it and a file
            // that qualifies half its Core calls is harder to read than one
            // that qualifies all of them. That is a style reason, which is what
            // it always actually was.
            double coatRoll = Ledger.Core.Physique.Fraction(wearer ?? "player", 7);
            Ledger.Core.Wardrobe.Dress(coatRoll, out double ch, out double cs, out double cv);
            // The cast sit above the crowd's ceiling on purpose — Rocco 0.75,
            // Ada 0.75, Sam 0.65 — and the player is a named character.
            // `Wardrobe.MaxValue` is 0.46 and exists so nobody in the crowd
            // outshines them, so lifting off the band keeps the hue and
            // saturation the wardrobe chose while placing the value where the
            // cast live. 0.68 is under Rocco's 0.75: the protagonist should not
            // be the brightest man on his own street either.
            //
            // BUT THE LIFT IS SCALED BY SATURATION, and the stills are why.
            // A flat +0.22 is fine on denim or burgundy and ruinous on grey or
            // stone, whose saturation floor is 0.02 — lifting those to 0.68
            // produces a near-white coat, which is what `review_day1_noon` and
            // `review_day2_night` at 45c96bc actually show. It is also the
            // exact look of the white-capsule fault this project already fixed
            // once, so it would have been read as a regression in that.
            //
            // Scaling by the band's own saturation means a coloured coat gets
            // the full step and a grey one barely moves, which is how cloth
            // behaves: a bright grey is just a pale grey, while a bright navy
            // is still navy. No new constant — the multiplier is the
            // saturation the wardrobe already chose.
            // AND THE LIFT IS FOR THE CAST ONLY, WHICH IT NEVER WAS.
            //
            // The paragraph above says "the player is a named character" and
            // then lifts everybody: `TryAttachExtra` calls straight through
            // here, so every walker in the city was being raised past
            // `Wardrobe.MaxValue` 0.46 — the constant whose entire job is that
            // nobody in the crowd outshines a cast authored at 0.65-0.75. A
            // comment describing one caller while the method has two is the
            // fault this project has recorded more often than any other, and
            // this one was load-bearing on a value ceiling with a CoreTest
            // behind it.
            //
            // `cast` comes from the SPAWN PATH rather than a roster.
            // `VoiceBank.Cast` is the nearest thing to a list and its own
            // comment says its ids do not all match the game's, so borrowing it
            // would dim a named character under the wrong id and nothing would
            // report it. The callers know: `GameController` and `ActThreeHost`
            // spawn the cast by name, `PopulationHost` spawns residents in a
            // loop, and the default is cast so a new authored character is
            // bright unless somebody says otherwise.
            float lift = cast ? 0.22f * Mathf.Clamp01((float)cs / 0.35f) : 0f;
            if (cast) LiftedCast++; else LiftedCrowd++;
            float coatV = Mathf.Min(0.68f, (float)cv + lift);
            var coatRgb = Color.HSVToRGB((float)ch, (float)cs, coatV);
            var coat = AssetLibrary.Opaque(coatRgb);
            // THE READING, taken here because this is the only place that has
            // all of it: the band the wardrobe chose, the saturation that
            // decided how much lift it got, and the RGB that actually reached
            // the material. `sat` is the one that matters — the lift is scaled
            // by it, so a low-saturation band both starts neutral and stays
            // neutral, and that is the shape of a coat that renders as bare
            // plastic.
            //
            // AND THE WASH IS ON THE SAME LINE, because on today's models it is
            // the only one of the two that runs — `bodySkinned=0 bodyDressed=0
            // bodyKeptMats=1`, so `coatRgb` is a colour computed for a material
            // nothing has been given for weeks. Printing the coat without the
            // wash beside it is printing the branch that is not taken.
            //
            // THE WASH IS APPENDED AFTER THE LOOP, NOT COMPUTED HERE, and that
            // is not tidiness. The wash now depends on the ALBEDO of the sheet
            // it is painting, which is not known until the renderers have been
            // walked — so computing it here would print a number the shader
            // never saw, which is precisely the class of quietly-wrong reading
            // this whole family of counters exists to stop. `_lastWash` carries
            // what was actually applied.
            string coatBand = Ledger.Core.Wardrobe.BandOf(coatRoll);
            CoatRead = coatBand
                     + $" hsv={ch:0.00}/{cs:0.00}/{coatV:0.00}"
                     + $" rgb={(int)(coatRgb.r * 255)},{(int)(coatRgb.g * 255)},{(int)(coatRgb.b * 255)}";
            _lastWash = "none applied";
            Skinned = Dressed = Kept = 0;
            PartsUpper = PartsLower = PartsWhole = PartsOwn = 0;
            double coatArea = 0, totalArea = 0;
            long coatVerts = 0, totalVerts = 0;
            CoverageRead = false;

            // THE SECOND WARDROBE DRAW, and it is the whole reason a crowd of
            // forty stops reading as forty monochrome figures.
            //
            // ITS OWN SALT. `Physique` spends salts 1-8 on the silhouette
            // traits and 23 is the body-model pick, so 11 is free and
            // uncorrelated with all of them — the same argument `Physique.For`
            // makes for using four independent draws rather than one hash with
            // four arithmetics on it. Reusing the coat's roll would give every
            // person trousers the same colour as their coat, which is where
            // this started.
            //
            // NO LIFT, EVER, unlike the coat above. The cast lift exists so a
            // named character's COAT sits above the crowd's ceiling — the
            // street identifies the player by their coat, in its own rumours.
            // Nobody has ever been recognised by their trousers, and lifting
            // both would put two bright garments on one body and undo what the
            // ceiling is for.
            double legRoll = Ledger.Core.Physique.Fraction(wearer ?? "player", 11);
            Ledger.Core.Wardrobe.Dress(legRoll, out double lh, out double ls, out double lv);
            // SLASHES, NOT SPACES — see the declaration. Band names are single
            // words (`black`, `denim`, `shellsuit`), so the whole value is one
            // whitespace-free token and no reader can truncate half of it.
            TrouserRead = Ledger.Core.Wardrobe.BandOf(legRoll)
                        + $"/hsv:{lh:0.00}/{ls:0.00}/{lv:0.00}";

            // TWO PASSES, BECAUSE THE DECISION IS ABOUT THE MODEL AND NOT ABOUT
            // ONE NAME. `BodyParts.Assign` needs to see every paintable mesh at
            // once: a body that is a SINGLE mesh cannot be dressed part-bare,
            // and the honest answer there is a coloured mannequin rather than a
            // nude. One renderer at a time cannot know that.
            var paint = new List<Renderer>();
            var worn = new List<Renderer>();
            foreach (var r in body.GetComponentsInChildren<Renderer>())
            {
                if (r == null) continue;
                var m = r.sharedMaterial;
                // KEEP ONLY WHAT IS ACTUALLY PAINTED, AND THE TEST IS A
                // TEXTURE RATHER THAN A NAME.
                //
                // This read `!m.name.StartsWith("Default")` and the build said
                // exactly what was wrong with it: `bodyKeptMats=2
                // bodySkinned=0 bodyDressed=0`. Both of the body's renderers
                // carry a material that is NOT called "Default…", so both were
                // kept and neither the skin nor the coat was ever applied —
                // the dressing code I shipped last cycle did not run once. The
                // pink is the model's own material.
                //
                // A NAME IS NOT EVIDENCE OF AUTHORSHIP. An untextured
                // stand-in has a name too. What distinguishes a material
                // somebody made from a placeholder is that it has a texture on
                // it, and that is a property rather than a guess.
                if (m != null && m.mainTexture != null)
                {
                    Kept++; KeptEver++;
                    // GATHERED, NOT WASHED HERE, AND THAT IS THE CHANGE.
                    //
                    // This used to call `Tint` on the spot with one colour for
                    // every textured renderer on the body — head, hair and
                    // trousers all multiplied by the coat's hue. Which garment
                    // a mesh IS cannot be decided one mesh at a time: `Body`
                    // means Kate's bare arms when her shirt is a separate mesh
                    // and means the whole of Big Vegas when nothing else on him
                    // is. `BodyParts.Garments` needs the full name list to tell
                    // those apart, which is exactly the two-pass argument the
                    // paint list below has carried since `Assign` landed.
                    worn.Add(r);
                    continue;
                }
                paint.Add(r);
            }

            // WHICH TEXTURED MESH IS COAT, WHICH IS TROUSERS, AND WHICH IS THE
            // ARTIST'S BUSINESS. The rule is in Core with tests over the real
            // shipped mesh names; this supplies membership and the live
            // materials, which is the split `instruments.md` asks for.
            var wornNames = new string[worn.Count];
            for (int i = 0; i < worn.Count; i++) wornNames[i] = worn[i].name;
            var kinds = Ledger.Core.BodyParts.Garments(wornNames);
            foreach (var u in Ledger.Core.BodyParts.Unclassified(wornNames))
                if (!_unknownParts.Contains(u)) _unknownParts.Add(u);

            var wornRead = new System.Text.StringBuilder();
            for (int i = 0; i < worn.Count; i++)
            {
                var r = worn[i];
                var m = r.sharedMaterial;
                // The albedo about to be washed, measured once per sheet.
                // Here rather than inside `Tint` because the texture is the
                // MATERIAL's, not the wash's, and putting it in `Tint`
                // would make the reading depend on how often the LOD
                // happened to grant this body — a count of grants wearing a
                // measurement's name.
                float sheet = m != null && m.mainTexture != null
                    ? AlbedoValueOf(m.mainTexture) : -1f;
                string went;
                switch (kinds[i])
                {
                    case Ledger.Core.BodyParts.Garment.Lower:
                        Tint(r, lh, ls, lv, sheet); PartsLower++; went = "legs"; break;
                    case Ledger.Core.BodyParts.Garment.Upper:
                        // THE RAW `cv`, NOT `coatV`. The lift above places a
                        // named character's coat MATERIAL above the crowd's
                        // ceiling; the wash normalises against that same
                        // ceiling, so handing it a lifted value would clamp
                        // everybody to 1.0 and hand back the white multiply
                        // this change exists to remove. One decision, two
                        // consumers, and they need different halves of it —
                        // which is exactly how the first version came to read
                        // `ch`/`cs` and drop `cv` on the floor.
                        Tint(r, ch, cs, cv, sheet); PartsUpper++; went = "coat"; break;
                    case Ledger.Core.BodyParts.Garment.Whole:
                        Tint(r, ch, cs, cv, sheet); PartsWhole++; went = "whole"; break;
                    default:
                        // LEFT ALONE, AND NOT WASHED WHITE. A multiply by white
                        // is the identity, so the two are the same pixels — but
                        // they are not the same NUMBER: `WashNearWhite` counts
                        // washes that changed nothing, and pushing every face
                        // and every shoe through it would bury the wardrobe
                        // fault it exists to find under skin that was never
                        // meant to be dressed.
                        PartsOwn++; OwnEver++; went = "own"; break;
                }
                if (wornRead.Length > 0) wornRead.Append(' ');
                wornRead.Append(r.name).Append("->").Append(went);
            }

            // THE BODY-LEVEL TALLY, CUMULATIVE OVER THE RUN AND READ ON THE
            // DONE LINE. Rule 6's proof: a wiring job with no counter cannot be
            // shown to have run, and this project has a milestone where forty
            // of sixty-one APIs were built, tested and called by nothing.
            //
            // Deliberately NOT in the save-and-restore set — see `Tinted`.
            // These are counts of what happened to the CITY, and restoring them
            // after every walker attach is what once made `bodyTinted` read 1
            // against 1,586 attachments.
            if (PartsUpper + PartsLower + PartsWhole > 0)
            {
                DressedBodies++;
                if (PartsUpper > 0 && PartsLower > 0) SplitBodies++;
                else if (PartsWhole > 0) WeldedBodies++;
                else UpperOnlyBodies++;
            }

            // WHICH RENDERER IS SKIN AND WHICH IS COAT, FROM THE NAME — and
            // the rule now lives in Core where it has unit tests, because the
            // version that lived here was wrong for weeks and could only have
            // been caught by a 28-minute Windows round trip.
            //
            // What was wrong with it: `name.Contains("face")` matched
            // `Beta_Surface`, which is the whole body. The player was painted
            // flesh from the neck down and the coat went on the joint balls,
            // and that is the naked figure in the middle of the noon still.
            // `BodyParts.IsFlesh` compares WORDS for equality; sur-face is not
            // face, and there is a test named after it.
            var names = new string[paint.Count];
            for (int i = 0; i < paint.Count; i++) names[i] = paint[i].name;
            var isFlesh = BodyParts.Assign(names);

            var parts = new System.Text.StringBuilder();
            var areas = new double[paint.Count];
            for (int i = 0; i < paint.Count; i++)
            {
                var r = paint[i];
                bool flesh = isFlesh[i];
                r.sharedMaterial = flesh ? skin : coat;
                if (flesh) { Skinned++; SkinnedEver++; }
                else { Dressed++; DressedEver++; }
                // EVERY DECISION THIS RULE HAS EVER MADE, distinct, because
                // `Parts` is rebuilt at every attach and the run ended on a
                // body that had nothing to paint — so it says "nothing to
                // paint" and can never explain `bodySkinnedEver=0`.
                //
                // Zero flesh over a whole run has two completely different
                // causes and no number separates them: either no renderer name
                // matches a bare word, or `Assign`'s single-mesh rule is
                // firing, which turns an all-bare model into an all-coat one on
                // purpose and is correct. Guessing between those is how the
                // sur-face bug survived for weeks. The names decide it.
                if (PartsEver.Count < 64)
                    PartsEver.Add($"{r.name}->{(flesh ? "skin" : "coat")}");

                // HOW MUCH OF THE PERSON THIS RENDERER IS. Measured on the
                // mesh the wardrobe just painted, so the answer cannot drift
                // from the decision it describes.
                double a = SurfaceArea(r);
                int verts = VertexCount(r);
                areas[i] = a;
                totalArea += a; totalVerts += verts;
                if (!flesh) { coatArea += a; coatVerts += verts; }
            }

            // NAME EVERY MESH, ITS SHARE AND WHICH WAY IT WENT.
            //
            // Rule 4's repair. `bodySkinned=1 bodyDressed=1 bodyCoatArea=0.296`
            // was in every verdict for as long as the player was naked, and it
            // is the correct reading of a body painted the wrong way round — it
            // simply never named the mesh, so nothing in the file connected
            // 29.6% to "the coat is on the joints". One line does:
            //
            //     bodyParts=[Beta_Surface:70.4%->skin Beta_Joints:29.6%->coat]
            //
            // and the fault is legible from the text alone, with no picture and
            // no round trip.
            for (int i = 0; i < paint.Count; i++)
            {
                double share = totalArea > 0 ? areas[i] / totalArea : 0;
                parts.Append(i == 0 ? "" : " ")
                     .Append(paint[i].name).Append(':')
                     .Append((share * 100.0).ToString("0.0")).Append("%->")
                     .Append(isFlesh[i] ? "skin" : "coat");
            }
            // BOTH LISTS, AND THE COMMENT THAT USED TO BE HERE IS NOW FALSE.
            //
            // It said: "`parts=()` in the verdict reads as 'the measurement did
            // not run', and on the run that fixed the bodies it meant the
            // opposite: every renderer arrived textured, `Kept` took all of
            // them, and there was nothing left to paint." That was true and it
            // is the exact sentence this change falsifies — a textured renderer
            // is no longer "nothing to paint", it is a mesh the wardrobe washes
            // as a coat, as trousers, or leaves to the artist, and which way it
            // went is the thing a still needs explaining.
            //
            // So the line now names every mesh on the body under either rule.
            // `->coat`/`->legs`/`->whole`/`->own` are the washed tier;
            // `->skin`/`->coat` with an area share are the painted tier, which
            // no shipped model has reached since texture extraction landed.
            // The one remaining empty case is a body with no renderers at all,
            // and it says so in words rather than as an empty bracket.
            string painted = parts.ToString(), washed = wornRead.ToString();
            Parts = painted.Length > 0 && washed.Length > 0 ? painted + " " + washed
                  : painted.Length > 0 ? painted
                  : washed.Length > 0 ? washed
                  : "no renderers on the body at all";

            // TWO MEASUREMENTS, TWO GATES, and the first run is why.
            //
            // These used to share one `if (totalArea > 0)`, so when the mesh
            // turned out to be non-readable — `mesh.vertices` returns an EMPTY
            // ARRAY rather than throwing — the area came back zero and took the
            // vertex fraction down with it. Both printed 0.000, which is
            // exactly what a coat covering nothing looks like.
            //
            // `vertexCount` is metadata and works on a non-readable mesh, so it
            // would have answered on its own. One condition guarding two
            // independent facts is the same fault as a reset that clears half a
            // class's counters: the half it forgets looks deliberate.
            //
            // And -1 rather than 0 for "not measured", because a fraction of
            // zero is a legitimate reading and must not be confused with the
            // absence of one.
            DressedAreaFraction = totalArea > 0 ? coatArea / totalArea : -1;
            DressedVertexFraction = totalVerts > 0 ? (double)coatVerts / totalVerts : -1;
            CoatRead += $" wash={_lastWash}";
            CoverageRead = totalArea > 0 && totalVerts > 0;

            // WHICH WAY UP, PRINTED. Setting the instantiated root's rotation to
            // identity above corrects nothing if the axis conversion sits on a
            // node BELOW it, which is what a Z-up FBX imported without
            // `bakeAxisConversion` leaves behind. `CharacterImport` now bakes it;
            // this reports the outcome rather than trusting that it took, and
            // says which transform any residual rotation is on.
            var childRot = body.transform.childCount > 0
                ? body.transform.GetChild(0).localRotation.eulerAngles
                : Vector3.zero;
            Upright = Vector3.Dot(body.transform.up, Vector3.up);
            Orientation = $"root={body.transform.localRotation.eulerAngles} "
                          + $"child0={childRot} up.y={Upright:0.000}";

            // THE BIND POSE, MEASURED BEFORE ANYTHING ANIMATES IT.
            //
            // The run reports `headAboveHips=-0.130 hipsAboveFeet=-0.778` — the
            // player is upside down — while `bodyUp=1.000` says the root is
            // perfectly upright. Two hypotheses fit that equally well and they
            // have opposite fixes:
            //
            //   IMPORT   `bakeAxisConversion = true` is wrong for these files.
            //            It was set because a body lay on its back, and the
            //            evidence that it worked was `bodyUp` going to 1.000 —
            //            which reads the ROOT and could never have seen the
            //            skeleton. If Mixamo's FBX were already Y-up, baking a
            //            conversion would have introduced the flip rather than
            //            removed it, and I would have confirmed the fix with an
            //            instrument that cannot see the fault.
            //   ANIMATE  the import is fine and something downstream — a clip,
            //            the avatar binding, or `CharacterRig`'s own solve — is
            //            driving the bones inverted.
            //
            // Guessing costs a 28-minute round trip per guess. Measuring the
            // BIND pose here, before a single frame has animated, separates
            // them in ONE: if the T-pose is already inverted it is the import,
            // and if the T-pose is upright while the run is not, it is
            // everything after.
            BindPoseRead = false;
            if (ReadBoneSpan(body, out float bh, out float bf))
            {
                BindHeadAboveHips = bh;
                BindHipsAboveFeet = bf;
                BindPoseRead = true;
            }

            // SCALE FROM THE BOUNDS, NOT FROM A CONSTANT. Mixamo's own scale
            // depends on how the file was exported, and `useFileScale` respects
            // whatever the FBX declares — which is the honest setting and also
            // the one that leaves the actual height unknown until it is
            // measured. `Mannequin` builds people 1.58-1.90m and the sim gates
            // on that range, so a body arriving at 100x would fail a gate rather
            // than quietly tower over the street.
            // AND BREADTH ACROSS, WHICH THIS THREW AWAY AND THE BOXES DID NOT.
            //
            // `Physique.For` draws breadth 0.86-1.18 from its OWN salt, with a
            // comment explaining why: one hash reused with different arithmetic
            // "gives correlated traits — everybody tall is also broad, and the
            // crowd collapses back onto one axis of variation wearing a
            // disguise". Four independent draws, deliberately, and this scaled
            // `Vector3.one * k` — height only. Two people the same height came
            // out geometrically identical.
            //
            // `Mannequin` has had it all along: `new Vector3(scale * Breadth,
            // scale, scale)`, one line, thirteen boxes. So upgrading a walker
            // from a box to a bought body LOST a shape trait, and body LOD
            // grants those bodies to the nearest twelve — the people you can
            // see best. The closer somebody got, the less their build varied.
            // That is the sameness the roadmap has been describing, with a
            // mechanism rather than a shrug, and it arrived with the feature
            // that was supposed to fix it.
            //
            // Found by grepping `Breadth` after `bodyFaces` measured 8 distinct
            // models among 14 bodies — the number said the models cannot carry
            // it alone, and this is what else was available and switched off.
            //
            // HEAD SCALE IS NOT HERE and that is not an oversight. `Mannequin`
            // scales a head that is a child transform; on a skinned mesh the
            // head is a BONE, and moving it means writing to the humanoid rig
            // every frame or the animator overwrites it. Different job, its own
            // failure mode, and it goes on the queue rather than into this
            // line.
            float measured = HeightOf(body);
            if (measured > 0.01f)
            {
                float k = targetHeightMetres / measured;
                float breadth = (float)Ledger.Core.Physique.For(wearer ?? "player").Breadth;
                body.transform.localScale = new Vector3(k * breadth, k, k * breadth);
                Breadth = breadth;
                if (BreadthsEver.Count < 64)
                    BreadthsEver.Add(breadth.ToString("0.00"));
                Why = $"ok (raw {measured:0.00}m scaled x{k:0.000} breadth x{breadth:0.000})";
            }
            else
            {
                Why = $"ok (no renderer bounds; left at file scale)";
            }

            // AND THE SAME MEASUREMENT AGAIN, AFTER SCALING, because the last
            // bisect had a hole in exactly this shape.
            //
            // The bind sample above is taken at instantiate, BEFORE this scale
            // is applied. It read +0.56 / +0.96 — upright — and I reported
            // that as "the import is innocent". It only ever showed the body
            // innocent up to that LINE. Everything between it and the
            // Animator was unmeasured, and the scale sits right in the gap.
            //
            // So the stages are now fully bracketed: bind (post-instantiate),
            // scaled (here), pre-solve (top of `CharacterRig.LateUpdate`, so
            // after the Animator), and post-solve. Whichever adjacent pair
            // disagrees is the stage that inverts the body, and there is
            // nowhere left for it to hide.
            if (ReadBoneSpan(body, out float sh, out float sf))
            {
                ScaledHeadAboveHips = sh;
                ScaledHipsAboveFeet = sf;
                ScaledPoseRead = true;
            }

            Attached++;
            StageNoClipTwin(prefab, host);
            return true;
        }

        /// THE LAST TWO SUSPECTS, SEPARATED BY A BODY THAT IS HANDED NO
        /// ANIMATION AT ALL.
        ///
        /// `importerRan=44` closed the import: the postprocessor runs on every
        /// model, so the bake experiment that came back identical to three
        /// decimals really was an experiment, and the bake really is not the
        /// variable. Bind pose upright, scaled pose upright, everything after
        /// the Animator inverted. Two suspects are left and they need opposite
        /// fixes:
        ///
        ///   the CLIP's curves are inverted   -> reauthor or reimport the clips
        ///   the AVATAR's mapping is inverted -> rebuild the human description
        ///
        /// The bind-pose reading cannot tell them apart, because a disabled
        /// Animator leaves the bones exactly where the bind pose put them —
        /// which is the number already measured, and it is upright. The
        /// distinguishing case is an Animator that is ENABLED and BOUND to the
        /// avatar but has no clip to play: it evaluates the avatar's own
        /// default humanoid pose through muscle space, so the avatar does all
        /// the work and no clip contributes anything.
        ///
        ///   twin upright  -> the avatar maps correctly and the clip inverts
        ///   twin inverted -> the avatar inverts, and the clip is innocent
        ///
        /// A SEPARATE, HIDDEN INSTANCE rather than a change to the player. I
        /// have twice made the body the subject of a test and twice had to ask
        /// whether the test moved it; a probe that touches the thing it
        /// measures cannot answer a question about what moved it. This one is
        /// disabled for rendering, parented off to the side, and never solved
        /// by `CharacterRig` — it exists for one reading and costs one skinned
        /// mesh for the length of the run.
        static void StageNoClipTwin(GameObject prefab, GameObject host)
        {
            if (prefab == null || host == null || TwinRead) return;
            var twin = Object.Instantiate(prefab, host.transform);
            twin.name = "NoClipTwin";
            twin.transform.localPosition = new Vector3(0f, -40f, 0f);
            foreach (var r in twin.GetComponentsInChildren<Renderer>()) r.enabled = false;
            // Any `CharacterRig` on the twin would solve it and contaminate the
            // very pose being read — the same reason the reading is taken before
            // the solve on the real body.
            foreach (var rig in twin.GetComponentsInChildren<CharacterRig>()) Object.Destroy(rig);

            var anim = twin.GetComponentInChildren<Animator>();
            if (anim == null) { TwinWhy = "no animator on the twin"; return; }
            // ENABLED AND BOUND, WITH NOTHING TO PLAY. Clearing the controller
            // rather than disabling the Animator is the whole experiment: a
            // disabled Animator reports the bind pose, which is already known
            // and already upright.
            anim.runtimeAnimatorController = null;
            anim.enabled = true;
            TwinHuman = anim.avatar != null && anim.avatar.isHuman;
            TwinWhy = TwinHuman ? "bound, no controller" : "avatar not human";
            _twin = twin;
        }

        static GameObject _twin;

        /// Read once, late, from the sim — the Animator needs a frame to
        /// evaluate before there is anything to measure, and reading in the
        /// same frame it was created would report the bind pose and quietly
        /// answer the wrong question.
        public static void ReadNoClipTwin()
        {
            if (_twin == null || TwinRead) return;
            if (ReadBoneSpan(_twin, out float h, out float f))
            {
                TwinHeadAboveHips = h;
                TwinHipsAboveFeet = f;
                TwinRead = true;
            }
        }

        public static float TwinHeadAboveHips { get; private set; }
        public static float TwinHipsAboveFeet { get; private set; }
        public static bool TwinRead { get; private set; }
        public static bool TwinHuman { get; private set; }
        public static string TwinWhy { get; private set; } = "not staged";

        /// World height of everything renderable under `go`. Uses renderer
        /// bounds rather than the transform, because a rig's root transform says
        /// nothing about how tall the mesh on it is.
        static float HeightOf(GameObject go)
        {
            var renderers = go.GetComponentsInChildren<Renderer>();
            if (renderers == null || renderers.Length == 0) return 0f;
            var bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++) bounds.Encapsulate(renderers[i].bounds);
            return bounds.size.y;
        }
    }
}
