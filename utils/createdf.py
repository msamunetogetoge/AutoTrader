from chart.models import *
from chart.controllers import get_data

import datetime
import sqlite3


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
