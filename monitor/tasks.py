# django-monitor-main/monitor/tasks.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from .models import MonitorTarget, MonitorResult
from .monitoring import (
    ping_host,
    http_check,
    parse_ping_output,
    measure_jitter,
    dns_resolve,
    get_tcp_retransmit_rate,   # 新增导入
)

import re

# Ping 目标（同时用于抖动采集）
TARGET_ADDRESSES = ['8.8.8.8', '1.1.1.1', 'baidu.com', '114.114.114.114']

# HTTP 响应时间监控目标
HTTP_TARGETS = [
    {'name': 'Google', 'url': 'https://www.google.com'},
    {'name': 'Baidu', 'url': 'https://www.baidu.com'},
    {'name': 'Cloudflare', 'url': 'https://www.cloudflare.com'},
    {'name': 'GitHub', 'url': 'https://github.com'},
]

DNS_TARGETS = [
    {'name': 'Google', 'domain': 'google.com'},
    {'name': 'Cloudflare', 'domain': 'cloudflare.com'},
    {'name': 'Baidu', 'domain': 'baidu.com'},
    {'name': 'Quad9', 'domain': 'dns.quad9.net'},
    {'name': '阿里DNS', 'domain': 'dns.aliyun.com'},
]

def multi_ping_task():
    """每分钟执行一次多目标 Ping + 网络抖动采集"""
    print(f"[{timezone.now()}] 执行多目标 Ping + Jitter 任务...")

    for address in TARGET_ADDRESSES:
        # 获取或创建监控目标
        target_obj, created = MonitorTarget.objects.get_or_create(
            address=address,
            defaults={
                'name': address,
                'target_type': 'ip' if re.match(r'^\d', address) else 'domain'
            }
        )

        # 基础 Ping 测试
        raw_result = ping_host(address)
        ping_time, packet_loss = parse_ping_output(raw_result)

        # 新增：网络抖动测量（执行8次ping取抖动）
        jitter_data = measure_jitter(address, count=8)

        # 保存到数据库（使用 jitter_std 作为主要抖动值）
        jitter_value = jitter_data.get('jitter_std') or jitter_data.get('jitter_range')

        MonitorResult.objects.create(
            target=target_obj,
            ping_time=ping_time,
            packet_loss=packet_loss,
            network_jitter=jitter_value,  # ← 关键：保存抖动数据
            status='up' if ping_time is not None else 'down'
        )

        # 控制台输出
        jitter_str = f"{jitter_value}ms" if jitter_value is not None else "N/A"
        print(f"  → {address}: {ping_time}ms, 丢包 {packet_loss}%, 抖动 {jitter_str}")

    print(f"[{timezone.now()}] 多目标 Ping + Jitter 任务完成")


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


def multi_dns_task():
    """每分钟执行一次多目标 DNS 解析时间采集"""
    print(f"[{timezone.now()}] 执行多目标 DNS 解析时间任务...")

    for target in DNS_TARGETS:
        target_obj, _ = MonitorTarget.objects.get_or_create(
            address=target['domain'],
            defaults={'name': target['name'], 'target_type': 'domain'}
        )

        result = dns_resolve(target['domain'])   # ← 现在能正常调用了
        dns_time = result.get('resolve_time') if result.get('success') else None
        status = 'up' if result.get('success') else 'down'

        MonitorResult.objects.create(
            target=target_obj,
            dns_resolve_time=dns_time,
            status=status
        )

        print(f"  → {target['name']} ({target['domain']}): {dns_time}ms, 状态: {status}")

    print(f"[{timezone.now()}] 多目标 DNS 任务完成")


def multi_tcp_retrans_task():
    """每分钟执行 TCP 重传率采集"""
    print(f"[{timezone.now()}] 执行 TCP 重传率采集任务...")

    # 使用系统级目标（或复用现有 MonitorTarget）
    target_obj, _ = MonitorTarget.objects.get_or_create(
        address='system_tcp',
        defaults={'name': 'TCP 重传率 (系统级)', 'target_type': 'ip'}
    )

    result = get_tcp_retransmit_rate()

    MonitorResult.objects.create(
        target=target_obj,
        tcp_retransmit_rate=result['retrans_rate'],
        status=result['status']
    )

    print(f"  → TCP 重传率: {result['retrans_rate']}%  状态: {result['status']}")


# =====================
# 启动调度器
# =====================
def start_scheduler():
    """启动后台定时任务（Ping + Jitter + HTTP + DNS）"""
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')  # 改成上海时区（新加坡/中国用户更合适）

    scheduler.add_job(
        multi_ping_task,
        IntervalTrigger(minutes=1),
        id='multi_ping_jitter',
        replace_existing=True
    )
    scheduler.add_job(
        multi_http_task,
        IntervalTrigger(minutes=1),
        id='multi_http',
        replace_existing=True
    )
    scheduler.add_job(
        multi_dns_task,
        IntervalTrigger(minutes=1),
        id='multi_dns',
        replace_existing=True
    )

    scheduler.add_job(
        multi_tcp_retrans_task,
        IntervalTrigger(minutes=1),
        id='multi_tcp_retrans',
        replace_existing=True
    )

    scheduler.start()
    print("✅ APScheduler 已成功启动 - Ping + Jitter + HTTP + DNS + TCP 每分钟执行一次")