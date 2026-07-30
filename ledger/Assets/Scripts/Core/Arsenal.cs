using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// THE WEAPON TABLE, as data rather than as a document.
    ///
    /// `weapons-spec.md` §5. Seven families and about sixteen carried objects,
    /// and the reason it is not seven rows is the note that got v2.1 sent
    /// back: *"7 feels too few and low budget."* The fix was not more knives.
    /// A small team makes an arsenal feel large the way Blood Money does — a
    /// modest carried set, a much larger set of objects already in the world,
    /// and a category of kill that uses no weapon at all.
    ///
    /// **NOT ONE DAMAGE NUMBER IN THIS FILE.** Nothing here is better than
    /// anything else. The pistol is not an upgrade over the knife; it is
    /// louder and works at range. Four of the carried things lose outright to
    /// a man who is ready and armed, because Tom Novak runs a bar.
    public enum Family
    {
        Hands, Blunt, Edged, Ligature, Firearm, Environment, Kit,
    }

    /// What happens when it goes wrong, which is the column v2 was missing and
    /// is the actual character of each object.
    public enum FailureMode
    {
        None,
        /// Losing, in public, slowly. The fists.
        LoseInPublic,
        /// He does not go down first time and now he is angry and awake.
        HeStaysUp,
        /// His hand gets to it. The knives, and the worst place to be.
        HeGetsAHandOnIt,
        /// It breaks and you are holding a stub, bleeding.
        ItBreaks,
        /// Interrupted halfway, which for a garrote is catastrophic.
        InterruptedMidway,
        /// You miss, and now everybody within a hundred metres is coming.
        MissAndTheStreetComes,
        /// He survives the fall and knows exactly what you did.
        HeSurvivesIt,
    }

    /// How hard it is to explain if somebody finds it on you.
    public enum Concealment
    {
        /// A bottle, a bar, a kitchen knife. Nobody asks.
        Innocent,
        /// Fits under a coat and raises an eyebrow.
        Concealable,
        /// Fits, and is damning.
        Damning,
        /// Does not fit. A man with a bat has already said something.
        Impossible,
    }

    /// One carryable object, or one thing the world offers.
    public class Weapon
    {
        public string Id;
        public string Name;
        public Family Family;

        /// dB-like, against `Perception` ambient floors. Zero is silent.
        public double Loudness;
        public double ReachMetres;
        /// Seconds from a coat to ready. The draw is the most important second
        /// in the game and it is visible to everyone in a cone.
        public double ReadySeconds;
        /// Whether you can change your mind once it is under way.
        public bool CanAbort;
        public bool VictimCriesOut;
        /// Against a man who is ready and armed. Most of these are false.
        public bool BeatsAReadyMan;
        public bool LeavesBody;
        /// Blood on YOUR clothes, which is a problem at nine in the morning.
        public bool MarksYou;
        /// What it leaves at the scene, in words, for Ellis and the writing.
        public string Trace;
        public Concealment Concealment;
        public FailureMode Fails;
        /// Can it be bought, or does it only come off a body or out of a
        /// kitchen? Drives §7.3 and, later, provenance.
        public bool Purchasable;
        /// Untraceable BY BEING ORDINARY. A knife from the victim's own
        /// kitchen has no provenance to follow, which is a better kind of
        /// clean than a filed serial number.
        public bool Anonymous;

        public override string ToString() => Name;
    }

    public static class Arsenal
    {
        public static readonly IReadOnlyList<Weapon> All = new List<Weapon>
        {
            // ---- Hands ----
            new Weapon { Id = "fists", Name = "fists", Family = Family.Hands,
                Loudness = 45, ReachMetres = 0.8, ReadySeconds = 0, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = false,
                MarksYou = true, Trace = "your face, in his memory",
                Concealment = Concealment.Innocent, Fails = FailureMode.LoseInPublic,
                Purchasable = false, Anonymous = true },
            new Weapon { Id = "knuckles", Name = "brass knuckles", Family = Family.Hands,
                Loudness = 42, ReachMetres = 0.8, ReadySeconds = 0.8, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = false,
                MarksYou = false, Trace = "a marked face that walks around town",
                Concealment = Concealment.Concealable, Fails = FailureMode.HeStaysUp,
                Purchasable = true, Anonymous = false },

            // ---- Blunt ----
            new Weapon { Id = "cosh", Name = "cosh", Family = Family.Blunt,
                Loudness = 38, ReachMetres = 1.0, ReadySeconds = 1.0, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = false,
                MarksYou = false, Trace = "bruising a doctor can read",
                Concealment = Concealment.Concealable, Fails = FailureMode.HeStaysUp,
                Purchasable = true, Anonymous = false },
            new Weapon { Id = "bottle", Name = "bottle", Family = Family.Blunt,
                Loudness = 70, ReachMetres = 1.0, ReadySeconds = 0.4, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = false,
                MarksYou = true, Trace = "glass, and blood — some of it yours",
                Concealment = Concealment.Innocent, Fails = FailureMode.ItBreaks,
                Purchasable = false, Anonymous = true },
            new Weapon { Id = "tyreiron", Name = "tyre iron", Family = Family.Blunt,
                Loudness = 55, ReachMetres = 1.2, ReadySeconds = 1.2, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = true, LeavesBody = true,
                MarksYou = true, Trace = "a wound nobody mistakes for a fall",
                Concealment = Concealment.Innocent, Fails = FailureMode.HeStaysUp,
                Purchasable = false, Anonymous = true },
            new Weapon { Id = "bat", Name = "baseball bat", Family = Family.Blunt,
                Loudness = 58, ReachMetres = 1.6, ReadySeconds = 0.5, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = true, LeavesBody = true,
                MarksYou = true, Trace = "a wound nobody mistakes for a fall",
                // NOT CONCEALABLE, AND THAT IS ITS USE. A man walking down
                // Hook Street with a bat has already said something.
                Concealment = Concealment.Impossible, Fails = FailureMode.HeStaysUp,
                Purchasable = true, Anonymous = false },

            // ---- Edged ----
            new Weapon { Id = "switchblade", Name = "switchblade", Family = Family.Edged,
                Loudness = 30, ReachMetres = 1.0, ReadySeconds = 0.9, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = true, Trace = "a wound signature, and blood",
                Concealment = Concealment.Damning, Fails = FailureMode.HeGetsAHandOnIt,
                Purchasable = true, Anonymous = false },
            new Weapon { Id = "kitchenknife", Name = "kitchen knife", Family = Family.Edged,
                Loudness = 30, ReachMetres = 1.0, ReadySeconds = 1.0, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = true, Trace = "a wound signature, and blood",
                Concealment = Concealment.Innocent, Fails = FailureMode.HeGetsAHandOnIt,
                // UNTRACEABLE BY BEING ORDINARY. Every building in the game has
                // one, so a knife from the victim's own kitchen has no
                // provenance to follow at all.
                Purchasable = false, Anonymous = true },
            new Weapon { Id = "icepick", Name = "ice pick", Family = Family.Edged,
                Loudness = 28, ReachMetres = 0.9, ReadySeconds = 0.9, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = true, Trace = "a wound a hurried coroner can miss",
                // Cheap, needs no permit, and explains itself if found on you.
                Concealment = Concealment.Innocent, Fails = FailureMode.HeGetsAHandOnIt,
                Purchasable = true, Anonymous = true },
            new Weapon { Id = "razor", Name = "straight razor", Family = Family.Edged,
                Loudness = 30, ReachMetres = 0.7, ReadySeconds = 0.6, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = true, Trace = "a wound signature, and blood",
                Concealment = Concealment.Concealable, Fails = FailureMode.HeGetsAHandOnIt,
                Purchasable = true, Anonymous = true },

            // ---- Ligature ----
            new Weapon { Id = "wire", Name = "wire", Family = Family.Ligature,
                Loudness = 0, ReachMetres = 0.5, ReadySeconds = 2.0, CanAbort = false,
                VictimCriesOut = false, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = false, Trace = "a mark on the neck and nothing else",
                Concealment = Concealment.Damning, Fails = FailureMode.InterruptedMidway,
                Purchasable = true, Anonymous = true },
            new Weapon { Id = "cord", Name = "cord", Family = Family.Ligature,
                Loudness = 0, ReachMetres = 0.5, ReadySeconds = 2.6, CanAbort = false,
                VictimCriesOut = false, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = false, Trace = "a mark on the neck and nothing else",
                Concealment = Concealment.Innocent, Fails = FailureMode.InterruptedMidway,
                Purchasable = false, Anonymous = true },

            // ---- Firearms, Phase 5 ----
            new Weapon { Id = "target22", Name = ".22 target pistol", Family = Family.Firearm,
                Loudness = 88, ReachMetres = 20, ReadySeconds = 1.5, CanAbort = true,
                VictimCriesOut = false, BeatsAReadyMan = true, LeavesBody = true,
                MarksYou = false, Trace = "a casing, and a wound that says this was a job",
                Concealment = Concealment.Damning, Fails = FailureMode.MissAndTheStreetComes,
                Purchasable = true, Anonymous = false },
            new Weapon { Id = "snub38", Name = ".38 snub", Family = Family.Firearm,
                Loudness = 100, ReachMetres = 20, ReadySeconds = 1.5, CanAbort = true,
                VictimCriesOut = false, BeatsAReadyMan = true, LeavesBody = true,
                // NO CASING. Revolvers do not eject, and that is a real
                // forensic difference at zero art cost.
                MarksYou = false, Trace = "a wound, and nothing on the ground",
                Concealment = Concealment.Damning, Fails = FailureMode.MissAndTheStreetComes,
                Purchasable = true, Anonymous = false },
            new Weapon { Id = "auto45", Name = ".45 automatic", Family = Family.Firearm,
                Loudness = 104, ReachMetres = 25, ReadySeconds = 1.5, CanAbort = true,
                VictimCriesOut = false, BeatsAReadyMan = true, LeavesBody = true,
                MarksYou = false, Trace = "brass on the pavement, and a wound",
                Concealment = Concealment.Damning, Fails = FailureMode.MissAndTheStreetComes,
                Purchasable = true, Anonymous = false },
            new Weapon { Id = "supp22", Name = "suppressed .22", Family = Family.Firearm,
                Loudness = 62, ReachMetres = 20, ReadySeconds = 1.6, CanAbort = true,
                VictimCriesOut = false, BeatsAReadyMan = true, LeavesBody = true,
                MarksYou = false, Trace = "a casing, and no memory of a bang",
                Concealment = Concealment.Damning, Fails = FailureMode.MissAndTheStreetComes,
                Purchasable = true, Anonymous = false },
            new Weapon { Id = "sawnoff", Name = "sawn-off", Family = Family.Firearm,
                Loudness = 110, ReachMetres = 8, ReadySeconds = 2.0, CanAbort = true,
                VictimCriesOut = false, BeatsAReadyMan = true, LeavesBody = true,
                MarksYou = true, Trace = "a wound that ends the argument about what happened",
                Concealment = Concealment.Impossible, Fails = FailureMode.MissAndTheStreetComes,
                Purchasable = true, Anonymous = false },

            // ---- The environment ----
            //
            // THE ONLY VIOLENCE IN THIS GAME THAT PRODUCES NO CRIME. The
            // observation model returns Aftermath with the wrong content: a
            // man fell down the stairs, and nobody is looking for anybody.
            new Weapon { Id = "stairs", Name = "the stairs", Family = Family.Environment,
                Loudness = 52, ReachMetres = 1.0, ReadySeconds = 0, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = false, Trace = "a man who fell down the stairs",
                Concealment = Concealment.Innocent, Fails = FailureMode.HeSurvivesIt,
                Purchasable = false, Anonymous = true },
            new Weapon { Id = "water", Name = "the dock", Family = Family.Environment,
                Loudness = 40, ReachMetres = 1.0, ReadySeconds = 0, CanAbort = true,
                VictimCriesOut = true, BeatsAReadyMan = false, LeavesBody = true,
                MarksYou = false, Trace = "a man who went into the water",
                Concealment = Concealment.Innocent, Fails = FailureMode.HeSurvivesIt,
                Purchasable = false, Anonymous = true },
        };

        public static Weapon Get(string id) => All.FirstOrDefault(w => w.Id == id);

        public static IEnumerable<Weapon> Of(Family f) => All.Where(w => w.Family == f);

        /// AN ACCIDENT IS NOT A CRIME — until somebody watches you do it.
        ///
        /// Unqualified, this ends the design: if the stairs always work, the
        /// optimal player never touches a weapon again. Three constraints,
        /// spec §5.2 Family 6, and this is the first of them in code.
        public static bool IsAccident(Weapon w) => w != null && w.Family == Family.Environment;

        /// An accident needs position AND privacy that most situations do not
        /// offer. He has to be at the top of the stairs, beside the rail, near
        /// the road — and you have to be alone with him there.
        public static bool AccidentAvailable(Weapon w, bool inPosition, int witnessesPresent)
            => IsAccident(w) && inPosition && witnessesPresent == 0;

        /// And being SEEN doing it is the worst observation in the game.
        /// There is no ambiguity in a push: no weapon, no struggle, nothing to
        /// point at. A full sighting of an accident is more damning than one
        /// of a stabbing, which is what stops this family dominating.
        public const double SeenAccidentPenalty = 1.35;

        // ---------------------------------------------------------------
        // THE THREAT, which is the main use — spec §5.1
        // ---------------------------------------------------------------

        public enum Threat
        {
            /// Nothing now. They remember, permanently.
            Comply,
            /// The common case, and time is the resource that matters.
            Freeze,
            /// A loud sound event, and now everyone is looking.
            FleeScreaming,
            /// Humiliating, public, and it hardens them.
            CallTheBluff,
            /// They are armed, or they are one of the outfits. The worst
            /// outcome available and it is on you.
            Escalate,
        }

        /// What happens when you point it at somebody.
        ///
        /// In a crime story most of what a weapon does happens before anybody
        /// is hurt, and v2 of the spec did not have this verb at all. It does
        /// more work than any row of the table: it makes carrying meaningful
        /// without killing, it gives fists and knives a non-lethal expressive
        /// range, and it makes a pistol terrifying to HOLD.
        public static Threat Brandish(Weapon w, double targetNerve, bool targetArmed,
                                      bool targetIsOutfit, bool inPublic,
                                      double reputationForViolence)
        {
            if (w == null) return Threat.CallTheBluff;
            if (targetArmed || targetIsOutfit) return Threat.Escalate;

            // How frightening the thing in your hand is, tempered by whether
            // anybody believes YOU would use it. A man who has never hurt
            // anyone holding a razor is a man holding a razor.
            double menace = Feel.Clamp01(
                (w.Family == Family.Firearm ? 0.95
                 : w.Family == Family.Edged ? 0.70
                 : w.Family == Family.Blunt ? 0.55
                 : w.Family == Family.Ligature ? 0.45
                 : 0.30)
                * (0.55 + 0.65 * Feel.Clamp01(reputationForViolence)));

            double nerve = Feel.Clamp01(targetNerve);
            if (nerve > menace + 0.20) return Threat.CallTheBluff;
            if (menace > nerve + 0.35) return inPublic ? Threat.FleeScreaming : Threat.Comply;
            return Threat.Freeze;
        }

        /// You can always escalate from a threat to an act. You can never
        /// un-draw — which is the one-way door the whole verb turns on.
        public static bool CanUndraw() => false;

        // ---------------------------------------------------------------
        // CARRY — a coat, not a grid (spec §7.1)
        // ---------------------------------------------------------------

        /// What fits. Not weight, not slots — CONCEALMENT. Your hands and what
        /// goes under a coat: realistically two things, three if one is small
        /// and you do not mind being obvious.
        public const int CoatCapacity = 2;
        public const int CoatCapacityIfOneIsSmall = 3;

        public static bool Fits(IEnumerable<Weapon> carried, Weapon adding)
        {
            var list = carried?.ToList() ?? new List<Weapon>();
            if (adding != null) list.Add(adding);
            if (list.Any(w => w.Concealment == Concealment.Impossible))
                // A bat or a sawn-off is not carried under a coat. It is
                // carried, visibly, which is a different decision entirely.
                return list.Count(w => w.Concealment == Concealment.Impossible) == 1
                       && list.Count <= 2;
            int cap = list.All(w => w.Concealment != Concealment.Damning)
                      ? CoatCapacityIfOneIsSmall : CoatCapacity;
            return list.Count <= cap;
        }

        /// FOUND IS WORSE THAN USED. A clean knife found on you the night
        /// after a stabbing on your street is not evidence of anything and
        /// will convict you socially anyway.
        public static double FriskCost(Weapon w)
        {
            if (w == null) return 0;
            switch (w.Concealment)
            {
                case Concealment.Innocent: return 0.0;
                case Concealment.Concealable: return 0.35;
                case Concealment.Damning: return 0.85;
                default: return 1.0;
            }
        }
    }
}
