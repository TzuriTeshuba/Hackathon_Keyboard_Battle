from scapy.all import *

PORT = 13117
class Client:
    def __init__(self, team_name):
        self.team_name = team_name
        self.age = 2

def main():
    if True:
        look_for_server()
        #connect_to_server()
        #play_game()

def look_for_server():
    print("looking for server")
    my_ip = get_if_addr(get_working_if())
    print("my ip: "+my_ip)
    sniff(filter = 'dst port 13117',store=False, prn=look_callback)#filter = 'dst port 13117', 

def look_callback(packet):
    if packet.haslayer(Raw):
        print(packet[Raw].load)

def connect_to_server(ip,port):
    print("connecting to server")

def play_game():
    print("playing game")

if __name__ == "__main__":
    main()