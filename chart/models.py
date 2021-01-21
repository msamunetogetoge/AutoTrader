from django.db import models
from django.forms import ModelForm
# Create your models here.


class SignalEvents(models.Model):
    time = models.DateTimeField(null=False)
    product_code = models.CharField(default="BTC_JPY", max_length=15)
    side = models.CharField(max_length=10)
    price = models.FloatField()
    size = models.FloatField()

    def __str__(self):
        return f"{self.time}:{self.product_code}:{self.side}:price={self.price},size={self.size}"


class Candle_1s(models.Model):
    time = models.DateTimeField(primary_key=True)
    product_code = models.CharField(default="BTC_JPY", max_length=15)
    open = models.FloatField()
    close = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    volume = models.FloatField()

    def __str__(self):
        return f"duration=s,{self.time} {self.product_code} open={self.open} close={self.close} volume={self.volume}"


class Candle_1m(models.Model):
    time = models.DateTimeField(primary_key=True)
    product_code = models.CharField(default="BTC_JPY", max_length=15)
    open = models.FloatField()
    close = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    volume = models.FloatField()

    def __str__(self):
        return f"duration=m,{self.time} {self.product_code} open={self.open} close={self.close} volume={self.volume}"


class Candle_1h(models.Model):
    time = models.DateTimeField(primary_key=True)
    product_code = models.CharField(default="BTC_JPY", max_length=15)
    open = models.FloatField()
    close = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    volume = models.FloatField()

    def __str__(self):
        return f"duration=h,{self.time} {self.product_code} open={self.open} close={self.close} volume={self.volume}"


class SmaParams(models.Model):
    name = models.CharField(max_length=10, default="Sma")
    smaperiod1 = models.IntegerField(default=26)
    smaperiod2 = models.IntegerField(default=52)


class EmaParams(models.Model):
    name = models.CharField(max_length=10, default="Ema")
    emaperiod1 = models.IntegerField(default=7)
    emaperiod2 = models.IntegerField(default=14)


class BbParams(models.Model):
    name = models.CharField(max_length=10, default="Bb")
    bbandN = models.IntegerField(default=20)
    bbandk = models.FloatField(default=2.0)


class RsiParams(models.Model):
    name = models.CharField(max_length=10, default="Rsi")
    rsiperiod = models.IntegerField(default=14)
    rsibuythread = models.FloatField(default=30.0)
    rsisellthread = models.FloatField(default=70.0)


class MacdParams(models.Model):
    name = models.CharField(max_length=10, default="Macd")
    macdfastperiod = models.IntegerField(default=12)
    macdslowperiod = models.IntegerField(default=26)
    macdsignalperiod = models.IntegerField(default=9)


class IchimokuParams(models.Model):
    name = models.CharField(max_length=10, default="Ichimoku")
    ichimokut = models.IntegerField(default=12)
    ichimokuk = models.IntegerField(default=26)
    ichimokus = models.IntegerField(default=52)


class SmaForm(ModelForm):
    class Meta:
        model = SmaParams
        exclude = ['name']


class EmaForm(ModelForm):
    class Meta:
        model = EmaParams
        exclude = ['name']


class BbForm(ModelForm):
    class Meta:
        model = BbParams
        exclude = ['name']


class MacdForm(ModelForm):
    class Meta:
        model = MacdParams
        exclude = ['name']


class IchimokuForm(ModelForm):
    class Meta:
        model = IchimokuParams
        exclude = ['name']


class RsiForm(ModelForm):
    class Meta:
        model = RsiParams
        exclude = ['name']
