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
    (5, "免费助手转成按席位收费，企业场景先跑通付费路径，社交分发反而成了护城河。"),
    (1, "卡住无人驾驶的不是识别算法，是高速场景的准入责任与事故归属该怎么定。"),
    (2, "既收算力钱又持股的供应商，把未来十几年的订单提前折成了今天的股权。"),
    (9, "家政和护工的动作数据成了新商品，隐私边界和定价权都还悬着。"),
    (4, "版本号跟得再快也要开发者迁移，谷歌赌的是生态补齐而非单点领先。"),
    (0, "换帅同时抬出万亿目标，字节在赌内容流量能低成本转成到店消费。"),
]

# invest 保留 8 条（按重要性排序）
INVEST_KEEP = [
    (4, "抛售源头是AI资本开支的融资结构，估值和偿付能力被放在一起怀疑。"),
    (9, "分歧不在需求强弱，而在核心供应商的表外敞口收缩会不会传导给整条链。"),
    (7, "买的是扩散模型的人才和速度，开源侧要补的是生成能力。"),
    (11, "定价已被紧缩预期完全主导，实物需求被挤到一边，触发点只能来自政策端。"),
    (2, "新州长拿许可当筹码，二百多亿美元的数据中心要先过立法这道关。"),
    (5, "机器人被说成星链最大收入源，靠的是车载算力与带宽绑定的协同。"),
    (8, "成果归属和数据权限谈崩了，学术圈干脆绕开商业公司自建开源工具。"),
    (1, "从上市到右舵批量出口只用了两个月，海外订单的兑现速度值得盯住。"),
]

OUTFIT = (
    "上海今天晴，眼下八点六度体感五点六，清早三点七、正午十一点八，湿度近六成，降水为零。"
    "温差八度，早晚按深秋穿：贴身细羊毛针织配高领打底，外层棉质小翻领挡风即可，先别上身厚羽绒；"
    "下身直筒长裤配不闷脚的皮面运动鞋，中午热了脱到单层也不打紧。"
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
