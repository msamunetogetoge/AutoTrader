
import datetime
import os
import sys

import pybitflyer

import key

from chart.models import *


class Ticker():
    """Ticker を取得するクラス。
    """

    def __init__(self, api_key, api_secret, code="BTC_JPY"):
        self.api = pybitflyer.API(api_key, api_secret)
        self.product_code = code
        self.ticker = self.api.ticker(product_code=self.product_code)

    def DateTime(self, time=None):
        timeformat = "%Y-%m-%dT%H:%M:%S"
        if time is None:
            date = self.ticker["timestamp"][:19]
            date = datetime.datetime.strptime(date, timeformat)
            return date
        else:
            date = time.strftime(timeformat)
            return date

    def TruncateDateTime(self, duration, time=None):
        if time is None:
            date = self.DateTime()
        else:
            date = self.DateTime(time)

        if duration == "h":
            timeformat = "%Y-%m-%dT%H"
            date = datetime.datetime.strptime(
                date.strftime(timeformat), timeformat)
        elif duration == "m":
            timeformat = "%Y-%m-%dT%H:%M"
            date = datetime.datetime.strptime(
                date.strftime(timeformat), timeformat)
        elif duration == "s":
            date = date
        return date

    def GetMidPrice(self):
        """GetMidPrice from ticker

        Returns:
            float: (BestBid +BestAsk) /2
        """
        return (self.ticker["best_bid"] + self.ticker["best_ask"]) / 2


class Candle(Ticker):
    """candlesticグラフを描く為のクラス。
    durationをs,m,hで指定して、tickerからcandleを作ったり、モデルに保存したりする。
    """

    def __init__(self, api_key, api_secret, code="BTC_JPY"):
        super().__init__(api_key=api_key, api_secret=api_secret, code=code)

    def Save(self, candle, duration):
        """models.Candle_1durationの要素を受け取って上書きするクラス

        Args:
            candle (class 'chart.models.Candle_1duration' の要素): 1duration = 1s,1m,1h
        """
        c = candle
        tablename = "Candle_1" + duration
        model = tablename
        cdl = eval(model)(
            time=c.time,
            open=c.open,
            close=c.close,
            high=c.high,
            low=c.low,
            volume=c.volume)
        cdl.save()

    def IsExistCandle(self, duration, time):
        date = self.TruncateDateTime(duration=duration, time=time)
        tablename = "Candle_1" + duration
        candle = eval(tablename)(time=date)
        if candle.volume is None:
            return False
        else:
            return True

    def GetCandle(self, duration):
        """[summary] Get or create django.db.models element. If 'tickdr' which ticker-class got were exits in models(Candle_1s, etc...), get it. If not exists, create it in models.

        Args:
            duration ([type]str in ['s7, 'm', 'h']) ): [description] s, m or h decide which models choosen.

        Returns:
            [type]chart.models.Candle_1s, 1m, 1h: [description] data whici is time = self.ticker['timestamp']
        """
        model = "Candle_1" + duration
        date = self.TruncateDateTime(duration)
        candle = eval(model)(time=date)
        if candle.volume is None:
            price = self.GetMidPrice()
            candle = eval(model)(
                time=date,
                open=price,
                close=price,
                high=price,
                low=price,
                volume=self.ticker["volume"])
            candle.save()
            return candle
        else:
            return candle

    def GetAllCandle(self, duration):
        """[summary]Get django.db.models object from duration. if duration='s', this funcution returns chart.models.Candle_1s.


        Args:
            duration ([type] str in ['s7, 'm', 'h']): [description] s, m or h decide which models choosen.

        Returns:
            [type]: [description] django.db.models from chart.models
        """
        model = "Candle_1" + duration
        model = eval(model)
        return model

    def CreateCandleWithDuration(self, duration, time=None):
        current_candle = self.GetCandle(duration)
        price = self.GetMidPrice()
        current_candle.close = price
        if current_candle.high <= price:
            current_candle.high = price
        elif current_candle.low >= price:
            current_candle.low = price
        current_candle.volume += self.ticker["volume"]
        current_candle.close = price
        current_candle.save()


class Balance():
    def __init__(self, api_key, api_secret, code="BTC_JPY"):
        self.api = pybitflyer.API(api_key, api_secret)
        self.product_code = code

    def GetBalance(self, codes=["JPY", "BTC"]):
        balance_dict = {}
        balances = self.api.getbalance()
        for balance in balances:
            code = balance["currency_code"]
            if code in codes:
                balance_dict[code] = balance

        return balance_dict
