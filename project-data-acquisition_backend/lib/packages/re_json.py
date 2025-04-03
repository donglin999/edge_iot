# coding: utf-8
import pandas as pd
import json

df = pd.read_excel('D:/工作文档/1预测性维护/1冲压机预测性维护项目/1武汉家用高冲预测性维护/数采程序/code_jiayongnuatong/device.xlsx',index_col=0).T
# print(df)
df.columns = df.columns.astype(str)
# print(df)
df.columns.str
# print(df)
data = df.to_dict()
# print(data)
# device_map格式化
device_map = []
for key,value in data.items():
    device_map.append(value)
data = {'device_map':device_map}


json_data = json.dumps(data,indent=4,separators=(',',':'),ensure_ascii=False)
f = open('D:/工作文档/1预测性维护/1冲压机预测性维护项目/1武汉家用高冲预测性维护/数采程序/code_jiayongnuatong/device_map.json','w', encoding='utf-8')
f.write(json_data)
f.close()
