using System.Collections.Generic;
using System.Linq;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The game-side half of access (roadmap M7.5). Walk up to a gated place
    /// and somebody either steps aside or does not, in their own words.
    ///
    /// The whole design lives in one rule: A REFUSAL MUST TEACH. Being told no
    /// is only interesting if you leave knowing what would have worked, so the
    /// game always follows the doorman's line with the near miss — the way in
    /// you came closest to having, with the figure. A door you cannot open and
    /// cannot learn about is level geometry.
    ///
    /// It is deliberately quiet about repeating itself. You hear a gate's line
    /// once per approach and once per day, because a doorman who says the same
    /// sentence every time you walk past is scenery, not a person.
    public partial class GameController
    {
        public List<Gate> Gates { get; } = AccessSetup.Build();

        const float GateNear = 3.0f, GateFar = 5.0f;
        readonly HashSet<string> _atGate = new HashSet<string>();
        readonly Dictionary<string, int> _gateSpokeDay = new Dictionary<string, int>();

        /// Whether the player has been let into a place. Read by anything that
        /// wants to know where they have actually been, and persisted.
        public readonly HashSet<string> PlacesEntered = new HashSet<string>();

        AccessState BuildAccessState(Gate gate)
        {
            var s = new AccessState
            {
                Notoriety = CurrentHeat,
                Dress = WearingCoat ? "coat" : "plain",
                Money = Wallet.Total,
                Hour = Now.Hour,
                Crew = Empire.ActiveCrew.Count(),
            };
            foreach (var arm in Empire.Arms) s.Standing[arm.Id] = arm.Standing;

            // An introduction is somebody who thinks well enough of you to say
            // your name in a room you are not in yet. Loyalty is that number.
            var mill = _gossip != null ? _gossip.Mill : null;
            if (mill != null)
                foreach (var g in mill.Agents)
                    if (g.Loyalty >= 0.65) s.Introductions.Add(g.DisplayName);

            // Leverage counts only if it is on the person actually standing here.
            if (gate != null && gate.Doorman != null)
                s.HoldsHookOnDoor = HooksBook.UsableHook(gate.Doorman) != null;

            return s;
        }

        void CheckGates()
        {
            if (_player == null || _ui == null || SimMode.Days > 0) return;
            var p = _player.transform.position;

            foreach (var gate in Gates)
            {
                var place = HookMap.Get(gate.Id);
                if (place == null) continue;
                float dx = (float)place.X - p.x, dz = (float)place.Z - p.z;
                float d = Mathf.Sqrt(dx * dx + dz * dz);

                if (_atGate.Contains(gate.Id))
                {
                    if (d >= GateFar) _atGate.Remove(gate.Id);
                    continue;
                }
                if (d > GateNear) continue;
                _atGate.Add(gate.Id);

                // Once a day per gate. A doorman who says the same sentence
                // every time you pass is scenery, not a person.
                if (_gateSpokeDay.TryGetValue(gate.Id, out var day) && day == Now.Day) continue;
                _gateSpokeDay[gate.Id] = Now.Day;

                var result = Doors.Try(gate, BuildAccessState(gate));
                if (result.Allowed)
                {
                    if (result.Paid > 0) Wallet.Spend(result.Paid, dirtyOk: true);
                    PlacesEntered.Add(gate.Id);
                    _ui.Toast(result.Line, 8f);
                    Audio.Ui(result.Paid > 0 ? "coin" : "door");
                }
                else
                {
                    // The line, then what would have worked — in ONE toast,
                    // stacked, because there is a single toast slot and the
                    // second call overwrites the first in the same frame: all
                    // four authored refusal lines were displaying for exactly
                    // zero frames (audit 2026-07-27). The pairing IS the
                    // feature, so it ships as a pair.
                    _ui.Toast(string.IsNullOrEmpty(result.Hint)
                        ? result.Line
                        : result.Line + "\n" + result.Hint, 10f);
                    Audio.Ui("page");
                }
            }
        }

        /// What the ledger panel shows about doors: only what the player has
        /// actually learned by being turned away, never the full key list.
        /// Knowing every way into every room without having tried is the same
        /// omniscience §6.2 spent the whole project refusing.
        public string GatesLine()
        {
            var seen = Gates.Where(g => _gateSpokeDay.ContainsKey(g.Id)).ToList();
            if (seen.Count == 0) return null;
            var sb = new System.Text.StringBuilder();
            foreach (var g in seen)
                sb.AppendLine(PlacesEntered.Contains(g.Id)
                    ? $"<b>{g.Name}</b> — you have been inside"
                    : $"<b>{g.Name}</b> — you have been turned away");
            return sb.ToString();
        }

        Dictionary<string, object> CaptureAccess() => new Dictionary<string, object>
        {
            { "entered", PlacesEntered.Cast<object>().ToList() },
        };

        void RestoreAccess(Dictionary<string, object> data)
        {
            if (data == null) return;
            PlacesEntered.Clear();
            var list = MiniJson.GetList(data, "entered");
            if (list == null) return;
            foreach (var id in list.OfType<string>()) PlacesEntered.Add(id);
        }
    }
}
