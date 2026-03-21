#!/usr/bin/env python3
"""
AI industry news fetcher for skill usage.

Fetches configured sources via Scrapling and prints a structured payload.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

from scrapling import Fetcher


PUBLIC_WEB_SOURCES = [
    {
        "name": "财联社-AI",
        "url": "https://www.cls.cn/subject/1321",
        "preferred_runtime": "agent-reach",
        "detail_runtime": "browser",
        "strategy": "html_list",
        "item_css": "div.p-t-20.p-b-20.b-b-w-1.b-b-s-s.b-c-e6e7ea",
        "css": ".subject-interest-small-content a",
        "title_css": ".subject-interest-small-content a strong",
        "date_css": ".subject-interest-small-title span",
        "summary_css": ".subject-interest-small-content a span",
        "enabled": True,
    },
    {
        "name": "36氪-AI",
        "url": "https://36kr.com/motif/327686782977",
        "preferred_runtime": "agent-reach",
        "detail_runtime": "browser",
        "strategy": "html_list",
        "item_css": ".article-item, .news-item, .kr-shadow-content",
        "css": ".article-title a, .news-item a",
        "date_css": ".publish-time",
        "summary_css": ".article-summary, .item-desc, .summary, p",
        "include_keywords": [
            "ai",
            "人工智能",
            "大模型",
            "模型",
            "智能体",
            "agent",
            "gpt",
            "claude",
            "openai",
            "anthropic",
            "kimi",
            "deepseek",
            "算力",
            "推理",
            "芯片",
            "aigc",
        ],
        "enabled": True,
    },
    {
        "name": "36氪快讯-AI",
        "url": "https://36kr.com/newsflashes/",
        "preferred_runtime": "agent-reach",
        "detail_runtime": "browser",
        "strategy": "html_list",
        "item_css": ".newsflash-item, .kr-shadow-content, li",
        "css": "h3 a, h2 a, .newsflash-item-title a, .article-item-title a",
        "date_css": "time, .time, .newsflash-item-time",
        "summary_css": ".newsflash-item-desc, .item-desc, .summary, p",
        "include_keywords": [
            "ai",
            "人工智能",
            "大模型",
            "模型",
            "智能体",
            "agent",
            "gpt",
            "claude",
            "openai",
            "anthropic",
            "kimi",
            "算力",
            "推理",
        ],
        "enabled": True,
    },
    {
        "name": "OpenAI新闻",
        "url": "https://openai.com/zh-Hans-CN/news/",
        "preferred_runtime": "browser",
        "strategy": "html_list",
        "item_css": "article, li",
        "css": "h3 a, .post-item a",
        "date_css": "time",
        "summary_css": ".text-token-text-primary, .post-card-description, p",
        "enabled": True,
    },
    {
        "name": "Anthropic新闻",
        "url": "https://www.anthropic.com/news",
        "preferred_runtime": "browser",
        "strategy": "html_list",
        "item_css": "li, article",
        "css": "h3 a, .news-item a",
        "date_css": "time",
        "summary_css": ".font-secondary, .news-summary, p",
        "enabled": True,
    },
    {
        "name": "Forrester博客",
        "url": "https://www.forrester.com/blogs/",
        "preferred_runtime": "browser",
        "strategy": "html_list",
        "item_css": "article, li",
        "css": ".blog-title a, h3 a",
        "date_css": ".blog-date, time",
        "summary_css": ".blog-excerpt, .entry-summary, p",
        "enabled": True,
    },
    {
        "name": "CMSWire",
        "url": "https://www.cmswire.com/",
        "preferred_runtime": "browser",
        "strategy": "html_list",
        "item_css": "article, li",
        "css": "h3 a, h2 a, .river-item__title a, .article-title a",
        "date_css": "time, .river-item time, .article-meta time",
        "summary_css": ".river-item__dek, .article-excerpt, .entry-summary, p",
        "enabled": True,
    },
    {
        "name": "CX Today",
        "url": "https://www.cxtoday.com/latest-news/",
        "preferred_runtime": "browser",
        "strategy": "html_list",
        "item_css": "article, li",
        "css": "h3 a, h2 a, .entry-title a, .jeg_post_title a",
        "date_css": "time, .jeg_meta_date a, .post-date",
        "summary_css": ".jeg_post_excerpt, .entry-content p, .post-excerpt, p",
        "enabled": True,
    },
    {
        "name": "Readhub-AI",
        "url": "https://readhub.cn/news/ai",
        "preferred_runtime": "agent-reach",
        "detail_runtime": "browser",
        "strategy": "html_list",
        "item_css": ".topic-item, .news-item, li",
        "css": "h3 a, h2 a, .topic-item-title a, .news-item-title a",
        "date_css": "time, .time, .publish-time",
        "summary_css": ".topic-item-summary, .summary, .desc, p",
        "enabled": True,
    },
    {
        "name": "GitHub Trending",
        "url": "https://github.com/trending?since=daily",
        "preferred_runtime": "agent-reach",
        "strategy": "html_list",
        "item_css": ".Box-row, .repo-list li",
        "css": "h2 a, .repo-title a",
        "date_css": "time-relative, relative-time",
        "summary_css": ".repo-description, .col-9, p",
        "include_keywords": [
            "ai",
            "agent",
            "model",
            "llm",
            "rag",
            "inference",
            "diffusion",
            "gpt",
            "claude",
            "openai",
            "anthropic",
            "deepseek",
            "machine learning",
            "ml",
        ],
        "fallback_to_now": True,
        "enabled": True,
    },
    {
        "name": "Google DeepMind博客",
        "url": "https://deepmind.google/discover/blog/",
        "preferred_runtime": "agent-reach",
        "strategy": "html_list",
        "item_css": "article, .blog-post, li",
        "css": "h3 a, .post-title a, .blog-post-title a",
        "date_css": "time, .post-date, .date",
        "summary_css": ".post-summary, .blog-post-summary, .description, p",
        "enabled": False,  # jina/agent-reach 无法获取博客列表标题和日期，需要 browser 模式
    },
    {
        "name": "Google Cloud博客",
        "url": "https://cloud.google.com/blog/",
        "preferred_runtime": "agent-reach",
        "strategy": "html_list",
        "item_css": "article, .blog-post, li",
        "css": "h3 a, .post-title a, .blog-card-title a",
        "date_css": "time, .post-date, .date",
        "summary_css": ".post-summary, .blog-summary, .description, p",
        "fallback_to_now": True,
        "enabled": True,
    },
]

RSS_SOURCES = [
    {
        "name": "SteveBlank",
        "url": "https://steveblank.com/feed/",
        "preferred_runtime": "rss",
        "strategy": "rss",
        "css": "title",
        "date_css": "pubDate",
        "enabled": True,
        "is_rss": True,
    },
]

SOURCES = PUBLIC_WEB_SOURCES + RSS_SOURCES
LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def fetch_with_scrapling(url: str):
    """Fetch a page with Scrapling."""
    fetcher = Fetcher()
    return fetcher.get(url)


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def selector_first_text(selection) -> Optional[str]:
    if selection is None:
        return None
    get_method = getattr(selection, "get", None)
    if callable(get_method):
        return get_method()
    extract_first = getattr(selection, "extract_first", None)
    if callable(extract_first):
        return extract_first()
    first_attr = getattr(selection, "first", None)
    if callable(first_attr):
        return first_attr()
    get_attr = getattr(first_attr, "get", None)
    if callable(get_attr):
        return get_attr()
    return first_attr


def clean_summary(value: Optional[str], title: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    lowered = text.lower()
    title_lower = clean_text(title).lower()
    noise_patterns = (
        "advertisement",
        "recommended",
        "read more",
        "subscribe",
        "sign up",
        "cookie",
        "privacy policy",
        "点击查看",
        "相关阅读",
        "推荐阅读",
        "广告",
    )
    if any(pattern in lowered for pattern in noise_patterns):
        return ""
    if title_lower and text == title:
        return ""
    if title_lower and lowered.startswith(title_lower):
        remainder = clean_text(text[len(title):])
        return remainder if remainder and remainder != text else ""
    return text


def normalize_summary_for_source(source_name: str, summary: str) -> str:
    text = clean_text(summary)
    if not text:
        return ""
    if source_name.startswith("36氪"):
        text = re.sub(r"^36氪获悉[，,:：]?\s*", "", text)
    text = re.sub(r"【原文链接.*$", "", text)
    text = re.sub(r"\s*（[^）]{0,20}记者.*?）$", "", text)
    if source_name == "Readhub-AI":
        text = re.sub(r"^据[^，。]{0,30}[，,:：]\s*", "", text)
    if source_name in {"CMSWire", "CX Today"}:
        text = re.sub(r"^(by|posted by)\s+[^.]+\.\s*", "", text, flags=re.IGNORECASE)
    return clean_text(text)


def infer_date_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    patterns = (
        r"/(?P<year>20\d{2})[-/.](?P<month>\d{1,2})[-/.](?P<day>\d{1,2})/",
        r"doc-[^/]*?(?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})",
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if not match:
            continue
        year = int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        try:
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            continue
    return None


def normalize_date_text_for_source(source_name: str, date_str: Optional[str], url: str) -> Optional[str]:
    text = clean_text(date_str)
    if text:
        if source_name == "OpenAI新闻":
            text = re.sub(r"^\s*(updated|published)\s*", "", text, flags=re.IGNORECASE)
        if source_name in {"CMSWire", "CX Today"}:
            text = re.sub(r"^\s*(updated|posted|published)\s*[:\-]?\s*", "", text, flags=re.IGNORECASE)
        if source_name == "Readhub-AI":
            text = re.sub(r"^\s*(今天|today)\s*", "今天 ", text, flags=re.IGNORECASE)
        return clean_text(text)
    if source_name == "Readhub-AI":
        return infer_date_from_url(url)
    return None


def extract_with_item_containers(resp, source: Dict[str, str]) -> Optional[List[Dict[str, Optional[str]]]]:
    item_css = source.get("item_css")
    if not item_css:
        return None

    item_nodes = resp.css(item_css)
    if not item_nodes:
        return None

    articles = []
    for node in item_nodes:
        title_selector = source.get("title_css") or source.get("css", "a")
        title = clean_text(selector_first_text(node.css(f"{title_selector}::text")))
        if not title:
            continue
        link = selector_first_text(node.css(f"{source.get('css', 'a')}::attr(href)"))
        date_str = selector_first_text(node.css(f"{source.get('date_css', 'time')}::text, {source.get('date_css', 'time')}::attr(datetime)"))
        summary_css = source.get("summary_css")
        summary = clean_summary(selector_first_text(node.css(f"{summary_css}::text")), title) if summary_css else ""
        normalized_link = normalize_link(source["url"], link)
        articles.append(
            {
                "title": title,
                "url": normalized_link,
                "date": normalize_date_text_for_source(source["name"], date_str, normalized_link),
                "summary": normalize_summary_for_source(source["name"], summary) or None,
            }
        )
    return articles


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=LOCAL_TZ)
    return value.astimezone(timezone.utc)


def local_today() -> datetime.date:
    return datetime.now(LOCAL_TZ).date()


def current_local_now() -> datetime:
    return datetime.now(LOCAL_TZ)


def adjust_yearless_candidate(candidate: datetime, now_local: datetime) -> datetime:
    """
    For month/day strings without a year, prefer a near-date interpretation.
    If the naive current-year result is implausibly far in the future, roll back one year.
    """
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=LOCAL_TZ)
    future_delta = candidate - now_local
    if future_delta > timedelta(days=2):
        candidate = candidate.replace(year=candidate.year - 1)
    return candidate


def is_suspicious_today_candidate(dt: Optional[datetime]) -> bool:
    if dt is None:
        return True
    local_dt = dt.astimezone(LOCAL_TZ)
    now_local = current_local_now()
    if local_dt > now_local + timedelta(hours=6):
        return True
    if abs(local_dt.year - now_local.year) >= 1 and abs((now_local - local_dt).days) > 31:
        return True
    return False


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse common article date formats."""
    if not date_str:
        return None

    raw = clean_text(date_str)
    lowered = raw.lower()
    now_local = current_local_now()

    try:
        parsed = parsedate_to_datetime(raw)
        return normalize_datetime(parsed)
    except Exception:
        pass

    iso_candidate = raw.replace("Z", "+00:00")
    try:
        return normalize_datetime(datetime.fromisoformat(iso_candidate))
    except Exception:
        pass

    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y/%m/%d %H:%M",
        "%Y.%m.%d",
        "%Y.%m.%d %H:%M",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M",
        "%B %d, %Y",
        "%B %d, %Y %H:%M",
        "%d %b %Y",
        "%d %b %Y %H:%M",
        "%b %d, %Y",
        "%b %d, %Y %H:%M",
    ):
        try:
            return normalize_datetime(datetime.strptime(raw, fmt))
        except ValueError:
            continue

    chinese_patterns = (
        (r"(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?", True),
        (r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?", False),
    )
    for pattern, has_year in chinese_patterns:
        match = re.search(pattern, raw)
        if not match:
            continue
        year = int(match.group("year")) if has_year else now_local.year
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        try:
            candidate = datetime(year, month, day, hour, minute, tzinfo=LOCAL_TZ)
            if not has_year:
                candidate = adjust_yearless_candidate(candidate, now_local)
            return normalize_datetime(candidate)
        except ValueError:
            continue

    month_day_patterns = (
        r"(?P<month>\d{1,2})/(?P<day>\d{1,2})(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?",
        r"(?P<month>\d{1,2})-(?P<day>\d{1,2})(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?",
    )
    for pattern in month_day_patterns:
        match = re.search(pattern, raw)
        if not match:
            continue
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        try:
            candidate = datetime(now_local.year, month, day, hour, minute, tzinfo=LOCAL_TZ)
            candidate = adjust_yearless_candidate(candidate, now_local)
            return normalize_datetime(candidate)
        except ValueError:
            continue

    relative_patterns = (
        (r"(\d+)\s*(分钟|mins?|minutes?)\s*(前|ago)?", "minutes"),
        (r"(\d+)\s*(小时|hours?|hrs?)\s*(前|ago)?", "hours"),
        (r"(\d+)\s*(天|days?)\s*(前|ago)?", "days"),
    )
    for pattern, unit in relative_patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue
        amount = int(match.group(1))
        return normalize_datetime(now_local - timedelta(**{unit: amount}))

    relative_day_patterns = (
        (r"^(今天|today)(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?$", 0),
        (r"^(昨天|yesterday)(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?$", 1),
    )
    for pattern, day_offset in relative_day_patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue
        base = now_local - timedelta(days=day_offset)
        hour = int(match.group("hour") or base.hour)
        minute = int(match.group("minute") or base.minute)
        candidate = datetime(base.year, base.month, base.day, hour, minute, tzinfo=LOCAL_TZ)
        return normalize_datetime(candidate)

    return None


def is_recent_article(dt: Optional[datetime], days: int) -> bool:
    """Treat undated articles as recent to avoid false negatives."""
    if dt is None:
        return True
    return datetime.now(timezone.utc) - dt <= timedelta(days=days)


def is_today_article(dt: Optional[datetime]) -> bool:
    """Keep only articles whose parsed date falls on the local current day."""
    if dt is None:
        return False
    if is_suspicious_today_candidate(dt):
        return False
    return dt.astimezone(LOCAL_TZ).date() == local_today()


def normalize_link(base_url: str, link: Optional[str]) -> str:
    if not link:
        return base_url
    link = link.strip()
    if link.startswith(("javascript:", "#")):
        return base_url
    return urljoin(base_url, link)


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    clean_path = parsed.path.rstrip("/")
    return f"{parsed.netloc.lower()}{clean_path}?{parsed.query}".rstrip("?")


def matches_keywords(title: str, summary: str, keywords: Optional[List[str]]) -> bool:
    if not keywords:
        return True
    lowered = f"{title} {summary}".lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def extract_news(
    source: Dict[str, str],
    recent_days: int,
    per_source_limit: int,
    today_only: bool,
) -> Dict[str, object]:
    """Extract recent articles from one source."""
    name = source["name"]
    url = source["url"]
    css = source.get("css", "a")
    date_css = source.get("date_css", "time")
    summary_css = source.get("summary_css")
    is_rss = source.get("is_rss", False)
    strategy = source.get("strategy", "html_list")
    include_keywords = source.get("include_keywords")

    try:
        resp = fetch_with_scrapling(url)
        status = getattr(resp, "status", 200)
        if status != 200:
            return {"name": name, "success": False, "error": f"HTTP {status}", "articles": []}

        articles: List[Dict[str, Optional[str]]] = []
        if is_rss or strategy == "rss":
            titles = resp.css("item title::text").getall()
            links = resp.css("item link::text").getall()
            dates = resp.css("item pubDate::text").getall()
            summaries = resp.css("item description::text").getall()
        else:
            container_articles = extract_with_item_containers(resp, source)
            if container_articles is not None:
                titles = [item["title"] for item in container_articles]
                links = [item.get("url") for item in container_articles]
                dates = [item.get("date") for item in container_articles]
                summaries = [item.get("summary") for item in container_articles]
            else:
                titles = resp.css(f"{css}::text").getall()
                links = resp.css(f"{css}::attr(href)").getall()
                dates = resp.css(f"{date_css}::text, {date_css}::attr(datetime)").getall()
                summaries = resp.css(f"{summary_css}::text").getall() if summary_css else []

        for index, raw_title in enumerate(titles):
            title = clean_text(raw_title)
            if not title:
                continue
            raw_link = links[index] if index < len(links) else url
            link = normalize_link(url, raw_link)
            date_str = normalize_date_text_for_source(name, dates[index] if index < len(dates) else None, link)
            summary = clean_summary(summaries[index] if index < len(summaries) else None, title)
            summary = normalize_summary_for_source(name, summary)
            if not matches_keywords(title, summary, include_keywords):
                continue
            parsed_date = parse_date(date_str)
            if today_only:
                if not is_today_article(parsed_date):
                    continue
            elif not is_recent_article(parsed_date, recent_days):
                continue

            articles.append(
                {
                    "title": title,
                    "url": link,
                    "date": clean_text(date_str) or None,
                    "summary": summary or None,
                    "source": name,
                    "parsed_date": parsed_date.replace(microsecond=0).isoformat().replace("+00:00", "Z") if parsed_date else None,
                }
            )
            if len(articles) >= per_source_limit:
                break

        return {
            "name": name,
            "success": True,
            "error": None,
            "articles": articles,
            "strategy": strategy,
            "preferred_runtime": source.get("preferred_runtime"),
        }
    except Exception as exc:
        return {
            "name": name,
            "success": False,
            "error": str(exc)[:200],
            "articles": [],
            "strategy": strategy,
            "preferred_runtime": source.get("preferred_runtime"),
        }


def dedupe_articles(articles: Iterable[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    seen = set()
    deduped = []
    for article in articles:
        title_key = clean_text(article.get("title", "")).lower()
        url_key = canonicalize_url(article.get("url", ""))
        key = (title_key, url_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(article)
    return deduped


def sort_articles(articles: Iterable[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    def sort_key(article: Dict[str, Optional[str]]):
        parsed = article.get("parsed_date")
        if not parsed:
            return (0, datetime.min)
        try:
            return (1, datetime.fromisoformat(parsed))
        except ValueError:
            return (0, datetime.min)

    return sorted(articles, key=sort_key, reverse=True)


def select_source_pool(source_group: str) -> List[Dict[str, str]]:
    if source_group == "public-web":
        return PUBLIC_WEB_SOURCES
    if source_group == "rss":
        return RSS_SOURCES
    return SOURCES


def select_sources(source_names: Optional[List[str]], source_group: str) -> List[Dict[str, str]]:
    enabled_sources = [source for source in select_source_pool(source_group) if source.get("enabled", True)]
    if not source_names:
        return enabled_sources

    wanted = {name.strip().lower() for name in source_names if name.strip()}
    return [source for source in enabled_sources if source["name"].lower() in wanted]


def fetch_all_news(
    recent_days: int,
    per_source_limit: int,
    source_names: Optional[List[str]],
    source_group: str,
    today_only: bool,
) -> Dict[str, object]:
    selected_sources = select_sources(source_names, source_group=source_group)
    source_results = []
    all_articles = []

    for source in selected_sources:
        result = extract_news(
            source,
            recent_days=recent_days,
            per_source_limit=per_source_limit,
            today_only=today_only,
        )
        source_results.append(result)
        if result["success"]:
            all_articles.extend(result["articles"])

    deduped = dedupe_articles(all_articles)
    sorted_articles = sort_articles(deduped)

    return {
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "recent_days": recent_days,
        "today_only": today_only,
        "requested_sources": source_names or [],
        "source_group": source_group,
        "sources": [
            {
                "name": result["name"],
                "success": result["success"],
                "count": len(result.get("articles", [])),
                "error": result.get("error"),
                "strategy": result.get("strategy"),
                "preferred_runtime": result.get("preferred_runtime"),
            }
            for result in source_results
        ],
        "articles": sorted_articles,
        "total": len(sorted_articles),
    }


def build_markdown(payload: Dict[str, object], limit: int) -> str:
    lines = [f"# AI News Digest ({payload['total']} items)"]
    for article in payload["articles"][:limit]:
        lines.append(
            f"- [{article['source']}] {article['title']} ({article.get('date') or 'date unknown'})\n"
            f"  {article['url']}"
        )
    failed_sources = [src for src in payload["sources"] if not src["success"]]
    if failed_sources:
        lines.append("")
        lines.append("## Source errors")
        for source in failed_sources:
            lines.append(f"- {source['name']}: {source.get('error') or 'unknown error'}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch AI industry news from configured sources.")
    parser.add_argument("--days", type=int, default=1, help="Only keep articles from the last N days.")
    parser.add_argument("--limit", type=int, default=20, help="Final maximum number of articles.")
    parser.add_argument(
        "--per-source-limit",
        type=int,
        default=10,
        help="Maximum number of articles to retain per source before dedupe.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Restrict fetch to a specific source name. Repeat to include multiple sources.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--source-group",
        choices=("public-web", "rss", "all"),
        default="public-web",
        help="Fetch only public web sources, only RSS sources, or all configured sources.",
    )
    parser.add_argument(
        "--today-only",
        action="store_true",
        default=True,
        help="Only keep articles whose parsed date is on the local current day. Enabled by default.",
    )
    parser.add_argument(
        "--no-today-only",
        action="store_false",
        dest="today_only",
        help="Disable today-only filtering and fall back to the rolling day window.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = fetch_all_news(
        recent_days=max(args.days, 1),
        per_source_limit=max(args.per_source_limit, 1),
        source_names=args.sources,
        source_group=args.source_group,
        today_only=args.today_only,
    )
    payload["articles"] = payload["articles"][: max(args.limit, 1)]
    payload["total"] = len(payload["articles"])

    if args.format == "markdown":
        print(build_markdown(payload, limit=args.limit))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    failed_count = sum(1 for source in payload["sources"] if not source["success"])
    if failed_count == len(payload["sources"]) and payload["sources"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
