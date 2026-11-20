# HirePilot — AI 招聘运营自动化 Agent 平台

Human-in-the-loop 的招聘自动化：Agent 筛简历、打分、生成个性化话术、经人工审核后触达候选人，
自动回答常见问题，敏感话题转人工。Java/Spring Boot 业务后台 + Python/Playwright 执行器 +
LLM 评估闭环 + 视觉 Agent 降级路线。

> 合规声明：本仓库所有演示均针对自建 Mock 招聘站（mock-site/）。
> 对真实招聘平台的生产化必须使用官方 API 或获得授权的 RPA，遵守平台协议。
> 简历数据为虚构人物，仅用于演示与评测。

## 架构

```
Spring Boot 3 (:8080)  <-REST->  Python Agent Worker  <-Playwright->  Mock 招聘站 (:9000)
  职位/候选人/审核队列            评估+触达+应答状态机                 动态DOM/抖动/模拟回复
  PostgreSQL / H2                LLM: OpenAI兼容(可离线Mock)
```

详见 docs/产品设计方案.md 与 docs/技术实现方案.md。

## 快速开始

### 0. 依赖
- Python 3.12+：pip install -r worker/requirements.txt 然后 playwright install chromium
- Docker（跑 Java 后台用；不装也能玩 standalone 模式）

### 0.5 Web 界面（推荐日常使用）

三个服务就绪后（后台容器 + Mock站 + Worker守护），浏览器打开 **http://127.0.0.1:8080** ：

    docker run -d --name hirepilot-backend -p 8080:8080 hirepilot-backend
    python mock-site/app.py
    python worker/main.py --serve        # 守护模式：接收页面按钮派发的任务

页面操作闭环：
1. 右上「＋ 新职位」填 JD/硬条件/FAQ 知识库（或直接用种子职位）
2. 点「筛选简历」→ Agent 后台执行，审核队列实时出现卡片（评分+理由+风险+拟发送话术）
3. 逐条审批：话术可改写后「批准」，或「否决」
4. 点「执行触达与回复」→ 自动发送+FAQ应答+约面/转人工
5. 「候选人」页点行看详情：技能 chips、评分理由、简历原文、带意图标注的聊天记录
6. 「运行记录」看每次任务统计；「重置」清空本职位重来

Worker 在线状态见侧边栏底部指示灯；离线时运行按钮禁用并提示启动命令。

前端为 **Vue 3 + Vite + Element Plus** 单页应用（`frontend/`），构建产物落在
`backend/src/main/resources/static/`，由 Spring Boot 同源 serving，无需额外前端服务器：

    cd frontend
    npm install
    npm run build        # 产物 -> backend 静态资源；随后重建后端镜像即可
    npm run dev          # 可选：开发模式 :5173，/api 自动代理到 :8080（热更新）

注意：`mock-site/`（:9000）是 Agent 扫描用的模拟第三方招聘站，刻意保持简陋与动态 DOM，
不属于产品界面，请勿将其与控制台（:8080）混淆。
界面截图见 docs/ui-1-reviews.png ~ ui-4-runs.png；UI 自动化验收脚本 scripts/ui_test.py、scripts/ui_screenshot.py。
### 1. 起 Mock 招聘站
    python mock-site/app.py        # http://127.0.0.1:9000

### 2. 离线演示（无需 Java / 无需 LLM Key）
    python worker/main.py --job 1 --auto-approve --standalone --fresh   # 第一轮：筛选+触达+FAQ
    python worker/main.py --job 1 --auto-approve --standalone           # 第二轮：约面意向->INTERVIEW

运行报告落在 worker/out/run-*.json。--auto-approve 仅演示用，模拟 HR 秒批。

### 3. 完整模式（Java 后台 + 人工审核）
    docker build -t hirepilot-backend backend/
    docker run -d --name hirepilot-backend -p 8080:8080 hirepilot-backend   # H2 开发库
    # 或 docker compose up -d                                              # PostgreSQL（需能拉镜像）

    python worker/main.py --job 1 --fresh        # 阶段1：发现+评估 -> 6 条待审核
    # HR 审核（API 或任意 REST 客户端）：
    #   GET  /api/reviews?decision=PENDING
    #   POST /api/reviews/{id}/approve   POST /api/reviews/{id}/reject
    python worker/main.py --job 1                # 阶段2：触达已批准 + FAQ 应答
    python worker/main.py --job 1                # 阶段3：二轮回复 -> 约面 INTERVIEW
    # 看板：GET /api/dashboard?jobId=1

### 4. 接入真实大模型（可选）
    $env:LLM_API_KEY="sk-..."     # DashScope/OpenAI/任意兼容服务
    $env:LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
    $env:LLM_MODEL="qwen-plus"; $env:VLM_MODEL="qwen-vl-max"   # VLM 用于视觉降级路线

无 Key 时自动使用确定性 MockLLM；API 调用失败逐次降级 Mock，流程不中断。
密钥写入项目根 .env（已 gitignore）。注意：百炼 Token Plan/Coding Plan 密钥按官方条款仅限
Claude Code/Codex 等 AI 工具交互式使用，不能用于后端服务；生产部署请换按量付费 API Key。

### 5. 评测回归
    python worker/eval/run_eval.py    # shortlist 准确率 / 硬条件误放行(红线=0) / 分数MAE

### 6. 重开一局

    Invoke-RestMethod -Method Post http://127.0.0.1:9000/api/reset   # 清Mock站聊天记录
    python worker/main.py --job 1 --fresh --reset                   # 清后台数据+断点，从头跑

--fresh 只清 Worker 本地断点；--reset 才清后台候选人/审核/消息（开发端点 /api/dev/reset，生产应禁用）。
后台已处理过的候选人自动跳过（skipped_existing），不会重复送审触发 409。
## 已验证的稳定性特性（E2E 实测）

| 特性 | 验证方式 | 结果 |
|---|---|---|
| 语义选择器抗混淆 | Mock 站 class 随机后缀 | 通过：全程未用 class 定位 |
| 三级降级抽取 | c007 混淆简历页 | 通过：DOM->打印版路线成功 |
| 重试+幂等 | 发送接口 20% 503 | 通过：重试后不重发（内容hash幂等） |
| 断点续跑 | 二次运行不加 --fresh | 通过：已处理候选人跳过，消息游标续读 |
| 硬条件护栏 | 年限/学历/必备技能规则 | 通过：4 人拒绝，误放行 0 |
| Human-in-the-loop | 未批准不触达；拒绝即 CLOSED | 通过 |
| 敏感转人工 | "35K不然免谈" | 通过：SENSITIVE->ESCALATED |
| 失败留证 | StepFailure 截图+HTML快照 | 通过：worker/out/incidents/ |
| 状态机校验 | 非法迁移 409 | 通过：Spring 侧 TRANSITIONS 表 |

## 目录

    backend/    Spring Boot 3 (Java 17)：domain/repo/service/api，H2开发/PostgreSQL生产
    worker/     Python Agent：pipeline/browser/visual_agent/llm/stability/backend_client
      eval/     标注评估集 + 回归脚本
    mock-site/  FastAPI 模拟招聘站（脏特性替身）
    docs/       产品设计 / 技术实现方案
    scripts/    dev.ps1 一键起 Mock站+Worker

## 路线图
P1：看板 UI、Redis 队列、worker 鉴权、钉钉告警、桌面 RPA 执行器。
P2：移动端(ADB/Appium)、选择器自愈、多模型评估对比、约面日历集成。