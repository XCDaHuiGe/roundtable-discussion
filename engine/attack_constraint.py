# -*- coding: utf-8 -*-
"""
交锋约束机制
确保反驳基于自己的知识体系，不乱引用
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from engine.knowledge_boundary_checker import (
    check_forbidden_words,
    check_knowledge_boundary,
    get_boundary,
    EXPERT_BOUNDARIES,
)


# ─── 交锋验证 ──────────────────────────────────────────────

def validate_attack(
    attacker: str,
    target: str,
    attack_content: str,
) -> Tuple[bool, str, List[str]]:
    """
    验证攻击是否合理
    
    Args:
        attacker: 攻击者姓名
        target: 被攻击者姓名
        attack_content: 攻击内容
    
    Returns:
        (是否合理, 原因, 违规列表)
    """
    violations = []
    
    # 1. 检查攻击者是否使用了禁用词
    forbidden = check_forbidden_words(attack_content, attacker)
    if forbidden:
        violations.append(f"使用了禁用词: {', '.join(forbidden)}")
    
    # 2. 检查是否引用了其他专家的核心概念
    other_concepts = _check_other_expert_concepts(attack_content, attacker)
    if other_concepts:
        violations.append(f"引用了其他专家概念: {', '.join(other_concepts)}")
    
    # 3. 检查是否使用了自己的知识体系
    own_concepts = _check_own_concepts(attack_content, attacker)
    if not own_concepts:
        violations.append(f"未使用{attacker}自己的核心概念")
    
    # 4. 检查攻击是否与目标相关
    relevance = _check_relevance(attack_content, target)
    if not relevance:
        violations.append(f"攻击内容与{target}无关")
    
    is_valid = len(violations) == 0
    reason = "攻击合理" if is_valid else "; ".join(violations)
    
    return is_valid, reason, violations


def _check_other_expert_concepts(text: str, expert_name: str) -> List[str]:
    """检查是否引用了其他专家的核心概念"""
    boundary = get_boundary(expert_name)
    if not boundary:
        return []
    
    found = []
    for other_name, other_boundary in EXPERT_BOUNDARIES.items():
        if other_name == expert_name:
            continue
        for concept in other_boundary.core_knowledge:
            if concept in text and concept not in boundary.core_knowledge:
                found.append(f"{concept}({other_name})")
    
    return found


def _check_own_concepts(text: str, expert_name: str) -> List[str]:
    """检查是否使用了自己的核心概念"""
    boundary = get_boundary(expert_name)
    if not boundary:
        return []
    
    found = []
    for concept in boundary.core_knowledge:
        if concept in text:
            found.append(concept)
    
    return found


def _check_relevance(text: str, target: str) -> bool:
    """检查攻击是否与目标相关"""
    # 简单检查：攻击内容是否包含目标姓名或相关概念
    if target in text:
        return True
    
    target_boundary = get_boundary(target)
    if not target_boundary:
        return True  # 无边界定义，默认相关
    
    # 检查是否引用了目标的核心概念
    for concept in target_boundary.core_knowledge:
        if concept in text:
            return True
    
    return False


# ─── 交锋约束注入 ──────────────────────────────────────────────

def get_attack_constraints(attacker: str, target: str) -> str:
    """
    获取交锋约束，用于注入Prompt
    
    Returns:
        格式化的约束文本
    """
    attacker_boundary = get_boundary(attacker)
    target_boundary = get_boundary(target)
    
    if not attacker_boundary or not target_boundary:
        return ""
    
    # 计算知识重叠
    overlap = set(attacker_boundary.core_knowledge) & set(target_boundary.core_knowledge)
    
    constraints = f"""
【交锋约束 - {attacker} vs {target}】

攻击者（{attacker}）规则：
- 核心知识：{', '.join(attacker_boundary.core_knowledge)}
- 禁用词：{', '.join(attacker_boundary.forbidden_words)}
- 必须使用：至少1个{attacker}的核心概念
- 禁止使用：{target}的核心概念（{', '.join(target_boundary.core_knowledge)}）

知识重叠：
- 共同概念：{', '.join(overlap) if overlap else '无'}
- 重叠度：{len(overlap)}/{len(attacker_boundary.core_knowledge)}

攻击要求：
1. 必须基于{attacker}自己的知识体系
2. 不能引用{target}的核心概念
3. 攻击要与{target}的立场相关
4. 要有具体的案例或比喻支持
"""
    return constraints


def get_defense_constraints(defender: str, attacker: str) -> str:
    """
    获取防御约束，用于注入Prompt
    
    Returns:
        格式化的约束文本
    """
    defender_boundary = get_boundary(defender)
    attacker_boundary = get_boundary(attacker)
    
    if not defender_boundary or not attacker_boundary:
        return ""
    
    constraints = f"""
【防御约束 - {defender} vs {attacker}】

防御者（{defender}）规则：
- 核心知识：{', '.join(defender_boundary.core_knowledge)}
- 禁用词：{', '.join(defender_boundary.forbidden_words)}
- 必须使用：至少1个{defender}的核心概念
- 禁止使用：{attacker}的核心概念（{', '.join(attacker_boundary.core_knowledge)}）

防御要求：
1. 必须基于{defender}自己的知识体系
2. 不能引用{attacker}的核心概念
3. 要承认对手说得有道理的部分
4. 要有具体的案例或比喻支持反驳
"""
    return constraints


# ─── 辩论配对推荐 ──────────────────────────────────────────────

def recommend_debate_pairs(
    topic: str,
    available_experts: List[str],
    count: int = 3,
) -> List[Tuple[str, str, str]]:
    """
    推荐辩论配对
    
    Args:
        topic: 话题
        available_experts: 可用专家列表
        count: 推荐数量
    
    Returns:
        [(expert1, expert2, reason), ...]
    """
    pairs = []
    
    for i, e1 in enumerate(available_experts):
        for e2 in available_experts[i+1:]:
            # 检查兼容性
            is_compatible, reason = _check_pair_compatibility(e1, e2)
            if is_compatible:
                # 检查话题相关性
                relevance = _check_topic_relevance(e1, e2, topic)
                if relevance:
                    pairs.append((e1, e2, f"{reason}; {relevance}"))
    
    # 按优先级排序（知识重叠度高的优先）
    pairs.sort(key=lambda x: _get_overlap_score(x[0], x[1]), reverse=True)
    
    return pairs[:count]


def _check_pair_compatibility(e1: str, e2: str) -> Tuple[bool, str]:
    """检查两个专家是否兼容"""
    b1 = get_boundary(e1)
    b2 = get_boundary(e2)
    
    if not b1 or not b2:
        return True, "知识边界未定义"
    
    # 检查时代兼容性
    if b1.era != b2.era:
        return True, f"跨时代辩论（{b1.era} vs {b2.era}）"
    
    # 检查知识重叠
    overlap = set(b1.core_knowledge) & set(b2.core_knowledge)
    if len(overlap) < 1:
        return False, "知识重叠度太低"
    
    return True, f"知识重叠: {', '.join(overlap)}"


def _check_topic_relevance(e1: str, e2: str, topic: str) -> str:
    """检查话题相关性"""
    b1 = get_boundary(e1)
    b2 = get_boundary(e2)
    
    if not b1 or not b2:
        return "话题相关"
    
    # 检查话题是否与专家的核心知识相关
    e1_relevant = any(k in topic for k in b1.core_knowledge)
    e2_relevant = any(k in topic for k in b2.core_knowledge)
    
    if e1_relevant and e2_relevant:
        return f"话题与{e1}和{e2}都相关"
    elif e1_relevant:
        return f"话题主要与{e1}相关"
    elif e2_relevant:
        return f"话题主要与{e2}相关"
    else:
        return "话题与两位专家都相关"


def _get_overlap_score(e1: str, e2: str) -> int:
    """计算知识重叠分数"""
    b1 = get_boundary(e1)
    b2 = get_boundary(e2)
    
    if not b1 or not b2:
        return 0
    
    overlap = set(b1.core_knowledge) & set(b2.core_knowledge)
    return len(overlap)


# 测试
if __name__ == "__main__":
    # 测试1：验证攻击
    print("测试1 - 验证攻击:")
    is_valid, reason, violations = validate_attack(
        attacker="芒格",
        target="老子",
        attack_content="你说的道法自然，在投资领域就是能力圈的概念",
    )
    print(f"  有效: {is_valid}")
    print(f"  原因: {reason}")
    if violations:
        print(f"  违规: {violations}")
    
    # 测试2：获取攻击约束
    print("\n测试2 - 获取攻击约束:")
    constraints = get_attack_constraints("芒格", "老子")
    print(constraints[:400])
    print("...")
    
    # 测试3：推荐辩论配对
    print("\n测试3 - 推荐辩论配对:")
    pairs = recommend_debate_pairs(
        topic="道与仁的冲突",
        available_experts=["老子", "孔子", "芒格", "尼采"],
        count=2,
    )
    for e1, e2, reason in pairs:
        print(f"  {e1} vs {e2}: {reason}")
