namespace Ledger.Core
{
    /// HOW WELL SOMEBODY KNOWS THE PLAYER BY SIGHT.
    ///
    /// WHY THIS EXISTS. `Perception.IdRung` has five rungs and the top one —
    /// *"that's Tom, runs the pub"* — is gated on `familiarity >=
    /// RecognitionFamiliarity`. It is the rung the whole design turns on: the
    /// difference between the street knowing a crime happened and the street
    /// knowing WHO, which is the consequence engine's only real input.
    ///
    /// It has never once been reachable. `Witnesses.Resolve` takes a
    /// `Func&lt;NpcWalker,double&gt;` for familiarity; `ViolenceHost.Commit`
    /// takes one and passes it through; and **no caller anywhere has ever
    /// supplied one**, so it defaults to null, every witness scores 0.0, and
    /// every person in the city is a stranger to a man they have known for
    /// three acts. The run says it plainly and has for weeks:
    /// `deedBestRung=1` — silhouette — across four staged deeds and
    /// forty-nine witnesses. Rule 6, in its purest form: built, tested in
    /// Core, and never called.
    ///
    /// WHY IT IS A LADDER AND NOT A MEASUREMENT. Rule 2 forbids inventing a
    /// threshold, and this is deliberately not one. There is exactly one
    /// threshold in play and it already exists and is already justified:
    /// `Perception.RecognitionFamiliarity` at 0.35. What this type does is
    /// name the cases the game can actually distinguish and put each on the
    /// correct side of that line — which is an authoring decision about
    /// fiction, not a number read off an instrument, and pretending otherwise
    /// would be worse than saying so.
    ///
    /// The ordering is the part that carries meaning, and it is what the tests
    /// assert. The absolute values are only ever compared against 0.35 and
    /// against each other.
    public static class Acquaintance
    {
        /// A face in the crowd. Cannot name you at any distance, in any light,
        /// however long they stare — which is correct, and is what makes a
        /// busy street safer than an empty one where your neighbour lives.
        public const double Stranger = 0.0;

        /// Somebody who has heard of you but has never had you pointed out.
        /// Deliberately BELOW recognition: gossip travels further than faces
        /// do, and a man who has heard about the warehouse still cannot pick
        /// you out of a bus queue. This is the rung the rumour system needs to
        /// stay honest — otherwise talk alone would let the whole city
        /// identify you, and the game's central tension would evaporate.
        public const double HeardOfYou = 0.20;

        /// Somebody the player has actually dealt with: a named character in
        /// the social graph, a shopkeeper, a face from the ring. Above
        /// recognition, because being able to say your name is the entire
        /// definition of this rung.
        public const double Known = 0.50;

        /// Crew, a companion, anybody who walks where you walk. They know your
        /// gait from behind in the dark, which is exactly the case
        /// `Rung4RecogniseMetres` is written for — recognition at
        /// twenty-five metres, with no face visible.
        public const double Close = 0.80;

        /// Family. There is no distance in this game at which your own
        /// household fails to know you.
        public const double Household = 1.00;

        /// The ladder, resolved from the facts a caller can actually supply.
        ///
        /// Ordered most-binding first, because these overlap in reality: a
        /// companion is also in the social graph, and family have certainly
        /// heard of you. Taking the strongest true statement is what a person
        /// does.
        public static double Of(bool sharesYourHome, bool walksWithYou,
                                bool inTheSocialGraph, bool hasHeardOfYou)
        {
            if (sharesYourHome) return Household;
            if (walksWithYou) return Close;
            if (inTheSocialGraph) return Known;
            if (hasHeardOfYou) return HeardOfYou;
            return Stranger;
        }

        /// Whether this much acquaintance carries a name. One place to ask, so
        /// a caller cannot drift from `Perception`'s constant by copying the
        /// comparison — which is how `RestArmDrop` and `LiveArmDrop` nearly
        /// ended up measuring two different angles on the same night.
        public static bool CanNameYou(double familiarity) =>
            familiarity >= Perception.RecognitionFamiliarity;
    }
}
