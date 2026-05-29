# -*- coding: utf-8 -*-
"""
Mutation Engine V4.0 — 变异引擎

核心公式：
NEW_STRATEGY = historical_strategy + contradiction + reality_failure + cross_domain_transfer

示例：
韩非子 + Amazon KPI + Tesla高压管理 + 开源社区失败案例 → 高压透明化组织模型
"""

import json
from llm_generate import call_llm_json
from anysearch_layer import search_source

MUTATE_PROMPT = """你是一个跨域策略变异专家。基于以下输入，生成一个新的策略。

## 原始策略
专家: {expert_name}
策略: {original_strategy}

## 矛盾点（来自辩论）
{contradictions}

## 现实失败案例
{failure_cases}

## 跨域素材（来自搜索）
{cross_domain_material}

## 要求

1. 结合原始策略、矛盾点、失败案例和跨域素材
2. 生成一个新的、更强大的策略
3. 新策略必须解决原始策略的弱点
4. 新策略必须有现实可行性

## 输出JSON格式

{{
  "new_strategy": "新策略描述（100-200字）",
  "mutations": [
    {{"source": "来源", "contribution": "贡献了什么"}}
  ],
  "strengths": ["新策略的优势"],
  "risks": ["新策略的风险"],
  "reality_check": "这个策略在现实中的可行性评估"
}}

只输出JSON，不要其他文字。"""

def mutate_strategy(expert_name: str, original_strategy: str,
                    contradictions: list = None, failure_cases: list = None,
                    cross_domain_query: str = None) -> dict:
    """执行策略变异"""
    cross_domain_material = ''
    if cross_domain_query:
        result = search_source(cross_domain_query, 'web', max_results=3)
        if result.get('success'):
            cross_domain_material = result.get('results', '')[:1000]
    
    contradictions_text = '\n'.join(f"- {c}" for c in (contradictions or []))
    failure_text = '\n'.join(f"- {f}" for f in (failure_cases or []))
    
    result = call_llm_json(
        MUTATE_PROMPT.format(
            expert_name=expert_name,
            original_strategy=original_strategy[:500],
            contradictions=contradictions_text or '无',
            failure_cases=failure_text or '无',
            cross_domain_material=cross_domain_material or '无',
        ),
        "你是跨域策略变异专家，结合多源信息生成更强策略。",
        max_tokens=2000,
        temperature=0.7,
    )
    
    if result['success'] and result.get('data'):
        return result['data']
    
    return {
        'new_strategy': original_strategy,
        'mutations': [],
        'strengths': [],
        'risks': [],
        'reality_check': '变异失败，保留原始策略',
    }

def batch_mutate(expert_name: str, strategies: list,
                 contradictions: list = None, failure_cases: list = None) -> list:
    """批量变异多个策略"""
    results = []
    for strategy in strategies[:3]:
        mutation = mutate_strategy(
            expert_name, strategy,
            contradictions, failure_cases,
        )
        results.append(mutation)
    return results