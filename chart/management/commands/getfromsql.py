from django.core.management.base import BaseCommand

import datetime
import sqlite3

from chart.models import *


class Command(BaseCommand):
    """[summary]Get data from stockdata.sql and save to Django models(Candle_1s, Candle_1m, Candle_1h)

    Args:
        BaseCommand ([type]):
    """

    def handle(self, *args, **options):
        def DateTime(date):
            timeformat = "%Y-%m-%dT%H:%M:%S"
            date = date[:19]
            date = datetime.datetime.strptime(date, timeformat)
            return date

        def register(datas, model_name):
            for data in datas:
                t = DateTime(data[0])
                eval(model_name)(time=t,
                                 open=data[1],
                                 close=data[2],
                                 high=data[3],
                                 low=data[4],
                                 volume=data[5]).save()

        def connectandsave(duration):

            model_name = "Candle_1" + duration
            name = "stockdata.sql"
            conn = sqlite3.connect(name)
            cur = conn.cursor()
            if duration == "s":
                table_name = "BTC_JPY_1s"
            elif duration == "m":
                table_name = "BTC_JPY_1m0s"
            elif duration == "h":
                table_name = "BTC_JPY_1h0m0s"
            cur.execute(
                f'SELECT * FROM {table_name}')
            X = cur.fetchall()
            register(datas=X, model_name=model_name)
            cur.close()
            conn.close()

        for duration in ["s", "m", "h"]:
            try:
                connectandsave(duration)
                print(f"End Saving {duration} Datas!")
            except sqlite3.OperationalError:
                print(f"No such table duration = {duration}")
