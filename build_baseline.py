#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽取跨班基线：从归档 html 里正则抽 <a class="n-title"> 已展示标题。

与历史 baseline_titles.json 做并集后写回 —— 归档节点会被定期删除，
所以基线必须固化在仓库里，否则跨班查重会漏掉老班次。

用法：
    python3 build_baseline.py            # 扫描 ./baseline/*.html 并写回 baseline_titles.json
    python3 build_baseline.py --print    # 顺便打印统计
"""
import re
import json
import pathlib
import html as htmlmod

BASE = pathlib.Path(__file__).parent
BL = BASE / "baseline"
STORE = BASE / "baseline_titles.json"


def extract(path: pathlib.Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = htmlmod.unescape(raw)
    ts = [re.sub(r"<[^>]+>", "", t).strip()
          for t in re.findall(r'<a class="n-title"[^>]*>(.*?)</a>', raw, re.S)]
    ts = [t for t in ts if t and "esc(it.title)" not in t and "it.title" not in t]
    seen, uniq = set(), []
    for t in ts:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def main() -> None:
    prev = {"per_file": {}, "all": []}
    if STORE.exists():
        try:
            prev = json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            prev = {"per_file": {}, "all": []}

    per_file = dict(prev.get("per_file") or {})
    all_titles = set(prev.get("all") or [])
    if BL.is_dir():
        for p in sorted(BL.glob("*.html")):
            ts = extract(p)
            per_file[p.name] = ts
            all_titles.update(ts)

    STORE.write_text(
        json.dumps({"per_file": per_file, "all": sorted(all_titles)},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"[ok] {STORE.name}: {len(all_titles)} 条去重标题（{len(per_file)} 个来源文件）")


if __name__ == "__main__":
    main()
