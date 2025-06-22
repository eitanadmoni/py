import socket
import argparse
import sys
import select
import random

NAME_POSITION = 2
IP_POSITION = 3
PORT_POSITION = 4


def update_udp_address(message, name_to_address):
    message_words = message.split()
    name, ip, port = message_words[NAME_POSITION], message_words[IP_POSITION], int(message_words[PORT_POSITION])
    print(f"name: {name}, ip: {ip}, port: {port}")
    name_to_address[name] = (ip, port)
    print(f"update address of {name}")


def send_private_message(message, name_to_address, myname):
    message_words = message.split()
    name = message_words[1]
    message_to_send =  f'{myname}: ' +  ' '.join(message_words[2:])
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_client:
        udp_client.sendto(message_to_send.encode() ,name_to_address[name])


def get_private_message(message):
    message_name_split = message.split(":")
    print(f"{message_name_split[0]} sent privately: ", end='')
    print(':'.join(message_name_split[1:]))


def handle_connection(sockets, server_socket, private_socket, myname):
    name_to_address = {}
    while True:
        readable, _, _ = select.select(sockets, [], [])
        for sock in readable:
            if sock == sys.stdin:
                message = sys.stdin.readline()
                if message.strip() == '/exit':
                    print("Exiting client...")
                    server_socket.sendall(message.encode('utf-8'))
                    return
                elif message.strip().startswith("/unicast"):
                    send_private_message(message.strip(), name_to_address, myname)
                else:
                    server_socket.sendall(message.encode('utf-8'))
                
            elif sock == server_socket:
                data = sock.recv(1024)
                if not data:
                    print("Server disconnected.")
                    return
                
                elif data.decode('utf-8').strip().startswith("client information:"):
                    update_udp_address(data.decode('utf-8').strip(), name_to_address)
                
                elif data.decode('utf-8').strip().startswith("kick message:"):
                    print(data.decode('utf-8'))
                    return
                
                elif data.decode('utf-8').strip().startswith("Shutdown:"):
                    print(data.decode('utf-8'))
                    return
                
                else: 
                    print(data.decode('utf-8'))
            
            elif sock == private_socket:
                data = sock.recv(1024)
                if not data:
                    print("udp connection disconnected.")
                    continue
                get_private_message(data.decode('utf-8'))
            


def client_connection(ip, port, name, room):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((ip, port))
            print(f"Connected to server at {ip} in port {port}")
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_port = random.randint(1000, 2000)
                udp_socket.bind(("", udp_port))
                tcp_socket.sendall(f"{name},{room},{udp_port}".encode('utf-8'))
                print(f"Sent client information: Name = {name}, Room = {str(room)}")
                handle_connection([tcp_socket, sys.stdin, udp_socket], tcp_socket, udp_socket, name)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        tcp_socket.close


def get_arguments():
    parser = argparse.ArgumentParser(description="Client of domain")
    parser.add_argument("ip", type=str, help="ip of server to connect to")
    parser.add_argument("port", type=int, help="port of server to connect to")
    parser.add_argument("name", type=str, help="name of the client")
    parser.add_argument("room", type=int, help="room to enter the client to")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    client_connection(args.ip, args.port, args.name, args.room)