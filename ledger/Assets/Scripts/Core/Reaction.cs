using System;

namespace Ledger.Core
{
    /// WHAT PEOPLE DO ABOUT IT. Stage 3 of the pipeline.
    ///
    /// `weapons-spec.md` §8. Graduated per person and driven by their own
    /// observation and their own temperament, because a ladder everybody
    /// climbs at the same rate is a state machine wearing a costume.
    ///
    /// THE HIGHEST-VALUE RUNG IS `Investigate`, and it is worth saying why: it
    /// turns one sound into a moving problem, and it explains itself to the
    /// player without any interface at all. A man walking toward the noise you
    /// made is the clearest possible statement of what is happening.
    public enum Reacted
    {
        /// Nothing. Most people, most of the time, and that is correct.
        Ignore = 0,
        /// A head turns. Free, constant, and the thing that makes a street
        /// feel alive rather than staged.
        Notice,
        /// Walks toward it.
        Investigate,
        /// Shouts — which is ITSELF a loud sound event, so alarm propagates
        /// through the same hearing model. Panic is emergent, not scripted.
        Alarm,
        /// Runs. Nerve decides.
        Flee,
        /// Goes to tell somebody (§4.5 — the delivery window).
        Deliver,
        /// Goes to find Ellis.
        FetchTheLaw,
        /// Rare, high-nerve, and it should be genuinely dangerous.
        Intervene,
    }

    public static class Reaction
    {
        /// A shout is a sound event like any other, which is the whole reason
        /// alarm spreads without a propagation system: somebody alarmed makes
        /// `Perception.LoudShout` where they stand, and everyone who can hear
        /// it runs this function.
        public const double AlarmLoudness = Perception.LoudShout;

        /// What does this person do?
        ///
        /// `severity` is how bad what they got was, 0..1 — an observation with
        /// a body in it is not a slammed door. `nerve` and `dutiful` come from
        /// `Gossiper`, which has had them since the mill was written.
        public static Reacted Decide(double severity, double nerve, double dutiful,
                                     double willingness, bool sawABody, bool alreadyAlarmed)
        {
            severity = Feel.Clamp01(severity);
            nerve = Feel.Clamp01(nerve);
            dutiful = Feel.Clamp01(dutiful);

            if (severity < 0.05) return Reacted.Ignore;
            if (severity < 0.2) return Reacted.Notice;

            // A body changes the shape of it. Below that, curiosity wins and
            // people walk toward things; at a body, temperament decides
            // whether they shout, run or go and find somebody.
            if (sawABody || severity >= 0.75)
            {
                if (nerve < 0.3) return Reacted.Flee;
                if (alreadyAlarmed && nerve > 0.85 && severity >= 0.9) return Reacted.Intervene;
                if (dutiful > 0.55) return Reacted.FetchTheLaw;
                if (willingness > 0.4) return Reacted.Deliver;
                return Reacted.Alarm;
            }

            // The middle of the ladder. Curiosity is the default and fear is
            // the exception, which is what makes a street feel like people
            // rather than like a security system.
            if (nerve < 0.25 && severity > 0.5) return Reacted.Flee;
            if (severity >= 0.45 && nerve > 0.4) return Reacted.Investigate;
            if (severity >= 0.45) return Reacted.Alarm;
            return Reacted.Notice;
        }

        /// How bad was it, from what they actually got. Derived from the slots
        /// rather than from the event, because two people at one killing did
        /// not witness the same thing and must not react as though they did.
        public static double Severity(Observation o)
        {
            if (o == null || o.Empty) return 0;
            double s = 0.10;
            if (o.Has(Slot.Act)) s += 0.30;
            if (o.Has(Slot.Victim)) s += 0.25;
            if (o.Has(Slot.Aftermath)) s += 0.35;
            if (o.Has(Slot.Draw)) s += 0.20;
            if (o.Has(Slot.Flight)) s += 0.05;
            return Feel.Clamp01(s);
        }

        /// Does this reaction make a noise other people can hear? Only one
        /// does, and that is the whole propagation model.
        public static double LoudnessOf(Reacted r) =>
            r == Reacted.Alarm ? AlarmLoudness : 0.0;

        // ---------------------------------------------------------------
        // CAUGHT IN THE ACT — spec §15.2, approved: ARREST, NO CHASE
        // ---------------------------------------------------------------

        public enum Lawful
        {
            /// He cannot place you. The escape hatch is social, not athletic.
            NothingToArrest,
            /// A hand on your arm, the street watching, and everything in your
            /// coat now in a drawer at the station.
            Arrest,
            /// You resisted. Permitted, and catastrophic.
            ResistedArrest,
        }

        /// A constable who watched it happen closes, and being taken is the
        /// outcome. There is deliberately NO CHASE: a foot chase is a
        /// different genre and would be the least distinguished thing in this
        /// game. Running still works, through the systems that already exist —
        /// you get away because he could not identify you, because the street
        /// was busy, because you had somewhere to be. Not because you outran
        /// him round a corner.
        public static Lawful Confront(Observation constablesView, bool playerResists)
        {
            if (constablesView == null) return Lawful.NothingToArrest;
            bool canPlaceYou = constablesView.Has(Slot.Actor) && constablesView.Rung >= 4;
            if (!canPlaceYou) return Lawful.NothingToArrest;
            return playerResists ? Lawful.ResistedArrest : Lawful.Arrest;
        }

        /// RESISTING IS ALLOWED AND IT IS THE WORST OUTCOME IN THE GAME.
        ///
        /// Not disallowed, not soft-failed — permitted, and catastrophic. A
        /// fight with a constable in public is an unambiguous full sighting
        /// for everybody present, with the one witness whose word carries by
        /// default. The option has to exist, because a game where the law
        /// cannot be resisted is not a crime game; and it has to be a mistake,
        /// because Tom Novak fighting a policeman is a man ending his own life
        /// in ninety seconds.
        ///
        /// **The game does not warn you.** The prompt says what it always says.
        public const double ResistPressure = 1.15;

        /// What an arrest hands over: everything you were carrying is now
        /// catalogued, and provenance becomes the interrogation.
        public static bool CataloguesYourCoat(Lawful outcome) =>
            outcome == Lawful.Arrest || outcome == Lawful.ResistedArrest;

        /// Being taken is itself an event with witnesses. Half the street
        /// watched Tom Novak get walked to a car, and that is a fact the mill
        /// carries like any other.
        public static bool IsPublicEvent(Lawful outcome) => CataloguesYourCoat(outcome);

        // ---------------------------------------------------------------
        // THE SURVIVOR — spec §15.3
        // ---------------------------------------------------------------

        /// THE MOST DANGEROUS WITNESS IN THE GAME IS THE MAN YOU FAILED TO
        /// KILL: close, lit, facing you, and with every reason in the world to
        /// talk. The whole spec was player → target → witnesses until the
        /// audit; the target perceives too.
        ///
        /// Being attacked guarantees rung 3 and usually rung 4 — he was
        /// looking right at you — so this returns the victim's own
        /// observation, biased rather than computed from a vantage.
        public static Observation AsVictim(Deed deed, string victimId,
                                           double familiarityWithActor,
                                           bool survived)
        {
            var o = new Observation
            {
                WitnessId = victimId,
                EventId = deed.EventId,
                Slots = Slot.Act | Slot.Victim | Slot.Actor,
                Rung = familiarityWithActor >= Perception.RecognitionFamiliarity ? 4 : 3,
                AccusedId = familiarityWithActor >= Perception.RecognitionFamiliarity
                            ? deed.ActorId : null,
                Certainty = 0.94,
                // He has every reason to talk, and the only thing that reliably
                // stops him is fear of the man who just tried it.
                Willingness = 0.9,
            };
            if (deed.WeaponDrawn) o.Slots |= Slot.Draw;
            if (deed.ActorFled) o.Slots |= Slot.Flight;
            // A dead man is not a witness. Stated in code because the whole
            // trade in `combat-spec.md` §2 turns on it: killing really does
            // solve the witness, and the second problem is always larger.
            if (!survived) { o.Slots = Slot.None; o.Rung = 0; o.AccusedId = null; o.Certainty = 0; }
            return o;
        }

        /// A fleeing target is a delivering witness who also happens to be the
        /// victim — the tensest chase in the design, and it needs no chase
        /// mechanic at all. He is going somewhere and you know where.
        public static bool IsFleeingVictim(Observation victimView, Reacted what) =>
            victimView != null && !victimView.Empty
            && (what == Reacted.Flee || what == Reacted.Deliver || what == Reacted.FetchTheLaw);
    }
}
