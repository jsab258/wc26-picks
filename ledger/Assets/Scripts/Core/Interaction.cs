using System;

namespace Ledger.Core
{
    /// Interaction grammar (game-feel-spec.md §5 and §6).
    ///
    /// The spec's rule: **every verb should have anticipation → action →
    /// consequence → recovery, and instant state flips are the hallmark of a
    /// prototype.** LEDGER flips instantly everywhere. A door is a boolean. A
    /// prompt pops. You walk through a crowd like a ghost, which quietly
    /// tells the player that none of it is real — and that is the most
    /// expensive sentence in the whole document, because it means the
    /// simulation underneath is being disbelieved on the strength of the
    /// contact layer.
    ///
    /// All of it is maths so it can be tested. A door that "feels heavy" is
    /// not a matter of opinion once you write down what heavy means: it
    /// accelerates, it overshoots slightly, it settles, and it cannot be
    /// reversed instantly.
    public enum VerbPhase
    {
        /// Nothing happening.
        Idle,
        /// The wind-up. The hand reaches; the player can still see it coming.
        Anticipation,
        /// The moment the state actually changes.
        Action,
        /// The world answering: the sound, the swing, the money changing hands.
        Consequence,
        /// Settling back to neutral. Skipping this is what makes an action
        /// feel like a light switch.
        Recovery,
    }

    /// One verb, in time. Not an animation — a clock that an animation, a
    /// sound and a state change can all hang off, so they cannot drift apart.
    public class VerbBeat
    {
        public double AnticipationSeconds = 0.18;
        public double ActionSeconds = 0.06;
        public double ConsequenceSeconds = 0.35;
        public double RecoverySeconds = 0.22;

        double _t = -1;
        bool _firedThisRun;

        public VerbPhase Phase { get; private set; } = VerbPhase.Idle;
        /// True on exactly the frame the state should change. The whole point
        /// of the class: ONE place decides when the door is actually open.
        public bool Fired { get; private set; }
        public bool Busy => Phase != VerbPhase.Idle;

        public double Total => AnticipationSeconds + ActionSeconds +
                               ConsequenceSeconds + RecoverySeconds;

        /// Begin, if not already going. Returns false if the verb was busy —
        /// which is how a verb refuses to be spammed without needing a
        /// cooldown bolted on beside it.
        public bool Begin()
        {
            if (Busy) return false;
            _t = 0;
            Phase = VerbPhase.Anticipation;
            Fired = false;
            _firedThisRun = false;
            return true;
        }

        public void Tick(double dt)
        {
            Fired = false;
            if (!Busy || dt <= 0) return;

            _t += dt;

            double a = AnticipationSeconds;
            double b = a + ActionSeconds;
            double c = b + ConsequenceSeconds;
            double d = c + RecoverySeconds;

            // Fire ONCE, the first tick at or past the action point.
            //
            // The obvious version — fire while inside the action window —
            // fires several times on a fast machine and zero times on a slow
            // one, which is the classic way a door opens at 240fps and does
            // not at 30. Latching a flag instead is correct at any frame
            // length AND at any phase length, including an anticipation of
            // zero for a verb that is meant to be instant. The crossing test
            // this replaced got the frame rate right and silently never fired
            // when anticipation was 0, because nothing crosses zero from
            // below.
            if (!_firedThisRun && _t >= a) { Fired = true; _firedThisRun = true; }

            Phase = _t >= d ? VerbPhase.Idle
                  : _t >= c ? VerbPhase.Recovery
                  : _t >= b ? VerbPhase.Consequence
                  : _t >= a ? VerbPhase.Action
                  : VerbPhase.Anticipation;
            if (Phase == VerbPhase.Idle) _t = -1;
        }

        /// 0..1 through the current phase, for anything that wants to lerp.
        public double PhaseProgress
        {
            get
            {
                if (!Busy) return 0;
                double a = AnticipationSeconds, b = a + ActionSeconds, c = b + ConsequenceSeconds;
                switch (Phase)
                {
                    case VerbPhase.Anticipation: return Feel.Clamp01(_t / Math.Max(1e-6, a));
                    case VerbPhase.Action: return Feel.Clamp01((_t - a) / Math.Max(1e-6, ActionSeconds));
                    case VerbPhase.Consequence: return Feel.Clamp01((_t - b) / Math.Max(1e-6, ConsequenceSeconds));
                    default: return Feel.Clamp01((_t - c) / Math.Max(1e-6, RecoverySeconds));
                }
            }
        }

        public void Cancel()
        {
            _t = -1; Phase = VerbPhase.Idle; Fired = false; _firedThisRun = true;
        }
    }

    /// A door with mass.
    ///
    /// Doors are the most-touched object in any game and ours is a boolean.
    /// The three things that make one feel heavy, in order of how much they
    /// buy: it takes TIME, it OVERSHOOTS and settles rather than stopping
    /// dead, and it LATCHES audibly at the very end of closing — the latch is
    /// the single most recognisable sound a door makes and the one nobody
    /// models.
    public class DoorSwing
    {
        /// Degrees. Positive is open.
        public double OpenAngle = 85.0;
        /// How fast it wants to move. A heavier door is a slower one.
        public double Stiffness = 7.0;
        /// Under 1 overshoots and comes back; at 1 it eases in flat. A door
        /// that never overshoots reads as a sliding panel.
        public double Damping = 0.62;

        public double Angle { get; private set; }
        public double Velocity { get; private set; }
        public bool Open { get; private set; }

        /// True on the frame the latch catches. Drives the click.
        public bool Latched { get; private set; }
        /// True on the frame the door reaches its open stop and thumps.
        public bool HitStop { get; private set; }

        public void Set(bool open)
        {
            Open = open;
        }

        public void Toggle() => Open = !Open;

        public void Tick(double dt)
        {
            Latched = false;
            HitStop = false;
            if (dt <= 0) return;

            double target = Open ? OpenAngle : 0.0;

            // A damped spring, integrated semi-implicitly so it stays stable
            // at any frame rate rather than exploding on a long frame.
            double accel = (target - Angle) * Stiffness * Stiffness
                         - Velocity * 2.0 * Damping * Stiffness;
            Velocity += accel * dt;
            double next = Angle + Velocity * dt;

            // The stops are real. A door does not pass through its own frame,
            // and hitting the wall is a sound.
            if (next <= 0.0)
            {
                if (Angle > 0.0 && Math.Abs(Velocity) > 0.5) Latched = true;
                next = 0.0;
                Velocity = 0.0;
            }
            else if (next >= OpenAngle * 1.15)
            {
                if (Angle < OpenAngle * 1.15) HitStop = true;
                next = OpenAngle * 1.15;
                Velocity = -Math.Abs(Velocity) * 0.25;   // bounces back a little
            }
            Angle = next;
        }

        /// Settled at either stop, so callers know when to stop simulating.
        public bool AtRest => Math.Abs(Velocity) < 0.01 &&
                              Math.Abs(Angle - (Open ? OpenAngle : 0.0)) < 0.05;
    }

    /// What happens when you walk into someone.
    ///
    /// Right now: nothing. You pass through a crowd like a ghost. This is
    /// the cheapest possible fix for the most damaging possible impression,
    /// because a person who does not notice being shoved is a person the
    /// player stops believing in — and this is a game about being noticed.
    public enum BumpReaction
    {
        /// Barely contact. A glance at most.
        Brush,
        /// A real knock. They stumble, they look, they say something.
        Knock,
        /// You ran into them. They are annoyed, and annoyance is a fact the
        /// gossip mill can carry.
        Shove,
    }

    public static class Bumps
    {
        /// Below this it did not happen.
        public const double MinSpeed = 0.6;

        public static BumpReaction Classify(double relativeSpeed) =>
            relativeSpeed >= Locomotion.RunSpeed * 0.75 ? BumpReaction.Shove :
            relativeSpeed >= Locomotion.WalkSpeed * 0.6 ? BumpReaction.Knock :
            BumpReaction.Brush;

        /// How far the person is pushed, in metres. Small — this is a
        /// stumble, not physics comedy.
        public static double Stagger(double relativeSpeed) =>
            Feel.Clamp(relativeSpeed * 0.12, 0.0, 0.55);

        /// How long they look at you afterwards. Being noticed is the
        /// currency of this game, so a shove buys more attention than a
        /// brush, and that attention is what the stance system reads.
        public static double AttentionSeconds(BumpReaction r) =>
            r == BumpReaction.Shove ? 4.0 :
            r == BumpReaction.Knock ? 2.2 :
            0.8;

        /// Whether it is worth a witness recording anything at all. A brush
        /// in a crowd is not an event; being shoved by the man everyone is
        /// already talking about is.
        public static bool WorthRemembering(BumpReaction r) => r != BumpReaction.Brush;
    }

    /// TRANSITIONS (game-feel-spec.md §8): "no hard cuts anywhere — fades,
    /// camera moves, a held beat."
    ///
    /// The Fall is the biggest thing that happens in LEDGER. Three days
    /// vanish, the money is seized, and every person on the street stops
    /// guessing about you and simply knows. It is currently a toast: a line
    /// of amber text that slides in over a normally-lit street while the
    /// world snaps three days forward in front of you.
    ///
    /// A curtain is the cheapest possible fix and the oldest trick in
    /// film — you do not show the cut, you hold black across it. The held
    /// beat is the part people skip and the part that does the work: the
    /// silence is what makes the player sit with it rather than read it.
    public class Curtain
    {
        public double FadeOutSeconds = 1.2;
        /// Long enough to be uncomfortable. That is the point.
        public double HoldSeconds = 2.6;
        public double FadeInSeconds = 2.2;

        double _t = -1;
        bool _firedThisRun;

        /// 0 = clear, 1 = fully black.
        public double Alpha { get; private set; }
        public bool Running => _t >= 0;
        /// True on the one tick where the world is fully hidden and may
        /// therefore be changed. Everything jarring goes here.
        public bool Hidden { get; private set; }

        public double Total => FadeOutSeconds + HoldSeconds + FadeInSeconds;

        public bool Begin()
        {
            if (Running) return false;
            _t = 0;
            _firedThisRun = false;
            Alpha = 0;
            return true;
        }

        public void Tick(double dt)
        {
            Hidden = false;
            if (!Running || dt <= 0) return;
            _t += dt;

            double a = FadeOutSeconds, b = a + HoldSeconds, c = b + FadeInSeconds;

            // Same latch as VerbBeat, for the same reason: a long frame must
            // not skip the moment, and that moment is where three days of
            // world state change. Missing it would show the player the cut.
            if (!_firedThisRun && _t >= a) { Hidden = true; _firedThisRun = true; }

            if (_t >= c) { Alpha = 0; _t = -1; return; }
            if (_t >= b) { Alpha = 1.0 - Feel.Clamp01((_t - b) / Math.Max(1e-6, FadeInSeconds)); return; }
            if (_t >= a) { Alpha = 1.0; return; }
            Alpha = Feel.Clamp01(_t / Math.Max(1e-6, FadeOutSeconds));
        }

        /// Text should appear only while the curtain is fully down, and go
        /// before the world comes back. A line fading in over the returning
        /// street is two things competing for the same beat.
        public double TextAlpha
        {
            get
            {
                // No Alpha guard needed: `into` is negative during the fade
                // out and past HoldSeconds during the fade in, so both edges
                // already clamp to zero. A redundant check here looked
                // load-bearing and was not — a deliberate break removed it
                // and no test noticed, which is how dead code earns its
                // place in a file forever.
                if (!Running) return 0;
                double a = FadeOutSeconds;
                double into = _t - a;
                double edge = Math.Min(0.5, HoldSeconds * 0.25);
                if (into < edge) return Feel.Clamp01(into / edge);
                if (into > HoldSeconds - edge) return Feel.Clamp01((HoldSeconds - into) / edge);
                return 1.0;
            }
        }
    }
    // -------------------------------------------------------------------

    /// MENU TRANSITIONS (game-feel-spec §8, the last item in it).
    ///
    /// The Fall gets a two-second curtain because it is the heaviest moment
    /// in the game. A menu is the opposite problem: it is the moment the
    /// player is most impatient, and a menu that takes its time is a menu
    /// that feels broken. So the numbers here are small, and the asymmetry
    /// runs the other way from everything else in this file — IN is fast,
    /// OUT is slower. Arriving should feel instant; leaving is allowed to be
    /// soft, because by then the player has already decided and is not
    /// waiting on anything.
    public static class Menus
    {
        /// Fast enough to read as instant, slow enough not to pop.
        public const double InSeconds = 0.12;
        /// Leaving may be soft: nothing is waiting on it.
        public const double OutSeconds = 0.20;
        /// Panel-to-panel inside one menu — options to keybindings and back.
        /// A hair quicker than a full open, because the frame around it never
        /// went anywhere and re-fading the whole screen would say it did.
        public const double SwapSeconds = 0.10;

        /// How far a panel rises as it arrives, in reference-resolution
        /// pixels. Small. Motion here is a hint that something moved, not an
        /// animation to be admired — and a panel that slides a long way is a
        /// panel the player is waiting on.
        public const double RisePixels = 14;

        /// Ease-out on the way in (fast start, gentle landing) and ease-in on
        /// the way out. Cubic, because quadratic is not quite enough to read
        /// at 120ms and quartic overshoots into sluggish.
        public static double EaseIn(double t)
        {
            t = Feel.Clamp01(t);
            double u = 1 - t;
            return 1 - u * u * u;
        }

        public static double EaseOut(double t)
        {
            t = Feel.Clamp01(t);
            return t * t * t;
        }
    }

    /// One panel's arrival and departure. Deliberately a state machine over
    /// an ALPHA rather than over a timer, so that reversing mid-transition
    /// picks up from where the panel actually is. A timer-based version
    /// restarts from zero when the player clicks Back and then immediately
    /// changes their mind, and the panel visibly flickers — which is the
    /// single most common way a menu transition goes wrong.
    public class PanelFade
    {
        public double InSeconds = Menus.InSeconds;
        public double OutSeconds = Menus.OutSeconds;
        public double RisePixels = Menus.RisePixels;

        /// 0 = absent, 1 = fully present. This is the state; everything else
        /// is read off it.
        public double Alpha { get; private set; }
        public bool Wanted { get; private set; }

        /// True whenever there is anything to draw. The caller keeps the
        /// object alive while this holds.
        public bool Visible => Alpha > 0.0001 || Wanted;

        /// Fires ONCE on the tick the panel has finished leaving, so the
        /// caller can deactivate it exactly once rather than every frame
        /// afterwards. Same latch as VerbBeat and Curtain, for the same
        /// reason: a long frame must not swallow the moment.
        public bool Gone { get; private set; }

        /// A panel accepts clicks the moment it starts arriving, not when it
        /// finishes. The forgiveness principle from §6: an impatient player
        /// who clicks at 40ms has hit the button they can see, and eating
        /// that click to protect an animation is how a menu earns the word
        /// clunky.
        public bool Interactable => Wanted && Alpha > 0.0001;

        /// Reference-resolution pixels of upward offset remaining. Positive
        /// means the panel is still below where it belongs.
        public double Rise => RisePixels * (1 - Menus.EaseIn(Alpha));

        public void Show() => Wanted = true;
        public void Hide() => Wanted = false;

        /// Present immediately, no transition. For a panel that is already
        /// meant to be on screen when the menu is first built — fading it in
        /// at boot would look like a stutter rather than a transition.
        public void SnapOn() { Wanted = true; Alpha = 1; Gone = false; }
        public void SnapOff() { Wanted = false; Alpha = 0; Gone = false; }

        public void Tick(double dt)
        {
            Gone = false;
            if (dt <= 0) return;
            bool wasPresent = Alpha > 0.0001;
            // Linear in alpha with the easing applied at read time, so the
            // reverse of a half-finished fade takes half the time rather than
            // the full one. Easing the alpha itself would make a reversal
            // start from the wrong place on the curve.
            double rate = Wanted
                ? (InSeconds > 0 ? 1.0 / InSeconds : double.MaxValue)
                : (OutSeconds > 0 ? -1.0 / OutSeconds : double.MinValue);
            Alpha = Feel.Clamp01(Alpha + rate * dt);
            if (!Wanted && wasPresent && Alpha <= 0.0001) Gone = true;
        }
    }

    /// Two panels sharing one frame — options and keybindings, a pause menu
    /// and its confirm. The outgoing one leaves while the incoming one
    /// arrives, overlapping, because a menu that blanks between two panels
    /// tells the player the whole screen went away when only its contents
    /// did.
    public class PanelSwap
    {
        public double Seconds = Menus.SwapSeconds;

        public readonly PanelFade A = new PanelFade();
        public readonly PanelFade B = new PanelFade();

        public PanelSwap()
        {
            A.InSeconds = A.OutSeconds = Menus.SwapSeconds;
            B.InSeconds = B.OutSeconds = Menus.SwapSeconds;
            A.RisePixels = B.RisePixels = 0;   // the frame did not move; neither do they
            A.SnapOn();
            B.SnapOff();
        }

        public void ToA() { A.Show(); B.Hide(); }
        public void ToB() { B.Show(); A.Hide(); }

        public void Tick(double dt) { A.Tick(dt); B.Tick(dt); }

        /// Both are drawn at once mid-swap, and that is the point.
        public bool Crossing => A.Alpha > 0.0001 && B.Alpha > 0.0001;
    }

}
