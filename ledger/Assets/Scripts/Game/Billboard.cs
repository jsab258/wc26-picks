using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// EVERYTHING THAT TURNS TO FACE THE CAMERA, aimed from one place.
    ///
    /// FOUND IN `review_day5_night.jpg`. Two rumour lines are printed across the
    /// frame BACKWARDS — "maybe the new owner ... handli" reading right to left,
    /// mirrored, at a diagonal — while the nameplates a few metres away read
    /// correctly. Every number that could have caught it was green in the same
    /// run: `textMirrored=0`, `speechUpDot=1.000`, `nameTagsUpDot=1.000`.
    ///
    /// THE CAUSE IS ORDERING, not maths. `SpeechBubble` aims itself in
    /// `LateUpdate` and `NpcWalker` aims its label from `Tick` — and
    /// `SimDirector.Shot` renders from `Update`, calling `cam.Render()` by hand
    /// into a RenderTexture. So the frame that gets committed is drawn with
    /// every billboard still pointing at the camera's pose from the PREVIOUS
    /// frame. The sim runs at `meanFrame=334ms`, so "the previous frame" is a
    /// third of a second of camera movement; on a bubble two metres from the
    /// lens that is easily enough to swing past it, and the built-in text shader
    /// is `Cull Off`, so the back face draws rather than disappearing.
    ///
    /// WHY THE NUMBERS ALL AGREED. Both up-dots are sampled inside the same
    /// `LateUpdate` that does the aiming — one line apart from it — so they
    /// report the orientation the code just set, which is never the orientation
    /// the picture was taken at. `textMirrored` ran once, at the audit moment,
    /// against `Camera.main`, and the audit moment is not a shot moment either.
    /// Three instruments, one blind spot, and the blind spot is the only instant
    /// anybody ever looks at. Same shape as `bubblesOnScreen=0` beside a still
    /// with two bubbles in it, fixed the same night.
    ///
    /// SO THE AIM MOVED HERE AND THE SHOT CALLS IT. `Shot` re-aims everything at
    /// the camera it is about to render from, immediately before rendering, and
    /// reports how far out they were beforehand — because a fix nobody measured
    /// is a fix nobody can tell decayed.
    ///
    /// AND IT IS ONE IMPLEMENTATION NOW. The yaw-only aim was written twice,
    /// with a paragraph in each explaining the degenerate-basis trap; `NpcWalker`
    /// got the fix first and `SpeechBubble` carried the bug for months with a
    /// comment admitting nobody had grepped for the second site. A third copy
    /// for the shot path would have been the same mistake a third time.
    public static class Billboard
    {
        // Transforms, not components: a nameplate is a `TextMesh` and a bubble is
        // a `SpeechBubble`, and the only thing this needs from either is where it
        // is and which way it points.
        static readonly List<Transform> _facing = new List<Transform>();

        /// How many billboards are being tracked. Reported so that "nothing was
        /// mis-aimed" and "nothing was registered" cannot read the same — the
        /// distinction rule 6 exists for.
        public static int Tracked => _facing.Count;

        public static void Register(Transform t)
        {
            if (t == null || _facing.Contains(t)) return;
            _facing.Add(t);
        }

        public static void Forget(Transform t)
        {
            if (t != null) _facing.Remove(t);
        }

        // NO `ResetAll`, DELIBERATELY. `WorldText` has a `ResetCounters` for
        // "the sim runs several worlds in one process" and nothing has ever
        // called it — a public API with no call site, which is the exact fault
        // rule 6 is about. The sweep for destroyed transforms in `AimAll` and
        // `Misaimed` already empties this list when a world goes away, so a
        // second mechanism would be an unreachable one.

        /// YAW ONLY. One-argument `LookRotation` takes world up as its hint, so a
        /// near-vertical forward gives a degenerate basis — and the review camera
        /// looks DOWN at the street, which is exactly that case. The first stills
        /// this project ever committed had names lying in the road, stretched
        /// across the pavement in perspective, for this reason. Flattening the
        /// direction to the horizontal plane removes the degeneracy instead of
        /// working around it.
        ///
        /// Returns false when the camera is directly overhead and there is no
        /// horizontal direction to use — the caller keeps the previous rotation,
        /// which is better than snapping to an arbitrary one.
        public static bool Aim(Transform t, Camera cam)
        {
            if (t == null || cam == null) return false;
            var to = t.position - cam.transform.position;
            to.y = 0f;
            if (to.sqrMagnitude <= 1e-6f) return false;
            t.rotation = Quaternion.LookRotation(to);
            return true;
        }

        /// Point everything at this camera, now. Returns how many were aimed.
        public static int AimAll(Camera cam)
        {
            int aimed = 0;
            for (int i = _facing.Count - 1; i >= 0; i--)
            {
                var t = _facing[i];
                // A destroyed Unity object compares equal to null, and a list of
                // them would otherwise grow for the life of the process — every
                // bubble ever spoken.
                if (t == null) { _facing.RemoveAt(i); continue; }
                if (Aim(t, cam)) aimed++;
            }
            return aimed;
        }

        /// How many tracked billboards are pointing more than `degrees` away from
        /// where this camera would want them.
        ///
        /// MEASURED BEFORE THE AIM, AT SHOT TIME. That ordering is the whole
        /// point: after `AimAll` this is zero by construction and would be a gate
        /// certifying itself. Before it, it is the size of the fault in the frame
        /// about to be committed, which is the quantity that was missing.
        ///
        /// Inactive labels are skipped — `NpcWalker` switches a nameplate off
        /// across the road, and something not drawn cannot be drawn backwards.
        public static int Misaimed(Camera cam, float degrees)
        {
            if (cam == null) return 0;
            int bad = 0;
            float cos = Mathf.Cos(degrees * Mathf.Deg2Rad);
            for (int i = _facing.Count - 1; i >= 0; i--)
            {
                var t = _facing[i];
                if (t == null) { _facing.RemoveAt(i); continue; }
                if (!t.gameObject.activeInHierarchy) continue;
                var to = t.position - cam.transform.position;
                to.y = 0f;
                if (to.sqrMagnitude <= 1e-6f) continue;
                if (Vector3.Dot(t.forward, to.normalized) < cos) bad++;
            }
            return bad;
        }

        /// The worst single misalignment in degrees, so the count has a size
        /// beside it. A hundred labels a degree out and one printed backwards are
        /// the same number under `Misaimed` and are not the same problem.
        public static float WorstDegrees(Camera cam)
        {
            if (cam == null) return 0f;
            float worst = 0f;
            for (int i = _facing.Count - 1; i >= 0; i--)
            {
                var t = _facing[i];
                if (t == null) { _facing.RemoveAt(i); continue; }
                if (!t.gameObject.activeInHierarchy) continue;
                var to = t.position - cam.transform.position;
                to.y = 0f;
                if (to.sqrMagnitude <= 1e-6f) continue;
                float d = Vector3.Angle(t.forward, to.normalized);
                if (d > worst) worst = d;
            }
            return worst;
        }
    }
}
