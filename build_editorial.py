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
# 2026-11-27 12:00 班（12 点班：只归档，不部署）。
#
# 跨班查重基线（本轮重建，656 条去重标题）：
#   · git 历史 37 个 revision 的 editorial.json（comments+order+hide 全量）
#   · drive 归档 html 11 份（11-23-18 ~ 11-27-06）正则抽 n-title
#   · 分两层：displayed（实际展示过，308 条）/ pooled（只进过池未展示，656 条）
#
# ★ 本轮值得记的现象：
#   1) invest 池只有 12 条，且「投行看盘口径」严重扎堆：美银Hartnett(8888/7777/
#      6666)、德银(标普看9000)、瑞银交易员(AI股见底) 三条都是「又一家投行说
#      美股见顶或见底」，与基线 31 条美股AI交易簇正面重叠 → 三条全 hide。
#   2) A股收盘簇基线已 4 条展示 + 6 条进池，本轮 invest[0]「创业板大涨超3%、
#      AI算力掀涨停潮」正好撞上；页面行情条本来就要展示创业板+3.79% → hide，
#      避免同一份收盘行情在页面上讲两遍。
#   3) 「英伟达逼近死亡交叉」撞 27 条英伟达簇；「铠侠成日本最便宜蓝筹股」
#      撞 9 条存储簇 → 均 hide。
#   4) business 34 条里大量是软文/活动/评测/早报：乾崑共创计划、极客公园议程、
#      报名最后2天、早报×2、手机评测×4、鸿蒙小折叠电脑 → 全部 hide。
#   5) 黎曼簇本轮两条同事件（陶哲轩下场验证 / 381个AI直播证P=NP），后者基线
#      已进过池 → 整簇 hide。
#   6) 小鹏科技日（簇 6）、蔚来世界模型3.0（★已展示过）、Anthropic（19）、
#      华为折叠（4）、ChatGPT（3）均撞基线 → hide。
#   7) 全轮没有一条标题命中「displayed」基线，12 条精选全是新稿。
#   8) 两处「同一事件最多留 2 条不同角度」，刻意做成互补而非同源：
#      · 黑五：business[24]「直邮已死」（中国卖家被税单逼走）
#              + invest[2]「BNPL 213 亿」（美国消费者加杠杆）
#        —— 主体和机制都不同，不是同一事件的两篇同源稿。
#      · 芯片：business[18]「马云走进芯片时代」讲平头哥自研十年，
#        与基线 11 条芯片稿（多为存储/管制/并购）不同题。
#
# business 保留 6 条：比亚迪买欧洲工厂 / 马云进芯片 / AI Agent刷基准 /
#                      舜宇智行分红超净利 / 光伏反内卷 / 黑五直邮之死
BUSINESS_KEEP = [
    (12, "从整车出口到接手工厂，本地化产能成了出海下半场的通行证"),
    (18, "从云栖大会到平头哥办公区，十年两次押注是阿里的长周期赌局"),
    (7, "多智能体组队跑实验，查询总耗时降31%，跑分之外还得看稳定性"),
    (30, "分红总额超过三年净利，转身又要募资补流，钱的去向最该问清"),
    (27, "亏损周期里集体反内卷，押注储能、技术与AI能否熬出曙光"),
    (24, "两张税单逼退直邮卖家，能在新规则下活下来的才是真卖家"),
]

# invest 保留 6 条：工业企业利润 / 私募规模首降 / 圣诞网购BNPL /
#                    欧元兑人民币 / 套利交易失灵 / SpaceX送股
INVEST_KEEP = [
    (4, "10月单月增速比9月快5.7个点，采矿业38.8%领跑，重心在资源端"),
    (6, "连续15个月扩张后首次收缩，总规模缩水6000亿，量化与创投是推手"),
    (2, "先买后付一季花掉213亿，消费者用杠杆买圣诞，是需求还是透支"),
    (8, "欧元区对华逆差9月扩大18.5%，贸易顺差与利差两头在托人民币"),
    (9, "累计还涨6.8%却录得年内首个下跌月，高盛富国花旗齐喊超额收益收窄"),
    (3, "从一次性馈赠升级为年复一年的股权转移，SpaceX在提前铺散户股东盘"),
]

OUTFIT = (
    "上海此刻晴，18.2℃、体感16.6℃，午后最高19℃、清晨最低8.2℃，"
    "昼夜温差逾10℃；湿度53%，降水概率0%，干爽不闷。白天薄针织或衬衫"
    "单穿就够，风衣留给早晚；出门带件外套搭手臂，午间脱下也不显臃肿。"
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
    # 池内未选中的数量 = 候选池条数 - 选中数（stale 不在池内，单独统计）
    stale_in_pool = [t for t in stale if t in {r["title"] for v in news.values() for r in v}]
    pool_hidden = total - len(selected)
    assert len(hide) == pool_hidden + len(stale) - len(stale_in_pool), (
        f"hide 数量不匹配 {len(hide)} != {pool_hidden}+{len(stale)}-{len(stale_in_pool)}"
    )
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
