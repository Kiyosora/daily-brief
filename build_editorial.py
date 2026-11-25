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
# 2026-11-25 18:00 班（18 点班：生成 + 推 GitHub + 部署 + 归档）。
#
# 跨班查重基线：拉 drive 里 16 份归档 html（11-19 18:00 ~ 11-25 12:00），
# 正则 <a class="n-title"[^>]*>(.*?)</a> 抽出实际展示标题 = 185 条（去重 182）。
# 16 班里 15 班一次拉通，11-22 06 那份签名过期（403），用 drive files get 重取。
#
# ★ 本轮值得记的现象：
#   1) **数据面两处临时故障，都自愈了**：
#      · 华尔街见闻 RSS 抓取超时 → invest 池整池为空（news=34 全是 business）。
#        用 refetch_invest.py 单独重抓该源补回 12 条（直连 rss.xml curl 一次成功）。
#      · eastmoney 行情被切（Remote end closed connection）→ market=0，
#        backfill_market.py 一次成功 7 项（腾讯+新浪双源交叉校验）。
#      → 教训：单源失败不等于整源报废，值得单独重试一次再决定降级。
#   2) **A股盘面在 12 点到 18 点之间彻底反转**：12:00 班展示的是早盘「震荡回升」，
#      本轮收盘是「沪指失守3500、创业板跌4.19%、超4900股飘绿」，方向完全相反。
#      这不是重复稿 —— 早盘稿是过程，收盘稿是当日定盘事实，保留并用收盘数据交叉验证。
#   3) **黄仁勋簇已到 18 条（基线），本轮候选还有 4 条同簇稿，全部 hide**：
#      business[8][31][33] + invest[10]。叠加 Anthropic 簇 14 条、黎曼簇，
#      这两个方向本轮完全空缺，选题重心整体转向「亚洲市场收盘」与「公司硬财报」。
#   4) **蚂蚁医疗健康模型与 11-23 18 班「蚂蚁医疗健康AI五连发」是同一事件** → hide。
#      韩国证安基金扩容则是 11-23 06「韩国救市」的后续（启动准备 → 摸底扩容能力），
#      事件有新事实（承诺10.76万亿韩元未缴款、仅占KOSPI市值0.3%），可作该簇第 2 条。
#
# hide 的四类来源：
#   1) 标题级跨班旧稿（16 班基线命中）：
#      business[17] 华为折叠+鸿蒙破亿、business[23] 苹果 AI 收费 | AG&I、
#      business[27] 世界模型变天了、business[30] 小米增长接力、business[32] 红果改写Q3。
#   2) 事件簇饱和（标题不重复但事件已上过）：
#      · 黄仁勋簇：business[12] 9520亿担保函、business[8][31][33]、invest[10] 董事会辞职
#        → hide（基线 18 条）。
#      · Anthropic 簇：business[1] 还藏2个最强模型、business[13] Opus 5.6 灰测、
#        business[29] 黎曼主导者回应 → hide（基线 14 条）。
#      · 世界模型簇：business[16] 高德 ABot-World → hide（基线 5 条，12:00 班刚上「世界模型变天了」）。
#      · 蚂蚁医疗簇：business[19] 蚂蚁开源医疗健康预测模型 → hide（11-23 18 班同事件）。
#      · 理想簇：business 无；invest[5] 理想 Q3 财报 → 与 11-25 06「理想去宁德化」是不同事件，保留。
#   3) 软文 / 会议报名 / 厂商发布稿 / 栏目稿 / 观点随笔：
#      business[2] 拓竹 3D 打印机、business[4] IDCC 议程、business[25] AIoT 年会议程、
#      business[28] 投资年会、business[8][31] 爱范儿早报、business[6] 腾讯金扁担随笔、
#      business[15] 年轻人攒后路、business[20] AI 与考试随笔、business[3] DQ 增长焦虑、
#      business[18] 转人工、business[9] 萨莉亚上外卖、business[21] 剧星传媒、
#      business[24] 泰励生物、business[26] iPhone 相机退休、business[7] Tibo 加盟 OpenAI（传闻）、
#      invest[2] 新债王债务危机、invest[6] 标普看空 5500、invest[9] Prosus 表态、
#      invest[11] 2027 见闻历（商品推广）。
#   4) 下一班可考虑换上来的候选：
#      business[21] 剧星传媒（2025 营收 +25.01%、净利率 1%、毛利率不足 5%）、business[24] 泰励生物、
#      business[26] 乔恩·麦考马克退休、business[9] 萨莉亚+寿司郎上美团外卖。
#
# business 保留 6 条：智谱 GLM-5.4 / 权龙创业格秩 / MAGI-2 开源 / 豆包小豆 /
#                      锂电长期可靠性 / 比亚迪第三代唐 EV
BUSINESS_KEEP = [
    (22, "首用Loop Transformer架构，纯代码渲染MV，编曲分镜全由模型自行完成"),
    (10, "六点算法提出者携港科大班底创业，复杂场景三维建模压到10美元内"),
    (5, "Sand.ai新模型图生视频登顶AA榜单，1080p官方价0.5元/秒并计划开源权重"),
    (14, "豆包新推个人智能体小豆，主打主动跟进，依托抖音生活服务与飞书生态"),
    (0, "新能安旧电池整包浸水仍可启动，储能规划产能已是全年出货预期两倍"),
    (11, "第三代唐EV砍掉第三排只做大五座，18.79万起顶配加两万选四驱线控包"),
]

# invest 保留 7 条：A股收盘 / 亚太收盘 / 韩国证安基金扩容 / AI占25%增长 /
#                     Ramp 支出放缓 / 理想Q3财报 / 小鹏科技日
INVEST_KEEP = [
    (4, "收盘沪指跌2.03%，超4900股飘绿但缩量2720亿，抗流感医药逆势涨停"),
    (8, "KOSPI收跌6.16%报4697点，SK海力士跌11%，资金转向10年期美债"),
    (0, "承诺10.76万亿韩元从未缴款，账面规模已缩到KOSPI市值的0.3%"),
    (3, "巴克莱估算AI投资贡献美国经济增长四分之一，股票占家庭净资产达35%"),
    (1, "Ramp客户token支出增速从7月42%掉到10月1.65%，两大模型商收入近乎停滞"),
    (5, "毛利率16.7%环比修复5.7个百分点，Q4指引上限331亿却远低于预期349亿"),
    (7, "Robotaxi开放主驾无人载客体验，IRON明年1月量产，YOYO-01瞄准2027年"),
]

OUTFIT = (
    "上海今天全天阴，此刻8.6℃、体感只有5.5℃，清晨最低探到2.4℃，午后也只有11.9℃，"
    "昼夜温差接近10℃；降水概率为零但湿度63%，风里是阴阴的湿冷。"
    "选哑光厚羊毛呢大衣或防风夹克，内搭加绒卫衣再叠一件薄针织衫，"
    "下装直筒牛仔裤配短靴，围条羊绒围巾护住脖子，进室内脱到卫衣。"
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
