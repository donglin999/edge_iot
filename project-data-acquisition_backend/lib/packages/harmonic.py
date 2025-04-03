"""
此函数功能为求倍频特征值
包括以转频和轴承故障频率为基频的谐波成分
输入为时域波形和采样频率，时域波形可为加速度/速度和包络波形，一般诊断多用速度（加速度波形积分得到）和包络波形
输出为各倍频成分幅值
注意如需智能判断，需考虑将频域进行归一化再设定规则判断属于哪类故障
"""
import random
import numpy as np
from scipy.fftpack import fft
from scipy.signal import detrend

#求接近2的n次幂接近值
def nextpow2(n):
    ##rint为四舍五入取最近整数
    N=np.rint(np.log2(np.abs(n))).astype('long')
    return pow(2,N)
#求单边频谱，yt时域波形，Fs采样率
def Spectrum_Calc(yt, Fs):
    L=len(yt)
    #去直流分量
    yt=detrend(yt)
    #加汉宁窗
    yt=yt*np.hanning(L)
    NFFT=nextpow2(L)
    fft_result=fft(yt,n=NFFT)
    Yf=fft_result/L
    ##尾部2为加窗后的幅值增强系数
    Yf=2*np.abs(Yf)*2
    L1=int(NFFT/2.56)
    #取单边谱
    Yf=Yf[0:L1]
    f=np.arange(0,Fs/2.56,Fs/NFFT)
    return f,Yf,fft_result
#计算一定窗口误差内的倍频幅值
def calc_harmonic(data, fs, normal_rpm=18000, rates=[0.5, 1, 2, 3, 4, 5 , 6 , 7 , 8 , 9 , 10],window=0.06):
    
    freq,amp,fft_result= Spectrum_Calc(data,fs)
    normal_freq = normal_rpm / 60
    freq = freq.reshape(-1)
    amp = amp.reshape(-1)
    harmonics = {}
    for rate in rates:
        harmonics['harmonic_' + str(rate)] = max(
            amp[(freq > normal_freq * rate *(1-window)) & (freq < normal_freq * rate *(1+window))])
    return harmonics


def BPFI_harmonic(data, fs,  normal_rpm=1440, BPFI=3.4,rates=[ 1, 2, 3, 4, 5],window=0.02):
    freq,amp,fft_result= Spectrum_Calc(data,fs)
    normal_freq = normal_rpm / 60
    BPFI_freq=normal_freq*BPFI
    freq = freq.reshape(-1)
    amp = amp.reshape(-1)
    BPFI_harmonics = {}
    for rate in rates:
        BPFI_harmonics['harmonic_' + str(rate)] = max(
            amp[(freq > BPFI_freq * rate *(1-window)) & (freq < BPFI_freq * rate *(1+window))])
    return BPFI_harmonics


def BPFO_harmonic(data, fs,  normal_rpm=1440,BPFO=2.4, rates=[1, 2, 3, 4, 5],window=0.02):
    freq,amp,fft_result= Spectrum_Calc(data,fs)
    normal_freq = normal_rpm / 60
    BPFO_freq = normal_freq * BPFO
    freq = freq.reshape(-1)
    amp = amp.reshape(-1)
    BPFO_harmonics = {}
    for rate in rates:
        BPFO_harmonics['harmonic_' + str(rate)] = max(
            amp[(freq > BPFO_freq * rate * (1 - window)) & (freq < BPFO_freq * rate * (1 + window))])
    return BPFO_harmonics


def BSF_harmonic(data, fs, normal_rpm=1440, BSF=3.5,rates=[1, 2, 3, 4, 5],window=0.06):
    freq,amp,fft_result= Spectrum_Calc(data,fs)
    normal_freq = normal_rpm / 60
    BSF_freq = normal_freq * BSF
    freq = freq.reshape(-1)
    amp = amp.reshape(-1)
    BSF_harmonics = {}
    for rate in rates:
        BSF_harmonics['harmonic_' + str(rate)] = max(
            amp[(freq > BSF_freq * rate * (1 - window)) & (freq < BSF_freq * rate * (1 + window))])
    return BSF_harmonics


if __name__=="__main__":
    t=np.arange(0,1000,1/3000)
    data =np.sin(2*np.pi*50*t)+np.sin(2*np.pi*25*t)*2+np.sin(2*np.pi*100*t)*8+np.sin(2*np.pi*150*t)*9+np.sin(2*np.pi*50*3.5*t)*10+np.sin(2*np.pi*50*2*3.5*t)*10++np.sin(2*np.pi*50*3*3.5*t)*10

    b=calc_harmonic(data, 3000, normal_rpm=3000)["harmonic_0.5"]
    c = BSF_harmonic(data, 3000, normal_rpm=3000)["harmonic_1"]
    print(b,c)
    