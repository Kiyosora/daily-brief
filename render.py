#!/usr/bin/env python3
"""渲染今日简报页面。

双层数据架构：
  烘焙层（服务端）—— RSS 新闻 + LLM 点评，部署时写死，保证首屏可读、无 JS 也能看
  实时层（浏览器）—— 热榜 / 行情 / 天气 / 新闻，页面打开时用 CORS 直连拉取，永远最新

外加：
  版本指针 —— localStorage 记录已见过的最新版时间戳，发现更新版自动跳转
  备忘录   —— localStorage 保存，不被每日更新覆盖
"""
from __future__ import annotations

import html
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIST = BASE / "dist"
DATA = json.loads((BASE / "data.json").read_text(encoding="utf-8"))
CONFIG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
try:
    EDITORIAL = json.loads((BASE / "editorial.json").read_text(encoding="utf-8"))
except Exception:
    EDITORIAL = {}

# editorial 全部以「标题」作为标识：标题即内容本身，跨轮次稳定，不会因 RSS 排序变化而错位
COMMENTS = EDITORIAL.get("comments", {})   # 标题 -> 点评
ORDER = EDITORIAL.get("order", {})          # 分类 -> [标题, ...]
HIDE = set(EDITORIAL.get("hide", []))       # [标题, ...]


def e(t) -> str:
    return html.escape(str(t if t is not None else ""))


def render_market(rows):
    chips = []
    for m in rows:
        pct = m.get("pct") or 0
        cls = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "—")
        chips.append(
            f'<div class="quote {cls}"><span class="q-name">{e(m["name"])}</span>'
            f'<span class="q-val">{m["value"]:,.2f}</span>'
            f'<span class="q-pct">{arrow} {abs(pct):.2f}%</span></div>')
    return f'<div class="quotes">{"".join(chips)}</div>' if chips else ""


def render_hot(key, name, rows):
    if not rows:
        return (f'<section class="card" data-hot="{key}"><header class="card-head">'
                f'<h2>{e(name)}</h2><span class="tag tag-dim">暂无数据</span></header>'
                f'<p class="empty">本轮抓取未取到内容。</p></section>')
    lis = []
    for r in rows:
        badge = r.get("change", "—")
        bcls = "tag-new" if badge in ("新", "NEW") else ""
        lis.append(
            f'<li><span class="rank">{r["rank"]}</span>'
            f'<a class="hl" href="{e(r["link"])}" target="_blank" rel="noopener">{e(r["title"])}</a>'
            f'<span class="heat">{e(r.get("heat_text",""))}</span>'
            f'<span class="tag {bcls}">{e(badge)}</span></li>')
    return (f'<section class="card" data-hot="{key}"><header class="card-head"><h2>{e(name)}</h2>'
            f'<span class="tag tag-dim">TOP {len(rows)}</span></header>'
            f'<ol class="hot-list">{"".join(lis)}</ol></section>')


def render_news(key, name, rows, extra_html=""):
    rows = [r for r in rows if r.get("title") not in HIDE]
    order = ORDER.get(key)
    if order:
        pos = {v: i for i, v in enumerate(order)}
        rows = sorted(rows, key=lambda r: pos.get(r.get("title", ""), 999))
    if not rows:
        return (f'<section class="card card-wide" data-news="{key}"><header class="card-head">'
                f'<h2>{e(name)}</h2><span class="tag tag-dim">暂无数据</span></header>'
                f'<p class="empty">本轮抓取未取到内容。</p></section>')
    blocks = []
    for r in rows:
        c = COMMENTS.get(r.get("title", "")) or COMMENTS.get(r.get("id", ""))
        ch = f'<p class="comment">{e(c)}</p>' if c else ""
        meta = f'<span class="meta-src">{e(r.get("source",""))}</span>'
        if r.get("published"):
            meta += f'<span class="meta-time">{e(r["published"])}</span>'
        blocks.append(f'<article class="news-item"><a class="n-title" href="{e(r.get("link",""))}" '
                      f'target="_blank" rel="noopener">{e(r.get("title",""))}</a>{ch}'
                      f'<div class="meta">{meta}</div></article>')
    return (f'<section class="card card-wide" data-news="{key}"><header class="card-head">'
            f'<h2>{e(name)}</h2><span class="tag tag-dim">{len(rows)} 条</span></header>'
            f'{extra_html}<div class="news-list">{"".join(blocks)}</div></section>')


def render_hourly(w):
    hourly = w.get("hourly") or []
    if len(hourly) < 4:
        return ""
    pts = [(h.get("time", ""), h.get("temp", 0), h.get("code", 0)) for h in hourly]
    temps = [p[1] for p in pts]
    lo, hi = min(temps), max(temps)
    span = max(hi - lo, 1)
    W, H = 320, 54
    step = W / max(len(pts) - 1, 1)
    coords = [(i * step, H - ((t - lo) / span) * (H - 12) - 6) for i, t in enumerate(temps)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = f"0,{H} " + poly + f" {W},{H}"
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{"#ff7a45" if c in (0,1,2) else "#7dd3fc"}" />'
        for (x, y), (_, _, c) in zip(coords, pts))
    return (f'<div class="chart"><svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" width="100%" height="54">'
            f'<polygon points="{area}" fill="url(#g1)"/><polyline points="{poly}" fill="none" stroke="#ff7a45" '
            f'stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>{dots}'
            f'<defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="#ff7a45" stop-opacity=".35"/>'
            f'<stop offset="100%" stop-color="#ff7a45" stop-opacity="0"/></linearGradient></defs>'
            f'</svg><div class="chart-axis"><span>{e((pts[0][0] or "")[-5:])}</span>'
            f'<span>{e((pts[-1][0] or "")[-5:])}</span></div></div>')


CSS = """
:root{--bg:#0c0e12;--card:#14171d;--card-2:#191d24;--line:rgba(255,255,255,.075);
--txt:#e9edf2;--dim:#8b95a5;--accent:#ff7a45;--up:#4ade80;--down:#f87171;--blue:#7dd3fc}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.6;padding:28px 20px 64px}
.wrap{max-width:1180px;margin:0 auto}
header.top{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px;margin-bottom:22px}
h1{font-size:27px;font-weight:700;letter-spacing:.3px}
h1 .accent{color:var(--accent)}
.sub{color:var(--dim);font-size:13px;margin-top:5px}
.pulse{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);margin-right:7px;animation:p 2s infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.25}}
.live{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--up);border:1px solid rgba(74,222,128,.3);border-radius:20px;padding:2px 9px;margin-left:8px}
.live .dot{width:5px;height:5px;border-radius:50%;background:var(--up)}
.live.off{color:var(--dim);border-color:var(--line)}
.live.off .dot{background:var(--dim)}
.hero{background:linear-gradient(135deg,#1b1f28,#15181f);border:1px solid var(--line);border-radius:18px;padding:26px 28px;margin-bottom:20px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-70px;top:-70px;width:230px;height:230px;border-radius:50%;background:radial-gradient(circle,rgba(255,122,69,.16),transparent 70%)}
.hero-main{display:flex;gap:38px;flex-wrap:wrap;position:relative;z-index:1}
.hero-left{min-width:210px}
.hero-right{flex:1;min-width:280px}
.city{font-size:16px;font-weight:600;letter-spacing:.5px}
.wx-desc{color:var(--dim);font-weight:400;font-size:13px;margin-left:6px}
.temp{font-size:62px;font-weight:200;line-height:1.05;margin:4px 0 6px;letter-spacing:-2px}
.deg{font-size:24px;color:var(--dim);margin-left:3px;vertical-align:super}
.hero-meta{color:var(--dim);font-size:13px}
.outfit-label{font-size:11px;letter-spacing:2px;color:var(--accent);text-transform:uppercase;margin-bottom:7px}
.outfit{font-size:15px;line-height:1.75;color:#d8dee8}
.chart{margin-top:14px}
.chart-axis{display:flex;justify-content:space-between;color:var(--dim);font-size:11px;margin-top:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}
.wide-stack{display:flex;flex-direction:column;gap:18px;margin-top:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px}
.card-wide{grid-column:1/-1}
.card-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;padding-bottom:11px;border-bottom:1px solid var(--line)}
.card-head h2{font-size:15px;font-weight:600;letter-spacing:.4px}
.tag{font-size:11px;color:var(--dim);border:1px solid var(--line);border-radius:20px;padding:2px 9px}
.tag-new{color:#0c0e12;background:var(--accent);border-color:var(--accent);font-weight:600}
.tag-dim{color:var(--dim)}
.empty{color:var(--dim);font-size:13px;padding:10px 0}
ol.hot-list{list-style:none}
ol.hot-list li{display:flex;align-items:center;gap:9px;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.035)}
ol.hot-list li:last-child{border-bottom:none}
.rank{min-width:20px;height:20px;border-radius:6px;background:var(--card-2);color:var(--dim);font-size:11px;display:flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}
ol.hot-list li:nth-child(-n+3) .rank{background:rgba(255,122,69,.16);color:var(--accent);font-weight:600}
.hl{flex:1;color:var(--txt);text-decoration:none;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hl:hover{color:var(--accent)}
.heat{font-size:11px;color:var(--dim);font-variant-numeric:tabular-nums;white-space:nowrap}
.news-item{padding:11px 0;border-bottom:1px solid rgba(255,255,255,.045)}
.news-item:last-child{border-bottom:none}
.n-title{color:var(--txt);text-decoration:none;font-size:14.5px;font-weight:500;display:block}
.n-title:hover{color:var(--accent)}
.comment{color:#a8b3c4;font-size:13px;margin-top:5px;padding-left:11px;border-left:2px solid rgba(255,122,69,.4)}
.meta{margin-top:6px;display:flex;gap:12px;font-size:11.5px;color:var(--dim)}
.meta-src{color:#6f7b8c}
.quotes{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:9px;margin-bottom:16px}
.quote{background:var(--card-2);border-radius:11px;padding:9px 11px;display:flex;flex-direction:column;gap:1px}
.q-name{font-size:11.5px;color:var(--dim)}
.q-val{font-size:16px;font-weight:600;font-variant-numeric:tabular-nums}
.q-pct{font-size:11.5px;font-variant-numeric:tabular-nums}
.up .q-pct{color:var(--up)}.down .q-pct{color:var(--down)}.flat .q-pct{color:var(--dim)}
.memo textarea{width:100%;min-height:170px;background:var(--card-2);color:var(--txt);border:1px solid var(--line);border-radius:12px;padding:13px 15px;font-family:inherit;font-size:14px;line-height:1.75;resize:vertical;flex:1}
.memo{display:flex;flex-direction:column}
.memo textarea:focus{outline:none;border-color:rgba(255,122,69,.5)}
.memo-bar{display:flex;justify-content:space-between;align-items:center;margin-top:9px;gap:10px;flex-wrap:wrap}
.memo-status{color:var(--dim);font-size:11.5px}
.btn{background:var(--card-2);color:var(--dim);border:1px solid var(--line);border-radius:9px;padding:5px 12px;font-size:12px;cursor:pointer;font-family:inherit;transition:.15s}
.btn:hover{color:var(--accent);border-color:rgba(255,122,69,.4)}
.btn.on{color:#0c0e12;background:var(--accent);border-color:var(--accent);font-weight:600}
.toolbar{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:16px;align-items:center}
.keyinput{flex:1;min-width:240px;background:var(--card-2);color:var(--txt);border:1px solid var(--line);border-radius:9px;padding:6px 12px;font-size:12px;font-family:inherit}
.keyinput:focus{outline:none;border-color:rgba(255,122,69,.5)}
footer{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);color:#5d6878;font-size:12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
@media (max-width:620px){body{padding:18px 13px 40px}.temp{font-size:50px}.hero{padding:20px}.hero-main{gap:18px}.card{padding:17px 16px}.hl{white-space:normal}}
"""

LIVE_JS = r"""
(function(){
"use strict";
var CFG = __CFG__;
var BAKED = __BAKED__;
/* __PATCHED_V2__ */
/* 标题归一化：压缩全角/半角空白差异，保证精选匹配与点评查找一致 */
function normT(s){return String(s==null?'':s).replace(/[\s\u3000]+/g,' ').trim();}
var HIDES=(BAKED.hide||[]).map(normT);
var CMAP={};
Object.keys(BAKED.comments||{}).forEach(function(k){var n=normT(k);if(n&&!CMAP[n])CMAP[n]=BAKED.comments[k];});

function $(s,r){return (r||document).querySelector(s);}
function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));}
function esc(s){var d=document.createElement('div');d.textContent=(s==null?'':s);return d.innerHTML;}

/* ---------- 实时层状态 ---------- */
var liveCount=0, liveFlag=null, liveText=null;
function markLive(){
  liveCount++;
  if(!liveFlag){liveFlag=$('#live-flag');liveText=$('#live-text');}
  if(liveFlag){liveFlag.classList.remove('off');}
  if(liveText){liveText.textContent='实时数据已连接';}
}

/* ---------- 版本指针：发现更新的烘焙版则自动跳转 ---------- */
var PKEY='db.pointer.v1';
try{
  var saved=JSON.parse(localStorage.getItem(PKEY)||'null');
  if(saved && saved.ts && BAKED.ts && saved.ts>BAKED.ts && saved.url && saved.url!==location.href){
    location.replace(saved.url); return;
  }
  localStorage.setItem(PKEY,JSON.stringify({ts:BAKED.ts||0,url:location.href}));
}catch(e){}

/* ---------- 实时层：热榜 ---------- */
function fmtHeat(n){ if(n>=1e8) return (n/1e8).toFixed(1)+'亿'; if(n>=1e4) return (n/1e4).toFixed(1)+'万'; return ''+n; }
function parseMd(text){
  var out=[],re=/^\|\s*(\d+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([\d,\.]+)\s*\|\s*([^|]*?)\s*\|\s*$/;
  text.split('\n').forEach(function(l){
    var m=l.trim().match(re); if(!m) return;
    var n=parseInt(String(m[4]).replace(/,/g,''),10)||0;
    out.push({rank:+m[1],title:m[2],link:m[3],heat:n,heatText:fmtHeat(n),change:m[5]||'—'});
  });
  return out;
}
function paintHot(key,items){
  var sec=$('[data-hot="'+key+'"]'); if(!sec||!items.length) return;
  var lis=items.map(function(r){
    var b=r.change, cls=(b==='新'||b==='NEW')?'tag-new':'';
    return '<li><span class="rank">'+r.rank+'</span><a class="hl" href="'+esc(r.link)+'" target="_blank" rel="noopener">'+esc(r.title)+'</a>'+
           '<span class="heat">'+esc(r.heatText)+'</span><span class="tag '+cls+'">'+esc(b)+'</span></li>';
  }).join('');
  var list=$('.hot-list',sec); if(!list){return;}
  list.innerHTML=lis;
  var tg=$('.card-head .tag',sec); if(tg) tg.textContent='TOP '+items.length+' · 实时';
}
CFG.hot.forEach(function(src){
  fetch(src.url,{cache:'no-store'}).then(function(r){return r.text();}).then(function(t){
    paintHot(src.key,parseMd(t).slice(0,12)); markLive();
  }).catch(function(){});
});

/* ---------- 实时层：行情 ---------- */
function paintMarket(rows){
  var box=$('[data-news="invest"] .quotes'); if(!box||!rows.length) return;
  box.innerHTML=rows.map(function(m){
    var pct=m.pct||0, cls=pct>0?'up':(pct<0?'down':'flat'), ar=pct>0?'▲':(pct<0?'▼':'—');
    return '<div class="quote '+cls+'"><span class="q-name">'+esc(m.name)+'</span><span class="q-val">'+Number(m.value).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2})+'</span>'+
           '<span class="q-pct">'+ar+' '+Math.abs(pct).toFixed(2)+'%</span></div>';
  }).join('');
}
fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f2,f3,f4,f12,f14&secids='+CFG.market.join(',')+'&fltt=2&invt=2',{cache:'no-store'})
 .then(function(r){return r.json();}).then(function(d){
  var rows=((d.data&&d.data.diff)||[]).filter(function(r){return typeof r.f2==='number';})
    .map(function(r){return {name:r.f14,value:r.f2,pct:r.f3};});
  paintMarket(rows); markLive();
 }).catch(function(){});

/* ---------- 实时层：天气 + 规则穿搭 ---------- */
var WMO={0:'晴',1:'晴间多云',2:'多云',3:'阴',45:'有雾',48:'雾凇',51:'小毛毛雨',53:'毛毛雨',55:'大毛毛雨',61:'小雨',63:'中雨',65:'大雨',71:'小雪',73:'中雪',75:'大雪',80:'阵雨',81:'强阵雨',82:'暴雨',95:'雷阵雨',96:'雷阵雨伴冰雹'};
function outfit(t,hi,lo,desc,prec,hum){
  var b=[];
  if(lo<=5) b.push('羽绒服/厚外套 + 保暖内搭，注意手脚保暖');
  else if(lo<=12) b.push('风衣/夹克或针织衫 + 长裤，早晚加一件开衫');
  else if(lo<=20) b.push('薄外套/卫衣 + 长裤，早晚温差大注意叠穿');
  else if(lo<=26) b.push('短袖/薄长袖即可，备一件薄外套应对空调');
  else b.push('轻薄透气夏装，注意防晒补水');
  if(prec) b.push('降水概率 '+prec+'%，记得带伞');
  if((hi-lo)>=8) b.push('昼夜温差较大，别只按中午温度穿');
  if(hum>=75) b.push('湿度 '+hum+'% 偏闷，别穿太厚');
  return desc+'，'+Math.round(lo)+'~'+Math.round(hi)+'°C；建议'+b.join('；')+'。';
}
function paintWeather(w){
  var t=$('.temp'),d=$('.wx-desc'),m=$('.hero-meta'),o=$('.outfit');
  if(!t) return;
  t.innerHTML=Math.round(w.temp)+'<span class="deg">°C</span>';
  if(d) d.textContent=w.day_desc||'';
  if(m) m.textContent='体感 '+Math.round(w.feels_like)+'° · 湿度 '+w.humidity+'% · '+Math.round(w.low)+'~'+Math.round(w.high)+'°'+(w.precip!=null?' · 降水概率 '+w.precip+'%':'');
  // 穿搭建议：editorial 已写好就不覆盖，保留 LLM 版本；没有才用规则版兜底
  if(o && !o.getAttribute('data-editorial')) o.textContent=outfit(w.temp,w.high,w.low,w.day_desc,w.precip,w.humidity);
}
fetch('https://api.open-meteo.com/v1/forecast?latitude='+CFG.lat+'&longitude='+CFG.lon+'&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max&timezone='+encodeURIComponent(CFG.tz)+'&forecast_days=1',{cache:'no-store'})
 .then(function(r){return r.json();}).then(function(d){
  var cur=d.current||{},dy=d.daily||{};
  paintWeather({temp:cur.temperature_2m,feels_like:cur.apparent_temperature,humidity:cur.relative_humidity_2m,
    low:(dy.temperature_2m_min||[])[0],high:(dy.temperature_2m_max||[])[0],
    day_desc:WMO[(dy.weather_code||[])[0]]||'',precip:(dy.precipitation_probability_max||[])[0]});
  markLive();
 }).catch(function(){});

/* ---------- 实时层：新闻 RSS（经 rss2json） ---------- */
var ADWORDS=/(报名|招商|加盟|优惠|促销|抽奖|广告|推广|软文|限时|福利|领取|优惠券|开户|返佣|代理加盟|直播预告|榜单揭晓|神历|白皮书下载|大会|峰会|论坛|开幕|年会|发布会|隆重|圆满|收官|实录)/;
function paintNews(key,items,site){
  var sec=$('[data-news="'+key+'"]'); if(!sec||!items.length) return;
  var box=$('.news-list',sec); if(!box) return;
  var clean=items.filter(function(it){
    if(ADWORDS.test(it.title||'')) return false;
    if(HIDES.indexOf(normT(it.title))>=0) return false;
    return true;
  });
  // editorial 精选为主干：保持顺序与点评；即使已掉出 feed 前 N 条也保留（用烘焙链接兜底）
  var curated=(BAKED.curated||{})[key]||[];
  if(curated.length){
    var byTitle={};
    clean.forEach(function(it){ var n=normT(it.title); if(!byTitle[n]) byTitle[n]=it; });
    var ordered=[],used={};
    curated.forEach(function(c){
      var n=normT(c.t);
      if(HIDES.indexOf(n)>=0) return;
      var it=byTitle[n];
      if(it){ ordered.push(it); used[normT(it.title)]=1; }
      else { ordered.push({title:c.t,link:c.l,site:c.s,published:c.p}); }
    });
    clean.forEach(function(it){ if(!used[normT(it.title)]) ordered.push(it); });
    clean=ordered;
  }
  box.innerHTML=clean.slice(0,16).map(function(it){
    var c=CMAP[normT(it.title)];
    var ch=c?'<p class="comment">'+esc(c)+'</p>':'';
    return '<article class="news-item"><a class="n-title" href="'+esc(it.link)+'" target="_blank" rel="noopener">'+esc(it.title)+'</a>'+ch+
      '<div class="meta"><span class="meta-src">'+esc(it.site||site)+'</span><span class="meta-time">'+esc(it.published)+'</span></div></article>';
  }).join('');
  var tg=$('.card-head .tag',sec); if(tg) tg.textContent='精选 '+Math.min(clean.length,16)+' 条 · 实时';
}
var rssGroups={};
CFG.rss.forEach(function(src){ (rssGroups[src.key]=rssGroups[src.key]||[]).push(src); });
Object.keys(rssGroups).forEach(function(key){
  var srcs=rssGroups[key];
  Promise.all(srcs.map(function(src){
    var api='https://api.rss2json.com/v1/api.json?count=12&rss_url='+encodeURIComponent(src.url);
    return fetch(api,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
      return (d.items||[]).map(function(it){
        var p=it.pubDate?new Date(it.pubDate):null;
        return {title:it.title,link:it.link,site:src.site,
          published:(p&&!isNaN(p))?(p.getMonth()+1)+'-'+String(p.getDate()).padStart(2,'0')+' '+String(p.getHours()).padStart(2,'0')+':'+String(p.getMinutes()).padStart(2,'0'):''};
      });
    }).catch(function(){return [];});
  })).then(function(lists){
    var merged=[],idx=0;
    while(true){ var added=false;
      for(var i=0;i<lists.length;i++){ if(idx<lists[i].length){merged.push(lists[i][idx]);added=true;} }
      if(!added) break; idx++;
    }
    if(merged.length){ paintNews(key,merged,srcs.map(function(x){return x.site;}).join(' / ')); markLive(); }
  });
});

/* ---------- 可选：LLM 点评（用户自带 MiniMax Key，存本地） ---------- */
var LKEY='db.llmkey.v1',LCACHE='db.llm.v1';
function llmPanel(){
  var bar=$('.toolbar');
  if(!bar) return;
  var key=''; try{key=localStorage.getItem(LKEY)||'';}catch(e){}
  bar.innerHTML='<input class="keyinput" id="llm-key" type="password" placeholder="可选：填入你的 MiniMax API Key，启用 AI 点评（仅存本机浏览器）">'+
    '<button class="btn" id="llm-save">保存 Key</button><button class="btn" id="llm-run">生成 AI 点评</button>'+
    '<span class="memo-status" id="llm-status"></span>';
  $('#llm-key').value=key;
  $('#llm-save').onclick=function(){
    var v=$('#llm-key').value.trim();
    try{localStorage.setItem(LKEY,v);}catch(e){}
    $('#llm-status').textContent=v?'已保存到本机':'已清空';
    $('#llm-save').classList.toggle('on',!!v);
  };
  $('#llm-run').onclick=runLLM;
  if(key){$('#llm-save').classList.add('on');$('#llm-status').textContent='已启用';}
}
async function runLLM(){
  var st=$('#llm-status'); if(!st) return;
  var key=''; try{key=localStorage.getItem(LKEY)||'';}catch(e){}
  if(!key){st.textContent='请先填入并保存 API Key';return;}
  st.textContent='生成中…';
  var nodes=$$('[data-news] .news-item');
  if(!nodes.length){ st.textContent='当前没有可点评的条目'; return; }
  var titles=nodes.map(function(n,i){return '- ['+i+'] '+(n.querySelector('.n-title')||{}).textContent;}).join('\n');
  var prompt='以下是今日商业与投资资讯标题列表：\n'+titles+'\n\n请为每条输出一行 JSON，格式为 {"id":"序号数字","c":"不超过30字的中文点评，必须基于标题真实信息，不复述标题，不编造数字"}。只输出 JSON 数组，不要任何其他文字。';
  try{
    var body=JSON.stringify({model:'MiniMax-M3.1-Flash',max_tokens:2000,messages:[{role:'user',content:prompt}]});
    var ends=['https://api.minimaxi.com/anthropic/v1/messages','https://api.minimax.io/anthropic/v1/messages'];
    var j=null,lastErr=null;
    for(var i=0;i<ends.length;i++){
      try{
        var r=await fetch(ends[i],{method:'POST',headers:{'content-type':'application/json','x-api-key':key,'anthropic-version':'2023-06-01'},body:body});
        j=await r.json();
        if(j && j.content) break;
        lastErr=new Error((j.error&&j.error.message)||('HTTP '+r.status));
      }catch(err){lastErr=err;}
    }
    if(!j||!j.content) throw (lastErr||new Error('接口无返回'));
    var txt=(j.content&&j.content[0]&&j.content[0].text)||'';
    var m=txt.match(/\[[\s\S]*\]/);
    var arr=JSON.parse(m?m[0]:txt);
    var map={};arr.forEach(function(o){if(o&&o.id!=null)map[String(o.id)]=o.c;});
    try{localStorage.setItem(LCACHE,JSON.stringify({ts:BAKED.ts||'',map:map}));}catch(e){}
    applyComments(map); st.textContent='已生成 '+arr.length+' 条点评';
  }catch(err){ st.textContent='失败：'+err.message; }
}
function applyComments(map){
  $$('[data-news] .news-item').forEach(function(el,i){
    var c=map[String(i)]; if(!c) return;
    if(el.querySelector('.comment')) return;
    var p=document.createElement('p'); p.className='comment'; p.textContent=c;
    var m=el.querySelector('.meta'); if(m){el.insertBefore(p,m);} else {el.appendChild(p);}
  });
}
try{
  var cached=JSON.parse(localStorage.getItem(LCACHE)||'null');
  if(cached&&cached.map) applyComments(cached.map);
}catch(e){}

/* ---------- 备忘录 ---------- */
(function(){
  var key='db.memo.v1',el=$('#memo'),st=$('#memo-status'),t=null;
  function load(){try{var v=localStorage.getItem(key);if(v){el.value=v;st.textContent='已保存 · '+new Date(v._ts||Date.now()).toLocaleString('zh-CN');}}catch(e){st.textContent='本地存储不可用';}}
  function save(){try{var v=el.value;v._ts=Date.now();localStorage.setItem(key,v);st.textContent='已自动保存 · '+new Date().toLocaleTimeString('zh-CN');}catch(e){st.textContent='保存失败';}}
  el.addEventListener('input',function(){clearTimeout(t);t=setTimeout(save,600);});
  $('#memo-copy').addEventListener('click',function(){el.select();try{navigator.clipboard.writeText(el.value);st.textContent='已复制';}catch(e){document.execCommand('copy');st.textContent='已复制';}});
  load();
})();

llmPanel();
})();
"""


def build() -> str:
    w = DATA.get("weather") or {}
    outfit = EDITORIAL.get("outfit") or DATA.get("outfit_fallback", "")
    hot = DATA.get("hot") or {}
    hot_meta = DATA.get("hot_meta") or {}
    news = DATA.get("news") or {}

    weather_html = ""
    if w and w.get("temp") is not None:
        weather_html = f"""
<section class="hero"><div class="hero-main">
  <div class="hero-left">
    <div class="city">{e(w.get('city',''))} <span class="wx-desc">{e(w.get('day_desc',''))}</span></div>
    <div class="temp">{w['temp']:.0f}<span class="deg">°C</span></div>
    <div class="hero-meta">体感 {w.get('feels_like',0):.0f}° · 湿度 {w.get('humidity',0)}% ·
      {w.get('low',0):.0f}~{w.get('high',0):.0f}°{(' · 降水概率 '+str(w['precip'])+'%') if w.get('precip') is not None else ''}</div>
  </div>
  <div class="hero-right">
    <div class="outfit-label">今日穿着建议</div>
    <p class="outfit" data-editorial="1">{e(outfit)}</p>
    {render_hourly(w)}
  </div>
</div></section>"""

    hot_cards = [render_hot(k, hot_meta.get(k, k), hot[k]) for k in
                 ("weibo", "xiaohongshu", "douyin", "zhihu", "bilibili") if k in hot]
    market_html = render_market(DATA.get("market") or [])
    business = render_news("business", "商业与科技", news.get("business", []))
    invest = render_news("invest", "投资与市场", news.get("invest", []), market_html)
    memo = """<section class="card memo"><header class="card-head"><h2>备忘录</h2><span class="tag tag-dim">仅本机保存</span></header>
      <textarea id="memo" placeholder="随手记点什么…（存在本机浏览器，不会被每日更新覆盖）"></textarea>
      <div class="memo-bar"><span class="memo-status" id="memo-status"></span><button class="btn" id="memo-copy">复制全部</button></div></section>"""

    # 烘焙给 JS 的数据
    baked_news = []
    for key in ("business", "invest"):
        for r in news.get(key, []):
            if r.get("title") in HIDE:
                continue
            baked_news.append({"id": r.get("id"), "title": r.get("title"), "key": key})
    title_comments = {t: c for t, c in COMMENTS.items() if c}
    # 精选清单：按 order 排序、去掉 hide，实时层据此保持精选置顶
    curated = {}
    for key in ("business", "invest"):
        rows = [r for r in news.get(key, []) if r.get("title") not in HIDE]
        o = ORDER.get(key)
        if o:
            pos = {v: i for i, v in enumerate(o)}
            rows = sorted(rows, key=lambda r: pos.get(r.get("title", ""), 999))
        curated[key] = [{"t": r.get("title", ""), "l": r.get("link", ""),
                         "s": r.get("source", ""), "p": r.get("published", "")}
                        for r in rows if r.get("title")]
    baked = {"ts": DATA.get("generated_at", ""), "news": baked_news,
             "comments": title_comments, "curated": curated,
             "hide": sorted(HIDE)}
    cfg = {
        "lat": CONFIG["city_lat"], "lon": CONFIG["city_lon"], "tz": CONFIG["timezone"],
        "market": CONFIG["market_symbols"],
        "hot": [{"key": s["key"], "url": s["url"]} for s in CONFIG["hot_sources"]],
        "rss": [{"key": s["key"], "url": s["url"], "site": s["site"]} for s in CONFIG["rss_sources"]],
    }

    js = (LIVE_JS
          .replace("__CFG__", json.dumps(cfg, ensure_ascii=False))
          .replace("__BAKED__", json.dumps(baked, ensure_ascii=False)))

    # 给烘焙新闻加 data-id，供 AI 点评注入
    business = business.replace('<article class="news-item">', '<article class="news-item">')
    for key, html in (("business", business), ("invest", invest)):
        for r in news.get(key, []):
            rid = r.get("id")
            if rid:
                html = html.replace(
                    f'<article class="news-item"><a class="n-title" href="{e(r.get("link",""))}"',
                    f'<article class="news-item" data-id="{rid}" data-t="{e(r.get("title",""))}"><a class="n-title" href="{e(r.get("link",""))}"')
        if key == "business":
            business = html
        else:
            invest = html

    ts = DATA.get("generated_at", "")
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(DATA.get('site_title','今日简报'))} · {e(DATA.get('date_label',''))}</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<header class="top">
  <div><h1><span class="accent">●</span> {e(DATA.get('site_title','今日简报'))}</h1>
    <div class="sub">{e(DATA.get('date_label',''))} · 更新于 {e(DATA.get('time_label',''))}</div></div>
  <div class="sub"><span class="pulse"></span>每日 06:00 / 12:00 / 18:00 自动刷新
    <span class="live off" id="live-flag"><span class="dot"></span><span id="live-text">连接中</span></span></div>
</header>
{weather_html}
<div class="toolbar"></div>
<div class="grid">{hot_cards[0] if len(hot_cards)>0 else ''}{hot_cards[1] if len(hot_cards)>1 else ''}
  {hot_cards[2] if len(hot_cards)>2 else ''}{hot_cards[3] if len(hot_cards)>3 else ''}
  {hot_cards[4] if len(hot_cards)>4 else ''}{memo}</div>
<div class="wide-stack">{business}{invest}</div>
<footer><span>数据源：微博热搜 · 小红书热帖 · 抖音 · 知乎 · B站 · 钛媒体 · 量子位 · 爱范儿 · 华尔街见闻 · 东方财富行情 · Open-Meteo</span>
  <span>烘焙于 {e(ts[:19].replace('T',' '))}</span></footer>
</div>
<script>
{js}
</script>
</body></html>"""


def main() -> None:
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(build(), encoding="utf-8")
    for name in ("collect.py", "render.py", "config.json"):
        src = BASE / name
        if src.exists():
            (DIST / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[ok] dist/index.html written ({(DIST/'index.html').stat().st_size/1024:.1f} KB) + pipeline files")


if __name__ == "__main__":
    main()
