from scapy.all import *

NETWORK_PREFIX = "172."
DEV_NET_PREFIX = NETWORK_PREFIX+"1."
TEST_NET_PREFIX = NETWORK_PREFIX+"99."
LAST_NET_IP = 24
LOCAL_HOST = "127.0.0.1"
ELAD_IP = ""
CLIENT_PORT = 13117


def main():
    print("starting server")
    if True:
        wait_for_clients()
        play_game()

def sidework():
    print("sidework")


def wait_for_clients():
    my_ip = get_if_addr(get_working_if())
    print("my ip: "+my_ip)
    for i in range(0,50):
        sendp(IP(src=LOCAL_HOST, dst=LOCAL_HOST)/UDP(dport=CLIENT_PORT)/Raw(load = "hello tbaby hello tbaby hello tbaby hello tbaby hello tbaby"))
    print("Server started, listening on IP address "+my_ip)
    # for i in range(0,LAST_NET_IP+1):
    #     client_ip = DEV_NET_PREFIX+str(i)
    #     print("client ip: "+client_ip)
    #     send(IP(src=my_ip, dst=client_ip)/UDP()/"hello tbaby")


def play_game():
    print("playing game")

if __name__ == "__main__":
    main()