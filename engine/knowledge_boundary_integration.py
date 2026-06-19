# -*- coding: utf-8 -*-
"""
知识边界集成模块
将知识边界检查器集成到实际辩论生成流程
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from engine.knowledge_boundary_checker import (
    check_knowledge_boundary,
    get_boundary,
    generate_expert_prompt_context,
    KnowledgeBoundary,
)


EXPERT_LIBRARY = Path(__file__).parent.parent / "expert-library" / "experts"


def load_expert_with_boundary(expert_name: str) -> Dict:
    """
    加载专家档案，包含知识边界信息
    
    Returns:
        {
            "name": str,
            "profile": str,  # 原始档案内容
            "boundary": KnowledgeBoundary,  # 知识边界
            "prompt_context": str,  # 用于Prompt的上下文
        }
    """
    # 查找专家文件
    profile_path = _find_expert_file(expert_name)
    if not profile_path:
        return {"name": expert_name, "profile": "", "boundary": None, "prompt_context": ""}
    
    # 读取档案
    profile = profile_path.read_text(encoding="utf-8")
    
    # 获取知识边界
    boundary = get_boundary(expert_name)
    
    # 生成Prompt上下文
    prompt_context = generate_expert_prompt_context(expert_name)
    
    return {
        "name": expert_name,
        "profile": profile,
        "boundary": boundary,
        "prompt_context": prompt_context,
    }


def _find_expert_file(expert_name: str) -> Optional[Path]:
    """查找专家档案文件"""
    for domain_dir in EXPERT_LIBRARY.iterdir():
        if not domain_dir.is_dir():
            continue
        for file in domain_dir.glob("*.md"):
            if file.name.startswith(expert_name) and "知识边界" not in file.name:
                return file
    return None


def validate_debate_content(
    content: Dict,
    experts: List[str],
) -> Dict:
    """
    验证辩论内容是否符合所有专家的知识边界
    
    Args:
        content: 辩论JSON数据
        experts: 专家姓名列表
    
    Returns:
        {
            "valid": bool,
            "violations": List[{
                "expert": str,
                "round": int,
                "type": str,
                "details": str,
                "forbidden_words": List[str],
            }],
            "warnings": List[str],
        }
    """
    violations = []
    warnings = []
    
    rounds = content.get("rounds", [])
    for round_idx, round_data in enumerate(rounds):
        # 检查立场阐述
        for stance in round_data.get("stances", []):
            expert = stance.get("expert", "")
            text = stance.get("stance", "")
            result = check_knowledge_boundary(text, expert)
            
            if not result["passed"]:
                violations.append({
                    "expert": expert,
                    "round": round_idx + 1,
                    "type": "stance",
                    "details": f"使用了禁用词: {', '.join(result['forbidden_words'])}",
                    "forbidden_words": result["forbidden_words"],
                })
            
            if result["warnings"]:
                warnings.extend([f"轮次{round_idx+1} - {expert}: {w}" for w in result["warnings"]])
        
        # 检查交锋
        for clash in round_data.get("clash_rounds", []):
            attacker = clash.get("attacker", "")
            attack_text = clash.get("attack_content", "")
            counter_text = clash.get("counter_attack", "")
            
            # 检查攻击
            result = check_knowledge_boundary(attack_text, attacker)
            if not result["passed"]:
                violations.append({
                    "expert": attacker,
                    "round": round_idx + 1,
                    "type": "attack",
                    "details": f"使用了禁用词: {', '.join(result['forbidden_words'])}",
                    "forbidden_words": result["forbidden_words"],
                })
            
            # 检查反驳
            target = clash.get("target", "")
            result = check_knowledge_boundary(counter_text, target)
            if not result["passed"]:
                violations.append({
                    "expert": target,
                    "round": round_idx + 1,
                    "type": "counter_attack",
                    "details": f"使用了禁用词: {', '.join(result['forbidden_words'])}",
                    "forbidden_words": result["forbidden_words"],
                })
    
    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
    }


def get_expert_debate_constraints(expert_name: str) -> str:
    """
    获取专家辩论约束，用于注入Prompt
    
    Returns:
        格式化的约束文本
    """
    boundary = get_boundary(expert_name)
    if not boundary:
        return ""
    
    return f"""
【{expert_name}的知识边界约束】
- 时代：{boundary.era}
- 核心知识：{', '.join(boundary.core_knowledge)}
- 禁用词：{', '.join(boundary.forbidden_words)}
- 比喻来源：{', '.join(boundary.metaphor_sources)}
- 规则：只用自己知识体系内的概念，不借用其他专家的核心概念
"""


def check_expert_compatibility(expert1: str, expert2: str) -> Tuple[bool, str]:
    """
    检查两位专家是否适合辩论
    
    Returns:
        (适合, 原因)
    """
    boundary1 = get_boundary(expert1)
    boundary2 = get_boundary(expert2)
    
    if not boundary1 or not boundary2:
        return True, "知识边界未定义，允许辩论"
    
    # 检查时代兼容性
    era1 = boundary1.era
    era2 = boundary2.era
    
    if era1 != era2:
        # 跨时代辩论需要翻译层
        if (era1 in ["春秋时期", "19世纪"] and era2 == "当代") or \
           (era2 in ["春秋时期", "19世纪"] and era1 == "当代"):
            return True, f"跨时代辩论（{era1} vs {era2}），需要时代翻译"
    
    # 检查知识重叠（包括语义关联）
    knowledge1 = set(boundary1.core_knowledge + boundary1.associated_knowledge)
    knowledge2 = set(boundary2.core_knowledge + boundary2.associated_knowledge)
    overlap = knowledge1 & knowledge2
    
    # 语义关联映射（概念不同但相关的也算重叠）
    SEMANTIC_LINKS = {
        "道": ["自然", "无为", "德", "天命"],
        "仁": ["义", "礼", "智", "信", "德", "君子", "圣人"],
        "德": ["道", "仁", "君子", "圣人"],
        "超人": ["权力意志", "永恒轮回", "价值"],
        "多元思维模型": ["逆向思维", "能力圈", "理性"],
        "君子": ["仁", "德", "礼", "圣人"],
        "圣人": ["道", "德", "仁", "君子"],
    }
    
    # 扩展重叠检查
    expanded_overlap = set(overlap)
    for concept in knowledge1:
        if concept in SEMANTIC_LINKS:
            for related in SEMANTIC_LINKS[concept]:
                if related in knowledge2:
                    expanded_overlap.add(f"{concept}↔{related}")
    
    if len(expanded_overlap) < 1:
        return False, f"知识重叠度太低（{expert1}: {era1} vs {expert2}: {era2}）"
    
    overlap = expanded_overlap
    
    return True, f"知识重叠: {', '.join(overlap)}"


# 测试
if __name__ == "__main__":
    # 测试1：加载专家档案
    print("测试1 - 加载芒格档案:")
    munger = load_expert_with_boundary("芒格")
    print(f"  名称: {munger['name']}")
    print(f"  边界: {munger['boundary'] is not None}")
    print(f"  Prompt上下文长度: {len(munger['prompt_context'])}")
    
    # 测试2：验证辩论内容
    print("\n测试2 - 验证辩论内容:")
    test_content = {
        "rounds": [
            {
                "stances": [
                    {"expert": "老子", "stance": "AI是道的自我展开，算法就像水的流动"}
                ],
                "clash_rounds": []
            }
        ]
    }
    result = validate_debate_content(test_content, ["老子"])
    print(f"  有效: {result['valid']}")
    print(f"  违规: {len(result['violations'])}")
    if result['violations']:
        print(f"  详情: {result['violations'][0]['details']}")
    
    # 测试3：检查专家兼容性
    print("\n测试3 - 检查专家兼容性:")
    compat, reason = check_expert_compatibility("老子", "孔子")
    print(f"  老子 vs 孔子: {'✅' if compat else '❌'} {reason}")
    
    compat, reason = check_expert_compatibility("老子", "芒格")
    print(f"  老子 vs 芒格: {'✅' if compat else '❌'} {reason}")
