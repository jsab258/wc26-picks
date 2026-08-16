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
            int mannequins = 0;
            foreach (var path in BodyModels())
            {
                // The rig mannequins get no prefab at all, so they cannot be
                // worn, shipped, or picked by any code that ever greps
                // `Resources/Characters` — the same `IsMannequin` the runtime
                // pool asks, one implementation on purpose (its comment in
                // `RealBody` carries the story).
                if (Ledger.Game.RealBody.IsMannequin(
                        System.IO.Path.GetFileNameWithoutExtension(path)))
                {
                    mannequins++;
                    continue;
                }
                BuildOne(path, path == BodyModel);
            }
            Debug.Log($"CharacterPrefab: {Variants} body prefab(s) written, "
                      + $"{mannequins} rig mannequin(s) skipped");
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
                    Debug.Log($"CharacterPrefab: wrote {mine} ok={ok} "
                              + $"avatar={avatar.name} human={avatar.isHuman} "
                              + $"clipsBound={ClipsBound} controller={ControllerWhy}");
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
        /// Everything else the forty-one clips could do — the greeting, the
        /// flinch, the smoke, sitting at a counter — is a later layer, and
        /// building all of it before seeing one frame of a walk cycle would be
        /// the same mistake as the systems this project keeps finding unrun.
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
