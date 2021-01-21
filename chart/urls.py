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
    path("optimize", views.optimize, name="optimize"),
    path("optimize/<str:duration>/", views.optimize, name="optimize_d"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
