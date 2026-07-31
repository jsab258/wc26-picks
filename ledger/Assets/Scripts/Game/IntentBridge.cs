using System.Collections.Generic;
using System.Text;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// The game-side half of the intent router (roadmap M6.5, design doc §17).
    /// Kept in its own file — DialogueUI is long enough — but part of the same
    /// class, because everything here needs the live dialogue state.
    ///
    /// Two jobs:
    ///
    ///  1. BUILD THE CATALOGUE of verbs available in this exact moment. It does
    ///     this by reading the ACTUAL BUTTONS: a verb is offered to the router if
    ///     and only if its button is on screen and clickable. That is not laziness
    ///     — it makes drift between what the player can click and what they can
    ///     say structurally impossible. Add a button, the router learns the verb.
    ///
    ///  2. EXECUTE a routed verb by calling the SAME handler the button calls.
    ///     There is exactly one implementation of "pay off"; typing it and
    ///     clicking it are the same code path, so they cannot disagree.
    ///
    /// Novel actions are the third path: the router says what the attempt should
    /// cost and what it should move, the Adjudicator decides whether it lands
    /// using nothing but simulation numbers, and ApplyNovel writes the (small,
    /// clamped) result into the same systems everything else writes into.
    public partial class DialogueUI
    {
        IntentRouter _router;

        /// Plain-language phrasing of whatever the two context-sensitive empire
        /// buttons currently mean. Set beside their labels so the router is told
        /// what the button DOES, not what its label happens to read.
        string _empireSayA, _empireSayB;

        IntentRouter Router
        {
            get
            {
                if (_router == null)
                {
                    // No client (no API key) is not a failure: the lexical path is
                    // the whole router then, and it costs nothing.
                    _router = new IntentRouter(_game != null ? _game.Llm : null,
                                               _game != null ? _game.Cost : null);
                }
                return _router;
            }
        }

        // ---------------------------------------------------------------
        // 1. The catalogue
        // ---------------------------------------------------------------

        /// activeInHierarchy, not activeSelf: the damage-control buttons live under
        /// a row that is hidden wholesale, and a button inside a hidden row is not
        /// something the player could click — so it is not something they can say.
        static bool Live(Button b) => b != null && b.gameObject.activeInHierarchy && b.interactable;

        IntentContext BuildIntentContext()
        {
            var ctx = new IntentContext
            {
                SpeakingTo = _current != null ? _current.Card.Name : null,
                Scene = SceneLine(),
            };

            if (Live(_payBtn))
            {
                var lead = CurrentLead();
                ctx.Verbs.Add(new VerbSpec("pay_off", "pay them to stop repeating it",
                        lead != null ? $"about £{BribePriceFor(lead)}; you have £{_game.PlayerCash}" : null)
                    .WithLexical("pay them off", "pay him off", "pay her off", "buy their silence",
                                 "buy his silence", "buy her silence", "offer them money"));
            }
            if (Live(_leanBtn))
            {
                ctx.Verbs.Add(new VerbSpec("lean_on", "frighten them into keeping it to themselves")
                    .WithLexical("lean on them", "lean on him", "lean on her",
                                 "scare them", "put the frighteners", "make them afraid"));
            }
            if (Live(_doubtBtn))
            {
                ctx.Verbs.Add(new VerbSpec("plant_doubt", "put a counter-story about into the street")
                    .WithLexical("plant doubt", "spread a counter", "muddy the water",
                                 "muddy the waters", "start a different story"));
            }
            if (Live(_hookBtn))
            {
                var hook = CurrentHostHook();
                ctx.Verbs.Add(new VerbSpec("use_hook", "use what you know about them against them",
                        hook != null ? (hook.Strong ? "you hold something serious" : "you hold something small") : null)
                    .WithLexical("use what i know", "use what you know", "remind them what i know",
                                 "hold it over them", "blackmail them"));
            }
            if (Live(_collectBtn))
            {
                var debtor = _game.Debts.Of(CurrentHostId() ?? "");
                ctx.Verbs.Add(new VerbSpec("collect_debt", "ask them for the money they owe",
                        debtor != null ? $"£{debtor.Amount} outstanding" : null)
                    .WithLexical("collect the debt", "collect what they owe", "call in the debt",
                                 "ask for my money", "want my money"));
            }
            if (Live(_forgiveBtn))
            {
                var debtor = _game.Debts.Of(CurrentHostId() ?? "");
                ctx.Verbs.Add(new VerbSpec("forgive_debt", "cancel what they owe, in front of them",
                        debtor != null ? $"£{debtor.Amount} written off" : null)
                    .WithLexical("tear out the page", "forgive the debt", "write it off",
                                 "forget the debt", "wipe the slate"));
            }
            // The two empire buttons mean something different in every context, so
            // their phrasing comes from whoever set the label.
            if (Live(_empireBtnA) && !string.IsNullOrEmpty(_empireSayA))
                ctx.Verbs.Add(new VerbSpec("empire_a", _empireSayA, _empireLabelA != null ? _empireLabelA.text : null));
            if (Live(_empireBtnB) && !string.IsNullOrEmpty(_empireSayB))
                ctx.Verbs.Add(new VerbSpec("empire_b", _empireSayB, _empireLabelB != null ? _empireLabelB.text : null));

            // Names a novel action may legitimately be aimed at: whoever is in the
            // room, your crew, and the three heads.
            if (_current != null) ctx.KnownPeople.Add(CurrentHostId() ?? _current.Card.Name);
            foreach (var c in _game.Empire.ActiveCrew) ctx.KnownPeople.Add(c.Name);
            foreach (var a in _game.Empire.Arms) ctx.KnownPeople.Add(a.HeadName);

            return ctx;
        }

        string SceneLine()
        {
            var sb = new StringBuilder();
            sb.Append(_game.Campaign.OpenMode ? "the open city" : "Hook Street");
            sb.Append(", day ").Append(_game.Now.Day);
            var lead = CurrentLead();
            if (lead != null) sb.Append("; they are carrying talk about you");
            if (_game.Empire.Patron != null) sb.Append("; you fly ").Append(_game.Empire.Patron.HeadName).Append("'s banner");
            return sb.ToString();
        }

        // ---------------------------------------------------------------
        // 2. Execution
        // ---------------------------------------------------------------

        /// The button a verb id belongs to. Checked for liveness before the line
        /// is committed to, because the world keeps moving while a model thinks
        /// and a verb that has expired in the meantime must not fire.
        Button ButtonFor(string verbId)
        {
            switch (verbId)
            {
                case "pay_off":      return _payBtn;
                case "lean_on":      return _leanBtn;
                case "plant_doubt":  return _doubtBtn;
                case "use_hook":     return _hookBtn;
                case "collect_debt": return _collectBtn;
                case "forgive_debt": return _forgiveBtn;
                case "empire_a":     return _empireBtnA;
                case "empire_b":     return _empireBtnB;
                default: return null;
            }
        }

        /// Runs a routed verb through the SAME handler its button uses. There is
        /// one implementation of each verb; typing it and clicking it are the
        /// same code, so they cannot drift apart.
        bool ExecuteVerb(string verbId)
        {
            if (!Live(ButtonFor(verbId))) return false;
            switch (verbId)
            {
                case "pay_off":      PayOff(); return true;
                case "lean_on":      LeanOn(); return true;
                case "plant_doubt":  PlantDoubt(); return true;
                case "use_hook":     UseHook(); return true;
                case "collect_debt": CollectDebt(); return true;
                case "forgive_debt": ForgiveDebt(); return true;
                case "empire_a":     EmpireAct(false); return true;
                case "empire_b":     EmpireAct(true); return true;
                default: return false;
            }
        }

        // ---------------------------------------------------------------
        // 3. Novel actions
        // ---------------------------------------------------------------

        AdjudicationInput NovelState(Intent intent)
        {
            var e = _game.Empire;
            var arm = ArmFor(intent);
            return new AdjudicationInput
            {
                Clean = _game.Wallet.Clean,
                Dirty = _game.Wallet.Dirty,
                Crew = System.Linq.Enumerable.Count(e.ActiveCrew),
                Hour = _game.Now.Hour,
                Standing = arm != null ? arm.Standing : 0.0,
                Heat = _game.CurrentHeat,
                HoldsHook = CurrentHostHook() != null,
            };
        }

        /// Which organization a novel action touches: the named target's employer
        /// if they have one, else the arm the target heads, else whoever you fly
        /// for, else the one paying you the most attention.
        RivalArm ArmFor(Intent intent)
        {
            var e = _game.Empire;
            var name = string.IsNullOrEmpty(intent.Target) ? CurrentHostId() : intent.Target;
            if (!string.IsNullOrEmpty(name))
            {
                var heads = e.Arms.Find(a => a.HeadName == name);
                if (heads != null) return heads;
                var employer = e.ArmOfMember(name);
                if (employer != null) return employer;
            }
            if (e.Patron != null) return e.Patron;
            RivalArm loudest = null;
            foreach (var a in e.Arms) if (loudest == null || a.Attention > loudest.Attention) loudest = a;
            return loudest;
        }

        /// Writes an adjudicated novel action into the simulation. Everything here
        /// is small by construction (magnitude is clamped at 0.15 twice over) and
        /// nothing here pays the player.
        void ApplyNovel(Intent intent, Adjudication verdict)
        {
            if (verdict.CashSpent > 0)
                _game.Wallet.Spend(verdict.CashSpent, dirtyOk: verdict.SpentDirty);

            var arm = ArmFor(intent);
            double m = verdict.Magnitude;

            switch (verdict.Effect)
            {
                case Effects.StandingUp:
                    if (arm != null) arm.Standing = Mathf.Clamp((float)(arm.Standing + m), -1f, 1f);
                    break;
                case Effects.StandingDown:
                    if (arm != null) arm.Standing = Mathf.Clamp((float)(arm.Standing - m), -1f, 1f);
                    break;
                case Effects.AttentionUp:
                    if (arm != null) arm.Attention = Mathf.Max(0f, (float)(arm.Attention + m));
                    break;
                case Effects.AttentionDown:
                    if (arm != null) arm.Attention = Mathf.Max(0f, (float)(arm.Attention - m));
                    break;
                case Effects.SuspicionUp:
                    _current?.Suspicion?.Raise(m, "something the new owner tried");
                    break;
                case Effects.SuspicionDown:
                    _current?.Suspicion?.Lower(m, "the new owner smoothed something over");
                    break;
                case Effects.Rumor:
                    SeedNovelRumor(intent, m);
                    break;
            }
        }

        /// The one novel effect that touches the gossip network. It enters through
        /// the ordinary Witness path at LOW confidence, so it decays, spreads, and
        /// can be contradicted exactly like anything else the street half-saw. A
        /// player cannot use this to plant a certainty.
        void SeedNovelRumor(Intent intent, double magnitude)
        {
            var holder = CurrentHostId();
            if (string.IsNullOrEmpty(holder) || _game.Gossip.Mill.Get(holder) == null) return;
            var summary = string.IsNullOrEmpty(intent.Because)
                ? "the new owner was talking about something they shouldn't have been"
                : intent.Because;
            _game.Gossip.Mill.Witness(holder,
                new Fact("player", "loose_talk_d" + _game.Now.Day, summary),
                summary, sensitive: false, now: _game.Now,
                confidence: Mathf.Clamp((float)(0.2 + magnitude), 0.2f, 0.45f));
        }

        // ---------------------------------------------------------------
        // 4. Narration
        // ---------------------------------------------------------------

        /// What a novel action reads like. The game never claims more than it did:
        /// a failed check says plainly why, and a passed one says what it moved.
        string NovelLine(Intent intent, Adjudication verdict)
        {
            if (!verdict.Passed) return $"You start to — and stop. {Capitalize(verdict.Reason)}.";

            var arm = ArmFor(intent);
            string who = arm != null ? arm.HeadName + "'s people" : "the street";
            string cost = verdict.CashSpent > 0 ? $" (-£{verdict.CashSpent})" : "";

            switch (verdict.Effect)
            {
                case Effects.StandingUp:   return $"It lands. {who} will remember you did that{cost}.";
                case Effects.StandingDown: return $"It lands, and it costs you. {who} won't forget it either{cost}.";
                case Effects.AttentionUp:  return $"It works. It also puts you further up {who}'s list{cost}.";
                case Effects.AttentionDown:return $"It works, quietly. {who} have other things to look at for a while{cost}.";
                case Effects.SuspicionUp:  return $"They go along with it. They also look at you a beat too long{cost}.";
                case Effects.SuspicionDown:return $"They let it go. Whatever they were wondering about, they stop{cost}.";
                case Effects.Rumor:        return $"You say it. It's out of your hands the moment it leaves your mouth{cost}.";
                default:                   return $"It goes the way you meant it to{cost}.";
            }
        }

        static string Capitalize(string s) =>
            string.IsNullOrEmpty(s) ? s : char.ToUpperInvariant(s[0]) + s.Substring(1);
    }
}
