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
# 2026-11-24 18:00 班（18 点班：生成 + 部署）。
#
# 跨班查重基线：拉取 11-21 06:00 / 11-21 12:00 / 11-21 18:00 / 11-22 06:00 /
# 11-22 12:00 / 11-22 18:00 / 11-23 06:00 / 11-23 12:00 / 11-23 18:00 /
# 11-24 06:00 / 11-24 12:00 共 11 班归档 html，正则 <a class="n-title"> 抽出
# 实际展示标题 = 143 条（去重 127）。基线用 drive files search 的 cdn_url 批量拉，
# 11/11 一次成功（2026-11-24 12:00 班更正过：签名不必逐节点重取）。
#
# ★ 本轮头号现象：「黄仁勋复职」事件簇第二次刷屏 ——
#   business 侧 6 条（[3][14][15][17][20][21]）+ invest 侧 6 条（[2][4][5][7][8][11]），
#   占 46 条候选池的 1/4。基线里该事件已上 8 条（11-24 06:00 三条 + 11-24 12:00 三条，
#   另有 11-21 06:00 特朗普呼吁复职一条），本轮按事件簇收敛，只留 2 个正交角度：
#        invest[8] 华尔街解读（卖方/买方情绪分层 + 事件本体数据）
#        invest[11] 利益冲突（特朗普持股一夜 +1500 万美元 + 参议员要求彻查）
#   business 侧 6 条全 hide（同一事件的多家媒体解读稿）。
#   invest[2] 次日回吐（纳指期货跌、英伟达盘前跌4%、韩股收涨6%、金油齐跌）→ hide，
#   与基线 #124「对冲失效/复盘惊心动魄的一天」+ #125「亚洲股市 韩股涨7%」重叠；
#   invest[4] 高盛「这波是真的吗」与 invest[8] 同属卖方视角 → hide；
#   invest[5]「谁才是真正掌权者」纯解读无硬事实 → hide；
#   invest[7] 木头姐 ARK 卖飞 → 轻量插曲 → hide。
#
# hide 的四类来源：
#   1) 标题级跨班旧稿（11 班基线命中 / 事件已上过）：
#      · 黎曼猜想簇：business[11]「Claude 黎曼猜想证明的主导者回应」→ hide
#        （11-21 12:00 / 11-21 18:00 / 11-22 18:00 / 11-23 12:00 已连上四班）。
#      · 具身基础模型簇：business[28] 实为自变量 WALL-OSS-1.0（零样本 55.1%），
#        11-23 18:00 已上 WALL-OSS-1.0 与 WALL-API → hide；business[26] WALL-API 同理。
#      · AI 办公簇：business[6]「AI办公不再只拼大模型」，11-24 06:00 已上
#        「800万对1000万，腾讯字节又在AI办公杠上了」→ hide。
#      · 比亚迪出海簇：business[13] 仰望U8 交付巴新（品牌稿）→ hide，
#        只留 business[10] 钛9 折叠方向盘量产（技术事件，但本轮未选）；
#      · 蚂蚁医疗簇：invest[3] 百灵模型取舍，11-23 18:00 已上「蚂蚁医疗健康AI五连发」
#        → hide。
#      · 永辉茅台簇：business[18]「永辉和茅台后会友期」与 invest[1] 同一事件
#        → 跨板块只留信息量更硬的 invest[1]（持股比例/分配金额/净资产）。
#   2) 软文 / 会议报名 / 栏目稿 / 产品促销 / 观点随笔：
#      business[1] Google Cloud 出海峰会报名、business[16] MEET2027 报名、
#      business[22] 亿邦产业互联网年会、business[25] 奇点智能技术大会、
#      business[31] 醒图新版本、business[29] 雷克萨斯 ES 车评、business[33] XREAL AURA 体验、
#      business[2] AI 与考试成绩的随笔、business[23] AI 审美降级、business[14] 爱范儿早报、
#      business[0] 陪伴机器人留存（问题式软文；同主题留 business[32] 宠物经济）、
#      invest[0] 2027 见闻历（自家产品推广）。
#   3) 标题不重复但事件/角度未变：business[30] 大模型 Benchmark、business[12] 阶跃星辰终端、
#      business[19] OceanBase OceanLake、business[9] 艾为电子并购钰泰（本轮未选）、
#      business[4] 端侧超节点、business[10] 方程豹钛9、business[8] iPhone 相机掌门人退休。
#   4) invest[6] A 股收盘综述与基线 #84（11-24 12:00 班中盘稿）不是同一份数据：
#      #84 描述的是 11-23 收盘，本条是 11-24 当天收盘（创业板高开 3.88% 后尾盘翻绿，
#      与本轮 backfill 行情一致：创业板 2278.99 -0.05%、沪指 3548.37 +0.27%）→ 保留。
#
# business 保留 6 条：文心5.5开源 / Robotaxi算账 / 苹果AI收费 / 具身融资流向 /
#                      艾为并购钰泰 / 宠物经济
BUSINESS_KEEP = [
    (7, "总参数2800亿、激活140亿，支持百万Token上下文，开源模型CodeArena第二"),
    (27, "小马Q3出行收入1.19亿增165%，文远广州单车经济性转正、日均21单"),
    (5, "iOS27.3测试版给云端AI设每日额度，端侧指令免费，超额靠iCloud+加购"),
    (24, "章鱼动力、傲意科技、英汉思动力48小时连融亿元级，美的等产业资本入场"),
    (9, "发股加现金收购钰泰100%股权，对手方34名，上市以来首单重组"),
    (32, "双11囤4362万袋猫粮，Z世代缩减开支却加码宠物，宠物股利润齐跌"),
]

# invest 保留 6 条：黄仁勋复辟(华尔街解读) / 黄仁勋复辟(利益冲突) / A股收盘 /
#                      三星独供折叠屏 / 涂鸦智能财报 / 茅台永辉清算
# 黄仁勋复职事件簇只留 2 条正交角度：invest[8]（市场与卖买方情绪）、invest[11]（政治利益冲突）。
INVEST_KEEP = [
    (8, "英伟达单日市值增9520亿美元创纪录，11天等待的代价是标普蒸发逾5万亿"),
    (6, "创业板高开近4%尾盘翻绿，科创50收涨近2%，机器人半导体接力，小金属领涨"),
    (11, "持股账面价值一夜增1500万，白宫称董事会听过政府高层意见，民主党议员要求彻查"),
    (9, "爆料称三星Display凭折痕与良率优势锁定至少五年，LG短期难破局"),
    (10, "收入9860万美元增19.5%，AI玩具陪伴机器人放量，毛利率降2.5百分点"),
    (1, "友谊使者成立12年，永辉持股30%可分1.16亿，茅台持股70%收回销售权"),
]

OUTFIT = (
    "上海白天晴，8.8℃只觉4.9℃，午后最高12.6℃，昼夜温差七度多；湿度五成半，"
    "降水概率两成出头，白天或有毛毛雨。早出晚归套风衣加薄针织，中午脱到卫衣就够；"
    "下身厚直筒长裤，鞋子选防水款。"
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
