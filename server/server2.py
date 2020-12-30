from socket import *
import struct
import threading
import time
import random
from team import Team
from colors import *
from exceptions import DisconnectException, NoTeamNameException


#Network Constants
NETWORK_PREFIX = "172."
DEV_NET_PREFIX = NETWORK_PREFIX+"1."
TEST_NET_PREFIX = NETWORK_PREFIX+"99."
CLIENT_PREFIX = DEV_NET_PREFIX
LAST_NET_IP = 24
LOCAL_HOST = "127.0.0.1"
CLIENT_PORT = 13117

#Server Constants
INITIAL_OFFER_PORT = 7531
INITIAL_LISTEN_PORT = 6421
UDP_COOKIE = 0xfeedbeef
OFFER_CODE = 0x2
SERVER_NAME = gethostbyname(gethostname())
TIMEOUT = 0.5
ACCEPT_TIMEOUT = 1.0

#Program constants
FORMAT = 'utf-8'
SECS_TO_WAIT = 10
NUM_GROUPS = 2

#Program variables
group_addrs = [[],[]]
client_dict = {}
game_mode_event = threading.Event()
game_over_event = threading.Event()



def init_fields():
    global group_addrs
    global client_dict
    group_addrs  = [[],[]]#TODO: make dynamic
    client_dict  = {}
    game_mode_event.clear()
    game_over_event.clear()

def main():
    while True:
        try:
            print_color(COLOR_GREEN,f"Server started, listening on IP address {SERVER_NAME}")
            init_fields()
            server_socket = socket(AF_INET, SOCK_STREAM)
            listen_port = bind_to_available_port(server_socket,INITIAL_LISTEN_PORT)
            threads = [
                threading.Thread(target=run_timer, name="TIMER_THREAD", args=()),
                threading.Thread(target=listen_for_clients, name="LISTEN_THREAD", args=[server_socket]),
                threading.Thread(target=send_offers, name="OFFER_THREAD", args=[listen_port])
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        except Exception as e:
            try:
                server_socket.close()
            except:
                pass
            #print(f"\n----\n{e}\n-------\n")
    return 0


def bind_to_available_port(sock, prt):
    while True:
        try:
            sock.bind((SERVER_NAME, prt))
            return prt
        except:
            prt += 1

def run_timer():
    time.sleep(SECS_TO_WAIT)
    game_mode_event.set()
    time.sleep(SECS_TO_WAIT)
    game_mode_event.clear()
    game_over_event.set()

### For dev lab broadcast only ###
def send_offers_dev(listen_port):
    BROADCAST_IP = "172.1.255.255"
    offer_sock = socket(AF_INET, SOCK_DGRAM,IPPROTO_UDP)
    offer_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    offer_port = bind_to_available_port(offer_sock,INITIAL_OFFER_PORT)
    msg_bytes = struct.pack('!Ibh', UDP_COOKIE ,OFFER_CODE,listen_port)
    while not game_mode_event.is_set():
        for i in range(0,LAST_NET_IP+1):
            offer_sock.sendto(msg_bytes, (DEV_NET_PREFIX + str(i), CLIENT_PORT))
            time.sleep(1.0)
    offer_sock.close()

### broadcast for whole network ###
def send_offers_net(listen_port):
    offer_sock = socket(AF_INET, SOCK_DGRAM,IPPROTO_UDP)
    offer_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    offer_port = bind_to_available_port(offer_sock,INITIAL_OFFER_PORT)
    msg_bytes = struct.pack('!Ibh', UDP_COOKIE ,OFFER_CODE,listen_port)
    while not game_mode_event.is_set():
        offer_sock.sendto(msg_bytes, ('<broadcast>', CLIENT_PORT))
        time.sleep(1.0)
    offer_sock.close()

### local ###
def send_offers(listen_port):
    offer_sock = socket(AF_INET, SOCK_DGRAM,IPPROTO_UDP)
    offer_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    offer_port = bind_to_available_port(offer_sock,INITIAL_OFFER_PORT)
    msg_bytes = struct.pack('!Ibh', UDP_COOKIE ,OFFER_CODE,listen_port)
    while not game_mode_event.is_set():
        offer_sock.sendto(msg_bytes, ('localhost', CLIENT_PORT))
        time.sleep(1.0)
    offer_sock.close()

def listen_for_clients(server_socket):
    num_clients = 0
    server_socket.listen()
    server_socket.settimeout(ACCEPT_TIMEOUT)
    print_color( COLOR_GREEN,f"[LISTENING] Server is listening on {SERVER_NAME}")
    threads = []
    while not game_mode_event.is_set():
        try:
            cnn, addr = server_socket.accept()
            num_clients += 1
            thread = threading.Thread(target=handle_client, name=f"HANDLER_{num_clients}", args=(cnn, addr))
            threads.append(thread)
            thread.start()
            print("new handler thread")
        except:
            pass
    for thread in threads:
        thread.join()
    server_socket.close()

def handle_client(cnn, addr):
    try:
        cnn.settimeout(TIMEOUT)
        team_name = get_team_name(cnn)
        group_num = random.randint(0,NUM_GROUPS-1)
        group_addrs[group_num].append(addr)
        team = Team(team_name)
        client_dict[addr] = team
        game_mode_event.wait()
        empty_socket(cnn, team)
        send_msg(cnn, get_welcome_message())
        while game_mode_event.is_set():
            msg = recv_letter(cnn)
            if (len(msg) and ord(msg[0])):
                handle_message(cnn,addr,group_num,team,msg)
        send_msg(cnn,game_over_msg())
    except DisconnectException:
        print_color(COLOR_GREEN, f"{addr} disconnected")
    except NoTeamNameException:
        send_msg(cnn,"You did not provide a name in time. good bye")
    finally:
        cnn.close()

def get_team_name(cnn):
    team_name = ""
    while not game_over_event.is_set():
        c = recv_letter(cnn)
        if c == None:
            raise DisconnectException
        elif not len(c):
            continue
        elif (c[0] != '\n'):
            team_name += c
        else:
            return team_name
    raise NoTeamNameException

def empty_socket(cnn,team):
    while True:
        c = recv_letter(cnn)
        if c == None:
            raise DisconnectException
        elif len(c):
            team.num_sent_early += 1
        else:
            return

def recv_letter(cnn):
    msg = ""
    try:
        msg = cnn.recv(1).decode(FORMAT)
        if not len(msg):
            msg = None
    except:
        msg = ""
    finally:
        return msg

def handle_message(cnn, addr, group, team, msg):
    team.score += 1
    team.msg += msg

def send_msg(cnn,msg):
    msg = colorize(COLOR_SEND,msg)
    msg_bytes = struct.pack(f"! {len(msg)}s",msg.encode())
    cnn.send(msg_bytes)

def get_welcome_message():
    msg = "Welcome to Keyboard Spamming Battle Royale.\n"
    for group_num in range(0,2):
        msg += f"\nGroup {group_num+1}:\n==\n"
        for adrs in group_addrs[group_num]:
            msg = msg + client_dict[adrs].name + "\n"
    msg += "\nStart pressing keys on your keyboard as fast as you can!!"
    return msg

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
    msg += f"Group {winner+1} wins!\n\nCongratulations to the winners:\n=="
    for addr in group_addrs[winner]:
        msg = msg + "\n" + client_dict[addr].name
    return msg


if __name__ == "__main__":
    main()