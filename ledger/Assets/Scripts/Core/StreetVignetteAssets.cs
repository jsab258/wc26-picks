using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Ledger.Core
{
    /// DID THE HELD BYTES REACH THE FRAME.
    ///
    /// WHY THIS EXISTS, in one measurement taken on 2 September: 37 props sat
    /// under `ledger/Assets/Props/base-mesh` and 14 generated pictures under
    /// `StreamingAssets/Decals/generated`, and a grep for `base-mesh` in
    /// either vignette file returned 0. Every frame the project had shipped
    /// was primitives. Nothing said so, because nothing counted. A prop
    /// nothing places and a picture nothing applies are inventory, not a
    /// street, and the number that tells the two apart is this one.
    ///
    /// BOTH HALVES OR NEITHER (rule 3b). `propsPlaced=0/23` and
    /// `propsPlaced=23/23` are different worlds and `0` alone is neither of
    /// them; a run where the plan asked for nothing prints the words
    /// `nothing measured` rather than a clean zero, because "the scene wants
    /// no props" and "the loader found none" have opposite next actions.
    ///
    /// THE ARITHMETIC AND THE STRING ARE HERE, not in the emitter, for the
    /// standing reason of 25 August: the Unity layer does not compile in the
    /// review container, so a tally written there ships UNRUN and an unrun
    /// formatter printing a plausible line is the silent-instrument failure.
    /// The emitter supplies membership and live state only: which piece, did
    /// the prefab load, was the PNG on disk, how tall did the mesh turn out.
    ///
    /// NOTE ON THE NAME `propsPlaced`. `AssetLibrary.PropsPlaced` already
    /// prints under that key on the SIM done line and counts every kit prop
    /// in the whole town with no denominator. This one is the vignette's, has
    /// a denominator, and every line it prints is prefixed `StreetVignette: `
    /// in the log and in the committed verdict, which is what tells the two
    /// apart. Said here because a grep for `propsPlaced=` finds both.
    public sealed class StreetVignetteAssets
    {
        sealed class Half
        {
            public int Asked, Landed;
            public readonly List<string> Absent = new List<string>();
            public string FirstWhy = "none";
            public readonly HashSet<string> Assets = new HashSet<string>(StringComparer.Ordinal);
        }

        readonly Half _props = new Half();
        readonly Half _decals = new Half();
        double _worstDelta = -1;
        string _worstAt = "none";

        /// How many absent names are listed before the line says so. Small
        /// because the verdict is read whole, and it ANNOUNCES ITSELF when it
        /// bites: a cap that outgrew its input once read as "three of five
        /// systems failed" when nothing was broken.
        public const int MaxNames = 6;

        Half Of(bool prop) => prop ? _props : _decals;

        /// THE DENOMINATOR, and it is recorded from the PLAN rather than from
        /// the loader's successes. Called once per mesh or decal piece before
        /// anything is loaded, so a run that dies halfway still prints what it
        /// was asked for.
        public void Ask(bool prop, string asset)
        {
            var h = Of(prop);
            h.Asked++;
            if (!string.IsNullOrEmpty(asset)) h.Assets.Add(asset);
        }

        /// It reached the scene: a prefab instantiated, or a picture bound to
        /// a quad. The numerator.
        public void Landed(bool prop) => Of(prop).Landed++;

        /// It did not, and WHY. The reason travels because "the prefab is not
        /// in Resources" and "the PNG has not been generated yet" are
        /// different amounts of work and read identically as a missing count.
        public void Absent(bool prop, string asset, string why)
        {
            var h = Of(prop);
            h.Absent.Add(Safe(asset));
            if (h.FirstWhy == "none") h.FirstWhy = Safe(why);
        }

        /// HOW FAR THE LOADED MESH IS FROM THE SIZE THE SCENE FILE SAYS IT
        /// IS, worst over the run, with the prop it happened on.
        ///
        /// NO BOUND HERE, ON PURPOSE (rule 2). Nothing has ever printed this
        /// series, so there is no number to fail against yet: ship the
        /// printer, read real runs, then set the bound from what it says. It
        /// exists because the scene file's `dims_m` were measured off the
        /// .glb by a script and the engine's importer is a second opinion
        /// about the same file, and a prop placed from dimensions that are
        /// not its own stands in the wrong place with every count green.
        public void NoteHeight(string name, double askedM, double gotM)
        {
            double d = Math.Abs(askedM - gotM);
            if (d > _worstDelta) { _worstDelta = d; _worstAt = Safe(name); }
        }

        /// THE WHOLE-RUN LINE. Whole-run numbers only: nothing per piece goes
        /// here, so a grep cannot merge one run's total with one prop's
        /// detail.
        public string Report()
        {
            if (_props.Asked == 0 && _decals.Asked == 0)
                return "assets nothing measured (the plan asked for no held prop and no decal)";
            var sb = new StringBuilder();
            sb.Append("assets propsPlaced=").Append(Frac(_props));
            sb.Append(" decalsApplied=").Append(Frac(_decals));
            // WHAT THE TWO NUMERATORS ARE COUNTING OVER, so a count of 23 out
            // of 23 cannot hide that it was one prop placed 23 times.
            sb.Append(" propAssets=").Append(N(_props.Assets.Count));
            sb.Append(" decalImages=").Append(N(_decals.Assets.Count));
            sb.Append(" propsAbsent=").Append(Names(_props));
            sb.Append(" decalsAbsent=").Append(Names(_decals));
            sb.Append(" propsAbsentWhy=").Append(_props.FirstWhy);
            sb.Append(" decalsAbsentWhy=").Append(_decals.FirstWhy);
            sb.Append(" propHeightMaxDeltaM=");
            if (_worstDelta < 0) sb.Append("nothing-measured");
            else sb.Append(_worstDelta.ToString("0.000", CultureInfo.InvariantCulture))
                   .Append("/at=").Append(_worstAt);
            return sb.ToString();
        }

        static string Frac(Half h) =>
            N(h.Landed) + "/" + N(h.Asked);

        static string N(int v) => v.ToString(CultureInfo.InvariantCulture);

        /// The absent names, comma separated with NO SPACES, capped, and the
        /// cap says when it bit and out of how many.
        static string Names(Half h)
        {
            if (h.Absent.Count == 0) return "none";
            var sb = new StringBuilder();
            for (int i = 0; i < h.Absent.Count && i < MaxNames; i++)
            {
                if (i > 0) sb.Append(',');
                sb.Append(h.Absent[i]);
            }
            if (h.Absent.Count > MaxNames)
                sb.Append(",(+").Append(N(h.Absent.Count - MaxNames))
                  .Append("more-of-").Append(N(h.Absent.Count)).Append(')');
            return sb.ToString();
        }

        /// No whitespace in a value: every reader of a `key=value` line in
        /// this project splits on whitespace and truncates in silence.
        static string Safe(string s)
        {
            if (string.IsNullOrEmpty(s)) return "unnamed";
            var sb = new StringBuilder(s.Length);
            foreach (var c in s) sb.Append(char.IsWhiteSpace(c) ? '-' : c);
            return sb.ToString();
        }
    }
}
