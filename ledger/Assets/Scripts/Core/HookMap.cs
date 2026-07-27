using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// The Hook district's place registry — the shared truth between the Tier-2
    /// generator (schedules must reference real places), the world builder
    /// (geometry goes where the registry says), and NPC schedules. Engine-free
    /// on purpose: the generator runs as a plain .NET tool in CI.
    /// Coordinates are the street grid (x, z). Places marked planned:true exist
    /// as data now and get geometry in the district build-out; the original
    /// one-street spots keep their built coordinates.
    public class HookPlace
    {
        public string Id;
        public string Name;
        public double X, Z;
        public string Kind;    // landmark | business | home | corner
        public bool Planned;   // true = geometry arrives with the district build-out
    }

    public static class HookMap
    {
        public static readonly List<HookPlace> Places = new List<HookPlace>
        {
            // The built street (M0 coordinates — do not move).
            P("bar_door",        "the Hook Street bar",       -6,   6, "landmark"),
            P("market_corner",   "the market corner",         10, -14, "business"),
            P("docks",           "the docks",                 18,  14, "landmark"),
            P("apartment_steps", "Ada's apartment steps",    -14,  12, "home"),
            P("north_corner",    "the north corner",          14,  12, "corner"),
            P("south_corner",    "the south corner",          14, -12, "corner"),
            P("west_row",        "the west row",             -16, -12, "home"),
            P("water_homes",     "the homes by the water",    16,  12, "home"),
            P("crossing",        "the crossing",               0,  -8, "corner"),

            // The district (planned; geometry in the build-out).
            P("pawnshop",        "Ruta's pawnshop",          -28,  -6, "business", true),
            P("chapel",          "Father Emil's chapel",     -34,  10, "landmark", true),
            P("ferry_stop",      "the ferry stop",            30,  18, "landmark", true),
            P("cab_rank",        "the cab rank",              24, -10, "corner",   true),
            P("warehouse_row",   "the old warehouse row",    -24, -20, "landmark", true),
            P("fish_market",     "the fish market",           26,   8, "business", true),
            P("boarding_house",  "the boarding house",       -30,   2, "home",     true),
            P("harbor_office",   "the harbormaster's office", 34,   6, "business", true),
            P("laundry",         "the steam laundry",        -22,   8, "business", true),
            P("teahouse",        "the teahouse",             -26,  14, "business", true),
            P("repair_yard",     "the boat repair yard",      28, -16, "business", true),
            P("customs_shed",    "the customs shed",          36,  12, "landmark", true),
            P("tenement_north",  "the north tenements",      -18,  20, "home",     true),
            P("tenement_south",  "the south tenements",      -20, -16, "home",     true),
            P("bakery",          "the corner bakery",        -12, -18, "business", true),

            // COPPER ROW, across the cut: the design doc's immigrant market
            // quarter — dense street life, cash economies, loyalty.
            //
            // Every one of these is somewhere money changes hands in NOTES, which
            // is the point of putting the district here at all: this is where
            // finite purses and Marek's book bite hardest, because nobody on this
            // street keeps their money anywhere you could subpoena it.
            P("covered_market",  "the covered market",         -6, 102, "landmark", true),
            P("weighhouse",      "the weighhouse",            -22, 104, "business", true),
            P("copper_rooms",    "the Copper Row rooms",       10, 100, "home",     true),
            P("money_changer",   "Vasu's money counter",       22, 110, "business", true),
            P("cut_bridge",      "the west bridge",           -26,  92, "corner",   true),
            P("north_market",    "the Northgate market",        4, 126, "business", true),
            P("stair_tenements", "the stair tenements",        34, 118, "home",     true),
            P("letter_stall",    "the letter-writer's stall", -14, 118, "business", true),

            // IRONSIDE, south past the goods yards: warehouses, logistics, and
            // places without witnesses.
            //
            // Every one of these is somewhere goods are HELD rather than sold,
            // which is the opposite of Copper Row and the reason both exist. A
            // market is a hundred people watching money change hands; a bonded
            // store is one clerk, a book, and a door that is shut at six. What
            // the player can do here is not different — who sees them do it is.
            P("goods_yard",      "the goods yard",            -34, -110, "landmark", true),
            P("bonded_store",    "the bonded store",            0, -104, "business", true),
            P("crane_wharf",     "the crane wharf",            34, -100, "landmark", true),
            P("weigh_office",    "the Ironside weigh office",  -6, -132, "business", true),
            P("night_gate",      "the night gate",             17,  -92, "corner",   true),
            P("dry_dock",        "the dry dock",              -40, -148, "landmark", true),
            P("watchmans_hut",   "the watchman's hut",         40, -140, "home",     true),
        };

        static HookPlace P(string id, string name, double x, double z, string kind, bool planned = false) =>
            new HookPlace { Id = id, Name = name, X = x, Z = z, Kind = kind, Planned = planned };

        public static HookPlace Get(string id) => Places.FirstOrDefault(p => p.Id == id);

        /// Rough walkability gate for generated schedules: consecutive stops must
        /// be reachable well inside a time slot at NPC walking speed.
        public const double MaxLegDistance = 90;
    }
}
