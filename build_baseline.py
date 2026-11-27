#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨班查重基线构建器。

产出 baseline_titles.json，两层结构：
  · displayed —— 上一批班次【实际展示过】的标题（comments + order），硬红线：
    命中即不再展示。
  · pooled    —— 进过候选池但被 hide 的标题，用来判断事件簇饱和度。

数据来源（旧的 OSS 预签名 URL 已过期，不要再用）：
  1) git 历史里所有 revision 的 editorial.json —— comments + order + hide 全量。
     这是最可靠的一份，仓库本身就是流水线的账本。
  2) drive 归档 html 的 n-title —— 用 space_download 把 /AI生成/ 递归下载到
     archives/ 后，正则抽取页面里真实渲染过的标题，补上 git 里没记到的稿子。

用法：
    cd /workspace/repo && python3 build_baseline.py            # 只用 git 历史
    python3 build_baseline.py --archives /workspace/brief/archives/ai   # 叠加归档 html
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import subprocess
import sys

TITLE_RE = re.compile(r'<a class="n-title"[^>]*>(.*?)</a>', re.S)
REPO = pathlib.Path(__file__).resolve().parent
OUT = REPO / "baseline_titles.json"


def git_titles(repo: pathlib.Path) -> tuple[set[str], set[str]]:
    """从 git 历史里所有 editorial.json 抽标题。

    返回 (displayed, pooled)。
    """
    revs = subprocess.run(
        ["git", "-C", str(repo), "log", "--all", "--format=%H"],
        capture_output=True, text=True,
    ).stdout.split()
    displayed: set[str] = set()
    pooled: set[str] = set()
    for sha in revs:
        r = subprocess.run(
            ["git", "-C", str(repo), "show", f"{sha}:editorial.json"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            continue
        try:
            ed = json.loads(r.stdout)
        except Exception:
            continue
        for t in (ed.get("comments") or {}):
            displayed.add(t)
            pooled.add(t)
        for titles in (ed.get("order") or {}).values():
            displayed.update(titles)
            pooled.update(titles)
        pooled.update(ed.get("hide") or [])
    return displayed, pooled, len(revs)


def archive_titles(root: pathlib.Path) -> set[str]:
    """从归档 html 里抽 n-title（页面真实渲染过的标题）。"""
    out: set[str] = set()
    if not root or not root.exists():
        return out
    for p in sorted(root.rglob("*.html")):
        body = p.read_text(encoding="utf-8", errors="ignore")
        for t in TITLE_RE.findall(body):
            t = re.sub(r"<[^>]+>", "", t)
            t = html.unescape(t).strip()
            if not t or "esc(" in t or "it.title" in t:
                continue
            out.add(t)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archives", default="", help="归档 html 目录（递归）")
    ap.add_argument("--repo", default=str(REPO), help="git 仓库目录")
    args = ap.parse_args()

    repo = pathlib.Path(args.repo)
    displayed, pooled, nrev = git_titles(repo)
    print(f"[ok] git 历史 {nrev} 个 revision → displayed {len(displayed)} / pooled {len(pooled)}")

    if args.archives:
        arch = archive_titles(pathlib.Path(args.archives))
        displayed |= arch
        pooled |= arch
        print(f"[ok] 归档 html 补充 {len(arch)} 条")

    OUT.write_text(
        json.dumps({"displayed": sorted(displayed), "pooled": sorted(pooled)},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] -> {OUT.name}（displayed {len(displayed)} / pooled {len(pooled)}）")


if __name__ == "__main__":
    main()
