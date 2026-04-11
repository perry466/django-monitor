"""
ASGI config for djangoproject project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoproject.settings')

application = get_asgi_application()

# ====================== 启动定时任务（加强版） ======================
print("正在尝试启动 APScheduler 定时任务...")

try:
    from monitor.tasks import start_scheduler
    start_scheduler()
    print("✅ APScheduler 已成功启动 - 每分钟执行一次多目标 Ping")
except Exception as e:
    print(f"❌ 启动定时任务失败: {e}")
    import traceback
    traceback.print_exc()