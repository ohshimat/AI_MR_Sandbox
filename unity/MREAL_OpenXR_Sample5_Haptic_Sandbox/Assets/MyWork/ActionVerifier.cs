using UnityEngine;

public class ActionVerifier : MonoBehaviour
{
    public Transform humanTransform;
    public Transform aiTransform;

    public float targetDistance = 1.0f;
    public float tolerance = 0.05f;

    public ExperienceLogger experienceLogger;

    public HumanEvaluator humanEvaluator;

    // Verify the position of the AI entity based on the human's position and direction
    public void VerifyPosition(ActionRequest request)
    {
        Vector3 direction = Vector3.zero;

        if (request.direction == "right")
        {
            direction = humanTransform.right;
        }
        else if (request.direction == "left")
        {
            direction = -humanTransform.right;
        }
        else if (request.direction == "forward")
        {
            direction = humanTransform.forward;
        }
        else
        {
            Debug.LogWarning(
                "Verification: Unknown direction = "
                + request.direction
            );

            return;
        }

        Vector3 expectedPosition =
            humanTransform.position +
            direction * targetDistance;

        float error =
            Vector3.Distance(
                aiTransform.position,
                expectedPosition
            );

        bool passed =
            error <= tolerance;

        if (passed)
        {
            Debug.Log(
                "Verification: PASS"
                + " Direction = "
                + request.direction
                + " Error = "
                + error
            );
        }
        else
        {
            Debug.Log(
                "Verification: FAIL"
                + " Direction = "
                + request.direction
                + " Error = "
                + error
            );
        }

        if (humanEvaluator != null)
        {
            humanEvaluator.StartEvaluation(
                request,
                error,
                passed
            );
        }
    }
    /*
    // Verify the position of the AI entity specifically to the right of the human
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
    */
}