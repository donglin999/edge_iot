from opcua import Client
import pandas as pd

class OPCDataRetriever:
    def __init__(self, server_url):
        self.server_url = server_url
        self.opc = None

    def connect(self):
        self.opc = Client(self.server_url, timeout=10)
        self.opc.connect()

    def traverse_and_read_nodes(self, node):
        data = []
        # 获取当前节点的子节点
        children = node.get_children()
        print(f"children:{children}")
        for child in children:
            print(f"child:{child}")
            try:
                value = child.get_value()
                data.append([child.get_browse_name(), value])
            except Exception as e:
                print(f"尝试读取节点报错: {e}")
                sub_data = self.traverse_and_read_nodes(child)
                data.extend(sub_data)  # 将子节点的数据添加到当前节点的数据中

        return data

    def list_and_read_items(self):
        if not self.opc:
            raise Exception("Not connected to OPC server.")

        # 获取根节点
        root = self.opc.get_root_node()
        # 获取Objects节点（通常是ns=2;s=Objects，但可能因服务器而异）
        objects_node = root.get_child(["0:Objects"])  # 假设Objects在命名空间2中

        # 如果Objects节点不存在，则抛出异常或返回空数据
        if not objects_node:
            raise Exception("Objects node not found.")

        # 遍历Objects节点下的所有子节点
        data = self.traverse_and_read_nodes(objects_node)
        return data

    def save_to_csv(self, data, filename='opc_data.csv'):
        df = pd.DataFrame(data, columns=['Node Name', 'Value'])
        df.to_csv(filename, index=False)
        print(f"Data has been saved to {filename}")

    def close(self):
        if self.opc:
            self.opc.disconnect()

    def run(self):
        self.connect()
        data = self.list_and_read_items()
        self.save_to_csv(data)
        self.close()


# 使用示例
if __name__ == "__main__":
    server_url = 'opc.tcp://192.168.2.130:16664'
    opc_retriever = OPCDataRetriever(server_url)
    opc_retriever.run()