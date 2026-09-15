# OPS Admin - 运维管理后台系统

一个现代化的企业级运维管理后台系统，提供服务器监控、告警管理、任务调度等功能。

## 🛠 技术栈

### Frontend
- **框架**: React 18 + Next.js 14
- **UI 组件库**: HeroUI
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **图表**: Recharts
- **图标**: Lucide React

### Backend
- **框架**: Django 4.2 + Django REST Framework
- **认证**: JWT (PyJWT)
- **数据库**: MySQL 8.0
- **服务器**: Gunicorn

### Infrastructure
- **容器化**: Docker + Docker Compose
- **数据持久化**: Docker Volumes

## 🚀 启动指南 (How to Run)

1. 确保 Docker Desktop 已启动
2. 在根目录执行：
   ```bash
   docker compose up --build
   ```
3. 等待容器启动完成（首次构建约需 3-5 分钟）

## 🔗 服务地址 (Services)

| 服务 | 地址 |
|------|------|
| 前端应用 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin |
| MySQL | localhost:3306 |

## 🧪 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

## ✨ 核心功能

### 1. 用户认证
- JWT Token 认证
- 登录/登出功能
- 会话持久化

### 2. 仪表盘
- 服务器状态概览
- 资源使用率统计（CPU/内存/磁盘）
- 实时图表展示
- 告警和任务快览

### 3. 登录验证码（验证码开关）
- **验证码总开关**：运维配置，关闭后任何情况都不要求验证码
- **默认不强制**：同一账号连续登录失败达到阈值（默认 3 次）后，登录页才显示验证码输入框
- **错误区分提示**：验证码错误（`CAPTCHA_INVALID`）与账号密码错误（`BAD_CREDENTIALS`）分别提示、不同样式
- **后端临时码**：SVG 图片验证码，一次性使用、5 分钟有效、点击可刷新
- **登录成功即清零**失败计数；管理员可在仪表盘「登录安全设置」中开关验证码、调整阈值、清空失败计数

## 📁 项目结构

```
taskId1016/
├── docker-compose.yml      # Docker 编排配置
├── README.md               # 项目说明文档
├── .gitignore              # Git 忽略配置
├── .dockerignore           # Docker 忽略配置
├── database/
│   └── init.sql            # 数据库初始化脚本
├── backend/                # Django 后端
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── entrypoint.sh
│   ├── ops_admin/          # Django 项目配置
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── api/                # API 应用
│       ├── models.py       # 数据模型
│       ├── views.py        # 视图
│       ├── serializers.py  # 序列化器
│       ├── urls.py         # 路由
│       ├── captcha.py      # 登录验证码（开关/阈值/生成/校验）
│       └── authentication.py # JWT 认证
├── scripts/
│   └── demo_captcha.sh     # 验证码流程一键演示脚本
└── frontend/               # Next.js 前端
    ├── Dockerfile
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    └── src/
        ├── app/            # Next.js App Router
        │   ├── login/      # 登录页面（含验证码输入）
        │   └── dashboard/  # 仪表盘页面（含登录安全设置）
        ├── components/     # React 组件
        ├── lib/            # 工具库
        ├── store/          # 状态管理
        └── types/          # TypeScript 类型
```

## 🗄️ 数据库设计

### Users (用户表)
- Django 内置用户模型

### Servers (服务器表)
- 服务器基本信息
- 状态和资源使用率

### Alerts (告警表)
- 告警信息
- 级别和状态

### Tasks (任务表)
- 任务信息
- 优先级和分配

### OperationLogs (操作日志表)
- 系统操作记录

### SystemConfig (系统配置表)
- 键值对配置，存储验证码开关（`captcha_enabled`）与失败阈值（`captcha_fail_threshold`）

### LoginFailRecord (登录失败记录表)
- 按用户名统计连续失败次数，登录成功即清零

### CaptchaRecord (验证码表)
- 后端生成的临时码：captcha_id、过期时间、一次性使用标记

## 🔐 登录验证码说明

### 触发流程
1. 默认不强制验证码，直接账号密码登录
2. 同一账号连续失败达到阈值（默认 3 次）→ 登录页自动出现验证码输入框
3. 此后必须先通过验证码校验，再校验账号密码
4. 登录成功 → 失败计数清零，验证码输入框消失

### 错误区分
| 场景 | HTTP | error 码 | 提示语 | 前端样式 |
|------|------|----------|--------|----------|
| 未填验证码 | 400 | `CAPTCHA_REQUIRED` | 请先获取并填写验证码 | 橙色警告 |
| 验证码错误/过期 | 400 | `CAPTCHA_INVALID` | 验证码错误或已过期 | 橙色警告 |
| 账号密码错误 | 401 | `BAD_CREDENTIALS` | 用户名或密码错误 | 红色错误 |

### 验证码相关 API
| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/auth/captcha/` | 公开 | 获取验证码图片（captcha_id + SVG data URI） |
| GET | `/api/auth/login-state/?username=x` | 公开 | 查询某账号是否需要验证码 |
| GET | `/api/auth/captcha/config/` | 公开 | 查看验证码开关与阈值 |
| POST | `/api/auth/captcha/config/` | 管理员 | 修改开关 / 阈值（1-10） |
| POST | `/api/auth/captcha/reset-fails/` | 管理员 | 清空所有登录失败计数 |

登录接口 `/api/auth/login/` 在需要验证码时额外接收 `captcha_id`、`captcha_code` 字段。

### 生产化建议（当前为可本地演示的实现）
- 失败计数 / 验证码目前存于业务库，高并发场景建议迁移到 Redis 并增加 IP 维度限流
- SVG 验证码字符可被源码解析（演示脚本即如此），生产建议替换为扭曲位图或第三方验证码服务
- 建议补充：账号锁定策略、验证码接口限流、审计告警

## 🔧 开发说明

### 本地开发（非 Docker）

**后端**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

**前端**:
```bash
cd frontend
npm install
npm run dev
```

### 本地快速演示（SQLite，无需 MySQL）

仅演示登录验证码流程时，可用 SQLite 一键启动，无需 MySQL / Docker：

```bash
cd backend
pip install Django==4.2.9 djangorestframework==3.14.0 django-cors-headers==4.3.1 PyJWT==2.8.0
export USE_SQLITE=true
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
U.objects.filter(username='admin').exists() or U.objects.create_superuser('admin', 'admin@ops.local', 'admin123')
"
python manage.py runserver 8000
```

然后任选其一体验：
- **命令行一键演示**：`./scripts/demo_captcha.sh`（自动走完整流程：失败触发 → 验证码错误/密码错误区分 → 登录成功清零 → 开关关闭/恢复）
- **页面体验**：另开终端 `cd frontend && npm install --legacy-peer-deps && npm run dev`，访问 http://localhost:3000 ，用错误密码连续登录 3 次

### 环境变量

后端环境变量（docker-compose.yml 中配置）:
- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口
- `DB_NAME`: 数据库名称
- `DB_USER`: 数据库用户
- `DB_PASSWORD`: 数据库密码
- `SECRET_KEY`: Django 密钥
- `USE_SQLITE`: 设为 `true` 时使用 SQLite（仅本地演示，无需 MySQL）

前端环境变量:
- `NEXT_PUBLIC_API_URL`: 后端 API 地址

## 🐳 Docker 配置说明

- **MySQL**: 持久化存储，数据保存在 `mysql_data` 卷，UTF8MB4 编码
- **Backend**: Django + Gunicorn，端口 8000
- **Frontend**: Next.js Standalone，端口 3000

## 🎨 UI 特性

- 响应式布局，适配桌面和移动端
- 现代化渐变背景和卡片设计
- 流畅的动画过渡效果
- 完善的加载状态和错误提示
- Toast 消息通知

## 📄 License

MIT License
