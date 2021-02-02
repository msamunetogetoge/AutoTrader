from django.core.management.base import BaseCommand

import time

from chart.models import *
from chart.controllers import get_data
import key
import threading


api_key = key.api_key
api_secret = key.api_secret


class StreamThread(threading.Thread):
    def __init__(self):
        super(StreamThread, self).__init__()
        self.setDaemon(False)
        self.name = "StreamThread"

    def run(self):
        while True:
            durations = ["s", "m", "h", "d"]
            cdl = get_data.Candle(api_key=api_key, api_secret=api_secret)
            for duration in durations:
                cdl.CreateCandleWithDuration(duration=duration)
                model = eval("Candle_1" + duration)
                ticker = model.objects.last()
                print(f"CreateCandleWithDuration:{ticker}")
                time.sleep(5)


class Command(BaseCommand):
    """[summary] get candles ftom bitflyer api and save to DB, and save() to Candle_1s, Candle_1m, Candle_1h.

    Args:
        BaseCommand ([type]): [description]
    """

    def handle(self, *args, **options):
        th = StreamThread()
        print("Start GetCandles")
        th.start()
