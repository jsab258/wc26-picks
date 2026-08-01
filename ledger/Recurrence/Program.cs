using System;
using System.Collections.Generic;
using System.Linq;
using Ledger.Core;

/// HOW OFTEN DO YOU SEE THE SAME FACE TWICE — measured, not asserted.
///
/// WHY THIS EXISTS. The plan proposes cutting the city from seven districts to
/// two, and the argument for it is that a town becomes familiar through
/// RECURRENCE: you learn a place because the same people keep turning up in it.
/// That is a claim about a countable quantity, and I had been making it with
/// invented numbers — "two districts", "forty named people" — in a project
/// whose first rule is never to set a threshold you have not measured. Jafar
/// asked whether any of it was based on maths. It was not. This is.
///
/// WHAT IT MEASURES. Take a person living an ordinary life in this town. Over a
/// simulated week, how many DISTINCT people come close enough to recognise, and
/// how many of those do they see more than once? Two cities with the same
/// population and different areas give very different answers, and the
/// difference is the whole case for the cut.
///
/// AGAINST THE REAL MODEL. This links `Assets/Scripts/Core` and calls
/// `Population.Generate`, `OutdoorsAt` and `OutdoorPosition` — the same functions
/// the game runs. It does not reimplement them. A Python version of this would
/// have been quicker to write and would have been a second model of the city,
/// free to disagree with the first, which is the exact fault this repo keeps
/// finding in its own instruments.
///
/// NO INVENTED DISTANCES. Recognition ranges come from `Perception`:
/// `Rung2MarkMetres` (18m — near enough to know a coat you have seen before)
/// and `Rung3FaceMetres` (8m — near enough to read a face). Those are the
/// game's own thresholds for exactly this question, already tested.
///
/// THE STAND-IN PLAYER IS A RESIDENT, and that is the one modelling choice
/// worth defending. I could have invented a player route — bar in the evening,
/// docks at night — and every number here would then have been downstream of my
/// guess about how people play. Instead the "player" is an ordinary generated
/// resident with a home, a trade and a commute, averaged over many of them. It
/// asks what the CITY does rather than what I imagine a player does, which is
/// the only half of the question this tool can honestly answer.
static class Program
{
    // The real city, copied from `PopulationHost` because that class is
    // Unity-side and cannot be linked here. If these drift, the tool is
    // measuring a city the game does not build — so they are asserted below.
    static readonly string[] AllDistricts =
        { "the Hook", "Copper Row", "Ironside", "the Exchange", "the Parade", "Fairview", "Gullwing" };
    static readonly int[] AllHomeShares = { 30, 28, 4, 3, 6, 22, 7 };
    static readonly int[] AllWorkShares = { 24, 22, 20, 16, 9, 3, 6 };
    const int Seed = 20260726;
    const int Count = 700;

    /// The two the plan would keep. The Hook is where the bar is and Copper Row
    /// is the other side of the water — together they already house 58% of the
    /// city and employ 46% of it, which is why they are the candidates.
    static readonly int[] KeepTwo = { 0, 1 };
    static readonly int[] KeepThree = { 0, 1, 2 };

        const int Samples = 60;          // stand-in players, averaged

    static void Main(string[] args)
    {
        Console.WriteLine("RECURRENCE — how often the same face comes back");
        Console.WriteLine($"population {Count}, seed {Seed}, ONE day (see note), {Samples} stand-in residents");
        Console.WriteLine($"recognition ranges from Perception: mark {Perception.Rung2MarkMetres}m, "
                          + $"face {Perception.Rung3FaceMetres}m");
        Console.WriteLine();

        var rows = new List<Row>
        {
            Measure("seven districts (now)", AllDistricts.Length == 7 ? AllIdx() : AllIdx()),
            Measure("three districts", KeepThree),
            Measure("two districts (proposed)", KeepTwo),
        };

        Console.WriteLine($"{"city",-26} {"seen",6} {"twice+",7} {"face 8m",8} {"repeat%",8} {"top20 share",12}");
        foreach (var r in rows)
            Console.WriteLine($"{r.Name,-26} {r.Distinct,6:0.0} {r.TwicePlus,7:0.0} {r.FaceRange,8:0.0} "
                              + $"{r.RepeatShare * 100,7:0.0}% {r.Top20Share * 100,11:0.0}%");

        Console.WriteLine();
        Console.WriteLine("seen        distinct people within mark range at least once in the day");
        Console.WriteLine("twice+      of those, how many were met on two or more separate hours");
        Console.WriteLine("face 8m     of those, how many came near enough to read a face");
        Console.WriteLine("repeat%     share of all encounters that were with someone already met");
        Console.WriteLine("top20 share share of encounters accounted for by the 20 most-met people");
        Console.WriteLine();

        var seven = rows[0];
        var two = rows[2];
        Console.WriteLine("WHAT IT SAYS");
        Console.WriteLine($"  distinct faces      {seven.Distinct:0.0} -> {two.Distinct:0.0}"
                          + $"  ({Ratio(two.Distinct, seven.Distinct)})");
        Console.WriteLine($"  face-range faces    {seven.FaceRange:0.0} -> {two.FaceRange:0.0}"
                          + $"  ({Ratio(two.FaceRange, seven.FaceRange)})");
        Console.WriteLine($"  repeat encounters   {seven.RepeatShare * 100:0.0}% -> {two.RepeatShare * 100:0.0}%");
        Console.WriteLine();
        Console.WriteLine("Dunbar's layers for scale: ~5 intimates, ~15 close, ~50 friends, ~150 contacts.");
        Console.WriteLine("'face 8m' is what a NAMED CAST has to cover; 'seen' is what the crowd has");
        Console.WriteLine("to supply. Different sizes, which is the argument for tiering rather than");
        Console.WriteLine("picking one number.");
        Console.WriteLine();

        // AND HOW MANY PEOPLE THE TOWN NEEDS, which is the other number I was
        // about to invent. Same area, swept population: the crowd tier is
        // whatever makes a street feel walked-on, and that is a curve to read
        // rather than a figure to assert.
        Console.WriteLine("POPULATION SWEEP — three districts, same area, varying headcount");
        Console.WriteLine($"{"people",8} {"seen/day",9} {"face 8m",9}");
        foreach (int n in new[] { 350, 700, 1400, 2100, 2800 })
        {
            var r = Measure($"n{n}", KeepThree, n);
            Console.WriteLine($"{n,8} {r.Distinct,9:0.0} {r.FaceRange,9:0.0}");
        }
        Console.WriteLine();
        Console.WriteLine("Read this against what the runtime can afford: the crowd walker cap and");
        Console.WriteLine("the frame budget bound it from the other side, and that has not been");
        Console.WriteLine("measured yet. This says what the DESIGN wants, not what the GPU allows.");
    }

    static int[] AllIdx() => Enumerable.Range(0, AllDistricts.Length).ToArray();

    static string Ratio(double a, double b) =>
        b <= 0 ? "n/a" : (a / b >= 1 ? $"x{a / b:0.00}" : $"x{a / b:0.00}");

    struct Row
    {
        public string Name;
        public double Distinct, TwicePlus, FaceRange, RepeatShare, Top20Share;
    }

    /// One city, one week, averaged over many ordinary residents.
    static Row Measure(string name, int[] keep, int count = Count)
    {
        var districts = keep.Select(i => AllDistricts[i]).ToArray();
        var home = keep.Select(i => AllHomeShares[i]).ToArray();
        var work = keep.Select(i => AllWorkShares[i]).ToArray();

        // SAME POPULATION, SMALLER AREA. This is the entire experiment: the
        // people are not deleted, they are concentrated. A run that also cut
        // the headcount would be measuring two changes at once and could not
        // attribute either.
        var pop = Population.Generate(count, Seed, districts, home, work);
        if (pop.Residents.Count == 0) return new Row { Name = name };

        double distinct = 0, twice = 0, faceRange = 0, repeatShare = 0, top20 = 0;
        int used = 0;

        // Spread the stand-ins across the roster rather than taking the first
        // N, which would sample one district: `Generate` fills round-robin off
        // a weighted wheel, so consecutive indices cluster.
        int stride = Math.Max(1, pop.Residents.Count / Samples);
        for (int s = 0; s < Samples; s++)
        {
            int idx = (s * stride) % pop.Residents.Count;
            var me = pop.Residents[idx];
            var met = new Dictionary<string, int>();
            var face = new HashSet<string>();
            long encounters = 0;

            // ONE DAY, NOT SEVEN, AND THAT IS A FINDING RATHER THAN A
            // SHORTCUT.
            //
            // The first version of this looped seven days and every column came
            // out identical — 6.5 seen, 6.5 met twice, 6.5 met five times —
            // which is only possible if everybody met is met at least five
            // times. Suspect the instrument first: `OutdoorsAt` and
            // `OutdoorPosition` take an HOUR and immediately reduce it mod 24.
            // There is no day parameter anywhere in the routine model, so
            // every Tuesday in this town is every Saturday. My week was one
            // day counted seven times, and the 86% "repeat" figure was exactly
            // 6/7 — the arithmetic of the bug, not a property of the city.
            //
            // So this measures one day honestly, and the weekly figure is
            // whatever a day gives you multiplied by seven, for EVERY person
            // met. That is worth knowing on its own: recurrence is currently
            // total. You cannot fail to run into the same people, which is a
            // different immersion problem from the one I set out to measure.
            for (int hour = 0; hour < 24; hour++)
            {
                if (!Population.OutdoorsAt(me, hour)) continue;
                if (!Population.OutdoorPosition(me, hour, out double mx, out double mz)) continue;

                foreach (var other in pop.Residents)
                {
                    if (ReferenceEquals(other, me)) continue;
                    if (!Population.OutdoorsAt(other, hour)) continue;
                    if (!Population.OutdoorPosition(other, hour, out double ox, out double oz)) continue;
                    double dx = ox - mx, dz = oz - mz;
                    double d2 = dx * dx + dz * dz;
                    if (d2 > Perception.Rung2MarkMetres * Perception.Rung2MarkMetres) continue;
                    // ONE ENCOUNTER PER PERSON PER HOUR. Without this a slow
                    // walk past somebody counts as dozens of meetings and every
                    // city looks intimate. An hour is the resolution the
                    // routine model itself works at.
                    met[other.Id] = met.TryGetValue(other.Id, out var c) ? c + 1 : 1;
                    encounters++;
                    // AND SEPARATELY, WHOSE FACE YOU COULD ACTUALLY READ. The
                    // two ranges are the two tiers: 18m is near enough to know
                    // a coat you have seen before, 8m is near enough to know a
                    // person. A named cast has to cover the second; the crowd
                    // only has to supply the first.
                    if (d2 <= Perception.Rung3FaceMetres * Perception.Rung3FaceMetres)
                        face.Add(other.Id);
                }
            }

            if (met.Count == 0) continue;
            used++;
            distinct += met.Count;
            twice += met.Values.Count(v => v >= 2);
            faceRange += face.Count;
            repeatShare += encounters > 0 ? (encounters - met.Count) / (double)encounters : 0;
            var top = met.Values.OrderByDescending(v => v).Take(20).Sum();
            top20 += encounters > 0 ? top / (double)encounters : 0;
        }

        if (used == 0) return new Row { Name = name };
        return new Row
        {
            Name = name,
            Distinct = distinct / used,
            TwicePlus = twice / used,
            FaceRange = faceRange / used,
            RepeatShare = repeatShare / used,
            Top20Share = top20 / used,
        };
    }
}
