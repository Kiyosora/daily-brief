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
# 2026-11-23 18:00 班（18 点班：部署）。
#
# 跨班查重：下载 11-21 12:00 / 11-21 18:00 / 11-22 12:00 / 11-22 18:00 /
# 11-23 06:00 / 11-23 12:00 共 6 班归档 html，正则抽出实际展示标题（去重后 67 条）
# 作基线，与本轮 46 条候选池逐条比对。
# （11-21 06:00 / 11-22 06:00 两个归档节点 OSS 签名取不到，已用记忆里的班次记录补齐判断。）
#
# 本轮候选池：business 34 条（三源轮转合并后）、invest 12 条。
# hide 的三类来源：
#   1) 软文 / 栏目稿：爱范儿早报｜、XREAL 体验、醒图新版本、华为星芒 O1 Pro 评测、
#      雷克萨斯 ES 车评、计算日 Token 成本、GTA6 随笔、机器人老板做自媒体、
#      AI 情绪生意、陪伴机器人留存、存储经济性软文、华尔街见闻「药捷安康研发日」活动稿。
#   2) 跨班旧稿（标题级命中）：iPhone 18 明年春、Nature 电刺激控糖、A 社另一道千禧难题、
#      黎曼猜想簇（爱范儿两条 + 早报内一条）、美股一夜崩盘情绪文。
#   3) 事件簇饱和（标题不重复但事件重复）：
#      · 现金流簇第 4 次（11-21 06:00 阿里现金流拐点 → 11-21 12:00 现金流为王周期
#        → 11-23 06:00 拆解大厂财报 AI 花钱 → 本轮 business[21] 现金流不会说谎）→ hide；
#      · 豆包办公 / WorkBuddy 簇（11-21 06:00 腾讯AI与WorkBuddy 已上）→ hide；
#      · 姚顺雨 Reddit AMA（11-21 12:00 同场 AMA）→ hide；
#      · 黄金簇（11-22 18:00 流动性提款机 + 11-23 06:00 黄金提款机）→ invest[9] 广发金价 hide；
#      · 沪指 3500 点（11-23 12:00 沪指失守3500）→ invest[10] 沪指收复3500 hide；
#      · 美股抄底簇：invest[2] 盘前反弹（事实）与 invest[7] 大摩喊抄底（观点）同簇 → 只留事实那条；
#      · 蚂蚁阿福簇跨板块：business[4] 五连发（产品面）vs invest[3] UpToDate 接入（合作面）
#        → 只留 business 那条；同源的 business[10] 开源同款模型、business[6] 大厂绕开医保也一并 hide；
#      · 自变量簇跨板块：invest[8] WALL-OSS-1.0（动作数据前置进预训练）与
#        business[5] WALL-API-1.0 同源同事件 → 只留 invest 那条。
#
# business 保留 5 条：AI 科研社区 / 真机评测 / 医疗大模型 / 机器人落地 / 求解器融资
BUSINESS_KEEP = [
    (7, "智能体自建期刊互审，查出代码泄漏后准确率由九成一掉到六成四。"),
    (16, "真机三百三十次测试整体成功率不足四成五，最佳模型七成，书写五十五次只成四次。"),
    (4, "一口气五模型两款开源，124B多模态版可本地部署，病历不必外传。"),
    (1, "上半年我国人形机器人出货超四万台，超六成项目仍停在验证演示阶段。"),
    (3, "数亿元D轮，上海集成电路基金首次出手软件，看中数学规划求解器。"),
]

# invest 保留 7 条：美股反弹 + 信用市场 + 卖方存储框架 + 具身模型 + 能源 + 资金流向 + 并购退出
INVEST_KEEP = [
    (2, "盘前科技股集体反弹，英伟达涨近10%，纳指期货涨超3%、黄金涨超2%。"),
    (11, "高收益债利差创年内最大单周走阔，抛售开始从低评级向高评级扩散。"),
    (5, "逻辑不是否定当前盈利，而是把2028年从极端短缺改判为供需再平衡。"),
    (8, "具身基础模型直接由画面和指令输出动作，动作数据前置进预训练阶段。"),
    (1, "布伦特本月跌逾两成至每桶92美元，欧洲却因炼能萎缩陷入柴油短缺。"),
    (4, "因缺AI敞口被冷落的印度股市，本月MSCI印度累计涨11%重获资金青睐。"),
    (0, "十年合资走到散伙，华润以四成折让要约退出，外资接盘42.6%股权。"),
]

OUTFIT = (
    "上海今天阴，白天转零星小毛毛雨，现在十三度八、体感十二度，最高十七度、"
    "入夜滑到十一度，湿度七成一，降水概率两成。"
    "穿搭走细密棉针织打底加轻薄羽绒马甲，外层防泼水防风壳；"
    "下身直筒厚长裤配加绒短靴，湿滑路面别穿平底布鞋。"
    "包里塞把折伞，走风大的路口记得收伞骨。"
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
