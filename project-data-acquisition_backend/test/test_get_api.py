import requests
import os

# Flask 服务器的 URL
flask_server_url = 'http://127.0.0.1:5000/OrderLabel'

# 发送 GET 请求到 Flask 接口
response = requests.get(flask_server_url)

# 检查响应状态码
if response.status_code == 200:
    # 获取文件内容
    file_content = response.content

    # 获取文件名（从响应头中提取 Content-Disposition）
    content_disposition = response.headers.get('Content-Disposition')
    if content_disposition:
        file_name = content_disposition.split(';')[1].split('=')[1].strip('"')
    else:
        # 如果没有 Content-Disposition，则使用默认文件名
        file_name = 'downloaded_file.xlsx'

    # 确保保存文件的文件夹存在
    save_folder = 'test'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # 将文件内容写入到指定文件
    file_path = os.path.join(save_folder, file_name)
    with open(file_path, 'wb') as file:
        file.write(file_content)

    print(f'File saved successfully: {file_path}')
elif response.status_code == 404:
    try:
        # 尝试解析JSON响应
        error_info = response.json()
        error_message = error_info.get('error', 'Unknown error occurred.')
        print(f'Error: {error_message}')
    except ValueError:
        # 如果响应不是有效的JSON，则打印原始文本响应
        print(f'Error: Unable to parse JSON response. Raw response: {response.text}')
else:
    # 处理其他错误
    print(f'Unexpected status code: {response.status_code}')