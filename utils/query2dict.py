def get_data(query):
    """[summary] make variable of chart.graphs.drawgraph.Graph().CustomDraw(kwargs) from querydict. The querydict from index.html

    Args:
        query ([type]): [description] querydict like <QueryDict: {'csrfmiddlewaretoken': ['2aboKu6bYhaa5OiUS5cWLytPpUpEMFLLqsYlZAE3MWervMwfoQ3HP9RlRcjEl9Uj'], 'smaperiod1': ['26'], 'smaperiod2': ['52'], 'emaperiod1': ['7'], 'emaperiod2': ['14'], 'bbandN': ['20'], 'bbandk': ['2.0'], 'rsiperiod': ['14'], 'rsibuythread': ['30.0'], 'rsisellthread': ['70.0'], 'macdfastperiod': ['12'], 'macdslowperiod': ['26'], 'macdsignaleriod': ['9'], 'ichimokut': ['12'], 'ichimokuk': ['26'], 'ichimokus': ['52']}>
    """
    kwargs = {}
    kwargs["Sma"] = {"params": (int(query["smaperiod1"]), int(query["smaperiod2"]))}
    kwargs["Ema"] = {"params": (int(query["emaperiod1"]), int(query["emaperiod2"]))}
    kwargs["Bb"] = {"params": (int(query["bbandN"]), float(query["bbandk"]))}
    kwargs["Rsi"] = {"params": (int(query["rsiperiod"]), float(query["rsibuythread"]), float(query["rsisellthread"]))}
    kwargs["Macd"] = {"params": (int(query["macdfastperiod"]), int(query["macdslowperiod"]), int(query["macdsignalperiod"]))}
    kwargs["Ichimoku"] = {"params": (int(query["ichimokut"]), int(query["ichimokuk"]), int(query["ichimokus"]))}
    return kwargs
