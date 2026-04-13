from django.db import models
from django.utils import timezone
from datetime import timedelta


class MonitorLog(models.Model):
    target = models.CharField(max_length=100, verbose_name='监控目标')
    result = models.TextField(verbose_name='日志内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')
    log_type = models.CharField(
        max_length=20,
        choices=[
            ('ping', 'Ping监控'),
            ('http', 'HTTP监控'),
            ('dns', 'DNS监控'),
            ('jitter', '抖动监控'),
            ('tcp_retrans', 'TCP重传'),
            ('system', '系统日志'),
            ('ai', 'AI分析'),
        ],
        default='system',
        verbose_name='日志类型'
    )
    level = models.CharField(
        max_length=10,
        choices=[('INFO', '信息'), ('WARNING', '警告'), ('ERROR', '错误')],
        default='INFO',
        verbose_name='日志级别'
    )

    class Meta:
        db_table = 'logs_monitorlog'
        verbose_name = '系统日志'
        verbose_name_plural = '系统日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {self.target} - {self.level}"


class AIConfig(models.Model):
    """AI 配置（支持 DeepSeek、Qwen、通义千问等）"""
    PROVIDER_CHOICES = [
        ('deepseek', 'DeepSeek'),
        ('qwen', '通义千问 (Qwen / DashScope)'),
        ('openai', 'OpenAI'),
        ('groq', 'Groq'),
        ('custom', '自定义 OpenAI 兼容接口'),
    ]

    provider = models.CharField(
        max_length=50,
        default='deepseek',
        choices=PROVIDER_CHOICES,
        verbose_name='提供商'
    )
    model_name = models.CharField(
        max_length=100,
        default='deepseek-chat',
        verbose_name='模型名称'
    )
    api_key = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name='API Key',
        help_text='留空则自动从 .env 读取对应环境变量（推荐）'
    )
    base_url = models.CharField(
        max_length=255,
        default='https://api.deepseek.com',
        blank=True,
        null=True,
        verbose_name='Base URL'
    )
    temperature = models.FloatField(default=0.3, verbose_name='Temperature')
    max_tokens = models.IntegerField(default=400, verbose_name='最大 Tokens')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        verbose_name = 'AI 配置'
        verbose_name_plural = 'AI 配置'
        db_table = 'logs_aiconfig'

    def __str__(self):
        return f"{self.provider} - {self.model_name}"