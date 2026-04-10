from django.http import JsonResponse
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