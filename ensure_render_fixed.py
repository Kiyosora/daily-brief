#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""幂等补丁：修 render.py 的三个已知缺陷（沙箱每次全新，补丁需随轮次重建）。

1) 静态烘焙层用 id 取点评（COMMENTS.get(r["id"])），但 editorial 约定以「标题原文」为标识
   → 无 JS 的首屏一条点评都看不到。改为标题优先、id 兜底。
2) 浏览器端实时层不认识 editorial 的 hide 名单（只有硬编码 ADWORDS 正则）
   → 被隐藏的软文/会议/未选中条目在页面上复活。把 hide 注入 baked，JS 侧统一排除。
3) 实时源标题与烘焙标题可能有全/半角空格差异（"|  附指南" vs "| 附指南"）
   → 精确字符串比较漏判。统一用 normT() 压缩空白后比较，精选匹配与点评查找走同一套。

另修：data-id/data-t 只替换了 business 字符串，invest 条目没挂上 → 一并修正。

用法: python3 ensure_render_fixed.py render.py
"""
import pathlib
import sys

MARK = "/* __PATCHED_V2__ */"

PATCHES = [
    # ---- 修复 1：静态层按标题取点评 ----
    (
        '        c = COMMENTS.get(r.get("id", ""))\n',
        '        c = COMMENTS.get(r.get("title", "")) or COMMENTS.get(r.get("id", ""))\n',
    ),
    # ---- 修复 2a：把 hide 名单注入 baked，供 JS 实时层使用 ----
    (
        '    baked = {"ts": DATA.get("generated_at", ""), "news": baked_news,\n'
        '             "comments": title_comments, "curated": curated}\n',
        '    baked = {"ts": DATA.get("generated_at", ""), "news": baked_news,\n'
        '             "comments": title_comments, "curated": curated,\n'
        '             "hide": sorted(HIDE)}\n',
    ),
    # ---- 修复 2b + 3：JS 侧注入 normT / HIDES / CMAP ----
    (
        'var CFG = __CFG__;\nvar BAKED = __BAKED__;\n',
        'var CFG = __CFG__;\nvar BAKED = __BAKED__;\n'
        '/* __PATCHED_V2__ */\n'
        "/* 标题归一化：压缩全角/半角空白差异，保证精选匹配与点评查找一致 */\n"
        "function normT(s){return String(s==null?'':s).replace(/[\\s\\u3000]+/g,' ').trim();}\n"
        'var HIDES=(BAKED.hide||[]).map(normT);\n'
        'var CMAP={};\n'
        'Object.keys(BAKED.comments||{}).forEach(function(k){var n=normT(k);if(n&&!CMAP[n])CMAP[n]=BAKED.comments[k];});\n',
    ),
    # ---- 修复 2b：实时层过滤 hide 名单 ----
    (
        "  var clean=items.filter(function(it){return !ADWORDS.test(it.title||'');});\n",
        "  var clean=items.filter(function(it){\n"
        "    if(ADWORDS.test(it.title||'')) return false;\n"
        "    if(HIDES.indexOf(normT(it.title))>=0) return false;\n"
        "    return true;\n"
        "  });\n",
    ),
    # ---- 修复 3：精选匹配按 normT 对齐 ----
    (
        "    var byTitle={};\n"
        "    clean.forEach(function(it){ if(!byTitle[it.title]) byTitle[it.title]=it; });\n"
        "    var ordered=[],used={};\n"
        "    curated.forEach(function(c){\n"
        "      var it=byTitle[c.t];\n"
        "      if(it){ ordered.push(it); used[c.t]=1; }\n"
        "      else { ordered.push({title:c.t,link:c.l,site:c.s,published:c.p}); }\n"
        "    });\n"
        "    clean.forEach(function(it){ if(!used[it.title]) ordered.push(it); });\n",
        "    var byTitle={};\n"
        "    clean.forEach(function(it){ var n=normT(it.title); if(!byTitle[n]) byTitle[n]=it; });\n"
        "    var ordered=[],used={};\n"
        "    curated.forEach(function(c){\n"
        "      var n=normT(c.t);\n"
        "      if(HIDES.indexOf(n)>=0) return;\n"
        "      var it=byTitle[n];\n"
        "      if(it){ ordered.push(it); used[normT(it.title)]=1; }\n"
        "      else { ordered.push({title:c.t,link:c.l,site:c.s,published:c.p}); }\n"
        "    });\n"
        "    clean.forEach(function(it){ if(!used[normT(it.title)]) ordered.push(it); });\n",
    ),
    # ---- 修复 3：点评查找走 CMAP（归一化键） ----
    (
        '    var c=(BAKED.comments||{})[it.title];\n',
        '    var c=CMAP[normT(it.title)];\n',
    ),
    # ---- 附带：invest 条目也挂上 data-id / data-t ----
    (
        "    for key in (\"business\", \"invest\"):\n"
        "        for r in news.get(key, []):\n"
        "            rid = r.get(\"id\")\n"
        "            if rid:\n"
        "                business = business.replace(\n"
        "                    f'<article class=\"news-item\"><a class=\"n-title\" href=\"{e(r.get(\"link\",\"\"))}\"',\n"
        "                    f'<article class=\"news-item\" data-id=\"{rid}\" data-t=\"{e(r.get(\"title\",\"\"))}\"><a class=\"n-title\" href=\"{e(r.get(\"link\",\"\"))}\"')\n",
        "    for key, html in ((\"business\", business), (\"invest\", invest)):\n"
        "        for r in news.get(key, []):\n"
        "            rid = r.get(\"id\")\n"
        "            if rid:\n"
        "                html = html.replace(\n"
        "                    f'<article class=\"news-item\"><a class=\"n-title\" href=\"{e(r.get(\"link\",\"\"))}\"',\n"
        "                    f'<article class=\"news-item\" data-id=\"{rid}\" data-t=\"{e(r.get(\"title\",\"\"))}\"><a class=\"n-title\" href=\"{e(r.get(\"link\",\"\"))}\"')\n"
        "        if key == \"business\":\n"
        "            business = html\n"
        "        else:\n"
        "            invest = html\n",
    ),
]


def main() -> int:
    target = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "render.py")
    text = target.read_text(encoding="utf-8")
    if MARK in text:
        print(f"[skip] {target.name} 已是补丁版（{MARK}）")
        return 0
    for i, (old, new) in enumerate(PATCHES, 1):
        if new in text:
            print(f"[ok] 补丁 {i} 已存在，跳过")
            continue
        if old not in text:
            print(f"[fail] 补丁 {i} 锚点未找到：\n{old[:120]}")
            return 1
        text = text.replace(old, new, 1)
        print(f"[ok] 补丁 {i} 已应用")
    target.write_text(text, encoding="utf-8")
    print(f"[done] {target} 补丁完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
