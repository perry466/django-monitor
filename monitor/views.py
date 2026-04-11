from django.shortcuts import render

def dashboard(request):
    return render(request,'monitor/dashboard.html')
def ping(request):
    return render(request, 'monitor/ping.html')

def loss(request):
    return render(request, 'monitor/loss.html')