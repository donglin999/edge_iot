from lib.HslCommunication import SiemensS7Net, SiemensPLCS

plc = SiemensS7Net(SiemensPLCS.S1200, "192.168.1.50")

# 连接到PLC
if plc.ConnectServer().IsSuccess:
    print("连接成功")

    # 写入bool类型数据到DB98.0
    result = plc.WriteBool("DB98.0", True)
    if result.IsSuccess:
        print("写入bool成功")
    else:
        print(f"写入bool失败: {result.Message}")

    # 写入int类型数据到DB98.2
    result = plc.WriteInt16("DB98.2", 12345)
    if result.IsSuccess:
        print("写入int成功")
    else:
        print(f"写入int失败: {result.Message}")

    # 写入real类型数据到DB98.4
    result = plc.WriteFloat("DB98.4", 123.45)
    if result.IsSuccess:
        print("写入real成功")
    else:
        print(f"写入real失败: {result.Message}")

    # 写入string类型数据到DB98.8
    result = plc.WriteString("DB98.8", "Hello PLC")
    if result.IsSuccess:
        print("写入string成功")
    else:
        print(f"写入string失败: {result.Message}")

    # 断开与PLC的连接
    plc.ConnectClose()
    print("断开连接")
else:
    print("连接失败")

