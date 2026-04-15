# django-monitor-main/logs/urls.py
from django.urls import path
from . import views
from .views import (
    ai_generate_report,
    save_ai_config,
    system_logs,
    get_system_logs,
    ai_analyze_logs,
    get_recent_ai_reports,
    download_logs

)
app_name = 'logs'

urlpatterns = [
    path('api/ai-report/', ai_generate_report, name='ai_generate_report'),
    path('api/ai-analyze-logs/', ai_analyze_logs, name='ai_analyze_logs'),

    path('api/save-ai-config/', save_ai_config, name='save_ai_config'),

    # 系统日志
    path('system-logs/', system_logs, name='system_logs'),
    path('api/system-logs/', get_system_logs, name='get_system_logs'),
    path('api/recent-ai-reports/',get_recent_ai_reports, name='recent_ai_reports'),
    path('download/',views.download_logs, name='download_logs'),
]