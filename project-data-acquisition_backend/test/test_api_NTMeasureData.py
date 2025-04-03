import requests
import json

# 定义URL
url = 'http://127.0.0.1:5000/NTMeasureData'

# 定义要发送的数据
data = {'Params': [{'Group': '', 'Lower': '21.9770', 'Name': '高度1', 'Nominal': '21.9870', 'Result': 'OK', 'Upper': '21.9970', 'Value': '21.9850'}, {'Group': '', 'Lower': '0.0000', 'Name': '内径圆柱度', 'Nominal': '0.0000', 'Result': 'OK', 'Upper': '0.0020', 'Value': '0.0008'}, {'Group': '', 'Lower': '0.0000', 'Name': '内径直角度', 'Nominal': '0.0000', 'Result': 'OK', 'Upper': '0.0020', 'Value': '0.0005'}, {'Group': '', 'Lower': '32.8740', 'Name': '外径1', 'Nominal': '32.8840', 'Result': 'OK', 'Upper': '32.8940', 'Value': '32.8835'}, {'Group': '', 'Lower': '32.8740', 'Name': '外径2', 'Nominal': '32.8840', 'Result': 'OK', 'Upper': '32.8940', 'Value': '32.8845'}, {'Group': 'T', 'Lower': '32.8740', 'Name': '外径实际值', 'Nominal': '32.8840', 'Result': 'OK', 'Upper': '32.8940', 'Value': '32.8835'}, {'Group': '', 'Lower': '0.0000', 'Name': '外径真圆度', 'Nominal': '0.0000', 'Result': 'OK', 'Upper': '0.0040', 'Value': '0.0006'}, {'Group': '', 'Lower': '0.0000', 'Name': '外径圆柱度', 'Nominal': '0.0000', 'Result': 'OK', 'Upper': '0.0040', 'Value': '0.0015'}, {'Group': '', 'Lower': '21.9770', 'Name': '高度2', 'Nominal': '21.9870', 'Result': 'OK', 'Upper': '21.9970', 'Value': '21.9846'}, {'Group': '', 'Lower': '21.9770', 'Name': '高度3', 'Nominal': '21.9870', 'Result': 'OK', 'Upper': '21.9970', 'Value': '21.9844'}, {'Group': '', 'Lower': '21.9770', 'Name': '高度4', 'Nominal': '21.9870', 'Result': 'OK', 'Upper': '21.9970', 'Value': '21.9842'}, {'Group': 'L', 'Lower': '21.9770', 'Name': '高度实际值', 'Nominal': '21.9870', 'Result': 'OK', 'Upper': '21.9970', 'Value': '21.9862'}, {'Group': '', 'Lower': '20.7900', 'Name': '内径1', 'Nominal': '20.8000', 'Result': 'OK', 'Upper': '20.8100', 'Value': '20.7992'}, {'Group': '', 'Lower': '20.7900', 'Name': '内径2', 'Nominal': '20.8000', 'Result': 'OK', 'Upper': '20.8100', 'Value': '20.8002'}, {'Group': 'O', 'Lower': '20.7900', 'Name': '内径实际值', 'Nominal': '20.8000', 'Result': 'OK', 'Upper': '20.8100', 'Value': '20.7992'}, {'Group': '', 'Lower': '0.0000', 'Name': '内径真圆度', 'Nominal': '0.0000', 'Result': 'OK', 'Upper': '0.0020', 'Value': '0.0003'}], 'ProgramCode': 'SK103-C-PC', 'ProgramNo': '108', 'Result': 'OK', 'Type': 'PC', "Operate_time": "2024-05-24 10:00:01", 'Workpiece_id': ''}

# 发送POST请求
headers = {'Content-Type': 'application/json'}  # 设置请求头，告诉服务器我们正在发送JSON数据
response = requests.post(url, data=json.dumps(data), headers=headers)

# 打印响应状态码和响应内容
print("Response Status Code:", response.status_code)
print("Response Content:", response.text)