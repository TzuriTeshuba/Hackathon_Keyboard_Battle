from socket import *
import struct
import time

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

def main():
    print("client running")
    (srv_ip, srv_port) = look_for_server()
    connect_to_server(srv_ip,srv_port)


def look_for_server():
    try:
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind(CLIENT_ADDR)
        while True:
            data, (src_ip,src_port) = sock.recvfrom(4096)
            print(f"got some data: {data}")
            if data:
                cookie, code, srv_port = struct.unpack('!Ibh', data[:UDP_MSG_LEN])
                print(f"\tfrom: {(src_ip,src_port)}\n\tcookie: {cookie}\n\tcode: {code}\n\tsrv_port: {srv_port}" )
                if cookie == UDP_COOKIE and code == OFFER_CODE:
                    sock.close()
                    return (src_ip, srv_port)
    except:
        print("closing client UDP socket")
        sock.close()
        return ("bad server",0)

def connect_to_server(srv_ip, srv_port):
    try:
        ###Send Team Name
        srv_adrs = (srv_ip,srv_port)
        print(f"connecting to server at ip: {srv_ip} port: {srv_port}")
        client = socket(AF_INET, SOCK_STREAM)
        client.connect(srv_adrs)
        print("connected!")
        msg_bytes = struct.pack(f"! {TEAM_NAME_LEN+1}s",(TEAM_NAME+"\n").encode())
        client.send(msg_bytes)
        ###get start/roster message
        print(client.recv(2048).decode(FORMAT))
    finally:
        time.sleep(15)
        print("closing TCP connection")
        client.close()

if __name__ == "__main__":
    main()