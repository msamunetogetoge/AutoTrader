from django.core.management.base import BaseCommand

import time

from chart.models import *
from chart.controllers import get_data
import key


class Command(BaseCommand):
    """[summary] get candles ftom bitflyer api and save to DB, and save() to Candle_1s, Candle_1m, Candle_1h.

    Args:
        BaseCommand ([type]): [description]
    """

    def handle(self, *args, **options):
        print("Start GetCandles")
        api_key = key.api_key
        api_secret = key.api_secret
        durations = ["s", "m", "h"]
        while True:
            cdl = get_data.Candle(api_key=api_key, api_secret=api_secret)
            for duration in durations:
                cdl.CreateCandleWithDuration(duration=duration)
                model = eval("Candle_1" + duration)
                ticker = model.objects.last()
                print(f"CreateCandleWithDuration:{ticker}")
            time.sleep(5)
