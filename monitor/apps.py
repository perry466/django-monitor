from django.apps import AppConfig


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'

    def ready(self):
        # 防止在开发服务器重载时重复启动调度器
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        from .tasks import start_scheduler
        start_scheduler()