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

        // ---- perception (spec §17.1: ~6Hz, staggered, Near band only) ----
        Perception.Attention _attention;
        float _nextPerceptionAt;
        float _lastPerceptionAt;
        float _stationaryFor;
        bool _attendingNow;
        /// Set once per walker so the whole crowd does not evaluate on the
        /// same frame. Without it the cost is a spike every sixth of a second
        /// rather than a flat line, which is the same amount of work and a
        /// much worse frame time.
        float _phase = -1f;

        /// Returns whether this walker's attention is currently on the player.
        ///
        /// Every accrual is multiplied by the real elapsed time rather than
        /// counted per evaluation, because this runs at 6Hz and the notice
        /// threshold is in seconds. Counting ticks would make being spotted
        /// depend on the tick rate — the FrameRate bug, one system over.
        bool TickPerception(Vector3 current)
        {
            if (_phase < 0f) _phase = Random.value / Perceivers.VisionHz;
            if (Time.time < _nextPerceptionAt) return _attendingNow;
            float dt = _lastPerceptionAt <= 0 ? 1f / Perceivers.VisionHz
                                              : Time.time - _lastPerceptionAt;
            _lastPerceptionAt = Time.time;
            _nextPerceptionAt = Time.time + 1f / Perceivers.VisionHz + _phase * 0.1f;

            var to = _player.position - current; to.y = 0;
            float metres = to.magnitude;
            if (metres > Perceivers.NearBandMetres)
            {
                _attention.Tick(dt, false, 0, 0, 0);
                return _attendingNow = false;
            }

            double light = Perceivers.LevelAt(_player.position);
            double offAxis = Perceivers.OffAxis(transform, _player.position);
            float speed = PlayerController.CurrentSpeed;

            // Cone, range and light first; the ray only if all three pass.
            bool inSight = Perception.InSight(metres, offAxis, light,
                                              occluded: false, subjectSpeed: speed);
            if (inSight && Perceivers.Occluded(current, _player.position)) inSight = false;

            HearLastSound(current, dt);

            _stationaryFor = speed < 0.1f ? _stationaryFor + dt : 0f;
            var notable = Notice.What(_stationaryFor, speed, GameController.NightAmount,
                                      whereTheyShouldNotBe: false,
                                      bloodVisible: false, weaponVisible: false);
            // A noteworthy person is noticed FASTER through the same
            // accumulator rather than through a second code path.
            double pull = 1.0 + Notice.Interest(notable, GameController.NightAmount);

            int rung = Perception.IdRung(metres, light, familiarity: 0.5,
                                         hasDistinguishingMark: false);
            bool wasAttending = _attendingNow;
            _attention.Tick(dt, inSight, Perception.ConeWeight(offAxis),
                            Perception.MotionFactor(speed) * pull, rung);
            _attendingNow = _attention.Noticed;

            // MUTUAL AWARENESS. Costs one predicate on top of a record that
            // already exists, and it is the difference between a witness you
            // know about and one you do not — which §4.4 calls the quiet horror
            // case and deliberately gives the player nothing for.
            Standoff.Consider(DisplayName, _attendingNow,
                              Standoff.PlayerCanRead(_player, transform, Perceivers.LevelAt(current)));

            if (_attendingNow && !wasAttending)
            {
                Perceivers.Looks++;
                if (notable == Notable.Loitering) Perceivers.LoiterNotices++;
                if (notable == Notable.RunningAtNight) Perceivers.NightRunNotices++;
                if (Notice.WorthRemarking(notable, Nerve, GameController.NightAmount))
                    Perceivers.Remarks++;
            }
            return _attendingNow;
        }

        Vector3 _investigateAt;
        float _investigateUntil = -1f;
        float _lastSoundHeardAt = -999f;
        /// Rises when something is heard and decays, which is what makes an
        /// already-nervous person hear more — `Perception.EffectiveFloor`
        /// takes it and drops their floor. Escalation with no state machine.
        float _alertness;

        public bool Investigating => _investigateUntil > Time.time;

        /// Did this walker hear the last thing that happened, and does it care?
        ///
        /// Called on the vision tick rather than on a timer of its own, so
        /// hearing genuinely costs nothing until something makes a sound.
        void HearLastSound(Vector3 current, double dt)
        {
            _alertness = Mathf.Max(0f, _alertness - (float)dt * 0.08f);
            if (!Perceivers.SoundIsFresh || Perceivers.LastSoundTime <= _lastSoundHeardAt) return;

            float metres = Vector3.Distance(current, Perceivers.LastSoundAt);
            double floor = Perceivers.AmbientFloorAt(current, Perceivers.PresentNearby);
            bool occluded = Perceivers.Occluded(current, Perceivers.LastSoundAt);
            if (!Perception.Heard(metres, Perceivers.LastSoundLoudness, floor, occluded, _alertness))
                return;

            _lastSoundHeardAt = Perceivers.LastSoundTime;
            _alertness = Mathf.Min(1f, _alertness + 0.35f);

            // What they DO about it is the reaction ladder's decision, not
            // this file's. Hearing something is not the same as caring, and a
            // timid person walking toward a gunshot would be wrong.
            double severity = Feel.Clamp01(Perceivers.LastSoundLoudness / 100.0);
            var what = Reaction.Decide(severity, Nerve, dutiful: 0.4,
                                       willingness: 0.7, sawABody: false,
                                       alreadyAlarmed: false);
            if (what == Reacted.Investigate)
            {
                _investigateAt = Perceivers.LastSoundAt;
                _investigateUntil = Time.time + 8f;
                Perceivers.NoiseInvestigations++;
            }
            else if (what == Reacted.Alarm)
            {
                // An alarm is a shout, so it makes the same kind of event it
                // came from. Panic propagates through the hearing model rather
                // than through a system built for it.
                Perceivers.Emit(current, Reaction.LoudnessOf(Reacted.Alarm), "alarm");
            }
        }

        /// Whether this walker's attention is currently on the player. Read by
        /// the hush, which needs a count of attending people per frame and
        /// must not re-run anybody's perception to get it.
        public bool AttendingPlayer => _attendingNow;

        /// Nerve, for whether they say something rather than only look. The
        /// crowd's walkers do not all have a `Gossiper` behind them, so this
        /// defaults to the middle of the range rather than pretending.
        public float Nerve = 0.5f;

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

        /// Set by GameController while this walker is the host of an open
        /// beat. Cleared the moment the window closes, so a host who was
        /// stood up goes back to their evening.
        public bool WaitingAsHost { get; set; }

        /// Begin one. Called on both halves of a pair, by whoever noticed the
        /// exchange — the walkers do not decide this, the gossip does.
        /// `aboutPlayer` is a parameter rather than a property set beforehand
        /// because it is the one input that decides whether this pair breaks
        /// off when he walks up, and a flag the caller can forget to set is a
        /// feature that silently never fires.
        public void BeginConfab(NpcWalker other, double tie, bool sensitive, bool hostile,
                                bool aboutPlayer)
        {
            if (other == null || other == this) return;
            if (Time.time < _confabBlockedUntil) return;
            _talkingTo = other;
            _confabTie = tie;
            _confabAboutPlayer = aboutPlayer;
            _confabTotal = (float)Confab.Seconds(tie, sensitive);
            _confabStarted = Time.time;
            _confabUntil = Time.time + _confabTotal;
            _confabDistance = Confab.Distance(tie, sensitive);
            _confabOffAxis = Confab.OffAxis(hostile);
            _hushing = false;
        }

        bool _confabAboutPlayer;
        double _confabTie;
        bool _hushing;
        float _confabBlockedUntil;

        /// THE MOMENT THE WHOLE THING IS FOR. A pair who break off as he
        /// walks up have told him they were talking about him, that they know
        /// he can see them, and that they would rather he had not heard —
        /// which no interface could say, and two people stopping does.
        /// Counted for the sim gate, and counted in PAIRS of numbers because
        /// the claim is conditional. "Some pairs hushed" is not the design —
        /// the design is that a pair discussing the fish price keeps talking
        /// while he walks straight through them, which is exactly what makes
        /// the ones who DON'T mean something. A run where every pair hushed
        /// is a proximity trigger, and a proximity trigger is what this is
        /// not; both failures need a number to be visible.
        public static int HushWalkBys { get; private set; }
        public static int Hushes { get; private set; }

        void CheckHush()
        {
            if (_hushing || _talkingTo == null || _player == null) return;
            float d = Vector3.Distance(transform.position, _player.position);
            if (d <= (float)Confab.HushRadiusMetres) HushWalkBys++;
            if (!Confab.ShouldHush(_confabAboutPlayer, d, _confabTie)) return;
            _hushing = true;
            Hushes++;
            // They finish the word. A pair that cuts out the frame he crosses
            // a line is a trigger, and a trigger is what this is not.
            _confabUntil = Mathf.Min(_confabUntil, Time.time + (float)Confab.HushSeconds);
            _confabTotal = Mathf.Max(0.01f, _confabUntil - _confabStarted);
            // And they do not pick it back up when he leaves. Somebody caught
            // talking about you moves off, and the street is quieter behind
            // you.
            _confabBlockedUntil = Time.time + (float)Confab.HushCooldownSeconds;
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

            // A HOST WAITS. Ada's invitation says "I'll wait up"; Rocco says
            // "my front step". They then walked their patrol route all
            // evening, and the player — who moves at about the same speed —
            // spent ninety in-game minutes in a tail chase that closed to
            // nine and a half metres and never any nearer. Four fixes went
            // at the marker, the radius and the bot's budget before it became
            // clear the invitation was walking away from whoever accepted it.
            //
            // This is a writing bug wearing a pathfinding costume: the text
            // promises somebody standing still, and only the text was doing
            // that.
            if (WaitingAsHost) return;

            // A conversation outranks a schedule. Somebody who walks off
            // mid-sentence because it is nine o'clock is the exact failure
            // this is meant to fix.
            CheckHush();
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
                // AND THEY LOOK AWAY. Breaking off while still staring at
                // each other is two people pausing; breaking off and finding
                // somewhere else to look is two people who have been caught,
                // and the second is the one worth the whole feature.
                if (_body != null) _body.LookAt = _hushing ? null : _talkingTo.transform;
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

            // WALKING TOWARD A NOISE, which spec §8 calls the highest-value
            // behaviour in the whole system — it turns one sound into a moving
            // problem, and it explains itself to the player with no interface
            // at all. A man coming toward the thing you just did is the
            // clearest statement this game can make.
            if (_investigateUntil > Time.time) target = _investigateAt;

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

            // PERCEPTION, and it is deliberately OR-ed with the stance gaze
            // above rather than replacing it. The stance ladder answers "how
            // does this person feel about you", which is a social question and
            // still the right one; this answers "can they physically see you
            // from there, in this light, at this hour", which nothing in the
            // project has ever asked. A man under a lamp is looked at from
            // across the street and the same man in a doorway is not.
            if (_player != null && TickPerception(current)) wantsToLook = true;

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
