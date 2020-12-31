from socket import *
import scapy.arch
import struct
import threading
import time
import random
from team import Team
from colors import *
from exceptions import DisconnectException, NoTeamNameException


#Network Constants
CLIENT_PORT = 13117
DEV_BROADCAST_IP = "172.1.255.255"
TEST_BROADCAST_IP = "172.99.255.255"
BROADCAST_IP = DEV_BROADCAST_IP
INITIAL_OFFER_PORT = 7531
INITIAL_LISTEN_PORT = 6421
SERVER_IP = scapy.arch.get_if_addr("eth1")


#Program Constants
UDP_COOKIE = 0xfeedbeef
OFFER_CODE = 0x2
TIMEOUT = 0.0
ACCEPT_TIMEOUT = 1.0
OFFER_DELAY = 1
TEAM_NAME_SUFFIX = "\n"
UTF_8_FORMAT = 'utf-8'
UDP_PACK_FORMAT = '!Ibh'

SECS_TO_WAIT = 4
NUM_GROUPS = 2
GAME_MODE_EVENT = threading.Event()
GAME_OVER_EVENT = threading.Event()

#Program variables
group_addrs = []
client_dict = {}


def init_fields():
    global group_addrs
    global client_dict
    group_addrs  = []
    for i in range(0,NUM_GROUPS):
        group_addrs.append([])
    client_dict  = {}
    GAME_MODE_EVENT.clear()
    GAME_OVER_EVENT.clear()


def main():
    while True:
        try:
            print_color(COLOR_GREEN,f"Server started, listening on IP address {SERVER_IP}")
            init_fields()
            server_socket = socket(AF_INET, SOCK_STREAM)
            listen_port = bind_to_available_port(server_socket,INITIAL_LISTEN_PORT)
            threads = [
                threading.Thread(target=run_timer, name="TIMER_THREAD", args=()),
                threading.Thread(target=listen_for_clients, name="LISTEN_THREAD", args=[server_socket]),
                threading.Thread(target=send_offers_broadcast, name="OFFER_THREAD", args=[listen_port])
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
    return 0

# binds @sock to a port >= @prt and @returns the port number
# socket * int -> int
def bind_to_available_port(sock, prt):
    while True:
        try:
            sock.bind((SERVER_IP, prt))
            return prt
        except:
            prt += 1

# set state of the game
def run_timer():
    time.sleep(SECS_TO_WAIT)
    GAME_MODE_EVENT.set()
    time.sleep(SECS_TO_WAIT)
    GAME_MODE_EVENT.clear()
    GAME_OVER_EVENT.set()

# sends offer message to dev network to connect to port @listen_port
# NOT CURRENTLY IN USE- FOR TESTING PURPOSES
def send_offers_dev(listen_port):
    offer_sock = socket(AF_INET, SOCK_DGRAM,IPPROTO_UDP)
    offer_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    offer_port = bind_to_available_port(offer_sock,INITIAL_OFFER_PORT)
    msg_bytes = struct.pack(UDP_PACK_FORMAT, UDP_COOKIE ,OFFER_CODE,listen_port)
    while not GAME_MODE_EVENT.is_set():
        offer_sock.sendto(msg_bytes, (BROADCAST_IP, CLIENT_PORT))
        time.sleep(OFFER_DELAY)
    offer_sock.close()

# sends offer broadcast to current network to connect to port @listen_port
def send_offers_broadcast(listen_port):
    offer_sock = socket(AF_INET, SOCK_DGRAM,IPPROTO_UDP)
    offer_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    offer_port = bind_to_available_port(offer_sock,INITIAL_OFFER_PORT)
    msg_bytes = struct.pack(UDP_PACK_FORMAT, UDP_COOKIE ,OFFER_CODE,listen_port)
    while not GAME_MODE_EVENT.is_set():
        offer_sock.sendto(msg_bytes, ('<broadcast>', CLIENT_PORT))
        time.sleep(OFFER_DELAY)
    offer_sock.close()

# accept client requests to connect and handle the client connection in new thread
def listen_for_clients(server_socket):
    server_socket.listen()
    server_socket.settimeout(ACCEPT_TIMEOUT)
    threads = []
    while not GAME_MODE_EVENT.is_set():
        try:
            cnn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, name=f"HANDLER_{addr}", args=(cnn, addr))
            threads.append(thread)
            thread.start()
        except:
            pass
    for thread in threads:
        thread.join()
    server_socket.close()

# (1) receives team name from client. if not provided before game start, closes connection
# (2) registers client to the game
# (3) send messages to and handles messages from client
def handle_client(cnn, addr):
    try:
        cnn.settimeout(TIMEOUT)
        team_name = get_team_name(cnn)
        group_num = random.randint(0,NUM_GROUPS-1)
        group_addrs[group_num].append(addr)
        team = Team(team_name)
        client_dict[addr] = team
        GAME_MODE_EVENT.wait()
        flush_socket(cnn, team)
        send_msg(cnn, get_welcome_message())
        while GAME_MODE_EVENT.is_set():
            msg = recv_letter(cnn)
            if (len(msg) and ord(msg[0])):
                handle_message(cnn,addr,group_num,team,msg)
        send_msg(cnn,game_over_msg())
    except DisconnectException:
        print_color(COLOR_RED, f"{addr} disconnected")
    except NoTeamNameException:
        send_msg(cnn,"You did not provide a name in time. good bye")
    except:
        pass
    finally:
        cnn.close()

# @returns team name from client socket @cnn
# @raises NoTeamNameException if properly formatted name not received before game starts
# socket -> string
def get_team_name(cnn):
    team_name = ""
    while not GAME_OVER_EVENT.is_set():
        c = recv_letter(cnn)
        if not len(c):
            continue
        elif (c[0] != TEAM_NAME_SUFFIX):
            team_name += c
        else:
            return team_name
    raise NoTeamNameException

# flushes out lingering data from socket @cnn
def flush_socket(cnn,team):
    while True:
        c = recv_letter(cnn)
        if len(c):
            team.num_sent_early += 1
        else:
            return

# @returns one character from socket @cnn or "" if nothing to read
# @raises DisconnectException if server closed connection with socket @cnn
# socket -> string
def recv_letter(cnn):
    msg = ""
    try:
        msg = cnn.recv(1).decode(UTF_8_FORMAT)
        if len(msg):
            return msg
    except:
        return ""
    raise DisconnectException

# update teams score and game statistics
def handle_message(cnn, addr, group, team, msg):
    team.score += 1

# send @msg to socket @cnn
def send_msg(cnn,msg):
    msg = colorize(COLOR_SEND,msg)
    msg_bytes = struct.pack(f"! {len(msg)}s",msg.encode())
    try:
        cnn.send(msg_bytes)
    except:
        raise DisconnectException


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