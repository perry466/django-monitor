# django-monitor-main/logs/admin.py
from django.contrib import admin
from .models import MonitorLog, AIConfig


@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ['provider', 'model_name', 'is_active']
    list_editable = ['is_active']


admin.site.register(MonitorLog)