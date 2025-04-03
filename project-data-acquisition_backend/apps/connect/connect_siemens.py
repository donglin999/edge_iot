#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from lib.HslCommunication import SiemensS7Net, SiemensPLCS
from settings import DevelopmentConfig
from utils.baseLogger import Log

class ConnectSiemens:
    def __init__(self):
        self.plc = SiemensS7Net(SiemensPLCS.S1200, DevelopmentConfig().PLC_IP)
        # print("连接成功")
    def write(self, addr, type, value):
        # 连接到PLC
        if type == "bool" or type == "BOOL":

            result = self.plc.WriteBool(addr, value)
            if result.IsSuccess:
                # print(f"写入{addr}成功")
                pass
            else:
                print(f"写入{addr}报错: {result.Message}")
                Log().printError(f"写入{addr}报错: {result.Message}")
        if type == "int" or type == "INT":

            result = self.plc.WriteInt32(addr, int(value))
            if result.IsSuccess:
                # print(f"写入{addr}成功")
                pass
            else:
                print(f"写入{addr}报错: {result.Message}")
                Log().printError(f"写入{addr}报错: {result.Message}")

        if type == "string" or type == "STRING":

            result = self.plc.WriteString(addr, value)
            if result.IsSuccess:
                # print(f"写入{addr}成功")
                pass
            else:
                print(f"写入{addr}报错: {result.Message}")
                Log().printError(f"写入{addr}报错: {result.Message}")

        if type == "float" or type == "FLOAT":

            result = self.plc.WriteFloat(addr, value)
            if result.IsSuccess:
                # print(f"写入{addr}成功")
                pass
            else:
                print(f"写入{addr}报错: {result.Message}")
                Log().printError(f"写入{addr}报错: {result.Message}")

        # 断开与PLC的连接
        self.plc.ConnectClose()
        # print("断开连接")



