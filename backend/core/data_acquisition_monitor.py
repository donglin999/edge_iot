#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据采集性能监控模块 - 监控数据采集性能和数据流状态
"""

import os
import sys
import time
import logging
import asyncio
import threading
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logs.log_config import get_logger
from models.process_models import HealthStatus, ConnectionStatus

logger = get_logger("backend", "core", "data_acquisition_monitor")

@dataclass
class DataFlowStatus:
    """数据流状态"""
    process_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    data_points_per_minute: float = 0.0
    last_data_time: Optional[datetime] = None
    error_rate: float = 0.0
    response_time_ms: float = 0.0
    data_quality_score: float = 100.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DataAcquisitionAlert:
    """数据采集告警"""
    process_name: str
    alert_type: str
    severity: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_time: Optional[datetime] = None

class DataAcquisitionMonitor:
    """数据采集性能监控类"""
    
    def __init__(self, db_path: str = "backend/data/process_monitoring.db"):
        self.logger = get_logger("backend", "core", "data_acquisition_monitor")
        self.db_path = db_path
        self.data_flow_status: Dict[str, DataFlowStatus] = {}
        self.alerts: Dict[str, List[DataAcquisitionAlert]] = {}
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.check_interval = 60  # 默认60秒检查一次
        self.data_timeout = 300  # 默认5分钟无数据视为异常
        self.alert_callbacks: Dict[str, callable] = {}
        self.status_callbacks: Dict[str, callable] = {}
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库存储"""
        try:
            # 确保数据目录存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建数据流状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_flow_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data_points_per_minute REAL DEFAULT 0.0,
                    last_data_time TEXT,
                    error_rate REAL DEFAULT 0.0,
                    response_time_ms REAL DEFAULT 0.0,
                    data_quality_score REAL DEFAULT 100.0,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # 创建数据采集告警表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_acquisition_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_time TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
    
    def register_process(self, process_name: str) -> bool:
        """注册进程监控"""
        try:
            if process_name not in self.data_flow_status:
                self.data_flow_status[process_name] = DataFlowStatus(process_name=process_name)
                
            if process_name not in self.alerts:
                self.alerts[process_name] = []
                
            self.logger.info(f"注册数据采集监控: {process_name}")
            return True
        except Exception as e:
            self.logger.error(f"注册数据采集监控失败: {e}")
            return False
    
    def unregister_process(self, process_name: str) -> bool:
        """取消注册进程监控"""
        try:
            if process_name in self.data_flow_status:
                del self.data_flow_status[process_name]
                
            if process_name in self.alerts:
                del self.alerts[process_name]
                
            if process_name in self.alert_callbacks:
                del self.alert_callbacks[process_name]
                
            if process_name in self.status_callbacks:
                del self.status_callbacks[process_name]
                
            self.logger.info(f"取消数据采集监控: {process_name}")
            return True
        except Exception as e:
            self.logger.error(f"取消数据采集监控失败: {e}")
            return False
    
    def set_alert_callback(self, process_name: str, callback: callable):
        """设置告警回调函数"""
        self.alert_callbacks[process_name] = callback
        self.logger.info(f"设置告警回调: {process_name}")
    
    def set_status_callback(self, process_name: str, callback: callable):
        """设置状态变化回调函数"""
        self.status_callbacks[process_name] = callback
        self.logger.info(f"设置状态回调: {process_name}")
    
    def start_monitoring(self, interval: int = 60, data_timeout: int = 300):
        """启动数据采集监控"""
        if self.monitoring_active:
            return
        
        self.check_interval = interval
        self.data_timeout = data_timeout
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_data_acquisition, daemon=True)
        self.monitoring_thread.start()
        self.logger.info(f"数据采集监控已启动，检查间隔: {interval}秒，数据超时: {data_timeout}秒")
    
    def stop_monitoring(self):
        """停止数据采集监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("数据采集监控已停止")
    
    def _monitor_data_acquisition(self):
        """数据采集监控线程"""
        while self.monitoring_active:
            try:
                for process_name, status in list(self.data_flow_status.items()):
                    # 检查数据流状态
                    self._check_data_flow_status(process_name, status)
                    
                    # 存储状态到数据库
                    self._store_data_flow_status(status)
                    
                    # 调用状态回调函数
                    if process_name in self.status_callbacks:
                        try:
                            self.status_callbacks[process_name](status)
                        except Exception as e:
                            self.logger.error(f"状态回调函数执行失败: {e}")
                
                # 等待下一次检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"数据采集监控线程异常: {e}")
                time.sleep(5)  # 发生异常时等待5秒
    
    def _check_data_flow_status(self, process_name: str, status: DataFlowStatus):
        """检查数据流状态"""
        try:
            # 检查最后数据时间
            if status.last_data_time:
                time_since_last_data = (datetime.now() - status.last_data_time).total_seconds()
                
                # 根据时间间隔判断状态
                if time_since_last_data > self.data_timeout:
                    # 数据超时，创建告警
                    if status.status != HealthStatus.CRITICAL:
                        status.status = HealthStatus.CRITICAL
                        self._create_alert(
                            process_name=process_name,
                            alert_type="data_timeout",
                            severity="critical",
                            message=f"数据采集中断超过 {self.data_timeout} 秒",
                            details={
                                "last_data_time": status.last_data_time.isoformat(),
                                "timeout_seconds": self.data_timeout,
                                "actual_seconds": time_since_last_data
                            }
                        )
                elif time_since_last_data > self.data_timeout / 2:
                    # 接近超时，设置警告状态
                    if status.status != HealthStatus.WARNING:
                        status.status = HealthStatus.WARNING
                        self._create_alert(
                            process_name=process_name,
                            alert_type="data_slow",
                            severity="warning",
                            message=f"数据采集速度减慢，{time_since_last_data:.1f} 秒未收到新数据",
                            details={
                                "last_data_time": status.last_data_time.isoformat(),
                                "warning_threshold": self.data_timeout / 2,
                                "actual_seconds": time_since_last_data
                            }
                        )
            else:
                # 没有数据记录
                if status.status != HealthStatus.UNKNOWN:
                    status.status = HealthStatus.UNKNOWN
                    self._create_alert(
                        process_name=process_name,
                        alert_type="no_data",
                        severity="warning",
                        message="未收到任何数据",
                        details={}
                    )
            
            # 检查错误率
            if status.error_rate > 0.2:  # 错误率超过20%
                if status.status != HealthStatus.CRITICAL:
                    status.status = HealthStatus.CRITICAL
                    self._create_alert(
                        process_name=process_name,
                        alert_type="high_error_rate",
                        severity="critical",
                        message=f"数据采集错误率过高: {status.error_rate:.1%}",
                        details={
                            "error_rate": status.error_rate,
                            "threshold": 0.2
                        }
                    )
            elif status.error_rate > 0.05:  # 错误率超过5%
                if status.status != HealthStatus.WARNING:
                    status.status = HealthStatus.WARNING
                    self._create_alert(
                        process_name=process_name,
                        alert_type="elevated_error_rate",
                        severity="warning",
                        message=f"数据采集错误率升高: {status.error_rate:.1%}",
                        details={
                            "error_rate": status.error_rate,
                            "threshold": 0.05
                        }
                    )
            
            # 检查数据质量评分
            if status.data_quality_score < 60:
                if status.status != HealthStatus.CRITICAL:
                    status.status = HealthStatus.CRITICAL
                    self._create_alert(
                        process_name=process_name,
                        alert_type="poor_data_quality",
                        severity="critical",
                        message=f"数据质量评分过低: {status.data_quality_score:.1f}",
                        details={
                            "data_quality_score": status.data_quality_score,
                            "threshold": 60
                        }
                    )
            elif status.data_quality_score < 80:
                if status.status != HealthStatus.WARNING:
                    status.status = HealthStatus.WARNING
                    self._create_alert(
                        process_name=process_name,
                        alert_type="reduced_data_quality",
                        severity="warning",
                        message=f"数据质量评分降低: {status.data_quality_score:.1f}",
                        details={
                            "data_quality_score": status.data_quality_score,
                            "threshold": 80
                        }
                    )
            
            # 如果一切正常，设置为健康状态
            if (status.last_data_time and 
                (datetime.now() - status.last_data_time).total_seconds() < self.data_timeout / 2 and
                status.error_rate < 0.05 and
                status.data_quality_score >= 80):
                
                if status.status != HealthStatus.HEALTHY:
                    status.status = HealthStatus.HEALTHY
                    
                    # 解决所有未解决的告警
                    self._resolve_all_alerts(process_name)
            
            # 更新时间戳
            status.timestamp = datetime.now()
            
        except Exception as e:
            self.logger.error(f"检查数据流状态失败: {e}")
    
    def _store_data_flow_status(self, status: DataFlowStatus):
        """存储数据流状态到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_flow_status 
                (process_name, status, data_points_per_minute, last_data_time, 
                error_rate, response_time_ms, data_quality_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                status.process_name,
                status.status.value,
                status.data_points_per_minute,
                status.last_data_time.isoformat() if status.last_data_time else None,
                status.error_rate,
                status.response_time_ms,
                status.data_quality_score,
                status.timestamp.isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"存储数据流状态失败: {e}")
    
    def _create_alert(self, process_name: str, alert_type: str, severity: str, message: str, details: Dict[str, Any]):
        """创建告警"""
        try:
            # 创建告警对象
            alert = DataAcquisitionAlert(
                process_name=process_name,
                alert_type=alert_type,
                severity=severity,
                message=message,
                details=details
            )
            
            # 添加到告警列表
            if process_name in self.alerts:
                self.alerts[process_name].append(alert)
                
                # 限制告警数量
                if len(self.alerts[process_name]) > 100:
                    self.alerts[process_name] = self.alerts[process_name][-100:]
            
            # 存储到数据库
            self._store_alert(alert)
            
            # 调用告警回调函数
            if process_name in self.alert_callbacks:
                try:
                    self.alert_callbacks[process_name](alert)
                except Exception as e:
                    self.logger.error(f"告警回调函数执行失败: {e}")
            
            self.logger.warning(f"创建告警: [{process_name}] {severity.upper()} - {message}")
            
        except Exception as e:
            self.logger.error(f"创建告警失败: {e}")
    
    def _store_alert(self, alert: DataAcquisitionAlert):
        """存储告警到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_acquisition_alerts 
                (process_name, alert_type, severity, message, details, timestamp, resolved, resolved_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.process_name,
                alert.alert_type,
                alert.severity,
                alert.message,
                json.dumps(alert.details),
                alert.timestamp.isoformat(),
                1 if alert.resolved else 0,
                alert.resolved_time.isoformat() if alert.resolved_time else None
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"存储告警失败: {e}")
    
    def _resolve_all_alerts(self, process_name: str):
        """解决所有未解决的告警"""
        try:
            if process_name not in self.alerts:
                return
            
            # 解决内存中的告警
            for alert in self.alerts[process_name]:
                if not alert.resolved:
                    alert.resolved = True
                    alert.resolved_time = datetime.now()
            
            # 解决数据库中的告警
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE data_acquisition_alerts
                SET resolved = 1, resolved_time = ?
                WHERE process_name = ? AND resolved = 0
            ''', (datetime.now().isoformat(), process_name))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"解决进程 {process_name} 的所有告警")
            
        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")
    
    def update_data_point(self, process_name: str, data_points: int = 1, errors: int = 0, response_time_ms: float = 0.0):
        """更新数据点信息"""
        try:
            if process_name not in self.data_flow_status:
                self.register_process(process_name)
            
            status = self.data_flow_status[process_name]
            
            # 更新最后数据时间
            status.last_data_time = datetime.now()
            
            # 更新数据点计数
            # 这里使用简单的指数移动平均来平滑数据
            alpha = 0.3  # 平滑因子
            
            # 计算每分钟数据点数
            points_per_minute = data_points * (60 / self.check_interval)
            status.data_points_per_minute = (alpha * points_per_minute + 
                                           (1 - alpha) * status.data_points_per_minute)
            
            # 更新错误率
            if data_points > 0:
                current_error_rate = errors / data_points
                status.error_rate = alpha * current_error_rate + (1 - alpha) * status.error_rate
            
            # 更新响应时间
            if response_time_ms > 0:
                status.response_time_ms = alpha * response_time_ms + (1 - alpha) * status.response_time_ms
            
            # 更新数据质量评分
            # 简单算法：基础分100，错误率每1%扣2分，响应时间每100ms扣1分
            quality_score = 100
            quality_score -= status.error_rate * 200  # 错误率扣分
            quality_score -= status.response_time_ms / 100  # 响应时间扣分
            
            # 限制在0-100范围内
            status.data_quality_score = max(0, min(100, quality_score))
            
            # 如果之前状态是未知，现在有数据了，更新状态
            if status.status == HealthStatus.UNKNOWN:
                status.status = HealthStatus.HEALTHY
            
            # 更新时间戳
            status.timestamp = datetime.now()
            
            # 存储状态到数据库
            self._store_data_flow_status(status)
            
            self.logger.debug(f"更新数据点: {process_name}, 点数: {data_points}, 错误: {errors}, 响应时间: {response_time_ms}ms")
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新数据点失败: {e}")
            return False
    
    def get_data_flow_status(self, process_name: str) -> Optional[Dict[str, Any]]:
        """获取数据流状态"""
        if process_name not in self.data_flow_status:
            return None
        
        status = self.data_flow_status[process_name]
        
        return {
            "process_name": status.process_name,
            "status": status.status.value,
            "data_points_per_minute": status.data_points_per_minute,
            "last_data_time": status.last_data_time.isoformat() if status.last_data_time else None,
            "error_rate": status.error_rate,
            "response_time_ms": status.response_time_ms,
            "data_quality_score": status.data_quality_score,
            "timestamp": status.timestamp.isoformat()
        }
    
    def get_all_data_flow_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据流状态"""
        result = {}
        for process_name, status in self.data_flow_status.items():
            result[process_name] = {
                "process_name": status.process_name,
                "status": status.status.value,
                "data_points_per_minute": status.data_points_per_minute,
                "last_data_time": status.last_data_time.isoformat() if status.last_data_time else None,
                "error_rate": status.error_rate,
                "response_time_ms": status.response_time_ms,
                "data_quality_score": status.data_quality_score,
                "timestamp": status.timestamp.isoformat()
            }
        return result
    
    def get_alerts(self, process_name: str, limit: int = 10, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """获取告警"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if include_resolved:
                cursor.execute('''
                    SELECT * FROM data_acquisition_alerts
                    WHERE process_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (process_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM data_acquisition_alerts
                    WHERE process_name = ? AND resolved = 0
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (process_name, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                alert_dict = dict(row)
                # 解析JSON字段
                if 'details' in alert_dict and alert_dict['details']:
                    try:
                        alert_dict['details'] = json.loads(alert_dict['details'])
                    except:
                        alert_dict['details'] = {}
                result.append(alert_dict)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取告警失败: {e}")
            return []
    
    def get_all_alerts(self, limit: int = 50, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """获取所有告警"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if include_resolved:
                cursor.execute('''
                    SELECT * FROM data_acquisition_alerts
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            else:
                cursor.execute('''
                    SELECT * FROM data_acquisition_alerts
                    WHERE resolved = 0
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                alert_dict = dict(row)
                # 解析JSON字段
                if 'details' in alert_dict and alert_dict['details']:
                    try:
                        alert_dict['details'] = json.loads(alert_dict['details'])
                    except:
                        alert_dict['details'] = {}
                result.append(alert_dict)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取所有告警失败: {e}")
            return []
    
    def resolve_alert(self, alert_id: int) -> bool:
        """解决告警"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE data_acquisition_alerts
                SET resolved = 1, resolved_time = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), alert_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"解决告警 ID: {alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")
            return False
    
    def get_data_flow_history(self, process_name: str, hours: int = 24, interval_minutes: int = 5) -> List[Dict[str, Any]]:
        """获取数据流历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 使用时间窗口聚合查询
            cursor.execute('''
                SELECT 
                    process_name,
                    strftime('%Y-%m-%dT%H:%M:00', timestamp) as time_window,
                    AVG(data_points_per_minute) as avg_data_points,
                    AVG(error_rate) as avg_error_rate,
                    AVG(response_time_ms) as avg_response_time,
                    AVG(data_quality_score) as avg_quality_score,
                    MAX(status) as status
                FROM data_flow_status
                WHERE process_name = ? AND timestamp BETWEEN ? AND ?
                GROUP BY process_name, time_window
                ORDER BY time_window DESC
            ''', (process_name, start_time.isoformat(), end_time.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取数据流历史记录失败: {e}")
            return []
    
    def get_data_flow_statistics(self, process_name: str, hours: int = 24) -> Dict[str, Any]:
        """获取数据流统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 查询统计信息
            cursor.execute('''
                SELECT 
                    COUNT(*) as sample_count,
                    AVG(data_points_per_minute) as avg_data_points,
                    MAX(data_points_per_minute) as max_data_points,
                    MIN(data_points_per_minute) as min_data_points,
                    AVG(error_rate) as avg_error_rate,
                    MAX(error_rate) as max_error_rate,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(response_time_ms) as max_response_time,
                    AVG(data_quality_score) as avg_quality_score,
                    MIN(data_quality_score) as min_quality_score
                FROM data_flow_status
                WHERE process_name = ? AND timestamp BETWEEN ? AND ?
            ''', (process_name, start_time.isoformat(), end_time.isoformat()))
            
            row = cursor.fetchone()
            
            # 查询状态分布
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM data_flow_status
                WHERE process_name = ? AND timestamp BETWEEN ? AND ?
                GROUP BY status
            ''', (process_name, start_time.isoformat(), end_time.isoformat()))
            
            status_rows = cursor.fetchall()
            
            # 查询告警统计
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM data_acquisition_alerts
                WHERE process_name = ? AND timestamp BETWEEN ? AND ?
                GROUP BY severity
            ''', (process_name, start_time.isoformat(), end_time.isoformat()))
            
            alert_rows = cursor.fetchall()
            
            conn.close()
            
            # 构建结果
            if row and row[0] > 0:
                stats = {
                    "process_name": process_name,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "hours": hours
                    },
                    "samples": row[0],
                    "data_points": {
                        "avg": row[1],
                        "max": row[2],
                        "min": row[3]
                    },
                    "error_rate": {
                        "avg": row[4],
                        "max": row[5]
                    },
                    "response_time": {
                        "avg": row[6],
                        "max": row[7]
                    },
                    "quality_score": {
                        "avg": row[8],
                        "min": row[9]
                    },
                    "status_distribution": {
                        status: count for status, count in status_rows
                    },
                    "alert_distribution": {
                        severity: count for severity, count in alert_rows
                    }
                }
                
                # 获取当前状态
                if process_name in self.data_flow_status:
                    current = self.data_flow_status[process_name]
                    stats["current"] = {
                        "status": current.status.value,
                        "data_points_per_minute": current.data_points_per_minute,
                        "error_rate": current.error_rate,
                        "response_time_ms": current.response_time_ms,
                        "data_quality_score": current.data_quality_score,
                        "last_data_time": current.last_data_time.isoformat() if current.last_data_time else None
                    }
                
                return stats
            else:
                return {
                    "process_name": process_name,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "hours": hours
                    },
                    "samples": 0,
                    "message": "No data available for the specified time range"
                }
            
        except Exception as e:
            self.logger.error(f"获取数据流统计信息失败: {e}")
            return {
                "process_name": process_name,
                "error": str(e)
            }

# 全局实例
data_acquisition_monitor = DataAcquisitionMonitor()