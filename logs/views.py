# django-monitor-main/logs/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from datetime import datetime, timedelta
from django.utils import timezone

from openai import OpenAI

# ==================== 正确导入模型 ====================
from .models import AIConfig, MonitorLog,AIReport
from monitor.models import MonitorResult
# ===================================================

def ai_analysis(request):
    """AI 智能分析页面"""
    ai_config = AIConfig.objects.filter(is_active=True).first()
    if not ai_config:
        ai_config = AIConfig.objects.create()

    context = {
        'title': 'AI 智能分析 - NEON MONITOR',
        'ai_config': ai_config,
    }
    return render(request, 'logs/ai_analysis.html', context)


@csrf_exempt
def ai_generate_report(request):
    """生成 AI 诊断报告"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '只支持 POST 请求'}, status=405)

    try:
        config = AIConfig.objects.filter(is_active=True).first()
        if not config:
            return JsonResponse({'success': False, 'error': '请先创建 AI 配置'}, status=400)

        # 智能获取 API Key
        api_key = config.api_key.strip() if config.api_key else None
        if not api_key:
            env_map = {
                'deepseek': 'DEEPSEEK_API_KEY',
                'qwen': 'DASHSCOPE_API_KEY',
                'openai': 'OPENAI_API_KEY',
                'groq': 'GROQ_API_KEY',
            }
            env_key = env_map.get(config.provider)
            if env_key:
                api_key = os.getenv(env_key)

        if not api_key:
            return JsonResponse({
                'success': False,
                'error': f'未找到 {config.provider} 的 API Key！请在配置页面填写或在 .env 中设置'
            }, status=400)

        # 获取最新监控数据
        recent_results = MonitorResult.objects.select_related('target').order_by('-timestamp')[:50]
        summary_data = [{
            "target": r.target.name if r.target else "系统",
            "ping": round(r.ping_time or 0, 1),
            "loss": round(r.packet_loss or 0, 1),
            "http": round(r.http_response_time or 0, 1),
            "dns": round(r.dns_resolve_time or 0, 2),
            "jitter": round(r.network_jitter or 0, 2),
            "retrans": round(r.tcp_retransmit_rate or 0, 3),
            "status": r.status,
            "time": r.timestamp.strftime("%H:%M")
        } for r in recent_results]

        data_str = json.dumps(summary_data[-20:], ensure_ascii=False, separators=(',', ':'))

        system_prompt = """你是一位经验丰富、专业严谨的网络运维专家。请基于监控数据生成一份有深度但简洁的中文诊断报告。

严格按照以下格式输出：

第一行：只输出整体健康评分，必须是以下之一（不要输出数字或其他内容）：
优秀 / 良好 / 需关注 / 严重

然后空一行

**系统整体分析：**
用2-3句话对当前网络状况做综合评价。要体现系统性思维，综合考虑 ping 延迟、丢包率、抖动、HTTP响应时间、DNS解析等多个维度。区分国内目标和国际目标的差异。如果大部分正常，要明确指出“整体运行平稳，仅个别国际/国内目标存在问题”。

**主要问题及建议：**
最多列出3条最重要的问题，每条严格使用以下格式：
1. **问题描述**（具体指出目标名称 + 具体指标异常数值 + 可能的影响）
   建议：一句实用、可操作的建议（优先给出具体措施）

要求：
- 语言专业、客观、简洁有力
- 总字数严格控制在 380 字以内
- 不要使用“左右”、“大约”等模糊词，要用具体数值"""

        client = OpenAI(
            api_key=api_key,
            base_url=config.base_url.strip() if config.base_url and config.base_url.strip() else None
        )

        response = client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"最近20条网络监控数据摘要：\n{data_str}\n\n请按要求生成诊断报告。"}
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=25
        )

        report = response.choices[0].message.content.strip()
        # ==================== 新增：自动保存监控数据分析报告 ====================
        try:
            lines = [line.strip() for line in report.strip().split('\n') if line.strip()]
            health_score = lines[0] if lines and lines[0] in ["优秀", "良好", "需关注", "严重"] else "需关注"

            AIReport.objects.create(
                report_type='monitor',
                title='网络监控诊断报告',
                content=report,
                model_used=f"{config.provider} - {config.model_name}",
                health_score=health_score
            )
            print(f"✅ AI监控报告已保存 - 评分: {health_score}")
        except Exception as save_e:
            print(f"⚠️ 保存AI监控报告失败: {save_e}")
        # ============================================================

        return JsonResponse({
            'success': True,
            'report': report,
            'model_used': f"{config.provider} - {config.model_name}"
        })

        return JsonResponse({
            'success': True,
            'report': report,
            'model_used': f"{config.provider} - {config.model_name}"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@csrf_exempt
def ai_analyze_logs(request):
    """新增：AI 分析系统日志"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '只支持 POST 请求'}, status=405)

    try:
        config = AIConfig.objects.filter(is_active=True).first()
        if not config:
            return JsonResponse({'success': False, 'error': '请先创建 AI 配置'}, status=400)

        # 获取 API Key（与原有逻辑一致）
        api_key = config.api_key.strip() if config.api_key else None
        if not api_key:
            env_map = {
                'deepseek': 'DEEPSEEK_API_KEY',
                'qwen': 'DASHSCOPE_API_KEY',
                'openai': 'OPENAI_API_KEY',
                'groq': 'GROQ_API_KEY',
            }
            env_key = env_map.get(config.provider)
            if env_key:
                api_key = os.getenv(env_key)

        if not api_key:
            return JsonResponse({'success': False, 'error': f'未找到 {config.provider} 的 API Key！'}, status=400)

        # 获取最近的系统日志（默认最近50条，可通过参数过滤）
        log_type = request.POST.get('log_type', 'all')  # all, ping, http, dns, jitter, tcp_retrans, system, ai
        level = request.POST.get('level', 'all')        # all, INFO, WARNING, ERROR

        queryset = MonitorLog.objects.all().order_by('-created_at')[:50]

        if log_type != 'all':
            queryset = queryset.filter(log_type=log_type)
        if level != 'all':
            queryset = queryset.filter(level=level)

        logs_data = []
        for log in queryset:
            logs_data.append({
                "time": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "target": log.target,
                "level": log.level,
                "type": log.get_log_type_display(),
                "content": log.result[:500] + "..." if len(log.result) > 500 else log.result
            })

        logs_str = json.dumps(logs_data, ensure_ascii=False, indent=2)

        system_prompt = """你是一位经验丰富的网络运维专家。请对提供的系统日志进行深度分析，并生成一份专业、简洁的中文诊断报告。

严格按照以下格式输出：

第一行：只输出整体日志健康评分（优秀 / 良好 / 需关注 / 严重）

然后空一行

**日志整体分析：**
用2-3句话总结日志反映的系统状况，重点指出频繁出现的错误、警告或异常模式。

**主要问题及建议：**
最多列出3条最重要的问题，每条格式如下：
1. **问题描述**（具体指出日志中出现的关键词、目标、次数或异常时间）
   建议：一句实用、可操作的处理建议

要求：
- 语言专业、客观、简洁
- 总字数控制在400字以内
- 如果日志正常，要明确指出“暂未发现明显异常”"""

        client = OpenAI(
            api_key=api_key,
            base_url=config.base_url.strip() if config.base_url and config.base_url.strip() else None
        )

        response = client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"最近系统日志数据（JSON格式）：\n{logs_str}\n\n请按要求生成日志分析报告。"}
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=30
        )

        report = response.choices[0].message.content.strip()
        # ==================== 新增：自动保存系统日志分析报告 ====================
        try:
            lines = [line.strip() for line in report.strip().split('\n') if line.strip()]
            health_score = lines[0] if lines and lines[0] in ["优秀", "良好", "需关注", "严重"] else "需关注"

            AIReport.objects.create(
                report_type='logs',
                title='系统日志分析报告',
                content=report,
                model_used=f"{config.provider} - {config.model_name}",
                health_score=health_score
            )
            print(f"✅ AI日志报告已保存 - 评分: {health_score}")
        except Exception as save_e:
            print(f"⚠️ 保存AI日志报告失败: {save_e}")
        # ============================================================

        return JsonResponse({
            'success': True,
            'report': report,
            'model_used': f"{config.provider} - {config.model_name}",
            'log_count': len(logs_data)
        })

        return JsonResponse({
            'success': True,
            'report': report,
            'model_used': f"{config.provider} - {config.model_name}",
            'log_count': len(logs_data)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def save_ai_config(request):
    """保存 AI 配置"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只支持 POST 请求'})

    try:
        data = json.loads(request.body)
        config = AIConfig.objects.filter(is_active=True).first()
        if not config:
            config = AIConfig.objects.create(is_active=True)

        config.provider = data.get('provider', config.provider)
        config.model_name = data.get('model_name', config.model_name).strip()
        config.base_url = data.get('base_url', config.base_url).strip()
        config.temperature = float(data.get('temperature', config.temperature))
        config.max_tokens = int(data.get('max_tokens', config.max_tokens))

        api_key_input = data.get('api_key', '').strip()
        config.api_key = api_key_input if api_key_input else None

        config.save()

        return JsonResponse({
            'success': True,
            'message': '✅ 配置保存成功！'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'保存失败: {str(e)}'
        })







# ====================== 系统日志功能 ======================
def system_logs(request):
    """系统日志主页面"""
    return render(request, 'logs/system_logs.html')


@csrf_exempt
def get_system_logs(request):
    """系统日志 - 直接从 MonitorResult 读取原始监控数据（适配当前前端）"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': '只支持GET请求'}, status=405)

    try:
        log_type = request.GET.get('log_type', 'all')   # all, ping, http, dns, jitter, tcp_retrans
        period = request.GET.get('period', 'all')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))

        queryset = MonitorResult.objects.select_related('target').order_by('-timestamp')

        # 根据前端选择的类型过滤
        if log_type != 'all':
            if log_type == 'ping':
                queryset = queryset.filter(ping_time__isnull=False)
            elif log_type == 'http':
                queryset = queryset.filter(http_response_time__isnull=False)
            elif log_type == 'dns':
                queryset = queryset.filter(dns_resolve_time__isnull=False)
            elif log_type == 'jitter':
                queryset = queryset.filter(network_jitter__isnull=False)
            elif log_type == 'tcp_retrans':
                queryset = queryset.filter(tcp_retransmit_rate__isnull=False)

        # 时间范围过滤
        now = timezone.now()
        if period == 'today':
            queryset = queryset.filter(timestamp__date=now.date())
        elif period == '7days':
            queryset = queryset.filter(timestamp__gte=now - timedelta(days=7))
        elif period == '30days':
            queryset = queryset.filter(timestamp__gte=now - timedelta(days=30))
        elif period == 'custom' and start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                if (end - start).days > 31:
                    return JsonResponse({'success': False, 'error': '时间跨度不能超过30天'}, status=400)
                queryset = queryset.filter(timestamp__range=(start, end))
            except ValueError:
                return JsonResponse({'success': False, 'error': '日期格式错误'}, status=400)

        total = queryset.count()
        start_idx = (page - 1) * per_page
        results = queryset[start_idx:start_idx + per_page]

        log_list = []
        for r in results:
            details = []
            if r.ping_time is not None:
                details.append(f"延迟 {r.ping_time:.1f}ms")
            if r.packet_loss is not None:
                details.append(f"丢包 {r.packet_loss:.1f}%")
            if r.http_response_time is not None:
                details.append(f"HTTP {r.http_response_time:.1f}ms")
            if r.dns_resolve_time is not None:
                details.append(f"DNS {r.dns_resolve_time:.2f}ms")
            if r.network_jitter is not None:
                details.append(f"抖动 {r.network_jitter:.2f}ms")
            if r.tcp_retransmit_rate is not None:
                details.append(f"TCP重传率 {r.tcp_retransmit_rate:.3f}%")

            result_text = " | ".join(details) if details else "无监控数据"

            log_list.append({
                'id': r.id,
                'target': r.target.name if r.target else '系统',
                'created_at': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'log_type': log_type if log_type != 'all' else 'monitor',
                'level': 'INFO',
                'result': result_text,
                'full_result': f"目标：{r.target.name if r.target else '系统'}\n"
                              f"时间：{r.timestamp}\n"
                              f"状态：{r.status}\n"
                              f"详细数据：\n{result_text}"
            })

        return JsonResponse({
            'success': True,
            'logs': log_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if total > 0 else 0
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ====================== 新增：获取最近AI报告 ======================
@csrf_exempt
def get_recent_ai_reports(request):
    """获取最近20次AI报告（仪表盘使用）"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': '只支持GET请求'}, status=405)

    try:
        reports = AIReport.objects.all()[:20]

        report_list = [{
            'id': r.id,
            'type': r.get_report_type_display(),
            'title': r.title,
            'content': r.content,
            'health_score': r.health_score,
            'model_used': r.model_used,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for r in reports]

        latest = reports.first()

        return JsonResponse({
            'success': True,
            'reports': report_list,
            'latest': {
                'id': latest.id,
                'content': latest.content,
                'health_score': latest.health_score,
                'model_used': latest.model_used,
                'created_at': latest.created_at.strftime('%Y-%m-%d %H:%M')
            } if latest else None
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ====================== 新增：下载日志为 CSV ======================
from django.http import HttpResponse
import csv
from datetime import timedelta

def download_logs(request):
    """下载系统日志为 CSV 文件（支持当前筛选条件）"""
    try:
        log_type = request.GET.get('log_type', 'all')
        period = request.GET.get('period', 'all')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        queryset = MonitorResult.objects.select_related('target').order_by('-timestamp')

        # 筛选条件（与 get_system_logs 保持一致）
        if log_type != 'all':
            if log_type == 'ping':
                queryset = queryset.filter(ping_time__isnull=False)
            elif log_type == 'http':
                queryset = queryset.filter(http_response_time__isnull=False)
            elif log_type == 'dns':
                queryset = queryset.filter(dns_resolve_time__isnull=False)
            elif log_type == 'jitter':
                queryset = queryset.filter(network_jitter__isnull=False)
            elif log_type == 'tcp_retrans':
                queryset = queryset.filter(tcp_retransmit_rate__isnull=False)

        if period == 'today':
            queryset = queryset.filter(timestamp__date=timezone.now().date())
        elif period == '7days':
            queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(days=7))
        elif period == '30days':
            queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(days=30))
        elif period == 'custom' and start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(timestamp__range=(start, end))
            except ValueError:
                pass  # 日期格式错误则不筛选

        # 生成 CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"NEON_Monitor_Logs_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        # CSV 表头
        writer.writerow(['时间', '目标', '监控类型', '延迟(ms)', '丢包率(%)', 'HTTP响应(ms)',
                        'DNS解析(ms)', '抖动(ms)', 'TCP重传率(%)', '状态'])

        for r in queryset:
            writer.writerow([
                r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                r.target.name if r.target else '系统',
                'Monitor',
                round(r.ping_time or 0, 1),
                round(r.packet_loss or 0, 1),
                round(r.http_response_time or 0, 1),
                round(r.dns_resolve_time or 0, 2),
                round(r.network_jitter or 0, 2),
                round(r.tcp_retransmit_rate or 0, 3),
                r.status or '正常'
            ])

        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"下载失败: {str(e)}", status=500)