#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import ssl
import paho.mqtt.client as mqtt

def get_data(client, userdata, msg):
    msg_payload_dic = msg.payload.decode("utf-8")
    print(f"msg_payload_dic: {msg_payload_dic}")
    msg_topic = msg.topic
    print(f"msg_topic: {msg_topic}")

ip = '10.18.62.29'
port = 8883
username = 'ZYY_WQSD'
passwd = 'ce2471e6d100468ea8783b5c79766a0b'
client = mqtt.Client()
client.username_pw_set(username, passwd)
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
client.tls_set_context(context)
client.connect(ip, port, 60)  # 添加了超时时间参数，可以根据需要调整
print(f"mqtt连接成功")
topic = "/sys/33fb0a8e1c27460a8a8bc21d265a1729/device/#"
client.subscribe(topic)
client.on_message = get_data  # 注意这里不再加括号
client.loop_forever()