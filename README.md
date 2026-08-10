# Skill Finder — AI 项目趋势追踪站

一个公开网站，每天自动发现并追踪 GitHub 上与 AI Agent、Agent Skill 和 MCP 相关的高 Star 开源仓库，提供真实的 1 日、7 日 Star 增长排行与 30 天趋势。

- **后端**：Python 3.11+、FastAPI、SQLAlchemy 2（异步）、asyncmy、MySQL 8.0、APScheduler、HTTPX
- **前端**：Vue 3、TypeScript、Vite、Pinia、Vue Router、Axios
- **测试**：pytest / pytest-asyncio / respx、Vitest / Vue Test Utils、Playwright

## 功能

- 每日自动发现（关键词 + Topic 搜索）并持续追踪已收录仓库
- 按 1 日增量、7 日增量、总 Star 排序
- 分类（Agent / Skill / MCP）、语言、最低 Star、关键词组合筛选
- 仓库详情页：分类依据、Topics、30 天 Star 趋势图
- 明暗主题、响应式布局、键盘与无障碍支持
- 手动触发采集接口，MySQL 命名锁防并发

## 环境要求

- MySQL 5.5+（`backend/sql/schema.sql` 为兼容 5.5 的语法；计划目标为 MySQL 8.0，迁移到 8.0 时可将 `TEXT` 类 JSON 列与排序规则按需升级）
- Python 3.11+（计划默认 3.12，本机已验证 3.11）
- Node.js 18+

## 从零启动

### 1. 安装 MySQL 8.0 并创建数据库

```sql
CREATE DATABASE skill_finder CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'skill_finder'@'localhost' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON skill_finder.* TO 'skill_finder'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 执行建表脚本

```powershell
Get-Content backend/sql/schema.sql -Raw | mysql -u root -p skill_finder
```

### 3. 配置后端环境变量

```powershell
cd backend
Copy-Item .env.example .env
```

编辑 `.env`，至少设置：

```dotenv
DATABASE_URL=mysql+asyncmy://skill_finder:change_me@127.0.0.1:3306/skill_finder?charset=utf8mb4
GITHUB_TOKEN=ghp_your_personal_access_token
ADMIN_KEY=replace_with_a_long_random_value
```

> 需要 GitHub Personal Access Token（至少 `public_repo` 只读权限）。

### 4. 安装后端依赖并启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r <(python -c "import tomllib,sys;d=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']+[i for g in d.get('dependency-groups',{}).get('dev',[])];print('\n'.join(d))")
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

也可以直接用 pip 安装：

```powershell
.\.venv\Scripts\python.exe -m pip install "fastapi>=0.116,<1" "uvicorn[standard]>=0.35,<1" "sqlalchemy>=2.0.40,<3" "asyncmy>=0.2.10,<1" "httpx>=0.28,<1" "apscheduler>=3.11,<4" "pydantic-settings>=2.10,<3" "pytest>=8.4,<9" "pytest-asyncio>=1.1,<2" "respx>=0.22,<1" "ruff>=0.12,<1"
```

### 5. 安装前端依赖并启动

```powershell
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 6. 手动触发首次采集

```powershell
$headers = @{ "X-Admin-Key" = "replace_with_your_admin_key" }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/admin/collections" -Headers $headers
```

返回 `202` 表示已接受，采集在后台执行。首次采集只建立基线，首页仓库的 1 日/7 日增量显示 `--`；第二个自然日采集后显示真实增量。

## API

统一前缀 `/api/v1`，统一错误响应 `{ "code", "message", "request_id" }`。

| 接口 | 说明 |
| --- | --- |
| `GET /health` | 应用状态 |
| `GET /repositories` | 排行榜，支持 `page`、`page_size`、`sort`、`category`、`language`、`min_stars`、`q` |
| `GET /repositories/{owner}/{name}` | 仓库详情 + 30 天趋势 |
| `GET /languages` | 可筛选语言及仓库数 |
| `GET /stats` | 统计信息 |
| `POST /admin/collections` | 手动触发采集（需 `X-Admin-Key`） |

## 运行测试

### 后端

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

> MySQL 集成测试需要设置 `TEST_DATABASE_URL`（如 `mysql+asyncmy://user:pass@127.0.0.1:3306/skill_finder_test?charset=utf8mb4`），未设置时这些测试明确跳过。

### 前端

```powershell
cd frontend
npm run lint
npm run typecheck
npm run test -- --run
npm run build
npm run test:e2e   # 需要先安装 Chromium：npx playwright install chromium
```

## 采集任务

默认每天北京时间 02:00 自动采集（`COLLECTION_CRON=0 2 * * *`，`SCHEDULER_ENABLED=false` 时关闭）。自动与手动任务共享同一把 MySQL 命名锁，并发触发只执行一个任务。

## 目录结构

```text
backend/            FastAPI 后端（采集、趋势计算、REST API）
  sql/schema.sql    MySQL 8.0 建表脚本
  app/              应用源码
  tests/            测试
frontend/           Vue 3 前端（排行榜、筛选、详情）
  tests/unit/       Vitest 单元测试
  tests/e2e/        Playwright 端到端测试
docs/               设计说明与实施计划
```

## 安全说明

- 所有密钥仅通过环境变量读取，`.env` 不提交版本库
- 源码与日志中的凭据均已脱敏
- 前端不持有 GitHub Token 或管理密钥
