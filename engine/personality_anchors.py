# -*- coding: utf-8 -*-
"""
Personality Anchors V4.0 — 人格锚点系统

防止训练过程中专家人格漂移。
每个专家有不可变的核心信念（immutable），违反锚点的融合/升级/写回会被拒绝。
"""

import os
import json
import re

EXPERT_LIBRARY = os.path.join(os.path.dirname(__file__), '..', 'expert-library')

def load_anchors(expert_name: str) -> dict:
    """从专家档案中提取人格锚点"""
    md_path = _find_expert_md(expert_name)
    if not md_path:
        return {'expert': expert_name, 'immutable': [], 'found': False}
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    anchors = []
    
    beliefs_match = re.search(r'### 核心信念\s*\n((?:- .+\n)+)', content)
    if beliefs_match:
        for line in beliefs_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('- ')
            if line and line != '待填充':
                anchors.append(line)
    
    values_match = re.search(r'### 价值排序\s*\n((?:- .+\n)+)', content)
    if values_match:
        for line in values_match.group(1).strip().split('\n')[:2]:
            line = line.strip().lstrip('- ')
            if line and line != '待填充':
                anchors.append(line)
    
    return {
        'expert': expert_name,
        'immutable': anchors[:5],
        'found': True,
    }

def check_anchor_violation(expert_name: str, new_strategy: dict) -> dict:
    """检查新策略是否违反人格锚点"""
    anchors = load_anchors(expert_name)
    
    if not anchors['found']:
        return {'violated': False, 'reason': '未找到专家档案'}
    
    if not anchors['immutable']:
        return {'violated': False, 'reason': '无锚点定义'}
    
    strategy_text = json.dumps(new_strategy, ensure_ascii=False)[:500]
    
    violations = []
    for anchor in anchors['immutable']:
        anchor_lower = anchor.lower()
        strategy_lower = strategy_text.lower()
        
        if '反' in anchor and any(word in strategy_lower for word in ['支持', '推崇', '认同']):
            violations.append(f"锚点'{anchor}'与策略可能存在矛盾")
        if '不' in anchor and any(word in strategy_lower for word in ['应该', '必须', '需要']):
            pass
    
    return {
        'violated': len(violations) > 0,
        'violations': violations,
        'anchors': anchors['immutable'],
    }

def _find_expert_md(expert_name: str) -> str:
    """Find expert markdown file"""
    experts_dir = os.path.join(EXPERT_LIBRARY, 'experts')
    for cat in ['philosophy', 'psychology', 'sociology', 'literature', 'economics']:
        cat_dir = os.path.join(experts_dir, cat)
        if not os.path.isdir(cat_dir):
            continue
        for f in os.listdir(cat_dir):
            if f.endswith('.md') and f[:-3] == expert_name:
                return os.path.join(cat_dir, f)
    return None