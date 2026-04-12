# django-monitor-main/monitor/monitoring.py
import subprocess
import socket
import requests
import platform
import psutil
import time
import statistics
import re

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
# 3. HTTP检测（增强版）
# =====================
def http_check(url, timeout=5, retries=1):
    """检查HTTP响应时间，支持简单重试"""
    for attempt in range(retries + 1):
        try:
            start = time.time()
            res = requests.get(url, timeout=timeout, allow_redirects=True)
            response_time = (time.time() - start) * 1000  # 转为 ms
            return {
                'status_code': res.status_code,
                'response_time': round(response_time, 2),
                'success': True
            }
        except requests.exceptions.Timeout:
            if attempt == retries:
                return {'error': 'timeout', 'response_time': None, 'success': False}
        except requests.exceptions.RequestException as e:
            if attempt == retries:
                return {'error': str(e), 'response_time': None, 'success': False}
        time.sleep(0.5)
    return {'error': 'unknown', 'response_time': None, 'success': False}


# =====================
# 4. DNS解析（增强版：返回时间 + IP）
# =====================
DNS_TARGETS = [
    {'name': 'Google', 'domain': 'google.com'},
    {'name': 'Cloudflare', 'domain': 'cloudflare.com'},
    {'name': 'Baidu', 'domain': 'baidu.com'},
    {'name': 'Quad9', 'domain': 'dns.quad9.net'},
    {'name': '阿里DNS', 'domain': 'dns.aliyun.com'},
]

def dns_resolve(domain):
    """增强版DNS解析：返回解析时间(ms)和IP"""
    try:
        start = time.perf_counter()
        ip = socket.gethostbyname(domain)
        dns_time = (time.perf_counter() - start) * 1000  # ms
        return {
            'ip': ip,
            'resolve_time': round(dns_time, 2),
            'success': True
        }
    except Exception as e:
        return {'error': str(e), 'resolve_time': None, 'success': False}

# =====================
# 5. 系统信息（内存/磁盘/网络速度）
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

    time_diff = current_time - _last_time
    if time_diff == 0:
        return 0.0

    speed = (current_bytes - _last_bytes) / 1024 / time_diff
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
        'network': network_speed
    }


# =====================
# 6. Ping 输出解析函数（关键修复）
# =====================
def parse_ping_output(output):
    """增强版解析（适配 Windows + Linux）"""
    try:
        if not output or "Error" in output or "Timeout" in output or "unreachable" in output.lower():
            return None, 0.0

        # 丢包率
        loss_match = re.search(r'(\d+)%\s*(?:loss|丢失|packet loss)', output, re.IGNORECASE)
        if not loss_match:
            loss_match = re.search(r'lost\s*=\s*(\d+)', output, re.IGNORECASE)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        # 平均延迟
        ping_time = None
        patterns = [
            r'average\s*=\s*(\d+)',      # Windows
            r'avg\s*=\s*([\d.]+)',       # Linux
            r'time[=<]\s*(\d+)',
            r'(\d+)\s*ms'
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                ping_time = float(match.group(1))
                break

        return ping_time, packet_loss
    except Exception:
        return None, 0.0


# =====================
# 网络抖动
# =====================

def measure_jitter(target, count=10):
    """通过多次 ping 计算抖动（推荐方式）"""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        output = subprocess.check_output(
            ['ping', param, str(count), target],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=10
        )

        # 提取所有 RTT 值（适配 Windows/Linux）
        rtt_pattern = r'time[=<]\s*([\d.]+)' if platform.system().lower() != 'windows' else r'(\d+)ms'
        rtts = [float(m.group(1)) for m in re.finditer(rtt_pattern, output)]

        if len(rtts) < 2:
            return {'jitter': 0.0, 'avg_latency': 0.0, 'min_latency': 0.0, 'max_latency': 0.0, 'raw_output': output}

        avg = statistics.mean(rtts)
        jitter_std = statistics.stdev(rtts) if len(rtts) > 1 else 0.0  # 标准差抖动（推荐）
        jitter_range = max(rtts) - min(rtts)  # 峰值抖动（更直观）

        return {
            'jitter_std': round(jitter_std, 2),
            'jitter_range': round(jitter_range, 2),
            'avg_latency': round(avg, 2),
            'min_latency': round(min(rtts), 2),
            'max_latency': round(max(rtts), 2),
            'packet_count': len(rtts),
            'raw_output': output
        }
    except Exception as e:
        return {'jitter_std': None, 'jitter_range': None, 'error': str(e)}