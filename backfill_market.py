#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行情源回填（eastmoney 在本沙箱出口被切断时的备用实现）。

主源：腾讯 qt.gtimg.cn     兜底：新浪 hq.sinajs.cn
输出 schema 与 collect.collect_market() 完全一致：name/code/value/pct/change。

腾讯行情行布局（实测 + 新浪交叉校验）：
  A股/港股指数: [1]=名称 [2]=代码 [3]=当前价 [4]=昨收 [31]=涨跌额 [32]=涨跌幅%
  腾讯外汇 wh*:  [1]=名称 [2]=代码 [3]=当前价 [6]=昨收 [12]=涨跌额 [13]=涨跌幅%
新浪 s_ 指数:   [0]=名称 [1]=当前点数 [2]=涨跌额 [3]=涨跌幅%
新浪 fx_s:      [1]=当前价 [3]=昨收 [10]=涨跌幅% [11]=涨跌额 [12]=振幅
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# 配置里的 eastmoney secid -> (腾讯代码, 新浪代码)
MAP = {
    "1.000001": ("sh000001", "s_sh000001", "index"),
    "0.399001": ("sz399001", "s_sz399001", "index"),
    "0.399006": ("sz399006", "s_sz399006", "index"),
    "1.000300": ("sh000300", "s_sh000300", "index"),
    "1.000016": ("sh000016", "s_sh000016", "index"),
    "100.HSI": ("hkHSI", "rt_hkHSI", "index"),
    "133.USDCNH": ("whUSDCNY", "fx_susdcnh", "fx"),
}

NAMES = {
    "1.000001": "上证指数",
    "0.399001": "深证成指",
    "0.399006": "创业板指",
    "1.000300": "沪深300",
    "1.000016": "上证50",
    "100.HSI": "恒生指数",
    "133.USDCNH": "离岸人民币",
}


def http(url: str, referer: str | None = None, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gb18030", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def f(x: str) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


def parse_tencent(text: str, kind: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in text.splitlines():
        m = re.match(r'v_([A-Za-z0-9_]+)="(.*)";', line.strip())
        if not m:
            continue
        code, payload = m.group(1), m.group(2)
        p = payload.split("~")
        if len(p) < 14:
            continue
        if kind == "fx":
            value, prev, chg_i, pct_i = f(p[3]), f(p[6]), 12, 13
        else:
            value, prev, chg_i, pct_i = f(p[3]), f(p[4]), 31, 32
        if value is None or len(p) <= pct_i:
            continue
        chg = f(p[chg_i])
        pct = f(p[pct_i])
        if chg is None:
            chg = round(value - prev, 6) if prev is not None else 0.0
        if pct is None:
            pct = round(chg / prev * 100, 4) if prev else 0.0
        out[code] = {
            "name": p[1] or code,
            "code": p[2] or code,
            "value": round(value, 4),
            "pct": round(pct, 4),
            "change": round(chg, 6),
        }
    return out


def parse_sina(text: str, kind: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in text.splitlines():
        m = re.match(r'var hq_str_([A-Za-z0-9_]+)="(.*)";', line.strip())
        if not m:
            continue
        code, payload = m.group(1), m.group(2)
        p = payload.split(",")
        if kind == "fx":
            if len(p) < 13:
                continue
            value, prev, pct, chg = f(p[1]), f(p[3]), f(p[10]), f(p[11])
        else:
            if len(p) < 4:
                continue
            value, chg, pct = f(p[1]), f(p[2]), f(p[3])
            prev = None
        if value is None:
            continue
        out[code] = {
            "name": NAMES.get(code, code),
            "code": code,
            "value": round(value, 4),
            "pct": round(pct, 4) if pct is not None else 0.0,
            "change": round(chg, 6) if chg is not None else 0.0,
        }
    return out


def collect() -> tuple[list[dict], list[str]]:
    notes: list[str] = []
    tencent: dict[str, dict] = {}
    sina: dict[str, dict] = {}

    t_codes = ",".join(v[0] for v in MAP.values())
    try:
        tencent = parse_tencent(http(f"https://qt.gtimg.cn/q={t_codes}"), "mixed")
    except Exception as exc:  # noqa: BLE001
        notes.append(f"tencent failed: {exc}")
    # 分类型重抓（指数与外汇字段位不同）
    for kind in ("index", "fx"):
        codes = ",".join(v[0] for v in MAP.values() if v[2] == kind)
        try:
            tencent.update(parse_tencent(http(f"https://qt.gtimg.cn/q={codes}"), kind))
        except Exception as exc:  # noqa: BLE001
            notes.append(f"tencent[{kind}] failed: {exc}")

    s_codes = ",".join(v[1] for v in MAP.values())
    try:
        sina = parse_sina(
            http(f"https://hq.sinajs.cn/list={s_codes}", referer="https://finance.sina.com.cn"),
            "mixed",
        )
    except Exception as exc:  # noqa: BLE001
        notes.append(f"sina failed: {exc}")
    for kind in ("index", "fx"):
        codes = ",".join(v[1] for v in MAP.values() if v[2] == kind)
        try:
            sina.update(
                parse_sina(
                    http(f"https://hq.sinajs.cn/list={codes}", referer="https://finance.sina.com.cn"),
                    kind,
                )
            )
        except Exception as exc:  # noqa: BLE001
            notes.append(f"sina[{kind}] failed: {exc}")

    rows: list[dict] = []
    for secid, (tcode, scode, kind) in MAP.items():
        t = tencent.get(tcode)
        s = sina.get(scode)
        picked, source = None, ""
        if t and s:
            # 双源交叉校验：涨跌幅一致（容差 0.15%）才采用腾讯值
            if abs(t["pct"] - s["pct"]) <= 0.15:
                picked, source = t, "tencent+sina"
            else:
                picked, source = t, "tencent(新浪校验偏差)"
                notes.append(
                    f"{secid} pct mismatch: tencent={t['pct']} sina={s['pct']}"
                )
        elif t:
            picked, source = t, "tencent"
        elif s:
            picked, source = s, "sina"
        if not picked:
            notes.append(f"{secid}: both sources failed")
            continue
        picked["name"] = NAMES.get(secid, picked["name"])
        picked["code"] = secid
        picked["_source"] = source
        rows.append(picked)
    return rows, notes


def main() -> int:
    rows, notes = collect()
    for n in notes:
        print(f"[note] {n}")
    if not rows:
        print("[fail] no market rows")
        return 1
    data_path = pathlib.Path(__file__).parent / "data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    data["market"] = rows
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] market backfilled: {len(rows)} items")
    for r in rows:
        print(
            f"   {r['name']:<8} {r['value']:>10} {r['pct']:>7}% "
            f"chg={r['change']:>8} src={r['_source']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
