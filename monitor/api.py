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
    parse_ping_output
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
# 2. 多目标 Ping API（按 id 排序）
# =====================
def multi_ping_api(request):
    try:
        targets_qs = MonitorTarget.objects.filter(
            description="category:ping", is_active=True
        ).order_by('id')          # ← 关键修改

        if not targets_qs.exists():
            defaults = [
                {'name': '8.8.8.8', 'address': '8.8.8.8'},
                {'name': '1.1.1.1', 'address': '1.1.1.1'},
                {'name': 'baidu.com', 'address': 'baidu.com'},
                {'name': '114.114.114.114', 'address': '114.114.114.114'},
            ]
            for d in defaults:
                MonitorTarget.objects.update_or_create(
                    address=d['address'],
                    defaults={'name': d['name'], 'target_type': 'ip' if d['address'][0].isdigit() else 'domain', 'description': 'category:ping'}
                )
            targets_qs = MonitorTarget.objects.filter(description="category:ping", is_active=True).order_by('id')

        targets_list = [{'name': t.name, 'address': t.address} for t in targets_qs]

        results = []
        history_data = {'labels': [], 'datasets': []}
        colors = ['#22d3ee', '#a855f7', '#f472b6', '#fb923c']

        for idx, target in enumerate(targets_list):
            latest = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp').first()
            ping_time = round(latest.ping_time, 1) if latest and latest.ping_time is not None else 0
            packet_loss = round(latest.packet_loss, 1) if latest and latest.packet_loss is not None else 0
            timestamp = timezone.localtime(latest.timestamp).strftime('%H:%M:%S') if latest else '无数据'

            results.append({
                'target': target['name'],
                'ping_time': ping_time,
                'packet_loss': packet_loss,
                'timestamp': timestamp
            })

            history = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp')[:20]
            time_labels = [timezone.localtime(h.timestamp).strftime('%H:%M') for h in reversed(history)]
            latency_values = [h.ping_time or 0 for h in reversed(history)]
            while len(time_labels) < 20:
                time_labels.insert(0, f"历史-{20-len(time_labels)}")
                latency_values.insert(0, 0)

            history_data['datasets'].append({
                'label': target['name'],
                'data': latency_values,
                'borderColor': colors[idx % len(colors)],
                'backgroundColor': 'transparent',
                'borderWidth': 3,
                'tension': 0.4,
                'pointRadius': 2,
                'pointHoverRadius': 5
            })

        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in targets_list],
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
# 5. 多目标 HTTP API（按 id 排序）
# =====================
def multi_http_api(request):
    try:
        targets_qs = MonitorTarget.objects.filter(
            description="category:http", is_active=True
        ).order_by('id')          # ← 关键修改

        if not targets_qs.exists():
            defaults = [
                {'name': 'Google', 'address': 'https://www.google.com'},
                {'name': 'Baidu', 'address': 'https://www.baidu.com'},
                {'name': 'Cloudflare', 'address': 'https://www.cloudflare.com'},
                {'name': 'GitHub', 'address': 'https://github.com'},
            ]
            for d in defaults:
                MonitorTarget.objects.update_or_create(
                    address=d['address'],
                    defaults={'name': d['name'], 'target_type': 'url', 'description': 'category:http'}
                )
            targets_qs = MonitorTarget.objects.filter(description="category:http", is_active=True).order_by('id')

        targets_list = [{'name': t.name, 'address': t.address} for t in targets_qs]

        results = []
        history_data = {'labels': [], 'datasets': []}
        colors = ['#f97316', '#8b5cf6', '#ec4899', '#14b8a6']

        for idx, target in enumerate(targets_list):
            latest = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp').first()
            http_time = round(latest.http_response_time, 1) if latest and latest.http_response_time is not None else 0
            timestamp = timezone.localtime(latest.timestamp).strftime('%H:%M:%S') if latest else '无数据'

            results.append({
                'target': target['name'],
                'url': target['address'],
                'response_time': http_time,
                'timestamp': timestamp
            })

            history = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp')[:20]
            time_labels = [timezone.localtime(h.timestamp).strftime('%H:%M') for h in reversed(history)]
            response_values = [h.http_response_time or 0 for h in reversed(history)]
            while len(time_labels) < 20:
                time_labels.insert(0, f"历史-{20-len(time_labels)}")
                response_values.insert(0, 0)

            history_data['datasets'].append({
                'label': target['name'],
                'data': response_values,
                'borderColor': colors[idx % len(colors)],
                'backgroundColor': 'transparent',
                'borderWidth': 3,
                'tension': 0.4,
                'pointRadius': 2,
            })

        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in targets_list],
            'results': results,
            'history': history_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(f'获取多目标HTTP数据失败: {str(e)}')


# =====================
# 6. 多目标 DNS API（按 id 排序）
# =====================
def multi_dns_api(request):
    try:
        targets_qs = MonitorTarget.objects.filter(
            description="category:dns", is_active=True
        ).order_by('id')          # ← 关键修改

        if not targets_qs.exists():
            defaults = [
                {'name': 'Google', 'address': 'google.com'},
                {'name': 'Cloudflare', 'address': 'cloudflare.com'},
                {'name': 'Baidu', 'address': 'baidu.com'},
                {'name': 'Quad9', 'address': 'dns.quad9.net'},
                {'name': '阿里DNS', 'address': 'dns.aliyun.com'},
            ]
            for d in defaults:
                MonitorTarget.objects.update_or_create(
                    address=d['address'],
                    defaults={'name': d['name'], 'target_type': 'domain', 'description': 'category:dns'}
                )
            targets_qs = MonitorTarget.objects.filter(description="category:dns", is_active=True).order_by('id')

        targets_list = [{'name': t.name, 'address': t.address} for t in targets_qs]

        results = []
        history_data = {'labels': [], 'datasets': []}
        colors = ['#22d3ee', '#a855f7', '#f472b6', '#fb923c', '#eab308']

        for idx, target in enumerate(targets_list):
            latest = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp').first()
            dns_time = round(latest.dns_resolve_time, 2) if latest and latest.dns_resolve_time is not None else 0
            timestamp = timezone.localtime(latest.timestamp).strftime('%H:%M:%S') if latest else '无数据'

            results.append({
                'target': target['name'],
                'domain': target['address'],
                'resolve_time': dns_time,
                'timestamp': timestamp
            })

            history = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp')[:20]
            time_labels = [timezone.localtime(h.timestamp).strftime('%H:%M') for h in reversed(history)]
            dns_values = [round(h.dns_resolve_time or 0, 2) for h in reversed(history)]
            while len(time_labels) < 20:
                time_labels.insert(0, f"历史-{20-len(time_labels)}")
                dns_values.insert(0, 0)

            history_data['datasets'].append({
                'label': target['name'],
                'data': dns_values,
                'backgroundColor': colors[idx % len(colors)],
                'borderColor': colors[idx % len(colors)],
                'borderWidth': 1,
                'borderRadius': 4,
            })

        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in targets_list],
            'results': results,
            'history': history_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(f'获取多目标DNS数据失败: {str(e)}')


# =====================
# 7. 多目标网络抖动 API（按 id 排序）
# =====================
def multi_jitter_api(request):
    try:
        targets_qs = MonitorTarget.objects.filter(
            description="category:ping", is_active=True
        ).order_by('id')          # ← 关键修改

        if not targets_qs.exists():
            defaults = [
                {'name': '8.8.8.8', 'address': '8.8.8.8'},
                {'name': '1.1.1.1', 'address': '1.1.1.1'},
                {'name': 'baidu.com', 'address': 'baidu.com'},
                {'name': '114.114.114.114', 'address': '114.114.114.114'},
            ]
            for d in defaults:
                MonitorTarget.objects.update_or_create(
                    address=d['address'],
                    defaults={'name': d['name'], 'target_type': 'ip' if d['address'][0].isdigit() else 'domain', 'description': 'category:ping'}
                )
            targets_qs = MonitorTarget.objects.filter(description="category:ping", is_active=True).order_by('id')

        targets_list = [{'name': t.name, 'address': t.address} for t in targets_qs]

        results = []
        history_data = {'labels': [], 'datasets': []}
        colors = ['#eab308', '#f59e0b', '#fb923c', '#f97316']

        for idx, target in enumerate(targets_list):
            latest = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp').first()
            jitter = round(latest.network_jitter, 2) if latest and latest.network_jitter is not None else 0.0
            ping_time = round(latest.ping_time, 1) if latest and latest.ping_time is not None else 0

            results.append({
                'target': target['name'],
                'jitter': jitter,
                'avg_latency': ping_time,
                'timestamp': timezone.localtime(latest.timestamp).strftime('%H:%M:%S') if latest else '无数据'
            })

            history = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp')[:20]
            time_labels = [timezone.localtime(h.timestamp).strftime('%H:%M') for h in reversed(history)]
            jitter_values = [round(h.network_jitter or 0, 2) for h in reversed(history)]
            while len(time_labels) < 20:
                time_labels.insert(0, f"历史-{20-len(time_labels)}")
                jitter_values.insert(0, 0)

            history_data['datasets'].append({
                'label': target['name'],
                'data': jitter_values,
                'borderColor': colors[idx % len(colors)],
                'backgroundColor': 'rgba(234, 179, 8, 0.08)',
                'borderWidth': 3.5,
                'tension': 0.35,
                'pointRadius': 2.5,
                'pointHoverRadius': 6,
            })

        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in targets_list],
            'results': results,
            'history': history_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(f'获取网络抖动数据失败: {str(e)}')


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


# =====================
# 多目标 TCP 重传率 API（系统级）
# =====================
def multi_tcp_retrans_api(request):
    try:
        latest = MonitorResult.objects.filter(
            tcp_retransmit_rate__isnull=False
        ).order_by('-timestamp').first()

        current_rate = round(latest.tcp_retransmit_rate, 3) if latest else 0.0

        history = MonitorResult.objects.filter(
            tcp_retransmit_rate__isnull=False
        ).order_by('-timestamp')[:20]

        time_labels = [timezone.localtime(h.timestamp).strftime('%H:%M') for h in reversed(history)]
        rate_values = [round(h.tcp_retransmit_rate or 0, 3) for h in reversed(history)]

        while len(time_labels) < 20:
            time_labels.insert(0, f"历史-{20 - len(time_labels)}")
            rate_values.insert(0, 0)

        return success({
            'current_rate': current_rate,
            'status': latest.status if latest else 'unknown',
            'timestamp': timezone.localtime(latest.timestamp).strftime('%H:%M:%S') if latest else '无数据',
            'history': {
                'labels': time_labels,
                'datasets': [{
                    'label': 'TCP 重传率 (%)',
                    'data': rate_values,
                    'backgroundColor': '#ef4444',
                    'borderColor': '#f87171',
                    'borderWidth': 2,
                    'borderRadius': 6,
                    'barThickness': 12,
                }]
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(f'获取TCP重传率数据失败: {str(e)}')


# =====================
# 8. 多目标 丢包率 API（与 Ping 共用 category:ping）
# =====================
def multi_loss_api(request):
    try:
        targets_qs = MonitorTarget.objects.filter(
            description="category:ping", is_active=True
        ).order_by('id')

        if not targets_qs.exists():
            defaults = [
                {'name': '8.8.8.8', 'address': '8.8.8.8'},
                {'name': '1.1.1.1', 'address': '1.1.1.1'},
                {'name': 'baidu.com', 'address': 'baidu.com'},
                {'name': '114.114.114.114', 'address': '114.114.114.114'},
            ]
            for d in defaults:
                MonitorTarget.objects.update_or_create(
                    address=d['address'],
                    defaults={
                        'name': d['name'],
                        'target_type': 'ip' if d['address'][0].isdigit() else 'domain',
                        'description': 'category:ping'
                    }
                )
            targets_qs = MonitorTarget.objects.filter(description="category:ping", is_active=True).order_by('id')

        targets_list = [{'name': t.name, 'address': t.address} for t in targets_qs]

        results = []
        history_data = {'labels': [], 'datasets': []}
        colors = ['#ef4444', '#f87171', '#fb923c', '#f59e0b']   # 红色系，更直观

        for idx, target in enumerate(targets_list):
            latest = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp').first()
            packet_loss = round(latest.packet_loss, 1) if latest and latest.packet_loss is not None else 0.0
            timestamp = timezone.localtime(latest.timestamp).strftime('%H:%M:%S') if latest else '无数据'

            results.append({
                'target': target['name'],
                'packet_loss': packet_loss,
                'timestamp': timestamp
            })

            # 历史数据（最近20次）
            history = MonitorResult.objects.filter(target__address=target['address']).order_by('-timestamp')[:20]
            time_labels = [timezone.localtime(h.timestamp).strftime('%H:%M') for h in reversed(history)]
            loss_values = [round(h.packet_loss or 0, 1) for h in reversed(history)]
            while len(time_labels) < 20:
                time_labels.insert(0, f"历史-{20 - len(time_labels)}")
                loss_values.insert(0, 0)

            history_data['datasets'].append({
                'label': target['name'],
                'data': loss_values,
                'borderColor': colors[idx % len(colors)],
                'backgroundColor': 'rgba(239, 68, 68, 0.15)',
                'borderWidth': 3,
                'tension': 0.4,
                'pointRadius': 3,
            })

        history_data['labels'] = time_labels if time_labels else [f"第{i}次" for i in range(20)]

        return success({
            'targets': [t['name'] for t in targets_list],
            'results': results,
            'history': history_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(f'获取多目标丢包率数据失败: {str(e)}')