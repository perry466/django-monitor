from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from .models import MonitorTarget, MonitorResult
from .monitoring import ping_host
import re

TARGET_ADDRESSES = ['8.8.8.8', '1.1.1.1', 'baidu.com', '114.114.114.114']


def parse_ping_output(output):
    """增强版解析（适配 Windows + Linux）"""
    try:
        if not output or "Error" in output or "Timeout" in output:
            return None, 0.0

        # 丢包率
        loss_match = re.search(r'(\d+)%\s*(?:loss|丢失|packet loss)', output, re.IGNORECASE)
        if not loss_match:
            loss_match = re.search(r'lost\s*=\s*(\d+)', output, re.IGNORECASE)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        # 延迟
        ping_time = None
        match = re.search(r'average\s*=\s*(\d+)', output, re.IGNORECASE)
        if match:
            ping_time = float(match.group(1))
        if not ping_time:
            match = re.search(r'avg\s*=\s*([\d.]+)', output, re.IGNORECASE)
            if match:
                ping_time = float(match.group(1))
        if not ping_time:
            match = re.search(r'time[=<]\s*(\d+)', output, re.IGNORECASE)
            if match:
                ping_time = float(match.group(1))
        if not ping_time:
            match = re.search(r'(\d+)\s*ms', output)
            if match:
                ping_time = float(match.group(1))

        return ping_time, packet_loss
    except:
        return None, 0.0


def multi_ping_task():
    """每分钟执行一次多目标 Ping"""
    print(f"[{timezone.now()}] 执行多目标 Ping 任务...")

    for address in TARGET_ADDRESSES:
        # 确保目标存在
        target_obj, _ = MonitorTarget.objects.get_or_create(
            address=address,
            defaults={'name': address, 'target_type': 'ip' if re.match(r'^\d', address) else 'domain'}
        )

        # 执行 Ping
        raw_result = ping_host(address)
        ping_time, packet_loss = parse_ping_output(raw_result)

        # 保存结果
        MonitorResult.objects.create(
            target=target_obj,
            ping_time=ping_time,
            packet_loss=packet_loss,
            status='up' if ping_time is not None else 'down'
        )

        print(f"  → {address}: {ping_time}ms, 丢包 {packet_loss}%")

    print(f"[{timezone.now()}] 多目标 Ping 任务完成")


# =====================
# 启动调度器函数（必须有这个！）
# =====================
def start_scheduler():
    """在项目启动时调用，启动后台定时任务"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        multi_ping_task,
        IntervalTrigger(minutes=1),
        id='multi_ping',
        replace_existing=True
    )
    scheduler.start()
    print("APScheduler 已启动 - 每分钟执行一次多目标 Ping")