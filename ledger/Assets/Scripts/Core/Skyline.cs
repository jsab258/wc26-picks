using System.Collections.Generic;
using System.Globalization;

namespace Ledger.Core
{
    /// WHAT THE HORIZON IS MADE OF, AND WHETHER IT IS STANDING ON ANYTHING.
    ///
    /// WHY IT EXISTS. Two faults in the same band, both found by a person
    /// opening a JPEG and neither visible to any of the twenty gates:
    ///
    ///   * the far towers were modern glass — a silhouette nobody chose, in a
    ///     town whose premise is British and LATE-ANALOG. Nothing measured
    ///     what KIND of shape stood there, so "the skyline is period" could
    ///     only ever be a claim;
    ///   * eight of the twenty-three stood off the edge of the ground plane
    ///     and hung in open sky. Nothing measured whether a block had any
    ///     ground under it.
    ///
    /// The repair for a picture-found fault is a number (rule 4), so this is
    /// the tally the placement writes as it goes and the string the verdict
    /// prints. It lives in Core because a formatter written in the Game layer
    /// ships unrun — the top layer does not compile locally and an unrun
    /// formatter printing a plausible string is the silent-instrument
    /// failure this project keeps a list of.
    ///
    /// WHAT STATISTIC EACH NUMBER IS, said plainly:
    ///
    ///   Kinds     a COUNT per silhouette kind over every block placed this
    ///             run, with the total as its denominator. Not a peak and
    ///             not a sample: the band is built once.
    ///   Foot      worst / median / n. The WORST is the block whose foot
    ///             deviates furthest from the ground plane IN EITHER
    ///             DIRECTION, printed signed — a block hanging 4m up and one
    ///             sunk 4m are equally wrong and a max of the raw value
    ///             would only ever see the first. Unbounded: the fault it
    ///             was written for was tens of metres, so it must not
    ///             saturate. The MEDIAN sits beside it because a peak
    ///             answers "did it ever" and cannot answer "is the band
    ///             seated" (a median cannot answer the first, either, which
    ///             is why both print).
    ///   WorstAt   the NAME and map position of the block the worst came
    ///             from, so the next reader can go and look at that one
    ///             rather than at twenty-three.
    ///   ByEdge    seated/standing per compass edge of the band. Per EDGE
    ///             rather than per district because that is the axis the
    ///             fault actually varied on: the ground rectangle is 854m
    ///             wide by 443m deep, so the blocks that hung were the ones
    ///             on the north end and the ones that stood were on the
    ///             sides. A single figure would have hidden that, and a
    ///             per-district figure would have attributed a placement
    ///             fault to whichever camera happened to face it.
    ///
    /// FOOT GAP ALONE COULD NOT HAVE FOUND THE FAULT, which is worth saying
    /// because it was the number first asked for. Every block was seated at
    /// y=0 exactly; the ground simply was not there. `ByEdge` is the half
    /// that sees it, and the two ship together for that reason.
    public sealed class Skyline
    {
        /// One placed block. `Foot` is metres of the block's lowest vertex
        /// above the ground plane it is meant to stand on — signed, so
        /// negative is sunk. `Edge` is one of N/E/S/W.
        struct Block
        {
            public string Kind, Name, Edge;
            public float Foot, X, Z;
            public bool OnGround;
        }

        readonly List<Block> _blocks = new List<Block>();

        /// Record one block. Called once per placement, from the builder,
        /// with values read off the placed object rather than off the
        /// intent — a target height is not evidence that a mesh reached it.
        public void Add(string kind, string name, string edge,
                        float foot, float x, float z, bool onGround)
        {
            _blocks.Add(new Block
            {
                Kind = kind ?? "unnamed",
                Name = name ?? "unnamed",
                Edge = edge ?? "?",
                Foot = foot,
                X = x,
                Z = z,
                OnGround = onGround,
            });
        }

        public int Count { get { return _blocks.Count; } }

        /// `[crane:3,gasholder:1,...]/n23` — the composition of the band, so
        /// "the skyline is period" stops being a claim and becomes a reading.
        /// Sorted by kind so two runs can be diffed by eye. The trailing
        /// count is the denominator rule 3b asks for: an empty band and a
        /// band of one kind must not print the same.
        public string Kinds()
        {
            if (_blocks.Count == 0) return "[nothing-measured]/n0";
            var tally = new SortedDictionary<string, int>(System.StringComparer.Ordinal);
            foreach (var b in _blocks)
            {
                int n;
                tally.TryGetValue(b.Kind, out n);
                tally[b.Kind] = n + 1;
            }
            var sb = new System.Text.StringBuilder("[");
            bool first = true;
            foreach (var kv in tally)
            {
                if (!first) sb.Append(',');
                first = false;
                sb.Append(kv.Key).Append(':').Append(kv.Value.ToString(CultureInfo.InvariantCulture));
            }
            return sb.Append("]/n").Append(_blocks.Count.ToString(CultureInfo.InvariantCulture)).ToString();
        }

        /// `<worst>/<median>/n23` in metres. See the class note for which
        /// statistic each one is; both print because neither can answer the
        /// other's question.
        public string Foot()
        {
            if (_blocks.Count == 0) return "nothing-measured/n0";
            float worst = 0f;
            var vals = new List<float>(_blocks.Count);
            foreach (var b in _blocks)
            {
                vals.Add(b.Foot);
                if (Abs(b.Foot) > Abs(worst)) worst = b.Foot;
            }
            vals.Sort();
            float med = vals.Count % 2 == 1
                ? vals[vals.Count / 2]
                : (vals[vals.Count / 2 - 1] + vals[vals.Count / 2]) * 0.5f;
            return worst.ToString("0.00", CultureInfo.InvariantCulture) + "/"
                 + med.ToString("0.00", CultureInfo.InvariantCulture) + "/n"
                 + _blocks.Count.ToString(CultureInfo.InvariantCulture);
        }

        /// `<name>@<x>,<z>` — the block `Foot`'s worst came from. A worst
        /// with no name sends the next reader through the whole band.
        public string WorstAt()
        {
            if (_blocks.Count == 0) return "nothing-measured";
            var pick = _blocks[0];
            foreach (var b in _blocks) if (Abs(b.Foot) > Abs(pick.Foot)) pick = b;
            return pick.Name + "@"
                 + pick.X.ToString("0", CultureInfo.InvariantCulture) + ","
                 + pick.Z.ToString("0", CultureInfo.InvariantCulture);
        }

        /// `[N:6/6,E:5/5,S:0/0,W:7/7]` — seated over standing, per edge. All
        /// four edges print every run even when empty, so "no blocks on the
        /// south edge" and "six blocks and none of them seated" cannot read
        /// the same way.
        public string ByEdge()
        {
            var order = new[] { "N", "E", "S", "W" };
            var sb = new System.Text.StringBuilder("[");
            for (int i = 0; i < order.Length; i++)
            {
                int stood = 0, seated = 0;
                foreach (var b in _blocks)
                {
                    if (b.Edge != order[i]) continue;
                    stood++;
                    if (b.OnGround) seated++;
                }
                if (i > 0) sb.Append(',');
                sb.Append(order[i]).Append(':')
                  .Append(seated.ToString(CultureInfo.InvariantCulture)).Append('/')
                  .Append(stood.ToString(CultureInfo.InvariantCulture));
            }
            return sb.Append(']').ToString();
        }

        static float Abs(float v) { return v < 0f ? -v : v; }
    }
}
