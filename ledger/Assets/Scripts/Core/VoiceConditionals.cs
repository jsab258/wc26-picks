using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace Ledger.Core
{
    /// A CHARACTER'S VOICE, AS THE NUMBERS THE MODEL WANTS.
    ///
    /// A voice in this game is not a setting. It is six arrays computed once
    /// from a ten-second reference clip, and they are constants — the model's
    /// `prepare_conditionals` depends on the clip and not on the words, which
    /// is why the voice encoder never has to run on the player's machine at
    /// all. Nineteen of them are committed under `game-design/voice-conds/`,
    /// about 2.5 MB the whole way.
    ///
    /// THIS IS A SECOND FORMAT AND THAT IS DELIBERATE. The tools all read the
    /// `.npz` beside it, which is a zip of NumPy arrays — openable in C# only
    /// by writing a zip reader and a `.npy` header parser, both of which are
    /// exactly the kind of hand-rolled second implementation this project has
    /// been bitten by. The `.bin` is the same numbers in a layout with no
    /// parsing left in it, written from the SAME dictionary in the same call
    /// as the `.npz`, and `precompute-voices --selftest` reads both back for
    /// all nineteen voices and requires them to agree element for element.
    ///
    /// LITTLE-ENDIAN, WHICH IS NOT AN ASSUMPTION WORTH HIDING. `BinaryReader`
    /// is little-endian by definition rather than by platform, so the reader
    /// and the writer agree by construction on every machine this ships to.
    public class VoiceConditionals
    {
        /// What the writer stamps on the front. A file that does not start
        /// with this is refused by name rather than misread into nonsense —
        /// a truncated or half-written voice must not become a quiet wrong
        /// answer, because a wrong conditioning array is a character speaking
        /// in somebody else's voice and nothing throws.
        public const string Magic = "LDGRVOICE1";

        /// The six arrays, by the names the Python wrote. Kept flat rather
        /// than split into a t3 half and a gen half, because the split lives
        /// in the names and inventing a second one here would be a third
        /// description of the same data.
        readonly Dictionary<string, Array3> _by = new Dictionary<string, Array3>();

        /// One array: its numbers and the shape they were written in.
        ///
        /// The shape travels WITH the numbers rather than being remembered by
        /// the caller. The prompt lengths differ per voice — of the nineteen
        /// committed, six distinct lengths, and one has 419 mel frames
        /// against 418 tokens' worth because the extractor and the tokeniser
        /// disagree by a frame on that clip. Anything that assumes a shape
        /// instead of reading it is right for eighteen voices.
        public class Array3
        {
            public int[] Shape;
            public float[] Floats;      // null when the array is integer
            public long[] Longs;        // null when the array is float

            public int Count
            {
                get { return Floats != null ? Floats.Length : (Longs != null ? Longs.Length : 0); }
            }

            /// The last dimension, which is what every consumer here wants —
            /// the prompt's length, the embedding's width.
            public int Rows { get { return Shape != null && Shape.Length > 1 ? Shape[1] : Count; } }
        }

        public int Count { get { return _by.Count; } }

        public IEnumerable<string> Names { get { return _by.Keys; } }

        public Array3 Get(string name)
        {
            Array3 a;
            return _by.TryGetValue(name, out a) ? a : null;
        }

        public bool Has(string name) { return _by.ContainsKey(name); }

        /// Read one voice. Returns null and says why rather than throwing,
        /// because this runs while a scene is loading and a missing voice is
        /// a character who cannot speak live rather than a crash.
        ///
        /// `why` is set on every failure path INCLUDING the ones that come
        /// out of the reader itself: a file that stops halfway through an
        /// array is the shape a half-finished copy takes, and "the voice did
        /// not load" and "the voice loaded wrong" must not look the same from
        /// the outside.
        public static VoiceConditionals Load(byte[] bytes, out string why)
        {
            why = null;
            if (bytes == null || bytes.Length < Magic.Length + 4)
            {
                why = bytes == null ? "no data" : "too short to be a voice file ("
                    + bytes.Length + " bytes)";
                return null;
            }
            for (int i = 0; i < Magic.Length; i++)
            {
                if (bytes[i] != (byte)Magic[i])
                {
                    why = "not a voice file; expected " + Magic + " on the front";
                    return null;
                }
            }

            var v = new VoiceConditionals();
            try
            {
                using (var ms = new MemoryStream(bytes))
                using (var r = new BinaryReader(ms, Encoding.ASCII))
                {
                    r.ReadBytes(Magic.Length);
                    int arrays = r.ReadInt32();
                    if (arrays < 0 || arrays > 64)
                    {
                        why = "claims " + arrays + " arrays, which is not a voice";
                        return null;
                    }
                    for (int a = 0; a < arrays; a++)
                    {
                        int nameLen = r.ReadInt32();
                        if (nameLen < 1 || nameLen > 256)
                        {
                            why = "array " + a + " has a name length of " + nameLen;
                            return null;
                        }
                        string name = Encoding.ASCII.GetString(r.ReadBytes(nameLen));
                        int code = r.ReadInt32();
                        int rank = r.ReadInt32();
                        if (rank < 1 || rank > 8)
                        {
                            why = name + " has rank " + rank;
                            return null;
                        }
                        var shape = new int[rank];
                        long count = 1;
                        for (int d = 0; d < rank; d++)
                        {
                            shape[d] = r.ReadInt32();
                            if (shape[d] < 0) { why = name + " has a negative dimension"; return null; }
                            count *= shape[d];
                        }
                        if (count > 8 * 1024 * 1024)
                        {
                            why = name + " claims " + count + " numbers";
                            return null;
                        }
                        var arr = new Array3 { Shape = shape };
                        if (code == 0)
                        {
                            arr.Floats = new float[count];
                            for (long i = 0; i < count; i++) arr.Floats[i] = r.ReadSingle();
                        }
                        else if (code == 1)
                        {
                            arr.Longs = new long[count];
                            for (long i = 0; i < count; i++) arr.Longs[i] = r.ReadInt64();
                        }
                        else
                        {
                            why = name + " has unknown type code " + code;
                            return null;
                        }
                        v._by[name] = arr;
                    }
                }
            }
            catch (EndOfStreamException)
            {
                // THE SHAPE A HALF-WRITTEN FILE TAKES. Every length above is
                // read from the file itself, so a truncated copy runs off the
                // end rather than reporting anything wrong — which is why this
                // is caught by name and turned into a reason.
                why = "the file ends part-way through an array: truncated or "
                    + "still being written";
                return null;
            }
            catch (IOException e)
            {
                why = "unreadable: " + e.Message;
                return null;
            }
            return v;
        }
    }
}
