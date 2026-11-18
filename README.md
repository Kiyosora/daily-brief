# 今日简报 · daily-brief

每日 06:00 / 12:00 / 18:00（Asia/Shanghai）自动刷新。

- `index.html` — 当日快照页面（热榜 / 行情 / 天气 / 商业科技 / 投资市场 + LLM 精选点评层）
- `render.py` — 页面渲染器（含 editorial 点评层支持与实时数据层修复补丁）
- `collect.py` — 全量数据抓取脚本
- `config.json` — 数据源与板块配置

页面自带浏览器端实时数据层：热榜、行情、天气、新闻均为打开即最新；
服务端快照提供「带 LLM 精选与点评」的当日精选层。

发布地址：https://kiyosora.github.io/daily-brief/
