from chart.models import *
from chart.controllers import ai, get_data
import key

from pathlib import Path
import os

from django_pandas.io import read_frame

import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import numpy as np
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


class Graph:
    def __init__(self, duration="h", num_data=300, backtest=False):
        self.ticker = get_data.Ticker(key.api_key, key.api_secret)
        self.duration = duration
        self.backtest = backtest
        if self.backtest is True:
            self.datas = Candle_BackTest
            self.num_data = self.datas.objects.all().count()
        else:
            self.datas = eval("Candle_1" + duration)
            self.num_data = num_data
        self.df = self.MakeDf()
        self.fig = make_subplots(rows=3, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2],
                                 specs=[[{"secondary_y": True}],
                                        [{}],
                                        [{}]])

    def MakeDf(self):
        """[summary] make pd.DataFrame(df) from candles, df.rows=['time', 'open', 'high', 'low', 'close', 'volume'], df.index = df.time, where df.time.dtype = datetime64[ns].len(df) = self.num_data

        Returns:
            [type]: [description] pd.DataFrame
        """
        df = read_frame(self.datas.objects.all().order_by("time"))
        df = df[["time", 'open', 'high', 'low', 'close', 'volume']]
        df = df.set_index("time")
        df = df[-self.num_data:]
        return df

    def DrawCandleStick(self, signalevents="tukau"):
        """[summary] draw candle stick of self.df and volume, if signalevents is not None, draw it, too.

        Args:
            signalevents ([type], optional): [description]. Defaults to None. django.db.models like SignalEvents

        Returns:
            [type]: [description]
        """
        self.fig.add_trace(go.Candlestick(x=self.df.index,
                                          open=self.df["open"],
                                          high=self.df["high"],
                                          low=self.df["low"],
                                          close=self.df["close"], name="Ticker"), secondary_y=True)
        self.fig.add_trace(go.Bar(x=self.df.index, y=self.df["volume"], name="Volume", marker_color='aqua'), secondary_y=False)
        self.fig.layout.yaxis2.showgrid = False
        self.fig.update_yaxes(autorange=True, fixedrange=False)
        self.fig.update_layout(autosize=False,
                               width=1000,
                               height=500,
                               margin=dict(
                                   l=50,
                                   r=50,
                                   b=10,
                                   t=50,
                                   pad=1
                               ),
                               paper_bgcolor="LightSteelBlue",
                               )
        self.fig.update_xaxes(rangeslider_thickness=0.03)
        if signalevents is not None:
            # if signalevents is not None,use REAL execution history
            signalevents = SignalEvents.objects.order_by("time")
            try:
                # if df have no items, stop drawing
                index_first = str(self.df.head(1).index.values[0])[:19]
            except IndexError as e:
                logging.error(e)
                plot_fig = plot(self.fig, output_type='div', include_plotlyjs=False)
                return plot_fig

            signalevents = signalevents.filter(time__gte=index_first)
            x = list(signalevents.values_list("time", flat=True))
            for i, t in enumerate(x):
                x[i] = self.ticker.TruncateDateTime(duration=self.duration, time=t)
            event = list(signalevents.values_list("side", "price", "size"))
            try:
                # 昔のデータ等はグラフに表示しない
                self.fig.add_trace(go.Scatter(x=x, y=self.df["close"][x], name="Child orders", mode="markers",
                                              text=event, textposition="bottom left", textfont=dict(
                    family="sans serif",
                    size=12,
                    color="black"),
                    marker=dict(
                    color='maroon',
                    size=6,)
                ), secondary_y=True)
            except Exception as e:
                logging.info(e)
                pass

        plot_fig = plot(self.fig, output_type='div', include_plotlyjs=False)
        return plot_fig

    def AddSma(self, *args):
        """[summary] Creating addplot instance, using args[0]=period1, args[1]=period2.
        Args:
            args ([type]tuple of int ): [description] (period1, period2)
        Returns:
            [type] mpf.make_addplot(): [description] Graph of Emas, Ema(args[0])=orange, Ema(args[1])=red.
        """
        if len(args) == 2 and len(self.df) > max(args):
            t = ai.Technical(candles=self.datas)
            self.df["sma1"] = t.Sma(timeperiod=args[0])[-self.num_data:]
            self.df["sma2"] = t.Sma(timeperiod=args[1])[-self.num_data:]
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["sma1"], name=f"sma({args[0]})", line=dict(color='darkorange', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["sma2"], name=f"sma({args[1]})", line=dict(color='tomato', width=1), visible='legendonly'), secondary_y=True)
        else:
            print("args=(period1, period2) where periods are int.")
            return None

    def AddEma(self, *args):
        """[summary] Creating addplot instance, using args[0]=period1, args[1]=period2.
        Args:
            args ([type]tuple of int ): [description] (period1, period2)
        Returns:
            [type] mpf.make_addplot(): [description] Graph of Emas, Ema(args[0])=orange, Ema(args[1])=red.
        """
        if len(args) == 2 and len(self.df) > max(args):
            t = ai.Technical(candles=self.datas)
            self.df["ema1"] = t.Ema(timeperiod=args[0])[-self.num_data:]
            self.df["ema2"] = t.Ema(timeperiod=args[1])[-self.num_data:]
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["ema1"], name=f"ema({args[0]})", line=dict(color='orange', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["ema2"], name=f"ema({args[1]})", line=dict(color='red', width=1), visible='legendonly'), secondary_y=True)
        else:
            print("args=(period1, period2) where periods are int.")
            return None

    def AddDEma(self, *args):
        """[summary] Creating addplot instance, using args[0]=period1, args[1]=period2.
        Args:
            args ([type]tuple of int ): [description] (period1, period2)
        Returns:
            [type] mpf.make_addplot(): [description] Graph of DEmas, DEma(args[0])=orange, DEma(args[1])=red.
        """
        if len(args) == 2 and len(self.df) > max(args):
            t = ai.Technical(candles=self.datas)
            self.df["dema1"] = t.DEma(timeperiod=args[0])[-self.num_data:]
            self.df["dema2"] = t.DEma(timeperiod=args[1])[-self.num_data:]
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["dema1"], name=f"dema({args[0]})", line=dict(color='orange', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["dema2"], name=f"dema({args[1]})", line=dict(color='red', width=1), visible='legendonly'), secondary_y=True)
        else:
            print("draw DEma:args=(period1, period2) or database length have some issue")
            return None

    def AddBb(self, *args):
        """[summary] Creating addplot instance, using args[0]=BbN, args[1]=Bbk.
        Args:
            args ([type]tuple of int ): [description] (BbN, Bbk)
        Returns:
            [type] mpf.make_addplot(): [description] Graph of BBands, bands =blue
        """
        if len(args) == 2 and len(self.df) > max(args):
            t = ai.Technical(candles=self.datas)
            u, _, l = t.Bbands(args[0], args[1])
            self.df["upperband"], self.df["lowerband"] = u[-self.num_data:], l[-self.num_data:]
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["upperband"], mode="lines", name="upperband", line=dict(color='blue', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["lowerband"], mode="lines", name="lowerband", line=dict(color='blue', width=1), visible='legendonly'), secondary_y=True)
        else:
            print("draw Bb:args=(BbN, Bbk) or database length have some issue")
            return None

    def AddMacd(self, *args):
        """[summary] Creating addplot instance, using args[0]=fastperiod,
                    args[1]=slowperiod, args[2]= signalperiod.
            Args:
                args ([type]tuple of int ): [description] (fastperiod, slowperiod, signalperiod)
            Returns:
                [type] mpf.make_addplot(): [description] Graph of Macd, macd = orange, macdsignal = red, macdhist = skyblue.
        """
        if len(args) == 3 and len(self.df) > max(args):
            t = ai.Technical(candles=self.datas)
            macd, macdsignal, macdhist = t.Macd(args[0], args[1], args[2])
            self.df["macd"], self.df["macdsignal"], self.df["macdhist"] = macd[-self.num_data:], macdsignal[-self.num_data:], macdhist[-self.num_data:]
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["macd"], mode="lines", name="macd", line=dict(color='orange', width=1)), row=2, col=1)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["macdsignal"], mode="lines", name="macd", line=dict(color='red', width=1)), row=2, col=1)
            self.fig.add_trace(go.Bar(x=self.df.index, y=self.df["macdhist"], name="macdhist", marker_color='blueviolet'), row=2, col=1)
        else:
            print("args=(fastperiod, slowperiod, signalperiod) or database length have some issue")
            return None

    def AddRsi(self, *args):
        """[summary] Creating addplot instance, using args[0]=period,
                    args[1]=buythread, args[2]= sellthread.
            Args:
                args ([type]tuple of (int, float, float) ): [description] (timeperiod, buythread, sellthread )
            Returns:
                [type] mpf.make_addplot(): [description] Graph of Rsi
        """
        if len(args) == 3 and len(self.df) > max(args):
            t = ai.Technical(candles=self.datas)
            self.df["rsi"] = t.Rsi(args[0])[-self.num_data:]
            self.df["buythread"] = np.array([30.0] * len(self.df)).reshape(-1,)
            self.df["sellthread"] = np.array([70.0] * len(self.df)).reshape(-1,)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["rsi"], mode="lines", name="rsi", line=dict(color='orange', width=2)), row=3, col=1)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["buythread"], mode="lines", name="buythread", line=dict(color='black', width=1, dash="dot")), row=3, col=1)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["sellthread"], mode="lines", name="sellthread", line=dict(color='black', width=1, dash="dot")), row=3, col=1)
            # apdict1 = mpf.make_addplot(self.df["rsi"], panel=3, color="orange")
            # apdict2 = mpf.make_addplot(self.df["buythread"], panel=3, color="black")
            # apdict3 = mpf.make_addplot(self.df["sellthread"], panel=3, color="black")
            # apdict = [apdict1, apdict2, apdict3]
            # return apdict
        else:
            print("draw Rsi:args=(timeperiod, buythread, sellthread ) or database length have some issue")
            return None

    def AddIchimoku(self, *args):
        """[summary] Creating addplot instance, using args[0]=t,
                    args[1]=k, args[2]= s.
            Args:
                args ([type]tuple of int ): [description] (t ,k, s)
            Returns:
                [type] mpf.make_addplot(): [description] Graph of Ichimoku, tenkansen = orange, kijunsen = red, senkou =black, chikou=pink
        """
        if len(args) == 3 and len(self.df) > max(args):
            t = ai.Technical(candles=self.datas)
            t, k, s_A, s_B, c = t.Ichimoku(args[0], args[1], args[2])
            self.df["tenkan"], self.df["kijun"], self.df["senkouA"], self.df["senkouB"], self.df["chikou"] = t[-self.num_data:], k[-self.num_data:], s_A[-self.num_data:], s_B[-self.num_data:], c[-self.num_data:]
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["tenkan"], mode="lines", name="tenkan", line=dict(color='orange', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["kijun"], mode="lines", name="kijun", line=dict(color='red', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["senkouA"], mode="lines", name="senkouA", line=dict(color='black', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["senkouB"], mode="lines", name="senkouB", line=dict(color='black', width=1), visible='legendonly'), secondary_y=True)
            self.fig.add_trace(go.Scatter(x=self.df.index, y=self.df["chikou"], mode="lines", name="chikou", line=dict(color='pink', width=1), visible='legendonly'), secondary_y=True)
        else:
            print("draw Ichimoku:args=(t, k, s ) or database length have some issue")
            return None

    def CustomDraw(self, **kwargs):
        """[summary] From kwargs, check
        Args:
            kwargs ([type] ): [description] ('code',{'params':(params)})
                                            like ('Bb', {'performance': 13569533.5, 'params': (10, 1.60), 'Enable': True})

        """

        addEma = self.AddEma(*kwargs["Ema"]["params"])
        addDEma = self.AddDEma(*kwargs["DEma"]["params"])
        addSma = self.AddSma(*kwargs["Sma"]["params"])
        addBb = self.AddBb(*kwargs["Bb"]["params"])
        addIchimoku = self.AddIchimoku(*kwargs["Ichimoku"]["params"])
        addMacd = self.AddMacd(*kwargs["Macd"]["params"])
        addRsi = self.AddRsi(*kwargs["Rsi"]["params"])

        plot_fig = self.DrawCandleStick()
        return plot_fig

    def DrawCandleStickWithOptimizedEvents(self, indicator=None):
        if indicator is not None:
            results = eval("ai.Optimize(candles=self.datas).Optimize" + indicator + "()")
            events = results[0]
            performance = results[1]
            params = results[2:]
            event = list(events["order"])
            try:
                add = eval("self.Add" + indicator + f"(*{params})")
            except AttributeError as e:
                logging.error(e)
                pass
            finally:
                x = list(BackTestSignalEvents.objects.values_list("time", flat=True))
                event = list(BackTestSignalEvents.objects.values_list("side", flat=True))
                self.fig.add_trace(go.Scatter(x=x, y=self.df["close"][x], name=f"Events of {indicator}", mode="markers+text",
                                              text=event, textposition="bottom left", textfont=dict(
                    family="sans serif",
                    size=18,
                    color="black"),
                    marker=dict(
                    color='maroon',
                    size=10,)
                ), secondary_y=True)
            self.fig.update_layout(title=f"Backtest:{indicator},params={params},performance={performance}")

        plot_fig = self.DrawCandleStick(signalevents=None)

        return plot_fig
