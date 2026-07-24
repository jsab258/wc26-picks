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

            var kb = new KnowledgeBase();
            seedKnowledge?.Invoke(kb);
            Suspicion = new SuspicionTracker();

            var key = Secrets.LoadAnthropicKey();
            if (string.IsNullOrEmpty(key)) return; // DialogueUI will prompt and call Reconnect

            Connect(key, kb);
        }

        public void Reconnect(string apiKey)
        {
            var kb = new KnowledgeBase();
            LenaSetup.SeedKnowledge(kb);
            Connect(apiKey, kb);
        }

        void Connect(string apiKey, KnowledgeBase kb)
        {
            _client?.Dispose(); // Reconnect (F2 re-key) must not leak the previous HttpClient.
            _client = new AnthropicClient(apiKey);
            _engine = new ConversationEngine(_client, Card, Memory, kb, Suspicion, _game.Cost);
        }

        public bool PlayerInRange(Transform player) =>
            player != null && Vector3.Distance(player.position, transform.position) <= TalkRange;

        public async Task<string> SayAsync(string playerInput)
        {
            if (_engine == null) return "(no API key configured)";
            try
            {
                return await _engine.SayToAsync(playerInput, _game.Now,
                    "Behind the counter of the Hook Street bar, talking with the new owner.");
            }
            catch (LlmApiException e)
            {
                Debug.LogError($"Lena API error: {e.Message}");
                return e.StatusCode == 401
                    ? "(the API key was rejected — press F2 to re-enter it)"
                    : "(she seems distracted — connection trouble, try again)";
            }
            catch (Exception e)
            {
                Debug.LogError($"Lena error: {e}");
                return "(she seems distracted — something went wrong, try again)";
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
