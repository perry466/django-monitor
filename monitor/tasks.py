# django-monitor-main/monitor/tasks.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from .models import MonitorTarget, MonitorResult
from .monitoring import ping_host, http_check, parse_ping_output   # ← 现在可以正确导入

import re

# Ping 目标
TARGET_ADDRESSES = ['8.8.8.8', '1.1.1.1', 'baidu.com', '114.114.114.114']

# HTTP 响应时间监控目标
HTTP_TARGETS = [
    {'name': 'Google', 'url': 'https://www.google.com'},
    {'name': 'Baidu', 'url': 'https://www.baidu.com'},
    {'name': 'Cloudflare', 'url': 'https://www.cloudflare.com'},
    {'name': 'GitHub', 'url': 'https://github.com'},
]


def multi_ping_task():
    """每分钟执行一次多目标 Ping"""
    print(f"[{timezone.now()}] 执行多目标 Ping 任务...")

    for address in TARGET_ADDRESSES:
        target_obj, _ = MonitorTarget.objects.get_or_create(
            address=address,
            defaults={'name': address, 'target_type': 'ip' if re.match(r'^\d', address) else 'domain'}
        )

        raw_result = ping_host(address)
        ping_time, packet_loss = parse_ping_output(raw_result)

        MonitorResult.objects.create(
            target=target_obj,
            ping_time=ping_time,
            packet_loss=packet_loss,
            status='up' if ping_time is not None else 'down'
        )

        print(f"  → {address}: {ping_time}ms, 丢包 {packet_loss}%")

    print(f"[{timezone.now()}] 多目标 Ping 任务完成")


def multi_http_task():
    """每分钟执行一次多目标 HTTP 响应时间检查"""
    print(f"[{timezone.now()}] 执行多目标 HTTP 响应时间任务...")

    for target in HTTP_TARGETS:
        target_obj, _ = MonitorTarget.objects.get_or_create(
            address=target['url'],
            defaults={'name': target['name'], 'target_type': 'url'}
        )

        result = http_check(target['url'])
        http_time = result.get('response_time') if result.get('success') else None
        status = 'up' if result.get('success') else 'down'

        MonitorResult.objects.create(
            target=target_obj,
            http_response_time=http_time,
            status=status
        )

        print(f"  → {target['name']} ({target['url']}): {http_time}ms, 状态: {status}")

    print(f"[{timezone.now()}] 多目标 HTTP 任务完成")


# =====================
# 启动调度器
# =====================
def start_scheduler():
    """启动后台定时任务（Ping + HTTP）"""
    scheduler = BackgroundScheduler(timezone='Asia/Singapore')  # 推荐使用新加坡时区
    scheduler.add_job(
        multi_ping_task,
        IntervalTrigger(minutes=1),
        id='multi_ping',
        replace_existing=True
    )
    scheduler.add_job(
        multi_http_task,
        IntervalTrigger(minutes=1),
        id='multi_http',
        replace_existing=True
    )
    scheduler.start()
    print("✅ APScheduler 已启动 - Ping + HTTP 每分钟执行一次")