using System;

namespace Ledger.Core
{
    /// CINEMATIC FRAMING for the authored beats (the-gap.md §5).
    ///
    /// The pressure points, the Fall, Ellis's offer, the audit — every one of
    /// them currently lands as a line of text over an ordinary gameplay
    /// frame. The writing is doing all the work and the camera is doing none.
    ///
    /// THE CONSTRAINT THAT DECIDES THE WHOLE DESIGN, and it is the same one
    /// M15 was built on: **no cutscenes.** The simulation is the interface. A
    /// game that takes the camera away to show you something has stopped
    /// being the thing this game is. So framing here is not a shot — it is
    /// the camera briefly stopping fighting the player and starting to
    /// COMPOSE, and giving up the instant they touch the stick.
    ///
    /// What that buys is real: a beat that is framed reads as authored, and
    /// the same beat centred and unheld reads as a notification.
    public enum ShotSize
    {
        /// The street, and the player small in it. For a beat about the
        /// world rather than about a person.
        Wide = 0,
        /// A person, waist up. The default for somebody saying something.
        Medium = 1,
        /// A face. Reserved — used for everything, it means nothing.
        Close = 2,
    }

    public static class Framing
    {
        // ---- composition ---------------------------------------------------

        /// Where a subject belongs horizontally, 0..1 across the frame.
        ///
        /// The thirds, not the middle. A centred subject is the visual
        /// grammar of a webcam; a subject on a third with their look-space
        /// ahead of them is the grammar of a film, and it costs nothing.
        public const double LeftThird = 1.0 / 3.0;
        public const double RightThird = 2.0 / 3.0;

        /// The subject goes on the third BEHIND them, so the space they are
        /// facing into is in frame. Getting this backwards — space behind the
        /// head, face against the edge — is the single most common amateur
        /// framing error and it reads as wrong even to people who cannot say
        /// why.
        public static double SubjectX(bool facesRight) => facesRight ? LeftThird : RightThird;

        /// Headroom as a fraction of frame height above the subject's head.
        ///
        /// It TIGHTENS as the shot tightens. A close-up framed with wide-shot
        /// headroom leaves a face stranded at the bottom of the frame with a
        /// wall above it, which is the other most common amateur error.
        public static double Headroom(ShotSize size) =>
            size == ShotSize.Wide ? 0.18
            : size == ShotSize.Medium ? 0.10
            : 0.055;

        /// How far back the camera sits, in metres, for each shot size.
        public static double Distance(ShotSize size) =>
            size == ShotSize.Wide ? 7.5
            : size == ShotSize.Medium ? 3.4
            : 1.8;

        /// Which shot a beat deserves. `weight` is 0..1 — how much this
        /// moment matters.
        ///
        /// Close is deliberately hard to reach. A game that pushes in on
        /// everything has taught the player that pushing in means nothing,
        /// and then it cannot push in on the one moment that needed it.
        public static ShotSize SizeFor(double weight, bool aboutAPerson)
        {
            weight = Feel.Clamp01(weight);
            if (!aboutAPerson) return ShotSize.Wide;
            return weight >= 0.85 ? ShotSize.Close : ShotSize.Medium;
        }

        // ---- the 180-degree line -------------------------------------------

        /// THE LINE. Two people talking define an axis, and the camera must
        /// stay on ONE side of it. Cross it and they appear to swap places
        /// between shots — the viewer loses who is where, which is
        /// disorienting in a way nobody can articulate and everybody feels.
        ///
        /// This is pure geometry and therefore exactly the sort of craft rule
        /// a procedural camera can obey perfectly and a human operator
        /// sometimes cannot. Returns the signed side: positive and negative
        /// are the two sides, and the camera must not change sign.
        public static double SideOfLine(double ax, double az, double bx, double bz,
                                        double camX, double camZ)
        {
            // Cross product of (B-A) with (Cam-A). Sign is the side.
            return (bx - ax) * (camZ - az) - (bz - az) * (camX - ax);
        }

        public static bool WouldCrossTheLine(double ax, double az, double bx, double bz,
                                             double fromX, double fromZ,
                                             double toX, double toZ)
        {
            double a = SideOfLine(ax, az, bx, bz, fromX, fromZ);
            double b = SideOfLine(ax, az, bx, bz, toX, toZ);
            // A camera ON the line has no side to keep, so moving off it is
            // never a crossing — otherwise a camera that starts exactly
            // between two speakers can never move at all.
            if (Math.Abs(a) < 1e-9 || Math.Abs(b) < 1e-9) return false;
            return (a > 0) != (b > 0);
        }

        // ---- the push ------------------------------------------------------

        /// How far a push-in may travel, as a fraction of the starting
        /// distance. SMALL. A push you notice is a cutscene; a push you feel
        /// is direction.
        public const double MaxPushFraction = 0.14;

        /// Seconds. Long enough to read as deliberate, short enough that the
        /// player does not feel held.
        public const double PushSeconds = 1.6;

        /// Distance multiplier at time `t` into a push.
        public static double Push(double t)
        {
            double p = Feel.Clamp01(t / PushSeconds);
            // Ease-out: it moves most at the start and settles, which is how
            // a dolly behaves and the opposite of a lerp.
            double eased = 1 - Math.Pow(1 - p, 3);
            return 1.0 - MaxPushFraction * eased;
        }

        // ---- the hold ------------------------------------------------------

        /// How long the frame is held, by beat weight.
        ///
        /// Capped hard. The held beat is what makes a moment land — it is the
        /// thing that gets cut first and does the most work — but a camera
        /// that holds too long stops being emphasis and becomes a game that
        /// has taken the controls away.
        public const double MinHoldSeconds = 1.2;
        public const double MaxHoldSeconds = 3.4;

        /// Clamped at the end as well as interpolated, because
        /// `1.2 + 2.2 * 1.0` comes out a hair OVER 3.4 in binary floating
        /// point and a documented cap that the function can exceed is not a
        /// cap. Caught by a test asserting the cap rather than asserting the
        /// formula back at itself.
        public static double HoldSeconds(double weight) =>
            Feel.Clamp(MinHoldSeconds + (MaxHoldSeconds - MinHoldSeconds) * Feel.Clamp01(weight),
                       MinHoldSeconds, MaxHoldSeconds);

        // ---- and the rule that keeps it a game ------------------------------

        /// ANY input ends it, immediately and completely.
        ///
        /// Not "after a blend", not "unless we are in the important part".
        /// The forgiveness principle from §6 says the player's intent wins
        /// the frame they express it, and a camera that argues for even a
        /// third of a second is the difference between direction and being
        /// handled.
        public const double InputCancelThreshold = 0.08;

        public static bool PlayerTookOver(double moveMagnitude, double lookMagnitude) =>
            moveMagnitude > InputCancelThreshold || lookMagnitude > InputCancelThreshold;

        /// How fast the composed framing gives way once they do. Fast, but
        /// not instant — a hard snap back to the gameplay camera is its own
        /// jolt, and the whole point was to stop jolting people.
        public const double YieldSeconds = 0.28;

        public static double Authority(double sinceCancel)
        {
            if (sinceCancel < 0) return 1.0;
            double p = Feel.Clamp01(sinceCancel / YieldSeconds);
            return 1.0 - p * p;
        }
    }

    /// One framed beat, from the moment it fires to the moment the player has
    /// it back. Deliberately a small state machine rather than a coroutine, so
    /// it is testable and so a save mid-beat cannot leave the camera holding.
    public class FramedBeat
    {
        public double Weight = 0.5;
        public bool AboutAPerson = true;

        double _t = -1;
        double _cancelledAt = -1;

        public bool Running => _t >= 0;
        public ShotSize Size { get; private set; }
        /// 1 while the framing owns the camera, falling to 0 as it yields.
        public double Authority { get; private set; }
        /// Distance multiplier to apply to the rig's normal follow distance.
        public double PushScale { get; private set; } = 1.0;
        /// Fires once, on the tick the beat is completely finished.
        public bool Done { get; private set; }

        public double Total => Framing.PushSeconds + Framing.HoldSeconds(Weight);

        public bool Begin(double weight, bool aboutAPerson)
        {
            if (Running) return false;
            Weight = Feel.Clamp01(weight);
            AboutAPerson = aboutAPerson;
            Size = Framing.SizeFor(Weight, aboutAPerson);
            _t = 0;
            _cancelledAt = -1;
            Authority = 1.0;
            PushScale = 1.0;
            Done = false;
            Begun++;
            return true;
        }

        /// The player moved or looked. From here the framing is on its way
        /// out and cannot be revived by them stopping again — a camera that
        /// comes BACK when you let go of the stick is the most infuriating
        /// version of this feature there is.
        public void Cancel()
        {
            if (!Running || _cancelledAt >= 0) return;
            _cancelledAt = _t;
        }

        /// STOP NOW, with no yield at all.
        ///
        /// Distinct from `Cancel`, which is the PLAYER taking the camera back
        /// and deliberately hands over across `YieldSeconds` — a hard snap
        /// there would be its own jolt. This is for the one case where there
        /// is no player and no jolt to avoid: the simulation about to render
        /// a measured frame, which must be the ordinary gameplay framing and
        /// not a composed one.
        ///
        /// It exists because the alternative was the framing being switched
        /// off in the sim entirely, which is how it went months without ever
        /// executing in a verified build.
        public void Abort()
        {
            _t = -1;
            _cancelledAt = -1;
            Authority = 0;
            PushScale = 1.0;
            Done = false;
        }

        /// How many beats have begun. The sim gate reads it: a camera layer
        /// that never runs looks exactly like one with nothing to frame.
        public static int Begun { get; private set; }

        // ---- the 180-degree rule, MEASURED before it is enforced ------------
        //
        // `SideOfLine` and `WouldCrossTheLine` have sat on the reach ledger
        // since they were written, under the ledger's own note: *"the 180
        // degree rule, computed and never consulted"* and *"the one that would
        // actually stop a bad cut"*. Three writers, no readers — rule 6.
        //
        // AND THE WIRING IS NOT THE FIRST STEP. The beat does not place the
        // camera: it pulls in ALONG THE RIG'S OWN LINE, deliberately, because
        // the rig has already solved collision and lag. So the beat cannot
        // cross the line by itself; the FOLLOW RIG can, by orbiting as the
        // player turns, and nobody has ever measured whether it does.
        //
        // Writing the enforcement first would be setting a policy against an
        // unmeasured quantity, which is rule 2 in camera form — and if the rig
        // turns out never to cross during a beat, the enforcement would be
        // dead code that looks like a feature. So this counts crossings and
        // says nothing else, and the fix (if the number asks for one) comes
        // after a run has been read.

        double _ax, _az, _bx, _bz;
        double _camX0, _camZ0;
        bool _watching;

        /// How many beats watched a line, and how many of those saw the camera
        /// cross it. A ratio, from one instant each — both incremented on the
        /// same beat, so they CAN be divided.
        public static int LineWatched { get; private set; }
        public static int LineCrossed { get; private set; }

        /// OF THE CROSSINGS, HOW MANY HAPPENED WHILE THE BEAT STILL OWNED THE
        /// CAMERA — and this is the split that decides whether there is
        /// anything to fix at all.
        ///
        /// The first reading was `lineWatched=43 lineCrossed=9`, and twenty-one
        /// percent looks like a clear mandate to write the enforcement. It is
        /// not, because the two ways to get there want opposite responses:
        ///
        ///   - the PLAYER swung the camera across. The beat has already
        ///     cancelled — `PlayerTookOver` fires on look input — and it is
        ///     handing the camera back over `YieldSeconds`. Nothing is wrong.
        ///     This file's whole position is that a camera taken away from the
        ///     player has stopped being the interface, so "correcting" this
        ///     would be the feature fighting the person using it.
        ///   - the RIG crossed on its own, following, lagging or sliding off a
        ///     collision, while the beat was live and composing. That is a
        ///     composed shot reversing who is looking at whom, and it is the
        ///     thing the 180-degree rule exists to prevent.
        ///
        /// One number cannot tell those apart, and building the correction
        /// against the pooled count risks a fix that only ever fires on the
        /// case that was already correct — which is rule 5b's shape, arriving
        /// before the guard rather than after it for once.
        public static int LineCrossedLive { get; private set; }

        /// Did THIS beat's camera cross? Read by the sim per beat.
        public bool Crossed { get; private set; }

        /// The line this beat is about, and where the camera stood when it
        /// began. A beat with nobody in it has no line to keep — the street is
        /// not a second subject — so it simply is not watched.
        public void HoldTheLine(double ax, double az, double bx, double bz,
                                double camX, double camZ)
        {
            _watching = false;
            Crossed = false;
            if (!Running || !AboutAPerson) return;
            // TWO SUBJECTS IN THE SAME PLACE HAVE NO LINE BETWEEN THEM, and
            // the cross product would be zero however the camera moved — so a
            // degenerate pair would report "never crosses" forever and read as
            // a clean bill of health.
            double dx = bx - ax, dz = bz - az;
            if (dx * dx + dz * dz < 0.25) return;   // half a metre apart, at least
            _ax = ax; _az = az; _bx = bx; _bz = bz;
            _camX0 = camX; _camZ0 = camZ;
            // STARTED ON THE LINE MEANS NO SIDE TO KEEP, and such a beat is
            // not watched at all rather than watched and never crossing —
            // counting it would dilute the ratio with beats that are
            // incapable of failing, which is the "quiet gate" fault in a
            // denominator.
            if (Math.Abs(Framing.SideOfLine(ax, az, bx, bz, camX, camZ)) < 1e-9) return;
            _watching = true;
            LineWatched++;
        }

        /// The camera is here now. Latches on the FIRST crossing rather than
        /// counting every frame it stays over there: one bad move is one bad
        /// move, and a per-frame count would report the same mistake sixty
        /// times a second and rank it above a hundred real ones.
        public void CameraMovedTo(double camX, double camZ)
        {
            if (!_watching || Crossed || !Running) return;
            // AGAINST WHERE THE CAMERA ACTUALLY STARTED, not a point
            // reconstructed from the side it was on. The first version built a
            // synthetic "from" by rotating the line — arithmetic that is only
            // as trustworthy as my sign conventions, to feed a function whose
            // entire job is to get those signs right. The real starting
            // position is sitting right there and needs no derivation.
            if (!Framing.WouldCrossTheLine(_ax, _az, _bx, _bz,
                                           _camX0, _camZ0, camX, camZ)) return;
            Crossed = true;
            LineCrossed++;
            // `_cancelledAt < 0` is "the player has not taken it back yet", so
            // the beat still owns the frame and this crossing is the RIG's.
            if (_cancelledAt < 0) LineCrossedLive++;
        }

        // NO RESET. The obvious companion here is a `ResetLineCounters()` for
        // test isolation, and it would be a public Core API with no caller in
        // the game — rule 6, self-inflicted, to save the tests from doing
        // arithmetic. The tests beside these already read `Begun` as a DELTA
        // against what it was before, which is the same discipline and needs
        // no surface. `WorldText.ResetCounters` is the version of this that
        // did get written, and it has sat unreachable ever since.

        public void Tick(double dt, double moveMagnitude = 0, double lookMagnitude = 0)
        {
            Done = false;
            if (!Running || dt <= 0) return;
            if (Framing.PlayerTookOver(moveMagnitude, lookMagnitude)) Cancel();

            _t += dt;
            PushScale = Framing.Push(_t);
            Authority = _cancelledAt >= 0
                ? Framing.Authority(_t - _cancelledAt)
                : 1.0;

            // Finished when it has run its length, or when it has finished
            // handing back. The latch is the same shape as VerbBeat's and
            // Curtain's, and for the same reason: a long frame must not
            // swallow the moment.
            bool over = _cancelledAt >= 0
                ? _t - _cancelledAt >= Framing.YieldSeconds
                : _t >= Total;
            if (over) { _t = -1; Authority = 0; PushScale = 1.0; Done = true; }
        }
    }
}
