# import json
import paho.mqtt.client as mqtt
import time


class ReadMqtt:
    def __init__(self, host='127.0.0.1', port=1883):
        self.multi_topics = None
        self.host = host
        self.port = port
        self.client = mqtt.Client()
        # self.client.username_pw_set("root", "root")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect

    def process_function(self, data):
        pass

    def on_message(self, client, userdata, msg):
        print("on_message 主题:" + msg.topic + " 消息:" + str(msg.payload.decode('utf-8')))

    # 订阅回调
    def on_subscribe(self, client, userdata, mid, granted_qos=0):
        print("On Subscribed: qos = %d" % granted_qos)

    # 取消订阅回调
    def on_unsubscribe(self, client, userdata, mid, granted_qos=0):
        print("On unSubscribed: qos = %d" % granted_qos)

    # 发布消息回调
    def on_publish(self, client, userdata, mid, granted_qos=0):
        print("On onPublish: qos = %d" % granted_qos)

    # 断开链接回调
    def on_disconnect(self, client, userdata, rc):
        print("Unexpected disconnection rc = " + rc)

    def pub_single_topic(self, topic):
        self.client.subscribe(topic)

    def on_running_message(self, client, userdata, msg):
        # thisData="on_running_message 主题:" + msg.topic + " 消息:" + str(msg.payload.decode('utf-8'))
        self.process_function(msg)

    def pub_multi_topics(self, topic):
        self.multi_topics = topic
        self.client.message_callback_add(self.multi_topics, self.on_running_message)

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        self.client.subscribe(self.multi_topics)

    def start(self):
        self.client.connect(host=self.host, port=self.port)
        self.client.loop_forever()


def testFC(msg):
    thisData = "on_running_message 主题:" + msg.topic + " 消息:" + str(msg.payload.decode('utf-8'))
    print(thisData)
    return None


if __name__ == '__main__':
    readMqtt = ReadMqtt(host='10.70.37.101', port=1883)
    readMqtt.process_function = testFC
    readMqtt.pub_multi_topics("shenghuo/#")
    readMqtt.start()
