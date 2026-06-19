# -*- coding: utf-8 -*-
"""统一修复所有模板 - 翻页逻辑 + 禁止滚动 + 设计优化"""

import os
import re
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"

STANDARD_JS = '''
<script>
(function(){
  const slides=document.querySelectorAll('.slide');
  const total=slides.length;
  let cur=0;
  const dotsContainer=document.getElementById('dots');
  const counter=document.getElementById('counter');
  const progress=document.getElementById('progressBar');
  const isHorizontal=document.body.style.flexDirection==='row'||document.documentElement.style.scrollSnapType?.includes('x');

  slides.forEach((s,i)=>{
    const dot=document.createElement('div');
    dot.className='dot'+(i===0?' active':'');
    dot.onclick=()=>go(i);
    dotsContainer.appendChild(dot);
  });

  function go(n){
    if(n<0||n>=total)return;
    slides[cur].classList.remove('visible');
    dotsContainer.children[cur]?.classList.remove('active');
    cur=n;
    slides[cur].scrollIntoView({behavior:'smooth',block:'start',inline:'start'});
    slides[cur].classList.add('visible');
    dotsContainer.children[cur]?.classList.add('active');
    if(counter)counter.textContent=(cur+1)+' / '+total;
    if(progress){const pct=Math.min(100,((cur+1)/total)*100);progress.style.width=pct+'%';}
  }

  document.getElementById('prevBtn')?.addEventListener('click',()=>go(cur-1));
  document.getElementById('nextBtn')?.addEventListener('click',()=>go(cur+1));

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
    if(e.target.closest('.nav-dot,.dots,.nav-btn,.expert-card,.speech-card,.clash-block,.insight-block,.question-card,.conclusion-item,.stat-item,.card'))return;
    go(cur+1);
  });

  go(0);
})();
</script>'''

CSS_FIXES = {
    'overflow_hidden': '''
.slide{overflow:hidden}''',
    'slide_height': '''
.slide{height:100vh;min-height:100vh}''',
    'body_scroll': '''
html,body{overflow:hidden}''',
}

def fix_template(file_path: Path) -> bool:
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    content = re.sub(r'overflow-y:\s*auto', 'overflow:hidden', content)
    content = re.sub(r'overflow-y:\s*scroll', 'overflow:hidden', content)
    content = re.sub(r'overflow:\s*auto', 'overflow:hidden', content)
    
    if '.slide{' in content and 'overflow:hidden' not in content.split('.slide{')[1].split('}')[0]:
        content = re.sub(r'(\.slide\s*\{)', r'\1overflow:hidden;', content)
    
    if 'height:100vh' not in content and '.slide{' in content:
        content = re.sub(r'(\.slide\s*\{[^}]*)(position)', r'\1height:100vh;\2', content)
    
    js_pattern = r'<script>\s*\([^)]*\)\s*\{[^}]*slides[^}]*\}[^}]*\)\s*\(\s*\)\s*;?\s*</script>'
    content = re.sub(js_pattern, STANDARD_JS, content, flags=re.DOTALL)
    
    if '<script>' not in content or 'slides=document.querySelectorAll' not in content:
        if '</body>' in content:
            content = content.replace('</body>', STANDARD_JS + '\n</body>')
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def batch_fix():
    templates = list(ENGINE_DIR.glob('template-*.html'))
    print(f"Found {len(templates)} templates")
    print("=" * 60)
    
    fixed = 0
    for t in sorted(templates):
        if fix_template(t):
            fixed += 1
            print(f"✓ Fixed: {t.name}")
        else:
            print(f"  Skip: {t.name}")
    
    print("=" * 60)
    print(f"Fixed {fixed}/{len(templates)} templates")

if __name__ == "__main__":
    batch_fix()