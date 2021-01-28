from django.core.management.base import BaseCommand
from chart.models import *


class Command(BaseCommand):
    """[summary]add objects to chart.models.AlgoList. If create new algo, make functions in chart.ai.Recognize, chart.ai.BackTest, chart.ai.Optimize

    Args:
        BaseCommand ([type]):
    """

    def handle(self, *args, **options):
        algolists = {"algo": ["Follow", "Bb", "DEma", "Ema", "Sma"],
                     "detail": ["現在の足の終値が前の足の終値を下回って、現在の保有ポジションの総損益が損失になったときは売る。",
                                "ボリンジャーバンドを使うアルゴリズム。終値が上限を下に超え、分散の計算に使うデータ数n/2個の終値の中で最大なら買う。売りはその逆",
                                "DEMAを使うアルゴリズム。ゴールデンクロスかつ、短期の平均線が終値を超えた時に買う。売る時は、デッドクロスが起こるか、一期前の終値が、買値か直近の終値を下回ったら売る。",
                                "EMAを使うアルゴリズム。ゴールデンクロスかつ、短期の平均線が終値を超えた時に買う。売る時は、デッドクロスが起こるか、一期前の終値が、買値か直近の終値を下回ったら売る。",
                                "SMAを使うアルゴリズム。ゴールデンクロスかつ、短期の平均線が終値を超えた時に買う。売る時は、デッドクロスが起こるか、一期前の終値が、買値か直近の終値を下回ったら売る。"
                                ]}

        for i in range(len(algolists["algo"])):
            algolist = AlgoList()
            algolist.algo = algolists["algo"][i]
            algolist.detail = algolists["detail"][i]
            algolist.save()
        print(AlgoList.objects.first())
