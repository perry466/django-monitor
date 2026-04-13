# django-monitor-main/logs/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from openai import OpenAI
from .models import AIConfig
from monitor.models import MonitorResult   # 注意：这里仍然从 monitor 取监控数据


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

        # ==================== 优化后的系统 Prompt ====================
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