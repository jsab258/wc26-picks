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
                OsseiCaseAnswerable = ActThree.Deflected,
                TotalWashed = Wallet.TotalWashed,
                TotalRacketIncome = e.TotalRacketIncome,
                BarTakingsToDate = TotalTakings,
                HandedOver = ActThree.SuccessorId != null,
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
            s.HasReadySuccessor = ready != null || ActThree.SuccessorId != null;
            if (ActThree.SuccessorId != null)
            {
                s.SuccessorId = ActThree.SuccessorId;
                s.SuccessorName = Empire.Crew.Find(c => c.Id == ActThree.SuccessorId)?.Name ?? ActThree.SuccessorId;
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

        void CheckActThree()
        {
            if (!Campaign.OpenMode || _gossip == null || _gossip.Mill == null) return;

            if (ActThree.AuditClosed) { TickEpilogue(); return; }

            if (!ActThree.Opened)
            {
                // Ossei can name the rackets when she has statements AND has
                // joined the two cases — PP6 is exactly that moment.
                bool osseiCanName = OsseiSpawned && ActTwo.Pp6Fired && OsseiInterviews.Count >= 2;
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
                    "A revenue letter came for the bar. Marek got one of those once. " +
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

            // PP3 — Ossei's offer. She comes to you, once, with two days left,
            // and she does not come at all if she was never on the case.
            if (!ActThree.Pp3Fired && OsseiSpawned && DaysLeftOnAudit <= 3)
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
            ToastLine(ActThreeState.EndingText(ActThree.Result, s.SuccessorName), 22f);
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

        // ---- the three verbs ----

        /// Sell up, pay everyone off, take the loss. The straight life is bought
        /// with the empire, at a bad price, and it cannot be undone.
        public bool SellUp()
        {
            if (!ActThree.Opened || ActThree.AuditClosed || ActThree.SoldUp) return false;
            int raised = Empire.Dissolve(Wallet, _gossip?.Mill, Now);
            ActThree.SoldUp = true;
            ToastLine("Halvard does it in an afternoon, for a percentage, without once asking why. " +
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
            if (!OsseiSpawned || OsseiInterviews.Count == 0) return false;
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

        /// Whoever gave Ossei her first statement about you. The one who talked
        /// is the one who gets burned — never a random pick.
        Gossiper FirstInformant()
        {
            if (OsseiInterviews.Count == 0 || _gossip?.Mill == null) return null;
            var first = OsseiInterviews[0];
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
