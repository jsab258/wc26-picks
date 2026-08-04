using System;

namespace Ledger.Core
{
    /// M21: THE RIVAL IS A PERSON WHO RINGS YOU, NOT A PLACE YOU TRAVEL TO.
    ///
    /// The roadmap says it plainly and has for weeks: `ResolveTable` already
    /// offers terms, takes accept, defy or counter, moves standing and
    /// attention, and writes the answer into her people's memory. "What is
    /// actually missing is her RINGING you: the summit is a place you go, not a
    /// call you take, and `Phones` has been built since M10."
    ///
    /// WHY THAT IS A MECHANIC AND NOT A CUTSCENE. A summit you walk to is an
    /// appointment you cannot miss, so the only decisions in it are the three
    /// `ResolveTable` already models. A call has a fourth answer the other
    /// three cannot express — NOT BEING THERE — and that answer is the one the
    /// rest of this game is built to make interesting. The phone layer already
    /// knows the player has to be near a line to be reached, already damps what
    /// travels down one, and already models not being able to place a voice.
    /// Being unreachable is a position you can take, and this is the first
    /// thing in the game that charges for it.
    ///
    /// WHAT IS HERE AND WHAT IS NOT. This decides WHETHER she has reason to
    /// call, and what each of the four answers is worth. It does not place the
    /// call, does not know where the player is standing, and does not touch a
    /// phone — the Game layer owns all of that, the same split every other Core
    /// file here keeps. Rule 6 applies and is not yet satisfied: this is not
    /// finished until something calls it and a gate proves the call happened.
    public enum Answered
    {
        /// You were near a line and you picked up.
        Took,
        /// The line rang out. You were not reachable, or you chose not to be.
        Missed,
        /// You picked up and said no.
        Refused,
    }

    /// One call she has decided to make.
    public class Summons
    {
        public string ArmId = "";
        public string HeadName = "";
        /// The day it is placed, and the hour she chose.
        public int Day;
        public int Hour;
        /// What she is ringing about, in her own frame.
        public string Terms = "";
    }

    public static class Summoning
    {
        /// SHE ONLY RINGS SOMEBODY SHE IS ALREADY THINKING ABOUT. Attention is
        /// the arm's own 0..1 measure of how much of it the player has, and it
        /// is what every other rival behaviour in `Empire` reads. Below this
        /// the player is not on her desk and a call would be the game telling
        /// them they matter rather than the world deciding it.
        ///
        /// NOT A NEW NUMBER: `ResolveTable` treats 0.5 as the attention a
        /// settlement buys back, so half her attention is already the game's
        /// statement of "this is a live matter".
        public const double RingsAbove = 0.5;

        /// And not before she has noticed at all. Stage 1 is `notice` — stage 0
        /// is quiet, and a quiet arm ringing you is the fault this guard exists
        /// to prevent rather than a dramatic surprise.
        public const int RingsFromStage = 1;

        /// HOW LONG SHE WAITS BEFORE TRYING AGAIN. A call a day is harassment
        /// and a call a fortnight is not a rival; three days is `Empire`'s own
        /// spacing for a rival act, and reusing it means the two cannot drift
        /// into contradicting each other about how often she moves.
        public const int DaysBetween = 3;

        /// Has this arm reason to ring today?
        ///
        /// DETERMINISTIC, and that is deliberate rather than convenient. A roll
        /// here would mean two loads of the same save differ in whether the
        /// phone rang, which is exactly the kind of thing this game must never
        /// do — the whole design turns on the player being able to believe that
        /// what happened followed from what they did.
        public static Summons Due(RivalArm arm, int day, int hour)
        {
            if (arm == null) return null;
            if (arm.Stage < RingsFromStage) return null;
            if (arm.Attention < RingsAbove) return null;
            if (arm.LastActDay >= 0 && day - arm.LastActDay < DaysBetween) return null;
            return new Summons
            {
                ArmId = arm.Id,
                HeadName = arm.HeadName,
                Day = day,
                Hour = hour,
                Terms = TermsFor(arm),
            };
        }

        /// What she wants, by how far along she is. Stage is the escalation
        /// ladder `Empire` already keeps; the words follow it rather than
        /// inventing a second one.
        public static string TermsFor(RivalArm arm) =>
            arm == null ? ""
            : arm.Stage >= 4 ? "She wants to settle it, one way or the other."
            : arm.Stage == 3 ? "She wants what you took back, and she is asking once."
            : arm.Stage == 2 ? "She wants a share, and she is being polite about it."
            : "She wants to know who you are.";

        /// WHAT NOT PICKING UP IS WORTH, AND IT IS NOT NOTHING.
        ///
        /// THE ORDERING IS THE DESIGN and the tests hold it rather than the
        /// magnitudes. Taking the call is where standing can be gained, because
        /// it is the only answer that leads to terms. Refusing to her face
        /// costs the most: she now knows exactly where you stand and so does
        /// everyone who was in the room. Missing sits between them and closer
        /// to refusing, because a man who is never reachable is telling you
        /// something — but he has not said it, and she cannot repeat it to
        /// anybody as a thing he said.
        ///
        /// AND MISSING IS NOT FREE THE OTHER WAY EITHER: it leaves her
        /// attention exactly where it was, so the matter stays live and she
        /// rings again in three days. Refusing spikes it, the way defying her
        /// at a table does.
        public static double StandingChange(Answered a) =>
            a == Answered.Took ? 0.10
            : a == Answered.Missed ? -0.15
            : -0.35;

        public static double AttentionChange(Answered a) =>
            a == Answered.Took ? -0.30
            : a == Answered.Missed ? 0.0
            : 0.35;

        /// What her people are told happened. Goes into the gossip layer
        /// through `Empire`'s own arm-memory path, so the street learns it the
        /// same way it learns everything else.
        public static string ReadOf(Summons s, Answered a) =>
            s == null ? ""
            : a == Answered.Took
                ? $"The new owner took {s.HeadName}'s call."
            : a == Answered.Missed
                ? $"{s.HeadName} rang the new owner. Nobody picked up."
                : $"{s.HeadName} rang the new owner and got told no.";

        /// Apply an answer to the arm. One place, so the three numbers cannot
        /// be moved by a caller that forgets one of them.
        public static void Apply(EmpireBook book, Summons s, Answered a, int day)
        {
            var arm = book?.ArmOf(s?.ArmId ?? "");
            if (arm == null) return;
            arm.Standing = Feel.Clamp(arm.Standing + StandingChange(a), -1, 1);
            arm.Attention = Feel.Clamp01(arm.Attention + AttentionChange(a));
            // THE CLOCK MOVES ON A MISS TOO. It has to: `Due` refuses to ring
            // again for three days from the last act, and if a missed call did
            // not count as an act she would ring every single day until
            // somebody answered — which is the harassment case this spacing
            // exists to prevent, reachable only through the one answer that
            // does not involve the player at all.
            arm.LastActDay = day;
        }
    }
}
