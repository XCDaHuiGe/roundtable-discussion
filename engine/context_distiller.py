# -*- coding: utf-8 -*-
"""
Context Distiller V4.0 — 认知蒸馏器

从搜索素材中提取：
- 共识点 (consensus)
- 冲突点 (conflicts)
- 弱信号 (weak_signals)
- 异见 (outlier_opinions)
- 情绪模式 (emotion_clusters)
- 现实案例 (reality_cases)
- 失败案例 (failure_cases)
"""

import json
from llm_generate import call_llm_json

DISTILL_PROMPT = """你是一个认知蒸馏专家。从以下搜索素材中提取高密度认知结构。

## 搜索素材
{material}

## 提取要求

从素材中提取以下7类信息（每类最多5条，每条不超过50字）：

1. **consensus** — 多个来源都认同的观点
2. **conflicts** — 不同来源之间的矛盾
3. **weak_signals** — 弱信号（少数人提到但可能重要的观点）
4. **outlier_opinions** — 异见（与主流相反的观点）
5. **emotion_clusters** — 情绪模式（愤怒/焦虑/乐观/悲观等）
6. **reality_cases** — 现实案例（具体事件、数据、实验）
7. **failure_cases** — 失败案例（什么方案失败了，为什么）

## 输出JSON格式

{{
  "consensus": ["观点1", "观点2"],
  "conflicts": ["矛盾1", "矛盾2"],
  "weak_signals": ["信号1"],
  "outlier_opinions": ["异见1"],
  "emotion_clusters": ["情绪模式1"],
  "reality_cases": ["案例1（含具体数据或事件）"],
  "failure_cases": ["失败案例1（含原因分析）"]
}}

只输出JSON，不要其他文字。"""


def distill(material_text: str) -> dict:
    """从素材中蒸馏认知结构"""
    if not material_text or len(material_text) < 50:
        return _empty_distill()

    result = call_llm_json(
        DISTILL_PROMPT.format(material=material_text[:3000]),
        "你是认知蒸馏专家，从搜索素材中提取高密度认知结构。",
        max_tokens=2000,
        temperature=0.3,
    )

    if result['success'] and result.get('data'):
        data = result['data']
        for key in ['consensus', 'conflicts', 'weak_signals', 'outlier_opinions',
                     'emotion_clusters', 'reality_cases', 'failure_cases']:
            if key not in data:
                data[key] = []
        return data

    return _empty_distill()


def _empty_distill() -> dict:
    return {
        'consensus': [],
        'conflicts': [],
        'weak_signals': [],
        'outlier_opinions': [],
        'emotion_clusters': [],
        'reality_cases': [],
        'failure_cases': [],
    }
