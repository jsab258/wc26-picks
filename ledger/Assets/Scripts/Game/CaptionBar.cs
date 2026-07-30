using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// The sounds, in words, for a player who cannot hear them (audit item 4).
    ///
    /// `Core/Captions` decides WHAT a sound reads as and whether it should be
    /// shown at all. This puts it on the screen and takes it off again, and
    /// owns nothing else — same split as everywhere in this project.
    ///
    /// AT THE BOTTOM, NOT THE TOP, and low contrast. Captions are the one
    /// accessibility feature most likely to be left on by somebody who does
    /// not strictly need it, and a bright box at the top of the frame in a
    /// game whose whole art direction is a dark wet street would be the
    /// loudest thing in the image. It has to be readable and it must not win.
    ///
    /// THREE LINES, oldest falling off. A caption stack that grows without
    /// limit turns a busy street into a scrolling log — the same failure the
    /// mixer's voice budget exists to prevent, in a different medium.
    public class CaptionBar : MonoBehaviour
    {
        public const int MaxLines = 3;
        public const float HoldSeconds = 3.5f;
        public const float FadeSeconds = 0.6f;

        class Line { public string Text; public float Until; public Text Ui; }

        static CaptionBar _instance;
        readonly List<Line> _lines = new List<Line>();
        RectTransform _stack;
        bool _hushShown;
        bool _stemShown;

        /// Counted so a verification run can assert the channel actually
        /// carried something, rather than that it was constructed. The ring
        /// spent a week reporting rings it had built and never drawn.
        public static int Shown { get; private set; }

        /// Counted separately because it is the fragile one: the hush has no
        /// sound event to hang itself on, so it is POLLED rather than pushed,
        /// and a polled channel dies silently in a way a pushed one does not.
        public static int Hushes { get; private set; }

        public static CaptionLevel Level =>
            (CaptionLevel)Mathf.Clamp(GameSettings.Current.Captions, 0, 2);

        public static void ResetCounters() { Shown = 0; Hushes = 0; }

        public static CaptionBar Ensure()
        {
            if (_instance != null) return _instance;
            var go = new GameObject("CaptionBar");
            Object.DontDestroyOnLoad(go);
            _instance = go.AddComponent<CaptionBar>();
            return _instance;
        }

        void Awake()
        {
            _instance = this;
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            // Above the world and below anything modal. A caption that a
            // dialogue panel covers is a caption nobody reads.
            canvas.sortingOrder = 400;
            var scaler = gameObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);

            var stack = new GameObject("Stack", typeof(RectTransform));
            stack.transform.SetParent(transform, false);
            _stack = (RectTransform)stack.transform;
            _stack.anchorMin = new Vector2(0.5f, 0f);
            _stack.anchorMax = new Vector2(0.5f, 0f);
            _stack.pivot = new Vector2(0.5f, 0f);
            _stack.anchoredPosition = new Vector2(0f, 110f);
            _stack.sizeDelta = new Vector2(1100f, 40f * MaxLines);
        }

        /// Put a line up. Null and blank are no-ops, so a caller can pass the
        /// result of `Captions.ForSound` straight through without asking
        /// whether it produced anything.
        public static void Show(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            var bar = Ensure();
            // The same line twice running is one event heard twice, not two
            // events — a door that slams while its caption is still up should
            // refresh the line rather than stack a duplicate under it.
            for (int i = 0; i < bar._lines.Count; i++)
                if (bar._lines[i].Text == text)
                {
                    bar._lines[i].Until = Time.time + HoldSeconds;
                    return;
                }
            bar._lines.Add(new Line { Text = text, Until = Time.time + HoldSeconds });
            while (bar._lines.Count > MaxLines)
            {
                if (bar._lines[0].Ui != null) Destroy(bar._lines[0].Ui.gameObject);
                bar._lines.RemoveAt(0);
            }
            Shown++;
            bar.Rebuild();
        }

        void Rebuild()
        {
            for (int i = 0; i < _lines.Count; i++)
            {
                var l = _lines[i];
                if (l.Ui == null)
                {
                    var go = new GameObject("Caption", typeof(RectTransform));
                    go.transform.SetParent(_stack, false);
                    var t = go.AddComponent<Text>();
                    t.font = UiTheme.LoadFont();
                    t.fontSize = UiTheme.Small;
                    t.alignment = TextAnchor.LowerCenter;
                    t.horizontalOverflow = HorizontalWrapMode.Overflow;
                    t.color = UiTheme.Dim;
                    var rt = (RectTransform)go.transform;
                    rt.anchorMin = new Vector2(0f, 0f);
                    rt.anchorMax = new Vector2(1f, 0f);
                    rt.pivot = new Vector2(0.5f, 0f);
                    rt.sizeDelta = new Vector2(0f, 36f);
                    l.Ui = t;
                }
                l.Ui.text = l.Text;
                ((RectTransform)l.Ui.transform).anchoredPosition =
                    new Vector2(0f, (_lines.Count - 1 - i) * 36f);
            }
        }

        void Update()
        {
            var level = Level;
            if (level != CaptionLevel.SpeechAndSound)
            {
                // Turned off mid-game: clear rather than leaving the last
                // three lines frozen on screen forever.
                if (_lines.Count > 0) Clear();
                _hushShown = _stemShown = false;
                return;
            }

            // THE STREET GOING QUIET, polled rather than emitted, because it
            // is the absence of a sound and there is no event to hang it on.
            // §6.2 calls this the best idea in the section and it is the one
            // channel a deaf player had no access to at all.
            var hush = Captions.ForHush(level, Perceivers.Hush, _hushShown);
            if (hush != null)
            {
                Show(hush);
                Hushes++;
                _hushShown = !_hushShown;
            }

            // The fourth channel. One low stem enters when somebody's
            // attention is genuinely on you and nothing else in the mix does
            // that, which is what makes it captionable without ambiguity.
            bool attention = Perceivers.Attending > 0;
            if (attention && !_stemShown) Show(Captions.ForAttentionStem(level, true));
            _stemShown = attention;

            for (int i = _lines.Count - 1; i >= 0; i--)
            {
                float left = _lines[i].Until - Time.time;
                if (left <= 0f)
                {
                    if (_lines[i].Ui != null) Destroy(_lines[i].Ui.gameObject);
                    _lines.RemoveAt(i);
                    continue;
                }
                if (_lines[i].Ui != null && left < FadeSeconds)
                {
                    var c = UiTheme.Dim;
                    c.a = Mathf.Clamp01(left / FadeSeconds);
                    _lines[i].Ui.color = c;
                }
            }
            if (_lines.Count > 0) Rebuild();
        }

        void Clear()
        {
            foreach (var l in _lines)
                if (l.Ui != null) Destroy(l.Ui.gameObject);
            _lines.Clear();
        }
    }
}
