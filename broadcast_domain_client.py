import socket
import argparse
import sys
import select


EXIT = '/exit'
MESSAGE_MAX_LENGTH = 1024


def handle_connection(sockets, client_socket):
    while True:
        readable, _, _ = select.select(sockets, [], [])
        for sock in readable:
            if sock == sys.stdin:
                message = sys.stdin.readline()
                client_socket.sendall(message.encode('utf-8'))
                if message.strip().lower() == EXIT:
                    print("Exiting client...")
                    return
            else:
                data = sock.recv(MESSAGE_MAX_LENGTH)
                if not data:
                    print("Server disconnected.")
                    return
                print(data.decode('utf-8'))


def client_connection(ip, port, name, room):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            print(f"Connected to server at {ip} in port {port}")

            s.sendall(f"{name},{room}".encode('utf-8'))
            print(f"Sent client information: Name = {name}, Room = {str(room)}")
            handle_connection([s, sys.stdin], s)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        s.close


def get_arguments():
    parser = argparse.ArgumentParser(description="Client of domain")
    parser.add_argument("ip", type=str, help="ip of server to connect to")
    parser.add_argument("port", type=int, help="port of server to connect to")
    parser.add_argument("name", type=str, help="name of the client")
    parser.add_argument("room", type=int, help="room to enter the client to")
    return parser.parse_args()


def main():
    args = get_arguments()
    client_connection(args.ip, args.port, args.name, args.room)

    
if __name__ == "__main__":
    main()
    