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
# 全局缓存
# =====================
_last_bytes = None
_last_time = None
_last_tcp_stats = {'sent': 0, 'retrans': 0, 'timestamp': 0}


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
# 2. TCP端口检测（修复：必须存在！）
# =====================
def tcp_check(target, port):
    """检查TCP端口是否开放"""
    try:
        sock = socket.create_connection((target, port), timeout=3)
        sock.close()
        return 'open'
    except Exception:
        return 'closed'


# =====================
# 3. HTTP检测
# =====================
def http_check(url, timeout=5, retries=1):
    """检查HTTP响应时间，支持简单重试"""
    for attempt in range(retries + 1):
        try:
            start = time.time()
            res = requests.get(url, timeout=timeout, allow_redirects=True)
            response_time = (time.time() - start) * 1000
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
# 4. DNS解析
# =====================
def dns_resolve(domain):
    """DNS解析时间"""
    try:
        start = time.perf_counter()
        ip = socket.gethostbyname(domain)
        dns_time = (time.perf_counter() - start) * 1000
        return {
            'ip': ip,
            'resolve_time': round(dns_time, 2),
            'success': True
        }
    except Exception as e:
        return {'error': str(e), 'resolve_time': None, 'success': False}


# =====================
# 5. 系统信息
# =====================
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
# 6. Ping 输出解析
# =====================
def parse_ping_output(output):
    """增强版解析（适配 Windows + Linux）"""
    try:
        if not output or "Error" in output or "Timeout" in output or "unreachable" in output.lower():
            return None, 0.0

        loss_match = re.search(r'(\d+)%\s*(?:loss|丢失|packet loss)', output, re.IGNORECASE)
        if not loss_match:
            loss_match = re.search(r'lost\s*=\s*(\d+)', output, re.IGNORECASE)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        ping_time = None
        patterns = [
            r'average\s*=\s*(\d+)',
            r'avg\s*=\s*([\d.]+)',
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
# 7. 网络抖动
# =====================
def measure_jitter(target, count=10):
    """通过多次 ping 计算抖动"""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        output = subprocess.check_output(
            ['ping', param, str(count), target],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=10
        )

        rtt_pattern = r'time[=<]\s*([\d.]+)' if platform.system().lower() != 'windows' else r'(\d+)ms'
        rtts = [float(m.group(1)) for m in re.finditer(rtt_pattern, output)]

        if len(rtts) < 2:
            return {'jitter_std': 0.0, 'avg_latency': 0.0}

        avg = statistics.mean(rtts)
        jitter_std = statistics.stdev(rtts) if len(rtts) > 1 else 0.0

        return {
            'jitter_std': round(jitter_std, 2),
            'avg_latency': round(avg, 2)
        }
    except Exception:
        return {'jitter_std': 0.0, 'avg_latency': 0.0}


# =====================
# 8. TCP 重传率监控（改进版）
# =====================
def get_tcp_retransmit_rate():
    """
    返回当前 TCP 重传率 (%)
    推荐阈值（更符合实际网络）：
    < 0.5%   → excellent
    0.5-2.0% → warning
    > 2.0%   → critical
    """
    try:
        system = platform.system().lower()
        current_sent = 0
        current_retrans = 0

        if system == 'linux':
            # 优先使用 nstat（如果可用），否则 fallback 到 netstat /proc
            try:
                output = subprocess.check_output(['nstat', '-z'],
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True, timeout=3)
                sent_match = re.search(r'TcpOutSegs\s+(\d+)', output)
                retrans_match = re.search(r'TcpRetransSegs\s+(\d+)', output)
            except Exception:
                try:
                    output = subprocess.check_output(['netstat', '-s'],
                                                     stderr=subprocess.STDOUT,
                                                     universal_newlines=True, timeout=3)
                except FileNotFoundError:
                    output = subprocess.check_output(['cat', '/proc/net/snmp'],
                                                     universal_newlines=True, timeout=3)

                # 更健壮的匹配（支持不同内核输出）
                sent_match = re.search(r'(\d+)\s+segments\s+send out', output, re.IGNORECASE)
                retrans_match = re.search(r'(\d+)\s+segments\s+retransmited?', output, re.IGNORECASE)  # 兼容 retransmited / retransmitted

                if not sent_match or not retrans_match:
                    # 备用：/proc/net/snmp Tcp 行（第12和13字段）
                    snmp_match = re.search(r'Tcp:\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(\d+)\s+(\d+)', output)
                    if snmp_match:
                        current_sent = int(snmp_match.group(1))
                        current_retrans = int(snmp_match.group(2))

            if sent_match:
                current_sent = int(sent_match.group(1))
            if retrans_match:
                current_retrans = int(retrans_match.group(1))

        else:  # Windows
            output = subprocess.check_output(['netstat', '-s'],
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True, timeout=5)
            sent_match = re.search(r'Segments Sent\s*=\s*(\d+)', output, re.IGNORECASE)
            retrans_match = re.search(r'Retransmitted Segments\s*=\s*(\d+)', output, re.IGNORECASE)

            current_sent = int(sent_match.group(1)) if sent_match else 0
            current_retrans = int(retrans_match.group(1)) if retrans_match else 0

        # 计算差值率
        global _last_tcp_stats
        now = time.time()

        if _last_tcp_stats['timestamp'] == 0 or (now - _last_tcp_stats['timestamp'] > 90):
            # 首次启动或间隔过长时，不计算比例，直接返回 0 并更新基线
            rate = 0.0
        else:
            delta_sent = max(current_sent - _last_tcp_stats['sent'], 1)
            delta_retrans = max(current_retrans - _last_tcp_stats['retrans'], 0)
            rate = round((delta_retrans / delta_sent) * 100, 3)

        # 更新缓存
        _last_tcp_stats.update({
            'sent': current_sent,
            'retrans': current_retrans,
            'timestamp': now
        })

        # 更合理的状态判断
        if rate < 0.5:
            status = 'excellent'
        elif rate < 2.0:
            status = 'warning'
        else:
            status = 'critical'

        return {
            'retrans_rate': rate,
            'status': status,
            'total_sent': current_sent,
            'total_retrans': current_retrans
        }

    except Exception as e:
        return {
            'retrans_rate': 0.0,
            'status': 'unknown',
            'error': str(e)
        }