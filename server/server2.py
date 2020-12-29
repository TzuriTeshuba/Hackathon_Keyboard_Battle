from socket import *
import struct
import threading
import time
import random
#program constants
COLOR_RED = "red"
COLOR_GREEN = "green"
COLOR_YELLOW = "yellow"
COLOR_BLUE = "blue"
COLOR_DEFUALT = "default"
COLOR_SEND = COLOR_YELLOW


COLORS = {
    COLOR_RED:"\u001b[31m",
    COLOR_GREEN:"\u001b[32m",
    COLOR_YELLOW:"\u001b[33m",
    COLOR_BLUE:"\u001b[34m",
    COLOR_DEFUALT:"\u001b[0m"
    }

def print_color(clr, msg):
    print(COLORS[clr]+msg+COLORS[COLOR_DEFUALT])

def colorize(clr, txt):
    return COLORS[clr]+txt+COLORS[COLOR_DEFUALT]

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
UDP_COOKIE = 0xfeedbeef
OFFER_CODE = 0x2
SERVER_NAME = gethostbyname(gethostname())
OFFER_ADDR = (SERVER_NAME, OFFER_PORT)
FORMAT = 'utf-8'
SECS_TO_WAIT = 5
NUM_GROUPS = 2
TIMEOUT = .0125

group_addrs = [[],[]]
group_scores = [0,0]
client_dict = {}
game_mode_event = threading.Event()
game_over_event = threading.Event()

class Team:
    def __init__(self, name):
        self.name = name
        self.score = 0

def init_fields():
    group_addrs = [[],[]]
    group_scores = [0,0]
    client_dict = {}
    game_mode_event.clear()
    game_over_event.clear()


def main():
    try:
        while True:
            print_color(COLOR_GREEN,"---------------- SERVER RUNNING -------------")
            init_fields()
            server_socket = socket(AF_INET, SOCK_STREAM)
            listen_port = bind_to_available_port(server_socket)
            threads = [
                threading.Thread(target=run_timer, name="TIMER_THREAD", args=()),
                threading.Thread(target=listen_for_clients, name="LISTEN_THREAD", args=[server_socket]),
                threading.Thread(target=send_offers, name="OFFER_THREAD", args=[listen_port])
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            print_color(COLOR_GREEN,"Game Is Officially Over!")
    except Exception as e:
        print_color(COLOR_RED,"Exiting... OPEN THREADS:\n")
        raise e
        #print(threading.enumerate())
    return 0

def run_timer():
    time.sleep(SECS_TO_WAIT)
    game_mode_event.set()
    time.sleep(SECS_TO_WAIT)
    game_mode_event.clear()
    game_over_event.set()

def bind_to_available_port(sock):
    prt = 5057
    while True:
        try:
            sock.bind((SERVER_NAME, prt))
            return prt
        except:
            print_color(COLOR_RED,f"port {prt} taken")
            prt += 1

def listen_for_clients(server_socket):
    num_clients = 0
    #listen_port = bind_to_available_port(server_socket)

    server_socket.listen()
    server_socket.settimeout(1)
    print_color( COLOR_GREEN,f"[LISTENING] Server is listening on {SERVER_NAME}")
    threads = []
    while not game_mode_event.is_set():
        try:
            cnn, addr = server_socket.accept()
            num_clients += 1
            thread = threading.Thread(target=handle_client, name=f"HANDLER_{num_clients}", args=(cnn, addr))
            threads.append(thread)
            thread.start()
            print_color(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 4}")
        except:
            x=1
    #game_over_event.wait()
    for thread in threads:
        thread.join()
    server_socket.close()


def handle_client(cnn, addr):
    #print(f"[NEW CONNECTION] {addr} connected.")
    cnn.settimeout(TIMEOUT)
    team_name = ""
    while True:
        ch = cnn.recv(1).decode(FORMAT)
        if ch[0] != '\n':
            team_name += ch
        else: break
    print_color(COLOR_YELLOW,"New Team: " + team_name)
    group_num = random.randint(0,NUM_GROUPS-1)
    group_addrs[group_num].append(addr)
    team = Team(team_name)
    client_dict[addr] = team
    game_mode_event.wait()
    ###send start_message
    welcome_msg = get_welcome_message() #TODO: make more efficient, maybe check len()
    welcome_bytes = struct.pack(f"! {len(welcome_msg)}s",colorize(COLOR_SEND,welcome_msg).encode())
    cnn.send(welcome_bytes)
    while game_mode_event.is_set():
        msg = recv_letter(cnn)
        if len(msg):
            print_color(COLOR_DEFUALT,"got: " + msg)
            handle_message(cnn,addr,group_num,team,msg)
            #cnn.send(("Server: msg received: "+msg).encode(FORMAT))
    msg = game_over_msg()
    msg_bytes = struct.pack(f"! {len(msg)}s",colorize(COLOR_SEND, msg).encode())
    print_color(COLOR_BLUE,msg)
    cnn.send(msg_bytes)
    cnn.close()

def recv_letter(cnn):
    msg = ""
    try:
        msg = cnn.recv(1).decode(FORMAT)
    except:
        msg = ""
    finally:
        return msg


def handle_message(cnn, addr, group, team, msg):
    team.score += 1

def game_over_msg():
    msg = "Game Over!\n"
    winner = 0
    max_score = -1
    for grp_num in range(0, NUM_GROUPS):
        score = 0
        for addr in group_addrs[grp_num]:
            team = client_dict[addr]
            score += team.score
        if score > max_score:
            winner = grp_num
            max_score = score
        msg = msg + f"Group {grp_num+1} typed in {score} characters.\n"
    msg += f"Group {winner} wins!\n\nCongratulations to the winners:\n=="
    for addr in group_addrs[winner]:
        msg = msg + "\n" + client_dict[addr].name
    return msg


def send_offers(listen_port):
    print_color(COLOR_GREEN,"sending offers")
    offer_sock = socket(AF_INET, SOCK_DGRAM)
    offer_sock.bind(OFFER_ADDR)
    msg_bytes = struct.pack('!Ibh', UDP_COOKIE ,OFFER_CODE,listen_port)
    while not game_mode_event.is_set():
        offer_sock.sendto(msg_bytes,('localhost',CLIENT_PORT))
        time.sleep(1.0)
    print_color(COLOR_GREEN,"all offers sent")
    offer_sock.close()




    # sock = socket(AF_INET, SOCK_RAW, IPPROTO_UDP)
    # length = 8+len(data);
    # checksum = 0
    # udp_header = struct.pack('!HHHH', src_port, dst_port, length, checksum)
    # sock.send(udp_header+data)

def get_welcome_message():
    msg = "Welcome to Keyboard Spamming Battle Royale.\n"
    for group_num in range(0,2):
        msg += f"\nGroup {group_num+1}:\n==\n"
        for adrs in group_addrs[group_num]:
            msg = msg + client_dict[adrs].name + "\n"
    msg += "\nStart pressing keys on your keyboard as fast as you can!!"
    return msg



if __name__ == "__main__":
    main()