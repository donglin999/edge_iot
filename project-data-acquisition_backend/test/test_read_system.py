import platform

print("系统名称：", platform.system())
print("发行版本：", platform.release())
print("详细版本：", platform.version())
print("硬件架构：", platform.machine())
print("处理器类型：", platform.processor())
print("系统信息元组：", platform.uname())
