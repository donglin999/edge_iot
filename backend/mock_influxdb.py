#!/usr/bin/env python3
"""
简单的模拟InfluxDB服务器
在端口8086上提供基本的HTTP响应来模拟InfluxDB API
"""
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
import random

class MockInfluxDBHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "pass",
                "checks": [
                    {
                        "name": "boltdb",
                        "status": "pass"
                    }
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path.startswith('/api/v2/query'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # 模拟查询响应
            mock_data = []
            now = datetime.now()
            for i in range(10):
                mock_data.append({
                    "_time": (now - timedelta(minutes=i)).isoformat(),
                    "_measurement": "temperature",
                    "_field": "value",
                    "_value": 20 + random.random() * 10,
                    "device": f"device_{i % 3 + 1}"
                })
            self.wfile.write(json.dumps(mock_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path.startswith('/api/v2/write'):
            self.send_response(204)  # No Content - write successful
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """禁用默认的日志输出"""
        pass

def start_mock_influxdb():
    """启动模拟InfluxDB服务器"""
    server = HTTPServer(('localhost', 8086), MockInfluxDBHandler)
    print("Mock InfluxDB server started on http://localhost:8086")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMock InfluxDB server stopped")
        server.shutdown()

if __name__ == "__main__":
    start_mock_influxdb()