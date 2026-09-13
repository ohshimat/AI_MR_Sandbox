using UnityEngine;

public class ActionVerifier : MonoBehaviour
{
    public Transform humanTransform;
    public Transform aiTransform;

    public float targetDistance = 1.0f;
    public float tolerance = 0.05f;

    public void VerifyRightPosition()
    {
        Vector3 expectedPosition =
            humanTransform.position +
            humanTransform.right * targetDistance;

        float error =
            Vector3.Distance(
                aiTransform.position,
                expectedPosition
            );

        if (error <= tolerance)
        {
            Debug.Log(
                "Verification: PASS  Error = " + error
            );
        }
        else
        {
            Debug.Log(
                "Verification: FAIL  Error = " + error
            );
        }
    }
}