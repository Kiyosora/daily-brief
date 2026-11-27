#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽取跨班基线：从归档 html / 部署站点页里正则抽 <a class="n-title"> 已展示标题。"""
import re, json, pathlib, html as htmlmod

BASE = pathlib.Path(__file__).parent
BL = BASE / "baseline"
out = {}
all_titles = set()
for p in sorted(BL.glob("*.html")):
    raw = p.read_text(encoding="utf-8", errors="ignore")
    raw = htmlmod.unescape(raw)
    ts = [re.sub(r"<[^>]+>", "", t).strip()
          for t in re.findall(r'<a class="n-title"[^>]*>(.*?)</a>', raw, re.S)]
    ts = [t for t in ts if t and "esc(it.title)" not in t and "it.title" not in t]
    # 去重保序
    seen, uniq = set(), []
    for t in ts:
        if t not in seen:
            seen.add(t); uniq.append(t)
    out[p.name] = uniq
    all_titles.update(uniq)
(BASE / "baseline_titles.json").write_text(
    json.dumps({"per_file": out, "all": sorted(all_titles)}, ensure_ascii=False, indent=2),
    encoding="utf-8")
for k, v in out.items():
    print(f"{k}: {len(v)} 条")
print(f"=== 去重合计 {len(all_titles)} 条 ===")
