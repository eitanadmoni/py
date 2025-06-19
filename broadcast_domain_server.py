import socket
import argparse
import select


SERVER_IP = "127.0.0.1"
MAX_CLIENTS = 4


def change_rooms(new_room, client, client_to_name_and_room, room_to_clients):
    old_room = client_to_name_and_room[client][1]
    if old_room != new_room:
        room_to_clients[old_room].remove(client)
        if new_room in room_to_clients:
            room_to_clients[new_room].append(client)
        else:
            room_to_clients[new_room] = [client]
        client_to_name_and_room[client] = (client_to_name_and_room[client][0], new_room)
        print(f"Client {client_to_name_and_room[client][0]} moved to room {new_room}")
        print(room_to_clients)


def handle_multiple_clients(clients, client_to_name_and_room,  room_to_clients):
    while True:
        if clients == []:
            print("No clients connected. Server shutting down.")
            break

        readable, _, _ = select.select(clients, [], [])
        for client in readable:
            try:
                data = client.recv(1024)
                print(data.decode('utf-8'))
                if not data:
                    clients.remove(client)
                    client.close()
                    continue

                if data.decode('utf-8') == '/exit':
                    print(f"Client {client_to_name_and_room[client][0]} has exited the room {client_to_name_and_room[client][1]}")
                    clients.remove(client)
                    client.close()
                    continue

                if data.decode('utf-8').split()[0] == '/transfer':
                    _, new_room = data.decode('utf-8').split()
                    new_room = int(new_room)
                    change_rooms(new_room, client, client_to_name_and_room, room_to_clients)
                    continue
                
                msg_client = client_to_name_and_room[client][0] + ": "
                for other_client in room_to_clients[client_to_name_and_room[client][1]]:
                    if other_client != client:
                        other_client.sendall(msg_client.encode() + data)

            except Exception as e:
                print(f"An error occurred: {e}")
                clients.remove(client)
                client.close()

    for client in clients:
        client.close()


def server_connection(port):
    room_to_clients = {}
    client_to_name_and_room = {}
    clients = []
    num_of_clients = 0
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((SERVER_IP, port))
            server_socket.listen()
            print(f"Server listening on port {port}")
            while num_of_clients < MAX_CLIENTS:
                client_socket, addr = server_socket.accept()
                print(f"Connected to client: {addr}")
                client_info = client_socket.recv(1024).decode('utf-8')
                name, room = client_info.split(',')
                room = int(room)
                clients.append(client_socket)
                print(f"Client {name} joined room {room}")
                if room in room_to_clients:
                    room_to_clients[room].append(client_socket)
                else:
                    room_to_clients[room] = [client_socket]                     
                client_to_name_and_room[client_socket] = (name,room)

                num_of_clients += 1

            handle_multiple_clients(clients, client_to_name_and_room, room_to_clients)

    except Exception as e:
        print(f"An error occurred: {e}")


def get_arguments():
    parser = argparse.ArgumentParser(description="Server of domain")
    parser.add_argument("port", type=int, help="port of server to bind to")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    server_connection(args.port)

