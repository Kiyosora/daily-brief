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
# 2026-11-25 12:00 班（12 点班：只生成 + 归档，不部署）。
#
# 跨班查重基线：重新拉取 drive 里 15 份归档 html（11-19 18:00 ~ 11-25 06:00），
# 正则 <a class="n-title"> 抽出实际展示标题 = 199 条（去重 179）。
# 基线用 drive files get 取新签名后批量拉，15/15 一次成功。
#
# ★ 本轮三个值得记的现象：
#   1) **RSS 池子被"早报/会议/厂商稿"占满**：business 34 条里，爱范儿早报 2 条、
#      量子位会议报名 2 条、大会 2 条、品牌交付稿/产品促销 4 条、栏目稿 1 条，
#      再叠加黄仁勋簇与自变量簇，真正"没上过页 + 有信息量"的只剩 5 条。
#      本轮 business 保留 5 条（下限附近），已经是这个池子的合理上限。
#   2) **黄仁勋簇饱和到只能留 1 条**：基线里黄仁勋相关已 10 条（11-19 18 首份财报、
#      11-21 06 特朗普呼吁复职、11-24 06 复职致意+科技债反弹、11-24 12 三条复职/
#      亚洲股市/白宫提前告知、11-24 18 华尔街解读+特朗普赚 1500 万、11-25 06 复职后
#      美股反跌）。本轮候选还有 6 条同簇稿，只能留 invest[0]——出口管制立法加速，
#      是全簇唯一的"政策外溢"新角度，且直接关联中国芯片通道；其余全 hide。
#   3) **盘面稿在 12 点已反转**：invest[4] 稿子是 09:56 的早盘快照（震荡回升），
#      但 11:36 钛媒体午评已转"三大指数集体下跌"，backfill 的 12:05 行情也全线收绿。
#      保留该条但把反转写进点评，避免页面静态层与实时行情 chip 自相矛盾。
#
# hide 的四类来源：
#   1) 标题级跨班旧稿（15 班基线命中）：
#      business[7] 文心 5.5 Flash Preview 开源、business[11] 华为折叠+鸿蒙破亿、
#      business[17] 苹果 AI 收费 | AG&I、business[24] 宝莱特飞检停产
#      （后两条 11-24 18 / 11-25 06 已上过）。
#   2) 事件簇饱和（标题不重复但事件已上过）：
#      · 黄仁勋簇：business[12][29][31]、invest[9][11] → hide（基线 10 条）。
#        invest[9] 另叠 Anthropic 簇（基线 12 条）双重饱和。
#      · Anthropic 簇：invest[9] → hide。
#      · 黎曼簇：business[23]「Claude 黎曼猜想主导者回应」→ hide（基线 11 条）。
#      · 自变量/具身簇：business[28]「具身行业通用智能时刻」、business[30] WALL-OSS-1.0
#        （基线 11-23 18 同篇）→ hide。
#      · 存储簇：business[27] 荣耀中端（06 班已以同理由 hide，本轮存储簇基线已 6 条）
#        → hide；invest[3] 闪迪是管理层供给侧新角度（1.2ZB 规模、中国吸增量）→ 保留。
#      · 小米簇：business[3]（结构侧：砍低端、ASP 涨四成）与 invest[6]（机构侧：
#        三家大行维持买入、盈利修正触底）角度正交，按"同簇最多 2 条"保留这两条。
#      · 黄金/金属簇：基线已有 5 条（锡价跌、黄金提款机×2、加息无差别抛洒、LME 铝逼仓），
#        invest[1] 摩根大通 2027/28 展望是本轮唯一新报告视角 → 保留。
#   3) 软文 / 会议报名 / 厂商发布稿 / 栏目稿 / 观点随笔：
#      business[1] Google Cloud 出海峰会报名、business[16] MEET2027 报名、
#      business[22] 亿邦产业互联网年会、business[25] 奇点智能技术大会、
#      business[4] 端侧超节点（量子位厂商稿）、business[10] 方程豹钛9 折叠方向盘、
#      business[13] 仰望U8 交付巴新（品牌稿）、business[5] 比亚迪唐 EV 上市（产品促销）、
#      business[19] 蚂蚁 OceanBase OceanLake 发布稿、business[2][26] 爱范儿早报、
#      business[18] 钛晨报（8 条混编栏目稿）、business[8] 实测小豆（06 班已 hide）、
#      business[14] AI 与考试随笔、business[15] 陪伴机器人留存、business[20] iPhone 相机退休、
#      business[32] 中国国航油价看跌期权、business[33] AI 审美降级、
#      invest[2]「AI 软件工厂 12 条军规」（厂商观点稿）。
#   4) 本轮不展示但内容合格的（移到 hide，避免"漏进 hide"导致页面上多出无点评条目）：
#      business[6] 红果改写 Q3 财报季（二线平台短剧/AI 广告换血，11-25 09:38 但与
#        08:49 档期重叠、本轮 business 槽位已满，18:00 班可考虑换上来）、
#      invest[8] 美国钢铁四年高位（AI 基建实体通胀，与戴尔/闪迪同属基建链）、
#      invest[11] 期权 1 天 20 倍（散户梗）已按黄仁勋簇 hide。
#
# business 保留 5 条：世界模型标准之争 / 小米增长接力 / 红果改写财报季 /
#                      劝父母卖房收息 / SpaceX 首评
BUSINESS_KEEP = [
    (0, "三周六家密集发布，评价口径从画面逼真转向因果推演，百度给出2+3标准"),
    (3, "Q3营收破千亿、经调整净利却只剩49亿，靠ASP同比涨四成和砍低端机撑住"),
    (6, "短剧与AI应用挤走高毛利广告主，二线平台只赚点击过路费，DAU粘性同步下滑"),
    (9, "三四线去化周期31.6个月，出租跑不赢国债，卖房换金融资产成'收息佬'选择"),
    (21, "瑞穗首次覆盖给205美元目标价，看重Starlink与AI整合的长期变现能力"),
]

# invest 保留 8 条：摩根大通十大风险 / A股午盘翻绿 / 戴尔积压订单 / 小米拐点 /
#                     出口管制立法 / 闪迪NAND / 摩根大通金属 / OpenAI网络安全
INVEST_KEEP = [
    (7, "报告称中期选举后十大风险同框，年底五周要同时消化五重冲击"),
    (4, "早盘一度回升，午盘三大指数集体翻绿，光模块走强、半导体继续杀跌"),
    (10, "积压订单1323亿美元创历史新高，AI代理把需求推向传统服务器"),
    (6, "三家大行维持买入，增至2027年复苏；盈利修正被认为已触底"),
    (0, "巴克莱称复职给两党议员加速出口管制立法提供新政治动能"),
    (3, "管理层重申1.2ZB的AI数据中心NAND规模预测，称中国能吃下全部增量"),
    (1, "铜铝继续看空、黄金称接近阶段底，修复窗口指向2027下半年"),
    (5, "网络安全被列为增长新曲线，CFO称3000亿美元TAM估算仍严重偏低"),
]

OUTFIT = (
    "上海白天阴、此刻晴间多云，午间最高12.1℃，清晨最低2.4℃，体感8.9℃；"
    "降水为零、湿度37%，是干冷不是湿冷。中午薄羊毛衫加防风尼龙外套就够，"
    "进室内脱到卫衣也不臃肿；早晚叠一件抓绒或羽绒马甲，羊绒围巾护住脖子，"
    "避开容易起静电的化纤绒里。"
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
