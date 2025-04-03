from opcua import Client
import pandas as pd
import time

class OPCDataRetriever:
    def __init__(self, server_url, node_id):
        self.server_url = server_url
        self.node_id = node_id
        self.opc = None

    def connect(self):
        self.opc = Client(self.server_url, timeout=10)
        self.opc.connect()

    def read_node_value(self, node_id):
        try:
            node = self.opc.get_node(node_id)
            value = node.get_value()
            return value
        except Exception as e:
            print(f"尝试读取节点 {node_id} 报错: {e}")
            return None

    def save_to_csv(self, data, filename='opc_data.csv'):
        df = pd.DataFrame(data, columns=['Timestamp', 'Value'])
        df.to_csv(filename, index=False)
        print(f"Data has been saved to {filename}")

    def run(self, interval=0.1, duration=60):  # interval in seconds, duration in seconds
        self.connect()
        start_time = time.time()
        data = []

        while (time.time() - start_time) < duration:
            value = self.read_node_value(self.node_id)
            if value is not None:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S.%f', time.localtime(time.time())) + str(time.time() % 1)[3:5]  # Get current time with milliseconds
                data.append([timestamp, value])
            time.sleep(interval)

        self.save_to_csv(data)
        self.close()

    def close(self):
        if self.opc:
            self.opc.disconnect()

# 使用示例
if __name__ == "__main__":
    server_url = 'opc.tcp://10.41.100.22:16664'
    node_id = 'ns=1;s=io_sig.ai_flt_3'
    opc_retriever = OPCDataRetriever(server_url, node_id)
    opc_retriever.run(interval=0.1, duration=60)  # 每100毫秒读取一次，持续60秒