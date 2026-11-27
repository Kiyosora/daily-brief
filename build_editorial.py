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
# 2026-11-28 06:00 班（06 点班：只归档，不部署）。
#
# 跨班查重基线：
#   · 仓库 baseline_titles.json 已固化 14 班 / 170 条去重「已展示」标题
#     （含新补的 11-27 18:00 归档 → build_baseline.py 跑出 170 条）
#   · 抽标题正则 <a class="n-title"[^>]*>(.*?)</a>，逐班核对最近五班清单
#
# ★ 本轮值得记的现象：
#   1) 标题级撞车 6 条：business[7] 韦东奕 / [22] AI Agents ClickBench / [23] 支付宝车载 /
#      [24] DeepSeek 226万亿Token / [27] 车企二手车残值 / [30] 爱奇艺破发 → 全部 hide。
#      其中 [23] 支付宝车载与 invest[10]「支付宝加码车载支付」是同一事件（广州车展 3.0），
#      且 11-27 18:00 班已展示过 → 跨板块一并 hide。
#   2) **LME 铝逼空撞车（险过）**：invest[5]「从铝市场逼空到LME紧急干预」看着是全新机制，
#      但基线里 11-25 06:00 班已展示「铝现货升水大幅收窄：LME收紧持仓规则，
#      干预数十年来最严重逼仓行情」→ 同一事件，必须 hide。
#      **教训：题目里带「LME」「逼空」这种专业词时，务必回基线全文搜一遍，别只看标题印象。**
#   3) invest[7]「日本烟草大涨」看着新，实际 11-27 06:00 班已展示
#      「英国帝国品牌大涨！美国奥驰亚考虑现金收购，日本烟草也在评估竞购」→ hide。
#   4) business[13] 与 business[19] 是同一事件：蚂蚁灵波 11-27 发布 LingBot-Map 2.0 +
#      LingBot-Navi（量子位同日两篇稿）。该事件在基线里从未展示过（18:00 班只留了评论、
#      没进最终 order）→ 属首秀，可以上，只留信息更全的 [19]。
#   5) **SHEIN 主动放弃**：business[12]「破发三个月，估值修复拐点」硬事实很足
#      （11-27 收 35.34 港元 vs 发行价 48.56、Q3 经调整净利 7.9 亿美元 +26.8%、
#      履约费用率 50.4%→45.7%、基石认购 22.1%），但基线 11-26 12:00 已展示
#      「SHEIN三季度盈利回升，欧洲市场寻求2027年下半年复苏」→ 同公司同财报的估值簇，跨班重复，hide。
#      宁少留一条，也不破坏「基线出现过就不再上」的纪律。
#   6) 广州车展稿成片（[2][5][8][11][14][17][20][26][31][33] 共 10 条）+ 软文（[0] 消研所周报、
#      [9] UV打印机众筹、[16] 钛动×腾讯云、[28] 具身抱团回应、[29] Claude Opus 做PPT、
#      [32] 35岁危机）→ 全部 hide。
#   7) invest[4]「标普19个月最佳一周…黄仁勋回归」是黄仁勋簇复盘稿，基线已 7 条 → hide；
#      invest[2] 是同一周交易日的**收盘**数据（标普收 7297.49、本周 +5.6%），
#      与基线里的盘前稿不是同一数据点，可上，评论只写收盘与周线，不复述「AI交易回暖」。
#   8) invest[1] 金属大反攻：伦铜九个月最大日涨 + 白银近8%，与基线「有色金属爆发」（A股早盘）
#      不同市场、不同交易日，且给了「中国稳市信号→商品」这条新因果链 → 上。
#
# business 保留 6 条：卫星互联网军备 / 蚂蚁灵波空间记忆 / 线上线下剥离资产 /
#                      泰晶科技定增 / Agent村社交实验 / 红果进客厅大屏
BUSINESS_KEEP = [
    (15, "一超一万颗在轨、订阅1360万；欧洲工厂月产500颗、FCC放行百万颗算力卫星"),
    (19, "纠偏写进模型内部而非外挂后端，1.0开源后Star近1.9万，7个数据集9项评测"),
    (3, "标的净资产2888万卖7382万，原实控人接盘易主时的兜底条款，第三期股份2027年中交割"),
    (6, "高位69.35元减持、低位21.43元定增10.11亿，3.83亿投随州与越南北宁扩产"),
    (18, "239个Agent跑四周烧175亿Token，572次推荐只有147次被接受"),
    (21, "日活1.68亿已超爱优腾芒合计1.55亿，字节正招OTT端产品经理，AI漫剧横屏正好适配"),
]

# invest 保留 6 条：美股收盘 / 金属反攻 / 美国贸易逆差 / OpenAI诉苹果 /
#                   黑五K型分化 / 美军云平台被黑
INVEST_KEEP = [
    (2, "标普收7297.49，本周累涨5.6%创19个月最大周涨幅，中概涨3.02%"),
    (1, "伦铜收涨3.2%创九个月最大日涨，沪铜主力+5.5%，白银期货涨近8%，稳市信号外溢"),
    (0, "逆差扩大10.7%至1495亿美元，进口3653亿创1992年以来最高"),
    (3, "指控苹果以一切可用手段不公平竞争并阻断其供应商渠道"),
    (8, "高盛调查千名消费者：年收入10万美元以上家庭50%加开销，5万美元以下48%要砍"),
    (9, "军方最大云平台之一首次公开披露被突破，事发于升级期间，是否取数仍未确认"),
]

OUTFIT = (
    "上海此刻晴、午后转阴，7.2℃、体感4.3℃，清晨最低6.5℃、白天最高15.2℃，"
    "湿度73%、降水概率几乎为零。清晨风凉，呢料大衣内搭薄羽绒最稳妥；"
    "午后回暖，卫衣叠衬衫就够，昼夜温差近9℃，脱穿两件最省事。"
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
