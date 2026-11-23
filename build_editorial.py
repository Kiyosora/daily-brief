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
# 2026-11-23 12:00 班（12 点班：只归档，不部署）。
#
# 跨班查重：下载 11-21 06:00 / 11-21 12:00 / 11-21 18:00 / 11-22 06:00 /
# 11-22 12:00 / 11-22 18:00 / 11-23 06:00 共 7 班归档 html，正则抽出实际展示标题
# （去重后 80 条左右）作基线，与本轮 46 条候选池逐条比对。
#
# 本轮候选池：business 34 条（三源轮转合并后）、invest 12 条。
# 大量条目是软文或已被上一班上过：
#   · 软文/栏目稿：钛晨报、Fintech 周报、银行理财评级报告、涨停/跌停板荐股、
#     个人养老金标尺、植发钓具、Swisse、硅基员工 ToB 观察、迅合科技、剪映黑客松、
#     大学生黑客松、见闻历 —— 全部 hide。
#   · 跨班旧稿：GPT-6.2 Astra、Nature 电刺激控糖、DeepSeek V1 创业（11-23 06:00 已上）；
#     华为星芒（11-21 06:00）、姚顺雨 Reddit AMA（11-21 12:00，同一场 AMA）；
#     特朗普三度喊话黄仁勋（11-21 06:00 同事件簇）、铠侠/存储（11-22 18:00 存储簇）。
#   · 黎曼猜想簇已在 11-21 12:00 / 11-21 18:00 / 11-22 18:00 连续三班出现，本轮不再重复；
#     只保留同一位数学家的另一道千禧难题（Navier–Stokes），属不同事件。
#
# business 保留 6 条：今日融资 + 高性能计算顶奖 + 消费电子 + 两篇正经技术发布 + 数学新主张
BUSINESS_KEEP = [
    (18, "注册半年、本轮仅数千万美元，估值从20亿翻到50亿，吉利汽车跟投。"),
    (10, "中科大铁钼辅因子量子化学项目摘得戈登·贝尔奖，国产超集群首次登顶。"),
    (11, "供应链称升级A20芯片与主板结构，短板仍落在Siri那一层。"),
    (13, "50个真实群聊、8万条消息、2395道题，考的是记忆能否用对而非只记住。"),
    (19, "同题比对快近六倍，公开集十四万次请求中位响应仅94毫秒。"),
    (4, "这次是纳维耶-斯托克斯存在性，与黎曼并非一题，陶哲轩称策略清楚但待整理。"),
]

# invest 保留 7 条：今日全球与A股盘面 + 资金面 + 卖方框架 + 大厂基本面 + 产业进展 + 创业方法论
# 底部条件簇只留高盛一条框架（美银美林芯片触底与 11-21/11-22 的芯片股簇重复）；
# 快钱投降与见底条件分属买方资金流、卖方策略两个角度。
INVEST_KEEP = [
    (8, "韩股领跌三星重挫，MSCI新兴市场抹去全年涨幅，美股期货反而反弹。"),
    (5, "早盘AI硬件逆势拉升、宇树领涨，港股权重科网股同步走低。"),
    (11, "高盛主经纪显示基本面策略净杠杆降到一年最低1%，慢钱还留在场内。"),
    (6, "AI货币化、美联储转鸽、机构仓位下降，三个条件目前一个都没满足。"),
    (10, "谷歌搜索广告增速降到12%，苹果服务分成也由12%降至10%。"),
    (4, "视觉编码器升级后汽车与机器人共用训练数据，野村看好这条飞轮。"),
    (1, "他称补贴换量会把AI应用拖回上一代打法，得按六个月后的模型做。"),
]

OUTFIT = (
    "上海今天阴，午后有零星小雨，体感十四度上下，最高十六度、入夜滑到十一度，"
    "湿度六成七，降水概率两成。"
    "选细密棉针织打底配薄羽绒马甲，外层防泼水冲锋衣；下身直筒长裤加厚袜皮鞋，包里塞把折伞。"
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
    # 再叠加「实时层缓存里还留着、直连 feed 已下架」的陈旧稿，
    # 它们不在候选池里，但会以无点评状态在实时层复活。
    stale = DATA.get("stale_titles") or []
    for t in stale:
        if t not in selected and t not in hide:
            hide.append(t)

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
    pool_hidden = len(hide) - len([t for t in stale if t not in selected])
    assert pool_hidden + len(selected) == total, f"数量不匹配 {pool_hidden}+{len(selected)}!={total}"
    assert 80 <= len(OUTFIT) <= 140, f"outfit 字数 {len(OUTFIT)} 越界"

    print(f"[ok] editorial.json written")
    print(f"     business 保留 {len(order['business'])} / invest 保留 {len(order['invest'])}")
    print(f"     comments {len(comments)} 条, hide {len(hide)} 条, outfit {len(OUTFIT)} 字")
    print("     --- 保留项 ---")
    for cat in ("business", "invest"):
        for t in order[cat]:
            print(f"     [{cat}] {t}")
            print(f"        → {comments[t]}  ({len(comments[t])}字)")
    print("     --- hide ---")
    for t in hide:
        print(f"     hide: {t}")


if __name__ == "__main__":
    main()
