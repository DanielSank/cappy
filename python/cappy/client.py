import socket
import json


message_obj = {
    "id": 1,
    "method": "square",
    "args": [4]
}
# Ask the service to square the number 4.


message_string = json.dumps(message_obj)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8083))
    sock.send(message_string)
    data = sock.recv(1024)
    sock.close()
    print data


if __name__ == "__main__":
    main()
