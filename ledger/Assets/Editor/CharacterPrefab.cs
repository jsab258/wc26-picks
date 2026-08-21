using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Ledger.EditorTools
{
    /// M17.1, step two: make the body REACHABLE AT RUNTIME.
    ///
    /// The audit answered step one — `models=44 humanoid=44 validHumanAvatar=44
    /// clips=44`, so Unity does produce valid human Avatars from these FBX once
    /// `CharacterImport` forces Humanoid. `CharacterRig.Bind` has had a tier one
    /// waiting for that since it was written: an `Animator` in the children with
    /// `avatar.isHuman`, and everything below it unchanged.
    ///
    /// WHAT WAS STILL MISSING is that nothing can LOAD the FBX. `Resources.Load`
    /// only reaches `Assets/Resources`, and the bodies live in
    /// `Assets/Characters`.
    ///
    /// MOVING THEM WOULD BE THE WRONG FIX: everything under `Resources` ships in
    /// the player whether or not it is used, so moving forty-four FBX there
    /// would put forty-one animation clips and two bodies in the build to reach
    /// one. Instead a PREFAB goes in `Resources` and REFERENCES the model — and
    /// Unity pulls a referenced asset into the build as a dependency, so exactly
    /// what is used ships and nothing else.
    ///
    /// Built by script rather than by hand because nobody opens the Editor on
    /// this project: CI is the only Unity that runs, so a prefab somebody made
    /// once and committed would be a binary nobody could review or regenerate.
    public static class CharacterPrefab
    {
        /// Joe since 15 Aug: the default body a gate or an empty pool falls
        /// back to should be a PERSON, not the grey rig mannequin the clips
        /// happened to be retargeted through. X Bot stood here only because
        /// it was the first FBX this project ever had.
        public const string BodyModel = "Assets/Characters/Joe.fbx";
        public const string ResourceDir = "Assets/Resources/Characters";
        public const string BodyPrefab = ResourceDir + "/Body.prefab";
        public const string ControllerPath = ResourceDir + "/Body.controller";

        /// The name the runtime asks `Resources.Load` for.
        public const string LoadPath = "Characters/Body";

        /// The float `CharacterRig` writes each frame. Named once here so the
        /// controller that reads it and the code that writes it cannot drift.
        public const string SpeedParam = "Speed";

        /// Reported on the done line so a run says whether the body has
        /// anything to play, rather than leaving it to be inferred from a
        /// screenshot. `-1` is "the builder did not run at all", which is a
        /// different fault from "it ran and found no clips".
        public static int ClipsBound = -1;
        public static string ControllerWhy = "not tried";

        /// Every body prefab written this run, newline-free for the done line.
        /// A run that finds one body and a run that finds five look identical
        /// from a screenshot of one character.
        public static int Variants;

        /// One controller PER GAIT ARCHETYPE, cached — built on first use,
        /// shared by every body of that archetype. WRITTEN BEFORE THE CLIPS
        /// ARRIVE (16 Aug), the pipeline's standing pattern: today only the
        /// shared idle/walk/run exist, so every archetype resolves to the
        /// same three clips and nothing changes; the moment Jafar's Mixamo
        /// re-pick lands `walk_old`, `idle_old` and the idle variants, old
        /// bodies walk old and idles stop being one loop — in that build,
        /// with no further code.
        static readonly System.Collections.Generic.Dictionary<string, RuntimeAnimatorController>
            _locomotions = new System.Collections.Generic.Dictionary<string, RuntimeAnimatorController>();

        /// Which gait a body wears, from its model name — the same
        /// name-keyed determinism `Physique` uses ("the same name is the
        /// same body, always"). "old" is the only special archetype until a
        /// female walk clip actually exists in the harvest; wiring an
        /// archetype whose clips cannot arrive would be rule 6 in advance.
        static string ArchetypeFor(string stem)
        {
            var s = stem.ToLowerInvariant();
            if (s.Contains("granny") || s.Contains("old") || s.Contains("elder"))
                return "old";
            return "default";
        }

        /// Which idle VARIANT a default body opens with, spread
        /// deterministically across whatever idle clips the harvest holds
        /// (`idle`, `idle_2`, `idle_bored`). Variety for one street-glance:
        /// two people waiting at a corner should not breathe in unison.
        static readonly string[] IdleVariants = { "idle", "idle_2", "idle_bored" };

        /// The clips a person can be DOING rather than travelling through.
        /// Every one of these was in Jafar's harvest with no consumer; the
        /// build log prints how many became states, so "the pick landed" and
        /// "the game can play it" stay separate facts.
        static readonly string[] ActivitySlots =
        {
            "talk", "argue", "greet", "phone_box", "lean_wall", "lean",
            "smoke", "drink", "sit", "carry", "carry_bag", "work_counter",
            "idle_bored", "look_around",
            // THE REACTION SET (queue: "wiring, not sourcing"). Clips on
            // disk since 18 August; `NpcWalker.React` is the consumer, so
            // adding a name here without a call site over there is rule 6.
            "flinch", "glance", "wave", "point", "head_no",
        };

        /// How many activity states the canonical controller carries.
        public static int ActivityStates = -1;

        static RuntimeAnimatorController LocomotionFor(string stem)
        {
            var arch = ArchetypeFor(stem);
            string idleKey = "idle";
            if (arch == "default")
            {
                int h = 0;
                foreach (char c in stem) h = h * 31 + c;
                idleKey = IdleVariants[((h % IdleVariants.Length)
                                       + IdleVariants.Length) % IdleVariants.Length];
            }
            var key = arch + ":" + idleKey;
            if (_locomotions.TryGetValue(key, out var cached) && cached != null)
                return cached;
            var built = BuildLocomotion(arch, idleKey);
            _locomotions[key] = built;
            return built;
        }

        /// EVERY BODY IN THE FOLDER, NOT JUST THE ONE NAMED ABOVE.
        ///
        /// A town where sixty-odd named people share one face is barely
        /// better than a town of boxes, and pointing `BodyModel` at a
        /// different single file would just move the problem.
        ///
        /// So this writes one prefab per body it finds and `RealBody` picks per
        /// character. Written BEFORE the bodies arrive on purpose: the drop
        /// then shows up in the next build instead of the one after, and the
        /// code is reviewed while it is cheap to be wrong about.
        ///
        /// Bodies are files directly in `Assets/Characters`; the forty-two
        /// clips live in A/B/C. Same test `CharacterImport` uses for
        /// readability, and it is the folder convention this project already
        /// relies on rather than a new one.
        static System.Collections.Generic.List<string> BodyModels()
        {
            var found = new System.Collections.Generic.List<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { "Assets/Characters" }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var rel = path.Substring("Assets/Characters/".Length);
                if (rel.Contains("/")) continue;
                found.Add(path);
            }
            // Sorted, because `FindAssets` order is not defined and a cast whose
            // faces reshuffle between builds is the same fault `Physique` exists
            // to prevent — "the same name is the same body, always".
            found.Sort(System.StringComparer.Ordinal);
            return found;
        }

        public static void Build()
        {
            ExtractTextures();
            Variants = 0;
            _locomotions.Clear();
            int mannequins = 0, cartoons = 0, unmeasured = 0;
            var cartoonWho = new System.Collections.Generic.List<string>();
            var unmeasuredWho = new System.Collections.Generic.List<string>();
            foreach (var path in BodyModels())
            {
                var stem = System.IO.Path.GetFileNameWithoutExtension(path);

                // The rig mannequins get no prefab at all, so they cannot be
                // worn, shipped, or picked by any code that ever greps
                // `Resources/Characters` — the same `IsMannequin` the runtime
                // pool asks, one implementation on purpose (its comment in
                // `RealBody` carries the story).
                if (Ledger.Game.RealBody.IsMannequin(stem))
                {
                    mannequins++;
                    continue;
                }

                // AND NEITHER DO THE CARICATURES. Same gate, one step later,
                // and deliberately NOT a second name list: `Proportion` is
                // measured arithmetic covered by CoreTests, and it judges
                // whatever gets dropped into `Assets/Characters` next rather
                // than only what somebody remembered to write down. The
                // reading is reported either way — a model that cannot be
                // measured is named and KEPT, because "unmeasured" and
                // "caricature" are different facts with different fixes and
                // silently dropping the first would empty the street.
                double floorY, neckY, crownY, neckFrac;
                if (!TryBoneHeights(path, out floorY, out neckY, out crownY)
                    || !Ledger.Core.Proportion.TryNeckFraction(
                            floorY, neckY, crownY, out neckFrac))
                {
                    unmeasured++;
                    unmeasuredWho.Add(stem);
                }
                else if (Ledger.Core.Proportion.IsCaricature(floorY, neckY, crownY))
                {
                    // The DECISION comes from Core, not from comparing the
                    // fraction against the constant here. Both spellings are
                    // the same rule, and a rule with two implementations is
                    // one that drifts — the fraction is read out only to put
                    // a number next to the name in the log.
                    cartoons++;
                    cartoonWho.Add($"{stem}:{neckFrac:F3}");
                    continue;
                }

                BuildOne(path, path == BodyModel);
            }
            Debug.Log($"CharacterPrefab: {Variants} body prefab(s) written, "
                      + $"{mannequins} rig mannequin(s) skipped, "
                      + $"{cartoons} caricature(s) skipped "
                      + $"[{(cartoonWho.Count == 0 ? "none" : string.Join(",", cartoonWho))}], "
                      + $"{unmeasured} unmeasured but kept "
                      + $"[{(unmeasuredWho.Count == 0 ? "none" : string.Join(",", unmeasuredWho))}]");

            // THE CANONICAL CONTROLLER, ONCE, AFTER EVERY BODY HAS BEEN THROUGH.
            //
            // These two are CANONICAL-ONLY statics — both are written under
            // `if (canonical)` in `MakeController`, which says so in its own
            // closing comment — and they used to be printed on the per-body
            // line inside `BuildOne`. One shared fact, fourteen lines, and the
            // value each line got depended only on whether that body happened
            // to be built before or after the canonical controller: six read
            // `clipsBound=-1 controller=not_tried` off the initialiser and
            // eight read the canonical result. Neither half described its own
            // body, and on 21 August the first half was read as six bodies
            // with no controller.
            //
            // `Variants` is the denominator (rule 3b): `not tried` is exactly
            // what this prints when no body reached the builder, so without a
            // count beside it a run that built nothing is indistinguishable
            // from one whose canonical body simply came last.
            // AND THE SPACES COME OUT, because a verdict value may not contain
            // one. `ok (idle+walk+run)` and `not tried` both do, and the
            // reader takes the first whitespace-delimited token — so the
            // earlier reading of this key was literally `controller=not`,
            // which is the truncation that looks like a finding.
            // NAMED `canonController*`, NOT `why` AND `of`. The first version
            // used those two bare words, and the key ledger took them as new
            // verdict keys — which they are, and they are the worst possible
            // ones: `why=` and `of=` are words that will be wanted again by
            // the next system that needs to say why something happened, and
            // then two unrelated numbers share a key and every reader that
            // greps for one silently gets the other. The dupkeys tool exists
            // because that already happened 30 times on one line.
            Debug.Log($"CharacterPrefab: canonical controller "
                      + $"canonClipsBound={ClipsBound} "
                      + $"canonControllerWhy=[{ControllerWhy.Replace(' ', '_')}] "
                      + $"canonBodies={Variants}");
        }

        /// THE THREE BONE HEIGHTS `Proportion` NEEDS, off the imported model.
        /// Hands back the raw heights rather than the fraction so the caller
        /// asks Core both questions — is it measurable, and is it a caricature
        /// — without either one being re-derived up here.
        ///
        /// Read from the transform hierarchy by name rather than through
        /// `Animator.GetBoneTransform`, for two reasons. `HeadTop_End` is not
        /// a Humanoid bone at all — Unity's enum has no crown — so half of
        /// what this needs could not be asked for that way. And this runs on
        /// the ASSET, before any avatar is guaranteed to have been built.
        ///
        /// The names are safe to depend on: every one of the ten models under
        /// `Assets/Characters` is a Mixamo export and carries the same
        /// `mixamorig:` skeleton, which `tools/body-proportions.py` confirmed
        /// by reading all ten off disk. A model that does NOT carry them
        /// returns false and is kept, not dropped.
        ///
        /// Import scale is irrelevant here on purpose — the reading is a
        /// ratio of two heights, so it survives whatever the importer does.
        static bool TryBoneHeights(string path,
                                   out double floorY, out double neckY, out double crownY)
        {
            floorY = neckY = crownY = 0.0;
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go == null) return false;

            Transform neck = null, crown = null;
            double floor = double.MaxValue;
            foreach (var t in go.GetComponentsInChildren<Transform>(true))
            {
                var bare = t.name;
                int colon = bare.LastIndexOf(':');
                if (colon >= 0) bare = bare.Substring(colon + 1);

                if (bare == "Neck") neck = t;
                else if (bare == "HeadTop_End") crown = t;
                else if (bare == "LeftToe_End" || bare == "RightToe_End"
                         || bare == "LeftToeBase" || bare == "RightToeBase"
                         || bare == "LeftFoot" || bare == "RightFoot")
                    floor = System.Math.Min(floor, t.position.y);
            }
            if (neck == null || crown == null || floor == double.MaxValue)
                return false;

            floorY = floor;
            neckY = neck.position.y;
            crownY = crown.position.y;
            return true;
        }

        /// THE EMBEDDED TEXTURES, PULLED OUT OF THE FBX, because Unity does not
        /// do it and every body has been a flat colour for want of this.
        ///
        /// MEASURED, NOT GUESSED, AND IT TOOK A REPORT TO GET HERE. Setting
        /// `materialImportMode` to `ImportViaMaterialDescription` was the first
        /// try and it was not enough: the run came back with materials on every
        /// body — Michelle 1, Remy 6, The Boss 4, thirty across ten models —
        /// every one of them on the Standard shader and every one of them
        /// `notex`. So the materials import fine and the textures never arrive,
        /// which is a different fault from the one I fixed and would have been
        /// invisible without the per-body line.
        ///
        /// The textures ARE in the files: counted by PNG signature, Michelle 4,
        /// Remy 22, Sophie 6, Joe 6, Martha 6, The Boss 3, Big Vegas and Sporty
        /// Granny 1 each, and only X Bot and Y Bot none — which is right,
        /// they are the grey stand-ins. Checked on disk here too: no `.fbm`
        /// folder and no `Textures` folder exists anywhere under
        /// `Assets/Characters`, so nothing has ever unpacked them.
        ///
        /// `ExtractTextures` writes them out as real assets and triggers a
        /// reimport, which is why it CANNOT live in `OnPreprocessModel` — that
        /// runs during an import and this starts one. It runs once, here,
        /// before any prefab is built.
        ///
        /// IDEMPOTENT BY THE FOLDER, so a second CI run does not re-extract
        /// twenty-two PNGs it already has. Cheap to check and it keeps the
        /// commit that lands the textures readable.
        public static int TexturesExtracted, TexturesModelsTried;

        static void ExtractTextures()
        {
            TexturesExtracted = TexturesModelsTried = 0;
            const string dir = CharacterImport.CharacterFolder + "Textures";
            try
            {
                if (!AssetDatabase.IsValidFolder(dir))
                    AssetDatabase.CreateFolder(
                        CharacterImport.CharacterFolder.TrimEnd('/'), "Textures");

                var extracted = new System.Collections.Generic.List<string>();
                foreach (var path in BodyModels())
                {
                    TexturesModelsTried++;
                    var importer = AssetImporter.GetAtPath(path) as ModelImporter;
                    if (importer == null) continue;
                    if (importer.ExtractTextures(dir))
                    {
                        TexturesExtracted++;
                        extracted.Add(System.IO.Path.GetFileName(path));
                        // The model has to be read again for its materials to
                        // bind to textures that did not exist when it was last
                        // imported. Without this the extraction succeeds and
                        // the bodies stay exactly as flat as before, which
                        // would read as the extraction having failed.
                        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);
                    }
                }
                AssetDatabase.Refresh();

                // THE DENOMINATOR. `TexturesExtracted=0` is consistent with
                // "already done on a previous run", "no model carries embedded
                // media" and "the call failed on every one of them", and those
                // have nothing in common. The count tried, the count that
                // yielded, and the names.
                int onDisk = AssetDatabase.FindAssets("t:Texture2D", new[] { dir }).Length;
                Debug.Log($"CharacterMaterials: extracted from {TexturesExtracted}"
                          + $" of {TexturesModelsTried} model(s), {onDisk} texture(s)"
                          + $" now in {dir}"
                          + (extracted.Count > 0
                                 ? " [" + string.Join(", ", extracted) + "]"
                                 : " [none needed extraction this run]"));
            }
            catch (System.Exception e)
            {
                // A DIAGNOSTIC THAT KILLS THE BUILD IS WORSE THAN NO
                // DIAGNOSTIC — the same rule `CharacterAudit` states, and this
                // one sits even earlier in the only entry point the whole
                // Windows pipeline goes through.
                Debug.Log($"CharacterMaterials: extraction FAILED "
                          + $"{e.GetType().Name}: {e.Message}");
            }
        }

        /// `isDefault` writes the extra copy at `Body.prefab`, which is what
        /// `RealBody` falls back to and what every existing gate names.
        static void BuildOne(string modelPath, bool isDefault)
        {
            try
            {
                var model = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
                if (model == null)
                {
                    Debug.Log($"CharacterPrefab: no model at {modelPath} — skipping");
                    return;
                }

                var avatar = AvatarOf(modelPath);
                if (avatar == null || !avatar.isHuman)
                {
                    // NOT AN ERROR, A FINDING. If the importer stopped producing
                    // a human avatar this says so instead of writing a prefab
                    // that binds to nothing and looks like it worked.
                    Debug.Log("CharacterPrefab: model has no valid human avatar — "
                              + "not writing a prefab that cannot bind");
                    return;
                }

                if (!AssetDatabase.IsValidFolder("Assets/Resources"))
                    AssetDatabase.CreateFolder("Assets", "Resources");
                if (!AssetDatabase.IsValidFolder(ResourceDir))
                    AssetDatabase.CreateFolder("Assets/Resources", "Characters");

                var instance = (GameObject)PrefabUtility.InstantiatePrefab(model);
                if (instance == null)
                {
                    Debug.Log("CharacterPrefab: could not instantiate the model");
                    return;
                }

                try
                {
                    instance.name = "Body";
                    var animator = instance.GetComponent<Animator>()
                                   ?? instance.AddComponent<Animator>();
                    animator.avatar = avatar;
                    // AND NOW A CONTROLLER, WHICH IS THE WHOLE VISIBLE FIX.
                    //
                    // The paragraph below is kept because its lesson is real,
                    // but its DECISION was wrong and the still is what says so:
                    // the player stands in the FBX's bind pose with both arms
                    // out at 119 degrees, because nothing has ever animated
                    // this body. The bracket proves our code is not doing it —
                    // `preArmDrop=118.6` sampled before a single line of
                    // `CharacterRig` runs, `liveArmDrop=118.6` after, the same
                    // number to a tenth of a degree.
                    //
                    // "An empty state machine would only fight it" was true of
                    // an EMPTY one. Forty-one clips were imported and audited
                    // every build and not one was ever played — `clips=44`
                    // reported as a success four days running. A breathing idle
                    // and a walk cycle are the difference between a person and
                    // a mannequin sliding along a pavement, and no amount of
                    // procedural lean substitutes for either.
                    //
                    // `CharacterRig.PoseIsDriven` was written for exactly this
                    // and has been false since the day it was added: with a
                    // controller present it now takes the composing branch it
                    // was designed for, and the rest-restore stands down
                    // because something else genuinely is driving the pose.
                    // BUILT ONCE PER ARCHETYPE AND SHARED within it — the
                    // cache stops `CreateAnimatorControllerAtPath` landing
                    // twice on one path, which is a failure mode nobody
                    // would read as "too many bodies". Which archetype a
                    // body gets is a function of its model name, so the
                    // same body walks the same way every build.
                    var gaitStem = System.IO.Path.GetFileNameWithoutExtension(modelPath);
                    animator.runtimeAnimatorController = LocomotionFor(gaitStem);
                    //
                    // AND THAT CONTRACT HAD A SHARP EDGE NOBODY HAD WRITTEN
                    // DOWN. An Animator with no controller drives nothing, so
                    // `CharacterRig` is the only thing writing these bones —
                    // which is intended — but `CharacterRig` decided whether to
                    // restore its rest pose by asking whether an Animator
                    // EXISTED. One does. It therefore took neither branch,
                    // never reset, and composed every frame onto its own
                    // previous output until the player was upside down in
                    // mid-air. Eight builds.
                    //
                    // The arrangement is still right. What was missing is that
                    // "there is an Animator" and "something is driving the
                    // pose" are different questions, and this is the line that
                    // makes them different.
                    animator.applyRootMotion = false;
                    // ALWAYS ANIMATE, and the reading is exact enough to name
                    // the cause. With the instrument finally scoped to one body,
                    // the bracket came back `restArmDrop=90.0 preArmDrop=90.0
                    // liveArmDrop=87.4` — a T-pose, to a tenth, on both sides of
                    // our solve, while `clipsBound=3` and `speedDriven=True` say
                    // the controller exists and is being driven.
                    //
                    // EXACTLY 90.0 IS THE TELL. A clip being evaluated would
                    // land anywhere; it would not land on the bind pose to a
                    // tenth of a degree. So the Animator is not writing these
                    // bones at all, and `CullUpdateTransforms` is the setting
                    // that does precisely that: it skips retargeting whenever no
                    // camera reports the renderer visible.
                    //
                    // The sim does not render a live camera every frame — it
                    // calls `cam.Render()` on demand into a RenderTexture for
                    // each still and each A/B probe — so `isVisible` is false
                    // for most of the run and the body freezes in its bind pose
                    // between shots. That is a correct optimisation meeting a
                    // renderer nobody is continuously looking at.
                    //
                    // One body. The saving `CullUpdateTransforms` buys is a
                    // retarget we want to happen anyway, and paying it always is
                    // the difference between a character and a mannequin.
                    animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;

                    var stem = System.IO.Path.GetFileNameWithoutExtension(modelPath)
                        .Replace(" ", "");
                    var mine = $"{ResourceDir}/Body_{stem}.prefab";
                    PrefabUtility.SaveAsPrefabAsset(instance, mine, out bool ok);
                    if (ok) Variants++;
                    // AND THE DEFAULT NAME TOO, so every gate and every caller
                    // that already says `Characters/Body` keeps working. Two
                    // files rather than a rename, because a rename would break
                    // the fallback path on the run that introduces it.
                    if (isDefault)
                        PrefabUtility.SaveAsPrefabAsset(instance, BodyPrefab, out _);
                    // PER-BODY FACTS ONLY. `ClipsBound` and `ControllerWhy`
                    // used to sit on this line and they are CANONICAL-ONLY
                    // statics — written under `if (canonical)`, as the comment
                    // at the bottom of `MakeController` says outright — while
                    // this line prints once per body. So the six bodies built
                    // before the canonical controller showed `clipsBound=-1
                    // controller=not_tried`, the eight built after showed
                    // `clipsBound=3 controller=ok`, and NEITHER group was
                    // describing its own body: one half was reading the
                    // initialiser and the other half was reading somebody
                    // else's result. It reads as six broken bodies, which is
                    // what it was read as on 21 August.
                    //
                    // A last-wins static printed per item is the `namesTracked`
                    // fault with a loop around it. They are whole-run facts, so
                    // they go on their own line, once.
                    Debug.Log($"CharacterPrefab: wrote {mine} ok={ok} "
                              + $"avatar={avatar.name} human={avatar.isHuman}");
                }
                finally
                {
                    Object.DestroyImmediate(instance);
                }

                AssetDatabase.SaveAssets();
            }
            catch (System.Exception e)
            {
                // Diagnostic, never fatal — it runs inside the one entry point
                // the whole Windows pipeline goes through.
                Debug.Log($"CharacterPrefab: FAILED {e.GetType().Name}: {e.Message}");
            }
        }

        /// ONE BLEND TREE ON SPEED: standing, walking, running.
        ///
        /// Deliberately the smallest thing that stops the body being a statue,
        /// and deliberately keyed on a quantity `CharacterRig` already has.
        /// Everything else the clips can do — the greeting, the flinch, the
        /// smoke, sitting at a counter — lives in the activity states below,
        /// which arrived as the later layer this paragraph once promised
        /// (activities first, the reaction set on 21 Aug).
        ///
        /// THRESHOLDS FROM THE GAME, NOT INVENTED. `Rig`'s own gait model and
        /// the walker's `MoveSpeed` put an ordinary walk at about 1.4 m/s,
        /// which is also the figure `Witnesses` passes to `Perception.InSight`
        /// as `subjectSpeed` for a person walking. The run threshold is the
        /// sprint speed the player controller already uses. If either moves,
        /// these are wrong and the frame will show it.
        ///
        /// WRAPPED, AND FAILING SOFT ON PURPOSE. This is Editor-only API that
        /// cannot be compiled outside CI, so a mistake here would otherwise
        /// take down the one entry point the whole Windows pipeline goes
        /// through — twenty-eight minutes to learn a method name. A null
        /// return leaves the body exactly as it was before this change and
        /// says why on the done line, which is a bad frame instead of no
        /// frames at all.
        static RuntimeAnimatorController BuildLocomotion(string arch, string idleKey)
        {
            // The default:idle pair keeps the historic asset path and is the
            // one that writes the done-line statics — every gate and every
            // landed verdict has watched THAT controller, and a variant
            // renaming it out from under them would read as the controller
            // vanishing. Variants get their own assets and their own log
            // line each.
            bool canonical = arch == "default" && idleKey == "idle";
            var assetPath = canonical
                ? ControllerPath
                : $"{ResourceDir}/Body_{arch}_{idleKey}.controller";
            if (canonical) ClipsBound = 0;
            try
            {
                // FALLBACK CHAINS, so an archetype whose clips have not
                // landed yet is byte-identical to the default — which is
                // the whole trick of writing this before the re-pick runs.
                AnimationClip idle, walk;
                if (arch == "old")
                {
                    idle = ClipFor("idle_old") ?? ClipFor("idle");
                    walk = ClipFor("walk_old") ?? ClipFor("walk");
                }
                else
                {
                    idle = ClipFor(idleKey) ?? ClipFor("idle");
                    walk = ClipFor("walk");
                }
                var run = ClipFor("run");
                if (idle == null)
                {
                    // WITHOUT AN IDLE THERE IS NO CONTROLLER WORTH HAVING. A
                    // tree whose zero-speed pose is a walk cycle looks worse
                    // than the statue, so this refuses rather than half-doing
                    // it — and says which clip was missing.
                    if (canonical) ControllerWhy = "no idle clip under Assets/Characters";
                    return null;
                }

                var controller = AnimatorController.CreateAnimatorControllerAtPath(assetPath);
                if (controller == null)
                {
                    if (canonical) ControllerWhy = "could not create controller asset";
                    return null;
                }
                controller.AddParameter(SpeedParam, AnimatorControllerParameterType.Float);

                var state = controller.CreateBlendTreeInController("Locomotion", out BlendTree tree, 0);
                tree.blendType = BlendTreeType.Simple1D;
                tree.blendParameter = SpeedParam;
                // Explicit, because automatic thresholds spread the children
                // evenly over 0..1 and would put a full run at one metre per
                // second — the clips would play, at the wrong speeds, which is
                // the kind of wrong that looks like a physics bug.
                tree.useAutomaticThresholds = false;

                int bound = 0;
                tree.AddChild(idle, 0f);   bound++;
                if (walk != null) { tree.AddChild(walk, 1.4f); bound++; }
                if (run != null) { tree.AddChild(run, 4.0f); bound++; }
                if (canonical) ClipsBound = bound;

                // THE ACTIVITY STATES (town-plan T3, "visible purpose").
                //
                // Jafar's harvest landed argue, phone_box, lean_wall, carry,
                // carry_bag, drink, smoke, sit, talk and greet, and NOTHING
                // LOADED ANY OF THEM — clips on disk with no consumer, which
                // is rule 6 in its purest form. These states give them one.
                //
                // UNCONNECTED BY DESIGN. A transition graph over ten states
                // needs conditions, exit times and a parameter per branch,
                // all built blind in an editor script with no inspector to
                // check it in; `Animator.CrossFade` plays a state by hash and
                // needs none of that, so the graph stays one blend tree plus
                // a handful of islands the rig can jump to and come back
                // from. The rig checks `HasState` first, so a clip that never
                // landed is a body that keeps walking rather than a warning
                // every frame.
                //
                // ON EVERY CONTROLLER, AND THE FIRST VERSION SAID CANONICAL
                // ONLY — measured wrong within one build. The reasoning was
                // "the variants exist to vary idle and walk, and ten more
                // states each would multiply the asset count for nothing",
                // which ignored that the idle variant is HASHED PER PERSON:
                // three variants plus the old archetype means roughly two
                // people in three are on a controller that had no activity
                // states at all, and `HasState` correctly refused them. The
                // run said it in one number — 81 confabs, `activityPeak=1`.
                //
                // The states are nodes pointing at clips that already exist,
                // so four controllers' worth is a rounding error against the
                // clips themselves.
                int states = 0;
                foreach (var slot in ActivitySlots)
                {
                    var clip = ClipFor(slot);
                    if (clip == null) continue;
                    var st = controller.layers[0].stateMachine.AddState(
                        Ledger.Game.CharacterRig.ActivityStatePrefix + slot);
                    st.motion = clip;
                    states++;
                }
                ActivityStates = states;
                // AND THE DENOMINATOR, which the first version also omitted
                // while its own commit message quoted the rule about zeros
                // needing one. `activityPeak=1` could mean the wire is broken
                // or the street is quiet; with this line beside it, "no
                // states were built" stops reading like "nobody did
                // anything".
                Debug.Log($"CharacterPrefab: activity states {states} of "
                          + $"{ActivitySlots.Length} on {arch}:{idleKey}");

                controller.layers[0].stateMachine.defaultState = state;

                // THE IK PASS, WITHOUT WHICH `OnAnimatorIK` NEVER FIRES AT ALL.
                //
                // This is the setting that makes foot IK possible rather than
                // the foot IK itself, and it belongs here because a controller
                // is built in code and has no inspector anybody can tick. It
                // defaults OFF, so `FootIk` would have shipped as a component
                // whose one method is never called — a system built, plausible
                // and never once running, which is rule 6 and has happened to
                // the noise ring and the caption bar before.
                //
                // `controller.layers` RETURNS A COPY, which is the trap in this
                // API and is why the line above it works by luck: mutating a
                // reference type reached through the copy (a state machine)
                // reaches the real thing, and assigning a value field (a bool)
                // on the copy does not. So the array is taken, changed, and
                // assigned back. `FootIk` reports `ikFrames`, so a build where
                // this silently failed says so in a number rather than in a
                // picture of feet sinking into the road.
                var layers = controller.layers;
                layers[0].iKPass = true;
                controller.layers = layers;

                AssetDatabase.SaveAssets();
                if (canonical)
                    ControllerWhy = $"ok (idle{(walk != null ? "+walk" : "")}{(run != null ? "+run" : "")})";
                // Every variant says what it is actually made of — the
                // done-line statics describe only the canonical controller,
                // so a variant quietly falling back to shared clips (the
                // expected state until the re-pick lands) is visible here
                // and nowhere else.
                Debug.Log($"CharacterPrefab: locomotion {arch}:{idleKey} -> "
                          + $"idle={idle.name} walk={(walk != null ? walk.name : "none")} "
                          + $"run={(run != null ? run.name : "none")} at {assetPath}");
                return controller;
            }
            catch (System.Exception e)
            {
                if (canonical)
                {
                    ControllerWhy = $"{e.GetType().Name}: {e.Message}";
                    ClipsBound = 0;
                }
                Debug.Log($"CharacterPrefab: locomotion {arch}:{idleKey} FAILED "
                          + $"{e.GetType().Name}: {e.Message}");
                return null;
            }
        }

        /// The clip whose file carries this key, e.g. `idle` from
        /// `idle__Breathing Idle_<guid>.fbx`.
        ///
        /// Off the KEY rather than the Mixamo title, because the key is the
        /// name this project chose and `_picks.json` records, while the title
        /// is whatever Adobe called it that year. `__preview__` clips are
        /// Unity's own scratch objects and are not animations anybody asked
        /// for — including one would bind a body to an editor artefact.
        static AnimationClip ClipFor(string key)
        {
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { "Assets/Characters" }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var file = System.IO.Path.GetFileName(path);
                int split = file.IndexOf("__", System.StringComparison.Ordinal);
                if (split < 0 || file.Substring(0, split) != key) continue;
                foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
                {
                    var clip = obj as AnimationClip;
                    if (clip != null && !clip.name.StartsWith("__preview__")) return clip;
                }
            }
            return null;
        }

        static Avatar AvatarOf(string path)
        {
            foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                var avatar = obj as Avatar;
                if (avatar != null && avatar.isValid && avatar.isHuman) return avatar;
            }
            return null;
        }
    }
}
