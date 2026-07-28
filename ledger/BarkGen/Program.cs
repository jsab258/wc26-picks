using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Ledger.Core;

/// BARK ENUMERATION — step 1 of the bark bank
/// (production-plan-audio-art.md §2b).
///
/// The point of this program is that the list of things the street can say
/// is NOT a design document. It is a property of the code: `StreetVoice`
/// branches on real state, and every branch it can reach is a slot that
/// needs lines. Writing that list by hand produces a list that is wrong the
/// day somebody adds a branch.
///
/// So this walks the actual state space, drives the real `StreetVoice`
/// functions with it, and reports what came out. Two things fall out of
/// that which a hand-written list could not give:
///
///   1. UNREACHABLE SLOTS. A branch nothing can produce is content nobody
///      will ever hear, and it is invisible until something enumerates.
///   2. THE REPETITION FIGURE. Not "does this slot have lines" but "how
///      many seconds of play before the player hears one twice", which is
///      the number that actually decides whether a street sounds alive.
///
/// Run:  dotnet run --project BarkGen -- [outfile]
///
/// It writes barks.json — the manifest the generation step fills in, and
/// the thing a human curation pass reads.
static class Program
{
    // How often each family of line is actually spoken, from the code that
    // schedules it. These are what turn a line count into a repeat interval.
    const double RecognitionEverySeconds = 45;    // GossipDirector._lastBark
    const double AmbientTypicalSeconds = 13;      // StreetVoice.AmbientEverySeconds, busy street
    const double GreetingPerDay = 1;              // GameController._barkDay

    /// A player should not hear the same line twice inside this. Ten minutes
    /// is generous; the ear notices a repeat long before that when the line
    /// is distinctive.
    const double RepeatFloorSeconds = 600;

    /// Far past any plausible bank size. Pick() is `seed % length`, so a
    /// sweep shorter than the longest bank silently under-reports it.
    const int SeedSweep = 200;

    static int Main(string[] args)
    {
        var slots = new List<Slot>();
        slots.AddRange(EnumerateExchange());
        slots.AddRange(EnumerateRecognition());
        slots.AddRange(EnumerateAmbient());
        slots.AddRange(EnumerateStanceReachability());

        Console.WriteLine("LEDGER — bark enumeration\n");
        Console.WriteLine($"{slots.Count} slot(s) the simulation can actually reach.\n");

        var thin = new List<Slot>();
        foreach (var group in slots.GroupBy(s => s.Family))
        {
            Console.WriteLine($"{group.Key}");
            foreach (var s in group.OrderBy(s => s.Id))
            {
                double repeat = s.EverySeconds * s.Lines.Count;
                // A slot at its cap is DONE even if the arithmetic still says
                // three minutes: past fourteen variants the answer is to vary
                // the state that picks the band, not to write a fifteenth way
                // of saying "cold one". Flagging it forever would train
                // whoever reads this to ignore the flag.
                bool short_ = s.Lines.Count < s.Wanted;
                string flag = s.Lines.Count == 0 ? "  EMPTY"
                    : short_ ? $"  repeats every {repeat:0}s, wants {s.Wanted}" : "";
                if (short_ || s.Lines.Count == 0) thin.Add(s);
                Console.WriteLine($"  {s.Id,-38} {s.Lines.Count,3} line(s){flag}");
            }
            Console.WriteLine();
        }

        Console.WriteLine(thin.Count == 0
            ? $"Every slot clears the repeat floor of {RepeatFloorSeconds:0}s."
            : $"{thin.Count} slot(s) short of the repeat floor of {RepeatFloorSeconds:0}s.");
        int wantTotal = slots.Sum(s => s.Wanted);
        int have = slots.Sum(s => s.Lines.Count);
        Console.WriteLine($"{have} line(s) written, {wantTotal} wanted — {wantTotal - have} to author.\n");

        var path = args.Length > 0 ? args[0] : "barks.json";
        File.WriteAllText(path, Manifest(slots));
        Console.WriteLine($"manifest: {Path.GetFullPath(path)}");
        return 0;
    }

    // -----------------------------------------------------------------
    // the state walks
    // -----------------------------------------------------------------

    /// Two people trading a rumour. The teller branches on CONFIDENCE; the
    /// hearer branches on their own disposition. Walked as a grid rather
    /// than as a list of branches, so a branch that no combination of state
    /// can reach shows up as a slot with no lines in it.
    static IEnumerable<Slot> EnumerateExchange()
    {
        var tell = new Dictionary<string, HashSet<string>>();
        var answer = new Dictionary<string, HashSet<string>>();
        var exchangePairs = new Dictionary<string, HashSet<string>>();

        foreach (double conf in Grid(0.05, 1.0, 0.05))
        foreach (double nerve in Grid(0, 1, 0.1))
        foreach (double loyalty in Grid(0, 1, 0.1))
        foreach (double greed in Grid(0, 1, 0.1))
        foreach (bool sensitive in new[] { false, true })
        {
            var from = Agent("from");
            var r = new Rumor
            {
                Content = new Fact("player", "location_d2_evening", "the warehouse"),
                Summary = "the new owner was at the warehouse on Tuesday",
                Confidence = conf, Sensitive = sensitive, OriginId = "from",
            };
            // Seeded well past any plausible bank size, so every alternative
            // in a Pick() is reached. A single seed would report one line per
            // branch and call the bank full; twelve seeds silently capped
            // every bank at twelve and reported fourteen-line banks as
            // twelve, which is the enumerator lying about the thing it exists
            // to measure.
            for (int seed = 0; seed < SeedSweep; seed++)
            {
                var to = Agent("to" + (seed % 11));
                to.Nerve = nerve; to.Loyalty = loyalty; to.Greed = greed;
                var lines = StreetVoice.Exchange(r, from, to, seed);
                if (lines.Count != 2) continue;
                Add(tell, TellBand(conf), lines[0].Text);
                Add(answer, AnswerBand(to, sensitive), lines[1].Text);
                Add(exchangePairs, TellBand(conf) + "_" + AnswerBand(to, sensitive),
                    lines[0].Text + " || " + lines[1].Text);
            }
        }

        foreach (var kv in tell)
            yield return new Slot($"exchange.tell.{kv.Key}", "OVERHEARD — one person telling another",
                kv.Value, AmbientTypicalSeconds,
                $"Somebody passing on a rumour they hold at {kv.Key} confidence. "
                + "The line must carry the story itself, because a player in "
                + "earshot LEARNS it from hearing this.");
        foreach (var kv in answer)
            yield return new Slot($"exchange.answer.{kv.Key}", "OVERHEARD — the hearer's reply",
                kv.Value, AmbientTypicalSeconds,
                $"The reply of somebody who is {kv.Key}. This is character, not "
                + "acknowledgement — the same news lands differently on a "
                + "frightened man and a greedy one.");
        foreach (var kv in exchangePairs)
            yield return new Slot($"exchange.pair.{kv.Key}", "DISTINCT CONVERSATIONS (telling x reply)",
                kv.Value, AmbientTypicalSeconds,
                "A COUNT, not a bank. Two banks welded together by one seed "
                + "give n conversations, not n squared, however many lines "
                + "each holds.");
    }

    static string TellBand(double conf) =>
        conf >= 0.8 ? "certain" : conf >= 0.5 ? "secondhand" : "doubtful";

    static string AnswerBand(Gossiper to, bool sensitive) =>
        to.Nerve > 0.65 && sensitive ? "nervous"
        : to.Loyalty > 0.65 ? "loyal"
        : to.Greed > 0.65 ? "greedy" : "neutral";

    /// Said as the player walks past, by somebody holding a story. Branches
    /// on the stance ladder — which is itself computed from state, so this
    /// walk drives Stance rather than passing stances in by hand.
    static IEnumerable<Slot> EnumerateRecognition()
    {
        var by = new Dictionary<string, HashSet<string>>();
        foreach (double susp in Grid(0, 1, 0.05))
        foreach (double loyalty in Grid(0, 1, 0.1))
        foreach (double strongest in Grid(0, 1, 0.1))
        foreach (bool leashed in new[] { false, true })
        foreach (bool coat in new[] { false, true })
        foreach (bool sensitive in new[] { false, true })
        {
            var stance = StreetVoice.Stance(susp, loyalty, strongest, leashed, coat);
            if (stance < StanceKind.Comments) continue;
            var g = Agent("g");
            var about = strongest > 0 ? new Rumor
            {
                Content = new Fact("player", "night_job_d5", "true"),
                Summary = "the new owner was out at three in the morning",
                Confidence = strongest, Sensitive = sensitive,
            } : null;
            for (int seed = 0; seed < SeedSweep; seed++)
            {
                var line = StreetVoice.Recognition(g, about, stance, seed);
                if (line != null) Add(by, RecognitionBand(stance, about), line.Text);
            }
        }
        foreach (var kv in by)
            yield return new Slot($"recognition.{kv.Key}", "AS YOU PASS — somebody who holds a story",
                kv.Value, RecognitionEverySeconds,
                "Short, pointed, and STOPPABLE — the player can turn round and "
                + "ask what they meant, so it must invite that rather than close it off.");
    }

    static string RecognitionBand(StanceKind s, Rumor about) =>
        s >= StanceKind.Confronts ? "confronts"
        : s == StanceKind.Refuses ? "refuses"
        : s == StanceKind.Avoids ? "avoids"
        : about != null && about.Sensitive ? "comments_sensitive" : "comments_plain";

    /// The city talking about ITSELF. This is the half that makes the place
    /// feel like it existed before the player arrived, and the half a player
    /// hears most often — so it is where repetition hurts first.
    static IEnumerable<Slot> EnumerateAmbient()
    {
        var open = new Dictionary<string, HashSet<string>>();
        var reply = new Dictionary<string, HashSet<string>>();
        // Distinct PAIRS, not distinct lines. What a listener experiences is
        // a conversation, and two fourteen-line banks welded together by
        // `seed + 1` give fourteen conversations rather than a hundred and
        // ninety-six. Counting lines cannot see that; counting pairs can.
        var pairs = new Dictionary<string, HashSet<string>>();

        foreach (int hour in Enumerable.Range(0, 24))
        foreach (double prosperity in Grid(0, 1, 0.1))
        foreach (double price in Grid(0.8, 1.4, 0.05))
        foreach (bool injured in new[] { false, true })
        foreach (bool feud in new[] { false, true })
        {
            var now = new GameTime(4, hour, 0);
            // The replier's identity is now half the input, so a walk that
            // uses one neighbour under-reports the bank exactly the way a
            // single seed did.
            for (int seed = 0; seed < SeedSweep; seed++)
            {
                var a = Agent("a" + (seed % 7));
                var b = Agent("b" + (seed % 11));
                var lines = StreetVoice.Ambient(a, b, now, prosperity, price, injured, feud, seed);
                if (lines.Count != 2) continue;
                string band = AmbientBand(hour, prosperity, price, injured, feud);
                Add(open, band, lines[0].Text);
                Add(reply, band, lines[1].Text);
                Add(pairs, band, lines[0].Text + " || " + lines[1].Text);
            }
        }

        foreach (var kv in open)
            yield return new Slot($"ambient.open.{kv.Key}", "THE CITY ABOUT ITSELF — opener",
                kv.Value, AmbientTypicalSeconds, AmbientBrief(kv.Key));
        foreach (var kv in reply)
            yield return new Slot($"ambient.reply.{kv.Key}", "THE CITY ABOUT ITSELF — reply",
                kv.Value, AmbientTypicalSeconds, AmbientBrief(kv.Key) + " The answer, not a new subject.");
        foreach (var kv in pairs)
            yield return new Slot($"ambient.pair.{kv.Key}", "DISTINCT CONVERSATIONS (opener x reply)",
                kv.Value, AmbientTypicalSeconds,
                "Not a bank to write — a COUNT. Two banks of n welded together "
                + "by a fixed offset give n conversations, not n squared, and "
                + "writing more lines does not fix it.");
    }

    static string AmbientBand(int hour, double prosperity, double price, bool injured, bool feud) =>
        feud ? "feud"
        : injured ? "injured"
        : price > 1.12 ? "prices"
        : prosperity < 0.35 ? "slump"
        : (hour >= 21 || hour < 5) ? "night" : "ordinary";

    static string AmbientBrief(string band) => band switch
    {
        "feud" => "Two people who are not speaking, speaking. Short. Nobody explains.",
        "injured" => "Somebody whose wound is not healing, and cannot afford to have it seen to.",
        "prices" => "The cost of living, going up, with nobody willing to say why.",
        "slump" => "A quiet street and everybody counting the weeks.",
        "night" => "Two people out at an hour that needs no explaining but gets one anyway.",
        _ => "Weather, family, the landlord, Thursday. Nothing about the player. "
             + "THIS IS THE MOST-HEARD LINE FAMILY IN THE GAME — it needs the "
             + "deepest bank and the most ordinary writing.",
    };

    /// Not lines: a check that the ladder is reachable at all. A stance no
    /// state can produce is a feature nobody will see, and the only way to
    /// know is to try every combination.
    static IEnumerable<Slot> EnumerateStanceReachability()
    {
        var reached = new HashSet<StanceKind>();
        foreach (double susp in Grid(0, 1, 0.02))
        foreach (double loyalty in Grid(0, 1, 0.05))
        foreach (double strongest in Grid(0, 1, 0.05))
        foreach (bool leashed in new[] { false, true })
        foreach (bool coat in new[] { false, true })
            reached.Add(StreetVoice.Stance(susp, loyalty, strongest, leashed, coat));

        foreach (StanceKind s in Enum.GetValues(typeof(StanceKind)))
            if (!reached.Contains(s))
                yield return new Slot($"UNREACHABLE.stance.{s}", "!! DEAD BRANCH",
                    new HashSet<string>(), double.MaxValue,
                    $"No combination of suspicion, loyalty, rumour confidence, leash "
                    + $"or coat produces {s}. Either the thresholds are wrong or the "
                    + $"stance should not exist.");
    }

    // -----------------------------------------------------------------

    class Slot
    {
        public string Id, Family, Brief;
        public HashSet<string> Lines;
        public double EverySeconds;
        public int Wanted;

        public Slot(string id, string family, HashSet<string> lines, double every, string brief)
        {
            Id = id; Family = family; Lines = lines; EverySeconds = every; Brief = brief;
            // What it would take to clear the repeat floor, capped so a rare
            // line does not demand a novel. Asking for forty variants of
            // "Whatever it is, no." is how a bank becomes filler.
            Wanted = every >= 1e6 ? 0
                : Math.Max(lines.Count, Math.Min(14, (int)Math.Ceiling(RepeatFloorSeconds / every)));
        }
    }

    static string Manifest(List<Slot> slots)
    {
        var root = new Dictionary<string, object>
        {
            { "generatedBy", "BarkGen — enumerated from Core/StreetVoice.cs, not authored by hand" },
            { "repeatFloorSeconds", RepeatFloorSeconds },
            { "slots", slots.Select(s => (object)new Dictionary<string, object>
                {
                    { "id", s.Id },
                    { "family", s.Family },
                    { "brief", s.Brief },
                    { "everySeconds", s.EverySeconds >= 1e6 ? -1 : s.EverySeconds },
                    { "wanted", s.Wanted },
                    { "have", s.Lines.Count },
                    { "lines", s.Lines.OrderBy(x => x).Cast<object>().ToList() },
                }).ToList() },
        };
        return MiniJson.Serialize(root);
    }

    static Gossiper Agent(string id) =>
        new Gossiper(id, id, new MemoryStore(id), new KnowledgeBase(), new SuspicionTracker());

    static IEnumerable<double> Grid(double from, double to, double step)
    {
        for (double v = from; v <= to + 1e-9; v += step) yield return v;
    }

    static void Add(Dictionary<string, HashSet<string>> d, string key, string line)
    {
        if (string.IsNullOrEmpty(line)) return;
        if (!d.TryGetValue(key, out var set)) d[key] = set = new HashSet<string>();
        set.Add(line);
    }
}
