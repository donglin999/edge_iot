# -*- coding: utf-8 -*-
import socket
import time
import pandas as pd
import os

interval = 2

client_PORT = 8567
server_PORT = 20108

curPath = os.path.dirname(os.path.realpath(__file__))
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

address = ("192.168.99.254", client_PORT)
server_addr=("192.168.99.68", server_PORT)
server_socket.bind(address)
server_socket.settimeout(1)

if __name__ == '__main__':
    while True:
        file_time = time.strftime("%Y%m%d%H", time.localtime())
        dirs = os.path.join(curPath, 'test_data/')
        file_name = os.path.join(dirs, file_time + '.csv')

        if not os.path.exists(file_name):
            name_list = [{'speed_vx': 'x轴振动速度', 'speed_vy': 'y轴振动速度', 'speed_vz': 'z轴振动速度',
                          'angle_vx': 'x轴振动角度', 'angle_vy': 'y轴振动角度', 'angle_vz': 'z轴振动角度',
                          'distance_vx': 'x轴振动位移', 'distance_vy': 'y轴振动位移', 'distance_vz': 'z轴振动位移',
                          'fs_vx': 'x轴振动频率', 'fs_vy': 'y轴振动频率', 'fs_vz': 'z轴振动频率', 'temp': '温度',
                          'electric_current': '电流'}]
            #pd.DataFrame(name_list).to_csv(file_name, index=False, mode='a', header=False)

        try:
            data = {}
            #振动速度
            vib_msg = bytes.fromhex('6803003A00032CFF')

            #电流
            msg = bytes.fromhex('010300000001840A')
            
            
            server = client_socket.sendto(vib_msg, server_addr)
            receive_data, client = server_socket.recvfrom(1024)
            rec_data = receive_data.hex()
            print(rec_data)
            if '68' == rec_data[:2]:
                data['speed_vx'] = int(rec_data[6:10],16)/10
                data['speed_vy'] = int(rec_data[10:14], 16)/10
                data['speed_vz'] = int(rec_data[14:18],16)/10
            elif '01' == rec_data[:2]:
                data['electric_current'] = int(rec_data[6:10], 16) / 100
                
            server = client_socket.sendto(msg, server_addr)
            receive_data, client = server_socket.recvfrom(1024)
            
            rec_data = receive_data.hex()
            print(rec_data)
            if '68' == rec_data[:2]:
                data['speed_vx'] = int(rec_data[6:10],16)/10
                data['speed_vy'] = int(rec_data[10:14], 16)/10
                data['speed_vz'] = int(rec_data[14:18],16)/10
            elif '01' == rec_data[:2]:
                data['electric_current'] = int(rec_data[6:10], 16) / 100

            data_list = [data]

            #pd.DataFrame(data_list).to_csv(file_name, index=False, mode='a', header=False)
            print(data_list)
            time.sleep(interval)
        except socket.timeout:
            print("time out")