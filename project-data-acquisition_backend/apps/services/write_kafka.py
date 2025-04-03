from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from json import dumps, loads


class KafkaManager:
    def __init__(self, bootstrap_servers, topic):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic

        # 推送消息到Kafka的类方法

    def produce_message(self, message):
        producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)
        try:
            # 发送消息到Kafka，这里假设消息是JSON格式的字符串
            future = producer.send(self.topic, value=dumps(message).encode('utf-8'))
            result = future.get(timeout=10)
            print(f"Message '{message}' sent to {self.topic}")
        except KafkaError as e:
            print(f"I'm sorry, but an error occurred: {e}")
        finally:
            producer.close()

            # 订阅Kafka主题并打印消息的实例方法（示例）

    def consume_messages(self, group_id='my-group'):
        consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',  # 从最早的记录开始消费
            enable_auto_commit=True,  # 允许自动提交偏移量
            group_id=group_id,  # 消费者组ID
            value_deserializer=lambda m: loads(m.decode('utf-8'))  # 消息值反序列化
        )

        for message in consumer:
            print(f"Consumed message: {message.value}")

        # Kafka集群地址，这里假设是本地运行，并且端口是9092


KAFKA_BROKER = 'localhost:9092'
# 要使用的Kafka主题
TOPIC = 'my_topic'

if __name__ == "__main__":
    # 创建Kafka管理类实例
    kafka_manager = KafkaManager(bootstrap_servers=KAFKA_BROKER, topic=TOPIC)

    # 推送消息
    message = {"key": "value", "message": "Hello"}
    kafka_manager.produce_message(message)

    # 注意：consume_messages通常是一个长时间运行的过程，
    # 因此你可能想要在一个单独的线程或进程中运行它，或者作为另一个脚本运行。
    # 例如，你可以通过注释或取消注释下面的行来测试它。
    # kafka_manager.consume_messages()