# -*- coding: utf-8 -*-
"""
V8 JSON → HTML-PPT Renderer

Converts V8 roundtable discussion JSON into a self-contained HTML slideshow
with horizontal scroll-snap layout, keyboard/mouse navigation, and multiple
color themes.

Usage:
    python html_renderer.py input.json output.html --theme gold
"""

import json
import html as html_mod
import argparse
from typing import Dict, List, Optional
from pathlib import Path


# ─── Theme definitions ───────────────────────────────────────────────────────

THEMES = {
    'gold': {
        'accent': '#D4A04A',
        'accent_light': '#E8C47A',
        'accent_dark': '#B8862D',
        'clash': '#ff4757',
        'insight': '#00d4aa',
        'gradient_start': '#D4A04A',
        'gradient_end': '#F0D68A',
        'card_bg': 'rgba(212,160,74,0.08)',
        'card_border': 'rgba(212,160,74,0.2)',
        'glow': 'rgba(212,160,74,0.3)',
    },
    'acid': {
        'accent': '#00E676',
        'accent_light': '#69F0AE',
        'accent_dark': '#00C853',
        'clash': '#FF5252',
        'insight': '#00BFA5',
        'gradient_start': '#00E676',
        'gradient_end': '#B2FF59',
        'card_bg': 'rgba(0,230,118,0.08)',
        'card_border': 'rgba(0,230,118,0.2)',
        'glow': 'rgba(0,230,118,0.3)',
    },
    'warm': {
        'accent': '#FF6B9D',
        'accent_light': '#FF8AB5',
        'accent_dark': '#E5537A',
        'clash': '#FF4081',
        'insight': '#FF80AB',
        'gradient_start': '#FF6B9D',
        'gradient_end': '#FFB74D',
        'card_bg': 'rgba(255,107,157,0.08)',
        'card_border': 'rgba(255,107,157,0.2)',
        'glow': 'rgba(255,107,157,0.3)',
    },
}

DEFAULT_AVATAR_COLORS = [
    '#D4A04A', '#5B8DEF', '#E5537A', '#00d4aa',
    '#FF9F43', '#A55EEA', '#48DBFB', '#FF6B6B',
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """HTML-escape text."""
    return html_mod.escape(str(text)) if text else ''


def _avatar_color(expert: dict, idx: int) -> str:
    """Get avatar color from expert dict or fallback to default."""
    c = expert.get('avatar_color', '')
    if c and c.startswith('#'):
        return c
    return DEFAULT_AVATAR_COLORS[idx % len(DEFAULT_AVATAR_COLORS)]


def _expert_initial(name: str) -> str:
    """Get first character(s) for avatar display."""
    if not name:
        return '?'
    # For Chinese names, take first char; for English, take initials
    parts = name.strip().split()
    if len(parts) > 1:
        return ''.join(p[0].upper() for p in parts[:2])
    return name[0]


def _stance_label(stance: str) -> str:
    """Map stance enum to display label."""
    mapping = {
        'support': '支持',
        'oppose': '反对',
        'neutral': '中立',
        'complex': '复杂',
    }
    return mapping.get(stance, stance)


# ─── Slide builders ──────────────────────────────────────────────────────────

def _build_cover(data: dict, t: dict) -> str:
    title = _esc(data.get('title', '圆桌讨论'))
    subtitle = _esc(data.get('subtitle', ''))
    experts = data.get('experts', [])
    rounds = data.get('rounds', [])
    books = data.get('books', [])

    expert_names = ' · '.join(_esc(e['name']) for e in experts)
    book_line = ''
    if books:
        book_line = f'<div class="cover-books">基于 {"、".join(_esc(b["name"]) + " — " + _esc(b["author"]) for b in books)}</div>'

    return f'''
    <div class="slide cover-slide">
      <div class="cover-glow"></div>
      <div class="cover-content">
        <div class="cover-badge">ROUNDTABLE DISCUSSION</div>
        <h1 class="cover-title">{title}</h1>
        {f'<p class="cover-subtitle">{subtitle}</p>' if subtitle else ''}
        {book_line}
        <div class="cover-stats">
          <div class="cover-stat">
            <span class="cover-stat-num">{len(experts)}</span>
            <span class="cover-stat-label">位专家</span>
          </div>
          <div class="cover-stat-divider"></div>
          <div class="cover-stat">
            <span class="cover-stat-num">{len(rounds)}</span>
            <span class="cover-stat-label">轮讨论</span>
          </div>
        </div>
        <div class="cover-experts">{expert_names}</div>
      </div>
    </div>'''


def _build_expert_grid(data: dict, t: dict) -> str:
    experts = data.get('experts', [])
    cards = ''
    for i, e in enumerate(experts):
        color = _avatar_color(e, i)
        name = _esc(e.get('name', ''))
        title = _esc(e.get('title', ''))
        belief = _esc(e.get('core_belief', ''))
        stance = _stance_label(e.get('stance', ''))
        initial = _expert_initial(name)

        cards += f'''
        <div class="expert-card" style="--card-color: {color}">
          <div class="expert-avatar" style="background: {color}">{initial}</div>
          <div class="expert-info">
            <div class="expert-name">{name}</div>
            <div class="expert-title">{title}</div>
            <div class="expert-stance">{stance}</div>
            <div class="expert-belief">{belief}</div>
          </div>
        </div>'''

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">EXPERTS</span>
        <h2 class="slide-title">专家阵营</h2>
      </div>
      <div class="expert-grid">{cards}
      </div>
    </div>'''


def _build_question_slide(round_data: dict, t: dict) -> str:
    rnum = round_data.get('round_number', '?')
    topic = _esc(round_data.get('topic', ''))
    question = _esc(round_data.get('core_question', ''))

    return f'''
    <div class="slide question-slide">
      <div class="question-glow"></div>
      <div class="question-content">
        <span class="slide-tag">ROUND {rnum}</span>
        <h2 class="question-topic">{topic}</h2>
        <div class="question-divider"></div>
        <p class="question-text">{question}</p>
      </div>
    </div>'''


def _build_stances_slide(stances_batch: list, round_num: int, batch_idx: int, total_batches: int, experts_map: dict, t: dict) -> str:
    items = ''
    for s in stances_batch:
        expert_name = s.get('expert', s.get('speaker', ''))
        text = _esc(s.get('text', s.get('stance', s.get('speech', s.get('content', '')))))
        color = experts_map.get(expert_name, t['accent'])
        initial = _expert_initial(expert_name)

        items += f'''
        <div class="stance-item">
          <div class="stance-avatar" style="background: {color}">{initial}</div>
          <div class="stance-body">
            <div class="stance-speaker">{_esc(expert_name)}</div>
            <div class="stance-text">{text}</div>
          </div>
        </div>'''

    page_info = f' ({batch_idx + 1}/{total_batches})' if total_batches > 1 else ''

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">ROUND {round_num} · 立场</span>
        <h2 class="slide-title">各抒己见{page_info}</h2>
      </div>
      <div class="stances-container">{items}
      </div>
    </div>'''


def _build_clash_slide(round_data: dict, experts_map: dict, t: dict) -> str:
    rnum = round_data.get('round_number', '?')
    clashes = round_data.get('clash_rounds', [])

    clash_html = ''
    for i, c in enumerate(clashes):
        attacker = c.get('attacker', '')
        target = c.get('target', '')
        attack = _esc(c.get('attack_content', ''))
        counter = _esc(c.get('counter_attack', ''))

        atk_color = experts_map.get(attacker, t['clash'])
        tgt_color = experts_map.get(target, t['accent'])

        counter_html = ''
        if counter:
            counter_html = f'''
            <div class="clash-item clash-counter">
              <div class="clash-speaker" style="color: {tgt_color}">{_esc(target)}</div>
              <div class="clash-text">{counter}</div>
            </div>'''

        clash_html += f'''
        <div class="clash-block">
          <div class="clash-label">碰撞交锋 #{i + 1}</div>
          <div class="clash-item clash-attack">
            <div class="clash-speaker" style="color: {atk_color}">{_esc(attacker)} → {_esc(target)}</div>
            <div class="clash-text">{attack}</div>
          </div>
          {counter_html}
        </div>'''

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">ROUND {rnum} · 碰撞</span>
        <h2 class="slide-title">激烈交锋</h2>
      </div>
      <div class="clash-container">{clash_html}
      </div>
    </div>'''


def _build_reality_case_slide(round_data: dict, t: dict) -> str:
    rnum = round_data.get('round_number', '?')
    cases = round_data.get('reality_cases', [])
    # Normalize: if dict (single case), wrap in list
    if isinstance(cases, dict):
        cases = [cases]
    if not cases:
        return ''

    cases_html = ''
    for c in cases:
        name = _esc(c.get('case_name', ''))
        source = _esc(c.get('case_source', ''))
        content = _esc(c.get('case_content', ''))
        outcome = _esc(c.get('case_outcome', ''))
        lesson = _esc(c.get('case_lesson', ''))

        cases_html += f'''
        <div class="case-card">
          <div class="case-header">
            <div class="case-name">{name}</div>
            <div class="case-source">{source}</div>
          </div>
          <div class="case-content">{content}</div>
          <div class="case-outcome">
            <span class="case-label">结果</span> {outcome}
          </div>
          <div class="case-lesson">
            <span class="case-label">教训</span> {lesson}
          </div>
        </div>'''

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">ROUND {rnum} · 现实</span>
        <h2 class="slide-title">现实案例</h2>
      </div>
      <div class="cases-container">{cases_html}
      </div>
    </div>'''


def _build_cost_slide(round_data: dict, t: dict) -> str:
    cost = round_data.get('cost_discussion')
    if not cost:
        return ''

    rnum = round_data.get('round_number', '?')
    scenario = _esc(cost.get('scenario', ''))
    worst = _esc(cost.get('worst_case', ''))
    survivor = _esc(cost.get('survivor_bias', ''))

    analysis_html = ''
    for item in cost.get('cost_analysis', []):
        if isinstance(item, dict):
            label = _esc(item.get('dimension', item.get('label', item.get('name', ''))))
            value = _esc(item.get('analysis', item.get('value', item.get('text', ''))))
        else:
            label = ''
            value = _esc(str(item))
        analysis_html += f'''
        <div class="cost-item">
          <div class="cost-dimension">{label}</div>
          <div class="cost-value">{value}</div>
        </div>'''

    survivor_html = ''
    if survivor:
        survivor_html = f'''
        <div class="cost-survivor">
          <div class="cost-survivor-label">幸存者偏差</div>
          <div class="cost-survivor-text">{survivor}</div>
        </div>'''

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">ROUND {rnum} · 代价</span>
        <h2 class="slide-title">代价分析</h2>
      </div>
      <div class="cost-container">
        <div class="cost-scenario">
          <span class="cost-scenario-label">假设场景</span>
          <span class="cost-scenario-text">{scenario}</span>
        </div>
        <div class="cost-analysis">{analysis_html}
        </div>
        <div class="cost-worst">
          <span class="cost-worst-label">最坏情况</span>
          <span class="cost-worst-text">{worst}</span>
        </div>
        {survivor_html}
      </div>
    </div>'''


def _build_human_nature_slide(round_data: dict, t: dict) -> str:
    hn = round_data.get('human_nature')
    if not hn:
        return ''

    rnum = round_data.get('round_number', '?')
    question = _esc(hn.get('question', ''))
    analysis = _esc(hn.get('psychological_analysis', ''))
    conclusion = _esc(hn.get('conclusion', ''))

    examples_html = ''
    for ex in hn.get('real_examples', []):
        examples_html += f'<div class="hn-example">{_esc(ex)}</div>'

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">ROUND {rnum} · 人性</span>
        <h2 class="slide-title">人性深处</h2>
      </div>
      <div class="hn-container">
        <div class="hn-question">{question}</div>
        <div class="hn-analysis">{analysis}</div>
        <div class="hn-examples">{examples_html}
        </div>
        <div class="hn-conclusion">
          <span class="hn-conclusion-label">结论</span>
          <span class="hn-conclusion-text">{conclusion}</span>
        </div>
      </div>
    </div>'''


def _build_upgrade_slide(round_data: dict, t: dict) -> str:
    upgrade = round_data.get('cognitive_upgrade')
    if not upgrade:
        return ''

    rnum = round_data.get('round_number', '?')
    old_thinking = _esc(upgrade.get('old_thinking', ''))
    new_thinking = _esc(upgrade.get('new_thinking', ''))
    complexity = _esc(upgrade.get('complexity', ''))
    actionable = _esc(upgrade.get('actionable_insight', ''))

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">ROUND {rnum} · 升级</span>
        <h2 class="slide-title">认知升级</h2>
      </div>
      <div class="upgrade-container">
        <div class="upgrade-block">
          <div class="upgrade-before">
            <div class="upgrade-label">旧思维</div>
            <div class="upgrade-text">{old_thinking}</div>
          </div>
          <div class="upgrade-arrow">→</div>
          <div class="upgrade-after">
            <div class="upgrade-label">新思维</div>
            <div class="upgrade-text">{new_thinking}</div>
          </div>
        </div>
        <div class="upgrade-complexity">
          <span class="upgrade-complexity-label">复杂性</span>
          <span class="upgrade-complexity-text">{complexity}</span>
        </div>
        <div class="upgrade-actionable">
          <span class="upgrade-actionable-label">可执行洞见</span>
          <span class="upgrade-actionable-text">{actionable}</span>
        </div>
      </div>
    </div>'''


def _build_final_insight(data: dict, t: dict) -> str:
    insight = _esc(data.get('final_insight', ''))
    return f'''
    <div class="slide insight-slide">
      <div class="insight-glow"></div>
      <div class="insight-content">
        <span class="slide-tag">FINAL INSIGHT</span>
        <h2 class="insight-title">最终洞见</h2>
        <div class="insight-divider"></div>
        <p class="insight-text">{insight}</p>
      </div>
    </div>'''


def _build_open_questions(data: dict, t: dict) -> str:
    questions = data.get('open_questions', [])
    items = ''
    for i, q in enumerate(questions):
        items += f'''
        <div class="oq-item">
          <div class="oq-num">{i + 1}</div>
          <div class="oq-text">{_esc(q)}</div>
        </div>'''

    return f'''
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">OPEN QUESTIONS</span>
        <h2 class="slide-title">开放问题</h2>
      </div>
      <div class="oq-container">{items}
      </div>
    </div>'''


# ─── CSS / JS templates ─────────────────────────────────────────────────────

def _build_css(t: dict) -> str:
    return f'''
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #0A0A0A;
      --bg2: #111111;
      --bg3: #1A1A1A;
      --text: #F5F5F5;
      --text2: #A0A0A0;
      --text3: #606060;
      --accent: {t['accent']};
      --accent-light: {t['accent_light']};
      --accent-dark: {t['accent_dark']};
      --clash: {t['clash']};
      --insight: {t['insight']};
      --card-bg: {t['card_bg']};
      --card-border: {t['card_border']};
      --glow: {t['glow']};
      --slide-w: 100vw;
      --slide-h: 100vh;
      --font-display: 'Noto Serif SC', serif;
      --font-body: 'Outfit', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    html {{ font-size: 16px; scroll-behavior: auto; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-body);
      overflow-x: hidden;
      overflow-y: hidden;
      height: 100vh;
      -webkit-font-smoothing: antialiased;
    }}

    /* ─── Slideshow container ─── */
    .slideshow {{
      display: flex;
      width: 100vw;
      height: 100vh;
      overflow-x: auto;
      overflow-y: hidden;
      scroll-snap-type: x mandatory;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
    }}
    .slideshow::-webkit-scrollbar {{ display: none; }}
    .slideshow {{ -ms-overflow-style: none; scrollbar-width: none; }}

    /* ─── Slide ─── */
    .slide {{
      flex: 0 0 var(--slide-w);
      width: var(--slide-w);
      height: var(--slide-h);
      scroll-snap-align: start;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      align-items: center;
      padding: 3rem 5rem;
      position: relative;
      overflow-y: auto;
      overflow-x: hidden;
    }}
    .slide::-webkit-scrollbar {{ width: 3px; }}
    .slide::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.15); border-radius: 2px; }}
    .slide::-webkit-scrollbar-track {{ background: transparent; }}

    /* ─── Progress bar ─── */
    .progress-bar {{
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent-light));
      z-index: 1000;
      transition: width 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
      box-shadow: 0 0 10px var(--glow);
    }}

    /* ─── Page counter ─── */
    .page-counter {{
      position: fixed;
      top: 1.5rem;
      right: 2rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      color: var(--text3);
      z-index: 1000;
      letter-spacing: 0.05em;
    }}

    /* ─── Nav dots ─── */
    .nav-dots {{
      position: fixed;
      bottom: 1.5rem;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      gap: 8px;
      z-index: 1000;
      padding: 8px 16px;
      background: rgba(10,10,10,0.8);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      border: 1px solid rgba(255,255,255,0.06);
    }}
    .nav-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--text3);
      cursor: pointer;
      transition: all 0.3s ease;
      border: none;
      outline: none;
    }}
    .nav-dot:hover {{ background: var(--text2); transform: scale(1.3); }}
    .nav-dot.active {{
      background: var(--accent);
      box-shadow: 0 0 8px var(--glow);
      transform: scale(1.2);
    }}

    /* ─── Slide header ─── */
    .slide-header {{
      width: 100%;
      max-width: 1000px;
      margin-bottom: 2.5rem;
    }}
    .slide-tag {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.15em;
      color: var(--accent);
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 4px 12px;
      border-radius: 4px;
      margin-bottom: 0.75rem;
    }}
    .slide-title {{
      font-family: var(--font-display);
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--text);
      line-height: 1.3;
    }}

    /* ─── Cover slide ─── */
    .cover-slide {{
      background: radial-gradient(ellipse at 30% 50%, rgba(20,20,20,1) 0%, var(--bg) 70%);
    }}
    .cover-glow {{
      position: absolute;
      top: 50%;
      left: 30%;
      width: 500px;
      height: 500px;
      background: radial-gradient(circle, var(--glow) 0%, transparent 70%);
      transform: translate(-50%, -50%);
      opacity: 0.4;
      pointer-events: none;
    }}
    .cover-content {{
      text-align: center;
      position: relative;
      z-index: 1;
    }}
    .cover-badge {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      letter-spacing: 0.3em;
      color: var(--accent);
      margin-bottom: 2rem;
    }}
    .cover-title {{
      font-family: var(--font-display);
      font-size: 3.2rem;
      font-weight: 700;
      color: var(--text);
      line-height: 1.3;
      margin-bottom: 1rem;
      max-width: 700px;
    }}
    .cover-subtitle {{
      font-size: 1.1rem;
      color: var(--text2);
      margin-bottom: 1.5rem;
    }}
    .cover-books {{
      font-size: 0.9rem;
      color: var(--text3);
      margin-bottom: 2rem;
      font-style: italic;
    }}
    .cover-stats {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2rem;
      margin-bottom: 2.5rem;
    }}
    .cover-stat {{
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .cover-stat-num {{
      font-family: var(--font-display);
      font-size: 3rem;
      font-weight: 700;
      color: var(--accent);
    }}
    .cover-stat-label {{
      font-size: 0.85rem;
      color: var(--text3);
      margin-top: 0.25rem;
    }}
    .cover-stat-divider {{
      width: 1px;
      height: 40px;
      background: var(--text3);
      opacity: 0.3;
    }}
    .cover-experts {{
      font-size: 0.9rem;
      color: var(--text2);
      letter-spacing: 0.05em;
    }}

    /* ─── Expert grid ─── */
    .expert-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
      width: 100%;
      max-width: 1000px;
    }}
    .expert-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      gap: 1rem;
      align-items: flex-start;
      transition: all 0.3s ease;
    }}
    .expert-card:hover {{
      border-color: var(--card-color, var(--accent));
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      transform: translateY(-2px);
    }}
    .expert-avatar {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-display);
      font-size: 1.2rem;
      font-weight: 700;
      color: #0A0A0A;
      flex-shrink: 0;
    }}
    .expert-info {{
      flex: 1;
      min-width: 0;
    }}
    .expert-name {{
      font-family: var(--font-display);
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 0.25rem;
    }}
    .expert-title {{
      font-size: 0.75rem;
      color: var(--text3);
      margin-bottom: 0.5rem;
    }}
    .expert-stance {{
      display: inline-block;
      font-size: 0.65rem;
      font-family: var(--font-mono);
      color: var(--accent);
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 2px 8px;
      border-radius: 3px;
      margin-bottom: 0.5rem;
    }}
    .expert-belief {{
      font-size: 0.8rem;
      color: var(--text2);
      line-height: 1.5;
    }}

    /* ─── Question slide ─── */
    .question-slide {{
      background: radial-gradient(ellipse at 50% 50%, rgba(20,20,20,1) 0%, var(--bg) 70%);
    }}
    .question-glow {{
      position: absolute;
      top: 50%;
      left: 50%;
      width: 600px;
      height: 600px;
      background: radial-gradient(circle, var(--glow) 0%, transparent 70%);
      transform: translate(-50%, -50%);
      opacity: 0.3;
      pointer-events: none;
    }}
    .question-content {{
      text-align: center;
      position: relative;
      z-index: 1;
      max-width: 800px;
    }}
    .question-topic {{
      font-family: var(--font-display);
      font-size: 2.8rem;
      font-weight: 700;
      color: var(--text);
      margin: 1.5rem 0;
      line-height: 1.3;
    }}
    .question-divider {{
      width: 60px;
      height: 3px;
      background: var(--accent);
      margin: 1.5rem auto;
      border-radius: 2px;
    }}
    .question-text {{
      font-size: 1.15rem;
      color: var(--text2);
      line-height: 1.8;
    }}

    /* ─── Stances ─── */
    .stances-container {{
      width: 100%;
      max-width: 1000px;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }}
    .stance-item {{
      display: flex;
      gap: 1.25rem;
      align-items: flex-start;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      transition: all 0.3s ease;
    }}
    .stance-item:hover {{
      border-color: var(--accent);
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    .stance-avatar {{
      width: 44px;
      height: 44px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-display);
      font-size: 1rem;
      font-weight: 700;
      color: #0A0A0A;
      flex-shrink: 0;
    }}
    .stance-body {{
      flex: 1;
    }}
    .stance-speaker {{
      font-family: var(--font-display);
      font-weight: 600;
      font-size: 1rem;
      color: var(--text);
      margin-bottom: 0.5rem;
    }}
    .stance-text {{
      font-size: 0.95rem;
      color: var(--text2);
      line-height: 1.7;
    }}

    /* ─── Clash ─── */
    .clash-container {{
      width: 100%;
      max-width: 1000px;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }}
    .clash-block {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      position: relative;
    }}
    .clash-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--clash);
      letter-spacing: 0.1em;
      margin-bottom: 1rem;
    }}
    .clash-item {{
      margin-bottom: 1rem;
    }}
    .clash-item:last-child {{ margin-bottom: 0; }}
    .clash-speaker {{
      font-family: var(--font-display);
      font-weight: 600;
      font-size: 0.95rem;
      margin-bottom: 0.5rem;
    }}
    .clash-text {{
      font-size: 0.9rem;
      color: var(--text2);
      line-height: 1.7;
      padding-left: 1rem;
      border-left: 2px solid var(--card-border);
    }}
    .clash-attack .clash-text {{
      border-left-color: var(--clash);
    }}
    .clash-counter .clash-text {{
      border-left-color: var(--insight);
    }}

    /* ─── Reality cases ─── */
    .cases-container {{
      width: 100%;
      max-width: 1000px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
    }}
    .case-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      transition: all 0.3s ease;
    }}
    .case-card:hover {{
      border-color: var(--accent);
      transform: translateY(-2px);
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    .case-header {{
      margin-bottom: 1rem;
    }}
    .case-name {{
      font-family: var(--font-display);
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text);
    }}
    .case-source {{
      font-size: 0.75rem;
      color: var(--text3);
      margin-top: 0.25rem;
    }}
    .case-content {{
      font-size: 0.9rem;
      color: var(--text2);
      line-height: 1.7;
      margin-bottom: 1rem;
    }}
    .case-outcome, .case-lesson {{
      font-size: 0.85rem;
      color: var(--text2);
      line-height: 1.6;
      margin-bottom: 0.75rem;
    }}
    .case-label {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 0.65rem;
      color: var(--accent);
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 2px 6px;
      border-radius: 3px;
      margin-right: 0.5rem;
    }}

    /* ─── Cost discussion ─── */
    .cost-container {{
      width: 100%;
      max-width: 1000px;
    }}
    .cost-scenario {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.5rem;
    }}
    .cost-scenario-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--accent);
      display: block;
      margin-bottom: 0.5rem;
    }}
    .cost-scenario-text {{
      font-size: 0.95rem;
      color: var(--text2);
      line-height: 1.7;
    }}
    .cost-analysis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .cost-item {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1.25rem;
    }}
    .cost-dimension {{
      font-family: var(--font-display);
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 0.5rem;
    }}
    .cost-value {{
      font-size: 0.85rem;
      color: var(--text2);
      line-height: 1.6;
    }}
    .cost-worst {{
      background: rgba(255,71,87,0.08);
      border: 1px solid rgba(255,71,87,0.2);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.5rem;
    }}
    .cost-worst-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--clash);
      display: block;
      margin-bottom: 0.5rem;
    }}
    .cost-worst-text {{
      font-size: 0.95rem;
      color: var(--text2);
      line-height: 1.7;
    }}
    .cost-survivor {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
    }}
    .cost-survivor-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--accent);
      display: block;
      margin-bottom: 0.5rem;
    }}
    .cost-survivor-text {{
      font-size: 0.9rem;
      color: var(--text2);
      line-height: 1.7;
    }}

    /* ─── Human nature ─── */
    .hn-container {{
      width: 100%;
      max-width: 1000px;
    }}
    .hn-question {{
      font-family: var(--font-display);
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 1.5rem;
      text-align: center;
    }}
    .hn-analysis {{
      font-size: 0.95rem;
      color: var(--text2);
      line-height: 1.8;
      margin-bottom: 1.5rem;
      padding: 1.25rem 1.5rem;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
    }}
    .hn-examples {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .hn-example {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1.25rem;
      font-size: 0.85rem;
      color: var(--text2);
      line-height: 1.6;
    }}
    .hn-conclusion {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
    }}
    .hn-conclusion-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--accent);
      display: block;
      margin-bottom: 0.5rem;
    }}
    .hn-conclusion-text {{
      font-size: 0.95rem;
      color: var(--text2);
      line-height: 1.7;
    }}

    /* ─── Cognitive upgrade ─── */
    .upgrade-container {{
      width: 100%;
      max-width: 1000px;
    }}
    .upgrade-block {{
      display: flex;
      gap: 1.5rem;
      align-items: stretch;
      margin-bottom: 1.5rem;
    }}
    .upgrade-before, .upgrade-after {{
      flex: 1;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .upgrade-before {{
      border-color: rgba(255,71,87,0.2);
      background: rgba(255,71,87,0.05);
    }}
    .upgrade-after {{
      border-color: rgba(0,212,170,0.2);
      background: rgba(0,212,170,0.05);
    }}
    .upgrade-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      letter-spacing: 0.1em;
      margin-bottom: 0.75rem;
    }}
    .upgrade-before .upgrade-label {{ color: var(--clash); }}
    .upgrade-after .upgrade-label {{ color: var(--insight); }}
    .upgrade-text {{
      font-size: 0.95rem;
      color: var(--text2);
      line-height: 1.7;
    }}
    .upgrade-arrow {{
      display: flex;
      align-items: center;
      font-size: 2rem;
      color: var(--accent);
      flex-shrink: 0;
    }}
    .upgrade-complexity, .upgrade-actionable {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1rem;
    }}
    .upgrade-complexity-label, .upgrade-actionable-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--accent);
      display: block;
      margin-bottom: 0.5rem;
    }}
    .upgrade-complexity-text, .upgrade-actionable-text {{
      font-size: 0.9rem;
      color: var(--text2);
      line-height: 1.7;
    }}

    /* ─── Final insight ─── */
    .insight-slide {{
      background: radial-gradient(ellipse at 50% 50%, rgba(0,212,170,0.05) 0%, var(--bg) 60%);
    }}
    .insight-glow {{
      position: absolute;
      top: 50%;
      left: 50%;
      width: 600px;
      height: 600px;
      background: radial-gradient(circle, rgba(0,212,170,0.15) 0%, transparent 70%);
      transform: translate(-50%, -50%);
      pointer-events: none;
    }}
    .insight-content {{
      text-align: center;
      position: relative;
      z-index: 1;
      max-width: 800px;
    }}
    .insight-title {{
      font-family: var(--font-display);
      font-size: 2.5rem;
      font-weight: 700;
      color: var(--insight);
      margin: 1.5rem 0;
    }}
    .insight-divider {{
      width: 60px;
      height: 3px;
      background: var(--insight);
      margin: 1.5rem auto;
      border-radius: 2px;
    }}
    .insight-text {{
      font-size: 1.1rem;
      color: var(--text2);
      line-height: 1.9;
    }}

    /* ─── Open questions ─── */
    .oq-container {{
      width: 100%;
      max-width: 1000px;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .oq-item {{
      display: flex;
      gap: 1.25rem;
      align-items: flex-start;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      transition: all 0.3s ease;
    }}
    .oq-item:hover {{
      border-color: var(--accent);
      transform: translateX(4px);
    }}
    .oq-num {{
      font-family: var(--font-mono);
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--accent);
      flex-shrink: 0;
      width: 32px;
      text-align: center;
    }}
    .oq-text {{
      font-size: 1rem;
      color: var(--text2);
      line-height: 1.7;
    }}

    /* ─── Responsive ─── */
    @media (max-width: 768px) {{
      .slide {{ padding: 2rem 1.5rem; }}
      .cover-title {{ font-size: 2rem; }}
      .question-topic {{ font-size: 1.8rem; }}
      .slide-title {{ font-size: 1.6rem; }}
      .expert-grid {{ grid-template-columns: repeat(2, 1fr); gap: 1rem; }}
      .upgrade-block {{ flex-direction: column; }}
      .upgrade-arrow {{ transform: rotate(90deg); justify-content: center; }}
      .cases-container {{ grid-template-columns: 1fr; }}
      .cost-analysis {{ grid-template-columns: 1fr; }}
      .hn-examples {{ grid-template-columns: 1fr; }}
      .nav-dots {{ display: none; }}
    }}
    @media (max-width: 480px) {{
      .expert-grid {{ grid-template-columns: 1fr; }}
      .cover-stats {{ gap: 1rem; }}
      .cover-stat-num {{ font-size: 2rem; }}
    }}
    '''


def _build_js(total_slides: int) -> str:
    return f'''
    (function() {{
      const slideshow = document.getElementById('slideshow');
      const progressBar = document.getElementById('progressBar');
      const pageCounter = document.getElementById('pageCounter');
      const dots = document.querySelectorAll('.nav-dot');
      const total = {total_slides};
      let current = 0;
      let wheelTimer = null;
      let isScrolling = false;

      function updateUI() {{
        const scrollLeft = slideshow.scrollLeft;
        const slideWidth = slideshow.clientWidth;
        current = Math.round(scrollLeft / slideWidth);
        if (current < 0) current = 0;
        if (current >= total) current = total - 1;

        // Progress bar
        const pct = ((current + 1) / total) * 100;
        progressBar.style.width = pct + '%';

        // Page counter
        pageCounter.textContent = (current + 1) + ' / ' + total;

        // Dots
        dots.forEach(function(d, i) {{
          d.classList.toggle('active', i === current);
        }});
      }}

      function goTo(idx) {{
        if (idx < 0) idx = 0;
        if (idx >= total) idx = total - 1;
        slideshow.scrollTo({{ left: idx * slideshow.clientWidth, behavior: 'smooth' }});
        current = idx;
        setTimeout(updateUI, 400);
      }}

      // Keyboard
      document.addEventListener('keydown', function(e) {{
        switch(e.key) {{
          case 'ArrowRight': case ' ': case 'PageDown':
            e.preventDefault(); goTo(current + 1); break;
          case 'ArrowLeft': case 'PageUp':
            e.preventDefault(); goTo(current - 1); break;
          case 'Home':
            e.preventDefault(); goTo(0); break;
          case 'End':
            e.preventDefault(); goTo(total - 1); break;
        }}
      }});

      // Mouse wheel with debounce
      slideshow.addEventListener('wheel', function(e) {{
        e.preventDefault();
        if (wheelTimer) return;
        wheelTimer = setTimeout(function() {{ wheelTimer = null; }}, 600);
        if (e.deltaY > 0 || e.deltaX > 0) {{
          goTo(current + 1);
        }} else {{
          goTo(current - 1);
        }}
      }}, {{ passive: false }});

      // Nav dots
      dots.forEach(function(dot, i) {{
        dot.addEventListener('click', function() {{ goTo(i); }});
      }});

      // Scroll event
      slideshow.addEventListener('scroll', function() {{
        if (!isScrolling) {{
          isScrolling = true;
          requestAnimationFrame(function() {{
            updateUI();
            isScrolling = false;
          }});
        }}
      }});

      // Resize
      window.addEventListener('resize', function() {{ goTo(current); }});

      // Init
      updateUI();
    }})();
    '''


# ─── Main render function ────────────────────────────────────────────────────

def render_html(data: dict, theme: str = 'gold') -> str:
    """Render V8 JSON to self-contained HTML string."""
    from v8_normalizer import normalize_v8
    data = normalize_v8(data)
    t = THEMES.get(theme, THEMES['gold'])

    # Build expert color map
    experts = data.get('experts', [])
    experts_map = {}
    for i, e in enumerate(experts):
        experts_map[e.get('name', '')] = _avatar_color(e, i)

    # Build slides
    slides = []

    # 1. Cover
    slides.append(_build_cover(data, t))

    # 2. Expert grid
    slides.append(_build_expert_grid(data, t))

    # 3. Rounds
    for rd in data.get('rounds', []):
        # Normalize: some outputs use 'speeches' instead of 'stances'
        if 'speeches' in rd and 'stances' not in rd:
            rd = dict(rd)
            rd['stances'] = rd['speeches']

        # Question
        slides.append(_build_question_slide(rd, t))

        # Stances (batch by 3)
        stances = rd.get('stances', [])
        batches = [stances[i:i + 3] for i in range(0, len(stances), 3)]
        for bi, batch in enumerate(batches):
            slides.append(_build_stances_slide(batch, rd.get('round_number', '?'), bi, len(batches), experts_map, t))

        # Clash
        if rd.get('clash_rounds'):
            slides.append(_build_clash_slide(rd, experts_map, t))

        # Reality cases
        if rd.get('reality_cases'):
            s = _build_reality_case_slide(rd, t)
            if s:
                slides.append(s)

        # Cost discussion
        if rd.get('cost_discussion'):
            s = _build_cost_slide(rd, t)
            if s:
                slides.append(s)

        # Human nature
        if rd.get('human_nature'):
            s = _build_human_nature_slide(rd, t)
            if s:
                slides.append(s)

        # Cognitive upgrade
        if rd.get('cognitive_upgrade'):
            s = _build_upgrade_slide(rd, t)
            if s:
                slides.append(s)

    # 4. Final insight
    slides.append(_build_final_insight(data, t))

    # 5. Open questions
    slides.append(_build_open_questions(data, t))

    total_slides = len(slides)

    # Build nav dots
    dots_html = ''
    for i in range(total_slides):
        active = ' active' if i == 0 else ''
        dots_html += f'      <button class="nav-dot{active}" data-idx="{i}"></button>\n'

    slides_html = '\n'.join(slides)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(data.get('title', '圆桌讨论'))}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
{_build_css(t)}
</style>
</head>
<body>

<div class="progress-bar" id="progressBar"></div>
<div class="page-counter" id="pageCounter">1 / {total_slides}</div>

<div class="slideshow" id="slideshow">
{slides_html}
</div>

<div class="nav-dots">
{dots_html}</div>

<script>
{_build_js(total_slides)}
</script>

</body>
</html>'''

    return html


def render_to_file(data: dict, output_path: str, theme: str = 'gold') -> str:
    """Render and save to file. Returns output path."""
    html = render_html(data, theme)
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding='utf-8')
    return str(p)


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Render V8 JSON to HTML slideshow')
    parser.add_argument('input', help='Input V8 JSON file')
    parser.add_argument('output', help='Output HTML file')
    parser.add_argument('--theme', default='gold', choices=list(THEMES.keys()),
                        help='Color theme (default: gold)')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    path = render_to_file(data, args.output, args.theme)
    print(f'Rendered to: {path}')
