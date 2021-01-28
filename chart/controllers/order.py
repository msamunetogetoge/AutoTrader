import pybitflyer

import key

from chart.controllers import get_data
import logging

logger = logging.getLogger(__name__)


class BitFlayer_Order():
    """[summary] bitflyer に成り行き注文で売買注文を行うクラス
    """

    def __init__(self, api_key, api_secret, product_code="BTC_JPY"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api = pybitflyer.API(api_key, api_secret)
        self.product_code = product_code

    def AvailableBalance(self, tax=0.001):
        """[summary]

        Args:
            tax (float, optional): [description]手数料をいれる. Defaults to 0.001.

        Returns:
            [type] dict : [description] like {"JPY": 50000, "BTC_JPY": 0.05} dict.
        """
        b = get_data.Balance(self.api_key, self.api_secret)
        balance_code = self.product_code.split("_")[0]
        balance = b.GetBalance()

        available_JPY = balance["JPY"]["available"]
        available_CRP = balance[balance_code]["available"]

        d = {"JPY": available_JPY, self.product_code: available_CRP}
        return d

    def AdjustSize(self, size=0.00000001):
        """[summary] 手数料込みで取り扱えるsizeを計算する。

        Args:
            size (float, optional): [description]. Defaults to 0.00000001.
            tax (float, optional): [description]. Defaults to 0.001.

        Returns:
            [type]float : [description] 1 satoshi 刻み
        """
        tax = self.api.gettradingcommission(product_code=self.product_code)["commission_rate"]
        useable = 1.0 - tax
        size = size * useable
        size = int(size * 100000000) / 100000000
        return size

    def BUY(self, currency, use_parcent=0.9, code="BTC_JPY"):
        """[summary] 買いたい額を円で指定して、bitflyer から成り行き注文を行う。
        売買が成立するとIDを返し、失敗するとNone を返す。

        Args:
            currency ([type]): [description]
            use_parcent (float, optional): [description]. Defaults to 0.9.
            code (str, optional): [description]. Defaults to "BTC_JPY".

        Returns:
            [type]dict : [description]  like{child_order_acceptance_id:xxxxxxxx} or None
        """
        ticker = get_data.Ticker(self.api_key, self.api_secret).ticker
        price = ticker["best_ask"]
        usecurrency = currency * use_parcent
        size = 1 / (price / usecurrency)
        size = self.AdjustSize(size=size)
        size = int(size * 100000000) / 100000000
        buy_code = self.api.sendchildorder(
            product_code=code,
            child_order_type="MARKET",
            side="BUY", size=size,
            minute_to_expire=10,
            time_in_force="GTC")
        if "child_order_acceptance_id" in buy_code.keys():
            return buy_code
        else:
            logger.error(Exception("Cant BUY"))
            print("Cant BUY")
            return None

    def SELL(self, code="BTC_JPY", size=0.00000001):
        """[summary] 売りたい量のbitcoinをbitcoinの枚数で指定して、bitflyer から成り行き注文を行う。
        売買が成立するとIDを返し、失敗するとNone を返す。

        Args:
            currency ([type]): [description]
            use_parcent (float, optional): [description]. Defaults to 0.9.
            code (str, optional): [description]. Defaults to "BTC_JPY".

        Returns:
            [type]dict : [description]  like{child_order_acceptance_id:xxxxxxxx} or None
        """
        size = self.AdjustSize(size=size)
        size = int(size * 100000000) / 100000000
        sell_code = self.api.sendchildorder(
            product_code=code,
            child_order_type="MARKET",
            side="SELL", size=size,
            minute_to_expire=10,
            time_in_force="GTC")
        if "child_order_acceptance_id" in sell_code.keys():
            return sell_code
        else:
            logger.error(Exception("Cant SELL"))
            print("Cant SELL")
            return None
