import numpy as np


def plc_datacheck(data):

    return True



def vk_datacheck(df):  # 输入数据类型dataframe
    '''
    if df.shape[0] == 10000 and df.shape[1] == 8 and df.abs().max().max() < 5:
         return True
     else:
         return False
    if df.shape[0] == 3000 and df.shape[1] == 8 and value_cnt(df.values, 0) < 800:
         return True
    else:
         return False
    '''
    return True




def value_cnt(arr, target=0):  # 统计numpy数组中某个数字出现的个数
    arr = np.array(arr)
    mask = (arr == target)
    arr_value = arr[mask]
    return arr_value.size


def art_datacheck(data):  # 输入数据类型数组
    # if len(data) == 8 and value_cnt(data, 4) < 8:
    #     return True
    # else:
    #     return False
    return True


if __name__ == '__main__':
    test = [0, 0, 0, 0, 1, 2]
    print(value_cnt(test))
