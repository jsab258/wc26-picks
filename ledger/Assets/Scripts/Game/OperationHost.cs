using System.Collections.Generic;
using System.Linq;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The game-side half of operation planning (roadmap M7.5).
    ///
    /// Building the state a plan is judged against, running the job, and — the
    /// part that makes it belong to THIS game rather than to any heist game —
    /// pushing the aftermath into the systems that already exist. Witnesses go
    /// into the gossip mill as ordinary sightings, so a job you were seen at
    /// becomes talk, and talk becomes heat, and heat is what closes the quiet
    /// loft above the laundry. Crew who came away rattled write it into their
    /// own memory in their own words, and that memory is what the model reads
    /// the next time you speak to them.
    ///
    /// Nothing here decides an outcome. Operations.Run does that, in Core, from
    /// numbers. This is the wiring on either side of it.
    public partial class GameController
    {
        public List<OperationTarget> Targets { get; } = OperationSetup.Build();
        /// The plan the player is currently assembling. Never null once the
        /// panel has been opened; null means they have not looked yet.
        public OperationPlan Plan;

        public OperationTarget TargetOf(string id) => Targets.FirstOrDefault(t => t.Id == id);
        public IEnumerable<OperationTarget> OpenTargets => Targets.Where(t => !t.Done);

        /// Jobs only exist once the city is open. During the week the player has
        /// an outfit telling them where to be; the point of the open city is
        /// that nobody does any more.
        public bool CanPlan => Campaign.OpenMode;

        public OperationState BuildOperationState()
        {
            var s = new OperationState
            {
                Heat = CurrentHeat,
                Coated = WearingCoat,
                // Nerve grows with what you have actually come through. Not a
                // stat the player raises — a record of nights survived.
                Nerve = Mathf.Clamp01(0.35f + 0.05f * Campaign.JobsDone - 0.10f * Campaign.Falls),
            };
            var mill = _gossip != null ? _gossip.Mill : null;
            foreach (var c in Empire.ActiveCrew)
            {
                s.Competence[c.Name] = c.Competence;
                var g = mill != null ? mill.Get(c.Name) : null;
                s.Loyalty[c.Name] = g != null ? g.Loyalty : 0.5;
            }
            return s;
        }

        public PlanRead ReadPlan()
        {
            if (Plan == null) return null;
            var target = TargetOf(Plan.TargetId);
            return target == null ? null : Operations.Read(Plan, target, BuildOperationState());
        }

        /// Does the job. Returns the outcome for the UI to narrate; everything
        /// that outlives the moment has already been written into the world.
        public OperationOutcome RunPlan()
        {
            var target = Plan != null ? TargetOf(Plan.TargetId) : null;
            if (target == null) return null;

            var rng = new System.Random(Now.Day * 7919 + Plan.Hour * 31 + target.Id.Length);
            var outcome = Operations.Run(Plan, target, BuildOperationState(), () => rng.NextDouble());

            if (outcome.Take > 0)
            {
                Wallet.EarnDirty(outcome.Take);
                Audio.Ui("coin");
            }
            if (!outcome.Success) Audio.Ui("dread");

            var mill = _gossip != null ? _gossip.Mill : null;
            if (mill != null)
            {
                // Witnesses enter as ORDINARY sightings — same path a bare-faced
                // night drop uses, same decay, same deniability. A job is not a
                // special kind of evidence; it is a night somebody saw you out.
                var pool = mill.Agents
                    .Where(a => a.Circle != "day" || Plan.Hour >= 8 && Plan.Hour < 20)
                    .Take(outcome.Witnesses).ToList();
                foreach (var w in pool)
                    mill.Witness(w.Id,
                        new Fact("player", $"job_d{Now.Day}_{target.Id}", "seen"),
                        $"somebody was at {target.Name} in the small hours, and it was not nothing",
                        sensitive: true, now: Now,
                        confidence: WearingCoat ? 0.55 : 0.9);

                // Your own people write it in their own words. That memory is
                // what the model reads the next time you talk to them.
                foreach (var id in outcome.Talkers)
                {
                    var g = mill.Get(id);
                    if (g == null) continue;
                    g.Loyalty = Mathf.Clamp01((float)(g.Loyalty - 0.08));
                    g.Memory.Append(new MemoryEvent(Now, "observation", 0.85,
                        outcome.Success
                            ? $"We did {target.Name}. It worked, and I have not slept properly since."
                            : $"We tried {target.Name} and it went wrong. I was there. I am still thinking about it."));
                }
            }

            LastOutcome = outcome;
            Plan = null;   // a plan is spent whether or not it worked
            return outcome;
        }

        public OperationOutcome LastOutcome { get; private set; }

        // ---- persistence ----

        List<object> CaptureTargets() => Targets.Select(t => (object)new Dictionary<string, object>
        {
            { "id", t.Id }, { "done", t.Done }, { "doneDay", t.DoneDay },
            { "difficulty", t.Difficulty },
        }).ToList();

        void RestoreTargets(List<object> list)
        {
            if (list == null) return;
            foreach (var raw in list)
            {
                var o = MiniJson.AsObject(raw);
                if (o == null) continue;
                var t = TargetOf(MiniJson.GetString(o, "id"));
                if (t == null) continue;
                t.Done = o.TryGetValue("done", out var d) && d is bool b && b;
                t.DoneDay = MiniJson.GetInt(o, "doneDay");
                // A failed job left the target harder; that must survive a save,
                // or reloading becomes the cheapest way to undo a bad night.
                if (o.TryGetValue("difficulty", out var diff) && diff != null)
                    t.Difficulty = Mathf.Clamp01((float)System.Convert.ToDouble(diff));
            }
        }
    }
}
