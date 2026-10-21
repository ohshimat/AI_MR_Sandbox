using UnityEngine;
using System.Net.Sockets;
using System.Text;

[System.Serializable]
public class AIREntityState
{
    public string type;
    public string id;
    public string direction;

    public float x;
    public float y;
    public float z;

    public float yaw;
}
public class AIRTargetPosition
{


    public string type;
    public string reference;
    public string direction;

    public float x;
    public float y;
    public float z;
}

public class AIRStateSender : MonoBehaviour
{
    public Transform humanTransform;
    public Transform aiTransform;

    private string host = "127.0.0.1";
    private int port = 50001;

    /*
    void Start()
    {
        SendHumanState();
    }
    */
    public void SendHumanState(string direction)
    {
        AIREntityState state = new AIREntityState();

        state.type = "air_entity_state";
        state.id = "Human_1";
        state.direction = direction;

        state.x = humanTransform.position.x;
        state.y = humanTransform.position.y;
        state.z = humanTransform.position.z;

        state.yaw = humanTransform.eulerAngles.y;

        string json = JsonUtility.ToJson(state);

        try
        {
            using (TcpClient client = new TcpClient(host, port))
            {
                NetworkStream stream = client.GetStream();

                byte[] data = Encoding.UTF8.GetBytes(json);

                stream.Write(
                    data,
                    0,
                    data.Length
                );

                byte[] receiveBuffer = new byte[1024];

                int received =
                    stream.Read(
                        receiveBuffer,
                        0,
                        receiveBuffer.Length
                    );

                if (received > 0)
                {
                    string responseJson =
                        Encoding.UTF8.GetString(
                            receiveBuffer,
                            0,
                            received
                        );

                    Debug.Log(
                        "AIR Response: " + responseJson
                    );

                    AIRTargetPosition target =
                        JsonUtility.FromJson<AIRTargetPosition>(
                            responseJson
                        );

                    if (target.type == "air_target_position")
                    {
                        aiTransform.position =
                            new Vector3(
                                target.x,
                                target.y,
                                target.z
                            );

                        Debug.Log(
                            "AI_1 moved by AIR target: "
                            + aiTransform.position
                        );
                    }
                }
            }

            Debug.Log(
                "AIR State sent: " + json
            );
        }
        catch (System.Exception e)
        {
            Debug.LogError(
                "AIR Send Error: " + e.Message
            );
        }
    }
}