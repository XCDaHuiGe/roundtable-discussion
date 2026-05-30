# -*- coding: utf-8 -*-
"""
深度训练引擎 V9.0 — Agent=LLM，Python=机械操作

核心设计：
  - Agent（你）本身就是LLM，负责搜索、阅读、生成辩论
  - Python模块只做机械操作：评分、提取、升级、保存
  - 不依赖任何外部LLM API（call_llm_json已删除）

Agent执行流程：
  1. Agent调用 step1_generate_topics() → 获取话题列表
  2. Agent自己用WebSearch/AnySearch搜索 → 采集素材
  3. Agent自己阅读专家档案 → 理解专家风格
  4. Agent自己生成辩论JSON → 传入step4评分
  5. Agent调用 step4_score_and_extract() → 机械评分+提取
  6. Agent调用 step5_upgrade_experts() → 机械升级档案
  7. Agent调用 save_training_result() → 机械保存

CLI模式（调试用）：
  python auto_train.py --check           # 检查同质化
  python auto_train.py --step1 --rounds 3 # 只生成话题
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'training'))

from training.debate_arena import DebateArena, DebateTopic
from training.fusion_engine import FusionEngine
from scorer_v3 import score_v3
from training.llm_extractor import LLMStrategyExtractor

EXPERT_LIBRARY = os.path.join(os.path.dirname(__file__), '..', 'expert-library')
MEMORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory')


# ═══════════════════════════════════════════════════════════════
#  Phase 1: 生成话题（机械操作）
# ═══════════════════════════════════════════════════════════════

def step1_generate_topics(rounds: int = 5, experts: List[str] = None) -> List[Dict]:
    """从专家信念冲突中生成话题（机械操作）"""
    arena = DebateArena(EXPERT_LIBRARY)

    if experts:
        all_topics = arena.generate_topics(count=rounds * 3, prefer_strong=True)
        filtered = [t for t in all_topics if t.expert1 in experts or t.expert2 in experts]
        topics = filtered[:rounds]
    else:
        topics = arena.generate_topics(count=rounds, prefer_strong=True)

    result = []
    for t in topics:
        result.append({
            'expert1': t.expert1,
            'expert2': t.expert2,
            'topic': t.topic,
            'belief1': t.belief1,
            'belief2': t.belief2,
            'conflict_type': t.conflict_type,
            'strength': t.strength,
            'keywords': _extract_keywords(t.topic),
        })
    return result


def _extract_keywords(topic_text: str) -> str:
    clean = re.sub(r'["""]', '', topic_text)
    clean = re.sub(r'[？！。，、；：]', ' ', clean)
    parts = clean.split('vs')
    if len(parts) == 2:
        return parts[0].strip()[:30]
    return ' '.join(clean.split()[:6])


# ═══════════════════════════════════════════════════════════════
#  Phase 2: 素材合并（机械操作）
#  注意：搜索由Agent自己执行，这里只做合并
# ═══════════════════════════════════════════════════════════════

def step2_build_material(search_snippets: str = "",
                         zhihu_snippets: str = "") -> str:
    """合并搜索素材为文本（机械操作）"""
    parts = []

    if search_snippets:
        parts.append(f"=== WebSearch 素材 ===\n{search_snippets[:1500]}")

    if zhihu_snippets:
        parts.append(f"=== 知乎素材 ===\n{zhihu_snippets[:500]}")

    return '\n\n'.join(parts)[:2000]


# ═══════════════════════════════════════════════════════════════
#  Phase 3: 辩论模板构建（机械操作）
#  注意：辩论内容由Agent自己生成，这里只提供模板
# ═══════════════════════════════════════════════════════════════

def step3_build_debate_template(topic: Dict) -> str:
    """构建辩论JSON模板（机械操作），Agent填充内容"""
    template = {
        "topic": topic['topic'],
        "experts": [topic['expert1'], topic['expert2']],
        "source_material": {"has_material": False, "material_preview": ""},
        "rounds": [
            {
                "round_number": 1,
                "round_name": "立场阐述",
                "synthesis": {"summary": "", "consensus": [], "disagreements": []},
                "speeches": [
                    {"expert": topic['expert1'], "stance": "", "content": "", "evidence": [], "quote": "", "emotion": "serious"},
                    {"expert": topic['expert2'], "stance": "", "content": "", "evidence": [], "quote": "", "emotion": "serious"}
                ]
            },
            {
                "round_number": 2,
                "round_name": "相互质疑",
                "synthesis": {"summary": "", "consensus": [], "disagreements": []},
                "speeches": [
                    {"expert": topic['expert1'], "target": topic['expert2'], "attack_type": "", "content": "", "evidence": []},
                    {"expert": topic['expert2'], "target": topic['expert1'], "attack_type": "", "content": "", "evidence": []}
                ]
            },
            {
                "round_number": 3,
                "round_name": "回应辩护",
                "synthesis": {"summary": "", "consensus": [], "disagreements": []},
                "speeches": [
                    {"expert": topic['expert1'], "content": "", "defense_success_rate": 70},
                    {"expert": topic['expert2'], "content": "", "defense_success_rate": 65}
                ]
            },
            {
                "round_number": 4,
                "round_name": "认知升级",
                "synthesis": {"summary": "", "consensus": [], "disagreements": []},
                "speeches": [
                    {"expert": topic['expert1'], "old_view": "", "new_view": "", "trigger": "", "content": ""},
                    {"expert": topic['expert2'], "old_view": "", "new_view": "", "trigger": "", "content": ""}
                ]
            }
        ],
        "clash_rounds": [
            {"attacker": topic['expert1'], "target": topic['expert2'], "attack_type": "", "attack_content": "", "counter_attack": ""}
        ],
        "key_quotes": [
            {"expert": topic['expert1'], "quote": "", "impact": "high"},
            {"expert": topic['expert2'], "quote": "", "impact": "high"}
        ]
    }
    return json.dumps(template, ensure_ascii=False, indent=2)


def get_expert_profile(expert_name: str) -> Optional[Dict]:
    """获取专家档案信息（机械操作）"""
    arena = DebateArena(EXPERT_LIBRARY)
    profile = arena.get_expert_profile(expert_name)
    if not profile:
        return None
    return {
        'name': profile.name,
        'beliefs': profile.beliefs[:3],
        'values': profile.values[:2],
        'thinking_style': profile.thinking_style,
        'argument_style': profile.argument_style,
    }


# ═══════════════════════════════════════════════════════════════
#  Phase 4: 评分 + 提取（机械操作）
# ═══════════════════════════════════════════════════════════════

def step4_score_and_extract(debate_json: Dict, scores: Dict = None) -> Dict:
    """评分和策略提取（机械操作）

    Args:
        debate_json: 辩论JSON
        scores: Agent传入的6维度分数（可选，未传入时使用默认分数）

    Returns:
        {"score": {"total": 68.5, "grade": "C"}, "extraction": {...}}
    """
    from scorer_v3 import default_scores

    result = {'score': {}, 'extraction': {}}

    temp_path = os.path.join(MEMORY_DIR, '_temp_debate.json')
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(debate_json, f, ensure_ascii=False, indent=2)

    try:
        scores_input = scores or default_scores()
        result['score'] = score_v3(scores_input)
    except Exception as e:
        result['score'] = {'total': 0, 'grade': 'F', 'error': str(e)}

    try:
        extractor = LLMStrategyExtractor()
        result['extraction'] = extractor.extract(temp_path)
    except Exception as e:
        result['extraction'] = {'experts': {}, 'error': str(e)}

    if os.path.exists(temp_path):
        os.remove(temp_path)

    return result


# ═══════════════════════════════════════════════════════════════
#  Phase 5: 升级专家（机械操作）
# ═══════════════════════════════════════════════════════════════

def step5_upgrade_experts(extraction: Dict, score_total: float) -> Dict:
    """融合增强式升级专家档案（机械操作）"""
    engine = FusionEngine(EXPERT_LIBRARY)
    upgrades = {}

    for expert_name, expert_data in extraction.get('experts', {}).items():
        strategy = {
            'attack_strategy': expert_data.get('attack_strategy', {}),
            'defense_weakness': expert_data.get('defense_weakness', {}),
            'style_fingerprint': expert_data.get('style_fingerprint', {}),
            'evidence_preference': expert_data.get('evidence_preference', {}),
            'interaction_pattern': expert_data.get('interaction_pattern', {}),
        }
        md_path = engine.find_expert_md(expert_name)
        if not md_path:
            continue
        try:
            engine.upgrade_expert(md_path, strategy, score_total)
            upgrades[expert_name] = True
        except Exception:
            pass

    return upgrades


# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def save_training_result(topic: Dict, material_text: str,
                         debate_json: Dict, score: Dict,
                         extraction: Dict, upgrades: Dict,
                         round_num: int = 1) -> str:
    """保存训练结果（机械操作）"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    path = os.path.join(MEMORY_DIR,
        f'deep_training_round{round_num}_{topic["expert1"]}_{topic["expert2"]}.json')

    record = {
        '训练轮次': f'第{round_num}轮',
        '话题': topic['topic'],
        '专家': [topic['expert1'], topic['expert2']],
        '核心冲突': f'{topic["belief1"]} ↔ {topic["belief2"]}',
        '素材长度': len(material_text),
        '辩论': debate_json,
        '评分': score,
        '策略提取': extraction,
        '专家升级': upgrades,
        '保存时间': datetime.now().isoformat(),
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return path


HOMOGENEOUS_VALUES = "专业能力/独立判断/持续学习"
HOMOGENEOUS_FRAMEWORK = "先看事实：发生了什么，数据怎么说？"
TEMPLATE_QUOTE_PATTERN = "我们再深一层。你说"


def check_homogeneity() -> list:
    """检查同质化（机械操作）"""
    issues = []
    experts_dir = os.path.join(EXPERT_LIBRARY, 'experts')

    for cat in ['philosophy', 'psychology', 'sociology', 'literature', 'economics']:
        cat_dir = os.path.join(experts_dir, cat)
        if not os.path.isdir(cat_dir):
            continue
        for f in os.listdir(cat_dir):
            if not f.endswith('.md'):
                continue
            path = os.path.join(cat_dir, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            name = f[:-3]

            if HOMOGENEOUS_VALUES in content:
                issues.append({'expert': name, 'category': cat, 'type': '同质化价值排序', 'severity': 'HIGH'})
            if HOMOGENEOUS_FRAMEWORK in content:
                issues.append({'expert': name, 'category': cat, 'type': '同质化分析框架', 'severity': 'HIGH'})
            if TEMPLATE_QUOTE_PATTERN in content:
                issues.append({'expert': name, 'category': cat, 'type': '模板化金句', 'severity': 'MEDIUM'})

    return issues


def print_homogeneity_report(issues: list):
    print(f"\n{'='*60}")
    print(f"  专家库质量报告")
    print(f"{'='*60}")

    high = [i for i in issues if i['severity'] == 'HIGH']
    medium = [i for i in issues if i['severity'] == 'MEDIUM']
    print(f"\n问题总数: {len(issues)} (HIGH: {len(high)}, MEDIUM: {len(medium)})")

    if high:
        print(f"\n--- HIGH ---")
        for i in high:
            print(f"  [{i['category']}] {i['expert']}: {i['type']}")
    if medium:
        print(f"\n--- MEDIUM ---")
        for i in medium:
            print(f"  [{i['category']}] {i['expert']}: {i['type']}")

    if not issues:
        print(f"\n  ✅ 无同质化问题")
    print(f"{'='*60}")


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='深度训练引擎 V9.0')
    parser.add_argument('--check', action='store_true', help='检查同质化')
    parser.add_argument('--step1', action='store_true', help='生成话题')
    parser.add_argument('--rounds', type=int, default=5, help='轮次')
    parser.add_argument('--experts', type=str, default=None, help='指定专家')
    parser.add_argument('--template', action='store_true', help='生成辩论模板')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    if args.check:
        issues = check_homogeneity()
        print_homogeneity_report(issues)
        return

    if args.step1:
        experts = args.experts.split(',') if args.experts else None
        topics = step1_generate_topics(args.rounds, experts)
        for i, t in enumerate(topics, 1):
            print(f"[{i}] {t['expert1']} vs {t['expert2']}")
            print(f"    话题: {t['topic']}")
            print(f"    冲突: {t['belief1'][:30]} ↔ {t['belief2'][:30]}")
            print(f"    关键词: {t['keywords']}")
        return

    if args.template:
        topics = step1_generate_topics(1)
        if topics:
            template = step3_build_debate_template(topics[0])
            print(template)
        return

    parser.print_help()


if __name__ == '__main__':
    main()