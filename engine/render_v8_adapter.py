# -*- coding: utf-8 -*-
"""V8数据适配器 - 将V8 JSON转换为各模板格式"""

import json
import re
from pathlib import Path
from typing import Dict, List

ENGINE_DIR = Path(__file__).parent
TEMPLATES_CONFIG = ENGINE_DIR / "templates.json"

TOPIC_TEMPLATES = {
    "投资": ["consulting-report", "premium-dark", "v3-magazine"],
    "金融": ["consulting-report", "premium-dark", "clean-review"],
    "哲学": ["editorial", "v2-starry", "rain-notes"],
    "科技": ["geek-report", "pixel-report", "dot-matrix"],
    "AI": ["geek-report", "pixel-report", "dot-matrix"],
    "文学": ["editorial", "sunrise", "v3-magazine"],
    "社会": ["dot-matrix", "editorial", "clean-review"],
    "情感": ["rain-notes", "sunrise", "story-field"],
    "心理": ["rain-notes", "editorial", "clean-review"],
    "创意": ["y2k-brand", "studio-photo", "pixel-report"],
    "经济": ["consulting-report", "clean-review", "premium-dark"],
    "叙事": ["story-field", "editorial", "sunrise"],
}

COLORS = ['#c23b22', '#4a6a9a', '#3a8a5c', '#d4a843', '#8a4aaa', '#e85d3a']

def sanitize(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def get_initial(name: str) -> str:
    return name[0] if name else "?"

def get_color(name: str) -> str:
    return COLORS[hash(name) % len(COLORS)]

def load_templates_config() -> Dict:
    with open(TEMPLATES_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)

def select_template(topic: str) -> Dict:
    config = load_templates_config()
    topic_upper = topic.upper()
    
    for key, candidates in TOPIC_TEMPLATES.items():
        if key in topic_upper:
            for t in config['templates']:
                if t['id'] in candidates:
                    return t
    
    default_ids = config['selection']['default']
    for t in config['templates']:
        if t['id'] in default_ids:
            return t
    
    return config['templates'][0]

def adapt_v8_to_generic(data: Dict) -> Dict:
    """将V8数据转换为通用格式"""
    generic = {
        'title': data.get('title', ''),
        'subtitle': data.get('subtitle', ''),
        'experts': [],
        'rounds': [],
        'conclusions': []
    }
    
    for e in data.get('experts', []):
        generic['experts'].append({
            'name': e.get('name', ''),
            'role': e.get('title', ''),
            'description': e.get('core_belief', '')
        })
    
    for r in data.get('rounds', []):
        round_data = {
            'question': r.get('topic', r.get('core_question', '')),
            'title': r.get('topic', ''),
            'stances': [],
            'clashes': [],
            'insight': {}
        }
        
        for s in r.get('stances', []):
            round_data['stances'].append({
                'speaker': s.get('expert', ''),
                'name': s.get('expert', ''),
                'content': s.get('stance', ''),
                'role': '发言'
            })
        
        for c in r.get('clash_rounds', []):
            round_data['clashes'].append({
                'speaker': c.get('attacker', ''),
                'content': c.get('attack_content', '')
            })
        
        if r.get('cognitive_upgrade'):
            upgrade = r['cognitive_upgrade']
            round_data['insight'] = {
                'core': upgrade.get('new_thinking', ''),
                'summary': upgrade.get('actionable_insight', ''),
                'explain': upgrade.get('complexity', '')
            }
        
        generic['rounds'].append(round_data)
    
    if data.get('final_insight'):
        generic['conclusions'].append({'content': data['final_insight']})
    
    for q in data.get('open_questions', []):
        generic['conclusions'].append({'content': q})
    
    return generic

def render_with_template(data: Dict, template_id: str) -> str:
    """使用指定模板渲染V8数据"""
    from engine.render_adapter import adapt, ADAPTERS
    
    generic_data = adapt_v8_to_generic(data)
    
    template_file = ENGINE_DIR / f"template-{template_id}.html"
    if not template_file.exists():
        template_file = ENGINE_DIR / "template-consulting-report.html"
    
    template_html = template_file.read_text(encoding='utf-8')
    
    slides_html = adapt(generic_data, template_id)
    
    html = template_html.replace('{{slides}}', slides_html)
    html = html.replace('{{title}}', sanitize(data.get('title', '圆桌洞见')))
    html = html.replace('{{subtitle}}', sanitize(data.get('subtitle', '')))
    
    return html

def render_v8_with_selected_template(data: Dict, topic: str = None) -> tuple:
    """根据话题选择模板并渲染"""
    if not topic:
        topic = data.get('title', '')
    
    template = select_template(topic)
    html = render_with_template(data, template['id'])
    
    return html, template['id'], template['name']