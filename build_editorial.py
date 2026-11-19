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
# business 保留 6 条（按重要性排序）
BUSINESS_KEEP = [
    (11, "利润再厚也得看现金进出，这篇质疑的不是增长，而是增长要花多少钱。"),
    (9, "从量产到工艺再到抢订单，融资只是起点，能迭代出下一代才是硬指标。"),
    (6, "英伟达掌门换人，供给端跟着生变，国产GPU的窗口和风险一起放大。"),
    (7, "门店越开越多、收入照涨，毛利却没跟上，扩张正在稀释单店的价值。"),
    (4, "同样的技术路线，决策前提和领导方式不同，结果就是两套完全不同的命运。"),
    (5, "平替把高端大衣的价格带打下来，商场正在重新给中产的体面定价。"),
]

# invest 保留 8 条（按重要性排序）
INVEST_KEEP = [
    (6, "开盘冲上去又回吐一半，市场的热情和定价的耐心同时露了底。"),
    (0, "为买芯片发债三百多亿，AI基建的钱已经开始靠杠杆往下铺。"),
    (2, "质疑的是客户融资的成色，年内翻过倍的筹码一旦松动，杀跌最重。"),
    (8, "美联储已经在给AI算通胀账，生产率红利还要等，需求端先来了。"),
    (10, "仓位低到五年谷底，空头一旦回补，这波反弹的燃料比基本面更足。"),
    (11, "营收、利润率、现金流三项都超预期，指引还上调，价格优势正在兑现。"),
    (7, "发射成本压下来，回收期缩到十几周，航天开始像一门基础设施生意。"),
    (1, "秘密令状要上公开法庭审，数据调取这条线上，苹果先赢下一局。"),
]

OUTFIT = (
    "上海今天晴，清早最低三点八，正午最高十一点五，眼下四度、体感接近零，湿度六成二，降水为零。"
    "晴冷干燥最怕起风失温，贴身层选细羊毛针织配高领打底，外层用棉质小翻领挡风就够，别急着上身厚羽绒；"
    "下身直筒加绒长裤配双不闷脚的皮面运动鞋，中午热了脱到单层也不打紧。"
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
    assert len(hide) + len(selected) == total, f"数量不匹配 {len(hide)}+{len(selected)}!={total}"
    assert 80 <= len(OUTFIT) <= 140, f"outfit 字数 {len(OUTFIT)} 越界"

    print(f"[ok] editorial.json written")
    print(f"     business 保留 {len(order['business'])} / invest 保留 {len(order['invest'])}")
    print(f"     comments {len(comments)} 条, hide {len(hide)} 条, outfit {len(OUTFIT)} 字")
    for t in hide:
        print(f"     hide: {t}")


if __name__ == "__main__":
    main()
