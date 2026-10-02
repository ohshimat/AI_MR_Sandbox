using UnityEngine;

public class HumanEvaluator : MonoBehaviour
{
    public ExperienceLogger experienceLogger;

    private bool waitingForEvaluation = false;

    private ActionRequest pendingRequest;
    private float pendingError;
    private bool pendingVerificationPassed;

    public void StartEvaluation(
        ActionRequest request,
        float error,
        bool verificationPassed)
    {
        pendingRequest = request;
        pendingError = error;
        pendingVerificationPassed =
            verificationPassed;

        waitingForEvaluation = true;

        Debug.Log(
            "Human Evaluation: " +
            "Press Y = Correct / N = Incorrect"
        );
    }

    void Update()
    {
        if (!waitingForEvaluation)
        {
            return;
        }

        if (Input.GetKeyDown(KeyCode.Y))
        {
            Debug.Log(
                "Human Evaluation: CORRECT"
            );

            if (experienceLogger != null)
            {
                experienceLogger.SaveExperience(
                    pendingRequest,
                    pendingError,
                    pendingVerificationPassed,
                    "correct"
                );
            }

            waitingForEvaluation = false;
        }

        if (Input.GetKeyDown(KeyCode.N))
        {
            Debug.Log(
                "Human Evaluation: INCORRECT"
            );

            if (experienceLogger != null)
            {
                experienceLogger.SaveExperience(
                    pendingRequest,
                    pendingError,
                    pendingVerificationPassed,
                    "incorrect"
                );
            }

            waitingForEvaluation = false;
        }
    }
}