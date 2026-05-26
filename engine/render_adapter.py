#!/usr/bin/env python3
"""
圆桌洞见渲染适配器
将圆桌洞见 JSON 数据转换为各模板所需的 HTML
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

def sanitize_text(text: str) -> str:
    """清理文本，移除多余空白"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_expert_initial(name: str) -> str:
    """获取专家名字首字"""
    if not name:
        return "?"
    return name[0]

def get_expert_color(expert_id: str, colors: List[str]) -> str:
    """根据专家 ID 获取颜色"""
    hash_val = sum(ord(c) for c in expert_id)
    return colors[hash_val % len(colors)]

def adapt_to_consulting_report(data: Dict, colors: List[str]) -> str:
    """适配为咨询报告风格"""
    title = sanitize_text(data.get('title', ''))
    subtitle = sanitize_text(data.get('subtitle', ''))
    rounds = data.get('rounds', [])
    conclusions = data.get('conclusions', [])
    experts = data.get('experts', [])
    
    slides_html = []
    
    # 封面
    slides_html.append(f'''
<div class="slide slide-cover">
  <div class="cover-logo">圆桌洞见<span>Roundtable Insight</span></div>
  <div class="cover-body">
    <h1>{title}</h1>
    <p class="cover-sub">{subtitle}</p>
    <p class="cover-date">{len(experts)} 位专家 · {len(rounds)} 轮讨论</p>
  </div>
  <div class="cover-footer">本报告由 AI 专家圆桌生成</div>
</div>
''')
    
    # 专家介绍页
    if experts:
        expert_cards = ""
        for e in experts[:6]:
            name = sanitize_text(e.get('name', ''))
            initial = get_expert_initial(name)
            role = sanitize_text(e.get('role', ''))
            desc = sanitize_text(e.get('description', ''))[:60]
            expert_cards += f'''
    <div class="expert-card">
      <div class="expert-avatar">{initial}</div>
      <div class="expert-name">{name}</div>
      <div class="expert-role">{role}</div>
      <div class="expert-desc">{desc}...</div>
    </div>'''
        
        slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">专家阵容</div>
  <h2 class="slide-title">{title}</h2>
  <div class="experts-grid">{expert_cards}
  </div>
</div>
''')
    
    # 轮次内容
    for i, round_data in enumerate(rounds):
        round_num = i + 1
        question = sanitize_text(round_data.get('question', round_data.get('title', f'Round {round_num}')))
        
        # 标题页
        slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} / {len(rounds)}</div>
  <h2 class="slide-title">{question}</h2>
</div>
''')
        
        # 发言页
        stances = round_data.get('stances', [])
        if stances:
            cards_html = ""
            for s in stances[:3]:
                speaker = sanitize_text(s.get('speaker', s.get('name', '')))
                content = sanitize_text(s.get('content', s.get('stance', '')))
                role = sanitize_text(s.get('role', '发言'))
                initial = get_expert_initial(speaker)
                
                cards_html += f'''
        <div class="speech-card">
          <div class="speech-meta">
            <div class="speaker-avatar" style="background:{get_expert_color(speaker, colors)}">{initial}</div>
            <div>
              <div class="speaker-name">{speaker}</div>
              <div class="speaker-role">{role}</div>
            </div>
          </div>
          <div class="speech-content">{content}</div>
        </div>'''
            
            slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} 发言</div>
  <div class="speech-cards">{cards_html}
  </div>
</div>
''')
        
        # 碰撞页
        clashes = round_data.get('clashes', [])
        if clashes:
            clashes_html = ""
            for c in clashes[:3]:
                speaker = sanitize_text(c.get('speaker', ''))
                content = sanitize_text(c.get('content', ''))
                clashes_html += f'''
        <div class="clash-item">
          <div class="clash-speaker">{speaker}</div>
          <div class="clash-text">{content}</div>
        </div>'''
            
            slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} 碰撞</div>
  <div class="clash-block">{clashes_html}
  </div>
</div>
''')
        
        # 洞见页
        insight = round_data.get('insight', {})
        if insight:
            core = sanitize_text(insight.get('core', insight.get('summary', '')))
            explain = sanitize_text(insight.get('explain', insight.get('detail', '')))
            
            slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} 洞见</div>
  <div class="insight-block">
    <div class="insight-q">{core}</div>
    <div class="insight-a">{explain}</div>
  </div>
</div>
''')
    
    # 结论页
    if conclusions:
        conclusions_html = ""
        for i, c in enumerate(conclusions[:4]):
            text = sanitize_text(c.get('content', c.get('text', '')))
            conclusions_html += f'''
        <div class="conclusion-item">
          <div class="conclusion-num">{i+1}</div>
          <div class="conclusion-text">{text}</div>
        </div>'''
        
        slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">核心结论</div>
  <h2 class="slide-title">圆桌洞见总结</h2>
  <div class="conclusions-grid">{conclusions_html}
  </div>
</div>
''')
    
    return '\n'.join(slides_html)


def adapt_to_editorial(data: Dict, colors: List[str]) -> str:
    """适配为杂志编辑风格"""
    title = sanitize_text(data.get('title', ''))
    subtitle = sanitize_text(data.get('subtitle', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])
    
    slides_html = []
    
    # 封面
    slides_html.append(f'''
<div class="slide" id="s1">
  <div class="frame">
    <div class="left">
      <div class="issue">Roundtable Insight</div>
      <div class="mega">{title[:8]}</div>
      <div class="subtext">{subtitle}</div>
    </div>
    <div class="right">
      <div class="article-row">
        <div class="art-num">参与专家</div>
        <div class="art-title">{" / ".join([e.get('name', '')[:4] for e in experts[:4]])}</div>
        <div class="art-body">{len(experts)} 位专家 · {len(rounds)} 轮交锋</div>
      </div>
      <div class="article-row">
        <div class="art-num">核心议题</div>
        <div class="art-title">{rounds[0].get('question', '')[:20] if rounds else ''}...</div>
      </div>
    </div>
  </div>
</div>
''')
    
    # 轮次
    for i, round_data in enumerate(rounds):
        round_num = i + 1
        question = sanitize_text(round_data.get('question', f'Round {round_num}'))
        
        # 标题
        slides_html.append(f'''
<div class="slide" id="s{2+i*3}">
  <div class="content">
    <div class="head-block">
      <div class="head-title">{question}</div>
      <div class="head-tag">Round {round_num}</div>
    </div>
  </div>
</div>
''')
        
        # 发言
        stances = round_data.get('stances', [])
        if stances:
            cols_html = ""
            for s in stances[:3]:
                speaker = sanitize_text(s.get('speaker', s.get('name', '')))
                content = sanitize_text(s.get('content', s.get('stance', '')))[:150]
                initial = get_expert_initial(speaker)
                cols_html += f'''
        <div class="col">
          <div class="col-num">{initial}</div>
          <div class="col-title">{speaker}</div>
          <div class="col-body">{content}...</div>
        </div>'''
            
            slides_html.append(f'''
<div class="slide" id="s{3+i*3}">
  <div class="content">
    <div class="head-block">
      <div class="head-title">各方立场</div>
    </div>
    <div class="col-grid">{cols_html}
    </div>
  </div>
</div>
''')
        
        # 洞见
        insight = round_data.get('insight', {})
        if insight:
            core = sanitize_text(insight.get('core', insight.get('summary', '')))
            explain = sanitize_text(insight.get('explain', insight.get('detail', '')))
            
            slides_html.append(f'''
<div class="slide" id="s{4+i*3}">
  <div class="content">
    <div class="quote">
      {core[:60]}...
      <span class="highlight">{core[60:120] if len(core)>60 else ''}</span>
    </div>
    <div class="body">
      <p>{explain[:200]}</p>
    </div>
  </div>
</div>
''')
    
    return '\n'.join(slides_html)


def adapt_to_geek_report(data: Dict, colors: List[str]) -> str:
    """适配为极客风格"""
    title = sanitize_text(data.get('title', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])
    
    slides_html = []
    
    # 封面
    expert_list = " | ".join([e.get('name', '')[:4] for e in experts[:6]])
    slides_html.append(f'''
<div class="slide" id="s1">
  <div class="inner">
    <div class="slides">
      <div class="slide" id="s1-1">
        <div class="meta-line top">
          <span class="local-label">SYSTEM://ROUNDTABLE_INSIGHT</span>
          <span class="local-label">EXPERTS: {len(experts)}</span>
          <span class="local-label">ROUNDS: {len(rounds)}</span>
        </div>
        <div class="hero-zone">
          <div class="hero-label">ROUNDTABLE_INSIGHT</div>
          <div class="hero-title">{title[:20]}</div>
          <div class="hero-sub">{title[20:40] if len(title)>20 else ''}</div>
        </div>
        <div class="meta-line bottom">
          <span class="local-label">{expert_list}</span>
        </div>
      </div>
    </div>
  </div>
</div>
''')
    
    # 轮次
    for i, round_data in enumerate(rounds):
        round_num = i + 1
        question = sanitize_text(round_data.get('question', f'Round_{round_num}'))
        
        slides_html.append(f'''
<div class="slide" id="s{2+i*2}">
  <div class="inner">
    <div class="slides">
      <div class="slide" id="s{2+i*2}-1">
        <div class="meta-line top">
          <span class="local-label">ROUND_{round_num}/{len(rounds)}</span>
          <span class="local-label">QUESTION</span>
        </div>
        <div class="question-block">
          <div class="question-text">{question}</div>
        </div>
        <div class="meta-line bottom">
          <span class="local-label">ANALYSIS_MODE</span>
        </div>
      </div>
    </div>
  </div>
</div>
''')
        
        # 发言
        stances = round_data.get('stances', [])
        if stances:
            stances_html = ""
            for j, s in enumerate(stances[:4]):
                speaker = sanitize_text(s.get('speaker', s.get('name', '')))
                content = sanitize_text(s.get('content', s.get('stance', '')))[:100]
                role = sanitize_text(s.get('role', 'ANALYST'))
                stances_html += f'''
        <div class="statement-block">
          <div class="statement-meta">
            <span class="statement-speaker">{speaker.upper()[:3]}</span>
            <span class="statement-role">{role}</span>
          </div>
          <div class="statement-text">{content}...</div>
        </div>'''
            
            slides_html.append(f'''
<div class="slide" id="s{3+i*2}">
  <div class="inner">
    <div class="slides">
      <div class="slide" id="s{3+i*2}-1">
        <div class="meta-line top">
          <span class="local-label">ROUND_{round_num}</span>
          <span class="local-label">EXPERT_STANCES</span>
        </div>
        <div class="statements-grid">{stances_html}
        </div>
        <div class="meta-line bottom">
          <span class="local-label">CONTENT_LENGTH: {sum(len(s.get('content','')) for s in stances[:4])}</span>
        </div>
      </div>
    </div>
  </div>
</div>
''')
    
    return '\n'.join(slides_html)


def adapt_to_clean_review(data: Dict, colors: List[str]) -> str:
    """适配为简约测评风格"""
    title = sanitize_text(data.get('title', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])
    
    slides_html = []
    
    # 封面
    slides_html.append(f'''
<div class="slide" id="s1">
  <div class="frame">
    <div class="cover-header">
      <div class="cover-badge">圆桌洞见</div>
      <div class="cover-stats">
        <div class="cover-stat">
          <div class="cover-stat-num">{len(experts)}</div>
          <div class="cover-stat-label">专家</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">{len(rounds)}</div>
          <div class="cover-stat-label">轮次</div>
        </div>
      </div>
    </div>
    <div class="cover-title">{title}</div>
    <div class="cover-experts">
      {" / ".join([e.get('name', '') for e in experts[:6]])}
    </div>
  </div>
</div>
''')
    
    # 轮次
    for i, round_data in enumerate(rounds):
        round_num = i + 1
        question = sanitize_text(round_data.get('question', f'Round {round_num}'))
        
        slides_html.append(f'''
<div class="slide" id="s{2+i}">
  <div class="frame">
    <div class="section-header">
      <span class="section-tag">Round {round_num}</span>
      <span class="section-title">{question}</span>
    </div>
''')
        
        stances = round_data.get('stances', [])
        if stances:
            for j, s in enumerate(stances[:3]):
                speaker = sanitize_text(s.get('speaker', s.get('name', '')))
                content = sanitize_text(s.get('content', s.get('stance', '')))
                role = sanitize_text(s.get('role', ''))
                initial = get_expert_initial(speaker)
                
                slides_html.append(f'''
    <div class="review-card">
      <div class="review-header">
        <div class="review-avatar">{initial}</div>
        <div class="review-info">
          <div class="review-name">{speaker}</div>
          <div class="review-role">{role}</div>
        </div>
      </div>
      <div class="review-content">{content}</div>
    </div>
''')
        
        insight = round_data.get('insight', {})
        if insight:
            core = sanitize_text(insight.get('core', insight.get('summary', '')))
            slides_html.append(f'''
    <div class="insight-card">
      <div class="insight-label">核心洞见</div>
      <div class="insight-text">{core}</div>
    </div>
''')
        
        slides_html.append(f'''
  </div>
</div>
''')
    
    return '\n'.join(slides_html)


def adapt_to_rain_notes(data: Dict, colors: List[str]) -> str:
    """适配为雨天手记风格"""
    title = sanitize_text(data.get('title', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])
    
    slides_html = []
    
    # 封面
    slides_html.append(f'''
<div class="slide" id="s1">
  <div class="frame">
    <div class="paper-texture"></div>
    <div class="rain-overlay"></div>
    <div class="cover-content">
      <div class="cover-date">圆桌洞见</div>
      <h1 class="cover-title">{title}</h1>
      <div class="cover-meta">
        <span>{len(experts)} 位专家</span>
        <span>·</span>
        <span>{len(rounds)} 轮讨论</span>
      </div>
    </div>
  </div>
</div>
''')
    
    # 轮次
    for i, round_data in enumerate(rounds):
        round_num = i + 1
        question = sanitize_text(round_data.get('question', f'Round {round_num}'))
        
        slides_html.append(f'''
<div class="slide" id="s{2+i}">
  <div class="frame">
    <div class="paper-texture"></div>
    <div class="note-header">
      <span class="note-round">Round {round_num}</span>
    </div>
    <h2 class="note-question">{question}</h2>
''')
        
        stances = round_data.get('stances', [])
        if stances:
            notes_html = ""
            for j, s in enumerate(stances[:3]):
                speaker = sanitize_text(s.get('speaker', s.get('name', '')))
                content = sanitize_text(s.get('content', s.get('stance', '')))
                notes_html += f'''
      <div class="note-entry">
        <div class="note-speaker">{speaker}</div>
        <div class="note-content">{content}</div>
      </div>'''
            
            slides_html.append(f'''
    <div class="notes-container">{notes_html}
    </div>
''')
        
        insight = round_data.get('insight', {})
        if insight:
            core = sanitize_text(insight.get('core', insight.get('summary', '')))
            slides_html.append(f'''
    <div class="rain-insight">
      <div class="insight-marker">~</div>
      <div class="insight-text">{core}</div>
    </div>
''')
        
        slides_html.append(f'''
  </div>
</div>
''')
    
    return '\n'.join(slides_html)


# 模板适配器注册表
ADAPTERS = {
    'consulting-report': adapt_to_consulting_report,
    'editorial': adapt_to_editorial,
    'geek-report': adapt_to_geek_report,
    'clean-review': adapt_to_clean_review,
    'rain-notes': adapt_to_rain_notes,
    # 更多模板可继续添加...
}


def adapt(data: Dict, template_id: str) -> str:
    """适配数据到指定模板"""
    adapter = ADAPTERS.get(template_id)
    if adapter:
        return adapter(data, ['#c23b22', '#4a6a9a', '#3a8a5c', '#d4a843', '#8a4aaa', '#e85d3a'])
    return adapt_to_consulting_report(data, ['#c23b22', '#4a6a9a', '#3a8a5c', '#d4a843', '#8a4aaa', '#e85d3a'])


def render(data: Dict, template_id: str, template_html: str) -> str:
    """使用适配后的内容渲染模板"""
    slides_html = adapt(data, template_id)
    
    # 替换模板中的占位符
    html = template_html
    html = html.replace('{{slides}}', slides_html)
    html = html.replace('{{title}}', sanitize_text(data.get('title', '圆桌洞见')))
    html = html.replace('{{subtitle}}', sanitize_text(data.get('subtitle', '')))
    
    return html
