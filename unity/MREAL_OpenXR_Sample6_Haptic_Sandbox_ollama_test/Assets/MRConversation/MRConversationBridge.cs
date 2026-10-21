using System;
using System.Collections;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

// Sample6 adapter. The original scripts are not changed.
public class MRConversationBridge : MonoBehaviour
{
    public Transform humanTransform;
    public Transform aiTransform;
    public PermissionChecker permissionChecker;
    public HumanEvaluator humanEvaluator;
    public string backendUrl = "http://127.0.0.1:50002";
    public string airHost = "127.0.0.1";
    public int airPort = 50001;
    [Range(0, 0.15f)] public float speechExpansion = 0.08f;
    public float audioGain = 8f;
    public bool spatialAudio = true;

    [Serializable] public class State
    {
        public string session, mode, stage, user_text, reply_text, result, request_id;
        public string command_id, command_kind, direction;
        public int epoch, panel_revision;
        public bool busy;
    }
    [Serializable] class Event
    {
        public string session, command_id, phase, message;
        public int epoch;
    }
    [Serializable] class ModeRequest { public string mode; }
    [Serializable] class Target { public string type; public float x, y, z; }

    public State Current { get; private set; } = new State { mode = "control", stage = "GUI未接続" };
    public bool Connected { get; private set; }
    public string Notice { get; private set; } = "";
    string instanceId, lastCommand = "";
    string localSession = "";
    int localEpoch = -1;
    Event lastEvent;
    bool localBlock;
    float lastPoll, expansion;
    AudioSource voice;
    Transform visual;
    MeshRenderer originalRenderer;
    bool originalRendererEnabled;
    readonly float[] samples = new float[256];

    void Awake()
    {
        Application.runInBackground = true;
        instanceId = Guid.NewGuid().ToString("N");
        var sender = FindObjectOfType<AIRStateSender>(true);
        if (sender != null)
        {
            if (humanTransform == null) humanTransform = sender.humanTransform;
            if (aiTransform == null) aiTransform = sender.aiTransform;
        }
        if (permissionChecker == null) permissionChecker = FindObjectOfType<PermissionChecker>(true);
        if (humanEvaluator == null) humanEvaluator = FindObjectOfType<HumanEvaluator>(true);
    }

    void Start()
    {
        if (aiTransform != null)
        {
            var audioObject = new GameObject("ConversationAudio");
            audioObject.transform.SetParent(aiTransform, false);
            voice = audioObject.AddComponent<AudioSource>();
            voice.playOnAwake = false;
            voice.spatialBlend = spatialAudio ? 1f : 0f;
            voice.rolloffMode = AudioRolloffMode.Linear;
            voice.minDistance = 1f;
            voice.maxDistance = 8f;
            // Sample6 AI_1 has a root MeshRenderer. Duplicate only its visual,
            // leaving the movement transform and collider size unchanged.
            originalRenderer = aiTransform.GetComponent<MeshRenderer>();
            var filter = aiTransform.GetComponent<MeshFilter>();
            if (originalRenderer != null && filter != null && filter.sharedMesh != null)
            {
                originalRendererEnabled = originalRenderer.enabled;
                var obj = new GameObject("ConversationVisual");
                obj.layer = aiTransform.gameObject.layer;
                visual = obj.transform;
                visual.SetParent(aiTransform, false);
                obj.AddComponent<MeshFilter>().sharedMesh = filter.sharedMesh;
                var renderer = obj.AddComponent<MeshRenderer>();
                renderer.sharedMaterials = originalRenderer.sharedMaterials;
                renderer.shadowCastingMode = originalRenderer.shadowCastingMode;
                renderer.receiveShadows = originalRenderer.receiveShadows;
                renderer.enabled = originalRendererEnabled;
                originalRenderer.enabled = false;
            }
        }
        StartCoroutine(Poll());
    }

    bool Ready => humanTransform != null && aiTransform != null && permissionChecker != null && voice != null;

    IEnumerator Poll()
    {
        while (true)
        {
            string info = Ready ? "AI_1 / Human_1 ready" : "Missing AI_1 / Human_1 / PermissionChecker";
            string url = backendUrl + "/poll?id=" + instanceId + "&ready=" + (Ready ? "1" : "0") + "&info=" + UnityWebRequest.EscapeURL(info);
            using (var req = UnityWebRequest.Get(url))
            {
                req.timeout = 2;
                req.SetRequestHeader("X-MRSandbox", "1");
                yield return req.SendWebRequest();
                if (req.result == UnityWebRequest.Result.Success)
                {
                    State state = null;
                    try { state = JsonUtility.FromJson<State>(req.downloadHandler.text); }
                    catch (Exception e) { Notice = e.Message; }
                    if (state != null && !string.IsNullOrEmpty(state.session))
                    {
                        if (state.session != localSession || state.epoch != localEpoch)
                        {
                            StopVoice();
                            localBlock = false;
                            localSession = state.session;
                            localEpoch = state.epoch;
                            lastCommand = "";
                            lastEvent = null;
                        }
                        Current = state;
                        Connected = true;
                        lastPoll = Time.realtimeSinceStartup;
                        if (!localBlock && !string.IsNullOrEmpty(state.command_id))
                        {
                            if (lastCommand != state.command_id)
                            {
                                lastCommand = state.command_id; // At most once per command.
                                StartCoroutine(Execute(state));
                            }
                            else if (lastEvent != null)
                                StartCoroutine(Post("/event", JsonUtility.ToJson(lastEvent), false));
                        }
                    }
                }
                else
                {
                    Connected = false;
                    Notice = req.responseCode == 409 ? "別のUnityが接続中です" : "PC用GUIを起動してください";
                    StopVoice();
                }
            }
            yield return new WaitForSecondsRealtime(0.2f);
        }
    }

    bool Valid(State state)
    {
        return isActiveAndEnabled && !localBlock && Connected &&
               state.session == localSession && state.epoch == localEpoch &&
               Current.command_id == state.command_id && Time.realtimeSinceStartup - lastPoll < 3f;
    }

    IEnumerator Execute(State state)
    {
        if (!Ready) { Complete(state, false, "対象やPermissionCheckerが未設定です"); yield break; }
        if (state.command_kind == "move" && state.mode == "control")
            yield return Move(state);
        else if (state.command_kind == "audio" && state.mode == "chat")
            yield return Speak(state);
        else Complete(state, false, "モードと命令が一致しません");
    }

    IEnumerator Move(State state)
    {
        if (!Valid(state)) yield break;
        var action = new ActionRequest { type = "action_request", action = "move", speaker = "Human_1", reference = "Human_1", direction = state.direction };
        if (state.direction != "right" && state.direction != "left" && state.direction != "forward")
        { Complete(state, false, "未対応の方向です"); yield break; }
        if (!permissionChecker.IsAllowed(action))
        { Complete(state, false, "Permission: DENIED"); yield break; }
        // Freeze the human pose for this request. Head motion during networking
        // must not make the verifier compare against a different reference pose.
        Vector3 human = humanTransform.position;
        float yaw = humanTransform.eulerAngles.y;
        Vector3 axis = state.direction == "forward" ? Vector3.forward : state.direction == "left" ? Vector3.left : Vector3.right;
        Vector3 expected = human + Quaternion.Euler(0, yaw, 0) * axis;
        var entity = new AIREntityState { type = "air_entity_state", id = "Human_1", direction = state.direction,
            x = human.x, y = human.y, z = human.z, yaw = yaw };
        string json = JsonUtility.ToJson(entity);
        Debug.Log("AIR State sent: " + json);
        SendEvent(state, "started", "");
        string host = airHost;
        int port = airPort;
        Task<string> task = Task.Run(() => ExchangeAir(host, port, json));
        while (!task.IsCompleted) yield return null;
        if (!Valid(state)) yield break;
        if (task.IsFaulted)
        { Complete(state, false, "AIRManager: " + task.Exception.GetBaseException().Message); yield break; }
        Target target = null;
        try { target = JsonUtility.FromJson<Target>(task.Result); }
        catch (Exception e) { Notice = e.Message; }
        if (target == null || target.type != "air_target_position")
        { Complete(state, false, "AIRManagerの応答形式が不正です"); yield break; }
        Vector3 position = new Vector3(target.x, target.y, target.z);
        float targetError = Vector3.Distance(position, expected);
        if (float.IsNaN(targetError) || float.IsInfinity(targetError) || targetError > 0.05f)
        { Complete(state, false, "AIRManagerの目標位置が要求と一致しません。移動しません。"); yield break; }
        // Final guard after the network response, including permission changes.
        if (!Valid(state) || !permissionChecker.IsAllowed(action)) yield break;
        aiTransform.position = position;
        float error = Vector3.Distance(aiTransform.position, expected);
        bool passed = error <= 0.05f;
        Debug.Log("AI_1 moved by AIR target: " + position);
        string result = "Verification: " + (passed ? "PASS" : "FAIL") + " Direction = " + state.direction + " Error = " + error.ToString("F4");
        if (humanEvaluator != null) humanEvaluator.StartEvaluation(action, error, passed);
        Complete(state, passed, result);
    }

    static string ExchangeAir(string host, int port, string json)
    {
        using (var client = new TcpClient())
        {
            var connect = client.BeginConnect(host, port, null, null);
            using (connect.AsyncWaitHandle)
            {
                if (!connect.AsyncWaitHandle.WaitOne(3000)) throw new TimeoutException("接続タイムアウト");
                client.EndConnect(connect);
            }
            client.ReceiveTimeout = 3000;
            client.SendTimeout = 3000;
            using (NetworkStream stream = client.GetStream())
            {
                byte[] send = Encoding.UTF8.GetBytes(json);
                stream.Write(send, 0, send.Length);
                var buffer = new byte[4096];
                int total = 0;
                // AIRManager returns one flat JSON object then closes. Read until
                // its closing brace so fragmented TCP packets are handled.
                while (total < buffer.Length)
                {
                    int count = stream.Read(buffer, total, buffer.Length - total);
                    if (count == 0) break;
                    total += count;
                    string response = Encoding.UTF8.GetString(buffer, 0, total).TrimEnd('\0', '\n', '\r', ' ');
                    if (response.EndsWith("}")) return response;
                }
                throw new IOException("完全な応答を受信できませんでした");
            }
        }
    }

    IEnumerator Speak(State state)
    {
        using (var req = UnityWebRequestMultimedia.GetAudioClip(backendUrl + "/audio?id=" + state.command_id, AudioType.WAV))
        {
            req.timeout = 10;
            req.SetRequestHeader("X-MRSandbox", "1");
            yield return req.SendWebRequest();
            if (!Valid(state)) yield break;
            if (req.result != UnityWebRequest.Result.Success)
            { Complete(state, false, "音声を取得できません: " + req.error); yield break; }
            var clip = DownloadHandlerAudioClip.GetContent(req);
            if (clip == null) { Complete(state, false, "音声を読み込めません"); yield break; }
            StopVoice();
            voice.clip = clip;
            voice.Play();
            SendEvent(state, "started", "");
            yield return null;
            while (voice != null && voice.isPlaying && Valid(state)) yield return null;
            if (Valid(state)) Complete(state, true, "AIの返答音声を再生しました");
            if (voice != null && voice.clip == clip) StopVoice();
        }
    }

    void Complete(State state, bool ok, string message)
    {
        if (!Valid(state)) return;
        Notice = message;
        if (ok) Debug.Log(message); else Debug.LogWarning(message);
        SendEvent(state, ok ? "complete" : "error", message);
    }

    void SendEvent(State state, string phase, string message)
    {
        var data = new Event { session = state.session, epoch = state.epoch, command_id = state.command_id, phase = phase, message = message };
        if (phase != "started") lastEvent = data; // Retry only the result, never the operation.
        StartCoroutine(Post("/event", JsonUtility.ToJson(data), false));
    }

    public void SetControlMode() { RequestMode("control"); }
    public void SetChatMode() { RequestMode("chat"); }
    void RequestMode(string mode)
    {
        if (mode == Current.mode) return;
        localBlock = true;
        StopVoice();
        StartCoroutine(Post("/mode", JsonUtility.ToJson(new ModeRequest { mode = mode }), true));
    }
    public void Record() { if (!Current.busy && !localBlock) StartCoroutine(Post("/record", "{}", true)); }
    public void StopInput()
    {
        localBlock = true;
        StopVoice();
        StartCoroutine(Post("/stop", "{}", true));
    }

    IEnumerator Post(string path, string json, bool showError)
    {
        using (var req = new UnityWebRequest(backendUrl + path, "POST"))
        {
            req.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            req.SetRequestHeader("X-MRSandbox", "1");
            req.timeout = 2;
            yield return req.SendWebRequest();
            if (showError && req.result != UnityWebRequest.Result.Success)
                Notice = "GUIへの要求が失敗しました: " + req.downloadHandler.text;
        }
    }

    void Update()
    {
        float level = 0;
        if (voice != null && voice.isPlaying && Current.mode == "chat")
        {
            voice.GetOutputData(samples, 0);
            float sum = 0;
            foreach (float sample in samples) sum += sample * sample;
            level = Mathf.Clamp01(Mathf.Sqrt(sum / samples.Length) * audioGain);
        }
        expansion = Mathf.Lerp(expansion, level * speechExpansion, 1 - Mathf.Exp(-12 * Time.unscaledDeltaTime));
        if (visual != null) visual.localScale = Vector3.one * (1 + expansion);
    }

    void StopVoice()
    {
        if (voice != null)
        {
            voice.Stop();
            if (voice.clip != null) Destroy(voice.clip);
            voice.clip = null;
        }
        expansion = 0;
        if (visual != null) visual.localScale = Vector3.one;
    }

    void OnDisable()
    {
        Connected = false;
        StopAllCoroutines();
        StopVoice();
    }
    void OnDestroy()
    {
        if (originalRenderer != null) originalRenderer.enabled = originalRendererEnabled;
        if (visual != null) Destroy(visual.gameObject);
        if (voice != null) Destroy(voice.gameObject);
    }
}
