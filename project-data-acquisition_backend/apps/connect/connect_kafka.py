import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
from settings import DevelopmentConfig
from utils.baseLogger import Log

class KafkaConnect:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KafkaConnect, cls).__new__(cls)
            cls._instance._init_producer()
        return cls._instance
    
    def _init_producer(self):
        """初始化Kafka生产者"""
        self.config = DevelopmentConfig()
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.kafka_bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            Log().printInfo(f"Kafka生产者创建成功，服务器：{self.config.kafka_bootstrap_servers}")
        except Exception as e:
            Log().printError(f"Kafka连接失败: {e}")
            self.producer = None
            
    def check_connection(self):
        """检查Kafka连接状态"""
        if not self.producer:
            return False
            
        try:
            # 获取集群元数据来检查连接
            self.producer.metrics()
            return True
        except Exception as e:
            Log().printError(f"Kafka连接检查失败: {e}")
            self.producer = None
            return False
            
    def ensure_connection(self):
        """确保Kafka连接可用"""
        if not self.check_connection():
            self._init_producer()
        return self.producer is not None
            
    def get_producer(self):
        """获取Kafka生产者实例"""
        self.ensure_connection()
        return self.producer
        
    def send_message(self, message, topic=None):
        """发送消息到Kafka"""
        if not self.ensure_connection():
            return False
                
        try:
            # 如果没有指定topic，使用配置中的默认topic
            kafka_topic = topic if topic else self.config.kafka_topic
            self.producer.send(kafka_topic, message)
            return True
        except Exception as e:
            Log().printError(f"发送消息到Kafka失败: {e}")
            self.producer = None  # 重置连接
            return False 