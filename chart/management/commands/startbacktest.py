from django.core.management.base import BaseCommand

from chart.controllers import ai
import key
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """[summary] get candles ftom bitflyer api and save to DB, and save() to Candle_1s, Candle_1m, Candle_1h.

    Args:
        BaseCommand ([type]): [description]
    """

    def add_arguments(self, parser):  # コマンド引数の定義

        # str型の必須引数の定義
        parser.add_argument('algo', type=str, help='使うアルゴリズムを指定')

    def handle(self, *args, **options):

        api_key = key.api_key
        api_secret = key.api_secret
        backtest = True
        print("Start backtest")
        logging.info("start backtest")
        while True:
            A = ai.Trade(api_key=api_key, api_secret=api_secret, backtest=backtest, duration="h")
            A.Trade(algo=options["algo"], time_sleep=0.15)
