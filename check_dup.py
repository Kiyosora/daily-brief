#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本轮候选池对跨班基线做查重 + 事件簇识别。

基线格式（build_baseline.py 产出）：
  · displayed —— 上一批班次实际展示过的标题，★ = 硬红线，命中即不再展示
  · pooled    —— 进过候选池但被 hide 的标题，用来判断事件簇饱和度
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
data = json.loads((BASE / "data.json").read_text(encoding="utf-8"))
base = json.loads((BASE / "baseline_titles.json").read_text(encoding="utf-8"))
displayed = set(base.get("displayed") or base.get("uniq") or [])
pooled = set(base.get("pooled") or base.get("uniq") or [])

# 事件簇关键词 -> 簇名
CLUSTERS = {
    "黄仁勋": ["黄仁勋", "英伟达", "nvidia", "Nvidia"],
    "小米": ["小米"],
    "世界模型": ["世界模型", "World", "物理AI", "空间"],
    "苹果": ["苹果", "iPhone", "Apple"],
    "理想": ["理想"],
    "小鹏": ["小鹏"],
    "存储": ["存储", "NAND", "DRAM", "内存", "闪迪", "美光", "铠侠"],
    "美股AI交易": ["纳指", "费半", "美股", "标普", "AI交易", "英伟达跌", "Anthropic", "德银", "美银", "华尔街", "加息", "泡沫"],
    "韩国": ["韩国", "韩股"],
    "A股收盘": ["沪指", "创业板", "A股", "三大股指", "尾盘", "收复", "失守", "涨停"],
    "机器人": ["机器人", "Robotaxi", "具身", "人形"],
    "Anthropic模型": ["Claude", "Opus", "Anthropic", "Sonnet"],
    "蚂蚁": ["蚂蚁", "阿福"],
    "Meta/OpenAI人才": ["Tibo", "OpenAI", "离职"],
    "黎曼": ["黎曼", "P=NP", "陶哲轩", "形式化"],
    "马斯克": ["马斯克", "SpaceX"],
    "阿里": ["阿里", "平头哥", "淘宝", "阿里云"],
    "芯片": ["芯片", "半导体", "晶圆"],
    "AI算力": ["AI算力", "算力", "科创50", "恒科"],
    "ChatGPT/OpenAI": ["ChatGPT", "OpenAI"],
    "手机": ["手机", "iPhone", "小米", "荣耀", "OPPO", "华为"],
    "早报": ["早报", "早餐"],
    "医药": ["医药", "创新药", "艾伯维", "制药"],
    "光伏": ["光伏", "储能", "组件"],
    "消费": ["网购", "零售", "黑五", "圣诞", "消费"],
}


def hit(title: str, keys: list[str]) -> bool:
    return any(k in title for k in keys)


print("=" * 78)
print("候选池查重（★ = 展示过·硬红线 | ○ = 只进过池）")
print("=" * 78)
for cat in ("business", "invest"):
    print(f"\n########## {cat} ##########")
    for i, it in enumerate(data["news"][cat]):
        t = it["title"]
        flags = []
        if t in displayed:
            flags.append("★展示过")
        elif t in pooled:
            flags.append("○进过池")
        partial = [u for u in displayed if u != t and (t[:16] == u[:16] or u[:16] == t[:16])]
        if partial:
            flags.append(f"≈近似:{partial[0][:24]}")
        clusters = [name for name, keys in CLUSTERS.items() if hit(t, keys)]
        if clusters:
            flags.append("簇:" + "/".join(clusters))
        mark = "★" if t in displayed else ("○" if t in pooled else " ")
        print(f"[{mark}{i:2d}] {t}")
        print(f"      {it.get('source')} {it.get('published')}  {' | '.join(flags) if flags else '-'}")

print("\n" + "=" * 78)
print("事件簇在基线中的饱和度（displayed 实际展示过 / pooled 进过池）")
print("=" * 78)
for name, keys in CLUSTERS.items():
    d = sum(1 for u in displayed if hit(u, keys))
    p = sum(1 for u in pooled if hit(u, keys))
    if d or p:
        print(f"  {name}: 展示过 {d} / 进过池 {p}")
