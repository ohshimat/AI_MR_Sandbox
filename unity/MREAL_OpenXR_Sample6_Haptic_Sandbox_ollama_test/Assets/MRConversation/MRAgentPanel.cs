using System.Collections.Generic;
using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.XR.Hands;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

// Direct index-finger touch uses XR Hands joint data, independently of the
// existing project's EventSystem. PC controls always remain in the Python GUI.
public class MRAgentPanel : MonoBehaviour
{
    public MRConversationBridge bridge;
    public Transform head;
    [Tooltip("XR hand poses are converted through this tracking-space transform. Set the same parent as the tracked hand visuals.")]
    public Transform trackingSpace;
    public Vector3 panelOffset = new Vector3(0.18f, -0.25f, 0.55f);
    [Range(0.005f, 0.04f)] public float touchDepth = 0.018f;
    public bool showFingerMarkers = true;
    Canvas panel;
    Text status;
    Text subtitle;
    Button control, chat, record, stop;
    readonly List<Button> buttons = new List<Button>();
    readonly List<XRHandSubsystem> subsystems = new List<XRHandSubsystem>();
    readonly int[] contact = { -1, -1 };
    readonly float[] lastTouch = { -10, -10 };
    readonly GameObject[] fingertips = new GameObject[2];
    float nextSearch;
    int panelRevision = -1;
    bool placed;
    Font font;

    void Start()
    {
        if (bridge == null) bridge = GetComponent<MRConversationBridge>();
        if (head == null && Camera.main != null) head = Camera.main.transform;
        var origin = FindObjectOfType<XROrigin>();
        if (trackingSpace == null && origin != null)
            trackingSpace = origin.CameraFloorOffsetObject != null ? origin.CameraFloorOffsetObject.transform : origin.transform;
        font = Font.CreateDynamicFontFromOSFont(new[] { "Yu Gothic UI", "Meiryo", "Arial" }, 30);
        var obj = new GameObject("AgentModePanel", typeof(RectTransform), typeof(Canvas));
        obj.transform.SetParent(transform, false);
        panel = obj.GetComponent<Canvas>();
        panel.renderMode = RenderMode.WorldSpace;
        panel.sortingOrder = 20;
        if (Camera.main != null) panel.worldCamera = Camera.main;
        obj.GetComponent<RectTransform>().sizeDelta = new Vector2(640, 340);
        obj.transform.localScale = Vector3.one * 0.0007f;
        var bg = obj.AddComponent<Image>();
        bg.color = new Color(0.035f, 0.09f, 0.13f, 0.95f);
        bg.raycastTarget = false;
        Label("Title", "AI_1  /  モード", new Vector2(0, 137), new Vector2(600, 40), 30);
        control = AddButton("操作", new Vector2(-155, 72), bridge.SetControlMode);
        chat = AddButton("会話", new Vector2(155, 72), bridge.SetChatMode);
        record = AddButton("話す（5秒）", new Vector2(-155, -7), bridge.Record);
        stop = AddButton("停止", new Vector2(155, -7), bridge.StopInput);
        status = Label("State", "PC用GUIを起動してください", new Vector2(0, -78), new Vector2(605, 46), 23);
        subtitle = Label("Subtitle", "", new Vector2(0, -130), new Vector2(605, 55), 19);
        for (int i = 0; i < 2; i++)
        {
            fingertips[i] = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            fingertips[i].name = "AgentPanelFinger" + i;
            Destroy(fingertips[i].GetComponent<Collider>());
            fingertips[i].transform.SetParent(transform, false);
            fingertips[i].transform.localScale = Vector3.one * 0.012f;
            fingertips[i].SetActive(false);
        }
        Recenter();
    }

    Text Label(string name, string value, Vector2 at, Vector2 size, int fontSize, Transform parent = null)
    {
        var obj = new GameObject(name, typeof(RectTransform), typeof(Text));
        obj.transform.SetParent(parent != null ? parent : panel.transform, false);
        var rt = obj.GetComponent<RectTransform>();
        rt.sizeDelta = size;
        rt.anchoredPosition = at;
        var text = obj.GetComponent<Text>();
        text.font = font;
        text.fontSize = fontSize;
        text.color = Color.white;
        text.alignment = TextAnchor.MiddleCenter;
        text.raycastTarget = false;
        text.supportRichText = false;
        text.text = value;
        return text;
    }

    Button AddButton(string text, Vector2 at, UnityEngine.Events.UnityAction action)
    {
        var obj = new GameObject(text, typeof(RectTransform), typeof(Image), typeof(Button));
        obj.transform.SetParent(panel.transform, false);
        var rt = obj.GetComponent<RectTransform>();
        rt.sizeDelta = new Vector2(290, 65);
        rt.anchoredPosition = at;
        var button = obj.GetComponent<Button>();
        button.targetGraphic = obj.GetComponent<Image>();
        button.transition = Selectable.Transition.None;
        button.onClick.AddListener(action);
        Label("Label", text, Vector2.zero, rt.sizeDelta, 28, obj.transform);
        buttons.Add(button);
        return button;
    }

    public void Recenter()
    {
        if (head == null && Camera.main != null) head = Camera.main.transform;
        if (panel == null || head == null) return;
        var yaw = Quaternion.Euler(0, head.eulerAngles.y, 0);
        panel.transform.position = head.position + yaw * panelOffset;
        panel.transform.rotation = yaw;
        placed = true;
        contact[0] = contact[1] = -1;
    }

    void Update()
    {
        if (panel == null || bridge == null) return;
        if (!placed) Recenter();
        if (bridge.Current.panel_revision != panelRevision)
        {
            panelRevision = bridge.Current.panel_revision;
            Recenter();
        }
        var neutral = new Color(0.17f, 0.24f, 0.30f);
        var selected = new Color(0.06f, 0.48f, 0.43f);
        control.image.color = bridge.Current.mode == "control" ? selected : neutral;
        chat.image.color = bridge.Current.mode == "chat" ? selected : neutral;
        record.interactable = bridge.Connected && !bridge.Current.busy;
        record.image.color = record.interactable ? selected : neutral * 0.6f;
        stop.image.color = neutral;
        status.text = bridge.Connected ? bridge.Current.stage : "PC用GUIとの接続待ち";
        subtitle.text = bridge.Current.mode == "chat" ? "AI合成音声 / " + Short(bridge.Current.reply_text) : Short(bridge.Current.result);
        if (Time.unscaledTime >= nextSearch)
        {
            nextSearch = Time.unscaledTime + 1;
            subsystems.Clear();
            SubsystemManager.GetSubsystems(subsystems);
        }
        bool tracked = false;
        foreach (var subsystem in subsystems)
        {
            if (!subsystem.running) continue;
            Touch(subsystem.leftHand, 0);
            Touch(subsystem.rightHand, 1);
            tracked = true;
            break;
        }
        if (!tracked || trackingSpace == null)
        {
            contact[0] = contact[1] = -1;
            foreach (var finger in fingertips) if (finger != null) finger.SetActive(false);
        }
        MouseClick();
    }

    void MouseClick()
    {
        // Screen-space ray for editor mouse testing, without replacing or adding
        // a second EventSystem in the user's existing XR scene.
        Vector2 point;
#if ENABLE_INPUT_SYSTEM
        if (Mouse.current == null || !Mouse.current.leftButton.wasPressedThisFrame) return;
        point = Mouse.current.position.ReadValue();
#else
        if (!Input.GetMouseButtonDown(0)) return;
        point = Input.mousePosition;
#endif
        Camera cam = panel.worldCamera != null ? panel.worldCamera : Camera.main;
        if (cam == null) return;
        Ray ray = cam.ScreenPointToRay(point);
        var plane = new Plane(panel.transform.forward, panel.transform.position);
        if (!plane.Raycast(ray, out float distance) || distance < 0) return;
        Vector3 world = ray.GetPoint(distance);
        foreach (var button in buttons)
        {
            var rt = (RectTransform)button.transform;
            var local = rt.InverseTransformPoint(world);
            if (button.interactable && rt.rect.Contains(new Vector2(local.x, local.y)))
            { button.onClick.Invoke(); break; }
        }
    }

    string Short(string value) { return string.IsNullOrEmpty(value) ? "" : value.Length > 65 ? value.Substring(0, 65) + "…" : value; }

    void Touch(XRHand hand, int index)
    {
        bool valid = trackingSpace != null && hand.isTracked && hand.GetJoint(XRHandJointID.IndexTip).TryGetPose(out _);
        fingertips[index].SetActive(valid && showFingerMarkers);
        if (!valid) { contact[index] = -1; return; }
        hand.GetJoint(XRHandJointID.IndexTip).TryGetPose(out Pose pose);
        Vector3 point = trackingSpace.TransformPoint(pose.position);
        fingertips[index].transform.position = point;
        int hit = -1;
        for (int i = 0; i < buttons.Count; i++)
        {
            var rt = (RectTransform)buttons[i].transform;
            var local = rt.InverseTransformPoint(point);
            float depth = Mathf.Abs(Vector3.Dot(point - rt.position, rt.forward));
            if (rt.rect.Contains(new Vector2(local.x, local.y)) && depth <= touchDepth)
            { hit = i; break; }
        }
        // Require the finger to leave before another activation. Crossing from
        // one button straight into another does not accidentally change mode.
        if (hit >= 0 && contact[index] < 0 && Time.unscaledTime - lastTouch[index] > 0.65f && buttons[hit].interactable)
        {
            lastTouch[index] = Time.unscaledTime;
            buttons[hit].onClick.Invoke();
        }
        contact[index] = hit;
    }

    void OnDestroy()
    {
        if (font != null) Destroy(font);
    }
}
