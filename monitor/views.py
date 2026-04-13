from django.shortcuts import render
from django.conf import settings
from  .models import MonitorResult,AIConfig
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
import os


def dashboard(request):
    return render(request,'monitor/dashboard.html')
def ping(request):
    return render(request, 'monitor/ping.html')

def loss(request):
    return render(request, 'monitor/loss.html')

def http_response(request):
    return render(request, 'monitor/http_response.html')

def jitter(request):
    return render(request, 'monitor/jitter.html')

def dns(request):
    return render(request, 'monitor/dns.html')

def tcp_retrans(request):
    return render(request,'monitor/tcp_retrans.html')

def ai_analysis(request):
    """AI 智能分析页面"""
    # 获取最新配置（取第一条激活的）
    ai_config = AIConfig.objects.filter(is_active=True).first()
    if not ai_config:
        ai_config = AIConfig.objects.create()  # 创建默认配置

    context = {
        'title': 'AI 智能分析 - NEON MONITOR',
        'ai_config': ai_config,
    }
    return render(request, 'monitor/ai_analysis.html', context)


@csrf_exempt
def ai_generate_report(request):
    """生成 AI 诊断报告 - 支持环境变量读取 API Key"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '只支持 POST 请求'})

    try:
        config = AIConfig.objects.filter(is_active=True).first()
        if not config:
            return JsonResponse({'success': False, 'error': '请先在后台或前端创建 AI 配置'})

        # ==================== 优先从环境变量读取 API Key ====================
        api_key = None
        if config.provider == 'deepseek':
            api_key = os.getenv('DEEPSEEK_API_KEY')
        elif config.provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
        else:
            api_key = config.api_key   # 兼容旧配置

        if not api_key:
            return JsonResponse({
                'success': False,
                'error': f'未找到 {config.provider} 的 API Key！请在 .env 文件中设置 DEEPSEEK_API_KEY'
            })

        # 获取监控数据（限制20条，节省token）
        recent_results = MonitorResult.objects.select_related('target').order_by('-timestamp')[:50]
        summary_data = []
        for r in recent_results:
            summary_data.append({
                "target": r.target.name if r.target else "系统",
                "ping": round(r.ping_time or 0, 1),
                "loss": round(r.packet_loss or 0, 1),
                "http": round(r.http_response_time or 0, 1),
                "dns": round(r.dns_resolve_time or 0, 2),
                "jitter": round(r.network_jitter or 0, 2),
                "retrans": round(r.tcp_retransmit_rate or 0, 3),
                "status": r.status,
                "time": r.timestamp.strftime("%H:%M")
            })

        data_str = json.dumps(summary_data[-20:], ensure_ascii=False, separators=(',', ':'))

        # 系统 Prompt（保持简洁，节省 token）
        system_prompt = """你是一个经验丰富的网络运维专家。请用中文生成极简诊断报告。
要求：
- 总长度严格控制在 280 字以内
- 第一行给出整体健康评分（优秀/良好/需关注/严重）
- 列出主要问题（最多3条）
- 每条问题给出1句实用解决建议
- 语气专业、直接、简洁"""

        user_prompt = f"""最近20条网络监控数据摘要：
{data_str}

请按要求生成诊断报告。"""

        # 调用 LLM
        client = OpenAI(
            api_key=api_key,
            base_url=config.base_url if config.base_url else None
        )

        response = client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=25
        )

        report = response.choices[0].message.content.strip()

        return JsonResponse({
            'success': True,
            'report': report,
            'model_used': config.model_name
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def save_ai_config(request):
    """前端保存 AI 配置（模型名称等）"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只支持 POST 请求'})

    try:
        data = json.loads(request.body)

        # 获取或创建配置
        config = AIConfig.objects.filter(is_active=True).first()
        if not config:
            config = AIConfig.objects.create(is_active=True)

        # 更新配置
        config.provider = data.get('provider', config.provider)
        config.model_name = data.get('model_name', config.model_name).strip()
        config.base_url = data.get('base_url', config.base_url).strip()
        config.temperature = float(data.get('temperature', config.temperature))
        config.max_tokens = int(data.get('max_tokens', config.max_tokens))

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