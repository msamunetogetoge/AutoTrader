from django.http import HttpRequest
from chart import models


def isAutoTrade(request: HttpRequest):
    """[summary] AutoTrade がONかOFFか判定する辞書autotrade.html からのpostの中身によって、

    Args:
        request (HttpRequest): [description]

    Returns:
        [type]dict: [description]
    """

    if not models.UsingProductCode.objects.exists():
        models.UsingProductCode(code="BTC_JPY").save()
    product_code = models.UsingProductCode.objects.last().code

    if models.UsingALgo.objects.exists():
        algo_name = models.UsingALgo.objects.first().algo.algo
        duration = models.UsingALgo.objects.first().duration

        dic = {"AUTOTRADE": True, "ALGO": f"AUTOTRADING algo= {algo_name}", "DURATION": f"duration = {duration}", "USINGPRODUCTCODE": product_code}
    else:

        dic = {"AUTOTRADE": False, "ALGO": "AUTOTRADIG OFF", "DURATION": "", "USINGPRODUCTCODE": product_code}
    return dic
