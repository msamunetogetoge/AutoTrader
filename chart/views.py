from django.shortcuts import render

from chart.graphs import drawgraph
from chart.controllers import ai
from chart import models
from utils import query2dict
import os
from pathlib import Path

import logging

# Create your views here.

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
logger = logging.getLogger(__name__)


def index(request, duration="h"):
    Ema = models.EmaForm
    Sma = models.SmaForm
    Bb = models.BbForm
    Ichimoku = models.IchimokuForm
    Rsi = models.RsiForm
    Macd = models.MacdForm
    G = drawgraph.Graph(duration)
    if request.method == "POST":
        kwargs = query2dict.get_data(request.POST)

    else:

        kwargs = {"Ema": {"params": (7, 14), "Enable": True},
                  "Sma": {"params": (7, 14), "Enable": True},
                  "Bb": {"params": (20, 2.0), "Enable": True},
                  "Macd": {"params": (12, 26, 9), "Enable": True},
                  "Rsi": {"params": (6, 30, 70), "Enable": True},
                  "Ichimoku": {"params": (9, 26, 52), "Enable": True}
                  }
    graph = G.CustomDraw(**kwargs)

    return render(request, "chart/index.html", {
        "graph": graph,
        "Ema": Ema,
        "Sma": Sma,
        "Bb": Bb,
        "Ichimoku": Ichimoku,
        "Rsi": Rsi,
        "Macd": Macd,
        "s": "s"
    })


def optimize(request, duration="h"):
    Ema = models.EmaForm
    Sma = models.SmaForm
    Bb = models.BbForm
    Ichimoku = models.IchimokuForm
    Rsi = models.RsiForm
    Macd = models.MacdForm
    G = drawgraph.Graph(duration)
    if duration == "s":
        candles = models.Candle_1s
    if duration == "m":
        candles = models.Candle_1m
    else:
        candles = models.Candle_1h
    codes = ["Ema", "Sma", "Bb", "Macd", "Rsi", "Ichimoku"]
    kwargs = {}
    optimized_params = ai.Optimize(candles=candles).OptimizeParams()
    for code in optimized_params.keys():
        kwargs[code] = {"params": optimized_params[code]["params"]}
    print(kwargs)
    graph = G.CustomDraw(**kwargs)

    return render(request, "chart/index.html", {
        "graph": graph,
        "Ema": Ema,
        "Sma": Sma,
        "Bb": Bb,
        "Ichimoku": Ichimoku,
        "Rsi": Rsi,
        "Macd": Macd
    })
