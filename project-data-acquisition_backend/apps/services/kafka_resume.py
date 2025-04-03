import time
import json
from settings import DevelopmentConfig
from utils.baseLogger import Log
from apps.utils.sqlite_manager import SQLiteManager
from apps.connect.connect_kafka import KafkaConnect

class KafkaResume:
    def __init__(self):
        self.config = DevelopmentConfig()
        self.sqlite_manager = SQLiteManager()
        self.kafka_connect = KafkaConnect()
            
    def process_pending_messages(self):
        """处理待发送的消息"""
        # 首先检查Kafka连接
        if not self.kafka_connect.ensure_connection():
            Log().printError("Kafka连接不可用，等待5秒后重试")
            time.sleep(5)
            return False
            
        messages = self.sqlite_manager.get_pending_messages(
            self.config.KAFKA_RESUME_BATCH_SIZE
        )
        
        if not messages:
            return True
            
        success_ids = []
        for msg_id, device_a_tag, device_name, message in messages:
            try:
                if self.kafka_connect.send_message(json.loads(message)):
                    success_ids.append(msg_id)
                else:
                    # 发送失败，退出处理
                    return False
            except Exception as e:
                Log().printError(f"发送消息失败 {device_a_tag}: {e}")
                return False
                
        # 标记成功发送的消息
        if success_ids:
            self.sqlite_manager.mark_as_sent(success_ids)
            
        return True
        
    def run(self):
        """运行断点续传服务"""
        Log().printInfo("启动Kafka断点续传服务")
        
        while True:
            try:
                # 处理待发送消息
                self.process_pending_messages()
                
                # 清理旧数据
                self.sqlite_manager.cleanup_old_data(
                    self.config.KAFKA_RESUME_RETENTION_DAYS
                )
                
            except Exception as e:
                Log().printError(f"断点续传服务异常: {e}")
                
            time.sleep(self.config.KAFKA_RESUME_INTERVAL) 