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
# 2026-11-27 18:00 班（18 点班：部署）。
#
# 跨班查重基线（本轮重建）：
#   · drive 归档 html 13 份（11-22-18 ~ 11-27-12）正则抽 n-title → 157 条去重「已展示」标题
#   · 仓库 editorial.json（12:00 班）order / hide 全量并入
#   · 两个存活部署站（dnb4q47zlffx1=11-24 18:00、0hmfcoyfcntn2=11-26 18:00）口径同上
#   · GitHub 历史 revision 本轮没拉到（api.github.com 限流），用归档口径 + 记忆里的簇记录兜底
#   （判据仍是「基线里实际展示过」，池里没上过的不算重复）
#
# ★ 本轮值得记的现象：
#   1) 标题级撞车只有 1 条：business[16]「20个AI Agents组队…ClickBench」=
#      12:00 班刚展示过 → hide。
#   2) business[7] 与 business[13] 是同一事件：蚂蚁灵波 11-27 当天发布 LingBot-Map 2.0
#      + LingBot-Navi，量子位发了两篇同源稿 → 按「同事件只留一条」只留信息更全的 [13]。
#   3) 爱奇艺也是两条同事件：business[6]「跌破1美元」vs business[32]「长视频的挽歌」
#      → 留 [6]（硬事实齐：30 个交易日低于 1 美元、2027-05-24 前需连续 10 个工作日回稳、
#      Q3 营收 60.1 亿 -10%、经营现金流转正）；[32] 纯评论 → hide。
#   4) ★ 韦东奕那条**不是**黎曼猜想：是与陈琦、章志飞合作解决「管道 Poiseuille 流
#      在大雷诺数下的线性稳定性」，悬了近 140 年的流体力学难题，成果发在 CPAM /
#      Annales ENS 等顶刊 → 与基线里黎曼 / 陶哲轩 / Claude 数学簇不同题，可上。
#   5) 英伟达簇基线 5 条全是黄仁勋复职 / 股价 / 估值；本轮 business[12] 是「11-26 起
#      禁止向马来、新加坡、泰国、印尼发服务器」的出口管制新事件，机制与主体都不同 → 可上。
#   6) 广州车展稿（阿维塔 / 蔚来 / 奔驰 / 零跑 / 问界 / 领克 / 华为巨鲸 / 广汽丰田 /
#      宝马 / 大众）共 10 条 → 全部 hide。
#   7) 软文 / 活动 / 评测 / 评论稿（钛动×腾讯云、天元重工、MEET2027 报名、
#      Claude Opus 做 PPT、Mate X8 评测、35岁危机、老铺黄金、具身抱团回应）→ 全部 hide。
#   8) invest[1]「AI交易回暖，纳指期货盘前涨2.5%」与基线已展示的「AI交易抛售压力缓解，
#      美股盘前科技股集体反弹」正面重叠 → hide。
#   9) invest[3] 与 invest[8] 属同一事件簇（国常会稳市），但角度不同：
#      [3]=国内政策工具箱 + 科技股涨停潮；[8]=亚太扩散（日经 / KOSPI）+ 券商定价
#      → 按「同簇 ≤2 条不同角度」两条全留。
#  10) business[30]「欧洲电商巨头涌向二手市场」是黑五簇第三条（12:00 班已展示直邮之死
#      + BNPL 213 亿）→ hide；改留 business[3] 车企二手车残值（主体不同：残值管理机制
#      而非欧洲礼品供给），硬数据同样扎实。
#  11) 数据要素新规、电池出保、零次方融资三条都是当天新事件，基线零命中 → 全留。
#
# business 保留 6 条：英伟达断供东南亚 / DeepSeek 领跑OpenRouter / 爱奇艺跌破1美元 /
#                      支付宝车载助手3.0 / 韦东奕泊肃叶流难题 / 车企二手车残值
BUSINESS_KEEP = [
    (12, "出口管制掐住四国转运，戴尔AI积压订单冲到1323亿美元却发不出去"),
    (0, "OpenRouter近30天榜前三全是中国模型，新版只跑满一周期就拉出745%涨幅"),
    (6, "连续30个交易日低于1美元触发纳斯达克警告，须在2027年5月24日前回稳10个工作日"),
    (2, "车企握语音主导权，支付宝退到后台对接商户与支付，已绑特斯拉、比亚迪等品牌"),
    (1, "与陈琦、章志飞合作解决泊肃叶流高雷诺数线性稳定性，论文发在CPAM等顶刊"),
    (3, "四年二手价格指数跌23.1%，约为新车跌幅两倍，三年以上新能源车源已占八成"),
]

# invest 保留 7 条：国常会稳市 / 亚洲救市 / 美团Q3 / AI泄露警告 /
#                    数据要素新规 / 动力电池出保 / 零次方机器人融资
INVEST_KEEP = [
    (3, "汇金类平准基金功能被点名优化，创业板收涨11.61%，科创50冲上12%"),
    (8, "日经涨2%、韩国KOSPI涨4%，机构把这轮拉升定性为信心修复而非单纯超跌"),
    (0, "营收1155.6亿超预期，营业利润27.4亿远超分析师预估5.27亿，外卖价格战降温"),
    (2, "Cognition CEO判断未来6到12个月难挡重大泄露，财富50强与政府机构高风险"),
    (10, "国家数据局11月26日就数据要素新规征求意见，12月6日截止，模型训练取材先立边界"),
    (7, "乘联分会估年底有260万辆车龄超8年新能源出保，换电池可能比卖车还贵"),
    (11, "清科产投等产业资本进场，团队出自清华AI机器人实验室，年底开放抓取API"),
]

OUTFIT = (
    "上海此刻晴，14.9℃、体感13.2℃，白天最高19.2℃、清晨最低8.2℃，"
    "昼夜温差近11℃；湿度68%，降水概率几乎为零。白天薄针织或衬衫单穿就够，"
    "傍晚风起再加件薄风衣或薄开衫，叠穿收腰也不显臃肿。"
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
