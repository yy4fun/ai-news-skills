# AI News Skills

一套面向 OpenClaw / Claude Code 的 AI 新闻自动化工作流。

> A pair of OpenClaw-compatible skills: one collects AI news from public web sources into a Feishu bitable, and the other generates daily briefs and morning guides from the collected data.

## 它能做什么

```
公开网页 ──→ 自动采集 ──→ 飞书原始新闻表 ──→ AI 筛选 ──→ 日报 & 晨间导读
         fetcher                            reporter
```

- **`ai_news_fetcher`** — 从多个公开源自动抓取 AI 新闻，写入飞书多维表格
- **`ai_news_reporter`** — 从飞书表读取新闻，AI 筛选高价值事件，生成日报

支持中文源（如 36氪、财联社）、英文源（如 Forrester）、官方博客（如 OpenAI、Anthropic）、GitHub Trending 等，可按需自行增减。详见 `references/sources.md`。

## 架构

```
┌─────────────────────────────────────────────────────────┐
│  cron 定时触发 / 飞书对话手动触发                          │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────── ai_news_fetcher ─────────────────────────┐
│                                                         │
│  curl r.jina.ai/URL          ← jina reader 转 markdown  │
│       │                                                 │
│       ▼                                                 │
│  normalize_agent_reach.py    ← 提取标题/链接/时间/摘要    │
│       │                                                 │
│       ▼                                                 │
│  build_source_items.py       ← 生成飞书入表 JSON         │
│       │                                                 │
│       ▼                                                 │
│  写入飞书多维表格（去重）                                  │
└─────────────────────────────────────────────────────────┘
                     ▼
┌─────────────── ai_news_reporter ────────────────────────┐
│                                                         │
│  按报道窗口键读取原始新闻                                  │
│       │                                                 │
│       ▼                                                 │
│  AI 筛选高价值事件 + 阅读全文                              │
│       │                                                 │
│       ▼                                                 │
│  生成日报 & 晨间导读                                      │
└─────────────────────────────────────────────────────────┘
```

## 前置依赖

| 依赖 | 用途 | 必须？ |
|---|---|---|
| [Agent Reach](https://github.com/Panniantong/Agent-Reach) | 给 AI agent 提供网页读取能力（读取 & 搜索 Twitter、Reddit、YouTube、GitHub 等） | ✅ fetcher 核心依赖 |
| Python 3.10+ | 运行 normalize / build 脚本 | ✅ |
| 飞书多维表格 | 存储原始新闻 & 日报输出 | ✅ |
| OpenClaw / Claude Code | 运行 skill、cron 调度 | ✅ |

### 关于 Agent Reach

`./install.sh` 会自动安装 Agent Reach。如果你想单独安装或在其他 AI agent 环境中使用，也可以：

**方式一**：在 AI agent（Claude Code / OpenClaw / Cursor 等）里发送：

```
帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

**方式二**：手动安装：

```bash
pip install agent-reach
agent-reach install --env=auto
agent-reach doctor    # 验证安装
```

> Agent Reach 底层使用 [jina reader](https://r.jina.ai) 将网页转为干净的 markdown（`curl r.jina.ai/URL`），这是 fetcher 采集管道的基础。

## Quick Start

### 1. 克隆仓库

```bash
git clone git@github.com:yy4fun/ai-news-skills.git
cd ai-news-skills
```

### 2. 一键安装

```bash
./install.sh
```

安装脚本会自动完成：

1. 检测并安装 [Agent Reach](https://github.com/Panniantong/Agent-Reach)（如未安装）
2. 把 `ai_news_fetcher` 和 `ai_news_reporter` 安装到 `~/.openclaw/workspace/skills/`
3. 运行 `agent-reach doctor` 验证环境

### 3. 配置飞书多维表格

```bash
# 复制示例配置
cp ~/.openclaw/workspace/skills/ai_news_fetcher/bitable_target.example.json \
   ~/.openclaw/workspace/skills/ai_news_fetcher/bitable_target.json

cp ~/.openclaw/workspace/skills/ai_news_reporter/bitable_target.example.json \
   ~/.openclaw/workspace/skills/ai_news_reporter/bitable_target.json
```

编辑 `bitable_target.json`，填入你的飞书信息：

```json
{
  "app_name": "你的应用名",
  "app_token": "你的 app_token",
  "table_name": "你的表名",
  "table_id": "你的 table_id",
  "url": "https://你的飞书域名/base/你的app_token"
}
```

### 4. 验证采集管道

不用等 cron，手动跑一次看看效果：

```bash
cd ~/.openclaw/workspace/skills/ai_news_fetcher

# 单源测试：抓取 OpenAI 新闻并解析
curl -s "https://r.jina.ai/https://openai.com/zh-Hans-CN/news/" \
  | python3 normalize_agent_reach.py --source "OpenAI新闻"

# 单源测试：GitHub Trending（无日期源，加 --fallback-to-now）
curl -s "https://r.jina.ai/https://github.com/trending?since=daily" \
  | python3 normalize_agent_reach.py --source "GitHub Trending" --fallback-to-now

# 完整管道测试（含入表 JSON 生成）
curl -s "https://r.jina.ai/https://www.cls.cn/subject/1321" \
  | python3 normalize_agent_reach.py --source "财联社-AI" \
  | python3 build_source_items.py --format bitable_records
```

输出是 JSON 格式的结构化新闻记录，包含 `title`、`url`、`date`、`summary` 等字段。

### 5. 配置 cron 定时采集

在 OpenClaw 中配置定时任务，让 fetcher 按你的节奏自动运行。建议：

- **先跑 fetcher** 采集入表
- **再跑 reporter** 生成日报

两个 skill 分开运行，不要混在一起。

## 目录结构

```
skills/
├── ai_news_fetcher/
│   ├── SKILL.md                          # skill 说明（给 AI agent 读的）
│   ├── _meta.json                        # skill 元数据
│   ├── fetcher.py                        # 源配置 & HTML 采集逻辑
│   ├── normalize_agent_reach.py          # jina markdown → 结构化记录
│   ├── build_source_items.py             # 结构化记录 → 飞书入表 JSON
│   ├── bitable_target.example.json       # 飞书配置示例
│   ├── references/
│   │   ├── sources.md                    # 新闻源清单 & 特殊规则
│   │   ├── execution.md                  # 执行流程详细说明
│   │   ├── data-model.md                 # 数据模型定义
│   │   └── gotchas.md                    # 踩坑记录
│   └── tests/
│       └── test_parse_date.py            # 时间解析测试
│
└── ai_news_reporter/
    ├── SKILL.md
    ├── _meta.json
    ├── build_daily_report.py             # 日报生成
    ├── build_event_candidates.py         # 事件筛选
    ├── build_signals.py                  # 信号提取
    ├── bitable_target.example.json
    └── references/
```

## 核心设计原则

- **原始时间保真**：`原始时间` 原样保留，`发布时间` 只在可信确认时才写入
- **采集与报告分离**：fetcher 只管抓和入表，reporter 只管读和生成
- **友好抓取**：遇到 403、验证码、登录墙就跳过，不硬刚
- **无日期源兜底**：GitHub Trending、Google Cloud 博客等无发布时间的源，使用 `--fallback-to-now` 用抓取时间代替

## 不包含的内容

公开版已做脱敏，不包含：

- 飞书真实 `app_token` / `table_id`
- 真实 `open_id` / `chat_id`
- cron 任务配置
- 运行日志和历史回执

## 添加新源

1. 在 `fetcher.py` 的 `PUBLIC_WEB_SOURCES` 列表中添加源配置
2. 在 `references/sources.md` 中记录源地址和特殊规则
3. 用管道命令手动测试：
   ```bash
   curl -s "https://r.jina.ai/新源URL" \
     | python3 normalize_agent_reach.py --source "新源名"
   ```
4. 如果新源没有发布时间，在源配置中加 `"fallback_to_now": True`，命令加 `--fallback-to-now`
5. 确认输出正常后，cron 会自动采集

## License

见 [LICENSE](LICENSE) 文件。
