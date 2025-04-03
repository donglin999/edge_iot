#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   util.py
@Time    :   2023/04/27 16:22:15
@Author  :   Jason Jiangfeng 
@Version :   1.0
@Contact :   jiangfeng24@midea.com
@Desc    :   util function
'''

# here put the import lib
import json
import os
from collections import namedtuple,defaultdict
from utils.baseLogger import Log
from functools import wraps
from threading import Thread
from pandas import DataFrame
from utils.vibprocess import VibFeature

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 获取父级目录
parent_dir = os.path.dirname(current_dir)

config_path = parent_dir +"/config/"
config_file_path = config_path+"config.json"

Feature = namedtuple('Feature', ['name', 'params'])


def RunInNewThread(number=1):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            threads = []
            for i in range(number):
                t = Thread(target=func, args=(*args,), kwargs=kwargs)
                t.daemon = True
                t.start()
                threads.append(t)
            return threads

        return wrapper

    return inner


def dataframe_apply(original_data: DataFrame, formulas: dict):
    '''
    用于将vk采集的原始电信号数据转换成有实际物理意义的传感数据
    original_data: 原始数据
    formulas: 字典形式的转换公式信息，字典key表示需要转换的列名，value值为转换方式
    return: 与original_data形状一致的DataFrame
    '''
    for column, formula in formulas.items():
        try:
            if column in original_data.columns:
                original_data.loc[:, column] = original_data[column].apply(eval(f"lambda data:{formula}"))
        except Exception as e:
            Log().printError(f"{column}列应用公式{formula}失败！\n {e}")
            pass
        return original_data


def calcu_feature(physical_data, client_cfg):
    '''
    用于计算物理传感数据的特征
    physical_data: 物理传感数据
    client_cfg: 采集卡配置
    return: 与original_data形状一致的DataFrame
    '''

    result = defaultdict(dict)
    feature_calcu_info = client_cfg.feature_calcu_info
    fs = client_cfg.fs
    # feature_calcu_info: 字典形式的特征计算需求，比如{'1':[Feature('acc_rms',10000),Feature('vel_rms',10000)]}
    for tunnel, features in feature_calcu_info.items():
        tempdata = physical_data.iloc[:, tunnel]
        vbf = VibFeature(tempdata, fs)
        for feature in features:
            temp = Feature(*feature)
            try:
                result[tunnel][temp.name] = float(vbf.get_feature_func(temp.name)(*temp.params))
            except Exception as e:
                Log().printError(f"采集卡{client_cfg.id} {tunnel}通道 计算{temp.name}特征失败！{e}")
    return result

def getconfig(key_name):
    """
    key_name: json取用的key
    return: 返回相应的config字段
    """
    with open(config_file_path, 'r', encoding='utf_8_sig') as load_f:
        config_dict = json.load(load_f)
        try:
            return config_dict[key_name]
        except Exception as e:
            Log().printError("Missing msg is " + key_name + ">>>>>>>>>>")
            Log().printError(e)


def getjson(json_name):
    """
    json_name: json取用来源的文件名
    return: 返回所有json数据
    """
    with open(config_path + json_name, 'r', encoding='utf_8_sig') as load_f:
        config_dict = json.load(load_f)
        try:
            return config_dict
        except Exception as e:
            Log().printError(e)
    

def pub_mqtt(client, topic, data):
    """
    client: mqtt client
    topic: mqtt 推送topic
    data: 组织好的data数据:
          {"temper.fb_sp_1"（英文测点名）: {"value": 1,"timestamp": 111111111111(13位数字时间戳), "quality":192}, ... ...}
    """
    json_data = json.dumps(data)
    client.publish(topic, json_data, 0)
    Log().printInfo("topic: " + topic + "; data already publish!")
    
def calc_trans(data, lower_limit, scope):
    value = round((data / 65535) * scope + lower_limit, 4)
    return value

def get_msg_dic(msg):
    json_msg = str(msg.payload.decode("utf-8"))
    dic_msg = json.loads(json_msg)
    return dic_msg