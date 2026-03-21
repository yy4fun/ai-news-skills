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

复制下面这句话发给你的 AI agent（Claude Code / OpenClaw / Cursor 等）：

```
帮我安装 AI News Skills：https://raw.githubusercontent.com/yy4fun/ai-news-skills/main/docs/install.md
```

agent 会自动完成所有安装和配置，装完让你填飞书表信息就行。

### 分步安装

如果你想分开装，也是发给 agent：

```
帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

```
帮我安装 AI News Skills：https://raw.githubusercontent.com/yy4fun/ai-news-skills/main/docs/install.md
```

## 效果示例

### 采集输出（ai_news_fetcher）

fetcher 采集后输出结构化 JSON，每条新闻包含标题、链接、时间、来源：

```json
{
  "fetched_at": "2026-03-21T04:01:47Z",
  "articles": [
    {
      "title": "我们如何监控内部编程智能体的对齐失范",
      "url": "https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment/",
      "date": "2026年3月19日",
      "summary": null,
      "source": "OpenAI新闻",
      "parsed_date": "2026-03-18T16:00:00Z"
    },
    {
      "title": "GPT-5.4 mini 与 nano 正式发布",
      "url": "https://openai.com/zh-Hans-CN/index/introducing-gpt-5-4-mini-and-nano/",
      "date": "2026年3月17日",
      "summary": null,
      "source": "OpenAI新闻",
      "parsed_date": "2026-03-16T16:00:00Z"
    }
  ],
  "total": 9,
  "source_group": "public-web"
}
```

写入飞书多维表格后，每条记录自动生成标题哈希、报道窗口键等字段，用于去重和后续日报生成。

### 日报输出（ai_news_reporter）

reporter 从原始新闻表筛选高价值事件，生成 signal 风格的日报：

```markdown
# AI日报｜2026-03-21

统计范围：2026-03-20 09:00 ~ 2026-03-21 09:00
原始记录：47
去重后：38
进入正文：5

## 今日新增信号

### Signal 1：OpenAI 发布 GPT-5.4 mini 与 nano
事件描述：OpenAI 推出两款轻量级模型，主打低成本高效推理……

问题还原：中小开发者需要低成本的生产级模型，但现有方案要么太贵要么能力不足

所属主题：算力
所属链路：模型供给 → 轻量化
所属节点：推理成本优化

旧方案：GPT-4o-mini 作为低成本选项，但上下文窗口和多模态能力有限
新变化：mini 和 nano 分别覆盖中低两档，nano 价格降至 $0.1/1M tokens
为什么重要：直接改变"能力 vs 成本"的选择曲线，agent 场景的调用成本可能降一个量级

待验证问题：
1. nano 在复杂 agent 工作流中的可靠性如何？
2. 竞品（Gemini Flash、Claude Haiku）是否会跟进降价？

关键原文链接：
- GPT-5.4 mini 与 nano 正式发布 | OpenAI新闻 | https://openai.com/...
```

以及发送到群聊的**晨间导读**：

```markdown
早上好。3月21日，周五。
先不急着被消息淹没，今天最值得先看的几件事在这里。

**今天最值得先看的 3 个信号**

**1. OpenAI 发布 GPT-5.4 mini 与 nano**
发生了什么：两款轻量模型上线，nano 价格降至 $0.1/1M tokens
为什么今天先看它：直接影响你的 agent 调用成本预算

---

**2. ……**

---

**今天还值得继续留意的一件事**
Anthropic 和 Google 是否会在本周跟进降价？上周 Claude 4 刚发布……

**完整版日报**
https://飞书文档链接
```

> 以上为示意，实际内容由 AI 根据当日新闻生成。日报模板详见 `ai_news_reporter/references/output-template.md`。

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
