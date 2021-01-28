from django.http import HttpRequest
from chart import models


import key


def isAutoTrade(request: HttpRequest):
    """[summary] AutoTrade がONかOFFか判定する辞書autotrade.html からのpostの中身によって、

    Args:
        request (HttpRequest): [description]

    Returns:
        [type]dict: [description]
    """
    api_key = key.api_key
    api_secret = key.api_secret
    if models.UsingALgo.objects.exists():
        algo_name = models.UsingALgo.objects.first().algo.algo
        dic = {"AUTOTRADE": True, "ALGO": "AUTOTRADING algo=" + algo_name}
    else:
        t1.alive = False
        dic = {"AUTOTRADE": False, "ALGO": "AUTOTRADIG OFF"}
    return dic
