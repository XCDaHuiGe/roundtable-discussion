#!/usr/bin/env python3
"""
圆桌洞见渲染适配器
将圆桌洞见 JSON 数据转换为各模板所需的 HTML

v8 JSON 字段规范：
  - round: topic, core_question, stances, clash_rounds, reality_cases,
           cost_discussion, human_nature, cognitive_upgrade, synthesis
  - stance: expert, stance, emotion
  - clash: attacker, target, attack_type, attack_content, counter_attack
  - expert: name, title, avatar_color, core_belief, interest, fear, bias
  - synthesis: answer, consensus[], disagreements[]
  - final: final_insight, open_questions[], final_consensus[], final_disagreements[]
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_expert_initial(name: str) -> str:
    if not name:
        return "?"
    return name[0]


def get_expert_color(expert_id: str, colors: List[str]) -> str:
    hash_val = sum(ord(c) for c in expert_id)
    return colors[hash_val % len(colors)]


def _round_topic(rd: Dict) -> str:
    return sanitize_text(rd.get('topic', rd.get('question', rd.get('title', ''))))


def _round_question(rd: Dict) -> str:
    return sanitize_text(rd.get('core_question', ''))


def _stance_expert(s: Dict) -> str:
    return sanitize_text(s.get('expert', s.get('speaker', s.get('name', ''))))


def _stance_text(s: Dict) -> str:
    return sanitize_text(s.get('stance', s.get('content', '')))


def _clash_rounds(rd: Dict) -> List[Dict]:
    return rd.get('clash_rounds', rd.get('clashes', []))


def _expert_name(e: Dict) -> str:
    return sanitize_text(e.get('name', ''))


def _expert_title(e: Dict) -> str:
    return sanitize_text(e.get('title', e.get('role', '')))


def _expert_desc(e: Dict) -> str:
    return sanitize_text(e.get('core_belief', e.get('description', '')))


def _synthesis_block(rd: Dict) -> Optional[Dict]:
    syn = rd.get('synthesis', {})
    if syn and syn.get('answer'):
        return syn
    return None


def _render_synthesis_html(synthesis: Dict, colors: List[str]) -> str:
    answer = sanitize_text(synthesis.get('answer', ''))
    if not answer:
        return ""
    parts = [f'<div class="synthesis-answer"><div class="synthesis-label" style="color:{colors[3]};font-weight:700;font-size:0.85em;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">综合答案</div><div style="line-height:1.8;color:rgba(255,255,255,0.85);">{answer}</div></div>']

    consensus = synthesis.get('consensus', [])
    if consensus:
        items = "".join(f'<div style="padding:3px 0;padding-left:1em;color:rgba(255,255,255,0.8);">✓ {sanitize_text(c)}</div>' for c in consensus)
        parts.append(f'<div style="margin-top:12px;"><div style="color:{colors[2]};font-weight:700;font-size:0.8em;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">共识点</div>{items}</div>')

    disagrees = synthesis.get('disagreements', [])
    if disagrees:
        items = "".join(f'<div style="padding:3px 0;padding-left:1em;color:rgba(255,255,255,0.8);">⚡ {sanitize_text(d)}</div>' for d in disagrees)
        parts.append(f'<div style="margin-top:10px;"><div style="color:{colors[4]};font-weight:700;font-size:0.8em;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">分歧点</div>{items}</div>')

    return f'<div class="synthesis-block" style="background:rgba(212,168,67,0.06);border:1px solid rgba(212,168,67,0.2);border-radius:10px;padding:20px 24px;margin-top:16px;">{"".join(parts)}</div>'


def _final_slide(data: Dict, colors: List[str]) -> str:
    final_insight = sanitize_text(data.get('final_insight', ''))
    open_qs = data.get('open_questions', [])
    final_consensus = data.get('final_consensus', [])
    final_disagreements = data.get('final_disagreements', [])

    parts = []
    if final_insight:
        parts.append(f'<div style="font-weight:700;font-size:0.85em;color:{colors[3]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">最终洞见</div>')
        parts.append(f'<div style="font-size:1.05em;line-height:1.9;color:rgba(255,255,255,0.9);margin-bottom:20px;">{final_insight}</div>')

    if final_consensus:
        items = "".join(f'<div style="padding:3px 0;padding-left:1em;">✓ {sanitize_text(c)}</div>' for c in final_consensus)
        parts.append(f'<div style="margin-top:12px;"><div style="color:{colors[2]};font-weight:700;font-size:0.85em;margin-bottom:6px;">最终共识</div>{items}</div>')

    if final_disagreements:
        items = "".join(f'<div style="padding:3px 0;padding-left:1em;">⚡ {sanitize_text(d)}</div>' for d in final_disagreements)
        parts.append(f'<div style="margin-top:10px;"><div style="color:{colors[4]};font-weight:700;font-size:0.85em;margin-bottom:6px;">未解分歧</div>{items}</div>')

    if open_qs:
        items = "".join(f'<div style="padding:4px 0;"><strong style="color:{colors[3]};">Q{i+1}:</strong> {sanitize_text(q)}</div>' for i, q in enumerate(open_qs))
        parts.append(f'<div style="margin-top:16px;"><div style="font-weight:700;font-size:0.85em;margin-bottom:6px;">留给读者</div>{items}</div>')

    return "\n".join(parts)


def _render_cases_html(rd: Dict, colors: List[str]) -> str:
    cases = rd.get('reality_cases', [])
    if not cases:
        return ""
    parts = []
    for c in cases:
        name = sanitize_text(c.get('case_name', ''))
        source = sanitize_text(c.get('case_source', ''))
        content = sanitize_text(c.get('case_content', ''))
        outcome = sanitize_text(c.get('case_outcome', ''))
        lesson = sanitize_text(c.get('case_lesson', ''))
        outcome_html = f'<div style="margin-top:6px;font-size:0.85em;color:{colors[1]};">代价：{outcome}</div>' if outcome else ''
        lesson_html = f'<div style="font-size:0.85em;color:{colors[3]};">教训：{lesson}</div>' if lesson else ''
        parts.append(f'<div style="margin-bottom:14px;padding:12px 16px;background:rgba(255,255,255,0.03);border-left:3px solid {colors[0]};border-radius:4px;"><div style="font-weight:700;color:{colors[0]};margin-bottom:4px;">{name} <span style="opacity:0.5;font-weight:400;font-size:0.8em;">{source}</span></div><div style="line-height:1.7;font-size:0.9em;color:rgba(255,255,255,0.8);">{content}</div>{outcome_html}{lesson_html}</div>')
    return f'<div style="margin-top:16px;"><div style="font-weight:700;font-size:0.85em;color:{colors[4]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">现实案例</div>{"".join(parts)}</div>'


def _render_cost_html(rd: Dict, colors: List[str]) -> str:
    cost = rd.get('cost_discussion', {})
    if not cost:
        return ""
    parts = []
    scenario = sanitize_text(cost.get('scenario', ''))
    if scenario:
        parts.append(f'<div style="color:{colors[3]};font-weight:600;margin-bottom:8px;">{scenario}</div>')
    for c in cost.get('cost_analysis', []):
        cn = sanitize_text(c.get('cost', ''))
        ca = sanitize_text(c.get('analysis', ''))
        parts.append(f'<div style="padding:4px 0;font-size:0.9em;"><span style="color:{colors[0]};font-weight:600;">{cn}</span>：{ca}</div>')
    worst = sanitize_text(cost.get('worst_case', ''))
    if worst:
        parts.append(f'<div style="margin-top:8px;font-size:0.85em;color:{colors[0]};">最坏情况：{worst}</div>')
    survivor = sanitize_text(cost.get('survivor_bias', ''))
    if survivor:
        parts.append(f'<div style="font-size:0.85em;color:{colors[4]};">幸存者偏差：{survivor}</div>')
    return f'<div style="margin-top:16px;"><div style="font-weight:700;font-size:0.85em;color:{colors[0]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">代价讨论</div>{"".join(parts)}</div>'


def _render_human_html(rd: Dict, colors: List[str]) -> str:
    human = rd.get('human_nature', {})
    if not human:
        return ""
    parts = []
    q = sanitize_text(human.get('question', ''))
    if q:
        parts.append(f'<div style="color:{colors[4]};font-weight:600;margin-bottom:6px;">{q}</div>')
    analysis = sanitize_text(human.get('psychological_analysis', ''))
    if analysis:
        parts.append(f'<div style="line-height:1.7;font-size:0.9em;color:rgba(255,255,255,0.8);">{analysis}</div>')
    for ex in human.get('real_examples', []):
        parts.append(f'<div style="font-size:0.85em;padding:2px 0;padding-left:1em;">• {sanitize_text(ex)}</div>')
    conclusion = sanitize_text(human.get('conclusion', ''))
    if conclusion:
        parts.append(f'<div style="margin-top:6px;font-size:0.9em;color:{colors[3]};font-weight:600;">{conclusion}</div>')
    return f'<div style="margin-top:16px;"><div style="font-weight:700;font-size:0.85em;color:{colors[4]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">人性层</div>{"".join(parts)}</div>'


def _render_upgrade_html(rd: Dict, colors: List[str]) -> str:
    upgrade = rd.get('cognitive_upgrade', {})
    if not upgrade:
        return ""
    old_t = sanitize_text(upgrade.get('old_thinking', ''))
    new_t = sanitize_text(upgrade.get('new_thinking', ''))
    complexity = sanitize_text(upgrade.get('complexity', ''))
    actionable = sanitize_text(upgrade.get('actionable_insight', ''))
    parts = []
    if old_t:
        parts.append(f'<div style="margin-bottom:8px;"><div style="font-size:0.8em;color:{colors[0]};font-weight:600;">旧思维</div><div style="font-size:0.9em;line-height:1.7;">{old_t}</div></div>')
    if new_t:
        parts.append(f'<div style="margin-bottom:8px;"><div style="font-size:0.8em;color:{colors[2]};font-weight:600;">新思维</div><div style="font-size:0.9em;line-height:1.7;">{new_t}</div></div>')
    if complexity:
        parts.append(f'<div style="font-size:0.85em;color:rgba(255,255,255,0.6);">{complexity}</div>')
    if actionable:
        parts.append(f'<div style="margin-top:6px;font-size:0.9em;color:{colors[3]};font-weight:600;">{actionable}</div>')
    return f'<div style="margin-top:16px;"><div style="font-weight:700;font-size:0.85em;color:{colors[3]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">认知升级</div>{"".join(parts)}</div>'


def _render_round_deep(rd: Dict, colors: List[str]) -> str:
    parts = []
    parts.append(_render_cases_html(rd, colors))
    parts.append(_render_cost_html(rd, colors))
    parts.append(_render_human_html(rd, colors))
    parts.append(_render_upgrade_html(rd, colors))
    return "\n".join(p for p in parts if p)


def adapt_to_consulting_report(data: Dict, colors: List[str]) -> str:
    title = sanitize_text(data.get('title', ''))
    subtitle = sanitize_text(data.get('subtitle', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])

    slides_html = []

    slides_html.append(f'''
<div class="slide slide-cover">
  <div class="cover-logo">圆桌洞见<span>Roundtable Insight</span></div>
  <div class="cover-body">
    <h1>{title}</h1>
    <p class="cover-sub">{subtitle}</p>
    <p class="cover-date">{len(experts)} 位专家 · {len(rounds)} 轮讨论</p>
  </div>
  <div class="cover-footer">本报告由 AI 专家圆桌生成</div>
</div>''')

    if experts:
        expert_cards = ""
        for e in experts[:6]:
            name = _expert_name(e)
            initial = get_expert_initial(name)
            role = _expert_title(e)
            desc = _expert_desc(e)[:60]
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
</div>''')

    for i, rd in enumerate(rounds):
        rn = i + 1
        topic = _round_topic(rd)
        core_q = _round_question(rd)

        slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {rn} / {len(rounds)}</div>
  <h2 class="slide-title">{topic}</h2>
  {f'<p style="color:rgba(255,255,255,0.5);font-size:0.9em;margin-top:8px;">{core_q}</p>' if core_q else ''}
</div>''')

        stances = rd.get('stances', [])
        if stances:
            cards_html = ""
            for s in stances[:3]:
                speaker = _stance_expert(s)
                content = _stance_text(s)
                initial = get_expert_initial(speaker)
                cards_html += f'''
        <div class="speech-card">
          <div class="speech-meta">
            <div class="speaker-avatar" style="background:{get_expert_color(speaker, colors)}">{initial}</div>
            <div>
              <div class="speaker-name">{speaker}</div>
            </div>
          </div>
          <div class="speech-content">{content}</div>
        </div>'''
            slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {rn} 发言</div>
  <div class="speech-cards">{cards_html}
  </div>
</div>''')

        clashes = _clash_rounds(rd)
        if clashes:
            clashes_html = ""
            for c in clashes[:3]:
                attacker = sanitize_text(c.get('attacker', c.get('speaker', '')))
                target = sanitize_text(c.get('target', ''))
                atk = sanitize_text(c.get('attack_content', c.get('content', '')))
                counter = sanitize_text(c.get('counter_attack', ''))
                header = f"{attacker} → {target}" if target else attacker
                clashes_html += f'''
        <div class="clash-item">
          <div class="clash-speaker">{header}</div>
          <div class="clash-text">{atk}</div>
          {f'<div class="clash-text" style="margin-top:8px;opacity:0.8;">反击：{counter}</div>' if counter else ''}
        </div>'''
            slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {rn} 碰撞</div>
  <div class="clash-block">{clashes_html}
  </div>
</div>''')

        deep_html = _render_round_deep(rd, colors)
        if deep_html:
            slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {rn} 深度分析</div>
  {deep_html}
</div>''')

        synthesis = _synthesis_block(rd)
        if synthesis:
            slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {rn} 综合答案</div>
  {_render_synthesis_html(synthesis, colors)}
</div>''')

    final_html = _final_slide(data, colors)
    if final_html:
        slides_html.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">最终洞见</div>
  {final_html}
</div>''')

    return '\n'.join(slides_html)


def adapt_to_editorial(data: Dict, colors: List[str]) -> str:
    title = sanitize_text(data.get('title', ''))
    subtitle = sanitize_text(data.get('subtitle', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])

    slides_html = []

    slides_html.append(f'''
<div class="slide">
  <div class="left">
    <div class="issue">Roundtable Insight</div>
    <div class="mega">{title[:12]}</div>
    <div class="subtext">{subtitle}</div>
  </div>
  <div class="right">
    <div class="article-row">
      <div class="art-num">参与专家</div>
      <div class="art-title">{" / ".join([_expert_name(e)[:4] for e in experts[:4]])}</div>
      <div class="art-body">{len(experts)} 位专家 · {len(rounds)} 轮交锋</div>
    </div>
  </div>
</div>''')

    for i, rd in enumerate(rounds):
        rn = i + 1
        topic = _round_topic(rd)

        slides_html.append(f'''
<div class="slide">
  <div class="head-block">
    <div class="head-title">{topic}</div>
    <div class="head-tag">Round {rn}</div>
  </div>
</div>''')

        stances = rd.get('stances', [])
        if stances:
            cols_html = ""
            for s in stances[:3]:
                speaker = _stance_expert(s)
                content = _stance_text(s)[:300]
                cols_html += f'''
    <div class="col">
      <div class="col-num">{speaker[0]}</div>
      <div class="col-title">{speaker}</div>
      <div class="col-body">{content}</div>
    </div>'''
            slides_html.append(f'''
<div class="slide">
  <div class="head-block">
    <div class="head-title">各方立场</div>
  </div>
  <div class="col-grid">{cols_html}
  </div>
</div>''')

        deep_html = _render_round_deep(rd, colors)
        if deep_html:
            slides_html.append(f'''
<div class="slide">
  <div class="head-block">
    <div class="head-title">深度分析</div>
  </div>
  {deep_html}
</div>''')

        synthesis = _synthesis_block(rd)
        if synthesis:
            slides_html.append(f'''
<div class="slide">
  <div class="head-block">
    <div class="head-title">综合答案</div>
  </div>
  {_render_synthesis_html(synthesis, colors)}
</div>''')

    final_html = _final_slide(data, colors)
    if final_html:
        slides_html.append(f'''
<div class="slide">
  <div class="head-block">
    <div class="head-title">最终洞见</div>
  </div>
  {final_html}
</div>''')

    return '\n'.join(slides_html)


def adapt_to_geek_report(data: Dict, colors: List[str]) -> str:
    title = sanitize_text(data.get('title', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])

    slides_html = []
    expert_list = " | ".join([_expert_name(e)[:4] for e in experts[:6]])

    slides_html.append(f'''
<div class="slide">
  <div class="meta-line top">
    <span>SYSTEM://ROUNDTABLE_INSIGHT</span>
    <span>EXPERTS: {len(experts)}</span>
    <span>ROUNDS: {len(rounds)}</span>
  </div>
  <div class="hero-zone">
    <div class="hero-label">ROUNDTABLE_INSIGHT</div>
    <div class="hero-title">{title}</div>
  </div>
  <div class="meta-line bottom">
    <span>{expert_list}</span>
  </div>
</div>''')

    for i, rd in enumerate(rounds):
        rn = i + 1
        topic = _round_topic(rd)

        slides_html.append(f'''
<div class="slide">
  <div class="meta-line top">
    <span>ROUND {rn}/{len(rounds)}</span>
    <span>QUESTION</span>
  </div>
  <div class="question-block">
    <div class="question-text-large">{topic}</div>
  </div>
  <div class="meta-line bottom">
    <span>ANALYSIS_MODE</span>
  </div>
</div>''')

        stances = rd.get('stances', [])
        if stances:
            stances_html = ""
            for s in stances[:4]:
                speaker = _stance_expert(s)
                content = _stance_text(s)[:300]
                stances_html += f'''
    <div class="statement-block">
      <div class="statement-meta">
        <span class="statement-speaker">{speaker}</span>
        <span class="statement-role">发言</span>
      </div>
      <div class="statement-text">{content}</div>
    </div>'''
            slides_html.append(f'''
<div class="slide">
  <div class="meta-line top">
    <span>ROUND {rn}</span>
    <span>EXPERT_STANCES</span>
  </div>
  <div class="statements-grid">{stances_html}
  </div>
  <div class="meta-line bottom">
    <span>CONTENT_LOADED</span>
  </div>
</div>''')

        deep_html = _render_round_deep(rd, colors)
        if deep_html:
            slides_html.append(f'''
<div class="slide">
  <div class="meta-line top">
    <span>ROUND {rn}</span>
    <span>DEEP_ANALYSIS</span>
  </div>
  {deep_html}
  <div class="meta-line bottom">
    <span>ANALYSIS_COMPLETE</span>
  </div>
</div>''')

        synthesis = _synthesis_block(rd)
        if synthesis:
            slides_html.append(f'''
<div class="slide">
  <div class="meta-line top">
    <span>ROUND {rn}</span>
    <span>SYNTHESIS</span>
  </div>
  {_render_synthesis_html(synthesis, colors)}
  <div class="meta-line bottom">
    <span>SYNTHESIS_GENERATED</span>
  </div>
</div>''')

    final_html = _final_slide(data, colors)
    if final_html:
        slides_html.append(f'''
<div class="slide">
  <div class="meta-line top">
    <span>FINAL</span>
    <span>INSIGHT</span>
  </div>
  {final_html}
  <div class="meta-line bottom">
    <span>END_OF_REPORT</span>
  </div>
</div>''')

    return '\n'.join(slides_html)


def adapt_to_clean_review(data: Dict, colors: List[str]) -> str:
    title = sanitize_text(data.get('title', ''))
    subtitle = sanitize_text(data.get('subtitle', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])

    slides_html = []

    slides_html.append(f'''
<div class="slide">
  <div class="cover-badge">Roundtable Insight</div>
  <div class="cover-title">{title}</div>
  <div class="cover-experts">{" / ".join([_expert_name(e) for e in experts[:6]])}</div>
</div>''')

    for i, rd in enumerate(rounds):
        rn = i + 1
        topic = _round_topic(rd)

        slides_html.append(f'''
<div class="slide">
  <div class="section-header">
    <span class="section-tag">Round {rn}</span>
    <span class="section-title">{topic}</span>
  </div>''')

        stances = rd.get('stances', [])
        if stances:
            for s in stances[:3]:
                speaker = _stance_expert(s)
                content = _stance_text(s)
                slides_html.append(f'''
  <div class="review-card">
    <div class="review-header">
      <div class="review-avatar">{speaker[0]}</div>
      <div class="review-info">
        <div class="review-name">{speaker}</div>
      </div>
    </div>
    <div class="review-content">{content}</div>
  </div>''')

        deep_html = _render_round_deep(rd, colors)
        if deep_html:
            slides_html.append(f'<div style="margin-top:12px;">{deep_html}</div>')

        synthesis = _synthesis_block(rd)
        if synthesis:
            slides_html.append(_render_synthesis_html(synthesis, colors))

        slides_html.append('</div>')

    final_html = _final_slide(data, colors)
    if final_html:
        slides_html.append(f'''
<div class="slide">
  <div class="section-header">
    <span class="section-tag">Final</span>
    <span class="section-title">最终洞见</span>
  </div>
  {final_html}
</div>''')

    return '\n'.join(slides_html)


def adapt_to_rain_notes(data: Dict, colors: List[str]) -> str:
    title = sanitize_text(data.get('title', ''))
    rounds = data.get('rounds', [])
    experts = data.get('experts', [])

    slides_html = []

    slides_html.append(f'''
<div class="slide">
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
</div>''')

    for i, rd in enumerate(rounds):
        rn = i + 1
        topic = _round_topic(rd)

        slides_html.append(f'''
<div class="slide">
  <div class="paper-texture"></div>
  <div class="note-header">
    <span class="note-round">Round {rn}</span>
  </div>
  <h2 class="note-question">{topic}</h2>''')

        stances = rd.get('stances', [])
        if stances:
            notes_html = ""
            for s in stances[:3]:
                speaker = _stance_expert(s)
                content = _stance_text(s)
                notes_html += f'''
    <div class="note-entry">
      <div class="note-speaker">{speaker}</div>
      <div class="note-content">{content}</div>
    </div>'''
            slides_html.append(f'''
  <div class="notes-container">{notes_html}
  </div>''')

        deep_html = _render_round_deep(rd, colors)
        if deep_html:
            slides_html.append(f'<div style="margin-top:12px;">{deep_html}</div>')

        synthesis = _synthesis_block(rd)
        if synthesis:
            slides_html.append(_render_synthesis_html(synthesis, colors))

        slides_html.append('</div>')

    final_html = _final_slide(data, colors)
    if final_html:
        slides_html.append(f'''
<div class="slide">
  <div class="paper-texture"></div>
  <div class="note-header">
    <span class="note-round">最终洞见</span>
  </div>
  {final_html}
</div>''')

    return '\n'.join(slides_html)


ADAPTERS = {
    'consulting-report': adapt_to_consulting_report,
    'editorial': adapt_to_editorial,
    'geek-report': adapt_to_geek_report,
    'clean-review': adapt_to_clean_review,
    'rain-notes': adapt_to_rain_notes,
}


def adapt(data: Dict, template_id: str) -> str:
    adapter = ADAPTERS.get(template_id)
    if adapter:
        return adapter(data, ['#c23b22', '#4a6a9a', '#3a8a5c', '#d4a843', '#8a4aaa', '#e85d3a'])
    return adapt_to_consulting_report(data, ['#c23b22', '#4a6a9a', '#3a8a5c', '#d4a843', '#8a4aaa', '#e85d3a'])


def render(data: Dict, template_id: str, template_html: str) -> str:
    slides_html = adapt(data, template_id)
    html = template_html
    html = html.replace('{{slides}}', slides_html)
    html = html.replace('{{title}}', sanitize_text(data.get('title', '圆桌洞见')))
    html = html.replace('{{subtitle}}', sanitize_text(data.get('subtitle', '')))
    return html
