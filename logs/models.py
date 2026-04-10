from django.db import models


class MonitorLog(models.Model):
    target = models.CharField(max_length=100)
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)