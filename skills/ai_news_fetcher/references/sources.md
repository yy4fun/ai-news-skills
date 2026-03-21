# 新闻源

这里只维护两类信息：

1. 当前主链源地址
2. 真正的源级特殊规则

## 当前默认主链

- 财联社-AI
  - `https://www.cls.cn/subject/1321`
- 36氪-AI
  - `https://36kr.com/motif/327686782977`
- 36氪快讯-AI
  - `https://36kr.com/newsflashes/`
- OpenAI新闻
  - `https://openai.com/zh-Hans-CN/news/`
- Anthropic新闻
  - `https://www.anthropic.com/news`
- Forrester博客
  - `https://www.forrester.com/blogs/`
- Readhub-AI
  - `https://readhub.cn/news/ai`
- CMSWire
  - `https://www.cmswire.com/`
- CX Today
  - `https://www.cxtoday.com/latest-news/`
- GitHub Trending
  - `https://github.com/trending?since=daily`
- Google DeepMind博客 (**暂停** — jina/agent-reach 无法获取标题和日期，需 browser 模式)
  - `https://deepmind.google/discover/blog/`
- Google Cloud博客
  - `https://cloud.google.com/blog/`

## 特殊规则

### GitHub Trending

- 无发布时间字段，normalize 时必须加 `--fallback-to-now`，用抓取时间代替
- 只保留标题或描述命中 AI 关键词的项目（agent、model、LLM、RAG、inference、diffusion 等）

### Google Cloud博客

- 无发布时间字段，normalize 时必须加 `--fallback-to-now`，用抓取时间代替

### 36氪快讯-AI

- 只保留 AI 相关内容
- 标题或摘要至少一个命中 AI 关键词

### CMSWire / CX Today

- 重点检查发布时间
- 抓不到可信时间就不要写入

## 暂不进入主链

- RSS
- 微信公众号
- Twitter / X

## 维护原则

这里只是新闻源地址的唯一真相源。

后续加减源，只改：

- `references/sources.md`
- `fetcher.py`
