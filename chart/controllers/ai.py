from django.forms.models import model_to_dict

import numpy as np
import talib
from collections import OrderedDict

from chart.models import *
from chart.controllers import get_data, order
import math
import datetime
import time
import logging


logger = logging.getLogger(__name__)


class Technical:
    def __init__(self, candles):
        """[summary]generate dict, np.array data from django.db.models(Candle_1s, Candle_1m, Candle_1h)

        Args:
            candles ([type] django.db.models ): [description] chart.models のmodels.
            self.candle_dict:辞書形式のcandle
            self.close:np.[type]:array, [shape] (len(self.candles), )
        """
        self.candles = list(candles.objects.order_by("time"))
        self.candle_dict = self.Model2Dict()
        self.close = np.array(self.candle_dict["close"]).reshape(-1,)

    def Model2Dict(self):
        self.candle_dict = {
            "time": [],
            "product_code": [],
            "open": [],
            "close": [],
            "high": [],
            "low": [],
            "volume": [],
        }
        for candle in self.candles:
            candle = model_to_dict(candle)
            for key, value in candle.items():
                self.candle_dict[key].append(value)
        return self.candle_dict

    def ATR(self, timeperiod=14):
        """[summary] caluclating ATR lsrge → volatility will be  larger.

        Args:
            timeperiod (int, optional): [description]. Defaults to 14.

        Returns:
            [type]: [description] np.array shape=(len(self.close), )
        """
        high = np.array(self.candle_dict["high"]).reshape(-1,)
        low = np.array(self.candle_dict["low"]).reshape(-1,)
        atr = talib.ATR(high, low, self.close, timeperiod=timeperiod)
        return atr

    def ADX(self, timeperiod=14):
        """[summary] caluclating ADX ADX large →trend is strong.

        Args:
            timeperiod (int, optional): [description]. Defaults to 14.

        Returns:
            [type]: [description] np.array shape=(len(self.close), )
        """
        high = np.array(self.candle_dict["high"]).reshape(-1,)
        low = np.array(self.candle_dict["low"]).reshape(-1,)
        adx = talib.ADX(high, low, self.close, timeperiod=timeperiod)
        DI_m = talib.MINUS_DI(high, low, self.close, timeperiod=timeperiod)
        DI_p = talib.PLUS_DI(high, low, self.close, timeperiod=timeperiod)
        return adx, DI_m, DI_p

    def DEma(self, timeperiod=12):
        """[summary] caluclating DEMA Finf out trend.

        Args:
            timeperiod (int, optional): [description]. Defaults to 12.

        Returns:
            [type]: [description] np.array shape=(len(self.close), ) First of timeperiod - 1 elements are nan.
        """
        ema = talib.DEMA(self.close, timeperiod=timeperiod)
        return ema

    def Ema(self, timeperiod=12):
        """[summary] caluclating EMA Finf out trend.

        Args:
            timeperiod (int, optional): [description]. Defaults to 12.

        Returns:
            [type]: [description] np.array shape=(len(self.close), ) First of timeperiod - 1 elements are nan.
        """
        ema = talib.EMA(self.close, timeperiod=timeperiod)
        return ema

    def Sma(self, timeperiod=12):
        """[summary] caluclating SMA Finf out trend.

        Args:
            timeperiod (int, optional): [description]. Defaults to 12.

        Returns:
            [type]: [description] np.array shape=(len(self.close), ) First of timeperiod - 1 elements are nan.
        """
        sma = talib.SMA(self.close, timeperiod=timeperiod)
        return sma

    def Bbands(self, timeperiod=5, nbdev=2):
        """[summary]Caluclating BBANDS. Find out if the current price is within two standard deviations.

        Args:
            timeperiod (int, optional): [description]. Defaults to 5.
            nbdev (int, optional): [description]. Defaults to 2.

        Returns:
            [type]: [description]upperband/lowerband = MA(timeperiod) ± nbdev*stdev, middleband = MA(timeperiod).
        """
        upperband, middleband, lowerband = talib.BBANDS(
            self.close, timeperiod=timeperiod, nbdevup=nbdev, nbdevdn=nbdev, matype=0)
        return upperband, middleband, lowerband

    def Macd(self, fastperiod=12, slowperiod=26, signalperiod=9):
        """[summary]Calculating MACD. MACD is constructed MAs. Find out when buy or sell from macd and macdsignal.

        Args:
            fastperiod (int, optional): [description]. Defaults to 12.
            slowperiod (int, optional): [description]. Defaults to 26.
            signalperiod (int, optional): [description]. Defaults to 9.

        Returns:
            macd, macdsignal, macdhist [type] np.array: [description] macd is ma(fastperiod) - ma(slowperiod), macdsignal = ma(signalperiod)
        """
        macd, macdsignal, macdhist = talib.MACDEXT(
            self.close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0)
        return macd, macdsignal, macdhist

    def Rsi(self, timeperiod=14):
        """[summary] 0 ~ 100 % RSI< 30% → buy , 70% → sell

        Args:
            timeperiod (int, optional): [description]. Defaults to 14.

        Returns:
            [type]np.array: [description]
        """
        return talib.RSI(self.close, timeperiod)

    def Hv(self, timeperiod=5, nbdev=1):
        """[summary] histrical volatility(standard deviations).

        Args:
            timeperiod (int, optional): [description]. Defaults to 5.
            nbdev (int, optional): [description]. Defaults to 1.

        Returns:
            [type]float : [description]
        """
        change = [0]
        for i in range(len(self.close)):
            if i == 0:
                continue
            dayChange = math.log(self.close[i] / self.close[i - 1])
            change.append(dayChange)
        change = np.array(change).reshape(-1,)
        return talib.STDDEV(change, timeperiod, nbdev)

    def Ichimoku(self, t=9, k=26, s=52):
        """[summary]一目均衡表. senkouA, senkouBが作る領域を雲と呼び、tenkan, kijun が雲を突き抜けるかどうかで売り買いを判断する

        Args:
            t (int, optional): [description]. Defaults to 9.
            k (int, optional): [description]. Defaults to 26.
            s (int, optional): [description]. Defaults to 52.

        Returns:
            [type]np.array: [description] tenkan = (Max(t days)+Min(t days) )/2,
             kijun = (Max(k days)+Min(k days) )/2
        """
        tenkan = [0] * t
        kijun = [0] * k
        senkouA = [0] * k
        senkouB = [0] * s
        chikou = [0] * k
        for i in range(len(self.close)):
            if i >= t:
                close = self.close[i - t:i]
                MIN = min(close)
                MAX = max(close)
                tenkan.append((MIN + MAX) / 2)
            if i >= k:
                close = self.close[i - k:i]
                MIN = min(close)
                MAX = max(close)
                kijun.append((MIN + MAX) / 2)
                senkouA.append((tenkan[i] + kijun[i]) / 2)
                chikou.append(self.close[i - k])
            if i >= s:
                close = self.close[i - s:i]
                MIN = min(close)
                MAX = max(close)
                senkouB.append((MIN + MAX) / 2)
        tenkan = np.array(tenkan).reshape(-1,)
        kijun = np.array(tenkan).reshape(-1,)
        senkouA = np.array(senkouA).reshape(-1,)
        senkouB = np.array(senkouB).reshape(-1,)
        chikou = np.array(chikou).reshape(-1,)
        return tenkan, kijun, senkouA, senkouB, chikou


class Recognize:
    """[summary] From given parameters and i (used like df[i]), recognize buy, sell, or do nothing. This class decide trading algo.

        Args:
            paremeters (optional): [description]

        Returns:
            [type]: [description] 'BUY', 'SELL' ,''
        """

    def RDEma(self, ema1, ema2, close, i=1):
        """[summary]短期移動平均線が長期移動平均線を下に交差し終値が短期移動平均線を下回っていれば買う。

        Args:
            ema1 ([type]): [description]
            ema2 ([type]): [description]
            close ([type]): [description]
            thread (float, optional): [description]. Defaults to 0.1.
            i (int, optional): [description]. Defaults to 1.

        Returns:
            [type]: [description]
        """
        if (ema1[i - 1] < ema2[i - 1] and ema1[i] >= ema2[i] and
                close[i] > ema1[i]):
            return "BUY"

        if (ema1[i - 1] > ema2[i - 1] and ema1[i] <= ema2[i] and
                close[i] < ema1[i]):
            return "SELL"
        return ""

    def REma(self, ema1, ema2, close, i=1):
        """[summary]短期移動平均線が長期移動平均線を下に交差し終値が短期移動平均線を下回っていれば買う。

        Args:
            ema1 ([type]): [description]
            ema2 ([type]): [description]
            close ([type]): [description]
            thread (float, optional): [description]. Defaults to 0.1.
            i (int, optional): [description]. Defaults to 1.

        Returns:
            [type]: [description]
        """
        if (ema1[i - 1] < ema2[i - 1] and ema1[i] >= ema2[i] and
                close[i] > ema1[i]):
            return "BUY"

        if (ema1[i - 1] > ema2[i - 1] and ema1[i] <= ema2[i] and
                close[i] < ema1[i]):
            return "SELL"
        return ""

    def RSma(self, sma1, sma2, close, i=1):
        if (sma1[i - 1] < sma2[i - 1] and sma1[i] >= sma2[i] and
                close[i] > sma1[i]):
            return "BUY"

        if (sma1[i - 1] > sma2[i - 1] and sma1[i] <= sma2[i] and
                close[i] < sma1[i]):
            return "SELL"
        return ""

    def RBb(self, bbUp, bbDown, close, n, i):
        if (bbDown[i - 1] > close[i - 1] and bbDown[i] <= close[i] and
                close[i] > max(close[i - n // 2:i - 1])):
            return "BUY"

        if (bbUp[i - 1] < close[i - 1] and bbUp[i] >= close[i] and
                close[i] < min(close[i - n // 2:i - 1])):
            return "SELL"
        return ""

    def RIchimoku(self, High, Low, tenkan, kijun, senkouA, senkouB, chikou, i):
        if (chikou[i - 1] < High[i - 1] and
            (senkouA[i] < Low[i] or senkouB[i] < Low[i]) and
                (chikou[i] >= High[i] or tenkan[i] > kijun[i])):
            return "BUY"

        if (chikou[i - 1] > Low[i - 1] and
            (senkouA[i] > High[i] or senkouB[i] > High[i]) and
                (chikou[i] <= Low[i] or tenkan[i] < kijun[i])):
            return "SELL"
        return ""

    def RMacd(self, macd, macdsignal, i):
        if (macd[i] < 0 and macdsignal[i] < 0 and
                macd[i - 1] < macdsignal[i - 1] and macd[i] >= macdsignal[i]):
            return "BUY"

        if(macd[i] > 0 and macdsignal[i] > 0 and
                macd[i - 1] > macdsignal[i - 1] and macd[i] <= macdsignal[i]):
            return "SELL"
        return ""

    def RRsi(self, values, i, buyThread=70, sellThread=30):
        if values[i - 1] == 0 or values[i - 1] == 100:
            return ""
        if values[i - 1] < buyThread and values[i] >= buyThread:
            return "BUY"

        if values[i - 1] > sellThread and values[i] <= sellThread:
            return "SELL"
        return ""


class BackTest(Recognize, Technical):
    """[summary]与えられたcandles でBackTest を行うクラス

    Args:
        Technical ([type]class): [description] Technical指標をまとめたクラス。
    """

    def __init__(self, candles):
        super().__init__(candles=candles)
        self.len_candles = len(self.candles)

    def SaveSignalEvents(self, i, side):
        """[summary]save backtest's signalevents. time=self.candles[i].time, price = self.candles[i].close, side = given

        Args:
            i ([type]): [description] choose candle paramerter
            side ([type]): [description] 'BUY' or 'SELL'
        """
        signalevents = BackTestSignalEvents()
        signalevents.time = self.candles[i].time
        signalevents.price = self.candles[i].close
        signalevents.side = side
        signalevents.save()

    def AddEvents(self, events, r, i):
        """[summary]add signal events to BackTestSignalEvents, and adding events(type=dict , keys=(index, order)).

        Args:
            events ([type]dict): [description] events={'index':[...], 'order':[...] }
            r ([type]str): [description] : r in {'BUY', 'SELL', ''}
            i ([type]int): [description] : i is index of event like self.candles[i]
        """
        if ((len(events["order"]) == 0 and r == "BUY") or
                (len(events["order"]) > 0 and r == "BUY" and events["order"][-1] == "SELL")):
            events["index"].append(i)
            events["order"].append("BUY")
            self.SaveSignalEvents(i, side="BUY")

        elif ((len(events["order"]) == 0 and r == "SELL") or
                (len(events["order"]) > 0 and r == "SELL" and events["order"][-1] == "BUY")):
            events["index"].append(i)
            events["order"].append("SELL")
            self.SaveSignalEvents(i, side="SELL")

    def BackTestDEma(self, period1=7, period2=14):
        if len(BackTestSignalEvents.objects.all()) > 0:
            BackTestSignalEvents.objects.all().delete()
        events = {"index": [], "order": []}
        if self.len_candles <= max(period1, period2):
            return events
        ema1 = self.DEma(period1)
        ema2 = self.DEma(period2)

        for i in range(max(period1, period2), self.len_candles):
            r = self.RDEma(ema1, ema2, self.close, i=i)
            self.AddEvents(events, r, i)

        return events

    def BackTestEma(self, period1=7, period2=14):
        if len(BackTestSignalEvents.objects.all()) > 0:
            BackTestSignalEvents.objects.all().delete()
        events = {"index": [], "order": []}
        if self.len_candles <= max(period1, period2):
            return events
        ema1 = self.Ema(period1)
        ema2 = self.Ema(period2)

        for i in range(max(period1, period2), self.len_candles):
            r = self.REma(ema1, ema2, self.close, i=i)
            self.AddEvents(events, r, i)

        return events

    def BackTestSma(self, period1=26, period2=52):
        if len(BackTestSignalEvents.objects.all()) > 0:
            BackTestSignalEvents.objects.all().delete()
        events = {"index": [], "order": []}
        if self.len_candles <= max(period1, period2):
            return events
        sma1 = self.Sma(period1)
        sma2 = self.Sma(period2)

        for i in range(max(period1, period2), self.len_candles):
            r = self.RSma(sma1, sma2, i)
            self.AddEvents(events, r, i)

        return events

    def BackTestBb(self, n=14, k=2.0):
        """[summary] n>=10

        Args:
            n (int, optional): [description]. Defaults to 14.
            k (float, optional): [description]. Defaults to 2.0.

        Returns:
            [type]: [description]
        """
        if len(BackTestSignalEvents.objects.all()) > 0:
            BackTestSignalEvents.objects.all().delete()
        events = {"index": [], "order": []}
        if self.len_candles <= n:
            return events

        bbUp, _, bbDown = self.Bbands(n, k)
        for i in range(n, self.len_candles):
            r = self.RBb(bbUp, bbDown, self.close, n, i)
            self.AddEvents(events, r, i)
        return events

    def BackTestIchimoku(self, t=9, k=26, s=52):
        if len(BackTestSignalEvents.objects.all()) > 0:
            BackTestSignalEvents.objects.all().delete()
        events = {"index": [], "order": []}
        if self.len_candles <= s:
            return events
        High = np.array(self.candle_dict["high"]).reshape(-1,)
        Low = np.array(self.candle_dict["low"]).reshape(-1,)
        tenkan, kijun, senkouA, senkouB, chikou = self.Ichimoku(t, k, s)

        for i in range(s, self.len_candles):
            r = self.RIchimoku(High, Low, tenkan, kijun, senkouA, senkouB, chikou, i)
            self.AddEvents(events, r, i)
        return events

    def BackTestMacd(self, fastperiod=12, slowperiod=26, signalperiod=9):
        events = {"index": [], "order": []}
        if len(BackTestSignalEvents.objects.all()) > 0:
            BackTestSignalEvents.objects.all().delete()
        if self.len_candles <= max(fastperiod, slowperiod, signalperiod):
            return events

        macd, macdsignal, _ = self.Macd(fastperiod, slowperiod, signalperiod)

        for i in range(max(fastperiod, slowperiod, signalperiod), self.len_candles):
            r = self.RMacd(macd, macdsignal, i)
            self.AddEvents(events, r, i)
        return events

    def BackTestRsi(self, period=14, buyThread=70, sellThread=30):
        if len(BackTestSignalEvents.objects.all()) > 0:
            BackTestSignalEvents.objects.all().delete()
        events = {"index": [], "order": []}
        if self.len_candles <= period:
            return events

        values = self.Rsi(period)
        for i in range(1, self.len_candles):
            r = self.RRsi(values, i, buyThread=70, sellThread=30)
            self.AddEvents(events, r, i)
        return events


class Optimize(BackTest):
    """[summary] Optimize Techinical indexes.

    Args:
        BackTest ([type]): [description]
        candles ([type] django.db.models ): [description] chart.models のmodels object.
    """

    def __init__(self, candles):
        super().__init__(candles=candles)

    def Profit(self, events, size=1.0):
        """[summary] calculating profit of Trading. Trading is based on self.candles and events

        Args:
            events ([type] dict ): [description]dict.keys()=('index', 'order'), index in [0, len(candles)], order in ['buy', 'sell']
            size (float, optional): [description]. Defaults to 1.0.

        Returns:
            [type]float: [description]
        """
        total = 0.0
        beforeSell = 0.0
        isHolding = False
        for i, oi in enumerate(events["index"]):
            order = events["order"][i]
            if i == 0 and order == "SELL":
                continue
            if order == "BUY":
                price = self.close[oi]
                total -= price * size
                isHolding = True
            if order == "SELL":
                price = self.close[oi]
                total += price * size
                isHolding = False
                beforeSell = total
        if isHolding is True:
            return beforeSell
        return total

    def OptimizeDEma(self, size=1.0):
        bestperiod1 = 7
        bestperiod2 = 14
        performance = 0.0
        profit = 0
        for period1 in range(3, 20):
            for period2 in range(12, 30):
                if period1 < period2:
                    events = self.BackTestDEma(period1=period1, period2=period2)
                    profit = self.Profit(events=events)
                if profit > performance:
                    performance = profit
                    bestperiod1 = period1
                    bestperiod2 = period2
        events = self.BackTestDEma(period1=bestperiod1, period2=bestperiod2)
        return events, performance, bestperiod1, bestperiod2

    def OptimizeEma(self, size=1.0):
        bestperiod1 = 7
        bestperiod2 = 14
        performance = 0.0
        profit = 0
        for period1 in range(3, 20):
            for period2 in range(10, 30):
                if period1 < period2:
                    events = self.BackTestEma(period1=period1, period2=period2)
                    profit = self.Profit(events=events)
                if profit > performance:
                    performance = profit
                    bestperiod1 = period1
                    bestperiod2 = period2
        events = self.BackTestEma(period1=bestperiod1, period2=bestperiod2)
        return events, performance, bestperiod1, bestperiod2

    def OptimizeSma(self, size=1.0):
        bestperiod1 = 7
        bestperiod2 = 14
        performance = 0.0
        profit = 0
        for period1 in range(3, 24):
            for period2 in range(7, 42):
                if period1 < period2:
                    events = self.BackTestSma(period1=period1, period2=period2)
                    profit = self.Profit(events=events)
                if profit > performance:
                    performance = profit
                    bestperiod1 = period1
                    bestperiod2 = period2
        events = self.BackTestEma(period1=bestperiod1, period2=bestperiod2)
        return events, performance, bestperiod1, bestperiod2

    def OptimizeBb(self, size=1.0):
        bestN = 20
        bestk = 2.0
        performance = 0.0
        for N in range(10, 30):
            for k in np.arange(1.0, 3.1, 0.1):
                events = self.BackTestBb(N, k)
                profit = self.Profit(events=events)
                if profit > performance:
                    performance = profit
                    bestN = N
                    bestk = k
        events = self.BackTestBb(bestN, bestk)
        return events, performance, bestN, bestk

    def OptimizeMacd(self, size=1.0):
        bestMacdFastPeriod = 12
        bestMacdSlowPeriod = 26
        bestMacdSignalPeriod = 9
        performance = 0.0
        for fastPeriod in range(5, 20):
            for slowPeriod in range(15, 35):
                for signalPeriod in range(5, 20):
                    events = self.BackTestMacd(fastPeriod, slowPeriod, signalPeriod)
                    profit = self.Profit(events=events)
                    if profit > performance:
                        bestMacdFastPeriod = fastPeriod
                        bestMacdSlowPeriod = slowPeriod
                        bestMacdSignalPeriod = signalPeriod
        events = self.BackTestMacd(bestMacdFastPeriod, bestMacdSlowPeriod, bestMacdSignalPeriod)
        return events, performance, bestMacdFastPeriod, bestMacdSlowPeriod, bestMacdSignalPeriod

    def OptimizeRsi(self, size=1.0):
        bestperiod = 14
        bestBuyThread, bestSellThread = 30.0, 70.0
        performance = 0.0
        for period in range(5, 25):
            events = self.BackTestRsi(period=period)
            profit = self.Profit(events=events)
            if profit > performance:
                performance = profit
                bestperiod = period
        events = self.BackTestRsi(period=bestperiod)
        return events, performance, bestperiod, bestBuyThread, bestSellThread

    def OptimizeIchimoku(self, size=1.0):
        performance = 0.0
        t = 9
        k = 26
        s = 52
        events = self.BackTestIchimoku()
        profit = self.Profit(events=events)
        if profit > performance:
            performance = profit
        events = self.BackTestIchimoku()
        return events, performance, t, k, s

    def OptimizeParams(self, size=1.0):
        """[summary] optimize parameter of technical indicators above.

        Args:
            size (float, optional): [description]. Defaults to 1.0.

        Returns:
            [type]OrderedDict: [description]like ('Bb', {'performance': 13569533.5, 'params': (10, 1.60), 'Enable': True})
        """
        optimizedparams = OrderedDict()
        Ema = self.OptimizeEma(size=size)
        Sma = self.OptimizeSma(size=size)
        Bb = self.OptimizeBb(size=size)
        Macd = self.OptimizeMacd(size=size)
        Rsi = self.OptimizeRsi(size=size)
        Ichimoku = self.OptimizeIchimoku()
        technical = ["Ema", "Sma", "Bb", "Macd", "Rsi", "Ichimoku"]
        performances = OrderedDict()
        for code in technical:
            performances[code] = eval(code)[1]
        performances = sorted(performances.items(), key=lambda x: x[1], reverse=True)
        for code, _ in performances:
            optimizedparams[code] = {"performance": eval(code)[1], "params": eval(code)[2:]}
        return optimizedparams

    def OptimizeParamsWithEvent(self, size=1.0):
        """[summary] optimize parameter of technical indicators above.

        Args:
            size (float, optional): [description]. Defaults to 1.0.

        Returns:
            [type]OrderedDict: [description]like ('Ema', {'events': {'index': [56, 79], 'order': ['SELL', 'BUY']},
             'performance': 969832.0, 'params': (5, 26)})
        """
        optimizedparamswithevents = OrderedDict()
        Ema = self.OptimizeEma(size=size)
        Sma = self.OptimizeSma(size=size)
        Bb = self.OptimizeBb(size=size)
        Macd = self.OptimizeMacd(size=size)
        Rsi = self.OptimizeRsi(size=size)
        Ichimoku = self.OptimizeIchimoku()
        technical = ["Ema", "Sma", "Bb", "Macd", "Rsi", "Ichimoku"]
        performances = OrderedDict()
        for code in technical:
            performances[code] = eval(code)[1]
        performances = sorted(performances.items(), key=lambda x: x[1], reverse=True)
        for code, _ in performances:
            optimizedparamswithevents[code] = {"events": eval(code)[0], "performance": eval(code)[1], "params": eval(code)[2:]}
        return optimizedparamswithevents


class Trade(Optimize):
    def __init__(self, api_key, api_secret, backtest=True, product_code="BTC_JPY", duration="h", stoplimitpercent=0.9):
        self.api_key = api_key
        self.api_secret = api_secret
        self.backtest = backtest
        self.product_code = product_code
        self.duration = duration
        self.candles = get_data.Candle(self.api_key, self.api_secret, code=self.product_code).GetAllCandle(duration=self.duration)
        super().__init__(candles=self.candles)
        self.b = get_data.Balance(self.api_key, self.api_secret, code=self.product_code)
        self.order = order.BitFlayer_Order(self.api_key, self.api_secret)
        self.availavlecurrency = self.order.AvailableBalance()["JPY"]
        self.availavlesize = self.order.AvailableBalance()[self.product_code]
        self.stoplimitpercent = stoplimitpercent
        self.stoplimit = 0.0
        self.b.GetExecutions()
        self.bestparams = None

    def GetClose(self):
        """[summary]Get Close data. If this function called, get new candle.
        """
        self.candles = get_data.Candle(self.api_key, self.api_secret, code=self.product_code).GetAllCandle(duration=self.duration)
        super().__init__(candles=self.candles)
        signalevent = SignalEvents.objects.last()
        signaltime = signalevent.time
        self.now_position = signalevent.side
        self.price = signalevent.price
        candles = self.candle_dict
        self.latest_close = candles["close"][-1]
        self.before_close = candles["close"][-2]
        print(f"now_position={signaltime, self.now_position, self.price},latest_close ={self.latest_close}, before_close={self.before_close} ")

    def SendOrders(self, SELLSIGNAL, BUYSIGNAL):
        """[summary]現在の足の終値が前の足の終値を下回って、現在の保有ポジションの総損益が損失になったときは成り行き注文でドテン売りする、または保有しているポジションがないときは成り行き注文で売る。
            買いポジションを取るときはこの逆。
        """
        logging.info(f"available curenncy={self.availavlecurrency}, available BTC={self.availavlesize}")
        self.GetClose()
        self.stoplimit = self.price * self.stoplimitpercent
        # SELL SIGNAL
        if (SELLSIGNAL or self.latest_close < self.stoplimit) and self.now_position == "BUY":
            performance = self.price - self.latest_close
            if self.backtest:
                print(f"BACKTEST SELL Trade Occur!, potision={self.price}, close={self.latest_close}, performance ={performance} ")
            else:
                sell_code = self.order.SELL(size=self.availavlesize)

                if sell_code is None:
                    logging.error("Cant SELL")
                else:
                    self.stoplimit = 0
                    logger.info(f"{datetime.datetime.now()}:SELL Trade Occured ID ={sell_code['child_order_acceptance_id']}")
        # BUY SIGNAL
        if BUYSIGNAL and self.now_position == "SELL":
            if self.backtest:
                print(f"BACKTEST BUY Trade Occur!, potision={self.price}, close={self.latest_close}")

            else:
                buy_code = self.order.BUY(currency=self.availavlecurrency)

                if buy_code is None:
                    logging.error("Cant BUY")
                else:
                    self.stoplimit = self.close[-1] * self.stoplimitpercent
                    logger.info(f"{datetime.datetime.now()}:BUY Trade Occured ID ={buy_code['child_order_acceptance_id']},size={self.availavlesize}")
        else:
            print(f"{datetime.datetime.now()} No Trade")
            logging.info("No Trade Occured")

    def BbAlgo(self):
        """[summary]現在の足の終値が,lowerbandを上に突き抜け、かつ、現在の終値がN/2 期で最大なら買う。売りは逆。
        """
        self.GetClose()
        if self.bestparams is None:
            _, _, bestN, bestk = self.OptimizeBb()
            bestparams = (bestN, bestk)
        else:
            bestN = self.bestparams[0]
            bestk = self.bestparams[1]
            bestparams = self.bestparams

        len_candles = self.len_candles - 1
        upperband, _, lowerband = self.Bbands(N, k)
        sellsignal = self.RBb(bbUp=upperband, bbDown=lowerband, close=self.close, n=N, i=len_candles) == "SELL"
        buysignal = self.RBb(bbUp=upperband, bbDown=lowerband, close=self.close, n=N, i=len_candles) == "BUY"
        return bestparams, sellsignal, buysignal

    def FollowAlgo(self):
        """[summary]現在の足の終値が前の足の終値を下回って、現在の保有ポジションの総損益が損失になったときは成り行き注文でドテン売りする、または保有しているポジションがないときは成り行き注文で売る。
            買いポジションを取るときはこの逆。
        """
        self.GetClose()
        sellsignal = min(self.latest_close, self.price) < self.before_close
        buysignal = max(self.latest_close, self.price) > self.before_close
        bestparams = ()
        return bestparams, sellsignal, buysignal

    def EmaAlgo(self):
        """[summary] golden closs + close > ema1 なら買う。dead closs + close<ema1 なら売る。
        """
        self.GetClose()
        if self.bestparams is None:
            _, _, bestperiod1, bestperiod2 = self.OptimizeEma()
            Emaperiod1 = bestperiod1
            Emaperiod2 = bestperiod2
            best_periods = (Emaperiod1, Emaperiod2)
        else:
            Emaperiod1 = self.bestparams[0]
            Emaperiod2 = self.bestparams[1]
            best_periods = self.bestparams
        len_candles = self.len_candles - 1
        Ema1 = self.Ema(Emaperiod1)
        Ema2 = self.Ema(Emaperiod2)
        sellsignal = self.REma(Ema1, Ema2, self.close, i=len_candles) == "SELL" or min(self.latest_close, self.price) < self.before_close
        buysignal = self.REma(Ema1, Ema2, self.close, i=len_candles) == "BUY"
        logging.info(f"Optimized Ema params={Emaperiod1, Emaperiod2}")
        print(f"Optimized Ema params={Emaperiod1, Emaperiod2}")
        return best_periods, sellsignal, buysignal

    def DEmaAlgo(self):
        """[summary] golden closs + close > ema1 なら買う。dead closs + close<ema1 なら売る。
        """
        self.GetClose()
        if self.bestparams is None:
            _, _, bestperiod1, bestperiod2 = self.OptimizeDEma()
            Emaperiod1 = bestperiod1
            Emaperiod2 = bestperiod2
            best_periods = (Emaperiod1, Emaperiod2)
        else:
            Emaperiod1 = self.bestparams[0]
            Emaperiod2 = self.bestparams[1]
            best_periods = self.bestparams
        len_candles = self.len_candles - 1
        Ema1 = self.DEma(Emaperiod1)
        Ema2 = self.DEma(Emaperiod2)
        sellsignal = self.RDEma(Ema1, Ema2, self.close, i=len_candles) == "SELL" or min(self.latest_close, self.price) < self.before_close
        buysignal = self.RDEma(Ema1, Ema2, self.close, i=len_candles) == "BUY"
        return best_periods, sellsignal, buysignal

    def SmaAlgo(self):
        """[summary] golden closs + close > ema1 なら買う。dead closs + close<ema1 なら売る。
        """
        self.GetClose()
        if self.bestparams is None:
            _, _, bestperiod1, bestperiod2 = self.OptimizeSma()
            Emaperiod1 = bestperiod1
            Emaperiod2 = bestperiod2
            best_periods = (Emaperiod1, Emaperiod2)
        else:
            Emaperiod1 = self.bestparams[0]
            Emaperiod2 = self.bestparams[1]
            best_periods = self.bestparams

        len_candles = self.len_candles - 1
        Ema1 = self.Sma(Emaperiod1)
        Ema2 = self.Sma(Emaperiod2)

        sellsignal = self.RSma(Ema1, Ema2, self.close, i=len_candles) == "SELL" or min(self.latest_close, self.price) < self.before_close
        buysignal = self.RSma(Ema1, Ema2, self.close, i=len_candles) == "BUY"
        return best_periods, sellsignal, buysignal

    def Trade(self, algo="Ema", time_sleep=60):
        print(f"backtest={self.backtest}")
        bestparams, SELLSIGNAL, BUYSIGNAL = eval("self." + algo + "Algo")()
        self.bestparams = bestparams
        self.SendOrders(SELLSIGNAL=SELLSIGNAL, BUYSIGNAL=BUYSIGNAL)
        print(f"Trade Done. algo={algo}, params={bestparams}")
