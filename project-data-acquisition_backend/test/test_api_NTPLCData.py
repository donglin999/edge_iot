import requests
import json

# 定义URL
url = 'http://127.0.0.1:5000/NTPLCData'

# 定义要发送的数据
data = {
 "State": "运行",
 "Devicemode": "自动",
 "Workingmode":"测量",
 "Sendtime":"2024-05-24 10:00:01"
}

# 发送POST请求
headers = {'Content-Type': 'application/json'}  # 设置请求头，告诉服务器我们正在发送JSON数据
response = requests.post(url, data=json.dumps(data), headers=headers)

# 打印响应状态码和响应内容
print("Response Status Code:", response.status_code)
print("Response Content:", response.text)