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
# 2026-11-24 12:00 班（12 点班：只归档，不部署）。
#
# 跨班查重基线：拉取 11-20 06:00 / 11-21 06:00 / 11-21 12:00 / 11-21 18:00 /
# 11-22 06:00 / 11-22 12:00 / 11-22 18:00 / 11-23 06:00 / 11-23 12:00 /
# 11-23 18:00 / 11-24 06:00 共 11 班归档 html，正则 <a class="n-title"> 抽出
# 实际展示标题 = 135 条（去重 129）。
#
# ★ 本轮头号现象：新闻池被「黄仁勋回归」事件簇刷屏 ——
#   business 侧 8 条（[4][5][8][11][12][30][32]）+ invest 侧 8 条（[0][2][3][4][5][6][7][8][9]），
#   占 46 条候选池的 1/3。而事件本体在 11-24 06:00 班已上过 2 条
#   （事件本体+股价、信用市场传导），本轮必须按事件簇收敛，只保留新增事实的不同角度。
#
# hide 的四类来源：
#   1) 标题级跨班旧稿（11 班基线命中）：
#      端侧大模型实测、XROGO 进工厂、蚂蚁医疗AI五连发、Agent版arXiv、
#      RoboChallenge Zero、iPhone 18 明年春。
#   2) 事件簇饱和（标题不重复但事件重复）：
#      · 黄仁勋复职簇：11-24 06:00 已上事件本体与信用市场传导，本轮只留
#        invest[0] 市场机制（对冲失效/空头止损/野村警告）+ invest[6] 白宫政治线
#        （特朗普背书、万斯协调、董事会提前告知白宫）两条不同角度；
#        business[4][5][8][11][12][30][32]、invest[2][7][8][9] 全部 hide。
#        invest[3] 亚太股市综述、invest[4] A股盘面综述属「亚洲市场」独立选题，
#        保留前者、hide 后者（与页面行情 chip 重复且只剩盘中噪音）。
#      · 黎曼猜想簇：business[2] 主导者回应、business[31] 早报内含黎曼条目 →
#        连同 11-21/11-22/11-23 三班已上的黎曼/Lean/NS 方程一并 hide。
#      · 具身基础模型簇：business[1] 实为自变量 WALL-OSS-1.0 + WALL-API-1.0 软文，
#        11-23 18:00 已上 WALL-OSS-1.0 与 WALL-API → hide。
#      · 蚂蚁阿福开源簇：business[19] 同款模型开源，11-23 18:00 已上「五连发」→ hide。
#      · 豆包工作簇：business[28] 21 个专业工作台，11-24 06:00 已上「腾讯字节 AI 办公」→ hide。
#      · 潮玩消费簇：business[0] 名创优品+泡泡玛特，11-20 06:00 / 11-21 18:00 已上
#        名创优品利润、泡泡玛特分蛋糕两条 → hide。
#      · 华为星芒簇：business[29] 评测稿 → hide。
#   3) 栏目稿 / 软文 / 评测 / 观点随笔：
#      business[14] AI 审美降级、business[18] AI 一人公司与网红、business[20] 雷克萨斯 ES 车评、
#      business[22] 存储经济性软文、business[23] 醒图新版本、business[26] XREAL AURA 体验、
#      business[29] 华为星芒评测、business[5]/[31] 爱范儿早报、invest[10] 华尔街见闻早餐 FM。
#   4) 已上过但角度未变：business[17] 自变量 WALL-API、business[2]/[31] 黎曼相关。
#
# business 保留 6 条：DeepSeek股东 / 芯片IPO / 长租公寓资本换血 / 自免被做空 /
#                      短剧演员卖脸 / 盒马催货函
BUSINESS_KEEP = [
    (27, "宁德时代、吉利入股，但梁文锋用治理结构焊死了投资者的经营话语权。"),
    (3, "星思半导体拿到赴港备案，估值曾打折六折，如今靠国资输血回到百亿。"),
    (9, "友邦两年出手两次、7507间房源险资接盘，开发商系基金开始退出。"),
    (21, "Abivax遭297页报告做空，靶心却是指向中国临床数据。"),
    (15, "有人主动卖脸授权做数字分身，也有人发现角色被AI顶替。"),
    (24, "盒马一纸预警函给3岁酸菜品牌免费背书，销量比三月涨六倍。"),
]

# invest 保留 5 条：Claude P/NP / 鲍曼调查 / 轧空机制 / 亚太股市 / 白宫政治线
# 黄仁勋复职事件簇只留 2 条不同角度：invest[0]（市场机制+野村警告）、invest[6]（政治线）。
# invest[3] 亚太股市综述单列为「亚洲市场」选题。
INVEST_KEEP = [
    (1, "论文唯一作者署名Claude，Lean全篇机器验证，但未经数学家人工审阅。"),
    (11, "美联储内部监察机构就6月17日私人晚宴约谈鲍曼，指向静默期违规。"),
    (0, "野村拆解：期权对冲失效叠加空头止损，机械性反弹解决不了结构问题。"),
    (3, "亚太指数终结八连跌，韩股涨超7%、SK海力士涨10%，芯片股领涨。"),
    (6, "复职宣布不到十分钟特朗普即公开背书，万斯按指示参与幕后协调。"),
]

OUTFIT = (
    "上海今早多云，十二度三、体感八度三，白天最高十二度四，入夜最低五度一，湿度四成九，"
    "降水概率两成三，白天有零星小毛毛雨。昼夜温差七度多，穿细密绒面打底叠轻薄羽绒马甲，"
    "外搭防泼水尼龙壳挡雨；下身厚斜纹长裤配防滑短靴，别穿平底帆布鞋。"
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
