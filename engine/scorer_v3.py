# -*- coding: utf-8 -*-
"""
Scorer V3.0 — 新评分体系

6维度评分（替代scorer_v2的7维度）：
- reality_grounding (25%) — 现实依据
- contradiction_handling (20%) — 矛盾处理
- strategic_depth (20%) — 策略深度
- cross_domain_transfer (15%) — 跨域迁移
- novelty (10%) — 新颖性
- personality_consistency (10%) — 人格一致性
"""

import json
from llm_generate import call_llm_json

SCORE_PROMPT = """你是一个辩论质量评估专家。对以下辩论进行6维度评分。

## 辩论内容
{debate_text}

## 评分维度（每项0-100分）

1. **reality_grounding** (25%) — 发言是否引用了真实案例、数据、事件？证据是否可验证？
2. **contradiction_handling** (20%) — 是否发现了对方论证中的矛盾？反驳是否有力？
3. **strategic_depth** (20%) — 论证是否有策略深度？是否有长远视角？
4. **cross_domain_transfer** (15%) — 是否有跨领域类比或迁移？
5. **novelty** (10%) — 是否有新颖的观点或角度？
6. **personality_consistency** (10%) — 专家发言是否体现其独特人格和核心信念？

## 输出JSON格式

{{
  "reality_grounding": 75,
  "contradiction_handling": 60,
  "strategic_depth": 80,
  "cross_domain_transfer": 50,
  "novelty": 65,
  "personality_consistency": 70,
  "details": {{
    "reality_grounding": "具体评价...",
    "contradiction_handling": "具体评价...",
    "strategic_depth": "具体评价...",
    "cross_domain_transfer": "具体评价...",
    "novelty": "具体评价...",
    "personality_consistency": "具体评价..."
  }}
}}

只输出JSON，不要其他文字。"""

WEIGHTS = {
    'reality_grounding': 0.25,
    'contradiction_handling': 0.20,
    'strategic_depth': 0.20,
    'cross_domain_transfer': 0.15,
    'novelty': 0.10,
    'personality_consistency': 0.10,
}

def score_v3(debate_json: dict) -> dict:
    """对辩论JSON进行V3评分"""
    debate_text = _extract_debate_text(debate_json)
    
    result = call_llm_json(
        SCORE_PROMPT.format(debate_text=debate_text[:4000]),
        "你是辩论质量评估专家，进行6维度严格评分。",
        max_tokens=2000,
        temperature=0.2,
    )
    
    if result['success'] and result.get('data'):
        data = result['data']
        total = 0
        for dim, weight in WEIGHTS.items():
            score = data.get(dim, 0)
            if isinstance(score, (int, float)):
                total += score * weight
        
        data['total'] = round(total, 1)
        data['grade'] = _grade(total)
        return data
    
    return {'total': 0, 'grade': 'F', 'error': result.get('error', '评分失败')}

def _extract_debate_text(debate_json: dict) -> str:
    """Extract readable text from debate JSON"""
    parts = []
    parts.append(f"话题: {debate_json.get('topic', '')}")
    
    for round_data in debate_json.get('rounds', []):
        parts.append(f"\n--- {round_data.get('round_name', '')} ---")
        if round_data.get('synthesis', {}).get('summary'):
            parts.append(f"综合: {round_data['synthesis']['summary']}")
        for speech in round_data.get('speeches', []):
            expert = speech.get('expert', '')
            content = speech.get('content', '')
            parts.append(f"[{expert}]: {content[:300]}")
    
    for quote in debate_json.get('key_quotes', []):
        if isinstance(quote, dict):
            parts.append(f"金句 [{quote.get('expert', '')}]: {quote.get('quote', '')}")
    
    return '\n'.join(parts)

def _grade(score: float) -> str:
    if score >= 90: return 'S'
    if score >= 80: return 'A'
    if score >= 70: return 'B'
    if score >= 60: return 'C'
    if score >= 50: return 'D'
    return 'F'