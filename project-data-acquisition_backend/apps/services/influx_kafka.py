import threading
import time
from datetime import datetime, timedelta, timezone
from influxdb_client import InfluxDBClient
import json
from settings import DevelopmentConfig
from utils.baseLogger import Log
from apps.connect.connect_kafka import KafkaConnect
from apps.utils.sqlite_manager import SQLiteManager

class InfluxKafka:
    def __init__(self):
        config = DevelopmentConfig()
        self.influx_url = config.INFLUXDB_URL
        self.influx_token = config.INFLUXDB_TOKEN
        self.influx_org = config.INFLUXDB_ORG
        self.influx_bucket = config.INFLUXDB_BUCKET
        
        # 初始化InfluxDB客户端
        self.client = InfluxDBClient(
            url=self.influx_url, 
            token=self.influx_token, 
            org=self.influx_org
        )
        self.query_api = self.client.query_api()
        
        # 初始化Kafka和SQLite
        self.kafka_connect = KafkaConnect()
        self.sqlite_manager = SQLiteManager()
        
        self.UploadSuccess_Count = 1
        self.query_Count = 1
        
    def query_device_data(self, device_a_tag, fields_to_query):
        """批量查询设备数据"""
        # 构建查询
        query = f'''
        from(bucket: "{self.influx_bucket}")
            |> range(start: -3s)
            |> filter(fn: (r) => r["device_a_tag"] == "{device_a_tag}")
            |> filter(fn: (r) => r["kafka_position"] != "")
            |> last()
        '''
        
        try:
            tables = self.query_api.query(query)
            results = {}
            for table in tables:
                for record in table.records:
                    field = record.get_field()
                    if field in fields_to_query:
                        results[field] = {
                            'value': record.get_value(),
                            'kafka_position': record.values.get('kafka_position', ''),
                            'cn_name': record.values.get('cn_name', '')
                        }
            return results
        except Exception as e:
            Log().printError(f"查询设备 {device_a_tag} 数据失败: {e}")
            return None
            
    def process_device_data(self, device_a_tag, device_name, data):
        """处理设备数据并发送到kafka"""
        if not data:
            return
            
        # 获取北京时间
        beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
        formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建kafka消息
        kafka_message = {
            "nodeId": device_a_tag,
            "timeStamp": formatted_time,
            "type": 1,
            "totalResult": "ok",
            "detectItems": [],
            "measures": []
        }
        
        # 添加测量值
        for field, field_data in data.items():
            measure = {
                "measureId": field,
                "value": str(field_data['value']),
                "status": 1
            }
            kafka_message["measures"].append(measure)
            
        # 尝试发送消息到Kafka
        if not self.kafka_connect.send_message(kafka_message):
            # 发送失败,保存到SQLite
            self.sqlite_manager.save_message(
                device_a_tag,
                device_name,
                json.dumps(kafka_message)
            )

    def process_and_send_data(self, device_config):
        """处理并发送数据主函数"""
        # 按设备分组获取需要发送到kafka的字段
        device_fields = {}
        for device, config in device_config.items():
            fields = []
            for field, field_config in config.items():
                if isinstance(field_config, dict) and field_config.get('to_kafka') == 1:
                    fields.append(field)
            if fields:
                device_fields[config['device_a_tag']] = {
                    'device_name': config['device_name'],
                    'fields': fields
                }
                
        # 启动设备数据处理线程
        for device_a_tag, device_info in device_fields.items():
            thread = threading.Thread(
                target=self._device_data_loop,
                args=(device_a_tag, device_info)
            )
            thread.start()
            
    def _device_data_loop(self, device_a_tag, device_info):
        """设备数据处理循环"""
        while True:
            try:
                # 查询数据
                data = self.query_device_data(
                    device_a_tag,
                    device_info['fields']
                )
                
                # 处理并发送数据
                if data:
                    self.process_device_data(
                        device_a_tag,
                        device_info['device_name'],
                        data
                    )

            except Exception as e:
                print(f"处理设备 {device_a_tag} 数据失败: {e}")
                
            time.sleep(1)  # 控制查询频率

