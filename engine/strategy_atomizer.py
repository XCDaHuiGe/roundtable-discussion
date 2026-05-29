"""
Strategy Atomizer V4.0 — 策略原子化

将自然语言策略转换为结构化原子：
{
  "trigger": "触发条件",
  "goal": "目标",
  "method": "方法",
  "risk": "风险",
  "counter": "反制策略",
  "emotion": "情绪基调",
  "evidence_preference": ["偏好证据类型"]
}
"""

import json
from llm_generate import call_llm_json

ATOMIZE_PROMPT = """你是一个策略分析专家。将以下自然语言策略转换为结构化原子。

## 策略内容
{strategy_text}

## 专家信息
专家: {expert_name}
核心信念: {beliefs}

## 要求

将策略分解为以下7个维度（每个维度简洁明了，不超过30字）：

1. **trigger** — 什么情况下使用这个策略
2. **goal** — 这个策略要达到什么目标
3. **method** — 具体怎么执行
4. **risk** — 这个策略的风险是什么
5. **counter** — 如何反制这个策略
6. **emotion** — 使用时的情绪基调（冷静/激进/温和/讽刺等）
7. **evidence_preference** — 偏好什么类型的证据（数据/案例/类比/权威引用等）

## 输出JSON格式

{{
  "trigger": "当对手...",
  "goal": "证明...",
  "method": "通过...",
  "risk": "可能被反驳...",
  "counter": "可以用...",
  "emotion": "冷静",
  "evidence_preference": ["数据", "案例"]
}}

只输出JSON，不要其他文字。"""


def atomize_strategy(strategy_text: str, expert_name: str = '', beliefs: str = '') -> dict:
    result = call_llm_json(
        ATOMIZE_PROMPT.format(
            strategy_text=strategy_text[:1000],
            expert_name=expert_name,
            beliefs=beliefs[:300],
        ),
        "你是策略分析专家，将自然语言策略转换为结构化原子。",
        max_tokens=1000,
        temperature=0.3,
    )

    if result['success'] and result.get('data'):
        data = result['data']
        for key in ['trigger', 'goal', 'method', 'risk', 'counter', 'emotion', 'evidence_preference']:
            if key not in data:
                data[key] = ''
        if not isinstance(data['evidence_preference'], list):
            data['evidence_preference'] = [str(data['evidence_preference'])]
        return data

    return {
        'trigger': '',
        'goal': '',
        'method': strategy_text[:50],
        'risk': '',
        'counter': '',
        'emotion': 'unknown',
        'evidence_preference': [],
    }


def atomize_extraction(extraction: dict) -> dict:
    atomized = {}

    for expert_name, expert_data in extraction.get('experts', {}).items():
        atoms = []

        attack = expert_data.get('attack_strategy', {})
        if attack.get('preferred_types'):
            for tactic in attack['preferred_types'][:3]:
                atom = atomize_strategy(
                    f"攻击策略: {tactic}. 证据: {attack.get('evidence_chain', '')}",
                    expert_name,
                )
                atom['type'] = 'attack'
                atoms.append(atom)

        style = expert_data.get('style_fingerprint', {})
        if style.get('markers'):
            atom = atomize_strategy(
                f"风格特征: {', '.join(style['markers'])}",
                expert_name,
            )
            atom['type'] = 'style'
            atoms.append(atom)

        atomized[expert_name] = atoms

    return atomized
