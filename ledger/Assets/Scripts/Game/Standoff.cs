using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// THE ONE DELIBERATE FLOURISH — `weapons-spec.md` §6.2 and §4.4.
    ///
    /// Mutual awareness has four states and the bottom-right one is a scene
    /// rather than a flag: **he has seen you, and he knows that you know.** It
    /// is the single most dramatic thing the perception model can produce and
    /// it costs nothing to detect, because both halves of the record already
    /// exist — `NpcWalker.AttendingPlayer` is one, and whether the walker is in
    /// front of the player inside facing-readable range is the other.
    ///
    /// FOUR TENTHS OF A SECOND. Not slow motion, not a cutscene, no sting: the
    /// street audio ducks and the frame tightens, once, and then it is over.
    /// Used for exactly this and nothing else, so it never becomes wallpaper —
    /// the moment a second thing borrows it, it stops meaning anything.
    ///
    /// AND ONLY ONCE PER PERSON. Eye contact with the same man twice in a
    /// minute is not two events, and re-firing on every glance would turn the
    /// most dramatic beat in the design into a stutter.
    public static class Standoff
    {
        public const float BeatSeconds = 0.4f;

        /// How long before the same person can produce another one.
        public const float PerPersonCooldown = 25f;

        /// AND A GLOBAL FLOOR, because per-person was not enough. The first CI
        /// run fired this two hundred and ninety-two times in nine days — with
        /// forty-two walkers, a twenty-five-second per-person cooldown still
        /// allows a beat every few seconds from somebody new. That is a tic, and
        /// a flourish that happens every few seconds is not a flourish, it is
        /// the ambient state of the game.
        ///
        /// Twelve seconds between ANY two, which caps it at roughly one a
        /// minute in the worst case and leaves it feeling like an event.
        public const float GlobalCooldown = 12f;

        /// How much tighter the frame closes at the peak of the beat, as a
        /// fraction of the corner brightness. Small — this is a held breath,
        /// not a vignette wipe.
        public const float FrameTighten = 0.12f;

        static float _firedAt = -999f;
        static readonly System.Collections.Generic.Dictionary<string, float> _lastPerPerson
            = new System.Collections.Generic.Dictionary<string, float>();

        public static int Beats;
        public static Awareness LastAwareness = Awareness.NeitherKnows;

        /// THE GHOST — who it is for, when it was raised, and which awareness
        /// earned it. Held rather than drawn here: this class owns the beat,
        /// and what a ghost LOOKS like is presentation.
        public static string GhostFor;
        public static float GhostAt = -999f;
        public static Awareness GhostAwareness = Awareness.NeitherKnows;
        public static int Ghosts;

        /// How long it hangs. Longer than the beat, because the beat is a held
        /// breath and the ghost is the thing you are meant to read.
        public const float GhostSeconds = 2.5f;

        public static bool GhostShowing => Time.time - GhostAt < GhostSeconds;

        public static bool Running => Time.time - _firedAt < BeatSeconds;

        /// 0 at rest, 1 at the peak of the beat, back to 0. Read by the grade.
        public static float Curve
        {
            get
            {
                float t = (Time.time - _firedAt) / BeatSeconds;
                if (t < 0 || t > 1) return 0;
                // Fast in, slow out: the catch of breath is the sharp part.
                return t < 0.25f ? t / 0.25f : 1f - (t - 0.25f) / 0.75f;
            }
        }

        /// Evaluate one walker. `theySeeYou` is their attention record;
        /// `youSeeThem` is whether they are in front of you and close enough
        /// that their facing is readable — the same predicate the symmetry rule
        /// promises the player (§15.1), so the beat can never fire for
        /// something the player had no way to perceive.
        public static void Consider(string who, bool theySeeYou, bool youSeeThem)
        {
            var a = Observe.AwarenessOf(youSeeThem, theySeeYou);
            LastAwareness = a;

            // THE GHOST (§6.2), which is the one item Phase 2 left outstanding.
            //
            // `Observe.GhostAllowed` has been written and tested since Phase 1
            // and had no caller. It permits the ghost for Standoff AND for
            // YouKnow — and this method returned early on everything that was
            // not a Standoff, so the YouKnow case could never have produced
            // one however the rest of the game was wired.
            //
            // WHY IT IS RESTRICTED AT ALL, because it looks like a limitation
            // and is the opposite: v3 of the spec showed the ghost for every
            // witness, which silently destroyed the quiet-horror case — if the
            // ghost always appears, being seen WITHOUT KNOWING IT cannot exist,
            // and that case is the best thing in the perception model. Keeping
            // it to mutual awareness also stops it being a readout of another
            // person's mind, which Tom has no right to, and makes it a picture
            // of something the character actually experienced.
            if (!string.IsNullOrEmpty(who) && Observe.GhostAllowed(a))
            {
                GhostFor = who;
                GhostAt = Time.time;
                GhostAwareness = a;
                Ghosts++;
            }

            if (a != Awareness.Standoff) return;
            if (string.IsNullOrEmpty(who)) return;
            if (Time.time - _firedAt < GlobalCooldown) return;
            if (_lastPerPerson.TryGetValue(who, out var last)
                && Time.time - last < PerPersonCooldown) return;

            _lastPerPerson[who] = Time.time;
            _firedAt = Time.time;
            Beats++;
            // The bed gets out of the way, using the duck that already exists
            // rather than a second volume system — `DuckForOverheard` is the
            // harder of the two ducks and this is the same kind of moment: a
            // thing you were not meant to be part of.
            Audio.DuckForOverheard(true);
        }

        /// Release the duck when the beat is over. Called once a frame.
        public static void Step()
        {
            if (!Running && Time.time - _firedAt < BeatSeconds + 0.5f)
                Audio.DuckForOverheard(false);
        }

        /// Whether the player is looking at this walker closely enough for the
        /// symmetry rule to hold — in front of the camera, within the distance
        /// at which a facing reads, and not through a wall.
        public static bool PlayerCanRead(Transform player, Transform them, double lightOnThem)
        {
            if (player == null || them == null) return false;
            Vector3 to = them.position - player.position; to.y = 0;
            float metres = to.magnitude;
            if (!Perception.FacingIsReadable(metres, lightOnThem)) return false;
            var cam = Camera.main;
            Vector3 fwd = cam != null ? cam.transform.forward : player.forward;
            fwd.y = 0;
            if (Vector3.Angle(fwd, to) > Perception.AcuityDegrees / 2) return false;
            return !Perceivers.Occluded(player.position, them.position);
        }

        /// For the sim report, and so a break run has something to read.
        public static void Reset()
        {
            Beats = 0;
            _firedAt = -999f;
            _lastPerPerson.Clear();
            LastAwareness = Awareness.NeitherKnows;
            Ghosts = 0;
            GhostFor = null;
            GhostAt = -999f;
            GhostAwareness = Awareness.NeitherKnows;
        }
    }
}
