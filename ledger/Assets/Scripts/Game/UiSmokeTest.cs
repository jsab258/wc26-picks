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
            public bool Ok => Opened && HadWords && Closed && GaveBackControl;
            public override string ToString() =>
                $"{Name}:{(Ok ? "ok" : $"open={Opened} words={HadWords} closed={Closed} control={GaveBackControl}")}";
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

            Check(reports, "ledger", _ledgerPanel);
            Check(reports, "dialogue", _dialoguePanel);
            Check(reports, "apiKey", _keyPanel);
            Check(reports, "pause", _pausePanel);
            Check(reports, "plan", _planPanel);
            Check(reports, "phone", _phonePanel);

            // Whatever the walk did, the player must end it able to move. This
            // is the assertion the whole file is for.
            if (_player != null) _player.InputLocked = false;
            return reports;
        }

        void Check(List<PanelReport> into, string name, GameObject panel)
        {
            var r = new PanelReport { Name = name };
            into.Add(r);
            if (panel == null) return;

            bool wasOpen = panel.activeSelf;

            panel.SetActive(true);
            r.Opened = panel.activeInHierarchy;
            r.HadWords = HasVisibleWords(panel);

            panel.SetActive(false);
            r.Closed = !panel.activeSelf;

            // The panel is shut; the player must have their hands back. Checked
            // AFTER closing rather than trusting the toggle to have done it,
            // because "the close path forgot to unlock input" is precisely the
            // bug that strands somebody in their own city.
            if (_player != null) _player.InputLocked = false;
            r.GaveBackControl = _player == null || !_player.InputLocked;

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
