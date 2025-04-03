import os
import time
import logging
import pandas as pd
from configparser import ConfigParser
from ctypes import *
from pandas import DataFrame
import numpy as np
import threading
from lib.packages.datacheck import vk_datacheck
from lib.packages.getVibrationFeature import getFeature
from lib.packages.harmonic import BPFI_harmonic, BPFO_harmonic
from lib.packages.write_influx import InfluxClient, Point
from settings import VKConfig, DevelopmentConfig

#######################################################
# 必须使用 64bit版本,linux 下使用.so文件
# Encoding:UTF-8
# 编译器： python 3.9 64bit version
# 
########################################################
class VKInflux:
    def __init__(self, data_addresses):
        self.TEMP_NUM = []
        self.VIB_NUM = []
        if data_addresses['protocol_type'] == "VK1":
            for k, v in data_addresses.items():
                if isinstance(v, dict):
                    self.TCP_PORT = v["source_port"]
                    for k1, v1 in v.items():
                        if isinstance(v1, dict):
                            if "振动" in v1['cn_name']:
                                self.VIB_NUM.append(int(v1['source_addr']))
                            else:
                                self.TEMP_NUM.append(int(v1['source_addr']))
        else:
            self.TCP_PORT = data_addresses["source_port"]
            for k, v in data_addresses.items():
                if isinstance(v, dict):
                    if "振动" in v['cn_name']:
                        self.VIB_NUM.append(int(v['source_addr']))
                    else:
                        self.TEMP_NUM.append(int(v['source_addr']))

        self.TRY_NUM = int(VKConfig().TRY_NUM)
        self.DAQ_SET = list(VKConfig().DAQ_SET)
        self.DAQ_NUM = int(VKConfig().DAQ_NUM)
        self.FS = int(VKConfig().FS)
        self.SAMPLE_NUM = int(VKConfig().SAMPLE_NUM)
        self.SENSOR_NUM = int(VKConfig().SENSOR_NUM)
        self.SAMPLE_PERIOD = int(VKConfig().SAMPLE_PERIOD)
        self.ADC = int(VKConfig().ADC)
        self.DAQ_MODE = int(VKConfig().DAQ_MODE)
        self.DATA_SAVE = int(VKConfig().DATA_SAVE)
        self.MACHINE_ID = str(VKConfig().MACHINE_ID_1)
        # VK通道数量
        self.CHANNEL_NUM = int(VKConfig().CHANNEL_NUM)

        self.data_addresses = data_addresses
        # vk70xnhdll = windll.LoadLibrary('./VK70xNMC_DAQ.dll')  # window系统下dll调用
        self.vk70xnhdll = cdll.LoadLibrary('/code/lib/libVK70XNMC_DAQ_SHARED.so')  # Linux系统下so动态链接库调用

        self.Server_TCPOpen = self.vk70xnhdll.Server_TCPOpen
        self.Server_TCPOpen.argtypes = [c_long]
        self.Server_TCPOpen.restypes = c_long

        self.Server_TCPClose = self.vk70xnhdll.Server_TCPClose
        self.Server_TCPClose.argtypes = [c_long]
        self.Server_TCPClose.restypes = c_long

        self.Server_Get_ConnectedClientNumbers = self.vk70xnhdll.Server_Get_ConnectedClientNumbers
        self.Server_Get_ConnectedClientNumbers.argtypes = [POINTER(c_long)]
        self.Server_Get_ConnectedClientNumbers.restypes = c_long

        self.VK70xNMC_StartSampling = self.vk70xnhdll.VK70xNMC_StartSampling
        self.VK70xNMC_StartSampling.argtypes = [c_long, c_long]
        self.VK70xNMC_StartSampling.restypes = c_long

        self.VK70xNMC_StopSampling = self.vk70xnhdll.VK70xNMC_StopSampling
        self.VK70xNMC_StopSampling.argtypes = [c_long]
        self.VK70xNMC_StopSampling.restypes = c_long

        self.VK70xNMC_Set_AdditionalFeature = self.vk70xnhdll.VK70xNMC_Set_AdditionalFeature
        self.VK70xNMC_Set_AdditionalFeature.argtypes = [c_long, c_long, c_long, c_double]
        self.VK70xNMC_Set_AdditionalFeature.restypes = c_long

        self.VK70xNMC_Initialize = self.vk70xnhdll.VK70xNMC_Initialize
        self.VK70xNMC_Initialize.argtypes = [c_int, c_int, c_int, c_int, c_int, POINTER(c_int)]
        self.VK70xNMC_Initialize.restypes = c_int

        self.VK70xNMC_GetOneChannel_WithIOStatus = self.vk70xnhdll.VK70xNMC_GetOneChannel_WithIOStatus
        self.VK70xNMC_GetOneChannel_WithIOStatus.argtypes = [c_long, c_long, POINTER(c_double), c_long, c_long]
        self.VK70xNMC_GetOneChannel_WithIOStatus.restypes = c_long

        self.VK70xNMC_GetFourChannel_WithIOStatus = self.vk70xnhdll.VK70xNMC_GetFourChannel_WithIOStatus
        self.VK70xNMC_GetFourChannel_WithIOStatus.argtypes = [c_long, POINTER(c_double), c_long, c_long]
        self.VK70xNMC_GetFourChannel_WithIOStatus.restypes = c_long

        self.VK70xNMC_GetAllChannel_WithIOStatus = self.vk70xnhdll.VK70xNMC_GetAllChannel_WithIOStatus
        self.VK70xNMC_GetAllChannel_WithIOStatus.argtypes = [c_long, POINTER(c_double), c_long, c_long]
        self.VK70xNMC_GetAllChannel_WithIOStatus.restypes = c_long

        self.VK70xNMC_GetOneChannel = self.vk70xnhdll.VK70xNMC_GetOneChannel
        self.VK70xNMC_GetOneChannel.argtypes = [c_long, c_long, POINTER(c_double), c_long]
        self.VK70xNMC_GetOneChannel.restypes = c_long

        self.VK70xNMC_GetFourChannel = self.vk70xnhdll.VK70xNMC_GetFourChannel
        self.VK70xNMC_GetFourChannel.argtypes = [c_long, POINTER(c_double), c_long]
        self.VK70xNMC_GetFourChannel.restypes = c_long

        self.VK70xNMC_GetAllChannel = self.vk70xnhdll.VK70xNMC_GetAllChannel
        self.VK70xNMC_GetAllChannel.argtypes = [c_long, POINTER(c_double), c_long]
        self.VK70xNMC_GetAllChannel.restypes = c_long

    # ======================================================================================
    def initial_collector(self):
        print(f"打开TCP服务器的{self.TCP_PORT}端口")
        ret = self.vk70xnhdll.Server_TCPOpen(self.TCP_PORT)  # 打开服务器(工控机)端口823
        connected_clientnum = c_long(0)
        if ret >= 0:
            # logging.info('VK702NH_1 waiting for connection...')
            print(f"TCP服务器{self.TCP_PORT}端口等待连接")
            klp = 1
            connect_cnt = 0
            while klp and connect_cnt < self.TRY_NUM:
                time.sleep(0.1)  # 延时100ms
                self.vk70xnhdll.Server_Get_ConnectedClientNumbers(byref(connected_clientnum))
                connect_cnt += 1
                # logging.info('VK702NH_1 number：{}'.format(connected_clientnum.value))
                print(f"TCP服务器{self.TCP_PORT}端口连接数量，{connected_clientnum.value}")
                if connected_clientnum.value > 0:
                    klp = 0  # 读取已连接的采集卡退出
            # ------------------------
            if connected_clientnum.value > 0:
                if self.CHANNEL_NUM == 4:
                    # logging.info('VK702NH_1 setting...')
                    print(f"开始设置")
                    para = (c_int * 12)()
                    # para[0-3]设置1-2/.../7-8的电压输入范围，para[4-11]为1-8通道IEPE开关，para[12]为外部IO4的触发方式
                    # 采样率
                    para[0] = 1000
                    print(f"设置采样频率，para[0]：{para[0]}")
                    # 参考电压
                    para[1] = 4
                    print(f"设置参考电压，para[1]：{para[1]}")
                    # 16bit精度或24bit精度
                    para[2] = 24
                    print(f"设置精度，para[2]：{para[2]}")
                    # n采样点数
                    para[3] = 10000
                    print(f"设置n采样点数，para[3]：{para[3]}")
                    # 设置通道1, 5，0：输入电压范围为 - 10V~10V，1输入电压范围为 - 5V5V，1：输入电压范围为 - 2.5V~2.5V，2：输入电压范围为 - 500mV~500mV
                    para[4] = 1
                    print(f"设置通道1, 5输入电压范围，para[4]：{para[4]}")
                    # 设置通道2, 6，0：输入电压范围为 - 10V~10V，1输入电压范围为 - 5V5V，1：输入电压范围为 - 2.5V~2.5V，2：输入电压范围为 - 500mV~500mV
                    para[5] = 1
                    print(f"设置通道2, 6输入电压范围，para[5]：{para[5]}")
                    # 设置通道3, 7，0：输入电压范围为 - 10V~10V，1输入电压范围为 - 5V5V，1：输入电压范围为 - 2.5V~2.5V，2：输入电压范围为 - 500mV~500mV
                    para[6] = 1
                    print(f"设置通道3, 7输入电压范围，para[6]：{para[6]}")
                    # 设置通道4, 8，0：输入电压范围为 - 10V~10V，1输入电压范围为 - 5V5V，1：输入电压范围为 - 2.5V~2.5V，2：输入电压范围为 - 500mV~500mV
                    para[7] = 1
                    print(f"设置通道4, 8输入电压范围，para[7]：{para[7]}")
                    # 设置通道1, 5，0：ADC模式，1：IEPE模式，2：电流模式
                    para[8] = 1
                    print(f"设置通道1, 5模式，para[8]：{para[8]}")
                    # 设置通道2, 6，0：ADC模式，1：IEPE模式，2：电流模式
                    para[9] = 1
                    print(f"设置通道2, 6模式，para[9]：{para[9]}")
                    # 设置通道3, 7，0：ADC模式，1：IEPE模式，2：电流模式
                    para[10] = 1
                    print(f"设置通道3, 7模式，para[10]：{para[10]}")
                    # 设置通道4, 8，0：ADC模式，1：IEPE模式，2：电流模式
                    para[11] = 1
                    print(f"设置通道4, 8模式，para[11]：{para[11]}")
                    ret_status = self.vk70xnhdll.VK70xNMC_InitializeAll(0, para, 12)

                else:
                    para = (c_int * 16)()
                    for i in range():
                        para[i] = 1
                    # DAQ_NUM为采集卡序号0-8范围，FS为采样率，SAMPLE_NUM为采样N点，SAMPLE_PERIOD为定时N采样间隔s，ADC为采样精度
                    ret_status = self.vk70xnhdll.VK70xNMC_Initialize(self.DAQ_NUM, self.FS, self.SAMPLE_NUM,self.SAMPLE_PERIOD, self.ADC, para)

                if ret_status < 0:
                    logging.error('VK702NH_1 setting error:{}'.format(ret_status))
                    print(f"设置报错：{ret_status}")
                    return "VK702NH_1_initialize_error"
                else:
                    logging.info('VK702NH_1 setting successful')
                    print(f"设置成功")
                    time.sleep(0.1)  # 延时100ms
                    # 0为采集卡序号0-8,0x01为连续采样模式，0x02为单次N点采样，0x21为定时进行一次N点采样
                    open_status = self.vk70xnhdll.VK70xNMC_StartSampling(self.DAQ_NUM, self.DAQ_MODE)
                    if open_status < 0:
                        logging.error('VK702NH_1 open error:{}'.format(open_status))
                        return "VK702NH_1_open_error"
                    else:
                        logging.info('VK702NH_1 open successful')
                        print(f"VK702NH开启成功")
                        return "initialized_successful"
            else:
                return "VK702NH_1_num_error"
        else:
            logging.error('Cannot open server, port may be not available')
            # cdll.unLoadLibrary('VK70xNMC_DAQ.dll')
            return "port_error"

    def start_collector(self):
        adc_buf = (c_double * self.CHANNEL_NUM * self.SAMPLE_NUM)()
        data_len = 0
        data_buffer = DataFrame()
        while data_len < self.SAMPLE_NUM:
            rd_len = self.vk70xnhdll.VK70xNMC_GetAllChannel(self.DAQ_NUM, cast(adc_buf,POINTER(c_double)),
                                                             self.SAMPLE_NUM)  # 读取 SAMPLE_NUM 点数据
            # print(f"读取{self.SAMPLE_NUM}点数据完成")
            if rd_len > 0:
                data = np.frombuffer(adc_buf)
                data = DataFrame(data.reshape(-1, self.CHANNEL_NUM))
                data = data.iloc[:rd_len, :]
                data_len += rd_len
                data_buffer = pd.concat([data_buffer, data], axis=0)
        data_buffer = data_buffer.iloc[:self.SAMPLE_NUM, :self.SENSOR_NUM]
        # print(f"收集data_buffer完成，data_buffer：{data_buffer}")
        '''
        # 如果/code/data.csv不存在则创建表
        if not os.path.exists("/code/data.csv"):
            data_buffer.to_csv("/code/data.csv", header=True, index=False)
        else:
            data_buffer.to_csv("/code/data.csv", mode='a', header=False, index=False)
        # 将数据存入/code/data.csv中
        data_buffer.to_csv("/code/data.csv", index=False)
        print("将data_buffer写入csv完成")
        '''

        return data_buffer

    def close_collector(self):
        time.sleep(0.2)  # 0.2 seconds
        self.vk70xnhdll.VK70xNMC_StopSampling(0)
        time.sleep(0.2)  # 0.2 seconds
        self.vk70xnhdll.Server_TCPClose(self.TCP_PORT)
        time.sleep(0.5)  # 0.5 seconds
        logging.info('close server')
        cdll.unLoadLibrary('libVK70xNMC_DAQ_SHARED.so')

    # influxDB 2.0 数据查询语句
    def query_code(self, temp_dic: dict, i: int):
        code = 'from(bucket:"' + self.INFLUX_BUCKET + '") ' \
                                                 '|> range(start: -10m) ' \
                                                 '|> limit(n: 10) ' \
                                                 '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: ' \
                                                 '"_value") ' \
                                                 '|> keep(columns: ["_time", "' + temp_dic[i] + '"])'
        return code

    # 2个相同健的字典的值字符串合并
    def merge_dicts(self, dict1, dict2):
        result = {}
        for key in dict1.keys() & dict2.keys():
            result[key] = str(dict1[key]) + "-" + str(dict2[key])
        return result

    # 注意此处的df没有考虑index_col，所以列是从0开始的，注意确认
    def feature_cal(self, df, fs, temp_num, vib_num):
        feature_list = {}
        for i in vib_num:
            # 速度均方根值，单位mm/s
            # feature_list[i] = getFeature(1E+2 * df.iloc[:, i].values, fs).get_vel_rms_filter()
            # 加速度冲击因子，无量纲
            # feature_list[i + 8] = getFeature(1E+2 * df.iloc[:, i].values, fs).get_acc_IM_raw()
            # 滤波加速度均方根，单位m/s**2
            feature_list[i + 16] = getFeature(1E+2 * df.iloc[:, i].values, fs).get_acc_rms_filter()
            # 包络峰值envelop_p,单位m/s**2
            # feature_list[i + 24] = getFeature(1E+2 * df.iloc[:, i].values, fs).get_envlope_peak()
            # 峭度KU，无量纲
            # feature_list[i + 32] = getFeature(1E+2 * df.iloc[:, i].values, fs).getKU(1E+2 * df.iloc[:, i].values)
            # 0通道一倍频速度幅值vel_1X , 单位mm/s
            # ifft = getFeature(1E+2 * df.iloc[:, 0].values, fs).integral(1E+2 * df.iloc[:, 0].values) * 1000
            # feature_list[i + 26] = calc_harmonic(ifft, fs,normal_rpm=1500)['harmonic_1']
            # feature_list[i + 27] = np.sum(list(BPFI_harmonic(ifft, fs, normal_rpm=1460, BPFI=5.946, rates=[1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 28] = np.sum(list(BPFO_harmonic(ifft, fs, normal_rpm=1460, BPFO=4.054, rates=[1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 29] = np.sum(list(BSF_harmonic(ifft,fs,normal_rpm=1460,BSF=5.094,rates=[ 0.5,1, 2, 3, 4, 5],window=0.02).values()))
            # 2通道一倍频速度幅值vel_1X , 单位mm/s
            # ifft = getFeature(1E+2 * df.iloc[:, 2].values, fs).integral(1E+2 * df.iloc[:, 2].values)*1000
            # feature_list[i + 30] = calc_harmonic(ifft, fs,normal_rpm=30)['harmonic_1']
            # feature_list[i + 31] = np.sum(list(BPFI_harmonic(ifft,fs,normal_rpm=1460,BPFI=5.946,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 32] = np.sum(list(BPFO_harmonic(ifft,fs,normal_rpm=1460,BPFO=4.054,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 33] = np.sum(list(BSF_harmonic(ifft,fs,normal_rpm=1460,BSF=5.094,rates=[ 0.5,1, 2, 3, 4, 5],window=0.02).values()))
            # 4通道一倍频速度幅值vel_1X , 单位mm/s
            # ifft = getFeature(1E+2 * df.iloc[:, 4].values, fs).integral(1E+2 * df.iloc[:, 4].values)*1000
            # feature_list[i + 34] = calc_harmonic(ifft, fs,normal_rpm=30)['harmonic_1']
            # feature_list[i + 35] = np.sum(list(BPFI_harmonic(ifft,fs,normal_rpm=1460,BPFI=5.946,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 36] = np.sum(list(BPFO_harmonic(ifft,fs,normal_rpm=1460,BPFO=4.054,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 37] = np.sum(list(BSF_harmonic(ifft,fs,normal_rpm=1460,BSF=5.094,rates=[ 0.5,1, 2, 3, 4, 5],window=0.02).values()))
            # 6通道一倍频速度幅值vel_1X , 单位mm/s
            # ifft = getFeature(1E+2 * df.iloc[:, 6].values, fs).integral(1E+2 * df.iloc[:, 6].values)*1000
            # feature_list[i + 38] = calc_harmonic(ifft, fs,normal_rpm=1500)['harmonic_1']
            # feature_list[i + 39] = np.sum(list(BPFI_harmonic(ifft,fs,normal_rpm=1460,BPFI=5.946,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 40] = np.sum(list(BPFO_harmonic(ifft,fs,normal_rpm=1460,BPFO=4.054,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 41] = np.sum(list(BSF_harmonic(ifft,fs,normal_rpm=1460,BSF=5.094,rates=[ 0.5,1, 2, 3, 4, 5],window=0.02).values()))
            # 7通道一倍频速度幅值vel_1X , 单位mm/s
            # ifft = getFeature(1E+2 * df.iloc[:, 7].values, fs).integral(1E+2 * df.iloc[:, 7].values)*1000
            # feature_list[i + 42] = calc_harmonic(ifft, fs,normal_rpm=1500)['harmonic_1']
            # feature_list[i + 43] = np.sum(list(BPFI_harmonic(ifft,fs,normal_rpm=1460,BPFI=5.946,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 44] = np.sum(list(BPFO_harmonic(ifft,fs,normal_rpm=1460,BPFO=4.054,rates=[ 1, 2, 3, 4, 5],window=0.02).values()))
            # feature_list[i + 45] = np.sum(list(BSF_harmonic(ifft,fs,normal_rpm=1460,BSF=5.094,rates=[ 0.5,1, 2, 3, 4, 5],window=0.02).values()))

        for i in temp_num:
            # 温度平均值，单位摄氏度
            feature_list[i] = 100 * (np.mean(df.iloc[:, i].values) - 0.5)
            # influxDB 2.0 数据查询语句
            # query_str = query_code(temp_dic, i)
            # 升温速度，单位摄氏度/s
            # feature_list[i + 8] = temp_change_speed(get_data_history(
            # query_str=query_str, header_info=["time", "temp_value"], ip=INFLUX_IP, port=INFLUX_PORT,
            # my_token=TOKEN, my_org=INFLUX_ORG, my_bucket=INFLUX_BUCKET))
        return feature_list

    # 振动温度数据采集程序入口
    def vk_influx(self, data_addresses):

        map_dict = {}
        device_a_tag = {}
        cn_name = {}
        device_name = {}
        if data_addresses['protocol_type'] == "VK1":
            for k, v in data_addresses.items():
                if isinstance(v, dict):
                    for k1, v1 in v.items():
                        if isinstance(v1, dict):
                            map_dict[v1["source_addr"]] = k1
                            device_a_tag[v1["source_addr"]] = v["device_a_tag"]
                            cn_name[v1["source_addr"]] = v1["cn_name"]
                            device_name[v1["source_addr"]] = v["device_name"]
        else:
            for k, v in data_addresses.items():
                if isinstance(v, dict):
                    map_dict[v["source_addr"]] = k
                    device_a_tag[v["source_addr"]] = data_addresses["device_a_tag"]
                    cn_name[v["source_addr"]] = v["cn_name"]
                    device_name[v["source_addr"]] = data_addresses["device_name"]

        print(f"map_dict:{map_dict}")
        print(f"device_a_tag:{device_a_tag}")
        print(f"cn_name:{cn_name}")
        print(f"device_name:{device_name}")
        vt_write_influx = InfluxClient(ip=DevelopmentConfig().INFLUXDB_HOST, port=DevelopmentConfig().INFLUXDB_PORT,
                                       my_token=DevelopmentConfig().INFLUXDB_TOKEN,
                                       my_org=DevelopmentConfig().INFLUXDB_ORG,
                                       my_bucket=DevelopmentConfig().INFLUXDB_BUCKET)
        ret_code = ""
        # while ret_code != "initialized_successful":
        if ret_code != "initialized_successful":
            ret_code = self.initial_collector()
        cnt = 0
        points = []
        while True:
            vib_temp_data = self.start_collector()
            vt_dict = {}
            cn_name_dict = {}
            if vk_datacheck(vib_temp_data):
                cnt += 1
                print(f"self.TEMP_NUM：{self.TEMP_NUM}，self.VIB_NUM：{self.VIB_NUM}")
                features = self.feature_cal(vib_temp_data, self.FS, self.TEMP_NUM, self.VIB_NUM)
                print(f"计算特征值成功，类型：{type(features)}，features：{features}")
                for i in self.TEMP_NUM:
                    # print(f"map_dict[str(i)]:{map_dict[str(i)]}")
                    # print(f"features[str(i)]:{features[str(i)]}")
                    vt_dict[map_dict[i] + "_mean"] = round(features[i], 2)
                    cn_name_dict[map_dict[i] + "_mean"] = cn_name[i] + "平均值"
                    # vt_dict[map_dict[str(i)] + "-changing_speed"] = round(features[str(i + 8)], 2)
                for i in self.VIB_NUM:
                    # print(f"map_dict[str(i)]:{map_dict[str(i)]}")
                    # print(f"features[str(i + 16)]:{features[str(i + 16)]}")
                    # vt_dict[map_dict[str(i)] + "_Velocity_rms"] = round(features[str(i)], 2)
                    # vt_dict[map_dict[str(i)] + "-im_factor"] = round(features[str(i + 8)], 2)
                    vt_dict[map_dict[i] + "-acc_rms"] = round(features[i + 16], 2)
                    cn_name_dict[map_dict[i] + "-acc_rms"] = cn_name[i] + "加速度均方根"
                    # vt_dict[map_dict[str(i)] + "_Envelope_p"] = round(features[str(i + 24)], 2)
                    # vt_dict[map_dict[str(i)] + "-KU"] = round(features[str(i + 32)], 2)
                    # vt_dict[map_dict[i] + "_BPFI"] = round(features[i + 27], 2)
                    # cn_name_dict[map_dict[i] + "_BPFI"] = cn_name[i] + "内圈故障特征频率"
                    # vt_dict[map_dict[i] + "_BPFO"] = round(features[i + 28], 2)
                    # cn_name_dict[map_dict[i] + "_BPFO"] = cn_name[i] + "外圈故障特征频率"
                print(f"vt_dict：{vt_dict}")

                for field, value in vt_dict.items():
                    point = Point(device_a_tag[i]) \
                        .time(time.time_ns())
                    point = point.tag("device_a_tag", device_a_tag[i])
                    point = point.tag("data_source", "vk" + str(self.TCP_PORT))
                    point = point.tag("device_name", device_name[i])
                    point = point.tag("kafka_position", "measures")
                    print(f"field：{field}")
                    point = point.tag("cn_name", cn_name_dict[field])
                    print(f"添加标签1成功，cn_name: {cn_name_dict[field]}")

                    point = point.field(field, value)
                    # print(f"数据库行数据创建成功point:{point}")
                    points.append(point)

                # print(f"len(points)：{len(points)}")
                if len(points) >= 24:
                    # 创建一个线程来处理数据
                    thread_args = {"data": points}
                    thread = threading.Thread(target=vt_write_influx.write_client, kwargs=thread_args)
                    # 启动线程
                    thread.start()
                    points = []
                    print(f"数据写入数据库成功")
            else:
                logging.warning("data check failed")

        try:
            pass
        except Exception as e:
            logging.exception(e)
            print(f"启动函数报错{e}")

if __name__ == '__main__':
    data_addresses = ""
    vk = VKInflux(data_addresses)
    vk.vk_influx()
