from django.urls import path
from . import views

app_name = 'targets'

urlpatterns = [
    path('config/', views.config_page, name='config'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('api/sync-targets/', views.sync_targets, name='sync_targets'),
    path('api/multi-target-monitoring/', views.get_multi_target_monitoring_data, name='multi_target_monitoring'),
]
