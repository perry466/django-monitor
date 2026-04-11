from django.shortcuts import render

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