import pandas as pd
import numpy as np
from scipy.fft import fft, fftfreq, ifft
# fft：计算一维序列的快速傅里叶变换。
# fftfreq：返回傅里叶变换频率。
# ifft：计算一维序列的逆快速傅里叶变换。
from scipy.fftpack import hilbert
from scipy.signal import detrend
# detrend 去线性趋势
from scipy import signal
from scipy import stats
from scipy.signal import find_peaks
import math
import warnings

warnings.filterwarnings("ignore")


class VibFeature():

    def __init__(self, data, fs, nperseg=None, f_start=None, f_end=None):
        self.X = data
        self.fs = fs
        if nperseg == None:
            L = len(data)
            self.nperseg = pow(2, np.ceil(np.log2(np.abs(L))).astype('long'))
        else:
            self.nperseg = nperseg

        if f_start == None:
            self.f_start = 10
        else:
            self.f_start = f_start

        if f_end == None:
            self.f_end = 1000
        else:
            self.f_end = f_end
        # 找到一个大于或等于数据长度的最小的2的幂次方。
        self.nfft = pow(2, np.ceil(np.log2(np.abs(len(data)))).astype('long'))

        self.acc = data
        self.lpf_wave_acc, self.hpf_wave_acc = self.filter_time(self.acc, self.f_start, self.f_end)
        self.f_acc_filter, self.p_acc_filter = self.signalFFT(self.lpf_wave_acc)

        self.vel = self.integral(self.lpf_wave_acc) * 1000
        # note ：integral积分算法正确性
        self.lpf_wave_vel, hpf_wave_vel = self.filter_time(self.vel, self.f_start, self.f_end)
        self.f_vel_filter, self.p_vel_filter = self.signalFFT(self.lpf_wave_vel)

        self.disp = self.integral(self.lpf_wave_vel) * 1000
        self.lpf_wave_disp, hpf_wave_disp = self.filter_time(self.disp, self.f_start, self.f_end)
        self.f_disp_filter, self.p_disp_filter = self.signalFFT(self.lpf_wave_disp)

        self.envelope_wave, self.f_envelope, self.p_envelope = self.envelope()
        u = int(np.ceil(100 / (self.fs / self.nfft)))

        peaks, peaks_properties = find_peaks(self.p_envelope[0:u], prominence=self.p_envelope.max() / 7,
                                             distance=int(np.ceil(2 / (self.fs / self.nfft))))
        self.peaks_envelope_f = self.f_envelope[peaks][0:10]
        self.peaks_envelope_p = self.p_envelope[peaks][0:10]

        self.funcName = {'振动加速度有效值': 'get_acc_rms_raw', '振动加速度峰值': 'get_acc_Peak_raw',
                         '振动加速度峰峰值': 'get_acc_PP_raw', '振动加速度裕度因子': 'get_acc_CL_raw',
                         '振动加速度能量': 'get_acc_Energy_raw', '振动加速度有效值（滤波）': 'get_acc_rms_filter',
                         '振动加速度峰值（滤波）': 'get_acc_Peak_filter', '振动加速度峰峰值（滤波）': 'get_acc_PP_filter',
                         '振动加速度裕度因子（滤波）': 'get_acc_CL_filter', '振动加速度能量（滤波）': 'get_acc_Energy_filter',
                         '振动加速度重心频率': 'get_acc_FC_filter', '振动加速度功率谱熵': 'get_acc_PsdE_filter',
                         '振动速度有效值': 'get_vel_rms_raw', '振动速度峰值': 'get_vel_Peak_raw',
                         '振动速度峰峰值': 'get_vel_PP_raw', '振动速度裕度因子': 'get_vel_CL_raw',
                         '振动速度能量': 'get_vel_Energy_raw', '振动速度有效值（滤波）': 'get_vel_rms_filter',
                         '振动速度峰值（滤波）': 'get_vel_Peak_filter', '振动速度峰峰值（滤波）': 'get_vel_PP_filter',
                         '振动速度裕度因子（滤波）': 'get_vel_CL_filter', '振动速度能量（滤波）': 'get_vel_Energy_filter',
                         '振动速度重心频率': 'get_vel_FC_filter', '振动速度功率谱熵': 'get_vel_PsdE_filter',
                         '振动位移有效值': 'get_disp_rms_raw', '振动位移峰值': 'get_disp_Peak_raw',
                         '振动位移峰峰值': 'get_disp_PP_raw', '振动位移裕度因子': 'get_disp_CL_raw',
                         '振动位移能量': 'get_disp_Energy_raw', '振动位移有效值（滤波）': 'get_disp_rms_filter',
                         '振动位移峰值（滤波）': 'get_disp_Peak_filter', '振动位移峰峰值（滤波）': 'get_disp_PP_filter',
                         '振动位移裕度因子（滤波）': 'get_disp_CL_filter', '振动位移能量（滤波）': 'get_disp_Energy_filter',
                         '振动位移重心频率': 'get_disp_FC_filter', '振动位移功率谱熵': 'get_disp_PsdE_filter',
                         '包络线峰值': 'get_envlope_peak', '包络谱基频1': 'get_envelop_firstBaseF',
                         '包络谱基频2': 'get_envelop_secondBaseF', '包络谱单数倍频和': 'get_envelop_oddBaseSum',
                         '包络谱复数倍频和': 'get_envelop_evenBaseSum',
                         }

    def get_feature_func(self,name):
        if name == 'acc_rms':
            return self.get_acc_rms_raw
        elif name == 'vel_rms':
            return self.get_vel_rms_raw
        else:
            return lambda *a: 'no feature func'
    # 频域积分，相比时域积分误差小
    # note:增加时域积分
    def integral(self, data):
        yt = detrend(data)
        L = len(yt)
        NFFT = self.nfft
        fft_result = fft(yt, NFFT)
        df = self.fs / NFFT
        dw = 2 * np.pi * df
        w1_1 = np.arange(0, NFFT / 2 + 1)
        w1 = w1_1 * dw
        w1[0] = np.inf
        w1_2 = w1[1:-1]
        w2 = np.flip(w1_2)
        w = np.concatenate((w1, w2))
        a = np.divide(fft_result, w)
        y_ifft = ifft(a, NFFT)
        y_ifft = y_ifft.real
        y_ifft = y_ifft[0:L]
        return y_ifft

    # 滤波功能（频域滤波，相当于完美滤波器）
    # note：增加时域滤波
    def filter_time(self, data, f_start=10, f_stop=1000):
        # 去直流分量
        yt = detrend(data)
        L = len(yt)
        NFFT = self.nfft
        fft_result = fft(yt, n=NFFT)
        # 采样频率
        sammple_frequency = self.fs
        # 采样点数
        sammple_dotNumber = len(fft_result)
        filter_start_frequency = f_start
        filter_end_frequency = f_stop
        # 最大分析频率
        max_analysis_frequency = sammple_frequency / 2.56
        # 数据点
        line_num = sammple_dotNumber
        filter_start_freq_index_L = np.ceil(filter_start_frequency / sammple_frequency * line_num)
        #  低侧低截止频率索引
        filter_start_freq_index_L = int(filter_start_freq_index_L)
        filter_end_freq_index_L = np.ceil(filter_end_frequency / sammple_frequency * line_num)
        # 低侧高截止频率索引
        filter_end_freq_index_L = int(filter_end_freq_index_L)
        filter_max_freq_index_L = np.ceil(max_analysis_frequency / sammple_frequency * line_num)
        # 低侧最大分析频率索引
        filter_max_freq_index_L = int(filter_max_freq_index_L)
        # 高侧低截止频率索引
        filter_start_freq_index_H = line_num + 1 - filter_start_freq_index_L
        # 高侧高截止频率索引
        filter_end_freq_index_H = line_num + 1 - filter_end_freq_index_L
        # 高侧最大分析频率索引
        filter_max_freq_index_H = line_num + 1 - filter_max_freq_index_L
        # 低通滤波
        lpf_spectrum = fft_result.copy()
        lpf_spectrum[0:filter_start_freq_index_L] = 0
        lpf_spectrum[filter_end_freq_index_L:filter_end_freq_index_H] = 0
        lpf_spectrum[filter_start_freq_index_H:line_num] = 0
        # 高通滤波
        hpf_spectrum = fft_result.copy()
        hpf_spectrum[0:filter_end_freq_index_L] = 0
        hpf_spectrum[filter_max_freq_index_L:filter_max_freq_index_H] = 0
        hpf_spectrum[filter_end_freq_index_H:line_num] = 0
        # 滤波后，加速度傅里叶反变换，
        lpf_wave_data = ifft(lpf_spectrum, n=NFFT).real
        hpf_wave_data = ifft(hpf_spectrum, n=NFFT).real
        lpf_wave_data = lpf_wave_data[0:L]
        hpf_wave_data = hpf_wave_data[0:L]
        return lpf_wave_data, hpf_wave_data

    # 对截至频率fs_filter以上的高频段进行包络处理，fs_filter默认为1000Hz，返回包络波形和包络频谱
    def envelope(self):
        h_yt = hilbert(self.hpf_wave_acc)
        envolope = np.sqrt(self.hpf_wave_acc ** 2 + h_yt ** 2)
        envolope = detrend(envolope)
        L = len(envolope)
        h_yt_envolope_hann = envolope * np.hanning(L)
        NFFT = self.nfft
        h_yt_envolope_fft = fft(h_yt_envolope_hann, n=NFFT)
        h_yt_envolope_amd = np.abs(h_yt_envolope_fft) * 2 * 2 / NFFT
        h_yt_envolope_amd = h_yt_envolope_amd[: int(NFFT / 2.56)]
        f_envolop = np.arange(0, self.fs / 2.56, self.fs / NFFT)
        return envolope, f_envolop, h_yt_envolope_amd

    def signalPSD(self, data):
        f, p = signal.welch(data,
                            fs=self.fs,
                            window='hann',
                            nperseg=self.nperseg,
                            return_onesided=True)
        return f, p

    def calculateIE(self, sig):
        HS = []
        for i in range(len(sig)):
            prob = sig[i] / sum(sig)
            HS.append(prob * np.log(prob))
        Hs = -sum(HS)
        return Hs

    def signalFilter(self, N, wn, btype):
        b, a = signal.butter(N, wn, btype)
        x_filter = signal.lfilter(b, a, self.X)
        return x_filter

    def signalFFT(self, data):
        yt = data * np.hanning(len(data))
        Y_fft = fft(yt, n=self.nfft)
        Y_amd = np.abs(Y_fft) * 2 / self.nfft
        p = Y_amd[:int(self.nfft / 2.56)]
        f = np.arange(0, self.fs / 2.56, self.fs / self.nfft)
        return f, p

    def getMean(self, data):
        mean = data.mean()
        return mean

    def getABSMean(self, data):
        absMean = abs(data).mean()
        return absMean

    def getSTD(self, data):
        std = data.std()
        return std

    def getVAR(self, data):
        var = data.var()
        return var

    def getRMSA(self, data):
        rmsa = (np.sum(np.sqrt(abs(data))) / (len(data))) ** 2
        return rmsa

    def getRMS(self, data):
        rms = np.sqrt(np.mean(pow(data, 2)))
        return rms

    def getPEAK(self, data):
        peak = abs(data).max()
        return peak

    def getPP(self, data):
        pp = data.max() - data.min()
        return pp

    def getSK(self, data):
        sk = stats.skew(data, bias=False)
        # sk = (np.sum([pow(x-self.getMean(), 3) for x in self.X])
        #       / pow(self.getSTD(), 3))*len(self.X)/((len(self.X)-1)*(len(self.X)-2))
        return sk

    def getKU(self, data):
        ku = stats.kurtosis(data)
        # ku = (np.sum([pow(x-self.getMean(), 4) for x in self.X])
        #       / pow(self.getSTD(), 4))*len(self.X)/((len(self.X)-1)*(len(self.X)-2))
        return ku

    def getSH(self, data):
        sh = self.getRMS(data) / self.getABSMean(data)
        return sh

    def getIM(self, data):
        im = self.getPEAK(data) / self.getABSMean(data)
        return im

    def getCR(self, data):
        cr = self.getPEAK(data) / self.getRMS(data)
        return cr

    def getCL(self, data):
        cl = self.getPEAK(data) / self.getRMSA(data)
        return cl

    def getEnergy(self, data):
        energy = np.sum(pow(data, 2)) / self.fs
        return energy

    def getFMean(self, p):
        Fmean = p.mean()
        return Fmean

    def getFSTD(self, p):
        Fstd = p.std()
        return Fstd

    def getFVAR(self, p):
        Fvar = p.var()
        return Fvar

    def getFSK(self, p):
        Fsk = stats.skew(p, bias=False)
        # Fsk = (np.sum([pow(x-self.getFMean(), 3) for x in self.p])
        #       / (len(self.p)-1)*pow(self.getFSTD(), 3))
        return Fsk

    def getFKU(self, p):
        Fku = stats.kurtosis(p, bias=False)
        # Fku = (np.sum([pow(x-self.getFMean(), 4) for x in self.p])
        #       / (len(self.p)-1)*pow(self.getFSTD(), 4))
        return Fku

    def getFC(self, f, p):
        S = []
        for i in range(len(f)):
            s = p[i] * f[i]
            S.append(s)
        fc = np.sum(S) / np.sum(p)
        return fc

    def getRVF(self, f, p):
        S = []
        for i in range(len(f)):
            s = p[i] * ((f[i] - self.getFC(f, p)) ** 2)
            S.append(s)
        rvf = np.sqrt(np.sum(S) / np.sum(p))
        return rvf

    def getRMSF(self, f, p):
        S = []
        for i in range(len(f)):
            s = ((f[i] ** 2) * p[i])
            S.append(s)
        rmsf = np.sqrt(np.sum(S) / np.sum(p))
        return rmsf

    def getSKF(self, f, p):
        S = []
        for i in range(len(f)):
            s = p[i] * ((f[i] - self.getFC(f, p)) ** 3)
            S.append(s)
        skF = np.sum(S) / len(f) * pow(self.getRVF(f, p), 3)
        return skF

    def getKUF(self, f, p):
        S = []
        for i in range(len(f)):
            s = p[i] * ((f[i] - self.getFC(f, p)) ** 4)
            S.append(s)
        kuF = np.sum(S) / len(f) * pow(self.getRVF(f, p), 4)
        return kuF

    def getFP1(self, f, p):
        S = []
        V = []
        for i in range(len(f)):
            s = p[i] * (f[i] ** 4)
            S.append(s)
            v = p[i] * (f[i] ** 2)
            V.append(v)
        fp1 = np.sqrt(np.sum(S) / np.sum(V))
        return fp1

    def getFP2(self, f, p):
        S = []
        V = []
        for i in range(len(f)):
            s = p[i] * (f[i] ** 2)
            S.append(s)
            v = p[i] * (f[i] ** 4)
            V.append(v)
        fp2 = np.sum(S) / np.sqrt(np.sum(p) * np.sum(V))
        return fp2

    def getFP3(self, f, p):
        fp3 = self.getRVF(f, p) / self.getFC(f, p)
        return fp3

    def getPsdE(self, data):
        f, p = self.signalPSD(data)
        p = p[:int(len(p) * (self.f_end / f[-1]))]
        psde = self.calculateIE(p)
        return psde

    """
    以下为高频振动数据特征提取
    包括功能函数和特征值提取函数
    """

    # 无滤波加速度有效值
    def get_acc_rms_raw(self):
        return self.getRMS(self.acc)

    # 无滤波加速度峰值
    def get_acc_Peak_raw(self):
        return self.getPEAK(self.acc)

    # 无滤波加速度峰峰值
    def get_acc_PP_raw(self):
        return self.getPP(self.acc)

    # 无滤波加速度标准差值
    def get_acc_STD_raw(self):
        return self.getSTD(self.acc)

    # 无滤波加速度波形因子值
    def get_acc_SH_raw(self):
        return self.getSH(self.acc)

    # 无滤波加速度脉冲因子值
    def get_acc_IM_raw(self):
        return self.getIM(self.acc)

    # 无滤波加速度峰值因子值
    def get_acc_CR_raw(self):
        return self.getCR(self.acc)

    # 无滤波加速度裕度因子
    def get_acc_CL_raw(self):
        return self.getCL(self.acc)

    # 无滤波加速度总能量
    def get_acc_Energy_raw(self):
        return self.getEnergy(self.acc)

    # 滤波段加速度有效值，一般取10~1000Hz范围，对于低转速设备取2~1000Hz范围
    def get_acc_rms_filter(self):
        rms = self.getRMS(self.lpf_wave_acc)
        return rms

    # 滤波段加速度峰值，一般取10~1000Hz范围，对于低转速设备取2~1000Hz范围
    def get_acc_Peak_filter(self):
        peak = self.getPEAK(self.lpf_wave_acc)
        return peak

    # 滤波段加速度峰峰值
    def get_acc_PP_filter(self):
        return self.getPP(self.lpf_wave_acc)

    # 滤波段加速度裕度因子
    def get_acc_CL_filter(self):
        return self.getCL(self.lpf_wave_acc)

    # 滤波段加速度总能量
    def get_acc_Energy_filter(self):
        return self.getEnergy(self.lpf_wave_acc)

    # 滤波段加速度谱重心频率
    def get_acc_FC_filter(self):
        return self.getFC(self.f_acc_filter, self.p_acc_filter)

    # 滤波段加速度功率谱熵
    def get_acc_PsdE_filter(self):
        return self.getPsdE(self.lpf_wave_acc)

    # 无滤波速度有效值
    def get_vel_rms_raw(self):
        rms = self.getRMS(self.vel)
        return rms

    # 无滤波速度峰值
    def get_vel_Peak_raw(self):
        peak = self.getPEAK(self.vel)
        return peak

    # 无滤波速度峰峰值
    def get_vel_PP_raw(self):
        return self.getPP(self.vel)

    # 无滤波速度裕度因子
    def get_vel_CL_raw(self):
        return self.getCL(self.vel)

    # 无滤波速度总能量
    def get_vel_Energy_raw(self):
        return self.getEnergy(self.vel)

    # 滤波段速度有效值
    def get_vel_rms_filter(self):
        rms = self.getRMS(self.lpf_wave_vel)
        return rms

    # 滤波段速度峰值
    def get_vel_Peak_filter(self):
        peak = self.getPEAK(self.lpf_wave_vel)
        return peak

    # 滤波段速度峰峰值
    def get_vel_PP_filter(self):
        return self.getPP(self.lpf_wave_vel)

    # 滤波段速度裕度因子
    def get_vel_CL_filter(self):
        return self.getCL(self.lpf_wave_vel)

    # 滤波段速度总能量
    def get_vel_Energy_filter(self):
        return self.getEnergy(self.lpf_wave_vel)

    # 滤波段速度谱重心频率
    def get_vel_FC_filter(self):
        return self.getFC(self.f_vel_filter, self.p_vel_filter)

    # 滤波段速度功率谱熵
    def get_vel_PsdE_filter(self):
        return self.getPsdE(self.lpf_wave_vel)

    # 无滤波位移有效值
    def get_disp_rms_raw(self):
        rms = self.getRMS(self.disp)
        return rms

    # 无滤波位移峰值
    def get_disp_Peak_raw(self):
        peak = self.getPEAK(self.disp)
        return peak

    # 无滤波位移峰峰值
    def get_disp_PP_raw(self):
        return self.getPP(self.disp)

    # 无滤波位移裕度因子
    def get_disp_CL_raw(self):
        return self.getCL(self.disp)

    # 无滤波位移总能量
    def get_disp_Energy_raw(self):
        return self.getEnergy(self.disp)

    # 滤波段位移有效值
    def get_disp_rms_filter(self):
        rms = self.getRMS(self.lpf_wave_disp)
        return rms

    # 滤波段位移峰值
    def get_disp_Peak_filter(self):
        peak = self.getPEAK(self.lpf_wave_disp)
        return peak

    # 滤波段位移峰峰值
    def get_disp_PP_filter(self):
        return self.getPP(self.lpf_wave_disp)

    # 滤波段位移裕度因子
    def get_disp_CL_filter(self):
        return self.getCL(self.lpf_wave_disp)

    # 滤波段位移总能量
    def get_disp_Energy_filter(self):
        return self.getEnergy(self.lpf_wave_disp)

    # 滤波段位移谱重心频率
    def get_disp_FC_filter(self):
        return self.getFC(self.f_disp_filter, self.p_disp_filter)

    # 滤波段位移功率谱熵
    def get_disp_PsdE_filter(self):
        return self.getPsdE(self.lpf_wave_disp)

    # 包络峰值
    def get_envlope_peak(self):
        peak = self.getPEAK(self.envelope_wave)
        return peak

    #包络谱第一个峰值频率
    def get_envelop_firstBaseF(self):

        return self.peaks_envelope_f[0]

    # 包络谱第二个峰值频率
    def get_envelop_secondBaseF(self):

        return self.peaks_envelope_f[1]

    # 包络谱第一个峰值幅值
    def get_envelop_FirstBaseP(self):

        return self.peaks_envelope_p[0]

    # 包络谱第二个峰值幅值
    def get_envelop_secondBaseP(self):

        return self.peaks_envelope_p[1]

    # 包络谱第单数个峰值幅值和
    def get_envelop_oddBaseSum(self):
        baseOddSum = self.peaks_envelope_p[[0, 2, 4, 6, 8]].sum()
        return baseOddSum

    # 包络谱第偶数个峰值幅值和
    def get_envelop_evenBaseSum(self):
        baseEvenSum = self.peaks_envelope_p[[1, 3, 5, 7, 9]].sum()
        return baseEvenSum