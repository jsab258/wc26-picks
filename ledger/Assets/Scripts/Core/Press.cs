namespace Ledger.Core
{
    /// M21: THE ONE CHANNEL THAT REACHES PEOPLE WHO WERE NOT THERE.
    ///
    /// The last named gap in the notoriety row, and it is a real hole rather
    /// than a decoration. Every other way information moves in this game is
    /// person to person: somebody sees a thing, tells somebody, and the telling
    /// decays with each hop. That is the moat and it is right. It also means
    /// that today, a killing in an empty alley is known to nobody for ever, and
    /// notoriety — the number that decides whether a doorman has heard of you —
    /// can only ever be bought with witnesses.
    ///
    /// A city has a newspaper. It is the one channel with no hops, no tie
    /// strength and no proximity: everybody who reads it learns the same thing
    /// on the same morning. That is exactly why it is dangerous, and why almost
    /// everything must fail to reach it.
    ///
    /// THREE RULES, AND EACH ONE IS A REFUSAL.
    ///
    /// **It does not know secrets.** A paper prints what the police and the
    /// street already have. So a story NAMES the player only when somebody
    /// would already say it to a detective — `HomicideBook.TestimonyGrade`, the
    /// same bar `Informing` weighs an accusation against and the same one Act
    /// III uses. Otherwise it runs the act without the name, which is the more
    /// interesting outcome anyway: the town knows a man was killed on Hook
    /// Street and does not know it was you.
    ///
    /// **It is not an eyewitness.** Reading a thing is weaker than seeing it,
    /// and the game already has a number for a channel that carries less than
    /// being in the room — `PhoneBook.FidelityOnTheLine`, with a comment saying a
    /// voice on a line is not a face across a table. A column of newsprint is
    /// not either. Reused rather than re-picked, so the two cannot drift into
    /// disagreeing about what secondhand is worth.
    ///
    /// **Most things are not news.** `Violence.Notoriety` already grades how
    /// much of a topic an act is — a brawl six people watched against a fight
    /// nobody saw — and the paper takes its threshold from the same scale. A
    /// bribe is never news. A body always is: `HomicideBook`'s own note says a
    /// body "does not stay a rumour", and this is the mechanism by which that
    /// sentence becomes true for people who were nowhere near it.
    ///
    /// WHAT IS NOT HERE. This decides WHETHER there is a story and what it
    /// says. It does not put it into anybody's head — the Game layer files it
    /// through the gossip mill, the same way every other fact in this game
    /// arrives. Rule 6: this is not finished until something calls it.
    public class Story
    {
        public int Day;
        /// The fact the town now holds. Subject is "player" only when the story
        /// names them; otherwise it is the place, so the town knows a thing
        /// happened somewhere without knowing who did it.
        public Fact Content = new Fact("", "", "");
        public bool NamesYou;
        /// What a reader ends up believing, 0..1. Below an eyewitness by
        /// construction.
        public double Confidence;
        /// The line itself, for the ledger screen and for the gossip summary.
        public string Headline = "";
    }

    public static class Press
    {
        /// HOW MUCH OF A TOPIC AN ACT HAS TO BE BEFORE A PAPER RUNS IT.
        ///
        /// On `Violence.Notoriety`'s scale, where a killing floors at 0.75 and a
        /// brawl six people watched comes to 0.70. So this admits a killing
        /// always, a genuinely public fight sometimes, and a scuffle nobody
        /// watched never — which is the shape a local paper actually has.
        ///
        /// NOT A NEW SCALE, and that is the point of putting it here rather
        /// than inventing a "newsworthiness" number: one model already grades
        /// how loud an act is, and a second would drift from it within a week.
        public const double RunsAbove = 0.65;

        /// What a reader believes, against what a witness believes.
        ///
        /// `PhoneBook.FidelityOnTheLine` is this game's existing statement of
        /// what a channel that is not the room is worth, written with the note
        /// that a voice on a line is not a face across a table. Newsprint is
        /// not either, and reusing the number means the two cannot come to
        /// disagree about what secondhand means.
        ///
        /// `PhoneBook`, NOT `Phones` — I wrote the filename. There is no type
        /// called `Phones`; that file declares `Phone`, `Call` and `PhoneBook`.
        /// Same family as the CS0103 that rode eighteen commits and killed four
        /// builds this morning, and the reason it cost seconds instead of a
        /// round trip is that this one is in Core, which compiles here. The
        /// lint written for that fault deliberately skips Core filenames
        /// because they collide with property names constantly — so the two
        /// halves cover different ground and both are needed.
        public const double Fidelity = PhoneBook.FidelityOnTheLine;

        /// Would a paper run this, and does it have the name?
        ///
        /// `streetCase` is the strongest thing anybody would say to a detective
        /// about the player — `HomicideBook` and `Informing` both already
        /// compute it, and the caller passes whichever it has rather than this
        /// file growing a third opinion.
        public static Story Print(int day, double loudness, double streetCase,
                                  bool lethal, string place)
        {
            if (loudness < RunsAbove && !lethal) return null;

            bool named = streetCase >= HomicideBook.TestimonyGrade;
            var s = new Story
            {
                Day = day,
                NamesYou = named,
                // A READER IS NOT A WITNESS, AND A NAMED STORY IS NOT A PROVEN
                // ONE. The confidence is the act's own loudness damped by the
                // channel — so a quiet killing that the street can nonetheless
                // pin on you makes a small, certain-sounding paragraph, and a
                // public brawl nobody will name you for makes a loud anonymous
                // one. Both are true to what a paper is.
                Confidence = Feel.Clamp01(loudness * Fidelity),
            };

            // THE FACT IT LEAVES BEHIND. Naming the player puts it on the same
            // topic key every witness uses, so a printed story and a seen one
            // CORROBORATE instead of stacking as two separate stories — the
            // distinction `GossipMill.DayCircleHeat` is built on, and the reason
            // this must not invent its own predicate.
            s.Content = named
                ? new Fact("player", lethal ? "killed" : "fought", "yes")
                : new Fact(string.IsNullOrEmpty(place) ? "the town" : place,
                           lethal ? "killing" : "trouble", "yes");

            s.Headline = named
                ? (lethal
                    ? $"KILLING ON {Loud(place)}: POLICE NAME THE PUBLICAN"
                    : $"BRAWL ON {Loud(place)}: PUBLICAN AMONG THEM")
                : (lethal
                    ? $"MAN FOUND DEAD ON {Loud(place)}"
                    : $"TROUBLE AGAIN ON {Loud(place)}");
            return s;
        }

        /// WHAT A PRINTED STORY IS WORTH AS NOTORIETY.
        ///
        /// A named story is the loudest thing that can happen to a reputation —
        /// everybody who reads a paper knows, at once, with no hops — so it is
        /// worth the act's full loudness. An unnamed one is worth nothing to
        /// notoriety AT ALL, and that refusal is the design: notoriety is how
        /// known YOU are, and a town reading about a body on Hook Street has
        /// learned nothing about the publican. It is not a smaller version of
        /// the same thing; it is a different thing, and the game already has
        /// somewhere for it — the street's mood and the police's pressure.
        public static double Notoriety(Story s) =>
            s == null || !s.NamesYou ? 0.0 : Feel.Clamp01(s.Confidence);

        /// Street names read as headlines. Trivial, and here rather than at the
        /// call site so the paper has one voice.
        static string Loud(string place) =>
            string.IsNullOrEmpty(place) ? "THE HOOK" : place.ToUpperInvariant();
    }
}
