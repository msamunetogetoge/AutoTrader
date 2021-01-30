from django.http import HttpRequest
from chart import models


def isAutoTrade(request: HttpRequest):
    """[summary] AutoTrade がONかOFFか判定する辞書autotrade.html からのpostの中身によって、

    Args:
        request (HttpRequest): [description]

    Returns:
        [type]dict: [description]
    """

    if models.UsingALgo.objects.exists():
        algo_name = models.UsingALgo.objects.first().algo.algo

        dic = {"AUTOTRADE": True, "ALGO": f"AUTOTRADING algo= {algo_name}"}
    else:

        dic = {"AUTOTRADE": False, "ALGO": "AUTOTRADIG OFF"}
    return dic
