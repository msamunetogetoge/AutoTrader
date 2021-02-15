from chart import models
import logging

logger = logging.getLogger(__name__)


def change_productcode():
    codes = ["BTC_JPY", "ETH_JPY"]
    if models.UsingProductCode.objects.exists():
        using_code = models.UsingProductCode.objects.last().code
        print(using_code)
        models.UsingProductCode.objects.all().delete()
        codes.remove(using_code)
        code = codes[0]
        models.UsingProductCode(code=code).save()
    else:
        models.UsingProductCode(code=codes[0]).save()
    code = models.UsingProductCode.objects.last()
    logger.info(f"Now, using product-code is {code}")
