# monitor/management/commands/clear_all_monitor_data.py
# # 最推荐：强制清除所有数据，但保留目标配置（下次任务会自动补默认目标）
# python manage.py clear_all_monitor_data --force --keep-targets
#
# # 如果你想连目标配置也一起删掉（完全重置）：
# # python manage.py clear_all_monitor_data --force


from django.core.management.base import BaseCommand
from monitor.models import MonitorTarget, MonitorResult, MonitoringSchedule
from logs.models import MonitorLog, AIReport

class Command(BaseCommand):
    help = '【彻底清除】清空整个系统所有采集数据（监控结果、日志、AI报告）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制执行，不询问确认',
        )
        parser.add_argument(
            '--keep-targets',
            action='store_true',
            help='保留监控目标配置（Ping、HTTP、DNS等分类的目标），只删采集数据',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        keep_targets = options.get('keep_targets', False)

        self.stdout.write(self.style.ERROR('⚠️  警告：即将彻底清除整个系统的所有采集数据！'))

        if not force:
            confirm = input('\n确定要删除所有监控数据、日志和AI报告吗？此操作不可恢复！\n请输入 "yes" 确认：')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('操作已取消。'))
                return

        deleted = {}

        # 1. 清空所有监控采集结果（最核心的数据）
        count = MonitorResult.objects.all().delete()[0]
        deleted['监控结果 (MonitorResult)'] = count

        # 2. 清空系统日志
        count = MonitorLog.objects.all().delete()[0]
        deleted['系统日志 (MonitorLog)'] = count

        # 3. 清空AI分析报告
        count = AIReport.objects.all().delete()[0]
        deleted['AI分析报告 (AIReport)'] = count

        # 4. 清空监控计划
        count = MonitoringSchedule.objects.all().delete()[0]
        deleted['监控计划 (MonitoringSchedule)'] = count

        # 5. 是否删除监控目标配置
        if not keep_targets:
            count = MonitorTarget.objects.all().delete()[0]
            deleted['监控目标配置 (MonitorTarget)'] = count
            self.stdout.write(self.style.WARNING('已删除所有监控目标配置'))
        else:
            self.stdout.write(self.style.SUCCESS('已保留监控目标配置'))

        # 输出结果
        self.stdout.write('\n✅ 清除完成！以下数据已被删除：')
        for name, num in deleted.items():
            self.stdout.write(f'   • {name}: {num} 条')

        self.stdout.write(self.style.SUCCESS('\n🎉 整个系统的采集数据已全部清空！'))

        # 自动触发一次采集，让系统立即生成新数据
        try:
            from monitor.tasks import multi_ping_task, multi_http_task, multi_dns_task, multi_tcp_retrans_task
            self.stdout.write('正在执行首次数据采集...')
            multi_ping_task()
            multi_http_task()
            multi_dns_task()
            multi_tcp_retrans_task()
            self.stdout.write(self.style.SUCCESS('首次采集完成！'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'首次采集失败（稍后会自动采集）：{e}'))