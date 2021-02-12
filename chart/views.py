from django.shortcuts import render
from django.views.generic import ListView
from django.utils import timezone
from autotrade.context_processors import isAutoTrade
import threading
from threading import Lock
import datetime

from utils import query2dict
from utils import changeproductcode
from chart.graphs import drawgraph
from chart.controllers import ai, get_data, order
from chart import models
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
    if not models.UsingProductCode.objects.exists():
        models.UsingProductCode(code="BTC_JPY").save()
    code = models.UsingProductCode.objects.last().code

    DEma = models.DEmaForm
    Ema = models.EmaForm
    Sma = models.SmaForm
    Bb = models.BbForm
    Ichimoku = models.IchimokuForm
    Rsi = models.RsiForm
    Macd = models.MacdForm

    G = drawgraph.Graph(duration=duration, num_data=100, product_code=code)
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
    })


def backtest(request, indicator=None):
    G = drawgraph.Graph(duration="h", num_data=300, backtest=True)
    graph = G.DrawCandleStickWithOptimizedEvents(indicator=indicator)
    algolist = models.AlgoList.objects.all().values_list("algo", flat=True)

    return render(request, "chart/backtest.html", {
        "graph": graph,
        "algolist": algolist,
    })


class SignalEventsView(ListView):
    def __init__(self):
        self.code = models.UsingProductCode.objects.last().code

    model = models.SignalEvents

    # context_object_name = 'signalevents'
    template_name = 'chart/signalevents.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

    def get_queryset(self):
        api_key = key.api_key
        api_secret = key.api_secret
        get_data.Balance(api_key=api_key, api_secret=api_secret, code=self.code).GetExecutions()
        return models.SignalEvents.objects.all().order_by("-time")


def Trade(request, duration="h", side=None):
    code = models.UsingProductCode.objects.last().code

    balance = get_data.Balance(key.api_key, key.api_secret, code=code).GetBalance()
    jpy = balance["JPY"]['available']
    btc = code.split("_")[0]
    btc = balance[btc]['available']

    child_order_acceptance_id = None
    signalevent = None
    G = drawgraph.Graph(duration=duration, num_data=30, product_code=code)
    plt_fig = G.DrawCandleStick()

    if request.method == "POST":
        orders = order.BitFlayer_Order(api_key=key.api_key, api_secret=key.api_secret, product_code=code)
        side = request.POST["order"]
        size = float(request.POST["num_order"])
        if side == "BUY":
            child_order_acceptance_id = orders.BUY(currency=size)
        elif side == "SELL":
            child_order_acceptance_id = orders.SELL(size=size)
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


event = threading.Event()


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
        logger.info(f'START Trading algo={self.algo_name} ')
        with self.Lock:
            while True:
                time_now = datetime.datetime.now()
                delta = datetime.timedelta(seconds=60 * self.sleep_time)
                next_trade = time_now + delta
                self.T.Trade(algo=self.algo_name)
                for duration in ["s", "m"]:
                    if eval("models.Candle_1" + duration + self.T.product_code).objects.all().count() > 50000:
                        eval("models.Candle_1" + duration + self.T.product_code).objects.all().delete()
                logger.info(f"Sleepng For Next Trade. Next Trade will {next_trade}")
                if event.wait(timeout=60 * self.sleep_time):
                    logger.info(f"END Trading algo= {self.algo_name}")
                    event.clear()
                    break


def AutoTrade(request):
    """[summary] from autotrade.html. this view switch autotrading ON/OFF, and select autotrading algo.
                models.UsingALgo detect using algo. ON/OFF switch is global stop.
                When POST request, TradeThread running and trading per 1/60/1440 minutes.

    Args:
        request ([type]): [description]

    Returns:
        [type]: [description]
    """
    api_key = key.api_key
    api_secret = key.api_secret
    tradetime = {"m": 1, "h": 60, "d": 1440}
    backtest = True
    code = models.UsingProductCode.objects.last().code

    if not models.SignalEvents.objects.exists():
        get_data.Balance(api_key=api_key, api_secret=api_secret).GetExecutions()
    signalevents = models.SignalEvents.objects.order_by("-time")[:5]
    algolists = models.AlgoList.objects.all()
    algolistsform = models.AlgoListForm()
    if request.method == "POST":
        # POST request has 2 pattern. 'select autotrading algo' or 'cancel or re-select autotrading algo'.
        if request.POST.get("stop_algo") is None:
            # 'select autotrading algo' pattern. add UsingAlgo objects.
            algo_name = request.POST.get("select_algo")
            algo = models.AlgoList.objects.get(algo=algo_name)

            duration = request.POST.get("select_duration")
            usingalgo = models.UsingALgo
            usingalgo(algo=algo, duration=duration).save()
            A = ai.Trade(api_key=api_key, api_secret=api_secret, backtest=backtest, duration=duration, product_code=code)
            try:
                pertrade = tradetime[duration]
            except KeyError as e:
                logger.error(e)
                pertrade = 60

            th = TradeThread(algo_name=algo_name, sleep_time=pertrade, TradeInstance=A)
            th.name = "TradeThread"
            th.start()

            return render(request, "chart/autotrade.html", {
                "usealgo": algo,
                "duration": duration,
                "signalevents": signalevents,
            })

        else:
            # 'cancel or re-select autotrading algo' pattern. delete UsingAlgo objects.
            event.set()
            models.UsingALgo.objects.all().delete()
            isAutoTrade(request)

            return render(request, "chart/autotrade.html", {
                "signalevents": signalevents,
                "algolists": algolists,
                "form": algolistsform,
                "durations": ["h", "d", "m"],
            })

    elif models.UsingALgo.objects.exists():
        algo = models.UsingALgo.objects.first().algo
        duration = models.UsingALgo.objects.first().duration

        return render(request, "chart/autotrade.html", {
            "usealgo": algo,
            "signalevents": signalevents,
            "duration": duration,
        })
    else:
        # if UsingAlgo has no object and not POST request, send html to usacble algolists, history and durations list.
        return render(request, "chart/autotrade.html", {

            "signalevents": signalevents,
            "algolists": algolists,
            "form": algolistsform,
            "durations": ["h", "d", "m"],
        })


def Change(request):
    changeproductcode.change_productcode()

    code = models.UsingProductCode.objects.last().code

    DEma = models.DEmaForm
    Ema = models.EmaForm
    Sma = models.SmaForm
    Bb = models.BbForm
    Ichimoku = models.IchimokuForm
    Rsi = models.RsiForm
    Macd = models.MacdForm

    G = drawgraph.Graph(duration="h", num_data=100, product_code=code)

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
    })
