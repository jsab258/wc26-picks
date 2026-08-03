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
        // must resolve to these or to cards in the same run. Ellis is deliberately
        // absent — the police have no friends here.
        static readonly string[] ExistingCast =
        {
            "rocco", "ada", "sam", "lena", "noor", "mirela", "josip",
            // Batch promotions and the hand-authored ring:
            "viktor", "ferko", "ruta", "vesna", "tibor",
            // Reserved for the doc's Tier-1 cast (§8):
            "emil", "june", "aldous", "sera", "danny", "mara", "marek", "ossei",
        };

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
            // RUN THE CHECKER WITHOUT SPENDING ANYTHING, because a validator
            // that has never executed is exactly how a generation run comes back
            // with sixty rejections and an empty directory after burning the
            // API budget — which is Jafar's, not mine. `--selftest` exercises
            // every writing rule against cards built to pass and cards built to
            // fail, in about a second, with no key.
            if (args.Contains("--selftest")) return SelfTest();

            // WHAT THE CARDS WE ALREADY HAVE WOULD SCORE, which turns "the old
            // sixty need regenerating" from an assumption into a count. Costs
            // nothing and needs no key: the validator is a script, and the
            // cards are already in the repository.
            if (args.Contains("--audit")) return Audit(ArgStr(args, "--audit", ""));

            // ENRICH, NOT REGENERATE, and the distinction is the whole task.
            //
            // The sixty existing cards fail exactly ONE rule — no example lines
            // — and nothing else. Regenerating them fresh would fix that and
            // mint sixty NEW ids, while the current ones are wired into
            // secrets, connections, schedules and promotions, five of them
            // already pulled up into the hand-written ring. That is spending
            // money to break references.
            //
            // So this reads the manifest, asks only for what is missing, and
            // writes the same people back with their ids, names, traits,
            // secrets, schedules and connections untouched.
            if (args.Contains("--enrich"))
                return await EnrichAsync(ArgStr(args, "--enrich", ""),
                                         ArgStr(args, "--out", "tier2-out"),
                                         ArgStr(args, "--model", "claude-sonnet-5"));

            int count = ArgInt(args, "--count", 60);
            int perCall = ArgInt(args, "--batch", 4);
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
                { "Rocco", "Ada", "Sam", "Lena", "Noor", "Joey", "Marla", "Mickey", "Mara" };
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
                    MaxTokens = 8000,
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

        /// Give existing cards the voice they were written without.
        static async Task<int> EnrichAsync(string path, string outDir, string model)
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
            {
                Console.WriteLine($"Tier2Gen --enrich: no such file '{path}'");
                return 1;
            }
            var cards = ParseCards(File.ReadAllText(path));
            if (cards == null || cards.Count == 0)
            {
                Console.WriteLine("Tier2Gen --enrich: no cards parsed");
                return 1;
            }

            var key = Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY");
            if (string.IsNullOrEmpty(key))
            {
                Console.WriteLine("Tier2Gen --enrich: ANTHROPIC_API_KEY is not set; nothing changed.");
                return 1;
            }

            var client = new AnthropicClient(key);
            long tin = 0, tout = 0;
            int done = 0, failed = 0;

            // ONE CARD PER CALL. A batch would be cheaper and would let one
            // malformed reply take twenty characters down with it — and the
            // cards being repaired are already in the game, so a partial
            // failure has to leave the survivors intact rather than roll back
            // sixty people.
            foreach (var card in cards)
            {
                var id = MiniJson.GetString(card, "id");
                if (MiniJson.GetList(card, "lines") != null) { done++; continue; }

                var ask = new StringBuilder();
                ask.AppendLine("Here is an existing character from the game. Do not change them.");
                ask.AppendLine();
                ask.AppendLine($"name: {MiniJson.GetString(card, "name")}");
                ask.AppendLine($"age: {MiniJson.GetInt(card, "age")}");
                ask.AppendLine($"occupation: {MiniJson.GetString(card, "occupation")}");
                ask.AppendLine($"summary: {MiniJson.GetString(card, "summary")}");
                ask.AppendLine($"personality: {MiniJson.GetString(card, "personality")}");
                ask.AppendLine($"speech: {MiniJson.GetString(card, "speech")}");
                ask.AppendLine($"need: {MiniJson.GetString(card, "need")}");
                ask.AppendLine();
                ask.AppendLine("Return ONLY a JSON object with two fields and nothing else:");
                ask.AppendLine("  lines: 2-3 short quotes this person would actually say, no");
                ask.AppendLine("         attribution and no quotation marks inside them. They must");
                ask.AppendLine("         DEMONSTRATE the speech behaviour above rather than restate");
                ask.AppendLine("         it, and they must sound like different people from card to");
                ask.AppendLine("         card.");
                ask.AppendLine("  fact:  one further first-person hard fact that places them in the");
                ask.AppendLine("         PERIOD through something they use or notice — a phone box, a");
                ask.AppendLine("         tab at the corner shop, wages in an envelope, who has a");
                ask.AppendLine("         telephone and who knocks to borrow one. Never a costume note.");

                LlmResponse res;
                try
                {
                    res = await client.CompleteAsync(new LlmRequest
                    {
                        Model = model,
                        MaxTokens = 700,
                        System = SystemPrompt(),
                        Messages = { new LlmMessage("user", ask.ToString()) },
                    });
                }
                catch (Exception e)
                {
                    Console.WriteLine($"  FAIL {id}: {e.Message}");
                    failed++;
                    continue;
                }
                tin += res.InputTokens;
                tout += res.OutputTokens;

                var obj = MiniJson.AsObject(MiniJson.Deserialize(Between(res.Text, '{', '}')));
                var lines = obj != null ? MiniJson.GetList(obj, "lines") : null;
                if (lines == null || lines.Count < 2 || lines.Count > 3)
                {
                    Console.WriteLine($"  FAIL {id}: no usable lines returned");
                    failed++;
                    continue;
                }
                card["lines"] = lines;
                var fact = obj != null ? MiniJson.GetString(obj, "fact") : null;
                if (!string.IsNullOrEmpty(fact))
                {
                    var facts = MiniJson.GetList(card, "hardFacts") ?? new List<object>();
                    // FIVE IS THE VALIDATOR'S CEILING, so a card already at it
                    // keeps what it has rather than being pushed out of spec by
                    // the thing meant to improve it.
                    if (facts.Count < 5) { facts.Add(fact); card["hardFacts"] = facts; }
                }

                // VALIDATED WITH THE SAME RULES AS A FRESH CARD, and rolled back
                // per card if it fails. An enrichment that quietly writes an
                // out-of-period line is worse than one that refuses: the card
                // was already shipping and would now be shipping wrong.
                // THE REAL CAST, NOT AN EMPTY SET — and getting this wrong cost
                // sixty calls for zero cards.
                //
                // I copied the empty `takenIds` from `Audit`, where it IS
                // correct: that mode asks only "would this PROSE pass", and
                // these cards collide with their own ids because they are
                // already in the game. Enrichment is the opposite case. A card
                // whose connections name `lena` or whose secret is known by
                // `sam` is CORRECT — those people exist — and validating
                // against an empty roster rejected all sixty for referencing
                // the cast they were written to reference.
                //
                // Every failure line read "connection to unknown id 'lena'" or
                // "secret.knownBy 'sam' does not exist", which is the validator
                // faithfully reporting the roster it was handed. The instrument
                // was fine; the arguments were wrong.
                //
                // Ids are also passed as TAKEN=false for the card's own id,
                // because a card being enriched is allowed to already exist —
                // that is the entire premise.
                var roster = new HashSet<string>(ExistingCast);
                foreach (var c in cards) roster.Add(MiniJson.GetString(c, "id"));
                var why = Validate(card, new HashSet<string>(),
                                   new HashSet<string>(StringComparer.OrdinalIgnoreCase),
                                   roster);
                if (why != null)
                {
                    Console.WriteLine($"  FAIL {id}: {why}");
                    card.Remove("lines");
                    failed++;
                    continue;
                }
                Console.WriteLine($"  ok   {id}");
                done++;
            }

            Directory.CreateDirectory(outDir);
            var outPath = Path.Combine(outDir, "tier2-batch-1.json");
            File.WriteAllText(outPath, MiniJson.Serialize(cards.Cast<object>().ToList()));
            foreach (var card in cards)
                File.WriteAllText(Path.Combine(outDir, MiniJson.GetString(card, "id") + ".md"),
                                  RenderMarkdown(card));
            Console.WriteLine($"Tier2Gen --enrich: {done} enriched, {failed} left as they were; "
                              + $"tokens {tin} in / {tout} out.");
            return failed > cards.Count / 2 ? 1 : 0;
        }

        /// The first balanced {...} in a reply, so a model that adds a sentence
        /// of preamble does not cost a card.
        static string Between(string text, char open, char close)
        {
            if (string.IsNullOrEmpty(text)) return "";
            int a = text.IndexOf(open), depth = 0;
            if (a < 0) return "";
            for (int i = a; i < text.Length; i++)
            {
                if (text[i] == open) depth++;
                else if (text[i] == close && --depth == 0) return text.Substring(a, i - a + 1);
            }
            return "";
        }

        static string SystemPrompt()
        {
            var sb = new StringBuilder();
            sb.AppendLine("You generate Tier-2 character cards for LEDGER, a crime/social sim set in the Hook district — the old-port quarter of Meridian Bay. Working-class, cash economy, everyone knows everyone's business.");
            sb.AppendLine();
            sb.AppendLine("HARD CANON (never contradict): Mickey, who owned the Hook Street bar, died three weeks ago; his nephew just inherited the bar. The old warehouse on warehouse row burned about a year ago and the case is still open. Existing people: Lena (the bar's bookkeeper, 31 years), Rocco (the doorman), Ada (retired schoolteacher on the apartment steps), Sam (street go-between), Noor (Meridian Courier reporter, rooms above Ada's), Marla (vegetable stall), Joey (dock hand).");
            sb.AppendLine();
            sb.AppendLine("Every card must be a small, grounded life with MECHANICAL INDIVIDUALITY: one concrete skill, access, or connection that could matter to a player building either an honest life or a quiet criminal outfit. No colorful lunatics, no assassins, no masterminds. Secrets are ordinary-sized and shameful or quietly criminal.");
            sb.AppendLine();
            // THE DECADE, WHICH THIS PROMPT DID NOT HAVE.
            //
            // `agency-model` records the era as decided — late-analog — and ends
            // that entry with "Cards and generation prompts inherit this." This
            // prompt did not. Every card it has ever written would read
            // identically in 1935, which is the same fault the writing pass found
            // in the hand-authored cards and plausibly why I twice described this
            // game in writing as 1930s.
            //
            // Stated as what a person NOTICES rather than as set dressing,
            // because that is what actually carries a decade in dialogue. A
            // character who mentions borrowing next door's phone is in the
            // period; a character wearing a described jacket is in a costume.
            sb.AppendLine("PERIOD — late analog, the eighties into the nineties. No internet, no mobile phones, no email, no texting. People reach each other through landlines, phone boxes, answering machines, and messages left with whoever is behind a bar. Being unreachable is normal and is part of how this world works. Money is cash, wages are in an envelope, and credit is somebody's word. Write what a character NOTICES and USES from that world rather than describing their clothes: the pools coupon, the meter, the tick at the corner shop, whose phone they borrow, what is on in the corner of the pub.");
            sb.AppendLine();
            // AND LINES, BECAUSE DESCRIBING A VOICE IS NOT HAVING ONE.
            //
            // `speech` alone produces adjectives — "gruff", "world-weary" — and
            // an adjective gets you the model's AVERAGE of that adjective, so
            // every card converges on the same person. The cards that work
            // already do the opposite: "rarely finishes a sentence without
            // naming a price", "laughs like a winch". Those are behaviours a
            // model can act on. Two or three lines of the character actually
            // TALKING anchors a register harder than any description, and it
            // costs a field.
            sb.AppendLine("VOICE — `speech` must name a BEHAVIOUR, not a mood. \"Rarely finishes a sentence without naming a price\" is usable; \"gruff and world-weary\" gets you the average of those words and every card sounds the same. Then `lines`: two or three things this person would actually say, in their own words, showing the behaviour you just named. Plain speech, contractions, sentences allowed to trail off. Never 'serves as' or 'boasts'; no delve, tapestry, testament, vibrant, crucial, pivotal, showcase.");
            sb.AppendLine();
            sb.AppendLine("Valid place ids for schedules (use ONLY these): " +
                string.Join(", ", HookMap.Places.Select(p => p.Id)) + ".");
            sb.AppendLine();
            sb.AppendLine("Output ONLY a bare JSON array of card objects — no prose, no code fences. Each card object has exactly these fields:");
            sb.AppendLine("id (lowercase single word, unique), name (first name, may repeat no existing name), age (int 18-75), occupation (string), circle (\"day\"|\"night\"|\"both\"), " +
                          "traits {greed, nerve, loyalty: each 0.05-0.9, at least one outside 0.4-0.6}, " +
                          "summary (2 sentences), personality (2 sentences), speech (1-2 sentences naming a speech BEHAVIOUR), " +
                          "lines (array of 2-3 short quotes this character would say, no attribution, no quotation marks), " +
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

        /// Score cards we already have against the rules we have now.
        ///
        /// "The sixty generated cards predate the writing rules, so they need
        /// regenerating" is an assumption, and regenerating them costs Jafar
        /// money. This turns it into a count, and into a REASON per card — so
        /// the decision he is being asked for comes with the actual damage
        /// rather than with my summary of it.
        ///
        /// Runs the real `Validate`, not a second copy of its rules. A separate
        /// audit checker would be free to disagree with the thing it audits,
        /// which is the fault this repo keeps finding in its own instruments.
        static int Audit(string path)
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
            {
                Console.WriteLine($"Tier2Gen --audit: no such file '{path}'");
                return 1;
            }
            var cards = ParseCards(File.ReadAllText(path));
            if (cards == null || cards.Count == 0)
            {
                Console.WriteLine("Tier2Gen --audit: no cards parsed");
                return 1;
            }

            // EVERY CARD JUDGED AS IF IT WERE NEW, so ids and names already in
            // the file do not count against themselves. The question is whether
            // the WRITING would pass, not whether the roster has duplicates.
            var reasons = new Dictionary<string, int>();
            var batchIds = new HashSet<string>(cards.Select(c => MiniJson.GetString(c, "id")));
            int ok = 0;
            foreach (var c in cards)
            {
                // NO TAKEN IDS. Four of these cards were later promoted into
                // the hand-written ring, so they now collide with themselves and
                // the audit reported four "id already taken" — a fact about the
                // roster masquerading as a fact about the writing. The question
                // here is only whether the PROSE would pass.
                var why = Validate(c, new HashSet<string>(),
                                   new HashSet<string>(StringComparer.OrdinalIgnoreCase), batchIds);
                if (why == null) { ok++; continue; }
                // Bucketed by the rule rather than by the card — thirty cards
                // failing one rule is a batch to rerun; thirty cards failing
                // thirty different rules is a prompt that does not work.
                var key = why.Split(new[] { " — ", ": ", " '" }, StringSplitOptions.None)[0];
                reasons[key] = reasons.TryGetValue(key, out var n) ? n + 1 : 1;
            }

            Console.WriteLine($"Tier2Gen --audit {Path.GetFileName(path)}");
            Console.WriteLine($"  {cards.Count} card(s), {ok} pass the current rules, {cards.Count - ok} do not");
            foreach (var kv in reasons.OrderByDescending(k => k.Value))
                Console.WriteLine($"  {kv.Value,4}  {kv.Key}");
            Console.WriteLine();
            Console.WriteLine("A count, not a verdict on the prose. These rules catch a MISSING voice");
            Console.WriteLine("and a wrong decade; they cannot tell good writing from adequate writing.");
            return 0;
        }

        /// Every writing rule, against cards built to pass and to fail.
        ///
        /// A GOOD CARD FIRST, and that ordering is the point. The failure this
        /// guards against is not "a bad card slips through" — it is a validator
        /// so strict that nothing survives it, and the run reports sixty
        /// rejections with the money already gone. So the first assertion is
        /// that a card written the way the prompt asks for is ACCEPTED.
        static int SelfTest()
        {
            int fails = 0;
            void Expect(string label, Dictionary<string, object> card, string wantSubstring)
            {
                var got = Validate(card, new HashSet<string>(ExistingCast),
                                   new HashSet<string>(StringComparer.OrdinalIgnoreCase),
                                   new HashSet<string> { "rocco" });
                bool ok = wantSubstring == null
                    ? got == null
                    : got != null && got.Contains(wantSubstring);
                Console.WriteLine((ok ? "  ok   " : "  FAIL ") + label
                                  + (ok ? "" : $" — got: {got ?? "accepted"}"));
                if (!ok) fails++;
            }

            // PARSED, NOT HAND-BUILT, AND THE FIRST RUN OF THIS TEST IS WHY.
            //
            // The first version assembled these dictionaries in C# and every
            // single case came back "age out of range" — including the one that
            // was supposed to pass. Suspect the instrument: `MiniJson.GetInt`
            // reads `v is double`, because a JSON number always arrives as a
            // double, and my literal `54` was a boxed int. The test was wrong
            // and the code was right, so nothing in `GetInt` was touched.
            //
            // Hand-building the input made the test a SECOND MODEL of what the
            // model returns, free to disagree with the first — the fault this
            // repo keeps finding in its own instruments. Going through the real
            // parser means the test can only ever be fed what production is fed.
            string place = HookMap.Places[0].Id;
            string baseJson = @"{
              ""id"": ""wilf"", ""name"": ""Wilf"", ""age"": 54,
              ""occupation"": ""knife grinder"", ""circle"": ""day"",
              ""traits"": { ""greed"": 0.3, ""nerve"": 0.5, ""loyalty"": 0.5 },
              ""summary"": ""Grinds knives off a barrow on the corner. Has done since the yard shut."",
              ""personality"": ""Patient with the work and impatient with everything else. Keeps a tally of who has not paid."",
              ""speech"": ""Names the price before he has looked at the blade, then argues himself down."",
              ""lines"": [
                ""Two quid. All right, one fifty, but you're robbing me."",
                ""Leave it with us, I'll be here Thursday.""
              ],
              ""hardFacts"": [ ""He has ground blades on this corner for nine years."",
                               ""The yard shut in the spring and never paid its last week."",
                               ""He drinks in the Hook Street bar on a Friday and nowhere else."" ],
              ""secret"": { ""kind"": ""shameful"",
                            ""line"": ""He sharpens for the yard that sacked him and takes the cash."",
                            ""knownBy"": [] },
              ""need"": ""a new stone for the wheel"",
              ""connections"": [ { ""to"": ""rocco"", ""weight"": 0.4 },
                                 { ""to"": ""ada"", ""weight"": 0.5 } ],
              ""schedule"": [ { ""place"": ""PLACE"", ""hour"": 8 },
                              { ""place"": ""PLACE"", ""hour"": 17 } ]
            }".Replace("PLACE", place);

            Dictionary<string, object> Card(Action<Dictionary<string, object>> tweak = null)
            {
                var c = MiniJson.AsObject(MiniJson.Deserialize(baseJson));
                tweak?.Invoke(c);
                return c;
            }

            Console.WriteLine("Tier2Gen --selftest — the writing rules, without spending anything");
            Expect("a card written as the prompt asks is ACCEPTED", Card(), null);
            Expect("no lines at all is rejected", Card(c => c.Remove("lines")), "lines must have");
            Expect("one line is rejected", Card(c => c["lines"] = new List<object> { "Two quid, mate." }),
                   "lines must have");
            Expect("a fragment is not a line",
                   Card(c => c["lines"] = new List<object> { "Aye.", "Two quid, take it or leave it." }),
                   "not a fragment");
            Expect("an out-of-period line is rejected",
                   Card(c => c["lines"] = new List<object>
                       { "Send us an email about it.", "Leave it with us till Thursday." }),
                   "does not exist in this period");
            Expect("an out-of-period secret is rejected",
                   Card(c => MiniJson.AsObject(c["secret"])["line"] =
                       "He has been selling the yard's stock list over email."),
                   "secret mentions");
            Expect("an out-of-period hard fact is rejected",
                   Card(c => c["hardFacts"] = new List<object>
                       { "He found the address on a website.", "b sentence here", "c sentence here" }),
                   "hard fact mentions");
            Expect("an out-of-period need is rejected",
                   Card(c => c["need"] = "a mobile phone so the yard can reach him"),
                   "does not exist in this period");
            Expect("adjective-only speech is rejected",
                   Card(c => c["speech"] = "Gruff and world-weary."), "must name a behaviour");
            // AND THE THINGS THAT ARE IN THE PERIOD AND MUST NOT TRIP IT. A
            // checker that rejected these would be quietly deleting the decade
            // it exists to protect.
            Expect("a payphone is in the world",
                   Card(c => c["lines"] = new List<object>
                       { "Ring us from the box on the corner.", "I'll leave word with the barman." }),
                   null);
            Expect("an answering machine is in the world",
                   Card(c => c["need"] = "somebody to answer the machine while he is out"), null);

            Console.WriteLine(fails == 0
                ? $"\n  all writing rules behave — {fails} failure(s)"
                : $"\n  {fails} FAILURE(S) — do not dispatch a generation run");
            return fails == 0 ? 0 : 1;
        }

        /// Things that cannot exist in a late-analog city, and the whole reason
        /// the era is a DESIGN decision rather than a flavour: information here
        /// gains a second channel without travelling at internet speed, which is
        /// what makes missed calls, wiretaps and being unreachable into play.
        /// A card that hands somebody an email has quietly deleted a mechanic.
        ///
        /// DELIBERATELY SHORT. Everything on this list is unambiguous for the
        /// eighties and nineties. Borderline period items are NOT here — CDs
        /// (1982), answering machines, pagers, car phones and DNA evidence
        /// (Pitchfork, 1987) are all in the world and a checker that guessed at
        /// them would reject correct cards. Rule 2: assert what can be asserted.
        static readonly string[] OutOfPeriod =
        {
            "internet", "email", "e-mail", "website", "web site", "online",
            "mobile phone", "smartphone", "smart phone", "text message",
            "texted her", "texted him", "texted me", "social media", "wifi",
            "wi-fi", "google", "facebook", "dvd", "usb", "download",
        };

        /// The offending word, or null. Substring rather than token match: the
        /// list carries multi-word phrases on purpose, so "mobile phone" is
        /// caught while an ordinary "mobile" — which meant something else and
        /// was in use — is not.
        static string Anachronism(string text)
        {
            if (string.IsNullOrEmpty(text)) return null;
            var lower = text.ToLowerInvariant();
            foreach (var w in OutOfPeriod)
                if (lower.Contains(w)) return w;
            return null;
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

            // THE WRITING, CHECKED. Everything above this asserts SHAPE — an id
            // is a word, an hour is an hour, a leg is walkable — and not one
            // line of it could tell a good card from a card that says the
            // character is "gruff" and could be any century. A prompt
            // instruction with no validator behind it is a suggestion, and this
            // generator's whole design is that the script rejects and the reason
            // goes back into the next prompt.
            var lines = MiniJson.GetList(card, "lines");
            if (lines == null || lines.Count < 2 || lines.Count > 3)
                return "lines must have 2-3 short quotes the character would actually say";
            foreach (var l in lines)
            {
                var text = (l as string ?? "").Trim();
                // Structural, not a tuned threshold: three words is the shortest
                // thing that can demonstrate a register rather than assert one.
                if (text.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length < 3)
                    return "each line must be something a person would actually say, not a fragment";
                var bad = Anachronism(text);
                if (bad != null) return $"line mentions '{bad}', which does not exist in this period";
            }

            // AND THE REST OF THE CARD IN THE SAME PERIOD, because the era only
            // holds if it holds everywhere: a card whose lines are impeccable
            // and whose secret is about an email is still out of the world.
            foreach (var field in new[] { "summary", "personality", "speech", "occupation", "need" })
            {
                var bad = Anachronism(MiniJson.GetString(card, field));
                if (bad != null) return $"{field} mentions '{bad}', which does not exist in this period";
            }
            // Including the two places a card carries its most load-bearing
            // sentences. A secret is what the whole social layer trades in and a
            // hard fact is what the character cannot be argued out of; either one
            // built on something that does not exist has broken the world in the
            // spot where it matters most.
            {
                var sec = MiniJson.GetObject(card, "secret");
                var bad = Anachronism(sec != null ? MiniJson.GetString(sec, "line") : null);
                if (bad != null) return $"secret mentions '{bad}', which does not exist in this period";
                foreach (var f in MiniJson.GetList(card, "hardFacts") ?? new List<object>())
                {
                    bad = Anachronism(f as string);
                    if (bad != null) return $"a hard fact mentions '{bad}', which does not exist in this period";
                }
            }

            // ADJECTIVES DESCRIBE A VOICE; BEHAVIOUR IS ONE. "Gruff and
            // world-weary" returns the model's average of two words and every
            // card converges on the same man. Caught by asking whether the field
            // is ONLY mood words, which is cheap and catches the actual failure
            // rather than trying to score prose.
            var speech = MiniJson.GetString(card, "speech");
            if (speech.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length < 6)
                return "speech must name a behaviour, not a mood — one or two sentences, not adjectives";

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

        /// Salvage parser: a hard max_tokens cut mid-card must not cost the whole
        /// batch (run 30199532311 died exactly that way). Walk the array tracking
        /// string/escape state, carve out each balanced top-level object, and
        /// parse them individually — complete cards survive a truncated tail.
        static List<Dictionary<string, object>> ParseCards(string text)
        {
            int start = text.IndexOf('[');
            if (start < 0) return null;
            var cards = new List<Dictionary<string, object>>();
            bool inStr = false, esc = false;
            int depth = 0, objStart = -1;
            for (int i = start; i < text.Length; i++)
            {
                char ch = text[i];
                if (inStr)
                {
                    if (esc) esc = false;
                    else if (ch == '\\') esc = true;
                    else if (ch == '"') inStr = false;
                    continue;
                }
                if (ch == '"') { inStr = true; continue; }
                if (ch == '{' || ch == '[')
                {
                    if (depth == 1 && ch == '{' && objStart < 0) objStart = i;
                    depth++;
                }
                else if (ch == '}' || ch == ']')
                {
                    depth--;
                    if (depth == 1 && ch == '}' && objStart >= 0)
                    {
                        try
                        {
                            var o = MiniJson.AsObject(MiniJson.Deserialize(text.Substring(objStart, i - objStart + 1)));
                            if (o != null) cards.Add(o);
                        }
                        catch (Exception) { /* a malformed card dies alone */ }
                        objStart = -1;
                    }
                    if (depth <= 0) break; // the array closed (or the text ran out honestly)
                }
            }
            return cards.Count > 0 ? cards : null;
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
            // RENDERED, OR THE FIELD IS DECORATION. `CharacterCard.Parse` puts
            // every `##` section into `Sections` and `ToPromptBlock` emits all of
            // them, so a section added here reaches the system prompt with no
            // other change — which is worth stating because the opposite
            // assumption is how this project has shipped systems that were built,
            // tested and never once called.
            sb.AppendLine("## Example Lines");
            sb.AppendLine("Things this person actually says. Match this register.");
            foreach (var l in MiniJson.GetList(card, "lines") ?? new List<object>())
                sb.AppendLine($"- \"{l}\"");
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
