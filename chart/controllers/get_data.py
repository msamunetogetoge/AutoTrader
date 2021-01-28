
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
        """[summary] create datetime.datetime object from ticker or str object

        Args:
            time ([type], optional): [description]. str or datetime.datetime object

        Returns:
            [type]datetime.datetime: [description]format='%Y-%m-%dT%H:%M:%S'
        """
        timeformat = "%Y-%m-%dT%H:%M:%S"
        if time is None:
            date = self.ticker["timestamp"][:19]
            date = datetime.datetime.strptime(date, timeformat)
            return date
        elif isinstance(time, str):
            date = time[:19]
            date = datetime.datetime.strptime(date, timeformat)
            return date

        elif isinstance(time, datetime.datetime):
            date = time
        else:
            print("time is str or datetime.datetime ")

        return date

    def TruncateDateTime(self, duration, time=None):
        """[summary] create trucated datetime like datetime.datetime(year,month,hour)

        Args:
            duration ([type]): [description]
            time ([type], optional): [description]. Defaults to None.

        Returns:
            [type]datetime.datetime: [description] duration='h'→datetime.datetime(year,month,hour),duration='m'→datetime.datetime(year,month,hour,minute)
        """
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
        """models.Candle_1durationの要素を受け取って上書きする

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

    def GetCandle(self, duration, time=None):
        """[summary] Get or create django.db.models objects.
            Filtering time=now(time=None) or given time, then, if  'ticker' was exits in models(Candle_1s, etc...), get it.
            If objects was not exists, create time=given time(or now) prices = self.MidPrice().

        Args:
            duration ([type]str in ['s, 'm', 'h']) ): [description] s, m or h decide which models choosen.

        Returns:
            [type]chart.models.Candle_1s, 1m, 1h: [description] data which is time = self.ticker['timestamp']
        """
        model = "Candle_1" + duration
        candle = eval(model)
        date = self.TruncateDateTime(duration=duration, time=time)
        if not candle.objects.filter(time=date).exists():
            price = self.GetMidPrice()
            candle = candle(
                time=date,
                open=price,
                close=price,
                high=price,
                low=price,
                volume=self.ticker["volume"])
            candle.save()
            return candle
        else:
            return candle.objects.filter(time=date).first()

    def GetAllCandle(self, duration):
        """[summary]Get django.db.models object from duration. if duration='s', this funcution returns chart.models.Candle_1s.
        Args:
            duration ([type] str in ['s, 'm', 'h']): [description] s, m or h decide which models choosen.

        Returns:
            [type]: [description] django.db.models from chart.models
        """
        model = "Candle_1" + duration
        model = eval(model)
        return model

    def CreateCandleWithDuration(self, duration, time=None):
        """[summary] get candle from self.GetCandle. then update candle params and save.

        Args:
            duration ([type]): [description]
        """
        current_candle = self.GetCandle(duration=duration, time=time)
        price = self.GetMidPrice()

        current_candle.open = current_candle.open
        current_candle.close = price
        if current_candle.high <= price:
            current_candle.high = price
        elif current_candle.low >= price:
            current_candle.low = price
        current_candle.volume += self.ticker["volume"]
        current_candle.save()


class Balance():
    def __init__(self, api_key, api_secret, code="BTC_JPY"):
        self.api = pybitflyer.API(api_key, api_secret)
        self.product_code = code

    def GetBalance(self):
        codes = ["JPY"]
        btc = self.product_code.split("_")[0]
        codes.append(btc)
        balance_dict = {}
        balances = self.api.getbalance()
        for balance in balances:
            code = balance["currency_code"]
            if code in codes:
                balance_dict[code] = balance

        return balance_dict

    def GetExecutions(self):
        executions = self.api.getchildorders(product_code="BTC_JPY", child_order_state="COMPLETED")
        for ex in executions:
            se = SignalEvents()
            se.price = ex["average_price"]
            se.side = ex["side"]
            se.size = ex["size"]
            se.time = ex["child_order_date"]
            se.save()
        # print(SignalEvents.objects.order_by("time").values_list("time", "side", "price")[:10])
