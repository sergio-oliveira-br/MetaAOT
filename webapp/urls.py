# webapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('health', views.health, name='health'),
    path('sleep60', views.sleep60, name='sleep60'),
]
