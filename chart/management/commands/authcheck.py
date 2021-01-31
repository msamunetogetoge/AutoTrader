import pybitflyer

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    print("key.py に情報を書き込みます。")

    api = input("api_keyを入力してください")
    secret = input("api_secretを入力してください")
    with open("key.py", "w") as key:
        key.write(f"api_key='{api}' \n")
        key.write(f"api_secret='{secret}' ")
    print("書き込みました。")
    bitflyerapi = pybitflyer.API(api, secret)
    balances = bitflyerapi.getbalance()[0]
    if "amount" in balances.keys():
        print("権限が与えられたapikeyです。")
    else:
        print("apikeyに権限がないようです。権限を確認してください。")
