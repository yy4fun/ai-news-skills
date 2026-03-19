# 执行流程

这个 skill 的最短闭环是：

`列表页采集 -> 轻量提取 -> 轻量判断 -> 去重 -> 入表`

## 两类入口

### cron 默认入口

用于每天自动采集。

目标：

- 稳定
- 无人值守
- 少分支
- 少调试动作

### 飞书补充入口

用于特殊场景补抓。

可选注入参数：

- `sources`
- `time_range`
- `output_target`

说明：

- 这三个参数都可以缺省
- 飞书补抓不是生产主链
- 飞书补抓优先用于补充和验证，不用于替代 cron

## 推荐执行顺序

1. 用 `agent-reach` 读取列表页（web channel：用 `exec` 运行 `curl -s "https://r.jina.ai/URL"`，**不要用 `web_fetch` 工具**，两者结果不同）。
2. 把 agent-reach 返回的原始文本通过 `normalize_agent_reach.py` 提取结构化记录（时间解析、摘要清洗均由脚本完成）。
3. 把结构化记录通过 `build_source_items.py --format bitable_records` 生成飞书入表 JSON（时间戳转换、字段映射、哈希均由脚本完成）。
4. 在入表前做轻量去重。
5. 将 bitable_records 写入飞书多维表格。
6. 一旦记录成功写入，就立即结束本轮采集，不要再补抓、补写或重跑字段转换。

典型管道命令：

```bash
curl -s "https://r.jina.ai/URL" | python3 normalize_agent_reach.py --source "财联社-AI" | python3 build_source_items.py --format bitable_records
```

也可以分步执行，每个源单独跑一次，最后汇总入表。

## cron 模式要求

cron 模式下必须遵守：

- 不进入调试模式
- 不读一堆文档后临场试探
- 不临时编写调试用 python 脚本（skill 自带的 `normalize_agent_reach.py` 和 `build_source_items.py` 不在此限，它们是 cron 默认管道的一部分）
- 不手工构造 bitable JSON 或手算 Unix 时间戳（由 `build_source_items.py` 完成）
- 不使用 `web_search`
- 不使用浏览器补抓

正确的 cron 行为应该是：

`agent-reach (curl r.jina.ai) -> normalize_agent_reach.py -> build_source_items.py -> 入表 -> 结束`

## 入表前判断

有任意一项不满足，就不要入表：

- 不是文章链接
- 标题为空
- 原文链接为空
- 原始时间缺失
- 无法从原始时间可信确认发布时间
- 标准化后的发布时间不是今天
- 是广告、推荐位、导航、分页或重复卡片

## 时间规则

### 采集阶段

- 页面抓到的原始时间文本先保留到 `原始时间`
- 不要用抓取时间代替发布时间
- 不要用当天零点代替发布时间
- 不要靠代理临场补全年份或猜时间

### 标准化阶段

默认只处理足够明确的时间：

- 明确的绝对日期时间
- 在当前上下文中容易确认的当日时间文本

如果仍无法给出可信 `发布时间`，就不要手工兜底写时间。

### 时间戳转换（禁止手算）

飞书日期时间字段接收 Unix 毫秒时间戳。LLM 手算时间戳极不可靠（实测经常差 1 年或数天）。**所有时间解析和时间戳转换必须通过 `normalize_agent_reach.py` + `build_source_items.py` 完成**，不要在 JSON 里直接手写 Unix 时间戳数字。

## 摘要规则

- `原文摘要` 优先提取页面已有的正文摘要或导语
- 不要把标题重复写成摘要
- 广告、推荐阅读、作者模板、站点噪声直接留空
- `摘要哈希` 只有在 `原文摘要` 存在时才写
- 如果 `agent-reach` 已经提取到可信摘要，不要再因为浏览器补抓把摘要覆盖成空值

## 去重

优先按下面顺序去重：

1. `原文链接`
2. `标题哈希 + 发布时间`

## 友好抓取

- 先去重，再决定是否继续读取
- 同一链接当天不重复阅读全文
- 同一事件已有足够证据时，不要把所有相关文章都点开
- 同站点连续请求要克制
- 遇到 403、验证码、登录墙、明显限流时直接跳过

## 本地脚本的角色

- `normalize_agent_reach.py` — 解析 agent-reach 原始文本，提取结构化字段（标题、链接、时间、摘要），处理时间标准化。**cron 默认管道必经环节。**
- `build_source_items.py` — 将结构化记录转为飞书 bitable 格式，完成 Unix 毫秒时间戳转换、字段映射、哈希计算。**cron 默认管道必经环节。**

`fetcher.py` 当前只保留作历史调试脚本，不再作为默认采集主路径。

## 飞书补充模式参数约定

如果用户在飞书里临时发起补抓，可以接受这些可选参数：

- `sources`
  - 一个或多个源名或网址
- `time_range`
  - 例如“今天”“过去24小时”“2026-03-17 到 2026-03-18”
- `output_target`
  - 例如飞书原始表、某个文件路径、某个文档

如果这些参数未提供：

- `sources` 默认用主链
- `time_range` 默认用今天
- `output_target` 默认写飞书原始新闻表
