using System;
using System.Collections.Generic;
using System.Text;
using Ledger.Core;

namespace Ledger.SaveChaos
{
    /// LAYER 4, TIME: what a save file does when it is not what the codec
    /// expected.
    ///
    ///     dotnet run -c Release --project ledger/SaveChaos
    ///     dotnet run -c Release --project ledger/SaveChaos -- --seed 7 --rounds 400
    ///
    /// WHY A FUZZER AND NOT MORE ROUND-TRIP TESTS. `SaveCodec` already has
    /// twenty checks in CoreTests and every one of them writes a save and reads
    /// it back. That proves the codec agrees with ITSELF, which is the one
    /// property a save file cannot be relied on to have — the interesting file
    /// is the one truncated by a full disk, half-written by a crash, edited by a
    /// player with a text editor, or produced by a build that no longer exists.
    /// None of those look like `Capture`'s output and all of them reach
    /// `Restore`.
    ///
    /// THE CONTRACT BEING TESTED is narrow and worth stating, because a fuzzer
    /// without a stated invariant just prints crashes and calls them findings:
    ///
    ///   1. `Restore` throws `SaveIncompatibleException` or it succeeds. Any
    ///      other exception is a bug, because the front end catches that one
    ///      type to decide what to tell the player — anything else escapes to
    ///      the top and the game dies on the load screen with a stack trace.
    ///   2. `PeekVersion` never throws at all. It is called BEFORE the game
    ///      commits to loading, to decide whether "Continue" is offered, so it
    ///      is reached by every corrupt file on the disk.
    ///   3. A save that LOADS produces a sane world. This is the one that
    ///      matters and the one round-trip tests structurally cannot ask: a
    ///      file that restores to day -2,000,000 with NaN patience is worse
    ///      than one that refuses to load, because it fails later, elsewhere,
    ///      and looks like a simulation bug.
    ///
    /// MUTATIONS ARE STRUCTURED, NOT RANDOM BYTES. Flipping bytes in JSON
    /// almost always yields a parse error, which exercises exactly one branch
    /// and reports a hundred passes for it. The mutations here keep the file
    /// PARSEABLE and change what it means — a key deleted, a number where a
    /// string was, a version from the future, a depth no recursive descent
    /// parser was built for. Random bytes are in there too, as one family of
    /// several rather than the whole test.
    static class Program
    {
        static int _checks, _failed;
        static readonly List<string> _findings = new List<string>();

        static void Main(string[] args)
        {
            int seed = ArgInt(args, "--seed", 1);
            int rounds = ArgInt(args, "--rounds", 300);

            string good = GoodSave();
            Console.WriteLine($"SaveChaos — seed {seed}, {rounds} round(s) per family, "
                              + $"baseline save {good.Length} bytes");

            // THE BASELINE FIRST, and it is not a formality. A fuzzer whose
            // baseline does not load is reporting on a broken harness, and
            // every mutation of a file that never worked "fails" identically.
            // Rule 3: suspect the instrument first.
            var baseline = Load(good);
            Require(baseline.outcome == Outcome.Loaded,
                    $"the UNMUTATED save loads (got {baseline.outcome}: {baseline.detail})");
            Require(baseline.sane, $"the unmutated save restores a sane world ({baseline.why})");
            if (_failed > 0)
            {
                Report();
                Environment.Exit(1);
            }

            var rng = new Random(seed);
            foreach (var family in Families())
            {
                int loaded = 0, refused = 0, wrong = 0, insane = 0;
                string firstWrong = null, firstInsane = null;
                for (int i = 0; i < rounds; i++)
                {
                    string mutated;
                    try { mutated = family.mutate(good, rng); }
                    // A MUTATOR THAT THROWS IS THE INSTRUMENT FAILING, not the
                    // codec, and the two must never be reported as the same
                    // thing. `breakrun.py` conflated them once and turned a
                    // SURVIVED into a RED.
                    catch (Exception e)
                    {
                        Require(false, $"mutator '{family.name}' threw: {e.GetType().Name}: {e.Message}");
                        break;
                    }
                    var r = Load(mutated);
                    if (r.outcome == Outcome.Refused) refused++;
                    else if (r.outcome == Outcome.Threw)
                    {
                        wrong++;
                        firstWrong ??= $"{r.detail} on: {Snip(mutated)}";
                    }
                    else
                    {
                        loaded++;
                        if (!r.sane) { insane++; firstInsane ??= $"{r.why} from: {Snip(mutated)}"; }
                    }
                }

                // ONE CHECK PER PROPERTY PER FAMILY, not one per sample. Three
                // hundred samples asserted individually is three hundred lines
                // of green that say the same thing once — the mistake that took
                // CoreTests to 14,953 checks before it was refactored back to
                // per-property assertions.
                Require(wrong == 0,
                        $"{family.name}: every refusal is a SaveIncompatibleException "
                        + $"({wrong} of {rounds} threw something else — {firstWrong})");
                Require(insane == 0,
                        $"{family.name}: every save that loads leaves a sane world "
                        + $"({insane} of {loaded} loaded insane — {firstInsane})");

                // AND THE FAMILY HAS TO ACTUALLY BITE. A mutator that silently
                // stopped mutating would report a perfect score forever, which
                // is the failure mode of every checker nobody has watched fail.
                Require(family.mustRefuseSome ? refused > 0 : true,
                        $"{family.name}: at least one mutation is rejected "
                        + $"(all {rounds} loaded — is the mutator still mutating?)");

                Console.WriteLine($"  {family.name,-22} loaded={loaded,-4} refused={refused,-4} "
                                  + $"wrongException={wrong} insane={insane}");
            }

            Report();
            Environment.Exit(_failed == 0 ? 0 : 1);
        }

        static void Report()
        {
            Console.WriteLine();
            if (_failed == 0)
            {
                Console.WriteLine($"save chaos ok — all {_checks} checks passed");
                return;
            }
            Console.WriteLine($"save chaos FAILED — {_failed} of {_checks} checks");
            foreach (var f in _findings) Console.WriteLine("  FAILED " + f);
        }

        static void Require(bool ok, string what)
        {
            _checks++;
            if (ok) return;
            _failed++;
            _findings.Add(what);
        }

        // ---- the harness -------------------------------------------------

        enum Outcome { Loaded, Refused, Threw }

        struct Result
        {
            public Outcome outcome;
            public string detail;
            public bool sane;
            public string why;
        }

        /// Load a candidate into a fresh authored world and judge the result.
        static Result Load(string json)
        {
            var r = new Result { sane = true, why = "ok" };

            // Contract 2 first, because it runs before the game commits to
            // anything and is therefore reached by every bad file on the disk.
            try { SaveCodec.PeekVersion(json); }
            catch (Exception e)
            {
                r.outcome = Outcome.Threw;
                r.detail = "PeekVersion threw " + e.GetType().Name;
                return r;
            }

            var wallet = new Wallet(300);
            var camp = new Campaign();
            var pk = new PlayerKnowledge();
            var secrets = new SecretsBook();
            var beats = new BeatBook();
            var (mill, _, _) = FreshMill();
            var debts = new DebtBook();
            GameTime now;
            try
            {
                now = SaveCodec.Restore(json, wallet, camp, pk, secrets, beats, mill, debts,
                                        out _);
            }
            catch (SaveIncompatibleException e)
            {
                r.outcome = Outcome.Refused;
                r.detail = e.Fault + ": " + e.Message;
                return r;
            }
            catch (Exception e)
            {
                r.outcome = Outcome.Threw;
                // THE FRAME, NOT JUST THE TYPE. "NullReferenceException" names
                // the symptom and every one of them looks identical in a
                // summary line; the first frame names the line to open. A
                // fuzzer that cannot tell you where is a fuzzer whose findings
                // get triaged by guessing.
                r.detail = e.GetType().Name + " at " + TopFrame(e) + ": " + e.Message;
                return r;
            }

            r.outcome = Outcome.Loaded;
            (r.sane, r.why) = Sane(now, wallet, camp);
            return r;
        }

        /// WHAT "SANE" MEANS, written down rather than felt.
        ///
        /// Every clause is a thing the rest of the game already assumes without
        /// checking — a day that counts up from one, a clock inside a day, a
        /// purse that is not negative, a patience that is a number. A restored
        /// world that breaks one of these does not fail here; it fails four
        /// systems away, on a later day, looking like a simulation bug.
        static (bool, string) Sane(GameTime now, Wallet wallet, Campaign camp)
        {
            // The ceiling is `SaveCodec`'s own, not a number invented here —
            // otherwise this check and the codec could drift apart and the
            // fuzzer would be measuring its own opinion. The derivation (an
            // `int` day used as a loop induction variable) is on the constant.
            if (now.Day < 1) return (false, $"day={now.Day}");
            if (now.Day > SaveCodec.MaxPlayableDay) return (false, $"day={now.Day} (absurd)");
            if (now.Hour < 0 || now.Hour > 23) return (false, $"hour={now.Hour}");
            if (now.Minute < 0 || now.Minute > 59) return (false, $"minute={now.Minute}");
            if (wallet.Clean < 0) return (false, $"clean={wallet.Clean}");
            if (wallet.Dirty < 0) return (false, $"dirty={wallet.Dirty}");
            if (double.IsNaN(camp.OutfitPatience) || double.IsInfinity(camp.OutfitPatience))
                return (false, $"patience={camp.OutfitPatience}");
            if (camp.JobsDone < 0 || camp.JobsMissed < 0)
                return (false, $"jobs={camp.JobsDone}/{camp.JobsMissed}");
            if (camp.DaysClosed < 0) return (false, $"daysClosed={camp.DaysClosed}");
            return (true, "ok");
        }

        /// A lived-in world, small enough to read and rich enough that the
        /// mutations have something to hit: money moved and laundered, a rumour
        /// that hopped, a secret used as a hook, a beat attended, a debt part
        /// paid.
        static string GoodSave()
        {
            var now = new GameTime(4, 21, 30);
            var (mill, _, _) = FreshMill();
            mill.Tick(now);
            var wallet = new Wallet(300);
            wallet.EarnDirty(180);
            wallet.Launder();
            var camp = new Campaign();
            camp.JobDone(); camp.JobMissed(); camp.CloseDay(0.4); camp.CloseDay(0.75);
            var pk = new PlayerKnowledge();
            pk.Learn(new Lead
            {
                HolderId = "rocco", HolderName = "Rocco",
                TopicKey = "player.location_d2_evening",
                Summary = "was at the warehouse", Confidence = 0.8, Sensitive = true,
            }, "you saw him watching", now);
            var secrets = new SecretsBook();
            var s = new Secret
            {
                Id = "rocco_skim", OwnerId = "rocco",
                Kind = SecretKind.Criminal, Summary = "the skim.",
            };
            secrets.Add(s);
            s.Learn("Lena", now);
            mill.UseHook("rocco", s, now);
            var beats = new BeatBook();
            var b = new Beat
            {
                Id = "tea", HostId = "Ada", Title = "Tea",
                Day = 3, StartHour = 22, EndHour = 24,
            };
            beats.Add(b);
            b.Restore(BeatState.Attended);
            var debts = new DebtBook();
            var d = new Debtor { Id = "sam", Name = "Sam", Amount = 120, Note = "stock" };
            debts.Add(d);
            d.Restore(false, true, 2);
            var extra = new Dictionary<string, object>
            {
                { "wearingCoat", true }, { "osseiSpawned", true },
            };
            return SaveCodec.Capture(now, wallet, camp, pk, secrets, beats, mill, debts, extra);
        }

        static (GossipMill, Gossiper, Gossiper) FreshMill()
        {
            var g = new SocialGraph();
            g.Link("rocco", "lena", 0.85);
            var mill = new GossipMill(g);
            var witness = new Gossiper("rocco", "Rocco", new MemoryStore("rocco"),
                                       new KnowledgeBase(), new SuspicionTracker(),
                                       "night", 0.6, 0.4, 0.5);
            var day = new Gossiper("lena", "Lena", new MemoryStore("lena"),
                                   new KnowledgeBase(), new SuspicionTracker(), "day");
            mill.Add(witness);
            mill.Add(day);
            mill.Witness("rocco", new Fact("player", "location_d2_evening", "warehouse"),
                         "the new owner was at the warehouse the night of the fire",
                         true, new GameTime(3, 20, 0));
            return (mill, witness, day);
        }

        // ---- the mutations -----------------------------------------------

        class Family
        {
            public string name;
            public Func<string, Random, string> mutate;
            /// Whether at least one mutation in this family MUST be rejected.
            /// False for families that legitimately produce loadable files —
            /// deleting an optional key is supposed to load, and demanding a
            /// refusal there would be demanding a bug.
            public bool mustRefuseSome;
        }

        static IEnumerable<Family> Families()
        {
            yield return new Family
            {
                name = "truncate",
                mustRefuseSome = true,
                // The full-disk and the killed-process case, and the one that
                // actually happens to players.
                mutate = (s, r) => s.Substring(0, 1 + r.Next(s.Length - 1)),
            };
            yield return new Family
            {
                name = "random bytes",
                mustRefuseSome = true,
                mutate = (s, r) =>
                {
                    var sb = new StringBuilder(s);
                    int n = 1 + r.Next(8);
                    for (int i = 0; i < n; i++)
                        sb[r.Next(sb.Length)] = (char)(32 + r.Next(94));
                    return sb.ToString();
                },
            };
            yield return new Family
            {
                name = "delete a key",
                mustRefuseSome = false,   // most keys are optional by design
                mutate = (s, r) => DropPair(s, r),
            };
            yield return new Family
            {
                name = "type confusion",
                mustRefuseSome = false,
                // A number where a string was and vice versa. THE FAMILY MOST
                // LIKELY TO FIND SOMETHING, because it keeps the file perfectly
                // well-formed and only breaks the codec's expectations — which
                // is exactly what an old build's save looks like.
                mutate = (s, r) => Retype(s, r),
            };
            yield return new Family
            {
                name = "absurd numbers",
                mustRefuseSome = false,
                // Contract 3's family. These parse, they load, and the question
                // is whether the world that comes out is one the game can run.
                mutate = (s, r) => Renumber(s, r),
            };
            yield return new Family
            {
                name = "version games",
                mustRefuseSome = true,
                mutate = (s, r) =>
                {
                    string[] v = { "999", "0", "-1", "\"two\"", "null", "1.5", "2.0" };
                    return ReplaceVersion(s, v[r.Next(v.Length)]);
                },
            };
            yield return new Family
            {
                name = "deep nesting",
                mustRefuseSome = false,
                // A recursive-descent parser meeting a file built to blow the
                // stack. It must come back as a refusal, not as a process that
                // dies without a message.
                mutate = (s, r) =>
                {
                    int depth = 200 + r.Next(2000);
                    var sb = new StringBuilder(s.Length + depth * 2);
                    sb.Append("{\"version\":2,\"deep\":");
                    for (int i = 0; i < depth; i++) sb.Append('[');
                    sb.Append('1');
                    for (int i = 0; i < depth; i++) sb.Append(']');
                    sb.Append('}');
                    return sb.ToString();
                },
            };
            yield return new Family
            {
                name = "duplicate keys",
                mustRefuseSome = false,
                mutate = (s, r) => Duplicate(s, r),
            };
            yield return new Family
            {
                name = "empty and blank",
                mustRefuseSome = true,
                mutate = (s, r) =>
                {
                    string[] junk = { "", "   ", "{}", "[]", "null", "0", "\"\"",
                                      "{\"version\":}", "{", "}" };
                    return junk[r.Next(junk.Length)];
                },
            };
        }

        /// Find the nth `"key": value` pair and hand it to `edit`, which
        /// returns the replacement text for the VALUE.
        ///
        /// Deliberately a scanner and not a parse-and-rewrite: reserialising
        /// through `MiniJson` would launder exactly the malformations this is
        /// trying to produce, and the result would be a test of MiniJson's
        /// output rather than of the codec's input.
        static string EditValue(string s, Random r, Func<string, string> edit,
                                bool deleteInstead = false)
        {
            var spots = new List<(int keyStart, int valStart, int valEnd)>();
            for (int i = 0; i < s.Length; i++)
            {
                if (s[i] != '"') continue;
                int keyStart = i;
                int keyEnd = s.IndexOf('"', i + 1);
                if (keyEnd < 0) break;
                i = keyEnd;
                int j = keyEnd + 1;
                while (j < s.Length && char.IsWhiteSpace(s[j])) j++;
                if (j >= s.Length || s[j] != ':') continue;
                j++;
                while (j < s.Length && char.IsWhiteSpace(s[j])) j++;
                if (j >= s.Length) break;
                int end = ValueEnd(s, j);
                if (end <= j) continue;
                spots.Add((keyStart, j, end));
            }
            if (spots.Count == 0) return s;
            var pick = spots[r.Next(spots.Count)];
            if (deleteInstead)
            {
                int cut = pick.valEnd;
                if (cut < s.Length && s[cut] == ',') cut++;
                return s.Substring(0, pick.keyStart) + s.Substring(cut);
            }
            string old = s.Substring(pick.valStart, pick.valEnd - pick.valStart);
            return s.Substring(0, pick.valStart) + edit(old) + s.Substring(pick.valEnd);
        }

        /// Where a JSON value ends, counting nesting and respecting strings.
        /// Not a parser — it only has to find the end of one value.
        static int ValueEnd(string s, int start)
        {
            int depth = 0;
            bool inStr = false;
            for (int i = start; i < s.Length; i++)
            {
                char c = s[i];
                if (inStr)
                {
                    if (c == '\\') { i++; continue; }
                    if (c == '"') inStr = false;
                    continue;
                }
                if (c == '"') { inStr = true; continue; }
                if (c == '{' || c == '[') depth++;
                else if (c == '}' || c == ']')
                {
                    if (depth == 0) return i;
                    depth--;
                }
                else if (c == ',' && depth == 0) return i;
            }
            return s.Length;
        }

        static string DropPair(string s, Random r) => EditValue(s, r, x => x, deleteInstead: true);

        static string Retype(string s, Random r) => EditValue(s, r, old =>
        {
            if (old.Length > 0 && old[0] == '"') return "12345";
            if (old.StartsWith("{")) return "\"was an object\"";
            if (old.StartsWith("[")) return "\"was an array\"";
            if (old == "true" || old == "false") return "\"maybe\"";
            if (old == "null") return "{}";
            return "\"" + old + "\"";           // a number becomes its own text
        });

        static string Renumber(string s, Random r)
        {
            string[] absurd =
            {
                "-1", "-2147483648", "2147483647", "9223372036854775807",
                "1e308", "-1e308", "0.1e-320", "99999999999999999999999999",
            };
            return EditValue(s, r, old =>
                old.Length > 0 && (char.IsDigit(old[0]) || old[0] == '-')
                    ? absurd[r.Next(absurd.Length)]
                    : old);
        }

        static string Duplicate(string s, Random r) => EditValue(s, r, old => old + "}, \"version\": 2");

        static string ReplaceVersion(string s, string v)
        {
            int i = s.IndexOf("\"version\"", StringComparison.Ordinal);
            if (i < 0) return s;
            int colon = s.IndexOf(':', i);
            if (colon < 0) return s;
            int end = ValueEnd(s, colon + 1);
            return s.Substring(0, colon + 1) + v + s.Substring(end);
        }

        /// The innermost `Ledger.` frame — the deepest line in our own code,
        /// which is where the fix goes. Framework frames above it are noise.
        static string TopFrame(Exception e)
        {
            foreach (var line in (e.StackTrace ?? "").Split('\n'))
            {
                var t = line.Trim();
                if (t.StartsWith("at Ledger.", StringComparison.Ordinal))
                    return t.Substring(3);
            }
            return "(no frame)";
        }

        static string Snip(string s) =>
            s.Length <= 160 ? s : s.Substring(0, 160) + "…";

        static int ArgInt(string[] args, string name, int fallback)
        {
            for (int i = 0; i + 1 < args.Length; i++)
                if (args[i] == name && int.TryParse(args[i + 1], out var v))
                    return v;
            return fallback;
        }
    }
}
