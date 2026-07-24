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

        /// Where the schedule says this NPC should be at the given time.
        Vector3 TargetFor(GameTime now)
        {
            int minute = now.Hour * 60 + now.Minute;
            Vector3 target = _schedule[_schedule.Count - 1].Position; // before first entry: last night's spot
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
                var next = Vector3.MoveTowards(current, flatTarget, MoveSpeed * Time.deltaTime);
                transform.position = next;
                var dir = flatTarget - current; dir.y = 0;
                if (dir.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), 8f * Time.deltaTime);
            }

            if (_label != null && Camera.main != null)
                _label.transform.rotation = Quaternion.LookRotation(_label.transform.position - Camera.main.transform.position);
        }
    }
}
