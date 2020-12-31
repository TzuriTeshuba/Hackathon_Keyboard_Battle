from socket import *
import scapy.arch
import struct
import time
import tty
import sys
import select
from colors import *
from exceptions import DisconnectException

#Network Constants
PORT = 13117
CLIENT_IP = scapy.arch.get_if_addr("eth1")
CLIENT_ADDR = (CLIENT_IP, PORT)

#Program Constants
TEAM_NAME = "Not You"
NAME_SUFFIX = "\n"
UDP_COOKIE = 0xfeedbeef
OFFER_CODE = 0x2
UDP_MSG_LEN = 7
UDP_PACK_FORMAT = '!Ibh'
UTF_8_FORMAT = 'utf-8'
TIMEOUT = 0.0
 

# forever - looks for server, connects, and plays game until server disconnects
def main():
    while True:
        print_color(COLOR_GREEN,"Client started, listening for offer requests...")
        (srv_ip, srv_port) = look_for_server()
        if srv_ip == None:
            continue
        cnn = connect_to_server(srv_ip,srv_port)
        if cnn == None:
            continue
        play_game(cnn)


# binds UDP socket and listens for offer messages from servers
# if succeeds @returns the server IP and port it is listening on
# if fails, sleeps one second and return (None, 0)
# None -> (string | None) * int
def look_for_server():
    try:
        sock = socket(AF_INET, SOCK_DGRAM,IPPROTO_UDP)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(CLIENT_ADDR)
        while True:
            data, (src_ip,src_port) = sock.recvfrom(UDP_MSG_LEN)
            l = len(data)
            if len(data) >= UDP_MSG_LEN:
                cookie, code, srv_port = struct.unpack(UDP_PACK_FORMAT, data[:UDP_MSG_LEN])
                if cookie == UDP_COOKIE and code == OFFER_CODE:
                    sock.close()
                    return (src_ip, srv_port)
    except Exception as e:
        print_color(COLOR_RED, str(e))
        print_color(COLOR_RED,"couldnt bind to port - closing client UDP socket, trying again in 1 sec")
        sock.close()
        time.sleep(1)
        return (None, 0)

# connects (TCP) to address at (@arv_ip, @srv_port)
# if succesful @returns the connection socket
# if fails @returns None
# string * int -> socket | None
def connect_to_server(srv_ip, srv_port):
    print_color(COLOR_GREEN,f"received offer from {srv_ip}, attempting to connect...")
    try:
        srv_adrs = (srv_ip,srv_port)
        cnn = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        cnn.connect(srv_adrs) 
        return cnn
    except Exception as e:
        print_color(COLOR_RED,"failed to connect to server")
        cnn.close()
        return None

# (1) sets socket to non-blocking
# (2) sends team name to server @cnn
# (3) until server disconnects, non-blokingly receives data from @cnn and keyboard
#     and sends data from keyboard to @cnn
# socket -> None
def play_game(cnn):
    try:
        cnn.settimeout(TIMEOUT)
        send_msg(cnn, TEAM_NAME+NAME_SUFFIX)
        tty.setcbreak(sys.stdin)#receive from keyboard on press (without enter)
        while True:
            recv_and_print(cnn)            
            c = get_char()
            if len(c):
                send_char(cnn,c)                
    except DisconnectException:
        print_color(COLOR_GREEN, "the server has closed the connection. game over.")            
    except Exception as e:
        pass
    finally:
        cnn.close()

# non-blockingly @returns a character from the keyboard if a key was pressed
# @returns "" if no key was pressed
# None -> string
def get_char():
    c = ""
    if select.select([sys.stdin],[],[],0)[0]:
        c = sys.stdin.read(1)
    return c

# sends @msg to @cnn
# raises DisconnectException if @cnn has disconnected
# socket * string -> None
def send_msg(cnn,msg):
    try:
        msg_bytes = struct.pack(f"! {len(msg)}s",msg.encode())
        cnn.send(msg_bytes)
    except:
        raise DisconnectException

# sends @c to @cnn
# raises DisconnectException if @cnn has disconnected
# same as send_msg but more efficient for single chars
# socket * string -> None
def send_char(cnn, c):
    try:
        msg_bytes = c.encode(UTF_8_FORMAT)
        cnn.send(msg_bytes)
    except:
        raise DisconnectException

# receives data from @cnn and prints it on screen in yellow
# raises DisconnectException if @cnn has disconnected
# socket -> None
def recv_and_print(cnn):
    msg = ""
    try:
        msg_bytes = cnn.recv(1024)
        msg = msg_bytes.decode(UTF_8_FORMAT)       
        if len(msg):
            print_color(COLOR_YELLOW,msg)
            return
    except Exception as e:
        return
    raise DisconnectException


if __name__ == "__main__":
    main()