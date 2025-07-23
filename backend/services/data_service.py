import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models.data_models import DataPoint, DataQueryRequest, DataQueryResponse, DeviceInfo, DataStats

logger = logging.getLogger(__name__)

class DataService:
    """Service for managing data acquisition and querying from real sources"""
    
    def __init__(self):
        self.influx_client = None
        self.influx_query_api = None
        self.bucket = "iot-data"
        self.org = "iot-org"
        self._initialize_influx()
    
    def _initialize_influx(self):
        """Initialize InfluxDB client"""
        try:
            from influxdb_client import InfluxDBClient
            import os
            
            url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
            token = os.getenv("INFLUXDB_TOKEN", "iot-token-12345")
            org = os.getenv("INFLUXDB_ORG", "iot-org")
            bucket = os.getenv("INFLUXDB_BUCKET", "iot-data")
            
            self.org = org
            self.bucket = bucket
            
            self.influx_client = InfluxDBClient(
                url=url,
                token=token,
                org=org
            )
            self.influx_query_api = self.influx_client.query_api()
            
            # 测试连接
            health = self.influx_client.health()
            logger.info(f"InfluxDB client initialized successfully, status: {health.status}")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            self.influx_client = None
            self.influx_query_api = None

    async def get_realtime_data(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time data from InfluxDB"""
        try:
            if not self.influx_query_api:
                return {"data": [], "total": 0, "message": "InfluxDB not available"}
            
            # 构建Flux查询
            flux_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -5m)
            |> filter(fn: (r) => r["_measurement"] =~ /.*/)
            '''
            
            # 添加设备过滤
            if query_params.get('device') and query_params['device']:
                flux_query += f'|> filter(fn: (r) => r["device_id"] == "{query_params["device"]}")\n'
            
            # 添加测点过滤
            if query_params.get('measurements') and query_params['measurements']:
                measurements = query_params['measurements']
                if isinstance(measurements, list) and len(measurements) > 0:
                    measurement_filter = ' or '.join([f'r["_field"] == "{m}"' for m in measurements])
                    flux_query += f'|> filter(fn: (r) => {measurement_filter})\n'
            
            # 限制结果
            limit = query_params.get('limit', 100)
            flux_query += f'|> limit(n: {limit})\n'
            flux_query += '|> sort(columns: ["_time"], desc: true)'
            
            logger.info(f"Executing Flux query: {flux_query}")
            
            # 执行查询
            result = self.influx_query_api.query(flux_query)
            
            # 解析结果
            data_points = []
            for table in result:
                for record in table.records:
                    data_point = {
                        "timestamp": record.get_time().isoformat() if record.get_time() else None,
                        "device": record.values.get("device_id", "unknown"),
                        "parameter": record.get_field(),
                        "value": str(record.get_value()),
                        "status": "normal" if record.get_value() is not None else "error",
                        "measurement": record.get_measurement(),
                        "unit": record.values.get("unit", "")
                    }
                    data_points.append(data_point)
            
            return {
                "data": data_points,
                "total": len(data_points),
                "query": flux_query
            }
            
        except Exception as e:
            logger.error(f"Error querying real-time data: {e}")
            return {"data": [], "total": 0, "error": str(e)}

    async def get_statistics(self) -> Dict[str, Any]:
        """Get real data statistics from InfluxDB"""
        try:
            if not self.influx_query_api:
                return {
                    "today_points": 0,
                    "realtime_rate": 0.0,
                    "total_devices": 0,
                    "active_devices": 0
                }
            
            # 获取今日数据点数量
            today_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: today())
            |> count()
            |> group()
            |> sum(column: "_value")
            '''
            
            # 获取最近1小时数据速率
            rate_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -1h)
            |> count()
            |> group()
            |> sum(column: "_value")
            '''
            
            # 获取设备数量
            device_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -24h)
            |> group(columns: ["device_id"])
            |> distinct(column: "device_id")
            |> count()
            '''
            
            today_result = self.influx_query_api.query(today_query)
            rate_result = self.influx_query_api.query(rate_query)
            device_result = self.influx_query_api.query(device_query)
            
            today_points = 0
            hourly_points = 0
            device_count = 0
            
            # 解析今日数据点
            for table in today_result:
                for record in table.records:
                    today_points = record.get_value() or 0
                    break
            
            # 解析小时数据点
            for table in rate_result:
                for record in table.records:
                    hourly_points = record.get_value() or 0
                    break
            
            # 解析设备数量
            for table in device_result:
                for record in table.records:
                    device_count = record.get_value() or 0
                    break
            
            # 计算实时速率（每秒数据点）
            realtime_rate = round(hourly_points / 3600.0, 2) if hourly_points > 0 else 0.0
            
            return {
                "today_points": today_points,
                "realtime_rate": realtime_rate,
                "total_devices": device_count,
                "active_devices": device_count  # 简化处理，认为所有设备都活跃
            }
            
        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            return {
                "today_points": 0,
                "realtime_rate": 0.0,
                "total_devices": 0,
                "active_devices": 0
            }

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get real device list from InfluxDB"""
        try:
            if not self.influx_query_api:
                return []
            
            # 查询所有设备及其最新数据时间
            query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -24h)
            |> group(columns: ["device_id"])
            |> last()
            |> group()
            '''
            
            result = self.influx_query_api.query(query)
            devices = []
            device_ids = set()
            
            for table in result:
                for record in table.records:
                    device_id = record.values.get("device_id")
                    if device_id and device_id not in device_ids:
                        device_ids.add(device_id)
                        
                        # 计算最后更新时间距现在的时间
                        last_time = record.get_time()
                        now = datetime.now(last_time.tzinfo) if last_time else datetime.now()
                        is_online = False
                        
                        if last_time:
                            time_diff = (now - last_time).total_seconds()
                            is_online = time_diff < 300  # 5分钟内有数据认为在线
                        
                        device = {
                            "id": device_id,
                            "name": device_id,
                            "type": "Data Collector",
                            "status": "online" if is_online else "offline",
                            "last_update": last_time.isoformat() if last_time else None
                        }
                        devices.append(device)
            
            logger.info(f"Found {len(devices)} devices from InfluxDB")
            return devices
            
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []

    async def get_measurements(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get measurements (fields) from InfluxDB"""
        try:
            if not self.influx_query_api:
                return []
            
            # 构建查询
            query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -24h)
            '''
            
            if device_id:
                query += f'|> filter(fn: (r) => r["device_id"] == "{device_id}")\n'
            
            query += '''
            |> group(columns: ["_field"])
            |> distinct(column: "_field")
            |> group()
            '''
            
            result = self.influx_query_api.query(query)
            measurements = []
            
            for table in result:
                for record in table.records:
                    field_name = record.get_field()
                    if field_name:
                        measurement = {
                            "name": field_name,
                            "description": field_name.replace("_", " ").title(),
                            "type": "numeric",
                            "unit": ""
                        }
                        measurements.append(measurement)
            
            logger.info(f"Found {len(measurements)} measurements for device {device_id}")
            return measurements
            
        except Exception as e:
            logger.error(f"Error getting measurements: {e}")
            return []

    async def export_data(self, query_params: Dict[str, Any], format_type: str = "csv") -> str:
        """Export data in specified format"""
        try:
            # 获取数据
            data_result = await self.get_realtime_data(query_params)
            data_points = data_result.get("data", [])
            
            if format_type.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if data_points:
                    fieldnames = data_points[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data_points)
                
                return output.getvalue()
            else:
                import json
                return json.dumps(data_points, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return ""

    async def get_database_status(self) -> Dict[str, Any]:
        """Get real database status"""
        try:
            if not self.influx_client:
                return {
                    "status": "disconnected",
                    "message": "InfluxDB client not initialized",
                    "connected": False
                }
            
            # 测试连接
            health = self.influx_client.health()
            
            # 测试查询能力
            test_query = f'from(bucket: "{self.bucket}") |> range(start: -1m) |> limit(n: 1)'
            try:
                self.influx_query_api.query(test_query)
                query_ok = True
            except:
                query_ok = False
            
            return {
                "status": "connected" if health.status == "pass" else "error",
                "message": health.message or "Connected",
                "connected": health.status == "pass",
                "version": getattr(health, 'version', 'unknown'),
                "bucket": self.bucket,
                "org": self.org,
                "query_capable": query_ok
            }
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return {
                "status": "error",
                "message": str(e),
                "connected": False
            }
    
    async def query_data(self, request: DataQueryRequest) -> DataQueryResponse:
        """Query data from InfluxDB"""
        try:
            if not self.influx_client:
                raise Exception("InfluxDB client not initialized")
            
            # 构建查询条件
            query = self._build_query(request)
            
            # 执行查询
            result = self.influx_client.query_api().query(query)
            
            # 解析结果
            data_points = []
            for table in result:
                for record in table.records:
                    data_point = DataPoint(
                        timestamp=record.get_time(),
                        device_id=record.get_field("device_id") or record.get_measurement(),
                        point_name=record.get_field("point_name") or record.get_field(),
                        value=record.get_value(),
                        unit=record.get_field("unit"),
                        quality=record.get_field("quality", "good")
                    )
                    data_points.append(data_point)
            
            return DataQueryResponse(
                data=data_points,
                total_count=len(data_points),
                start_time=request.start_time,
                end_time=request.end_time
            )
        except Exception as e:
            logger.error(f"Error querying data: {e}")
            raise

    def _build_query(self, request: DataQueryRequest) -> str:
        """构建InfluxDB查询语句"""
        query_parts = ['from(bucket: "iot_data")']
        
        # 时间范围
        if request.start_time:
            query_parts.append(f'|> range(start: {request.start_time.isoformat()}')
        else:
            query_parts.append('|> range(start: -1h')
            
        if request.end_time:
            query_parts.append(f', stop: {request.end_time.isoformat()})')
        else:
            query_parts.append(')')
        
        # 设备过滤
        if request.devices:
            device_filter = ' or '.join([f'r["device_id"] == "{device}"' for device in request.devices])
            query_parts.append(f'|> filter(fn: (r) => {device_filter})')
        
        # 数据点过滤
        if request.points:
            point_filter = ' or '.join([f'r["_field"] == "{point}"' for point in request.points])
            query_parts.append(f'|> filter(fn: (r) => {point_filter})')
        
        # 限制结果数量
        if request.limit:
            query_parts.append(f'|> limit(n: {request.limit})')
        
        return '\n'.join(query_parts)

    async def get_data_statistics(self) -> DataStats:
        """Get data statistics from InfluxDB"""
        try:
            if not self.influx_client:
                # 如果InfluxDB不可用，返回基本统计信息
                return DataStats(
                    total_devices=0,
                    active_devices=0,
                    total_measurements=0,
                    total_data_points=0,
                    data_rate_per_second=0.0,
                    storage_size_mb=0.0,
                    oldest_data=None,
                    newest_data=None
                )
            
            # 查询设备总数
            device_query = '''
            from(bucket: "iot_data")
            |> range(start: -24h)
            |> group(columns: ["device_id"])
            |> count()
            |> group()
            |> sum()
            '''
            
            # 查询数据点总数
            data_points_query = '''
            from(bucket: "iot_data")
            |> range(start: -24h)
            |> count()
            '''
            
            # 查询最新数据时间
            latest_data_query = '''
            from(bucket: "iot_data")
            |> range(start: -24h)
            |> last()
            '''
            
            # 执行查询
            device_result = self.influx_client.query_api().query(device_query)
            data_points_result = self.influx_client.query_api().query(data_points_query)
            latest_result = self.influx_client.query_api().query(latest_data_query)
            
            # 解析结果
            total_devices = 0
            total_data_points = 0
            newest_data = None
            
            if device_result:
                for table in device_result:
                    for record in table.records:
                        total_devices = record.get_value()
            
            if data_points_result:
                for table in data_points_result:
                    for record in table.records:
                        total_data_points = record.get_value()
            
            if latest_result:
                for table in latest_result:
                    for record in table.records:
                        newest_data = record.get_time()
            
            # 计算数据速率（基于最近1小时的数据）
            rate_query = '''
            from(bucket: "iot_data")
            |> range(start: -1h)
            |> count()
            '''
            rate_result = self.influx_client.query_api().query(rate_query)
            hourly_data_points = 0
            if rate_result:
                for table in rate_result:
                    for record in table.records:
                        hourly_data_points = record.get_value()
            
            data_rate_per_second = hourly_data_points / 3600.0 if hourly_data_points > 0 else 0.0
            
            return DataStats(
                total_devices=total_devices,
                active_devices=total_devices,  # 简化处理，实际应该查询活跃设备
                total_measurements=total_devices * 10,  # 估算每个设备10个测点
                total_data_points=total_data_points,
                data_rate_per_second=data_rate_per_second,
                storage_size_mb=total_data_points * 0.001,  # 估算存储大小
                oldest_data=datetime.now() - timedelta(days=7),  # 简化处理
                newest_data=newest_data
            )
        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            # 返回默认值而不是抛出异常
            return DataStats(
                total_devices=0,
                active_devices=0,
                total_measurements=0,
                total_data_points=0,
                data_rate_per_second=0.0,
                storage_size_mb=0.0,
                oldest_data=None,
                newest_data=None
            )

    async def get_devices(self) -> Dict[str, Any]:
        """Get device list from InfluxDB"""
        try:
            if not self.influx_client:
                return {"devices": [], "total_count": 0}
            
            # 查询设备列表
            query = '''
            from(bucket: "iot_data")
            |> range(start: -24h)
            |> group(columns: ["device_id"])
            |> last()
            |> group()
            '''
            
            result = self.influx_client.query_api().query(query)
            devices = []
            
            for table in result:
                for record in table.records:
                    device_id = record.get_field("device_id") or record.get_measurement()
                    device_info = DeviceInfo(
                        device_id=device_id,
                        device_name=device_id,  # 简化处理
                        device_type="unknown",
                        status="online",  # 简化处理
                        last_update=record.get_time(),
                        point_count=10  # 简化处理
                    )
                    devices.append(device_info)
            
            return {
                "devices": devices,
                "total_count": len(devices)
            }
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return {"devices": [], "total_count": 0}

    async def get_points(self, device_id: str) -> List[str]:
        """Get points for a device from InfluxDB"""
        try:
            if not self.influx_client:
                return []
            
            # 查询指定设备的数据点
            query = f'''
            from(bucket: "iot_data")
            |> range(start: -24h)
            |> filter(fn: (r) => r["device_id"] == "{device_id}")
            |> group(columns: ["_field"])
            |> last()
            |> group()
            '''
            
            result = self.influx_client.query_api().query(query)
            points = []
            
            for table in result:
                for record in table.records:
                    field_name = record.get_field()
                    if field_name and field_name not in ["device_id", "point_name", "unit", "quality"]:
                        points.append(field_name)
            
            return points
        except Exception as e:
            logger.error(f"Error getting points: {e}")
            return []

    async def get_database_status(self) -> Dict[str, Any]:
        """Get database status"""
        try:
            if self.influx_client is None:
                return {
                    "status": "disconnected",
                    "message": "InfluxDB client not initialized",
                    "connected": False
                }
            
            # Test connection
            health = self.influx_client.health()
            return {
                "status": health.status,
                "message": health.message,
                "connected": True,
                "version": health.version
            }
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return {
                "status": "error",
                "message": str(e),
                "connected": False
            }