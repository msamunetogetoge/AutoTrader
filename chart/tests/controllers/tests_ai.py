from django.test import TestCase

from chart.models import *
from chart.controllers import ai, get_data

import key
from utils import createdf

import numpy as np
import datetime
import time
from collections import OrderedDict

# Create your tests here.


class TechnicalTests(TestCase):

    def test_init(self):
        """[summary]testing class returns dict

        Returns:
            [type]dict: [description] {time:... ,open:...,close:..., high:...,low:... }
        """
        t = ai.Technical(eval("Candle_1h"))
        keys = ["time",
                "product_code",
                "open",
                "close",
                "high",
                "low",
                "volume"]
        t_keys = list(t.candle_dict.keys())
        self.assertEqual(keys, t_keys)

    def test_EMA(self):
        """[summary]calculate EMA from models.Candle_1h timeperiod=10

        Returns:
            [type]: [description]
        """
        createdf.connectandsave()
        timeperiod = 5
        t = ai.Technical(eval("Candle_1h"))
        ema = t.Ema(timeperiod=timeperiod)
        element_num = len(t.candle_dict["close"])
        self.assertEqual(ema.shape, (element_num,))

    def test_Bbands(self):
        """[summary]calculate Bbands from models.Candle_1h timeperiod=5.
        Check return arraies shape, upperbound > lowerbound

        Returns:
            [type]: [description]
        """
        createdf.connectandsave()

        t = ai.Technical(eval("Candle_1h"))
        timeperiod = 5
        upperband, middleband, lowerband = t.Bbands(timeperiod=timeperiod)
        element_num = len(t.candle_dict["close"])
        is_one = 1 * (upperband > lowerband)[timeperiod:]
        is_one = np.prod(is_one)
        self.assertEqual(upperband.shape, (element_num,))
        self.assertEqual(upperband.shape, lowerband.shape)
        self.assertEqual(is_one, 1)

    def test_Macd(self):
        """[summary]calculate Macd from models.Candle_1h timeperiods=12,26,9.
        Check return arraies shape

        Returns:
            [type]: [description]
        """
        createdf.connectandsave()

        t = ai.Technical(eval("Candle_1h"))
        macd, macdsignal, macdhist = t.Macd()
        element_num = len(t.candle_dict["close"])

        self.assertEqual(macd.shape, (element_num,))
        self.assertEqual(macd.shape, macdsignal.shape)
        self.assertEqual(macd.shape, macdhist.shape)

    def test_Rsi(self):
        """[summary]calculate Rsi from models.Candle_1h timeperiods=14
        Check return array shape, values in [0,100]

        Returns:
            [type]: [description]
        """
        createdf.connectandsave()

        t = ai.Technical(eval("Candle_1h"))
        timeperiod = 14
        values = t.Rsi(timeperiod)
        real_values = values[timeperiod:]
        element_num = len(t.candle_dict["close"])
        lager_zero = np.all(0 <= real_values)
        lower_hundred = np.all(100 >= real_values)

        self.assertEqual(values.shape, (element_num,))
        self.assertEqual(lager_zero, True)
        self.assertEqual(lower_hundred, True)

    def test_Hv(self):
        """[summary]calculate Hv from models.Candle_1h timeperiods=5, ndev=1
        Check return larger than zero

        Returns:
            [type]: [description]
        """
        createdf.connectandsave()

        t = ai.Technical(eval("Candle_1h"))
        timeperiod = 5
        ndev = 1
        value = t.Hv(timeperiod, ndev)[timeperiod:]
        lager_zero = np.all(value > 0)

        self.assertEqual(lager_zero, True)

    def test_Ichimoku(self):
        """[summary]calculate Hv from models.Candle_1h timeperiods=5, ndev=1
        Check return larger than zero

        Returns:
            [type]: [description]
        """
        createdf.connectandsave()
        t = ai.Technical(eval("Candle_1h"))
        tenkan, kijun, senkouA, senkouB, chikou = t.Ichimoku()
        element_num = len(t.candle_dict["close"])
        self.assertEqual(tenkan.shape, (element_num,))
        self.assertEqual(tenkan.shape, kijun.shape)
        self.assertEqual(tenkan.shape, senkouA.shape)
        self.assertEqual(tenkan.shape, senkouB.shape)
        self.assertEqual(tenkan.shape, chikou.shape)


class BackTestTests(TestCase):
    """[summary]BackTestTest : noevents → returns dict{'index':[], 'order':[]}. order is 'Sell' or 'Buy'.
                QoptimizeTest: performance is lager than 0.

    Args:
        TestCase ([type]): [description]
    """

    def test_BackTest_init(self):
        """[summary] Testing Candle length is calculated by len(self.candles),
                    where self.candles =list(models.Candle_1h.objects.all()),etc.
        """
        createdf.connectandsave(1)
        b = ai.BackTest(eval("Candle_1h"))
        length = len(b.candles)
        self.assertIs(b.len_candles, length)

    def test_BackTestEMA(self):
        createdf.connectandsave()
        orders = ["", "Sell", "Buy"]
        b = ai.BackTest(eval("Candle_1h"))
        period1 = 7
        period2 = 14
        events = b.BackTestEma(period1, period2)
        length = len(events["index"])

        if length == 0:
            self.assertEqual(events["order"], [])
        else:
            for i in range(length):
                self.assertEqual(events["order"][i] in orders, True)
                self.assertEqual(events["index"][i] < b.len_candles, True)

    def test_Optimize_EMA(self):
        createdf.connectandsave()
        opt = ai.Optimize(eval("Candle_1h"))
        performance, bestperiod1, bestperiod2 = opt.OptimizeEma()
        self.assertEqual(performance >= 0, True)

    def test_BackTestBb(self):
        createdf.connectandsave()
        orders = ["", "Sell", "Buy"]
        b = ai.BackTest(eval("Candle_1h"))
        n = 14
        k = 2
        events = b.BackTestBb(n, k)
        length = len(events["index"])
        if length == 0:
            self.assertEqual(events["order"], [])
        else:
            for i in range(length):
                self.assertEqual(events["order"][i] in orders, True)
                self.assertEqual(events["index"][i] < b.len_candles, True)

    def test_Optimize_BB(self):
        createdf.connectandsave()
        opt = ai.Optimize(eval("Candle_1h"))
        performance, bestperiod1, bestperiod2 = opt.OptimizeBb()
        self.assertEqual(performance >= 0, True)

    def test_BackTestIchimoku(self):
        createdf.connectandsave()
        orders = ["", "Sell", "Buy"]
        b = ai.BackTest(eval("Candle_1h"))
        t, k, s = 9, 26, 52
        events = b.BackTestIchimoku(t, k, s)
        length = len(events["index"])
        if length == 0:
            self.assertEqual(events["order"], [])
        else:
            for i in range(length):
                self.assertEqual(events["order"][i] in orders, True)
                self.assertEqual(events["index"][i] < b.len_candles, True)

    def test_BackTestMacd(self):
        createdf.connectandsave()
        orders = ["", "Sell", "Buy"]
        b = ai.BackTest(eval("Candle_1h"))
        fastperiod = 12
        slowperiod = 26
        signalperiod = 9
        events = b.BackTestMacd(fastperiod, slowperiod, signalperiod)
        length = len(events["index"])
        if length == 0:
            self.assertEqual(events["order"], [])
        else:
            for i in range(length):
                self.assertEqual(events["order"][i] in orders, True)
                self.assertEqual(events["index"][i] < b.len_candles, True)

    def test_Optimize_Macd(self):
        createdf.connectandsave()
        opt = ai.Optimize(eval("Candle_1h"))
        performance, bestMacdFastPeriod, bestMacdSlowPeriod, bestMacdSignalPeriod = opt.OptimizeMacd()
        self.assertEqual(performance >= 0, True)

    def test_BsckTestRsi(self):
        createdf.connectandsave()
        orders = ["", "Sell", "Buy"]
        b = ai.BackTest(eval("Candle_1h"))
        period = 14
        buyThread = 70
        sellThread = 30
        events = b.BackTestRsi(period, buyThread, sellThread)
        length = len(events["index"])
        if length == 0:
            self.assertEqual(events["order"], [])
        else:
            for i in range(length):
                self.assertEqual(events["order"][i] in orders, True)
                self.assertEqual(events["index"][i] < b.len_candles, True)

    def test_OptimizeRdi(self):
        createdf.connectandsave()
        opt = ai.Optimize(eval("Candle_1h"))
        performance, bestperiod, bestBuyThread, bestSellThreadd = opt.OptimizeRsi()
        self.assertEqual(performance >= 0, True)

    def test_OptimizeParams(self):
        """[summary]Check optimized-params are ordered by performance
        """
        createdf.connectandsave()
        opt = ai.Optimize(eval("Candle_1h"))
        optimizedparams = opt.OptimizeParams()
        print(optimizedparams)
        ks = optimizedparams.keys()
        length = len(list(ks))
        for i in range(length - 1):
            k_1 = list(ks)[i]
            k_2 = list(ks)[i + 1]
            p_1 = optimizedparams[k_1]["performance"]
            p_2 = optimizedparams[k_2]["performance"]
            b = p_1 >= p_2
            self.assertEqual(b, True)


class TradeTests(TestCase):

    # def test_is_Create(self):
    #     api_key = key.api_key
    #     api_secret = key.api_secret
    #     ts = ai.Trade(api_key, api_secret, duration="s")
    #     tm = ai.Trade(api_key, api_secret, duration="m")
    #     time.sleep(2)
    #     candle = get_data.Candle(api_key, api_secret)
    #     candle.CreateCandleWithDuration("s")
    #     candle.CreateCandleWithDuration("m")
    #     bs = ts.is_Create()
    #     bm = tm.is_Create()

    #     self.assertEqual(bs, True)
    #     self.assertEqual(bm, False)

    def test_Trade(self):
        """[summary] Testing Trade with only backetest.
        """
        createdf.connectandsave()
        api_key = key.api_key
        api_secret = key.api_secret
        t = ai.Trade(api_key=api_key, api_secret=api_secret)
        t.Trade()
