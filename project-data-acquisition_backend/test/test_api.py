import requests
import json

# 定义URL
url = 'http://127.0.0.1:5000/Data'
# 定义要发送的数据
data = {
  "prototype_type": "非手板",
  "test_item": [
    {
      "testItemVersion": "G.2",
      "testFieldDictionaryGroups": [
        {
          "groupName": "电寿命",
          "groupInternalName": "ATTRIBUTE24112652000663824",
          "location": "表身",
          "testFieldDictionarys": [
            {
              "attributeDisplayName": "释放时间",
              "paraUnit": "ms",
              "location": "表身",
              "attributeName": "ATTRIBUTE24112652000663830"
            },
            {
              "attributeDisplayName": "释放电压",
              "paraUnit": "V",
              "location": "表身",
              "attributeName": "ATTRIBUTE24112652000663828"
            },
            {
              "attributeDisplayName": "吸合时间",
              "paraUnit": "ms",
              "location": "表身",
              "attributeName": "ATTRIBUTE24112652000663829"
            },
            {
              "attributeDisplayName": "接触电阻",
              "paraUnit": "mΩ",
              "location": "表身",
              "attributeName": "ATTRIBUTE24112652000663826"
            },
            {
              "attributeDisplayName": "动作电压",
              "paraUnit": "V",
              "location": "表身",
              "attributeName": "ATTRIBUTE24112652000663827"
            },
            {
              "attributeDisplayName": "线圈电阻",
              "paraUnit": "Ω",
              "location": "表身",
              "attributeName": "ATTRIBUTE24112652000663825"
            }
          ]
        }
      ],
      "testFormItemName": "19、电寿命",
      "station_number": "",
      "testFormItemNumber": "52013928859",
      "equipment": "EQ00003366",
      "doStandardNumber": "QM-J070.0063-2023",
      "testDesc": "",
      "sampleNumber": "1#",
      "testerName": "ex_wangli32"
    }
  ],
  "sample_number": "P0000003286698",
  "order_number": "ST2024120050",
  "time": "2024-12-05 15:32:46"
}
# 发送POST请求
headers = {'Content-Type': 'application/json'}  # 设置请求头，告诉服务器我们正在发送JSON数据
response = requests.post(url, data=json.dumps(data), headers=headers)

# 打印响应状态码和响应内容
print("Response Status Code:", response.status_code)
print("Response Content:", response.text)