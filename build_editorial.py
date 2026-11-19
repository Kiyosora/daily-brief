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
    (1, "收入结构从卖方案转向车队运营，估值逻辑更像出行服务商，重资产扩张会压住现金流。"),
    (3, "周畅离职后嫡系上位，路线之争已定，接下来看10万亿怎么拆到业务线。"),
    (2, "潮玩被当成正经生意做反而熄火，说明这门生意的门槛不在IP而在渠道。"),
    (10, "高储蓄是过去高增长模式留下的遗产，住房与养老预期才是真正的蓄水池。"),
    (4, "一边分红一边募资、第一大客户占近七成，这套组合拳经不起交易所问询。"),
    (5, "同轮融资新老股价格差近一倍，上市审核大概率会把定价公允性列为重点。"),
]

# invest 保留 7 条（按重要性排序）
INVEST_KEEP = [
    (3, "云增速跳到35%、AI应用使用量领先，但算力吃紧已经在拖模型迭代。"),
    (8, "剔除AI投入利润还在涨，说明这轮不是需求问题，是投入节奏和现金流的问题。"),
    (11, "超预期财报接不住股价，市场在定价的不再是业绩，而是换帅后的执行不确定性。"),
    (4, "AI公司按1.5万亿估值挂牌，是给整个赛道重新定锚，同日游戏预购也在抢注意力。"),
    (0, "机构在减仓科技股、系统性策略却开始回补，散户被推到最后一棒的位置。"),
    (7, "360亿增量资金已建完仓，11月23日上市那天的换手压力值得关注。"),
    (5, "五十年头一次公开清仓退场，这位老手对估值的判断比观点本身更值得看。"),
]

OUTFIT = (
    "上海今天晴，午后最高11.3°C、清早最低3.9°C，体感只有7°C，降水为零但风里发干。"
    "昼夜温差七度以上，棉质衬衫打底外搭羊毛开衫，白天可脱到单层，"
    "晨晚加一件薄羽绒压住颈口，配条厚一点的直筒长裤护住腿脚。"
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
