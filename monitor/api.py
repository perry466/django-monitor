# django-monitor-main/monitor/api.py
from django.http import JsonResponse
from django.utils import timezone
from monitor.models import MonitorResult, MonitorTarget
from .monitoring import (
    ping_host,
    tcp_check,
    http_check,
    dns_resolve,
    system_info,
    parse_ping_output   # 新增
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
# 1. Ping检测（单个）
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
# 2. 多目标 Ping API（修复重点！）
# =====================
PING_TARGETS = [
    {'name': '8.8.8.8', 'address': '8.8.8.8'},
    {'name': '1.1.1.1', 'address': '1.1.1.1'},
    {'name': 'baidu.com', 'address': 'baidu.com'},
    {'name': '114.114.114.114', 'address': '114.114.114.114'},
]

def multi_ping_api(request):
    """返回4个Ping目标的最新状态 + 最近20条历史数据（用于趋势图）"""
    try:
        results = []
        history_data = {
            'labels': [],
            'datasets': []
        }
        colors = ['#22d3ee', '#a855f7', '#f472b6', '#fb923c']

        for idx, target in enumerate(PING_TARGETS):
            # 最新一条记录
            latest = MonitorResult.objects.filter(
                target__address=target['address']
            ).order_by('-timestamp').first()

            ping_time = round(latest.ping_time, 1) if latest and latest.ping_time is not None else 0
            packet_loss = round(latest.packet_loss, 1) if latest and latest.packet_loss is not None else 0
            timestamp = latest.timestamp.strftime('%H:%M:%S') if latest else '无数据'

            results.append({
                'target': target['name'],
                'ping_time': ping_time,
                'packet_loss': packet_loss,
                'timestamp': timestamp
            })

            # 最近20条历史记录
            history = MonitorResult.objects.filter(
                target__address=target['address']
            ).order_by('-timestamp')[:20]

            time_labels = [h.timestamp.strftime('%H:%M') for h in reversed(history)]
            latency_values = [h.ping_time or 0 for h in reversed(history)]

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

        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in PING_TARGETS],
            'results': results,
            'history': history_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(f'获取多目标Ping数据失败: {str(e)}')


# =====================
# 3. TCP端口检测
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
# 4. HTTP响应时间检测（单个）
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
# 5. 多目标 HTTP 响应时间 API
# =====================
HTTP_TARGETS = [
    {'name': 'Google', 'url': 'https://www.google.com'},
    {'name': 'Baidu', 'url': 'https://www.baidu.com'},
    {'name': 'Cloudflare', 'url': 'https://www.cloudflare.com'},
    {'name': 'GitHub', 'url': 'https://github.com'},
]

def multi_http_api(request):
    """多目标 HTTP 响应时间"""
    try:
        results = []
        history_data = {'labels': [], 'datasets': []}
        colors = ['#f97316', '#8b5cf6', '#ec4899', '#14b8a6']

        for idx, target in enumerate(HTTP_TARGETS):
            latest = MonitorResult.objects.filter(
                target__address=target['url']
            ).order_by('-timestamp').first()

            http_time = round(latest.http_response_time, 1) if latest and latest.http_response_time is not None else 0
            timestamp = latest.timestamp.strftime('%H:%M:%S') if latest else '无数据'

            results.append({
                'target': target['name'],
                'url': target['url'],
                'response_time': http_time,
                'timestamp': timestamp
            })

            history = MonitorResult.objects.filter(
                target__address=target['url']
            ).order_by('-timestamp')[:20]

            time_labels = [h.timestamp.strftime('%H:%M') for h in reversed(history)]
            response_values = [h.http_response_time or 0 for h in reversed(history)]

            while len(time_labels) < 20:
                time_labels.insert(0, f"历史-{20 - len(time_labels)}")
                response_values.insert(0, 0)

            history_data['datasets'].append({
                'label': target['name'],
                'data': response_values,
                'borderColor': colors[idx],
                'backgroundColor': 'transparent',
                'borderWidth': 3,
                'tension': 0.4,
                'pointRadius': 2,
            })

        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in HTTP_TARGETS],
            'results': results,
            'history': history_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(f'获取多目标HTTP数据失败: {str(e)}')


# =====================
# 6. DNS + 综合 + 系统信息
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


def system_api(request):
    data = system_info()
    return success(data)