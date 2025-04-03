import paho.mqtt.client as mqtt
import time

# 定义MQTT服务器的地址和端口
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC = "/IMRC"
MESSAGE = "100"


# 定义当客户端连接到MQTT服务器时执行的回调函数
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # 连接成功后，可以立即开始发布消息，因为这是一个无限循环


# 创建MQTT客户端实例
client = mqtt.Client()

# 绑定连接回调函数
client.on_connect = on_connect

# 连接到MQTT服务器
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# 启动MQTT客户端的后台线程
client.loop_start()

try:
    while True:
        # 发布消息到指定的主题
        client.publish(TOPIC, MESSAGE)
        print(f"Published '{MESSAGE}' to topic '{TOPIC}'")
        # 等待2秒
        time.sleep(2)
except KeyboardInterrupt:
    # 当用户按下Ctrl+C时，停止MQTT客户端的后台线程并断开连接
    client.loop_stop()
    client.disconnect()
    print("Disconnected from MQTT broker.")