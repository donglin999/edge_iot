#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/04/18 16:22:15
@Author  :   lihj210
@Version :   1.0
@Contact :   lihj210@midea.com
@Desc    :   系统级的参数配置
'''

#  import lib
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_precious_secret_key')
    DEBUG = True
    LOG_FILE = "/apps/data_acquisition/Logs/"

# 开发环境配置
class DevelopmentConfig(Config):
    """项目配置核心类"""
    DEBUG = False
    # 配置日志
    # LOG_LEVEL = "DEBUG"
    LOG_LEVEL = "INFO"


    # 配置INFLUXDB
    # 项目上线以后，这个地址就会被替换成真实IP地址，mysql也是
    INFLUXDB_HOST = '10.41.68.46'
    INFLUXDB_PORT = 8086
    INFLUXDB_TOKEN = 'tKwtme7RYKb3c9LmBxxVKhWv-MF9TT9XTXFdlm5Q6eU6Q1RS0Ywjk2ND8a1S_CQUcpaNeEHWJwk9NQFnzJZa1g== '
    INFLUXDB_ORG = "IMRC"
    INFLUXDB_BUCKET = "Record"
    INFLUXDB_URL = "http://" + INFLUXDB_HOST + ":" + str(INFLUXDB_PORT)
    # INFLUXDB_DATABASE = "phm"



    # 配置redis
    # 项目上线以后，这个地址就会被替换成真实IP地址，mysql也是
    REDIS_ENABLED = False
    REDIS_HOST = '10.141.6.103'
    REDIS_PORT = 6379
    REDIS_PASSWORD = ''
    # REDIS_PASSWORD = 'k+5p2K{nZf'
    REDIS_POLL = 10

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database/db.sqlite3')
    # 动态追踪修改设置，如未设置只会提示警告
    SQLALCHEMY_TRACK_MODIFICATIONS = True


    # rabbitmq参数配置
    RABBITUSER = "user"
    RABBITPASSWORD = "password"
    RABBITHOST = "your ip"
    RABBITPORT = 5372

    # API_ENABLED = True
    API_ENABLED = False
    API_TAG = "API_KAFKA"



config_by_name = dict(
    dev=DevelopmentConfig,
)
key = Config.SECRET_KEY
