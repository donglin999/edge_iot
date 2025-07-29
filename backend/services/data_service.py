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
                org=org,
                timeout=5000  # 设置5秒超时
            )
            self.influx_query_api = self.influx_client.query_api()
            
            # 测试连接
            health = self.influx_client.health()
            logger.info(f"InfluxDB client initialized successfully, status: {health.status}")
        except Exception as e:
            logger.warning(f"InfluxDB not available, using mock data: {e}")
            self.influx_client = None
            self.influx_query_api = None

    def _get_mock_statistics(self) -> Dict[str, Any]:
        """Get mock statistics when InfluxDB is not available"""
        import random
        from datetime import datetime, timedelta
        
        # 生成模拟数据
        now = datetime.now()
        today_points = random.randint(1000, 5000)
        realtime_rate = round(random.uniform(0.5, 2.0), 2)
        total_devices = random.randint(5, 15)
        active_devices = random.randint(3, total_devices)
        
        return {
            "today_points": today_points,
            "realtime_rate": realtime_rate,
            "total_devices": total_devices,
            "active_devices": active_devices,
            "mock_data": True
        }

    def _get_mock_devices(self) -> List[Dict[str, Any]]:
        """Get mock device list when InfluxDB is not available"""
        import random
        from datetime import datetime, timedelta
        
        device_types = ["PLC", "RTU", "DCS", "SCADA"]
        statuses = ["online", "offline", "maintenance"]
        now = datetime.now()
        
        devices = []
        for i in range(random.randint(5, 15)):
            device_id = f"DEVICE_{i+1:03d}"
            device_type = random.choice(device_types)
            status = random.choice(statuses)
            last_update = now - timedelta(minutes=random.randint(1, 60))
            
            devices.append({
                "device_id": device_id,
                "device_name": f"设备 {i+1}",
                "device_type": device_type,
                "status": status,
                "last_update": last_update.isoformat(),
                "point_count": random.randint(10, 50),
                "mock_data": True
            })
        
        return devices

    def _get_mock_realtime_data(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get mock real-time data when InfluxDB is not available"""
        import random
        from datetime import datetime, timedelta
        
        # 生成模拟实时数据
        data_points = []
        now = datetime.now()
        
        # 生成10-20个数据点
        num_points = random.randint(10, 20)
        for i in range(num_points):
            timestamp = now - timedelta(seconds=i*30)  # 每30秒一个数据点
            device_id = query_params.get('device', f"DEVICE_{random.randint(1, 5):03d}")
            parameter = random.choice(["temperature", "pressure", "flow", "level", "voltage"])
            value = round(random.uniform(10, 100), 2)
            
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "device": device_id,
                "parameter": parameter,
                "value": str(value),
                "status": "normal",
                "measurement": "iot_data",
                "unit": "°C" if parameter == "temperature" else "bar" if parameter == "pressure" else "m³/h" if parameter == "flow" else "m" if parameter == "level" else "V",
                "mock_data": True
            })
        
        return {
            "data": data_points,
            "total": len(data_points),
            "mock_data": True
        }

    async def get_realtime_data(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time data from InfluxDB"""
        try:
            if not self.influx_query_api:
                logger.info("InfluxDB not available, returning mock data")
                return self._get_mock_realtime_data(query_params)
            
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
            return self._get_mock_realtime_data(query_params)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get real data statistics from InfluxDB"""
        try:
            if not self.influx_query_api:
                logger.info("InfluxDB not available, returning mock statistics")
                return self._get_mock_statistics()
            
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
            return self._get_mock_statistics()

    async def get_devices(self) -> Dict[str, Any]:
        """Get real device list from InfluxDB"""
        try:
            if not self.influx_query_api:
                logger.info("InfluxDB not available, returning mock devices")
                devices = self._get_mock_devices()
                return {
                    "devices": devices,
                    "total_count": len(devices)
                }
            
            # 查询设备列表
            query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -24h)
            |> group(columns: ["device_id"])
            |> last()
            |> group()
            '''
            
            result = self.influx_query_api.query(query)
            devices = []
            
            for table in result:
                for record in table.records:
                    device_id = record.get_field("device_id") or record.get_measurement()
                    device_info = {
                        "device_id": device_id,
                        "device_name": device_id,  # 简化处理
                        "device_type": "unknown",
                        "status": "online",  # 简化处理
                        "last_update": record.get_time().isoformat() if record.get_time() else None,
                        "point_count": 10  # 简化处理
                    }
                    devices.append(device_info)
            
            return {
                "devices": devices,
                "total_count": len(devices)
            }
            
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            devices = self._get_mock_devices()
            return {
                "devices": devices,
                "total_count": len(devices)
            }

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