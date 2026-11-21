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
    (0, "战略连番重排说明落地路径没跑通，AI资源分配仍在试错阶段。"),
    (11, "AI相关收入被单列成可披露口径，云厂商的变现路径开始被验证。"),
    (6, "赚的是算力转售与套利差价，供给一多就迅速被挤成红海。"),
    (5, "印尼供给政策松动叠加AI需求预期回落，供需两端同时向下定价。"),
    (7, "免税门槛压到150欧以下再叠加处理费，低价小包的成本优势直接消失。"),
    (2, "潮玩与现制饮品抢同一批年轻客群和商场流量，扩张节奏会互相牵制。"),
]

# invest 保留 7 条（按重要性排序）
INVEST_KEEP = [
    (10, "一周蒸发四万亿美元且跌幅陡峭，杠杆出清比情绪退潮更关键。"),
    (8, "三大支柱同时松动，芯片是AI交易最拥挤的一环，踩踏也最深。"),
    (5, "高盛交易主管定性为全面清仓而非轮动，警惕流动性收缩接力。"),
    (4, "租金涨的是资金成本不是需求，信贷一收紧供给就先塌。"),
    (11, "1700万行Lean代码可复核，但正式承认仍要过同行评审这一关。"),
    (0, "期限压到元旦前，基辅担心被推向一份以俄方条件为基础的协议。"),
    (2, "只说巨额税费不说明落地方式，悬着的政策本身就是不确定性。"),
]

OUTFIT = (
    "上海今天晴，当前九点七度、体感七点五，湿度六成二、无降水，早晚最低三点三度、午后最高十三点四度。"
    "昼夜温差十度出头，风一吹就凉：内搭选薄羊毛高领或美利奴保暖层，午后升温脱到单层即可；"
    "外罩防风呢料大衣挡早晚凉意，羽绒先收着；下身直筒长裤配短靴，走动不闷脚。"
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
