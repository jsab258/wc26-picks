using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// Combat phase 3b — THE BODY (game-design/combat-spec.md §7b).
    ///
    /// This is not a damage system and it is not part of the fighting. It is
    /// what happens to a world after somebody in it dies, and it is the
    /// largest genuinely new piece of work the lethality answer created.
    ///
    /// The design problem, stated honestly: killing a witness has to GENUINELY
    /// WORK. If it does not stop the rumour, the choice is fake and the player
    /// notices inside one attempt. So the containment has to be real — and the
    /// price has to be bigger than what it bought. Everything below exists to
    /// make that trade true as arithmetic rather than as an assertion in a
    /// design document.
    ///
    /// The shape of it: killing the only witness to a killing genuinely drops
    /// the police from a manhunt back to an investigation. It never drops them
    /// back to procedure, and it never drops them to nothing. Each body you
    /// add to fix the last one leaves you worse off than before the first.
    public class Killing
    {
        public string VictimId;
        public string VictimName;
        public int Day;
        public int Hour;
        public string Where;

        /// Everybody who saw it and can put YOU at the end of it. The ids are
        /// gossipers; whether they are still alive is the mill's business, and
        /// whether they will still say so is nobody's — a killing cannot be
        /// bought or scared quiet.
        public readonly List<string> SawYouDoIt = new List<string>();

        /// Everybody who knows there is a body without being able to name who
        /// made it. They escalate the police without convicting anybody.
        public readonly List<string> KnowsOfIt = new List<string>();

        /// The topic key this killing occupies in the mill. Per victim, so two
        /// killings are two facts and containing one never touches the other.
        public string TopicKey => "player.killed_" + VictimId;

        public Fact Fact => new Fact("player", "killed_" + VictimId, "true");

        public string Summary =>
            $"the new owner killed {VictimName}";
    }

    /// How hard the police are looking. Read off Mara Ellis's behaviour, never
    /// off a meter — she is the one character in the game equipped to carry
    /// this, and design-doc §8 has her as patient rather than threatening.
    public enum Inquiry
    {
        /// No body. Ellis appears on street heat alone, as she always has.
        None,
        /// There is a body and it is a case. She is on the street whatever the
        /// talk is doing, and she is not asking about you.
        Procedure,
        /// She is asking about you by name.
        Investigation,
        /// She has enough to act on and is no longer being patient.
        Manhunt,
    }

    /// The register of killings, and the police pressure that follows from it.
    public class HomicideBook
    {
        readonly List<Killing> _killings = new List<Killing>();
        public IReadOnlyList<Killing> Killings => _killings;
        public int BodyCount => _killings.Count;
        public bool Any => _killings.Count > 0;

        /// Weight per body, whether or not anyone can name you for it. A body
        /// found in an alley with nobody around is still a homicide file.
        public const double PerBody = 0.4;
        /// Weight of the strongest living witness who can name you.
        public const double NamedWeight = 0.6;
        /// Every witness after the first. Corroboration is what turns one
        /// person's word into a case.
        public const double PerExtraWitness = 0.25;

        public const double InvestigationAt = 0.7;
        public const double ManhuntAt = 1.0;

        /// Testimony grade — deliberately the same bar Act III already uses for
        /// what would stand up in front of a magistrate
        /// (`LedgerState.CaseStandsAt`, and it said `ActThree` here for
        /// months — a type that has never existed. Nothing dereferences a
        /// comment, so the compiler could not say so; it was found by
        /// copying the name out of it into real code, which is the only
        /// way a false comment ever gets found).
        public const double TestimonyGrade = 0.5;

        public Killing Record(string victimId, string victimName, int day, int hour, string where)
        {
            if (string.IsNullOrEmpty(victimId)) return null;
            var existing = _killings.FirstOrDefault(k => k.VictimId == victimId);
            // You cannot kill the same person twice, and a double-recorded body
            // would double the pressure off one act.
            if (existing != null) return existing;
            var k = new Killing
            {
                VictimId = victimId, VictimName = victimName ?? victimId,
                Day = day, Hour = hour, Where = where,
            };
            _killings.Add(k);
            return k;
        }

        public Killing Of(string victimId) => _killings.FirstOrDefault(k => k.VictimId == victimId);

        // -- WHERE THE DETECTIVE IS LOOKING ---------------------------------

        /// Who the law is currently asking about instead of you, and the day the
        /// charge stuck. Empty when nobody has been pointed at.
        ///
        /// THIS IS THE HALF OF `Informing` THAT DID NOT EXIST. `RedirectsInquiry`
        /// was written last night and returns a bool that nothing could act on,
        /// because the roadmap's own note says why: *"`Inquiry` is derived from
        /// the homicide book rather than stored, so there is no value to point
        /// elsewhere."* A verb whose effect has nowhere to land is rule 6 on
        /// four-hour-old code.
        public string PointedAt { get; private set; } = "";
        public int PointedOnDay { get; private set; } = -1;

        /// How much of the NAMED pressure a fresh redirect takes off, and how
        /// long before it is entirely gone.
        ///
        /// IT SUBTRACTS FROM THE NAMED TERM ONLY, and that is the design rather
        /// than a safety clamp. `Pressure` is bodies plus whoever will name you;
        /// a detective who has been pointed at somebody else stops weighing the
        /// witness, and the bodies are still on her desk. So a redirect can walk
        /// a manhunt back to an investigation and can never walk it to nothing —
        /// the same arithmetic, and the same lesson, as killing the one witness
        /// to your killing, which this book has always priced that way.
        ///
        /// AND IT DECAYS, WHICH IS THE WHOLE POINT. Buying time is a decision
        /// with a shape: four days of quiet, then she is back, and you have a
        /// `lied_to_police` fact on you for the rest of the save if it blew back.
        /// A permanent redirect would be the most exploitable thing in the game —
        /// `Informing`'s own comment says exactly that about manhunts — and a
        /// consequence that expires cleanly is the opposite of consequence
        /// persistence 95, which is the moat this project is built on.
        /// THE SIZE COMES OUT OF THE EXISTING NUMBERS, not out of the air. The
        /// strongest case there is — one body, one witness certain — is
        /// `PerBody + NamedWeight` = 1.00, a manhunt. For a redirect to walk
        /// that back to an investigation and no further it must leave at least
        /// `InvestigationAt - PerBody` = 0.30 of the named 0.60 standing, so the
        /// relief cannot exceed 0.50. 0.45 sits just inside that rather than on
        /// the boundary, because a gate decided by the last bit of a double is a
        /// gate decided by nothing.
        ///
        /// My first draft was 0.60, written before any of this was worked out,
        /// and it took a manhunt to 0.64 — straight past investigation into
        /// procedure, which is most of the way to the exploit `Informing`
        /// exists to refuse. The test caught it in a second because it asserted
        /// the SENTENCE in the comment rather than the number in the code.
        public const double RedirectRelief = 0.45;
        public const int RedirectHolds = 4;

        /// A charge stuck. She is asking about them now.
        ///
        /// Only ever called with `Accusation.Charged` and an inquiry that was
        /// below `Investigation` — `Informing.RedirectsInquiry` is the gate, and
        /// it lives there rather than here so the police machinery does not have
        /// to know what an accusation is.
        public void PointAt(string suspectId, int day)
        {
            if (string.IsNullOrEmpty(suspectId) || suspectId == "player") return;
            PointedAt = suspectId;
            PointedOnDay = day;
        }

        /// How much of the named pressure is currently lifted, 0..1.
        ///
        /// `today` below the day it was pointed means the caller does not know
        /// what day it is, and the answer is then zero rather than full relief:
        /// an un-wired caller must not get a discount it never asked for. That
        /// is the same principle as `perfOk` refusing to pass on no samples —
        /// an absent measurement is not a passing one.
        public double RedirectReliefOn(int today)
        {
            if (string.IsNullOrEmpty(PointedAt) || PointedOnDay < 0) return 0;
            if (today < PointedOnDay) return 0;
            int elapsed = today - PointedOnDay;
            if (elapsed >= RedirectHolds) return 0;
            return RedirectRelief * (1.0 - (double)elapsed / RedirectHolds);
        }

        /// Plant every witness's version in the mill, as facts rather than
        /// stories. `alive` answers whether a given id is still walking around
        /// — a dead witness carries nothing, and that is the entire point of
        /// the trade this system exists to price.
        public void FileWith(GossipMill mill, Killing k, GameTime now, Func<string, bool> alive = null)
        {
            if (mill == null || k == null) return;
            foreach (var id in k.SawYouDoIt)
            {
                if (alive != null && !alive(id)) continue;
                mill.Witness(id, k.Fact, k.Summary, true, now,
                    Violence.BodyConfidence, indelible: true);
            }
            foreach (var id in k.KnowsOfIt)
            {
                if (alive != null && !alive(id)) continue;
                // They know there is a body. They cannot put you at the end of
                // it, so what they carry is the death, not the killer.
                var f = new Fact(k.VictimId, "died", "violently");
                mill.Witness(id, f, $"{k.VictimName} was killed", false, now, 1.0, indelible: true);
            }
        }

        /// Who can still put you at the end of a killing, and how sure the
        /// strongest of them is. A witness the mill has forgotten does not
        /// count — but the mill cannot forget an indelible rumour, so in
        /// practice only death removes one, which is exactly the pressure the
        /// design wants on the player.
        public List<string> LiveWitnesses(GossipMill mill, Func<string, bool> alive = null)
        {
            var live = new List<string>();
            if (mill == null) return live;
            foreach (var k in _killings)
                foreach (var id in k.SawYouDoIt)
                {
                    if (live.Contains(id)) continue;
                    if (alive != null && !alive(id)) continue;
                    var g = mill.Get(id);
                    if (g == null) continue;
                    var r = g.BestOfValue(k.TopicKey, "true");
                    if (r != null && r.Confidence >= TestimonyGrade) live.Add(id);
                }
            return live;
        }

        /// The number that decides how hard the police are looking.
        ///
        /// Worked through, because the balance IS the design and it should be
        /// checkable by reading rather than by playing:
        ///
        ///   one body, nobody saw            0.40  procedure
        ///   one body, one witness at 0.6    0.76  investigation
        ///   one body, one witness certain   1.00  manhunt
        ///   two bodies, nobody left to talk 0.80  investigation
        ///   three bodies, nobody left       1.20  manhunt
        ///
        /// Read the third and fourth lines together: killing the one witness to
        /// your killing REALLY DOES take the manhunt off you. It takes you back
        /// to an investigation — not to procedure, and never to nothing. Do it
        /// once more and you are past where the first body put you. Violence
        /// works, and it costs more than it saves, and here that is arithmetic.
        ///
        /// AND ONE MORE LINE, SINCE 4 AUGUST. If a charge against somebody else
        /// has stuck, the named half is reduced while it holds:
        ///
        ///   one body, one witness certain              1.00  manhunt
        ///   the same, day the redirect lands           0.73  investigation
        ///   the same, one day later                    0.80  investigation
        ///   the same, two days later                   0.87  investigation
        ///   the same, three days later                 0.93  investigation
        ///   the same, four days later                  1.00  manhunt again
        ///
        /// Read the first and last lines together: pointing a detective at
        /// somebody buys you four days and gives back exactly what it took.
        ///
        /// A THINNER CASE MOVES FURTHER, and that is right rather than a bug.
        /// One witness at 0.6 is 0.76, an investigation; redirected on the day
        /// it lands it is 0.60, procedure. The relief is a fixed fraction of the
        /// named pressure, so it is worth more when less of the street is
        /// naming you — which is what having less to redirect away from means.
        ///
        /// `today` defaults to -1, meaning the caller does not know the date, and
        /// then no relief applies at all. A discount nobody asked for is worse
        /// than no discount.
        public double Pressure(GossipMill mill, Func<string, bool> alive = null, int today = -1)
        {
            if (_killings.Count == 0) return 0;
            double p = _killings.Count * PerBody;
            var live = LiveWitnesses(mill, alive);
            if (live.Count > 0)
            {
                double best = 0;
                foreach (var k in _killings)
                    foreach (var id in live)
                    {
                        var r = mill.Get(id)?.BestOfValue(k.TopicKey, "true");
                        if (r != null && r.Confidence > best) best = r.Confidence;
                    }
                double named = NamedWeight * best + PerExtraWitness * (live.Count - 1);
                // THE BODIES ARE NOT REDIRECTED. Only the part of the pressure
                // that comes from somebody naming you is, which is what makes
                // this incapable of clearing an inquiry however well it goes.
                p += named * (1.0 - RedirectReliefOn(today));
            }
            return p;
        }

        public Inquiry Stage(GossipMill mill, Func<string, bool> alive = null, int today = -1)
        {
            double p = Pressure(mill, alive, today);
            if (p <= 0) return Inquiry.None;
            if (p >= ManhuntAt) return Inquiry.Manhunt;
            if (p >= InvestigationAt) return Inquiry.Investigation;
            return Inquiry.Procedure;
        }

        // -- save/load ----------------------------------------------------

        // THE REDIRECT SAVES. A consequence that survives until you reload is
        // not a consequence, and this project scores itself 95 on persistence —
        // so where the detective is looking has to be in the file with the
        // bodies. `SaveChaos` throws malformed values at every field here, and
        // `RedirectReliefOn` already refuses a day it cannot make sense of.
        public Dictionary<string, object> ToJson() => new Dictionary<string, object>
        {
            { "pointedAt", PointedAt },
            { "pointedOnDay", PointedOnDay },
            { "killings", _killings.Select(k => (object)new Dictionary<string, object>
                {
                    { "victim", k.VictimId }, { "name", k.VictimName },
                    { "day", k.Day }, { "hour", k.Hour }, { "where", k.Where },
                    { "saw", k.SawYouDoIt.Cast<object>().ToList() },
                    { "knew", k.KnowsOfIt.Cast<object>().ToList() },
                }).ToList() },
        };

        public void FromJson(Dictionary<string, object> d)
        {
            _killings.Clear();
            PointedAt = "";
            PointedOnDay = -1;
            if (d == null) return;
            // NAMING THE PLAYER FROM A FILE IS THE SAME REFUSAL AS NAMING THEM
            // FROM CODE. `PointAt` will not do it and neither will a save — a
            // hand-edited file must not be a second, quieter route into a state
            // the game says is impossible. Same shape as `Restore` clamping
            // negative job counts, which `SaveChaos` found fifteen of.
            string who = MiniJson.GetString(d, "pointedAt");
            if (!string.IsNullOrEmpty(who) && who != "player")
            {
                PointedAt = who;
                PointedOnDay = MiniJson.GetInt(d, "pointedOnDay");
            }
            foreach (var o in MiniJson.GetList(d, "killings") ?? new List<object>())
            {
                var k = o as Dictionary<string, object>;
                if (k == null) continue;
                var rec = new Killing
                {
                    VictimId = MiniJson.GetString(k, "victim"),
                    VictimName = MiniJson.GetString(k, "name"),
                    Day = MiniJson.GetInt(k, "day"),
                    Hour = MiniJson.GetInt(k, "hour"),
                    Where = MiniJson.GetString(k, "where"),
                };
                foreach (var s in MiniJson.GetList(k, "saw") ?? new List<object>())
                    if (s is string id) rec.SawYouDoIt.Add(id);
                foreach (var s in MiniJson.GetList(k, "knew") ?? new List<object>())
                    if (s is string id) rec.KnowsOfIt.Add(id);
                if (!string.IsNullOrEmpty(rec.VictimId)) _killings.Add(rec);
            }
        }
    }

    /// What the inquiry stage DOES — kept apart from the arithmetic so the
    /// consequences can be read in one place, and so the Game layer has one
    /// obvious thing to ask.
    public static class Police
    {
        /// Below Procedure, Ellis waits for the street to get loud. From
        /// Procedure up she is already there, and the heat threshold is moot:
        /// a body is how a detective gets assigned.
        public static bool SummonsEllis(Inquiry i) => i >= Inquiry.Procedure;

        /// She asks about the player by name rather than about the street.
        public static bool AsksAboutYou(Inquiry i) => i >= Inquiry.Investigation;

        /// Act III cannot be waited out once there is a case with your name on
        /// it. The audit clock is a paperwork clock; this is not.
        public static bool ForcesActThree(Inquiry i) => i >= Inquiry.Investigation;

        /// The endings that stop being reachable. Handing the bar to a
        /// successor and walking away is not available to somebody the police
        /// are actively hunting, and no amount of empire management changes
        /// that.
        public static bool BarsQuietExit(Inquiry i) => i >= Inquiry.Manhunt;

        /// While there is an open homicide, nothing about the player goes cold.
        /// Ellis already stretches rumour half-life by being on the street;
        /// this stretches it further, because people keep retelling what the
        /// police keep asking about.
        public static double RumorHalfLifeHours(Inquiry i, double baseHours) =>
            i >= Inquiry.Investigation ? baseHours * 2.0
            : i >= Inquiry.Procedure ? baseHours * 1.5
            : baseHours;

        /// A floor under day-circle suspicion. Not a raise applied once — a
        /// floor, because the reason it is there does not go away.
        ///
        /// AND SINCE 4 AUGUST IT CAN FALL, WHICH THE SENTENCE ABOVE DOES NOT
        /// SAY BY ITSELF. `HomicideBook.PointAt` moves the stage down for four
        /// days, so a floor of 0.7 becomes 0.45 and then climbs back. The claim
        /// survives — the floor still tracks the reason rather than being a
        /// one-off bump, and the bodies are still on the books the whole time —
        /// but "does not go away" now means the CAUSE, not the number.
        public static double SuspicionFloor(Inquiry i) =>
            i >= Inquiry.Manhunt ? 0.7 :
            i >= Inquiry.Investigation ? 0.45 :
            i >= Inquiry.Procedure ? 0.15 : 0.0;

        public static string Describe(Inquiry i) =>
            i == Inquiry.Manhunt ? "They are not being patient any more."
            : i == Inquiry.Investigation ? "The detective has started using your name."
            : i == Inquiry.Procedure ? "There is a detective on the street who was not here last week."
            : "";
    }

    /// THE CREW WHO WATCHED (combat-spec §7b).
    ///
    /// "Nobody who saw it is ever quite the same about you." Loyalty already
    /// exists and already moves; what a killing does is different in kind. It
    /// puts a CEILING on how loyal somebody can ever be again, and no amount
    /// of paying them well, supplying their need or protecting them lifts it.
    public static class Watched
    {
        /// A steady hand is nearly unchanged. A nervous one is permanently
        /// half out the door — and the nervous ones are the ones who talk.
        public static double LoyaltyCeiling(double nerve) =>
            Feel.Clamp(0.35 + 0.5 * Feel.Clamp01(nerve), 0.35, 0.85);

        /// Apply the ceiling to somebody who watched. Idempotent: calling it
        /// again on the same person does nothing further, so a nightly tick can
        /// hold the ceiling down without grinding loyalty to zero.
        public static void Saw(Gossiper g, GameTime now)
        {
            if (g == null) return;
            double ceiling = LoyaltyCeiling(g.Nerve);
            if (g.Loyalty > ceiling) g.Loyalty = ceiling;
            g.Nerve = Feel.Clamp01(g.Nerve - 0.1);
            if (!g.Memory.Events.Any(e => e.Text.StartsWith("I watched them do it")))
                g.Memory.Append(new MemoryEvent(now, "observation", 1.0,
                    "I watched them do it. I have not decided what that makes me."));
        }

        /// Would this person go to the police about it? The ones with the least
        /// to lose and the least nerve for it — which is not the same set as
        /// the disloyal ones, and that asymmetry is the interesting part.
        public static bool WouldTalkToPolice(Gossiper g) =>
            g != null && g.Nerve < 0.35 && g.Loyalty < 0.5 && !g.Leashed;
    }
}
