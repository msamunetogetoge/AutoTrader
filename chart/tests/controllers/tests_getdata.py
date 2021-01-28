from django.test import TestCase

from chart.models import *
from chart.controllers import get_data
from utils import createdf

import key

import datetime
import time


# Create your tests here.


class TickerTest(TestCase):
    """[summary]Check functions can get Ticker, can make TruncateDatetime, Get Midproce

    Args:
        TestCase ([type]): [description]
    """

    def test_GetTicker(self):
        api_key = key.api_key
        api_secret = key.api_secret
        t = get_data.Ticker(api_key, api_secret)
        ticker_info = ['product_code', 'state', 'timestamp', 'tick_id', 'best_bid', 'best_ask', 'best_bid_size', 'best_ask_size', 'total_bid_depth', 'total_ask_depth', 'market_bid_size', 'market_ask_size', 'ltp', 'volume', 'volume_by_product']
        ticker = t.ticker
        self.assertEqual(list(ticker.keys()), ticker_info)

    def test_Datetime_timeNone(self):
        api_key = key.api_key
        api_secret = key.api_secret
        t = get_data.Ticker(api_key, api_secret)
        date = t.DateTime()

        durations = ["h", "m", "s"]
        h = datetime.datetime(date.year, date.month, date.day, date.hour)
        m = datetime.datetime(date.year, date.month, date.day, date.hour, date.minute)
        s = datetime.datetime(date.year, date.month, date.day, date.hour, date.minute, date.second)

        date_h = t.TruncateDateTime("h")
        date_m = t.TruncateDateTime("m")
        date_s = t.TruncateDateTime("s")
        for duration in durations:
            self.assertEqual(eval(duration), eval("date_" + duration))

        def test_Datetime_timeNotNone(self):
            api_key = key.api_key
            api_secret = key.api_secret
            t = get_data.Ticker(api_key, api_secret)
            time_now = datetime.datetime.now()
            date = t.DateTime(time=time_now)

            durations = ["h", "m", "s"]
            h = datetime.datetime(date.year, date.month, date.day, date.hour)
            m = datetime.datetime(date.year, date.month, date.day, date.hour, date.minute)
            s = datetime.datetime(date.year, date.month, date.day, date.hour, date.minute, date.second)

            date_h = t.TruncateDateTime(duration="h", time=time_now)
            date_m = t.TruncateDateTime(duration="m", time=time_now)
            date_s = t.TruncateDateTime(duration="s", time=time_now)
            for duration in durations:
                self.assertEqual(eval(duration), eval("date_" + duration))

    def test_GetMidPrice(self):
        api_key = key.api_key
        api_secret = key.api_secret
        t = get_data.Ticker(api_key, api_secret)
        mid = t.GetMidPrice()
        self.assertEqual(mid, (t.ticker['best_bid'] + t.ticker['best_ask']) / 2)


class CandleTest(TestCase):

    def test_Save(self):
        createdf.connectandsave()
        api_key = key.api_key
        api_secret = key.api_secret
        c = get_data.Candle(api_key, api_secret)
        candle = Candle_1h.objects.order_by("time").last()
        durations = ["s", "m", "h"]
        for duration in durations:
            c.Save(candle, duration)
            self.assertEqual(eval("Candle_1" + duration).objects.exists(), True)

    def test_GetCandle_candlenotexists(self):
        """[summary] createdf.connectandsave() generate only Candle_1h.SoCandle_1s has no objects.
        GetCsndle function create new candle of Candle_1s"""
        createdf.connectandsave()
        duration = "s"
        api_key = key.api_key
        api_secret = key.api_secret
        c = get_data.Candle(api_key, api_secret)
        self.assertEqual(Candle_1s.objects.exists(), False)
        candle = c.GetCandle(duration=duration)
        self.assertEqual(Candle_1s.objects.exists(), True)
        self.assertEqual(candle, Candle_1s.objects.first())

    def test_GetCandle_candleisexists(self):
        """[summary] create new_candle in Candle_1h, then candle=GetCandle('h') is equal to new_candle
        """
        createdf.connectandsave()
        duration = "h"
        api_key = key.api_key
        api_secret = key.api_secret
        c = get_data.Candle(api_key, api_secret)
        now_time = c.TruncateDateTime(duration=duration, time=datetime.datetime.now())
        new_candle = Candle_1h(
            time=now_time,
            open=0,
            close=0,
            high=0,
            low=0,
            volume=0)
        new_candle.save()
        candle = c.GetCandle(duration=duration, time=now_time)
        # print(f"Get Candle returns last object of Candle_1h")
        # print(f"candle.time={candle.time}, new_candle.time ={new_candle.time}")
        self.assertEqual(candle, new_candle)

    def test_CreateCandleWithDuration(self):
        """[summary] create new candle data of datetime.datetime.now(new_candle). CreateCandleWithDuration(duration,now) makes new_candles to another candle(after_candle).
            They have same primaly key, so they are equal but not is.
        """
        duration = "h"
        api_key = key.api_key
        api_secret = key.api_secret
        c = get_data.Candle(api_key, api_secret)
        now_time = c.TruncateDateTime(duration=duration, time=datetime.datetime.now())
        new_candle = Candle_1h(
            time=now_time,
            open=4000000,
            close=3000000,
            high=4100000,
            low=3000000,
            volume=10000)
        new_candle.save()
        c.CreateCandleWithDuration(duration=duration, time=now_time)
        after_candle = Candle_1h.objects.last()
        self.assertEqual(new_candle, after_candle)
        self.assertIsNot(new_candle, after_candle)


class BalanceTests(TestCase):

    def test_GetBalance(self):

        api_key = key.api_key
        api_secret = key.api_secret
        codes = ["JPY", "BTC"]
        b = get_data.Balance(api_key, api_secret)
        balance = b.GetBalance()
        print(balance)
        balance_jp = balance[codes[0]]
        k = ['currency_code', 'amount', 'available']
        self.assertEqual(list(balance.keys()), codes)
        self.assertEqual(list(balance_jp.keys()), k)

    def test_GetExecutions(self):
        api_key = key.api_key
        api_secret = key.api_secret
        b = get_data.Balance(api_key, api_secret)
        b.GetExecutions()
        self.assertEqual(SignalEvents.objects.exists(), True)
