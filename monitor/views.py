from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# 只导入需要的模型（移除了 AIConfig）
from .models import MonitorResult


# ====================== 所有监控页面都需要登录才能访问 ======================
@login_required(login_url='/login/')
def dashboard(request):
    return render(request, 'monitor/dashboard.html')


@login_required(login_url='/login/')
def ping(request):
    return render(request, 'monitor/ping.html')


@login_required(login_url='/login/')
def loss(request):
    return render(request, 'monitor/loss.html')


@login_required(login_url='/login/')
def http_response(request):
    return render(request, 'monitor/http_response.html')


@login_required(login_url='/login/')
def jitter(request):
    return render(request, 'monitor/jitter.html')


@login_required(login_url='/login/')
def dns(request):
    return render(request, 'monitor/dns.html')


@login_required(login_url='/login/')
def tcp_retrans(request):
    return render(request, 'monitor/tcp_retrans.html')