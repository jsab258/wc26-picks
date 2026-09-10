using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// D18, THE CONTENT RULE, AT THE ONE ENFORCEMENT SITE THAT IS CODE.
    ///
    /// canon.md, section "The content rule (D18, permanent)", and
    /// ledger-v2/respec/decision-register/D18-content-rule.md. Four of the
    /// five enforcement sites are text and a person can read them. This one
    /// is a GENERATOR, and D18 names the difference in as many words: a
    /// crowd that samples ages cannot be allowed to sample a child. A text
    /// site can be reviewed; a generator has to be UNABLE to produce the
    /// thing, because nobody reviews three thousand residents.
    ///
    /// WHY IT IS IN CORE. Core is the layer whose tests run in the container
    /// where this work happens. The Game layer does not compile here, so a
    /// predicate written there would ship UNRUN, and an unrun guard that
    /// returns a plausible answer is this project's named silent-instrument
    /// failure. So the RULE lives here with its tests, and the Game layer
    /// supplies only membership: which model stems are in the pool, which
    /// trade a resident drew.
    ///
    /// WHAT IT DOES NOT DO. It does not read dialogue: that is
    /// tools/content-gate.py, which walks the banks, the barks, the cast
    /// cards, the prompt specs and the brand bible. It does not judge tone,
    /// spectacle or reward, none of which any predicate can see. It answers
    /// exactly two questions a generator asks: is this age a person we may
    /// show, and does this NAME describe somebody or something we may not.
    public static class ContentRule
    {
        /// THE FLOOR, IN YEARS. Eighteen because D18 says no children
        /// anywhere and eighteen is the line the rule's own phrasing takes.
        ///
        /// THE NUMBER IS HERE BEFORE ANY AGE EXISTS, and that is deliberate
        /// rather than premature. `Resident` today has twelve fields and not
        /// one of them is an age, so nothing in the crowd can sample a child
        /// because nothing in the crowd samples an age at all. That is a
        /// fact about today's code and not a guarantee: the day somebody
        /// adds `int Age` to a resident, the floor they need is already
        /// here, already tested, and already the thing `Generate` calls.
        /// Adding the guard after the field is how the field ships without
        /// one.
        public const int AdultFloorYears = 18;

        /// Is this a person the work may show? Ages below the floor are
        /// refused, and so are absurd ones: a negative age is a bug that
        /// would otherwise pass a `>= 18` test by arithmetic accident.
        public static bool IsShowableAge(int years)
        {
            return years >= AdultFloorYears && years <= 120;
        }

        /// WORDS THAT NAME SOMEBODY UNDER THE FLOOR. Compared as WORDS,
        /// through `BodyParts.Words`, never with `Contains`: the stem
        /// arrives with its spaces stripped, so `SportyGranny` becomes
        /// {sporty, granny}, and equality on a segment is the whole subject
        /// of `BodyParts`. Substring matching here would refuse `Kate`
        /// for containing nothing and accept nothing for containing
        /// everything: `kid` sits inside `kidney`, `boy` inside `boyer`,
        /// and `child` inside `Childers`, a real surname.
        ///
        /// `boy`, `girl` and `school` ARE here, and that is the opposite
        /// call from the one the dialogue gate makes. It is deliberate and
        /// the difference is the channel. In BRITISH SPEECH "the Hendricks
        /// boy" is a grown man out of work, so tools/content-gate.py does
        /// not refuse the word; in an FBX FILE NAME nobody ships a rig
        /// called `Boy` meaning a forty-year-old. Written the other way
        /// first, and the test caught it: `school_boy` split to
        /// {school, boy} and neither word was listed, so the one model stem
        /// most likely to arrive would have walked straight into the pool.
        /// `lad` and `lass` are still absent: they are adult words in both
        /// channels.
        ///
        /// `Boyer`, `Childers` and `Kidman` are surnames and pass, because
        /// this is equality on a segment and not a substring test. That is
        /// the whole subject of `BodyParts`, and all three are accepting
        /// fixtures in CoreTests.
        static readonly string[] Underage =
        {
            "child", "children", "kid", "kids", "baby", "babies", "infant",
            "toddler", "newborn", "schoolboy", "schoolgirl", "schoolchild",
            "schoolkid", "pupil", "teen", "teenager", "teenage", "juvenile",
            "youngster", "adolescent", "junior", "nursery", "preschool",
            "school", "boy", "boys", "girl", "girls",
        };

        /// Does this model stem name somebody under the floor?
        ///
        /// THE DAY A `Child.fbx` LANDS IN Assets/Characters, THIS IS WHAT
        /// KEEPS IT OFF QUAY STREET. `RealBody` already keeps `X Bot` and
        /// `Y Bot` out of the pool by name, so the pool already has the
        /// shape this needs; this adds one more reason to refuse, and it is
        /// the reason canon cares about. A refusal is VISIBLE by the same
        /// route the archetype roster is visible: the caller counts what it
        /// refused and prints the count, because a body silently dropped
        /// looks exactly like a body that was never there.
        public static bool IsUnderageModel(string modelStem)
        {
            if (string.IsNullOrEmpty(modelStem)) return false;
            foreach (var w in BodyParts.Words(modelStem))
                foreach (var u in Underage)
                    if (string.Equals(w, u, StringComparison.OrdinalIgnoreCase))
                        return true;
            return false;
        }

        /// Trades a resident may not be given: the ones whose whole function
        /// is a thing D18 removes. Alcohol and gambling only, and the list
        /// is short on purpose.
        ///
        /// `barman`, `barmaid` and `bartender` are NOT here, and that is a
        /// judgement rather than an oversight. The rule keeps pubs as
        /// places, a place has staff, and what that staff serves is a design
        /// question D18 sends to ruling 6 rather than a word this list can
        /// settle. `brewer`, `bookmaker` and `turf accountant` are here
        /// because there is no version of those jobs that is not the thing
        /// the rule removes.
        static readonly string[] RefusedTrades =
        {
            "brewer", "brewery", "distiller", "distillery", "off-licence",
            "bookmaker", "bookie", "turf accountant", "croupier",
            "bingo caller", "betting clerk",
        };

        /// May a resident be given this trade? Whole-string, case and
        /// hyphen insensitive, because a trade is a table entry rather than
        /// free text and a substring test here would refuse "brewery
        /// labourer" for the wrong half of the phrase.
        public static bool IsShowableTrade(string trade)
        {
            if (string.IsNullOrEmpty(trade)) return false;
            var t = trade.Trim().ToLowerInvariant().Replace('-', ' ');
            foreach (var r in RefusedTrades)
                if (t == r.Replace('-', ' ')) return false;
            return true;
        }

        /// Everything in a table this rule refuses, as a list rather than a
        /// bool, so a caller can PRINT what it dropped.
        ///
        /// A zero needs its denominator: `Screen` returns the refusals and
        /// the caller reports them beside the count it examined, so "0
        /// refused" beside "30 trades screened" cannot be confused with a
        /// screen that never ran.
        public static List<string> Screen(IEnumerable<string> trades)
        {
            var bad = new List<string>();
            if (trades == null) return bad;
            foreach (var t in trades)
                if (!IsShowableTrade(t)) bad.Add(t);
            return bad;
        }
    }
}
