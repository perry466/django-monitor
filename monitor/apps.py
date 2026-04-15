# django-monitor-main/monitor/apps.py
from django.apps import AppConfig
import os


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'

    def ready(self):
        # 防止在开发服务器重载时重复启动调度器
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        try:
            from .tasks import start_scheduler
            start_scheduler()
            print("✅ APScheduler 定时任务已在 MonitorConfig.ready() 中成功启动")
            print("   - 时区：Asia/Shanghai")
            print("   - 每分钟执行：Ping + Jitter、HTTP、DNS、TCP重传率")
        except Exception as e:
            print(f"❌ APScheduler 启动失败: {e}")
            import traceback
            traceback.print_exc()