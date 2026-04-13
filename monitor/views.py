from django.shortcuts import render
from django.conf import settings
from  .models import MonitorResult,AIConfig
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
import os


def dashboard(request):
    return render(request,'monitor/dashboard.html')
def ping(request):
    return render(request, 'monitor/ping.html')

def loss(request):
    return render(request, 'monitor/loss.html')

def http_response(request):
    return render(request, 'monitor/http_response.html')

def jitter(request):
    return render(request, 'monitor/jitter.html')

def dns(request):
    return render(request, 'monitor/dns.html')

def tcp_retrans(request):
    return render(request,'monitor/tcp_retrans.html')
