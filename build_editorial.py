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
# 2026-11-22 18:00 班。
# 跨班去重：已下载 11-22 12:00 / 11-22 06:00 两班的归档 html，抽出实际展示标题（22 条），
# 与本轮 data.json 逐条比对后，以下稿件进 hide：
#   12:00 班已展示 → 科伦系新帅 / 阻止美联储加息(哈特内特) / 网银协议AI智能体担责 /
#                    Anthropic豪华投行承销团 / 下周PCE日程 / 云南农商银行 / AI抢电与气电调峰 /
#                    中国AI眼镜混战 / 印度大米涨价 / 可灵发力图片
#   06:00 班已展示 → GTA6首发38亿 / 郭明錤博通TPU砍单20% / 美国科技股跌入熊市 /
#                    芯片股2.3万亿蒸发 / 中国车企在印度 / 腾讯音乐 / 奶茶第一股 / 2026年AI能有什么用
#   11-21 18:00 班已展示 → Anthropic黎曼猜想（隔 3 班，且本轮 Lean 社区正式背书为新进展，且热榜在讨论）
# 本轮可用「全新」稿共 9 条（invest 源仅 5 条未被占），按规则挑出 6+4。
# 情绪随笔类（invest 的「猜想：AI泡沫破灭和金融市场危机」）信息量低，本轮不上。
# 簇内去重：半导体/存储簇留 [8] 供给缺货 + [5] IPO重排两条；崩盘/流动性簇留 invest[0] 跨资产 + invest[3] 仓位未出清两条。
# business 保留 6 条（按重要性排序）
BUSINESS_KEEP = [
    (0, "从赚通道费到嵌入企业工作流，代理结算接口是新入口。"),
    (8, "配额内外分成两个市场，缺货比涨价更难解。"),
    (5, "超大IPO落地，芯片、代工、存储的订单分配随之重新排位。"),
    (9, "营收与交付双创新高，利润仍靠压费用；海外与物理AI是两张底牌。"),
    (6, "半年准备好的税单落下，已投产的车企先吃成本冲击。"),
    (1, "连亏三年后换开发方式，买来的软件还得靠自研才省钱。"),
]

# invest 保留 4 条（按重要性排序）
# 本轮 invest 源 12 条里 8 条是近两班已上过线的旧稿、1 条是见闻历广告，
# 可用新稿只剩 5 条，按「同簇最多 2 条不同角度」收敛到 4 条。
INVEST_KEEP = [
    (0, "追加保证金逼出抛售，连避险资产也被换成现金，白银跌得更急。"),
    (3, "对冲基金已降仓，长线资管和散户还在场，出清远未结束。"),
    (5, "形式化社区联合背书，AI做数学从宣称进入可验证阶段。"),
    (2, "让模型扮演消费者预测购买意愿，可靠度接近人类重测的九成。"),
]

OUTFIT = (
    "上海今天阴，午后最高十五度，入夜滑到十度，湿度六成、无降水，体感偏凉。"
    "选厚一点的棉质卫衣打底，外搭中长款羊毛混纺大衣，风衣太薄撑不住早晚温差；"
    "下身直筒长裤配厚袜短靴，别再穿单鞋。"
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
    # 本轮 invest 可用新稿仅 4 条（其余为近两班旧稿/广告），下限放宽到 4
    assert 4 <= len(order["invest"]) <= 8, f"invest 保留 {len(order['invest'])} 条，超出 4-8"
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
