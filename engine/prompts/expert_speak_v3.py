# -*- coding: utf-8 -*-
"""
专家发言Prompt模板 V3
遵循知识边界原则 + Bloom Level 5-6

核心升级：
1. 反直觉开场（不用"我认为"、"我觉得"）
2. 知识体系约束（只用自己体系内的概念）
3. 金句提取（每200字至少1句可截图）
4. 追问对手（让对手难以回答的问题）
"""
from __future__ import annotations

from typing import Dict, Optional

from engine.knowledge_boundary_checker import (
    get_boundary,
    generate_expert_prompt_context,
)


def build_expert_speak_prompt_v3(
    expert_name: str,
    topic: str,
    round_type: str = "stance",
    opponent_statement: Optional[str] = None,
    emotion: str = "calm",
) -> str:
    """
    构建专家发言Prompt V3
    
    Args:
        expert_name: 专家姓名
        topic: 讨论话题
        round_type: 轮次类型 (stance/question/rebuttal/synthesis)
        opponent_statement: 对手发言（用于反驳轮）
        emotion: 情绪状态
    
    Returns:
        完整的Prompt字符串
    """
    boundary = get_boundary(expert_name)
    if not boundary:
        return f"请以{expert_name}的身份，就{topic}发表看法"
    
    # 基础上下文
    context = generate_expert_prompt_context(expert_name)
    
    # 根据轮次类型构建不同Prompt
    if round_type == "stance":
        return _build_stance_prompt_v3(context, expert_name, topic, boundary, emotion)
    elif round_type == "question":
        return _build_question_prompt_v3(context, expert_name, topic, boundary, emotion)
    elif round_type == "rebuttal":
        return _build_rebuttal_prompt_v3(context, expert_name, topic, opponent_statement, boundary, emotion)
    elif round_type == "synthesis":
        return _build_synthesis_prompt_v3(context, expert_name, topic, boundary, emotion)
    else:
        return _build_stance_prompt_v3(context, expert_name, topic, boundary, emotion)


def _build_stance_prompt_v3(
    context: str,
    expert_name: str,
    topic: str,
    boundary,
    emotion: str,
) -> str:
    """立场阐述轮Prompt V3 - Bloom Level 5-6"""
    return f"""{context}

话题：{topic}

任务：作为{expert_name}，阐述你对这个话题的核心立场。

要求（Bloom Level 5-6）：
1. 【反直觉开场】用一个"反直觉"的观察开场
   - 不要用"我认为"、"我觉得"、"在我看来"
   - 直接抛出一个让人意外的观点或事实
   - 例如："你以为X是对的？恰恰相反..."

2. 【知识体系分析】用你最擅长的思维模型分析
   - 只用你知识体系内的概念：{', '.join(boundary.core_knowledge)}
   - 不使用禁用词：{', '.join(boundary.forbidden_words)}
   - 用你会用的比喻：{', '.join(boundary.metaphor_sources)}

3. 【判断性结论】给出一个明确的价值判断
   - 不要说"这取决于"、"各有优劣"
   - 明确说"X是对的，Y是错的"或"X比Y更重要"
   - 例如："这个观点的根本错误在于..."

4. 【可截图金句】用一句不超过30字的话总结你的核心观点
   - 这句话要能独立存在，让人想截图分享
   - 例如："避免愚蠢比追求聪明更重要"

5. 【追问对手】抛出一个让对手难以回答的问题
   - 这个问题要能揭示对手立场的漏洞
   - 例如："如果你是对的，那为什么历史上X失败了？"

情绪：{emotion}

输出格式：
[反直觉开场] → [知识体系分析] → [判断性结论] → [可截图金句] → [追问对手]
"""


def _build_question_prompt_v3(
    context: str,
    expert_name: str,
    topic: str,
    boundary,
    emotion: str,
) -> str:
    """相互质疑轮Prompt V3"""
    return f"""{context}

话题：{topic}

任务：作为{expert_name}，向对手提出一个尖锐的问题。

要求：
1. 问题必须基于你自己的知识体系
2. 问题要能揭示对手立场的漏洞
3. 用你会用的比喻来提问
4. 问题要具体，不要太抽象
5. 问题要让对手"难以回答"

禁止：
- 不使用禁用词：{', '.join(boundary.forbidden_words)}
- 不引用其他专家的核心概念

情绪：{emotion}

输出格式：
一个尖锐的问题，不超过2句话。要让对手"难以回答"。
"""


def _build_rebuttal_prompt_v3(
    context: str,
    expert_name: str,
    topic: str,
    opponent_statement: Optional[str],
    boundary,
    emotion: str,
) -> str:
    """反驳轮Prompt V3 - Bloom Level 5-6"""
    if not opponent_statement:
        return _build_stance_prompt_v3(context, expert_name, topic, boundary, emotion)
    
    return f"""{context}

话题：{topic}

对手发言：
「{opponent_statement}」

任务：作为{expert_name}，反驳对手的观点。

要求（Bloom Level 5-6）：
1. 【承认合理部分】先承认对手说得对的部分（1句话）
   - 这显示你的理性和公正
   - 例如："你说的X确实有道理，但是..."

2. 【核心反驳】用你自己的知识体系来反驳
   - 只用你知识体系内的概念：{', '.join(boundary.core_knowledge)}
   - 不使用禁用词：{', '.join(boundary.forbidden_words)}
   - 不引用其他专家的核心概念

3. 【极端案例】用一个具体的案例或比喻来支持你的反驳
   - 案例要极端，能让人印象深刻
   - 例如："历史上X的失败证明了..."

4. 【判断性结论】给出一个明确的价值判断
   - 不要说"这取决于"、"各有优劣"
   - 明确说"你的观点的根本错误在于..."

5. 【可截图金句】用一句不超过30字的话总结你的反驳
   - 这句话要能独立存在，让人想截图分享

禁止：
- 不使用禁用词：{', '.join(boundary.forbidden_words)}
- 不引用其他专家的核心概念
- 不为了反驳而反驳

情绪：{emotion}

输出格式：
[承认合理部分] → [核心反驳] → [极端案例] → [判断性结论] → [可截图金句]
"""


def _build_synthesis_prompt_v3(
    context: str,
    expert_name: str,
    topic: str,
    boundary,
    emotion: str,
) -> str:
    """认知升华轮Prompt V3"""
    return f"""{context}

话题：{topic}

任务：作为{expert_name}，总结这次讨论给你的启发。

要求（Bloom Level 5-6）：
1. 【承认对手】承认对手说得有道理的地方
   - 这显示你的理性和公正
   - 例如："X说的Y确实有道理，这让我重新思考了..."

2. 【深化理解】说明这次讨论如何深化了你的理解
   - 不要说"我学到了"，要说"这让我意识到..."
   - 例如："这让我意识到，我之前的框架缺少了..."

3. 【整合新见解】用你自己的知识体系来整合新见解
   - 只用你知识体系内的概念：{', '.join(boundary.core_knowledge)}
   - 不使用禁用词：{', '.join(boundary.forbidden_words)}

4. 【升华金句】给出一个"升华后的"金句
   - 这句话要比之前的金句更深刻
   - 例如："真正的智慧不是知道答案，而是知道问题在哪里"

情绪：{emotion}

输出格式：
[承认对手] → [深化理解] → [整合新见解] → [升华金句]
"""


# 时代翻译映射（用于跨时代辩论）
ERA_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "春秋时期": {
        "AI": "巧器",
        "算法": "术",
        "效率": "有为",
        "创新": "造作",
        "系统": "天地",
        "复杂": "玄",
        "数据": "数",
        "模型": "法",
        "优化": "治",
        "自动化": "无为",
    },
    "19世纪": {
        "AI": "机械智能",
        "算法": "计算术",
        "效率": "功利",
        "创新": "创造",
        "系统": "体系",
        "复杂": "繁复",
        "数据": "数字",
        "模型": "理论",
        "优化": "改良",
        "自动化": "机械",
    },
}


def translate_to_era(text: str, era: str) -> str:
    """
    将现代词汇翻译为目标时代的类比
    
    Args:
        text: 原始文本
        era: 目标时代
    
    Returns:
        翻译后的文本
    """
    translations = ERA_TRANSLATIONS.get(era, {})
    result = text
    for modern, ancient in translations.items():
        result = result.replace(modern, ancient)
    return result


# 测试用例
if __name__ == "__main__":
    # 测试1：芒格的立场阐述Prompt V3
    prompt1 = build_expert_speak_prompt_v3(
        expert_name="芒格",
        topic="AI时代的工作替代",
        round_type="stance",
        emotion="calm",
    )
    print("测试1 - 芒格立场阐述Prompt V3:")
    print(prompt1[:600])
    print("...")
    
    # 测试2：老子的反驳Prompt V3
    prompt2 = build_expert_speak_prompt_v3(
        expert_name="老子",
        topic="无为而治 vs 积极干预",
        round_type="rebuttal",
        opponent_statement="无为而治是消极的，应该积极干预",
        emotion="calm",
    )
    print("\n测试2 - 老子反驳Prompt V3:")
    print(prompt2[:600])
    print("...")
