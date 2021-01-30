from django.test import TestCase

from chart.models import *
from chart.controllers import ai, get_data


import key
from utils import createdf
import time
import threading
from threading import Lock


class AutoTradeTest(TestCase):

    # def test_DrawCandleStick(self):
    #     createdf.connectandsave()
    #     G = drawgraph.Graph()
    #     periods = (7, 14)
    #     addplt = G.AddEma(*periods)
    #     self.assertIs(G.DrawCandleStick(), mpf.plot(G.df, type="candle", style='yahoo', volume=True))
    #     self.assertIs(G.DrawCandleStick(apds=addplt), mpf.plot(G.df, type="candle", style='yahoo', volume=True, addplot=addplt))

    def test_startbacktest(self):
        createdf.connectandsave()
        # createdf.csv2models()
        api_key = key.api_key
        api_secret = key.api_secret
        b = get_data.Balance(api_key=api_key, api_secret=api_secret)
        b.GetExecutions()
        # algo_name = "Ema"
        # time_sleep = 0.02
        # rep = 2
        backtest = True
        A = ai.Trade(api_key=api_key, api_secret=api_secret, backtest=backtest, duration="h")
        # A.Trade(algo=algo_name, rep=rep, time_sleep=time_sleep)
        th = threading.Thread(group=None, target=A.Trade)
        th.start()
        th.join()
        self.assertEqual(threading.active_count(), 1)
        # th.join(timeout=1.0)
        # time.sleep(5)
        # print(f"thread is alive? {th.is_alive()}")
        # self.assertEqual(threading.active_count(), 1)
