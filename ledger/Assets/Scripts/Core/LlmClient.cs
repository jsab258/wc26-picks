using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Ledger.Core
{
    public class LlmMessage
    {
        public string Role;
        public string Content;
        public LlmMessage(string role, string content) { Role = role; Content = content; }
    }

    public class LlmRequest
    {
        public string Model;
        public string System;
        public List<LlmMessage> Messages = new List<LlmMessage>();
        public int MaxTokens = 1024;
    }

    public class LlmResponse
    {
        public string Text = "";
        public string StopReason = "";
        public int InputTokens;
        public int OutputTokens;
        public string Model = "";
    }

    public interface ILlmClient
    {
        Task<LlmResponse> CompleteAsync(LlmRequest request, CancellationToken ct = default);
    }

    /// Model tiering per design doc: cheap/fast for the ambient population,
    /// stronger for the authored core cast. Cost table used by CostTracker
    /// (USD per million tokens; sonnet uses post-intro sticker prices so
    /// estimates stay conservative).
    public static class Models
    {
        public const string Core = "claude-sonnet-5";
        public const string Ambient = "claude-haiku-4-5";

        public static readonly Dictionary<string, (double inPerM, double outPerM)> Cost =
            new Dictionary<string, (double, double)>
            {
                { Core, (3.0, 15.0) },
                { Ambient, (1.0, 5.0) },
            };
    }

    /// Raw-HTTP Anthropic Messages API client. Dependency-free by design so the
    /// identical code runs under Unity (Mono/IL2CPP) and plain .NET; the official
    /// C# SDK is not validated for Unity runtimes. Wire format per Anthropic docs.
    public class AnthropicClient : ILlmClient, IDisposable
    {
        readonly HttpClient _http;
        readonly string _apiKey;
        public int MaxRetries = 3;
        public Func<int, TimeSpan> RetryDelay = attempt => TimeSpan.FromSeconds(Math.Pow(2, attempt)); // 2s,4s,8s

        public AnthropicClient(string apiKey, TimeSpan? timeout = null)
        {
            _apiKey = apiKey;
            _http = new HttpClient { Timeout = timeout ?? TimeSpan.FromSeconds(60) };
        }

        public async Task<LlmResponse> CompleteAsync(LlmRequest request, CancellationToken ct = default)
        {
            var messages = new List<object>();
            foreach (var m in request.Messages)
                messages.Add(new Dictionary<string, object> { { "role", m.Role }, { "content", m.Content } });

            var body = new Dictionary<string, object>
            {
                { "model", request.Model },
                { "max_tokens", request.MaxTokens },
                { "messages", messages },
            };
            if (!string.IsNullOrEmpty(request.System)) body["system"] = request.System;

            var json = MiniJson.Serialize(body);

            for (int attempt = 0; ; attempt++)
            {
                using var msg = new HttpRequestMessage(HttpMethod.Post, "https://api.anthropic.com/v1/messages");
                msg.Headers.Add("x-api-key", _apiKey);
                msg.Headers.Add("anthropic-version", "2023-06-01");
                msg.Content = new StringContent(json, Encoding.UTF8, "application/json");

                HttpResponseMessage resp;
                try
                {
                    resp = await _http.SendAsync(msg, ct).ConfigureAwait(false);
                }
                catch (Exception ex) when (ex is HttpRequestException || ex is TaskCanceledException)
                {
                    if (attempt >= MaxRetries || ct.IsCancellationRequested) throw;
                    await Task.Delay(RetryDelay(attempt + 1), ct).ConfigureAwait(false);
                    continue;
                }

                var text = await resp.Content.ReadAsStringAsync().ConfigureAwait(false);
                int status = (int)resp.StatusCode;
                resp.Dispose();

                if (status == 429 || status >= 500)
                {
                    if (attempt >= MaxRetries)
                        throw new LlmApiException(status, ExtractErrorMessage(text));
                    await Task.Delay(RetryDelay(attempt + 1), ct).ConfigureAwait(false);
                    continue;
                }
                if (status >= 400)
                    throw new LlmApiException(status, ExtractErrorMessage(text));

                return ParseResponse(text);
            }
        }

        static string ExtractErrorMessage(string body)
        {
            try
            {
                var root = MiniJson.AsObject(MiniJson.Deserialize(body));
                var error = MiniJson.GetObject(root, "error");
                return MiniJson.GetString(error, "message") ?? body;
            }
            catch { return body; }
        }

        public static LlmResponse ParseResponse(string json)
        {
            var root = MiniJson.AsObject(MiniJson.Deserialize(json));
            var result = new LlmResponse
            {
                StopReason = MiniJson.GetString(root, "stop_reason") ?? "",
                Model = MiniJson.GetString(root, "model") ?? "",
            };
            var usage = MiniJson.GetObject(root, "usage");
            result.InputTokens = MiniJson.GetInt(usage, "input_tokens");
            result.OutputTokens = MiniJson.GetInt(usage, "output_tokens");

            var content = MiniJson.GetList(root, "content");
            if (content != null)
            {
                var sb = new StringBuilder();
                foreach (var blockObj in content)
                {
                    var block = MiniJson.AsObject(blockObj);
                    if (MiniJson.GetString(block, "type") == "text")
                        sb.Append(MiniJson.GetString(block, "text"));
                }
                result.Text = sb.ToString();
            }
            return result;
        }

        public void Dispose() => _http.Dispose();
    }

    public class LlmApiException : Exception
    {
        public int StatusCode { get; }
        public LlmApiException(int statusCode, string message) : base($"HTTP {statusCode}: {message}")
        {
            StatusCode = statusCode;
        }
    }
}
