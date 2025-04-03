import requests
import json  # 导入json模块以解析JSON数据

# 定义第一个URL
url = 'https://limsuat.midea.com/LIMS-Server/MPLM_Service_Gateway/TokenGenerator/getToken'
# 定义要发送的数据
headers = {
    "__TokenAuthorization_UserName_": "ex_dengcc2",
    "__TokenAuthorization_Function_": "getTestForm"
}  # 设置请求头
response = requests.post(url, headers=headers)

# 打印响应状态码和响应内容
print("Response Status Code:", response.status_code)
print("Response Content:", response.text)

# 解析JSON响应并提取token
try:
    json_response = json.loads(response.text)  # 将响应文本转换为JSON对象
    token = json_response["token"]  # 从JSON对象中提取token
except json.JSONDecodeError:
    print("Error decoding JSON response")
    token = None  # 如果JSON解析失败，设置token为None

# 定义第二个URL
url = 'https://limsuat.midea.com/LIMS-Server/MPLM_Service_Gateway/raclimsRestfulController/getTestForm'
# 定义要发送的数据
headers = {
    "__TokenAuthorization_UserName_": "ex_dengcc2",
    "__TokenAuthorization_Function_": "getTestForm",
    "__TokenAuthorization_UID_": token  # 使用提取的token
}  # 设置请求头
body = {"EntrustmentOrder": "ST2024070117"}

response = requests.post(url, headers=headers, json=body)  # 注意使用json参数发送JSON数据

# 打印响应状态码和响应内容
print("Response Status Code:", response.status_code)
print("Response Content:", response.text)