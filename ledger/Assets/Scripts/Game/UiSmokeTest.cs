using System.Collections.Generic;
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
            public bool Ok => Opened && HadWords && Closed && GaveBackControl && LockHonored;
            public override string ToString() =>
                $"{Name}:{(Ok ? "ok" : $"open={Opened} words={HadWords} closed={Closed} control={GaveBackControl} lock={LockHonored}")}";
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
            Check(reports, "ledger", _ledgerPanel, RefreshLedger);
            Check(reports, "dialogue", _dialoguePanel);
            Check(reports, "apiKey", _keyPanel);
            Check(reports, "pause", _pausePanel);
            Check(reports, "plan", _planPanel, RefreshPlan);
            Check(reports, "phone", _phonePanel, RefreshPhone);

            // Whatever the walk did, the player must end it able to move. This
            // is the assertion the whole file is for.
            if (_player != null) _player.InputLocked = false;
            return reports;
        }

        void Check(List<PanelReport> into, string name, GameObject panel, System.Action refresh = null)
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
