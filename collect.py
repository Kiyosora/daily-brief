#!/usr/bin/env python3
"""抓取今日简报所需的全部数据源，输出 data.json。

设计原则：
- 全部为确定性抓取，不依赖模型，任何单点失败都降级为空列表而不中断整体。
- 每个条目带稳定 id（便于模型点评与页面渲染对齐）。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch(url: str, timeout: int = 15, referer: str | None = None, retries: int = 3) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
            if referer:
                req.add_header("Referer", referer)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            for enc in ("utf-8", "gb18030", "gbk"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", "replace")
        except Exception as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(1.2 * (attempt + 1))
    raise last if last else RuntimeError("fetch failed")


def now_cn() -> dt.datetime:
    tz = dt.timezone(dt.timedelta(hours=8))
    return dt.datetime.now(tz)


# ---------------------------------------------------------------- 热榜解析
def parse_hot_md(text: str, limit: int) -> list[dict]:
    """解析 dataxapi 的 markdown 榜单表格。"""
    items = []
    row_re = re.compile(r"^\|\s*(\d+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([\d,\.]+)\s*\|\s*([^|]*?)\s*\|\s*$")
    for line in text.splitlines():
        m = row_re.match(line.strip())
        if not m:
            continue
        rank, title, link, heat, change = m.groups()
        title = html.unescape(title).strip()
        link = html.unescape(link).strip()
        heat_num = heat.replace(",", "")
        try:
            heat_int = int(float(heat_num))
        except ValueError:
            heat_int = 0
        items.append({
            "rank": int(rank),
            "title": title,
            "link": link,
            "heat": heat_int,
            "heat_text": format_heat(heat_int),
            "change": change.strip() or "—",
        })
    return items[:limit]


def format_heat(n: int) -> str:
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}亿"
    if n >= 10_000:
        return f"{n / 10_000:.1f}万"
    return str(n)


# ---------------------------------------------------------------- RSS 解析
def strip_tags(s: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse_rss(text: str, source: str, limit: int) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except Exception:
        return items
    nodes = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for node in nodes:
        def pick(*tags):
            for t in tags:
                found = node.find(t)
                if found is not None and found.text:
                    return found.text.strip()
                if t.startswith("{http://www.w3.org/2005/Atom}"):
                    found = node.find(t)
                    if found is not None:
                        link = found.get("href")
                        if link:
                            return link.strip()
            return ""
        title = strip_tags(pick("title", "{http://www.w3.org/2005/Atom}title"))
        link = pick("link", "{http://www.w3.org/2005/Atom}link")
        desc = strip_tags(pick("description", "{http://www.w3.org/2005/Atom}summary",
                               "{http://purl.org/rss/1.0/modules/content/}encoded"))
        pub = pick("pubDate", "{http://purl.org/dc/elements/1.1/}date",
                   "{http://www.w3.org/2005/Atom}updated")
        if not title:
            continue
        items.append({
            "source": source,
            "title": title,
            "link": link,
            "summary": desc[:220],
            "published": normalize_time(pub),
        })
    return items[:limit]


def normalize_time(raw: str) -> str:
    if not raw:
        return ""
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = dt.datetime.strptime(raw.strip(), fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
            return parsed.astimezone(dt.timezone(dt.timedelta(hours=8))).strftime("%m-%d %H:%M")
        except ValueError:
            continue
    return raw[:16]


# ---------------------------------------------------------------- 天气
WMO = {
    0: "晴", 1: "晴间多云", 2: "多云", 3: "阴", 45: "有雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨", 56: "冻毛毛雨", 57: "强冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨", 66: "冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "米雪",
    80: "阵雨", 81: "强阵雨", 82: "暴雨", 85: "阵雪", 86: "强阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷暴伴冰雹",
}


def collect_weather() -> dict:
    q = urllib.parse.urlencode({
        "latitude": CONFIG["city_lat"],
        "longitude": CONFIG["city_lon"],
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,is_day",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "hourly": "temperature_2m,weather_code",
        "timezone": CONFIG["timezone"],
        "forecast_days": 1,
    })
    data = json.loads(fetch(f"https://api.open-meteo.com/v1/forecast?{q}", timeout=15))
    cur = data.get("current", {})
    daily = data.get("daily", {})
    code = int(cur.get("weather_code", 0))
    dcode = int((daily.get("weather_code") or [0])[0])
    hourly_t = data.get("hourly", {}).get("temperature_2m") or []
    hourly_c = data.get("hourly", {}).get("weather_code") or []
    hourly_time = data.get("hourly", {}).get("time") or []
    hourly = []
    for i, (t, c) in enumerate(zip(hourly_t, hourly_c)):
        stamp = hourly_time[i] if i < len(hourly_time) else ""
        hourly.append({"time": stamp, "temp": t, "code": int(c)})
    return {
        "city": CONFIG["city"],
        "temp": cur.get("temperature_2m"),
        "feels_like": cur.get("apparent_temperature"),
        "humidity": cur.get("relative_humidity_2m"),
        "code": code,
        "desc": WMO.get(code, "未知"),
        "high": (daily.get("temperature_2m_max") or [None])[0],
        "low": (daily.get("temperature_2m_min") or [None])[0],
        "precip": (daily.get("precipitation_probability_max") or [None])[0],
        "day_code": dcode,
        "day_desc": WMO.get(dcode, "未知"),
        "hourly": hourly,
    }


def fallback_outfit(w: dict) -> str:
    if not w or w.get("temp") is None:
        return "天气数据暂不可用。"
    t = w["temp"]
    hi, lo = w.get("high") or t, w.get("low") or t
    desc = w.get("day_desc", "")
    bits = [f"{CONFIG['city']}今日{desc}，{lo:.0f}~{hi:.0f}°C"]
    if lo <= 5:
        bits.append("建议羽绒服/厚外套 + 保暖内搭，注意手脚保暖")
    elif lo <= 12:
        bits.append("建议风衣/夹克或针织衫 + 长裤，早晚加一件开衫")
    elif lo <= 20:
        bits.append("建议薄外套/卫衣 + 长裤，早晚温差大注意叠穿")
    elif lo <= 26:
        bits.append("建议短袖/薄长袖即可，备一件薄外套应对空调")
    else:
        bits.append("建议轻薄透气的夏装，注意防晒补水")
    if w.get("precip"):
        bits.append(f"降水概率 {w['precip']}%，记得带伞")
    if (hi - lo) >= 8:
        bits.append("昼夜温差较大，别只按中午温度穿")
    return "；".join(bits) + "。"


# ---------------------------------------------------------------- 行情
def collect_market() -> list[dict]:
    secs = ",".join(CONFIG["market_symbols"])
    url = ("https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f2,f3,f4,f12,f14"
           f"&secids={secs}&fltt=2&invt=2")
    try:
        data = json.loads(fetch(url, timeout=15, referer="https://quote.eastmoney.com/"))
    except Exception as exc:
        print(f"[warn] market failed: {exc}", file=sys.stderr)
        return []
    out = []
    for row in (data.get("data") or {}).get("diff") or []:
        value = row.get("f2")
        pct = row.get("f3")
        if not isinstance(value, (int, float)) or value in (None, "-"):
            continue
        out.append({
            "name": row.get("f14"),
            "code": row.get("f12"),
            "value": value,
            "pct": pct if isinstance(pct, (int, float)) else 0,
            "change": row.get("f4") if isinstance(row.get("f4"), (int, float)) else 0,
        })
    return out


# ---------------------------------------------------------------- 主流程
def main() -> None:
    now = now_cn()
    limit = CONFIG.get("hot_limit", 12)
    nlimit = CONFIG.get("news_limit", 8)
    # 每个来源抓取深度：与浏览器端实时层 rss2json count=12 对齐
    depth = 12
    # 分类候选池上限：静态快照层会按 hide 过滤展示，留出足够挑选空间
    pool_cap = max(nlimit, 36)

    hot: dict[str, list] = {}
    for src in CONFIG["hot_sources"]:
        try:
            hot[src["key"]] = parse_hot_md(fetch(src["url"], timeout=20), limit)
        except Exception as exc:
            print(f"[warn] hot {src['key']} failed: {exc}", file=sys.stderr)
            hot[src["key"]] = []

    # 按来源分桶抓取（每个来源都抓满 depth，候选池才有多样性）
    news: dict[str, list] = {"business": [], "invest": []}
    groups: dict[str, list[list]] = {}
    by_site: dict[str, list] = {}
    for src in CONFIG["rss_sources"]:
        try:
            got = parse_rss(fetch(src["url"], timeout=20), src["site"], depth)
        except Exception as exc:
            print(f"[warn] rss {src['site']} failed: {exc}", file=sys.stderr)
            continue
        for item in got:
            # id 用标题哈希，跨轮次稳定（RSS 更新不会让同一��目换 id）
            digest = hashlib.md5(item["title"].encode("utf-8")).hexdigest()[:6]
            item["id"] = f"{src['key'][:2]}{digest}"
        groups.setdefault(src["key"], []).append(got)
        by_site[src["site"]] = got
    # 轮转合并各来源：与浏览器端实时层的合并算法保持一致，
    # 避免首个来源（钛媒体）吃满配额、量子位/爱范儿永远进不了快照层。
    # 每个分类总量封顶，避免候选池无限膨胀。
    for key, buckets in groups.items():
        merged: list = []
        idx = 0
        while len(merged) < pool_cap and any(idx < len(b) for b in buckets):
            for b in buckets:
                if idx < len(b) and len(merged) < pool_cap:
                    merged.append(b[idx])
            idx += 1
        news[key] = merged

    # 实时层（浏览器端）用 rss2json 读同一批 RSS，它带缓存，可能还留着
    # 本站直连 feed 已经下架的旧稿。把「实时层有、直连 feed 已无」的标题标成陈旧，
    # 统一进 hide，免得陈旧或重复稿在实时层里以无点评状态复活。
    stale_titles: list[str] = []
    for src in CONFIG["rss_sources"]:
        fresh = {it["title"] for it in by_site.get(src["site"], [])}
        if not fresh:
            continue
        try:
            api = ("https://api.rss2json.com/v1/api.json?count=12&rss_url="
                   + urllib.parse.quote(src["url"], safe=""))
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            js = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore"))
            live = {(i.get("title") or "").strip() for i in (js.get("items") or [])}
        except Exception as exc:
            print(f"[warn] rss2json {src['site']} failed: {exc}", file=sys.stderr)
            continue
        for t in sorted(live - fresh):
            if t:
                stale_titles.append(t)

    try:
        weather = collect_weather()
    except Exception as exc:
        print(f"[warn] weather failed: {exc}", file=sys.stderr)
        weather = {}

    try:
        market = collect_market()
    except Exception as exc:
        print(f"[warn] market failed: {exc}", file=sys.stderr)
        market = []

    data = {
        "generated_at": now.isoformat(),
        "date_label": f"{now.year}年{now.month}月{now.day}日 {['周一','周二','周三','周四','周五','周六','周日'][now.weekday()]}",
        "time_label": now.strftime("%H:%M"),
        "site_title": CONFIG["site_title"],
        "weather": weather,
        "outfit_fallback": fallback_outfit(weather),
        "hot": hot,
        "hot_meta": {s["key"]: s["name"] for s in CONFIG["hot_sources"]},
        "market": market,
        "news": news,
        "stale_titles": stale_titles,
    }

    out = BASE / "data.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] data.json written: hot={sum(len(v) for v in hot.values())} "
          f"news={sum(len(v) for v in news.values())} market={len(market)} "
          f"weather={'ok' if weather else 'fail'} stale={len(stale_titles)}")


if __name__ == "__main__":
    main()
