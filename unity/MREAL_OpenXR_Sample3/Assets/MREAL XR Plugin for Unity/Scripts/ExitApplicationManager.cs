using UnityEngine;
using UnityEngine.InputSystem;

public class ExitApplicationManager : MonoBehaviour
{
    [SerializeField] private InputAction _action;

    private void OnEnable()
    {
        _action?.Enable();
    }

    private void OnDisable()
    {
        _action?.Disable();
    }

    private void Update()
    {
        if (_action == null) return;

        var value = _action.ReadValue<float>();

        if(value == 1)
        {
            Exit();
        }
    }

    private void Exit()
    {
        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }

}
