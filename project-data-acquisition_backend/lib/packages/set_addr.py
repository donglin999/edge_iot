# -*- coding: utf-8 -*-
import socket
import time
import os

client_PORT = 8567
server_PORT = 20108

curPath = os.path.dirname(os.path.realpath(__file__))
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

address = ("10.177.152.66", client_PORT)
server_addr=("10.177.104.251", server_PORT)
server_socket.bind(address)
server_socket.settimeout(1)

if __name__ == '__main__':
    msg = bytes.fromhex('50060069B58822A1')
    server = client_socket.sendto(msg, server_addr)
    receive_data, client = server_socket.recvfrom(1024)
    rec_data = receive_data.hex()
    print(rec_data)
    time.sleep(1)
    msg = bytes.fromhex('5006001A0074A5AB')
    server = client_socket.sendto(msg, server_addr)
    receive_data, client = server_socket.recvfrom(1024)
    rec_data = receive_data.hex()
    print(rec_data)
    time.sleep(1)
    msg = bytes.fromhex('500600000000844B')
    server = client_socket.sendto(msg, server_addr)
    receive_data, client = server_socket.recvfrom(1024)
    rec_data = receive_data.hex()
    print(rec_data)
