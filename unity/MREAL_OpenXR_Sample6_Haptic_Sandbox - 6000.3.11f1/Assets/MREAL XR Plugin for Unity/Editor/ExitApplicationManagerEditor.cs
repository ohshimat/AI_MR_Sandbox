using UnityEngine;
using UnityEditor;

[CustomEditor(typeof(ExitApplicationManager))]
public class ExitApplicationEditor : Editor
{   public override void OnInspectorGUI()
    {
        EditorGUILayout.LabelField("Exit Application Configuration", EditorStyles.boldLabel);
        GUILayout.Space(5);

        SerializedProperty property = serializedObject.GetIterator();
        bool enterChildren = true;
        while (property.NextVisible(enterChildren))
        {
            enterChildren = false;
            if (property.name == "m_Script")
                continue;

            EditorGUILayout.PropertyField(property, true);
        }

        serializedObject.ApplyModifiedProperties();
    }
}
