from influxdb_client import InfluxDBClient,Point
from influxdb_client.client.write_api import WriteOptions, SYNCHRONOUS
from configparser import ConfigParser
from pandas import DataFrame
import numpy as np


class InfluxClient:
    def __init__(self, ip, port, my_token, my_org, my_bucket):
        self.org = my_org
        self.bucket = my_bucket
        self.db_client = InfluxDBClient(url="http://" + ip + ":" + str(port), token=my_token, org=my_org)
        self.write_api = self.db_client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.db_client.query_api()
        self.delete_api = self.db_client.delete_api()

    def write_client(self, data):
        self.write_api.write(self.bucket, self.org, data)

    def query_test(self):
        results = []
        tables = self.query_api.query('from(bucket:"airpressure") |> range(start: -10m)')
        for table in tables:
            for row in table.records:
                results.append((row.get_field(), row.get_value()))
        print(results)

    def query_data_frame(self, query_str: str, header_info: list):
        """query_str example"""
        # 'from(bucket:"my-bucket") '
        # '|> range(start: -10m) '
        # '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
        # # '|> keep(columns: ["location", "temperature"])'
        data_query = self.query_api.query_data_frame(query_str)
        query_data_frame = DataFrame(np.array(data_query))
        query_data_frame = query_data_frame.dropna()
        query_data_frame = query_data_frame.iloc[:, 2:]
        if query_data_frame.shape[1] == len(header_info):
            query_data_frame.columns = header_info
        return query_data_frame

    def change_filed_type(self, target_measure, target_field):
        query_str = f'from(bucket: "{self.bucket}") |> range(start: 0) |> filter(fn: (r) => r._measurement == "{target_measure}") |> set(key: "{target_field}", value: (r) => toFloat(v: r.{target_field}))'
        self.query_api.query(query_str)

    def delete(self, target):
        self.delete_api.delete(start="2023-05-23T00:00:00Z", stop="2023-05-26T13:26:00Z", predicate='_measurement="' +
                                                                                                    target + '"',
                               bucket=self.bucket, org=self.org)


if __name__ == '__main__':
    conf = ConfigParser()
    conf.read('config.ini', encoding='gbk')
    current_config = "configure_dame3066n"
    TOKEN = str(conf.get(current_config, "TOKEN"))
    INFLUX_IP = str(conf.get(current_config, "INFLUX_IP"))
    INFLUX_PORT = int(conf.get(current_config, "INFLUX_PORT"))
    INFLUX_ORG = str(conf.get(current_config, "INFLUX_ORG"))
    INFLUX_BUCKET = str(conf.get(current_config, "INFLUX_BUCKET"))
    write_influx = InfluxClient(ip=INFLUX_IP, port=INFLUX_PORT, my_token=TOKEN, my_org=INFLUX_ORG,
                                my_bucket=INFLUX_BUCKET)
    json_body = []
    json = {
        "measurement": 'test_0112',
        "tags": {
            "tag1": "t1"
        },
        "fields": {
            "a": 1,
            "b": 2,
            "c": 4
        }
    }
    json_body.append(json)
    # print(json_body)
    # write_influx.write_client(data=json_body)
    # write_influx.query_test()
    head_info = ["time", "x_electric_current-mean", "z_electric_current-mean"]
    data = write_influx.query_data_frame(
        'from(bucket:"' + INFLUX_BUCKET + '") '
                                          '|> range(start: -10m) '
                                          '|> limit(n: 10) '
                                          '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                          '|> keep(columns: ["_time","x_electric_current-mean", '
                                          '"z_electric_current-mean"])',
        head_info
    )

    # data.to_csv("test.csv",encoding="UTF-8")
