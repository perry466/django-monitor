from django.contrib import admin
from .models import AIConfig, MonitorTarget, MonitorResult


@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ['provider', 'model_name', 'is_active']
    list_editable = ['is_active']

    fieldsets = [
        ('基本配置', {
            'fields': ['provider', 'model_name', 'api_key']
        }),
        ('高级选项', {
            'fields': ['base_url', 'temperature', 'max_tokens'],
            'classes': ('collapse',),
        }),
    ]


# 注册其他模型
admin.site.register(MonitorTarget)
admin.site.register(MonitorResult)