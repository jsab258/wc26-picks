using System.Collections.Generic;
using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// M18, wired in the same commit as its Core. The person at your shoulder.
    ///
    /// WIRED IMMEDIATELY, for the reason `HouseholdHost` says out loud: a Core
    /// system with no caller is this project's oldest failure, and the reach
    /// ledger it would otherwise go on is supposed to count DOWN. `Brandish`,
    /// `MayFrisk` and `Acquire` all sat at zero callers for a month while
    /// reading as finished work.
    ///
    /// HOW LITTLE IS IN HERE IS THE POINT. There is no companion perception
    /// pass, no follower witness hook, no "escort saw it" branch anywhere in
    /// the game. `Witnesses.Resolve` walks every `NpcWalker` within eighty
    /// metres of a deed and hands each to `Observe.Resolve`, so an escort is a
    /// witness through the same path as the man across the road. That part is
    /// true and is the whole design.
    ///
    /// **THE SENTENCE THAT USED TO BE HERE WAS WRONG IN THREE PLACES, and I
    /// spent a night reasoning from it.** It said that setting
    /// `NpcWalker.Escorting` "puts a person at the player's shoulder, and from
    /// that moment" they are handed a two-metre sightline, a face-toward of
    /// TRUE, and `SecondsWatching` from their stance.
    ///
    ///   - IT SETS A TARGET, NOT A POSITION. They have to walk there.
    ///     `CompanionHost.Ask` has no proximity requirement, so the sim
    ///     recruits whoever is willing wherever they stand — and the build
    ///     read `companionSight dist=31.0m`. At 1.4 m/s that is twenty-two
    ///     seconds away, during which she sees what somebody thirty metres off
    ///     sees, which is correctly almost nothing.
    ///   - FACE-TOWARD IS COMPUTED, NOT TRUE. `Witnesses` has its own note
    ///     saying the first draft hardcoded it and that a constant there
    ///     "decides identification for the whole street". The escort walks
    ///     half a metre BEHIND the shoulder, so it is usually false and rung 3
    ///     is unreachable for her by design. Rung 4 is the one she should
    ///     get, and that needs familiarity.
    ///   - `SecondsWatching` NO LONGER COMES FROM STANCE. It was changed on
    ///     3 August to the accrued attention the walker already measures,
    ///     because stance is the SUSPICION ladder and loyalty pulls it down —
    ///     so the one person guaranteed to be looking at you was scored as not
    ///     looking.
    ///
    /// Every one of those was true when written. Together they described a
    /// companion who could not fail to see, which is why three rounds of
    /// diagnosis went looking anywhere except at whether she had arrived.
    ///
    /// That is why this file reads the witness record rather than writing one.
    /// The only thing it does at a deed is note the EVENT ID against the
    /// companion, and even that is bookkeeping: the observation itself already
    /// exists and belongs to `Witnesses`.
    public class CompanionHost
    {
        /// Everybody who has ever walked with the player this run, departed or
        /// not — because somebody who left carrying six things you did is more
        /// interesting than somebody who is still here.
        readonly List<Companion> _all = new List<Companion>();
        public IReadOnlyList<Companion> All => _all;

        public Companion Current { get; private set; }
        public NpcWalker Walking { get; private set; }

        /// Counters the sim reads. `Recruited` and `Departed` together are the
        /// evidence the thing ran at all — a companion system that never
        /// attached anybody reports a serene zero exposure.
        public int Recruited { get; private set; }
        public int Departed { get; private set; }
        public int Noted { get; private set; }
        public int LastAdds { get; private set; }
        /// How much walked out of the door the last time somebody did.
        public int CarriedOut { get; private set; }

        /// Ask somebody to come out with you.
        ///
        /// The loyalty and nerve come from the `Gossiper`, which is the same
        /// record `Empire` reads when deciding whether a crew member walks and
        /// `GossipMill` reads when deciding whether they repeat what they know.
        /// ONE SOURCE, deliberately: a companion whose loyalty lived in its own
        /// field would drift from the loyalty everything else consults, and the
        /// entire design is that these are the same number.
        public bool Ask(Gossiper g, NpcWalker body, int day, Transform player = null)
        {
            if (g == null || body == null) return false;
            if (Current != null && !Current.Departed) return false;
            if (!Escort.WillWalk(g.Loyalty, g.Nerve)) return false;

            var c = _all.Find(x => x.Id == g.Id);
            if (c == null)
            {
                c = new Companion { Id = g.Id, Name = g.DisplayName, SinceDay = day };
                _all.Add(c);
            }
            else
            {
                // COMING BACK DOES NOT WIPE WHAT THEY SAW. A companion who
                // left and returned still knows the six things they stood next
                // to, and a design where reconciliation launders them would
                // make walking away a way to clear your record.
                c.Departed = false;
                c.WhyLeft = "";
                c.SinceDay = day;
            }

            Current = c;
            Walking = body;
            body.Escorting = true;

            // AND TELL THEM WHERE YOU ARE, HERE, ONCE, PERMANENTLY.
            //
            // THE BUG THIS FIXES, and it was self-reinforcing. `NpcWalker`
            // learns the player's transform from exactly one place —
            // `GossipDirector.TickStances`, a proximity sweep over the bodies
            // that are live right now. An escort who falls behind drops out of
            // that sweep, so `_player` stops being refreshed; and both the
            // escort's target selection AND its catch-up speed are guarded on
            // `_player != null`. Fall behind, stop being told where to go, fall
            // further behind.
            //
            // `companionSight[dist=29.4m]` is that loop, and it survived the
            // catch-up-speed fix untouched because the speed was never the
            // problem: a walker with no player reference does not hurry
            // anywhere, it just keeps its schedule.
            //
            // The companion is the one walker whose relationship to the player
            // is permanent, so it must not depend on a proximity sweep to know
            // who they are following.
            if (player != null) body.SetPlayer(player);
            // Already looking, which is what `Vantage.SecondsWatching` reads.
            // Not a cheat: somebody walking beside you IS watching you, and
            // the alternative — an escort mid-stride and oblivious — is the
            // version where the feature has no cost.
            if (body.Stance < StanceKind.Watches) body.Stance = StanceKind.Watches;
            Recruited++;
            return true;
        }

        /// Check whether the one walking with you has stopped being yours.
        ///
        /// CALLED NIGHTLY RATHER THAN ON A TRIGGER, because loyalty moves for
        /// reasons that have nothing to do with the companion — `Empire`
        /// squeezes it, cuts move it, the rival poaches against it. The
        /// departure has to be able to happen for any of those, which means
        /// asking the question on the clock rather than at the moment the
        /// player does something.
        public bool CheckLoyalty(Gossiper g, int day)
        {
            if (Current == null || Current.Departed || g == null) return false;
            if (!Escort.WalksAway(g.Loyalty)) return false;

            Current.Departed = true;
            Current.LeftDay = day;
            Current.WhyLeft = $"loyalty {g.Loyalty:0.00} below {Escort.WalksAwayBelow:0.00}";
            if (Walking != null) Walking.Escorting = false;
            Walking = null;
            Departed++;

            // AND WHAT THEY TAKE WITH THEM, NAMED AT THE MOMENT THEY GO.
            //
            // `Escort.CarriesAway` was unreached when this file was first
            // written — I built the API for exactly this moment and then wrote
            // the departure without calling it, which is the failure this
            // project has on its wall (`Brandish` 0, `MayFrisk` 0, `Acquire`
            // 0). The reach check caught it in the same session, which is the
            // whole reason that check exists.
            //
            // Logged rather than pushed into the mill FOR NOW, and the
            // distinction is deliberate: every one of these is already an
            // `Observation` held by `Witnesses`, at full rung, produced when
            // it happened. The betrayal does not need to manufacture evidence
            // — it needs to stop suppressing it, and routing it into
            // `GossipMill` belongs with the M19 work on how testimony reaches
            // the law. Naming it here makes the accumulation visible in a run
            // instead of invisible until then.
            CarriedOut = Escort.CarriesAway(Current).Count;
            Debug.Log($"CompanionHost: {Current.Id} walked — {Current.WhyLeft}, "
                      + $"carrying {CarriedOut} thing(s) they stood next to you for"
                      + (CarriedOut > 0 ? $": {string.Join(", ", Escort.CarriesAway(Current))}" : ""));
            return true;
        }

        /// A deed happened; note it against whoever was standing next to you.
        ///
        /// GUARDED ON THE WITNESS RECORD AND NOT ON PROXIMITY. It would be
        /// easy to write `if (distance < 5) c.Saw(...)` here, and it would be
        /// a second opinion about who saw what — a copy of the perception
        /// model, living beside the real one and free to disagree with it.
        /// This project has had that fault four times in one day. So the
        /// question "did they see it" is asked of the thing that answers it:
        /// the `Observation` that `Witnesses.Resolve` already produced for
        /// them. An escort who was somehow blind — round a corner, in the
        /// dark, arrived late — is not noted, because the model said so.
        public void NoteDeed(string eventId)
        {
            if (Current == null || Current.Departed || Walking == null) return;
            foreach (var o in Witnesses.Last)
            {
                if (o == null || o.Empty) continue;
                if (o.WitnessId != Walking.DisplayName) continue;
                Current.Saw(eventId);
                Noted++;
                return;
            }
        }

        /// WHAT THEY SEE THAT YOU DO NOT — the half of the trade the player
        /// gets, and it costs no new number at all.
        ///
        /// Both lists come from the same perception model, evaluated from two
        /// different places: who is watching the player from the player's own
        /// position and facing, and who is watching from the companion's.
        /// `Escort.Adds` subtracts. So a companion who walks where you walk and
        /// looks where you look tells you nothing, and one covering your back
        /// tells you what is behind you — which makes WHERE THEY WALK a real
        /// thing rather than a modifier on a stat.
        public List<string> WatchersTheyAdd(Transform player)
        {
            var adds = new List<string>();
            if (Current == null || Current.Departed || Walking == null || player == null)
            { LastAdds = 0; return adds; }

            var mine = new List<string>();
            var theirs = new List<string>();
            foreach (var npc in Object.FindObjectsByType<NpcWalker>(FindObjectsSortMode.None))
            {
                if (npc == null || npc == Walking) continue;
                if (npc.Stance < StanceKind.Watches) continue;
                var at = npc.transform.position + Vector3.up * 1.6f;
                if (Sees(player, at)) mine.Add(npc.DisplayName);
                if (Sees(Walking.transform, at)) theirs.Add(npc.DisplayName);
            }
            adds.AddRange(Escort.Adds(mine, theirs));
            LastAdds = adds.Count;
            return adds;
        }

        /// One sightline through the ordinary model. `Perceivers` owns light,
        /// occlusion and off-axis; nothing is re-derived here, because a second
        /// copy of a threshold is how the wet-road value drifted from itself.
        static bool Sees(Transform eye, Vector3 targetHead)
        {
            if (eye == null) return false;
            float m = Vector3.Distance(eye.position, targetHead);
            if (Perceivers.Occluded(eye.position + Vector3.up * 1.6f, targetHead)) return false;
            return Perception.InSight(m, Perceivers.OffAxis(eye, targetHead),
                                      Perceivers.LevelAt(targetHead), false);
        }

        /// One line for the verdict, so a run can be judged on it.
        ///
        /// `exposure` is what walks out of the door if they turn — the count of
        /// things they were standing next to you for. Reported and never fed
        /// back, the same rule `Household.MeanBond` carries: the moment an
        /// ending calculation consumes it, the relationship has become a stat
        /// and M18's done-condition has been quietly failed.
        public string Report()
        {
            string who = Current == null ? "none"
                       : $"{Current.Id}{(Current.Departed ? "(left)" : "")}";
            return $"companion[with={who} recruited={Recruited} departed={Departed} "
                 + $"noted={Noted} exposure={Escort.Exposure(Current)} adds={LastAdds} "
                 + $"carriedOut={CarriedOut}]";
        }
    }
}
