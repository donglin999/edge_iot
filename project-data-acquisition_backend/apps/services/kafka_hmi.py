from kafka import KafkaConsumer
from json import loads
import modbus_tk.modbus_tcp as mt
import modbus_tk.defines as cst
import time

from utils.baseLogger import Log


class KafkaHMI:
    def __init__(self, bootstrap_servers, topic, hmi_ip, hmi_port, group_id='my-group2'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.hmi_ip = hmi_ip
        self.hmi_port = hmi_port
        self.D312 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.D313 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.D314 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.D315 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.D316 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def kafka_hmi(self):
        while True:
            try:
                consumer = KafkaConsumer(
                    self.topic,
                    bootstrap_servers=self.bootstrap_servers,
                    auto_offset_reset='earliest',  # 从最早的记录开始消费
                    # auto_offset_reset='latest',
                    enable_auto_commit=True,  # 允许自动提交偏移量
                    group_id='kafka_group_U_PHM_B-' + str(time.time()),  # 消费者组ID
                    value_deserializer=lambda m: loads(m.decode('utf-8'))  # 消息值反序列化
                )
                print(f"kafka服务器连接完成，服务器地址：{self.bootstrap_servers}，订阅主题：{self.topic}")
                break
            except Exception as e:
                Log().printError(f"kafka服务器连接报错: {e}")
                print(f"kafka服务器连接报错: {e}")
                time.sleep(3)
                continue


        for message in consumer:

            print(f"Consumed message: {message.value}")
            if message.value["deviceACode"] == "A0101070001160006":
                print(f"开始整理拉床报警")
                if "拉床液压站小马达加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    print(f"拉床液压站小马达加速度均方根值偏高或值极高")
                    self.D312[0] = 1
                else:
                    print(f"拉床液压站小马达加速度均方根值正常")
                    self.D312[0] = 0
                if "拉床液压站大马达加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    print(f"拉床液压站大马达加速度均方根值偏高或值极高")
                    self.D312[1] = 1
                else:
                    print(f"拉床液压站大马达加速度均方根值正常")
                    self.D312[1] = 0
                if "拉床液压站液压油温度rms值偏高或值极高" in message.value['briefDescription']:
                    print(f"拉床液压站液压油温度rms值偏高或值极高")
                    self.D312[2] = 1
                else:
                    print(f"拉床液压站液压油温度rms值正常")
                    self.D312[2] = 0
                if "拉床液压站液压油液位rms值偏低或值极低" in message.value['briefDescription']:
                    print(f"拉床液压站液压油液位rms值偏低或值极低")
                    self.D312[3] = 1
                else:
                    print(f"拉床液压站液压油液位rms值正常")
                    self.D312[3] = 0

            if message.value["deviceACode"] == "A0302010001160093":
                print(f"开始整理脱油机冷却箱水位rms值偏高或值极高报警")
                if "脱油机冷却箱水位rms值偏高或值极高" in message.value['briefDescription']:
                    print(f"脱油机冷却箱水位rms值偏高或值极高")
                    self.D312[4] = 1
                else:
                    print(f"脱油机冷却箱水位rms值偏高或值极高正常")
                    self.D312[4] = 0

            if message.value["deviceACode"] == "A0101050003160110":
                if "平面磨上轴涡轮加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    print(f"平面磨上轴涡轮加速度均方根值偏高或值极高")
                    self.D312[5] = 1
                else:
                    print(f"平面磨上轴涡轮加速度均方根值偏高或值极高正常")
                    self.D312[5] = 0
                if "平面磨冷却液进水管温度平均值偏高或值极高" in message.value['briefDescription']:
                    print(f"平面磨冷却液进水管温度平均值偏高或值极高")
                    self.D312[6] = 1
                else:
                    print(f"平面磨冷却液进水管温度平均值偏高或值极高正常")
                    self.D312[6] = 0
                if "平面磨上轴涡杆温度平均值偏高或值极高" in message.value['briefDescription']:
                    print(f"平面磨上轴涡杆温度平均值偏高或值极高")
                    self.D312[7] = 1
                else:
                    print(f"平面磨上轴涡杆温度平均值偏高或值极高正常")
                    self.D312[7] = 0
                if "平面磨上砂轮轴温度平均值偏高或值极高" in message.value['briefDescription']:
                    print(f"平面磨上砂轮轴温度平均值偏高或值极高")
                    self.D312[8] = 1
                else:
                    print(f"平面磨上砂轮轴温度平均值偏高或值极高正常")
                    self.D312[8] = 0
                if "平面磨研磨腔温度平均值偏高或值极高" in message.value['briefDescription']:
                    print(f"平面磨研磨腔温度平均值偏高或值极高")
                    self.D312[9] = 1
                else:
                    print(f"平面磨研磨腔温度平均值偏高或值极高正常")
                    self.D312[9] = 0

            if message.value["deviceACode"] == "A0101050002160018":
                if "内园磨1#磨头加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    self.D312[10] = 1
                else:
                    self.D312[10] = 0
                if "内园磨1#磨头电机加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    self.D312[11] = 1
                else:
                    self.D312[11] = 0
                if "内园磨1#工件主轴加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    self.D312[12] = 1
                else:
                    self.D312[12] = 0
                if "内园磨1#工件主轴电机加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    self.D312[13] = 1
                else:
                    self.D312[13] = 0
                if "内园磨1#磨头主轴轴承BPFI值偏高或值极高" in message.value['briefDescription']:
                    self.D312[14] = 1
                else:
                    self.D312[14] = 0
                if "内园磨1#磨头加速度均方根值偏高或值极高" in message.value['briefDescription']:
                    self.D312[15] = 1
                else:
                    self.D312[15] = 0
                if "内园磨1#磨头主轴轴承BPFO值偏高或值极高" in message.value['briefDescription']:
                    self.D313[0] = 1
                else:
                    self.D313[0] = 0
                if "内园磨1#工件主轴轴承BPFI值偏高或值极高" in message.value['briefDescription']:
                    self.D313[1] = 1
                else:
                    self.D313[1] = 0
                if "内园磨1#工件主轴轴承BPFO值偏高或值极高" in message.value['briefDescription']:
                    self.D313[2] = 1
                else:
                    self.D313[2] = 0
                if "内园磨1#磨头油雾润滑滴油速度rms值偏低或值极低" in message.value['briefDescription']:
                    self.D313[3] = 1
                else:
                    self.D313[3] = 0
                if "内圆磨1#磨头温度均值偏高或值极高" in message.value['briefDescription']:
                    self.D313[4] = 1
                else:
                    self.D313[4] = 0
                if "内圆磨1#磨头电机温度均值偏高或值极高" in message.value['briefDescription']:
                    self.D313[5] = 1
                else:
                    self.D313[5] = 0
                if "内圆磨1#工件主轴温度均值偏高或值极高" in message.value['briefDescription']:
                    self.D313[6] = 1
                else:
                    self.D313[6] = 0
                if "内圆磨1#工件主轴电机温度均值偏高或值极高" in message.value['briefDescription']:
                    self.D313[7] = 1
                else:
                    self.D313[7] = 0
                if "内圆磨1#磨头温度rate偏高或值极高" in message.value['briefDescription']:
                    self.D313[8] = 1
                else:
                    self.D313[8] = 0
                if "内圆磨1#磨头电机温度rate偏高或值极高" in message.value['briefDescription']:
                    self.D313[9] = 1
                else:
                    self.D313[9] = 0
                if "内圆磨1#工件主轴温度rate偏高或值极高" in message.value['briefDescription']:
                    self.D313[10] = 1
                else:
                    self.D313[10] = 0
                if "内圆磨1#工件主轴电机温度rate偏高或值极高" in message.value['briefDescription']:
                    self.D313[11] = 1
                else:
                    self.D313[11] = 0
                if "内圆磨1#X轴电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D313[12] = 1
                else:
                    self.D313[12] = 0
                if "内圆磨1#Y轴电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D313[13] = 1
                else:
                    self.D313[13] = 0
                if "内圆磨1#R轴电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D313[14] = 1
                else:
                    self.D313[14] = 0
                if "内圆磨1#E轴电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D313[15] = 1
                else:
                    self.D313[15] = 0

            if message.value["deviceACode"] == "A0303020002160092":

                if "倒角机动力头2#传感器电池电量偏低或值极低" in message.value['briefDescription']:
                    self.D314[0] = 1
                else:
                    self.D314[0] = 0
                if "倒角机动力头2#温度平均值偏高或值极高" in message.value['briefDescription']:
                    self.D314[1] = 1
                else:
                    self.D314[1] = 0
                if "倒角机动力头1#X轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[2] = 1
                else:
                    self.D314[2] = 0
                if "倒角机动力头1#Y轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[3] = 1
                else:
                    self.D314[3] = 0
                if "倒角机动力头1#Z轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[4] = 1
                else:
                    self.D314[4] = 0
                if "倒角机动力头1#加速度峰值偏高或值极高" in message.value['briefDescription']:
                    self.D314[5] = 1
                else:
                    self.D314[5] = 0
                if "倒角机动力头1#Z轴包络值偏高或值极高" in message.value['briefDescription']:
                    self.D314[6] = 1
                else:
                    self.D314[6] = 0
                if "倒角机动力头1#传感器电池电量偏低或值极低" in message.value['briefDescription']:
                    self.D314[7] = 1
                else:
                    self.D314[7] = 0
                if "倒角机动力头1#温度平均值偏高或值极高" in message.value['briefDescription']:
                    self.D314[8] = 1
                else:
                    self.D314[8] = 0
                if "倒角机动力头2#X轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[9] = 1
                else:
                    self.D314[9] = 0
                if "倒角机动力头2#Y轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[10] = 1
                else:
                    self.D314[10] = 0
                if "倒角机动力头2#Z轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[11] = 1
                else:
                    self.D314[11] = 0
                if "倒角机动力头2#Z轴加速度峰值偏高或值极高" in message.value['briefDescription']:
                    self.D314[12] = 1
                else:
                    self.D314[12] = 0
                if "倒角机动力头2#Z轴包络值偏高或值极高" in message.value['briefDescription']:
                    self.D314[13] = 1
                else:
                    self.D314[13] = 0
                if "倒角机动力头1#X轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[14] = 1
                else:
                    self.D314[14] = 0
                if "倒角机动力头1#Y轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D314[15] = 1
                else:
                    self.D314[15] = 0
                if "倒角机动力头1#Z轴加速度有效值偏高或值极高" in message.value['briefDescription']:
                    self.D315[0] = 1
                else:
                    self.D315[0] = 0
                if "倒角机动力头1#加速度峰值偏高或值极高" in message.value['briefDescription']:
                    self.D315[1] = 1
                else:
                    self.D315[1] = 0
                if "倒角机动力头1#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[2] = 1
                else:
                    self.D315[2] = 0
                if "倒角机动力头1#公转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[3] = 1
                else:
                    self.D315[3] = 0
                if "倒角机动力头2#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[4] = 1
                else:
                    self.D315[4] = 0
                if "倒角机动力头2#公转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[5] = 1
                else:
                    self.D315[5] = 0
                if "倒角机动力头3#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[6] = 1
                else:
                    self.D315[6] = 0
                if "倒角机动力头3#公转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[7] = 1
                else:
                    self.D315[7] = 0
                if "倒角机动力头4#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[8] = 1
                else:
                    self.D315[8] = 0
                if "倒角机动力头6#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[9] = 1
                else:
                    self.D315[9] = 0
                if "倒角机动力头6#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[10] = 1
                else:
                    self.D315[10] = 0
                if "倒角机动力头7#公转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[11] = 1
                else:
                    self.D315[11] = 0
                if "倒角机动力头7#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[12] = 1
                else:
                    self.D315[12] = 0
                if "倒角机动力头8#公转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[13] = 1
                else:
                    self.D315[13] = 0
                if "倒角机动力头8#自转电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[14] = 1
                else:
                    self.D315[14] = 0
                if "倒角机动力头9#弹簧孔电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D315[15] = 1
                else:
                    self.D315[15] = 0
                if "倒角机动力头9#吸入孔电机电流rms值偏高或值极高" in message.value['briefDescription']:
                    self.D316[0] = 1
                else:
                    self.D316[0] = 0

                # 将列表转换为二进制字符串
                # 使用join方法将列表中的整数转换为字符串（这里实际上是将1转为'1'），然后拼接起来
                binary_str = ''.join(str(x) for x in self.D312[::-1])
                # 将二进制字符串转换为十进制数
                # 使用int函数，并指定基数为2（表示二进制）
                decimal_num = int(binary_str, 2)
                # 打印结果
                print("二进制数:", binary_str)
                print("十进制数:", decimal_num)
                master = mt.TcpMaster(self.hmi_ip, self.hmi_port)  # 目标机（PLC或触摸屏）地址
                master.set_timeout(5)
                addr = 312
                value = decimal_num
                w = master.execute(slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, output_value=[value], data_format='>f')
                print(f"将值{value}写入HMI：{self.hmi_ip}，数据地址：{addr}成功，返回结果W1：{w}")
                r = master.execute(slave=1, function_code=cst.READ_HOLDING_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, data_format='>f')
                print(f"从HMI：{self.hmi_ip}，数据地址：{addr}读取到的数据为{r}")

                # 将列表转换为二进制字符串
                # 使用join方法将列表中的整数转换为字符串（这里实际上是将1转为'1'），然后拼接起来
                binary_str = ''.join(str(x) for x in self.D313[::-1])
                # 将二进制字符串转换为十进制数
                # 使用int函数，并指定基数为2（表示二进制）
                decimal_num = int(binary_str, 2)
                # 打印结果
                print("二进制数:", binary_str)
                print("十进制数:", decimal_num)
                master = mt.TcpMaster(self.hmi_ip, self.hmi_port)  # 目标机（PLC或触摸屏）地址
                master.set_timeout(5)
                addr = 313
                value = decimal_num
                w = master.execute(slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, output_value=[value], data_format='>f')
                print(f"将值{value}写入HMI：{self.hmi_ip}，数据地址：{addr}成功，返回结果W1：{w}")
                r = master.execute(slave=1, function_code=cst.READ_HOLDING_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, data_format='>f')
                print(f"从HMI：{self.hmi_ip}，数据地址：{addr}读取到的数据为{r}")

                # 将列表转换为二进制字符串
                # 使用join方法将列表中的整数转换为字符串（这里实际上是将1转为'1'），然后拼接起来
                binary_str = ''.join(str(x) for x in self.D314[::-1])
                # 将二进制字符串转换为十进制数
                # 使用int函数，并指定基数为2（表示二进制）
                decimal_num = int(binary_str, 2)
                # 打印结果
                print("二进制数:", binary_str)
                print("十进制数:", decimal_num)
                master = mt.TcpMaster(self.hmi_ip, self.hmi_port)  # 目标机（PLC或触摸屏）地址
                master.set_timeout(5)
                addr = 314
                value = decimal_num
                w = master.execute(slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, output_value=[value], data_format='>f')
                print(f"将值{value}写入HMI：{self.hmi_ip}，数据地址：{addr}成功，返回结果W1：{w}")
                r = master.execute(slave=1, function_code=cst.READ_HOLDING_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, data_format='>f')
                print(f"从HMI：{self.hmi_ip}，数据地址：{addr}读取到的数据为{r}")

                # 将列表转换为二进制字符串
                # 使用join方法将列表中的整数转换为字符串（这里实际上是将1转为'1'），然后拼接起来
                binary_str = ''.join(str(x) for x in self.D315[::-1])
                # 将二进制字符串转换为十进制数
                # 使用int函数，并指定基数为2（表示二进制）
                decimal_num = int(binary_str, 2)
                # 打印结果
                print("二进制数:", binary_str)
                print("十进制数:", decimal_num)
                master = mt.TcpMaster(self.hmi_ip, self.hmi_port)  # 目标机（PLC或触摸屏）地址
                master.set_timeout(5)
                addr = 315
                value = decimal_num
                w = master.execute(slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, output_value=[value], data_format='>f')
                print(f"将值{value}写入HMI：{self.hmi_ip}，数据地址：{addr}成功，返回结果W1：{w}")
                r = master.execute(slave=1, function_code=cst.READ_HOLDING_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, data_format='>f')
                print(f"从HMI：{self.hmi_ip}，数据地址：{addr}读取到的数据为{r}")

                # 将列表转换为二进制字符串
                # 使用join方法将列表中的整数转换为字符串（这里实际上是将1转为'1'），然后拼接起来
                binary_str = ''.join(str(x) for x in self.D316[::-1])
                # 将二进制字符串转换为十进制数
                # 使用int函数，并指定基数为2（表示二进制）
                decimal_num = int(binary_str, 2)
                # 打印结果
                print("二进制数:", binary_str)
                print("十进制数:", decimal_num)
                master = mt.TcpMaster(self.hmi_ip, self.hmi_port)  # 目标机（PLC或触摸屏）地址
                master.set_timeout(5)
                addr = 316
                value = decimal_num
                w = master.execute(slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, output_value=[value], data_format='>f')
                print(f"将值{value}写入HMI：{self.hmi_ip}，数据地址：{addr}成功，返回结果W1：{w}")
                r = master.execute(slave=1, function_code=cst.READ_HOLDING_REGISTERS,
                                   starting_address=addr,
                                   quantity_of_x=2, data_format='>f')
                print(f"从HMI：{self.hmi_ip}，数据地址：{addr}读取到的数据为{r}")

if __name__ == "__main__":
    KAFKA_BROKER = '10.60.11.201:19092'
    # 要使用的Kafka主题
    TOPIC = 'alarm_data'
    hmi_ip = '192.168.8.65'
    hmi_port = 502
    # 创建KafkaConsumerClass实例并调用consume_messages方法
    consumer_instance = KafkaHMI(bootstrap_servers=KAFKA_BROKER, topic=TOPIC, hmi_ip=hmi_ip, hmi_port=hmi_ip)
    consumer_instance.kafka_hmi()