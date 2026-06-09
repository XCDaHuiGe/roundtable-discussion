# -*- coding: utf-8 -*-
from __future__ import annotations

from html import escape
from typing import Callable

from engine.html_ppt_v13 import ReadingBlock, ReadingPage


READING_CSS = """
*{box-sizing:border-box}
html,body{width:100%;height:100%;margin:0;overflow:hidden;background:#f2eadc;color:#171717;font-family:"Noto Sans SC","Microsoft YaHei",Arial,sans-serif}
body.theme-editorial{--paper:#f2eadc;--paper-soft:#fffaf4;--ink:#171717;--muted:#3f3b35;--accent:#982b23;--accent-2:#bf8a2e;--accent-3:#244d66}
body.theme-obsidian{--paper:#111318;--paper-soft:#181b22;--ink:#f4efe4;--muted:#c9c2b4;--accent:#e05a47;--accent-2:#d7a64a;--accent-3:#78a8c8}
body.theme-blueprint{--paper:#e8eef2;--paper-soft:#f8fbfd;--ink:#102233;--muted:#334b5c;--accent:#1d5f8f;--accent-2:#b17624;--accent-3:#7a2d3b}
.slide{height:100vh;width:100vw;overflow:hidden;display:none;align-items:center;justify-content:center;padding:42px 70px;background:
radial-gradient(circle at 8% 12%,rgba(154,42,33,.10),transparent 24%),
linear-gradient(90deg,rgba(20,20,20,.045) 1px,transparent 1px),
linear-gradient(180deg,rgba(20,20,20,.035) 1px,transparent 1px),
#f2eadc;background-size:auto,44px 44px,44px 44px,auto}
body.theme-obsidian .slide{background:radial-gradient(circle at 8% 12%,rgba(224,90,71,.16),transparent 24%),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(180deg,rgba(255,255,255,.035) 1px,transparent 1px),var(--paper);color:var(--ink)}
body.theme-blueprint .slide{background:radial-gradient(circle at 84% 12%,rgba(29,95,143,.14),transparent 22%),linear-gradient(90deg,rgba(16,34,51,.06) 1px,transparent 1px),linear-gradient(180deg,rgba(16,34,51,.045) 1px,transparent 1px),var(--paper);color:var(--ink)}
.slide.visible{display:flex}
.reading-page{width:100%;height:100%;max-width:1280px;max-height:800px;display:grid;grid-template-rows:auto 1fr auto;gap:18px;overflow:hidden}
.reading-header{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(300px,.85fr);gap:38px;align-items:end;border-bottom:3px solid #171717;padding-bottom:14px}
.reading-kicker{font-size:12px;letter-spacing:.18em;color:#982b23;font-weight:900}
.reading-title{font-size:clamp(32px,3.6vw,52px);line-height:1.03;margin:6px 0 0;font-weight:950;letter-spacing:0}
.reading-thesis{font-size:18px;line-height:1.6;margin:0;color:#3f3b35;border-left:5px solid #982b23;padding-left:18px}
.reading-body{min-height:0;overflow:hidden}
.reading-block{border-top:1px solid rgba(23,23,23,.18);padding:11px 0 0;min-height:0}
.reading-block-title{font-size:18px;font-weight:900;margin:0 0 7px;line-height:1.25}
.reading-block-label{display:inline-block;font-size:11px;font-weight:900;letter-spacing:.10em;color:#982b23;margin-bottom:7px}
.reading-block-text{font-size:14px;line-height:1.55;color:#2f2b27;margin:0}
.takeaway-strip{border:3px solid #171717;background:#fffaf4;padding:12px 18px;display:grid;grid-template-columns:120px 1fr;gap:18px;align-items:center;overflow:hidden;box-shadow:8px 8px 0 rgba(23,23,23,.10)}
.takeaway-strip strong{font-size:15px;color:#982b23;letter-spacing:.08em}
.takeaway-strip p{font-size:17px;line-height:1.42;margin:0;font-weight:900}
.brief-grid{display:grid;grid-template-columns:1.12fr .88fr;grid-template-rows:1fr 1fr;gap:16px;height:100%}
.brief-zone{background:rgba(255,250,244,.86);border:1px solid rgba(23,23,23,.20);padding:18px 20px;overflow:hidden;box-shadow:0 18px 40px rgba(36,25,12,.07)}
.brief-zone:nth-child(1){border-left:7px solid #982b23}
.brief-zone:nth-child(2){border-left:7px solid #bf8a2e}
.brief-zone:nth-child(3){border-left:7px solid #244d66}
.brief-zone:nth-child(4){border-left:7px solid #171717}
.brief-zone h3{font-size:15px;margin:0 0 12px;letter-spacing:.10em;color:#982b23}
.brief-zone .reading-block{border-top:0;padding-top:0;margin-bottom:12px}
.stance-spectrum{height:100%;display:grid;grid-template-columns:30% 1fr;gap:22px}
.issue-tree{background:#171717;color:#fffaf4;padding:24px;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between}
.issue-tree h3{font-size:24px;margin:0 0 14px;color:#fffaf4}
.issue-tree p{font-size:16px;line-height:1.6;margin:0;color:#35312c}
.issue-tree p,.issue-tree .reading-block-text{color:rgba(255,250,244,.82)}
.issue-tree .reading-block{border-top-color:rgba(255,250,244,.26)}
.spectrum-map{position:relative;background:rgba(255,250,244,.72);border:1px solid rgba(23,23,23,.18);padding:18px 22px;overflow:hidden;box-shadow:0 18px 46px rgba(36,25,12,.08)}
.spectrum-axis{height:5px;background:#171717;margin:24px 8px 18px;position:relative}
.spectrum-axis::before,.spectrum-axis::after{position:absolute;top:-28px;font-size:13px;font-weight:900;color:#171717}
.spectrum-axis::before{content:"文化解释";left:0}
.spectrum-axis::after{content:"结构解释";right:0}
.stance-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-rows:minmax(0,1fr);gap:10px;height:calc(100% - 47px)}
.stance-card{background:#fffaf4;border-left:5px solid #bf8a2e;padding:12px 14px;overflow:hidden;min-height:0}
.stance-card .reading-block-title{font-size:16px;margin-bottom:5px}
.stance-card .reading-block-label{font-size:10px;margin-bottom:5px}
.stance-card .reading-block-text{font-size:13px;line-height:1.42}
.clash-courtroom{height:100%;display:grid;grid-template-columns:1fr 220px 1fr;gap:18px;align-items:stretch}
.clash-side,.clash-center{background:#fffaf4;border:1px solid rgba(23,23,23,.20);padding:24px;overflow:hidden;box-shadow:0 18px 46px rgba(36,25,12,.07)}
.clash-side.attack{border-top:8px solid #982b23}
.clash-side.defense{border-top:8px solid #244d66}
.clash-center{display:flex;flex-direction:column;justify-content:center;text-align:center;border:3px solid #171717;background:#171717;color:#fffaf4;box-shadow:8px 8px 0 rgba(23,23,23,.12)}
.clash-center h3{font-size:24px;margin:0 0 12px;color:#fffaf4}
.clash-center .reading-block-text{color:rgba(255,250,244,.82)}
.cover-page{width:100%;height:100%;max-width:1280px;max-height:800px;display:grid;grid-template-columns:1fr 360px;gap:44px;overflow:hidden}
.cover-main{display:flex;flex-direction:column;justify-content:center;border-top:8px solid #171717;border-bottom:3px solid #171717}
.cover-kicker{font-size:13px;letter-spacing:.22em;color:#982b23;font-weight:950;margin-bottom:22px}
.cover-title{font-size:clamp(58px,7.6vw,106px);line-height:.98;margin:0 0 28px;font-weight:950;letter-spacing:-.02em}
.cover-thesis{font-size:24px;line-height:1.5;color:#332f2a;max-width:760px;margin:0}
.cover-side{background:#171717;color:#fffaf4;padding:34px;display:grid;grid-template-rows:auto 1fr auto;overflow:hidden;box-shadow:14px 14px 0 rgba(23,23,23,.12)}
.cover-meta{font-size:15px;line-height:1.8;color:rgba(255,250,244,.82)}
.cover-stats{display:grid;grid-template-columns:1fr;gap:14px;align-self:center}
.cover-stat{border-top:1px solid rgba(255,250,244,.28);padding-top:12px}
.cover-stat b{display:block;font-size:44px;line-height:1;font-weight:950;color:#f2eadc}
.cover-stat span{font-size:13px;letter-spacing:.12em;color:#d49a3a}
.cover-takeaway{font-size:17px;line-height:1.5;font-weight:850;color:#fffaf4}
#progress{position:fixed;left:0;top:0;height:4px;width:0;background:#982b23;z-index:50;transition:width .35s ease}
.nav-dots{position:fixed;right:24px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:10px;z-index:60}
.nav-dot{width:9px;height:9px;border-radius:50%;border:1px solid rgba(23,23,23,.45);background:rgba(23,23,23,.12);cursor:pointer;padding:0}
.nav-dot.active{background:#982b23;border-color:#982b23;transform:scale(1.28)}
.nav-ui{position:fixed;left:24px;bottom:22px;z-index:60;display:flex;align-items:center;gap:12px;color:#49443d;font-family:Consolas,"SFMono-Regular",monospace;font-size:12px}
.nav-btn{width:34px;height:34px;border:1px solid rgba(23,23,23,.35);background:#fffaf4;color:#171717;cursor:pointer}
body.theme-obsidian .reading-header,body.theme-blueprint .reading-header{border-bottom-color:var(--ink)}
body.theme-obsidian .reading-kicker,body.theme-obsidian .reading-block-label,body.theme-obsidian .takeaway-strip strong,body.theme-obsidian .brief-zone h3,body.theme-blueprint .reading-kicker,body.theme-blueprint .reading-block-label,body.theme-blueprint .takeaway-strip strong,body.theme-blueprint .brief-zone h3{color:var(--accent)}
body.theme-obsidian .reading-thesis,body.theme-blueprint .reading-thesis{color:var(--muted);border-left-color:var(--accent)}
body.theme-obsidian .reading-block-text,body.theme-blueprint .reading-block-text{color:var(--muted)}
body.theme-obsidian .brief-zone,body.theme-obsidian .spectrum-map,body.theme-obsidian .stance-card,body.theme-obsidian .clash-side,body.theme-blueprint .brief-zone,body.theme-blueprint .spectrum-map,body.theme-blueprint .stance-card,body.theme-blueprint .clash-side{background:var(--paper-soft);border-color:rgba(120,120,120,.28)}
body.theme-obsidian .issue-tree,body.theme-obsidian .clash-center,body.theme-obsidian .cover-side{background:#050608;color:var(--ink)}
body.theme-blueprint .issue-tree,body.theme-blueprint .clash-center,body.theme-blueprint .cover-side{background:#102233;color:#f8fbfd}
body.theme-obsidian .takeaway-strip,body.theme-blueprint .takeaway-strip{background:var(--paper-soft);border-color:var(--ink);color:var(--ink)}
body.theme-obsidian .takeaway-strip p,body.theme-blueprint .takeaway-strip p{color:var(--ink)}
body.theme-obsidian .cover-main,body.theme-blueprint .cover-main{border-color:var(--ink)}
body.theme-obsidian .cover-thesis,body.theme-blueprint .cover-thesis{color:var(--muted)}
body.theme-obsidian .nav-btn{background:#181b22;color:#f4efe4;border-color:rgba(255,255,255,.35)}
body.theme-blueprint .nav-btn{background:#f8fbfd;color:#102233;border-color:rgba(16,34,51,.35)}
body.theme-obsidian #progress,body.theme-obsidian .nav-dot.active,body.theme-blueprint #progress,body.theme-blueprint .nav-dot.active{background:var(--accent);border-color:var(--accent)}
body.theme-obsidian .clash-center .reading-block-text,body.theme-blueprint .clash-center .reading-block-text{color:rgba(255,250,244,.82)}
@media(max-width:900px){.slide{padding:34px 28px}.reading-header,.stance-spectrum,.clash-courtroom,.cover-page{grid-template-columns:1fr}.brief-grid,.stance-grid{grid-template-columns:1fr}.reading-title{font-size:32px}.cover-title{font-size:48px}.reading-page{max-height:820px}.cover-side{display:none}}
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


def render_reading_html(pages: list[ReadingPage], title: str = "圆桌洞见", theme: str = "editorial") -> str:
    theme = theme if theme in {"editorial", "obsidian", "blueprint"} else "editorial"
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
<body class="theme-{escape(theme)}">
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
    if page.page_type == "cover":
        body = _render_cover(page)
        return (
            f'<section class="slide{visible}" data-page-type="{escape(page.page_type)}" '
            f'data-layout="cover">\n{body}\n</section>'
        )
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


def _render_cover(page: ReadingPage) -> str:
    stats = "".join(
        f'<div class="cover-stat"><b>{escape(block.text)}</b><span>{escape(block.title)}</span></div>'
        for block in page.blocks[:3]
    )
    return f"""<div class="cover-page">
  <main class="cover-main">
    <div class="cover-kicker">READING DECK / 圆桌洞见</div>
    <h1 class="cover-title reading-title">{escape(page.title)}</h1>
    <p class="cover-thesis">{escape(page.thesis)}</p>
  </main>
  <aside class="cover-side">
    <div class="cover-meta">文化属性 / 杀富济贫 / 天道与规律 / 专家轮辩</div>
    <div class="cover-stats">{stats}</div>
    <div class="cover-takeaway">{escape(page.takeaway)}</div>
  </aside>
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
  <p class="reading-block-text">{escape(_clip_text(block.text, 140))}</p>
</article>"""


def _render_stance_card(block: ReadingBlock) -> str:
    label = f'<span class="reading-block-label">{escape(block.label)}</span>' if block.label else ""
    return f"""<article class="reading-block stance-card" data-kind="{escape(block.kind)}">
  {label}
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(_clip_text(block.text, 105))}</p>
</article>"""


def _split_blocks(blocks: list[ReadingBlock], count: int) -> list[list[ReadingBlock]]:
    zones = [[] for _ in range(count)]
    for index, block in enumerate(blocks):
        zones[index % count].append(block)
    return zones


def _clip_text(text: str, limit: int) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip("，。；、 ") + "…"


_LAYOUT_RENDERERS: dict[str, Callable[[ReadingPage], str]] = {
    "reading_brief_4zone": _render_reading_brief,
    "stance_spectrum": _render_stance_spectrum,
    "clash_courtroom": _render_clash_courtroom,
}
