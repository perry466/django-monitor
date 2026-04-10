from django.urls import path
from . import views

app_name = 'monitor'

urlpatterns = [
    path('', views.index, name='index'),  # 首页
    path('latency/', views.latency, name='latency'),  # 延迟测试
    path('ping/', views.ping, name='ping'),
    path('http/', views.http, name='http'),
    path('jitter/', views.jitter, name='jitter'),
    path('dns/', views.dns, name='dns'),
    path('tcp/', views.tcp, name='tcp'),
]
