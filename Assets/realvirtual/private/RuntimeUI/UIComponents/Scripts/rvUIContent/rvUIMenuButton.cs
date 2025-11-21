using System;
using NaughtyAttributes;
using realvirtual;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.UI;
#if UNITY_EDITOR
using UnityEditor;
#endif

[ExecuteInEditMode]
public class rvUIMenuButton : rvUIContent
{
    
    public bool isOn;
    public bool interactable = false;
    public bool IsToggle = true;
    
    
    public Color colorOff;
    public Color colorOn;

    public rvUIIcon icon;
    
    public string text;
    public bool hideText = false;
    
    public UnityEvent OnClick = new UnityEvent();
    public UnityEvent OnToggleOn = new UnityEvent();
    public UnityEvent OnToggleOff = new UnityEvent();
    

    private Image targetGraphic;

    void OnValidate()
    {
        // Defer layout refresh to avoid Unity error about SendMessage during OnValidate
        #if UNITY_EDITOR
        EditorApplication.delayCall += () =>
        {
            if (this != null)
                RefreshLayout();
        };
        #else
        RefreshLayout();
        #endif
    }
    

    public Color GetCurrentColor()
    {
        return isOn ? colorOn : colorOff;
    }

    void Start()
    {
        Init();
    }
    
    void Init()
    {
        RefreshLayout();
        
    }
    

    public override void RefreshLayout()
    {
        Toggle toggle = GetComponentInChildren<Toggle>(true);
        toggle.SetIsOnWithoutNotify(isOn);
        toggle.onValueChanged.RemoveListener(OnValueChanged);
        toggle.onValueChanged.AddListener(OnValueChanged);
        
        targetGraphic = GetComponent<Image>();
        
        RefreshVisuals();
        RefreshText();
    }
    
    void RefreshText()
    {
        rvUIText textComponent = GetComponentInChildren<rvUIText>();

        if (hideText)
        {
            textComponent?.SetText("");
        }else{
            textComponent?.SetText(text);
        }
        
        rvUISizeLink sizeLink = GetComponentInChildren<rvUISizeLink>();
        sizeLink?.Refresh();
    }
    
    void RefreshVisuals()
    {
        targetGraphic = GetComponent<Image>();
        targetGraphic.color = GetCurrentColor();
        
    }

    public void ToggleOn()
    {
        if (!isOn)
        {
            OnValueChanged(!isOn);
        }
    }

    public void ToggleOff()
    {
        if (isOn)
        {
            OnValueChanged(!isOn);
        }
    }

    public void Toggle()
    {
        isOn = !isOn;
        OnValueChanged(isOn);
    }

    void OnValueChanged(bool value)
    {
        Toggle toggle = GetComponentInChildren<Toggle>(true);
        if(!interactable)
        {
            // Revert the toggle state
            toggle.SetIsOnWithoutNotify(!value);
            return;
        }

        toggle.SetIsOnWithoutNotify(value);

        isOn = value;
        RefreshVisuals();
        OnClick.Invoke();
        
        if(!IsToggle && isOn)
        {
            // If it's a button, revert back to off state
            isOn = false;
            toggle.SetIsOnWithoutNotify(false);
            RefreshVisuals();
            return;
        }

        if (value)
        {
            OnToggleOn.Invoke();
        }
        else
        {
            OnToggleOff.Invoke();
        }
    }


    public void SetSpriteIcon(Sprite icon)
    {
        this.icon.ApplySprite(icon);
    }
    
    public void SetMaterialIcon(string icon)
    {
        this.icon.ApplyMaterialIcon(icon);
    }

    public void SetText(string text)
    {
        this.text = text;
        RefreshText();
    }
}
