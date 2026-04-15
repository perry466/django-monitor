from django.db import models
from django.utils import timezone


class MonitorTarget(models.Model):
    """监控目标模型"""
    TARGET_TYPES = [
        ('ip', 'IP地址'),
        ('domain', '域名'),
        ('url', 'URL'),
    ]

    name = models.CharField(max_length=100, verbose_name='目标名称')
    address = models.CharField(max_length=255, verbose_name='IP地址或域名')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES, default='domain', verbose_name='目标类型')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'monitor_targets'
        verbose_name = '监控目标'
        verbose_name_plural = '监控目标'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.address})"

    def save(self, *args, **kwargs):
        # 自动检测目标类型
        if self.address.startswith(('http://', 'https://')):
            self.target_type = 'url'
        elif self._is_ip_address(self.address):
            self.target_type = 'ip'
        else:
            self.target_type = 'domain'
        super().save(*args, **kwargs)

    def _is_ip_address(self, address):
        """判断是否为IP地址"""
        import re
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(ip_pattern, address))


class MonitorResult(models.Model):
    """监控结果模型"""
    target = models.ForeignKey('MonitorTarget', on_delete=models.CASCADE, verbose_name='监控目标')
    ping_time = models.FloatField(null=True, blank=True, verbose_name='延迟(ms)')
    packet_loss = models.FloatField(null=True, blank=True, verbose_name='丢包率(%)')
    http_response_time = models.FloatField(null=True, blank=True, verbose_name='HTTP响应时间(ms)')
    dns_resolve_time = models.FloatField(null=True, blank=True, verbose_name='DNS解析时间(ms)')
    network_jitter = models.FloatField(null=True, blank=True, verbose_name='网络抖动(ms)')
    tcp_retransmit_rate = models.FloatField(null=True, blank=True, verbose_name='TCP重传率(%)')
    status = models.CharField(max_length=20, default='unknown', verbose_name='状态')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')

    class Meta:
        db_table = 'monitor_results'
        verbose_name = '监控结果'
        verbose_name_plural = '监控结果'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.target.name} - {self.timestamp}"


class MonitoringSchedule(models.Model):
    """监控计划模型"""
    FREQUENCY_CHOICES = [
        ('1m', '每分钟'),
        ('5m', '每5分钟'),
        ('15m', '每15分钟'),
        ('30m', '每30分钟'),
        ('1h', '每小时'),
        ('6h', '每6小时'),
        ('12h', '每12小时'),
        ('1d', '每天'),
    ]

    target = models.ForeignKey('MonitorTarget', on_delete=models.CASCADE, verbose_name='监控目标')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='5m', verbose_name='监控频率')
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    last_run = models.DateTimeField(null=True, blank=True, verbose_name='最后执行时间')
    next_run = models.DateTimeField(null=True, blank=True, verbose_name='下次执行时间')

    class Meta:
        db_table = 'monitoring_schedules'
        verbose_name = '监控计划'
        verbose_name_plural = '监控计划'

    def __str__(self):
        return f"{self.target.name} - {self.frequency}"