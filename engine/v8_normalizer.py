# -*- coding: utf-8 -*-
"""
V8 JSON 格式标准化器

不同来源生成的V8 JSON字段名不一致，此模块统一为渲染器期望的格式。

已知变体：
  stance文本: 'speech' / 'content' / 'text' / 'stance'
  clash结构: {challenger,attack,counter,response,target} / {attacker,attack_content,counter_attack}
  reality_cases: dict(单案例) / list(多案例)
  case字段: {content,lesson,outcome,source} / {case_name,case_source,case_content,...}
  cost字段: {cost_analyses,...} / {analyses,...}
  round_number: 存在 / 缺失
"""

import copy
from typing import Dict, List


def normalize_v8(data: dict) -> dict:
    """标准化V8 JSON为渲染器期望的格式"""
    data = copy.deepcopy(data)

    # 标准化 experts
    for i, exp in enumerate(data.get('experts', [])):
        if 'title' not in exp and 'identity' in exp:
            exp['title'] = exp['identity']
        if 'avatar_color' not in exp:
            colors = ['#8B4513', '#2E8B57', '#4169E1', '#8B008B', '#DAA520', '#CD5C5C']
            exp['avatar_color'] = colors[i % len(colors)]

    # 标准化 rounds
    for i, rd in enumerate(data.get('rounds', [])):
        # round_number
        if 'round_number' not in rd:
            rd['round_number'] = i + 1

        # stances
        for s in rd.get('stances', []):
            if 'text' not in s and 'stance' not in s:
                s['text'] = s.get('speech', s.get('content', s.get('stance', '')))
            elif 'text' not in s and 'stance' in s:
                s['text'] = s['stance']

        # clash_rounds
        clashes = rd.get('clash_rounds', [])
        if isinstance(clashes, dict):
            clashes = [clashes]
            rd['clash_rounds'] = clashes
        normalized_clashes = []
        for c in clashes:
            nc = _normalize_clash(c)
            if nc:
                normalized_clashes.append(nc)
        rd['clash_rounds'] = normalized_clashes

        # reality_cases
        cases = rd.get('reality_cases', [])
        if isinstance(cases, dict):
            cases = [cases]
        elif not isinstance(cases, list):
            cases = []
        rd['reality_cases'] = [_normalize_case(c) for c in cases if isinstance(c, dict)]

        # cost_discussion
        cd = rd.get('cost_discussion', {})
        if isinstance(cd, dict):
            if 'cost_analyses' in cd and 'analyses' not in cd:
                cd['analyses'] = cd.pop('cost_analyses')
            # Normalize cost_analysis items
            analyses = cd.get('analyses', [])
            normalized_analyses = []
            for a in analyses:
                if isinstance(a, dict):
                    normalized_analyses.append(a)
                elif isinstance(a, str):
                    normalized_analyses.append({'dimension': '', 'analysis': a})
            cd['analyses'] = normalized_analyses

        # human_nature - already consistent, just ensure dict
        hn = rd.get('human_nature', {})
        if not isinstance(hn, dict):
            rd['human_nature'] = {}

        # cognitive_upgrade - already consistent, just ensure dict
        cu = rd.get('cognitive_upgrade', {})
        if not isinstance(cu, dict):
            rd['cognitive_upgrade'] = {}

    return data


def _normalize_clash(c: dict) -> dict:
    """标准化clash结构"""
    if not isinstance(c, dict):
        return None

    # 已经是标准格式
    if 'attacker' in c and 'attack_content' in c:
        return c

    # 内卷格式: challenger/attack/counter/response/target
    if 'challenger' in c:
        return {
            'attacker': c.get('challenger', ''),
            'target': c.get('target', ''),
            'attack_type': '',
            'attack_content': c.get('attack', ''),
            'emotion': 'critical',
            'counter_attack': c.get('response', c.get('counter', '')),
            'counter_emotion': 'serious',
        }

    # 亲密关系格式: attacks (list of attack objects)
    if 'attacks' in c and isinstance(c['attacks'], list):
        attacks = c['attacks']
        if len(attacks) >= 2:
            return {
                'attacker': attacks[0].get('from', attacks[0].get('expert', '')),
                'target': attacks[0].get('to', attacks[1].get('expert', '')),
                'attack_type': attacks[0].get('type', ''),
                'attack_content': attacks[0].get('content', ''),
                'emotion': attacks[0].get('emotion', 'critical'),
                'counter_attack': attacks[1].get('content', ''),
                'counter_emotion': attacks[1].get('emotion', 'serious'),
            }
        elif len(attacks) == 1:
            return {
                'attacker': attacks[0].get('expert', ''),
                'target': '',
                'attack_type': attacks[0].get('type', ''),
                'attack_content': attacks[0].get('content', ''),
                'emotion': attacks[0].get('emotion', 'critical'),
                'counter_attack': '',
                'counter_emotion': 'serious',
            }

    # Fallback: try common field names
    return {
        'attacker': c.get('attacker', c.get('from', '')),
        'target': c.get('target', c.get('to', '')),
        'attack_type': c.get('attack_type', c.get('type', '')),
        'attack_content': c.get('attack_content', c.get('content', c.get('argument', ''))),
        'emotion': c.get('emotion', 'critical'),
        'counter_attack': c.get('counter_attack', c.get('rebuttal', c.get('response', ''))),
        'counter_emotion': c.get('counter_emotion', 'serious'),
    }


def _normalize_case(c: dict) -> dict:
    """标准化reality case结构"""
    if not isinstance(c, dict):
        return {}

    # 已经是标准格式
    if 'case_name' in c:
        return c

    # 内卷格式: content/lesson/outcome/source
    if 'content' in c and 'case_name' not in c:
        return {
            'case_name': c.get('name', c.get('title', '')),
            'case_source': c.get('source', ''),
            'case_content': c.get('content', c.get('description', '')),
            'case_outcome': c.get('outcome', ''),
            'case_lesson': c.get('lesson', c.get('relevance', '')),
        }

    # 亲密关系格式: title/description/relevance
    if 'title' in c:
        return {
            'case_name': c.get('title', ''),
            'case_source': c.get('source', ''),
            'case_content': c.get('description', c.get('content', '')),
            'case_outcome': c.get('outcome', ''),
            'case_lesson': c.get('relevance', c.get('lesson', '')),
        }

    # Fallback
    return {
        'case_name': c.get('name', c.get('title', '')),
        'case_source': c.get('source', ''),
        'case_content': c.get('content', c.get('description', c.get('text', ''))),
        'case_outcome': c.get('outcome', ''),
        'case_lesson': c.get('lesson', c.get('relevance', '')),
    }
