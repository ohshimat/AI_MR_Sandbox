using UnityEngine;

public class PermissionChecker : MonoBehaviour
{
    public bool allowMove = true;

    public bool IsAllowed(ActionRequest request)
    {
        if (request.action == "move")
        {
            return allowMove;
        }

        return false;
    }
}