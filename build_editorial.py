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
# 2026-11-24 06:00 班（06 点班：只归档，不部署）。
#
# 跨班查重基线：拉取 11-21 06:00 / 11-21 12:00 / 11-21 18:00 / 11-22 06:00 /
# 11-22 12:00 / 11-22 18:00 / 11-23 06:00 / 11-23 12:00 / 11-23 18:00 共 9 班
# 归档 html，正则 <a class="n-title"> 抽出实际展示标题 = 107 条（去重 101）。
#
# ★ 归档 html 的 OSS 签名坑（实测）：drive files download 返回的 URL 带
#   response-cache-control 参数，而该参数会被算进 OSS canonical resource，
#   直接用会 SignatureDoesNotMatch；且手抄签名极易张冠李戴（错配 8 次里 7 次失败）。
#   可靠做法：取 drive files search / drive files get 返回的 cdn_url，
#   【只保留 Expires / OSSAccessKeyId / Signature 三个参数】原样 curl。
#
# 本轮候选池：business 34 条（三源轮转交织后）、invest 12 条。
# invest 12 条全部是 11-24 00:04~05:47 新发（华尔街见闻夜间档），标题级全新。
# business 池以 11-23 傍晚稿为主，其中 7 条标题级命中历史基线。
#
# hide 的三类来源：
#   1) 标题级跨班旧稿（9 班基线命中）：
#      XROGO 进工厂、蚂蚁医疗AI五连发、Agent版arXiv、RoboChallenge Zero、
#      杉数D轮、Nature 电刺激控糖、iPhone 18 明年春。
#   2) 事件簇饱和（标题不重复但事件重复）：
#      · 蚂蚁阿福开源簇：business[13] 开源同款模型 == 已上过的「五连发」里的开源项 → hide；
#        business[24] 大厂绕开医保是「医保/DRG-DIP 支付结构」新事件（从未展示过）→ 保留；
#      · 自变量簇：business[11] WALL-API-1.0 == 11-23 18:00 已上的 WALL-OSS-1.0 → hide；
#      · 黎曼猜想簇：business[31] Lean 官方认证 == 11-21 12:00/18:00 + 11-22 18:00
#        三班已上；business[26] 早报内含黎曼条目 → 一并 hide；
#      · GTA6 簇：business[33] == 11-22 06:00 已上的 GTA6 首日 38 亿美元 → hide；
#      · 豆包/办公AI 簇：11-21 06:00 已上 WorkBuddy 登顶，本轮只留 business[3]
#        「腾讯字节 AI 办公」一条（两侧硬数据），business[22] 21 个工作台、
#        business[27] 三家趋同同簇 → hide；
#      · 姚顺雨 Reddit AMA：11-21 12:00 同一场 AMA → hide；
#      · 华为星芒：11-21 06:00 已上「华为星芒发车」+ 本条是评测软文 → hide；
#      · 存储簇：11-22 18:00「拿不到货」+ 11-23 18:00「高盛下修 2028 存储价」已上，
#        business[16] 存储经济性为软文 → hide；
#      · 苹果RED 特别版 invest[0]：产品促销稿（恰逢公益周年 + 为假日季销售注入动力）→ hide。
#   3) 观点随笔 / 评测 / 栏目稿：AI 审美大降级、当AI开始自己上班、AI情绪生意、
#      机器人老板做自媒体、陪伴机器人留存、雷克萨斯 ES 车评、XREAL AURA 体验、
#      华为星芒 O1 Pro 评测、醒图新版本、存储经济性软文。
#
# business 保留 6 条：端侧大模型 / AI办公 / AI网购 / 医疗AI支付 / 禾赛财报 / 反内鬼招聘
BUSINESS_KEEP = [
    (3, "腾讯WorkBuddy日活破千万，豆包工作三个月DAU 800万。"),
    (1, "无界方舟Edge0-145B开源，12G显存笔记本可跑，对标Opus 4.6。"),
    (12, "购物车权限交给AI，2000元洗地机砍200元还搭赠品。"),
    (24, "医保支出破3万亿，医疗AI市场仅11亿，付费方只有院长控费账。"),
    (6, "Q3营收10.68亿增34%，激光雷达仍占九成，新业务仅0.9亿。"),
    (15, "OpenAI反内鬼岗9个增至22个，要求8年调查加政府许可。"),
]

# invest 保留 8 条：英伟达回归 / 信用市场 / 美国PMI / 三星存储 / 大摩情绪 /
#                   SpaceX算力 / Anthropic数据主权 / 礼来肿瘤并购
# 黄仁勋簇最多留 2 条：invest[4] 事件本体 + 股价反应、invest[8] 信用市场传导；
# invest[2] 回旋镖CEO、invest[7] 大到不能解雇 属同簇评论，invest[5] 特朗普力挺与
# stale 标题重复 → 三条全 hide。
INVEST_KEEP = [
    (4, "辞职11天后官复原职，英伟达盘前一度涨35%。"),
    (8, "投资级利差创4月8日来最大单日降幅，高收益反向指标七个月最大升幅。"),
    (11, "综合PMI初值54.6环比降1.3点，交货延宕为2022年来最长。"),
    (10, "2027至2029年产能已锁定，厂商仅能满足六到七成需求。"),
    (9, "首席经济学家称客户抵触最强，标普一度跌破200日均线。"),
    (6, "Anthropic每月付31亿美元算力费，SpaceX AI部门已占营收过半。"),
    (1, "EFS公测开放自定义云存储，提示词仍强制留存30天。"),
    (3, "八款肿瘤药在晚期临床，其中三款明年出结果。"),
]

OUTFIT = (
    "上海今早晴，九度二、体感五度七，白天最高十二度四，入夜最低四度七，湿度六成八，"
    "降水概率不足一成，白天或有零星小毛毛雨。"
    "穿搭走细密棉针织打底叠轻薄羽绒马甲，外层防风防泼水尼龙壳；"
    "下身厚直筒长裤配加绒短靴，湿滑路面别穿平底布鞋。"
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
