using UnityEngine;
using UnityEngine.XR.OpenXR;
using TMPro;

[System.Serializable]
public class PrefabEntry
{
    public bool IsEnabled = true;
    public GameObject objectPrefab;
    public TextMeshPro textPrefab;
    
}

public class TargetManager : MonoBehaviour
{
    public PrefabEntry[] entries = new PrefabEntry[15];

    private VarjoMarkerTrackingFeature vmtf;
    private bool isVMTFEnabled = false;

    private GameObject[] objectInstance = new GameObject[15];
    private TextMeshPro[] textInstance = new TextMeshPro[15];

    private void Start()
    {
        vmtf = OpenXRSettings.Instance.GetFeature<VarjoMarkerTrackingFeature>();
        if (vmtf != null && vmtf.enabled)
        {
            isVMTFEnabled = true;
        }
        else
        {
            Debug.LogError("You need to enable the OpenXR VarjoMarkerTracking extension");
        }


        for (int i = 0; i < 15; i++)
        {
            if (entries[i].IsEnabled)
            {
                if(entries[i].objectPrefab != null)
                {
                    objectInstance[i] = Instantiate(entries[i].objectPrefab, Vector3.zero, Quaternion.identity);
                    objectInstance[i].SetActive(false);
                }

                if (entries[i].textPrefab != null)
                {
                    textInstance[i] = Instantiate(entries[i].textPrefab, Vector3.zero, Quaternion.identity);
                    textInstance[i].gameObject.SetActive(false);
                }
            }

        }
    }

    private void OnEnable()
    {
        Application.onBeforeRender += OnBeforeRender;
    }

    private void OnDisable()
    {
        Application.onBeforeRender -= OnBeforeRender;
    }

    private void OnBeforeRender()
    {
        if (isVMTFEnabled)
        {
            for (int i = 0; i < 15; i++)
            {
                if (objectInstance[i] != null)
                    objectInstance[i].SetActive(false);

                if (textInstance[i] != null)
                    textInstance[i].gameObject.SetActive(false);
            }

            foreach (var target in vmtf.targetTransforms)
            {
                ulong id = target.Key;
                Vector3 markerPosition = target.Value.position;
                Quaternion markerRotation = target.Value.rotation;

                UpdateObjectPosition(id, markerPosition, markerRotation);
                UpdateTextPosition(id, markerPosition, markerRotation);
            }
        }
    }

    public void UpdateObjectPosition(ulong id, Vector3 markerPosition, Quaternion markerRotation)
    {
        if (objectInstance[id - 1] != null)
        {
            objectInstance[id - 1].transform.position = markerPosition;
            objectInstance[id - 1].transform.rotation = markerRotation;
            objectInstance[id - 1].SetActive(true);
        }
    }

    public void UpdateTextPosition(ulong id, Vector3 markerPosition, Quaternion markerRotation)
    {
        if (textInstance[id - 1] != null)
        {
            textInstance[id - 1].transform.position = markerPosition;
            textInstance[id - 1].transform.rotation = markerRotation;

            if(textInstance[id - 1].text == "")
                textInstance[id - 1].text = "Target " + id;

            Transform cameraTransform = Camera.main.transform;
            textInstance[id - 1].transform.LookAt(textInstance[id - 1].transform.position + cameraTransform.rotation * Vector3.forward, cameraTransform.rotation * Vector3.up);

            textInstance[id - 1].gameObject.SetActive(true);
        }
    }
}
