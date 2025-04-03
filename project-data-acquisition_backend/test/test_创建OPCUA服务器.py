from opcua import Client, Server, ua
from opcua.ua import NodeId
import time

# 创建 OPC UA 服务器
server = Server()
server.set_endpoint("opc.tcp://localhost:4840")

# 读取服务器的配置并启动服务器
server.load_application_instance_certificate("server_cert.der")
server.load_private_key("server_pk.pem")

if not server.is_running():
    server.start()
    print("Server started at opc.tcp://localhost:4840")

# 定义命名空间，假设我们创建一个新的命名空间 URI 和索引
uri = "http://example.org/freeopcua/server/"
idx = server.register_namespace(uri)

# 创建一个根对象
root = server.get_root_node()
objects = root.add_object(NodeId(2, idx, 2), "Objects")

# 创建10个数据地址并写入1-10
for i in range(1, 11):
    node_id = NodeId(2, idx, i)
    var_name = f"ScalarTypes.Int32.{i}"
    var_node = objects.add_variable(node_id, var_name, ua.Variant(i, ua.VariantType.Int32))
    var_node.set_writable()
    var_node.set_value(ua.Variant(i, ua.VariantType.Int32))
    print(f"Created node {var_name} with value {i}")

# 保持服务器运行
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping server...")
    server.stop()