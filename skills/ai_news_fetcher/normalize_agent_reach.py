#!/usr/bin/env python3
"""
Normalize agent-reach list-page output into structured article records.

Accepted input:
1. JSON array/dict produced by an agent step
2. Lightweight markdown/text blocks with title/link/time/summary hints
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_summary(value: Optional[str], title: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    noise_patterns = (
        "advertisement",
        "recommended",
        "read more",
        "subscribe",
        "cookie",
        "相关阅读",
        "推荐阅读",
        "广告",
    )
    lowered = text.lower()
    if any(pattern in lowered for pattern in noise_patterns):
        return ""
    if clean_text(title) == text:
        return ""
    return text


def current_local_now() -> datetime:
    return datetime.now(LOCAL_TZ)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=LOCAL_TZ)
    return value.astimezone(timezone.utc)


def adjust_yearless_candidate(candidate: datetime, now_local: datetime) -> datetime:
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=LOCAL_TZ)
    if candidate - now_local > timedelta(days=2):
        candidate = candidate.replace(year=candidate.year - 1)
    return candidate


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None

    raw = clean_text(date_str)
    lowered = raw.lower()
    now_local = current_local_now()

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
        "%B %d, %Y",
        "%B %d, %Y %H:%M",
        "%b %d, %Y",
        "%b %d, %Y %H:%M",
        "%d %B %Y",
        "%d %B %Y %H:%M",
        "%d %b %Y",
        "%d %b %Y %H:%M",
    ):
        try:
            return normalize_datetime(datetime.strptime(raw, fmt))
        except ValueError:
            continue

    # English month-day without year (e.g. "Mar 18", "March 18")
    en_month_day_patterns = (
        (r"^(?P<month_name>[A-Z][a-z]+)\s+(?P<day>\d{1,2})$", True),
    )
    for pattern, _ in en_month_day_patterns:
        match = re.match(pattern, raw)
        if not match:
            continue
        month_name = match.group("month_name")
        day = int(match.group("day"))
        for mfmt in ("%B", "%b"):
            try:
                month = datetime.strptime(month_name, mfmt).month
                candidate = datetime(now_local.year, month, day, tzinfo=LOCAL_TZ)
                candidate = adjust_yearless_candidate(candidate, now_local)
                return normalize_datetime(candidate)
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


def article_from_mapping(item: Dict[str, object], default_source: str) -> Optional[Dict[str, object]]:
    title = clean_text(item.get("title"))
    url = clean_text(item.get("url") or item.get("link"))
    original_time = clean_text(
        item.get("original_time")
        or item.get("date")
        or item.get("time")
        or item.get("published_at_raw")
    )
    summary = normalize_summary(item.get("summary") or item.get("excerpt") or item.get("description"), title)
    source = clean_text(item.get("source")) or default_source
    if not title or not url or not original_time:
        return None
    parsed_date = parse_date(original_time)
    if not parsed_date:
        return None
    return {
        "title": title,
        "url": url,
        "date": original_time,
        "summary": summary or None,
        "source": source,
        "parsed_date": parsed_date.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def parse_json_payload(raw: str, default_source: str) -> Optional[List[Dict[str, object]]]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        if isinstance(payload.get("articles"), list):
            items = payload["articles"]
        else:
            items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        return None

    articles = []
    for item in items:
        if not isinstance(item, dict):
            continue
        article = article_from_mapping(item, default_source)
        if article:
            articles.append(article)
    return articles


_TIME_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)"
    r"|^(\d{1,2}月\d{1,2}日(?:\s+\d{1,2}:\d{2})?)"
    r"|^(\d+\s*(?:分钟|小时|天|hours?|mins?|minutes?|days?)\s*(?:前|ago)?)\s*$"
)
_HEADLINE_RE = re.compile(r"\*{0,2}【(.+?)】\*{0,2}")
_NOISE_URLS = re.compile(
    r"/(our|subject|download|vip|fm|invest|usercenter|seek-report|"
    r"information|live|video|topics|activity|station|policy|"
    r"newsflashes/catalog|account)"
)


def _is_article_url(url: str) -> bool:
    """Filter out navigation/noise URLs, keep article links."""
    if _NOISE_URLS.search(url):
        return False
    if re.search(r"/(detail|p|newsflashes)/\d+", url):
        return True
    if re.search(r"/news/|/blogs?/|/article", url):
        return True
    return False


def _extract_headline_and_summary(link_text: str) -> tuple:
    """Extract headline from 【headline】 pattern; rest is summary."""
    match = _HEADLINE_RE.search(link_text)
    if match:
        headline = clean_text(match.group(1))
        rest = link_text[:match.start()] + link_text[match.end():]
        rest = re.sub(r"^\*+|\*+$", "", rest).strip()
        summary = clean_text(rest)
        return headline, summary
    return clean_text(link_text), ""


def _detect_time(text: str) -> Optional[str]:
    """Check if a line is a standalone time indicator."""
    stripped = text.strip()
    match = _TIME_LINE_RE.match(stripped)
    if match:
        time_part = match.group(1) or match.group(2) or match.group(3)
        if time_part:
            return clean_text(time_part)
    return None


def parse_markdown_payload(raw: str, default_source: str) -> List[Dict[str, object]]:
    articles = []
    current: Dict[str, str] = {}
    pending_time: Optional[str] = None
    url_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")

    def flush() -> None:
        nonlocal pending_time
        if not current:
            return
        article = article_from_mapping(current, default_source)
        if article:
            articles.append(article)
        current.clear()

    for line in raw.splitlines():
        text = clean_text(line)
        if not text:
            flush()
            continue

        # Detect standalone time lines (e.g. "2026-03-18 23:50 来自 第一财经", "1分钟前")
        detected_time = _detect_time(text)
        if detected_time:
            if current and "url" in current and "date" not in current:
                # Time AFTER a URL (36kr pattern): attach to current article
                current["date"] = detected_time
            else:
                # Time BEFORE a URL (cls.cn pattern): remember for next article
                pending_time = detected_time
            continue

        url_match = url_pattern.search(text)
        if url_match:
            url = clean_text(url_match.group(2))
            if _is_article_url(url):
                flush()
                link_text = url_match.group(1)
                headline, summary = _extract_headline_and_summary(link_text)
                current["title"] = headline
                current["url"] = url
                if summary:
                    current["summary"] = summary
                if pending_time:
                    current["date"] = pending_time
                    pending_time = None
            continue

        if text.startswith("|") and text.endswith("|"):
            parts = [clean_text(part) for part in text.strip("|").split("|")]
            if len(parts) >= 4 and parts[0] not in {"标题", "---"}:
                flush()
                current["title"] = parts[0]
                current["url"] = parts[1]
                current["date"] = parts[2]
                current["summary"] = parts[3]
                flush()
            continue

        lowered = text.lower()
        if lowered.startswith("标题") or lowered.startswith("title"):
            current["title"] = clean_text(text.split(":", 1)[-1].split("：", 1)[-1])
        elif lowered.startswith("链接") or lowered.startswith("原文链接") or lowered.startswith("url") or lowered.startswith("link"):
            current["url"] = clean_text(text.split(":", 1)[-1].split("：", 1)[-1])
        elif lowered.startswith("时间") or lowered.startswith("发布时间") or lowered.startswith("原始时间") or lowered.startswith("date") or lowered.startswith("time"):
            current["date"] = clean_text(text.split(":", 1)[-1].split("：", 1)[-1])
        elif lowered.startswith("摘要") or lowered.startswith("summary") or lowered.startswith("导语"):
            current["summary"] = clean_text(text.split(":", 1)[-1].split("：", 1)[-1])
        elif current and "url" in current and "summary" not in current:
            # Body text after a URL match (e.g. 36kr flash body paragraphs)
            if len(text) > 20 and not text.startswith(("收藏", "阅 ", "评论", "分享", "微博", "微信", "![", "[](http")):
                current["summary"] = text

    flush()
    return articles


def parse_input(raw: str, default_source: str) -> List[Dict[str, object]]:
    parsed = parse_json_payload(raw, default_source)
    if parsed is not None:
        return parsed
    return parse_markdown_payload(raw, default_source)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize agent-reach text into structured AI news records.")
    parser.add_argument("--input", help="Path to raw agent-reach output. Reads stdin when omitted.")
    parser.add_argument("--source", required=True, help="Default source name when input items do not include it.")
    return parser.parse_args()


def read_input(path: Optional[str]) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    return sys.stdin.read()


def main() -> int:
    args = parse_args()
    raw = read_input(args.input)
    articles = parse_input(raw, args.source)
    payload = {
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "articles": articles,
        "total": len(articles),
        "source_group": "public-web",
        "requested_sources": [args.source],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
