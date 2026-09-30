using UnityEngine;

public class EquirectStereo : MonoBehaviour
{
    public Camera captureCamera;

    public Transform leftEye;
    public Transform rightEye;

    public RenderTexture cubeRTLeft;
    public RenderTexture cubeRTRight;

    public RenderTexture equirectRTLeft;
    public RenderTexture equirectRTRight;
    public RenderTexture equirectRTSBS;

    //public float stereoSeparation = 0.064f;

    void LateUpdate()
    {
        //captureCamera.stereoSeparation = stereoSeparation;

        // 左眼・右眼の360° Cubemapを生成
        const int AllCubemapFaces = 0x3f; // 00111111
        // 左目の「ワールド位置」から撮影
        captureCamera.transform.position = leftEye.position;
        captureCamera.transform.rotation = Quaternion.identity;
        captureCamera.RenderToCubemap(
            cubeRTLeft,
            AllCubemapFaces,
            Camera.MonoOrStereoscopicEye.Mono
        );

        // 右目の「ワールド位置」から撮影
        captureCamera.transform.position = rightEye.position;
        captureCamera.transform.rotation = Quaternion.identity;
        captureCamera.RenderToCubemap(
            cubeRTRight,
            AllCubemapFaces,
            Camera.MonoOrStereoscopicEye.Mono
        );

        // 各眼を独立した2:1 Equirectangular画像へ変換
        cubeRTLeft.ConvertToEquirect(
            equirectRTLeft,
            Camera.MonoOrStereoscopicEye.Mono
        );

        cubeRTRight.ConvertToEquirect(
            equirectRTRight,
            Camera.MonoOrStereoscopicEye.Mono
        );
        Graphics.CopyTexture(
            equirectRTLeft, 0, 0,
            0, 0, 4096, 2048,
            equirectRTSBS, 0, 0,
            0, 0
        );

        Graphics.CopyTexture(
            equirectRTRight, 0, 0,
            0, 0, 4096, 2048,
            equirectRTSBS, 0, 0,
            4096, 0
        );
    }
}