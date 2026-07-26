using System.Linq;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// The planning panel (roadmap M7.5). Four decisions and a sentence telling
    /// you what somebody thinks of them.
    ///
    /// It is a PANEL OF CHOICES, not a loadout screen, and the difference is
    /// that every control here changes the sentence at the bottom. If a control
    /// did not move the read it would not be a decision and it would not be on
    /// this panel.
    ///
    /// The read is words. Never a bar, never a percentage, never a colour-coded
    /// meter — that is the approved decision on visible odds, and the moment
    /// this panel grows a percentage the game has become a spreadsheet. It is
    /// also delivered in a CREW MEMBER'S VOICE when you have crew, because the
    /// person telling you this is a bad idea should be somebody who is coming
    /// with you.
    public partial class DialogueUI
    {
        GameObject _planPanel;
        Text _planTitle, _planBody, _planRead, _planWorry;
        Button _planGo, _planClose;
        Text _planGoLabel;
        int _planIndex;

        void TogglePlan()
        {
            if (_game == null || !_game.CanPlan) return;
            if (_planPanel == null) BuildPlanPanel();
            bool open = !_planPanel.activeSelf;
            _planPanel.SetActive(open);
            _player.InputLocked = open;
            if (open)
            {
                if (_game.Plan == null)
                {
                    var first = _game.OpenTargets.FirstOrDefault();
                    _game.Plan = new OperationPlan(first != null ? first.Id : null) { Hour = 23 };
                }
                RefreshPlan();
            }
            Audio.Ui("page");
        }

        void BuildPlanPanel()
        {
            _planPanel = MakePanel(_canvas, "Plan", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(760, 560));

            _planTitle = MakeText(_planPanel.transform, "PlanTitle", new Vector2(0.5f, 1),
                new Vector2(0, -20), new Vector2(700, 32), 22, TextAnchor.UpperCenter);
            _planTitle.color = UiTheme.Amber;

            _planBody = MakeText(_planPanel.transform, "PlanBody", new Vector2(0.5f, 1),
                new Vector2(0, -58), new Vector2(700, 300), 17, TextAnchor.UpperLeft);

            // Each row cycles rather than expanding into a submenu: four
            // decisions should fit on one screen you can read at a glance.
            Row("The job", 0, -104, CycleTarget);
            Row("How", 0, -150, CycleApproach);
            Row("When", 0, -196, CycleHour);
            Row("Who", 0, -242, CycleCrew);
            Row("Tools", 0, -288, () => { _game.Plan.Tools = !_game.Plan.Tools; RefreshPlan(); });

            _planRead = MakeText(_planPanel.transform, "PlanRead", new Vector2(0.5f, 0),
                new Vector2(0, 150), new Vector2(700, 60), 19, TextAnchor.UpperCenter);
            _planRead.color = UiTheme.Amber;
            _planWorry = MakeText(_planPanel.transform, "PlanWorry", new Vector2(0.5f, 0),
                new Vector2(0, 100), new Vector2(700, 48), 16, TextAnchor.UpperCenter);
            _planWorry.color = UiTheme.Dim;

            _planGo = MakeButton(_planPanel.transform, "Go", new Vector2(0.5f, 0), new Vector2(-160, 30), new Vector2(280, 44));
            _planGoLabel = _planGo.GetComponentInChildren<Text>();
            _planGo.onClick.AddListener(Commit);

            _planClose = MakeButton(_planPanel.transform, "Not tonight", new Vector2(0.5f, 0), new Vector2(160, 30), new Vector2(280, 44));
            _planClose.onClick.AddListener(TogglePlan);

            _planPanel.SetActive(false);
        }

        void Row(string label, float x, float y, UnityEngine.Events.UnityAction onClick)
        {
            var b = MakeButton(_planPanel.transform, label, new Vector2(0.5f, 1), new Vector2(x, y), new Vector2(640, 38));
            b.onClick.AddListener(onClick);
            _planRows.Add(b.GetComponentInChildren<Text>());
        }

        readonly System.Collections.Generic.List<Text> _planRows = new System.Collections.Generic.List<Text>();

        void CycleTarget()
        {
            var open = _game.OpenTargets.ToList();
            if (open.Count == 0) return;
            _planIndex = (_planIndex + 1) % open.Count;
            _game.Plan.TargetId = open[_planIndex].Id;
            RefreshPlan();
        }

        void CycleApproach()
        {
            _game.Plan.Approach = _game.Plan.Approach == Approach.Quiet ? Approach.Forced
                : _game.Plan.Approach == Approach.Forced ? Approach.Social : Approach.Quiet;
            RefreshPlan();
        }

        void CycleHour()
        {
            // Four hours worth choosing between, not twenty-four worth scrolling.
            int[] hours = { 23, 3, 12, 19 };
            int i = System.Array.IndexOf(hours, _game.Plan.Hour);
            _game.Plan.Hour = hours[(i + 1) % hours.Length];
            RefreshPlan();
        }

        void CycleCrew()
        {
            var crew = _game.Empire.ActiveCrew.Select(c => c.Name).ToList();
            if (crew.Count == 0) return;
            // Cycles through: nobody, then each person, then everybody.
            int have = _game.Plan.Crew.Count;
            _game.Plan.Crew.Clear();
            if (have == 0 && crew.Count > 0) _game.Plan.Crew.Add(crew[0]);
            else if (have < crew.Count) _game.Plan.Crew.AddRange(crew.Take(have + 1));
            RefreshPlan();
        }

        void RefreshPlan()
        {
            if (_game.Plan == null || _planPanel == null) return;
            var target = _game.TargetOf(_game.Plan.TargetId);
            _planTitle.text = "P L A N N I N G";

            if (target == null)
            {
                _planBody.text = "There is nothing on the board. Everything you knew about has been done.";
                _planRead.text = "";
                _planWorry.text = "";
                _planGo.gameObject.SetActive(false);
                return;
            }
            _planGo.gameObject.SetActive(true);

            _planBody.text =
                $"<b>{target.Name}</b>\n\n" +
                "Four things to decide. Each one buys you something and costs you\n" +
                "something else, and the line at the bottom is what it looks like\n" +
                "from where your people are standing.";

            var crewNames = _game.Plan.Crew.Count == 0 ? "nobody — you go alone"
                : string.Join(", ", _game.Plan.Crew);

            if (_planRows.Count >= 5)
            {
                _planRows[0].text = $"The job:  {target.Name}";
                _planRows[1].text = "How:  " + (_game.Plan.Approach == Approach.Quiet ? "quietly, and slowly"
                    : _game.Plan.Approach == Approach.Forced ? "force it, and be quick"
                    : "talk your way in");
                _planRows[2].text = $"When:  {HourWord(_game.Plan.Hour)}";
                _planRows[3].text = $"Who:  {crewNames}";
                _planRows[4].text = "Tools:  " + (_game.Plan.Tools ? "carry them" : "go empty-handed");
            }

            var read = _game.ReadPlan();
            if (read != null && GameSettings.Current.ShowOdds)
            {
                // In a crew member's voice when there is one. The person telling
                // you this is a bad idea ought to be somebody who is coming.
                var speaker = _game.Plan.Crew.FirstOrDefault();
                _planRead.text = speaker != null ? $"{speaker}: \"{read.Line}\"" : read.Line;
                _planWorry.text = read.Worry;
            }
            else
            {
                _planRead.text = "";
                _planWorry.text = "Nobody offers an opinion. (Odds are off in options.)";
            }
            _planGoLabel.text = $"Go at {HourWord(_game.Plan.Hour)}";
        }

        static string HourWord(int h) =>
            h == 3 ? "three in the morning" : h == 12 ? "the middle of the day"
            : h == 19 ? "just after dark" : "eleven at night";

        void Commit()
        {
            var outcome = _game.RunPlan();
            _planPanel.SetActive(false);
            _player.InputLocked = false;
            if (outcome == null) return;

            Toast(outcome.Line, 10f);
            if (outcome.Take > 0) Toast($"+${outcome.Take}, and none of it can be spent where anyone is looking.", 8f);
            if (outcome.Witnesses > 0)
                Toast(outcome.Witnesses == 1
                    ? "One person saw something. One is enough to start with."
                    : $"{outcome.Witnesses} people saw something.", 9f);
            foreach (var who in outcome.Talkers)
                Toast($"{who} has not said much since. That is not the same as saying nothing.", 9f);
        }
    }
}
