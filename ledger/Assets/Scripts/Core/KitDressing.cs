using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Ledger.Core
{
    /// WHAT THE STREET-DRESSING PASS ACTUALLY STOOD UP — the tally the two
    /// Kenney kits' placement writes as it goes, and the whole-run done-line
    /// fragment the verdict prints from it.
    ///
    /// WHY IT EXISTS. `agent-reports/kit-survey.md` found 58 models in
    /// `city-kit-roads` and `city-kit-suburban` that no line of the Game layer
    /// names, and ordered 19 of them placed. Every one of those call sites
    /// falls through to a fallback primitive on a miss, SILENTLY — which is
    /// how `city_kit_*_bench` missed for a week with nothing red. A placement
    /// plan with no counter cannot be verified afterwards (rule 6: ~40 of 61
    /// Core APIs once shipped with no call site at all), so the counter ships
    /// in the same batch as the placement rather than after it.
    ///
    /// IT LIVES IN CORE for the reason `GroundGain` and `Skyline` do, and it
    /// is a standing rule rather than a preference (`.claude/rules/
    /// instruments.md`, 25 Aug, after the third instance): the Game layer does
    /// not compile in this container, so a formatter written there ships
    /// UNRUN, and an unrun formatter printing a plausible string is the
    /// silent-instrument failure this project keeps paying for. The tally, the
    /// arithmetic and the string are here where 3,900 checks run in eight
    /// seconds; the Game layer supplies only membership, order and live state.
    ///
    /// IT IS EMITTED BARE AND MUST NEVER BE WRAPPED IN A KEY. `Line()` returns
    /// TWENTY space-separated `key=value` tokens, not one value, so
    /// `$"kitDressing={Line()}"` produces `kitDressing=kitPlaced=243/320/5/72refused`
    /// — a token with two `=` in it. Every reader in this repo splits on
    /// whitespace and takes the FIRST `=`, so that reader gets `kitDressing`
    /// holding a nonsense value and `kitPlaced` MISSING ENTIRELY. It shipped
    /// that way and was caught before the first landed run
    /// (`agent-reports/kit-dressing-audit.md` C1). The sibling this was
    /// modelled on, `LooseEnds.Line()`, returns ONE value with no `=` in it,
    /// which is why wrapping THAT one is correct — one word, two contracts,
    /// and the wrapper was copied across the gap. `BadTokens()` at the bottom
    /// of this file is the contract as code, and the test runs the wrapped
    /// string through it as its REJECTING case.
    ///
    /// WHAT STATISTIC EVERY NUMBER ON THIS LINE IS: a WHOLE-RUN CUMULATIVE
    /// COUNT, one per call, from the first placement to the last. Not a peak,
    /// not a median, not a last-wins, and not a per-shot number. That sentence
    /// is here because a cumulative count sampled on a SHOT line freezes at
    /// the last screenshot while its per-frame neighbour keeps climbing —
    /// `namesManagedEver` printed 28 ever-managed beside 44 offered in one
    /// frame, which cannot both be true, and it cost an afternoon and a
    /// deleted counter. `Line()` is called ONCE, at the end of the run, on the
    /// done line. Nothing here may be emitted on a screenshot line.
    ///
    /// THE PAIRS ARE PAIRS, NOT TWO KEYS. Every count ships the denominator it
    /// is a fraction OF, in the same value, separated by `/` — `placed/offered
    /// /missed`, `lit/placed`, `metres/samples`. Two keys whose relationship
    /// the reader must remember is how `collidingBubbles=91 bubblesOnScreen=16`
    /// got quoted as a ratio of two different instants four times in one
    /// night. Here there is only one instant — the end of the run — but the
    /// same shape is used anyway, because a reader greping one key out of a
    /// 4KB line must get the denominator with it or not at all.
    ///
    /// THE NAMED KEYS ARE VIEWS OF `kitBy`, NOT SECOND MEASUREMENTS. `signPosts`
    /// is the `sign_post` row of `kitBy` and cannot disagree with it: they are
    /// one variable printed twice, and anybody reading them as corroboration is
    /// reading one number twice (the `pulseMedian`/`uneaseMedian` fault, where
    /// an honest-looking fork turned out to be arithmetic). They are printed
    /// anyway because `tools/gates.py --series` and `--constant` read FLAT
    /// top-level keys: a count living only inside a bracketed row list has no
    /// series and cannot be seen never to have moved.
    ///
    /// A ZERO ON A FLAG KEY IS AMBIGUOUS BY CONSTRUCTION, AND THE DENOMINATOR
    /// THAT RESOLVES IT IS PER FAMILY, IN THE KEY ITSELF. `Flagged` has only a
    /// positive form, so "twelve works lamps and none of them carries a light"
    /// and "nobody wired the `Flagged` call" would both print
    /// `worksLampsWired=0/12`. So they do not: a family that was placed and
    /// recorded NO flag call of any kind prints `nothing-flagged/12`, and
    /// `0/12` is reserved for a family whose flag channel is demonstrably
    /// alive. This is the `soundsAdmitted=0 dropped=0 stolen=0` shape, where
    /// `Admit` returned before any counter moved and silence upstream printed
    /// identically to a working budget.
    ///
    /// THE PARAGRAPH HERE USED TO SEND THE READER TO `kitFlagsBy`'s RUN TOTAL
    /// FOR THAT DENOMINATOR, AND THAT WAS WRONG (audit C10). `kitFlagsBy`'s
    /// `n` counts flag calls across EVERY family, so one live planter channel
    /// made `n` non-zero and thereby certified `worksLampsWired=0/12` as a
    /// finding even if the works-lamp call site had never been written. A
    /// run-total denominator cannot answer a per-family question. It is quoted
    /// rather than deleted because it read as obviously right to everyone who
    /// read it.
    ///
    /// A REFUSAL IS NOT A FLAG AND NOT A MISS — IT IS THE THIRD OUTCOME. A site
    /// the geometry refused (a planter whose footprint lands in the road) filed
    /// only a `Flagged` reason and NO outcome, so `kitPlaced=243/320/5` had
    /// seventy-two sites in a bucket the key did not name: `missed=5` read as
    /// "the prop path is all but perfect" beside an offered count 30% above
    /// placed, which read as the prop path failing, and both readings were
    /// wrong (audit C2). `Refused` is now the third outcome and it carries its
    /// own reason row and its own run total in `kitRefusedBy`. Folding
    /// refusals into `Missed` would have restored the identity and produced a
    /// DIFFERENT wrong conclusion — `plantersPlaced=16/40` with 24 misses reads
    /// as twenty-four planters that failed to load, and nothing failed to load.
    ///
    /// THE TWO WORDS ARE DIFFERENT FACTS. `nothing-offered` means no call ever
    /// named this family: the placer never ran here, and it must not read as a
    /// clean zero (rule 3b — `contrastFailing=0` beside a `ContrastWorst` that
    /// only moves for a failure read as forty labels passing). `nothing-measured`
    /// means the family ran but no scalar arrived. A family that offered sites
    /// and placed nothing prints numbers — `0/12/12/0refused` — and is a
    /// FINDING. `Amount()` collapsed those two words into one for the
    /// never-offered case, which is the one distinction it exists to make
    /// (audit C5); it now returns `nothing-offered` when no call ever named the
    /// family, and `kitAmounts` does the same one level up.
    ///
    /// THE IDENTITY TO READ FIRST is `placed + missed + refused <= offered` on
    /// every `kitBy` row. The placer files a site with `Offered`, then exactly
    /// one of `Placed`/`Missed`/`Refused`. A row whose three outcomes exceed
    /// offered is not a statistic, it is the caller not filing its sites — the
    /// same shape as `GroundGain`'s `admitted + dropped == maskGroundRays`.
    ///
    /// IT SETS NO BOUND AND MUST NOT GROW ONE. This is the printer whose
    /// series a later gate's threshold comes from, in that order (rule 2: a
    /// bound chosen before the series is a rounding wearing a measurement's
    /// clothes). The only bounds in the file are the two ROW CAPS, and both
    /// announce themselves with `+Nmore` every time they bite, because a cap
    /// nobody is told about is indistinguishable from a finding (`| head -3`
    /// on the character audit read as three of five bodies failing when
    /// nothing was broken).
    ///
    /// THE CAP PARAGRAPH HERE USED TO SAY `TailCap` BOUNDED ONLY LISTS THAT
    /// ARE EMPTY IN A HEALTHY RUN. That was false for two of the three lists
    /// it bounded, and the first replay of the live call sites proved it: at
    /// ten distinct flag rows the cap ate `works_lamp/lit` — the row this very
    /// header named as the thing you must read before believing the works-lamp
    /// key — and `yard_fence/in_terrace` with it (audit C10). Per-family rows
    /// are now bounded by `RowCap`, which is DERIVED (`Catalogue.Length +
    /// TailCap`: one row per family the catalogue knows about, plus the same
    /// headroom the unrecognised tails get) rather than chosen, and `TailCap`
    /// bounds only lists keyed by a name the Game layer invented.
    public sealed class KitDressing
    {
        // ---- THE CATALOGUE ------------------------------------------------
        // The families and variants `kit-survey.md` ordered placed, in a fixed
        // ORDINAL order so two runs diff by eye. It lives here rather than
        // being passed in because `Line()` takes no arguments by contract, and
        // because a family that is never mentioned can only print the words
        // `nothing-offered` if something knows it was supposed to exist. A
        // family the Game layer names and this list does not is NOT dropped —
        // it lands in `kitUnknownBy`, which is the only way a typo in a call
        // site reads as a typo rather than as a placer that never ran.
        static readonly string[] Catalogue =
        {
            "lamp",
            "works_cluster",
            "works_cone",
            "works_barrier",
            "works_lamp",
            "sign_post",
            "sign_plate_name",
            "sign_plate_warning",
            "signal_head_secondary",
            "planter",
            "yard_fence",
        };

        /// The six lamp forms of `city-kit-roads`. The survey's proposed key
        /// said `lampVariants=N/5` because `curved` was already standing before
        /// this pass; the DENOMINATOR HERE IS 6, the whole district table
        /// (curved/square x single/double/cross), because the question the key
        /// answers is "did the table branch", and the already-placed form is
        /// part of the branch.
        static readonly string[] LampVariants =
        {
            "curved", "curved_double", "curved_cross",
            "square", "square_double", "square_cross",
        };

        /// Fence run lengths, in kit units of 1x. `Measured` carries the METRES
        /// separately: the variant says which model stood up, the scalar says
        /// how much street it covered, and neither can be derived from the
        /// other.
        static readonly string[] FenceVariants = { "1x1", "1x2", "1x3", "1x4" };

        /// THE ONE STEM `TrafficHost` MOUNTS. Taken from the live call site
        /// (`Placed("signal_head_secondary", "vertical")`) and not from the
        /// brief, which listed this family as having one form: the LIVE
        /// CODEBASE is the accepting fixture, and a stem the catalogue does not
        /// know would otherwise print in the unrecognised tail beside the
        /// typos, which is where a reader stops trusting the tail.
        static readonly string[] HeadVariants = { "vertical" };

        /// The flag strings the named keys read. They are named here, in the
        /// tested layer, so the Game-layer call site has one spelling to match
        /// rather than a remembered one — a flag misspelt at the call site
        /// prints as its own row in `kitFlagsBy` and leaves the named key at
        /// zero, which is exactly the diagnostic pair needed to find it.
        /// A WORKS LAMP CARRIES A POINT LIGHT THAT JOINED THE NIGHT SWEEP.
        ///
        /// IT USED TO BE `FlagLit = "lit"` AND THAT NAME WAS FALSE BY THE TIME
        /// IT WAS FIRST READ. `StreetDressing.Emit` builds the light with
        /// `enabled = false` and hands it to `WorldBuilder.RegisterStreetLight`
        /// — the lamp is BORN DARK and the night sweep owns its state from
        /// there — so `worksLampsLit=18/18` would have been read as "every
        /// works lamp is emitting" when it said nothing whatever about
        /// emission (audit C3). The question moved and the number kept its
        /// name, which is the drift this project has been bitten by three
        /// times in one night.
        ///
        /// WHAT IT DOES AND DOES NOT ANSWER, so nobody has to re-derive it: it
        /// answers "did every placed works lamp get a light rigged into the
        /// registry", which is the half that broke (a Light built outside
        /// `WorldBuilder` kept whatever `enabled` it was born with, because
        /// `SetLampsEnabled` walks `Lamps` and nothing else). It does NOT
        /// answer "are they emitting at night" — that is the sweep's question
        /// and `WorldBuilder.LampSweeps` is where that instrument belongs.
        public const string FlagNightLight = "night_light";
        public const string FlagPainted = "painted";

        /// HOW MANY ROWS KEYED BY A NAME THE GAME LAYER INVENTED a list prints
        /// before it says `+Nmore`. Not a measured threshold and not a gate:
        /// these lists — unrecognised families, unrecognised variants — are
        /// empty in a healthy run, and eight is enough names to find the call
        /// site that produced them while keeping one bad loop from writing a
        /// kilobyte into the done line.
        const int TailCap = 8;

        /// HOW MANY PER-FAMILY ROWS a list prints before it says `+Nmore`, for
        /// the three lists that are NON-EMPTY BY DESIGN in a healthy run:
        /// amounts, flags and refusals.
        ///
        /// DERIVED, NOT CHOSEN, because there is no landed series to set a
        /// number from and a bound invented here would be a rounding wearing a
        /// measurement's clothes (rule 2). One row for every family the
        /// catalogue knows about, plus the same headroom the unrecognised tails
        /// get. `TailCap` was doing this job at 8 and the first replay of the
        /// live call sites printed TEN distinct flag rows, so it bit — on
        /// `works_lamp/lit`, the one row the design says you must read.
        static readonly int RowCap = Catalogue.Length + TailCap;

        const string NothingOffered = "nothing-offered";
        const string NothingMeasured = "nothing-measured";
        const string NothingFlagged = "nothing-flagged";
        /// The numeric slot of an amount row whose scalar is INTENSIVE, where a
        /// sum of the samples is arithmetic nobody can use. See `AmountCell`.
        const string NoSum = "nosum";

        sealed class Fam
        {
            public long Offered, Placed, Missed, Refused, Samples, BadSamples;
            public double Metres;
            /// EVERY SAMPLE, not just the sum. The spread is the half a sum
            /// cannot carry, and two of the three live call sites file an
            /// INTENSIVE quantity here (see `Measured`). A few hundred floats
            /// per run is nothing; being unable to answer "is any lamp the
            /// wrong height" would have cost a build.
            public readonly List<double> Samp = new List<double>();
            public readonly Dictionary<string, long> VarPlaced = new Dictionary<string, long>();
            public readonly Dictionary<string, long> VarMissed = new Dictionary<string, long>();
            public readonly Dictionary<string, long> Flags = new Dictionary<string, long>();
            /// WHY the geometry refused a site, keyed by reason. Kept apart
            /// from `Flags` because they answer different questions and mixing
            /// them made one run total stand as the denominator for both.
            public readonly Dictionary<string, long> Refusals = new Dictionary<string, long>();
        }

        /// WHAT SCALAR EACH CATALOGUE FAMILY FILES THROUGH `Measured`, AND
        /// WHETHER ADDING THEM UP MEANS ANYTHING. Pairs of
        /// `family, kind, "sum"|"nosum"`, read by `AmountCell`.
        ///
        /// IT EXISTS BECAUSE FOUR UNITS SHARED ONE CHANNEL WITH NO LABEL
        /// (audit C4). `lamp` files metres of HEIGHT, `signal_head_secondary`
        /// metres of MOUNT GAP, `yard_fence` metres of RUN, and `planter` filed
        /// square metres of footprint — and every one of them printed into the
        /// same `<sum>/<n>/<bad>bad/<min>..<med>..<max>` cell, where only the
        /// fence's sum meant anything. Summing 41 lamp heights prints 200.20
        /// and reads as metres of lamp.
        ///
        /// SO AN INTENSIVE ROW PRINTS `nosum` IN THE SUM'S SLOT rather than a
        /// number nobody may use, and the kind rides in the row name
        /// (`lamp/height:...`) — which is this project's standing rule that a
        /// number says what it is a statistic OF, applied to the unit.
        static readonly string[] AmountKinds =
        {
            "lamp", "height", NoSum,
            "planter", "height", NoSum,
            "signal_head_secondary", "mountgap", NoSum,
            "yard_fence", "run", "sum",
        };

        readonly Dictionary<string, Fam> _fam = new Dictionary<string, Fam>();

        // ---- WHAT THE PLACER FILES ----------------------------------------

        /// A site where a dressing object COULD stand was offered to the
        /// placer. The DENOMINATOR of everything else on the line: without it,
        /// `plantersPlaced=0` cannot tell "no planter sites exist in the city
        /// plan" from "sixteen sites and the model never loaded", and those
        /// have completely different fixes.
        public void Offered(string family)
        {
            At(family).Offered++;
        }

        /// A kit model stood up. `variant` is the kit stem, or "" when the
        /// family has one form — an empty variant files the family count only
        /// and creates no variant row, so `works_cone` never grows a bogus
        /// one-row breakdown.
        public void Placed(string family, string variant)
        {
            var f = At(family);
            f.Placed++;
            var v = Safe(variant);
            if (v.Length > 0) Bump(f.VarPlaced, v);
        }

        /// The placer fell back to a primitive, or the prop was not found.
        /// THE WHOLE REASON THIS CLASS EXISTS: the fallback is silent in the
        /// frame — a grey box at the right size reads as dressing from ten
        /// metres — so the miss count is the only thing that can say the kit
        /// model is not the thing standing there.
        public void Missed(string family, string variant)
        {
            var f = At(family);
            f.Missed++;
            var v = Safe(variant);
            if (v.Length > 0) Bump(f.VarMissed, v);
        }

        /// THE GEOMETRY REFUSED THE SITE — a planter footprint in the road, a
        /// fence run standing through a terrace, a cone off the carriageway.
        /// The site existed and was offered; nothing was ever asked of the
        /// asset loader, so this is NOT a miss and reading it as one is the
        /// wrong conclusion in the other direction (`plantersPlaced=16/40` with
        /// 24 misses reads as twenty-four planters that failed to load).
        ///
        /// THE OUTCOME AND THE REASON ARE ONE CALL ON PURPOSE. The five live
        /// sites filed `Flagged(...); continue;` and no outcome at all, so the
        /// reason was recorded and the site vanished from the identity. One
        /// idea, two calls, and the one nobody looks at is the one missing a
        /// line — so there is no way to file the reason without filing the
        /// outcome.
        public void Refused(string family, string reason)
        {
            var f = At(family);
            f.Refused++;
            var r = Safe(reason);
            Bump(f.Refusals, r.Length > 0 ? r : "unnamed");
        }

        /// A scalar carried by a placement — metres of fence run, etc. Summed
        /// with its SAMPLE COUNT, because a total alone cannot tell one 12.4m
        /// run from twelve 3.5m ones and the survey asks for exactly that
        /// distinction. A non-finite amount is REFUSED and counted as `bad`
        /// rather than poisoning the sum into `NaN`, which would take the
        /// whole key down with it.
        ///
        /// WHAT THIS IS A STATISTIC OF, AND WHAT IT MUST NOT BE USED FOR: a
        /// CUMULATIVE SUM with its sample count. That is the right statistic
        /// for an EXTENSIVE quantity — metres of fence, tonnes of clutter,
        /// anything where two placements add up. It is the wrong statistic for
        /// an INTENSIVE one: a foot gap, a spacing, a tilt. "Is any planter
        /// hanging in the air" is a max-and-median question and a sum answers
        /// it with the number of planters (`Skyline.Foot` is the shape for
        /// that, worst beside median beside n, and it exists because eight
        /// blocks hung over open sea at foot gap 0.00 exactly). Filing a gap
        /// here would print a large number that grows with the placement count
        /// and means nothing — which is the `armStreetWorst` fault, a worst
        /// that never stops being a median, one aggregation earlier.
        ///
        /// WHICH KIND EACH FAMILY FILES IS DECLARED IN `AmountKinds` AND
        /// PRINTED, because the paragraph above was true and invisible: three
        /// of the four live callers file an intensive quantity and every one of
        /// them printed a sum. An intensive row now prints `nosum`.
        ///
        /// AND A CONSTANT IS NOT A MEASUREMENT. `planter` filed
        /// `2.96f * 2.22f`, which the compiler folds, so sixteen planters filed
        /// sixteen copies of one literal and the spread printed
        /// `6.57..6.57..6.57` — the strongest-looking evidence on the line and
        /// the only cell on it that could not have disagreed with itself
        /// (audit C4). If the caller cannot measure the thing, it must not file
        /// it.
        public void Measured(string family, float amount)
        {
            var f = At(family);
            if (float.IsNaN(amount) || float.IsInfinity(amount)) { f.BadSamples++; return; }
            f.Metres += amount;
            f.Samples++;
            f.Samp.Add(amount);
        }

        /// A boolean property of an already-placed object — a works lamp
        /// carrying a registered light, a nameplate that got lettering.
        /// POSITIVE FORM ONLY: it is called when the property holds and not
        /// called when it does not, so a zero here is ambiguous on its own, and
        /// the denominator that resolves it is THIS FAMILY'S own flag-call
        /// count, printed as the word `nothing-flagged` in the named key. See
        /// the class note; `kitFlagsBy`'s run total cannot do that job and was
        /// documented as though it could.
        ///
        /// NOT FOR A REFUSED SITE. `Refused` is the outcome for that and files
        /// its own reason row; a refusal filed here left the site out of the
        /// identity entirely.
        public void Flagged(string family, string flag)
        {
            var k = Safe(flag);
            Bump(At(family).Flags, k.Length > 0 ? k : "unnamed");
        }

        // ---- THE DONE-LINE FRAGMENT ---------------------------------------

        /// EVERY KEY BELOW IS A WHOLE-RUN CUMULATIVE COUNT, taken at the one
        /// instant this method is called — the end of the run. Space-free by
        /// construction: the verdict is space-separated `key=value` and every
        /// reader in this repo splits on whitespace, so a space inside a value
        /// truncates it silently (`crowdBodyWidth=0.45(narrowest 0.39 broadest
        /// 0.53)` came back as `0.45(narrowest`, with no sign it had been cut).
        /// Structure is carried by `/`, `:` and bracketed lists, all of which
        /// `tools/verdict-read.py` consumes whole.
        public string Line()
        {
            var t = new List<string>();

            // RUN TOTALS — placed/offered/missed/refused over every family,
            // catalogued or not. The one key that says the pass ran at all;
            // everything else is a breakdown of it. ALL FOUR FIELDS, because
            // `243/320/5` left seventy-two geometry refusals in a bucket the
            // key did not name, and `missed=5` beside an offered count 30%
            // higher than placed supports two opposite wrong readings.
            t.Add("kitPlaced=" + Total(f => f.Placed) + "/" + Total(f => f.Offered)
                  + "/" + Total(f => f.Missed) + "/" + Total(f => f.Refused) + "refused");

            // HOW MANY CATALOGUE FAMILIES stood something up / were named by
            // any call, then the catalogue size, then the count of names the
            // catalogue does not know. `5/8/11/0unknown` reads: five catalogue
            // families placed something, eight were mentioned at all, eleven
            // are expected, no name was unrecognised.
            //
            // THE FIRST TWO ARE CATALOGUE-SCOPED, WHICH THEY WERE NOT. They
            // counted ALL families including names the catalogue does not know,
            // against a third field that is catalogue-only — so eleven junk
            // names printed `0/11/11/11unknown`, which reads at a glance as a
            // full house of expected families and is the exact opposite
            // (audit C9). An unrecognised name is counted once, in the field
            // that names it.
            t.Add("kitFamilies=" + N(CatalogueFamiliesWith(f => f.Placed > 0))
                  + "/" + N(CatalogueFamiliesWith(f => true))
                  + "/" + N(Catalogue.Length) + "/" + N(UnknownNames().Count) + "unknown");

            // PER FAMILY, cumulative: `<placed>/<offered>/<missed>/<refused>`,
            // catalogue order. Every catalogue family prints EVERY RUN — a
            // family that vanished from the placement and a family that placed
            // nothing must not print alike, so an unmentioned one prints the
            // words.
            var by = new List<string>();
            foreach (var name in Catalogue) by.Add(name + ":" + FamRow(name));
            t.Add("kitBy=" + Fixed(by));

            // PER VARIANT, cumulative: `<family>/<variant>:<placed>/<missed>`,
            // catalogue order, then any variant the catalogue does not know —
            // capped and announced. A variant missing from the fetch prints
            // `0/0`; a variant that was asked for and never loaded prints
            // `0/N`, and only the second is a broken asset.
            t.Add("kitByVariant=" + FixedPlusTail(CatalogueVariantRows(), UnknownVariantRows()));

            // PER FAMILY SCALARS, cumulative, keyed `<family>/<kind>` so the
            // unit is on the row: `<sum-or-nosum>/<samples>/<bad>bad/
            // <min>..<median>..<max>`. Only families that carried one appear;
            // none at all prints the words — `nothing-offered` when no call
            // named any family, `nothing-measured` when families ran and no
            // scalar arrived, which are different facts.
            t.Add("kitAmounts=" + Tail(AmountRows(),
                  _fam.Count == 0 ? NothingOffered : NothingMeasured, RowCap));

            // PER FAMILY FLAG, cumulative, with the run total of flag CALLS
            // beside it — named `calls` and not `n` because the rows shown can
            // be capped and a reader dividing a shown subset by a full total is
            // the arithmetic that invites. It is not the denominator for a flag
            // zero: that one is per family and lives in the named key.
            t.Add("kitFlagsBy=" + Tail(FlagRows(), NothingFlagged, RowCap)
                  + "/" + N(Total(f => FlagTotal(f))) + "calls");

            // PER FAMILY REFUSAL REASON, cumulative, with the run total of
            // refused SITES beside it. The reasons were in `kitFlagsBy` and the
            // sites were nowhere; both halves of a refusal are here now, and
            // this list plus `kitPlaced`'s fourth field are the same population
            // counted two ways.
            t.Add("kitRefusedBy=" + Tail(RefusedRows(), "nothing-refused", RowCap)
                  + "/" + N(Total(f => f.Refused)) + "sites");

            // NAMES THE CATALOGUE DOES NOT KNOW — a typo at a call site, or a
            // family somebody added here and not there. `[none]` over the count
            // of families this run mentioned at all, so a clean result ships
            // the denominator that proves it examined something.
            t.Add("kitUnknownBy=" + Tail(UnknownRows(), "none", TailCap)
                  + "/" + N(UnknownNames().Count) + "of" + N(_fam.Count));

            // ---- THE SURVEY'S TEN KEYS ------------------------------------
            // Views of the counters above, flat and greppable so
            // `gates.py --series` can carry each one across runs. They cannot
            // disagree with `kitBy`; see the class note.

            // DISTINCT catalogue lamp forms that stood up at least once, over
            // the six the district table can choose from. Not a count of lamps:
            // it answers "did the table branch", which no total can.
            t.Add("lampVariants=" + (_fam.ContainsKey("lamp")
                  ? DistinctPlaced("lamp", LampVariants) + "/" + N(LampVariants.Length)
                  : NothingOffered));

            // PER LAMP FORM `<placed>/<missed>`, then the family's own totals.
            // The row sum and `n` disagree exactly when a lamp was placed under
            // a blank or unrecognised variant, which is the self-check.
            t.Add("lampsByKind=" + VariantList("lamp", LampVariants)
                  + "/n" + PlacedOf("lamp") + "of" + OfferedOf("lamp"));

            t.Add("signPosts=" + PlacedOver("sign_post"));
            t.Add("signPlates=" + PlacedOver("sign_plate_name", "sign_plate_warning"));

            // NAME plates that got lettering, over NAME plates placed. A blank
            // white blade reads as a fault in the frame and nothing else
            // measures it.
            //
            // ONE FAMILY, BECAUSE THE KEY NAMES ONE. It spanned both plate
            // families, numerator and denominator, so unpainted WARNING plates
            // would have diluted a ratio whose name claims name plates only
            // (audit C7's second half). Warning-plate lettering, when somebody
            // builds signage, needs its own key rather than a share of this
            // one.
            t.Add("namePlatesPainted=" + FlagOver(FlagPainted, "sign_plate_name"));

            // Roadworks clusters as SITES, and the props inside them. The
            // cluster is its own family: without it a cluster that placed
            // nothing is invisible, because every prop count would simply be
            // lower and nothing would say how many clusters there were.
            t.Add("worksClusters=" + PlacedOver("works_cluster"));
            t.Add("worksProps=" + PlacedOver("works_cone", "works_barrier", "works_lamp"));

            // Works lamps carrying a point light that joined the night sweep,
            // over works lamps placed. NOT "emitting": the lamp is born dark
            // and the sweep owns its state, so this key answers whether the
            // light was RIGGED, which is the half that broke. See
            // `FlagNightLight`, which was called `lit` and read as the other
            // question.
            t.Add("worksLampsWired=" + FlagOver(FlagNightLight, "works_lamp"));

            // Low secondary heads mounted, over the signal posts that offered a
            // mount. `0/8` is a dead mount path and nothing else would say so.
            t.Add("secondaryHeads=" + PlacedOver("signal_head_secondary"));

            t.Add("yardFenceRuns=" + PlacedOver("yard_fence"));
            t.Add("yardFenceMetres=" + Amount("yard_fence"));
            t.Add("plantersPlaced=" + PlacedOver("planter"));

            return string.Join(" ", t.ToArray());
        }

        // ---- ROWS ---------------------------------------------------------

        string FamRow(string name)
        {
            Fam f;
            if (!_fam.TryGetValue(name, out f)) return NothingOffered;
            return N(f.Placed) + "/" + N(f.Offered) + "/" + N(f.Missed)
                   + "/" + N(f.Refused) + "refused";
        }

        List<string> CatalogueVariantRows()
        {
            var rows = new List<string>();
            AddVariantRows(rows, "lamp", LampVariants);
            AddVariantRows(rows, "signal_head_secondary", HeadVariants);
            AddVariantRows(rows, "yard_fence", FenceVariants);
            return rows;
        }

        /// A family nobody named collapses to ONE worded row rather than six
        /// zeros. Six `lamp/curved:0/0` rows are six zeros with no denominator
        /// in sight, and the reader has to go and find `kitBy` to learn whether
        /// the placer ran at all — which is the archaeology rule 3b exists to
        /// delete.
        void AddVariantRows(List<string> rows, string family, string[] variants)
        {
            Fam f;
            if (!_fam.TryGetValue(family, out f))
            {
                rows.Add(family + ":" + NothingOffered);
                return;
            }
            foreach (var v in variants)
                rows.Add(family + "/" + v + ":" + VarCell(f, v));
        }

        /// Variants named by a call that the catalogue does not list, ordinal
        /// by `<family>/<variant>` so the list is stable between runs.
        List<string> UnknownVariantRows()
        {
            var rows = new List<string>();
            foreach (var kv in Ordered(_fam))
            {
                var known = VariantsOf(kv.Key);
                var seen = new SortedDictionary<string, bool>(System.StringComparer.Ordinal);
                foreach (var v in kv.Value.VarPlaced.Keys) seen[v] = true;
                foreach (var v in kv.Value.VarMissed.Keys) seen[v] = true;
                foreach (var v in seen.Keys)
                {
                    if (Contains(known, v)) continue;
                    rows.Add(kv.Key + "/" + v + ":" + VarCell(kv.Value, v));
                }
            }
            return rows;
        }

        string VarCell(Fam f, string variant)
        {
            long p = 0, m = 0;
            if (f != null)
            {
                f.VarPlaced.TryGetValue(variant, out p);
                f.VarMissed.TryGetValue(variant, out m);
            }
            return N(p) + "/" + N(m);
        }

        List<string> AmountRows()
        {
            var rows = new List<string>();
            foreach (var kv in Ordered(_fam))
                if (kv.Value.Samples > 0 || kv.Value.BadSamples > 0)
                    rows.Add(kv.Key + "/" + AmountKind(kv.Key) + ":" + AmountCell(kv.Key, kv.Value));
            return rows;
        }

        List<string> FlagRows()
        {
            return NamedRows(f => f.Flags);
        }

        List<string> RefusedRows()
        {
            return NamedRows(f => f.Refusals);
        }

        /// ONE WALK FOR BOTH ROW LISTS. They differ only in which dictionary
        /// they read, and two copies of an ordinal walk is the shape where one
        /// of them quietly loses its sort.
        delegate Dictionary<string, long> PickRows(Fam f);

        List<string> NamedRows(PickRows pick)
        {
            var rows = new List<string>();
            foreach (var kv in Ordered(_fam))
            {
                var named = new SortedDictionary<string, long>(System.StringComparer.Ordinal);
                foreach (var fk in pick(kv.Value)) named[fk.Key] = fk.Value;
                foreach (var fk in named)
                    rows.Add(kv.Key + "/" + fk.Key + ":" + N(fk.Value));
            }
            return rows;
        }

        List<string> UnknownRows()
        {
            var rows = new List<string>();
            foreach (var name in UnknownNames()) rows.Add(name + ":" + FamRow(name));
            return rows;
        }

        List<string> UnknownNames()
        {
            var names = new List<string>();
            foreach (var kv in Ordered(_fam))
                if (!Contains(Catalogue, kv.Key)) names.Add(kv.Key);
            return names;
        }

        // ---- THE NAMED VIEWS ----------------------------------------------

        /// `<placed>/<offered>` summed over one or more families, or the words
        /// when NONE of them was ever named. Summed rather than printed per
        /// family where the survey asked one question of several models — the
        /// per-family split is on `kitBy` in the same line, so nothing is lost.
        /// AND OVER SEVERAL FAMILIES IT SHIPS ITS COVERAGE, `<named>of<N>`,
        /// because `any` was true the moment ONE family was present: with only
        /// `works_cone` wired, `worksProps=40/40` was a perfect score for a
        /// roadworks pass that placed no barriers and no lamps, and nothing in
        /// the key said two of its three families were never named (audit C8).
        /// The evidence was in `kitBy`, which a reader quoting a flat key does
        /// not open.
        ///
        /// ONLY FOR MULTI-FAMILY GROUPS. `plantersPlaced=16/40/1of1` is a field
        /// that can never say anything — a single-family key already prints the
        /// words when its family is unnamed. Each key's shape is stable across
        /// runs, which is what a series needs; it is uniformity BETWEEN keys
        /// that is being traded away, and that was never available anyway.
        string PlacedOver(params string[] families)
        {
            long p = 0, o = 0; int named = 0;
            foreach (var name in families)
            {
                Fam f;
                if (!_fam.TryGetValue(name, out f)) continue;
                named++; p += f.Placed; o += f.Offered;
            }
            if (named == 0) return NothingOffered;
            var cell = N(p) + "/" + N(o);
            if (families.Length > 1) cell += "/" + N(named) + "of" + N(families.Length);
            return cell;
        }

        /// `<flagged>/<placed>` over one or more families. The denominator is
        /// what was PLACED, not what was offered: a flag is a property of an
        /// object that exists, so offering a site it never filled cannot dilute
        /// it. Reads `nothing-offered` when no family here was ever named.
        ///
        /// AND `nothing-flagged/<placed>` WHEN THE CHANNEL IS DEAD FOR THESE
        /// FAMILIES, which is the denominator a flag zero needs and the one
        /// this class documented in the wrong place. `Flagged` has a positive
        /// form only, so "twelve works lamps, none of them carries a light" and
        /// "nobody ever wrote the `Flagged` call" both wanted to print
        /// `0/12`. They no longer can: `0/12` means this family recorded flag
        /// calls of SOME kind and not this one — which is the diagnostic pair
        /// that finds a misspelt flag — and the words mean no flag call of any
        /// kind reached it. The class header used to send the reader to
        /// `kitFlagsBy`'s run total for this, which is cross-family and cannot
        /// answer it.
        string FlagOver(string flag, params string[] families)
        {
            long hit = 0, placed = 0, calls = 0; bool any = false;
            foreach (var name in families)
            {
                Fam f;
                if (!_fam.TryGetValue(name, out f)) continue;
                any = true; placed += f.Placed; calls += FlagTotal(f);
                long n;
                if (f.Flags.TryGetValue(flag, out n)) hit += n;
            }
            if (!any) return NothingOffered;
            if (calls == 0) return NothingFlagged + "/" + N(placed);
            return N(hit) + "/" + N(placed);
        }

        /// `<sum>/<samples>/<refused>bad` in whatever unit the caller passed —
        /// metres, for the fence. The sample count is not the placement count
        /// and is not meant to be: they agree only when every placement carried
        /// a scalar, and their disagreement is the finding.
        ///
        /// THE TWO WORDS ARE DIFFERENT FACTS AND THIS METHOD COLLAPSED THEM.
        /// `TryGetValue` failing is the NEVER-OFFERED case — no call ever named
        /// the family — and it returned `nothing-measured`, which means the
        /// family ran and carried no scalar. Those are the two facts this whole
        /// class exists to keep apart, and the one method that had to make the
        /// distinction printed one string for both (audit C5).
        string Amount(string family)
        {
            Fam f;
            if (!_fam.TryGetValue(family, out f)) return NothingOffered;
            if (f.Samples == 0 && f.BadSamples == 0) return NothingMeasured;
            return AmountCell(family, f);
        }

        /// WHAT KIND OF SCALAR A FAMILY FILES, or `unknown` for a name the
        /// catalogue does not list — where the kind genuinely is not known and
        /// saying so is the honest cell.
        static string AmountKind(string family)
        {
            for (int i = 0; i < AmountKinds.Length; i += 3)
                if (AmountKinds[i] == family) return AmountKinds[i + 1];
            return "unknown";
        }

        /// Whether adding this family's samples up produces a number anybody
        /// may quote. Unknown families keep their sum: the kind is printed
        /// beside it, and inventing a refusal for a name nobody declared would
        /// throw away the one reading a typo'd call site can offer.
        static bool AmountSums(string family)
        {
            for (int i = 0; i < AmountKinds.Length; i += 3)
                if (AmountKinds[i] == family) return AmountKinds[i + 2] == "sum";
            return true;
        }

        /// `<sum>/<n>/<bad>bad/<min>..<median>..<max>` — BOTH QUESTIONS ON ONE
        /// ROW, because the callers ask two different ones through one channel
        /// and neither statistic can answer the other's.
        ///
        /// The SUM answers "how much" and is meaningful only for an EXTENSIVE
        /// quantity: metres of fence run add up. The TRIPLE answers "is any of
        /// them wrong" and is the only readable half for an INTENSIVE one: a
        /// lamp's height, a signal head's mount gap. Summing 41 lamp heights
        /// prints 210.42 and means nothing at all — it would read as metres of
        /// lamp, and a reader has no way to tell which kind of quantity a row
        /// is from the number. The min and max are on the row so that
        /// judgement is available without going to the source.
        ///
        /// A MEDIAN CANNOT SEE A TAIL AND A MAX CANNOT SEE A MIDDLE, which is
        /// why all three print. `billboardStale` read median 0.000 and was
        /// called fine with 38 of 57 stale and a worst of 116.9 degrees.
        ///
        /// AND AN INTENSIVE ROW PRINTS `nosum` WHERE THE SUM WOULD GO. The
        /// paragraph above was written, was true, and was invisible: three of
        /// the four live callers file an intensive quantity and every one of
        /// them printed a sum a reader could quote. `AmountKinds` is the table
        /// that decides, and the kind rides in the row name.
        string AmountCell(string family, Fam f)
        {
            var cell = (AmountSums(family)
                        ? f.Metres.ToString("0.00", CultureInfo.InvariantCulture)
                        : NoSum)
                     + "/" + N(f.Samples) + "/" + N(f.BadSamples) + "bad/";
            if (f.Samp.Count == 0) return cell + NothingMeasured;
            var v = new List<double>(f.Samp);
            v.Sort();
            double med = v.Count % 2 == 1
                ? v[v.Count / 2]
                : (v[v.Count / 2 - 1] + v[v.Count / 2]) * 0.5;
            return cell + F(v[0]) + ".." + F(med) + ".." + F(v[v.Count - 1]);
        }

        static string F(double v) { return v.ToString("0.00", CultureInfo.InvariantCulture); }

        string VariantList(string family, string[] variants)
        {
            Fam f;
            if (!_fam.TryGetValue(family, out f)) return "[" + NothingOffered + "]";
            var rows = new List<string>();
            foreach (var v in variants) rows.Add(v + ":" + VarCell(f, v));
            return Fixed(rows);
        }

        string DistinctPlaced(string family, string[] variants)
        {
            Fam f;
            if (!_fam.TryGetValue(family, out f)) return "0";
            int n = 0;
            foreach (var v in variants)
            {
                long p;
                if (f.VarPlaced.TryGetValue(v, out p) && p > 0) n++;
            }
            return N(n);
        }

        /// NAMED `...Of` AND NOT `Placed`/`Offered`, deliberately. Those two
        /// names are the class's PUBLIC verbs, and an overload differing only
        /// in arity is the shape that produced CS0119 in this project — a name
        /// that binds to the wrong member and reads as normal. Two ideas, two
        /// names.
        string PlacedOf(string family)
        {
            Fam f;
            return _fam.TryGetValue(family, out f) ? N(f.Placed) : "0";
        }

        string OfferedOf(string family)
        {
            Fam f;
            return _fam.TryGetValue(family, out f) ? N(f.Offered) : "0";
        }

        // ---- PLUMBING -----------------------------------------------------

        Fam At(string family)
        {
            var k = Safe(family);
            if (k.Length == 0) k = "unnamed";
            Fam f;
            if (!_fam.TryGetValue(k, out f)) { f = new Fam(); _fam[k] = f; }
            return f;
        }

        delegate long Pick(Fam f);

        long Total(Pick pick)
        {
            long n = 0;
            foreach (var kv in _fam) n += pick(kv.Value);
            return n;
        }

        /// CATALOGUE FAMILIES ONLY, so it shares a denominator with
        /// `Catalogue.Length` printed beside it. The version this replaced
        /// walked every family including names the catalogue does not know, and
        /// printed them against a catalogue-only third field.
        int CatalogueFamiliesWith(System.Predicate<Fam> test)
        {
            int n = 0;
            foreach (var name in Catalogue)
            {
                Fam f;
                if (_fam.TryGetValue(name, out f) && test(f)) n++;
            }
            return n;
        }

        static long FlagTotal(Fam f)
        {
            long n = 0;
            foreach (var kv in f.Flags) n += kv.Value;
            return n;
        }

        /// Families in ORDINAL name order. Dictionary order is an arbitrary
        /// winner that changes between runs, and a row list that reshuffles
        /// reads as a world that changed — the tie-break `GroundGain.TopMat`
        /// exists for, one layer up.
        static SortedDictionary<string, Fam> Ordered(Dictionary<string, Fam> src)
        {
            var s = new SortedDictionary<string, Fam>(System.StringComparer.Ordinal);
            foreach (var kv in src) s[kv.Key] = kv.Value;
            return s;
        }

        static string[] VariantsOf(string family)
        {
            if (family == "lamp") return LampVariants;
            if (family == "yard_fence") return FenceVariants;
            if (family == "signal_head_secondary") return HeadVariants;
            return EmptyNames;
        }

        static readonly string[] EmptyNames = new string[0];

        static bool Contains(string[] set, string name)
        {
            for (int i = 0; i < set.Length; i++) if (set[i] == name) return true;
            return false;
        }

        static void Bump(Dictionary<string, long> d, string k)
        {
            long n;
            d[k] = (d.TryGetValue(k, out n) ? n : 0) + 1;
        }

        /// A FIXED list — the catalogue — printed whole. Never capped: a cap
        /// here would hide a family that exists, which is the one thing the
        /// catalogue is for.
        static string Fixed(List<string> rows)
        {
            if (rows.Count == 0) return "[" + NothingOffered + "]";
            return "[" + string.Join(",", rows.ToArray()) + "]";
        }

        /// AN UNBOUNDED list — anything keyed by a name the Game layer chose.
        /// Capped and it says so when it bites. `empty` is the WORD printed
        /// when there is nothing, so an empty bracket can never be mistaken for
        /// a list that was cut short.
        ///
        /// THE CAP IS AN ARGUMENT BECAUSE THERE ARE TWO OF THEM AND ONE WAS
        /// DOING BOTH JOBS. `TailCap` (8) bounds lists of invented names, which
        /// are empty in a healthy run; `RowCap` bounds the per-family lists,
        /// which are not. At eight the shared cap ate `works_lamp/lit` off a
        /// ten-row healthy replay.
        static string Tail(List<string> rows, string empty, int cap)
        {
            if (rows.Count == 0) return "[" + empty + "]";
            var sb = new StringBuilder("[");
            int shown = rows.Count < cap ? rows.Count : cap;
            for (int i = 0; i < shown; i++)
            {
                if (i > 0) sb.Append(',');
                sb.Append(rows[i]);
            }
            if (rows.Count > shown) sb.Append(",+").Append(N(rows.Count - shown)).Append("more");
            return sb.Append(']').ToString();
        }

        /// The catalogue rows in full, then the unrecognised ones capped. Both
        /// in one value because they answer one question — what forms stood up
        /// — and splitting them into two keys is the shape this file's header
        /// argues against.
        static string FixedPlusTail(List<string> fixedRows, List<string> tailRows)
        {
            var all = new List<string>(fixedRows);
            int over = 0;
            for (int i = 0; i < tailRows.Count; i++)
            {
                if (i < TailCap) all.Add(tailRows[i]); else over++;
            }
            if (all.Count == 0) return "[" + NothingOffered + "]";
            var s = "[" + string.Join(",", all.ToArray());
            if (over > 0) s += ",+" + N(over) + "more";
            return s + "]";
        }

        static string N(long v) { return v.ToString(CultureInfo.InvariantCulture); }
        static string N(int v) { return v.ToString(CultureInfo.InvariantCulture); }

        /// A FAMILY, VARIANT OR FLAG NAME MAY BE ANYTHING — it is a string the
        /// Game layer chose, and one of them will eventually come off an asset
        /// filename. The verdict is space-separated `key=value`, the row lists
        /// are comma-separated inside brackets, and these rows already use `:`,
        /// `/` and `+` structurally. `crowdBodyWidth` cost a reading by emitting
        /// a single space; this is the same fault waiting in a field nobody
        /// validates.
        ///
        /// IT IS AN ALLOW-LIST, AND THAT IS THE OPPOSITE OF THE SHAPECHECK ONE.
        /// The first version listed the characters to FOLD, and it shipped
        /// blind to `(` — `1x2 (Instance)` came through as `1x2_(instance)`,
        /// which `tools/verdict-read.py`'s lint refuses whenever the closing
        /// paren is the thing that got cut. A deny-list silently passes every
        /// structural character nobody thought of, which is exactly the
        /// ShapeCheck fault (`CS1003` discarded by a set of ids somebody
        /// thought to add). The direction is what differs: an allow-list over
        /// DIAGNOSTICS discards findings, and an allow-list over an output
        /// ALPHABET can only over-fold, whose failure mode is a visibly
        /// mangled name rather than a silently broken line.
        ///
        /// UNITY'S ` (Instance)` SUFFIX IS NOT STRIPPED, unlike its twin in
        /// `GroundGain.Safe`. There it is noise on a material name that
        /// genuinely belongs to an instance; here the caller is supposed to
        /// pass a KIT STEM, so a clone suffix arriving at all is a call-site
        /// fault and hiding it would delete the evidence. The two are separate
        /// normalisations on purpose and neither is a copy of the other — but
        /// they are one IDEA with two implementations, which is the shape this
        /// project keeps getting bitten by, and unifying them means changing
        /// `GroundGain`'s pinned expectations with its tests in hand.
        static string Safe(string name)
        {
            if (string.IsNullOrEmpty(name)) return "";
            var n = name.Trim().ToLowerInvariant();
            var sb = new StringBuilder(n.Length);
            for (int i = 0; i < n.Length; i++)
            {
                char c = n[i];
                bool keep = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
                            || c == '_' || c == '-' || c == '.' || c == '#';
                sb.Append(keep ? c : '_');
            }
            return sb.ToString().Trim('_');
        }

        /// EVERY WAY A DONE-LINE FRAGMENT BREAKS THE READER CONTRACT, named, or
        /// an empty list — with `walked`, the count of tokens examined, so a
        /// clean result cannot be confused with a walk that examined nothing
        /// (rule 3b: `lint-static: 0 static/instance errors` was a walker that
        /// entered no method bodies at all).
        ///
        /// IT LIVES HERE RATHER THAN IN THE TEST BECAUSE THE TEST'S COPY COULD
        /// NOT SEE THE FAULT IT WAS WRITTEN FOR. The sweep was a loop inside
        /// `TestKitDressing` over a hand-listed array of seven of the ten lines
        /// the test builds, and the three it left out were the three least
        /// ordinary strings in the file — the typo case, the only line carrying
        /// a `+Nmore` cap, and the blank-family case (audit C11). Worse, the
        /// fault it was written for — a token with two `=` in it — is made by
        /// the GAME layer's wrapper and never appeared in any string the test
        /// walked: the guard and the fault were one line of C# apart and in
        /// different files. A checker that takes a string can be pointed at the
        /// wrapped form, and the test points it there as its rejecting case.
        ///
        /// THE CONTRACT: space-separated tokens, each a `key=value` with the
        /// key a bare identifier and exactly one `=`; brackets and parentheses
        /// balanced inside the value, which is what `tools/verdict-read.py`
        /// refuses on. It is deliberately not a parse — `verdict-read.py` takes
        /// the FIRST `=`, so a second one does not fail to parse, it silently
        /// returns the wrong thing, and that is the whole reason to check.
        /// INTERNAL, NOT PUBLIC, AND THAT IS THE HONEST VISIBILITY. Nothing in
        /// the Game layer should call this — it is the reader contract as code,
        /// for the layer where tests run, and `CoreTests` compiles these
        /// sources into its own assembly so `internal` reaches it. A `public`
        /// one was a tested Core API with no caller in Game, which
        /// `tools/reach-check.sh` reports as "built is not running" and is
        /// right to: rule 6 does not have an exception for instruments.
        internal static List<string> BadTokens(string fragment, out int walked)
        {
            walked = 0;
            var bad = new List<string>();
            if (string.IsNullOrEmpty(fragment)) { bad.Add("empty fragment"); return bad; }
            foreach (var tok in fragment.Split(' '))
            {
                walked++;
                if (tok.Length == 0) { bad.Add("empty token (a double space)"); continue; }
                var eq = tok.IndexOf('=');
                if (eq <= 0 || eq >= tok.Length - 1) { bad.Add("not key=value: " + tok); continue; }
                if (tok.IndexOf('=', eq + 1) >= 0)
                    bad.Add("two `=` in one token, so every reader that splits on the first one "
                            + "returns a nonsense value and loses the real key: " + tok);
                var key = tok.Substring(0, eq);
                foreach (var ch in key)
                    if (!char.IsLetter(ch)) { bad.Add("key is not a bare identifier: " + key); break; }
                var val = tok.Substring(eq + 1);
                int open = 0, close = 0, po = 0, pc = 0;
                foreach (var ch in val)
                {
                    if (ch == '[') open++;
                    if (ch == ']') close++;
                    if (ch == '(') po++;
                    if (ch == ')') pc++;
                }
                if (open != close || po != pc)
                    bad.Add("unbalanced delimiter, which verdict-read.py refuses: " + tok);
            }
            return bad;
        }
    }
}
