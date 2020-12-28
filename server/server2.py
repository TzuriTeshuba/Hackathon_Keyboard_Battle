from socket import *
import struct
import threading
import time

#Client Constants
NETWORK_PREFIX = "172."
DEV_NET_PREFIX = NETWORK_PREFIX+"1."
TEST_NET_PREFIX = NETWORK_PREFIX+"99."
CLIENT_PREFIX = DEV_NET_PREFIX
LAST_NET_IP = 24
LOCAL_HOST = "127.0.0.1"
CLIENT_PORT = 13117

#Server Constants
UDP_HEADER = 8
TCP_HEADER = 20
OFFER_PORT = 5060
LISTEN_PORT = 5061
UDP_COOKIE = 0xfeedbeef
OFFER_CODE = 0x2
SERVER_NAME = gethostbyname(gethostname())
OFFER_ADDR = (SERVER_NAME, OFFER_PORT)
SERVER_ADDR = (SERVER_NAME, LISTEN_PORT)
FORMAT = 'utf-8'
SECS_TO_WAIT = 5

group_addrs = [[],[]]
client_dict = {}
game_mode_event = threading.Event()

class Team:
    def __init__(self, name):
        self.name = name
        self.score = 0

def main():
    print("socket server running")
    threading.Thread(target=send_offers, args=()).start()
    threading.Thread(target=listen_for_clients, args=()).start()
    game_mode_event.wait()
    print("Game Over!")



def listen_for_clients():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(SERVER_ADDR)
    server_socket.listen()
    print(f"[LISTENING] Server is listening on {SERVER_NAME}")
    while not game_mode_event.is_set():
        cnn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(cnn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")

def handle_client(cnn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    team_name = ""
    while True:
        ch = cnn.recv(1).decode(FORMAT)
        if ch[0] != '\n':
            team_name += ch
        else: break
    print("New Team: " + team_name)
    group_addrs[0].append(addr)
    team = Team(team_name)
    client_dict[addr] = team
    game_mode_event.wait()
    ###send start_message
    roster_msg = get_roster_message()
    roster_bytes = struct.pack(f"! {len(roster_msg)}s",roster_msg.encode())
    cnn.send(roster_bytes)
    while game_mode_event.is_set():
        msg = cnn.recv(1024).decode(FORMAT)
        print("got: " +msg)
        if True:
            msg_length = int(msg)
            msg = cnn.recv(msg_length).decode(FORMAT)
            print(f"[{addr}] {msg}")
            cnn.send("Msg received".encode(FORMAT))
    cnn.close()

def send_offers():
    for i in range(0,SECS_TO_WAIT):
        server_sock = socket(AF_INET, SOCK_DGRAM)
        server_sock.bind(OFFER_ADDR)
        msg_bytes = struct.pack('!Ibh', UDP_COOKIE ,OFFER_CODE,LISTEN_PORT)
        #msg_bytes = "hello tbaby".encode()
        server_sock.sendto(msg_bytes,('localhost',CLIENT_PORT))
        print("offer sent")
        time.sleep(1.0)
    game_mode_event.set()

    # sock = socket(AF_INET, SOCK_RAW, IPPROTO_UDP)
    # length = 8+len(data);
    # checksum = 0
    # udp_header = struct.pack('!HHHH', src_port, dst_port, length, checksum)
    # sock.send(udp_header+data)

def get_roster_message():
    msg = "Welcome to Keyboard Spamming Battle Royale.\n"
    for group_num in range(0,2):
        msg += f"Group {group_num+1}:\n==\n"
        for adrs in group_addrs[group_num]:
            msg = msg + client_dict[adrs].name + "\n"
    msg += "\nStart pressing keys on your keyboard as fast as you can!!"
    return msg


if __name__ == "__main__":
    main()