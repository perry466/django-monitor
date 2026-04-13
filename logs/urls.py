# django-monitor-main/logs/urls.py
from django.urls import path
from .views import ai_generate_report, save_ai_config

app_name = 'logs'

urlpatterns = [
    path('api/ai-report/', ai_generate_report, name='ai_generate_report'),
    path('api/save-ai-config/', save_ai_config, name='save_ai_config'),
]