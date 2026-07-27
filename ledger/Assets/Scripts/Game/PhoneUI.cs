using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// The telephone panel (roadmap M10).
    ///
    /// Stand near a line, press the key, and you get a list of the people that
    /// line might reach. Pick one and it rings — and the panel deliberately does
    /// NOT tell you in advance whether they will answer.
    ///
    /// That absence is the whole design. A list that greyed out whoever is not
    /// near the phone would be a menu of guaranteed outcomes, and the interesting
    /// thing about a telephone in 1920-something is that you are gambling on
    /// somebody's afternoon. You find out by ringing, and ringing has a cost:
    /// whoever picks up knows you called.
    ///
    /// Three outcomes, three different panels-worth of decision:
    ///   they answer      -> you talk, and the line damps what either of you can
    ///                       read in the other
    ///   somebody else    -> leave word or hang up, and hanging up is not free
    ///                       either, because they heard the phone ring
    ///   nobody           -> the hour was wrong, which is information
    public partial class DialogueUI
    {
        GameObject _phonePanel;
        Text _phoneTitle, _phoneBody, _phoneResult;
        readonly List<Button> _phoneRows = new List<Button>();
        Button _phoneMessage, _phoneClose;
        string _phonePlaceId;
        Call _lastCall;

        /// The line the player is standing next to, or null.
        string LineInReach()
        {
            if (_game == null || _player == null) return null;
            foreach (var p in _game.Phones.All)
            {
                if (!_game.PhoneNear(p.PlaceId, _player.transform.position)) continue;
                return p.PlaceId;
            }
            return null;
        }

        void TogglePhone()
        {
            if (_game == null) return;
            var line = LineInReach();
            if (_phonePanel == null || !_phonePanel.activeSelf)
            {
                if (line == null)
                {
                    Toast("There is no telephone here. The bar has one, and so do four other places on this map.", 6f);
                    return;
                }
                _phonePlaceId = line;
            }
            if (_phonePanel == null) BuildPhonePanel();

            bool open = !_phonePanel.activeSelf;
            _phonePanel.SetActive(open);
            _player.InputLocked = open;
            if (open) { _lastCall = null; RefreshPhone(); }
            Audio.Ui("page");
        }

        void BuildPhonePanel()
        {
            _phonePanel = MakePanel(_canvas, "Phone", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(700, 520));

            _phoneTitle = MakeText(_phonePanel.transform, "PhoneTitle", new Vector2(0.5f, 1),
                new Vector2(0, -20), new Vector2(640, 32), 22, TextAnchor.UpperCenter);
            _phoneTitle.color = UiTheme.Amber;

            _phoneBody = MakeText(_phonePanel.transform, "PhoneBody", new Vector2(0.5f, 1),
                new Vector2(0, -56), new Vector2(640, 56), 16, TextAnchor.UpperCenter);
            _phoneBody.color = UiTheme.Dim;

            // Six rows is enough for any line's regulars, built once and hidden
            // when a line has fewer.
            for (int i = 0; i < 6; i++)
            {
                var b = MakeButton(_phonePanel.transform, "-", new Vector2(0.5f, 1),
                    new Vector2(0, -118 - i * 44), new Vector2(600, 38));
                int index = i;
                b.onClick.AddListener(() => RingRow(index));
                _phoneRows.Add(b);
            }

            _phoneResult = MakeText(_phonePanel.transform, "PhoneResult", new Vector2(0.5f, 0),
                new Vector2(0, 120), new Vector2(620, 80), 17, TextAnchor.UpperCenter);

            _phoneMessage = MakeButton(_phonePanel.transform, "Leave word", new Vector2(0.5f, 0),
                new Vector2(-150, 40), new Vector2(260, 42));
            _phoneMessage.onClick.AddListener(LeaveWord);

            _phoneClose = MakeButton(_phonePanel.transform, "Hang up", new Vector2(0.5f, 0),
                new Vector2(150, 40), new Vector2(260, 42));
            _phoneClose.onClick.AddListener(TogglePhone);
        }

        void RefreshPhone()
        {
            var phone = _game.Phones.AtPlace(_phonePlaceId);
            if (phone == null) return;

            _phoneTitle.text = phone.PlaceName.ToUpperInvariant();
            _phoneBody.text = phone.LiveAt(_game.Now.Hour)
                ? "Who do you want?"
                : "It is the wrong hour for this line. You can try it anyway.";

            for (int i = 0; i < _phoneRows.Count; i++)
            {
                bool has = i < phone.Regulars.Count;
                _phoneRows[i].gameObject.SetActive(has);
                if (!has) continue;
                var who = phone.Regulars[i];
                // NOT greyed out by whether they are there. You find out by
                // ringing; that is what a telephone is.
                _phoneRows[i].GetComponentInChildren<Text>().text = who;
                _phoneRows[i].interactable = true;
            }

            _phoneResult.text = _lastCall?.Line ?? "";
            _phoneResult.color = _lastCall == null ? UiTheme.Dim
                : _lastCall.Result == CallResult.Answered ? UiTheme.Credit
                : _lastCall.Result == CallResult.SomebodyElse ? UiTheme.Amber
                : UiTheme.Dim;

            // Leaving word only means anything when a person is holding the
            // receiver and it is not the person you rang for.
            _phoneMessage.gameObject.SetActive(
                _lastCall != null && _lastCall.Result == CallResult.SomebodyElse);
            _phoneClose.GetComponentInChildren<Text>().text = _lastCall == null ? "Not now" : "Hang up";
        }

        void RingRow(int index)
        {
            var phone = _game.Phones.AtPlace(_phonePlaceId);
            if (phone == null || index >= phone.Regulars.Count) return;

            _lastCall = _game.RingLine(_phonePlaceId, phone.Regulars[index]);
            Audio.Ui(_lastCall.Result == CallResult.NoAnswer ? "page" : "door");

            // They answered: this becomes a conversation, and the line damps
            // what either of you can read in the other. The player gets told
            // that plainly, because a hidden modifier is a lie.
            if (_lastCall.Result == CallResult.Answered)
            {
                Toast($"{_lastCall.AnsweredByName} is on the line. You cannot see their face, " +
                      "and they cannot see yours.", 8f);
                _game.BeginPhoneConversation(_lastCall.AnsweredById);
                TogglePhone();
                return;
            }
            RefreshPhone();
        }

        void LeaveWord()
        {
            if (_lastCall == null || _lastCall.Result != CallResult.SomebodyElse) return;
            var wanted = _lastCall.WantedId;
            bool left = _game.LeavePhoneMessage(_lastCall,
                $"{_game.Me.Surname} rang for {wanted}. Wouldn't say what about.");
            Toast(left
                ? $"You leave word with {_lastCall.AnsweredByName}. They will pass it on, " +
                  "and they will also remember that you rang."
                : "There is nobody to leave it with.", 9f);
            _lastCall = null;
            TogglePhone();
        }
    }
}
