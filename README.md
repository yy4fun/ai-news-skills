# AI News Skills

一套面向 OpenClaw / Claude Code 的 AI 新闻自动化工作流。

> A pair of OpenClaw-compatible skills: one collects AI news from public web sources into a Feishu bitable, and the other generates daily briefs and morning guides from the collected data.

## 它能做什么

```
公开网页 ──→ 自动采集 ──→ 飞书原始新闻表 ──→ AI 筛选 ──→ 日报 & 晨间导读
         fetcher                            reporter
```

- **`ai_news_fetcher`** — 从 12 个公开源自动抓取 AI 新闻，写入飞书多维表格
- **`ai_news_reporter`** — 从飞书表读取新闻，AI 筛选高价值事件，生成日报

### 已接入的新闻源

| 源 | 类型 | 说明 |
|---|---|---|
| 财联社-AI | 中文 | 金融科技视角 |
| 36氪-AI / 36氪快讯 | 中文 | 创投视角 |
| Readhub-AI | 中文 | 聚合 |
| OpenAI 新闻 | 官方 | 产品/研究/安全动态 |
| Anthropic 新闻 | 官方 | 产品/研究/政策动态 |
| GitHub Trending | 代码 | 每日热门 AI 项目（关键词过滤） |
| Google Cloud 博客 | 官方 | 云 AI 产品更新 |
| Forrester 博客 | 英文 | 行业分析 |
| CMSWire | 英文 | 企业技术 |
| CX Today | 英文 | 客户体验/AI |

> Google DeepMind 博客已注册但暂停（jina reader 无法提取标题/日期，需 browser 模式）

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
| [jina reader](https://r.jina.ai) | 将网页转为干净的 markdown（通过 `curl r.jina.ai/URL` 调用） | ✅ fetcher 核心依赖 |
| Python 3.10+ | 运行 normalize / build 脚本 | ✅ |
| 飞书多维表格 | 存储原始新闻 & 日报输出 | ✅ |
| OpenClaw / Claude Code | 运行 skill、cron 调度 | ✅ |

### 验证 jina reader 是否可用

```bash
# 随便抓一个页面试试，能看到 markdown 输出就 OK
curl -s "https://r.jina.ai/https://openai.com/zh-Hans-CN/news/" | head -50
```

如果能看到 markdown 格式的网页内容，说明 jina reader 正常工作。这就是 fetcher 的 "agent-reach" 读取层——不需要额外安装任何包。

## Quick Start

### 1. 克隆仓库

```bash
git clone git@github.com:yy4fun/ai-news-skills.git
cd ai-news-skills
```

### 2. 安装 skills

```bash
./install.sh
```

会把 `ai_news_fetcher` 和 `ai_news_reporter` 安装到 `~/.openclaw/workspace/skills/`。

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
