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
    (5, "整车毛利承压，往出行服务和智能化转移才是它的底牌逻辑。"),
    (9, "黄仁勋交棒后的首份财报，看点在路线图能否接住AI算力需求。"),
    (1, "AI制药一级市场热度未退，诺奖得主背书把融资速度推得更快。"),
    (0, "机器人进店试用接连失误，出货增长与真实岗位需求明显脱节。"),
    (7, "降价没换来客流，涨价却守住价格带，酒店业分化已成定局。"),
    (6, "美妆靠并购扩品类，收购容易，渠道与用户运营才是硬仗。"),
]

# invest 保留 8 条（按重要性排序）
INVEST_KEEP = [
    (2, "营收回增但资本开支冲到814亿，自由现金流转负是真正的代价。"),
    (4, "波斯湾再起交火，油价与避险资产的波动会先于外交进展定价。"),
    (6, "午后算力硬件点火带指数翻红，尾盘ETF放量显示资金在抄底。"),
    (5, "收紧财务担保等于抽走AI基建输血，高杠杆Neocloud先扛不住。"),
    (9, "AI需求把HBM4推向翻倍涨价，NAND却在二季度转入下行周期。"),
    (1, "两发火箭进入海射准备，民营商业航天的发射节奏在加密。"),
    (3, "央行购金和ETF资金流正在改写金价与实际利率的旧相关性。"),
    (10, "红果短剧负责人接手本地生活，抖音想把内容流量导进交易。"),
]

OUTFIT = (
    "上海今天多云转小毛毛雨，午后最高14.9°C、傍晚回落到11°C，降水概率93%，"
    "体感只剩8.9°C，湿度67%又潮。建议棉质风衣内搭薄针织，鞋子换成防水款替代麂皮，"
    "白天别急着脱外套，夜里加一件轻羽绒也不过分。"
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
