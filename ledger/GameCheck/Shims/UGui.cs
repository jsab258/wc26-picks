// THE FOUR uGUI TYPES, AND NOTHING ELSE.
//
// `UnityEngine.Modules` on NuGet is Unity's own reference assembly set and it
// covers every type this project uses EXCEPT `UnityEngine.UI` — uGUI ships as
// a separate Unity package (com.unity.ugui) and is not in the modules feed.
// Compiling the Game layer against the real assemblies produced exactly 114
// errors and every one of them was one of these four names.
//
// SO THIS FILE IS DELIBERATELY TINY, and it must stay that way. Everything
// else is checked against Unity's real signatures; only these four are our
// approximation, and each one we add is a place a real compile error could
// hide. If this file starts growing, the harness is drifting from being a
// compiler into being a second opinion, which is worth much less.
//
// The members are the ones the Game layer actually touches, taken from the
// code rather than from memory of the uGUI API. `Text.font` is a `Font` and
// `alignment` a `TextAnchor` because that is what uGUI uses — getting those
// wrong would make correct code fail here, which is the one failure mode a
// compile check must not have.
using System;
using UnityEngine;
using UnityEngine.Events;

// THE EVENT SYSTEM, same reasoning — it lives in the uGUI package too.
namespace UnityEngine.EventSystems
{
    public class UIBehaviour : MonoBehaviour { }

    public class BaseInputModule : UIBehaviour { }

    public class StandaloneInputModule : BaseInputModule { }

    public class EventSystem : UIBehaviour
    {
        public static EventSystem current;
        public GameObject currentSelectedGameObject;
        public void SetSelectedGameObject(GameObject o) { }
        public bool IsPointerOverGameObject() => false;
    }
}

namespace UnityEngine.UI
{
    public class Graphic : MonoBehaviour
    {
        public Color color;
        public bool raycastTarget;
        public RectTransform rectTransform;
    }

    public class Image : Graphic
    {
        public Sprite sprite;
        public Material material;
        public bool preserveAspect;
        public float fillAmount;
    }

    public class CanvasScaler : MonoBehaviour
    {
        public enum ScaleMode { ConstantPixelSize, ScaleWithScreenSize, ConstantPhysicalSize }
        public enum ScreenMatchMode { MatchWidthOrHeight, Expand, Shrink }
        public ScaleMode uiScaleMode;
        public ScreenMatchMode screenMatchMode;
        public Vector2 referenceResolution;
        public float matchWidthOrHeight;
        public float scaleFactor;
        public float referencePixelsPerUnit;
    }

    public class GraphicRaycaster : MonoBehaviour
    {
        public bool ignoreReversedGraphics;
    }

    public class Slider : Selectable
    {
        public enum Direction { LeftToRight, RightToLeft, BottomToTop, TopToBottom }
        [Serializable] public class SliderEvent : UnityEvent<float> { }
        public Direction direction;
        public float value;
        public float minValue;
        public float maxValue;
        public bool wholeNumbers;
        public RectTransform fillRect;
        public RectTransform handleRect;
        public SliderEvent onValueChanged = new SliderEvent();
    }

    public class Text : Graphic
    {
        public string text;
        public Font font;
        public int fontSize;
        public FontStyle fontStyle;
        public TextAnchor alignment;
        public float lineSpacing;
        public bool supportRichText;
        public bool resizeTextForBestFit;
        public HorizontalWrapMode horizontalOverflow;
        public VerticalWrapMode verticalOverflow;
        public float preferredWidth;
        public float preferredHeight;
    }

    public class Selectable : MonoBehaviour
    {
        public bool interactable;
        public Graphic targetGraphic;
        public void Select() { }
    }

    public class Button : Selectable
    {
        [Serializable] public class ButtonClickedEvent : UnityEvent { }
        public ButtonClickedEvent onClick = new ButtonClickedEvent();
    }

    public class InputField : Selectable
    {
        [Serializable] public class OnChangeEvent : UnityEvent<string> { }
        [Serializable] public class SubmitEvent : UnityEvent<string> { }

        public string text;
        public int characterLimit;
        public bool isFocused;
        public int caretPosition;
        public Text textComponent;
        public Graphic placeholder;
        public Color caretColor;
        public OnChangeEvent onValueChanged = new OnChangeEvent();
        public SubmitEvent onEndEdit = new SubmitEvent();
        public SubmitEvent onSubmit = new SubmitEvent();
        public void ActivateInputField() { }
        public void DeactivateInputField() { }
    }
}
