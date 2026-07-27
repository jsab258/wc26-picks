using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// Phones and the distance layer (roadmap M10).
    ///
    /// A second information channel, with its own reach and its own fidelity —
    /// and the whole design turns on one period-correct fact:
    ///
    /// **A PHONE IS A PLACE, NOT A POCKET.**
    ///
    /// You do not call a person. You call the bar, or the hall phone at the
    /// boarding house, or the foundry office, and whoever is near it answers.
    /// That single constraint generates every interesting thing here without a
    /// line of special-case code:
    ///
    ///   - Reaching somebody is a gamble on their schedule, so timing is play.
    ///   - Somebody else picking up is not a failure state, it is the most
    ///     interesting outcome — you now decide whether to leave a message with
    ///     a person who now knows you called.
    ///   - A message travels as talk, with an extra hop and less confidence,
    ///     which is the gossip mill doing its existing job.
    ///   - Being unreachable at the wrong moment is a thing that happens TO the
    ///     player, which the walking city could never do before.
    ///
    /// The trade against meeting somebody in person is deliberate and symmetric:
    /// a phone reaches across the city instantly, and it cannot read a face. So
    /// suspicion moves less on a call — your lies land better, and so do theirs.

    public enum CallResult
    {
        /// Nobody has a phone there.
        NoLine,
        /// It rang out. Nobody near it.
        NoAnswer,
        /// They answered.
        Answered,
        /// Somebody else answered. The interesting one.
        SomebodyElse,
    }

    /// A phone, which belongs to somewhere.
    public class Phone
    {
        public string PlaceId;
        public string PlaceName;
        /// Who can be expected near it, in the order they would reach for it.
        public readonly List<string> Regulars = new List<string>();
        /// A hall phone in a boarding house is answered by whoever is passing.
        /// A private line in an office is not.
        public bool Public;
        /// Hours the line is worth trying at all. A foundry office at three in
        /// the morning is a bell in an empty room.
        public int OpenFrom = 7, OpenTo = 23;

        public bool LiveAt(int hour) => hour >= OpenFrom && hour < OpenTo;
    }

    public class Call
    {
        public CallResult Result;
        public string PlaceId, PlaceName;
        /// Who actually picked up, when anybody did.
        public string AnsweredById, AnsweredByName;
        /// Who you were trying to reach.
        public string WantedId;
        public string Line;
    }

    public class PhoneBook
    {
        /// A call cannot read a face, so suspicion moves less than half as far
        /// as it would across a table. This is the price of reach, and it cuts
        /// both ways — which is what stops it being a straight upgrade.
        public const double FidelityOnTheLine = 0.45;

        /// A message left with somebody arrives as talk rather than as speech:
        /// one more hop, and the confidence to match.
        public const double MessageConfidence = 0.55;

        readonly List<Phone> _phones = new List<Phone>();
        public IReadOnlyList<Phone> All => _phones;

        public void Add(Phone p) { if (p != null) _phones.Add(p); }

        public Phone AtPlace(string placeId)
        {
            foreach (var p in _phones) if (p.PlaceId == placeId) return p;
            return null;
        }

        /// Every line this person could conceivably be reached on.
        public List<Phone> LinesFor(string personId)
        {
            var list = new List<Phone>();
            foreach (var p in _phones) if (p.Regulars.Contains(personId)) list.Add(p);
            return list;
        }

        /// Ring a place and see who picks up.
        ///
        /// `whoIsNear` answers "is this person by that phone right now" — it
        /// comes from the same schedules the walkers use, so a call is a real
        /// question about where somebody is rather than a dice roll.
        public Call Ring(string placeId, string wantedId, GameTime now,
            Func<string, string, bool> whoIsNear, Func<string, string> nameOf = null)
        {
            var phone = AtPlace(placeId);
            var call = new Call { PlaceId = placeId, WantedId = wantedId, PlaceName = phone?.PlaceName };
            if (phone == null)
            {
                call.Result = CallResult.NoLine;
                call.Line = "There is no line there. Some places in this city still expect you to walk.";
                return call;
            }
            if (!phone.LiveAt(now.Hour))
            {
                call.Result = CallResult.NoAnswer;
                call.Line = $"It rings in an empty {phone.PlaceName}. Nobody keeps that line at this hour.";
                return call;
            }

            // Whoever is nearest the phone reaches for it, in the order they
            // would — which is why calling somewhere at the wrong hour gets you
            // the wrong person rather than getting you nobody.
            foreach (var candidate in phone.Regulars)
            {
                if (whoIsNear != null && !whoIsNear(candidate, placeId)) continue;
                call.AnsweredById = candidate;
                call.AnsweredByName = nameOf != null ? nameOf(candidate) : candidate;
                call.Result = candidate == wantedId ? CallResult.Answered : CallResult.SomebodyElse;
                call.Line = call.Result == CallResult.Answered
                    ? $"{call.AnsweredByName} picks up on the fourth ring."
                    : $"{call.AnsweredByName} picks up. Not who you wanted, and now they know you rang.";
                return call;
            }

            call.Result = CallResult.NoAnswer;
            call.Line = $"It rings out. Whoever is in {phone.PlaceName} is not answering the phone.";
            return call;
        }

        /// Leave a message with whoever answered.
        ///
        /// The cost is the point: the person holding your message now knows you
        /// called and roughly what about, and they are under no obligation at
        /// all to be discreet. It goes into the mill as talk — one hop out,
        /// second-hand confidence — which is exactly what a message passed along
        /// by somebody actually is.
        public bool LeaveMessage(Call call, GossipMill mill, string aboutWhom, string summary, GameTime now)
        {
            if (call == null || mill == null || call.AnsweredById == null) return false;
            var taker = mill.Get(call.AnsweredById);
            if (taker == null) return false;

            taker.Memory.Append(new MemoryEvent(now, "conversation", 0.5,
                $"Took a message on the {call.PlaceName} line. {summary}"));
            taker.Rumors.Add(new Rumor
            {
                Content = new Fact(aboutWhom, "left_word", call.WantedId ?? "somebody"),
                OriginId = call.AnsweredById,
                Summary = summary,
                Confidence = MessageConfidence,
                Hops = 1,
                Sensitive = false,
            });
            return true;
        }

        /// Can this person be reached AT ALL right now, on any line? The answer
        /// the player most wants and the one they are never simply told — it is
        /// what makes an evening where somebody cannot be found feel like the
        /// city rather than like a locked door.
        public bool ReachableNow(string personId, GameTime now, Func<string, string, bool> whoIsNear)
        {
            foreach (var p in LinesFor(personId))
            {
                if (!p.LiveAt(now.Hour)) continue;
                if (whoIsNear == null || whoIsNear(personId, p.PlaceId)) return true;
            }
            return false;
        }

        /// How much a suspicion move is worth when it happens on the phone.
        /// A voice on a line is not a face across a table, in both directions.
        public static double Damped(double inPersonAmount) => inPersonAmount * FidelityOnTheLine;

        public Dictionary<string, object> Capture()
        {
            var list = new List<object>();
            foreach (var p in _phones)
                list.Add(new Dictionary<string, object>
                {
                    { "place", p.PlaceId }, { "name", p.PlaceName },
                    { "public", p.Public }, { "from", p.OpenFrom }, { "to", p.OpenTo },
                    { "regulars", new List<object>(p.Regulars.ToArray()) },
                });
            return new Dictionary<string, object> { { "phones", list } };
        }

        public void Restore(Dictionary<string, object> data)
        {
            var list = MiniJson.GetList(data, "phones");
            if (list == null) return;
            _phones.Clear();
            foreach (var raw in list)
            {
                var o = MiniJson.AsObject(raw);
                if (o == null) continue;
                var phone = new Phone
                {
                    PlaceId = MiniJson.GetString(o, "place"),
                    PlaceName = MiniJson.GetString(o, "name"),
                    Public = o.TryGetValue("public", out var pv) && pv is bool pb && pb,
                    OpenFrom = MiniJson.GetInt(o, "from"),
                    OpenTo = MiniJson.GetInt(o, "to"),
                };
                foreach (var r in MiniJson.GetList(o, "regulars") ?? new List<object>())
                    if (r is string id) phone.Regulars.Add(id);
                _phones.Add(phone);
            }
        }
    }
}
