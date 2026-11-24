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
# 2026-11-25 06:00 班（06 点班：只生成 + 归档，不部署）。
#
# 跨班查重基线：拉取 11-19 12:00 / 11-19 18:00 / 11-20 06:00 / 11-21 06:00 /
# 11-21 12:00 / 11-21 18:00 / 11-22 06:00 / 11-22 12:00 / 11-22 18:00 /
# 11-23 06:00 / 11-23 12:00 / 11-23 18:00 / 11-24 06:00 / 11-24 12:00 /
# 11-24 18:00 共 15 班归档 html，正则 <a class="n-title"> 抽出实际展示标题
# = 199 条（去重 179）。基线用 drive files search 的 cdn_url 批量拉，
# 13/15 一次成功，11-23 12:00 与 11-23 18:00 签名失效（403），
# 改用 drive files get 取新签名后补齐（15/15）。
#
# ★ 本轮两个值得记的现象：
#   1) **事件簇整体退潮**：上一班（11-24 18:00）被「黄仁勋复职」刷屏，本轮该簇
#      彻底降温——候选池里只剩 business[26][29] 两稿、invest[5] 一稿，
#      而基线已累计上 8 条黄仁勋 + 12 条 Anthropic + 2 条黎曼 + 1 条自变量。
#      本轮全部 hide，不再留任何正交角度（簇已彻底饱和，留一条就是重复）。
#   2) **英伟达回归当日美股反而大跌**：invest[8] 费半盘中一度 -9%、
#      半导体 ETF -5.2%、英伟达 -8%、Anthropic -14% 跌破万亿。
#      这是新事件（不是 11-24 12:00/18:00 的"反弹"那一稿）→ 留 invest[8]。
#      同簇的 invest[5]「Anthropic 破发 + 创始人套现」本轮 hide：
#      破发事件基线已连上两班（11-21 06「距破发仅差5美分」、11-22 12「豪华投行承销团压力」）。
#
# hide 的四类来源：
#   1) 标题级跨班旧稿（15 班基线命中）：
#      business[7] 文心 5.5 Flash Preview 开源（11-24 18:00 已上）→ hide；
#      business[14] 苹果 iOS 端 AI 收费 | AG&I（11-24 18:00 已上，且 stale 里有转义版
#        AG&amp;I，靠 verify_page.py 的 unescape 归一化避免误判泄漏）→ hide。
#   2) 事件簇饱和（标题不重复但事件已上过）：
#      · 黄仁勋簇：business[26][29] → hide（基线 8 条）。
#      · Anthropic 簇：invest[5] → hide（基线 12 条，破发主题连上两班）。
#      · 黎曼簇：business[20] → hide（基线 11-21 12 起连上四班）。
#      · 自变量簇：business[9] WALL-OSS-1.0（11-23 18:00 已上同篇）、
#        business[33] WALL-API-1.0、business[28]「具身行业通用智能时刻」
#        （实为同一波发布叙事）→ 全 hide。
#      · 存储簇：invest[0] 惠普「内存成本控制取得进展」是终端厂商验证端的新角度
#        （11-22 18 拿不到货 → 11-23 18 高盛下修 2028 价 → 11-24 06 三星产能锁到 2031
#        → 本轮惠普指引超预期），与基线不重叠 → 保留。
#   3) 软文 / 会议报名 / 厂商发布稿 / 栏目稿 / 观点随笔：
#      business[1] Google Cloud 出海峰会报名、business[16] MEET2027 报名、
#      business[22] 亿邦产业互联网年会、business[25] 奇点智能技术大会、
#      business[4] 端侧超节点（量子位厂商稿）、business[10] 方程豹钛9 折叠方向盘、
#      business[13] 仰望U8 交付巴新（品牌稿）、business[2] 比亚迪唐 EV 上市（产品促销）、
#      business[19] 蚂蚁 OceanBase OceanLake 发布稿、business[23] 爱范儿早报、
#      business[31] AI 审美降级、business[11] AI 与考试随笔、business[30] 猛犸象、
#      business[24] 无限暖暖、business[0] 陪伴机器人留存（问题式行业稿）、
#      business[5] 实测小豆（豆包个人智能体，stale[6] 已有"个人Agent的大厂战事"同题）。
#   4) 本轮不展示但内容合格的（移到 hide，避免"漏进 hide"导致页面上多出无点评条目）：
#      business[6] 荣耀中端（存储涨价传导，与 invest[0] 同主题只留后者）、
#      business[12] 中国国航油价看跌期权、business[15] 零跑 Q3（收入317亿增63%、
#      净利仅0.4亿、毛利率降3.6点、出口6.33万台增263.7%）、
#      business[17] iPhone 相机掌门人退休、invest[1] 铜价跌4.3%（与 invest[6] 同属
#      LME 金属周期簇）、invest[2] 大众工人罢工、invest[9] 摩根大通"物理AI ChatGPT时刻"
#      （具身簇）、invest[11] 美伊战争风险定价。
#
# business 保留 6 条：DeepSeek C端限额 / 理想去宁德化 / 摩尔线程回购 /
#                      斯菱智驱收购银球 / 宝莱特飞检停产 / 华为折叠 + 鸿蒙破亿
BUSINESS_KEEP = [
    (18, "长对话超7天失效、单次输入压到4万字、每日总量封顶，C端三重限额摊开算力账本"),
    (21, "8月已跌出宁德前五大，转拿欣旺达39%装机份额登顶，L9电池包已自制"),
    (27, "一边回购一边拿45亿募资理财；Q3营收增近18倍首度扭亏，前三季现金流净流出33亿"),
    (32, "标的净利两年从1.46亿滑到0.37亿，评估增值60%却不设业绩承诺，风险留给中小股东"),
    (3, "飞检查出编造枸橼酸根检验记录并责令停产，涉事子公司前三季度营收仅占集团3.77%"),
    (8, "首款鸿蒙小折叠电脑同步亮相，HarmonyOS 5/6/7装机量突破1亿台"),
]

# invest 保留 7 条：美股全线下跌 / 惠普指引超预期 / GTCR 500亿私有化 /
#                      城堡证券业绩 / OPEC+ 2027产量 / LME 铝逼仓规则 / 咖啡豆库存
INVEST_KEEP = [
    (8, "费半一度跌9%，半导体ETF跌5.2%、科技ETF跌3.05%，反弹行情当半场熄火"),
    (0, "内存成本开始被消化，新财年EPS指引3.15-3.45美元高于预期，盘后一度涨15%"),
    (3, "此前与CD&R的联合方案告吹后转为独立推进，若成将是支付业最大规模LBO之一"),
    (4, "前三季度净交易收入破150亿美元已超去年全年，第三季单季34亿同比增29%"),
    (7, "本月底部长会按独立产能审计重设各国基准，布伦特本月已跌25%，伊朗与霍尔木兹成最大变量"),
    (6, "Tom-next触发门槛从可用库存50%砍到30%，超5个工作日持仓强制降息借出"),
    (10, "ICE仓库库存单日激增19%至26.8万袋，创1998年以来最大单日增幅，供应紧张缓解"),
]

OUTFIT = (
    "上海清晨晴，2.4℃体感0℃，湿度95%，湿冷而非干冷；白天转阴，最高12.2℃最低2.3℃，"
    "降水概率为零。厚呢大衣或夹棉外套配高领针织，午后升温脱到卫衣即可；"
    "下身加绒直筒长裤，防水短靴，再搭一条薄羊绒围巾。"
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
