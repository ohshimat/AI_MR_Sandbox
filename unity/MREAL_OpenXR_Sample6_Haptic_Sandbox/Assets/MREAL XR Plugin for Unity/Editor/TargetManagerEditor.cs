using UnityEngine;
using UnityEditor;

[CustomEditor(typeof(TargetManager))]
public class TargetManagerEditor : Editor
{
    SerializedProperty entriesProperty;

    void OnEnable()
    {
        entriesProperty = serializedObject.FindProperty("entries");
    }

    public override void OnInspectorGUI()
    {
        bool wasGUIEnabled = GUI.enabled;
        GUI.enabled = !EditorApplication.isPlaying;

        serializedObject.Update();

        EditorGUILayout.LabelField("Target Configuration", EditorStyles.boldLabel);
        GUILayout.Space(5);

        EditorGUI.indentLevel++;
            for (int i = 0; i < entriesProperty.arraySize; i++)
            {
                SerializedProperty entryProperty = entriesProperty.GetArrayElementAtIndex(i);
                EditorGUILayout.PropertyField(entryProperty, new GUIContent($"ID {i + 1}"), true);

                if (i < entriesProperty.arraySize - 1)
                {
                    GUILayout.Space(5);
                }
            }
            EditorGUI.indentLevel--;

        serializedObject.ApplyModifiedProperties();

        GUI.enabled = wasGUIEnabled;
    }
}
