from django.urls import path
from . import views

app_name = 'targets'

urlpatterns = [
    path('', views.index, name='index'),
    path('check/', views.check_targets, name='check_targets'),
]
