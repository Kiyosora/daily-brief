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
# business 保留 5 条（按重要性排序）
# 2026-11-22 06:00 班：钛媒体 business 源里有 8 条是 11-21 18:00 班已上过线的旧稿，
# 本轮只挑本次新发布且未展示过的条目，避免同一批稿连续两班重复。
BUSINESS_KEEP = [
    (5, "从出口转向本地建厂，印度市场考的是供应链掌控与落地速度。"),
    (7, "销量还能涨但毛利被价格战吃掉，行业进入以钱换份额阶段。"),
    (1, "报表变好看不等于价值变厚，版权沉淀与付费黏性才是长期变量。"),
    (3, "流量能拉起一轮热度，接不接得住要看单店模型和供应链议价。"),
    (0, "生成能力已经不稀缺，稀缺的是能定价的真实场景和交付闭环。"),
]

# invest 保留 7 条（按重要性排序）
# 同簇规则：美股崩盘簇只留「全景」+「结构性」两个不同角度。
INVEST_KEEP = [
    (11, "AI叙事退潮叠加流动性收紧，估值锚从增长切回盈利。"),
    (0, "算力供给受电力与产能双重约束，大厂开始用二供压价。"),
    (9, "半导体指数单周跌幅创二十年之最，拥挤交易的踩踏最惨。"),
    (8, "交易规模远超软银自身资产负债表，融资方案就是最大变数。"),
    (7, "形态相似不等于路径复制，杠杆水平和政策空间都不相同。"),
    (2, "政治表态与实际谈判进度脱节，短期难改贸易安排的僵局。"),
    (4, "首日流水刷新纪录，验证的是成熟IP叠加等待周期的组合效应。"),
]

OUTFIT = (
    "上海今天晴转多云，早晨五点九度、体感三点一度，湿度七成九、无降水，"
    "最低五点六度、午后最高十五点六度。早晨体感偏凉但湿度高，"
    "穿薄羊绒高领打底加一件防风夹克，午后升温到十五度左右脱成单层即可；"
    "下身直筒牛仔裤配短靴，湿冷路面走起来也不闷脚。"
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
