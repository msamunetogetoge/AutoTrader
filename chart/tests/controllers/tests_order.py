from django.test import TestCase

from chart.models import *
from chart.controllers import order

import key

# Create your tests here.


class OrderTests(TestCase):

    def test_Buy(self):
        api_key = key.api_key
        api_secret = key.api_secret
        b = order.BitFlayer_Order(api_key, api_secret)
        buy_code = b.Buy(currency=100)
        self.assertEqual(buy_code, None)

    def test_sell(self):
        api_key = key.api_key
        api_secret = key.api_secret
        b = order.BitFlayer_Order(api_key, api_secret)
        sell_code = b.Sell(size=0.000000001)
        self.assertEqual(sell_code, None)

    def test_AvailableBalance(self):
        api_key = key.api_key
        api_secret = key.api_secret
        b = order.BitFlayer_Order(api_key, api_secret)
        d = b.AvailableBalance()
        key_list = ["JPY", b.product_code]
        self.assertEqual(list(d.keys()), key_list)

    def test_AdjustSize(self):
        api_key = key.api_key
        api_secret = key.api_secret
        b = order.BitFlayer_Order(api_key, api_secret)
        size = b.AdjustSize(size=1.0)
        print(size)
