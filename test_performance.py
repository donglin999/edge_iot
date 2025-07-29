#!/usr/bin/env python3
"""
性能测试脚本 - 测试API响应时间
"""

import requests
import time
import statistics

def test_api_performance():
    """测试API性能"""
    base_url = "http://localhost:8000"
    
    # 测试健康检查接口
    print("=== 测试健康检查接口 ===")
    health_times = []
    for i in range(5):
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # 转换为毫秒
            health_times.append(duration)
            print(f"  请求 {i+1}: {duration:.2f}ms")
        except Exception as e:
            print(f"  请求 {i+1}: 失败 - {e}")
    
    if health_times:
        print(f"  平均响应时间: {statistics.mean(health_times):.2f}ms")
        print(f"  最快响应时间: {min(health_times):.2f}ms")
        print(f"  最慢响应时间: {max(health_times):.2f}ms")
    
    # 测试进程状态接口
    print("\n=== 测试进程状态接口 ===")
    process_times = []
    for i in range(5):
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/api/processes/", timeout=30)
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # 转换为毫秒
            process_times.append(duration)
            print(f"  请求 {i+1}: {duration:.2f}ms")
        except Exception as e:
            print(f"  请求 {i+1}: 失败 - {e}")
    
    if process_times:
        print(f"  平均响应时间: {statistics.mean(process_times):.2f}ms")
        print(f"  最快响应时间: {min(process_times):.2f}ms")
        print(f"  最慢响应时间: {max(process_times):.2f}ms")
    
    # 测试缓存效果
    print("\n=== 测试缓存效果 ===")
    cache_times = []
    for i in range(3):
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/api/processes/", timeout=30)
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            cache_times.append(duration)
            print(f"  缓存请求 {i+1}: {duration:.2f}ms")
            time.sleep(1)  # 等待1秒
        except Exception as e:
            print(f"  缓存请求 {i+1}: 失败 - {e}")
    
    if cache_times:
        print(f"  缓存平均响应时间: {statistics.mean(cache_times):.2f}ms")
    
    # 测试清除缓存
    print("\n=== 测试清除缓存 ===")
    try:
        response = requests.post(f"{base_url}/api/processes/clear-cache", timeout=10)
        print(f"  清除缓存: {response.status_code}")
    except Exception as e:
        print(f"  清除缓存失败: {e}")

if __name__ == "__main__":
    test_api_performance() 