from django.test import TestCase

from chart.models import *
from chart.controllers import get_data, ai
from chart.graphs import drawgraph

import key
from utils import createdf

import numpy as np
import talib
import datetime


# Create your tests here.


class GraphTest(TestCase):

    # def test_DrawCandleStick(self):
    #     createdf.connectandsave()
    #     G = drawgraph.Graph()
    #     periods = (7, 14)
    #     addplt = G.AddEma(*periods)
    #     self.assertIs(G.DrawCandleStick(), mpf.plot(G.df, type="candle", style='yahoo', volume=True))
    #     self.assertIs(G.DrawCandleStick(apds=addplt), mpf.plot(G.df, type="candle", style='yahoo', volume=True, addplot=addplt))

    def test_Draw(self):
        createdf.connectandsave()
        G = drawgraph.Graph()
        G.DrawCandleStick()

    def test_CustomDraw(self):
        createdf.connectandsave()
        G = drawgraph.Graph()
        kwargs = {"Sma": {"params": (7, 14), "Enable": True},
                  "Ema": {"params": (7, 14), "Enable": True},
                  "Bb": {"params": (20, 2.0), "Enable": False},
                  "Macd": {"params": (12, 26, 9), "Enable": True},
                  "Rsi": {"params": (6, 30, 70), "Enable": True},
                  "Ichimoku": {"params": (9, 26, 52), "Enable": True}
                  }
        G.CustomDraw(**kwargs)

    def test_DrawCandleStickWithOptimizedEvents(self):
        createdf.connectandsave(num_data=300)
        G = drawgraph.Graph()
        G.DrawCandleStickWithOptimizedEvents(indicator="Ema")
