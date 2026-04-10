from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
from .models import MonitorTarget, MonitorResult

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'monitor/index.html')

def latency(request):
    return render(request, 'monitor/latency.html')

def ping(request):
    return render(request, 'monitor/ping.html')

def http(request):
    return render(request, 'monitor/http.html')

def jitter(request):
    return render(request, 'monitor/jitter.html')

def dns(request):
    return render(request, 'monitor/dns.html')

def tcp(request):
    return render(request, 'monitor/tcp.html')

