using UnityEngine.XR.OpenXR.Features;
using UnityEngine;
using System.Runtime.InteropServices;
using System;
using UnityEngine.XR.OpenXR;
using System.Collections.Generic;
using AOT;

#if UNITY_EDITOR
[UnityEditor.XR.OpenXR.Features.OpenXRFeature(
    UiName = "MREAL_target_tracking_Extension",
    Desc = "MREAL XR Plugin for Unity provides support for MREAL functions.",
    OpenxrExtensionStrings = "XR_VARJO_marker_tracking",
    Company = "Canon Inc.",
    Version = "1.0",
    BuildTargetGroups = new[] { UnityEditor.BuildTargetGroup.Standalone },
    Priority = -200,
    FeatureId = "com.openxr.varjo.marker.tracking"
    )]
#endif

public class VarjoMarkerTrackingFeature : OpenXRFeature
{
    static VarjoMarkerTrackingFeature singleton;

    public VarjoMarkerTrackingFeature()
    {
        singleton = this;
    }

    ~VarjoMarkerTrackingFeature()
    {
        singleton = null;
    }

    /*XrResult xrGetInstanceProcAddr(
        XrInstance                                  instance,
        const char*                                 name,
        PFN_xrVoidFunction*                         function);*/
    internal delegate int Type_xrGetInstanceProcAddr(ulong instance, [MarshalAs(UnmanagedType.LPStr)] string name, out IntPtr function);

    /*XrResult xrSetMarkerTrackingVARJO(
        XrSession                                   session,
        XrBool32                                    enabled);*/
    internal delegate XrResult Type_xrSetMarkerTrackingVARJO(ulong session, XrBool32 enabled);

    /*XrResult xrSetMarkerTrackingTimeoutVARJO(
        XrSession                                   session,
        uint64_t                                    markerId,
        XrDuration                                  timeout);*/
    internal delegate XrResult Type_xrSetMarkerTrackingTimeoutVARJO(ulong session, ulong markerId, long timeout);

    /*XrResult xrSetMarkerTrackingPredictionVARJO(
        XrSession                                   session,
        uint64_t                                    markerId,
        XrBool32                                    enable);*/
    internal delegate XrResult Type_xrSetMarkerTrackingPredictionVARJO(ulong session, ulong markerId, XrBool32 enable);

    /*XrResult xrGetMarkerSizeVARJO(
        XrSession                                   session,
        uint64_t                                    markerId,
        XrExtent2Df*                                size);*/
    internal delegate XrResult Type_xrGetMarkerSizeVARJO(ulong session, ulong markerId, ref XrExtent2Df size);

    /*XrResult xrCreateMarkerSpaceVARJO(
        XrSession                                   session,
        const XrMarkerSpaceCreateInfoVARJO*         createInfo,
        XrSpace*                                    space);*/
    internal delegate XrResult Type_xrCreateMarkerSpaceVARJO(ulong session, in XrMarkerSpaceCreateInfoVARJO createInfo, out ulong space);

    /*XrResult xrDestroySpace(
        XrSpace                                     space);*/
    internal delegate XrResult Type_xrDestroySpace(ulong space);

    /*XrResult xrLocateSpace(
        XrSpace space,
        XrSpace baseSpace,
        XrTime time,
        XrSpaceLocation* location);*/
    internal delegate XrResult Type_xrLocateSpace(ulong space, ulong baseSpace, long time, ref XrSpaceLocation location);

    /*XrResult xrWaitFrame(
        XrSession                                   session,
        const XrFrameWaitInfo*                      frameWaitInfo,
        XrFrameState*                               frameState);*/
    internal delegate int Type_xrWaitFrame(ulong session, in XrFrameWaitInfo waitInfo, ref XrFrameState state);

    /*XrResult xrPollEvent(
        XrInstance                                  instance,
        XrEventDataBuffer*                          eventData);*/
    internal delegate int Type_xrPollEvent(ulong instance, ref XrEventDataBuffer eventData);


    /*typedef struct XrExtent2Df {
        float    width;
        float    height;
    } XrExtent2Df;*/
    [StructLayout(LayoutKind.Sequential)]
    public struct XrExtent2Df
    {
        public float width;
        public float height;
    };

    /*typedef struct XrPosef {
        XrQuaternionf    orientation;
        XrVector3f       position;
    } XrPosef;*/
    [StructLayout(LayoutKind.Sequential)]
    public struct XrPosef
    {
        public XrQuaternionf orientation;
        public XrVector3f position;
    }

    /*typedef struct XrQuaternionf {
        float    x;
        float    y;
        float    z;
        float    w;
    } XrQuaternionf;*/ 
    [StructLayout(LayoutKind.Sequential)]
    public struct XrQuaternionf
    {
        public float x;
        public float y;
        public float z;
        public float w;
    }

    /*typedef struct XrVector3f {
        float    x;
        float    y;
        float    z;
    } XrVector3f;*/
    [StructLayout(LayoutKind.Sequential)]
    public struct XrVector3f
    {
        public float x;
        public float y;
        public float z;
    }

    /*typedef struct XrMarkerSpaceCreateInfoVARJO {
        XrStructureType    type;
        const void*        next;
        uint64_t           markerId;
        XrPosef            poseInMarkerSpace;
    } XrMarkerSpaceCreateInfoVARJO;*/
    [StructLayout(LayoutKind.Sequential)]
    public struct XrMarkerSpaceCreateInfoVARJO
    {
        public XrStructureType type;
        public IntPtr next;
        public ulong markerId;
        public XrPosef poseInMarkerSpace;
    }

    /*typedef struct XrFrameWaitInfo {
        XrStructureType    type;
        const void*        next;
    } XrFrameWaitInfo;*/
    [StructLayout(LayoutKind.Sequential)]
    internal struct XrFrameWaitInfo
    {
        int stype;
        IntPtr next;
    };

    /*typedef struct XrFrameState {
        XrStructureType    type;
        void*              next;
        XrTime             predictedDisplayTime;
        XrDuration         predictedDisplayPeriod;
        XrBool32           shouldRender;
    } XrFrameState;*/
    [StructLayout(LayoutKind.Sequential)]
    internal struct XrFrameState
    {
        int stype;
        IntPtr next;
        public long predictedDisplayTime;
        public long predictedDisplayPeriod;
        public int shouldRender;
    }

    /*typedef struct XrEventDataBuffer {
        XrStructureType    type;
        const void*        next;
        uint8_t            varying[4000];
    } XrEventDataBuffer;*/
    [StructLayout(LayoutKind.Sequential)]
    public struct XrEventDataBuffer
    {
        public XrStructureType type;
        public IntPtr next;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4000)]
        public byte[] varying;

        public static XrEventDataBuffer Create()
        {
            return new XrEventDataBuffer
            {
                type = XrStructureType.XR_TYPE_EVENT_DATA_BUFFER,
                next = IntPtr.Zero,
                varying = new byte[4000]
            };
        }
    }

    /*typedef struct XrEventDataMarkerTrackingUpdateVARJO{
        XrStructureType type;
        const void* next;
        uint64_t markerId;
        XrBool32 isActive;
        XrBool32 isPredicted;
        XrTime time;
    } XrEventDataMarkerTrackingUpdateVARJO;*/
    [StructLayout(LayoutKind.Sequential)]
    public struct XrEventDataMarkerTrackingUpdateVARJO
    {
        public XrStructureType type;
        public IntPtr next;
        public ulong markerId;
        public XrBool32 isActive;
        public XrBool32 isPredicted;
        public long time;
    }

    /*typedef struct XrSpaceLocation {
        XrStructureType         type;
        void*                   next;
        XrSpaceLocationFlags    locationFlags;
        XrPosef                 pose;
    } XrSpaceLocation;*/
    [StructLayout(LayoutKind.Sequential)]
    public struct XrSpaceLocation
    {
        public XrStructureType type;
        public IntPtr next;
        public XrSpaceLocationFlags locationFlags;
        public XrPosef pose;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TempStruct
    {
        public ulong markerId;
        public XrBool32 isActive;
        public XrBool32 isPredicted;
        public long time;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TransformData
    {
        public Vector3 position;
        public Quaternion rotation;
    }

    public enum XrStructureType : int
    {
        XR_TYPE_UNKNOWN = 0,
        XR_TYPE_EVENT_DATA_BUFFER = 16,
        XR_TYPE_SPACE_LOCATION = 42,
        XR_TYPE_EVENT_DATA_MARKER_TRACKING_UPDATE_VARJO = 1000124001,
        XR_TYPE_MARKER_SPACE_CREATE_INFO_VARJO = 1000124002,
    }

    [Flags]
    public enum XrSpaceLocationFlags : ulong
    {
        XR_SPACE_LOCATION_ORIENTATION_VALID_BIT = 0x00000001,
        XR_SPACE_LOCATION_POSITION_VALID_BIT = 0x00000002,
        XR_SPACE_LOCATION_ORIENTATION_TRACKED_BIT = 0x00000004,
        XR_SPACE_LOCATION_POSITION_TRACKED_BIT = 0x00000008
    }

    public enum XrResult : int
    {
        XR_SUCCESS = 0,
        XR_TIMEOUT_EXPIRED = 1,
        XR_SESSION_LOSS_PENDING = 3,
        XR_EVENT_UNAVAILABLE = 4,
        XR_SPACE_BOUNDS_UNAVAILABLE = 7,
        XR_SESSION_NOT_FOCUSED = 8,
        XR_FRAME_DISCARDED = 9,
        XR_ERROR_VALIDATION_FAILURE = -1,
        XR_ERROR_RUNTIME_FAILURE = -2,
        XR_ERROR_OUT_OF_MEMORY = -3,
        XR_ERROR_API_VERSION_UNSUPPORTED = -4,
        XR_ERROR_INITIALIZATION_FAILED = -6,
        XR_ERROR_FUNCTION_UNSUPPORTED = -7,
        XR_ERROR_FEATURE_UNSUPPORTED = -8,
        XR_ERROR_EXTENSION_NOT_PRESENT = -9,
        XR_ERROR_LIMIT_REACHED = -10,
        XR_ERROR_SIZE_INSUFFICIENT = -11,
        XR_ERROR_HANDLE_INVALID = -12,
        XR_ERROR_INSTANCE_LOST = -13,
        XR_ERROR_SESSION_RUNNING = -14,
        XR_ERROR_SESSION_NOT_RUNNING = -16,
        XR_ERROR_SESSION_LOST = -17,
        XR_ERROR_SYSTEM_INVALID = -18,
        XR_ERROR_PATH_INVALID = -19,
        XR_ERROR_PATH_COUNT_EXCEEDED = -20,
        XR_ERROR_PATH_FORMAT_INVALID = -21,
        XR_ERROR_PATH_UNSUPPORTED = -22,
        XR_ERROR_LAYER_INVALID = -23,
        XR_ERROR_LAYER_LIMIT_EXCEEDED = -24,
        XR_ERROR_SWAPCHAIN_RECT_INVALID = -25,
        XR_ERROR_SWAPCHAIN_FORMAT_UNSUPPORTED = -26,
        XR_ERROR_ACTION_TYPE_MISMATCH = -27,
        XR_ERROR_SESSION_NOT_READY = -28,
        XR_ERROR_SESSION_NOT_STOPPING = -29,
        XR_ERROR_TIME_INVALID = -30,
        XR_ERROR_REFERENCE_SPACE_UNSUPPORTED = -31,
        XR_ERROR_FILE_ACCESS_ERROR = -32,
        XR_ERROR_FILE_CONTENTS_INVALID = -33,
        XR_ERROR_FORM_FACTOR_UNSUPPORTED = -34,
        XR_ERROR_FORM_FACTOR_UNAVAILABLE = -35,
        XR_ERROR_API_LAYER_NOT_PRESENT = -36,
        XR_ERROR_CALL_ORDER_INVALID = -37,
        XR_ERROR_GRAPHICS_DEVICE_INVALID = -38,
        XR_ERROR_POSE_INVALID = -39,
        XR_ERROR_INDEX_OUT_OF_RANGE = -40,
        XR_ERROR_VIEW_CONFIGURATION_TYPE_UNSUPPORTED = -41,
        XR_ERROR_ENVIRONMENT_BLEND_MODE_UNSUPPORTED = -42,
        XR_ERROR_NAME_DUPLICATED = -44,
        XR_ERROR_NAME_INVALID = -45,
        XR_ERROR_ACTIONSET_NOT_ATTACHED = -46,
        XR_ERROR_ACTIONSETS_ALREADY_ATTACHED = -47,
        XR_ERROR_LOCALIZED_NAME_DUPLICATED = -48,
        XR_ERROR_LOCALIZED_NAME_INVALID = -49,
        XR_ERROR_GRAPHICS_REQUIREMENTS_CALL_MISSING = -50,
        XR_ERROR_RUNTIME_UNAVAILABLE = -51,
        XR_ERROR_ANDROID_THREAD_SETTINGS_ID_INVALID_KHR = -1000003000,
        XR_ERROR_ANDROID_THREAD_SETTINGS_FAILURE_KHR = -1000003001,
        XR_ERROR_CREATE_SPATIAL_ANCHOR_FAILED_MSFT = -1000039001,
        XR_ERROR_SECONDARY_VIEW_CONFIGURATION_TYPE_NOT_ENABLED_MSFT = -1000053000,
        XR_ERROR_CONTROLLER_MODEL_KEY_INVALID_MSFT = -1000055000,
        XR_ERROR_REPROJECTION_MODE_UNSUPPORTED_MSFT = -1000066000,
        XR_ERROR_COMPUTE_NEW_SCENE_NOT_COMPLETED_MSFT = -1000097000,
        XR_ERROR_SCENE_COMPONENT_ID_INVALID_MSFT = -1000097001,
        XR_ERROR_SCENE_COMPONENT_TYPE_MISMATCH_MSFT = -1000097002,
        XR_ERROR_SCENE_MESH_BUFFER_ID_INVALID_MSFT = -1000097003,
        XR_ERROR_SCENE_COMPUTE_FEATURE_INCOMPATIBLE_MSFT = -1000097004,
        XR_ERROR_SCENE_COMPUTE_CONSISTENCY_MISMATCH_MSFT = -1000097005,
        XR_ERROR_DISPLAY_REFRESH_RATE_UNSUPPORTED_FB = -1000101000,
        XR_ERROR_COLOR_SPACE_UNSUPPORTED_FB = -1000108000,
        XR_ERROR_SPACE_COMPONENT_NOT_SUPPORTED_FB = -1000113000,
        XR_ERROR_SPACE_COMPONENT_NOT_ENABLED_FB = -1000113001,
        XR_ERROR_SPACE_COMPONENT_STATUS_PENDING_FB = -1000113002,
        XR_ERROR_SPACE_COMPONENT_STATUS_ALREADY_SET_FB = -1000113003,
        XR_ERROR_UNEXPECTED_STATE_PASSTHROUGH_FB = -1000118000,
        XR_ERROR_FEATURE_ALREADY_CREATED_PASSTHROUGH_FB = -1000118001,
        XR_ERROR_FEATURE_REQUIRED_PASSTHROUGH_FB = -1000118002,
        XR_ERROR_NOT_PERMITTED_PASSTHROUGH_FB = -1000118003,
        XR_ERROR_INSUFFICIENT_RESOURCES_PASSTHROUGH_FB = -1000118004,
        XR_ERROR_UNKNOWN_PASSTHROUGH_FB = -1000118050,
        XR_ERROR_RENDER_MODEL_KEY_INVALID_FB = -1000119000,
        XR_RENDER_MODEL_UNAVAILABLE_FB = 1000119020,
        XR_ERROR_MARKER_NOT_TRACKED_VARJO = -1000124000,
        XR_ERROR_MARKER_ID_INVALID_VARJO = -1000124001,
        XR_ERROR_SPATIAL_ANCHOR_NAME_NOT_FOUND_MSFT = -1000142001,
        XR_ERROR_SPATIAL_ANCHOR_NAME_INVALID_MSFT = -1000142002,
        XR_ERROR_SPACE_MAPPING_INSUFFICIENT_FB = -1000169000,
        XR_ERROR_SPACE_LOCALIZATION_FAILED_FB = -1000169001,
        XR_ERROR_SPACE_NETWORK_TIMEOUT_FB = -1000169002,
        XR_ERROR_SPACE_NETWORK_REQUEST_FAILED_FB = -1000169003,
        XR_ERROR_SPACE_CLOUD_STORAGE_DISABLED_FB = -1000169004,
        XR_ERROR_PASSTHROUGH_COLOR_LUT_BUFFER_SIZE_MISMATCH_META = -1000266000,
        XR_ERROR_HINT_ALREADY_SET_QCOM = -1000306000,
        XR_ERROR_SPACE_NOT_LOCATABLE_EXT = -1000429000,
        XR_ERROR_PLANE_DETECTION_PERMISSION_DENIED_EXT = -1000429001,
        XR_RESULT_MAX_ENUM = 0x7FFFFFFF
    }

    public enum XrBool32 : uint
    {
        False = 0,
        True = 1,
    }

    Type_xrGetInstanceProcAddr oldProc;
    Type_xrWaitFrame oldWaitFrame;
    Type_xrPollEvent oldPollEvent;

    private ulong currentInstanceId = 0;
    private ulong currentSession = 0;
    private long predictedDisplayTime = 0;

    List<Delegate> callbacks = new();
    protected IntPtr GetCallback<T>(T functionAddr) where T : System.Delegate
    {
        callbacks.Add(functionAddr);
        IntPtr fp = Marshal.GetFunctionPointerForDelegate(functionAddr);
        return fp;
    }

    protected override IntPtr HookGetInstanceProcAddr(IntPtr func)
    {
        oldProc = (Type_xrGetInstanceProcAddr)Marshal.GetDelegateForFunctionPointer(xrGetInstanceProcAddr, typeof(Type_xrGetInstanceProcAddr));

        return GetCallback<Type_xrGetInstanceProcAddr>(new Type_xrGetInstanceProcAddr(HookStaticGetInstanceProcAddr));
    }

    public T GetInstanceProc<T>(string procName) where T : System.Delegate
    {
        if (xrGetInstanceProcAddr == null)
        {
            return null;
        }
        IntPtr fp = IntPtr.Zero;
        if (oldProc == null)
        {
            return null;
        }
        int returnValue = oldProc(currentInstanceId, procName, out fp);
        if (returnValue == 0)
        {
            return (T)Marshal.GetDelegateForFunctionPointer(fp, typeof(T));
        }
        else
        {
            return null;
        }
    }
    [MonoPInvokeCallback(typeof(Type_xrGetInstanceProcAddr))]
    static int HookStaticGetInstanceProcAddr(ulong instance, string name, out IntPtr function)
    {
        VarjoMarkerTrackingFeature vmtf = singleton;
        if (vmtf != null)
        {
            return vmtf.HookGetInstanceProcAddr(instance, name, out function);
        }
        else
        {
            function = IntPtr.Zero;
            return -1;
        }
    }

    int HookGetInstanceProcAddr(ulong instance, string name, out IntPtr function)
    {
        if (name == "xrWaitFrame")
        {
            IntPtr fp;
            int returnValue = oldProc(instance, name, out fp);
            oldWaitFrame = (Type_xrWaitFrame)Marshal.GetDelegateForFunctionPointer(fp, typeof(Type_xrWaitFrame));
            function = GetCallback<Type_xrWaitFrame>(new Type_xrWaitFrame(HookStaticWaitFrame));
            return returnValue;
        }

        if (name == "xrPollEvent")
        {
            IntPtr fp;
            int returnValue = oldProc(instance, name, out fp);
            oldPollEvent = (Type_xrPollEvent)Marshal.GetDelegateForFunctionPointer(fp, typeof(Type_xrPollEvent));
            function = GetCallback<Type_xrPollEvent>(new Type_xrPollEvent(HookStaticPollEvent));
            return returnValue;
        }

        return oldProc(instance, name, out function);
    }

    [MonoPInvokeCallback(typeof(Type_xrWaitFrame))]
    static int HookStaticWaitFrame(ulong session, in XrFrameWaitInfo waitInfo, ref XrFrameState state)
    {
        VarjoMarkerTrackingFeature vmtf = singleton;
        if (vmtf != null)
        {
            return vmtf.HookWaitFrame(session, waitInfo, ref state);
        }
        else
        {
            return -1;
        }
    }

    int HookWaitFrame(ulong session, in XrFrameWaitInfo waitInfo, ref XrFrameState state)
    {
        int returnValue = oldWaitFrame(session, waitInfo, ref state);
        predictedDisplayTime = state.predictedDisplayTime;
        return returnValue;
    }


    [MonoPInvokeCallback(typeof(Type_xrPollEvent))]
    static int HookStaticPollEvent(ulong instance, ref XrEventDataBuffer eventData)
    {
        VarjoMarkerTrackingFeature vmtf = singleton;
        if (vmtf != null)
        {
            return vmtf.HookPollEvent(instance, ref eventData);
        }
        else
        {
            return -1;
        }
    }

    private Dictionary<ulong, ulong> targetSpaces = new();

    int HookPollEvent(ulong instance, ref XrEventDataBuffer eventData)
    {
        int returnValue = oldPollEvent(instance, ref eventData);
        if (returnValue == 0)
        {
            if (eventData.type == XrStructureType.XR_TYPE_EVENT_DATA_MARKER_TRACKING_UPDATE_VARJO)
            {
                XrEventDataMarkerTrackingUpdateVARJO marker_update = ConvertToXrEventDataMarkerTrackingUpdateVARJO(eventData);
                ulong id = marker_update.markerId;

                if (!targetSpaces.ContainsKey(id))
                {
                    XrMarkerSpaceCreateInfoVARJO spaceInfo = new XrMarkerSpaceCreateInfoVARJO
                    {
                        type = XrStructureType.XR_TYPE_MARKER_SPACE_CREATE_INFO_VARJO,
                        markerId = id,
                        poseInMarkerSpace = new XrPosef
                        {
                            orientation = new XrQuaternionf { w = 1.0f },
                            position = new XrVector3f()
                        }
                    };
                    ulong targetSpace;

                    XrResult result = GetInstanceProc<Type_xrSetMarkerTrackingTimeoutVARJO>("xrSetMarkerTrackingTimeoutVARJO")(currentSession, id, 1000000000);
                    if (result != XrResult.XR_SUCCESS)
                    {
                        Debug.LogError($"xrSetMarkerTrackingTimeoutVARJO : {result}");
                        return returnValue;
                    }

                    result = GetInstanceProc<Type_xrSetMarkerTrackingPredictionVARJO>("xrSetMarkerTrackingPredictionVARJO")(currentSession, id, (XrBool32)(id % 2));
                    if (result != XrResult.XR_SUCCESS)
                    {
                        Debug.LogError($"xrSetMarkerTrackingPredictionVARJO : {result}");
                        return returnValue;
                    }

                    result = GetInstanceProc<Type_xrCreateMarkerSpaceVARJO>("xrCreateMarkerSpaceVARJO")(currentSession, in spaceInfo, out targetSpace);
                    if (result != XrResult.XR_SUCCESS)
                    {
                        Debug.LogError($"xrSetMarkerTrackingPredictionVARJO : {result}");
                        return returnValue;
                    }
                    targetSpaces[id] = targetSpace;
                }

                if (marker_update.isActive == XrBool32.True)
                {
                    // if (XR_SUCCESS !=
                    //    xrLocateSpace(markerSpaces.at(id), m_appSpace, frameState.predictedDisplayTime, &location)) {
                    //    break;
                    //}
                    // if (marker_update.isPredicted) {
                    //    // Process marker as dynamic
                    //} else {
                    //    // Process marker as stationary
                    //}
                }
                else
                {
                    if (targetSpaces.ContainsKey(id))
                    {
                        ulong space = targetSpaces[id];

                        XrResult result = GetInstanceProc<Type_xrDestroySpace>("xrDestroySpace")(space);
                        if (result == XrResult.XR_SUCCESS)
                        {
                            targetSpaces.Remove(id);
                        }
                        else
                        {
                            Debug.LogError($"Failed to destroy XrSpace with ID {id}: {result}");
                            return returnValue;
                        }
                    }
                }

                UpdateTargetPoses();
            }
        }
        return returnValue;
    }

    private static XrEventDataMarkerTrackingUpdateVARJO ConvertToXrEventDataMarkerTrackingUpdateVARJO(XrEventDataBuffer eventDataBuffer)
    {
        XrEventDataMarkerTrackingUpdateVARJO markerUpdateEventData = new()
        {
            type = XrStructureType.XR_TYPE_EVENT_DATA_MARKER_TRACKING_UPDATE_VARJO,
            next = IntPtr.Zero,
            markerId = 0,
            isActive = XrBool32.False,
            isPredicted = XrBool32.False,
            time = 0
        };

        TempStruct tempStruct = new()
        {
            markerId = 0,
            isActive = XrBool32.False,
            isPredicted = XrBool32.False,
            time = 0
        };

        GCHandle handle = GCHandle.Alloc(eventDataBuffer.varying, GCHandleType.Pinned);
        try
        {
            IntPtr ptr = handle.AddrOfPinnedObject();
            tempStruct = Marshal.PtrToStructure<TempStruct>(ptr);

            markerUpdateEventData.type = eventDataBuffer.type;
            markerUpdateEventData.next = eventDataBuffer.next;
            markerUpdateEventData.markerId = tempStruct.markerId;
            markerUpdateEventData.isActive = tempStruct.isActive;
            markerUpdateEventData.isPredicted = tempStruct.isPredicted;
            markerUpdateEventData.time = tempStruct.time;

            return markerUpdateEventData;
        }
        finally
        {
            handle.Free();
        }
    }

    override protected void OnSessionBegin(ulong xrSession)
    {
        currentSession = xrSession;

        XrResult result = GetInstanceProc<Type_xrSetMarkerTrackingVARJO>("xrSetMarkerTrackingVARJO")(currentSession, XrBool32.True);
        if (result != XrResult.XR_SUCCESS)
        {
            Debug.LogError($"xrSetMarkerTrackingVARJO : {result}");
            return;
        }
    }

    override protected void OnSessionEnd(ulong xrSession)
    {
        XrResult result = GetInstanceProc<Type_xrSetMarkerTrackingVARJO>("xrSetMarkerTrackingVARJO")(currentSession, XrBool32.False);
        if (result != XrResult.XR_SUCCESS)
        {
            Debug.LogError($"xrSetMarkerTrackingVARJO : Error, {result}");
            return;
        }

        currentSession = 0;
    }

    override protected void OnSessionDestroy(ulong xrSession)
    {
        if (currentSession == 0)
        {
            return;
        }

        XrResult result = GetInstanceProc<Type_xrSetMarkerTrackingVARJO>("xrSetMarkerTrackingVARJO")(currentSession, XrBool32.False);
        if (result != XrResult.XR_SUCCESS)
        {
            Debug.LogError($"xrSetMarkerTrackingVARJO : Error, {result}" );
            return;
        }

        currentSession = 0;
    }

    override protected bool OnInstanceCreate(ulong xrInstance)
    {
        if (!OpenXRRuntime.IsExtensionEnabled("XR_VARJO_marker_tracking"))
        {
            Debug.LogWarning("XR_VARJO_marker_tracking is not enabled, disabling XR_VARJO_marker_tracking.");
            return false;
        }

        currentInstanceId = xrInstance;
        return true;
    }

    override protected void OnInstanceDestroy(ulong xrInstance)
    {
        currentInstanceId = 0;
    }

    public Dictionary<ulong, XrPosef> targetPoses = new();
    public Dictionary<ulong, TransformData> targetTransforms = new();

    private void UpdateTargetPoses()
    {
        targetTransforms.Clear();

        if (currentInstanceId == 0 || currentSession == 0)
        {
            return;
        }

        foreach (var target in targetSpaces)
        {
            XrSpaceLocation spaceLocation = new XrSpaceLocation();
            spaceLocation.type = XrStructureType.XR_TYPE_SPACE_LOCATION;

            XrResult result = GetInstanceProc<Type_xrLocateSpace>("xrLocateSpace")(target.Value, OpenXRFeature.GetCurrentAppSpace(), predictedDisplayTime, ref spaceLocation);
            if (result == XrResult.XR_SUCCESS)
            {
                if ((spaceLocation.locationFlags & XrSpaceLocationFlags.XR_SPACE_LOCATION_POSITION_VALID_BIT) != 0 &&
                    (spaceLocation.locationFlags & XrSpaceLocationFlags.XR_SPACE_LOCATION_ORIENTATION_VALID_BIT) != 0)
                {
                    targetPoses[target.Key] = spaceLocation.pose;

                    TransformData tempTransformData = new()
                    {
                        position = PositionToUnity(spaceLocation.pose.position),
                        rotation = OrientationToUnity(spaceLocation.pose.orientation)
                    };

                    targetTransforms[target.Key] = tempTransformData;
                }
            }
            else
            {
                Debug.LogError($"xrLocateSpace : {result}");
            }
        }
    }
    private Vector3 PositionToUnity(XrVector3f pos)
    {
        return new Vector3(pos.x, pos.y, -pos.z);
    }

    private Quaternion OrientationToUnity(XrQuaternionf ori)
    {
        return new Quaternion(ori.x, ori.y, -ori.z, -ori.w);
    }
}
