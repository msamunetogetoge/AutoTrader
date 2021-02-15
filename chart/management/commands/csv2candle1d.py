from django.core.management.base import BaseCommand

import pandas as pd
from chart.models import *


class Command(BaseCommand):
    """[summary]Get data from csv file to Candle1d.

    Args:
        BaseCommand ([type]):
    """

    def add_arguments(self, parser):  # コマンド引数の定義

        # str型の必須引数の定義
        parser.add_argument('data_name', type=str, help='使うcsvデータの相対パス')

    def handle(self, *args, **options):
        def csv2models():
            data_name = options["data_name"]
            csv_data = pd.read_csv(data_name)
            csv_data["time"] = pd.to_datetime(csv_data["time"], format='%Y年%m月%d日')
            for _, data in csv_data.iterrows():
                model = Candle_1d()
                model.time = data.time
                model.close = int(data.close.replace(",", ""))
                model.open = int(data.open.replace(",", ""))
                model.high = int(data.high.replace(",", ""))
                model.low = int(data.low.replace(",", ""))
                model.volume = int(float(data.volume.replace("K", "")) * 1000)
                model.save()
            first = Candle_1d.objects.first().time
            last = Candle_1d.objects.last().time
            print(f"data is saved! first object is {first}, last object is {last} ")
        csv2models()
