using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// Act III — The Ledger Comes Due (`act3-draft.md`).
    ///
    /// The crisis is an AUDIT: the least dramatic instrument available, which
    /// is what makes it frightening. Somebody with a mandate asks to see the
    /// bar's books, and the bar's books are the one document in this game that
    /// has been quietly lying since day one.
    ///
    /// Everything the player did to the ledger is now evidence in the other
    /// direction. Launder too little and the night money has nowhere to have
    /// come from. Launder too much and the bar earned more than a bar on this
    /// street possibly could. The lie has a shape, and the shape is now being
    /// measured. It cannot be fought — only survived, deflected onto somebody,
    /// or answered by choosing which life to keep.
    ///
    /// THE RULE THAT MATTERS MOST HERE: **the player never picks an ending from
    /// a list.** Each ending is a condition the world can be IN when the audit
    /// closes. More than one can be live at once, and then the last thing the
    /// player did decides between them. Which ending somebody earned is exactly
    /// the kind of thing that must never come from a coin flip or from a
    /// language model, so all of it is a pure function of state and all of it
    /// is tested.

    public enum Ending
    {
        /// The audit has not closed.
        None,
        /// Empire and life both survive. Requires the information landscape
        /// actively managed. Should be rare, and should feel earned rather
        /// than lucky.
        Both,
        /// You kept everything you built, and nobody is left who knew you
        /// before it.
        Kingdom,
        /// You gave up the business to keep the people.
        StraightLife,
        /// The ledger took it all. This is what doing nothing produces, which
        /// is correct: it comes due whether or not you answer it.
        BurnBoth,
        /// Handed to somebody you built up. Not a fifth cell in the matrix — a
        /// way of leaving it, and the only ending with an epilogue.
        Quiet,
    }

    /// Everything the ending depends on, gathered in one place so the decision
    /// is a function rather than a scattering of ifs across the game layer.
    public class LedgerState
    {
        // The empire.
        public int BusinessesOwned;
        public int RacketsEstablished;
        public int CrewCount;
        public bool EmpireDissolved;      // sold up and paid off before the close

        // The life.
        public double BestDayLifeLoyalty; // the strongest surviving relationship
        public int DayLifeDeparted;       // how many walked away

        // The information landscape.
        public double DayCircleRacketHeat; // how firmly the day circle holds it
        public bool OsseiCaseAnswerable;   // her strongest lead discredited, bought or contradicted

        // The books themselves.
        public int TotalWashed;
        public int TotalRacketIncome;
        public int BarTakingsToDate;

        // Succession.
        public bool HasReadySuccessor;
        public string SuccessorId, SuccessorName;
        public bool HandedOver;

        /// How the man reading the books has been handled. Not a bribe — a
        /// count of days you produced what was asked for, against days you told
        /// him to put it in writing.
        public int Cooperations, Stonewalls;
        /// The real books went somewhere else on the last day.
        public bool LedgersMoved;

        /// Above this, the day circle holds the rackets as fact rather than as
        /// talk, and "Both" is off the table.
        public const double FactThreshold = 0.5;

        /// Testimony grade: a surviving lead at or above this stands up in
        /// front of a magistrate, below it Ossei's case is answerable without
        /// her deal (act3-draft.md answer 3).
        public const double CaseStandsAt = 0.5;
        /// Above this, a relationship counts as surviving.
        public const double TrustThreshold = 0.55;
        /// Above this, the inspection finds the shape of it and you keep
        /// nothing. Deliberately not the top of the range: books that a careful
        /// reader would ask about are survivable, and books that describe a
        /// business which does not exist are not.
        public const double BooksHoldThreshold = 0.62;
    }

    public class ActThreeState
    {
        public bool Opened;
        public int OpenedDay = -1;
        public bool Pp1Fired, Pp2Fired, Pp3Fired, Pp4Fired, Pp5Fired;

        /// The audit runs to a day, and that day is named in the letter. Not a
        /// timer the player watches tick — a date somebody wrote down.
        public int AuditClosesDay = -1;
        public bool AuditClosed;
        public Ending Result = Ending.None;

        /// Set when the player hands over. The epilogue runs from here.
        public string SuccessorId;
        public int EpilogueDay = -1;
        public const int EpilogueDays = 3;

        /// The two things the player can actually DO about the audit, as
        /// opposed to the many things they can do about the world. Both are
        /// one-way: you cannot un-sell a business or un-name a name.
        public bool SoldUp;
        public bool Deflected;

        /// The man doing the reading, and how he has been dealt with. Once a
        /// day, every day of the six — the only Act III verb that is not
        /// irreversible, and the only one that costs nothing but attention.
        public bool InspectorArrived;
        public int Cooperations, Stonewalls;
        public int LastDealtDay = -1;

        /// The last day (PP5). Two calls, and reaching one is not reaching
        /// another.
        public int LastDayActions;
        public bool LedgersMoved;
        public int LastDayLeft => Math.Max(0, LastDayBudget - LastDayActions);
        public bool IsLastDay(int day) => Opened && !AuditClosed && day >= AuditClosesDay - 1;
        /// Who the audit was pointed at instead, and who told you about them —
        /// because the street knows who talks, and the second name is the price.
        public string DeflectedOnto, BurnedWitnessId;

        /// How long the letter gives you. Long enough to act, short enough that
        /// you cannot do everything.
        public const int DaysOfGrace = 6;

        /// The act opens when the Table has been answered AND one of the two
        /// ledgers has become undeniable: Ossei can name the rackets, or the
        /// empire is too big for the bar to explain its own money.
        public static bool ShouldOpen(bool tableAnswered, bool osseiCanName, int businessesOwned,
            int racketsEstablished) =>
            tableAnswered && (osseiCanName || businessesOwned + racketsEstablished >= 3);

        /// How wrong the books look. 0 = the lie holds, 1 = it does not.
        ///
        /// Wrong in BOTH directions, which is the whole idea. Money washed far
        /// beyond what a bar on this street could plausibly turn over is as
        /// damning as racket income with no laundering behind it at all.
        public static double LedgerStrain(LedgerState s)
        {
            if (s == null) return 0;
            double unexplained = s.TotalRacketIncome <= 0
                ? 0
                : Math.Clamp(1.0 - (double)s.TotalWashed / Math.Max(1, s.TotalRacketIncome), 0, 1);

            // A bar can plausibly account for washing about a third of what it
            // takes over the counter. Past that the till is telling a story
            // nobody on this street believes.
            double plausible = Math.Max(1, s.BarTakingsToDate) * 0.35;
            double tooMuch = Math.Clamp((s.TotalWashed - plausible) / Math.Max(1.0, plausible), 0, 1);

            return Math.Clamp(Math.Max(unexplained, tooMuch), 0, 1);
        }

        /// The word for it. No number ever reaches the player.
        public static string StrainWord(double strain) =>
            strain < 0.2 ? "the books look like a bar's books"
            : strain < 0.45 ? "there are one or two months a careful reader would ask about"
            : strain < 0.7 ? "the shape of it is wrong, and a careful reader will see the shape"
            : "these books describe a business that does not exist";

        /// How much of the business the inspection actually looks at.
        ///
        /// THE POINT OF THIS: the audit cannot be fought and must not be
        /// buyable — an inspector with a price would collapse the whole ending
        /// matrix into "did you save up". But it can be **narrowed**, by the
        /// least dramatic means available: producing what is asked for, on the
        /// day it is asked for, without being difficult about it.
        ///
        /// So Act III gains a verb that is not one of the three irreversible
        /// ones. It is available every day of the six, it rewards attention
        /// rather than money, and it never overrides the matrix — it only moves
        /// where in the matrix you are standing.
        /// 0.045 per morning, halved from 0.09 on 2026-07-27 (decision 10).
        ///
        /// At the old number the balance lab measured an aggressive campaign
        /// going from 100% Burn Both when the inspector was ignored to 100%
        /// Kingdom when he was answered every day — six mornings of paperwork
        /// outweighing three acts of laundering decisions. The audit is supposed
        /// to be the bill for how the business was RUN; it should not be
        /// argueable down almost entirely at the counter.
        ///
        /// Stonewalling keeps its full 0.15, and that asymmetry is deliberate:
        /// being difficult with a revenue man was never meant to be a strategy,
        /// and it is much easier to make somebody look harder than to make them
        /// look away.
        public static double ScopeFactor(int cooperations, int stonewalls) =>
            Math.Clamp(1.0 - 0.045 * cooperations + 0.15 * stonewalls, 0.55, 1.6);

        public static string ScopeWord(double factor) =>
            factor <= 0.75 ? "he is looking at the quarter he asked for and nothing either side of it"
            : factor < 1.1 ? "he is looking at what an inspection ordinarily looks at"
            : factor < 1.35 ? "he has started asking for years you did not offer"
            : "he is going through the whole of it, and taking his time";

        /// What the inspection will actually SEE: the strain in the books,
        /// widened or narrowed by how you have handled the man reading them,
        /// and eased if the case has been pointed at somebody else — they do
        /// not look as hard at a business they have already stopped suspecting.
        public static double SeenStrain(LedgerState s)
        {
            if (s == null) return 0;
            double seen = LedgerStrain(s) * ScopeFactor(s.Cooperations, s.Stonewalls);
            if (s.OsseiCaseAnswerable) seen *= 0.7;
            // What is not in the cellar cannot be read out of it. Deliberately
            // the single largest movement any one action makes, because it is
            // the last day, it costs a whole call, and it is only available to
            // somebody Lena decided about a long time ago.
            if (s.LedgersMoved) seen *= 0.55;
            return Math.Clamp(seen, 0, 1);
        }

        // ---- the endings ----

        /// Every ending the world currently qualifies for, best-first.
        ///
        /// Several can be live at once. That is deliberate: the matrix is a
        /// description of the world, not a menu, and when more than one fits
        /// the player's last decisions choose.
        public static List<Ending> Eligible(LedgerState s)
        {
            var list = new List<Ending>();
            if (s == null) return list;

            // The Quiet Ending outranks everything, because it is the only one
            // the player has to actively reach for — you cannot arrive at it by
            // accident.
            //
            // It survives any amount of strain, and that is not an oversight:
            // you signed it over, so what the inspection finds lands on the
            // person whose name is now on the licence. Leaving somebody holding
            // your books is the cost of the quietest door out, and the epilogue
            // is where you find out what it cost them.
            if (s.HandedOver && s.HasReadySuccessor) list.Add(Ending.Quiet);

            bool lifeSurvives = s.BestDayLifeLoyalty >= LedgerState.TrustThreshold;
            bool empireSurvives = !s.EmpireDissolved &&
                (s.BusinessesOwned > 0 || s.RacketsEstablished > 0);
            bool landscapeManaged = s.DayCircleRacketHeat < LedgerState.FactThreshold
                                     && s.OsseiCaseAnswerable;

            // THE BOOKS HAVE TO HOLD.
            //
            // Without this the whole "wrong in both directions" mechanic was
            // flavour: it changed the words Lena said and nothing else, and an
            // audit resolved without ever reading the document it came to read.
            // Every laundering decision across three acts was decorative.
            //
            // So keeping ANYTHING now requires the ledger to survive being
            // looked at. Managing every mouth on the street does not save books
            // that describe a business which does not exist — that is the one
            // thing the street's opinion cannot argue with, and it is the whole
            // reason the crisis is an audit rather than a raid.
            double seen = SeenStrain(s);
            bool booksHold = seen < LedgerState.BooksHoldThreshold;

            // BOTH ASKS FOR MORE THAN THE OTHERS, and it asks for the one thing
            // that cannot be arranged in the last week: books that are actually
            // defensible, not merely well-handled.
            //
            // The balance lab caught this. With the mitigations stacking
            // multiplicatively — a case pointed elsewhere at 0.7, a narrowed
            // scope at 0.55 — an aggressive campaign's strain fell from 1.00 to
            // 0.39, and Both fired in fifty-one runs out of a hundred. That is
            // not "rare and earned rather than lucky" (§8) and it is not "not
            // reachable on a first playthrough" (player decision, 2026-07-27);
            // it is a two-step win button.
            //
            // So the mitigations keep doing what they should — they save you
            // from losing everything — and they no longer BUY you the best
            // ending. For that the underlying business has to have made sense
            // all along, which is a judgement about three acts of play rather
            // than about six mornings of paperwork.
            bool booksAreClean = LedgerStrain(s) < LedgerState.BooksHoldThreshold;

            if (empireSurvives && lifeSurvives && landscapeManaged && booksHold && booksAreClean)
                list.Add(Ending.Both);
            // Selling up is the one route the books cannot follow you down:
            // there is nothing in them because there is nothing left to be in
            // them, and taking that loss is exactly what you paid for it.
            //
            // THE CONDITION IS "no empire", not "dissolved an empire". It used
            // to be the latter, and that quietly meant a player who never built
            // one had no ending available except Burn Both — they could not
            // reach the straight life because you cannot sell what you never
            // bought. The balance lab found it immediately: the do-nothing plan
            // ended in "you lose the business and you lose the people" a hundred
            // times out of a hundred, having neither.
            //
            // Never building it is a way of keeping your life, and it is the
            // hardest one to play. It gets the same door.
            if (!empireSurvives && lifeSurvives) list.Add(Ending.StraightLife);
            // Kingdom is "you kept what you built", and it does NOT require the
            // life to be gone — Both already outranks it in this list, so the
            // ordering does that work. Requiring it here left a hole the tests
            // fell straight into: a player who kept the empire, kept a friend,
            // managed the street and survived the reading, but whose books were
            // only saved by handling rather than by making sense, qualified for
            // nothing and got Burn Both. They survived the audit. Losing
            // everything is the one thing that clearly did not happen to them.
            //
            // What they get instead is the ending whose text is about keeping
            // the street and finding the people in it civil and no more, which
            // is exactly what an enterprise that never added up costs you.
            if (empireSurvives && booksHold) list.Add(Ending.Kingdom);
            if (!list.Contains(Ending.Both) && !list.Contains(Ending.StraightLife)
                && !list.Contains(Ending.Quiet) && !list.Contains(Ending.Kingdom))
                list.Add(Ending.BurnBoth);
            return list;
        }

        /// What actually happens when the books are opened. Never random, never
        /// the model's call — the world is in a state, and the state resolves.
        public static Ending Resolve(LedgerState s)
        {
            var live = Eligible(s);
            return live.Count == 0 ? Ending.BurnBoth : live[0];
        }

        /// Can this person hold it? Deliberately a judgement of a PERSON —
        /// competence, loyalty, standing on their own feet, and nobody in the
        /// crew who will not work with them. The player is never shown the
        /// number, because being asked to judge somebody is the point.
        public static bool CouldHold(double competence, double loyalty, bool independent, bool feuding) =>
            independent && !feuding && competence >= 0.55 && loyalty >= 0.6;

        // ---- authored text ----

        public const string OpenText =
            "There is a letter on the counter when you come down, addressed to the bar rather than to you. " +
            "It is courteous, entirely procedural, and it names a date.";

        public const string Pp1LetterText =
            "Under the Revenue Act, the licensed premises known as the Hook Street bar is required to produce " +
            "its books of account for inspection. A date is given. There is no threat in it anywhere, " +
            "which is what makes it the worst thing that has ever arrived at this address.";

        public static string Pp2LenaText(double loyalty, double strain)
        {
            if (loyalty < 0.35)
                return "Lena reads the letter twice, puts it back on the counter, and says the books are in the cellar " +
                       "where they have always been. She does not offer to walk you through them. You have not earned that, " +
                       "and she is not pretending otherwise.";
            if (loyalty < LedgerState.TrustThreshold)
                return "\"They'll want the ledgers,\" Lena says. \"The real ones are where Marek left them.\" " +
                       "She tells you that much and stops, and the stopping is deliberate.";
            return "Lena puts the kettle on, which she has not done since Marek died. Then she takes you through it, " +
                   "month by month, in the flat voice of somebody who has been waiting years to be asked. " +
                   $"By the end you know exactly where the lie holds and exactly where it does not: {StrainWord(strain)}.";
        }

        public const string Pp3OsseiText =
            "Ossei does not arrest anybody. She sets a name on the table — not yours — and explains, without " +
            "any pleasure in it, that an audit finds whatever it is pointed at. Give her the arm that has been " +
            "hardest on you, with enough to make it stick, and it will be pointed elsewhere.\n\n" +
            "Everything you would hand her came from somebody who told you. The street knows who talks.";

        public static string Pp4SuccessionText(string name) =>
            $"{name} finds you before you find them. Not a betrayal — an offer, and they have clearly been " +
            "rehearsing it. They know what is coming. They are asking for the thing you are about to lose, " +
            "and they are asking for it because they think they can carry it.\n\n" +
            "Nobody will tell you whether they are right.";

        /// THE INSPECTOR. Act III's crisis had no face — the letter arrived,
        /// the date passed, and the books were read offstage by nobody.
        ///
        /// He is not corrupt, and the design depends on that: an inspector with
        /// a price turns the ending matrix into "did you save up enough". He is
        /// not cruel either, and that is the frightening part. He is a man doing
        /// a job he is good at, who explains each step because the procedure
        /// requires him to explain it, and who is not interested in you as a
        /// person at all. Everybody else in this game can be talked around.
        /// He cannot, and the only thing you can move is how much he looks at.
        public const string InspectorName = "Tobias Reisz";

        public const string InspectorArrivesText =
            "He is at the bar at ten past nine with a case and a folding rule, and he introduces himself " +
            "twice — once to you and once to Lena, in the same words. Tobias Reisz, Board of Excise. " +
            "He asks where he may sit, and then he asks whether the light is always this poor.";

        public static string InspectorAskText(int day, double scope) =>
            $"Reisz has an item for today and he says it out loud, the way he says everything: " +
            $"{ScopeWord(scope)}. He will want it before he leaves.";

        public const string CooperateText =
            "You put it in front of him inside the hour. He reads it, writes one line, and thanks you " +
            "by your surname. It costs you a morning and it buys the only thing he has to sell, which " +
            "is not looking any further than he was asked to.";

        public const string StonewallText =
            "You tell him to put the request in writing. He says \"of course\" without any edge at all, " +
            "writes it, and hands it to you — and then writes something else, for himself, which he does " +
            "not hand to anybody. A man with a reason to widen the thing he is doing now has one.";

        public const string Pp5CallsText =
            "The last day. You can reach a few people, and reaching one is not reaching another. " +
            "Whoever picks up is the campaign you actually played.";

        /// PP5 — the last day, made into a scene rather than a sentence.
        ///
        /// The line above was written first and it describes something that did
        /// not exist: there was nothing to DO on the last day except wait for
        /// the ninth of the month. This is the doing.
        ///
        /// Three things you might say to three kinds of person, and the budget
        /// is two — so "reaching one is not reaching another" is a rule rather
        /// than a mood. Each one moves state the endings already read, so none
        /// of them is an ending button:
        ///
        ///   - Lena moves the real ledgers, which narrows what can be found.
        ///     Gated on loyalty, because it is a felony you are asking her to
        ///     commit for you on a few hours' notice.
        ///   - Somebody on the crew is told to go quiet, which takes them out
        ///     of the count and out of the inspection's reach.
        ///   - Somebody in the day life hears it from you rather than from the
        ///     street, which is the only thing that has ever repaired one of
        ///     those relationships.
        ///
        /// And it runs on the telephone, which is what makes it a scene: a
        /// phone is a place, so whether you reach anybody at all on the last
        /// day is a question about where they happen to be standing.
        public const int LastDayBudget = 2;

        public static string LastDayLenaText(bool willing) => willing
            ? "\"They're in the cellar and they're in Marek's hand,\" Lena says. \"Give me until four.\" " +
              "She does not ask what happens to her if somebody notices, and you do not offer to tell her."
            : "Lena listens to the whole of it. Then she says that the books are where they have always been, " +
              "and that she has a daughter, and that those two facts are the same answer.";

        public static string LastDayCrewText(string name) =>
            $"{name} is gone inside the hour — no argument, no goodbye worth the name. " +
            "Whatever the inspection turns over, it will not turn them over, and whatever you built with them " +
            "is finished either way.";

        public static string LastDayTruthText(string name) =>
            $"You tell {name} yourself, before the street can. It goes badly and it goes honestly, " +
            "and at the end of it they are still standing there — which is more than the alternative " +
            "was ever going to give you.";

        public const string LastDaySpentText =
            "There is not time for another. The date on the letter is tomorrow and it was always going to " +
            "come down to which two people you could reach.";

        /// Will she do it? A felony, at short notice, for somebody she has to
        /// have decided about long before today.
        public static bool WillMoveTheLedgers(double lenaLoyalty) => lenaLoyalty >= 0.7;

        /// Kingdom covers two worlds, and the difference is the entire point of
        /// the matrix's second axis.
        ///
        /// One is the empire kept at the cost of everybody who knew you before
        /// it. The other — found by the test that asks whether every input can
        /// change the ending — is the player who kept the empire AND somebody
        /// who still counts them, but did not earn Both because the enterprise
        /// never quite added up. That is not the same evening, and until now it
        /// was told it had nobody left, which was simply untrue.
        ///
        /// The ending stays Kingdom either way: you kept what you built, and
        /// there are five endings, not six. What changes is what it cost.
        public static string KingdomText(bool anybodyLeft) => anybodyLeft
            ? "The books hold. Everything you built is still yours, and there is still one person in this city " +
              "who knew you before any of it and did not stop knowing you. You are aware, sitting with them, " +
              "of how narrow that is. It would have taken one more careless month. It still might."
            : "The books hold. Everything you built is still yours. Ada is civil at the market and does not " +
              "stop walking; Lena works her hours and goes home. You have the street. That is the whole of it.";

        /// The straight life has two roads into it and they do not feel the
        /// same. One is a man who built something and gave it up; the other is
        /// a man who was handed the makings of it and never did — which is the
        /// harder game to play and deserves its own paragraph rather than
        /// somebody else's.
        public static string StraightLifeText(bool everBuiltIt) => everBuiltIt
            ? "There is nothing in the books because there is nothing left to be in them. You sold up, paid " +
              "everyone off, and took the loss. The bar is a bar. Somebody asks you, weeks later, whether it " +
              "is true what they used to say about this place, and you get to tell the truth."
            : "The inspection takes an afternoon. There was never anything in the books, because you never put " +
              "anything in them — and the whole of what that cost you is invisible, which is the point. " +
              "Marek's people drifted off to other people's rounds. The street decided you were nobody in " +
              "particular. You have a bar, and the hours are bad, and everybody who knew you when you arrived " +
              "still knows you.";

        public static string EndingText(Ending e, string successorName = null) =>
            e == Ending.Both
                ? "The books are opened, and they are a bar's books. The inspector is bored by two o'clock. " +
                  "Nobody in the day circle ever quite says what they think you do, and nobody in the night one " +
                  "quite believes you got away with it. You did. It took managing every mouth on this street, " +
                  "and you will be managing them tomorrow too."
            : e == Ending.Kingdom
                ? KingdomText(anybodyLeft: false)
            : e == Ending.StraightLife
                ? StraightLifeText(everBuiltIt: true)
            : e == Ending.Quiet
                ? $"You sign it over to {successorName ?? "them"} and take the boat. Whether what you built " +
                  "survives you is not up to you anymore, which is the first honest thing about it."
                : "The audit finds the shape of it, and the street was already saying the rest out loud. " +
                  "You lose the business and you lose the people, and the order in which those two happen " +
                  "turns out not to matter at all.";

        /// The only ending with an after.
        ///
        /// Three mornings, and you are not in any of them — you hear about the
        /// street the way anybody who left hears about anywhere, second-hand and
        /// late. What arrives is decided by the world you handed over rather than
        /// by how the handover felt: a street you starved is still starved, and a
        /// crew that liked you does not necessarily like them.
        public static string EpilogueText(int dayIndex, string successorName, LedgerState s)
        {
            string who = successorName ?? "whoever took it";
            bool hot = s != null && s.DayCircleRacketHeat >= LedgerState.FactThreshold;
            bool intact = s != null && s.BestDayLifeLoyalty >= LedgerState.TrustThreshold;

            if (dayIndex <= 0)
                return $"First morning off the street. Somebody who came in on the same boat says the bar opened on time and " +
                       $"{who} was behind the counter at seven, which is earlier than you ever managed.";
            if (dayIndex == 1)
                return hot
                    ? $"Word comes down the line that the talk about the Hook has not stopped, it has only changed its subject. " +
                      $"{who} inherited the street's opinion of you along with everything else. That was not in the papers you signed."
                    : $"Word comes down the line that nothing is happening on the Hook at all. {who} is running it quietly, " +
                      "the way you kept saying you would once things settled. Things never did settle. They have, now, for somebody else.";
            return intact
                ? $"A letter, forwarded twice, in handwriting you know. It does not ask you to come back and it does not " +
                  "say you were wrong. It tells you what the street had for breakfast and who is arguing with whom, " +
                  "and it is signed the way people sign letters to somebody they still count."
                : $"No letter. {who} has your old address and has not used it. You find you are not surprised, " +
                  "and the not being surprised is the part that stays with you.";
        }

        // ---- persistence ----

        public Dictionary<string, object> Capture() => new Dictionary<string, object>
        {
            { "opened", Opened }, { "openedDay", OpenedDay },
            { "pp1", Pp1Fired }, { "pp2", Pp2Fired }, { "pp3", Pp3Fired },
            { "pp4", Pp4Fired }, { "pp5", Pp5Fired },
            { "closesDay", AuditClosesDay }, { "closed", AuditClosed },
            { "result", Result.ToString() },
            { "successor", SuccessorId ?? "" }, { "epilogueDay", EpilogueDay },
            { "soldUp", SoldUp }, { "deflected", Deflected },
            { "deflectedOnto", DeflectedOnto ?? "" }, { "burned", BurnedWitnessId ?? "" },
            { "inspector", InspectorArrived }, { "cooperations", Cooperations },
            { "stonewalls", Stonewalls }, { "dealtDay", LastDealtDay },
            { "lastDayActions", LastDayActions }, { "ledgersMoved", LedgersMoved },
        };

        public void Restore(Dictionary<string, object> d)
        {
            if (d == null) return;
            Opened = Flag(d, "opened");
            OpenedDay = MiniJson.GetInt(d, "openedDay");
            Pp1Fired = Flag(d, "pp1"); Pp2Fired = Flag(d, "pp2"); Pp3Fired = Flag(d, "pp3");
            Pp4Fired = Flag(d, "pp4"); Pp5Fired = Flag(d, "pp5");
            AuditClosesDay = MiniJson.GetInt(d, "closesDay");
            AuditClosed = Flag(d, "closed");
            var r = MiniJson.GetString(d, "result");
            Result = r == "Both" ? Ending.Both : r == "Kingdom" ? Ending.Kingdom
                : r == "StraightLife" ? Ending.StraightLife : r == "Quiet" ? Ending.Quiet
                : r == "BurnBoth" ? Ending.BurnBoth : Ending.None;
            var succ = MiniJson.GetString(d, "successor");
            SuccessorId = string.IsNullOrEmpty(succ) ? null : succ;
            EpilogueDay = MiniJson.GetInt(d, "epilogueDay");
            SoldUp = Flag(d, "soldUp");
            Deflected = Flag(d, "deflected");
            var onto = MiniJson.GetString(d, "deflectedOnto");
            DeflectedOnto = string.IsNullOrEmpty(onto) ? null : onto;
            var burned = MiniJson.GetString(d, "burned");
            BurnedWitnessId = string.IsNullOrEmpty(burned) ? null : burned;
            InspectorArrived = Flag(d, "inspector");
            Cooperations = MiniJson.GetInt(d, "cooperations");
            Stonewalls = MiniJson.GetInt(d, "stonewalls");
            LastDealtDay = MiniJson.GetInt(d, "dealtDay");
            LastDayActions = MiniJson.GetInt(d, "lastDayActions");
            LedgersMoved = Flag(d, "ledgersMoved");
        }

        static bool Flag(Dictionary<string, object> o, string key) =>
            o != null && o.TryGetValue(key, out var v) && v is bool b && b;
    }
}
