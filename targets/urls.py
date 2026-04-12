from django.urls import path
from . import views

app_name = 'targets'

urlpatterns = [
    path('config/', views.config_page, name='config'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('api/get-targets-by-category/', views.get_targets_by_category, name='get_targets_by_category'),
    path('api/sync-targets/', views.sync_targets, name='sync_targets'),
]