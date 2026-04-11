from django.http import JsonResponse
from django.utils import timezone
from monitor.models import MonitorResult,MonitorTarget
from .monitoring import (
    ping_host,
    tcp_check,
    http_check,
    dns_resolve,
    system_info
)


# =====================
# 统一返回格式
# =====================
def success(data=None):
    return JsonResponse({
        'code': 0,
        'msg': 'success',
        'data': data
    })


def error(msg='error'):
    return JsonResponse({
        'code': 1,
        'msg': msg,
        'data': None
    })


# =====================
# 1. Ping检测
# =====================
def ping_api(request):
    target = request.GET.get('target')

    if not target:
        return error('target is required')

    result = ping_host(target)

    return success({
        'type': 'ping',
        'target': target,
        'result': result
    })

# =====================
# 6. 多目标 Ping 监控 API（供图表使用）
# =====================
from django.utils import timezone
from monitor.models import MonitorResult   # 确保导入正确

TARGETS = [
    {'name': '8.8.8.8', 'address': '8.8.8.8'},
    {'name': '1.1.1.1', 'address': '1.1.1.1'},
    {'name': 'baidu.com', 'address': 'baidu.com'},
    {'name': '114.114.114.114', 'address': '114.114.114.114'},
]

def multi_ping_api(request):
    """返回4个目标的最新状态 + 每个目标最近20条历史数据（用于趋势图）"""
    try:
        results = []
        history_data = {
            'labels': [],
            'datasets': []
        }

        colors = ['#22d3ee', '#a855f7', '#f472b6', '#fb923c']

        for idx, target in enumerate(TARGETS):
            # 1. 获取最新一条记录（用于卡片）
            latest = MonitorResult.objects.filter(
                target__address=target['address']
            ).order_by('-timestamp').first()

            if latest:
                ping_time = latest.ping_time or 0
                packet_loss = latest.packet_loss or 0
                timestamp = latest.timestamp.strftime('%H:%M:%S')
            else:
                ping_time = 0
                packet_loss = 0
                timestamp = '无数据'

            results.append({
                'target': target['name'],
                'ping_time': round(ping_time, 1),
                'packet_loss': round(packet_loss, 1),
                'timestamp': timestamp
            })

            # 2. 获取最近20条历史记录（用于折线图）
            history = MonitorResult.objects.filter(
                target__address=target['address']
            ).order_by('-timestamp')[:20]

            # 时间标签（倒序转正序）
            time_labels = [h.timestamp.strftime('%H:%M') for h in reversed(history)]
            latency_values = [h.ping_time or 0 for h in reversed(history)]

            # 如果不足20条，用0补齐
            while len(time_labels) < 20:
                time_labels.insert(0, f"历史-{20-len(time_labels)}")
                latency_values.insert(0, 0)

            history_data['datasets'].append({
                'label': target['name'],
                'data': latency_values,
                'borderColor': colors[idx],
                'backgroundColor': 'transparent',
                'borderWidth': 3,
                'tension': 0.4,
                'pointRadius': 2,
                'pointHoverRadius': 5
            })

        # 统一的时间标签（取第一个目标的标签作为X轴）
        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in TARGETS],
            'results': results,           # 用于卡片显示
            'history': history_data       # 用于趋势图
        })

    except Exception as e:
        return error(f'获取多目标数据失败: {str(e)}')


# =====================
# 2. TCP端口检测
# =====================
def tcp_api(request):
    target = request.GET.get('target')
    port = request.GET.get('port')

    if not target or not port:
        return error('target and port are required')

    try:
        port = int(port)
    except:
        return error('invalid port')

    result = tcp_check(target, port)

    return success({
        'type': 'tcp',
        'target': target,
        'port': port,
        'result': result
    })


# =====================
# 3. HTTP检测
# =====================
def http_api(request):
    url = request.GET.get('url')

    if not url:
        return error('url is required')

    result = http_check(url)

    return success({
        'type': 'http',
        'url': url,
        'result': result
    })


# =====================
# 4. DNS解析
# =====================
def dns_api(request):
    domain = request.GET.get('domain')

    if not domain:
        return error('domain is required')

    result = dns_resolve(domain)

    return success({
        'type': 'dns',
        'domain': domain,
        'result': result
    })


# =====================
# 5. 综合检测（企业常用）
# =====================
def full_check_api(request):
    target = request.GET.get('target')

    if not target:
        return error('target is required')

    data = {
        'ping': ping_host(target),
        'tcp_80': tcp_check(target, 80),
        'tcp_443': tcp_check(target, 443),
    }

    return success({
        'type': 'full_check',
        'target': target,
        'result': data
    })


# =====================
# 5. 首页仪表盘（内存/磁盘/带宽）
# =====================

def system_api(request):
    data = system_info()
    return success(data)