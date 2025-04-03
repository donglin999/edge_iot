import pandas as pd
from pandas import DataFrame
import numpy as np
from packages.write_influx import InfluxClient
from packages.HslCommunication import MelsecMcNet


def temp_change_speed(temp_data: DataFrame):
    """1st column of temp_data is [time],2nd column is [temp_value]"""
    if temp_data.shape[1] == 2 and temp_data.shape[0] > 1:
        df = pd.to_datetime(temp_data.iloc[:, 0])
        df = df.astype(int) / 10 ** 9
        x = df.values
        y = temp_data.iloc[:, 1].values
        y = y.astype(np.float)
        slope = np.polyfit(x, y, 1)
        return slope[0]
    else:
        return 0.0


def get_data_history(query_str: str, header_info: list, ip: str, port: int, my_token: str, my_org: str, my_bucket: str):
    influx_query = InfluxClient(ip, port, my_token, my_org, my_bucket)
    data_frame = influx_query.query_data_frame(query_str, header_info)
    return data_frame


# 磨削状态确认
# def plc_working_mode(plc_ip, plc_port, grinding_start_register):
#     cnt = 2
#     start_data = []
#     start_status = False
#     end_status = False
#     while True:
#         read_plc = MelsecMcNet(plc_ip, plc_port)
#         if not read_plc.ConnectServer().IsSuccess:
#             continue
#         else:
#             break
#     while cnt > 0:
#         while True:
#             if read_plc.ReadInt16(grinding_start_register).IsSuccess:
#                 start_data.append(read_plc.ReadInt16(grinding_start_register).Content)
#                 cnt += -1
#                 break
#             else:
#                 continue
#     read_plc.ConnectClose()
#     if start_data[0] == 0 and start_data[1] == 1:
#         start_status = True
#     if start_data[0] == 0 or start_data[1] == 0:
#         end_status = True
#     return start_status, end_status

def plc_working_mode(plc_ip, plc_port, grinding_start_register):
    cnt = 1
    start_data = []
    start_status = False
    end_status = False
    while True:
        read_plc = MelsecMcNet(plc_ip, plc_port)
        if not read_plc.ConnectServer().IsSuccess:
            print('read_plc init failed')
            continue
        else:
            break
    while cnt > 0:
        while True:
            if read_plc.ReadInt16(grinding_start_register).IsSuccess:
                start_data.append(read_plc.ReadInt16(grinding_start_register).Content)
                cnt += -1
                break
            else:
                continue
    read_plc.ConnectClose()
    if start_data[0] == 1:
        start_status = True
    if start_data[0] == 0:
        end_status = True
    return start_status, end_status


if __name__ == '__main__':
    pass
