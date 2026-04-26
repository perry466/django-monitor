# BookerTao MONITOR - 网络监控系统

https://img.shields.io/badge/Django-6.0.4-green.svg
https://img.shields.io/badge/Python-3.8+-blue.svg
https://img.shields.io/badge/License-MIT-yellow.svg

一个功能完善的**企业级网络监控系统**，支持多目标实时监控、AI智能分析、可视化仪表盘等功能。

## ✨ 核心特性

- **多维度网络监控**
  - Ping延迟 & 丢包率监控
  - HTTP响应时间监控
  - DNS解析时间监控
  - 网络抖动(Jitter)监控
  - TCP重传率监控
- **AI智能分析**
  - 自动生成网络诊断报告
  - 支持DeepSeek、通义千问、OpenAI等多种AI模型
  - 智能健康评分（优秀/良好/需关注/严重）
- **多目标管理**
  - 灵活配置监控目标（支持IP、域名、URL）
  - 分类管理（ping/http/dns/jitter）
  - 实时启用/禁用监控目标
- **可视化仪表盘**
  - 实时系统资源监控（内存、磁盘、网络）
  - 历史数据趋势图表
  - 系统日志查看与导出
- **用户认证系统**
  - 用户注册/登录/登出
  - 会话管理

## 🛠 技术栈

| 技术        | 版本   | 用途         |
| :---------- | :----- | :----------- |
| Django      | 6.0.4  | Web框架      |
| MySQL       | 8.0+   | 数据库       |
| APScheduler | 3.11.2 | 定时任务调度 |
| OpenAI      | 2.31.0 | AI接口调用   |
| Chart.js    | 4.4.1  | 数据可视化   |
| TailwindCSS | -      | 前端样式     |

## 📦 安装部署

### 1. 环境要求

- Python >= 3.8
- MySQL >= 8.0
- pip

### 2. 克隆项目

bash

```
git clone https://github.com/your-repo/django-monitor.git
cd django-monitor
```



### 3. 创建虚拟环境

bash

```
# Windows
python -m venv ll_env
ll_env\Scripts\activate

# Linux/Mac
python3 -m venv ll_env
source ll_env/bin/activate
```



### 4. 安装依赖

bash

```
pip install -r requirements.txt
```



### 5. 数据库配置

创建MySQL数据库：

sql

```
CREATE DATABASE network_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```



修改 `djangoproject/settings.py` 中的数据库配置：

python

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'network_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```



### 6. 环境变量配置

复制 `.env` 文件并配置API密钥：

bash

```
# .env
DEEPSEEK_API_KEY=your_deepseek_api_key
# OPENAI_API_KEY=your_openai_api_key
# DASHSCOPE_API_KEY=your_dashscope_api_key
```



### 7. 数据库迁移

bash

```
python manage.py makemigrations
python manage.py migrate
```



### 8. 创建超级管理员

bash

```
python manage.py createsuperuser
```



### 9. 启动服务

bash

```
python manage.py runserver 0.0.0.0:8000
```



访问 [http://localhost:8000](http://localhost:8000/)

## 🚀 使用指南

### 默认监控目标

系统首次启动会自动创建以下默认监控目标：

| 分类 | 目标地址                                          | 名称       |
| :--- | :------------------------------------------------ | :--------- |
| Ping | 8.8.8.8                                           | Google DNS |
| Ping | 1.1.1.1                                           | Cloudflare |
| Ping | [baidu.com](https://baidu.com/)                   | 百度       |
| HTTP | [https://www.google.com](https://www.google.com/) | Google     |
| HTTP | [https://www.baidu.com](https://www.baidu.com/)   | Baidu      |
| DNS  | [google.com](https://google.com/)                 | Google     |
| DNS  | [cloudflare.com](https://cloudflare.com/)         | Cloudflare |

### 配置监控目标

1. 登录系统（首次使用需注册账号）
2. 点击侧边栏「多目标监控配置」
3. 选择监控类型（Ping/HTTP/抖动/DNS）
4. 填写目标名称和地址
5. 保存配置

### 查看监控数据

- **延迟测试**: `/monitor/ping/` - 查看各目标Ping延迟
- **丢包率测试**: `/monitor/loss/` - 查看丢包率统计
- **HTTP响应时间**: `/monitor/http-response/`
- **网络抖动**: `/monitor/jitter/`
- **DNS解析时间**: `/monitor/dns/`
- **TCP重传率**: `/monitor/tcp-retrans/`

### AI智能分析

1. 点击侧边栏「小树智能分析」
2. 选择「分析监控数据」或「分析系统日志」
3. 等待AI生成诊断报告
4. 查看健康评分和改进建议

### 定时任务

系统使用APScheduler自动执行监控任务：

- **执行频率**: 每分钟
- **监控项目**: Ping + Jitter、HTTP、DNS、TCP重传率
- **时区**: Asia/Shanghai

## 📁 项目结构

text

```
django-monitor/
├── accounts/          # 用户认证模块
│   ├── forms.py       # 注册表单
│   ├── models.py      # 用户资料模型
│   └── views.py       # 登录/注册视图
├── monitor/           # 核心监控模块
│   ├── api.py         # REST API接口
│   ├── monitoring.py  # 监控功能实现
│   ├── tasks.py       # 定时任务调度
│   └── models.py      # 监控目标/结果模型
├── logs/              # 日志与AI模块
│   ├── models.py      # 日志/AI配置/报告模型
│   └── views.py       # AI分析、日志导出
├── targets/           # 目标配置模块
│   └── views.py       # 多目标配置管理
├── templates/         # HTML模板
│   ├── base.html      # 基础模板
│   ├── monitor/       # 监控页面
│   ├── logs/          # 日志和AI页面
│   └── accounts/      # 登录注册页面
└── djangoproject/     # 项目配置
    ├── settings.py    # Django配置
    └── urls.py        # URL路由
```



## 🔧 API接口

| 接口                              | 方法 | 说明                   |
| :-------------------------------- | :--- | :--------------------- |
| `/monitor/api/multi-ping/`        | GET  | 获取多目标Ping数据     |
| `/monitor/api/multi-http/`        | GET  | 获取多目标HTTP响应时间 |
| `/monitor/api/multi-dns/`         | GET  | 获取多目标DNS解析时间  |
| `/monitor/api/multi-jitter/`      | GET  | 获取网络抖动数据       |
| `/monitor/api/multi-loss/`        | GET  | 获取丢包率数据         |
| `/monitor/api/multi-tcp-retrans/` | GET  | 获取TCP重传率          |
| `/monitor/api/system/`            | GET  | 获取系统资源信息       |
| `/logs/api/ai-report/`            | POST | 生成AI监控报告         |
| `/logs/api/ai-analyze-logs/`      | POST | 生成AI日志分析         |
| `/logs/api/system-logs/`          | GET  | 获取系统日志           |

## 🧪 测试

bash

```
# 运行所有测试
python manage.py test

# 测试特定模块
python manage.py test monitor
python manage.py test logs
```



## 📊 数据清理

系统提供了数据清理命令：

bash

```
# 清空所有采集数据，保留目标配置
python manage.py clear_all_monitor_data --force --keep-targets

# 完全重置（删除所有数据和目标配置）
python manage.py clear_all_monitor_data --force
```



## ⚙️ 配置说明

### AI模型配置

支持以下AI提供商：

| 提供商   | 默认模型                | 环境变量          |
| :------- | :---------------------- | :---------------- |
| DeepSeek | deepseek-chat           | DEEPSEEK_API_KEY  |
| 通义千问 | qwen-plus               | DASHSCOPE_API_KEY |
| OpenAI   | gpt-4o-mini             | OPENAI_API_KEY    |
| Groq     | llama-3.3-70b-versatile | GROQ_API_KEY      |

### 监控阈值参考

| 指标      | 优秀    | 警告       | 严重     |
| :-------- | :------ | :--------- | :------- |
| Ping延迟  | < 50ms  | 50-150ms   | > 150ms  |
| 丢包率    | < 1%    | 1-5%       | > 5%     |
| HTTP响应  | < 500ms | 500-2000ms | > 2000ms |
| 网络抖动  | < 10ms  | 10-25ms    | > 25ms   |
| TCP重传率 | < 0.5%  | 0.5-2%     | > 2%     |

## ❓ 常见问题

### Q: 定时任务没有执行？

检查APScheduler是否正常启动。查看控制台输出是否有：

text

```
✅ APScheduler 已成功启动（时区：Asia/Shanghai）
```



### Q: AI分析失败？

1. 检查API Key是否正确配置
2. 确认网络可以访问AI服务
3. 查看后台错误日志

### Q: 监控数据显示异常？

1. 确认MySQL数据库连接正常
2. 检查定时任务是否在执行
3. 使用 `python manage.py clear_all_monitor_data --keep-targets` 清理数据后重启

## 📝 更新日志

### v1.0.0 (2026-04-26)

- ✅ 完整的多目标网络监控功能
- ✅ AI智能分析与报告生成
- ✅ 用户认证系统
- ✅ 系统日志查看与导出
- ✅ 响应式Web界面
- ✅ 实时系统资源监控

## 👨‍💻 作者

**Booker Tao** - [GitHub](https://github.com/bookertao)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](https://license/) 文件

------

*如有问题或建议，欢迎提Issue或Pull Request* ❤️