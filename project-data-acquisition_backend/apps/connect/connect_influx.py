#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# here put the import lib
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from settings import DevelopmentConfig
from utils.baseLogger import Log

def w_influx(client, device_name, data):

    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(DevelopmentConfig().INFLUXDB_BUCKET, DevelopmentConfig().INFLUXDB_ORG, data)
    # Log().printInfo("device: " + device_name + "; data already store influxdb!")

class InfluxClient:
    def __init__(self):
        self.org = DevelopmentConfig().INFLUXDB_ORG
        self.ip = DevelopmentConfig().INFLUXDB_HOST
        self.port = DevelopmentConfig().INFLUXDB_PORT
        self.token = DevelopmentConfig().INFLUXDB_TOKEN

    def connect(self):
        try:
            client = InfluxDBClient(url="http://" + self.ip + ":" + str(self.port),
                                    token=self.token, org=self.org)
            # Log().printInfo(f"创建influx客户端完成")
            return client

        except Exception as e:
            Log().printError(f"创建influx客户端报错：{e}")
            print(f"创建influx客户端报错：{e}")
            raise

if __name__ == '__main__':
    influx_client = InfluxClient()
    json_body = []
    json = {
        "measurement": 'test',
        "machine_id": 'A0201010001150330',
        "tags": {
            "tag1": "t1"
        },
        "fields": {
            "LefA": 1
        }
    }
    json_body.append(json)
    w_influx(influx_client, 'A0201010001150330', json_body)