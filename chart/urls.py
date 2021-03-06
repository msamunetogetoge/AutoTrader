import os
from pathlib import Path

from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:duration>/", views.index, name="index_d"),
    path("backtest", views.backtest, name="backtest"),
    path("backtest/<str:indicator>/", views.backtest, name="backtest_b"),
    path("signalevents", views.SignalEventsView.as_view(), name="signalevents"),
    path("trade", views.Trade, name="trade"),
    path("trade/<str:duration>/", views.Trade, name="trade_d"),
    path("autotrade", views.AutoTrade, name="autotrade"),
    path("change", views.Change, name="change"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
