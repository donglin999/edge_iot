import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from settings import DevelopmentConfig
from utils.baseLogger import Log

class SQLiteManager:
    def __init__(self):
        self.db_path = DevelopmentConfig().SQLITE_DB_PATH
        self.table_name = DevelopmentConfig().SQLITE_TABLE_NAME
        self._init_db()
        
    def _init_db(self):
        """初始化数据库和表"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 创建连接
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_a_tag TEXT,
                device_name TEXT,
                message TEXT,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER DEFAULT 0
            )
        ''')
        
        # 创建索引
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_status_time 
            ON {self.table_name} (status, create_time)
        ''')
        
        conn.commit()
        conn.close()
        
    def save_message(self, device_a_tag, device_name, message):
        """保存消息到SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                INSERT INTO {self.table_name} 
                (device_a_tag, device_name, message) 
                VALUES (?, ?, ?)
            ''', (device_a_tag, device_name, message))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            Log().printError(f"保存消息到SQLite失败: {e}")
            return False
            
    def get_pending_messages(self, batch_size=100):
        """获取待发送的消息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT id, device_a_tag, device_name, message 
                FROM {self.table_name}
                WHERE status = 0
                ORDER BY create_time ASC
                LIMIT ?
            ''', (batch_size,))
            
            messages = cursor.fetchall()
            conn.close()
            return messages
        except Exception as e:
            Log().printError(f"获取待发送消息失败: {e}")
            return []
            
    def mark_as_sent(self, message_ids):
        """标记消息为已发送"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                UPDATE {self.table_name}
                SET status = 1
                WHERE id IN ({','.join(['?']*len(message_ids))})
            ''', message_ids)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            Log().printError(f"标记消息状态失败: {e}")
            return False
            
    def cleanup_old_data(self, days=7):
        """清理旧数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cleanup_date = datetime.now() - timedelta(days=days)
            
            cursor.execute(f'''
                DELETE FROM {self.table_name}
                WHERE create_time < ? AND status = 1
            ''', (cleanup_date.strftime('%Y-%m-%d %H:%M:%S'),))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            Log().printError(f"清理旧数据失败: {e}")
            return False 