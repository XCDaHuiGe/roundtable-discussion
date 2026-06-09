# -*- coding: utf-8 -*-
from __future__ import annotations

from html import escape
from typing import Any, Callable

from engine.html_ppt_v12 import Page


BASE_CSS = """
*{box-sizing:border-box}
html,body{width:100%;height:100%;margin:0;overflow:hidden;background:#101214;color:#f7f3ea;font-family:"Noto Sans SC","Microsoft YaHei",Arial,sans-serif}
body{position:relative}
.slide{height:100vh;width:100vw;overflow:hidden;display:none;align-items:center;justify-content:center;padding:7vh 7vw;position:relative;background:linear-gradient(135deg,#101214 0%,#171a1f 52%,#202018 100%)}
.slide.visible{display:flex}
.slide::before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 18% 20%,rgba(245,199,91,.14),transparent 30%),radial-gradient(circle at 86% 74%,rgba(99,179,237,.12),transparent 32%);pointer-events:none}
.page{position:relative;z-index:1;width:min(1180px,100%);height:min(760px,86vh);display:flex;flex-direction:column;gap:24px;overflow:hidden}
.page-header{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;border-bottom:1px solid rgba(247,243,234,.18);padding-bottom:18px;min-height:74px}
.kicker{font-family:Consolas,"SFMono-Regular",monospace;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#f5c75b}
h1,h2,h3,p{margin:0}
h1{font-size:clamp(46px,7vw,92px);line-height:1.02;max-width:780px}
h2{font-size:clamp(28px,4vw,52px);line-height:1.12}
h3{font-size:20px;line-height:1.28}
p{font-size:clamp(15px,1.5vw,19px);line-height:1.72;color:rgba(247,243,234,.78)}
.hero{display:grid;grid-template-columns:1.08fr .92fr;gap:54px;align-items:center;height:100%}
.hero-copy{display:flex;flex-direction:column;gap:24px}
.hero-panel,.card,.statement{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.13);padding:24px;overflow:hidden}
.hero-panel{display:flex;flex-direction:column;gap:18px}
.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;overflow:hidden}
.grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;overflow:hidden}
.stack{display:flex;flex-direction:column;gap:16px;overflow:hidden}
.card{min-height:0}
.card-name{font-size:22px;font-weight:800;color:#ffffff;margin-bottom:8px}
.card-role{font-family:Consolas,"SFMono-Regular",monospace;font-size:11px;letter-spacing:.12em;color:#f5c75b;margin-bottom:12px;text-transform:uppercase}
.speech-card{display:grid;grid-template-columns:112px 1fr;gap:20px;align-items:start}
.speaker{font-weight:800;font-size:22px;color:#f5c75b}
.clash-card{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.label{font-family:Consolas,"SFMono-Regular",monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#9bd4ff;margin-bottom:10px}
.statement{margin:auto;max-width:860px;text-align:center}
.statement p{font-size:clamp(20px,2.5vw,34px);line-height:1.55;color:#fff}
#progress{position:fixed;left:0;top:0;height:3px;width:0;background:#f5c75b;z-index:50;transition:width .35s ease}
.nav-dots{position:fixed;right:24px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:10px;z-index:60}
.nav-dot{width:10px;height:10px;border-radius:50%;border:1px solid rgba(247,243,234,.55);background:rgba(247,243,234,.18);cursor:pointer;padding:0}
.nav-dot.active{background:#f5c75b;border-color:#f5c75b;transform:scale(1.25)}
.nav-ui{position:fixed;left:24px;bottom:22px;z-index:60;display:flex;align-items:center;gap:12px;color:rgba(247,243,234,.65);font-family:Consolas,"SFMono-Regular",monospace;font-size:12px}
.nav-btn{width:34px;height:34px;border:1px solid rgba(247,243,234,.25);background:rgba(255,255,255,.06);color:#f7f3ea;cursor:pointer}
@media (max-width:800px){.slide{padding:6vh 5vw}.page{height:88vh;gap:16px}.hero,.grid-2,.grid-3,.clash-card{grid-template-columns:1fr}h1{font-size:44px}h2{font-size:30px}.speech-card{grid-template-columns:1fr}.nav-dots{right:12px}.nav-ui{left:12px;bottom:12px}}
"""


NAVIGATION_JS = """
<script>
(function(){
  const sections=[...document.querySelectorAll('.slide')];
  const total=sections.length;
  let cur=0;
  const dotsContainer=document.getElementById('navDots');
  const progress=document.getElementById('progress');
  const counter=document.getElementById('counter');
  sections.forEach((s,i)=>{
    const dot=document.createElement('button');
    dot.className='nav-dot'+(i===0?' active':'');
    dot.setAttribute('aria-label','第 '+(i+1)+' 页');
    dot.onclick=()=>go(i);
    dotsContainer.appendChild(dot);
  });
  function go(n){
    if(n<0||n>=total)return;
    sections[cur].classList.remove('visible');
    dotsContainer.children[cur]?.classList.remove('active');
    cur=n;
    sections[cur].scrollIntoView({behavior:'smooth',block:'start'});
    sections[cur].classList.add('visible');
    dotsContainer.children[cur]?.classList.add('active');
    const pct=Math.min(100,((cur+1)/total)*100);
    progress.style.width=pct+'%';
    if(counter)counter.textContent=(cur+1)+' / '+total;
  }
  document.getElementById('prevBtn').onclick=()=>go(cur-1);
  document.getElementById('nextBtn').onclick=()=>go(cur+1);
  document.addEventListener('keydown',e=>{
    if(e.key==='ArrowDown'||e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){
      e.preventDefault();go(cur+1);
    }else if(e.key==='ArrowUp'||e.key==='ArrowLeft'||e.key==='PageUp'){
      e.preventDefault();go(cur-1);
    }else if(e.key==='Home'){
      e.preventDefault();go(0);
    }else if(e.key==='End'){
      e.preventDefault();go(total-1);
    }
  });
  let wheelTimer=null;
  document.addEventListener('wheel',e=>{
    e.preventDefault();
    if(wheelTimer)return;
    wheelTimer=setTimeout(()=>wheelTimer=null,400);
    if(e.deltaY>0)go(cur+1);
    else if(e.deltaY<0)go(cur-1);
  },{passive:false});
  document.body.addEventListener('click',e=>{
    if(e.target.closest('.nav-dot,.nav-dots,.nav-btn,.expert-card,.speech-card,.clash-card,.card,.statement'))return;
    go(cur+1);
  });
  go(0);
})();
</script>
"""


def render_html(pages: list[Page], title: str = "圆桌洞见") -> str:
    slides = "\n".join(_render_slide(page, index) for index, page in enumerate(pages))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>
{BASE_CSS}
</style>
</head>
<body>
<div id="progress"></div>
<div id="navDots" class="nav-dots"></div>
<div class="nav-ui">
  <button id="prevBtn" class="nav-btn" type="button" aria-label="上一页">&lt;</button>
  <span id="counter">1 / {len(pages)}</span>
  <button id="nextBtn" class="nav-btn" type="button" aria-label="下一页">&gt;</button>
</div>
{slides}
{NAVIGATION_JS}
</body>
</html>
"""


def _render_slide(page: Page, index: int) -> str:
    visible = " visible" if index == 0 else ""
    body = _RENDERERS.get(page.page_type, _render_default)(page)
    return (
        f'<section class="slide{visible}" data-page-type="{escape(page.page_type)}" '
        f'data-layout="{escape(page.layout or "")}">\n{body}\n</section>'
    )


def _page_shell(page: Page, content: str, kicker: str | None = None) -> str:
    label = kicker or page.page_type.replace("_", " ")
    subtitle = f'<p>{escape(page.subtitle)}</p>' if page.subtitle else ""
    return f"""<div class="page">
  <header class="page-header">
    <div>
      <div class="kicker">{escape(label)}</div>
      <h2>{escape(page.title)}</h2>
    </div>
    {subtitle}
  </header>
  {content}
</div>"""


def _render_cover(page: Page) -> str:
    subtitle = escape(page.subtitle or "6 位专家跨越时空的圆桌洞见")
    return f"""<div class="page hero">
  <div class="hero-copy">
    <div class="kicker">ROUNDTABLE INSIGHT V12</div>
    <h1>{escape(page.title)}</h1>
    <p>{subtitle}</p>
  </div>
  <aside class="hero-panel">
    <h3>稳定出片协议</h3>
    <p>结构先行，容量约束，单一导航，最终验收。</p>
  </aside>
</div>"""


def _render_list(page: Page) -> str:
    cards = []
    for idx, item in enumerate(page.items, start=1):
        title = item.get("title") or f"{idx:02d}"
        text = item.get("text", "")
        cards.append(f"""<article class="card">
  <div class="label">{idx:02d}</div>
  <h3>{escape(str(title))}</h3>
  <p>{escape(str(text))}</p>
</article>""")
    return _page_shell(page, f'<div class="stack">{"".join(cards)}</div>')


def _render_experts(page: Page) -> str:
    cards = []
    for item in page.items:
        cards.append(f"""<article class="card expert-card">
  <div class="card-name">{escape(str(item.get("name", "")))}</div>
  <div class="card-role">{escape(str(item.get("title", "")))}</div>
  <p>{escape(str(item.get("belief", "")))}</p>
</article>""")
    return _page_shell(page, f'<div class="grid-3">{"".join(cards)}</div>')


def _render_round_overview(page: Page) -> str:
    return _page_shell(page, f"""<div class="statement">
  <p>{escape(page.body)}</p>
</div>""")


def _render_speech(page: Page) -> str:
    cards = []
    for item in page.items:
        cards.append(f"""<article class="card speech-card">
  <div class="speaker">{escape(str(item.get("expert", "")))}{escape(str(item.get("part", "")))}</div>
  <p>{escape(str(item.get("text", "")))}</p>
</article>""")
    return _page_shell(page, f'<div class="grid-2">{"".join(cards)}</div>')


def _render_clash(page: Page) -> str:
    item = page.items[0] if page.items else {}
    content = f"""<article class="clash-card">
  <div class="card">
    <div class="label">{escape(str(item.get("attack_type", "attack")))}</div>
    <h3>{escape(str(item.get("attacker", "")))}</h3>
    <p>{escape(str(item.get("attack", "")))}</p>
  </div>
  <div class="card">
    <div class="label">response</div>
    <h3>{escape(str(item.get("target", "")))}</h3>
    <p>{escape(str(item.get("defense", "")))}</p>
  </div>
</article>"""
    return _page_shell(page, content, "clash")


def _render_summary(page: Page) -> str:
    body = page.body or "深度不等于页数，深度等于认知增量。"
    return f"""<div class="page">
  <div class="statement">
    <div class="kicker">FINAL STATEMENT</div>
    <h2>{escape(page.title)}</h2>
    <p>{escape(body)}</p>
  </div>
</div>"""


def _render_default(page: Page) -> str:
    if page.items:
        return _render_list(page)
    return _page_shell(page, f'<div class="statement"><p>{escape(page.body)}</p></div>')


_RENDERERS: dict[str, Callable[[Page], str]] = {
    "cover": _render_cover,
    "insight_overview": _render_list,
    "hypothesis_evolution": _render_list,
    "tension_map": _render_list,
    "experts": _render_experts,
    "round_overview": _render_round_overview,
    "speech": _render_speech,
    "clash": _render_clash,
    "cost_analysis": _render_list,
    "human_nature": _render_list,
    "consensus_state": _render_list,
    "open_questions": _render_list,
    "summary": _render_summary,
}
