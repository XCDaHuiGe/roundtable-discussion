# -*- coding: utf-8 -*-
"""
深度训练引擎 V8.0 — Agent可调用的步骤函数库

设计原则：
  - SKILL.md 是编排器（Agent按SKILL定义的流程执行）
  - 本文件是函数库（Agent在每一步调用对应的Python函数）
  - WebSearch / 知乎MCP 是Agent工具，由Agent自己调用，结果传入本文件

SKILL流程与本文件的对应关系：
  Phase 1: Agent调用 → step1_generate_topics()     → 返回话题列表
  Phase 2: Agent用WebSearch/MCP搜索，自行采集素材
  Phase 3: Agent调用 → step3_generate_debate()      → 传入搜索素材，返回辩论JSON
  Phase 4: Agent调用 → step4_score_and_extract()    → 返回评分+策略
  Phase 5: Agent调用 → step5_upgrade_experts()       → 更新专家档案

CLI模式（调试/测试用）：
  python auto_train.py --check              # 检查同质化
  python auto_train.py --step1 --rounds 3   # 只跑Phase 1
  python auto_train.py --step3 --debate-file xxx.json  # 只跑Phase 3
  python auto_train.py --all --rounds 5 --skip-search  # 全流程（跳过搜索）
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
from training.zhihu_miner import search_zhihu
from training.fusion_engine import FusionEngine
from training.scorer_v2 import score_discussion as score_v2
from training.llm_extractor import LLMStrategyExtractor
from llm_generate import call_llm_json

EXPERT_LIBRARY = os.path.join(os.path.dirname(__file__), '..', 'expert-library')
MEMORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory')
CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content')


# ═══════════════════════════════════════════════════════════════
#  Phase 1: 生成话题
# ═══════════════════════════════════════════════════════════════

def step1_generate_topics(rounds: int = 5, experts: List[str] = None,
                          expert_library: str = None) -> List[Dict]:
    """
    Phase 1: 从专家信念冲突中生成话题

    Args:
        rounds: 话题数量
        experts: 指定专家名列表（可选）
        expert_library: 专家库路径（可选，默认用项目目录）

    Returns:
        话题列表，每个元素包含:
        {
            "expert1": "孔子", "expert2": "韩非子",
            "topic": "话题标题",
            "belief1": "信念A", "belief2": "信念B",
            "conflict_type": "方法论冲突", "strength": "强",
            "keywords": "搜索关键词"
        }
    """
    lib = expert_library or EXPERT_LIBRARY
    arena = DebateArena(lib)

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
#  Phase 2: 内容采集辅助（知乎MCP）
#  注意：WebSearch是Agent工具，由Agent自行调用
# ═══════════════════════════════════════════════════════════════

def step2_search_zhihu(keywords: str, limit: int = 5) -> Dict:
    """
    Phase 2辅助: 调用知乎MCP搜索

    Args:
        keywords: 搜索关键词（从step1返回的keywords字段获取）
        limit: 结果数量

    Returns:
        {"success": bool, "results": list, "count": int, "error": str|None}
    """
    try:
        result = search_zhihu(keywords, limit=limit)
        if result:
            items = [result] if isinstance(result, str) else result
            return {'success': True, 'results': items, 'count': len(items), 'error': None}
        return {'success': True, 'results': [], 'count': 0, 'error': None}
    except Exception as e:
        return {'success': False, 'results': [], 'count': 0, 'error': str(e)}


def step2_build_material(zhihu_results: List = None,
                         web_search_results: List = None,
                         web_search_snippets: str = None) -> str:
    """
    Phase 2辅助: 合并搜索素材为文本

    Agent采集完WebSearch和知乎MCP后，调用此函数合并素材。
    合并后的文本直接插入到step3的debate prompt中。

    Args:
        zhihu_results: 知乎MCP返回的结果列表
        web_search_results: WebSearch返回的结果列表（dict或str）
        web_search_snippets: WebSearch结果的文本摘要（Agent可直接传入）

    Returns:
        合并后的素材文本（最多2000字）
    """
    parts = []

    if web_search_snippets:
        parts.append(f"=== WebSearch 素材 ===\n{web_search_snippets[:1500]}")
    elif web_search_results:
        for item in web_search_results[:5]:
            if isinstance(item, dict):
                text = item.get('snippet', item.get('content', item.get('description', '')))
            else:
                text = str(item)
            if text:
                parts.append(text[:400])

    if zhihu_results:
        parts.append("=== 知乎素材 ===")
        for item in zhihu_results[:5]:
            if isinstance(item, str):
                parts.append(item[:400])
            elif isinstance(item, dict):
                parts.append(item.get('content', item.get('excerpt', ''))[:400])

    combined = '\n---\n'.join(parts)
    return combined[:2000]


# ═══════════════════════════════════════════════════════════════
#  Phase 3: 生成辩论
# ═══════════════════════════════════════════════════════════════

def step3_generate_debate(topic: Dict, material_text: str = "",
                          expert_library: str = None) -> Optional[Dict]:
    """
    Phase 3: 生成4轮深度辩论

    Args:
        topic: step1返回的话题dict
        material_text: step2_build_material返回的素材文本
        expert_library: 专家库路径

    Returns:
        辩论JSON dict，或None（失败时）
    """
    lib = expert_library or EXPERT_LIBRARY
    arena = DebateArena(lib)

    profile1 = arena.get_expert_profile(topic['expert1'])
    profile2 = arena.get_expert_profile(topic['expert2'])
    if not profile1 or not profile2:
        return None

    beliefs1 = '; '.join(profile1.beliefs[:3])
    beliefs2 = '; '.join(profile2.beliefs[:3])
    values1 = profile1.values[0] if profile1.values else ''
    values2 = profile2.values[0] if profile2.values else ''
    style1 = profile1.argument_style or profile1.thinking_style
    style2 = profile2.argument_style or profile2.thinking_style

    material_section = ""
    if material_text:
        material_section = f"""
## 搜索素材（辩论中必须引用这些真实案例和数据）

{material_text}
"""

    prompt = f"""你是一个圆桌讨论主持人，组织以下专家进行深度辩论。

## 话题
{topic['topic']}

信念冲突：{topic['belief1']} ↔ {topic['belief2']}
冲突类型：{topic['conflict_type']}（强度：{topic['strength']}）
{material_section}
## 参与专家

【{topic['expert1']}】
核心信念：{beliefs1}
最看重：{values1}
论证风格：{style1}

【{topic['expert2']}】
核心信念：{beliefs2}
最看重：{values2}
论证风格：{style2}

## 辩论规则

1. **第一轮：立场阐述**（每人200-400字）
   - 必须引用搜索素材中的真实案例或数据
   - 必须体现该专家的核心信念和论证风格
   - 每人给出一个金句

2. **第二轮：相互质疑**（每人300-700字）
   - 必须针对对方的具体论点反驳
   - 必须指出对方论证中的逻辑漏洞或事实矛盾
   - 引用搜索素材作为反驳证据

3. **第三轮：回应辩护**（每人200-400字）
   - 回应对方的质疑
   - 承认合理的部分，坚持核心立场
   - 给出防御成功率（0-100%）

4. **第四轮：认知升级**（每人100-200字）
   - 经过辩论后，自己的认知有什么变化？
   - 旧观点→新观点
   - 触发因素是什么？

## 输出JSON格式

{{
  "topic": "{topic['topic']}",
  "experts": ["{topic['expert1']}", "{topic['expert2']}"],
  "source_material": {{
    "has_material": {str(bool(material_text)).lower()},
    "material_preview": "{material_text[:100] if material_text else '无'}"
  }},
  "rounds": [
    {{
      "round_number": 1,
      "round_name": "立场阐述",
      "synthesis": {{
        "summary": "综合答案：双方的核心分歧是什么，各自证据有多硬",
        "consensus": ["共识点"],
        "disagreements": ["分歧点"]
      }},
      "speeches": [
        {{
          "expert": "{topic['expert1']}",
          "stance": "立场关键词",
          "content": "发言内容（200-400字，必须引用搜索素材中的具体案例或数据）",
          "evidence": ["引用的具体案例或数据来源"],
          "quote": "金句",
          "emotion": "serious"
        }},
        {{
          "expert": "{topic['expert2']}",
          "stance": "立场关键词",
          "content": "发言内容（200-400字）",
          "evidence": ["引用的具体案例或数据来源"],
          "quote": "金句",
          "emotion": "serious"
        }}
      ]
    }},
    {{
      "round_number": 2,
      "round_name": "相互质疑",
      "synthesis": {{
        "summary": "综合答案",
        "consensus": [],
        "disagreements": []
      }},
      "speeches": [
        {{
          "expert": "{topic['expert1']}",
          "target": "{topic['expert2']}",
          "attack_type": "质疑类型",
          "content": "质疑内容（300-700字，针对对方第一轮具体论点反驳）",
          "evidence": ["反驳证据"]
        }},
        {{
          "expert": "{topic['expert2']}",
          "target": "{topic['expert1']}",
          "attack_type": "质疑类型",
          "content": "质疑内容（300-700字）",
          "evidence": ["反驳证据"]
        }}
      ]
    }},
    {{
      "round_number": 3,
      "round_name": "回应辩护",
      "synthesis": {{
        "summary": "综合答案",
        "consensus": [],
        "disagreements": []
      }},
      "speeches": [
        {{
          "expert": "{topic['expert1']}",
          "content": "辩护内容（200-400字）",
          "defense_success_rate": 70
        }},
        {{
          "expert": "{topic['expert2']}",
          "content": "辩护内容（200-400字）",
          "defense_success_rate": 65
        }}
      ]
    }},
    {{
      "round_number": 4,
      "round_name": "认知升级",
      "synthesis": {{
        "summary": "最终综合答案：辩论后双方的认知变化和未解分歧",
        "consensus": ["最终共识点"],
        "disagreements": ["未解分歧"]
      }},
      "speeches": [
        {{
          "expert": "{topic['expert1']}",
          "old_view": "旧观点",
          "new_view": "新认知",
          "trigger": "触发因素（来自对方的哪个论点或搜索素材）",
          "content": "认知升级描述（100-200字）"
        }},
        {{
          "expert": "{topic['expert2']}",
          "old_view": "旧观点",
          "new_view": "新认知",
          "trigger": "触发因素",
          "content": "认知升级描述（100-200字）"
        }}
      ]
    }}
  ],
  "clash_rounds": [
    {{
      "attacker": "{topic['expert1']}",
      "target": "{topic['expert2']}",
      "attack_type": "攻击类型",
      "attack_content": "攻击内容摘要",
      "counter_attack": "反击内容摘要"
    }}
  ],
  "key_quotes": [
    {{"expert": "{topic['expert1']}", "quote": "最犀利的金句", "impact": "high"}},
    {{"expert": "{topic['expert2']}", "quote": "最犀利的金句", "impact": "high"}}
  ]
}}

请生成完整的、有深度的辩论内容。每次发言都必须有具体论据，不能空泛。如果提供了搜索素材，必须在发言中引用。"""

    result = call_llm_json(
        prompt,
        "你是圆桌讨论主持人，生成真实、有深度、有引用的辩论。每位专家的发言必须体现其独特风格和核心信念。",
        max_tokens=8000,
        temperature=0.8,
    )

    if result['success'] and result.get('data'):
        return result['data']
    return None


# ═══════════════════════════════════════════════════════════════
#  Phase 4: 评分 + 提取策略
# ═══════════════════════════════════════════════════════════════

def step4_score_and_extract(debate_json: Dict) -> Dict:
    """
    Phase 4: 对辩论JSON进行评分和策略提取

    Args:
        debate_json: step3返回的辩论JSON dict

    Returns:
        {
            "score": {"total": float, "grade": str, ...},
            "extraction": {"experts": {专家名: 策略数据}, ...}
        }
    """
    result = {'score': {}, 'extraction': {}}

    temp_path = os.path.join(MEMORY_DIR, '_temp_debate.json')
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(debate_json, f, ensure_ascii=False, indent=2)

    try:
        result['score'] = score_v2(temp_path)
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
#  Phase 5: 升级专家
# ═══════════════════════════════════════════════════════════════

def step5_upgrade_experts(extraction: Dict, score_total: float,
                          expert_library: str = None) -> Dict:
    """
    Phase 5: 融合增强式升级专家档案

    Args:
        extraction: step4返回的extraction字段
        score_total: step4返回的score.total
        expert_library: 专家库路径

    Returns:
        {"升级成功的专家名": True, ...}
    """
    lib = expert_library or EXPERT_LIBRARY
    engine = FusionEngine(lib)
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
#  工具函数: 同质化检查
# ═══════════════════════════════════════════════════════════════

HOMOGENEOUS_VALUES = "专业能力/独立判断/持续学习"
HOMOGENEOUS_FRAMEWORK = "先看事实：发生了什么，数据怎么说？"
TEMPLATE_QUOTE_PATTERN = "我们再深一层。你说"


def check_homogeneity(expert_library: str = None) -> list:
    lib = expert_library or EXPERT_LIBRARY
    issues = []
    experts_dir = os.path.join(lib, 'experts')

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
#  工具函数: 保存训练结果
# ═══════════════════════════════════════════════════════════════

def save_training_result(topic: Dict, material_text: str,
                         debate_json: Dict, score: Dict,
                         extraction: Dict, upgrades: Dict,
                         round_num: int = 1) -> str:
    """保存单轮训练结果到memory目录，返回文件路径"""
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


# ═══════════════════════════════════════════════════════════════
#  CLI入口（调试/测试用）
# ═══════════════════════════════════════════════════════════════

def _run_all_phases(rounds: int, experts: List[str] = None,
                    skip_search: bool = False):
    """全流程测试模式（跳过Agent工具，用Python可调用的模块）"""
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"  深度训练引擎 V8.0 — 全流程测试模式")
    print(f"  轮次: {rounds} | 跳过搜索: {skip_search}")
    print(f"{'='*60}")

    # Phase 1
    print(f"\n  Phase 1: 生成话题")
    topics = step1_generate_topics(rounds, experts)
    for i, t in enumerate(topics, 1):
        print(f"  [{i}] {t['expert1']} vs {t['expert2']}")
        print(f"      {t['topic'][:60]}...")

    total_upgrades = 0

    for round_num, topic in enumerate(topics, 1):
        print(f"\n{'━'*60}")
        print(f"  训练 #{round_num}/{len(topics)} | {topic['expert1']} vs {topic['expert2']}")
        print(f"{'━'*60}")

        # Phase 2
        material_text = ""
        if not skip_search:
            print(f"\n  Phase 2: 内容采集")
            zhihu = step2_search_zhihu(topic['keywords'])
            print(f"  📱 知乎MCP: {zhihu['count']} 条 {'✅' if zhihu['success'] else '❌ ' + zhihu.get('error', '')}")
            material_text = step2_build_material(zhihu_results=zhihu['results'])
        else:
            print(f"\n  Phase 2: 跳过搜索")

        # Phase 3
        print(f"\n  Phase 3: 生成辩论")
        debate_json = step3_generate_debate(topic, material_text)
        if not debate_json:
            print(f"  ❌ 辩论生成失败，跳过")
            continue
        print(f"  ✅ 辩论生成成功")

        # Phase 4
        print(f"\n  Phase 4: 评分 + 提取策略")
        score_extract = step4_score_and_extract(debate_json)
        score_total = score_extract['score'].get('total', 0)
        grade = score_extract['score'].get('grade', 'F')
        print(f"  ⚖️ 评分: {score_total:.1f} ({grade})")

        # Phase 5
        upgrades = {}
        if score_total >= 60:
            print(f"\n  Phase 5: 升级专家")
            upgrades = step5_upgrade_experts(score_extract['extraction'], score_total)
            total_upgrades += len(upgrades)
            for name in upgrades:
                print(f"  📈 {name}: 升级完成")
        else:
            print(f"\n  Phase 5: 跳过（评分 < 60）")

        # 保存
        path = save_training_result(topic, material_text, debate_json,
                                    score_extract['score'], score_extract['extraction'],
                                    upgrades, round_num)
        print(f"  📄 保存: {os.path.basename(path)}")

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  完成 | 升级: {total_upgrades} 位 | 耗时: {elapsed:.1f}s")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='深度训练引擎 V8.0')
    parser.add_argument('--check', action='store_true', help='检查同质化')
    parser.add_argument('--all', action='store_true', help='全流程测试模式')
    parser.add_argument('--step1', action='store_true', help='只跑Phase 1（生成话题）')
    parser.add_argument('--rounds', type=int, default=5, help='轮次')
    parser.add_argument('--experts', type=str, default=None, help='指定专家（逗号分隔）')
    parser.add_argument('--skip-search', action='store_true', help='跳过搜索')
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

    if args.all:
        experts = args.experts.split(',') if args.experts else None
        _run_all_phases(args.rounds, experts, args.skip_search)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
