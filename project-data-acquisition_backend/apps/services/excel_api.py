import os
import pandas as pd
import requests
import json
from datetime import datetime


class ExcelToJsonUploader:
    def __init__(self, directory, upload_url, access_token):
        self.directory = directory
        self.upload_url = upload_url
        self.access_token = access_token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

    def find_latest_excel_file(self):
        latest_excel_file = max(
            (os.path.join(self.directory, f) for f in os.listdir(self.directory) if f.endswith(".xlsx")),
            key=os.path.getctime
        )
        return latest_excel_file

    def excel_to_json(self, excel_file):
        df = pd.read_excel(excel_file)
        json_data = df.to_json(orient='records')
        return json_data

    def upload_json(self, json_data):
        data = {
            'fileData': json_data
        }
        response = requests.post(self.upload_url, headers=self.headers, data=json.dumps(data))
        return response

    def run(self):
        latest_excel_file = self.find_latest_excel_file()
        json_data = self.excel_to_json(latest_excel_file)
        print(f"整理后的json内容：{json_data[1:-1]}")
        response = self.upload_json(json_data)

        if response.status_code == 200:
            print("文件上传成功！")
        else:
            print(f"文件上传失败，状态码：{response.status_code}，响应内容：{response.text}")


# 使用示例
if __name__ == "__main__":
    directory = r"C:\IMRC"
    upload_url = "http://10.74.135.5:5000/OrderLabel"
    # upload_url = "https://lims.midea.com/LIMS-Server/MPLM_Service_Gateway/raclimsRestfulController/upLoadFileAndData"
    access_token = "YOUR_ACCESS_TOKEN"  # 请替换为实际的访问令牌

    uploader = ExcelToJsonUploader(directory, upload_url, access_token)
    uploader.run()