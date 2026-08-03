using System.Collections.Generic;

namespace Ledger.Core
{
    /// WHAT THE PLAYER JUST ASSERTED, IF ANYTHING.
    ///
    /// WHY THIS EXISTS. `ConversationEngine.ProcessClaim` checks a claim
    /// against what somebody knows, raises suspicion on a contradiction and
    /// lowers it when the story checks out. `GossipMill.PlayerClaims` records
    /// what the player has told people so the street can carry it. Both are
    /// written, both are tested in `SimHarness`, and both have sat on the reach
    /// ledger with the same note: *"the player asserting something the street
    /// can then carry is the spine of `law as a tool`, and nothing in the game
    /// yet lets them make a claim."*
    ///
    /// Nothing let them make a claim because nothing turned a sentence into a
    /// `Fact`. That is this file, and it is the missing inch between a typed
    /// line and the entire information layer.
    ///
    /// LEXICAL, NOT MODEL. The router asks a model when a lexical pass fails,
    /// and this deliberately does not. A claim moves suspicion and enters the
    /// permanent record of what the player has said; a model that hallucinates
    /// one produces an alibi the player never gave, gets caught contradicting a
    /// witness, and raises suspicion over a sentence that was never typed. A
    /// missed claim costs nothing and can be typed again. The two errors are
    /// not remotely symmetric, so this only fires on shapes it is sure of.
    ///
    /// THE PLACES COME FROM THE CALLER. A vocabulary invented here would drift
    /// from the map the moment a district is added — the same fault as a metric
    /// whose scope is "every TextMesh in the scene". The game passes the names
    /// it actually has.
    public static class Claims
    {
        /// The key `Fact` has always used for where somebody was, quoted from
        /// the example in `Fact`'s own summary and from the harness that has
        /// exercised this path for months: `player.location_d2_evening`.
        public static string LocationKey(GameTime when) =>
            $"location_d{when.Day}_{when.Slot.ToString().ToLowerInvariant()}";

        /// The openers that mean "I am telling you where I was". First person
        /// and past tense, both required.
        ///
        /// "were you at" and "he was at" must not match, and that is not
        /// pedantry: a question is the opposite of a claim, and attributing
        /// somebody else's whereabouts to the player would file an alibi they
        /// never offered.
        static readonly string[] Openers =
        {
            "i was at ", "i was in ", "i was over at ", "i was round at ",
            "i was down at ", "i was up at ", "ive been at ", "i have been at ",
            "i spent the evening at ", "i spent the night at ",
        };

        // WRITTEN THE WAY THE INPUT ARRIVES, NOT THE WAY IT IS TYPED. `Extract`
        // strips apostrophes before matching, so an opener spelled "i've been
        // at" can never match anything — the normalisation happens on one side
        // of a comparison and the table has to live on that side too. Caught by
        // the test named for the tense, which is what tests in a compiling
        // layer are for.

        /// The vocabulary, built from the map the game actually has.
        ///
        /// Two forms per place: the full name without its article — "hook
        /// street pub" — and the last word, "pub", because that is how people
        /// speak. The short form is only registered when it is UNIQUE: three
        /// places on this map end in "corner", and letting the north corner
        /// answer to "corner" would file an alibi naming a place the player did
        /// not say. An ambiguous alibi is worse than none, because it can be
        /// contradicted by a witness to a different place entirely.
        public static Dictionary<string, string> KnownPlaces()
        {
            var full = new Dictionary<string, string>();
            var shortCount = new Dictionary<string, int>();
            var shortId = new Dictionary<string, string>();
            foreach (var p in HookMap.Places)
            {
                if (p == null || string.IsNullOrEmpty(p.Name)) continue;
                string n = p.Name.ToLowerInvariant();
                if (n.StartsWith("the ", System.StringComparison.Ordinal)) n = n.Substring(4);
                full[n] = p.Id;
                int sp = n.LastIndexOf(' ');
                string last = sp < 0 ? n : n.Substring(sp + 1);
                shortCount[last] = shortCount.TryGetValue(last, out var c) ? c + 1 : 1;
                shortId[last] = p.Id;
            }
            foreach (var kv in shortCount)
                if (kv.Value == 1 && !full.ContainsKey(kv.Key)) full[kv.Key] = shortId[kv.Key];
            return full;
        }

        /// Turn a typed line into a claim about where the player was, or null.
        ///
        /// `places` maps a spoken name to the id the world uses — "the anchor"
        /// to "anchor" — so the caller owns the vocabulary and this owns the
        /// grammar.
        public static Fact Extract(string said, GameTime now, IDictionary<string, string> places)
        {
            if (string.IsNullOrEmpty(said) || places == null) return null;
            string s = " " + said.ToLowerInvariant().Replace(",", " ").Replace(".", " ")
                                 .Replace("'", "").Replace("  ", " ");

            // A DENIAL IS NOT A CLAIM THIS MODEL CAN HOLD, and the reason is
            // worth writing down because the obvious encoding is actively
            // harmful. "I was never at the warehouse" would have to become a
            // value like `not_warehouse`, and `CheckClaim` compares values for
            // equality — so a witness who knows the player was at the CINEMA
            // would read `cinema != not_warehouse` as a contradiction and the
            // player would be caught lying about something they were telling
            // the truth about. Skipped, deliberately, until `Fact` can carry a
            // negation. Nothing is lost: the player simply has to say where
            // they were, which is what an alibi is.
            if (s.Contains(" never ") || s.Contains(" wasnt ") || s.Contains(" was not ")
                || s.Contains(" nowhere near "))
                return null;

            foreach (var opener in Openers)
            {
                // THE LEADING SPACE IS PART OF THE SEARCH AND NOT PART OF THE
                // OPENER. `s` is prefixed with a space so that "i was at" only
                // matches at a word boundary — otherwise "hawaii was at" would
                // — and the offset has to account for it. Getting this wrong by
                // one produced a tail of "t the anchor" and no match at all,
                // which the first test caught in a second because it is a Core
                // test rather than a 28-minute round trip.
                int i = s.IndexOf(" " + opener, System.StringComparison.Ordinal);
                if (i < 0) continue;
                string tail = s.Substring(i + 1 + opener.Length);
                foreach (var kv in places)
                {
                    if (string.IsNullOrEmpty(kv.Key)) continue;
                    string name = kv.Key.ToLowerInvariant();
                    // Anchored at the START of what follows the opener, so
                    // "I was at the pub after I left the docks" claims the pub
                    // and not the docks. The first place named after "I was at"
                    // is the one being claimed; everything after it is a story.
                    if (tail.StartsWith(name, System.StringComparison.Ordinal)
                        || tail.StartsWith("the " + name, System.StringComparison.Ordinal))
                        return new Fact("player", LocationKey(now), kv.Value);
                }
            }
            return null;
        }
    }
}
