---
name: ai_news_fetcher
description: >
  采集公开网页 AI 新闻并写入飞书原始新闻表。
  触发场景：抓取AI新闻、采集新闻、更新原始新闻表、补抓新闻源、维护新闻池、
  指定时间范围或来源写入飞书、cron新闻采集。
  不触发：生成日报、写signal、发早报、归并事件、阅读全文写判断 → 这些交给 ai_news_reporter。
---

# AI 新闻抓取 Skill

只做一件事：`采集公开网页新闻 → 标准化 → 写入飞书原始新闻表`

不负责：生成日报、归并事件、写判断更新、发送早报消息 → 交给 `ai_news_reporter`

## 前置依赖

- **飞书多维表格**：需要一张飞书 Bitable 表用于存储原始新闻，将表的 `app_token` 和 `table_id` 填入 `bitable_target.json`（参考 `bitable_target.example.json`）
- **Agent Reach**：需要安装 [Agent Reach](https://github.com/Panniantong/Agent-Reach)，用于将网页转为结构化文本
- **Python 3.10+**：运行 normalize / build 脚本

> 本 skill 不内置任何飞书凭证。`bitable_target.json` 由用户在本地创建，已被 `.gitignore` 排除。

## 执行前必读

- `references/execution.md` — 执行流程、门控检查点、模式说明
- `references/data-model.md` — 字段定义
- `references/sources.md` — 源地址和源级特殊规则
- `references/gotchas.md` — 仅排障时读
- `bitable_target.json` — 飞书目标配置

## 管道（不可跳步）

```
curl r.jina.ai → normalize_agent_reach.py → build_source_items.py → 入表
```

## 硬约束

1. 管道必须走 `normalize_agent_reach.py` + `build_source_items.py`，禁止手算时间戳或手工构造 bitable JSON
2. 采集任务只做"抓取并写入"，不顺带生成日报、发消息、查整表、回写分析字段
3. 写入成功即结束，不二次补抓或重跑
4. cron 模式不用浏览器、不进调试模式、不临时编写脚本
5. 用 `curl r.jina.ai`（agent-reach），不用 `web_fetch` 工具
6. 时间、链接或来源不可信时，不写入
7. 任务结束只返回：`写入N条` 或 `0条写入`
