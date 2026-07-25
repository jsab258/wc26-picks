using System;
using System.IO;
using System.Threading.Tasks;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Attaches Lena's brain (Core conversation engine + memory + suspicion)
    /// to an in-world character. Persists memory to a readable markdown file
    /// in the player's data folder.
    public class ConversationHost : MonoBehaviour
    {
        public const float TalkRange = 3.0f;

        GameController _game;
        ConversationEngine _engine;
        AnthropicClient _client;

        public CharacterCard Card { get; private set; }
        public MemoryStore Memory { get; private set; }
        public KnowledgeBase Knowledge { get; private set; }
        public SuspicionTracker Suspicion { get; private set; }
        public bool Ready => _engine != null;
        public string MemoryFilePath { get; private set; }

        public void Initialize(GameController game, string cardMarkdown,
            Action<KnowledgeBase> seedKnowledge, Action<MemoryStore> seedMemories)
        {
            _game = game;
            Card = CharacterCard.Parse(cardMarkdown);

            MemoryFilePath = Path.Combine(Application.persistentDataPath, "memories", $"{Card.Id}.md");
            Memory = new MemoryStore(Card.Id, MemoryFilePath);
            seedMemories?.Invoke(Memory);

            // One knowledge base for the character's whole life: the conversation
            // engine checks claims against it AND the gossip mill shares it, so a lie
            // told in dialogue can be contradicted by a rumor and vice versa.
            Knowledge = new KnowledgeBase();
            seedKnowledge?.Invoke(Knowledge);
            Suspicion = new SuspicionTracker();

            var key = Secrets.LoadAnthropicKey();
            if (string.IsNullOrEmpty(key)) return; // DialogueUI will prompt and call Reconnect

            Connect(key);
        }

        public void Reconnect(string apiKey) => Connect(apiKey);

        void Connect(string apiKey)
        {
            _client?.Dispose(); // Reconnect (F2 re-key) must not leak the previous HttpClient.
            _client = new AnthropicClient(apiKey);
            _engine = new ConversationEngine(_client, Card, Memory, Knowledge, Suspicion, _game.Cost);
        }

        public bool PlayerInRange(Transform player) =>
            player != null && Vector3.Distance(player.position, transform.position) <= TalkRange;

        /// Where this character usually is when spoken to; set per character at spawn.
        public string SceneContext = "On Hook Street, talking with the new owner.";

        /// Live campaign flavor appended to the scene each turn (street mood, and for
        /// those who'd know it, the state of the bar's takings). Set by GameController.
        public Func<string> ExtraContext;

        public async Task<string> SayAsync(string playerInput)
        {
            if (_engine == null) return "(no API key configured)";
            try
            {
                var scene = ExtraContext != null ? $"{SceneContext} {ExtraContext()}" : SceneContext;
                return await _engine.SayToAsync(playerInput, _game.Now, scene);
            }
            catch (LlmApiException e)
            {
                Debug.LogError($"{Card.Name} API error: {e.Message}");
                return e.StatusCode == 401
                    ? "(the API key was rejected — press F2 to re-enter it)"
                    : "(they seem distracted — connection trouble, try again)";
            }
            catch (Exception e)
            {
                Debug.LogError($"{Card.Name} error: {e}");
                return "(they seem distracted — something went wrong, try again)";
            }
        }

        public async Task RunReflectionAsync(GameTime now)
        {
            try { await _engine.ReflectAsync(now.Day, now); }
            catch (Exception e) { Debug.LogWarning($"Reflection failed: {e.Message}"); }
        }

        public string DebugReport()
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"== {Card.Name} ==");
            sb.AppendLine($"Suspicion: {Suspicion.Value:0.00} ({Suspicion.Level})");
            sb.AppendLine($"Memory file: {MemoryFilePath}");
            sb.AppendLine();
            sb.AppendLine("Beliefs:");
            foreach (var b in Memory.Beliefs) sb.AppendLine($"- {b}");
            sb.AppendLine();
            sb.AppendLine("Recent events:");
            int start = Mathf.Max(0, Memory.Events.Count - 12);
            for (int i = start; i < Memory.Events.Count; i++)
                sb.AppendLine(Memory.Events[i].ToLine());
            sb.AppendLine();
            sb.Append(_game.Cost.Report());
            return sb.ToString();
        }

        void OnDestroy() => _client?.Dispose();
    }
}
