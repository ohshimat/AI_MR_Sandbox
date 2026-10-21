using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using System.IO;

public static class MRConversationInstaller
{
    [MenuItem("Tools/MR Sandbox/Add Conversation to Current Scene")]
    public static void Install()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
        { EditorUtility.DisplayDialog("MR Sandbox", "再生を停止してから実行してください。", "OK"); return; }
        var existing = Object.FindObjectOfType<MRConversationBridge>(true);
        if (existing != null) { Selection.activeGameObject = existing.gameObject; return; }
        var sender = Object.FindObjectOfType<AIRStateSender>(true);
        var permission = Object.FindObjectOfType<PermissionChecker>(true);
        if (sender == null || sender.aiTransform == null || sender.humanTransform == null || permission == null)
        { EditorUtility.DisplayDialog("MR Sandbox", "Sample6のMainを開き、AIRStateSenderのAI/Human参照とPermissionCheckerを確認してください。", "OK"); return; }
        var original = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if (string.IsNullOrEmpty(original.path) || original.isDirty)
        { EditorUtility.DisplayDialog("MR Sandbox", "先にCtrl+Sで現在のシーンを保存してください。保存後、もう一度このメニューを選びます。", "OK"); return; }
        string directory = Path.GetDirectoryName(original.path).Replace('\\', '/');
        string copyPath = AssetDatabase.GenerateUniqueAssetPath(directory + "/Main_Conversation.unity");
        if (!EditorSceneManager.SaveScene(original, copyPath, true)) return;
        EditorSceneManager.OpenScene(copyPath);
        sender = Object.FindObjectOfType<AIRStateSender>(true);
        permission = Object.FindObjectOfType<PermissionChecker>(true);
        Undo.IncrementCurrentGroup();
        Undo.SetCurrentGroupName("Add MR Conversation");
        int group = Undo.GetCurrentGroup();
        var obj = new GameObject("MRConversation");
        Undo.RegisterCreatedObjectUndo(obj, "Create conversation bridge");
        var bridge = Undo.AddComponent<MRConversationBridge>(obj);
        bridge.aiTransform = sender.aiTransform;
        bridge.humanTransform = sender.humanTransform;
        bridge.permissionChecker = permission;
        bridge.humanEvaluator = Object.FindObjectOfType<HumanEvaluator>(true);
        var panel = Undo.AddComponent<MRAgentPanel>(obj);
        panel.bridge = bridge;
        panel.head = Camera.main != null ? Camera.main.transform : null;
        // New controller owns routing. Disable the legacy network entry point in
        // this scene so another Python sender cannot bypass the selected mode.
        foreach (var receiver in Object.FindObjectsOfType<TcpSpeechReceiver>(true))
        {
            Undo.RecordObject(receiver, "Disable legacy receiver");
            receiver.enabled = false;
            PrefabUtility.RecordPrefabInstancePropertyModifications(receiver);
        }
        EditorSceneManager.MarkSceneDirty(obj.scene);
        Undo.CollapseUndoOperations(group);
        Selection.activeGameObject = obj;
        EditorUtility.DisplayDialog("MR Sandbox", "Main_Conversationとしてシーンを複製し、会話機能を追加しました。Ctrl+Sで保存してください。\n元のMainはそのままです。新しいシーンでは旧TcpSpeechReceiverを無効にし、新GUIを使います。\n手のパネルは再生時に作成されます。", "OK");
    }
}
