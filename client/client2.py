from socket import *
import struct
import time
import threading
import tty
import sys


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
TIMEOUT = 0.0125

def main():
    while True:
        print("client running")
        (srv_ip, srv_port) = look_for_server()
        connect_to_server(srv_ip,srv_port)
        #print(threading.enumerate())
        print("Game is officially over")


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

def connect_to_server(srv_ip, srv_port):
    try:
        ###Send Team Name
        srv_adrs = (srv_ip,srv_port)
        print(f"connecting to server at ip: {srv_ip} port: {srv_port}")
        cnn = socket(AF_INET, SOCK_STREAM)
        cnn.connect(srv_adrs) #FAILS on second game
        print("connected!")
        send_msg(cnn, TEAM_NAME+"\n")
        ###get start/roster message
        print(cnn.recv(2048).decode(FORMAT))
        ###send chars
        cnn.settimeout(TIMEOUT)
        tty.setcbreak(sys.stdin)
        while True:
            c = sys.stdin.read(1)          
            send_char(cnn,c)
            recv_and_print(cnn)
    except Exception as e:
        print(e)
    finally:
        cnn.setblocking(True)
        recv_and_print(cnn)
        print("closing TCP connection")
        cnn.close()
        #cnn.detach()
        #cnn.shutdown(SHUT_RDWR)

def send_msg(cnn,msg):
    msg_bytes = struct.pack(f"! {len(msg)}s",msg.encode())
    cnn.send(msg_bytes)


def send_char(cnn, c):
    try:
        msg_bytes = struct.pack(f"! 1s",(""+c).encode())
        cnn.send(msg_bytes)
    finally:
        return

def recv_and_print(cnn):
    try:
        print(cnn.recv(2048).decode(FORMAT))
    finally:
        return

if __name__ == "__main__":
    main()