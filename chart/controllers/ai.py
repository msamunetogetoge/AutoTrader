from django.forms.models import model_to_dict

import numpy as np
import talib
from collections import OrderedDict

from chart.models import *
from chart.controllers import get_data, order
import math
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
        self.candles = list(candles.objects.all())
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


class BackTest(Technical):
    """[summary]どのタイミングで売買するかを決める為のクラス

    Args:
        Technical ([type]class): [description] Technical指標をまとめたクラス。各指標に対して売買の基準を決定する
    """

    def __init__(self, candles):
        super().__init__(candles=candles)
        self.len_candles = len(self.candles)

    def BackTestEma(self, period1=7, period2=14):
        events = {"index": [], "order": []}
        if self.len_candles <= max(period1, period2):
            return events

        ema1 = self.Ema(period1)
        ema2 = self.Ema(period2)

        for i in range(1, self.len_candles):
            if i < max(period1, period2):
                continue
            if ema1[i - 1] < ema2[i - 1] and ema1[i] >= ema2[i]:
                events["index"].append(i)
                events["order"].append("Buy")

            if ema1[i - 1] > ema2[i - 1] and ema1[i] <= ema2[i]:
                events["index"].append(i)
                events["order"].append("Sell")

        return events

    def BackTestSma(self, period1=26, period2=52):
        events = {"index": [], "order": []}
        if self.len_candles <= max(period1, period2):
            return events

        sma1 = self.Sma(period1)
        sma2 = self.Sma(period2)

        for i in range(1, self.len_candles):
            if i < max(period1, period2):
                continue
            if sma1[i - 1] < sma2[i - 1] and sma1[i] >= sma2[i]:
                events["index"].append(i)
                events["order"].append("Buy")

            if sma1[i - 1] > sma2[i - 1] and sma1[i] <= sma2[i]:
                events["index"].append(i)
                events["order"].append("Sell")

        return events

    def BackTestBb(self, n=14, k=2.0):
        events = {"index": [], "order": []}
        if self.len_candles <= n:
            return events

        bbUp, _, bbDown = self.Bbands(n, k)
        for i in range(1, self.len_candles):
            if i < n:
                continue

            if (bbDown[i - 1] > self.close[i - 1] and bbDown[i] <= self.close[i]):
                events["index"].append(i)
                events["order"].append("Buy")

            if bbUp[i - 1] < self.close[i - 1] and bbUp[i] >= self.close[i]:
                events["index"].append(i)
                events["order"].append("Sell")
        return events

    def BackTestIchimoku(self, t=9, k=26, s=52):
        events = {"index": [], "order": []}
        if self.len_candles <= s:
            return events
        High = np.array(self.candle_dict["high"]).reshape(-1,)
        Low = np.array(self.candle_dict["low"]).reshape(-1,)
        tenkan, kijun, senkouA, senkouB, chikou = self.Ichimoku(t, k, s)

        for i in range(1, self.len_candles):
            if (chikou[i - 1] < High[i - 1] and chikou[i] >= High[i] and
                senkouA[i] < Low[i] and senkouB[i] < Low[i] and
                    tenkan[i] > kijun[i]):
                events["index"].append(i)
                events["order"].append("Buy")

            if (chikou[i - 1] > Low[i - 1] and chikou[i] <= Low[i] and
                senkouA[i] > High[i] and senkouB[i] > High[i] and
                    tenkan[i] < kijun[i]):
                events["index"].append(i)
                events["order"].append("Sell")

        return events

    def BackTestMacd(self, fastperiod=12, slowperiod=26, signalperiod=9):
        events = {"index": [], "order": []}
        if self.len_candles <= min(fastperiod, slowperiod, signalperiod):
            return events

        macd, macdsignal, _ = self.Macd(fastperiod, slowperiod, signalperiod)

        for i in range(1, self.len_candles):
            if (macd[i] < 0 and
                macdsignal[i] < 0 and
                macd[i - 1] < macdsignal[i - 1] and
                    macd[i] >= macdsignal[i]):
                events["index"].append(i)
                events["order"].append("Buy")

            if (macd[i] > 0 and
                macdsignal[i] > 0 and
                macd[i - 1] > macdsignal[i - 1] and
                    macd[i] <= macdsignal[i]):
                events["index"].append(i)
                events["order"].append("Sell")

        return events

    def BackTestRsi(self, period=14, buyThread=70, sellThread=30):
        events = {"index": [], "order": []}
        if self.len_candles <= period:
            return events

        values = self.Rsi(period)
        for i in range(1, self.len_candles):
            if values[i - 1] == 0 or values[i - 1] == 100:
                continue

            if values[i - 1] < buyThread and values[i] >= buyThread:
                events["index"].append(i)
                events["order"].append("Buy")

            if values[i - 1] > sellThread and values[i] <= sellThread:
                events["index"].append(i)
                events["order"].append("Sell")

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
            if i == 0 and order == "Sell":
                continue
            if order == "Buy":
                price = self.close[oi]
                total -= price * size
                isHolding = True
            if order == "Sell":
                price = self.close[oi]
                total += price * size
                isHolding = False
                beforeSell = total
        if isHolding is True:
            return beforeSell
        return total

    def OptimizeEma(self, size=1.0):
        bestperiod1 = 7
        bestperiod2 = 14
        performance = 0.0
        for period1 in range(3, 20):
            for period2 in range(10, 30):
                events = self.BackTestEma(period1=period1, period2=period2)
                profit = self.Profit(events=events)
                if profit > performance:
                    performance = profit
                    bestperiod1 = period1
                    bestperiod2 = period2
        return performance, bestperiod1, bestperiod2

    def OptimizeSma(self, size=1.0):
        bestperiod1 = 26
        bestperiod2 = 52
        performance = 0.0
        for period1 in range(14, 42):
            for period2 in range(35, 70):
                events = self.BackTestSma(period1=period1, period2=period2)
                profit = self.Profit(events=events)
                if profit > performance:
                    performance = profit
                    bestperiod1 = period1
                    bestperiod2 = period2
        return performance, bestperiod1, bestperiod2

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
        return performance, bestN, bestk

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
        return performance, bestMacdFastPeriod, bestMacdSlowPeriod, bestMacdSignalPeriod

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
        return performance, bestperiod, bestBuyThread, bestSellThread

    def OptimizeIchimoku(self, size=1.0):
        performance = 0.0
        t = 9
        k = 26
        s = 52
        events = self.BackTestIchimoku()
        profit = self.Profit(events=events)
        if profit > performance:
            performance = profit
        return performance, t, k, s

    def OptimizeParams(self, size=1.0):

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
            performances[code] = eval(code)[0]
        performances = sorted(performances.items(), key=lambda x: x[1], reverse=True)
        for code, _ in performances:
            optimizedparams[code] = {"performance": eval(code)[0], "params": eval(code)[1:]}
        return optimizedparams


class Trade():
    def __init__(self, api_key, api_secret, product_code="BTC_JPY", duration="h", stoplimitpercent=0.9):
        self.api_key = api_key
        self.api_secret = api_secret
        self.product_code = product_code
        self.duration = duration
        self.ticker = get_data.Candle(self.api_key, self.api_secret, code=self.product_code)
        self.candles = self.ticker.GetAllCandle(duration=self.duration)
        self.order = order.BitFlayer_Order(self.api_key, self.api_secret)
        self.stoplimitpercent = stoplimitpercent
        self.stoplimit = 0.0

    # def is_Create(self):
    #     ticker = self.ticker.ticker

    #     time_now = datetime.datetime.now()
    #     time_now = self.ticker.TruncateDateTime(time=time_now)
    #     b = self.ticker.IsExistCandle(duration=self.duration, time=time_now)
    #     if datetime_now != last_date:
    #         return True
    #     else:
    #         return False

    # def IsOrder(self, duration):
    #     Optimize(candles=Candle_1s)→最後のindex が今→true

    def Trade(self, backtest=True):
        """[summary]1.Prepare constants and optimizedparameters has information of useful or not.
         2. Calculate Techniques.
         3. For each truncate-time, calculate buy or sell, and count points.

        Args:
            candles ([type]django.db.models): [description] models.Candle_1s etc...
        """
        availavlecurrency = self.order.AvailableBalance()["JPY"]
        availavlesize = self.order.AvailableBalance()[self.product_code]

        t = Technical(candles=self.candles)
        optimizedparams = Optimize(candles=self.candles).OptimizeParams()
        ks = optimizedparams.keys()
        for code in list(ks):
            if optimizedparams[code]["performance"] > 0:
                optimizedparams[code]["Enable"] = True
            else:
                optimizedparams[code]["Enable"] = False

        length = len(list(self.candles.objects.all()))

        Emaperiod1 = optimizedparams["Ema"]["params"][0]
        Emaperiod2 = optimizedparams["Ema"]["params"][1]
        Ema1 = t.Ema(Emaperiod1)
        Ema2 = t.Ema(Emaperiod2)
        Smaperiod1 = optimizedparams["Sma"]["params"][0]
        Smaperiod2 = optimizedparams["Sma"]["params"][1]
        Sma1 = t.Sma(Smaperiod1)
        Sma2 = t.Sma(Smaperiod2)
        BbN = optimizedparams["Bb"]["params"][0]
        Bbk = optimizedparams["Bb"]["params"][1]
        bbUp, _, bbDown = t.Bbands(BbN, Bbk)
        Ichimokut = optimizedparams["Ichimoku"]["params"][0]
        Ichimokuk = optimizedparams["Ichimoku"]["params"][1]
        Ichimokus = optimizedparams["Ichimoku"]["params"][2]
        High = np.array(t.candle_dict["high"]).reshape(-1,)
        Low = np.array(t.candle_dict["low"]).reshape(-1,)
        tenkan, kijun, senkouA, senkouB, chikou = t.Ichimoku(Ichimokut, Ichimokuk, Ichimokus)
        Macdfastperiod = optimizedparams["Macd"]["params"][0]
        Macdslowperiod = optimizedparams["Macd"]["params"][1]
        Macdsignalperiod = optimizedparams["Macd"]["params"][2]
        macd, macdsignal, _ = t.Macd(Macdfastperiod, Macdslowperiod, Macdsignalperiod)
        Rsiperiod = optimizedparams["Rsi"]["params"][0]
        Rsibuythread = optimizedparams["Rsi"]["params"][1]
        Rsisellthread = optimizedparams["Rsi"]["params"][2]
        Rsivalues = t.Rsi(Rsiperiod)

        print(optimizedparams)

        for i in range(1, length):
            buyPoint = 0
            sellPoint = 0
            if optimizedparams["Ema"]["Enable"] and min(Emaperiod1, Emaperiod2) <= i:
                if Ema1[i - 1] < Ema2[i - 1] and Ema1[i] >= Ema2[i]:
                    buyPoint += 1

                if Ema1[i - 1] > Ema2[i - 1] and Ema1[i] <= Ema2[i]:
                    sellPoint += 1
            if optimizedparams["Sma"]["Enable"] and min(Smaperiod1, Smaperiod2) <= i:
                if Sma1[i - 1] < Sma2[i - 1] and Sma1[i] >= Sma2[i]:
                    buyPoint += 1

                if Sma1[i - 1] > Sma2[i - 1] and Sma1[i] <= Sma2[i]:
                    sellPoint += 1
            if optimizedparams["Bb"]["Enable"] and BbN <= i:
                if bbDown[i - 1] > t.close[i - 1] and bbDown[i] <= t.close[i]:
                    buyPoint += 1
                if bbUp[i - 1] < t.close[i - 1] and bbUp[i] >= t.close[i]:
                    sellPoint += 1
            if optimizedparams["Macd"]["Enable"]:
                if macd[i] < 0 and macdsignal[i] < 0 and macd[i - 1] < macdsignal[i - 1] and macd[i] >= macdsignal[i]:
                    buyPoint += 1
                if macd[i] > 0 and macdsignal[i] > 0 and macd[i - 1] > macdsignal[i - 1] and macd[i] <= macdsignal[i]:
                    sellPoint += 1
            if optimizedparams["Ichimoku"]["Enable"]:
                if (chikou[i - 1] < High[i - 1] and chikou[i] >= High[i] and
                    senkouA[i] < Low[i] and senkouB[i] < Low[i] and
                        tenkan[i] > kijun[i]):
                    buyPoint += 1
                if (chikou[i - 1] > Low[i - 1] and chikou[i] <= Low[i] and
                    senkouA[i] > High[i] and senkouB[i] > High[i] and
                        tenkan[i] < kijun[i]):
                    sellPoint += 1
            if optimizedparams["Rsi"]["Enable"] and Rsivalues[i - 1] != 0 and Rsivalues[i - 1] != 100:
                if Rsivalues[i - 1] < Rsibuythread and Rsivalues[i] >= Rsibuythread:
                    buyPoint += 1
                if Rsivalues[i - 1] > Rsisellthread and Rsivalues[i] <= Rsisellthread:
                    sellPoint += 1

            if buyPoint > 0:
                if backtest:
                    print("Buy Trade Occur!")
                else:
                    return None
                    buy_code = self.order.Buy(currency=availavlecurrency)
                    self.stoplimit = t.close[-1] * self.stoplimitpercent
                    if buy_code is None:
                        logging.error("Cant Buy")

            if sellPoint > 0:
                if backtest:
                    print("Sell Trade Occur!")
                else:
                    sell_code = self.order.Sell(size=availavlesize)
                    self.stoplimit = 0
                    if sell_code is None:
                        logging.error("Cant Sell")

            if not(buyPoint > 0 or sellPoint > 0 or self.stoplimit > t.close[i]):
                print("No Trade")
