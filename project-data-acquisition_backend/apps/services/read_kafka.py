from kafka import KafkaConsumer
from json import loads


class KafkaConsumerClass:
    def __init__(self, bootstrap_servers, topic, group_id='my-group2'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id

    def consume_messages(self):
        consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            # auto_offset_reset='earliest',  # 从最早的记录开始消费
            auto_offset_reset='latest',
            enable_auto_commit=True,  # 允许自动提交偏移量
            group_id=self.group_id,  # 消费者组ID
            value_deserializer=lambda m: loads(m.decode('utf-8'))  # 消息值反序列化
        )

        for message in consumer:
            print(f"Consumed message: {message.value}")

        # Kafka集群地址，这里假设是本地运行，并且端口是9092

if __name__ == "__main__":
    KAFKA_BROKER = '10.172.27.80:19092'
    # 要使用的Kafka主题
    TOPIC = 'qm_data'
    # 创建KafkaConsumerClass实例并调用consume_messages方法
    consumer_instance = KafkaConsumerClass(bootstrap_servers=KAFKA_BROKER, topic=TOPIC)
    consumer_instance.consume_messages()