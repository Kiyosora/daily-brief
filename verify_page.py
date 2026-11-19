import json, pathlib, re
from playwright.sync_api import sync_playwright

url = pathlib.Path('dist/index.html').resolve().as_uri()
errs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1280, 'height': 1200})
    pg.on('console', lambda m: errs.append(f'console.{m.type}: {m.text}') if m.type in ('error','warning') else None)
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
    # 注意：不能用 wait_until='networkidle'——页面实时层的外部请求
    # （行情接口等）在受限出口里会一直挂着，networkidle 必然 30s 超时。
    pg.goto(url, wait_until='domcontentloaded')
    pg.wait_for_timeout(12000)

    # 静态层（无 JS 时的首屏内容）
    baked_comments = pg.eval_on_selector_all('.news-item .comment', 'els => els.map(e => e.textContent.trim())')
    items = pg.eval_on_selector_all('.news-item', 'els => els.map(e => e.getAttribute("data-t") || e.querySelector(".n-title")?.textContent.trim())')
    quotes = pg.eval_on_selector_all('.quote .q-name', 'els => els.map(e => e.textContent.trim())')
    outfit = pg.eval_on_selector('.outfit', 'e => e.textContent.trim()')
    outfit_editorial = pg.eval_on_selector('.outfit', 'e => e.getAttribute("data-editorial")')

    pg.screenshot(path='shot_top.png', clip={'x':0,'y':0,'width':1280,'height':1200})
    pg.screenshot(path='shot_full.png', full_page=True)
    b.close()

editorial = json.loads(pathlib.Path('editorial.json').read_text(encoding='utf-8'))
hidden = set(editorial['hide'])
selected = editorial['order']['business'] + editorial['order']['invest']

print('=== 静态/实时层点评条数 ===', len(baked_comments))
print('=== 行情 chip ===', quotes)
print('=== outfit 是否 editorial 版 ===', outfit_editorial, '|', outfit[:40], '...')
print('=== 隐藏项泄漏检查 ===')
leaked = [t for t in hidden if any(t[:18] in (i or '') for i in items)]
print('  泄漏条目:', leaked if leaked else '无 ✅')
print('=== 选中项是否都在页面 ===')
missing = [t for t in selected if not any(t[:18] in (i or '') for i in items)]
print('  缺失:', missing if missing else '全部在页 ✅')
print('=== JS 报错 ===')
print('  ', '\n   '.join(errs) if errs else '零报错 ✅')
