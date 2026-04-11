# django-monitor-main/monitor/urls.py
from django.urls import path
from . import api
from . import views

urlpatterns = [
    # 页面路由
    path('ping/', views.ping, name='ping'),
    path('loss/', views.loss, name='loss'),
    path('http-response/', views.http_response, name='http_response'),   # ← HTTP页面

    # API路由
    path('api/ping/', api.ping_api),
    path('api/multi-ping/', api.multi_ping_api),
    path('api/tcp/', api.tcp_api),
    path('api/http/', api.http_api),                    # ← 单个HTTP检测
    path('api/multi-http/', api.multi_http_api),        # ← 多目标HTTP（图表用）
    path('api/dns/', api.dns_api),
    path('api/full/', api.full_check_api),
    path('api/system/', api.system_api),
]