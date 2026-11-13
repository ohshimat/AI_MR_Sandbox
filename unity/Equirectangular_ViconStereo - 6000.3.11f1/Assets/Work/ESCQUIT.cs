using UnityEngine;
using UnityEngine.InputSystem;

public class EscapeQuit : MonoBehaviour
{
    void Update()
    {
        var keyboard = Keyboard.current;
        if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
        {
            Application.Quit();
        }
    }
}
