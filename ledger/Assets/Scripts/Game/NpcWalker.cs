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
            npc._label.characterSize = 0.12f;
            npc._label.fontSize = 32;
            npc._label.anchor = TextAnchor.MiddleCenter;
            npc._label.color = Color.white;

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

            if (_label != null && Camera.main != null)
                _label.transform.rotation = Quaternion.LookRotation(_label.transform.position - Camera.main.transform.position);
        }

        /// Street-wise steering: walk straight when the line is clear of building
        /// masses, otherwise follow the street cross (nearest arm, corner at the
        /// intersection). Stateless and re-evaluated every tick, so a schedule
        /// change mid-walk just bends the route. Replaces the old straight-line
        /// move that let characters pass through buildings.
        Vector3 Steer(Vector3 cur, Vector3 target)
        {
            if (WorldBuilder.SegmentClear(cur, target)) return target;
            var targetArm = NearestOnCross(target);
            if (WorldBuilder.SegmentClear(cur, targetArm)) return targetArm;
            var myArm = NearestOnCross(cur);
            if ((myArm - cur).sqrMagnitude > 0.04f && WorldBuilder.SegmentClear(cur, myArm)) return myArm;
            return new Vector3(0, cur.y, 0); // toward the intersection until a turn opens
        }

        /// Closest point on the two street centerlines (x = 0 or z = 0).
        static Vector3 NearestOnCross(Vector3 p)
        {
            var ns = new Vector3(0, p.y, p.z);
            var ew = new Vector3(p.x, p.y, 0);
            return (ns - p).sqrMagnitude <= (ew - p).sqrMagnitude ? ns : ew;
        }
    }
}
