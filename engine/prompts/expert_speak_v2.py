# -*- coding: utf-8 -*-
"""
专家发言Prompt模板 V2
遵循知识边界原则
"""
from __future__ import annotations

from typing import Dict, Optional

from engine.knowledge_boundary_checker import (
    get_boundary,
    generate_expert_prompt_context,
)


def build_expert_speak_prompt(
    expert_name: str,
    topic: str,
    round_type: str = "stance",
    opponent_statement: Optional[str] = None,
    emotion: str = "calm",
) -> str:
    """
    构建专家发言Prompt
    
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
        return _build_stance_prompt(context, expert_name, topic, emotion)
    elif round_type == "question":
        return _build_question_prompt(context, expert_name, topic, emotion)
    elif round_type == "rebuttal":
        return _build_rebuttal_prompt(context, expert_name, topic, opponent_statement, emotion)
    elif round_type == "synthesis":
        return _build_synthesis_prompt(context, expert_name, topic, emotion)
    else:
        return _build_stance_prompt(context, expert_name, topic, emotion)


def _build_stance_prompt(context: str, expert_name: str, topic: str, emotion: str) -> str:
    """立场阐述轮Prompt"""
    return f"""{context}

话题：{topic}

任务：作为{expert_name}，阐述你对这个话题的核心立场。

要求：
1. 用你最擅长的分析框架来分析这个话题
2. 用你会用的比喻和案例（不要用超出你时代的案例）
3. 给出一个"像你会说的"金句
4. 保持你一贯的表达风格

情绪：{emotion}

输出格式：
先用1-2句话说明你的核心立场，然后展开分析，最后用金句收尾。
"""


def _build_question_prompt(context: str, expert_name: str, topic: str, emotion: str) -> str:
    """相互质疑轮Prompt"""
    return f"""{context}

话题：{topic}

任务：作为{expert_name}，向对手提出一个尖锐的问题。

要求：
1. 问题必须基于你自己的知识体系
2. 问题要能揭示对手立场的漏洞
3. 用你会用的比喻来提问
4. 问题要具体，不要太抽象

情绪：{emotion}

输出格式：
一个尖锐的问题，不超过2句话。
"""


def _build_rebuttal_prompt(
    context: str,
    expert_name: str,
    topic: str,
    opponent_statement: Optional[str],
    emotion: str,
) -> str:
    """反驳轮Prompt"""
    if not opponent_statement:
        return _build_stance_prompt(context, expert_name, topic, emotion)
    
    return f"""{context}

话题：{topic}

对手发言：
「{opponent_statement}」

任务：作为{expert_name}，反驳对手的观点。

要求：
1. 先承认对手说得对的部分（1句话）
2. 用你自己的知识体系来反驳（不要借用别人的理论）
3. 用一个具体的案例或比喻来支持你的反驳
4. 最后用一句金句总结你的立场

禁止：
- 不要使用禁用词
- 不要引用其他专家的核心概念
- 不要为了反驳而反驳

情绪：{emotion}

输出格式：
先承认，再反驳，再举例，再金句。
"""


def _build_synthesis_prompt(context: str, expert_name: str, topic: str, emotion: str) -> str:
    """认知升华轮Prompt"""
    return f"""{context}

话题：{topic}

任务：作为{expert_name}，总结这次讨论给你的启发。

要求：
1. 承认对手说得有道理的地方
2. 说明这次讨论如何深化了你的理解
3. 用你自己的知识体系来整合新见解
4. 给出一个"升华后的"金句

情绪：{emotion}

输出格式：
先承认，再深化，再整合，再金句。
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
    # 测试1：老子的立场阐述Prompt
    prompt1 = build_expert_speak_prompt(
        expert_name="老子",
        topic="AI时代的工作替代",
        round_type="stance",
        emotion="calm",
    )
    print("测试1 - 老子立场阐述Prompt:")
    print(prompt1[:500])
    print("...")
    
    # 测试2：芒格的反驳Prompt
    prompt2 = build_expert_speak_prompt(
        expert_name="芒格",
        topic="道德与能力哪个更重要",
        round_type="rebuttal",
        opponent_statement="道德是门槛，能力是加分项",
        emotion="serious",
    )
    print("\n测试2 - 芒格反驳Prompt:")
    print(prompt2[:500])
    print("...")
    
    # 测试3：时代翻译
    text = "AI的算法效率很高，自动化程度很高"
    translated = translate_to_era(text, "春秋时期")
    print(f"\n测试3 - 时代翻译:")
    print(f"  原文: {text}")
    print(f"  翻译: {translated}")
