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
# 2026-11-26 06:00 班（06 点班：只生成 + 推 GitHub + 归档，不部署）。
#
# 跨班查重基线：drive 里 12 份归档 html（11-21 18:00 ~ 11-25 12:00）用
# space_download 全部拉回本地，正则 <a class="n-title"[^>]*>(.*?)</a> 抽出实际展示标题
# = 153 条去重标题；另加 11-25 18:00 班（仓库 editorial.json order）13 条
# —— 该班部署两次全部 404、归档 html 未入库，只能从 GitHub 仓库回补，合计 166 条。
#
# ★ 本轮值得记的现象：
#   1) **11-25 18:00 班的两次部署都 404**（节点 今日简报-n71k6z4dpcpbx /
#      今日简报-yazhhf5f9l42v），线上主地址仍是 11-24 18:00 的 dnb4q47zlffx1，
#      停在 11-24 快照。那班归档 html 也没进 drive，只在 GitHub 仓库留了 editorial.json
#      → **基线要同时读「归档 html」和「仓库 editorial.json」，否则会漏掉上一班。**
#   2) **Loop 架构簇饱和**：11-25 18:00 班已上「智谱 GLM-5.4 首用 Loop Transformer」，
#      本轮 business[16] 是同一架构的深度拆解（9400万参数、显存降98%、LoopWM 论文）。
#      虽然标题级全新，但事件已上过 → hide，选题重心转向其他硬事实。
#   3) **黄仁勋簇基线已达 7 条**，本轮 business[18] 再辞职、business[33] 重返英伟达、
#      business[31] 早报、invest[9] WSJ 专栏评论 → 全 hide，簇内一条不留。
#   4) **Anthropic 簇基线 7 条**（含 11-25 06「Anthropic重挫14%跌破万亿」）：
#      business[15] 破发七坑、business[19] 还藏2个最强模型 → hide。
#      business[25] Tibo 加盟 OpenAI 也 hide（且与 invest[0] OpenAI 庭审同公司，避免同页重复）。
#   5) **美股盘面同事件双稿**：invest[6] 纳指跌超4%恐陷熊市 与 invest[7] 跌入熊市
#      是同一盘中事件 → 只留 [7]（含 VIX、芯片ETF、通胀超预期等更硬数据），[6] hide。
#   6) **信用线留 2 条不同角度**：invest[1] CDS 成本创新高（市场定价）
#      + invest[2] 标普列入观察负面（评级机构行动），未超「同簇 ≤2」。
#
# hide 的四类来源：
#   1) 标题级跨班旧稿（13 班基线命中）：
#      business[5] MAGI-2、business[11] 比亚迪唐EV、business[14] 实测小豆、
#      business[17] 华为折叠+鸿蒙、business[23] 苹果AI收费、business[28] 视觉泰斗创业、
#      business[29] 黎曼主导者回应、invest[A股/亚太/韩国/巴克莱/Ramp/理想/小鹏] 同事件旧稿。
#   2) 事件簇饱和（标题不重复但事件已上过）：
#      · Loop 架构簇：business[16] → hide（11-25 18:00 班已上 GLM-5.4 Loop Transformer）。
#      · 黄仁勋簇：business[18][31][33]、invest[9] → hide（基线 7 条）。
#      · Anthropic 簇：business[15][19] → hide（基线 7 条）。
#      · 黎曼/数学簇：business[29] → hide（基线 2 条 + P/NP 一条）。
#      · 豆包簇：business[30] 豆包购物入口 → hide（11-25 18:00 刚上「实测小豆」）。
#      · 医疗AI 主题：business[3] 保留 —— 它是巴伦视角的落地评测与 OpenEvidence 数据，
#        与 11-23 18「蚂蚁医疗AI五连发」、11-24 06「大厂绕开医保」都不是同一事件。
#   3) 软文 / 会议报名 / 厂商发布稿 / 观点随笔：
#      business[2] 拓竹 3D打印机、business[4] IDCC 议程、business[10] 九章云极峰会、
#      business[8][31] 爱范儿早报、business[12] 朋友圈随笔、business[20] AI与考试随笔、
#      business[21] 穷鬼超市、business[22] IDCC 议程、business[24] 腾讯视频随笔、
#      business[32] 数据资产说理稿、business[13] 逐际×商汤合作稿、business[26] iPhone 相机退休、
#      business[0] 海外陪伴机器人编译稿、business[25] Tibo 加盟传闻。
#   4) 下一班可考虑换上来的候选：
#      business[2] 拓竹 P3C（国补后 6374.2 元起，5 打印头+2 槽位）、
#      business[30] 豆包购物入口、business[13] 逐际动力×商汤大装置、
#      invest[5] 高盛「AI 抛售尚未见底」、invest[11] OceanBase AI 收入破亿。
#
# business 保留 6 条：医疗AI落地 / 智元AIMA生态 / 商汤开源生图模型 /
#                      和仁科技控制权 / 银行股抱团 / 岭南控股资产注入
BUSINESS_KEEP = [
    (3, "OpenEvidence月活70.3万，肝胆肿瘤智能体已推广至122家医疗机构"),
    (7, "五年投不低于20亿建AIMA生态，灵心一年孵化3万+智能体、2万+用户"),
    (1, "商汤开源生图模型SenseNova U1.6，速度极快，已上线小浣熊与ComfyUI"),
    (9, "通策医疗拟转让14%股份，宏旺微跨界成第二大股东"),
    (27, "内地银行指数三年翻倍，南向今年净买入近500亿港元，净息差仅1.4%"),
    (6, "2.07亿收购都市酒店70%股权，踩点兑现三年前资产注入承诺"),
]

# invest 保留 8 条：纳指跌入熊市 / CDS 创新高 / 标普列入负面观察 / Burry 转净多头 /
#                     美联储褐皮书 / 摩根大通看日股 / 胡塞袭击炼油厂 / OpenAI 庭审
INVEST_KEEP = [
    (7, "盘中跌4.5%，VIX升破33，芯片ETF重挫超7%，通胀强化加息预期"),
    (1, "CoreWeave与英伟达五年期CDS成本双双刷新纪录，违约概率定价逾70%"),
    (2, "AA评级被列入观察负面，90天内可能遭下调，焦点直指管理层治理"),
    (3, "清空纳指看跌期权后转为净多头，仍持英伟达看涨期权，为其近期最偏多状态"),
    (4, "12个地区维持轻微至适度扩张，数据中心与国防撑工业，高利率挤压消费"),
    (8, "信贷收紧与CTA集中去杠杆成下一压力，高收益债利差持续走阔"),
    (10, "布油一度下探89.5美元后反弹升破92美元，红海港口受威胁"),
    (0, "OpenAI指定Cravath顶级合伙人辩护，明年3月得州陪审团审理"),
]

OUTFIT = (
    "上海今天全天阴，清晨最低探到9.3℃、体感只有7.4℃，午后最高也才17.8℃，昼夜温差近8℃；"
    "降水概率不足一成但湿度70%，风里是湿冷的阴天味。选哑光厚羊毛呢大衣或防风夹克，"
    "内搭加绒卫衣叠薄针织，围条羊绒围巾护住脖子。"
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
