from socket import *
import struct
import time
import tty
import sys
import select


TEAM_NAME = "Gucci-Manes"
TEAM_NAME_LEN = len(TEAM_NAME)
HEADER = 64
PORT = 13117
CLIENT_NAME = "localhost"#gethostbyname(gethostname())
CLIENT_ADDR = (CLIENT_NAME, PORT)
UDP_COOKIE = 0xfeedbeef
OFFER_CODE = 0x2
UDP_MSG_LEN = 7
FORMAT = 'utf-8'
TIMEOUT = 0.0#0.0125

def main():
    while True:
        print("--------------------- CLIENT RUNNING ---------------------------")
        (srv_ip, srv_port) = look_for_server()
        cnn = connect_to_server(srv_ip,srv_port)
        if cnn == None:
            continue
        play_game(cnn)


def look_for_server():
    try:
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind(CLIENT_ADDR)
        while True:
            data, (src_ip,src_port) = sock.recvfrom(4096)
            if data:
                cookie, code, srv_port = struct.unpack('!Ibh', data[:UDP_MSG_LEN])
                #print(f"\tfrom: {(src_ip,src_port)}\n\tcookie: {cookie}\n\tcode: {code}\n\tsrv_port: {srv_port}" )
                if cookie == UDP_COOKIE and code == OFFER_CODE:
                    print("found server - closing client UDP socket")
                    sock.close()
                    return (src_ip, srv_port)
    except:
        print("couldnt bind to port - closing client UDP socket")
        sock.close()
        return ("bad server",0)

def play_game(cnn):
    try:
        send_msg(cnn, TEAM_NAME+"\n")
        cnn.settimeout(TIMEOUT)
        tty.setcbreak(sys.stdin)
        while True:
            c = get_char()
            if len(c):
                #print(f"read: {c}")
                if not send_char(cnn,c):
                    break
            recv_and_print(cnn)
    except:
        x=1
    finally:
        cnn.close()


def connect_to_server(srv_ip, srv_port):
    try:
        srv_adrs = (srv_ip,srv_port)
        cnn = socket(AF_INET, SOCK_STREAM)
        cnn.connect(srv_adrs) #FAILS on second game
        print("connected!")
        return cnn
    except Exception as e:
        print("failed to connect to server")
        cnn.close()
        return None


def get_char():
    c = ""
    if select.select([sys.stdin],[],[],.25)[0]:
        c = sys.stdin.read(1)
    return c

def send_msg(cnn,msg):
    msg_bytes = struct.pack(f"! {len(msg)}s",msg.encode())
    cnn.send(msg_bytes)

def send_char(cnn, c):
    try:
        msg_bytes = struct.pack(f"! 1s",(""+c).encode())
        cnn.send(msg_bytes)
        return True
    except Exception as e: #timeout as e:
        print("--send failed:")
        print(e)
        return False

def recv_and_print(cnn):
    try:
        msg = cnn.recv(2048).decode(FORMAT)
        if len(msg):
            print("read from sock: "+ msg)
    finally:
        return

if __name__ == "__main__":
    main()