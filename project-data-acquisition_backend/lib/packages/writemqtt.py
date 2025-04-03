import paho.mqtt.client as mqtt
import time,json

class WriteMqtt:
    def __init__(self,host='127.0.0.1',port=1883,keepalive=600):
        self.mqtt_client=mqtt.Client()
        self.mqtt_client.connect(host=host,port=port,keepalive=keepalive)

    def write_dict(self,data):
        print(data.keys())
        for key in data.keys():
            self.mqtt_client.publish(topic=key,payload=data[key],qos=0)

    def write_topic(self,topic,payload):
        self.mqtt_client.publish(topic=topic,payload=payload,qos=0)


if __name__=='__main__':
    write_mqtt=WriteMqtt(host='127.0.0.1',port=1883)
    data={'a':1,'b':2,'c':3}
    for i in range(1):
        #write_mqtt.write_dict(data)
        write_mqtt.write_topic(topic='test',payload=data)
        time.sleep(1)
        
