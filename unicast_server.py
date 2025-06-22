import socket
import argparse
import select


SERVER_IP = "127.0.0.1"
import time

def change_rooms(new_room, client, client_to_name_and_room, room_to_clients, locked_rooms):
    if new_room in locked_rooms:
        client.sendall("The room is locked!".encode('utf-8'))
        return
    old_room = client_to_name_and_room[client][1]
    if old_room != new_room:
        room_to_clients[old_room].remove(client)
        if new_room in room_to_clients:
            room_to_clients[new_room].append(client)
        else:
            room_to_clients[new_room] = [client]
        client_to_name_and_room[client] = (client_to_name_and_room[client][0], new_room)
        print(f"Client {client_to_name_and_room[client][0]} moved to room {new_room}")
        enter_room_message(client, new_room, room_to_clients, client_to_name_and_room)
        left_room_message(client, old_room, room_to_clients, client_to_name_and_room)


def remove_client(clients, client, room_to_clients, client_to_name_and_room, client_to_ip_and_udp_port):
    print(f"Client {client_to_name_and_room[client][0]} has exited the room {client_to_name_and_room[client][1]}")
    left_room_message(client,client_to_name_and_room[client][1], room_to_clients, client_to_name_and_room)
    clients.remove(client)
    room_to_clients[client_to_name_and_room[client][1]].remove(client)
    client_to_name_and_room.pop(client)
    client_to_ip_and_udp_port.pop(client)
    client.close()


def find_client_by_name(client_to_name_and_room, room_to_cleints, room, client_name):
    for client in room_to_cleints[room]:
        if client_to_name_and_room[client][0] == client_name:
            return client
    return False


def kick_client(kick_message, kicker, clients, room_to_clients, client_to_name_and_room, client_to_ip_and_udp_port):
    client_name = kick_message.split()[1]
    client = find_client_by_name(client_to_name_and_room, room_to_clients, client_to_name_and_room[kicker][1], client_name)
    if not client:
        kicker.sendall("There is no such member in your room!".encode('utf-8'))
        return
    client.sendall("kick message: you kicked out from the connection".encode('utf-8'))
    remove_client(clients, client, room_to_clients, client_to_name_and_room, client_to_ip_and_udp_port)


def close_room(room, room_to_clients, clients, client_to_name_and_room):
    for client in room_to_clients[room]:
        remove_client(clients, client, room_to_clients, client_to_name_and_room)


def lock_room(room, locked_rooms):
    if room not in locked_rooms:
        locked_rooms.append(room)


def client_room_status(client, room, room_to_clients, client_to_name_and_room):
    for other_client in room_to_clients[room]:
        if other_client != client:
            client.sendall(f"{client_to_name_and_room[other_client][0]} in your room".encode('utf-8'))
            time.sleep(0.1)


def enter_room_message(client, room, room_to_clients, client_to_name_and_room):
    for other_client in room_to_clients[room]:
        if other_client != client:
            other_client.sendall(f"{client_to_name_and_room[other_client][0]} enter your room".encode('utf-8'))
            time.sleep(0.1)


def left_room_message(client, room, room_to_clients, client_to_name_and_room):
    for other_client in room_to_clients[room]:
        if other_client != client:
            other_client.sendall(f"{client_to_name_and_room[client][0]} left the room".encode('utf-8'))
            time.sleep(0.1)


def room_status(room, room_to_clients, client_to_name_and_room):
     for client in room_to_clients[room]:
            client_room_status(client, room, room_to_clients, client_to_name_and_room)


def send_history(client, client_to_name_and_room, room_to_history):
    room = client_to_name_and_room[client][1]
    if room not in room_to_history.keys():
        client.sendall("There is no history in your room".encode('utf-8'))
        return
    client.sendall('Message history of your room:\n'.encode('utf-8'))
    for message in room_to_history[room]:
        client.sendall(message.encode('utf-8'))
        time.sleep(0.1)
    client.sendall('Sent all history of your room'.encode('utf-8'))


def send_message(client, data, client_to_name_and_room, room_to_clients, room_to_history):
    msg_client = client_to_name_and_room[client][0] + ": "
    room = client_to_name_and_room[client][1]
    if room in room_to_history.keys():
        room_to_history[room].append(msg_client + data.decode('utf-8'))
    else:
        room_to_history[room] = [msg_client + data.decode('utf-8')]
    for other_client in room_to_clients[room]:
        if other_client != client:
            other_client.sendall(msg_client.encode('utf-8') + data)


def send_personal_data_to_clients(client, client_to_ip_and_udp_port, client_to_name_and_room):
    for other_client in client_to_ip_and_udp_port:
        if other_client != client:
            msg = "client information: " + client_to_name_and_room[client][0] + " " + client_to_ip_and_udp_port[client][0] + " " + client_to_ip_and_udp_port[client][1]
            other_client.sendall(msg.encode())
            time.sleep(0.1)


def send_personal_data_to_specific_client(client,  client_to_ip_and_udp_port, client_to_name_and_room):
    for other_client in client_to_ip_and_udp_port:
        if other_client != client:
            msg = "client information: " + client_to_name_and_room[other_client][0] + " " + client_to_ip_and_udp_port[other_client][0] + " " + client_to_ip_and_udp_port[other_client][1]
            client.sendall(msg.encode())
            time.sleep(0.1)


def add_client(server_socket, client_to_ip_and_udp_port, clients, room_to_clients, client_to_name_and_room, locked_rooms):
    client_socket, addr = server_socket.accept()
    print(f"Connected to client: {addr}")
    client_info = client_socket.recv(1024).decode('utf-8')
    name, room, udp_port = client_info.split(',')
    room = int(room)
    if room in locked_rooms:
        client_socket.sendall("This room is locked!".encode('utf-8'))
        client_socket.close()
        return
    
    client_to_ip_and_udp_port[client_socket] = (addr[0], udp_port)
    clients.append(client_socket)
    print(f"Client {name} joined room {room}")
    if room in room_to_clients:
        room_to_clients[room].append(client_socket)
    else:
        room_to_clients[room] = [client_socket]                     
    client_to_name_and_room[client_socket] = (name,room)
    enter_room_message(client_socket, room, room_to_clients, client_to_name_and_room)
    send_personal_data_to_clients(client_socket,  client_to_ip_and_udp_port, client_to_name_and_room)
    send_personal_data_to_specific_client(client_socket, client_to_ip_and_udp_port, client_to_name_and_room)


def handle_multiple_clients(clients, server_socket, client_to_name_and_room,  room_to_clients, client_to_ip_and_udp_port):
    locked_rooms = []
    room_to_history = {}
    for room in room_to_clients.keys():
        room_status(room, room_to_clients, client_to_name_and_room)

    while True:
        if len(clients) == 1:
            print("No clients connected. Server shutting down.")
            break
        readable, _, _ = select.select(clients, [], [])
        for client in readable:
            if client == server_socket:
                add_client(server_socket, client_to_ip_and_udp_port, clients, room_to_clients, client_to_name_and_room, locked_rooms)
                continue
            try:
                data = client.recv(1024)
                if not data:
                    clients.remove(client)
                    client.close()
                    continue

                elif data.decode('utf-8').strip() == '/exit':
                    remove_client(clients, client, room_to_clients, client_to_name_and_room, client_to_ip_and_udp_port)
                    continue

                elif data.decode('utf-8').strip().split()[0] == '/transfer':
                    _, new_room = data.decode('utf-8').split()
                    new_room = int(new_room)
                    change_rooms(new_room, client, client_to_name_and_room, room_to_clients, locked_rooms)
                    continue

                elif data.decode('utf-8').strip().startswith("/kick"):
                    kick_client(data.decode('utf-8').strip(), client, clients, room_to_clients, client_to_name_and_room, client_to_ip_and_udp_port)
                
                elif data.decode('utf-8').strip() == '/close-room':
                    close_room(client_to_name_and_room[client][1], room_to_clients, clients, client_to_name_and_room)

                elif data.decode('utf-8').strip() == '/lock-room':
                    lock_room(client_to_name_and_room[client][1], locked_rooms)

                elif data.decode('utf-8').strip() == '/room-status':
                    client_room_status(client, client_to_name_and_room[client][1], room_to_clients, client_to_name_and_room)

                elif data.decode('utf-8').strip() == '/shutdown':
                    for clinet in clients:
                        client.sendall("Shutdown: The server had shut down".encode('utf-8'))
                        remove_client(clients, client, room_to_clients, client_to_name_and_room)
                    return
                elif data.decode('utf-8').strip() == '/history':
                    send_history(client, client_to_name_and_room, room_to_history)
                else:
                    send_message(client, data, client_to_name_and_room, room_to_clients, room_to_history)
                    

            except Exception as e:
                print(f"An error occurred: {e}")
                clients.remove(client)
                client.close()

    for client in clients:
        client.close()


def server_connection(port):
    room_to_clients = {}
    client_to_name_and_room = {}
    client_to_ip_and_udp_port = {}
    clients = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((SERVER_IP, port))
            server_socket.listen()
            clients.append(server_socket)
            print(f"Server listening on port {port}")
            client_socket, addr = server_socket.accept()
            print(f"Connected to client: {addr}")
            client_info = client_socket.recv(1024).decode('utf-8')
            name, room, udp_port = client_info.split(',')
            client_to_ip_and_udp_port[client_socket] = (addr[0], udp_port)
            room = int(room)
            clients.append(client_socket)
            print(f"Client {name} joined room {room}")
            if room in room_to_clients:
                room_to_clients[room].append(client_socket)
            else:
                room_to_clients[room] = [client_socket]                     
            client_to_name_and_room[client_socket] = (name,room)
            handle_multiple_clients(clients,server_socket,  client_to_name_and_room, room_to_clients, client_to_ip_and_udp_port)


    except Exception as e:
        print(f"An error occurred: {e}")


def get_arguments():
    parser = argparse.ArgumentParser(description="Server of domain")
    parser.add_argument("port", type=int, help="port of server to bind to")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    server_connection(args.port)

