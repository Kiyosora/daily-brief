#!/usr/bin/env python3
"""跨班查重基线构建器。

从 drive 的归档 html 节点里抽出「上一批班次实际展示过的标题」，
作为本轮选题的重复基线。

cdn_url 由 node_id + 签名 + 可选子目录拼装（避免手抄整串 URL 出错）。
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

HOST = "https://matrix-internal-cn.oss-cn-shanghai.aliyuncs.com/Mavis/482531219858612224/files"
FNAME = "%E4%BB%8A%E6%97%A5%E7%AE%80%E6%8A%A5-{date}.html"
QUERY = "Expires=1795608107&OSSAccessKeyId=LTAI5tD6kjGs53up52CwdPJ3&Signature={sig}"

# (日期, node_id, 子目录或None, 签名)
ARCHIVES = [
    ("2026-11-25-12", "467055057740361", "467055057740360", "3kM9wjAA9ahYoFMunQStYkvhOWc%3D"),
    ("2026-11-25-06", "466965480714560", "466958377119934", "mQn3iXkTdvnyD3Ak7vNsaTeF7GY%3D"),
    ("2026-11-24-18", "466789207224518", "466789207224517", "5Vm0ZoQSz2VMd86xUfYjNzaF7vI%3D"),
    ("2026-11-24-12", "466700577288666", "466700577288665", "CWkpWkOErSoZ8%2BXnjVjV6HEozvQ%3D"),
    ("2026-11-24-06", "466609990537827", "466609990537826", "wqz9vFio%2BUO0y76rIQONxaPN8M4%3D"),
    ("2026-11-23-18", "466433827275060", "466433827275059", "SyMldJD/lNlMzBYMqFb2HuFAgBM%3D"),
    ("2026-11-23-12", "466348145267255", None, "gfAznxRQ8o9ikIPKQg%2BWUVPPkcI%3D"),
    ("2026-11-23-06", "466254768542672", None, "DhvQf%2BCfll9SaR0Hk224OjraeJM%3D"),
    ("2026-11-22-18", "466079325467366", None, "5H7G9za8H50GjtRIzzx1rIhxoxo%3D"),
    ("2026-11-22-12", "465991356616983", None, "nO2QU4fK0ejLcxP74tzyrJLUU2Q%3D"),
    ("2026-11-22-06", "465896824156521", None, "F8N0FCxxHoIumLt2u/zJ3cLy4eo%3D"),
    ("2026-11-21-18", "465726339133818", None, "Yt/9CFm0TcO5qcbD5Cn0ZJd57ZE%3D"),
    ("2026-11-21-12", "465638774018597", None, "JrHCLQVe9q4rI2bBrHbyXOWuD6c%3D"),
    ("2026-11-21-06", "465546724061655", None, "hqEBb40z1U1cT%2BVCGfF4L2eYM7U%3D"),
    ("2026-11-20-06", "465187686273317", None, "3hPuDsDSZFV1tUt3QJ6KRs%2B3vgI%3D"),
    ("2026-11-19-18", "465020244357419", None, "3fmJ7G6GvtgQpS1kkF%2BWGul59rI%3D"),
]

TITLE_RE = re.compile(r'<a class="n-title"[^>]*>(.*?)</a>', re.S)
OUT = Path(__file__).resolve().parent / "baseline_titles.json"


def url_for(date: str, node: str, sub: str | None, sig: str) -> str:
    base = f"{HOST}/{node}" + (f"/{sub}" if sub else "")
    return f"{base}/{FNAME.format(date=date)}?{QUERY.format(sig=sig)}"


def main() -> None:
    baseline: dict[str, list[str]] = {}
    failures: list[str] = []
    for date, node, sub, sig in ARCHIVES:
        url = url_for(date, node, sub, sig)
        out = Path(f"/tmp/arch_{date}.html")
        r = subprocess.run(
            ["curl", "-sS", "-o", str(out), "-w", "%{http_code}", "--max-time", "40", url],
            capture_output=True, text=True,
        )
        code = (r.stdout or "").strip()[-3:]
        size = out.stat().st_size if out.exists() else 0
        body = out.read_text(encoding="utf-8", errors="ignore") if size else ""
        if code != "200" or size < 10000 or "SignatureDoesNotMatch" in body:
            failures.append(f"{date}: http={code} size={size}")
            print(f"[FAIL] {date}  http={code} size={size}", file=sys.stderr)
            continue
        titles = []
        for t in TITLE_RE.findall(body):
            t = re.sub(r"<[^>]+>", "", t)
            t = html.unescape(t).strip()
            # 排除 JS 模板串里的 esc(it.title) 占位
            if not t or "esc(" in t or "it.title" in t:
                continue
            titles.append(t)
        baseline[date] = titles
        print(f"[ok] {date}  {len(titles)} 条")

    allt = [t for v in baseline.values() for t in v]
    uniq = sorted(set(allt))
    OUT.write_text(json.dumps({"per_shift": baseline, "all": allt, "uniq": uniq},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 基线: {len(baseline)} 班 / {len(allt)} 条 / 去重 {len(uniq)} ===")
    if failures:
        print(f"[warn] 失败 {len(failures)}: {failures}")
    print(f"[ok] -> {OUT}")


if __name__ == "__main__":
    main()
