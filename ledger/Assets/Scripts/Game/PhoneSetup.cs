using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The city's telephone lines (roadmap M10), and the query that makes them
    /// mean anything: is this person actually near that phone right now.
    ///
    /// Core owns the rule that a phone is a place rather than a pocket. This
    /// file owns the two things Core cannot know — WHERE the lines are, and
    /// where everybody is standing.
    ///
    /// Reachability reads live walker positions rather than schedule tables.
    /// The schedules would have been easier and would have lied: a character
    /// pulled out of their routine by the Director, or standing in the bar
    /// because the player walked them there, is exactly the case where "can I
    /// reach them" gets interesting, and a table would have said yes while the
    /// person was two districts away.
    public partial class GameController
    {
        public PhoneBook Phones { get; } = new PhoneBook();

        /// How near a phone somebody has to be to pick it up. Generous: you are
        /// in the room, not on the receiver.
        public const float PhoneReach = 9f;

        readonly Dictionary<string, Vector3> _phoneSpots = new Dictionary<string, Vector3>();

        void BuildPhones()
        {
            // Five lines, and the choice of WHICH five is the design. The bar is
            // yours. The boarding house hall phone is the one where anybody
            // might answer. The letter-writer's stall is across the water in the
            // market quarter — a public line in a place whose whole trade is
            // other people's messages, so reaching it is a fact about the day and
            // whoever takes your words does this for a living. The harbourmaster's
            // is official, keeps office hours, and answering it is somebody's job.
            //
            // AND WHAT ROOM EACH ONE STANDS IN, which is authored here because
            // nothing in the world can derive it. `Acoustics.SpaceFor` maps a
            // position to a space and only ever returns `Outdoors` or `Alley` —
            // it reads the STREET graph, and a telephone is indoors by
            // definition except when it is not. Asking it about the bar would
            // have said "outdoors" and thrown away the whole detail
            // `Audio.OpenLine` exists for: its own comment says "a hall behind
            // Ellis tells you which building he is in and nobody wrote a line
            // of dialogue for it".
            //
            // The stall is the one that is genuinely outdoors, and the boarding
            // houses and the club are halls — a stairwell, a lobby, a room with
            // a ceiling far enough away to ring. That is the same reasoning the
            // paragraph above uses to pick which five lines exist.
            Line("bar", "the bar", 10, 24, new[] { "Lena", "Rocco" });
            Line("boarding_house", "the boarding house", 7, 22, new[] { "Ada", "Sam", "Donna" },
                 isPublic: true, space: SpaceKind.Hall);
            Line("letter_stall", "the letter-writer's stall", 8, 18, new[] { "Tony Brela", "Mitch Sedlak" },
                 space: SpaceKind.Outdoors);
            Line("harbor_office", "the harbourmaster's office", 9, 17, new[] { "Hal" });
            Line("pawnshop", "Rita's pawnshop", 10, 20, new[] { "Rita", "Victor" });
            // M14: the outer districts' lines. The exchange is official and
            // keeps the hours of the place it rings — the Marquee answers at
            // night, the counting house only inside office hours, and the
            // Gullwing boarding house whenever the keeper is awake, which is
            // most hours; an off-season boarding house is mostly waiting.
            Line("counting_house", "the counting house", 9, 17, new[] { "Hal" });
            Line("marquee_club", "the Marquee club", 19, 4, new string[0],
                 isPublic: true, space: SpaceKind.Hall);
            Line("gull_boarding", "the Gullwing boarding house", 7, 23, new string[0],
                 isPublic: true, space: SpaceKind.Hall);

            Debug.Log($"Phones: {Phones.All.Count} lines on the exchange");
        }

        /// What each line's room sounds like, for `Audio.OpenLine`. Kept here
        /// rather than on `Phone` because it is a fact about this city's
        /// geography and `Core.Phone` is the model — the same reason the
        /// physical spot lives in `_phoneSpots` and not on the phone.
        readonly Dictionary<string, SpaceKind> _phoneSpaces = new Dictionary<string, SpaceKind>();

        void Line(string placeId, string name, int from, int to, string[] regulars,
                  bool isPublic = false, SpaceKind space = SpaceKind.Room)
        {
            _phoneSpaces[placeId] = space;
            var phone = new Phone
            {
                PlaceId = placeId, PlaceName = name,
                OpenFrom = from, OpenTo = to, Public = isPublic,
            };
            phone.Regulars.AddRange(regulars);
            Phones.Add(phone);

            // Where the thing physically is, so "near the phone" is a question
            // about the world rather than about a table.
            var place = HookMap.Get(placeId);
            var spot = place != null
                ? new Vector3((float)place.X, 0, (float)place.Z)
                : WorldBuilder.BarDoor;
            _phoneSpots[placeId] = spot;
        }

        /// Is this person within reach of that phone right now?
        ///
        /// Walkers first, because a body in the world is the truth. Falls back
        /// to the crowd's level-of-detail position for anybody who has no body
        /// at the moment — somebody in the mid band still exists and can still
        /// answer a telephone, and a system that said otherwise would make the
        /// city smaller every time the player looked away.
        public bool NearPhone(string personId, string placeId)
        {
            if (!_phoneSpots.TryGetValue(placeId, out var spot)) return false;

            // THE PLAYER IS NOT IN THE WALKER LIST, AND UNTIL NOW THAT MEANT
            // THE ANSWER FOR HIM WAS ALWAYS NO.
            //
            // This walks `_npcs` by display name and then the crowd, and the
            // player is in neither — so `NearPhone("player", …)` returned false
            // for every line at every hour. Harmless while the only caller
            // asked about somebody being RUNG; the moment the rival started
            // telephoning the player, "you were not reachable" became the only
            // outcome the mechanic could ever produce.
            //
            // That is rule 5b's twin: a run in which the thing being asserted
            // CAN happen. `Answered.Took` was unreachable, and the first
            // build's `summonsMissed=1` reads identically whether the player
            // was out on the street or whether picking up is impossible.
            //
            // Found by reading the lookup rather than by trusting the number,
            // which is the only way this surfaces — a mechanic that always
            // takes one branch looks exactly like a mechanic whose condition
            // never held.
            if (personId == "player")
                return _player != null
                       && Vector3.Distance(_player.transform.position, spot) <= PhoneReach;

            foreach (var npc in _npcs)
            {
                if (npc == null || npc.DisplayName != personId) continue;
                return Vector3.Distance(npc.transform.position, spot) <= PhoneReach;
            }

            var crowd = CrowdPositionOf(personId);
            if (crowd.HasValue) return Vector3.Distance(crowd.Value, spot) <= PhoneReach;
            return false;
        }

        /// Ring a line. Everything the player needs to know comes back in the
        /// Call; nothing about it is decided here.
        public Call RingLine(string placeId, string wantedId)
        {
            var mill = _gossip != null ? _gossip.Mill : null;
            // AND WHETHER THE PLAYER CAN PLACE THE VOICE.
            //
            // `familiarityOf` reuses `Acquaintance` rather than inventing a
            // second scale — the same ladder that decides whether somebody can
            // name the player in the street decides whether the player can name
            // them down a wire, read from the other end. Two scales for one
            // idea is how the wardrobe and the poach path each grew a second
            // implementation that quietly disagreed with the first.
            //
            // Every phone here is a `Handset` for now; the callbox and the bad
            // line are what `Phone` will carry when there is a callbox in the
            // world to stand at.
            return Phones.Ring(placeId, wantedId, Now, NearPhone,
                id => mill?.Get(id)?.DisplayName ?? id,
                id =>
                {
                    var g = mill?.Get(id);
                    if (g == null) return Acquaintance.Stranger;
                    return Acquaintance.Of(false, false, true, true);
                },
                Acoustics.LineKind.Handset);
        }

        /// Is the PLAYER standing next to this line? Distinct from NearPhone,
        /// which asks about a cast member — the player has no gossiper id and
        /// answers to a position rather than to a name.
        public bool PhoneNear(string placeId, Vector3 where) =>
            _phoneSpots.TryGetValue(placeId, out var spot)
            && Vector3.Distance(where, spot) <= PhoneReach;

        /// They picked up. Open the conversation, and tell the engine that this
        /// one is happening down a wire: a voice on a line is not a face across
        /// a table, so what either party can read in the other is damped.
        public void BeginPhoneConversation(string whoId)
        {
            var host = HostFor(whoId);
            if (host == null) return;
            host.OnTheLine = true;
            // AND IT SOUNDS LIKE A WIRE, WHICH IT NEVER HAS.
            //
            // `Audio.OpenLine` builds the hiss, the caller's room arriving as
            // a dulled wash, and the mains hum induced in the earpiece — and
            // had no caller. `ConversationHost` already puts the wire into the
            // TEXT through `AsHeardOnTheLine`; the sound was the other half of
            // one idea and it was the half nobody looked at. Until now a voice
            // on the telephone was sample-identical to the same voice standing
            // in the room, which `Acoustics` calls throwing away the mechanic's
            // entire identity.
            //
            // `Handset` matches what `BuildPhones` gives `PhoneBook`, so the
            // acoustic and the social model are reading the same line kind
            // rather than two constants that happen to agree today.
            Audio.OpenLine(Acoustics.LineKind.Handset, SpaceOfPhoneNear(whoId));
            _ui?.OpenConversation(host);
        }

        /// The room the OTHER person is standing in — whichever line they are
        /// within reach of. Falls back to `Room`, which is what an unknown
        /// interior sounds like and is the same default `Audio.OpenLine` takes.
        SpaceKind SpaceOfPhoneNear(string whoId)
        {
            foreach (var p in Phones.All)
                if (NearPhone(whoId, p.PlaceId)
                    && _phoneSpaces.TryGetValue(p.PlaceId, out var s)) return s;
            return SpaceKind.Room;
        }

        /// Leave word with whoever answered.
        public bool LeavePhoneMessage(Call call, string summary) =>
            Phones.LeaveMessage(call, _gossip != null ? _gossip.Mill : null, "player", summary, Now);

        /// Who could the player plausibly ring right now, and about whom. Used
        /// by the F1 readout and, next, by the panel the player rings from.
        public string PhoneStatusLine()
        {
            var sb = new System.Text.StringBuilder();
            sb.Append("-- the exchange --\n");
            foreach (var p in Phones.All)
            {
                sb.Append($"  {p.PlaceName}: {(p.LiveAt(Now.Hour) ? "open" : "closed at this hour")}");
                var here = new List<string>();
                foreach (var who in p.Regulars)
                    if (NearPhone(who, p.PlaceId)) here.Add(who);
                sb.Append(here.Count > 0 ? $" — {string.Join(", ", here)} in reach\n" : " — nobody by it\n");
            }
            return sb.ToString();
        }
    }
}
