# Skill Finder — AI 项目趋势追踪站

一个公开网站，每天抓取 GitHub Trending 日/周/月榜单，过滤出 AI Agent、Skill、MCP、插件等 AI 相关项目，每期取 Star 增长 Top 10，展示真实的 1 日、7 日、30 日 Star 增长排行与 30 天趋势。

- **后端**：Python 3.11+、FastAPI、SQLAlchemy 2（异步）、asyncmy、MySQL 8.0、APScheduler、HTTPX、Scrapling
- **前端**：Vue 3、TypeScript、Vite、Pinia、Vue Router、Axios
- **测试**：pytest / pytest-asyncio / respx、Vitest / Vue Test Utils、Playwright

## 功能

- 每日用 Scrapling 抓取 `github.com/trending` 的日/周/月榜，AI 关键词过滤后每期取 Top 10（默认，可配置）
- 按 1 日增量、7 日增量、30 日增量、总 Star 排序
- 分类（Agent / Skill / MCP / 插件）、语言、最低 Star、关键词组合筛选
- 仓库详情页：分类依据、Topics、30 天 Star 趋势图
- 主页一键"刷新数据"：手动触发采集，完成后自动刷新榜单（30 分钟冷却防滥用）
- 近 30 天最热：基于 last30days 多源研究的 Agent / Skill 方向 Top 20 榜单（手动刷新 + 结果缓存）
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

全新数据库直接执行完整建表脚本：

```powershell
Get-Content backend/sql/schema.sql -Raw | mysql -u root -p skill_finder
```

> 已有旧库升级：先执行 `backend/sql/migrate-trending.sql` 新增 `trending_entries` 表；如果希望丢弃旧采集器的全量仓库数据、从趋势 Top 10 重新开始，再执行一次 `backend/sql/purge-existing-data.sql`。

### 3. 配置后端环境变量

```powershell
cd backend
Copy-Item .env.example .env
```

编辑 `.env`，至少设置：

```dotenv
DATABASE_URL=mysql+asyncmy://skill_finder:change_me@127.0.0.1:3306/skill_finder?charset=utf8mb4
ADMIN_KEY=replace_with_a_long_random_value
```

GitHub Token 保存在本地文件（不经过环境变量）：

```powershell
# 在 backend/.secrets/github_token 中粘贴你的 token（单行、无换行）
New-Item -ItemType Directory -Force -Path .secrets
Set-Content -Path .secrets\github_token -Value "ghp_your_personal_access_token" -NoNewline
```

> `.secrets/` 已被 `.gitignore` 排除，不会提交到版本库。
> 需要 GitHub Personal Access Token（至少 `public_repo` 只读权限）。
> 若想改用环境变量，也可设置 `GITHUB_TOKEN`，文件优先级更高。

### 4. 安装后端依赖并启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r <(python -c "import tomllib,sys;d=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']+[i for g in d.get('dependency-groups',{}).get('dev',[])];print('\n'.join(d))")
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

也可以直接用 pip 安装：

```powershell
.\.venv\Scripts\python.exe -m pip install "fastapi>=0.116,<1" "uvicorn[standard]>=0.35,<1" "sqlalchemy>=2.0.40,<3" "asyncmy>=0.2.10,<1" "httpx>=0.28,<1" "scrapling[fetchers]>=0.4,<1" "apscheduler>=3.11,<4" "pydantic-settings>=2.10,<3" "pytest>=8.4,<9" "pytest-asyncio>=1.1,<2" "respx>=0.22,<1" "ruff>=0.12,<1"
```

> Scrapling 的 `Fetcher`/`AsyncFetcher` 基于 curl_cffi，无需执行 `scrapling install` 下载浏览器。若本机访问 `github.com` 需要代理，在 `.env` 里设置 `TRENDING_PROXY`。

### 5. 安装前端依赖并启动

```powershell
cd frontend
npm install
npm run dev
```

访问 http://localhost:10002

### 6. 手动触发首次采集

```powershell
$headers = @{ "X-Admin-Key" = "replace_with_your_admin_key" }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/admin/collections" -Headers $headers
```

返回 `202` 表示已接受，采集在后台执行。采集会抓取 GitHub Trending 日/周/月三张榜并写入当期 Top 10，日/周/月增量来自榜单本身的期内涨星数，首次采集即可展示。

## API

统一前缀 `/api/v1`，统一错误响应 `{ "code", "message", "request_id" }`。

| 接口 | 说明 |
| --- | --- |
| `GET /health` | 应用状态 |
| `GET /repositories` | 排行榜，支持 `page`、`page_size`、`sort`（`daily_stars` / `weekly_stars` / `monthly_stars` / `total_stars`）、`category`（`AGENT` / `SKILL` / `MCP` / `PLUGIN`）、`language`、`min_stars`、`q` |
| `GET /repositories/{owner}/{name}` | 仓库详情 + 30 天趋势 |
| `GET /languages` | 可筛选语言及仓库数 |
| `GET /stats` | 统计信息 |
| `POST /collections/refresh` | 手动触发采集（公开，30 分钟冷却；采集中重复触发返回 409） |
| `GET /last30days/rankings?direction=agent\|skill` | 近 30 天最热榜单缓存（Agent / Skill 方向 Top 20） |
| `POST /last30days/rankings/refresh` | 手动刷新指定方向榜单（同步执行，可能需要几分钟） |
| `GET /last30days/status` | last30days 引擎诊断与可用来源 |
| `POST /last30days` | 自由主题研究（调试用，页面不再使用） |
| `POST /admin/collections` | 手动触发采集（需 `X-Admin-Key`） |

> 首次使用近 30 天最热功能前，需重新执行一次最新的 `backend/sql/schema.sql`（新增 `last30days_reports` 表；只建新表，不影响既有数据）。

## 运行测试

### 后端

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

> **警告**：MySQL 集成测试的 fixture 会 **DROP 并重建全部数据表**。必须使用**独立测试库**，严禁指向生产库（如 `skill_finder`）。
>
> 先创建测试库并执行建表脚本，再设置 `TEST_DATABASE_URL`：
>
> ```powershell
> mysql -u root -p -e "CREATE DATABASE skill_finder_test CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
> Get-Content backend/sql/schema.sql -Raw | mysql -u root -p skill_finder_test
> $env:TEST_DATABASE_URL = "mysql+asyncmy://user:pass@127.0.0.1:3306/skill_finder_test?charset=utf8mb4"
> .\.venv\Scripts\python.exe -m pytest tests/integration -q
> ```
>
> 未设置 `TEST_DATABASE_URL` 时集成测试明确跳过，不触碰任何数据库。

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

默认每天北京时间 02:00 自动采集（`COLLECTION_CRON=0 2 * * *`，`SCHEDULER_ENABLED=false` 时关闭）。每次采集流程：

1. 用 Scrapling 抓取 `github.com/trending?since=daily|weekly|monthly` 三张榜（支持 `TRENDING_PROXY`）。
2. 按 `TRENDING_AI_KEYWORDS` 过滤（不区分大小写、按词边界匹配名称与描述）。
3. 每期按期内涨星降序取前 `TRENDING_TOP_N`（默认 10），三张榜合并去重。
4. 用 GitHub API 逐个补全 github_id、topics、forks 等字段（每期约 10 个请求，token 消耗很小）。
5. 写入 `repositories`、当日 `star_snapshots` 与 `trending_entries`；某期抓取失败时保留该期旧数据并标记任务为 `PARTIAL`。

自动与手动任务共享同一把 MySQL 命名锁，并发触发只执行一个任务。掉出榜单的仓库仍保留在列表底部（增量显示 `--`），按总 Star 排序时仍可查看。

## 目录结构

```text
backend/            FastAPI 后端（Trending 采集、趋势计算、REST API）
  sql/schema.sql             MySQL 建表脚本（含 trending_entries）
  sql/migrate-trending.sql   旧库升级：新增 trending_entries 表
  sql/purge-existing-data.sql 可选：清空旧全量采集数据
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
