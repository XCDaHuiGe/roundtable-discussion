# -*- coding: utf-8 -*-
from __future__ import annotations

from html import escape
from typing import Callable

from engine.html_ppt_v13 import ReadingBlock, ReadingPage


READING_CSS = """
*{box-sizing:border-box}
html,body{width:100%;height:100%;margin:0;overflow:hidden;background:#f4efe4;color:#1d1d1b;font-family:"Noto Sans SC","Microsoft YaHei",Arial,sans-serif}
.slide{height:100vh;width:100vw;overflow:hidden;display:none;align-items:center;justify-content:center;padding:54px 72px;background:#f4efe4}
.slide.visible{display:flex}
.reading-page{width:100%;height:100%;max-width:1280px;max-height:760px;display:grid;grid-template-rows:auto 1fr auto;gap:20px;overflow:hidden}
.reading-header{display:grid;grid-template-columns:1fr minmax(260px,420px);gap:32px;align-items:end;border-bottom:2px solid #1d1d1b;padding-bottom:16px}
.reading-kicker{font-size:13px;letter-spacing:.16em;color:#9f2f25;font-weight:800}
.reading-title{font-size:42px;line-height:1.12;margin:5px 0 0;font-weight:900;letter-spacing:0}
.reading-thesis{font-size:18px;line-height:1.55;margin:0;color:#49443d}
.reading-body{min-height:0;overflow:hidden}
.reading-block{border-top:1px solid rgba(29,29,27,.2);padding:13px 0 0;min-height:0}
.reading-block-title{font-size:18px;font-weight:850;margin-bottom:7px;line-height:1.25}
.reading-block-label{display:inline-block;font-size:12px;font-weight:800;letter-spacing:.08em;color:#9f2f25;margin-bottom:7px}
.reading-block-text{font-size:15px;line-height:1.55;color:#35312c;margin:0}
.takeaway-strip{border:2px solid #1d1d1b;background:#fffaf0;padding:14px 18px;display:grid;grid-template-columns:110px 1fr;gap:18px;align-items:center;overflow:hidden}
.takeaway-strip strong{font-size:16px;color:#9f2f25}
.takeaway-strip p{font-size:17px;line-height:1.45;margin:0;font-weight:700}
.brief-grid{display:grid;grid-template-columns:1.05fr 1fr;grid-template-rows:1fr 1fr;gap:20px;height:100%}
.brief-zone{background:#fffaf0;border:1px solid rgba(29,29,27,.24);padding:18px;overflow:hidden}
.brief-zone h3{font-size:18px;margin:0 0 12px}
.brief-zone .reading-block{border-top:0;padding-top:0;margin-bottom:12px}
.stance-spectrum{height:100%;display:grid;grid-template-columns:32% 1fr;gap:24px}
.issue-tree{background:#fffaf0;border:1px solid rgba(29,29,27,.24);padding:20px;overflow:hidden}
.issue-tree h3{font-size:22px;margin:0 0 12px}
.issue-tree p{font-size:16px;line-height:1.6;margin:0;color:#35312c}
.spectrum-map{position:relative;background:linear-gradient(90deg,rgba(159,47,37,.08),rgba(191,150,70,.08),rgba(58,91,124,.09));border:1px solid rgba(29,29,27,.24);padding:20px;overflow:hidden}
.spectrum-axis{height:4px;background:#1d1d1b;margin:24px 10px 18px;position:relative}
.spectrum-axis::before,.spectrum-axis::after{position:absolute;top:-26px;font-size:13px;font-weight:800;color:#1d1d1b}
.spectrum-axis::before{content:"文化解释";left:0}
.spectrum-axis::after{content:"结构解释";right:0}
.stance-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.stance-card{background:rgba(255,250,240,.88);border-left:4px solid #b07d2b;padding:12px;overflow:hidden;min-height:104px}
.stance-card .reading-block-title{font-size:17px}
.stance-card .reading-block-text{font-size:14px;line-height:1.48}
.clash-courtroom{height:100%;display:grid;grid-template-columns:1fr 260px 1fr;gap:18px;align-items:stretch}
.clash-side,.clash-center{background:#fffaf0;border:1px solid rgba(29,29,27,.24);padding:20px;overflow:hidden}
.clash-side.attack{border-top:6px solid #9f2f25}
.clash-side.defense{border-top:6px solid #3a5b7c}
.clash-center{display:flex;flex-direction:column;justify-content:center;text-align:center;border:2px solid #1d1d1b}
.clash-center h3{font-size:22px;margin:0 0 10px}
#progress{position:fixed;left:0;top:0;height:3px;width:0;background:#9f2f25;z-index:50;transition:width .35s ease}
.nav-dots{position:fixed;right:24px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:10px;z-index:60}
.nav-dot{width:10px;height:10px;border-radius:50%;border:1px solid rgba(29,29,27,.45);background:rgba(29,29,27,.12);cursor:pointer;padding:0}
.nav-dot.active{background:#9f2f25;border-color:#9f2f25;transform:scale(1.25)}
.nav-ui{position:fixed;left:24px;bottom:22px;z-index:60;display:flex;align-items:center;gap:12px;color:#49443d;font-family:Consolas,"SFMono-Regular",monospace;font-size:12px}
.nav-btn{width:34px;height:34px;border:1px solid rgba(29,29,27,.35);background:#fffaf0;color:#1d1d1b;cursor:pointer}
@media(max-width:900px){.slide{padding:42px 34px}.reading-header,.stance-spectrum,.clash-courtroom{grid-template-columns:1fr}.brief-grid,.stance-grid{grid-template-columns:1fr}.reading-title{font-size:32px}.reading-page{max-height:820px}}
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
    if(e.target.closest('.nav-dot,.nav-dots,.nav-btn,.reading-block,.stance-card,.clash-side,.clash-center'))return;
    go(cur+1);
  });
  go(0);
})();
</script>
"""


def render_reading_html(pages: list[ReadingPage], title: str = "圆桌洞见") -> str:
    slides = "\n".join(_render_slide(page, index) for index, page in enumerate(pages))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>
{READING_CSS}
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


def _render_slide(page: ReadingPage, index: int) -> str:
    visible = " visible" if index == 0 else ""
    renderer = _LAYOUT_RENDERERS.get(page.layout, _render_reading_brief)
    body = renderer(page)
    return (
        f'<section class="slide{visible}" data-page-type="{escape(page.page_type)}" '
        f'data-layout="{escape(page.layout)}">\n{body}\n</section>'
    )


def _render_shell(page: ReadingPage, body: str) -> str:
    return f"""<div class="reading-page">
  <header class="reading-header">
    <div>
      <div class="reading-kicker">阅读重点</div>
      <h1 class="reading-title">{escape(page.title)}</h1>
    </div>
    <p class="reading-thesis">{escape(page.thesis)}</p>
  </header>
  <main class="reading-body">{body}</main>
  <footer class="takeaway-strip"><strong>最终洞见</strong><p>{escape(page.takeaway)}</p></footer>
</div>"""


def _render_reading_brief(page: ReadingPage) -> str:
    zones = _split_blocks(page.blocks, 4)
    names = ["问题定义", "结构化内容", "证据与观点", "读者带走什么"]
    html = []
    for name, blocks in zip(names, zones):
        html.append(f'<section class="brief-zone"><h3>{escape(name)}</h3>{"".join(_render_block(block) for block in blocks)}</section>')
    return _render_shell(page, f'<div class="brief-grid">{"".join(html)}</div>')


def _render_stance_spectrum(page: ReadingPage) -> str:
    stance_cards = "".join(_render_stance_card(block) for block in page.blocks)
    body = f"""<div class="stance-spectrum">
  <aside class="issue-tree">
    <h3>命题拆解</h3>
    <p>{escape(page.thesis)}</p>
    <div class="reading-block"><span class="reading-block-label">判断路径</span><p class="reading-block-text">先看专家站位，再看他们背后的解释框架：文化、制度、资本、规律与行动选择。</p></div>
  </aside>
  <section class="spectrum-map">
    <div class="spectrum-axis"></div>
    <div class="stance-grid">{stance_cards}</div>
  </section>
</div>"""
    return _render_shell(page, body)


def _render_clash_courtroom(page: ReadingPage) -> str:
    by_kind = {block.kind: block for block in page.blocks}
    attack = by_kind.get("attack", ReadingBlock("attack", "攻击方", ""))
    defense = by_kind.get("defense", ReadingBlock("defense", "回应方", ""))
    essence = by_kind.get("essence", ReadingBlock("essence", "冲突本质", "观点冲突"))
    body = f"""<div class="clash-courtroom">
  <section class="clash-side attack">{_render_block(attack)}</section>
  <section class="clash-center"><h3>{escape(essence.title)}</h3><p class="reading-block-text">{escape(essence.text)}</p></section>
  <section class="clash-side defense">{_render_block(defense)}</section>
</div>"""
    return _render_shell(page, body)


def _render_block(block: ReadingBlock) -> str:
    label = f'<span class="reading-block-label">{escape(block.label)}</span>' if block.label else ""
    return f"""<article class="reading-block" data-kind="{escape(block.kind)}">
  {label}
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(block.text)}</p>
</article>"""


def _render_stance_card(block: ReadingBlock) -> str:
    label = f'<span class="reading-block-label">{escape(block.label)}</span>' if block.label else ""
    return f"""<article class="reading-block stance-card" data-kind="{escape(block.kind)}">
  {label}
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(block.text)}</p>
</article>"""


def _split_blocks(blocks: list[ReadingBlock], count: int) -> list[list[ReadingBlock]]:
    zones = [[] for _ in range(count)]
    for index, block in enumerate(blocks):
        zones[index % count].append(block)
    return zones


_LAYOUT_RENDERERS: dict[str, Callable[[ReadingPage], str]] = {
    "reading_brief_4zone": _render_reading_brief,
    "stance_spectrum": _render_stance_spectrum,
    "clash_courtroom": _render_clash_courtroom,
}
