# AI News Skills

一套面向 OpenClaw / Claude Code 风格代理的 AI 新闻工作流 skills。

> English summary:
> A pair of OpenClaw-compatible skills for AI news operations:
> one skill collects raw news into a Feishu bitable, and the other turns a reporting window into a signal-style daily brief and morning guide.

这个公开版仓库聚焦两件事：

- `ai_news_fetcher`
  - 从公开网页源采集 AI 新闻
  - 保留原始时间、原始摘要
  - 写入飞书原始新闻表
- `ai_news_reporter`
  - 从原始新闻表读取一个报道窗口的数据
  - 做过滤、筛选、原文阅读
  - 生成日报与晨间导读

仓库里保留的是通用流程、模板和脚本骨架；真实飞书配置、聊天目标、运行日志都已经做了剥离和脱敏。

## 适用场景

- 想搭一个“新闻采集 -> 原始表 -> 日报生成”的代理工作流
- 想把采集和报告拆成两个职责清晰的 skills
- 想参考“原始时间保真 + 发布时间标准化 + 报道窗口键”这一套结构

## 依赖

这套 skills 默认假设你的环境里已经有可用的网页读取能力。

其中 `ai_news_fetcher` 的默认主链依赖：

- `agent-reach`

它主要用于：

- 读取公开网页列表页文本
- 提供较干净的标题、链接、原始时间、摘要候选

如果没有 `agent-reach`：

- `ai_news_fetcher` 的默认 cron 主链不会完整工作
- 你需要自己替换成其他网页读取器，或者改写 skill 的读取层

换句话说：

- `ai_news_fetcher` = 采集与标准化 skill
- `agent-reach` = 默认网页读取器
- `ai_news_reporter` = 基于原始表的日报生成 skill

## 核心设计

### `ai_news_fetcher`

- 只负责采集和入表
- 不负责日报生成
- 优先保留：
  - `标题`
  - `原文链接`
  - `原始时间`
  - `原文摘要`
- 再生成：
  - `发布时间`
  - 哈希字段
  - 处理状态

### `ai_news_reporter`

- 只负责读表和生成日报
- 不重新抓公开网页
- 优先按 `报道窗口键` 取数
- 由大模型筛高价值事件、阅读全文、按模板写成日报

## 目录结构

```text
skills/
  ai_news_fetcher/
  ai_news_reporter/
```

## 先配置什么

这两个 skills 都依赖飞书多维表格。

仓库里只提供示例配置文件：

- `skills/ai_news_fetcher/bitable_target.example.json`
- `skills/ai_news_reporter/bitable_target.example.json`

使用时请各自复制为：

- `skills/ai_news_fetcher/bitable_target.json`
- `skills/ai_news_reporter/bitable_target.json`

然后填入你自己的：

- `app_name`
- `app_token`
- `table_name`
- `table_id`
- `url`

## Quick Start

### 1. 克隆仓库

```bash
git clone git@github.com:yy4fun/ai-news-skills.git
cd ai-news-skills
```

### 2. 安装到本机 OpenClaw

```bash
./install.sh
```

默认会把两个 skills 安装到：

```text
~/.openclaw/workspace/skills/
```

注意：

- 这个安装脚本只安装 `ai_news_fetcher` 和 `ai_news_reporter`
- 不会自动安装 `agent-reach`
- 如果你准备按默认主链运行采集，请先确保 `agent-reach` 已可用

### 3. 填写飞书配置

复制示例配置：

```bash
cp ~/.openclaw/workspace/skills/ai_news_fetcher/bitable_target.example.json \
  ~/.openclaw/workspace/skills/ai_news_fetcher/bitable_target.json

cp ~/.openclaw/workspace/skills/ai_news_reporter/bitable_target.example.json \
  ~/.openclaw/workspace/skills/ai_news_reporter/bitable_target.json
```

然后填入你自己的飞书多维表格信息。

### 4. 先单独测试

建议先：

- 用 `ai_news_fetcher` 测试采集
- 再用 `ai_news_reporter` 测试日报生成

确认飞书表和文档链路都正常后，再配置 cron / automation。

### 5. 典型触发方式

安装完成后，常见用法是：

- 让 `ai_news_fetcher` 采集并写入飞书原始新闻表
- 让 `ai_news_reporter` 按 `报道窗口键` 生成日报和晨间导读

如果你在 OpenClaw / Claude Code 风格环境里手动触发，建议让两个 skill 分开运行：

- 先跑采集
- 再跑报告

## 推荐工作流

1. `ai_news_fetcher`
   - 采集公开网页新闻
   - 写入飞书原始新闻表
2. `ai_news_reporter`
   - 按 `报道窗口键` 或时间窗口读取原始新闻
   - 做基础过滤与去重
   - 筛选高价值事件
   - 生成日报和晨间导读

## 不包含的内容

公开版不会包含这些真实配置或运行数据：

- 飞书真实 `app_token`
- 真实 `table_id`
- 真实 `open_id` / `chat_id`
- 本地 cron 任务配置
- 运行日志
- 历史回执和投递队列

## 发布建议

如果你准备把这个目录同步到 GitHub，建议单独建一个新仓库，例如：

- `openclaw-ai-news-skills`

然后只同步这个目录，不要直接同步整个 `.openclaw` 工作目录。

## 后续你需要自己补的部分

- 真实飞书多维表格配置
- `agent-reach` 或你自己的网页读取器
- 你的 cron / automation 配置
- 目标群聊或私聊接收人
- 你自己的新闻源维护策略
