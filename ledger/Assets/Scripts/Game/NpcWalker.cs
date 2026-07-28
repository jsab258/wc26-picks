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
            // Was 1.0 — half a capsule. A body's ground contact is its
            // SOLE, and the two numbers are 10cm apart.
            go.transform.position = schedule[0].pos + Vector3.up * Mannequin.SoleBelowOrigin;
            // A BODY, not a capsule. Ten boxes and a sphere articulated by
            // Core/Rig — which will not be mistaken for a person and is
            // unmistakably a person WALKING, and that is the whole difference
            // between a populated street and objects sliding along one.
            //
            // The name colour becomes the clothes; skin is a warm neutral off
            // the same hue, so a crowd is varied without anybody being
            // pillar-box red from the neck up.
            var skin = new Color(Mathf.Lerp(color.r, 0.72f, 0.65f),
                                 Mathf.Lerp(color.g, 0.58f, 0.65f),
                                 Mathf.Lerp(color.b, 0.47f, 0.65f));
            Mannequin.Build(go, skin, color, name);

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

        // ---- M15.2: being perceived ----
        //
        // The stance is computed in Core from state the player could only read
        // in a panel; here it becomes something they can WATCH. A body that
        // turns to follow you across a street says "they have heard about the
        // warehouse" better than any readout, and it says it while you are
        // busy doing something else.
        public StanceKind Stance = StanceKind.Indifferent;
        Transform _player;
        float _nextAvoidStep;

        public void SetPlayer(Transform player) => _player = player;

        /// SOMEBODY WALKED INTO YOU (game-feel-spec.md §5).
        ///
        /// Until now the player passed through a crowd like a ghost, which
        /// quietly tells them none of it is real — the most damaging
        /// impression in the whole document, because it makes the simulation
        /// underneath get disbelieved on the strength of the contact layer.
        ///
        /// A shove is also a FACT in a game about being noticed, so a real
        /// knock buys real attention and the stance system reads it.
        Vector3 _stagger;
        float _staredUntil;

        public void Bumped(Vector3 fromPlayer, float relativeSpeed)
        {
            var kind = Bumps.Classify(relativeSpeed);
            var away = fromPlayer; away.y = 0;
            if (away.sqrMagnitude > 0.001f)
                _stagger = away.normalized * (float)Bumps.Stagger(relativeSpeed);
            _staredUntil = Time.time + (float)Bumps.AttentionSeconds(kind);
            if (Bumps.WorthRemembering(kind)) BumpsWorthRemembering++;
        }

        /// Knocks and shoves only. Read by the sim so "you barge through this
        /// city" is something the world can know about you.
        public int BumpsWorthRemembering { get; private set; }

        CharacterRig _body;
        Vector3 _lastBodyPos;
        double _gaitPhase;

        /// The gait, from distance actually covered rather than from whether
        /// the walk state says "walking". Somebody shoved sideways, steering
        /// round a bin or stopped by a red light all move at speeds their
        /// state machine does not know about, and a stride that ignores that
        /// is the foot-sliding every graybox crowd has.
        void DriveBody()
        {
            if (_body == null)
            {
                _body = CharacterRig.Attach(gameObject);
                _lastBodyPos = transform.position;
                if (_body == null) return;
            }
            float dt = Time.deltaTime;
            if (dt <= 0) return;
            var here = transform.position;
            float moved = Vector3.Distance(new Vector3(here.x, 0, here.z),
                                           new Vector3(_lastBodyPos.x, 0, _lastBodyPos.z));
            _lastBodyPos = here;
            double speed = moved / dt;
            _body.Speed = speed;
            // Cadence rises with speed, so a hurrying person takes faster
            // steps rather than longer ones.
            _gaitPhase = (_gaitPhase + speed * dt * 0.62) % 1.0;
            _body.Phase = _gaitPhase;
        }

        // ---- standing and talking to somebody ----------------------------
        //
        // The game's whole thesis is that the antagonist is gossip, and the
        // street has always shown none of it: rumours pass along the contact
        // graph every tick while a dozen people walk past each other in
        // silence. Now that there are bodies, the exchange can be a thing you
        // WATCH — two strangers stopping, turning in, leaning toward each
        // other. That is the central mechanic taught without a line of UI.
        //
        // Every number comes from Core/Confab, which is where they are
        // tested. This holds the state.
        NpcWalker _talkingTo;
        float _confabUntil, _confabStarted, _confabTotal;
        double _confabDistance = Confab.NearMetres;
        double _confabOffAxis = Confab.OffAxisDegrees;

        public bool InConfab => _talkingTo != null && Time.time < _confabUntil;

        /// Begin one. Called on both halves of a pair, by whoever noticed the
        /// exchange — the walkers do not decide this, the gossip does.
        public void BeginConfab(NpcWalker other, double tie, bool sensitive, bool hostile)
        {
            if (other == null || other == this) return;
            _talkingTo = other;
            _confabTotal = (float)Confab.Seconds(tie, sensitive);
            _confabStarted = Time.time;
            _confabUntil = Time.time + _confabTotal;
            _confabDistance = Confab.Distance(tie, sensitive);
            _confabOffAxis = Confab.OffAxis(hostile);
        }

        /// Where this walker wants to stand and face while talking, or false
        /// if they are not. Returns the target the ordinary steering should
        /// be overridden with.
        bool ConfabTarget(Vector3 current, out Vector3 stand, out Vector3 face)
        {
            stand = current; face = transform.forward;
            if (!InConfab) { _talkingTo = null; return false; }
            var them = _talkingTo.transform.position;
            var toThem = them - current; toThem.y = 0;
            if (toThem.sqrMagnitude < 0.0001f) return false;

            float commitment = (float)Confab.Commitment(Time.time - _confabStarted, _confabTotal);

            // THE LISTENER WALKS OVER, not both. Two people converging on a
            // point neither occupied reads as choreography, because that is
            // something that only happens when somebody arranged it.
            // Somebody with news stands still; somebody who wants it comes.
            var dir = toThem.normalized;
            stand = _approachesInConfab
                ? them - dir * (float)_confabDistance
                : current;
            // Ease in, so the walk over is a walk rather than a snap.
            stand = Vector3.Lerp(current, stand, commitment);

            // Shoulders angled off the line between them, not squared up:
            // face-on is the posture of an argument, and a street staging
            // every conversation that way reads as one about to kick off.
            face = Quaternion.Euler(0, (float)(_confabOffAxis * _offAxisSide), 0) * dir;
            return true;
        }

        bool _approachesInConfab;
        float _offAxisSide = 1f;

        /// Which of the pair goes to the other, and which way each angles
        /// off. Set once when the pair is formed so the two halves cannot
        /// disagree — both leaning the same way puts them shoulder to
        /// shoulder facing a wall.
        public void SetConfabRole(bool approaches, bool leansLeft)
        {
            _approachesInConfab = approaches;
            _offAxisSide = leansLeft ? -1f : 1f;
        }

        public void Tick(GameTime now)
        {
            var target = TargetFor(now);
            var current = transform.position;

            // A conversation outranks a schedule. Somebody who walks off
            // mid-sentence because it is nine o'clock is the exact failure
            // this is meant to fix.
            if (ConfabTarget(current, out var standAt, out var faceDir))
            {
                var step = Vector3.MoveTowards(current, new Vector3(standAt.x, current.y, standAt.z),
                                               MoveSpeed * 0.55f * Time.deltaTime);
                transform.position = step;
                if (faceDir.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation,
                        Quaternion.LookRotation(faceDir), 5f * Time.deltaTime);
                // The head goes to the person they are talking to, which is
                // what the off-axis stance leaves room for: the body is
                // angled and the face is not.
                if (_body != null) _body.LookAt = _talkingTo.transform;
                DriveBody();
                return;
            }

            // The stumble resolves over a moment rather than teleporting them
            // sideways: displacement first, recovery after.
            if (_stagger.sqrMagnitude > 0.0001f)
            {
                var step = Vector3.ClampMagnitude(_stagger, 2.2f * Time.deltaTime);
                transform.position = current + step;
                _stagger -= step;
                current = transform.position;
            }

            // Somebody who wants nothing to do with you puts distance between
            // you — the ladder's "avoids" rung, expressed as walking away
            // rather than as a word in a book.
            if (_player != null && Stance >= StanceKind.Avoids && Stance < StanceKind.Confronts)
            {
                float toPlayer = Vector3.Distance(current, _player.position);
                if (toPlayer < 7f && Time.time > _nextAvoidStep)
                {
                    _nextAvoidStep = Time.time + 2.5f;
                    var away = (current - _player.position); away.y = 0;
                    if (away.sqrMagnitude > 0.01f)
                        target = current + away.normalized * 9f;
                }
            }

            var flatTarget = new Vector3(target.x, current.y, target.z);

            bool moving = (flatTarget - current).sqrMagnitude > 0.04f;
            if (moving)
            {
                var waypoint = Steer(current, flatTarget);
                var next = Vector3.MoveTowards(current, waypoint, MoveSpeed * Time.deltaTime);
                transform.position = next;
                var dir = waypoint - current; dir.y = 0;
                if (dir.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), 8f * Time.deltaTime);
            }

            // GAZE. How far off somebody picks you out is how much they have
            // heard — and standing still to look at you is the cheapest, most
            // legible signal in the game.
            // Just been walked into? Then they are looking at you, whatever
            // their stance would otherwise have them do. Nobody ignores being
            // shoved, and a stance ladder that let them is a ladder the
            // player would immediately catch out.
            // WITH THE HEAD, NOT THE FEET, now that there is a head.
            //
            // Every version of this until now turned the whole body to face
            // you, because a capsule has no other way to look at anything.
            // That reads as squaring up: it is the posture of somebody about
            // to start something, applied to a stranger who has merely
            // clocked you. In a game whose antagonist is gossip that is
            // precisely the wrong signal — being NOTICED and being CONFRONTED
            // are different rungs of the same ladder and were rendering
            // identically.
            //
            // `Rig.LookSplit` distributes the turn down chest, neck and head,
            // and `MustTurnBody` decides when somebody has to come round
            // because their neck cannot get there. So the body turns when a
            // person would actually turn, and otherwise they just look.
            bool wantsToLook = false;
            if (_player != null && Time.time < _staredUntil) wantsToLook = true;
            else if (_player != null && !moving)
            {
                float gaze = (float)StreetVoice.GazeMetres(Stance);
                var toYou = _player.position - current; toYou.y = 0;
                wantsToLook = gaze > 0.5f && toYou.sqrMagnitude > 0.04f
                              && toYou.magnitude <= gaze;
            }

            if (_body != null) _body.LookAt = wantsToLook ? _player : null;

            // The body still comes round for the two cases where a person
            // would: when their neck has run out, and when they are staring
            // at you rather than glancing.
            if (wantsToLook && (_body == null || _body.MustTurn
                                || Time.time < _staredUntil))
            {
                var at = _player.position - transform.position; at.y = 0;
                if (at.sqrMagnitude > 0.01f)
                    transform.rotation = Quaternion.Slerp(transform.rotation,
                        Quaternion.LookRotation(at),
                        (Time.time < _staredUntil ? 9f : 3.5f) * Time.deltaTime);
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

            // Last, and after every branch above that can move them: the
            // stagger, the avoid step and the walk are all displacement this
            // frame, and a gait measured before any of them is a gait that
            // disagrees with where the body went.
            DriveBody();
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
