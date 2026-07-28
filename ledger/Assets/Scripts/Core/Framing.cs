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
