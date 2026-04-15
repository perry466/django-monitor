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
    get_tcp_retransmit_rate,
)


# =====================
# 动态获取目标
# =====================
def get_targets_for_category(category: str):
    """根据分类获取活跃监控目标"""
    return MonitorTarget.objects.filter(
        description=f"category:{category}",
        is_active=True
    ).order_by('name')


# =====================
# 定时任务
# =====================
def multi_ping_task():
    """每分钟执行一次多目标 Ping + 网络抖动采集"""
    print(f"[{timezone.now()}] 执行多目标 Ping + Jitter 任务...")

    targets_qs = get_targets_for_category('ping')
    if not targets_qs.exists():
        print("  ⚠️  'ping' 分类暂无目标，使用默认目标并自动保存")
        defaults = [
            {'address': '8.8.8.8', 'name': '8.8.8.8', 'type': 'ip'},
            {'address': '1.1.1.1', 'name': '1.1.1.1', 'type': 'ip'},
            {'address': 'baidu.com', 'name': 'baidu.com', 'type': 'domain'},
            {'address': '114.114.114.114', 'name': '114.114.114.114', 'type': 'ip'},
        ]
        for d in defaults:
            MonitorTarget.objects.update_or_create(
                address=d['address'],
                defaults={
                    'name': d['name'],
                    'target_type': d['type'],
                    'description': 'category:ping',
                    'is_active': True,
                }
            )
        targets_qs = get_targets_for_category('ping')

    for target_obj in targets_qs:
        address = target_obj.address
        raw_result = ping_host(address)
        ping_time, packet_loss = parse_ping_output(raw_result)
        jitter_data = measure_jitter(address, count=8)
        jitter_value = jitter_data.get('jitter_std') or 0.0

        MonitorResult.objects.create(
            target=target_obj,
            ping_time=ping_time,
            packet_loss=packet_loss,
            network_jitter=jitter_value,
            status='up' if ping_time is not None else 'down'
        )

        jitter_str = f"{jitter_value}ms" if jitter_value else "N/A"
        print(f"  → {target_obj.name} ({address}): {ping_time}ms, 丢包 {packet_loss}%, 抖动 {jitter_str}")

    print(f"[{timezone.now()}] 多目标 Ping + Jitter 任务完成")


def multi_http_task():
    """每分钟执行多目标 HTTP 响应时间"""
    print(f"[{timezone.now()}] 执行多目标 HTTP 响应时间任务...")

    targets_qs = get_targets_for_category('http')
    if not targets_qs.exists():
        print("  ⚠️  'http' 分类暂无目标，使用默认目标并自动保存")
        defaults = [
            {'address': 'https://www.google.com', 'name': 'Google', 'type': 'url'},
            {'address': 'https://www.baidu.com', 'name': 'Baidu', 'type': 'url'},
            {'address': 'https://www.cloudflare.com', 'name': 'Cloudflare', 'type': 'url'},
            {'address': 'https://github.com', 'name': 'GitHub', 'type': 'url'},
        ]
        for d in defaults:
            MonitorTarget.objects.update_or_create(
                address=d['address'],
                defaults={
                    'name': d['name'],
                    'target_type': d['type'],
                    'description': 'category:http',
                    'is_active': True,
                }
            )
        targets_qs = get_targets_for_category('http')

    for target_obj in targets_qs:
        result = http_check(target_obj.address)
        http_time = result.get('response_time') if result.get('success') else None
        status = 'up' if result.get('success') else 'down'

        MonitorResult.objects.create(
            target=target_obj,
            http_response_time=http_time,
            status=status
        )
        print(f"  → {target_obj.name} ({target_obj.address}): {http_time}ms, 状态: {status}")

    print(f"[{timezone.now()}] 多目标 HTTP 任务完成")


def multi_dns_task():
    """每分钟执行多目标 DNS 解析时间"""
    print(f"[{timezone.now()}] 执行多目标 DNS 解析时间任务...")

    targets_qs = get_targets_for_category('dns')
    if not targets_qs.exists():
        print("  ⚠️  'dns' 分类暂无目标，使用默认目标并自动保存")
        defaults = [
            {'address': 'google.com', 'name': 'Google', 'type': 'domain'},
            {'address': 'cloudflare.com', 'name': 'Cloudflare', 'type': 'domain'},
            {'address': 'baidu.com', 'name': 'Baidu', 'type': 'domain'},
            {'address': 'dns.quad9.net', 'name': 'Quad9', 'type': 'domain'},
            {'address': 'dns.aliyun.com', 'name': '阿里DNS', 'type': 'domain'},
        ]
        for d in defaults:
            MonitorTarget.objects.update_or_create(
                address=d['address'],
                defaults={
                    'name': d['name'],
                    'target_type': d['type'],
                    'description': 'category:dns',
                    'is_active': True,
                }
            )
        targets_qs = get_targets_for_category('dns')

    for target_obj in targets_qs:
        result = dns_resolve(target_obj.address)
        dns_time = result.get('resolve_time') if result.get('success') else None
        status = 'up' if result.get('success') else 'down'

        MonitorResult.objects.create(
            target=target_obj,
            dns_resolve_time=dns_time,
            status=status
        )
        print(f"  → {target_obj.name} ({target_obj.address}): {dns_time}ms, 状态: {status}")

    print(f"[{timezone.now()}] 多目标 DNS 任务完成")


def multi_tcp_retrans_task():
    """每分钟执行 TCP 重传率采集（系统级，无需配置）"""
    print(f"[{timezone.now()}] 执行 TCP 重传率采集任务...")
    target_obj, _ = MonitorTarget.objects.get_or_create(
        address='system_tcp',
        defaults={'name': 'TCP 重传率 (系统级)', 'target_type': 'ip', 'description': 'system'}
    )
    result = get_tcp_retransmit_rate()
    MonitorResult.objects.create(
        target=target_obj,
        tcp_retransmit_rate=result['retrans_rate'],
        status=result['status']
    )
    print(f"  → TCP 重传率: {result['retrans_rate']}%  状态: {result['status']}")


# =====================
# 启动调度器（已优化时区）
# =====================
def start_scheduler():
    """启动 APScheduler 并明确指定上海时区"""
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')  # ← 关键：确保定时任务使用正确时区

    scheduler.add_job(multi_ping_task, IntervalTrigger(minutes=1),
                      id='multi_ping_jitter', replace_existing=True)
    scheduler.add_job(multi_http_task, IntervalTrigger(minutes=1),
                      id='multi_http', replace_existing=True)
    scheduler.add_job(multi_dns_task, IntervalTrigger(minutes=1),
                      id='multi_dns', replace_existing=True)
    scheduler.add_job(multi_tcp_retrans_task, IntervalTrigger(minutes=1),
                      id='multi_tcp_retrans', replace_existing=True)

    scheduler.start()
    print("✅ APScheduler 已成功启动（时区：Asia/Shanghai）")
    print("   - 每分钟执行：Ping + Jitter、HTTP、DNS、TCP重传率")