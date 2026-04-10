import subprocess
import socket
import requests
import time


def ping_test(address):
    """执行ping测试"""
    try:
        # Windows系统
        if hasattr(subprocess, 'list2cmdline'):
            result = subprocess.run(['ping', '-n', '4', address],
                                    capture_output=True, text=True, timeout=10)
        # Linux/Mac系统
        else:
            result = subprocess.run(['ping', '-c', '4', address],
                                    capture_output=True, text=True, timeout=10)

        # 解析ping结果
        lines = result.stdout.split('\n')
        avg_time = 0
        packet_loss = 0

        for line in lines:
            if '平均' in line or 'avg' in line.lower():
                # Windows: 平均 = 45ms
                # Linux: avg = 45.000 ms
                import re
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    avg_time = float(match.group(1))
            elif 'packet loss' in line.lower() or '丢包' in line:
                import re
                match = re.search(r'(\d+)%', line)
                if match:
                    packet_loss = float(match.group(1))

        return {
            'time': avg_time,
            'loss': packet_loss,
            'status': 'up' if avg_time > 0 else 'down'
        }
    except Exception as e:
        return {'time': 0, 'loss': 100, 'status': 'down'}


def http_test(url):
    """执行HTTP响应时间测试"""
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'

    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒

        return {
            'response_time': response_time,
            'status_code': response.status_code,
            'status': 'up' if response.status_code < 400 else 'down'
        }
    except Exception as e:
        return {'response_time': 0, 'status_code': 0, 'status': 'down'}


def dns_test(hostname):
    """执行DNS解析时间测试"""
    try:
        start_time = time.time()
        socket.gethostbyname(hostname)
        resolve_time = (time.time() - start_time) * 1000  # 转换为毫秒

        return {
            'resolve_time': resolve_time,
            'status': 'up'
        }
    except Exception as e:
        return {'resolve_time': 0, 'status': 'down'}
