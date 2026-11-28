#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 editorial.json：comments / hide / order 统一以「新闻标题原文」为 key。

标题不手抄，一律按索引从 data.json 取，避免引号/标点转义错位。
带自检断言：order 去重、跨板块不串、评论全覆盖、字数区间、hide 与 order 不相交。
"""
from __future__ import annotations

import json
import pathlib
import re

BASE = pathlib.Path(__file__).parent
DATA = json.loads((BASE / "data.json").read_text(encoding="utf-8"))


def norm_ws(s: str) -> str:
    """标题归一化：与 render.py 实时层的 normT 保持一致（压缩空白 + trim）。

    同一条稿在直连 feed 里可能是单空格、在陈旧稿缓存里是双空格，字符串不等 →
    会同时进 order 和 hide → 实时层把「已展示」的那条自己过滤掉，页面上直接消失。
    """
    return re.sub(r"[\s\u3000]+", " ", s or "").strip()

# ---------------------------------------------------------------- 选题
# 2026-11-28 18:00 班（18 点班：部署）。
#
# 跨班查重基线：仓库 baseline_titles.json 已固化 16 班 / 193 条去重「已展示」标题。
# 标题比对 + 专有名词回基线全文扫，两轮都做。
#
# ★ 本轮查重结果（8 条 EXACT 撞车 + 多个簇收敛 + 1 条险过）：
#   1) EXACT 撞车直接 hide：
#      business[6]  AI服务器卖爆了但卖服务器的不赚钱了（11-28-12 已上过）
#      business[10] 韦东奕近140年数学难题
#      business[12] 水井坊6年换8帅
#      business[21] 港交所科技100大换血
#      business[22] 蚂蚁灵波 LingBot-Map 2.0
#      business[25] 20个AI Agents / ClickBench
#      business[26] 支付宝行动座舱
#      business[32] 中国客车出海壁垒（11-28-12 已上过）
#   2) business[0] 英伟达禁向东南亚四国发服务器 = 基线「英伟达暂停向东南亚四国交付
#      AI服务器」同一事件（钛媒体英文稿 + 中文稿同源）→ hide。
#   3) business[16]「首个带跨任务空间记忆的原生基模开源」= 蚂蚁灵波同事件，
#      11-28-06 已展示 → hide（量子位同日两稿一起没）。
#   4) ⚠️ business[3]「蔚来开始用AI改造自己」= 基线「任少卿带着世界模型3.0来了」
#      **同一事件簇**（11-25 第三届 NIO IN 发布了世界模型 NWM 3.0 + NOMI 4.0，
#      本篇同场发布会）→ hide。险过：标题完全不像，但正文对上了 NWM 3.0。
#   5) business[24]「客户不买单，具身智能的'第一'还值几个钱」= GPT-6 Astra 引发的
#      具身榜单刷榜潮（基线已有「GPT-6.2 Astra再次暴击具身模型」+「RoboChallenge
#      Zero首期评测发布」），本篇是同潮的**反方解读** → hide。
#   6) invest[9] 高盛对冲基金主管警告清仓 = 11-28-12 已上过 → hide。
#   7) invest[10] 全球大救市独缺美联储 = 救市簇第 4 次（国常会 / 亚洲群起 / 韩国）
#      → hide。
#   8) invest[11] OpenAI 视为比编程更大市场 = 11-25-12「OpenAI瞄上网络安全」同一事件
#      → hide。
#   9) invest[3]「AI股神喊抄底」与 invest[4] 同属「AI 交易没完」叙事，只留 [4]
#      （卖方给出四大指标与2028年时点，机制更硬）；[3] 是私募致投资者信的喊单，
#      硬事实更少 → hide。
#  10) 广州车展成片车评稿（[2][5][8][11][14][17][20][29][33]）+ 展会/评级/软文
#      （[4] 众擎大会、[7] 商汤信通院评级、[16] 钛动×腾讯云、[19] 钛动×腾讯云、
#      [31] Claude Opus 做PPT、[30] 宿华黄仁勋回宫、[9] 复联5救市、[1] …）→ 全部 hide。
#  11) business[27]「广州车展看汽车产业链权力位移」判定为**可上**：它不是一车一稿的
#      车评软广，事件主体是「零供关系 + 账期监管」；新机制（中汽协受工信部委托对
#      17 家重点车企启动供应商账期年度调研评估）与车展官方数据基线均无。
#      基线虽有「理想去宁德化凶猛」，但那篇讲的是理想自研电池，本篇只取账期监管
#      与车展结构两条线 → 评论刻意避开理想/宁德细节，不撞簇。
#  12) business[13] DeepSeek 账单 = 11-27 上线的**新功能**（聊天框内 Token 账单、
#      对标 V4.1-Flash 空闲时段定价），基线的「DeepSeek限额」是 11-16 的限流事件，
#      日期与机制都不同 → 可上；评论只讲账单与调用量，不复述限额。
#  13) business[1] 卡帕西用 Claude 造「美国版《文明》」：基线全无卡帕西条目，
#      事实具体（7 小时、4.5 万行代码、524 个都市区）→ 可上。
#
# business 保留 6 条：大润发半年报 / DeepSeek 账单 / 腾讯混元 Hy3D 3.6 /
#                      广州车展零供关系 / AI公司招营销人才 / 卡帕西AI造文明
BUSINESS_KEEP = [
    (18, "高鑫零售半年营收274.87亿同比降9.9%，净亏5.17亿，上年同期仅1.27亿"),
    (13, "App与网页上线Token账单，OpenRouter调用量59.2万亿Token居首"),
    (28, "上线腾讯云Token Hub供API，Miora、LAP接入，数百美术盲测"),
    (27, "车展整车1106台新能源占六成，中汽协启动17家车企账期年度评估"),
    (15, "OpenAI在招50个营销岗、Anthropic19个，企业客户岗年薪32至40万美元"),
    (1, "Claude连跑7小时写4.5万行代码造地图，收录524个都市区"),
]

# invest 保留 8 条：Anthropic限制模型能力 / 花旗350亿账务差错 / 美国家庭股票敞口 /
#                   摩根大通驳斥半导体见顶 / 得州解冻数据中心 / 标普下调法国展望 /
#                   个人养老金四周年 / 冯骥追问AI财富归属
INVEST_KEEP = [
    (1, "付费用户做ML研究，模型暗改训练参数和实验条件，代码缺陷频出"),
    (2, "内部模型超范围使用致RWA低估约350亿美元，占该子公司申报额两成"),
    (0, "德银EPFR口径显示家庭股票敞口创40%新高，AI下挫中散户照买"),
    (4, "费半自高点回落约40%，四大指标未亮警，周期料延至2028年"),
    (8, "州长办公室指令解冻1800余个数据中心许可，开发商抢在政权交接前拿批文"),
    (6, "A+评级维持但展望转负，警告大选后政治极化与赤字高企难压"),
    (7, "四周年货架扩至基金351只保险233款，累计缴存1452亿元仍偏冷"),
    (5, "黑神话制作人称智力首次脱离肉身成可复制资本要素，破坏性超历次革命"),
]

OUTFIT = (
    "上海此刻晴、11℃，体感只有7.2℃，白天最高14.7℃、清晨最低6.4℃，湿度44%、降水概率为零。"
    "昼夜温差八度多，风衣内搭薄羽绒最稳；午后阴转晴回暖，羊毛衫配衬衫两件叠穿即可。"
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
    selected_ws = {norm_ws(t) for t in selected}
    stale_added: list[str] = []
    for t in stale:
        # 同稿不同空白：已展示过就绝不能进 hide，否则实时层会把它整条滤掉
        if norm_ws(t) in selected_ws:
            continue
        if t not in selected and t not in hide:
            hide.append(t)
            stale_added.append(t)

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
    assert len(hide) == pool_hidden + len(stale_added), (
        f"hide 数量不匹配 {len(hide)} != {pool_hidden}+{len(stale_added)}"
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
