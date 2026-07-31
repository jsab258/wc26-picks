using System.Collections.Generic;

namespace Ledger.Core
{
    /// Accumulates token usage per model and estimates spend — instrumentation is
    /// an M0 pass/fail requirement (target: <= $0.05 per ambient played hour).
    public class CostTracker
    {
        class Bucket { public long InputTokens; public long OutputTokens; public int Calls; }
        readonly Dictionary<string, Bucket> _byModel = new Dictionary<string, Bucket>();

        public void Record(string model, int inputTokens, int outputTokens)
        {
            if (!_byModel.TryGetValue(model, out var b))
                _byModel[model] = b = new Bucket();
            b.InputTokens += inputTokens;
            b.OutputTokens += outputTokens;
            b.Calls++;
        }

        public int TotalCalls
        {
            get { int n = 0; foreach (var b in _byModel.Values) n += b.Calls; return n; }
        }

        public double EstimateUsd()
        {
            double usd = 0;
            foreach (var kv in _byModel)
            {
                if (!Models.Cost.TryGetValue(kv.Key, out var rate)) continue;
                usd += kv.Value.InputTokens / 1_000_000.0 * rate.inPerM;
                usd += kv.Value.OutputTokens / 1_000_000.0 * rate.outPerM;
            }
            return usd;
        }

        public string Report()
        {
            var sb = new System.Text.StringBuilder();
            foreach (var kv in _byModel)
                sb.AppendLine($"{kv.Key}: {kv.Value.Calls} calls, {kv.Value.InputTokens} in / {kv.Value.OutputTokens} out tokens");
            sb.AppendLine($"Estimated total: £{EstimateUsd():0.0000}");
            return sb.ToString();
        }
    }
}
