from socket import *
import struct
import time
import tty
import sys
import select


TEAM_NAME = "Not You"
PORT = 13117
CLIENT_NAME = "localhost"#gethostbyname(gethostname())
CLIENT_ADDR = (CLIENT_NAME, PORT)
UDP_COOKIE = 0xfeedbeef
OFFER_CODE = 0x2
UDP_MSG_LEN = 7
FORMAT = 'utf-8'
TIMEOUT = 0.0
INACTIVE_ITERS_TOLERANCE = 100000
BAD_IP = "Bad IP" 

### COLORS ###
COLOR_RED = "red"
COLOR_GREEN = "green"
COLOR_YELLOW = "yellow"
COLOR_BLUE = "blue"
COLOR_DEFUALT = "default"

COLORS = {
    COLOR_RED:"\u001b[31m",
    COLOR_GREEN:"\u001b[32m",
    COLOR_YELLOW:"\u001b[33m",
    COLOR_BLUE:"\u001b[34m",
    COLOR_DEFUALT:"\u001b[0m"
    }

def print_color(clr, msg):
    print(COLORS[clr]+msg+COLORS[COLOR_DEFUALT])

def main():
    while True:
        print_color(COLOR_GREEN,"--------------------- CLIENT RUNNING ---------------------------")
        print_color(COLOR_GREEN,"Client started, listening for offer requests...")
        (srv_ip, srv_port) = look_for_server()
        if srv_ip == None:
            continue
        cnn = connect_to_server(srv_ip,srv_port)
        if cnn == None:
            continue
        play_game(cnn)

def try_udp_bind():
    while True:
        sock = socket(AF_INET, SOCK_DGRAM)
        try:
            sock.bind(CLIENT_ADDR)
            return 
        except:
            sock.close()
            print_color(COLOR_RED,"failed udp connect. trying again...")


def look_for_server():
    bytes_by_addr = {}
    try:
        sock = socket(AF_INET, SOCK_DGRAM,IPPROTO_UDP)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.bind(CLIENT_ADDR)#TODO: handle exception!!
        while True:
            #TODO: handle (1) len(data) < 7 bytes, (2)  un/packing data raise exception
            data, (src_ip,src_port) = sock.recvfrom(UDP_MSG_LEN)#TODO: get all bytes, can raise exception?
            l = len(data)
            print_color(COLOR_BLUE, f"UDP read {l} from ({src_ip},{src_port})" )
            print_color(COLOR_YELLOW, f"({src_ip},{src_port})")
            if len(data) >= UDP_MSG_LEN:
                cookie, code, srv_port = struct.unpack('!Ibh', data[:UDP_MSG_LEN])
                #print(f"\tfrom: {(src_ip,src_port)}\n\tcookie: {cookie}\n\tcode: {code}\n\tsrv_port: {srv_port}" )
                if cookie == UDP_COOKIE and code == OFFER_CODE:
                    sock.close()
                    return (src_ip, srv_port)
    except Exception as e:
        print_color(COLOR_RED, str(e))
        print_color(COLOR_RED,"couldnt bind to port - closing client UDP socket")
        sock.close()
        return None

def connect_to_server(srv_ip, srv_port):
    print_color(COLOR_GREEN,f"received offer from {srv_ip}, attempting to connect...")
    try:
        srv_adrs = (srv_ip,srv_port)
        cnn = socket(AF_INET, SOCK_STREAM)#TODO: filter message types?
        cnn.connect(srv_adrs) 
        print_color(COLOR_GREEN,"connected!")
        return cnn
    except Exception as e:
        print_color(COLOR_RED,"failed to connect to server")
        cnn.close()
        return None

def play_game(cnn):
    print_color(COLOR_GREEN, "Playing game")
    try:
        send_msg(cnn, TEAM_NAME+"\n")
        cnn.settimeout(TIMEOUT)
        tty.setcbreak(sys.stdin)
        #sys.stdin.flush()
        while True:
            if not recv_and_print(cnn):
                print_color(COLOR_GREEN, "The server closed the connection, game over")
                break
            c = get_char()
            if len(c) and (not send_char(cnn,c)):
                break
    except Exception as e:
        print_color(COLOR_RED,"\n--------\nin play_game:\n"+str(e))
    finally:
        cnn.close()


def get_char():
    c = ""
    if select.select([sys.stdin],[],[],0)[0]:
        c = sys.stdin.read(1)
    return c

def send_msg(cnn,msg):#TODO: handle failure like in send_char
    try:
        msg_bytes = struct.pack(f"! {len(msg)}s",msg.encode())
        cnn.send(msg_bytes)
    except:
        return False
def send_char(cnn, c):#TODO: improve effeciency
    try:
        msg_bytes = c.encode(FORMAT)
        #msg_bytes = struct.pack(f"! 1s",(""+c).encode())
        cnn.send(msg_bytes)
        return True
    except:
        return False

def recv_and_print(cnn):
    msg = ""
    try:
        msg_bytes = cnn.recv(4096)
        msg = msg_bytes.decode(FORMAT)       
        if len(msg):#got some bytes
            print_color(COLOR_YELLOW,"read from sock:\n"+ msg)
            return True
        else:
            return False
    except Exception as e:
        return True


if __name__ == "__main__":
    main()