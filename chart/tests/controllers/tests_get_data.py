from django.test import TestCase

from chart.models import *
from chart.controllers import get_data

import key

import datetime


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


class BalanceTests(TestCase):

    def test_Get_Balance(self):
        api_key = key.api_key
        api_secret = key.api_secret
        codes = ["JPY", "BTC"]
        b = get_data.Balance(api_key, api_secret)
        balance = b.GetBalance(codes=codes)
        print(balance)
        balance_jp = balance[codes[0]]
        k = ['currency_code', 'amount', 'available']
        self.assertEqual(list(balance.keys()), codes)
        self.assertEqual(list(balance_jp.keys()), k)
