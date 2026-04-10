from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)


def config_page(request):
    """多目标监控配置页面"""
    return render(request, 'targets/config.html')


def dashboard_page(request):
    """多目标监控仪表盘页面"""
    return render(request, 'targets/dashboard.html')


@csrf_exempt
def sync_targets(request):
    """同步目标配置到服务器"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # 在这里可以将目标配置保存到数据库
            # 示例：保存到模型中
            # for key, value in data.items():
            #     if value:
            #         TargetConfig.objects.update_or_create(
            #             name=key,
            #             defaults={'address': value}
            #         )

            return JsonResponse({'status': 'success', 'message': '配置同步成功'})
        except Exception as e:
            logger.error(f"同步目标配置失败: {str(e)}")
            return JsonResponse({'status': 'error', 'message': '同步失败'})

    return JsonResponse({'status': 'error', 'message': '只支持POST请求'})


def get_multi_target_monitoring_data(request):
    """获取多目标监控数据"""
    try:
        # 这里应该从数据库或缓存中获取真实的监控数据
        # 模拟数据结构
        monitoring_data = {
            'ping_data': [45, 52, 38, 61],  # 各目标延迟(ms)
            'loss_data': [0.1, 0.2, 0.0, 0.3],  # 各目标丢包率(%)
            'http_data': [120, 150, 95, 180],  # 各目标HTTP响应时间(ms)
            'jitter_data': [5, 8, 3, 12],  # 各目标网络抖动(ms)
            'tcp_retransmit_data': [0.01, 0.02, 0.005, 0.03],  # 各目标TCP重传率(%)
            'dns_data': [generate_dns_data()],  # DNS解析时间分布
            'targets_status': [True, True, False, True]  # 各目标在线状态
        }

        return JsonResponse(monitoring_data)
    except Exception as e:
        logger.error(f"获取监控数据失败: {str(e)}")
        return JsonResponse({'error': '获取数据失败'}, status=500)


def generate_dns_data():
    """生成DNS解析时间数据（24小时分布）"""
    import random
    return [random.randint(10, 200) for _ in range(24)]


# 如果需要数据库模型，可以创建如下模型
"""
class TargetConfig(models.Model):
    name = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.address}"
"""
