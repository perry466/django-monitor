# django-monitor-main/monitor/urls.py
from django.urls import path
from . import api
from . import views
from .views import ai_generate_report,save_ai_config

urlpatterns = [
    # ==================== 页面路由 ====================
    path('ping/', views.ping, name='ping'),
    path('loss/', views.loss, name='loss'),
    path('http-response/', views.http_response, name='http_response'),
    path('jitter/', views.jitter, name='jitter'),
    path('dns/', views.dns, name='dns'),
    path('tcp-retrans/', views.tcp_retrans, name='tcp_retrans'),  # ← TCP重传率页面

    # ==================== API路由 ====================
    path('api/ping/', api.ping_api),
    path('api/multi-ping/', api.multi_ping_api),
    path('api/tcp/', api.tcp_api),
    path('api/http/', api.http_api),
    path('api/multi-http/', api.multi_http_api),
    path('api/multi-jitter/', api.multi_jitter_api, name='multi_jitter'),
    path('api/multi-loss/', api.multi_loss_api, name='multi_loss_api'),
    path('api/multi-dns/', api.multi_dns_api, name='multi_dns'),
    path('api/ai-report/',ai_generate_report, name='ai_generate_report'),
    path('api/save-ai-config/', save_ai_config, name='save_ai_config'),
    # ←←← 关键：TCP 重传率 API（必须这样写） ←←←
    path('api/multi-tcp-retrans/', api.multi_tcp_retrans_api, name='multi_tcp_retrans'),

    path('api/full/', api.full_check_api),
    path('api/system/', api.system_api),
]