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
# 2026-11-28 12:00 班（12 点班：只归档，不部署）。
#
# 跨班查重基线：仓库 baseline_titles.json 已固化 15 班 / 182 条去重「已展示」标题。
# 标题比对 + 专有名词回基线全文扫，两轮都做。
#
# ★ 本轮查重结果（4 条 EXACT 撞车 + 多个簇收敛）：
#   1) EXACT 撞车直接 hide：
#      business[7] 韦东奕近140年数学难题（11-27-18 已上过）
#      business[19] 蚂蚁灵波 LingBot-Map 2.0 空间记忆（11-28-06 已上过）
#      business[22] 20个AI Agents / ClickBench（11-27-12 已上过）
#      business[23] 支付宝行动座舱（11-27-18 已上过）
#   2) **business[13]「首个带跨任务空间记忆的原生基模开源」= [19] 同一事件**
#      （量子位同日两篇稿）→ 事件已在 11-28-06 上过 → 两个一起 hide。
#      这正是「hide ≠ 上过」的反例：这里事件确实已展示过。
#   3) **invest[4] 铝市逼空 / LME 紧急出手 = 11-25-06「铝现货升水收窄、LME收紧持仓规则、
#      干预数十年来最严重逼仓行情」同一事件** → hide。险过，跟 11-28-06 班踩的是同一个坑。
#   4) invest[2]「OpenAI 视为比编程更大市场」= 11-25-12「OpenAI瞄上网络安全：比编程更大的
#      下一个市场」同一事件（标题都直接复述了对方）→ hide。
#   5) invest[3] 特朗普拯救黄仁勋 / 美股 → 黄仁勋簇基线已 7 条 → hide。
#      invest[1] 全球大救市独缺美联储 → 救市簇基线已 3 条（国常会稳市 / 亚洲群起救市 /
#      韩国救市）→ hide。
#      invest[9] 早餐FM-Radio → 内含「10月工业企业利润增20.1%」与 11-27-12 已展示稿重复 → hide。
#   6) 广州车展稿成片（[2][5][8][11][14][17][20][26][31][33] 共 10 条）+ 展会/评级类软文
#      （[4] 商汤信通院评级、[16] 钛动×腾讯云、[1] 众擎大会、[29] Claude Opus 做PPT、
#      [28] 具身抱团回应、[24] 宿华黄仁勋）→ 全部 hide。
#   7) invest 留 [0] 不留 [11]：两条同属「AI 拥挤交易退潮 + 高盛警告」簇（基线 11-23-12
#      已有「快钱率先投降」）。[0] 给的是新机制（2027 净供给增量 + AI capex 对盈利的
#      拉动减速 + 2028 盈利前景），[11] 的恐慌指数/轮动失效与基线重叠更大 → 只留 [0]。
#   8) business[0] 戴尔财报簇判定：11-25-12 已上过「戴尔电话会 AI服务器积压订单1320亿」
#      （需求面）。本轮 [0] 是同一份财报的另一面 —— 利润被挤压、股价从 9 月高点腰斩，
#      并给出 HPE/ADI 同期跌幅，机制已变（需求爆发 → 定价权转移）→ 属新角度，可上。
#   9) invest[10] Anthropic 重回发行价：与基线 11-25-06「Anthropic重挫14%跌破万亿」是
#      同一股价线的**新状态**（首个完整交易周收涨 10.98%、站上 83 美元发行价），非重复。
#      同簇的 [5]「纽约时报作家隐瞒金主背景」偏八卦 → 不留。
#   10) invest[7] 英国国防部 10 万预备役 → 基线完全无此簇，全新事件 → 上。
#
# business 保留 6 条：AI服务器利润清算 / 港交所科技100换血 / 中国客车出海壁垒 /
#                      格力系老兵做飞利浦 / 袁记招股开堡店 / 水井坊6年换8帅
BUSINESS_KEEP = [
    (0, "HPE、ADI同日跌16.31%、17.37%，订单创纪录却卖不到利润"),
    (15, "曦智、群核等新兴科技股入列，AI硬件与先进制造取代互联网平台"),
    (27, "欧洲上半年纯电客车注册8141辆增49%，宇通比亚迪合计占28.5%"),
    (30, "河北格力营销4.6亿入股恩博力持股82.2%，原经销商成中国区掌舵人"),
    (32, "发行价23至28港元，单店日商三年从5394元降到4627元，第二曲线承压"),
    (6, "三季度营收增2.69%终结五连降，前三季度仍降16.75%，再由财务总监代管"),
]

# invest 保留 5 条：信贷市场割裂 / 高盛清仓警告 / 英国预备役动员 /
#                   Anthropic重回发行价 / 美元见顶信号
INVEST_KEEP = [
    (8, "AI债供给激增与低评级偿债压力分化，投资级利差仅走阔11个基点"),
    (0, "八周内最大规模清仓之一，2027年股票净供给增量将创2000年以来最大"),
    (7, "国防部向约10万人发函更新联系方式与民用技能，部长称属常规行政整顿"),
    (10, "首个完整交易周收涨10.98%至91.88美元，终结连续两日跌破发行价"),
    (6, "美元自9月中旬涨5%后自20个月高位回撤，实际收益率曲线走平常伴见顶"),
]

OUTFIT = (
    "上海此刻阴，13℃、体感9.9℃，白天最高14.2℃、清晨最低6℃，湿度54%、降水概率为零。"
    "风不大但阴天湿冷贴着皮肤，羊毛混纺大衣或风衣内搭薄羽绒最稳妥；"
    "午后回暖，针织开衫配长袖衬衫就够，早晚温差近8℃，脱穿两件最省事。"
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


if __name__ == "__main__":
    main()
