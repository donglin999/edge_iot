import json
import pickle

# with open('D:/Person/Code/rotating_equipment/hefei/pentu/device_map.json', 'r', encoding='utf_8_sig') as load_f:
#     config_dict = json.load(load_f)
#     for key,value in config_dict.items():
#         pickle_path = 'D:/Person/Code/rotating_equipment/hefei/pentu/config/'+'pickle_'+key
#         df = open(pickle_path, 'wb')
#         pickle.dump(value, df)
#         df.close()
        
df = open('D:/Person/Code/rotating_equipment/hefei/pentu/config/'+'pickle_'+'W3_1', 'rb')
data = pickle.load(df)
print(data)
df.close()
