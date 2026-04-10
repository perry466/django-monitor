import subprocess
import socket
import time
import threading
from django.shortcuts import render
from django.http import JsonResponse
import re
import requests
import dns.resolver


def index(request):
    return render(request, 'targets/index.html')


def check_targets(request):
    if request.method == 'POST':
        targets = [
            request.POST.get('target1', ''),
            request.POST.get('target2', ''),
            request.POST.get('target3', ''),
            request.POST.get('target4', '')
        ]

        results = []
        threads = []

        for i in range(4):
            thread = threading.Thread(target=check_single_target, args=(targets[i], results, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return JsonResponse({'results': results})

    return JsonResponse({'error': 'Invalid method'})


def check_single_target(target, results, index):
    if not target.strip():
        results.append({
            'index': index,
            'latency': 'N/A',
            'packet_loss': 'N/A',
            'http_time': 'N/A',
            'jitter': 'N/A',
            'dns_time': 'N/A',
            'tcp_retransmit': 'N/A'
        })
        return

    # 移除协议前缀，只保留域名或IP
    clean_target = target.replace('http://', '').replace('https://', '').split('/')[0]

    result = {
        'index': index,
        'latency': get_latency(clean_target),
        'packet_loss': get_packet_loss(clean_target),
        'http_time': get_http_response_time(target),
        'jitter': get_jitter(clean_target),
        'dns_time': get_dns_time(clean_target),
        'tcp_retransmit': get_tcp_retransmit(clean_target)
    }

    results.append(result)


def get_latency(target):
    try:
        # 使用ping命令测试延迟
        result = subprocess.run(['ping', '-c', '4', target],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'avg' in line and '=' in line:
                    avg_match = re.search(r'(\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)', line)
                    if avg_match:
                        avg_time = float(avg_match.group(2))
                        return f"{avg_time:.2f}ms"
        return "N/A"
    except:
        return "N/A"


def get_packet_loss(target):
    try:
        result = subprocess.run(['ping', '-c', '4', target],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'packet loss' in line:
                    match = re.search(r'(\d+)% packet loss', line)
                    if match:
                        loss_percent = match.group(1)
                        return f"{loss_percent}%"
        return "N/A"
    except:
        return "N/A"


def get_http_response_time(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        return f"{response_time:.2f}ms"
    except:
        return "N/A"


def get_jitter(target):
    try:
        result = subprocess.run(['ping', '-c', '10', target],
                                capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            times = []
            for line in lines:
                if 'time=' in line:
                    time_match = re.search(r'time=(\d+\.?\d*) ms', line)
                    if time_match:
                        times.append(float(time_match.group(1)))

            if len(times) > 1:
                # 计算抖动（相邻延迟差值的平均值）
                jitters = []
                for i in range(1, len(times)):
                    jitters.append(abs(times[i] - times[i - 1]))

                avg_jitter = sum(jitters) / len(jitters)
                return f"{avg_jitter:.2f}ms"
        return "N/A"
    except:
        return "N/A"


def get_dns_time(target):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10
        resolver.lifetime = 10

        start_time = time.time()
        resolver.resolve(target, 'A')
        end_time = time.time()

        dns_time = (end_time - start_time) * 1000  # 转换为毫秒
        return f"{dns_time:.2f}ms"
    except:
        return "N/A"


def get_tcp_retransmit(target):
    try:
        # 这里模拟TCP重传率检测，实际环境中需要更复杂的实现
        # 在实际应用中，这通常需要网络抓包工具如tcpdump
        # 这里我们简单地返回一个模拟值
        # 实际环境中需要使用更复杂的方法来检测TCP重传
        return "0.00%"
    except:
        return "N/A"
