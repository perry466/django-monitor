from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from monitor.models import MonitorTarget
import logging

logger = logging.getLogger(__name__)

def config_page(request):
    """多目标监控配置主页面（分Tab）"""
    return render(request, 'targets/config.html')

def dashboard_page(request):
    """多目标监控仪表盘页面"""
    return render(request, 'targets/dashboard.html')

@csrf_exempt
def sync_targets(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category = data.get('category')
            targets = data.get('targets', [])

            if not category:
                return JsonResponse({'status': 'error', 'message': '缺少category参数'}, status=400)

            # 删除旧配置
            MonitorTarget.objects.filter(description=f"category:{category}").delete()

            saved_count = 0
            for item in targets:
                if not item.get('address'):
                    continue
                MonitorTarget.objects.update_or_create(
                    address=item['address'],
                    defaults={
                        'name': item.get('name', item['address']),
                        'target_type': item.get('type', 'domain'),
                        'description': f"category:{category}",
                        'is_active': item.get('is_active', True),
                    }
                )
                saved_count += 1

            return JsonResponse({
                'status': 'success',
                'message': f'{category.upper()} 配置已保存，共 {saved_count} 个目标'
            })
        except Exception as e:
            logger.error(f"保存失败: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': '只支持POST'}, status=405)


@csrf_exempt
def get_targets_by_category(request):
    category = request.GET.get('category')
    if not category:
        return JsonResponse({'status': 'error', 'message': '缺少category参数'}, status=400)

    targets = MonitorTarget.objects.filter(
        description=f"category:{category}",
        is_active=True
    ).order_by('id').values('id', 'name', 'address', 'target_type', 'is_active')

    return JsonResponse({'status': 'success', 'targets': list(targets)})