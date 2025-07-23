#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   baseLogger.py
@Time    :   2023/04/27 16:24:59
@Author  :   Jason Jiangfeng 
@Version :   1.0
@Contact :   jiangfeng24@midea.com
@Desc    :   base log class
'''

# here put the import lib
import logging
import os
import time
from datetime import datetime

del_files = 7

# 使用相对路径，确保本地环境有写权限
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
# log_path = "d:/Users/ex_wuxx18/Desktop/midea_project/project-data-acquisition/"


def delete_files(folder_path):
    # 遍历文件夹中的所有文件和子文件夹
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            # 获取文件的创建时间
            create_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            # 计算文件创建时间距离现在的时间差
            time_diff = datetime.now() - create_time
            # 如果时间差超过1周，则删除该文件
            if time_diff.days > del_files:
                os.remove(file_path)
        elif os.path.isdir(file_path):
            # 递归调用自身，继续遍历子文件夹中的所有文件和子文件夹
            delete_files(file_path)
    # 删除空子文件夹
    if not os.listdir(folder_path):
        os.rmdir(folder_path)
        
class Log:
    def __init__(self, name="default"):
        self.logger = logging.getLogger()  # 创建logger
        self.logger.setLevel(logging.INFO)  # 日志root等级
        # 自动确保name以/结尾
        if not name.endswith("/"):
            name += "/"
        self.log_path = os.path.join(log_path, name)  # 日志目录
        # 日志内容格式
        self.formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        if not os.path.exists(self.log_path):  # 目录不存在就创建
            os.makedirs(self.log_path)

    def printLog(self, log_type, log_content):  # 输出日志
        logTime = time.strftime('%Y%m%d%H', time.localtime(time.time()))  # 当前时间到小时
        log_file = self.log_path + logTime + '.log'  # 文件名
        if not os.path.exists(log_file):  # 日志文件不存在就创建
            fd = open(log_file, mode="w", encoding="utf_8_sig")
            fd.close()
        
        try:
            delete_files(log_path)
        except Exception as e:
            print(f"删除日志文件失败: {e}")
        
        # 用不同的 handler 对不同等级的日志消息进行处理
        if log_type == "INFO":
            self.file_handler = logging.FileHandler(log_file, mode='a', encoding='UTF-8')
            self.file_handler.setLevel(logging.INFO)
            self.file_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handler)
            self.logger.info(log_content)
            self.logger.removeHandler(self.file_handler)
        elif log_type == "WARNING":
            self.file_handler = logging.FileHandler(log_file, mode='a', encoding='UTF-8')
            self.file_handler.setLevel(logging.WARNING)
            self.file_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handler)
            self.logger.warning(log_content)
            self.logger.removeHandler(self.file_handler)
        elif log_type == "ERROR":
            self.file_handler = logging.FileHandler(log_file, mode='a', encoding='UTF-8')
            self.file_handler.setLevel(logging.ERROR)
            self.file_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handler)
            self.logger.error(log_content)
            self.logger.removeHandler(self.file_handler)
        elif log_type == "CRITICAL":
            self.file_handler = logging.FileHandler(log_file, mode='a', encoding='UTF-8')
            self.file_handler.setLevel(logging.CRITICAL)
            self.file_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handler)
            self.logger.critical(log_content)
            self.logger.removeHandler(self.file_handler)

    def printInfo(self, log_content):
        self.printLog("INFO", log_content)

    def printWarning(self, log_content):
        self.printLog("WARNING", log_content)

    def printError(self, log_content):
        self.printLog("ERROR", log_content)

    def printCritical(self, log_content):
        self.printLog("CRITICAL", log_content)


if __name__ == '__main__':
    Log = Log()
    Log.printInfo('111')
    Log.printWarning('222')
    Log.printError('333')
