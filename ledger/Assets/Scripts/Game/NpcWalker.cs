using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Schedule-driven background character: walks toward wherever their daily
    /// schedule says they should be right now. The sim heart of "the city has
    /// routines you can learn".
    public class NpcWalker : MonoBehaviour
    {
        const float MoveSpeed = 2.6f;

        struct Entry { public int MinuteOfDay; public Vector3 Position; }

        readonly List<Entry> _schedule = new List<Entry>();
        TextMesh _label;
        /// Fully legible this close; gone by the far one. Recognition, not HUD.
        const float LabelFullAt = 4f;
        const float LabelFadeOut = 11f;

        public string DisplayName { get; private set; }

        public static NpcWalker Spawn(string name, Color color, (GameTime at, Vector3 pos)[] schedule)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            go.name = $"NPC_{name}";
            go.transform.position = schedule[0].pos + Vector3.up * 1.0f;
            go.GetComponent<Renderer>().material.color = color;

            var npc = go.AddComponent<NpcWalker>();
            npc.DisplayName = name;
            foreach (var (at, pos) in schedule)
                npc._schedule.Add(new Entry { MinuteOfDay = at.Hour * 60 + at.Minute, Position = pos });

            // Floating name label (billboarded toward the camera each frame).
            var labelGo = new GameObject("Label");
            labelGo.transform.SetParent(go.transform, false);
            labelGo.transform.localPosition = new Vector3(0, 1.4f, 0);
            npc._label = labelGo.AddComponent<TextMesh>();
            npc._label.text = name;
            npc._label.characterSize = 0.055f;   // was 0.12: legible, not a banner
            npc._label.fontSize = 48;
            npc._label.anchor = TextAnchor.MiddleCenter;
            npc._label.color = new Color(1f, 1f, 1f, 0f);   // fades in on approach
            labelGo.SetActive(false);

            return npc;
        }

        // A temporary detour from the ordinary routine (roadmap M8). The
        // Director schedules people into unusual places; a routine you can learn
        // is only interesting if it can also be broken for a reason.
        Vector3 _detour;
        int _detourFromDay = -1, _detourToDay = -1, _detourFromHour, _detourToHour;

        /// Puts this character somewhere they would not normally be, between two
        /// hours, for a run of days. Replaces any detour already set — one reason
        /// to be out of place at a time.
        public void SetDetour(Vector3 where, int fromDay, int days, int fromHour, int toHour)
        {
            _detour = where;
            _detourFromDay = fromDay;
            _detourToDay = fromDay + Mathf.Max(0, days - 1);
            _detourFromHour = Mathf.Clamp(fromHour, 0, 23);
            _detourToHour = Mathf.Clamp(toHour, _detourFromHour + 1, 24);
        }

        public void ClearDetour() => _detourFromDay = _detourToDay = -1;

        public bool OnDetour(GameTime now) =>
            _detourFromDay >= 0 && now.Day >= _detourFromDay && now.Day <= _detourToDay
            && now.Hour >= _detourFromHour && now.Hour < _detourToHour;

        /// Where the schedule says this NPC should be at the given time — unless
        /// something has taken them out of their routine.
        Vector3 TargetFor(GameTime now)
        {
            if (OnDetour(now)) return _detour;
            int minute = now.Hour * 60 + now.Minute;
            Vector3 target = _schedule[_schedule.Count - 1].Position; // before first entry: last night's spot
            foreach (var e in _schedule)
                if (minute >= e.MinuteOfDay) target = e.Position;
            return target;
        }

        /// Where this character's routine would put them at a given time,
        /// ignoring any detour — so a meeting can be arranged AT somebody rather
        /// than at a coordinate nobody visits.
        public Vector3 RoutinePosition(GameTime now)
        {
            int minute = now.Hour * 60 + now.Minute;
            Vector3 target = _schedule[_schedule.Count - 1].Position;
            foreach (var e in _schedule)
                if (minute >= e.MinuteOfDay) target = e.Position;
            return target;
        }

        public void Tick(GameTime now)
        {
            var target = TargetFor(now);
            var current = transform.position;
            var flatTarget = new Vector3(target.x, current.y, target.z);

            if ((flatTarget - current).sqrMagnitude > 0.04f)
            {
                var waypoint = Steer(current, flatTarget);
                var next = Vector3.MoveTowards(current, waypoint, MoveSpeed * Time.deltaTime);
                transform.position = next;
                var dir = waypoint - current; dir.y = 0;
                if (dir.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), 8f * Time.deltaTime);
            }

            // A NAME IS NOT A NAMEPLATE. Every walker used to carry its name in
            // white, at full size, at every distance — which is why a street of
            // a dozen people read as a wall of text (playtest 2026-07-28). A
            // name now behaves like recognition does: it resolves as you get
            // close enough to speak to somebody, and it is not there at all
            // across the road.
            if (_label != null && Camera.main != null)
            {
                var cam = Camera.main.transform.position;
                float d = Vector3.Distance(transform.position, cam);
                float alpha = Mathf.Clamp01((LabelFadeOut - d) / (LabelFadeOut - LabelFullAt));
                if (alpha <= 0.01f)
                {
                    if (_label.gameObject.activeSelf) _label.gameObject.SetActive(false);
                }
                else
                {
                    if (!_label.gameObject.activeSelf) _label.gameObject.SetActive(true);
                    var c = _label.color; c.a = alpha; _label.color = c;
                    _label.transform.rotation = Quaternion.LookRotation(_label.transform.position - cam);
                }
            }
        }

        /// Street-wise steering. Walk straight when the line is clear of
        /// buildings; otherwise get to the nearest STREET and follow it.
        ///
        /// This used to fall back to "the nearest point on the founding cross",
        /// which was true when the city had two roads and became nonsense the
        /// moment it had forty. It now uses the real network, so people walk
        /// down streets to get places instead of cutting diagonally across the
        /// blocks between them — which is most of what makes a crowd read as a
        /// crowd rather than as particles.
        ///
        /// Stateless and re-evaluated every tick, so a schedule change mid-walk
        /// just bends the route, and the accelerated CI sim stays deterministic.
        Vector3 Steer(Vector3 cur, Vector3 target)
        {
            if (WorldBuilder.SegmentClear(cur, target)) return target;

            // Aim for the street outside the destination first.
            var targetStreet = NearestStreetPoint(target);
            if (WorldBuilder.SegmentClear(cur, targetStreet)) return targetStreet;

            // Otherwise get onto our own street and follow it round.
            var myStreet = NearestStreetPoint(cur);
            if ((myStreet - cur).sqrMagnitude > 0.04f && WorldBuilder.SegmentClear(cur, myStreet))
                return myStreet;

            // Last resort: the nearest junction, which is always on tarmac and
            // always connected to everywhere else.
            var j = Ledger.Core.StreetMap.NearestNode(cur.x, cur.z, junctionsOnly: true);
            return j != null ? new Vector3((float)j.X, cur.y, (float)j.Z) : new Vector3(0, cur.y, 0);
        }

        /// Closest point on any street, pulled a little toward the pavement so
        /// people walk beside the traffic rather than down the middle of it.
        static Vector3 NearestStreetPoint(Vector3 p)
        {
            if (!Ledger.Core.StreetMap.NearestOnStreet(p.x, p.z, out var sx, out var sz, out var edge))
                return p;
            var onRoad = new Vector3((float)sx, p.y, (float)sz);
            var toWalker = new Vector3(p.x - onRoad.x, 0, p.z - onRoad.z);
            float pavement = (float)edge.Width / 2f + 1.1f;
            return toWalker.sqrMagnitude < 0.01f
                ? onRoad
                : onRoad + toWalker.normalized * pavement;
        }
    }
}
