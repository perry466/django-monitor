from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from .models import MonitorTarget, MonitorResult
from .monitoring import ping_host
import re

TARGET_ADDRESSES = ['8.8.8.8', '1.1.1.1', 'baidu.com', '114.114.114.114']

def parse_ping_output(output):
    """简单解析 ping 输出，提取延迟和丢包率"""
    try:
        # 丢包率
        loss_match = re.search(r'(\d+)%', output)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        # 平均延迟（rtt avg）
        avg_match = re.search(r'avg = ([\d.]+)', output)
        if not avg_match:
            avg_match = re.search(r'time=([\d.]+)', output)  # Windows
        ping_time = float(avg_match.group(1)) if avg_match else None

        return ping_time, packet_loss
    except:
        return None, 0.0

def multi_ping_task():
    """每分钟执行一次：对4个目标进行Ping并保存结果"""
    print(f"[{timezone.now()}] 执行多目标 Ping 任务...")

    for address in TARGET_ADDRESSES:
        # 确保目标存在于 MonitorTarget 中
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

    print(f"[{timezone.now()}] 多目标 Ping 任务完成")

# 启动调度器（在项目启动时调用）
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(multi_ping_task, IntervalTrigger(minutes=1), id='multi_ping', replace_existing=True)
    scheduler.start()
    print("APScheduler 已启动 - 每分钟执行一次多目标 Ping")