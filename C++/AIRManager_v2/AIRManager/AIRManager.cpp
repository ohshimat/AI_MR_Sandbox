#include <iostream>
#include <string>
#include <cmath>
#include <sstream>

#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

//AIR Manager TCP Port = 50001

struct Entity
{
    std::string id;

    float x;
    float y;
    float z;

    float yaw;
};

//-------- JSON string extraction function --------
std::string GetJsonString(
    const std::string& json,
    const std::string& key)
{
    std::string pattern = "\"" + key + "\":\"";

    size_t start = json.find(pattern);

    if (start == std::string::npos)
        return "";

    start += pattern.length();

    size_t end = json.find("\"", start);

    return json.substr(start, end - start);
}
//-------- JSON float extraction function --------
float GetJsonFloat(
    const std::string& json,
    const std::string& key)
{
    std::string pattern = "\"" + key + "\":";

    size_t start = json.find(pattern);

    if (start == std::string::npos)
        return 0.0f;

    start += pattern.length();

    size_t end = json.find_first_of(",}", start);

    return std::stof(
        json.substr(start, end - start)
    );
}
//-------------------------------------------------
int main()
{
    Entity human;

    human.id = "Human_1";

    float moveDistance = 1.0f;

    human.x = 0.0f;
    human.y = 1.0f;
    human.z = 0.0f;

    human.yaw = 0.0f;

    constexpr float PI = 3.14159265358979323846f;

    std::cout << "AIR Manager started." << std::endl;

	//-------- AIR Manager TCP Server --------

    WSADATA wsaData;

    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
    {
        std::cout << "WSAStartup failed." << std::endl;
        return 1;
    }

    SOCKET serverSocket =
        socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    sockaddr_in serverAddr{};

    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    serverAddr.sin_port = htons(50001);

    bind(
        serverSocket,
        reinterpret_cast<sockaddr*>(&serverAddr),
        sizeof(serverAddr)
    );

    listen(serverSocket, 1);

    std::cout << "AIR Manager waiting on port 50001..."
        << std::endl;

    while (true)
    {
        SOCKET clientSocket = accept(serverSocket, nullptr, nullptr);
        if (clientSocket == INVALID_SOCKET)
        {
            std::cout << "accept failed." << std::endl;
            break;
        }
        std::cout << "Client connected." << std::endl;

        char buffer[1024] = {};

        int received = recv(clientSocket, buffer, sizeof(buffer) - 1, 0);

        if (received > 0)
        {
            buffer[received] = '\0';

            std::string json(buffer);

            std::cout << "Received: "
                << json
                << std::endl;

            Entity human;

            human.id = GetJsonString(json, "id");
            human.x = GetJsonFloat(json, "x");
            human.y = GetJsonFloat(json, "y");
            human.z = GetJsonFloat(json, "z");
            human.yaw = GetJsonFloat(json, "yaw");
            std::string direction = GetJsonString(json, "direction");

            std::cout << "AIR Entity: "
                << human.id
                << std::endl;

            std::cout << "Position: ("
                << human.x << ", "
                << human.y << ", "
                << human.z << ")"
                << std::endl;

            std::cout << "Yaw: "
                << human.yaw
                << std::endl;

            std::cout << "Direction: " << direction
                << std::endl;

            float yawRad =
                human.yaw * PI / 180.0f;

            // Unity座標系に合わせた身体基準ベクトル
            float rightX = std::cos(yawRad);
            float rightZ = -std::sin(yawRad);
            float forwardX = std::sin(yawRad);
            float forwardZ = std::cos(yawRad);

            float dirX = 0.0f;
            float dirZ = 0.0f;

            if (direction == "right")
            {
                dirX = rightX;
                dirZ = rightZ;
            }
            else if (direction == "left")
            {
                dirX = -rightX;
                dirZ = -rightZ;
            }
            else if (direction == "forward")
            {
                dirX = forwardX;
                dirZ = forwardZ;
            }

            float moveDistance = 1.0f;

            float targetX = human.x + dirX * moveDistance;
            float targetY = human.y;
            float targetZ = human.z + dirZ * moveDistance;

            //-------- Send target position to AIR Manager --------
            std::ostringstream responseStream;

            responseStream
                << "{"
                << "\"type\":\"air_target_position\","
                << "\"reference\":\"Human_1\","
                << "\"direction\":\"right\","
                << "\"x\":" << targetX << ","
                << "\"y\":" << targetY << ","
                << "\"z\":" << targetZ
                << "}";

            std::string response =
                responseStream.str();

            send(
                clientSocket,
                response.c_str(),
                static_cast<int>(response.size()),
                0
            );

            //-------- Debug output --------
            std::cout << "Sent: "
                << response
                << std::endl;

            std::cout << "Entity ID: "
                << human.id
                << std::endl;

            std::cout << "Position: ("
                << human.x << ", "
                << human.y << ", "
                << human.z << ")"
                << std::endl;

            std::cout << "Yaw: "
                << human.yaw
                << std::endl;

            std::cout << "Right Direction: ("
                << rightX << ", 0, "
                << rightZ << ")"
                << std::endl;

            std::cout << "Target Position: ("
                << targetX << ", "
                << targetY << ", "
                << targetZ << ")"
                << std::endl;

            std::cout << "Direction: "
                << direction
                << std::endl;

            //-------- windows socket cleanup --------
            closesocket(clientSocket);

            std::cout << "Waiting for next command..."
                << std::endl;
        }
    }
    closesocket(serverSocket);

    WSACleanup();

    return 0;
}