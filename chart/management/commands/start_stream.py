from django.core.management.base import BaseCommand

import time

from chart.models import *
from chart.controllers import get_data
import key


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Start GetCandles")
        api_key = key.api_key
        api_secret = key.api_secret
        durations = ["s", "m", "h"]
        while True:
            cdl = get_data.Candle(api_key=api_key, api_secret=api_secret)
            for duration in durations:
                cdl.CreateCandleWithDuration(duration)
                model = "Candle_1" + duration
                ticker = eval(model).objects.last()
                print(f"CreateCandleWithDuration:{ticker}")
            time.sleep(5)
