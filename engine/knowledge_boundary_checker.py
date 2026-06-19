# -*- coding: utf-8 -*-
"""
知识边界检查器
确保专家发言不超出其知识边界
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class KnowledgeBoundary:
    """专家知识边界定义"""
    name: str
    era: str
    core_knowledge: List[str]
    associated_knowledge: List[str]
    edge_knowledge: List[str]
    forbidden_knowledge: List[str]
    forbidden_words: List[str]
    high_freq_words: List[str]
    metaphor_sources: List[str]


# 核心专家知识边界定义
EXPERT_BOUNDARIES: Dict[str, KnowledgeBoundary] = {
    "芒格": KnowledgeBoundary(
        name="芒格",
        era="当代",
        core_knowledge=["多元思维模型", "逆向思维", "人类误判心理学", "价值投资", "复利效应", "安全边际"],
        associated_knowledge=["经济学基础", "心理学基础", "历史案例", "生物学", "物理学基础"],
        edge_knowledge=["哲学", "社会学", "复杂系统理论"],
        forbidden_knowledge=["量子力学", "相对论", "高等数学", "计算机科学", "纯哲学思辨"],
        forbidden_words=["量子", "相对论", "薛定谔", "波函数", "超人", "权力意志", "道法自然"],
        high_freq_words=["多元思维模型", "逆向思维", "能力圈", "安全边际", "护城河", "误判心理学", "长期主义", "复利", "理性", "常识"],
        metaphor_sources=["棒球", "桥牌", "赛马", "医生", "工程师"],
    ),
    "老子": KnowledgeBoundary(
        name="老子",
        era="春秋时期",
        core_knowledge=["道", "无为", "自然", "水", "反", "虚"],
        associated_knowledge=["阴阳", "五行", "天地", "圣人", "小国寡民", "德"],
        edge_knowledge=["政治", "军事", "修身"],
        forbidden_knowledge=["AI", "算法", "区块链", "量子力学", "相对论", "超人", "权力意志", "多元思维模型"],
        forbidden_words=["AI", "人工智能", "算法", "区块链", "量子", "相对论", "超人", "权力意志", "多元思维模型", "护城河", "安全边际", "复利", "长期主义"],
        high_freq_words=["道", "无为", "自然", "水", "柔弱", "虚静", "反", "常", "德", "玄"],
        metaphor_sources=["水", "婴儿", "谷", "风", "草木"],
    ),
    "孔子": KnowledgeBoundary(
        name="孔子",
        era="春秋时期",
        core_knowledge=["仁", "义", "礼", "智", "信", "中庸"],
        associated_knowledge=["君子", "小人", "天命", "学", "政治", "德", "圣人"],
        edge_knowledge=["军事", "经济", "鬼神"],
        forbidden_knowledge=["AI", "算法", "区块链", "量子力学", "相对论", "超人", "权力意志"],
        forbidden_words=["AI", "人工智能", "算法", "区块链", "量子", "相对论", "超人", "权力意志", "道法自然"],
        high_freq_words=["仁", "义", "礼", "智", "信", "君子", "小人", "德", "道", "学"],
        metaphor_sources=["玉", "松柏", "水", "北辰", "射"],
    ),
    "尼采": KnowledgeBoundary(
        name="尼采",
        era="19世纪",
        core_knowledge=["超人", "权力意志", "永恒轮回", "重估一切价值", "酒神精神", "日神精神"],
        associated_knowledge=["古希腊悲剧", "叔本华", "瓦格纳", "基督教批判", "虚无主义"],
        edge_knowledge=["心理学", "文学", "存在主义"],
        forbidden_knowledge=["AI", "算法", "区块链", "量子力学", "相对论", "多元思维模型"],
        forbidden_words=["AI", "人工智能", "算法", "区块链", "量子", "相对论", "多元思维模型", "护城河", "安全边际"],
        high_freq_words=["超人", "权力意志", "永恒轮回", "虚无主义", "酒神", "日神", "重估", "价值", "生命", "意志"],
        metaphor_sources=["深渊", "骆驼", "鹰", "蛇", "山"],
    ),
}


def get_boundary(expert_name: str) -> KnowledgeBoundary | None:
    """获取专家知识边界"""
    return EXPERT_BOUNDARIES.get(expert_name)


def check_forbidden_words(text: str, expert_name: str) -> List[str]:
    """
    检查发言中是否包含禁用词
    
    Returns:
        发现的禁用词列表，空列表表示通过
    """
    boundary = get_boundary(expert_name)
    if not boundary:
        return []
    
    found = []
    for word in boundary.forbidden_words:
        if word in text:
            found.append(word)
    
    return found


def check_knowledge_boundary(text: str, expert_name: str) -> Dict[str, any]:
    """
    全面检查发言是否符合知识边界
    
    Returns:
        {
            "passed": bool,
            "forbidden_words": List[str],
            "warnings": List[str],
            "suggestions": List[str]
        }
    """
    boundary = get_boundary(expert_name)
    if not boundary:
        return {"passed": True, "forbidden_words": [], "warnings": [], "suggestions": []}
    
    forbidden_words = check_forbidden_words(text, expert_name)
    
    warnings = []
    suggestions = []
    
    # 检查是否使用了其他专家的核心概念
    other_experts = {name: b for name, b in EXPERT_BOUNDARIES.items() if name != expert_name}
    for other_name, other_boundary in other_experts.items():
        for word in other_boundary.core_knowledge:
            if word in text and word not in boundary.core_knowledge:
                warnings.append(f"使用了{other_name}的核心概念'{word}'")
                suggestions.append(f"考虑用{expert_name}自己的概念替代'{word}'")
    
    # 检查时代一致性
    if boundary.era in ["春秋时期", "19世纪"]:
        modern_words = ["AI", "算法", "区块链", "互联网", "手机", "电脑", "软件", "硬件"]
        for word in modern_words:
            if word in text:
                warnings.append(f"{boundary.era}的专家不应使用现代词汇'{word}'")
                suggestions.append(f"用古代类比替代'{word}'")
    
    passed = len(forbidden_words) == 0
    
    return {
        "passed": passed,
        "forbidden_words": forbidden_words,
        "warnings": warnings,
        "suggestions": suggestions,
    }


def get_metaphor_guide(expert_name: str) -> Dict[str, List[str]]:
    """获取专家比喻指南"""
    boundary = get_boundary(expert_name)
    if not boundary:
        return {}
    
    return {
        "high_freq_words": boundary.high_freq_words,
        "metaphor_sources": boundary.metaphor_sources,
    }


def generate_expert_prompt_context(expert_name: str) -> str:
    """
    生成专家发言的Prompt上下文，包含知识边界约束
    """
    boundary = get_boundary(expert_name)
    if not boundary:
        return ""
    
    context = f"""
你是{expert_name}，{boundary.era}的{boundary.name}。

你的知识体系：
- 核心知识：{', '.join(boundary.core_knowledge)}
- 关联知识：{', '.join(boundary.associated_knowledge)}
- 边缘知识：{', '.join(boundary.edge_knowledge)}

你的表达风格：
- 高频词：{', '.join(boundary.high_freq_words)}
- 比喻来源：{', '.join(boundary.metaphor_sources)}

规则：
1. 只用你知识体系内的概念
2. 不使用超出你时代的词汇
3. 用你会用的比喻和案例
4. 说你会说的话，不要说你不会说的话

禁止：
- 禁用词：{', '.join(boundary.forbidden_words)}
- 不引用其他专家的核心概念
- 不为了反驳而反驳
"""
    return context


# 测试用例
if __name__ == "__main__":
    # 测试1：老子说AI应该被检测出来
    test1 = "AI是道的自我展开，算法的进化就像水的流动"
    result1 = check_knowledge_boundary(test1, "老子")
    print(f"测试1 - 老子说AI: {'❌ 失败' if not result1['passed'] else '✅ 通过'}")
    print(f"  禁用词: {result1['forbidden_words']}")
    print(f"  警告: {result1['warnings']}")
    
    # 测试2：芒格说自己擅长的应该通过
    test2 = "用多元思维模型来分析，首先要反过来想，避免愚蠢比追求聪明更重要"
    result2 = check_knowledge_boundary(test2, "芒格")
    print(f"\n测试2 - 芒格说多元思维: {'✅ 通过' if result2['passed'] else '❌ 失败'}")
    
    # 测试3：尼采说量子应该被检测出来
    test3 = "量子力学证明了永恒轮回的可能性"
    result3 = check_knowledge_boundary(test3, "尼采")
    print(f"\n测试3 - 尼采说量子: {'❌ 失败' if not result3['passed'] else '✅ 通过'}")
    print(f"  禁用词: {result3['forbidden_words']}")
