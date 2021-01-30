from django.shortcuts import render
from django.views.generic import ListView
from django.utils import timezone
from autotrade.context_processors import isAutoTrade
import threading
from threading import Lock
import time


from chart.graphs import drawgraph
from chart.controllers import ai, get_data, order
from chart import models
from utils import query2dict
import key

import os
from pathlib import Path

import logging

# Create your views here.

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
logger = logging.getLogger(__name__)


def index(request, duration="h"):
    DEma = models.DEmaForm
    Ema = models.EmaForm
    Sma = models.SmaForm
    Bb = models.BbForm
    Ichimoku = models.IchimokuForm
    Rsi = models.RsiForm
    Macd = models.MacdForm
    G = drawgraph.Graph(duration=duration, num_data=100)
    if request.method == "POST":
        kwargs = query2dict.get_data(request.POST)
    else:

        kwargs = {"DEma": {"params": (7, 14), "Enable": True},
                  "Ema": {"params": (7, 14), "Enable": True},
                  "Sma": {"params": (7, 14), "Enable": True},
                  "Bb": {"params": (20, 2.0), "Enable": True},
                  "Macd": {"params": (12, 26, 9), "Enable": True},
                  "Rsi": {"params": (6, 30, 70), "Enable": True},
                  "Ichimoku": {"params": (9, 26, 52), "Enable": True}
                  }
    graph = G.CustomDraw(**kwargs)

    return render(request, "chart/index.html", {
        "graph": graph,
        "DEma": DEma,
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
    G = drawgraph.Graph(duration=duration, num_data=50)
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


def backtest(request, indicator=None):
    G = drawgraph.Graph(duration="h", num_data=300, backtest=True)
    graph = G.DrawCandleStickWithOptimizedEvents(indicator=indicator)

    return render(request, "chart/backtest.html", {
        "graph": graph,
    })


class SignalEventsView(ListView):
    model = models.SignalEvents
    # context_object_name = 'signalevents'
    template_name = 'chart/signalevents.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

    def get_queryset(self):
        return models.SignalEvents.objects.all().order_by("-time")


def Trade(request, duration="h", side=None, code="BTC_JPY"):
    balance = get_data.Balance(key.api_key, key.api_secret, code=code).GetBalance()
    jpy = balance["JPY"]['available']
    btc = code.split("_")[0]
    btc = balance[btc]['available']

    child_order_acceptance_id = None
    signalevent = None
    G = drawgraph.Graph(duration=duration, num_data=30)
    plt_fig = G.DrawCandleStick()

    if request.method == "POST":
        orders = order.BitFlayer_Order(api_key=key.api_key, api_secret=key.api_secret, product_code=code)
        side = request.POST["order"]
        size = float(request.POST["num_order"])
        if side == "BUY":
            child_order_acceptance_id = orders.BUY(currency=size)
        elif side == "SELL":
            child_order_acceptance_id = orders.SELL(currency=size)
        if child_order_acceptance_id is not None:
            signalevent = models.SignalEvents.objects.last()
            child_order_acceptance_id = child_order_acceptance_id["child_order_acceptance_id"]

    return render(request, "chart/trade.html", {
        "jpy": jpy,
        "btc": btc,
        "graph": plt_fig,
        "id": child_order_acceptance_id,
        "signalevents": signalevent
    })


stop = False


class TradeThread(threading.Thread):
    def __init__(self, algo_name: str, sleep_time: int, TradeInstance: ai.Trade):
        super(TradeThread, self).__init__()
        self.setDaemon(False)
        self.Lock = Lock()
        self.algo_name = algo_name
        self.T = TradeInstance
        self.sleep_time = sleep_time
        self.name = "TradeThread"

    def run(self):
        print(f'START Trading algo={self.algo_name} ')
        with self.Lock:
            while not stop:
                self.T.Trade(algo=self.algo_name, time_sleep=self.sleep_time)
        print(f"END Trading algo= {self.algo_name}")


def AutoTrade(request):
    """[summary] from autotrade.html. this view switch autotrading ON/OFF, and select autotrading algo.
                models.UsingALgo detect using algo. ON/OFF switch is global stop.
                TradeThread is running and trading per 45 minutes background when autotrade.html POSTs "select_algo"
    """
    global stop
    api_key = key.api_key
    api_secret = key.api_secret
    signalevents = models.SignalEvents.objects.order_by("-time")[:5]
    algolists = models.AlgoList.objects.all()
    algolistsform = models.AlgoListForm()
    if request.method == "POST":
        # POST request has 2 pattern. 'select autotrading algo' or 'cancel or re-select autotrading algo'.
        print(f"Aliving Thread is {threading.active_count()}")
        if request.POST.get("stop_algo") is None:
            stop = False
            # 'select autotrading algo' pattern. add UsingAlgo objects.
            algo_name = request.POST.get("select_algo")
            algo = models.AlgoList.objects.get(algo=algo_name)
            usingalgo = models.UsingALgo
            usingalgo(algo=algo).save()
            if isAutoTrade(request)["AUTOTRADE"]:
                print("isAuoTrade was called")
                backtest = False
                A = ai.Trade(api_key=api_key, api_secret=api_secret, backtest=backtest, duration="h")
                th = TradeThread(algo_name=algo_name, sleep_time=45, TradeInstance=A)
                th.name = "TradeThread"
                th.start()

            else:
                logging.error("Cant Start Trade")

            return render(request, "chart/autotrade.html", {
                "usealgo": algo,
                "signalevents": signalevents,
            })

        else:
            # 'cancel or re-select autotrading algo' pattern. delete UsingAlgo objects.
            stop = True
            models.UsingALgo.objects.all().delete()
            isAutoTrade(request)

            return render(request, "chart/autotrade.html", {

                "signalevents": signalevents,
                "algolists": algolists,
                "form": algolistsform
            })

    elif models.UsingALgo.objects.exists():
        print(isAutoTrade(request)["ALGO"])
        algo = models.UsingALgo.objects.first().algo

        return render(request, "chart/autotrade.html", {
            "usealgo": algo,
            "signalevents": signalevents,
        })

    else:
        # if UsingAlgo has no object and not POST request, send html to usacble algo list and history.
        return render(request, "chart/autotrade.html", {

            "signalevents": signalevents,
            "algolists": algolists,
            "form": algolistsform
        })
