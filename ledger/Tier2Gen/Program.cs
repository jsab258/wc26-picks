using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Ledger.Core;

namespace Ledger.Tier2Gen
{
    /// The Tier-2 batch generator (game-design/tier2-pipeline-spec.md): the
    /// machine that makes density purchasable. Runs headless in CI with the
    /// ANTHROPIC_API_KEY secret (player authorization 2026-07-26), generates
    /// character cards for the Hook district against the HookMap place registry,
    /// script-validates every card (no LLM in the validator), and feeds failures
    /// back into the next request — the self-healing batch loop.
    ///
    /// Output: one markdown card per character + a JSON manifest, written to
    /// --out AND printed to stdout between TIER2-MANIFEST markers so the cards
    /// can be harvested from the CI job log (artifact hosts are not always
    /// reachable from the dev environment; logs are).
    static class Program
    {
        // Ids that already exist in the game; generated connections and knownBy
        // must resolve to these or to cards in the same run. Ossei is deliberately
        // absent — the police have no friends here.
        static readonly string[] ExistingCast = { "rocco", "ada", "sam", "lena", "noor", "mirela", "josip" };

        static readonly string[] OccupationPool =
        {
            "night cab driver", "pawnbroker", "priest's housekeeper", "ferry ticket clerk",
            "fish seller", "steam laundry worker", "baker", "boat repairer", "harbor clerk",
            "customs assistant", "boarding house keeper", "net mender", "dock crane operator",
            "market porter", "seamstress", "scrap dealer", "midwife", "letter writer",
            "tea house keeper", "ice seller", "chandler", "night watchman", "washerwoman",
            "eel fisherman", "knife grinder", "street cook", "coal carrier", "sign painter",
            "rent collector's runner", "bottle collector", "ferry deckhand", "locksmith",
        };

        static int Main(string[] args) => MainAsync(args).GetAwaiter().GetResult();

        static async Task<int> MainAsync(string[] args)
        {
            int count = ArgInt(args, "--count", 60);
            int perCall = ArgInt(args, "--batch", 5);
            string outDir = ArgStr(args, "--out", "tier2-out");
            string model = ArgStr(args, "--model", "claude-sonnet-5");

            var key = Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY");
            if (string.IsNullOrEmpty(key))
            {
                Console.WriteLine("Tier2Gen: ANTHROPIC_API_KEY is not set; nothing generated.");
                return 1;
            }

            Directory.CreateDirectory(outDir);
            var client = new AnthropicClient(key);
            var accepted = new List<Dictionary<string, object>>();
            var takenIds = new HashSet<string>(ExistingCast);
            var takenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
                { "Rocco", "Ada", "Sam", "Lena", "Noor", "Josip", "Mirela", "Marek", "Mara" };
            var usedOccupations = new HashSet<string>();
            var lastFailures = new List<string>();
            int calls = 0, maxCalls = Math.Max(6, count / perCall * 3);
            long tokensIn = 0, tokensOut = 0;

            while (accepted.Count < count && calls < maxCalls)
            {
                calls++;
                int want = Math.Min(perCall, count - accepted.Count);
                var request = new LlmRequest
                {
                    Model = model,
                    MaxTokens = 4000,
                    System = SystemPrompt(),
                    Messages = { new LlmMessage("user", UserPrompt(want, takenIds, takenNames, usedOccupations, lastFailures)) },
                };
                lastFailures.Clear();

                LlmResponse response;
                try { response = await client.CompleteAsync(request); }
                catch (Exception e)
                {
                    Console.WriteLine($"Tier2Gen: call {calls} failed: {e.Message}");
                    continue;
                }
                tokensIn += response.InputTokens;
                tokensOut += response.OutputTokens;

                var cards = ParseCards(response.Text);
                if (cards == null)
                {
                    Console.WriteLine($"Tier2Gen: call {calls} returned unparseable output; retrying.");
                    lastFailures.Add("your previous output was not a parseable bare JSON array — output ONLY the JSON array");
                    continue;
                }
                var batchIds = new HashSet<string>(cards.Select(c => MiniJson.GetString(c, "id") ?? ""));
                foreach (var card in cards)
                {
                    var problem = Validate(card, takenIds, takenNames, batchIds);
                    var id = MiniJson.GetString(card, "id") ?? "(no id)";
                    if (problem == null)
                    {
                        accepted.Add(card);
                        takenIds.Add(id);
                        takenNames.Add(MiniJson.GetString(card, "name") ?? id);
                        usedOccupations.Add((MiniJson.GetString(card, "occupation") ?? "").ToLowerInvariant());
                        Console.WriteLine($"  ok   {accepted.Count,3}/{count}  {id}");
                    }
                    else
                    {
                        lastFailures.Add($"{id}: {problem}");
                        Console.WriteLine($"  FAIL {id}: {problem}");
                    }
                }
            }

            foreach (var card in accepted)
            {
                var id = MiniJson.GetString(card, "id");
                File.WriteAllText(Path.Combine(outDir, $"{id}.md"), RenderMarkdown(card));
            }
            var manifest = MiniJson.Serialize(accepted.Cast<object>().ToList());
            File.WriteAllText(Path.Combine(outDir, "manifest.json"), manifest);

            Console.WriteLine($"Tier2Gen: {accepted.Count}/{count} cards in {calls} calls; " +
                              $"tokens {tokensIn} in / {tokensOut} out.");
            Console.WriteLine("===TIER2-MANIFEST-BEGIN===");
            Console.WriteLine(manifest);
            Console.WriteLine("===TIER2-MANIFEST-END===");
            return accepted.Count >= count ? 0 : 1;
        }

        static string SystemPrompt()
        {
            var sb = new StringBuilder();
            sb.AppendLine("You generate Tier-2 character cards for LEDGER, a crime/social sim set in the Hook district — the old-port quarter of Meridian Bay. Working-class, cash economy, everyone knows everyone's business.");
            sb.AppendLine();
            sb.AppendLine("HARD CANON (never contradict): Marek, who owned the Hook Street bar, died three weeks ago; his nephew just inherited the bar. The old warehouse on warehouse row burned about a year ago and the case is still open. Existing people: Lena (the bar's bookkeeper, 31 years), Rocco (the doorman), Ada (retired schoolteacher on the apartment steps), Sam (street go-between), Noor (Meridian Courier reporter, rooms above Ada's), Mirela (vegetable stall), Josip (dock hand).");
            sb.AppendLine();
            sb.AppendLine("Every card must be a small, grounded life with MECHANICAL INDIVIDUALITY: one concrete skill, access, or connection that could matter to a player building either an honest life or a quiet criminal outfit. No colorful lunatics, no assassins, no masterminds. Secrets are ordinary-sized and shameful or quietly criminal.");
            sb.AppendLine();
            sb.AppendLine("Valid place ids for schedules (use ONLY these): " +
                string.Join(", ", HookMap.Places.Select(p => p.Id)) + ".");
            sb.AppendLine();
            sb.AppendLine("Output ONLY a bare JSON array of card objects — no prose, no code fences. Each card object has exactly these fields:");
            sb.AppendLine("id (lowercase single word, unique), name (first name, may repeat no existing name), age (int 18-75), occupation (string), circle (\"day\"|\"night\"|\"both\"), " +
                          "traits {greed, nerve, loyalty: each 0.05-0.9, at least one outside 0.4-0.6}, " +
                          "summary (2 sentences), personality (2 sentences), speech (1-2 sentences on how they talk), " +
                          "hardFacts (array of 3-5 first-person checkable facts), " +
                          "secret {kind: \"shameful\"|\"criminal\", line (one sentence), knownBy (array of 0-2 ids)}, " +
                          "need (one thing they want that the player could supply), " +
                          "connections (array of 2-4 {to: existing-or-batch id, weight: 0.3-0.8}), " +
                          "schedule (array of 2-5 {place: place-id, hour: int 0-23}, hours strictly ascending).");
            return sb.ToString();
        }

        static string UserPrompt(int want, HashSet<string> takenIds, HashSet<string> takenNames,
            HashSet<string> usedOccupations, List<string> failures)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"Generate {want} cards.");
            sb.AppendLine("Ids already taken (do not reuse): " + string.Join(", ", takenIds) + ".");
            sb.AppendLine("Names already taken (do not reuse): " + string.Join(", ", takenNames) + ".");
            var fresh = OccupationPool.Where(o => !usedOccupations.Contains(o)).Take(want * 2).ToList();
            if (fresh.Count > 0)
                sb.AppendLine("Prefer occupations not yet covered, e.g.: " + string.Join(", ", fresh) + ".");
            if (failures.Count > 0)
            {
                sb.AppendLine("Your previous batch had rejected cards — fix these mistakes this time:");
                foreach (var f in failures.Take(10)) sb.AppendLine("- " + f);
            }
            return sb.ToString();
        }

        /// The script validator (spec rules, no LLM). Returns null when valid,
        /// otherwise the reason — which goes back into the next prompt.
        static string Validate(Dictionary<string, object> card, HashSet<string> takenIds,
            HashSet<string> takenNames, HashSet<string> batchIds)
        {
            if (card == null) return "not an object";
            var id = MiniJson.GetString(card, "id");
            if (string.IsNullOrEmpty(id) || id.Any(ch => !char.IsLetter(ch)) || id != id.ToLowerInvariant())
                return "id must be one lowercase word";
            if (takenIds.Contains(id)) return "id already taken";
            var name = MiniJson.GetString(card, "name");
            if (string.IsNullOrEmpty(name)) return "missing name";
            if (takenNames.Contains(name)) return "name already taken";
            int age = MiniJson.GetInt(card, "age");
            if (age < 18 || age > 75) return "age out of range";
            var circle = MiniJson.GetString(card, "circle");
            if (circle != "day" && circle != "night" && circle != "both") return "circle must be day|night|both";
            foreach (var field in new[] { "summary", "personality", "speech", "occupation", "need" })
                if (string.IsNullOrEmpty(MiniJson.GetString(card, field))) return $"missing {field}";

            var traits = MiniJson.GetObject(card, "traits");
            if (traits == null) return "missing traits";
            bool nonBeige = false;
            foreach (var t in new[] { "greed", "nerve", "loyalty" })
            {
                if (!traits.ContainsKey(t)) return $"missing trait {t}";
                double v = Convert.ToDouble(traits[t]);
                if (v < 0.05 || v > 0.9) return $"trait {t} out of 0.05-0.9";
                if (v < 0.4 || v > 0.6) nonBeige = true;
            }
            if (!nonBeige) return "all traits beige (0.4-0.6); at least one must sit outside";

            var facts = MiniJson.GetList(card, "hardFacts");
            if (facts == null || facts.Count < 3 || facts.Count > 5) return "hardFacts must have 3-5 entries";

            var secret = MiniJson.GetObject(card, "secret");
            if (secret == null) return "missing secret";
            var kind = MiniJson.GetString(secret, "kind");
            if (kind != "shameful" && kind != "criminal") return "secret.kind must be shameful|criminal";
            if (string.IsNullOrEmpty(MiniJson.GetString(secret, "line"))) return "missing secret.line";
            var knownBy = MiniJson.GetList(secret, "knownBy") ?? new List<object>();
            if (knownBy.Count > 2) return "secret.knownBy max 2";
            foreach (var k in knownBy.OfType<string>())
                if (!takenIds.Contains(k) && !batchIds.Contains(k)) return $"secret.knownBy '{k}' does not exist";

            var conns = MiniJson.GetList(card, "connections");
            if (conns == null || conns.Count < 2 || conns.Count > 4) return "connections must have 2-4 entries";
            foreach (var c in conns)
            {
                var co = MiniJson.AsObject(c);
                var to = co != null ? MiniJson.GetString(co, "to") : null;
                if (string.IsNullOrEmpty(to)) return "connection missing 'to'";
                if (to == id) return "connection to self";
                if (!takenIds.Contains(to) && !batchIds.Contains(to)) return $"connection to unknown id '{to}'";
                double w = co.ContainsKey("weight") ? Convert.ToDouble(co["weight"]) : -1;
                if (w < 0.3 || w > 0.8) return "connection weight out of 0.3-0.8";
            }

            var sched = MiniJson.GetList(card, "schedule");
            if (sched == null || sched.Count < 2 || sched.Count > 5) return "schedule must have 2-5 stops";
            int lastHour = -1;
            HookPlace prev = null;
            foreach (var s in sched)
            {
                var so = MiniJson.AsObject(s);
                var placeId = so != null ? MiniJson.GetString(so, "place") : null;
                var place = placeId != null ? HookMap.Get(placeId) : null;
                if (place == null) return $"schedule stop at unknown place '{placeId}'";
                int hour = so.ContainsKey("hour") ? Convert.ToInt32(so["hour"]) : -1;
                if (hour < 0 || hour > 23) return "schedule hour out of 0-23";
                if (hour <= lastHour) return "schedule hours must be strictly ascending";
                if (prev != null)
                {
                    double dx = place.X - prev.X, dz = place.Z - prev.Z;
                    if (Math.Sqrt(dx * dx + dz * dz) > HookMap.MaxLegDistance)
                        return $"schedule leg {prev.Id} -> {place.Id} too far to walk";
                }
                lastHour = hour;
                prev = place;
            }
            return null;
        }

        static List<Dictionary<string, object>> ParseCards(string text)
        {
            // Tolerate stray prose/fences around the array: parse from first '[' to last ']'.
            int a = text.IndexOf('['), b = text.LastIndexOf(']');
            if (a < 0 || b <= a) return null;
            var parsed = MiniJson.Deserialize(text.Substring(a, b - a + 1));
            var list = MiniJson.AsList(parsed);
            if (list == null) return null;
            var cards = list.Select(MiniJson.AsObject).ToList();
            return cards.Any(c => c == null) ? null : cards;
        }

        /// Same markdown shape the engine already parses (CharacterCard.Parse).
        static string RenderMarkdown(Dictionary<string, object> card)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"# {MiniJson.GetString(card, "name")}");
            sb.AppendLine($"id: {MiniJson.GetString(card, "id")}");
            sb.AppendLine("tier: ambient");
            sb.AppendLine();
            sb.AppendLine("## Summary");
            sb.AppendLine(MiniJson.GetString(card, "summary"));
            sb.AppendLine();
            sb.AppendLine("## Personality");
            sb.AppendLine(MiniJson.GetString(card, "personality"));
            sb.AppendLine();
            sb.AppendLine("## Speech Style");
            sb.AppendLine(MiniJson.GetString(card, "speech"));
            sb.AppendLine();
            sb.AppendLine("## Hard Facts");
            foreach (var f in MiniJson.GetList(card, "hardFacts") ?? new List<object>())
                sb.AppendLine($"- {f}");
            return sb.ToString();
        }

        static int ArgInt(string[] args, string name, int fallback)
        {
            for (int i = 0; i < args.Length - 1; i++)
                if (args[i] == name && int.TryParse(args[i + 1], out var v)) return v;
            return fallback;
        }

        static string ArgStr(string[] args, string name, string fallback)
        {
            for (int i = 0; i < args.Length - 1; i++)
                if (args[i] == name) return args[i + 1];
            return fallback;
        }
    }
}
