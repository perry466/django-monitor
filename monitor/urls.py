from django.urls import path
from . import api
from . import views

urlpatterns = [
    # 页面
    path('ping/', views.ping),

    # API
    path('api/ping/', api.ping_api),
    path('api/tcp/', api.tcp_api),
    path('api/http/', api.http_api),
    path('api/dns/', api.dns_api),
    path('api/full/', api.full_check_api),
    path('api/system/', api.system_api),
]