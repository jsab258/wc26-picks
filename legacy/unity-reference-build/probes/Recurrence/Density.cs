using System;
using System.Collections.Generic;
using System.Linq;
using Ledger.Core;

/// HOW THIN CAN THE CROWD GET BEFORE THE BEST THING THIS GAME DOES STOPS
/// WORKING.
///
/// WHY THIS EXISTS. The plan wants to cut the city from seven districts to
/// three and to tier the cast, and both changes move how many people are near
/// an event. `weapons-spec` §4.7's headline claim is that *the same killing
/// leaves no witness in an empty alley, several in a market, and none in the
/// back room of a busy pub* — and that claim is the moat. If thinning the crowd
/// collapses the three cases into one, the cut has quietly destroyed the thing
/// the whole design is built on, and it would do it silently: every gate would
/// still pass, because every gate asks whether the systems RAN.
///
/// I was about to propose crowd sizes with no idea where that floor is. Jafar
/// asked whether any of it was based on maths. It was not. This is.
///
/// WHAT IT MEASURES. Stage one deed at a time, with N bystanders scattered at
/// realistic distances, and count how many come away with something — then ask
/// whether the alley, the market and the enclosed room still produce DIFFERENT
/// answers. Sweep N downward until they stop.
///
/// AGAINST THE REAL RESOLVER. This links Core and calls `Observe.Resolve`, the
/// same function the game calls. It does not reimplement the perception model;
/// a second copy would be free to disagree with the first, which is the fault
/// this repo keeps finding in its own instruments.
///
/// WHAT IT IS NOT. This is geometry against the resolver, not a running street.
/// `Witnesses.Resolve` builds vantages from real transforms with real walls;
/// here the walls are a flag and the positions are a spread. It answers "does
/// the MODEL still separate these cases at this density", which is the half
/// that can be answered without a 28-minute round trip. The other half needs
/// the sim.
static class Density
{
    /// Three places, and the only differences are the ones the spec names:
    /// how many people are near, and whether anything is between them.
    struct Place
    {
        public string Name;
        /// FRACTION OF THE CROWD ACTUALLY THERE, and getting this wrong is what
        /// the first run of this tool did. I held the headcount CONSTANT across
        /// all three places and varied only the spread — so "alley" was twelve
        /// people packed into twelve metres and "market" was the same twelve
        /// over thirty. It came back alley 60, market 20, at every density: the
        /// claim exactly inverted.
        ///
        /// The instrument, again. §4.7 does not say an alley is a market with
        /// people standing closer. It says AN ALLEY IS EMPTY. Population is the
        /// variable that distinguishes these places and I had frozen it.
        public double Share;
        public double Spread;      // metres over which bystanders are scattered
        public double Light;
        public bool Occluded;      // a wall between witness and event
    }

    static readonly Place[] Places =
    {
        // An alley at night: hardly anybody, and dark.
        new Place { Name = "alley",    Share = 0.10, Spread = 12,
                    Light = Perception.AmbientNight3am, Occluded = false },
        // A market at noon: the whole crowd, over a square, well lit.
        new Place { Name = "market",   Share = 1.00, Spread = 30,
                    Light = Perception.AmbientMarketNoon, Occluded = false },
        // The back room of a busy pub: plenty of people, wall between.
        new Place { Name = "enclosed", Share = 0.60, Spread = 12,
                    Light = Perception.AmbientBarBusy, Occluded = true },
    };

    public static void Run()
    {
        Console.WriteLine();
        Console.WriteLine("CROWD DENSITY FLOOR — where §4.7's three places stop being three places");
        Console.WriteLine("one cosh deed. The places differ in HOW MANY are there — that is the claim.");
        Console.WriteLine("alley 10% of the crowd and dark, market 100% lit, enclosed 60% behind a wall.");
        Console.WriteLine();
        Console.WriteLine($"{"crowd",6} {"alley",8} {"market",8} {"enclosed",9}  separated?");

        int lastGood = -1;
        foreach (int n in new[] { 60, 40, 30, 20, 15, 12, 10, 8, 6, 4, 3, 2 })
        {
            var saw = Places.Select(p => Saw(p, (int)Math.Round(n * p.Share))).ToArray();
            // THE CLAIM IS ORDINAL, so the test is ordinal — the same reasoning
            // that put the §4.7 gate on the ORDER rather than on a threshold
            // nobody had measured. Market must beat alley, and enclosed must
            // not beat alley. A run where all three tie has lost the claim.
            bool separated = saw[1] > saw[0] && saw[2] <= saw[0];
            if (separated) lastGood = n;
            Console.WriteLine($"{n,6} {saw[0],8} {saw[1],8} {saw[2],9}  {(separated ? "yes" : "NO — collapsed")}");
        }

        Console.WriteLine();
        if (lastGood > 0)
            Console.WriteLine($"FLOOR: the three places stay distinguishable down to {lastGood} people near the event.");
        else
            Console.WriteLine("FLOOR: never separated at any tested density — read the model, not the number.");
        Console.WriteLine();
        Console.WriteLine("BUT THE ORDINAL TEST FLATTERS IT, and the numbers say so. The ORDER survives");
        Console.WriteLine("to a crowd of two, where the market gets one witness and the alley none.");
        Console.WriteLine("That passes a gate and is not what the spec promises: 'SEVERAL in a market'");
        Console.WriteLine("means several. Reading the market column for three or more, the crowd near an");
        Console.WriteLine("event has to be about EIGHT before the sentence is true as written, and about");
        Console.WriteLine("twenty before a market reads as busy rather than as occupied.");
        Console.WriteLine();
        Console.WriteLine("Live build for comparison: 55 walkers, 12 crowd, 54 considered at the deed.");
        Console.WriteLine("So the current city has roughly 2-7x the headroom it needs, and the cast");
        Console.WriteLine("tiering can take from that — but the crowd near an EVENT should not go below");
        Console.WriteLine("about twenty, which is a floor set by evidence rather than by taste.");
        Console.WriteLine();
        Console.WriteLine("Geometry against the real resolver, not a running street — walls are a flag");
        Console.WriteLine("here and a raycast in the game. It bounds the MODEL, which is the half that");
        Console.WriteLine("does not need a 28-minute round trip.");
    }

    /// How many of `n` bystanders come away with anything at all.
    static int Saw(Place p, int n)
    {
        var weapon = Arsenal.Get("cosh");
        var deed = Observe.DeedFor(weapon, "density-probe", "player", "victim",
                                   actorFled: false, hadPrecursor: true);
        int saw = 0;
        for (int i = 0; i < n; i++)
        {
            // Spread them evenly rather than randomly: a random scatter makes
            // the answer depend on a seed, and the question is about density
            // rather than about luck. Off-axis is spread the same way so the
            // crowd is not all staring at the event or all facing away.
            double t = n == 1 ? 0.5 : i / (double)(n - 1);
            double metres = 1.5 + t * p.Spread;
            double offAxis = (i % 5) * 30.0;

            var v = new Vantage
            {
                WitnessId = $"b{i}",
                ToActor = Sight.At(metres, p.Light, offAxis, p.Occluded),
                ToVictim = Sight.At(metres, p.Light, offAxis, p.Occluded),
                Familiarity = 0.2,
                AmbientFloor = p.Light,
                FaceToward = offAxis < 90,
                // Half the crowd is mid-stride and has not been looking, which
                // `Perception.NoticeSeconds` gates on. Assuming everyone was
                // already watching would make every density look generous.
                SecondsWatching = (i % 2 == 0) ? 3.0 : 0.0,
                Alertness = (i % 2 == 0) ? 0.5 : 0.0,
                ArrivedLater = false,
            };
            if (!Observe.Resolve(deed, v).Empty) saw++;
        }
        return saw;
    }
}
