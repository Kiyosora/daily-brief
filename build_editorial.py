#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 editorial.json：comments / hide / order 统一以「新闻标题原文」为 key。

标题不手抄，一律按索引从 data.json 取，避免引号/标点转义错位。
带自检断言：order 去重、跨板块不串、评论全覆盖、字数区间、hide 与 order 不相交。
"""
from __future__ import annotations

import json
import pathlib

BASE = pathlib.Path(__file__).parent
DATA = json.loads((BASE / "data.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- 选题
# 2026-11-23 06:00 班。
#
# 本轮修复了 collect.py 的一个真实缺陷：分类内多来源合并时是「先到先得 + 截断」，
# 首个来源（钛媒体）会吃满 12 条配额，量子位/爱范儿永远进不了快照层；
# 而浏览器端实时层用的是各来源轮转合并。两者已对齐为同一套轮转算法，
# 快照层候选池从 12 条钛媒体变成 34 条（三源），可选面明显变宽。
#
# 跨班去重：已下载 11-21 06:00 / 11-21 18:00 / 11-22 06:00 / 11-22 12:00 / 11-22 18:00
# 五班归档 html，抽出实际展示标题（56 条去重后），与本轮候选池逐条比对。
#
# business 保留 6 条（按重要性排序）——量子位 3 条 + 钛媒体 3 条，兼顾 AI 硬新闻与非 AI 产业线索
BUSINESS_KEEP = [
    (22, "变形物体操控拿下全球首个全通，这类任务此前正是最难的坎。"),
    (30, "算力、模型服务和AI工具各自能辨认出收入，钱的去向开始分层。"),
    (27, "单笔金额不大，但数币在电力资金链上的通道被打通了。"),
    (25, "新项目由V1作者创立，主打能装在自己机器上的开源Agent。"),
    (1, "靠葡萄糖自发电驱动神经刺激，控糖从给药变成有源电路。"),
    (21, "印度靠莫尔比的产业集群和低价出口，一度反超中国。"),
]

# invest 保留 5 条（按重要性排序）
# 本轮 invest 源仍只有华尔街见闻一个，12 条里 9 条是近两班已上过线的旧稿，
# 全新稿只有 3 条（[0][1][2]）。按既定做法：全新稿优先，再补当天仍在发酵的两条主线
# ——[3] 跨资产去杠杆的主框架、[7] 政策临界点，各自只留一个角度，簇内不重复。
INVEST_KEEP = [
    (2, "F4会议后先备好稳定基金，回购限额松绑三个月待命。"),
    (1, "今年1月才从八成加到百分百，现在反向调回，11月30日施行。"),
    (3, "避险资产在最需要时反被抛售换现金，跨资产去杠杆正在发生。"),
    (0, "公司债加ABS的混合结构，替昂贵的AI芯片找到不压垮资产负债表的买单方。"),
    (7, "目标位标普6845点，距上周五收盘只剩约1.2%，框架正在变成现实。"),
]

OUTFIT = (
    "上海今天阴，体感十一度，午后最高十六度、入夜滑到十一度，湿度七成八，降水概率一成五。"
    "选厚棉质针织打底，外搭防风短羽绒，中长风衣偏薄撑不住湿冷；"
    "下身直筒长裤配厚袜短靴，备一条薄围巾。"
)


def main() -> None:
    news = DATA["news"]
    comments: dict[str, str] = {}
    order: dict[str, list[str]] = {"business": [], "invest": []}

    for cat, picks in (("business", BUSINESS_KEEP), ("invest", INVEST_KEEP)):
        items = news[cat]
        for idx, comment in picks:
            title = items[idx]["title"]
            comments[title] = comment
            order[cat].append(title)

    # hide = 所有未选中的条目（order 之外的必须全部进 hide，否则仍会显示）
    selected = set(order["business"]) | set(order["invest"])
    hide = [
        r["title"]
        for cat in ("business", "invest")
        for r in news[cat]
        if r["title"] not in selected
    ]
    # 再叠加「实时层缓存里还留着、直连 feed 已下架」的陈旧稿，
    # 它们不在候选池里，但会以无点评状态在实时层复活。
    stale = DATA.get("stale_titles") or []
    for t in stale:
        if t not in selected and t not in hide:
            hide.append(t)

    editorial = {"outfit": OUTFIT, "comments": comments, "hide": hide, "order": order}
    (BASE / "editorial.json").write_text(
        json.dumps(editorial, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---------------- 自检断言 ----------------
    assert 4 <= len(order["business"]) <= 6, f"business 保留 {len(order['business'])} 条，超出 4-6"
    assert 5 <= len(order["invest"]) <= 8, f"invest 保留 {len(order['invest'])} 条，超出 5-8"
    assert len(order["business"]) == len(set(order["business"])), "business order 有重复"
    assert len(order["invest"]) == len(set(order["invest"])), "invest order 有重复"
    assert not (set(order["business"]) & set(order["invest"])), "order 跨板块串了"
    assert len(comments) == len(order["business"]) + len(order["invest"]), "评论数与选中数不符"
    for t, c in comments.items():
        assert c.strip(), f"空评论: {t}"
        assert len(c) <= 45, f"评论超45字({len(c)}): {t} -> {c}"
        assert t not in c, f"评论复述标题: {t}"
    for t in order["business"] + order["invest"]:
        assert t in comments, f"选中但无点评: {t}"
    assert not (set(hide) & selected), "hide 与 order 有交集"
    total = sum(len(v) for v in news.values())
    pool_hidden = len(hide) - len([t for t in stale if t not in selected])
    assert pool_hidden + len(selected) == total, f"数量不匹配 {pool_hidden}+{len(selected)}!={total}"
    assert 80 <= len(OUTFIT) <= 140, f"outfit 字数 {len(OUTFIT)} 越界"

    print(f"[ok] editorial.json written")
    print(f"     business 保留 {len(order['business'])} / invest 保留 {len(order['invest'])}")
    print(f"     comments {len(comments)} 条, hide {len(hide)} 条, outfit {len(OUTFIT)} 字")
    print("     --- 保留项 ---")
    for cat in ("business", "invest"):
        for t in order[cat]:
            print(f"     [{cat}] {t}")
    print("     --- hide ---")
    for t in hide:
        print(f"     hide: {t}")


if __name__ == "__main__":
    main()
