import subprocess
import socket
import requests
import platform
import psutil
import time
# =====================
# 1. Ping
# =====================

def ping_host(target):
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        output = subprocess.check_output(
            ['ping', param, '1', target],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=5
        )
        return output
    except subprocess.TimeoutExpired:
        return 'timeout'
    except Exception as e:
        return str(e)


# =====================
# 2. TCP端口检测
# =====================
def tcp_check(target, port):
    try:
        sock = socket.create_connection((target, port), timeout=3)
        sock.close()
        return 'open'
    except Exception:
        return 'closed'


# =====================
# 3. HTTP检测
# =====================
def http_check(url):
    try:
        res = requests.get(url, timeout=5)
        return {
            'status_code': res.status_code,
            'response_time': res.elapsed.total_seconds()
        }
    except Exception as e:
        return str(e)


# =====================
# 4. DNS解析
# =====================
def dns_resolve(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except Exception as e:
        return str(e)


# =====================
# 5. 内存/磁盘/带宽
# =====================

_last_bytes = None
_last_time = None


def get_network_speed():
    global _last_bytes, _last_time

    net = psutil.net_io_counters()
    current_bytes = net.bytes_sent + net.bytes_recv
    current_time = time.time()

    if _last_bytes is None:
        _last_bytes = current_bytes
        _last_time = current_time
        return 0.0

    # 计算时间差
    time_diff = current_time - _last_time
    if time_diff == 0:
        return 0.0

    # 计算速度（KB/s）
    speed = (current_bytes - _last_bytes) / 1024 / time_diff

    # 更新记录
    _last_bytes = current_bytes
    _last_time = current_time

    return round(speed, 2)


def system_info():
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    network_speed = get_network_speed()

    return {
        'memory': memory,
        'disk': disk,
        'network': network_speed  # 👉 现在是 KB/s
    }