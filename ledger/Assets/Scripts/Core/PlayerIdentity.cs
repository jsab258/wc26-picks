using System.Collections.Generic;

namespace Ledger.Core
{
    /// Who the player is, and what this street calls them.
    ///
    /// Open since 24 July and delegated to me on the 27th. The name is **Tomas
    /// Vrba** — Marek's sister's boy, off the boat with one suitcase and a
    /// letter.
    ///
    /// WHY THIS ONE. It had to sit beside Sedlak, Brela, Farid, Halvard and
    /// Danica without sounding like it came from a different game, and it had to
    /// survive being said out loud a thousand times. Vrba is two syllables, hard
    /// to soften, and it is a WORD (willow, in the language the docks half-speak)
    /// — which is the kind of name a city shortens without affection.
    ///
    /// THE PART THAT IS ACTUALLY A DESIGN DECISION, and the reason this is a
    /// class rather than a constant: for two months the game has said "the new
    /// owner" everywhere, and I came to this expecting to find and replace it.
    /// That would have been wrong. **"The new owner" is not a placeholder. It is
    /// what people call you before they know you**, and this is a game about
    /// being known. So the name is something the street LEARNS, and what
    /// somebody calls you is a readout of where you stand with them:
    ///
    ///   the new owner  — they know the bar changed hands, not who you are
    ///   Vrba           — you are a fact on this street now
    ///   Tomas          — they have decided about you, and it was fine
    ///   Toma           — two or three people, ever
    ///
    /// That gradient costs nothing, uses relationship state that already exists,
    /// and turns "somebody used your first name" into a thing the player can
    /// notice happening. A find-and-replace would have thrown that away.
    public class PlayerIdentity
    {
        public string First = "Tomas";
        public string Diminutive = "Toma";
        public string Surname = "Vrba";
        /// What you are to somebody who has not placed you yet. Deliberately the
        /// same string the whole game already used.
        public string Unplaced = "the new owner";

        /// The uncle. Named in the founding premise; his book of debts is the
        /// inheritance, so his name is load-bearing and lives here too.
        public string BenefactorFirst = "Marek";
        public string BenefactorRelation = "your mother's brother";

        public string Full => $"{First} {Surname}";

        /// Deliberately NOT gendered anywhere in the writing. The name works
        /// either way, the street mostly uses the surname, and that keeps a
        /// later "who are you" option free rather than costing a rewrite.
        public const string GenderNote = "unset by design; the street uses the surname";

        /// What this person calls you, from what they know and how they feel.
        ///
        /// `knowsName` is the gate — closeness cannot promote a stranger, because
        /// somebody can like the look of you and still not know what to call you.
        public string AddressBy(bool knowsName, double closeness)
        {
            if (!knowsName) return Unplaced;
            if (closeness >= 0.75) return Diminutive;
            if (closeness >= 0.45) return First;
            return Surname;
        }

        /// How the player is referred to in a rumor — third person, by whoever is
        /// passing it on. Talk travels further than acquaintance does, so a
        /// rumor about you can carry your surname into mouths that have never
        /// met you. That is exactly how a name gets around a district.
        public string InTalk(bool streetKnowsName) =>
            streetKnowsName ? Surname : Unplaced;

        /// Does this person know what to call you? They do once they have
        /// remembered anything about you at all — which is the same moment the
        /// game starts treating them as somebody who has met you, so there is no
        /// second bookkeeping to keep in step.
        public static bool KnowsName(Gossiper g) =>
            g != null && g.Memory != null && g.Memory.Events.Count > 0;

        /// Convenience for the game layer: what this person calls you right now.
        public string AddressBy(Gossiper g) =>
            g == null ? Unplaced : AddressBy(KnowsName(g), g.Loyalty);

        public Dictionary<string, object> Capture() => new Dictionary<string, object>
        {
            { "first", First }, { "diminutive", Diminutive }, { "surname", Surname },
        };

        public void Restore(Dictionary<string, object> data)
        {
            if (data == null) return;
            var f = MiniJson.GetString(data, "first");
            var d = MiniJson.GetString(data, "diminutive");
            var s = MiniJson.GetString(data, "surname");
            if (!string.IsNullOrEmpty(f)) First = f;
            if (!string.IsNullOrEmpty(d)) Diminutive = d;
            if (!string.IsNullOrEmpty(s)) Surname = s;
        }
    }
}
