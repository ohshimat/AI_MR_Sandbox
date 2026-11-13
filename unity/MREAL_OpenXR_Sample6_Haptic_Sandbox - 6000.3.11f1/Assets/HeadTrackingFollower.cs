using UnityEngine;

public class HeadTrackingFollower : MonoBehaviour
{
    public Transform headTransform;

    void LateUpdate()
    {
        if (headTransform == null)
            return;

        transform.position = headTransform.position;

        float yaw = headTransform.eulerAngles.y;
        transform.rotation = Quaternion.Euler(0f, yaw, 0f);
    }
}