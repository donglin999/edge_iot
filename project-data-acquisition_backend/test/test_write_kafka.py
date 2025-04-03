import json
import time
from datetime import datetime, timezone, timedelta
from kafka import KafkaProducer

kafka_bootstrap_servers = '10.41.68.47:19092'
kafka_producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers,value_serializer=lambda x: json.dumps(x).encode('utf-8'))

print(f"kafka生产者创建成功，服务器：{kafka_bootstrap_servers}")
topic = 'mc_data'

while True:
    # 假设local_time是一个UTC时间对象
    # 例如，我们可以手动创建一个UTC时间
    utc_time = datetime.now(timezone.utc)
    # 将UTC时间转换为北京时间（UTC+8）
    # 注意：timedelta(hours=8)用于将UTC时间转换为北京时间
    beijing_time = utc_time + timedelta(hours=8)
    # 使用strftime来格式化时间
    formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

    kafka_message = {
        "timeStamp": formatted_time,
        "nodeId": 1,
        "type": 1,
        "measures": [
            {
                "measureId": "runningstatus",
                "value": 1,
                "status": 1
            }
        ]
    }
    kafka_producer.send(topic, kafka_message)
    print(f"send，kafka_message：{kafka_message}")
    time.sleep(2)


