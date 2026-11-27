#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓候选稿正文首段，用于核实硬事实（不编造数字）。"""
import json, pathlib, re, sys, urllib.request, html as htmlmod

d = json.loads(pathlib.Path('data.json').read_text(encoding='utf-8'))
news = d['news']
targets = []
for spec in sys.argv[1:]:
    cat, idx = spec.split(':')
    targets.append((cat, int(idx)))

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
for cat, idx in targets:
    it = news[cat][idx]
    url = it.get('link','')
    print("="*80)
    print(f"[{cat}][{idx}] {it['title']}  ({it.get('source')})")
    print(f"link={url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        raw = urllib.request.urlopen(req, timeout=25).read()
        for enc in ('utf-8','gbk','gb18030'):
            try:
                txt = raw.decode(enc); break
            except Exception: continue
        else:
            txt = raw.decode('utf-8', 'ignore')
        m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', txt, re.S|re.I)
        if not m:
            m = re.search(r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']', txt, re.S|re.I)
        if m:
            print("DESC:", htmlmod.unescape(m.group(1)).strip()[:600])
        body = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', txt, flags=re.S)
        body = re.sub(r'<[^>]+>', ' ', body)
        body = htmlmod.unescape(body)
        body = re.sub(r'\s+', ' ', body).strip()
        # 找正文起始位置（跳过导航）
        key = it['title'][:8]
        pos = body.find(key)
        seg = body[pos:pos+1400] if pos > 0 else body[:1400]
        print("BODY:", seg[:1400])
    except Exception as e:
        print("FETCH-FAIL:", repr(e))
