import openpyxl


def read_excel_to_dict(file_path):
    # 加载工作簿
    workbook = openpyxl.load_workbook(file_path)
    # 假设读取第一个工作表
    sheet = workbook.active

    # 初始化字典
    dn = {}

    # 遍历所有行（从第二行开始，因为第一行通常是标题行）
    for row in sheet.iter_rows(min_row=2, values_only=True):
        # row[0] 是第一列的值，row[1] 是第二列的值
        if row[0] is not None and row[1] is not None:  # 确保第二列的值不为空
            dn[row[1]] = row[0]

    return dn


# 使用示例
file_path = 'E:\微清\顺德\预测性维护\注塑厂\注塑机\edge_iot\数据地址清单2.xlsx'  # 替换为你的Excel文件路径

dn = read_excel_to_dict(file_path)
print(dn)