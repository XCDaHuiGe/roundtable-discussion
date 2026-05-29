"""
Reality Validator V4.0 — 自动现实验证

对辩论中的每个核心论点进行现实验证：
claim → search → evidence → counter_evidence → reality_score
"""

import json
from anysearch_layer import search_source
from llm_generate import call_llm_json

VALIDATE_PROMPT = """你是一个现实验证专家。根据以下搜索结果，验证给定论点的真实性。

## 论点
{claim}

## 搜索结果
{search_results}

## 要求

1. 从搜索结果中找到支持该论点的真实案例（real_cases）
2. 从搜索结果中找到反驳该论点的失败案例（failure_cases）
3. 给出置信度评分（0-1）

## 输出JSON格式

{{
  "claim": "{claim}",
  "real_cases": ["支持案例1（含具体数据或事件）"],
  "failure_cases": ["反驳案例1（含具体原因）"],
  "confidence": 0.75,
  "verdict": "partially_true / mostly_true / mostly_false / unverifiable"
}}

只输出JSON，不要其他文字。"""


def validate_claim(claim: str, search_results: str = None) -> dict:
    if not search_results:
        result = search_source(claim, 'web', max_results=5)
        search_results = result.get('results', '')[:2000] if result.get('success') else '无搜索结果'

    llm_result = call_llm_json(
        VALIDATE_PROMPT.format(claim=claim, search_results=search_results[:2000]),
        "你是现实验证专家，根据搜索结果验证论点的真实性。",
        max_tokens=1500,
        temperature=0.2,
    )

    if llm_result['success'] and llm_result.get('data'):
        data = llm_result['data']
        data.setdefault('claim', claim)
        data.setdefault('real_cases', [])
        data.setdefault('failure_cases', [])
        data.setdefault('confidence', 0.5)
        data.setdefault('verdict', 'unverifiable')
        return data

    return {
        'claim': claim,
        'real_cases': [],
        'failure_cases': [],
        'confidence': 0.0,
        'verdict': 'unverifiable',
    }


def validate_debate_claims(debate_json: dict) -> list:
    claims = []

    for quote in debate_json.get('key_quotes', []):
        if isinstance(quote, dict) and quote.get('quote'):
            claims.append(quote['quote'])

    for round_data in debate_json.get('rounds', []):
        if round_data.get('round_number') == 1:
            for speech in round_data.get('speeches', []):
                if speech.get('stance'):
                    claims.append(speech['stance'])

    validations = []
    for claim in claims[:5]:
        validation = validate_claim(claim)
        validations.append(validation)

    return validations
