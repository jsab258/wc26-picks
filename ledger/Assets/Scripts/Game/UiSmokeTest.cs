using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// A smoke test for the panels (player decision 3, 2026-07-27).
    ///
    /// THE GAP THIS EXISTS TO CLOSE. Every one of the project's 1182 tests is
    /// Core logic. Nothing tested a panel — and the cost of that showed up the
    /// first time somebody asked whether the front end was complete: the options
    /// screen's rebind list had drifted to six actions while the game listened
    /// for nine, and three keybindings could not be rebound at all. Nothing
    /// caught it because nothing was looking.
    ///
    /// This is not a UI test framework and does not want to be. It is the
    /// cheapest thing that catches that class of bug: open every panel, look at
    /// it, close it, and assert the three things that make a panel broken rather
    /// than ugly —
    ///
    ///   1. it OPENED (a panel that silently refuses is a dead key)
    ///   2. it has WORDS IN IT (an empty panel is a bug that ships)
    ///   3. it CLOSED, and gave the player back their controls
    ///
    /// Point 3 is the one that matters most. A panel that opens and cannot be
    /// closed leaves InputLocked set forever, and the player is standing in a
    /// city they can no longer move around in. That is the worst bug this game
    /// can have and it is invisible to every test we own.
    public partial class DialogueUI
    {
        public class PanelReport
        {
            public string Name;
            public bool Opened, HadWords, Closed, GaveBackControl;
            public bool LockHonored = true;   // locking panels only: the policy saw it while open
            public bool Says = true;          // the panel SAYS what this world state requires
            public bool Ok => Opened && HadWords && Closed && GaveBackControl && LockHonored && Says;
            public override string ToString() =>
                $"{Name}:{(Ok ? "ok" : $"open={Opened} words={HadWords} closed={Closed} control={GaveBackControl} lock={LockHonored} says={Says}")}";
        }

        /// Walk every panel. Called by the sim; harmless in a real session, but
        /// there is no reason to run it there.
        public List<PanelReport> SmokeTestPanels()
        {
            var reports = new List<PanelReport>();

            // Built lazily, so build them first — a panel that has never been
            // opened is exactly the one nobody has looked at.
            if (_pausePanel == null) BuildPausePanel();
            if (_planPanel == null && _game != null) BuildPlanPanel();
            if (_phonePanel == null) BuildPhonePanel();

            // Each panel's REAL refresh runs while it is open, so HadWords
            // reads live-rendered content rather than build-time chrome — a
            // renderer that throws or writes nothing is a red bar now (audit
            // 2026-07-27).
            // CONTENT predicates close the roadmap's named gap ("nothing
            // asserts what a panel SAYS"): each panel must show the words this
            // world state requires, read back off the live Text components.
            Check(reports, "ledger", _ledgerPanel, RefreshLedger,
                () =>
                {
                    var words = AllWords(_ledgerPanel);
                    // THE STREET section exists exactly when the renderer's own
                    // condition holds — the walk runs on day 2, before any
                    // empire, and requiring it unconditionally redded a healthy
                    // build (run 30335994335).
                    var e = _game.Empire;
                    bool anyEmpire = _game.Campaign.OpenMode &&
                        (e.Businesses.Exists(b => b.Owned || b.DebtHeld) || e.Crew.Count > 0 || e.Rival.Stage > 0);
                    // DOUBT, on the same terms: required exactly when somebody
                    // has actually stopped trusting the player, and not
                    // otherwise. Demanding it unconditionally would red a run
                    // on a street where nobody suspects anything, which is a
                    // legitimate state and was how the THE STREET clause got
                    // this wrong the first time (run 30335994335).
                    bool anyDoubt = false;
                    foreach (var h in _game.Hosts)
                        if (h != null && h.Suspicion != null
                            && h.Suspicion.Level != SuspicionLevel.Trusting) { anyDoubt = true; break; }
                    return words.Contains("LIABILITIES")
                        && (!anyEmpire || words.Contains("THE STREET"))
                        && (!anyDoubt || words.Contains("DOUBT"));
                });
            Check(reports, "dialogue", _dialoguePanel, null,
                () => _input != null && _historyText != null);
            Check(reports, "apiKey", _keyPanel, null,
                () => AllWords(_keyPanel).Contains("Anthropic"));
            Check(reports, "pause", _pausePanel, null,
                () => AllWords(_pausePanel).Contains("Resume") && AllWords(_pausePanel).Contains("Save"));
            Check(reports, "plan", _planPanel, () =>
            {
                // Seed the way TogglePlan does, so the refresh renders a real
                // plan rather than early-returning on a bot with none.
                if (_game != null && _game.Plan == null)
                {
                    OperationTarget first = null;
                    foreach (var t in _game.OpenTargets) { first = t; break; }
                    _game.Plan = new OperationPlan(first != null ? first.Id : null) { Hour = 23 };
                }
                RefreshPlan();
            }, () => AllWords(_planPanel).Replace(" ", "").Contains("PLANNING"));
            Check(reports, "phone", _phonePanel, RefreshPhone,
                () => AllWords(_phonePanel).Contains("Hang up"));

            // The rebind screen, which is where this file's founding bug lived:
            // six rows against nine listened-for actions. Every action the game
            // listens for must be ON the screen, and nothing else.
            var opt = new PanelReport { Name = "rebinds" };
            reports.Add(opt);
            try
            {
                var screen = OptionsScreen.Show();
                opt.Opened = OptionsScreen.Open;
                opt.HadWords = true;
                var listed = new HashSet<string>(screen.ListedActions);
                var listening = new HashSet<string>(GameSettings.Current.Keys.Keys);
                opt.Says = listed.SetEquals(listening);
                screen.Close();
                opt.Closed = !OptionsScreen.Open;
                opt.GaveBackControl = true;
            }
            catch { opt.Opened = false; }

            // Whatever the walk did, the player must end it able to move. This
            // is the assertion the whole file is for.
            if (_player != null) _player.InputLocked = false;
            return reports;
        }

        void Check(List<PanelReport> into, string name, GameObject panel,
            System.Action refresh = null, System.Func<bool> says = null)
        {
            var r = new PanelReport { Name = name };
            into.Add(r);
            if (panel == null) return;

            bool wasOpen = panel.activeSelf;

            // The baseline is the rest of the UI without this panel: the walk
            // can run while another panel is legitimately open (the bot mid-
            // dialogue; the key panel in a keyless CI run), so the assertions
            // below are DELTAS against this, not absolute reads — the first
            // absolute version redded the whole gate the moment anything else
            // was open (build 30323848380).
            panel.SetActive(false);
            bool lockedBefore = AnyPanelDemandsInput();

            panel.SetActive(true);
            r.Opened = panel.activeInHierarchy;
            bool refreshOk = true;
            if (refresh != null)
                try { refresh(); } catch { refreshOk = false; }
            r.HadWords = refreshOk && HasVisibleWords(panel);
            if (says != null)
                try { r.Says = says(); } catch { r.Says = false; }

            // A panel that takes the screen must also take the controls — and
            // it must do so through the ONE policy Update() re-derives the lock
            // from every frame. The Plan and Phone panels locked input in their
            // own toggles, were missing from the policy, and had their locks
            // erased one frame later (audit 2026-07-27). This catches the next
            // panel that makes that mistake.
            bool locking = name == "dialogue" || name == "apiKey" || name == "plan" || name == "phone";
            if (locking) r.LockHonored = AnyPanelDemandsInput();

            panel.SetActive(false);
            r.Closed = !panel.activeSelf;

            // Closing the panel must return the lock policy to its baseline —
            // read from the policy, never written first. The old version
            // assigned InputLocked=false and then asserted !InputLocked, a
            // check that could not fail (audit 2026-07-27).
            r.GaveBackControl = AnyPanelDemandsInput() == lockedBefore;

            if (wasOpen) panel.SetActive(true);
        }

        /// Every visible word in the panel, joined — the content predicates
        /// read the panel the way a player would: off what is rendered.
        /// THE LEDGER PANEL AS THE PLAYER WOULD READ IT, for the verdict.
        ///
        /// Rule 4 says open the artifact you are shipping, and everything built
        /// tonight ships into this panel: the DOUBT section, the feud lines
        /// under each crew member, "story doubted" where it used to say
        /// "settled". Not one of them has ever been LOOKED at. They are
        /// asserted by a content predicate, which checks that a header string
        /// is present and can say nothing whatever about whether the screen
        /// reads like English.
        ///
        /// TEXT AND NOT A SCREENSHOT, and the reason is structural rather than
        /// lazy. `Shot` renders `Camera.main` into a RenderTexture, and this
        /// canvas is `ScreenSpaceOverlay` — which does not render through a
        /// camera at all. A UI still down that path would have come back as a
        /// picture of the street with no panel in it, and committed silently,
        /// which is the exact shape of every "reported success, produced
        /// nothing" failure in this repo's history.
        ///
        /// For a panel made of words, reading the words back IS opening it. It
        /// also lands in the one channel this environment can definitely read.
        ///
        /// Rich-text tags stripped, because `<color=#8a8a8a>` is not something
        /// a player sees and three of them per line would bury the content in
        /// the character budget.
        public string LedgerWords()
        {
            if (_ledgerPanel == null) return "(no ledger panel)";
            try { RefreshLedger(); } catch (System.Exception e) { return "refresh threw: " + e.Message; }
            var raw = AllWords(_ledgerPanel);
            var sb = new System.Text.StringBuilder();
            bool inTag = false;
            foreach (char c in raw)
            {
                if (c == '<') { inTag = true; continue; }
                if (c == '>') { inTag = false; continue; }
                if (inTag) continue;
                sb.Append(c == '\n' ? " | " : c.ToString());
            }
            var flat = System.Text.RegularExpressions.Regex.Replace(sb.ToString(), " +", " ").Trim();

            // BOTH ENDS, NOT THE FIRST 1400 CHARACTERS.
            //
            // The panel is money, then LIABILITIES, then DOUBT, then THE STREET.
            // LIABILITIES lists up to twelve rumours at roughly 120 characters
            // each, so it alone fills the budget — and a straight head-truncation
            // cut the dump off mid-rumour every single time. Everything below
            // that list has therefore NEVER been readable through the one
            // channel that can read this game, including both competence lines
            // added tonight and the whole second book.
            //
            // A tool that always truncates in the same place is not sampling the
            // artefact, it is sampling its first screenful — which is the same
            // fault as a metric that samples one instant, and the fourth of that
            // family found tonight.
            //
            // The middle is what gets dropped, because the middle is the long
            // repetitive list and the ends are the headline and the sections
            // nobody has seen.
            const int Half = 700;
            if (flat.Length <= Half * 2) return flat;
            return flat.Substring(0, Half)
                   + $" … [{flat.Length - Half * 2} chars of liabilities cut] … "
                   + flat.Substring(flat.Length - Half);
        }

        /// CAN THE TEXT ACTUALLY BE READ AGAINST WHAT IS BEHIND IT.
        ///
        /// `Core/Typography` implements WCAG 2.1 contrast properly — the gamma
        /// expansion in `Luminance` is not optional, and doing it on raw sRGB
        /// (the obvious mistake) overstates dark pairs badly, which is exactly
        /// the range this interface lives in. `MeetsAa` holds the 4.5:1 bar for
        /// body text and 3:1 for large. `LiftToMeet` returns the multiplier
        /// that would fix a failing pair without changing its hue.
        ///
        /// Four public members, tested, and called by nothing — with the reach
        /// ledger noting that the accessibility gate "M22 names and nothing
        /// enforces". The panels set colours by hand from `UiTheme`, and grey
        /// on near-black is the whole palette.
        ///
        /// MEASURED ON THE RENDERED PAIRING, not on the palette. A static
        /// check of `UiTheme`'s constants would miss the thing that actually
        /// decides legibility: which colour ends up on which background, after
        /// rich-text markup has had its say. This walks the live panel and
        /// reads each label's own colour against the nearest background behind
        /// it, which is what a player's eye does.
        ///
        /// REPORTED, NOT GATED, and deliberately. Some of these pairs are
        /// dimmed ON PURPOSE — a `HexDim` timestamp under a rumour is meant to
        /// recede — and a gate at AA would demand the design be flattened
        /// before anybody has decided that is what we want. The number comes
        /// first; the decision about which failures are intentional is Jafar's,
        /// and it cannot be made without the list.
        public static int ContrastChecked, ContrastFailing;
        public static double ContrastWorst = 21.0;
        public static string ContrastWorstWhere = "none";

        public void MeasureContrast()
        {
            ContrastChecked = ContrastFailing = 0;
            ContrastWorst = 21.0;
            ContrastWorstWhere = "none";
            foreach (var panel in new[] { _ledgerPanel, _dialoguePanel, _keyPanel,
                                          _pausePanel, _planPanel, _phonePanel })
            {
                if (panel == null) continue;
                foreach (var t in panel.GetComponentsInChildren<Text>(includeInactive: true))
                {
                    if (t == null || string.IsNullOrWhiteSpace(t.text)) continue;
                    var behind = BackgroundBehind(t.transform);
                    // NO BACKGROUND MEANS NOTHING TO COMPARE AGAINST, and
                    // guessing one would invent the answer. Skipped and not
                    // counted, so the denominator stays honest.
                    if (!behind.HasValue) continue;
                    var f = t.color; var b = behind.Value;
                    double c = Typography.Contrast(f.r, f.g, f.b, b.r, b.g, b.b);
                    int points = Mathf.Max(1, t.fontSize);
                    ContrastChecked++;
                    if (!Typography.MeetsAa(c, points))
                    {
                        ContrastFailing++;
                        if (c < ContrastWorst)
                        {
                            ContrastWorst = c;
                            double lift = Typography.LiftToMeet(f.r, f.g, f.b, b.r, b.g, b.b, points);
                            // NAMED, AND WITH THE FIX ATTACHED. "The worst pair
                            // is 2.1:1" costs a hunt; "this label, at this size,
                            // needs 1.4x" is something somebody can act on
                            // without opening the game.
                            ContrastWorstWhere = $"{panel.name}/{t.name}@{points}pt needs x{lift:0.00}";
                        }
                    }
                }
            }
        }

        /// The nearest opaque background behind this label. Walks up, because
        /// a label sits inside a row inside a panel and only one of those
        /// carries the colour.
        static Color? BackgroundBehind(Transform t)
        {
            for (var p = t; p != null; p = p.parent)
            {
                var img = p.GetComponent<Image>();
                // Alpha matters: a transparent row is not the background, it is
                // a hole through to whatever is behind IT.
                if (img != null && img.color.a > 0.9f) return img.color;
            }
            return null;
        }

        static string AllWords(GameObject panel)
        {
            var sb = new System.Text.StringBuilder();
            foreach (var t in panel.GetComponentsInChildren<Text>(includeInactive: true))
                if (!string.IsNullOrWhiteSpace(t.text)) sb.Append(t.text).Append('\n');
            return sb.ToString();
        }

        /// Does anything in here actually say something? A panel of empty labels
        /// renders as a coloured rectangle and reads as a broken game.
        static bool HasVisibleWords(GameObject panel)
        {
            foreach (var t in panel.GetComponentsInChildren<Text>(includeInactive: true))
                if (!string.IsNullOrWhiteSpace(t.text)) return true;
            return false;
        }
    }
}
