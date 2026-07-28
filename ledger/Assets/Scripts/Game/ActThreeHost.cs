using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Act III — The Ledger Comes Due (`act3-draft.md`), driven off world state.
    ///
    /// Core owns the arithmetic: what the books look like, which endings the
    /// world qualifies for, whether a person could hold what you built. This
    /// file owns the three things Core cannot know — WHEN the letter arrives,
    /// WHO is standing in front of you when the choice is offered, and what
    /// actually moves in the world when you take it.
    ///
    /// The design rule this file exists to protect: **the player never picks an
    /// ending from a list.** There is no ending menu anywhere in here. There are
    /// three verbs — sell up, deflect, hand over — each of which changes the
    /// world, and on the closing day the world is read and it resolves. A player
    /// who does nothing at all still gets an ending, because the audit was never
    /// waiting for them to be ready.
    public partial class GameController
    {
        public ActThreeState ActThree { get; } = new ActThreeState();

        /// Everything the ending depends on, read fresh off the world. Never
        /// cached: the whole point is that the answer on the closing morning is
        /// the answer for the state the world is actually in.
        public LedgerState Books()
        {
            var e = Empire;
            var s = new LedgerState
            {
                BusinessesOwned = e.Businesses.FindAll(b => b.Owned).Count,
                RacketsEstablished = e.Rackets.FindAll(r => r.Established).Count,
                CrewCount = e.Crew.FindAll(c => !c.Departed).Count,
                EmpireDissolved = ActThree.SoldUp,
                DayCircleRacketHeat = CurrentHeat,
                // Deflection answers her case — but so does a managed
                // information landscape: no surviving lead of testimony grade
                // (act3-draft.md answer 3: "You CAN refuse Ellis and still
                // reach Both"). Deflected was the sole source before the
                // audit, which made her deal compulsory for that ending.
                // The record is street KNOWLEDGE, not rumor — a leash cannot
                // hide it and a denial cannot cut it.
                PublicRecord = AnyoneKnowsDidTime(),
                EllisCaseAnswerable = ActThree.Deflected
                    || (_gossip != null && _gossip.Mill != null
                        && _gossip.Mill.StrongestSurvivingPlayerLead() < LedgerState.CaseStandsAt),
                TotalWashed = Wallet.TotalWashed,
                TotalRacketIncome = e.TotalRacketIncome,
                BarTakingsToDate = TotalTakings,
                HandedOver = ActThree.SuccessorId != null,
                Cooperations = ActThree.Cooperations,
                Stonewalls = ActThree.Stonewalls,
                LedgersMoved = ActThree.LedgersMoved,
            };

            // The life: the named people whose circle is the daylight one. Best
            // rather than average, because one person who still counts you a
            // friend IS a life kept — and averaging would let a crowd of polite
            // acquaintances stand in for it.
            foreach (var h in _hosts)
            {
                if (h == null || h.Card == null) continue;
                var g = _gossip?.Mill?.Get(h.Card.Name);
                if (g == null || g.Circle == "night") continue;
                if (Empire.CrewOf(g.Id) != null) continue;      // your people are the empire, not the life
                if (g.Loyalty > s.BestDayLifeLoyalty) s.BestDayLifeLoyalty = g.Loyalty;
                if (g.Loyalty <= 0.15) s.DayLifeDeparted++;
            }

            var ready = ReadySuccessor();
            // The NAMED successor is judged as a person too, on the closing
            // morning: still here, not departed. "SuccessorId != null" alone
            // collapsed Quiet's guard to HandedOver — a burned or departed
            // successor still resolved Quiet with self-contradicting text
            // (audit 2026-07-27). Handing over to somebody who then left is
            // exactly a hand-over that failed.
            var named = ActThree.SuccessorId != null
                ? Empire.Crew.Find(c => c.Id == ActThree.SuccessorId && !c.Departed) : null;
            s.HasReadySuccessor = ready != null || named != null;
            if (named != null)
            {
                s.SuccessorId = named.Id;
                s.SuccessorName = named.Name;
            }
            else if (ready != null) { s.SuccessorId = ready.Id; s.SuccessorName = ready.Name; }
            return s;
        }

        /// Is there anybody who could actually carry this?
        ///
        /// Judged as a PERSON, never as a slot: they must be competent, loyal,
        /// standing on their own feet (running something of yours unsupervised),
        /// and at war with nobody in the crew. The player is shown none of these
        /// numbers — they get a name, and have to decide whether they believe it.
        bool AnyoneKnowsDidTime()
        {
            if (_gossip == null || _gossip.Mill == null) return false;
            var didTime = new Fact("player", "did_time", "true");
            foreach (var a in _gossip.Mill.Agents)
                if (a.Knowledge.CheckClaim(didTime) == ClaimResult.Consistent) return true;
            return false;
        }

        public CrewMember ReadySuccessor()
        {
            CrewMember best = null;
            double bestScore = -1;
            foreach (var c in Empire.Crew)
            {
                if (c.Departed) continue;
                var g = _gossip?.Mill?.Get(c.Id);
                if (g == null) continue;
                bool independent = c.Assignment != null;
                bool feuding = false;
                foreach (var other in Empire.Crew)
                {
                    if (other == c || other.Departed) continue;
                    if (Harm.FeudBetween(c.Id, other.Id) != null) { feuding = true; break; }
                }
                if (!ActThreeState.CouldHold(c.Competence, g.Loyalty, independent, feuding)) continue;
                double score = c.Competence + g.Loyalty;
                if (score > bestScore) { bestScore = score; best = c; }
            }
            return best;
        }

        // ---- the act ----

        int _lastAuditSeenDay = -1;

        void CheckActThree()
        {
            if (!Campaign.OpenMode || _gossip == null || _gossip.Mill == null) return;

            // A calendar jump during the audit gives the grace days back
            // (audit 2026-07-27) — the letter promised days, not dates. Same
            // for the epilogue's three mornings: a Fall inside them used to
            // skip the remaining vignettes silently.
            if (_lastAuditSeenDay >= 0 && Now.Day > _lastAuditSeenDay + 1)
            {
                int jumped = Now.Day - _lastAuditSeenDay - 1;
                if (ActThree.Opened && !ActThree.AuditClosed)
                    ActThree.AuditClosesDay =
                        ActThreeState.ClosesDayAfterJump(ActThree.AuditClosesDay, _lastAuditSeenDay, Now.Day);
                else if (ActThree.AuditClosed && ActThree.EpilogueDay >= 0)
                    ActThree.EpilogueDay += jumped;
            }
            _lastAuditSeenDay = Now.Day;

            if (ActThree.AuditClosed) { TickEpilogue(); return; }

            if (!ActThree.Opened)
            {
                // Ellis can name the rackets when she has statements AND has
                // joined the two cases — PP6 is exactly that moment.
                bool osseiCanName = EllisSpawned && ActTwo.Pp6Fired && EllisInterviews.Count >= 2;
                if (!ActThreeState.ShouldOpen(ActTwo.TableFired, osseiCanName,
                    Empire.Businesses.FindAll(b => b.Owned).Count,
                    Empire.Rackets.FindAll(r => r.Established).Count)) return;

                ActThree.Opened = true;
                ActThree.OpenedDay = Now.Day;
                ActThree.AuditClosesDay = Now.Day + ActThreeState.DaysOfGrace;
                ToastLine(ActThreeState.OpenText, 13f);
                return;
            }

            // PP1 — the letter itself, read properly, the same morning.
            if (!ActThree.Pp1Fired)
            {
                ActThree.Pp1Fired = true;
                ToastLine(ActThreeState.Pp1LetterText, 16f);
                // Lena reads over your shoulder, because of course she does.
                var lena = _gossip.Mill.Get("Lena");
                lena?.Memory.Append(new MemoryEvent(Now, "observation", 0.95,
                    "A revenue letter came for the bar. Mickey got one of those once. " +
                    "I watched him not sleep for a fortnight."));
                return;
            }

            // PP2 — the cellar, and how much of it Lena is willing to show you.
            // Fires when you are actually standing near her: the scene is her
            // deciding what you have earned, so it needs you in the room.
            if (!ActThree.Pp2Fired && _player != null)
            {
                foreach (var npc in _npcs)
                {
                    if (npc == null || npc.DisplayName != "Lena") continue;
                    if (Vector3.Distance(npc.transform.position, _player.transform.position) > 6f) break;
                    var g = _gossip.Mill.Get("Lena");
                    ActThree.Pp2Fired = true;
                    ToastLine(ActThreeState.Pp2LenaText(g?.Loyalty ?? 0.3, ActThreeState.LedgerStrain(Books())), 17f);
                    break;
                }
            }

            // The inspector arrives the morning after the letter and is in the
            // bar every day until the close. He is the act's only recurring
            // face, and the only one you cannot talk around.
            if (!ActThree.InspectorArrived && Now.Day > ActThree.OpenedDay && Now.Hour >= 9)
            {
                ActThree.InspectorArrived = true;
                ToastLine(ActThreeState.InspectorArrivesText, 16f);
                SpawnInspector();
            }

            // And he has an item for today, once a day, which the player can
            // answer or refuse. Neither costs money; both cost a morning or a
            // reputation, and the difference decides how much he reads.
            if (ActThree.InspectorArrived && ActThree.LastDealtDay != Now.Day && Now.Hour >= 10
                && Now.Day < ActThree.AuditClosesDay)
            {
                ToastLine(ActThreeState.InspectorAskText(Now.Day,
                    ActThreeState.ScopeFactor(ActThree.Cooperations, ActThree.Stonewalls)), 12f);
                ActThree.LastDealtDay = Now.Day;   // asked; answering it is the player's move
                ActThree.InspectorAskedDay = Now.Day;
            }

            // PP3 — Ellis's offer. She comes to you, once, with two days left,
            // and she does not come at all if she was never on the case.
            if (!ActThree.Pp3Fired && EllisSpawned && DaysLeftOnAudit <= 3)
            {
                ActThree.Pp3Fired = true;
                ToastLine(ActThreeState.Pp3OsseiText, 17f);
            }

            // PP4 — succession. Fires the moment somebody is genuinely ready,
            // which is a fact about how you have treated your people rather than
            // a beat on a calendar.
            if (!ActThree.Pp4Fired)
            {
                var ready = ReadySuccessor();
                if (ready != null)
                {
                    ActThree.Pp4Fired = true;
                    ToastLine(ActThreeState.Pp4SuccessionText(ready.Name), 16f);
                }
            }

            // PP5 — the last day, and the phone.
            if (!ActThree.Pp5Fired && DaysLeftOnAudit <= 1)
            {
                ActThree.Pp5Fired = true;
                ToastLine(ActThreeState.Pp5CallsText, 14f);
            }

            // The close. It happens on its named day whether or not the player
            // did anything, because that is what a date on a letter is.
            if (Now.Day >= ActThree.AuditClosesDay && Now.Hour >= 9) CloseAudit();
        }

        /// How long is left, in days. Used for the beats' timing and for the
        /// ledger readout — the player is told the DATE, never a countdown.
        public int DaysLeftOnAudit =>
            ActThree.Opened && !ActThree.AuditClosed ? Mathf.Max(0, ActThree.AuditClosesDay - Now.Day) : -1;

        void CloseAudit()
        {
            if (ActThree.AuditClosed) return;
            var s = Books();
            ActThree.AuditClosed = true;
            ActThree.Result = ActThreeState.Resolve(s);
            // The straight life has two roads in and they do not read the same:
            // a man who built something and gave it up, and a man who was handed
            // the makings and never did.
            string ending =
                ActThree.Result == Ending.StraightLife
                    ? ActThreeState.StraightLifeText(everBuiltIt: ActThree.SoldUp || Empire.TotalRacketIncome > 0)
                : ActThree.Result == Ending.Kingdom
                    ? ActThreeState.KingdomText(anybodyLeft: s.BestDayLifeLoyalty >= LedgerState.TrustThreshold)
                : ActThreeState.EndingText(ActThree.Result, s.SuccessorName);
            ToastLine(ending, 22f);
            Debug.Log($"ACT III: audit closed day {Now.Day} — {ActThree.Result} " +
                      $"(strain {ActThreeState.LedgerStrain(s):F2}, heat {s.DayCircleRacketHeat:F2}, " +
                      $"life {s.BestDayLifeLoyalty:F2}, owned {s.BusinessesOwned}, rackets {s.RacketsEstablished})");

            if (ActThree.Result == Ending.Quiet) ActThree.EpilogueDay = Now.Day;
            Audio.Ui("dread");
        }

        int _lastEpilogueDay = -1;

        /// Three mornings after the handover, and then the game is over in the
        /// only way this game is willing to be over: you stop hearing.
        void TickEpilogue()
        {
            if (ActThree.Result != Ending.Quiet || ActThree.EpilogueDay < 0) return;
            int index = Now.Day - ActThree.EpilogueDay - 1;
            if (index < 0 || index >= ActThreeState.EpilogueDays) return;
            if (Now.Day == _lastEpilogueDay || Now.Hour < 8) return;
            _lastEpilogueDay = Now.Day;
            var s = Books();
            ToastLine(ActThreeState.EpilogueText(index, s.SuccessorName, s), 16f);
        }


        NpcWalker _inspectorWalker;

        /// He does not walk the district. He is at the bar, at a table, from
        /// nine until six, and the fact that he does not go anywhere is the
        /// characterisation: everybody else in this game has a life you can
        /// intersect, and he has an appointment with your books.
        void SpawnInspector()
        {
            if (_inspectorWalker != null) return;
            var seat = WorldBuilder.BarDoor + new Vector3(2.5f, 0, -1.5f);
            _inspectorWalker = NpcWalker.Spawn(ActThreeState.InspectorName,
                new Color(0.34f, 0.33f, 0.30f), new[]
                {
                    (new GameTime(0, 9, 0), seat),
                    (new GameTime(0, 13, 0), seat + new Vector3(0.6f, 0, 0.4f)),  // he takes lunch where he sits
                    (new GameTime(0, 18, 0), WorldBuilder.BarDoor + new Vector3(6, 0, -4)), // and leaves at six
                });
            _npcs.Add(_inspectorWalker);   // he is NOT in the gossip mill: he does not talk to the street

            var host = _inspectorWalker.gameObject.AddComponent<ConversationHost>();
            host.Initialize(this, InspectorCard, null, null);
            host.SceneContext = "At a table just inside the Hook Street bar, papers squared, talking with the owner.";
            host.ExtraContext = () =>
            {
                var s = Books();
                int left = Mathf.Max(0, ActThree.AuditClosesDay - Now.Day);
                // Counts go to the model as WORDS: what we feed it is what it
                // says back, and "on 3 occasion(s)" is a spreadsheet talking
                // (audit 2026-07-27). The closing DATE stays a date — the
                // letter has one on it.
                string remain = left <= 0 ? "it closes today"
                    : left == 1 ? "one day remains"
                    : left == 2 ? "two days remain" : "a few days remain";
                string Times(int n) => n == 0 ? "not once" : n == 1 ? "once" : n == 2 ? "twice" : "time after time";
                return $"The inspection closes on day {ActThree.AuditClosesDay}; {remain}. " +
                       $"Your present scope: {ActThreeState.ScopeWord(ActThreeState.ScopeFactor(s.Cooperations, s.Stonewalls))}. " +
                       $"You have been given what you asked for {Times(s.Cooperations)} and refused {Times(s.Stonewalls)}. " +
                       "You do not accuse, you do not threaten, and you do not take anything from anybody. " +
                       "You state what you require and when you require it.";
            };
            _hosts.Add(host);
        }

        /// Authored rather than generated, because Act III's whole crisis rests
        /// on this man being exactly one thing and never bending.
        public const string InspectorCard = @"# Tobias Reese
id: reisz
tier: core

## Summary
Inspector, Board of Excise, nineteen years. Fifty-ish, grey, entirely unremarkable — the sort of man who is already sitting down when you notice he has come in. He is at a table in the bar every day until the date on the letter, and he is not going anywhere else.

## Personality
Incorruptible, and not out of principle — out of a total lack of interest. He is not building a case, he does not think you are wicked, and he could not tell you the name of the street outside. He is reading a document. He explains each step because the procedure requires him to explain it, and the courtesy is real and worth nothing.

## Speech Style
Flat, exact, complete sentences. Names the regulation before the request. Says ""of course"" to refusals. Never raises his voice and never repeats himself, and both of those are worse than the alternative.

## Hard Facts
- I am here under the Revenue Act. Everything I do, I will tell you I am doing.
- I do not take anything from anybody. Not a drink, not a lift, not a favour.
- What I am asked to inspect is set out in the letter. What I inspect beyond it depends on the cooperation I receive.
- I have been doing this for nineteen years and I have never once been surprised by a bar.
";

        // ---- the three verbs ----

        /// Today's item: produce it, or tell him to put it in writing.
        ///
        /// The one Act III verb that is not irreversible and costs no money.
        /// It is available every day of the six and it does exactly one thing —
        /// it moves how much of the business gets read. Which is the only thing
        /// about this man that can be moved at all.
        public bool AnswerInspector(bool cooperate)
        {
            if (!ActThree.Opened || ActThree.AuditClosed || !ActThree.InspectorArrived) return false;
            if (ActThree.InspectorAskedDay != Now.Day) return false;   // one item a day, and he has to have asked
            ActThree.InspectorAskedDay = -1;

            if (cooperate)
            {
                ActThree.Cooperations++;
                ToastLine(ActThreeState.CooperateText, 13f);
            }
            else
            {
                ActThree.Stonewalls++;
                ToastLine(ActThreeState.StonewallText, 14f);
                // Lena has watched a revenue man be told to put it in writing
                // before, and she knows how that one went.
                _gossip?.Mill?.Get("Lena")?.Memory.Append(new MemoryEvent(Now, "observation", 0.9,
                    "They sent the excise man away with a piece of paper today. " +
                    "Mickey did that once. It did not go the way he thought it would."));
            }
            return true;
        }

        /// Has he asked for something today that is still unanswered?
        public bool InspectorWaiting => ActThree.Opened && !ActThree.AuditClosed
            && ActThree.InspectorArrived && ActThree.InspectorAskedDay == Now.Day;

        // ---- PP5: the last day ----

        /// What, if anything, this person is worth reaching on the last day.
        /// Null when there is nothing to say to them that would change anything,
        /// which is most people — and is the point.
        public string LastDayOffer(string whoId)
        {
            if (!ActThree.IsLastDay(Now.Day) || ActThree.LastDayLeft <= 0) return null;
            if (whoId == "Lena") return ActThree.LedgersMoved ? null : "Ask her to move the books";
            if (Empire.CrewOf(whoId) != null) return "Tell them to go quiet";
            var g = _gossip?.Mill?.Get(whoId);
            if (g != null && g.Circle != "night" && Empire.CrewOf(whoId) == null
                && whoId != ActThreeState.InspectorName && whoId != "Ellis")
                return "Tell them yourself, before the street does";
            return null;
        }

        /// Spend one of the last day's two calls.
        ///
        /// Every one of these moves state the endings already read — the books,
        /// the crew count, a relationship — so none of them is an ending button
        /// wearing a conversation. And all three run just as well down a
        /// telephone line, which is what turns "whoever picks up is the campaign
        /// you actually played" from a nice sentence into a mechanic.
        public bool SpendLastDay(string whoId)
        {
            if (LastDayOffer(whoId) == null) return false;
            var mill = _gossip?.Mill;

            if (whoId == "Lena")
            {
                double loyalty = mill?.Get("Lena")?.Loyalty ?? 0;
                bool willing = ActThreeState.WillMoveTheLedgers(loyalty);
                ToastLine(ActThreeState.LastDayLenaText(willing), 16f);
                ActThree.LastDayActions++;      // the call is spent either way
                if (!willing) return true;
                ActThree.LedgersMoved = true;
                mill?.Get("Lena")?.Memory.Append(new MemoryEvent(Now, "conversation", 1.0,
                    "I moved Mickey's books the night before the inspection because they asked me to. " +
                    "I have thought about that evening more than any other."));
                return true;
            }

            var crew = Empire.CrewOf(whoId);
            if (crew != null)
            {
                ActThree.LastDayActions++;
                crew.Departed = true;
                crew.Assignment = null;
                ToastLine(ActThreeState.LastDayCrewText(crew.Name), 14f);
                var g = mill?.Get(whoId);
                g?.Memory.Append(new MemoryEvent(Now, "conversation", 0.95,
                    "They told me to go and not come back, and they told me before it happened rather than after. " +
                    "That is not nothing. It is not much, but it is not nothing."));
                if (g != null) g.Loyalty = Mathf.Clamp01((float)g.Loyalty + 0.1f);
                return true;
            }

            // The day life. The only repair this game has ever offered one of
            // these relationships is hearing it from you first.
            var friend = mill?.Get(whoId);
            if (friend == null) return false;
            ActThree.LastDayActions++;
            friend.Loyalty = Mathf.Clamp01((float)friend.Loyalty + 0.28f);
            friend.Memory.Append(new MemoryEvent(Now, "conversation", 1.0,
                "They came and told me the whole of it themselves, the day before it broke. " +
                "I did not take it well. I would rather have had it that way than the other."));
            // They now genuinely know, and knowing is a fact in this world
            // rather than a mood — it goes into the mill like anything else.
            mill.Witness(whoId, new Fact("player", "confessed", "true"),
                "the one who owns the bar told me what they have really been doing, to my face", true, Now, 1.0);
            ToastLine(ActThreeState.LastDayTruthText(friend.DisplayName ?? whoId), 15f);
            return true;
        }

        /// Sell up, pay everyone off, take the loss. The straight life is bought
        /// with the empire, at a bad price, and it cannot be undone.
        public bool SellUp()
        {
            if (!ActThree.Opened || ActThree.AuditClosed || ActThree.SoldUp) return false;
            int raised = Empire.Dissolve(Wallet, _gossip?.Mill, Now);
            ActThree.SoldUp = true;
            ToastLine("Hal does it in an afternoon, for a percentage, without once asking why. " +
                      $"Everything you took a year to build goes in six hours and raises ${raised}. " +
                      "The bar is a bar again, and the cellar is a cellar.", 16f);
            return true;
        }

        /// Point the audit at somebody else.
        ///
        /// The arm you give up is the one that has been hardest on you, which
        /// makes it feel like justice right up until the bill: everything you
        /// know about them, you know because somebody told you, and the street
        /// knows who talks. That person is burned by name.
        public bool Deflect()
        {
            if (!ActThree.Opened || ActThree.AuditClosed || ActThree.Deflected) return false;
            if (!EllisSpawned || EllisInterviews.Count == 0) return false;
            var mill = _gossip?.Mill;
            if (mill == null) return false;

            RivalArm worst = null;
            foreach (var a in Empire.Arms)
                if (worst == null || a.Attention > worst.Attention) worst = a;
            if (worst == null || worst.Attention < 0.25) return false;

            ActThree.Deflected = true;
            ActThree.DeflectedOnto = worst.Id;
            worst.Attention = Mathf.Clamp01((float)worst.Attention + 0.3f);
            worst.Standing = Mathf.Clamp01((float)worst.Standing - 0.4f);

            // Somebody's statement is what made this possible, and the street
            // works out whose. This is the cost, and it is a person.
            var burned = FirstInformant();
            if (burned != null)
            {
                ActThree.BurnedWitnessId = burned.Id;
                burned.Loyalty = Mathf.Clamp01((float)burned.Loyalty - 0.5f);
                burned.Memory.Append(new MemoryEvent(Now, "observation", 1.0,
                    "What I said in confidence came back out of a revenue office with my name on it. " +
                    "I know exactly who it went through."));
                mill.Witness(burned.Id, new Fact("player", "informs", "police"),
                    "the one who owns the bar talks to the revenue people, and uses what you tell them", true, Now, 0.9);
                ToastLine($"It is pointed elsewhere by the end of the week. {burned.DisplayName} finds out " +
                          "on Thursday, from somebody who was not being cruel about it.", 15f);
            }
            else ToastLine("It is pointed elsewhere by the end of the week. Nobody says anything to you about it at all.", 13f);

            _ossei?.Memory.Append(new MemoryEvent(Now, "conversation", 0.95,
                $"The bar's owner gave me the {worst.Id} arm, with enough to work with. " +
                "I took it. I would like to say I did not enjoy how quickly they decided."));
            return true;
        }

        /// Whoever gave Ellis her first statement about you. The one who talked
        /// is the one who gets burned — never a random pick.
        Gossiper FirstInformant()
        {
            if (EllisInterviews.Count == 0 || _gossip?.Mill == null) return null;
            var first = EllisInterviews[0];
            int cut = first.IndexOf(" told you:", System.StringComparison.Ordinal);
            var name = cut > 0 ? first.Substring(0, cut) : null;
            return name != null ? _gossip.Mill.Get(name) : null;
        }

        /// Sign it over. The only ending you have to reach for.
        public bool HandOver(string crewId)
        {
            if (!ActThree.Opened || ActThree.AuditClosed || ActThree.SuccessorId != null) return false;
            var ready = ReadySuccessor();
            if (ready == null || ready.Id != crewId) return false;

            ActThree.SuccessorId = ready.Id;
            var g = _gossip?.Mill?.Get(ready.Id);
            g?.Memory.Append(new MemoryEvent(Now, "conversation", 1.0,
                "It is mine. Signed, in daylight, with the revenue people already asking questions. " +
                "They knew what they were handing me and they handed it to me anyway."));
            ToastLine($"You sign it over to {ready.Name}. They read every page, which nobody has ever done " +
                      "in front of you before, and then they put their name under yours.", 15f);
            return true;
        }

        /// The act's line in the ledger screen. A date and a shape, never a
        /// countdown and never a number.
        public string ActThreeLedgerLine()
        {
            if (!ActThree.Opened) return null;
            if (ActThree.AuditClosed)
                return ActThree.Result == Ending.Quiet && ActThree.EpilogueDay >= 0
                    ? "-- it is not yours anymore --"
                    : "-- the books have been opened --";
            var s = Books();
            var sb = new System.Text.StringBuilder();
            sb.Append("-- the audit --\n");
            sb.Append($"  the inspection is set for day {ActThree.AuditClosesDay}\n");
            sb.Append($"  {ActThreeState.StrainWord(ActThreeState.LedgerStrain(s))}\n");
            if (ActThree.SoldUp) sb.Append("  there is nothing left for them to find\n");
            if (ActThree.Deflected) sb.Append("  they are looking somewhere else, and somebody paid for that\n");
            if (ActThree.SuccessorId != null) sb.Append($"  it is {s.SuccessorName}'s name on the licence now\n");
            return sb.ToString();
        }

        /// Capture/restore hangs off the main save; kept here so the act owns
        /// its own persistence the way every other system does.
        public Dictionary<string, object> CaptureActThree() => ActThree.Capture();
        public void RestoreActThree(Dictionary<string, object> d) => ActThree.Restore(d);
    }
}
