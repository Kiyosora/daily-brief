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
    (5, "即时零售烧钱战收尾，补贴退坡腾出的预算转向算力与模型自研。"),
    (7, "后训练卡在思维链过长，瓶颈不在算力而在奖励设计与推理预算。"),
    (4, "利率高位叠加技术商业化进深水区，估值尺子从增长叙事换回现金流。"),
    (0, "抢的是产能与时间窗口，不是低价优势，面板产线改造周期才是稀缺来源。"),
    (6, "从玩具属性做到千万级下载，说明AI应用起量靠玩法直觉而非参数堆料。"),
    (1, "厂商从拼榜单转向补生态接口，商业化瓶颈在系统集成而非本体硬件。"),
]

# invest 保留 7 条（按重要性排序）
INVEST_KEEP = [
    (10, "监管调查叠加业绩担忧，资金从科技股撤向美债与贵金属，避险情绪全面升温。"),
    (3, "恐慌指数升至九分，趋势跟踪基金的被动卖盘尚未出清，短期波动难收敛。"),
    (11, "央行独立性受政治压力牵制，市场对降息路径的定价可能需要整体重估。"),
    (7, "连续加息仍在选项内，但留给家庭与企业缓冲期，急剧转向的空间被压缩。"),
    (1, "方案已降温，但软银押注存储说明AI算力焦虑正外溢到上游产能。"),
    (5, "形式化验证是硬门槛，源码公开不等于同行认可，数学界复核才决定分量。"),
    (9, "美墨接近达成而美加滞后，关税与供应链安排可能出现分叉。"),
]

OUTFIT = (
    "上海今天晴，午间十二点五度、体感十度，早晚最低三点三度、最高十三点二度，湿度四成三、无降水。"
    "昼夜温差近十度，早出晚归都得顶得住：内搭薄羊毛高领或美利奴保暖层，中午升温后正好脱到单层；"
    "外罩防风呢料或哑光棉服挡早晚凉意，羽绒先收着；下身直筒长裤配皮质短靴最省事。"
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
