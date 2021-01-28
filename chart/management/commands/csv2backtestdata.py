from django.core.management.base import BaseCommand

import pandas as pd
from chart.models import *


class Command(BaseCommand):
    """[summary]Get data from stockdata.sql and save to Django models(Candle_1s, Candle_1m, Candle_1h)

    Args:
        BaseCommand ([type]):
    """

    def handle(self, *args, **options):
        def csv2models():
            data_name = "BTC_JPY_bitflyer.csv"
            csv_data = pd.read_csv(data_name)
            csv_data["time"] = pd.to_datetime(csv_data["time"], format='%Y年%m月%d日')
            for _, data in csv_data.iterrows():
                model = Candle_BackTest()
                model.time = data.time
                model.close = int(data.close.replace(",", ""))
                model.open = int(data.open.replace(",", ""))
                model.high = int(data.high.replace(",", ""))
                model.low = int(data.low.replace(",", ""))
                model.volume = int(float(data.volume.replace("K", "")) * 1000)
                model.save()
            first = Candle_BackTest.objects.first().time
            last = Candle_BackTest.objects.last().time
            print(f"data is saved! first object is {first}, last object is {last} ")
        csv2models()
