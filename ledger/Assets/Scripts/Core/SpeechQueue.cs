using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// A LINE TAKES NINE SECONDS AND A FRAME TAKES SIXTEEN MILLISECONDS.
    ///
    /// That is the whole problem this file exists for. `SpeechLoop.Run` is a
    /// blocking call that occupies its thread for the length of a sentence, and
    /// calling it from `Update` would freeze the game solid while somebody
    /// thinks of what to say. So it runs on a worker, and this is the thing
    /// standing between the world and that worker.
    ///
    /// THE POLICY IS HERE AND THE THREAD IS NOT. Core owns what gets to be
    /// said, in what order, and when a line stops being worth saying; the Game
    /// layer owns the thread, because that needs the engine and cannot be
    /// tested in this container. The split is the same one `ISpeechBackend`
    /// draws, and for the same reason — a scheduling bug found here costs
    /// seconds, and the same bug found in the Game layer costs a ~28-minute
    /// build.
    ///
    /// THE RULE THAT MATTERS MOST IS THE SHELF LIFE, and it is a game-feel
    /// rule rather than an engineering one. If four people want to speak and
    /// each line costs nine seconds, the fourth arrives thirty-six seconds
    /// late — long after the player has walked away from whatever prompted it.
    /// A character answering a question nobody remembers asking is worse than
    /// a character who said nothing, so a line that has sat too long is thrown
    /// away rather than delivered late. Counted, because a feature that
    /// quietly discards most of its work must say so.
    ///
    /// ONE AT A TIME, ON PURPOSE. There is one model, one session, and one
    /// set of key/value tensors; two lines at once would need two of each and
    /// two gigabytes more memory. The queue is therefore a queue and not a
    /// pool, and the depth is small — a backlog is just a list of lines that
    /// will expire before they are reached.
    public enum SpeechDrop
    {
        /// Still waiting or in flight.
        None = 0,
        /// The queue was full when it was offered.
        Full = 1,
        /// It waited longer than its shelf life and was never worth saying.
        Stale = 2,
        /// Generated, but the moment had passed by the time it was ready.
        TooLate = 3,
        /// The backend failed, or the line came back unusable.
        Failed = 4,
    }

    /// One line somebody wants said.
    public sealed class SpeechJob
    {
        public string VoiceId;
        public string Text;
        /// When it was asked for. Everything about expiry is measured from here.
        public double Offered;
        public double Started;
        public double Finished;
        public SpeechDrop Drop = SpeechDrop.None;
        /// The audio, once the worker has produced it. Null until then.
        public float[] Samples;
        public SpeechRun Run;

        /// Whether this is worth playing. Deliberately strict — see
        /// `SpeechRun.Usable`, which this defers to.
        public bool Speakable => Drop == SpeechDrop.None
                                 && Samples != null && Samples.Length > 0
                                 && Run != null && Run.Usable;
    }

    public class SpeechQueue
    {
        /// How long a line stays worth saying, from the moment it was asked
        /// for. Not measured — a judgement about the player, like
        /// `SpeechDirector.PatienceSeconds`, and exposed rather than buried
        /// for the same reason.
        ///
        /// LONGER THAN THE DIRECTOR'S PATIENCE ON PURPOSE. Patience is how
        /// long one line may take to GENERATE; this is how long the moment
        /// lasts. A line that took three seconds is still worth hearing a
        /// beat later, so the shelf outlives the deadline.
        public double ShelfSeconds = 8.0;

        /// How many lines may be waiting. SMALL, because a backlog is a list
        /// of lines that will expire before they are reached — a deeper queue
        /// does not buy more speech, it buys more discarded speech and a
        /// longer wait for the one line that does get through.
        public int Depth = 2;

        public int Offered { get; private set; }
        public int Refused { get; private set; }
        public int Expired { get; private set; }
        public int Started { get; private set; }
        public int Spoken { get; private set; }
        public int Failed { get; private set; }

        /// EVERY ZERO'S DENOMINATOR. `Spoken == 0` cannot tell "the model is
        /// too slow" from "nobody ever asked", and those have nothing in
        /// common.
        public int Seen => Offered + Refused;

        readonly List<SpeechJob> _waiting = new List<SpeechJob>();
        readonly List<SpeechJob> _done = new List<SpeechJob>();
        SpeechJob _inFlight;

        /// True while a line is being generated. The Game layer's worker asks
        /// this rather than tracking it itself, so there is one answer.
        public bool Busy { get { lock (_waiting) { return _inFlight != null; } } }
        public int Waiting { get { lock (_waiting) { return _waiting.Count; } } }

        /// Somebody wants a line said. Returns false when it was refused, and
        /// the counter says why.
        public bool Offer(string voiceId, string text, double now)
        {
            var t = VoiceBank.Normalise(text);
            if (string.IsNullOrEmpty(voiceId) || string.IsNullOrEmpty(t)) return false;
            lock (_waiting)
            {
                Expire(now);
                // THE SAME LINE TWICE IS ONE LINE. Two walkers reacting to the
                // same event in the same frame is normal, and generating it
                // twice would spend the whole budget saying one thing.
                foreach (var w in _waiting)
                    if (w.VoiceId == voiceId && w.Text == t) return false;
                if (_waiting.Count >= Depth) { Refused++; return false; }
                _waiting.Add(new SpeechJob { VoiceId = voiceId, Text = t, Offered = now });
                Offered++;
                return true;
            }
        }

        /// The worker asks for something to do. Null when there is nothing
        /// ready, or when a line is already in flight.
        public SpeechJob TakeNext(double now)
        {
            lock (_waiting)
            {
                Expire(now);
                if (_inFlight != null || _waiting.Count == 0) return null;
                var job = _waiting[0];
                _waiting.RemoveAt(0);
                job.Started = now;
                _inFlight = job;
                Started++;
                return job;
            }
        }

        /// The worker hands back what it produced. `samples` may be null when
        /// generation failed; the run says why.
        public void Deliver(SpeechJob job, SpeechRun run, float[] samples, double now)
        {
            if (job == null) return;
            lock (_waiting)
            {
                job.Run = run;
                job.Samples = samples;
                job.Finished = now;
                if (run == null || !run.Usable || samples == null || samples.Length == 0)
                {
                    job.Drop = SpeechDrop.Failed;
                    Failed++;
                }
                else if (now - job.Offered > ShelfSeconds)
                {
                    // GENERATED AND THROWN AWAY, and this is the case worth
                    // counting most. It means the machine CAN speak and cannot
                    // speak in time, which is a completely different problem
                    // from a machine that cannot speak at all — and both would
                    // otherwise show up as silence.
                    job.Drop = SpeechDrop.TooLate;
                    Expired++;
                }
                if (ReferenceEquals(_inFlight, job)) _inFlight = null;
                _done.Add(job);
            }
        }

        /// A STREAMED line hands nothing back — its audio already played,
        /// chunk by chunk, while it was in flight. This closes the job's
        /// lifecycle without entering `_done`, so `Collect` cannot build a
        /// second clip and say the line twice; and it never marks TooLate,
        /// because a line that STARTED inside the shelf and is still
        /// playing is the feature working, not a miss.
        public void DeliverStreamed(SpeechJob job, SpeechRun run, double now)
        {
            if (job == null) return;
            lock (_waiting)
            {
                job.Run = run;
                job.Finished = now;
                Streamed++;
                if (ReferenceEquals(_inFlight, job)) _inFlight = null;
            }
        }

        /// Lines that played progressively rather than through `Collect`.
        public int Streamed { get; private set; }

        /// The main thread collects a finished line, or null. Called every
        /// frame; returns one at a time so a burst cannot stall a frame
        /// building several audio clips at once.
        public SpeechJob Collect()
        {
            lock (_waiting)
            {
                if (_done.Count == 0) return null;
                var job = _done[0];
                _done.RemoveAt(0);
                if (job.Speakable) Spoken++;
                return job;
            }
        }

        /// Anything that waited too long, dropped where it sits. Called from
        /// inside the lock by everything that touches the queue, so a line
        /// cannot go stale merely because nothing happened to ask.
        void Expire(double now)
        {
            for (int i = _waiting.Count - 1; i >= 0; i--)
            {
                if (now - _waiting[i].Offered <= ShelfSeconds) continue;
                _waiting[i].Drop = SpeechDrop.Stale;
                _waiting.RemoveAt(i);
                Expired++;
            }
        }

        /// One line for the verdict. No spaces in a value — `verdict.txt` is
        /// space-separated `key=value` and a space silently truncates every
        /// reader of it.
        public string Verdict()
        {
            lock (_waiting)
            {
                return string.Format(
                    "speechSeen={0} speechQueued={1} speechRefused={2} speechStarted={3} "
                    + "speechSpoken={4} speechExpired={5} speechFailed={6} speechWaiting={7}",
                    Seen, Offered, Refused, Started, Spoken, Expired, Failed, _waiting.Count);
            }
        }

        public void Reset()
        {
            lock (_waiting)
            {
                _waiting.Clear();
                _done.Clear();
                _inFlight = null;
                Offered = Refused = Expired = Started = Spoken = Failed = 0;
            }
        }
    }
}
