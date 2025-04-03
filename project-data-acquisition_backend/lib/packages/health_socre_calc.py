import math


def condition_cal(feature, wl, al, thresh_rate=0.8):  # wl是预警阈值，al指的是报警阈值  ,
    status = " "
    score = 100
    if feature < (wl * thresh_rate):
        score = 100
        status = "good"
    elif (wl * thresh_rate) <= feature < wl:
        score = int(100 - (feature - thresh_rate * wl) / ((1 - thresh_rate) * wl) * 100 * (1 - thresh_rate))
        status = "good"
    elif wl <= feature < al:
        score = int(100 * thresh_rate - (feature - wl) / (al - wl) * 40)
        status = "warning"
    elif al <= feature:
        score = int(60 / math.exp(feature / al - 1))
        status = "alarming"
    return score, status
