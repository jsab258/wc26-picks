using System;

namespace Ledger.Core
{
    /// GAME FEEL (game-feel-spec.md §2, §3, §7), as maths rather than as
    /// MonoBehaviour code.
    ///
    /// The spec's uncomfortable line was that "you can fix 70% of 'this feels
    /// cheap' without a single art asset, and we have done none of it." The
    /// two worst offenders were both here: the player reached full speed in
    /// one frame, and the camera was welded to a point 5.5 metres behind his
    /// head. Neither is an art problem.
    ///
    /// This lives in Core because feel is the kind of thing that gets quietly
    /// broken. A camera that overshoots at 30fps but not at 144, a limp that
    /// makes you slower than you should be, an acceleration curve that is
    /// secretly frame-rate dependent — all of those are invisible in a
    /// screenshot and obvious in the hands, which is the worst possible
    /// combination for a system with no tests. Every claim below is checkable
    /// without opening Unity.
    public static class Feel
    {
        /// Exponential approach, done the frame-rate-independent way.
        ///
        /// The everywhere-version of this is `current + (target - current) *
        /// 0.1f`, which is a different spring at every frame rate: the same
        /// game feels tighter on a fast machine and floatier on a slow one,
        /// and the tuning you did at 60fps is wrong for everyone else.
        /// Going through exp() makes the remaining error after T seconds
        /// exactly e^(-stiffness*T) no matter how the frames were sliced.
        public static double Approach(double current, double target, double stiffness, double dt)
        {
            if (dt <= 0 || stiffness <= 0) return current;
            double k = 1.0 - Math.Exp(-stiffness * dt);
            return current + (target - current) * k;
        }

        public static double Clamp01(double v) => v < 0 ? 0 : v > 1 ? 1 : v;

        public static double Clamp(double v, double lo, double hi) => v < lo ? lo : v > hi ? hi : v;

        /// Shortest signed angular distance from a to b, in degrees, in
        /// (-180, 180]. Turning 350 degrees the long way round is the classic
        /// way a character spins on the spot when it should have flinched.
        public static double DeltaAngle(double a, double b)
        {
            double d = (b - a) % 360.0;
            if (d > 180.0) d -= 360.0;
            if (d <= -180.0) d += 360.0;
            return d;
        }

        public static double MoveTowardsAngle(double current, double target, double maxDelta)
        {
            double d = DeltaAngle(current, target);
            if (Math.Abs(d) <= maxDelta) return Norm(target);
            return Norm(current + Math.Sign(d) * maxDelta);
        }

        static double Norm(double a)
        {
            a %= 360.0;
            if (a < 0) a += 360.0;
            return a;
        }

        public static double HeadingDegrees(double x, double z) =>
            Norm(Math.Atan2(x, z) * (180.0 / Math.PI));
    }

    /// Momentum. You lean into a start and settle out of a stop.
    ///
    /// Deceleration is deliberately faster than acceleration, which is how
    /// real bodies work and, more usefully, is what stops "let go of the
    /// stick" from feeling like ice. The asymmetry is the whole trick: too
    /// little and you teleport, too much and you are driving a boat.
    public class Locomotion
    {
        public const double WalkSpeed = 4.0;
        public const double RunSpeed = 7.0;

        /// m/s^2. ~0.2s from stopped to a walk — long enough to feel, short
        /// enough that nobody calls it sluggish.
        public double Accel = 20.0;
        public double Decel = 28.0;
        /// A body cannot pivot instantly. 540 deg/s means a full reversal
        /// costs a third of a second, which reads as a person changing their
        /// mind rather than a turret slewing.
        public double TurnDegreesPerSecond = 540.0;

        public double VelocityX, VelocityZ;
        /// Degrees, 0 = +Z, matching the heading convention above.
        public double FacingDegrees;

        public double Speed => Math.Sqrt(VelocityX * VelocityX + VelocityZ * VelocityZ);

        /// How much of top speed we are actually doing, 0..1. Drives FOV,
        /// head bob, and the footstep cadence — one number, so they can never
        /// disagree with each other.
        public double Effort(double topSpeed) => topSpeed <= 0 ? 0 : Feel.Clamp01(Speed / topSpeed);

        public void Stop()
        {
            VelocityX = VelocityZ = 0;
        }

        /// desiredX/desiredZ is the stick: a direction, magnitude 0..1.
        public void Step(double desiredX, double desiredZ, double topSpeed, double dt)
        {
            if (dt <= 0) return;

            double mag = Math.Sqrt(desiredX * desiredX + desiredZ * desiredZ);
            if (mag > 1.0) { desiredX /= mag; desiredZ /= mag; mag = 1.0; }

            double targetX = desiredX * topSpeed;
            double targetZ = desiredZ * topSpeed;

            // Linear approach rather than exponential, on purpose: an
            // exponential never quite arrives, so top speed would be an
            // asymptote you can feel yourself never reaching.
            double rate = mag > 0.001 ? Accel : Decel;
            double diffX = targetX - VelocityX, diffZ = targetZ - VelocityZ;
            double d = Math.Sqrt(diffX * diffX + diffZ * diffZ);
            double step = rate * dt;
            if (d <= step || d <= 1e-9)
            {
                VelocityX = targetX; VelocityZ = targetZ;
            }
            else
            {
                VelocityX += diffX / d * step;
                VelocityZ += diffZ / d * step;
            }

            if (mag > 0.001)
                FacingDegrees = Feel.MoveTowardsAngle(FacingDegrees,
                    Feel.HeadingDegrees(desiredX, desiredZ),
                    TurnDegreesPerSecond * dt);
        }
    }

    /// The camera follows; it is not welded on.
    ///
    /// Three separate cheap wins, all in one place because they have to agree
    /// about speed: lag, FOV that opens as you move, and look-ahead so the
    /// frame leads you into where you are going rather than trailing you.
    public class CameraRig
    {
        /// Higher is tighter. 9 lags by about a tenth of a second, which the
        /// eye reads as weight rather than as delay.
        public double Stiffness = 9.0;
        public double BaseFov = 60.0;
        /// Widening on the move is the oldest trick there is for making speed
        /// felt rather than measured. Keep it small; large FOV pumps make
        /// people ill.
        public double FovGain = 7.0;
        public double LookAheadMetres = 2.2;

        public double X, Y, Z;
        public double Fov;
        public double AheadX, AheadZ;
        bool _placed;

        /// Snap without lag — for spawns, loads, and teleports, where a
        /// spring would sweep the camera across the entire city.
        public void Place(double x, double y, double z)
        {
            X = x; Y = y; Z = z;
            Fov = BaseFov;
            AheadX = AheadZ = 0;
            _placed = true;
        }

        /// Beyond this, it was a teleport and not a movement, so cut rather
        /// than sweep. Getting out of a car, loading a save, waking up after
        /// the Fall — every one of those moves the player further than any
        /// stride could, and a spring would answer by flying the camera
        /// across the city. Handling it here means every future teleport is
        /// covered without anyone remembering to call anything.
        public double TeleportMetres = 8.0;

        public void Follow(double targetX, double targetY, double targetZ,
                           double effort, double headingX, double headingZ, double dt)
        {
            if (!_placed) { Place(targetX, targetY, targetZ); return; }

            double dx = targetX - X, dy = targetY - Y, dz = targetZ - Z;
            if (dx * dx + dy * dy + dz * dz > TeleportMetres * TeleportMetres)
            {
                Place(targetX, targetY, targetZ);
                return;
            }

            effort = Feel.Clamp01(effort);
            double lead = LookAheadMetres * effort;
            AheadX = Feel.Approach(AheadX, headingX * lead, Stiffness * 0.6, dt);
            AheadZ = Feel.Approach(AheadZ, headingZ * lead, Stiffness * 0.6, dt);

            X = Feel.Approach(X, targetX + AheadX, Stiffness, dt);
            Y = Feel.Approach(Y, targetY, Stiffness, dt);
            Z = Feel.Approach(Z, targetZ + AheadZ, Stiffness, dt);

            // FOV settles more slowly than position, so stopping feels like
            // settling rather than snapping shut.
            Fov = Feel.Approach(Fov, BaseFov + FovGain * effort, 4.0, dt);
        }
    }

    /// State written on the body (spec §7). We have simulated injury since
    /// the harm system landed and never once shown it.
    ///
    /// The insight that makes a limp cheap: a limp is not an animation, it is
    /// an ASYMMETRY. The good leg carries a long stride, the bad one hurries
    /// a short one. Do that to the footstep cadence and the sound alone
    /// reads as injured before any model exists to show it.
    public static class Gait
    {
        /// Metres between footfalls at a walk. Roughly a real stride, so the
        /// cadence reads as a person rather than as a metronome.
        public const double StrideMetres = 1.6;

        /// How lopsided a limp gets at its worst. Above about 0.5 it stops
        /// reading as injured and starts reading as broken animation.
        public const double MaxAsymmetry = 0.45;

        /// Severity 0..1, where 1 is barely able to stand.
        public static double SeverityFromCapability(double capability) =>
            Feel.Clamp01(1.0 - capability);

        /// The stride for one footfall. Alternates long/short when hurt.
        ///
        /// A pair of steps always covers the same ground as two healthy ones,
        /// so a limp changes the RHYTHM and not the speed. Anything else and
        /// the sound would drift out of sync with the movement, which is the
        /// single most obvious way a footstep system announces itself as fake.
        public static double StrideFor(int footfall, double severity)
        {
            double a = MaxAsymmetry * Feel.Clamp01(severity);
            bool good = (footfall & 1) == 0;
            return StrideMetres * (good ? 1.0 + a : 1.0 - a);
        }

        /// Hurt people are slower. Bounded, because a player who cannot move
        /// is a player who has stopped playing.
        public static double SpeedFactor(double severity) =>
            Feel.Clamp(1.0 - 0.45 * Feel.Clamp01(severity), 0.55, 1.0);

        /// Vertical head travel in metres. Small — this is the difference
        /// between "alive" and "seasick".
        public static double BobAmplitude(double effort) =>
            0.012 + 0.030 * Feel.Clamp01(effort);

        /// A limping step lands harder on the good leg. Drives footstep
        /// volume, which is what actually sells it through headphones.
        public static double StepWeight(int footfall, double severity)
        {
            double a = 0.35 * Feel.Clamp01(severity);
            bool good = (footfall & 1) == 0;
            return Feel.Clamp(1.0 + (good ? a : -a), 0.4, 1.6);
        }
    }

    /// Input buffering (spec §1). A key pressed just before an action becomes
    /// legal still counts. Without it the game feels like it is ignoring you,
    /// and players do not report that as "no input buffer" — they report the
    /// game as unresponsive.
    public class InputBuffer
    {
        public double WindowSeconds = 0.15;
        double _pressedAt = double.NegativeInfinity;
        bool _spent = true;

        public void Press(double now)
        {
            _pressedAt = now;
            _spent = false;
        }

        /// True at most once per press, and only inside the window.
        public bool Consume(double now)
        {
            if (_spent) return false;
            if (now - _pressedAt > WindowSeconds) return false;
            _spent = true;
            return true;
        }

        public void Clear() => _spent = true;
    }

    /// Forgiveness windows (spec §1): a prompt stays valid for a beat after
    /// you step out of range. The alternative is a prompt that flickers on
    /// the boundary, which teaches players to stand unnaturally still.
    public class Forgiveness
    {
        public double GraceSeconds = 0.3;
        double _lastSeen = double.NegativeInfinity;

        public void SeenInRange(double now) => _lastSeen = now;

        public bool StillOffered(double now) => now - _lastSeen <= GraceSeconds;

        public void Drop() => _lastSeen = double.NegativeInfinity;
    }
}
