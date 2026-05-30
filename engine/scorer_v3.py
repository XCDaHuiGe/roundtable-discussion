# -*- coding: utf-8 -*-
"""
Scorer V3.0 — 纯计算评分

Agent传入6维度分数，Python只做加权计算。
零LLM依赖。

评分维度：
- reality_grounding (25%) — 现实依据
- contradiction_handling (20%) — 矛盾处理
- strategic_depth (20%) — 策略深度
- cross_domain_transfer (15%) — 跨域迁移
- novelty (10%) — 新颖性
- personality_consistency (10%) — 人格一致性
"""

WEIGHTS = {
    'reality_grounding': 0.25,
    'contradiction_handling': 0.20,
    'strategic_depth': 0.20,
    'cross_domain_transfer': 0.15,
    'novelty': 0.10,
    'personality_consistency': 0.10,
}


def score_v3(scores: dict) -> dict:
    """
    计算6维度加权总分

    Args:
        scores: Agent传入的6维度分数dict
            {
                "reality_grounding": 75,
                "contradiction_handling": 60,
                "strategic_depth": 80,
                "cross_domain_transfer": 50,
                "novelty": 65,
                "personality_consistency": 70
            }

    Returns:
        {"total": 68.5, "grade": "C", "dimensions": {...}}
    """
    total = 0
    dimensions = {}

    for dim, weight in WEIGHTS.items():
        score = scores.get(dim, 50)
        if isinstance(score, (int, float)):
            weighted = score * weight
            total += weighted
            dimensions[dim] = {'score': score, 'weight': weight, 'weighted': round(weighted, 2)}

    grade = _grade(total)
    return {
        'total': round(total, 1),
        'grade': grade,
        'dimensions': dimensions,
    }


def _grade(score: float) -> str:
    if score >= 90: return 'S'
    if score >= 80: return 'A'
    if score >= 70: return 'B'
    if score >= 60: return 'C'
    if score >= 50: return 'D'
    return 'F'


def default_scores() -> dict:
    """返回默认分数（Agent未评分时使用）"""
    return {
        'reality_grounding': 50,
        'contradiction_handling': 50,
        'strategic_depth': 50,
        'cross_domain_transfer': 50,
        'novelty': 50,
        'personality_consistency': 50,
    }