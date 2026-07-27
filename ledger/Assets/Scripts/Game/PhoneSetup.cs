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
            // might answer. The foundry office is across the water, so reaching
            // it at all is a fact about the day. The harbourmaster's is
            // official, keeps office hours, and answering it is somebody's job.
            Line("bar", "the bar", 10, 24, new[] { "Lena", "Rocco" });
            Line("boarding_house", "the boarding house", 7, 22, new[] { "Ada", "Sam", "Danica" }, isPublic: true);
            Line("foundry_office", "the foundry office", 8, 18, new[] { "Anton Brela", "Mirek Sedlak" });
            Line("harbor_office", "the harbourmaster's office", 9, 17, new[] { "Halvard" });
            Line("pawnshop", "Ruta's pawnshop", 10, 20, new[] { "Ruta", "Viktor" });

            Debug.Log($"Phones: {Phones.All.Count} lines on the exchange");
        }

        void Line(string placeId, string name, int from, int to, string[] regulars, bool isPublic = false)
        {
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
            return Phones.Ring(placeId, wantedId, Now, NearPhone,
                id => mill?.Get(id)?.DisplayName ?? id);
        }

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
