import socket

host = "127.0.0.1"
port = 50000

message = "Hello from Python"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall(message.encode("utf-8"))

print("送信しました:", message)