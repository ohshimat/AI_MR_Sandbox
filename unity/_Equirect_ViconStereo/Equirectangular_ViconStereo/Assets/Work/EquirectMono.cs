using UnityEngine;

public class EquirectMono : MonoBehaviour
{
    public Camera captureCamera;
    public RenderTexture cubeRT;
    public RenderTexture equirectRT;

    void LateUpdate()
    {
        captureCamera.RenderToCubemap(cubeRT, 63);

        cubeRT.ConvertToEquirect(
            equirectRT,
            Camera.MonoOrStereoscopicEye.Mono
        );
    }
}