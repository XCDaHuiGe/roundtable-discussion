# -*- coding: utf-8 -*-
"""
知识边界检查器
确保专家发言不超出其知识边界
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass


EXPERT_LIBRARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'expert-library')

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


def _parse_boundary_md(md_text: str, expert_name: str) -> KnowledgeBoundary:
    """从 _知识边界.md 文件解析出 KnowledgeBoundary

    解析逻辑：按 ## 分节，按 - 提取列表项。
    """
    def _extract_list(section_text: str, heading: str) -> List[str]:
        """从某节中提取 - 开头的列表项"""
        items = []
        in_section = False
        for line in section_text.split('\n'):
            line = line.strip()
            if line.startswith('###') and heading in line:
                in_section = True
                continue
            if in_section and line.startswith('###'):
                break  # 到了下一个子节
            if in_section and line.startswith('- '):
                # 去掉括号里的解释，只保留主词
                item = line[2:].strip()
                # "道（万物本源、自然规律）" → "道"
                item = re.split(r'[（(]', item)[0].strip()
                if item:
                    # "AI、人工智能" → ["AI", "人工智能"]
                    for part in re.split(r'[、,，]', item):
                        part = part.strip()
                        if part:
                            items.append(part)
        return items

    def _extract_section(md: str, heading: str) -> str:
        """提取 ## 某节的全部内容"""
        pattern = rf'## {re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)'
        m = re.search(pattern, md, re.DOTALL)
        return m.group(1) if m else ""

    # 提取时代
    era_section = _extract_section(md_text, "时代背景")
    era = "当代"
    for line in era_section.split('\n'):
        if '活跃时期' in line:
            if '春秋' in line or '战国' in line:
                era = "春秋时期"
            elif '19世纪' in line or '18' in line:
                era = "19世纪"
            else:
                era = "当代"
            break

    # 提取知识图谱
    knowledge_section = _extract_section(md_text, "知识图谱")
    core = _extract_list(knowledge_section, "核心知识")
    associated = _extract_list(knowledge_section, "关联知识")
    edge = _extract_list(knowledge_section, "边缘知识")
    forbidden = _extract_list(knowledge_section, "禁区知识")

    # 提取表达词汇库
    vocab_section = _extract_section(md_text, "表达词汇库")
    high_freq = _extract_list(vocab_section, "高频词")
    metaphor = _extract_list(vocab_section, "比喻来源")
    forbidden_words = _extract_list(vocab_section, "禁用词")

    return KnowledgeBoundary(
        name=expert_name,
        era=era,
        core_knowledge=core,
        associated_knowledge=associated,
        edge_knowledge=edge,
        forbidden_knowledge=forbidden,
        forbidden_words=forbidden_words,
        high_freq_words=high_freq,
        metaphor_sources=metaphor,
    )


def _load_boundaries_from_md() -> Dict[str, KnowledgeBoundary]:
    """扫描 expert-library/experts/ 下所有 _知识边界.md 文件"""
    boundaries = {}
    experts_dir = os.path.join(EXPERT_LIBRARY, 'experts')
    if not os.path.isdir(experts_dir):
        return boundaries

    for category in os.listdir(experts_dir):
        cat_dir = os.path.join(experts_dir, category)
        if not os.path.isdir(cat_dir):
            continue
        for fname in os.listdir(cat_dir):
            if not fname.endswith('_知识边界.md'):
                continue
            expert_name = fname.replace('_知识边界.md', '')
            md_path = os.path.join(cat_dir, fname)
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()
                boundaries[expert_name] = _parse_boundary_md(md_text, expert_name)
            except Exception:
                pass  # 解析失败跳过，使用硬编码 fallback

    return boundaries


# 启动时加载 md 文件中的边界定义
_MD_BOUNDARIES = _load_boundaries_from_md()


# 核心专家知识边界定义（硬编码 fallback，md 文件优先）
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
    "卡尼曼": KnowledgeBoundary(
        name="卡尼曼",
        era="当代",
        core_knowledge=["系统1", "系统2", "前景理论", "认知偏差", "损失厌恶"],
        associated_knowledge=["行为经济学", "统计学", "神经科学"],
        edge_knowledge=["进化心理学", "社会心理学"],
        forbidden_knowledge=["量子力学", "相对论", "纯数学"],
        forbidden_words=["量子", "相对论", "超人", "权力意志", "道法自然"],
        high_freq_words=["系统1", "系统2", "认知偏差", "损失厌恶", "前景理论", "锚定效应", "过度自信"],
        metaphor_sources=["视觉错觉", "赌博", "医生诊断", "天气预报"],
    ),
    "津巴多": KnowledgeBoundary(
        name="津巴多",
        era="当代",
        core_knowledge=["情境力量", "时间透视", "英雄主义", "平庸之恶", "从众"],
        associated_knowledge=["认知心理学", "社会学", "政治学"],
        edge_knowledge=["进化心理学", "神经科学"],
        forbidden_knowledge=["量子力学", "相对论", "纯数学"],
        forbidden_words=["量子", "相对论", "超人", "权力意志", "道法自然"],
        high_freq_words=["情境力量", "时间透视", "英雄主义", "平庸之恶", "从众", "服从"],
        metaphor_sources=["监狱", "时钟", "镜子", "舞台"],
    ),
    "赫拉利": KnowledgeBoundary(
        name="赫拉利",
        era="当代",
        core_knowledge=["想象的共同体", "认知革命", "农业革命", "数据主义", "人类世"],
        associated_knowledge=["生物学", "哲学", "经济学", "政治学"],
        edge_knowledge=["计算机科学", "神经科学"],
        forbidden_knowledge=["量子力学细节", "相对论细节", "纯数学"],
        forbidden_words=["量子", "相对论", "超人", "权力意志", "道法自然"],
        high_freq_words=["想象的共同体", "叙事", "认知革命", "数据主义", "人类世", "智人"],
        metaphor_sources=["蚂蚁", "病毒", "算法", "宗教"],
    ),
}


def get_boundary(expert_name: str) -> KnowledgeBoundary | None:
    """获取专家知识边界（md 文件优先，硬编码 fallback）"""
    if expert_name in _MD_BOUNDARIES:
        return _MD_BOUNDARIES[expert_name]
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
    all_boundaries = {**EXPERT_BOUNDARIES, **_MD_BOUNDARIES}
    other_experts = {name: b for name, b in all_boundaries.items() if name != expert_name}
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
