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
# 2026-11-26 18:00 班（18 点班：生成 + 推 GitHub + 部署 + 归档）。
#
# 跨班查重基线（本轮重建，147 条去重标题）：
#   · drive 里 10 份归档 html（11-22-18 ~ 11-26-12）正则抽 n-title = 132 条
#   · 仓库 editorial.json（12:00 班，5+7）+ git 历史两份：
#     - e03eeea4 = 11-26 06:00 班（6+8）
#     - 96e8c892 = 11-25 18:00 班（6+7，该班两次部署均 404 且未归档，
#       只能从 git 历史回补——所以基线必须同时读「归档 html」+「git 历史 editorial.json」）
#
# ★ 本轮值得记的现象：
#   1) **本轮 invest 池只有 12 条**（11-25 18:00 班 19 条 → 本轮 12 条），
#      供给明显收缩，可选空间窄；因此对「事件簇饱和」的判定比平时更克制。
#   2) **存储簇基线已 4 条**（存储行业变天 / 三星产能售罄 / 闪迪NAND / 高盛下修价格目标），
#      本轮 business[27]「存储行业从未如此精彩」+ invest[1]「存储短缺冲击购物季、
#      苹果微软集体涨价」→ 全 hide，簇内一条不留。
#   3) **Anthropic 簇基线 6 条**（含 11-25 06「Anthropic重挫14%跌破万亿」），
#      本轮 invest[4] 贝莱德驳斥见顶论（Anthropic上市=应用层大爆发）→ hide。
#   4) **美股 AI 交易簇基线已厚**（12:00 班两条：AI交易抛压暂歇/纳指入熊BTIG；
#      06:00 班两条：CDS创新高/标普列入观察负面），本轮 invest[3] 汇丰「科技股已
#      定价最坏情景」→ hide（同题材第三家投行口径）。
#   5) **黎曼簇基线 4 条**（A社940页手稿 / Lean社区形式化验证 / P/NP 攻克 / P/NP 一次），
#      本轮 business[19]「黎曼猜想证明代码暴砍99.5%」→ hide。
#   6) **理想簇基线 3 条**（理想去宁德化凶猛 / 理想三季报 / 砍掉宁德时代），
#      本轮 invest[9]「理想预计Q4扭亏」→ hide（同一份三季报口径的衍生稿）。
#   7) **蔚来/小鹏科技日簇本轮集中出现**（business[10][17][26]、invest[2][10]）：
#      蔚来科技日（世界模型3.0 + NOMI4.0 + 李斌换电表态）与小鹏科技日（IRON 物理AI）
#      是两个公司的两场发布会。本轮按「同公司同场发布会最多留 1 条」处理：
#      蔚来留 business[10]（技术面），小鹏留 invest[2]（战略面），
#      business[17]/[26]/invest[10] 因同事件簇 hide。
#      注：baseline「Robotaxi开始算一辆车的账了」已在 11-24 18:00 班上过，
#      business[17]「小鹏科技日 Robotaxi 无人运营」同题材 → hide。
#   8) **华为折叠簇基线已有**（华为大折叠+小折叠电脑+1亿鸿蒙），
#      本轮 business[8]「首款鸿蒙小折叠电脑」→ hide（同一场发布）。
#   9) **黄仁勋簇基线 7 条**、**豆包小豆簇**（11-25 18:00 实测小豆 + stale）→
#      business[33] 早报（软文 + 双簇叠加）→ hide。
#
# hide 的四类来源：
#   1) 软文 / 会议议程 / 报名 / 早报随笔 / 观点随笔 / 采购指南：
#      business[1][3][4][6][9][11][12][13][14][15][18][20][23][25][27][30][33]、
#      invest[0]。
#      （business[25]「15分钟AI短片」与 business[7] 同簇，一并 hide。）
#   2) 事件簇饱和：storage / Anthropic / 美股AI交易 / 黎曼 / 理想 / 华为折叠 /
#      黄仁勋 / 豆包 / Robotaxi / 蔚来科技日 / 小鹏科技日。
#   3) 标题级跨班旧稿：business[16][22][28][31]（基线命中）、invest[4]。
#   4) 下一班可考虑换上来的候选：
#      business[30] 互动影游「百铲大战」、business[2] 国产模型能否追上 Opus 5.5、
#      business[13] 沈向洋的 AI 非共识、invest[3] 汇丰「科技股定价最坏情景」、
#      invest[10] 蔚来科技日重开、invest[9] 理想 Q4 扭亏。
#
# business 保留 6 条：AI公司估值75亿 / AI视频每半秒5毛 / 蔚来世界模型3.0 /
#                      九阳减持 / 美债避险失效 / 股份行村改支
BUSINESS_KEEP = [
    (0, "75亿买的不是模型，是英伟达、Anthropic、亚马逊三家同时押注的入口位置"),
    (7, "每秒五毛把AI视频从尝鲜拉进流水线，长镜头编排也能规模化"),
    (10, "世界模型替真车喂数据，训练提效5倍；强化学习进座舱，车企自研闭环"),
    (24, "从豆浆机到AI的剧本硬造出310%涨幅，股东在高位选择落袋"),
    (21, "波动率抬升让美债不再是无风险避风港，2027年配置逻辑要重写"),
    (32, "交卷时间被拉长，监管给中小银行留的整改窗口比市场以为的更宽"),
]

# invest 保留 6 条：摩根大通2027 A股 / 日央行50基点 / RenMac避险失灵 /
#                    A股今日收盘 / 速腾聚创财报 / 小鹏物理AI
INVEST_KEEP = [
    (11, "21%空间由盈利而非估值支撑，杠铃结构押国产算力与高股息两端"),
    (7, "若真一次性加50基点，套息交易平仓压力会先砸日元再外溢风险资产"),
    (5, "把英伟达比作房利美是核心指控：替弱信用对手背书，把风险藏进循环融资"),
    (6, "PCE超预期推高加息预期，沪指靠银行中字头扛住，创业板一度跌超1%"),
    (8, "营收增四成但毛利率从25%掉到15%，1.37亿拨备还没结清替换成本"),
    (2, "强调协作而非主从，物理AI的叙事从单机能力转向人机组织方式"),
]

OUTFIT = (
    "上海今天晴转阴，此刻13.4℃、体感11.6℃，清晨最低9.3℃、午后最高17.9℃，"
    "温差近9℃；湿度73%，降水概率只有2%，风还是有点凉。选卡其色防风夹克或薄呢外套，"
    "内搭长袖针织，下摆配宽松长裤，早晚加件短款卫衣也不显臃肿。"
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
