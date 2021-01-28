from chart.models import *
from chart.controllers import get_data

import datetime
import sqlite3
import pandas as pd


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


def connectandsave(num_data=60):
    """[summary] create model objects(Candle_1h) from stockdata.sql tablename=BTC_JPY_1h0m0s.

    Args:
        num_data (int, optional): [description]. Defaults to 60.
    """
    model_name = "Candle_1h"
    name = "stockdata.sql"
    conn = sqlite3.connect(name)
    cur = conn.cursor()

    table_name = "BTC_JPY_1h0m0s"
    cur.execute(
        f'SELECT * FROM {table_name} WHERE time is not null LIMIT {num_data}')
    X = cur.fetchall()
    register(datas=X, model_name=model_name)
    cur.close()
    conn.close()


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
        print(model)
        model.save()
    print("models saved!")
