#!/usr/bin/env python3
"""把本轮候选池对跨班基线做查重 + 事件簇识别。"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
data = json.loads((BASE / "data.json").read_text(encoding="utf-8"))
base = json.loads((BASE / "baseline_titles.json").read_text(encoding="utf-8"))
uniq = base["uniq"]

# 事件簇关键词 -> 簇名
CLUSTERS = {
    "黄仁勋": ["黄仁勋", "英伟达", "nvidia", "Nvidia"],
    "小米": ["小米"],
    "世界模型": ["世界模型", "World", "物理AI", "空间"],
    "苹果": ["苹果", "iPhone", "Apple"],
    "理想": ["理想"],
    "小鹏": ["小鹏"],
    "存储": ["存储", "NAND", "DRAM", "内存", "闪迪", "美光"],
    "美股AI交易": ["纳指", "费半", "美股", "标普", "AI交易", "英伟达跌", "Anthropic"],
    "韩国": ["韩国", "韩股"],
    "A股收盘": ["沪指", "创业板", "A股", "三大股指", "尾盘", "收复", "失守"],
    "机器人": ["机器人", "Robotaxi", "具身", "人形"],
    "Anthropic模型": ["Claude", "Opus", "Anthropic", "Sonnet"],
    "蚂蚁": ["蚂蚁", "阿福"],
    "Meta/OpenAI人才": ["Tibo", "OpenAI", "离职"],
}


def hit(title: str, keys: list[str]) -> bool:
    return any(k in title for k in keys)


print("=" * 78)
print("候选池查重（★ = 标题级已上过）")
print("=" * 78)
for cat in ("business", "invest"):
    print(f"\n########## {cat} ##########")
    for i, it in enumerate(data["news"][cat]):
        t = it["title"]
        exact = t in uniq
        partial = []
        for u in uniq:
            if t != u and (t[:18] == u[:18] or u[:18] == t[:18]):
                partial.append(u)
        clusters = [name for name, keys in CLUSTERS.items() if hit(t, keys)]
        flags = []
        if exact:
            flags.append("★标题已上")
        if partial:
            flags.append(f"≈近似已上:{partial[0][:24]}")
        if clusters:
            flags.append("簇:" + "/".join(clusters))
        mark = "★" if exact else (" " if not partial else "≈")
        print(f"[{mark}{i:2d}] {t}")
        print(f"      {it.get('source')} {it.get('published')}  {' | '.join(flags)}")

print("\n" + "=" * 78)
print("基线里出现过的高频关键词（判断事件簇饱和度）")
print("=" * 78)
for name, keys in CLUSTERS.items():
    c = sum(1 for u in uniq if hit(u, keys))
    if c:
        print(f"  {name}: {c} 条")
