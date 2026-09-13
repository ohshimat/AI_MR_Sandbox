using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Collections.Concurrent;

using TMPro;

[System.Serializable]
public class ActionRequest
{
    public string type;
    public string speaker;
    public string action;
    public string reference;
    public string direction;
}

[System.Serializable]
public class SpeechMessage
{
    public string type;
    public string speaker;
    public string text;
}

public class TcpSpeechReceiver : MonoBehaviour
{
    private TcpListener listener;
    private Thread listenerThread;

    private ConcurrentQueue<string> messages =
        new ConcurrentQueue<string>();

    public TMP_Text speechText;

    void Start()
    {
        Application.runInBackground = true;

        listenerThread = new Thread(Listen);
        listenerThread.IsBackground = true;
        listenerThread.Start();

        Debug.Log("TCP server started.");
    }

    void Listen()
    {
        listener =
            new TcpListener(IPAddress.Loopback, 50000);

        listener.Start();

        while (true)
        {
            using (TcpClient client =
                   listener.AcceptTcpClient())

            using (NetworkStream stream =
                   client.GetStream())
            {
                byte[] buffer = new byte[4096];

                int length =
                    stream.Read(
                        buffer,
                        0,
                        buffer.Length
                    );

                string message =
                    Encoding.UTF8.GetString(
                        buffer,
                        0,
                        length
                    );

                messages.Enqueue(message);
            }
        }
    }

    void Update()
    {
        while (messages.TryDequeue(out string message))
        {
            ActionRequest request =
                JsonUtility.FromJson<ActionRequest>(message);

            Debug.Log(
                $"Action: {request.action}, " +
                $"Reference: {request.reference}, " +
                $"Direction: {request.direction}"
            );

            if (speechText != null)
            {
                speechText.text =
                    "Action: " + request.action + "\n" +
                    "Reference: " + request.reference + "\n" +
                    "Direction: " + request.direction;
            }
        }
    }

    void OnDestroy()
    {
        listener?.Stop();
        listenerThread?.Interrupt();
    }
}