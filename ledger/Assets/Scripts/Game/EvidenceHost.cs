using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE OBJECT HAS A LIFE — weapons-spec Phase 4, §7.3 and §7.4.
    ///
    /// Phase 3 made the act happen. This is what the act leaves behind that is
    /// not blood: a physical thing with a history, which somebody sold you,
    /// which you used, which you got rid of, and which Ellis can follow back.
    ///
    /// THE POINT IS THAT ELLIS HUNTS THE OBJECT RATHER THAN YOU. A detective
    /// who looks for the culprit is a detective the player can only hide from.
    /// A detective who looks for the *knife* is a detective the player can
    /// bargain with, mislead, out-run and out-think, because the knife has a
    /// seller with a memory and a canal it could be at the bottom of. That is
    /// the whole reason provenance exists, and it costs no new perception code
    /// — it is a string on an object.
    ///
    /// FOUR ROUTES, ALL SOCIAL, and no random world loot. A pistol in a bin is
    /// a video game; a pistol you can name the seller of is this game. Bought
    /// is the strongest thread at 0.85 because a named seller who remembers
    /// leads to a CONVERSATION rather than to a forensics lab. Ordinary is 0.05
    /// because every kitchen has one.
    ///
    /// DISPOSAL IS A VERB SOMEBODY CAN WATCH YOU PERFORM, which the spec calls
    /// the best single idea to survive from v1 untouched. Getting rid of it
    /// removes the object and leaves the act of getting rid of it — and if
    /// somebody saw that, you have traded a findable weapon for a witness who
    /// watched a man drop something in the canal at two in the morning. That is
    /// a worse position than having kept it, and `ResidualRisk` says so in a
    /// number the player can reason their way to before finding out.
    public static class EvidenceHost
    {
        /// Every object the player has ever held, by instance id. Never pruned:
        /// a disposed item still has a history, and the history is the point.
        static readonly Dictionary<string, Traces.Item> _items =
            new Dictionary<string, Traces.Item>();

        public static IEnumerable<Traces.Item> All => _items.Values;
        public static int Acquired { get; private set; }
        public static int Disposed { get; private set; }
        public static int DisposalsSeen { get; private set; }
        /// Latched highs, because a gate reads them at the end of a run and the
        /// object it cares about may have been dropped hours earlier.
        public static double PeakTraceability { get; private set; }
        public static double PeakResidual { get; private set; }
        public static int Accidents { get; private set; }
        public static int AccidentsRefused { get; private set; }

        public static void Reset()
        {
            _items.Clear();
            Acquired = Disposed = DisposalsSeen = 0;
            PeakTraceability = PeakResidual = 0;
            Accidents = AccidentsRefused = 0;
        }

        // ---- WHERE IT CAME FROM (spec §7.3) -------------------------------

        /// Take possession of something, by one of the four social routes.
        ///
        /// `fromWhom` is the thread. It is deliberately a person's name and not
        /// an id of a shop, because every route in this design ends at somebody
        /// who can be leaned on — by the player, or by Ellis.
        public static Traces.Item Acquire(string instanceId, string weaponId,
                                          Traces.Origin origin, string fromWhom)
        {
            var it = Traces.Acquire(instanceId, weaponId, origin, fromWhom);
            if (it == null) return null;
            _items[instanceId] = it;
            Acquired++;
            double t = Traces.Traceability(it);
            if (t > PeakTraceability) PeakTraceability = t;
            return it;
        }

        public static Traces.Item Get(string instanceId) =>
            instanceId != null && _items.TryGetValue(instanceId, out var it) ? it : null;

        /// Something was done with it, in order, never cleared. `killed:` is
        /// the prefix `Item.UsedInAKilling` reads, which is what turns a frisk
        /// into an interrogation.
        public static void Used(Traces.Item it, string what, string onWhom)
        {
            Traces.Used(it, what, onWhom);
            if (it != null)
            {
                double r = Traces.ResidualRisk(it);
                if (r > PeakResidual) PeakResidual = r;
            }
        }

        /// How strong the thread back to you is, right now.
        public static double Traceability(Traces.Item it) => Traces.Traceability(it);

        // ---- GETTING RID OF IT (spec §7.4) --------------------------------

        /// Drop it somewhere, and find out who was watching.
        ///
        /// WHO SAW IT IS ASKED OF THE WORLD, not passed in. Disposal being
        /// witnessable is the entire idea, so the witness test has to run
        /// against the real street — same sensors, same occlusion, same light
        /// as everything else. A caller that supplied its own answer would be
        /// deciding the interesting part for itself.
        public static bool Dispose(Traces.Item it, string where, Vector3 at,
                                   IEnumerable<NpcWalker> npcs)
        {
            if (it == null || it.Disposed) return false;
            bool seen = SomebodyWatching(at, npcs);
            Traces.Dispose(it, where, seen);
            Disposed++;
            if (seen) DisposalsSeen++;
            double r = Traces.ResidualRisk(it);
            if (r > PeakResidual) PeakResidual = r;
            return seen;
        }

        /// What it still costs you once it is gone. Never zero if it was used
        /// in a killing and somebody watched you get rid of it.
        public static double ResidualRisk(Traces.Item it) => Traces.ResidualRisk(it);

        /// Anybody with an unobstructed line to this spot, close enough to make
        /// out what a pair of hands is doing. Deliberately shorter than the
        /// sighting range: recognising that a man threw something is a closer
        /// question than recognising that a man is there.
        /// The same question, asked from outside, so a caller staging a
        /// "somebody is watching" case can CHOOSE a spot that satisfies it
        /// instead of picking one that looks right and hoping.
        ///
        /// WHY THIS IS PUBLIC. `disposal` and `accident` both compare a watched
        /// place against an unwatched one, and both went red together on a run
        /// reading `seen=False` against `seen=False`, `risk=0.30` against
        /// `risk=0.30`, and an accident available in company. All three are what
        /// you get when the "crowded" spot has nobody watching it.
        ///
        /// The sim was picking that spot by counting NEIGHBOURS within
        /// `Rung2MarkMetres`, while this asks for range AND an unobstructed line
        /// AND the watcher to be facing within half the field of view. A knot of
        /// people all looking the other way maximises the first and fails the
        /// second, so the selection criterion and the test criterion were
        /// different questions — the scope mismatch this project keeps finding
        /// in a new place. Now the stager asks the predicate.
        public static bool Watched(Vector3 at, IEnumerable<NpcWalker> npcs) =>
            SomebodyWatching(at, npcs);

        static bool SomebodyWatching(Vector3 at, IEnumerable<NpcWalker> npcs)
        {
            if (npcs == null) return false;
            foreach (var n in npcs)
            {
                if (n == null) continue;
                Vector3 eye = n.transform.position + Vector3.up * 1.6f;
                if (Vector3.Distance(n.transform.position, at) > Perception.Rung2MarkMetres)
                    continue;
                if (Perceivers.Occluded(eye, at + Vector3.up * 1.0f)) continue;
                if (Perceivers.OffAxis(n.transform, at) > Perception.FovDegrees * 0.5) continue;
                return true;
            }
            return false;
        }

        // ---- ELLIS FOLLOWS THE OBJECT -------------------------------------

        /// The strongest thread still leading anywhere, and what it leads to.
        ///
        /// This is what a detective works on when she has no witness: not "who
        /// did it" but "whose knife was it, and who did he sell it to".
        public static Traces.Item StrongestThread(out double risk)
        {
            Traces.Item worst = null;
            risk = 0;
            foreach (var it in _items.Values)
            {
                double r = Traces.ResidualRisk(it);
                if (r <= risk) continue;
                risk = r;
                worst = it;
            }
            return worst;
        }

        /// Whether the detective is asking about the player by name yet, and
        /// how much of the pressure a body is responsible for.
        public static bool EllisIsAskingAboutYou(HomicideBook book, GossipMill mill, int today = -1)
        {
            if (book == null) return false;
            return Police.AsksAboutYou(InquiryOf(book, mill, today));
        }

        /// The inquiry level, which follows from bodies and from who can still
        /// name you rather than from street noise.
        ///
        /// ONE IMPLEMENTATION NOW. This used to compute the stage itself —
        /// bodies, plus a flat `NamedWeight` if anybody could name you, plus
        /// corroboration — beside `HomicideBook.Stage`, which computes the same
        /// stage scaled by how sure the strongest witness is. Two answers to one
        /// question, agreeing most of the time and differing whenever the
        /// strongest witness was under certain, and this is the fifth pair of
        /// this shape found in a night. The redirect made it urgent rather than
        /// merely untidy: `PointAt` moves `Stage` and could never have moved
        /// this, so the game would have had a detective who was looking
        /// elsewhere according to one call and at you according to the other.
        ///
        /// THE BEHAVIOUR CHANGE IS DELIBERATE AND SMALL, and it is stated rather
        /// than slipped in. `LiveWitnesses` only returns people at or above
        /// `TestimonyGrade` (0.50), so the flat version was reading 0.60 for a
        /// witness the mill grades between 0.50 and 1.00 — pessimistic by up to
        /// 0.30 of pressure. `Stage` uses the grade the mill actually holds,
        /// which is the number every other consequence in this game is decided
        /// by, so the divergence resolves toward the rest of the project rather
        /// than away from it.
        public static Inquiry InquiryOf(HomicideBook book, GossipMill mill, int today = -1) =>
            book == null || book.BodyCount == 0 ? Inquiry.None : book.Stage(mill, null, today);

        /// Who among the people who watched would actually go to the police.
        ///
        /// Not the disloyal ones — the ones with the least nerve AND the least
        /// to lose, and that asymmetry is the interesting part: the man who
        /// likes you least is not the man who talks.
        public static List<string> WhoWouldTalk(GossipMill mill, IEnumerable<string> whoWatched)
        {
            var talkers = new List<string>();
            if (mill == null || whoWatched == null) return talkers;
            foreach (var id in whoWatched)
            {
                var g = mill.Get(id);
                if (Watched.WouldTalkToPolice(g)) talkers.Add(id);
            }
            return talkers;
        }

        // ---- ACCIDENTS (spec §5.2, family 6) ------------------------------

        /// THE ONLY VIOLENCE IN THE GAME THAT PRODUCES NO CRIME, and it is
        /// hedged three ways or it ends the design: if the stairs always work,
        /// the optimal player never touches a weapon again.
        ///
        /// He has to be in position, and you have to be ALONE with him there —
        /// so this asks the world how many people can see the spot rather than
        /// taking a caller's word for it. And being seen doing it is the worst
        /// observation in the game: there is no weapon, no struggle, nothing to
        /// point at, so a full sighting of a push is more damning than one of a
        /// stabbing. That penalty is what stops the family dominating.
        public static bool AccidentAvailable(Weapon w, Vector3 at, bool inPosition,
                                             IEnumerable<NpcWalker> npcs)
        {
            int watching = 0;
            if (npcs != null)
                foreach (var n in npcs)
                {
                    if (n == null) continue;
                    if (Vector3.Distance(n.transform.position, at) > Perception.DetectRangeMetres)
                        continue;
                    if (Perceivers.Occluded(n.transform.position + Vector3.up * 1.6f,
                                            at + Vector3.up * 1.0f)) continue;
                    watching++;
                }
            bool ok = Arsenal.AccidentAvailable(w, inPosition, watching);
            if (ok) Accidents++; else AccidentsRefused++;
            return ok;
        }

        /// And it only reads as an accident because there was nothing to draw.
        public static bool IsAccident(Weapon w) => Arsenal.IsAccident(w);
    }
}
