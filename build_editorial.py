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
# 2026-11-22 12:00 班。
# 跨班去重：11-22 06:00 班与 11-21 18:00 班的选题清单已逐一比对，
# 重复稿（2026年AI能有什么用/腾讯音乐/奶茶第一股/中国车企在印度/马化腾改腾讯AI航道/
# 泡泡玛特瑞幸/数智周报/郭明錤TPU/英国入欧/GTA6/特朗普俄乌/特朗普数据中心税/Anthropic黎曼）
# 全部进 hide，本轮只留新发布或换了角度的条目。
# business 保留 5 条（按重要性排序）
BUSINESS_KEEP = [
    (3, "数据中心抢稳定电力，气电调峰与东数西算的账本一起重算。"),
    (0, "输液大王执掌三十载后交棒二代，科伦进入家族接班考验。"),
    (2, "海外已成单极，国内形态与定价各走各路，规模优势尚未出现。"),
    (4, "由缺粮变成压价难题，库存高企反推出口价上涨，过剩第一次反噬。"),
    (1, "图像生成从尝鲜走向批量商用，比拼的是一致性而不是单张惊艳。"),
]

# invest 保留 5 条（按重要性排序）
# Anthropic 一条只留「承销团被套」角度，与 11-21 06:00 班的股价视角分开。
INVEST_KEEP = [
    (0, "标普6845就是逼美联储收手的价位，距触发仅80点，市场被逼到墙角。"),
    (6, "富国24日生效的新协议把智能体误操作算作客户授权，责任归用户。"),
    (3, "史上最大IPO次日砸盘，承销团骑虎难下，AI板块跟着蒸发4万亿。"),
    (5, "下周三PCE与GDP修正值同日出炉，核心PCE若破3.2%继续压制科技股。"),
    (4, "云南122家农信法人合并成一家银行，1.4万亿农信资产整体承继。"),
]

OUTFIT = (
    "上海今天晴，早晨五度、午后十五度，傍晚又滑回十度；湿度四成三、无降水，"
    "白天干爽，风一吹就凉。上身穿薄羊绒或羊毛混纺针织开衫，内搭纯棉长袖，"
    "下身直筒牛仔裤配灯芯绒，脚下短靴保住脚踝。午后进室内脱掉外套即可，别一早就穿太厚。"
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
