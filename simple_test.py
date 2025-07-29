#!/usr/bin/env python3
"""
简单测试脚本
"""

import socket
import time

def test_connection():
    """测试连接"""
    print("=== 测试后端连接 ===")
    
    # 测试端口连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    
    try:
        result = sock.connect_ex(('localhost', 8000))
        if result == 0:
            print("✓ 端口8000可以连接")
        else:
            print("✗ 端口8000无法连接")
    except Exception as e:
        print(f"✗ 连接测试失败: {e}")
    finally:
        sock.close()
    
    # 测试HTTP请求
    try:
        import urllib.request
        start_time = time.time()
        response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        print(f"✓ HTTP请求成功，耗时: {duration:.2f}ms")
        print(f"  状态码: {response.getcode()}")
    except Exception as e:
        print(f"✗ HTTP请求失败: {e}")

if __name__ == "__main__":
    test_connection() 