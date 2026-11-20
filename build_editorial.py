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
    (4, "AI需求已连续十三个季度三位数增长，云的资本开支正在被真实用量接住。"),
    (9, "利润率已站上两位数，真正的考题是这份利润跑不跑得赢资本开支。"),
    (5, "外资零售巨头在华电商过半，胜负手会从门店数量转向履约成本。"),
    (6, "登顶靠的是外部模型的集成能力，自研与商业化之间的账还没算平。"),
    (8, "同时绑定英伟达与摩尔线程，是分散供应商风险，还是让估值锚更模糊？"),
    (10, "默沙东这轮退场说明专利悬崖逼近，后来者要拼的是适应症而非同靶点。"),
]

# invest 保留 7 条（按重要性排序）
INVEST_KEEP = [
    (0, "监管盯的是收入确认口径；估值锚从叙事换回现金流，跌幅才讲得通。"),
    (3, "全球股市连跌七日创三年最长，AI交易的分歧已从估值吵到现金流。"),
    (4, "首日光环一天耗尽，说明边际买盘只认首日，之后要靠业绩接棒。"),
    (1, "白宫公开施压既是筹码也是信号，董事会独立性与外部干预的边界更模糊。"),
    (6, "新一轮打击若落地，油价与避险资产会先动，亚洲市场开盘最敏感。"),
    (9, "签证不确定性比薪资更致命，硅谷的用工成本与创新节奏都会被抬高。"),
    (11, "十年节点重启新系列，鸿蒙的AI入口是想抢下一个设备周期的门票。"),
]

OUTFIT = (
    "上海今早晴，眼下三点二度、体感零点三度，清晨三点一度、正午十三点三度，湿度八成六、降水为零。"
    "昼夜温差十度，体感接近初冬：贴身薄羊毛高领打底，外罩哑光棉服或厚呢大衣挡风，厚羽绒先收着；"
    "下身直筒长裤配防滑皮面鞋，中午热了脱到单层也不打紧。"
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
