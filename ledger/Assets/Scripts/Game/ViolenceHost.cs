using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE ACT — weapons-spec Phase 3, and the half `Witnesses` was waiting for.
    ///
    /// Phase 2 built everything that happens AFTER a violent act: who saw it,
    /// what slots they filled, how far up the identification ladder they got,
    /// how long they take to carry it somewhere. All of it drove off a
    /// synthetic deed the sim director conjured, because nothing in the game
    /// could produce a real one.
    ///
    /// This is the act. The threat that is the main use of a weapon, the strike
    /// that lands, the killing, the noise it makes, the blood one of them
    /// leaves on you, and the man who did not die and is now the most dangerous
    /// witness in the game.
    ///
    /// EVERY RULE HERE IS ALREADY DECIDED IN CORE, and none of them had a
    /// caller. `Arsenal.Brandish` knows what pointing a thing at somebody does.
    /// `Traces` knows what blood is worth and how it ages. `Reaction.AsVictim`
    /// knows what the target saw. The reach ledger counted thirty-three of
    /// these across phases 2-4; this file is where the phase-3 ones get a call
    /// site, and it deliberately contains no rule of its own — every number
    /// comes from the same world sensors `Witnesses` reads, because a second
    /// copy of a threshold is how the wet-road value drifted from itself.
    ///
    /// WHAT THIS FILE DOES NOT DO, and the first draft did: attenuate the sound
    /// itself. It multiplied the deed's loudness by `Acoustics.OutsideBleed`,
    /// which reads plausibly and is dimensionally wrong — loudness here is dB
    /// on `Perception`'s scale, and `OutsideBleed` is a 0..1 MIXER GAIN for
    /// ducking the street bed when the player walks through a door. 55 dB times
    /// 0.28 is 15 dB, which is under the quietest ambient floor in the game, so
    /// the back-room case would have "worked" for a completely bogus reason.
    ///
    /// The real model was already there and needs nothing from this file: the
    /// emitter reports the sound at its true loudness, and every listener
    /// applies its own occlusion and its own floor through
    /// `Perception.AudibleRadius`. A wall is 22 dB (`WallAttenuation`), a busy
    /// bar is a 68 dB floor (`AmbientBarBusy`), and the back room of a busy pub
    /// is quiet on the street because of both — not because this file said so.
    ///
    /// STATIC, LIKE `Witnesses`, and for the same reason: the sim director, the
    /// player controller and the gates all have to read one answer about what
    /// just happened rather than each recomputing it from a different frame.
    public static class ViolenceHost
    {
        // ---- THE THREAT (spec §5.1) --------------------------------------
        //
        // "In a crime story most of what a weapon does happens before anybody
        // is hurt." The verb did not exist in v2 of the spec and it does more
        // work than any row of the weapon table: it makes carrying meaningful
        // without killing, it gives fists and knives a non-lethal expressive
        // range, and it makes a pistol terrifying to HOLD.

        public static Arsenal.Threat LastThreat { get; private set; }
        public static string LastThreatTarget { get; private set; }
        public static int Brandishes { get; private set; }
        public static int ThreatsThatFled { get; private set; }
        public static int ThreatsCalled { get; private set; }
        public static int ThreatsComplied { get; private set; }
        /// The object currently in the hand, drawn by `HeldObject`.
        public static GameObject Held { get; private set; }

        /// Point it at somebody. Returns what they do about it.
        ///
        /// The outcomes are wired here rather than left to the caller, because
        /// every one of them is a thing other people can see happen: a scream
        /// is a loud event the whole street hears, complying leaves a permanent
        /// memory in somebody who now knows exactly what you are, and calling
        /// the bluff hardens them. Brandishing is not a free action.
        public static Arsenal.Threat Brandish(Weapon w, NpcWalker target, Vector3 actorAt,
                                              bool inPublic, double reputationForViolence,
                                              double targetNerve, bool targetArmed = false,
                                              bool targetIsOutfit = false,
                                              Transform hand = null)
        {
            var threat = Arsenal.Brandish(w, targetNerve, targetArmed, targetIsOutfit,
                                          inPublic, reputationForViolence);
            Brandishes++;
            LastThreat = threat;
            LastThreatTarget = target != null ? target.DisplayName : null;

            // AND IT IS IN YOUR HAND. Nineteen weapons existed as data with no
            // mesh anywhere, so the most legible act in a game about being seen
            // was invisible — a threat nobody could see being made. `Drawn`
            // stays raised afterwards because `CanUndraw` is false: the object
            // does not go away, which is the whole point of the verb.
            if (hand != null) Held = HeldObject.Draw(hand, w);

            switch (threat)
            {
                case Arsenal.Threat.FleeScreaming:
                    // A scream carries further than the act would have, and it
                    // goes through the same emitter a door slam uses. One noise
                    // model for the whole game, or the ring and the captions
                    // stop agreeing with the perception.
                    ThreatsThatFled++;
                    Perceivers.Emit(actorAt, Perception.LoudShout, "scream");
                    if (target != null) target.Stance = StanceKind.Avoids;
                    break;
                case Arsenal.Threat.CallTheBluff:
                    // Humiliating, public, and it hardens them — so the stance
                    // goes UP the ladder rather than down.
                    ThreatsCalled++;
                    if (target != null) target.Stance = StanceKind.Confronts;
                    break;
                case Arsenal.Threat.Comply:
                case Arsenal.Threat.Freeze:
                    ThreatsComplied++;
                    if (target != null && target.Stance < StanceKind.Watches)
                        target.Stance = StanceKind.Watches;
                    break;
                case Arsenal.Threat.Escalate:
                    if (target != null) target.Stance = StanceKind.Confronts;
                    break;
            }
            return threat;
        }

        /// You can never put it away again — the one-way door the whole verb
        /// turns on. Here so the UI can refuse to offer a button that does not
        /// exist rather than offering one that silently does nothing.
        public static bool CanUndraw() => Arsenal.CanUndraw();

        // ---- THE ACT ------------------------------------------------------

        /// What one violent act produced, in one place, so every gate and panel
        /// reads the same answer.
        public class Aftermath
        {
            public Deed Deed;
            /// Everybody who got something, from `Witnesses.Resolve`.
            public List<Observation> Seen;
            /// The target's own account. Empty when they did not survive,
            /// which is the trade the whole design turns on.
            public Observation VictimView;
            /// True when the victim is alive and taking it somewhere.
            public bool VictimIsFleeing;
            /// The best "that was a killing" any bystander got, 0..1.
            public double KillingConfidence;
            /// Whether it put blood on the player.
            public bool MarkedYou;
            /// What it sounded like at the source, in dB.
            public double Loudness;
            public int SawSomething;
        }

        public static Aftermath Last { get; private set; }
        public static int Acts { get; private set; }
        public static int Killings { get; private set; }
        public static int FleeingVictims { get; private set; }
        /// The best killing-confidence any act in the run produced. Latched,
        /// because the gate reads it at the end and `Last` is only the last.
        public static double PeakKillingConfidence { get; private set; }

        /// The player's coat, stained. One stain, deliberately: this is a coat,
        /// not a damage model.
        public static Stain PlayerStain { get; private set; }
        public static int StainsTaken { get; private set; }
        public static int StainsWashed { get; private set; }
        public static int StainsNoticed { get; private set; }
        public static double WorstStainCost { get; private set; }

        public static void Reset()
        {
            Last = null;
            Acts = Killings = FleeingVictims = 0;
            Brandishes = ThreatsThatFled = ThreatsCalled = ThreatsComplied = 0;
            StainsTaken = StainsWashed = StainsNoticed = 0;
            PeakKillingConfidence = 0;
            WorstStainCost = 0;
            PlayerStain = null;
            LastThreat = Arsenal.Threat.Freeze;
            LastThreatTarget = null;
            Held = null;
            HeldObject.ResetCounters();
        }

        /// Do it, and let the world decide what that meant.
        public static Aftermath Commit(Weapon w, Transform actor, NpcWalker victim,
                                       string eventId, bool lethal, GameTime now,
                                       HarmBook harm = null,
                                       double familiarityWithActor = 0.0,
                                       bool actorFled = false, bool hadPrecursor = false,
                                       System.Func<NpcWalker, double> familiarityOf = null)
        {
            if (actor == null || victim == null) return null;
            string victimId = victim.DisplayName;
            Vector3 victimAt = victim.transform.position;

            var deed = Observe.DeedFor(w, eventId, "player", victimId, actorFled, hadPrecursor);

            // WHO SAW IT — the Phase 2 machinery, now driven by a real act
            // rather than by one the sim director invented to keep it exercised.
            var seen = Witnesses.Resolve(deed, actor, victimAt, familiarityOf);

            // AND WHAT IT SOUNDED LIKE. Emitted at the source, at the deed's
            // own loudness, because that is what a sound IS — every listener
            // applies its own walls and its own floor downstream. A victim who
            // cries out is louder than the weapon: the shout is the event.
            double loudness = deed.Loudness;
            if (deed.VictimCriesOut && !lethal)
                loudness = System.Math.Max(loudness, Perception.LoudShout);
            if (loudness > 0)
                Perceivers.Emit(victimAt, loudness, lethal ? "killing" : "struggle");

            // THE TARGET PERCEIVES TOO, and the spec was player -> witnesses
            // until the audit caught it. The most dangerous witness in the game
            // is the man you failed to kill: close, lit, facing you, and with
            // every reason in the world to talk.
            var victimView = Reaction.AsVictim(deed, victimId, familiarityWithActor,
                                               survived: !lethal);
            // AND THE STREET LEARNS WHO YOU ARE. `Violence.Notoriety` has been
            // unit-tested and uncalled since it was written — it is the model
            // that says a brawl outside the bar at noon is the day's news and
            // the same fight in an alley at three is a sound somebody
            // half-heard, and nothing had ever asked it.
            //
            // The witness count is the one already gathered for this deed, so
            // the reputation and the perception agree about how public it was
            // rather than each counting its own crowd.
            if (Game != null && Game.Campaign != null)
                Game.Campaign.Noted(Violence.Notoriety(seen.Count, lethal));

            var reacted = lethal ? Reacted.Ignore : Reacted.Flee;
            bool fleeing = Reaction.IsFleeingVictim(victimView, reacted);
            if (fleeing)
            {
                FleeingVictims++;
                victim.Stance = StanceKind.Avoids;
            }

            // HOW SURE A BYSTANDER IS THAT THIS WAS A KILLING — a different
            // fact from whether they can name anybody. "Somebody killed a man
            // here" travels faster than "Tom Novak killed a man here", and it
            // is the one Ellis acts on first.
            double confidence = 0;
            if (lethal)
                foreach (var o in seen)
                {
                    if (o == null || o.Empty) continue;
                    var walker = WalkerNamed(o.WitnessId);
                    if (walker == null) continue;
                    Vector3 eye = walker.transform.position + Vector3.up * 1.6f;
                    double metres = Vector3.Distance(walker.transform.position, victimAt);
                    bool occluded = Perceivers.Occluded(eye, victimAt + Vector3.up * 1.0f);
                    double c = Ledger.Core.Violence.KillingConfidence(metres, occluded);
                    if (c > confidence) confidence = c;
                }
            if (confidence > PeakKillingConfidence) PeakKillingConfidence = confidence;

            // BLOOD. Not every weapon marks you, and which ones do is most of
            // the reason to pick a cosh over a razor.
            bool marked = Traces.Marks(w);
            if (marked)
            {
                PlayerStain = new Stain
                {
                    AgeMinutes = 0,
                    Strength = 1.0,
                    FromWhom = victimId,
                    YourOwn = false,
                };
                StainsTaken++;
            }

            // AND SOMEBODY IS ACTUALLY HURT. `HarmBook` has carried injuries
            // since M6 and nothing violent had ever filed one, so `IsHurt` and
            // `LooksLike` — the description a witness gives — were both dead.
            if (harm != null)
            {
                var kind = lethal ? InjuryKind.Bad
                         : w != null && w.Family == Family.Edged ? InjuryKind.Cut
                         : w != null && w.Family == Family.Blunt ? InjuryKind.Broken
                         : InjuryKind.Bruised;
                harm.Inflict(victimId, victimId, kind, now.Day,
                             w != null ? w.Name : "hands", visible: true);
            }

            int sawSomething = 0;
            foreach (var o in seen) if (o != null && !o.Empty) sawSomething++;

            Acts++;
            if (lethal) Killings++;
            Last = new Aftermath
            {
                Deed = deed,
                Seen = new List<Observation>(seen),
                VictimView = victimView,
                VictimIsFleeing = fleeing,
                KillingConfidence = confidence,
                MarkedYou = marked,
                Loudness = loudness,
                SawSomething = sawSomething,
            };
            return Last;
        }

        /// What a witness would say the victim looks like now. Rung-2 evidence
        /// — a describable mark, not a name — and the reason `HarmBook` cares
        /// whether an injury is visible.
        public static string VictimLooksLike(HarmBook harm, string victimId, int day) =>
            harm == null || string.IsNullOrEmpty(victimId) ? null
            : harm.IsHurt(victimId, day) ? harm.LooksLike(victimId, day) : null;

        // ---- BLOOD, AFTERWARDS (spec §15.4) -------------------------------
        //
        // The point of all of this is TIME: one violent minute should cost
        // three in-game days. Blood is the cheapest way to buy that, because
        // dealing with it is a decision rather than a timer you wait out.

        /// It does not fade usefully on its own. Called on the game clock.
        public static void AgeStain(double minutes) => Traces.Age(PlayerStain, minutes);

        /// Water, privacy, and twenty-five minutes. Any one of them missing and
        /// you are still wearing it.
        public static bool WashStain(double minutesSpent, bool hasWaterAndPrivacy)
        {
            if (!Traces.Wash(PlayerStain, minutesSpent, hasWaterAndPrivacy)) return false;
            StainsWashed++;
            PlayerStain = null;
            return true;
        }

        /// Would somebody standing there see it. Light and distance, from the
        /// same sensors everything else uses — which is why a stain that would
        /// ruin you in the bar is invisible on the walk home.
        public static bool StainNoticeableFrom(Vector3 eye, Vector3 playerAt) =>
            PlayerStain != null
            && Traces.Noticeable(PlayerStain, Vector3.Distance(eye, playerAt),
                                 Perceivers.LevelAt(playerAt));

        /// A stain is a distinguishing mark, exactly like a limp: it feeds the
        /// identification ladder rather than the case file.
        public static bool StainIsAMark() => Traces.CountsAsMark(PlayerStain);

        /// Blood noticed by a stranger is a rumour; blood noticed by the woman
        /// you are seeing is a scene.
        public static double StainSocialCost(double familiarity) =>
            Traces.SocialCost(PlayerStain, familiarity);

        /// Everybody near enough to see blood on the player right now. Returns
        /// the worst social cost among them, and turns their heads — a stain
        /// nobody reacts to is a stat rather than a consequence.
        public static double NoticeStain(Vector3 playerAt, IEnumerable<NpcWalker> npcs,
                                         System.Func<NpcWalker, double> familiarityOf)
        {
            if (PlayerStain == null || npcs == null) return 0;
            double worst = 0;
            foreach (var n in npcs)
            {
                if (n == null) continue;
                if (!StainNoticeableFrom(n.transform.position + Vector3.up * 1.6f, playerAt))
                    continue;
                StainsNoticed++;
                double cost = StainSocialCost(familiarityOf != null ? familiarityOf(n) : 0.0);
                if (cost > worst) worst = cost;
                if (n.Stance < StanceKind.Notices) n.Stance = StanceKind.Notices;
            }
            if (worst > WorstStainCost) WorstStainCost = worst;
            return worst;
        }

        // ---- HELPERS ------------------------------------------------------

        /// The walker behind a witness id. `Witnesses` reports ids because Core
        /// deals in ids; the reactions above need the object.
        static IEnumerable<NpcWalker> _npcs;
        public static void BindWalkers(IEnumerable<NpcWalker> npcs) => _npcs = npcs;

        static NpcWalker WalkerNamed(string id)
        {
            if (_npcs == null || string.IsNullOrEmpty(id)) return null;
            foreach (var n in _npcs)
                if (n != null && n.DisplayName == id) return n;
            return null;
        }
    }
}
