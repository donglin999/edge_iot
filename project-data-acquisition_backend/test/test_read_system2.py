import subprocess
import platform

def check_centos_version():
    try:
        # 执行命令并获取输出
        result = subprocess.run(['cat', '/etc/centos-release'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)

        # 检查命令是否成功执行
        if result.returncode == 0:
            # 获取输出结果
            output = result.stdout.strip()
            return output
    except Exception as e:
        print("系统名称：", platform.system())
        print("发行版本：", platform.release())
        print("详细版本：", platform.version())
        print("硬件架构：", platform.machine())
        print("处理器类型：", platform.processor())
        print("系统信息元组：", platform.uname())
        return platform.uname()


    # 调用函数并打印结果
print(check_centos_version())
