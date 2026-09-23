using UnityEngine;
using UnityEngine.InputSystem;

public class ResetPosition : MonoBehaviour
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

        if (value == 1)
        {
            Reset();
        }
    }

    private Vector3 _initialPosition;
    private Quaternion _initialRotation;

    void Start()
    {
        _initialPosition = gameObject.transform.position;
        _initialRotation = gameObject.transform.rotation;
    }

    public void Reset()
    {
        gameObject.transform.position = _initialPosition;
        gameObject.transform.rotation = _initialRotation;
    }
}