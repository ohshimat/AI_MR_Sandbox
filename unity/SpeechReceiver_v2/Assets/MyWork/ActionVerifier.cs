using UnityEngine;

public class ActionVerifier : MonoBehaviour
{
    public Transform humanTransform;
    public Transform aiTransform;

    public float targetDistance = 1.0f;
    public float tolerance = 0.05f;

    public ExperienceLogger experienceLogger;

    public HumanEvaluator humanEvaluator;

    public void VerifyRightPosition(ActionRequest request)
    {
        Vector3 expectedPosition =
            humanTransform.position +
            humanTransform.right * targetDistance;

        float error =
            Vector3.Distance(
                aiTransform.position,
                expectedPosition
            );

        bool passed = error <= tolerance;

        if (passed)
        {
            Debug.Log("Verification: PASS  Error = " + error);
        }
        else
        {
            Debug.Log("Verification: FAIL  Error = " + error);
        }

        if (humanEvaluator != null)
        {
            humanEvaluator.StartEvaluation(
                request,
                error,
                passed
            );
        }
        else
        {
            Debug.LogWarning(
                "HumanEvaluator is not assigned."
            );
        }

    }
}