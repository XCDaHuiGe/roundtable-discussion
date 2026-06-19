# -*- coding: utf-8 -*-
from __future__ import annotations

from html import escape
from typing import Callable

from engine.html_ppt_v13 import ReadingBlock, ReadingPage


READING_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=IBM+Plex+Mono:wght@400;600&display=swap');

*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
body.theme-editorial{
  --paper:#f4efe6;--paper-soft:#fffaf2;--ink:#161616;--muted:#50483d;
  --accent:#a7342a;--accent-2:#0f5d63;--accent-3:#c69236;
  --paper-rgb:244,239,230;--ink-rgb:22,22,22;--accent-rgb:167,52,42;
  --serif:'Noto Serif SC','Source Han Serif SC',Georgia,serif;
  --sans:'Noto Sans SC','Microsoft YaHei',Arial,sans-serif;
  --mono:'IBM Plex Mono',Consolas,monospace;
  font-family:var(--sans);color:var(--ink);background:var(--paper)
}
body.theme-obsidian{
  --paper:#101217;--paper-soft:#191c23;--ink:#f7efe2;--muted:#cfc3b2;
  --accent:#e05a47;--accent-2:#7fb8c9;--accent-3:#d6a849;
  --paper-rgb:16,18,23;--ink-rgb:247,239,226;--accent-rgb:224,90,71;
  --serif:'Noto Serif SC','Source Han Serif SC',Georgia,serif;
  --sans:'Noto Sans SC','Microsoft YaHei',Arial,sans-serif;
  --mono:'IBM Plex Mono',Consolas,monospace;
  font-family:var(--sans);color:var(--ink);background:var(--paper)
}
body.theme-blueprint{
  --paper:#e9eff3;--paper-soft:#f9fcff;--ink:#102233;--muted:#385164;
  --accent:#1d5f8f;--accent-2:#8a3b42;--accent-3:#b17624;
  --paper-rgb:233,239,243;--ink-rgb:16,34,51;--accent-rgb:29,95,143;
  --serif:'Noto Serif SC','Source Han Serif SC',Georgia,serif;
  --sans:'Noto Sans SC','Microsoft YaHei',Arial,sans-serif;
  --mono:'IBM Plex Mono',Consolas,monospace;
  font-family:var(--sans);color:var(--ink);background:var(--paper)
}
.slide{
  height:100vh;width:100vw;overflow:hidden;display:none;align-items:center;justify-content:center;
  padding:48px 72px;position:relative;background:var(--paper)
}
.slide.visible{display:flex}
.slide::before{
  content:"";position:absolute;inset:0;z-index:0;pointer-events:none;
  background:
    linear-gradient(90deg,rgba(var(--ink-rgb),.045) 1px,transparent 1px),
    linear-gradient(180deg,rgba(var(--ink-rgb),.035) 1px,transparent 1px);
  background-size:64px 64px
}
.slide[data-tone="dark"]{background:var(--ink);color:var(--paper)}
.slide[data-tone="dark"]::before{
  background:
    radial-gradient(circle at 18% 20%,rgba(var(--accent-rgb),.25),transparent 24%),
    linear-gradient(90deg,rgba(var(--paper-rgb),.07) 1px,transparent 1px),
    linear-gradient(180deg,rgba(var(--paper-rgb),.06) 1px,transparent 1px);
  background-size:auto,64px 64px,64px 64px
}
.slide[data-tone="dark"] .reading-page,.slide[data-tone="dark"] .cover-page{color:var(--paper)}
.slide[data-tone="dark"] .reading-thesis,.slide[data-tone="dark"] .reading-block-text{color:rgba(var(--paper-rgb),.82)}
.slide[data-tone="dark"] .takeaway-strip,.slide[data-tone="dark"] .brief-zone,.slide[data-tone="dark"] .focus-side,.slide[data-tone="dark"] .case-panel,.slide[data-tone="dark"] .question-card{
  background:rgba(var(--paper-rgb),.08);border-color:rgba(var(--paper-rgb),.22);box-shadow:none
}
.slide[data-tone="dark"] .reading-header{border-bottom-color:var(--paper)}
.reading-page{
  position:relative;z-index:1;width:100%;height:100%;max-width:1320px;max-height:820px;
  display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:20px;overflow:hidden
}
.reading-header{
  display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:34px;align-items:end;
  border-bottom:3px solid var(--ink);padding-bottom:14px
}
.reading-kicker{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:600}
.reading-title{font-family:var(--serif);font-size:clamp(30px,3.2vw,50px);line-height:1.08;margin-top:8px;font-weight:900}
.reading-thesis{font-family:var(--serif);font-size:17px;line-height:1.62;color:var(--muted);border-left:4px solid var(--accent);padding-left:18px}
.reading-body{min-height:0;overflow:hidden}
.reading-block{border-top:1px solid rgba(var(--ink-rgb),.15);padding-top:12px;min-height:0;overflow:hidden}
.reading-block-title{font-family:var(--serif);font-size:18px;line-height:1.28;font-weight:800;margin-bottom:7px}
.reading-block-label{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:7px}
.reading-block-text{font-size:14px;line-height:1.58;color:var(--muted)}
.takeaway-strip{
  border:3px solid var(--ink);background:var(--paper-soft);padding:13px 18px;
  display:grid;grid-template-columns:110px minmax(0,1fr);gap:18px;align-items:center;overflow:hidden;
  box-shadow:7px 7px 0 rgba(var(--ink-rgb),.09)
}
.takeaway-strip strong{font-family:var(--mono);font-size:12px;letter-spacing:.12em;color:var(--accent);text-transform:uppercase}
.takeaway-strip p{font-family:var(--serif);font-size:17px;line-height:1.42;font-weight:800}
.cover-page{position:relative;z-index:1;width:100%;height:100%;max-width:1320px;max-height:820px;display:grid;grid-template-columns:1fr 330px;gap:42px;overflow:hidden}
.cover-main{display:flex;flex-direction:column;justify-content:center;border-top:8px solid currentColor;border-bottom:3px solid currentColor}
.cover-kicker{font-family:var(--mono);font-size:12px;letter-spacing:.22em;color:var(--accent);text-transform:uppercase;font-weight:600;margin-bottom:24px}
.cover-title{font-family:var(--serif);font-size:clamp(58px,7vw,98px);line-height:.98;font-weight:900;margin-bottom:28px}
.cover-thesis{font-size:22px;line-height:1.55;color:var(--muted);max-width:760px}
.cover-side{background:var(--ink);color:var(--paper);padding:30px;display:grid;grid-template-rows:auto 1fr auto;box-shadow:12px 12px 0 rgba(var(--ink-rgb),.1);overflow:hidden}
.cover-meta{font-size:14px;line-height:1.75;color:rgba(var(--paper-rgb),.82)}
.cover-stats{display:grid;gap:14px;align-self:center}
.cover-stat{border-top:1px solid rgba(var(--paper-rgb),.25);padding-top:12px}
.cover-stat b{display:block;font-family:var(--serif);font-size:42px;line-height:1;font-weight:900}
.cover-stat span{font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:var(--accent-3);text-transform:uppercase}
.cover-takeaway{font-family:var(--serif);font-size:16px;line-height:1.5;font-weight:800}
.brief-grid{display:grid;grid-template-columns:1.12fr .88fr;grid-template-rows:1fr 1fr;gap:16px;height:100%}
.brief-zone{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.14);border-top:5px solid var(--accent);padding:18px 20px;overflow:hidden;box-shadow:0 10px 28px rgba(var(--ink-rgb),.06)}
.brief-zone:nth-child(2){border-top-color:var(--accent-2)}.brief-zone:nth-child(3){border-top-color:var(--accent-3)}.brief-zone:nth-child(4){border-top-color:var(--ink)}
.brief-zone h3{font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:var(--accent);text-transform:uppercase;margin-bottom:13px}
.brief-zone .reading-block{border-top:0;padding-top:0;margin-bottom:12px}
.focus-grid{height:100%;display:grid;grid-template-columns:minmax(0,1.08fr) 360px;gap:26px;align-items:stretch}
.focus-main{display:flex;flex-direction:column;justify-content:center;border-left:8px solid var(--accent);padding-left:28px;overflow:hidden}
.focus-number{font-family:var(--mono);font-size:12px;letter-spacing:.18em;color:var(--accent);text-transform:uppercase;margin-bottom:16px}
.focus-main h2{font-family:var(--serif);font-size:clamp(46px,5.6vw,82px);line-height:1.02;font-weight:900;margin-bottom:24px}
.focus-main p{font-family:var(--serif);font-size:21px;line-height:1.55;color:var(--muted)}
.focus-side{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.16);padding:22px;display:grid;gap:14px;overflow:hidden}
.stance-spectrum{height:100%;display:grid;grid-template-columns:30% 1fr;gap:22px}
.issue-tree{background:var(--ink);color:var(--paper);padding:24px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}
.issue-tree h3{font-family:var(--serif);font-size:24px;margin-bottom:14px}
.issue-tree p{font-size:15px;line-height:1.62;color:rgba(var(--paper-rgb),.82)}
.spectrum-map{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.14);padding:20px;overflow:hidden;box-shadow:0 10px 28px rgba(var(--ink-rgb),.06)}
.spectrum-axis{height:4px;background:var(--ink);margin:22px 6px 18px;position:relative}
.spectrum-axis::before,.spectrum-axis::after{position:absolute;top:-27px;font-family:var(--mono);font-size:11px;font-weight:600;color:var(--ink)}
.spectrum-axis::before{content:"规律 / 结构";left:0}.spectrum-axis::after{content:"选择 / 人情";right:0}
.stance-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-rows:minmax(0,1fr);gap:10px;height:calc(100% - 46px)}
.stance-card{background:var(--paper-soft);border-left:4px solid var(--accent-2);padding:12px 14px;overflow:hidden}
.stance-card .reading-block-title{font-size:15px}.stance-card .reading-block-text{font-size:12px;line-height:1.45}
.case-file{height:100%;display:grid;grid-template-columns:38% 1fr;gap:22px}
.case-lead{background:var(--ink);color:var(--paper);padding:26px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}
.case-lead h2{font-family:var(--serif);font-size:38px;line-height:1.08;font-weight:900;color:var(--paper)}
.case-lead p{font-size:16px;line-height:1.62;color:rgba(var(--paper-rgb),.84)}
.case-panel{display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:minmax(0,1fr);gap:14px;background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.14);padding:18px;overflow:hidden}
.shock-poster{height:100%;display:grid;grid-template-columns:minmax(0,1.15fr) 330px;gap:28px;overflow:hidden}
.shock-poster-main{position:relative;background:var(--ink);color:var(--paper);padding:34px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}
.shock-poster-main::after{content:"";position:absolute;right:-9%;top:10%;width:34%;height:80%;border:18px solid var(--accent);opacity:.72;transform:rotate(10deg)}
.shock-poster-main h2{font-family:var(--serif);font-size:clamp(48px,5.8vw,88px);line-height:.98;font-weight:900;max-width:780px;position:relative;z-index:1}
.shock-poster-main p{font-size:18px;line-height:1.58;color:rgba(var(--paper-rgb),.82);max-width:760px;position:relative;z-index:1}
.shock-poster-side,.evidence-wall,.cost-panel,.interrogation-room,.xray-diagnosis{overflow:hidden}
.shock-poster-side{display:grid;grid-template-rows:repeat(3,minmax(0,1fr));gap:14px}
.shock-chip{background:var(--paper-soft);border-left:7px solid var(--accent);padding:18px;overflow:hidden}
.evidence-wall{height:100%;display:grid;grid-template-columns:1.1fr .9fr;grid-template-rows:1fr 1fr;gap:14px}
.evidence-card{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.16);padding:22px;overflow:hidden;box-shadow:0 10px 28px rgba(var(--ink-rgb),.06)}
.evidence-card:first-child{grid-row:span 2;background:var(--ink);color:var(--paper);border-color:var(--ink)}
.evidence-card:first-child .reading-block-text{color:rgba(var(--paper-rgb),.82)}
.cost-blast{height:100%;display:grid;grid-template-columns:42% 1fr;gap:22px;overflow:hidden}
.cost-number{background:var(--accent);color:var(--paper);padding:32px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}
.cost-number b{font-family:var(--serif);font-size:clamp(64px,8vw,124px);line-height:.9;font-weight:900}
.cost-number span{font-family:var(--mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase}
.cost-panel{display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:minmax(0,1fr);gap:14px}
.cost-card{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.16);border-top:6px solid var(--accent);padding:18px;overflow:hidden}
.interrogation-room{height:100%;display:grid;grid-template-columns:1fr 230px 1fr;gap:16px}
.interrogation-room .clash-center{box-shadow:inset 0 0 0 8px rgba(var(--paper-rgb),.08)}
.xray-diagnosis{height:100%;display:grid;grid-template-columns:35% 1fr;gap:20px}
.xray-core{background:var(--ink);color:var(--paper);padding:26px;display:flex;flex-direction:column;justify-content:center;overflow:hidden}
.xray-core h2{font-family:var(--serif);font-size:42px;line-height:1.04}
.xray-grid{display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:minmax(0,1fr);gap:14px;overflow:hidden}
.xray-card{background:var(--paper-soft);border-left:6px solid var(--accent-2);padding:18px;overflow:hidden}
.clash-courtroom{height:100%;display:grid;grid-template-columns:1fr 200px 1fr;gap:18px}
.clash-side,.clash-center{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.14);padding:24px;overflow:hidden;box-shadow:0 10px 28px rgba(var(--ink-rgb),.06)}
.clash-side.attack{border-top:6px solid var(--accent)}.clash-side.defense{border-top:6px solid var(--accent-2)}
.clash-center{background:var(--ink);color:var(--paper);display:flex;flex-direction:column;justify-content:center;text-align:center;border:3px solid var(--ink)}
.clash-center h3{font-family:var(--serif);font-size:20px;margin-bottom:12px;color:var(--paper)}
.evolution-ladder{height:100%;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;align-items:stretch}
.step-card{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.14);border-top:7px solid var(--accent);padding:20px;display:grid;grid-template-rows:auto auto 1fr;gap:10px;overflow:hidden}
.step-card:nth-child(2){border-top-color:var(--accent-2)}.step-card:nth-child(3){border-top-color:var(--accent-3)}.step-card:nth-child(4){border-top-color:var(--ink)}
.step-index{font-family:var(--mono);font-size:12px;color:var(--accent);letter-spacing:.12em}
.tension-bars{height:100%;display:grid;grid-template-columns:1fr 1fr;gap:14px;align-content:stretch}
.tension-item{background:var(--paper-soft);border-left:7px solid var(--accent);padding:16px 18px;overflow:hidden}
.tension-item:nth-child(2n){border-left-color:var(--accent-2)}.tension-item:nth-child(3n){border-left-color:var(--accent-3)}
.bar{height:5px;background:rgba(var(--ink-rgb),.13);margin-top:10px}.bar span{display:block;height:100%;background:var(--accent)}
.question-wall{height:100%;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.question-card{background:var(--paper-soft);border:1px solid rgba(var(--ink-rgb),.14);padding:18px 20px;overflow:hidden}
.question-card .reading-block-title{font-size:20px;color:var(--accent)}
#progress{position:fixed;left:0;top:0;height:3px;width:0;background:var(--accent);z-index:50;transition:width .35s ease}
.nav-dots{position:fixed;right:20px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:8px;z-index:60}
.nav-dot{width:8px;height:8px;border-radius:50%;border:1px solid rgba(var(--ink-rgb),.35);background:rgba(var(--ink-rgb),.1);cursor:pointer;padding:0}
.nav-dot.active{background:var(--accent);border-color:var(--accent);transform:scale(1.28)}
.nav-ui{position:fixed;left:20px;bottom:18px;z-index:60;display:flex;align-items:center;gap:10px;color:var(--muted);font-family:var(--mono);font-size:11px}
.nav-btn{width:32px;height:32px;border:1px solid rgba(var(--ink-rgb),.24);background:var(--paper-soft);color:var(--ink);cursor:pointer;font-family:var(--mono);font-size:14px}
#esc-overlay{position:fixed;inset:0;z-index:100;background:rgba(var(--ink-rgb),.92);display:none;align-items:center;justify-content:center;backdrop-filter:blur(8px)}
#esc-overlay.visible{display:flex}
#esc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;padding:40px;max-width:90vw;max-height:85vh;overflow:hidden}
.esc-thumb{aspect-ratio:16/10;background:var(--paper-soft);border:2px solid transparent;cursor:pointer;overflow:hidden;position:relative}
.esc-thumb.active{border-color:var(--accent)}
.esc-thumb-label{position:absolute;bottom:0;left:0;right:0;padding:8px;background:rgba(var(--ink-rgb),.82);color:var(--paper);font-family:var(--mono);font-size:10px;letter-spacing:.1em}
[data-anim]{opacity:0;transform:translateY(22px);transition:opacity .6s cubic-bezier(.4,0,.2,1),transform .6s cubic-bezier(.4,0,.2,1)}
.slide.visible [data-anim]{opacity:1;transform:translateY(0)}
[data-anim="fade-left"]{transform:translateX(-28px)}[data-anim="fade-right"]{transform:translateX(28px)}[data-anim="scale-in"]{transform:scale(.94)}
.slide.visible [data-anim="fade-left"],.slide.visible [data-anim="fade-right"]{transform:translateX(0)}
.slide.visible [data-anim="scale-in"]{transform:scale(1)}
[data-stagger] [data-anim]:nth-child(1){transition-delay:.05s}[data-stagger] [data-anim]:nth-child(2){transition-delay:.12s}[data-stagger] [data-anim]:nth-child(3){transition-delay:.19s}[data-stagger] [data-anim]:nth-child(4){transition-delay:.26s}[data-stagger] [data-anim]:nth-child(5){transition-delay:.33s}[data-stagger] [data-anim]:nth-child(6){transition-delay:.4s}
@media(max-width:900px){
  .slide{padding:30px 22px}.reading-header,.cover-page,.focus-grid,.stance-spectrum,.case-file,.clash-courtroom{grid-template-columns:1fr}
  .brief-grid,.question-wall,.tension-bars,.evolution-ladder,.case-panel,.stance-grid{grid-template-columns:1fr}
  .cover-side{display:none}.nav-dots{display:none}.reading-page{max-height:820px}.focus-main h2{font-size:34px}.cover-title{font-size:40px}
}
@media(max-height:680px){.slide{padding:28px 54px}.reading-page{gap:12px}.reading-title{font-size:30px}.reading-block-text{font-size:12px}}
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
  const escOverlay=document.getElementById('esc-overlay');
  const escGrid=document.getElementById('esc-grid');

  sections.forEach((s,i)=>{
    const dot=document.createElement('button');
    dot.className='nav-dot'+(i===0?' active':'');
    dot.setAttribute('aria-label','第 '+(i+1)+' 页');
    dot.onclick=()=>go(i);
    dotsContainer.appendChild(dot);
  });

  sections.forEach((s,i)=>{
    const thumb=document.createElement('div');
    thumb.className='esc-thumb'+(i===0?' active':'');
    thumb.innerHTML='<div class="esc-thumb-label">'+(i+1)+' / '+total+'</div>';
    thumb.onclick=()=>{go(i);toggleEsc(false)};
    escGrid.appendChild(thumb);
  });

  function go(n){
    if(n<0||n>=total)return;
    sections[cur].classList.remove('visible');
    dotsContainer.children[cur]?.classList.remove('active');
    escGrid.children[cur]?.classList.remove('active');
    cur=n;
    sections[cur].scrollIntoView({behavior:'smooth',block:'start'});
    sections[cur].classList.add('visible');
    dotsContainer.children[cur]?.classList.add('active');
    escGrid.children[cur]?.classList.add('active');
    const pct=Math.min(100,((cur+1)/total)*100);
    progress.style.width=pct+'%';
    if(counter)counter.textContent=(cur+1)+' / '+total;
  }

  function toggleEsc(show){
    if(show===undefined)show=!escOverlay.classList.contains('visible');
    escOverlay.classList.toggle('visible',show);
  }

  document.getElementById('prevBtn').onclick=()=>go(cur-1);
  document.getElementById('nextBtn').onclick=()=>go(cur+1);

  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'){
      e.preventDefault();toggleEsc();return;
    }
    if(escOverlay.classList.contains('visible'))return;
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
    if(escOverlay.classList.contains('visible'))return;
    e.preventDefault();
    if(wheelTimer)return;
    wheelTimer=setTimeout(()=>wheelTimer=null,400);
    if(e.deltaY>0)go(cur+1);
    else if(e.deltaY<0)go(cur-1);
  },{passive:false});

  document.body.addEventListener('click',e=>{
    if(e.target.closest('.nav-dot,.nav-dots,.nav-btn,.reading-block,.stance-card,.clash-side,.clash-center,.question-card,.esc-thumb,#esc-overlay'))return;
    go(cur+1);
  });

  escOverlay.addEventListener('click',e=>{
    if(e.target===escOverlay)toggleEsc(false);
  });

  go(0);
})();
</script>
"""


def render_reading_html(pages: list[ReadingPage], title: str = "圆桌洞见", theme: str = "editorial") -> str:
    valid_themes = {"editorial", "obsidian", "blueprint"}
    theme = theme if theme in valid_themes else "editorial"
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
<div id="esc-overlay"><div id="esc-grid"></div></div>
{slides}
{NAVIGATION_JS}
</body>
</html>
"""


def _render_slide(page: ReadingPage, index: int) -> str:
    visible = " visible" if index == 0 else ""
    layout = "cover" if page.page_type == "cover" else page.layout
    tone = f' data-tone="{escape(str(page.meta.get("tone")))}"' if page.meta.get("tone") else ""
    renderer = _VARIANT_RENDERERS.get(page.layout_variant) or _LAYOUT_RENDERERS.get(page.layout, _render_reading_brief)
    body = _render_cover(page) if page.page_type == "cover" else renderer(page)
    return (
        f'<section class="slide{visible}" data-page-type="{escape(page.page_type)}" '
        f'data-layout="{escape(layout)}" data-display-logic="{escape(page.display_logic)}" '
        f'data-layout-variant="{escape(page.layout_variant)}"{tone}>\n{body}\n</section>'
    )


def _render_shell(page: ReadingPage, body: str) -> str:
    return f"""<div class="reading-page">
  <header class="reading-header" data-anim="fade-up">
    <div>
      <div class="reading-kicker">{escape(_kicker(page))}</div>
      <h1 class="reading-title">{escape(page.title)}</h1>
    </div>
    <p class="reading-thesis">{escape(page.thesis)}</p>
  </header>
  <main class="reading-body" data-stagger>{body}</main>
  <footer class="takeaway-strip" data-anim="fade-up"><strong>最终洞见</strong><p>{escape(page.takeaway)}</p></footer>
</div>"""


def _render_cover(page: ReadingPage) -> str:
    stats = "".join(
        f'<div class="cover-stat"><b>{escape(block.text)}</b><span>{escape(block.title)}</span></div>'
        for block in page.blocks[:3]
    )
    cover_meta = page.meta.get("cover_meta", "专家圆桌 / 深度蒸馏")
    return f"""<div class="cover-page">
  <main class="cover-main" data-anim="fade-up">
    <div class="cover-kicker">ROUNDTABLE OS / 圆桌洞见</div>
    <h1 class="cover-title reading-title">{escape(page.title)}</h1>
    <p class="cover-thesis">{escape(page.thesis)}</p>
  </main>
  <aside class="cover-side" data-anim="fade-right">
    <div class="cover-meta">{escape(cover_meta)}</div>
    <div class="cover-stats">{stats}</div>
    <div class="cover-takeaway">{escape(page.takeaway)}</div>
  </aside>
</div>"""


def _render_reading_brief(page: ReadingPage) -> str:
    zones = _split_blocks(page.blocks, 4)
    names = ["问题定义", "结构化内容", "证据与观点", "读者带走"]
    html = []
    for name, blocks in zip(names, zones):
        html.append(f'<section class="brief-zone" data-anim="fade-up"><h3>{escape(name)}</h3>{"".join(_render_block(block) for block in blocks)}</section>')
    return _render_shell(page, f'<div class="brief-grid" data-stagger>{"".join(html)}</div>')


def _render_magazine_focus(page: ReadingPage) -> str:
    side = "".join(_render_block(block) for block in page.blocks[:4])
    body = f"""<div class="focus-grid">
  <section class="focus-main" data-anim="fade-left">
    <div class="focus-number">{escape(page.page_type.upper())}</div>
    <h2>{escape(page.title)}</h2>
    <p>{escape(page.thesis)}</p>
  </section>
  <aside class="focus-side" data-anim="fade-right">{side}</aside>
</div>"""
    return _render_shell(page, body)


def _render_stance_spectrum(page: ReadingPage) -> str:
    stance_cards = "".join(_render_stance_card(block) for block in page.blocks)
    body = f"""<div class="stance-spectrum">
  <aside class="issue-tree" data-anim="fade-left">
    <h3>命题拆解</h3>
    <p>{escape(page.thesis)}</p>
    <div class="reading-block"><span class="reading-block-label">判断路径</span><p class="reading-block-text">先看专家站位，再看他们背后的解释框架：规律、制度、资本、情感与行动选择。</p></div>
  </aside>
  <section class="spectrum-map" data-anim="fade-right">
    <div class="spectrum-axis"></div>
    <div class="stance-grid" data-stagger>{stance_cards}</div>
  </section>
</div>"""
    return _render_shell(page, body)


def _render_case_file(page: ReadingPage) -> str:
    lead = page.blocks[1] if len(page.blocks) > 1 else (page.blocks[0] if page.blocks else ReadingBlock("case", "冲击事件", page.thesis))
    panel = "".join(_render_block(block) for block in page.blocks if block is not lead)
    body = f"""<div class="case-file">
  <section class="case-lead" data-anim="fade-left">
    <div class="reading-kicker">SHOCK EVENT</div>
    <h2>{escape(lead.title)}</h2>
    <p>{escape(_clip_text(lead.text, 260))}</p>
  </section>
  <section class="case-panel" data-anim="fade-right" data-stagger>{panel}</section>
</div>"""
    return _render_shell(page, body)


def _render_shock_poster(page: ReadingPage) -> str:
    lead = next((block for block in page.blocks if block.kind == "event"), page.blocks[0] if page.blocks else ReadingBlock("event", page.title, page.thesis))
    side_blocks = [block for block in page.blocks if block is not lead][:3]
    chips = "".join(
        f'<article class="shock-chip" data-anim="fade-up">{_render_block_inner(block, 118)}</article>'
        for block in side_blocks
    )
    body = f"""<div class="shock-poster">
  <section class="shock-poster-main" data-anim="fade-left">
    <div class="reading-kicker">SHOCK POSTER / {escape(page.display_logic.upper())}</div>
    <h2>{escape(lead.title)}</h2>
    <p>{escape(_clip_text(lead.text or page.thesis, 260))}</p>
  </section>
  <aside class="shock-poster-side" data-anim="fade-right" data-stagger>{chips}</aside>
</div>"""
    return _render_shell(page, body)


def _render_evidence_wall(page: ReadingPage) -> str:
    cards = "".join(
        f'<article class="evidence-card" data-anim="fade-up">{_render_block_inner(block, 150)}</article>'
        for block in page.blocks[:4]
    )
    return _render_shell(page, f'<div class="evidence-wall" data-stagger>{cards}</div>')


def _render_cost_blast(page: ReadingPage) -> str:
    cost_blocks = [block for block in page.blocks if block.kind == "cost"]
    other_blocks = [block for block in page.blocks if block.kind != "cost"]
    cards = "".join(
        f'<article class="cost-card" data-anim="fade-up">{_render_block_inner(block, 132)}</article>'
        for block in [*cost_blocks, *other_blocks][:4]
    )
    lead = cost_blocks[0] if cost_blocks else (page.blocks[0] if page.blocks else ReadingBlock("cost", "代价", page.thesis))
    body = f"""<div class="cost-blast">
  <section class="cost-number" data-anim="fade-left">
    <span>COST BLAST</span>
    <b>{escape(lead.title)}</b>
    <p class="reading-block-text">{escape(_clip_text(lead.text, 150))}</p>
  </section>
  <section class="cost-panel" data-anim="fade-right" data-stagger>{cards}</section>
</div>"""
    return _render_shell(page, body)


def _render_interrogation_room(page: ReadingPage) -> str:
    by_kind = {block.kind: block for block in page.blocks}
    attack = by_kind.get("attack", page.blocks[0] if page.blocks else ReadingBlock("attack", "质询", page.thesis))
    defense = by_kind.get("defense", page.blocks[1] if len(page.blocks) > 1 else ReadingBlock("defense", "回应", page.takeaway))
    center = by_kind.get("essence", ReadingBlock("essence", "核心盘问", page.thesis or page.title))
    body = f"""<div class="interrogation-room">
  <section class="clash-side attack" data-anim="fade-left">{_render_block(attack)}</section>
  <section class="clash-center" data-anim="scale-in"><h3>{escape(center.title)}</h3><p class="reading-block-text">{escape(_clip_text(center.text, 150))}</p></section>
  <section class="clash-side defense" data-anim="fade-right">{_render_block(defense)}</section>
</div>"""
    return _render_shell(page, body)


def _render_xray_diagnosis(page: ReadingPage) -> str:
    cards = "".join(
        f'<article class="xray-card" data-anim="fade-up">{_render_block_inner(block, 130)}</article>'
        for block in page.blocks[:4]
    )
    body = f"""<div class="xray-diagnosis">
  <section class="xray-core" data-anim="fade-left">
    <div class="reading-kicker">DIAGNOSIS</div>
    <h2>{escape(page.title)}</h2>
  </section>
  <section class="xray-grid" data-anim="fade-right" data-stagger>{cards}</section>
</div>"""
    return _render_shell(page, body)


def _render_clash_courtroom(page: ReadingPage) -> str:
    by_kind = {block.kind: block for block in page.blocks}
    attack = by_kind.get("attack", ReadingBlock("attack", "攻击方", ""))
    defense = by_kind.get("defense", ReadingBlock("defense", "回应方", ""))
    essence = by_kind.get("essence", ReadingBlock("essence", "冲突本质", "观点冲突"))
    body = f"""<div class="clash-courtroom">
  <section class="clash-side attack" data-anim="fade-left">{_render_block(attack)}</section>
  <section class="clash-center" data-anim="scale-in"><h3>{escape(essence.title)}</h3><p class="reading-block-text">{escape(essence.text)}</p></section>
  <section class="clash-side defense" data-anim="fade-right">{_render_block(defense)}</section>
</div>"""
    return _render_shell(page, body)


def _render_evolution_ladder(page: ReadingPage) -> str:
    cards = []
    for index, block in enumerate(page.blocks[:4], start=1):
        cards.append(f"""<article class="step-card" data-anim="fade-up">
  <div class="step-index">STEP {index:02d}</div>
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(_clip_text(block.text, 190))}</p>
</article>""")
    return _render_shell(page, f'<div class="evolution-ladder" data-stagger>{"".join(cards)}</div>')


def _render_tension_bars(page: ReadingPage) -> str:
    items = []
    for index, block in enumerate(page.blocks[:8], start=1):
        width = 48 + (index * 9) % 42
        items.append(f"""<article class="tension-item" data-anim="fade-up">
  <span class="reading-block-label">{escape(block.kind)}</span>
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(_clip_text(block.text, 125))}</p>
  <div class="bar"><span style="width:{width}%"></span></div>
</article>""")
    return _render_shell(page, f'<div class="tension-bars" data-stagger>{"".join(items)}</div>')


def _render_question_wall(page: ReadingPage) -> str:
    cards = []
    for block in page.blocks[:8]:
        cards.append(f"""<article class="question-card" data-anim="fade-up">
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(_clip_text(block.text, 150))}</p>
</article>""")
    return _render_shell(page, f'<div class="question-wall" data-stagger>{"".join(cards)}</div>')


def _render_block(block: ReadingBlock) -> str:
    label = f'<span class="reading-block-label">{escape(block.label)}</span>' if block.label else ""
    return f"""<article class="reading-block" data-kind="{escape(block.kind)}" data-anim="fade-up">
  {label}
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(_clip_text(block.text, 150))}</p>
</article>"""


def _render_block_inner(block: ReadingBlock, limit: int = 150) -> str:
    label = f'<span class="reading-block-label">{escape(block.label or block.kind)}</span>'
    return f"""{label}
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(_clip_text(block.text, limit))}</p>"""


def _render_stance_card(block: ReadingBlock) -> str:
    label = f'<span class="reading-block-label">{escape(block.label)}</span>' if block.label else ""
    return f"""<article class="reading-block stance-card" data-kind="{escape(block.kind)}" data-anim="scale-in">
  {label}
  <h3 class="reading-block-title">{escape(block.title)}</h3>
  <p class="reading-block-text">{escape(_clip_text(block.text, 112))}</p>
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


def _kicker(page: ReadingPage) -> str:
    return {
        "case_shock": "现实反噬",
        "round_opening": "回合开场",
        "cognitive_upgrade": "认知位移",
        "tension_map": "张力图谱",
        "open_questions": "开放问题",
    }.get(page.page_type, "阅读重点")


_LAYOUT_RENDERERS: dict[str, Callable[[ReadingPage], str]] = {
    "reading_brief_4zone": _render_reading_brief,
    "magazine_focus": _render_magazine_focus,
    "stance_spectrum": _render_stance_spectrum,
    "case_file": _render_case_file,
    "clash_courtroom": _render_clash_courtroom,
    "evolution_ladder": _render_evolution_ladder,
    "tension_bars": _render_tension_bars,
    "question_wall": _render_question_wall,
}


_VARIANT_RENDERERS: dict[str, Callable[[ReadingPage], str]] = {
    "shock_poster": _render_shock_poster,
    "evidence_wall": _render_evidence_wall,
    "cost_blast": _render_cost_blast,
    "interrogation_room": _render_interrogation_room,
    "xray_diagnosis": _render_xray_diagnosis,
    "delta_map": _render_evolution_ladder,
    "stance_radar": _render_stance_spectrum,
    "mechanism_cutaway": _render_tension_bars,
    "editorial_spread": _render_magazine_focus,
    "manifesto_poster": _render_magazine_focus,
    "quiet_notes": _render_question_wall,
}
