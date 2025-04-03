# -*- coding: utf-8 -*-
"""
by ningkq1 2024/12/3
"""
import os
import logging
import time
import queue
from datetime import datetime
from ctypes import *
from abc import ABC, abstractmethod
from queue import Queue
import pandas as pd
import numpy as np
from settings import VK701NDCConfig
from utils.baseLogger import Log
from utils.util import dataframe_apply, calcu_feature, RunInNewThread

# from utils import dataframe_apply, calcu_feature, RunInNewThread

PATH = os.path.dirname(__file__)

# 动态库默认在当前目录
libVK70XNMC_DAQ_SHARED = os.path.join(PATH, "/code/lib/libVK70XNMC_DAQ_SHARED.so")
libVK702NHMC_DAQ_SHARED = os.path.join(PATH, "/code/lib/libVK702NHMC_DAQ_SHARED.so")
libVK70XNMC_DAQ_SHARED = os.path.join(PATH, "/code/lib/centos7/libVK70XNMC_DAQ_SHARED.so")
libVK702NHMC_DAQ_SHARED = os.path.join(PATH, "/code/lib/centos7/libVK702NHMC_DAQ_SHARED.so")



class VKConfigBase:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def update(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return f"{self.__dict__}"

    def initialize_all_para(self):
        '''
        根据接口要求初始化参数
        '''
        para = (c_int * 12)()
        for i, item in enumerate([self.fs, self.voltage, self.accuracy, self.samplenumber] + self.params):
            para[i] = item
        return para


class VKConfig:
    '''
    '''

    def __init__(self, configdict):
        self.vkclient = {}
        self.parse(configdict)

    def parse(self, configdict):
        for id, config in configdict.items():
            if id > 7:
                continue
            self.vkclient[id] = VKConfigBase(**config)
            Log().printInfo(f'采集卡{id}加载配置完成!')

    def get(self, id):
        if id in self.vkclient:
            return self.vkclient[id]
        return None

    def __contains__(self, item):
        return item in self.vkclient


class VKBase(ABC):
    port: int = 8234
    Buffer: dict = {}

    def __init__(self,data_addresses):
        self.Server_TCPOpen = None
        self.Server_Get_ConnectedClientNumbers = None
        self.Server_Get_ConnectedClientHandle = None
        self.StartSampling = None
        self.GetAllChannel = None
        self.config = VKConfig({})
        self.dll_init()
        self.outputque = Queue(100)

        self.save_enable = False
        self.save_path = os.path.join(PATH, 'data')
        self.saveque = Queue(100)

    @abstractmethod
    def dll_init(self):
        pass

    @abstractmethod
    def load_client_cfg(self):
        pass

    def get(self):
        try:
            data = self.outputque.get(timeout=10)
            return data
        except queue.Empty:
            Log().printError("VK服务输出队列为空！")
            return None

    @RunInNewThread()
    def server_init(self):
        '''
        vk 服务端初始化一般分为以下几个步骤
        step1: load_client_cfg - 加载采集卡设置
        step2: Server_TCPOpen - 打开服务端监听端口
        step3: Server_Get_ConnectedClientNumbers - 获得连接上服务器的采集卡
        step4: Server_Get_ConnectedClientHandle - 通过采集卡id获取采集卡的ip
        step5: client_process - 采集和数据处理线程
        '''
        self.load_client_cfg()
        if self.save_enable:
            self.saving_original_data()
        ret = self.Server_TCPOpen(self.port)
        if ret >= 0:
            Log().printInfo(f"{self.__class__.__name__} 成功在端口{self.port}开启监听服务")
            connected_clientnum = c_long(0)
            while connected_clientnum.value < 0:
                ret = self.Server_Get_ConnectedClientNumbers(byref(connected_clientnum))
                if ret >= 0:
                    Log().printInfo(f"{self.__class__.__name__} 服务器打开成功，采集卡连接数量:{connected_clientnum.value}")
                    break
                elif ret == -11:
                    Log().printInfo(f"{self.__class__.__name__} 服务器未打开")
                elif ret == -12:
                    Log().printInfo(f"{self.__class__.__name__} 无采集卡连接到服务器")
                else:
                    Log().printInfo(f"{self.__class__.__name__} 异常退出:{ret}")
                time.sleep(0.1)
            clienthandle = c_int(0)
            clientip = create_string_buffer(128)
            started_client = set()
            while True:
                for i in range(8):
                    if i not in self.config:
                        # 没有配置的客户端不做处理
                        continue
                    ret = self.Server_Get_ConnectedClientHandle(i, byref(clienthandle), clientip)
                    if ret >= 0 and i not in started_client:
                        started_client.add(i)
                        Log().printInfo(
                            f"采集卡id：{i},采集卡IP：{clientip.value.decode('utf-8')},采集卡连接句柄：{clienthandle.value}")
                        client_cfg = self.config.get(i)
                        client_cfg.id = i
                        client_cfg.ip = clientip.value.decode('utf-8')
                        self.client_process(client_cfg)
                        time.sleep(1)
                    elif ret == -11:
                        Log().printError(f"采集卡ID：{i}服务器未打开！")
                    elif ret == -12:
                        Log().printError(f"请求的采集卡ID：{i}索引号错误！")
                    elif ret == -13:
                        pass
                        # logger.error(f"请求的采集卡ID：{i}未连接或不存在！")
                    else:
                        pass
                time.sleep(5)
        elif ret == -13:
            Log().printError(f"{self.__class__.__name__} 服务器端口已被占用！")
        else:
            Log().printError(f"{self.__class__.__name__} 服务器启动异常！")

    @RunInNewThread()
    def client_process(self, client_cfg: VKConfigBase = None):
        '''处理采集卡客户端连接'''
        para = client_cfg.initialize_all_para()
        Log().printInfo(
            f'采集卡{client_cfg.id} para:{",".join(map(lambda a: str(a), para))} DAQ_MODE:{client_cfg.DAQ_MODE}, channel_num:{client_cfg.channel_num},fs:{client_cfg.fs}')
        while True:
            ret = self.initialize_all(client_cfg.id, para, len(para))
            time.sleep(0.1)
            if ret >= 0:
                Log().printInfo(f" 采集卡ID:{client_cfg.id} 初始化成功！")
                break
        while True:
            ret = self.StartSampling(client_cfg.id, client_cfg.DAQ_MODE)
            time.sleep(0.1)
            if ret >= 0:
                Log().printInfo(f"采集卡ID:{client_cfg.id}, 开始采集！")
                break
        adc_buf = (c_double * client_cfg.channel_num * client_cfg.samplenumber)()
        while True:
            data_buffer = pd.DataFrame()
            data_len = 0
            while data_len < client_cfg.samplenumber:
                rd_len = self.GetAllChannel(client_cfg.id, cast(adc_buf, POINTER(c_double)), client_cfg.samplenumber)
                if rd_len > 0:
                    data = np.frombuffer(adc_buf)
                    data = pd.DataFrame(data.reshape(-1, client_cfg.channel_num))
                    data = data.iloc[:rd_len, :]
                    data_buffer = pd.concat([data_buffer, data], axis=0)
                    data_len += rd_len
                else:
                    Log().printInfo(f"采集卡ID:{client_cfg.id} 数据读入长度为{rd_len}")
            original_data = data_buffer.iloc[:client_cfg.fs, :]
            # 根据传感器配置转换原始电信号数据
            physical_data = dataframe_apply(original_data, client_cfg.sensor_conversion_info)
            # 是否保存原始数据
            if self.save_enable:
                self.saveque.put((client_cfg.id, physical_data), block=False)
            # 根据配置计算特征
            feature_data = calcu_feature(physical_data, client_cfg)
            # 特征计算结果同步到下游模块
            self.outputque.put((client_cfg.id, feature_data), block=False)

    @RunInNewThread()
    def saving_original_data(self):
        try:
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)
                for i in range(8):
                    os.makedirs(os.path.join(self.save_path, str(i)))  # , exist_ok=True
        except Exception as e:
            Log().printError(f"创建保存路径失败：{e}")
        while True:
            try:
                data = self.saveque.get()
                if isinstance(data[1], pd.DataFrame):
                    filetemp = os.path.join(self.save_path, str(data[0]),
                                            datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '.csv')
                    data[1].to_csv(filetemp, index=False)
            except Exception as e:
                Log().printError(f"保存数据出错：{e}")
                time.sleep(0.1)
                pass


class VK701NDC(VKBase):
    def load_client_cfg(self):
        '''根据采集卡连接id加载采集卡配置设定'''
        self.config = VKConfig(VK701NDCConfig().vkconfig)
        self.save_enable = VK701NDCConfig().save_enable
        # self.save_path = config.save_path

    def dll_init(self):
        self.vkdll = cdll.LoadLibrary(libVK70XNMC_DAQ_SHARED)
        self.Server_TCPOpen = self.vkdll.Server_TCPOpen
        self.Server_TCPOpen.argtypes = [c_long]
        self.Server_TCPOpen.restypes = c_long
        # 关闭服务
        self.Server_TCPClose = self.vkdll.Server_TCPClose
        self.Server_TCPClose.argtypes = [c_long]
        self.Server_TCPClose.restypes = c_long
        # 开始采样
        self.StartSampling = self.vkdll.VK70xNMC_StartSampling
        self.StartSampling.argtypes = [c_long, c_long]
        self.StartSampling.restypes = c_long
        # 停止采样
        self.StopSampling = self.vkdll.VK70xNMC_StopSampling
        self.StopSampling.argtypes = [c_long]
        self.StopSampling.restypes = c_long
        # 
        self.Set_AdditionalFeature = self.vkdll.VK70xNMC_Set_AdditionalFeature
        self.Set_AdditionalFeature.argtypes = [c_long, c_long, c_long, c_double]
        self.Set_AdditionalFeature.restypes = c_long
        # 初始化
        self.Initialize = self.vkdll.VK70xNMC_Initialize
        self.Initialize.argtypes = [c_int, c_int, c_int, c_int, c_int, POINTER(c_int)]
        self.Initialize.restypes = c_int
        # 初始化2
        self.initialize_all = self.vkdll.VK70xNMC_InitializeAll
        self.initialize_all.argtypes = [c_int, POINTER(c_int), c_int]
        self.initialize_all.restypes = c_int
        # 获取连接服务器的采集卡数量，不超过8 
        self.Server_Get_ConnectedClientNumbers = self.vkdll.Server_Get_ConnectedClientNumbers
        self.Server_Get_ConnectedClientNumbers.argtypes = [POINTER(c_long)]
        self.Server_Get_ConnectedClientNumbers.restypes = c_long
        # 获取连接到服务器的采集卡连接句柄
        self.Server_Get_ConnectedClientHandle = self.vkdll.Server_Get_ConnectedClientHandle
        self.Server_Get_ConnectedClientHandle.argtypes = [c_int, POINTER(c_int), POINTER(c_char)]
        self.Server_Get_ConnectedClientHandle.restypes = c_int

        self.GetAllChannel = self.vkdll.VK70xNMC_GetFourChannel
        self.GetAllChannel.argtypes = [c_long, POINTER(c_double), c_long]
        self.GetAllChannel.restypes = c_long
        # self.GetAllChannel = self.vkdll.VK70xNMC_GetAllChannel
        # self.GetAllChannel.argtypes = [c_long, POINTER(c_double), c_long]
        # self.GetAllChannel.restypes = c_long
    def vk701NDC_influx(self, vk, data_addresses):
        while True:
            data = vk.get()
            Log().printInfo(data)
            # print(f"输出队列长度{vk.outputque.qsize()}")
            # print(f"保存队列长度{vk.saveque.qsize()}")
            # time.sleep(10)


class VK702NHMC(VKBase):
    def load_client_cfg(self):
        '''根据采集卡连接id加载采集卡配置设定'''
        self.config = VKConfig(VK701NDCConfig().vkconfig)

    def dll_init(self):
        self.vkdll = cdll.LoadLibrary(libVK70XNMC_DAQ_SHARED)

        self.Server_TCPOpen = self.vkdll.Server_TCPOpen
        self.Server_TCPOpen.argtypes = [c_long]
        self.Server_TCPOpen.restypes = c_long

        self.Server_TCPClose = self.vkdll.Server_TCPClose
        self.Server_TCPClose.argtypes = [c_long]
        self.Server_TCPClose.restypes = c_long

        self.Server_Get_ConnectedClientNumbers = self.vkdll.Server_Get_ConnectedClientNumbers
        self.Server_Get_ConnectedClientNumbers.argtypes = [POINTER(c_long)]
        self.Server_Get_ConnectedClientNumbers.restypes = c_long

        self.StartSampling = self.vkdll.VK702NHMC_StartSampling
        self.StartSampling.argtypes = [c_long, c_long]
        self.StartSampling.restypes = c_long

        self.StopSampling = self.vkdll.VK702NHMC_StopSampling
        self.StopSampling.argtypes = [c_long]
        self.StopSampling.restypes = c_long

        self.Set_AdditionalFeature = self.vkdll.VK702NHMC_Set_AdditionalFeature
        self.Set_AdditionalFeature.argtypes = [c_long, c_long, c_long, c_double]
        self.Set_AdditionalFeature.restypes = c_long

        self.Initialize = self.vkdll.VK702NHMC_Initialize
        self.Initialize.argtypes = [c_long, c_long, c_long, c_long, c_long, POINTER(c_long)]
        self.Initialize.restypes = c_long

        self.VK702NHMC_GetOneChannel_WithIOStatus = self.vkdll.VK702NHMC_GetOneChannel_WithIOStatus
        self.VK702NHMC_GetOneChannel_WithIOStatus.argtypes = [c_long, c_long, POINTER(c_double), c_long, c_long]
        self.VK702NHMC_GetOneChannel_WithIOStatus.restypes = c_long

        self.VK702NHMC_GetFourChannel_WithIOStatus = self.vkdll.VK702NHMC_GetFourChannel_WithIOStatus
        self.VK702NHMC_GetFourChannel_WithIOStatus.argtypes = [c_long, POINTER(c_double), c_long, c_long]
        self.VK702NHMC_GetFourChannel_WithIOStatus.restypes = c_long

        self.VK702NHMC_GetAllChannel_WithIOStatus = self.vkdll.VK702NHMC_GetAllChannel_WithIOStatus
        self.VK702NHMC_GetAllChannel_WithIOStatus.argtypes = [c_long, POINTER(c_double), c_long, c_long]
        self.VK702NHMC_GetAllChannel_WithIOStatus.restypes = c_long

        self.VK702NHMC_GetOneChannel = self.vkdll.VK702NHMC_GetOneChannel
        self.VK702NHMC_GetOneChannel.argtypes = [c_long, c_long, POINTER(c_double), c_long]
        self.VK702NHMC_GetOneChannel.restypes = c_long

        self.VK702NHMC_GetFourChannel = self.vkdll.VK702NHMC_GetFourChannel
        self.VK702NHMC_GetFourChannel.argtypes = [c_long, POINTER(c_double), c_long]
        self.VK702NHMC_GetFourChannel.restypes = c_long

        self.VK702NHMC_GetFourChannel = self.vkdll.VK702NHMC_GetFourChannel
        self.VK702NHMC_GetFourChannel.argtypes = [c_long, POINTER(c_double), c_long]
        self.VK702NHMC_GetFourChannel.restypes = c_long

        self.GetAllChannel = self.vkdll.VK702NHMC_GetAllChannel
        self.GetAllChannel.argtypes = [c_long, POINTER(c_double), c_long]
        self.GetAllChannel.restypes = c_long