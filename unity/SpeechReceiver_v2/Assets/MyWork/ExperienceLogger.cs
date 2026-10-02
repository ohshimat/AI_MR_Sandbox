using UnityEngine;
using System;
using System.IO;

[System.Serializable]
public class ExperienceRecord
{
    public string timestamp;
    public string speaker;
    public string action;
    public string reference;
    public string direction;

    public float error;
    public bool verificationPassed;

    // CHECKPOINT-7で追加
    public string humanEvaluation;
}

public class ExperienceLogger : MonoBehaviour
{
    private string logFilePath;

    void Start()
    {
        logFilePath =
            Path.Combine(
                Application.persistentDataPath,
                "experience.jsonl"
            );

        Debug.Log(
            "Experience log: " + logFilePath
        );
    }

    public void SaveExperience(
        ActionRequest request,
        float error,
        bool verificationPassed,
        string humanEvaluation)
    {
        ExperienceRecord record =
            new ExperienceRecord();

        record.timestamp =
            DateTime.Now.ToString("o");

        record.speaker = request.speaker;
        record.action = request.action;
        record.reference = request.reference;
        record.direction = request.direction;

        record.error = error;
        record.verificationPassed =
            verificationPassed;

        record.humanEvaluation =
            humanEvaluation;

        string json =
            JsonUtility.ToJson(record);

        // ★ 実際にファイルへ追記する部分
        File.AppendAllText(
            logFilePath,
            json + Environment.NewLine
        );

        Debug.Log(
            "Experience saved: " + json
        );
    }
}