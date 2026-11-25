#!/usr/bin/env python3
"""只补抓 invest 分类（华尔街见闻）RSS，并合并回 data.json。
主 collect.py 因网络超时漏掉 invest 源时使用。
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import collect

BASE = Path(__file__).resolve().parent
UA = collect.UA
SRC = "https://dedicated.wallstreetcn.com/rss.xml"
SITE = "华尔街见闻"


def grab(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    got = collect.parse_rss(text, SITE, 12)
    for it in got:
        digest = hashlib.md5(it["title"].encode("utf-8")).hexdigest()[:6]
        it["id"] = f"in{digest}"
    return got


def main() -> None:
    data = json.loads((BASE / "data.json").read_text(encoding="utf-8"))
    got = grab(BASE / "wscn.xml")
    if not got:
        print("[fail] invest rss parse empty", file=sys.stderr)
        sys.exit(1)
    data["news"]["invest"] = got
    print(f"[ok] invest refreshed: {len(got)} 条")

    # 该源的 stale 扫描（与 collect.py 同算法）
    fresh = {it["title"] for it in got}
    stale = []
    try:
        api = "https://api.rss2json.com/v1/api.json?count=12&rss_url=" + urllib.parse.quote(SRC, safe="")
        req = urllib.request.Request(api, headers={"User-Agent": UA})
        js = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore"))
        live = {(i.get("title") or "").strip() for i in (js.get("items") or [])}
        stale = sorted(live - fresh)
    except Exception as exc:
        print(f"[warn] rss2json {SITE} failed: {exc}", file=sys.stderr)

    existing = data.get("stale_titles", [])
    for t in stale:
        if t not in existing:
            existing.append(t)
    data["stale_titles"] = existing
    print(f"[ok] stale_titles: {len(existing)} (含 invest 源新扫 {len(stale)} 条)")

    (BASE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] data.json: news.invest={len(got)} market={len(data.get('market',[]))}")


if __name__ == "__main__":
    main()
