import requests

# 文件的路径，这里应该是一个你想要上传的文件的路径
file_path = '数据地址清单.xlsx'

# Flask 应用运行的 URL 和端口（默认是 127.0.0.1:5000）
url = 'http://127.0.0.1:5000/SaveFile'
data = {"equipment": "A2202020122210041"}
# 创建一个带有文件的 POST 请求
with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files, data=data)

# 打印响应内容
print(response.status_code)
print(response.json())