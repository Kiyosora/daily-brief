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
    (8, "二十八年来最激进的一次下注，节奏一旦抬起来就很难降回去，考验的是耐心。"),
    (6, "第一份没有老黄站台的成绩单，市场看的不是数字，是他敢不敢继续押注。"),
    (5, "把烧掉的Token折成一张可放贷的凭证，AI烧钱速度催生了新的信贷生意。"),
    (11, "社交的差距看着只差一步，产品节奏和组织效率却是两个时代的问题。"),
    (3, "真正的价值在单位成本下降，存储便宜了才谈得上训练规模往上堆。"),
    (7, "退役发动机被改造成数据中心供电备件，供应链在替算力瓶颈找绕路方案。"),
]

# invest 保留 7 条（按重要性排序）
INVEST_KEEP = [
    (6, "这个数字成了参照系，后面想上市的AI公司都得先跟它对表。"),
    (3, "增长数据很亮眼，但八百多亿资本开支把自由现金流拖成了负数。"),
    (11, "一边解释上次为什么没加，一边预告下次一定要加，姿态比数据更鹰。"),
    (10, "抛售已经不看基本面只看流动性，这种状态下抄底和做空同样危险。"),
    (0, "进展快到自己设定的红线，这份披露比任何路演材料都说明问题。"),
    (1, "收入微降，毛利率却从六成四抬到六成八，利润靠的是成本控制。"),
    (2, "经调整利润同比塌了八成多，却还高于市场预期，AI投入的账大家算过了。"),
]

OUTFIT = (
    "上海今天阴，午后最高十一点五、清早最低三点九，眼下八点五，体感只有五点五，降水为零但风是干的。"
    "昼夜温差接近八度，棉质打底外搭羊毛开衫最省事，白天热了脱到单层，颈口塞件薄羽绒，"
    "下身配条厚一点的直筒长裤护住腿脚。"
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
