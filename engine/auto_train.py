# -*- coding: utf-8 -*-
"""
自动化深度训练入口 V8.0

串联已有模块，实现 deep-training SKILL 定义的完整流程：
  debate_arena → zhihu_miner → llm_generate → scorer_v2 → llm_extractor → fusion_engine

用法：
  python auto_train.py --check                   # 仅检查同质化
  python auto_train.py --rounds 5                 # 默认5轮深度训练
  python auto_train.py --experts 孔子,老子        # 指定专家对
  python auto_train.py --rounds 3 --skip-search   # 跳过搜索（调试用）

流程（对应 deep-training SKILL）：
  Phase 1: 生成话题 — debate_arena 从信念冲突中生成
  Phase 2: 内容采集 — zhihu_miner 知乎MCP + WebSearch（Agent提供）
  Phase 3: 生成辩论 — llm_generate 4轮辩论（提供搜索素材）
  Phase 4: 评分提取 — scorer_v2 + llm_extractor
  Phase 5: 升级专家 — fusion_engine 融合增强
"""

import argparse
import json
import os
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

HOMOGENEOUS_VALUES = "专业能力/独立判断/持续学习"
HOMOGENEOUS_FRAMEWORK = "先看事实：发生了什么，数据怎么说？"
TEMPLATE_QUOTE_PATTERN = "我们再深一层。你说"


# ═══ Phase 1: 生成话题 ═══════════════════════════════════════

def generate_topics(arena: DebateArena, rounds: int,
                    experts: List[str] = None) -> List[DebateTopic]:
    """从专家信念冲突中生成话题"""
    if experts:
        filtered = []
        all_topics = arena.generate_topics(count=rounds * 3, prefer_strong=True)
        for t in all_topics:
            if t.expert1 in experts or t.expert2 in experts:
                filtered.append(t)
        return filtered[:rounds]
    return arena.generate_topics(count=rounds, prefer_strong=True)


# ═══ Phase 2: 内容采集 ═══════════════════════════════════════

def collect_material(topic: DebateTopic, skip_search: bool = False) -> Dict:
    """采集搜索素材（知乎MCP + WebSearch）"""
    material = {
        'zhihu': [],
        'web_search': [],
        'combined_text': '',
    }

    if skip_search:
        return material

    keywords = _extract_keywords(topic.topic)

    # 知乎MCP采集
    print(f"  📱 知乎MCP: 搜索 '{keywords[:30]}...'")
    try:
        zhihu_result = search_zhihu(keywords, limit=5)
        if zhihu_result:
            material['zhihu'] = [zhihu_result] if isinstance(zhihu_result, str) else zhihu_result
            print(f"  📱 知乎MCP: 获取到 {len(material['zhihu'])} 条结果")
    except Exception as e:
        print(f"  📱 知乎MCP: 失败 ({e})")

    # WebSearch结果（从文件读取，Agent可预先写入）
    web_file = os.path.join(CONTENT_DIR, f'websearch_{topic.expert1}_{topic.expert2}.json')
    if os.path.exists(web_file):
        with open(web_file, 'r', encoding='utf-8') as f:
            material['web_search'] = json.load(f)
        print(f"  🔍 WebSearch: 从 {os.path.basename(web_file)} 加载 {len(material['web_search'])} 条")

    # 合并素材文本
    parts = []
    for item in material['zhihu'][:3]:
        if isinstance(item, str):
            parts.append(item[:500])
    for item in material['web_search'][:3]:
        if isinstance(item, dict):
            parts.append(item.get('snippet', item.get('content', ''))[:500])
        elif isinstance(item, str):
            parts.append(item[:500])
    material['combined_text'] = '\n---\n'.join(parts)

    return material


def _extract_keywords(topic_text: str) -> str:
    """从话题文本中提取搜索关键词"""
    import re
    clean = re.sub(r'["""]', '', topic_text)
    clean = re.sub(r'[？！。，、；：]', ' ', clean)
    parts = clean.split('vs')
    if len(parts) == 2:
        return parts[0].strip()[:30]
    words = clean.split()
    return ' '.join(words[:6])


# ═══ Phase 3: 生成辩论 ═══════════════════════════════════════

def generate_debate(topic: DebateTopic, arena: DebateArena,
                    material: Dict) -> Optional[Dict]:
    """生成4轮深度辩论（提供搜索素材作为依据）"""
    profile1 = arena.get_expert_profile(topic.expert1)
    profile2 = arena.get_expert_profile(topic.expert2)

    if not profile1 or not profile2:
        return None

    beliefs1 = '; '.join(profile1.beliefs[:3])
    beliefs2 = '; '.join(profile2.beliefs[:3])
    values1 = profile1.values[0] if profile1.values else ''
    values2 = profile2.values[0] if profile2.values else ''
    style1 = profile1.argument_style or profile1.thinking_style
    style2 = profile2.argument_style or profile2.thinking_style

    material_section = ""
    if material.get('combined_text'):
        material_section = f"""
## 搜索素材（辩论中必须引用这些真实案例和数据）

{material['combined_text'][:2000]}
"""

    prompt = f"""你是一个圆桌讨论主持人，组织以下专家进行深度辩论。

## 话题
{topic.topic}

信念冲突：{topic.belief1} ↔ {topic.belief2}
冲突类型：{topic.conflict_type}（强度：{topic.strength}）
{material_section}
## 参与专家

【{topic.expert1}】
核心信念：{beliefs1}
最看重：{values1}
论证风格：{style1}

【{topic.expert2}】
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
  "topic": "{topic.topic}",
  "experts": ["{topic.expert1}", "{topic.expert2}"],
  "source_material": {{
    "zhihu_count": {len(material.get('zhihu', []))},
    "web_search_count": {len(material.get('web_search', []))}
  }},
  "rounds": [
    {{
      "round_number": 1,
      "round_name": "立场阐述",
      "synthesis": {{
        "summary": "综合答案：双方的核心分歧是什么，各自证据有多硬",
        "consensus": ["共识点1"],
        "disagreements": ["分歧点1"]
      }},
      "speeches": [
        {{
          "expert": "{topic.expert1}",
          "stance": "立场关键词",
          "content": "发言内容（200-400字，必须引用搜索素材）",
          "evidence": ["引用的案例或数据"],
          "quote": "金句",
          "emotion": "serious"
        }},
        {{
          "expert": "{topic.expert2}",
          "stance": "立场关键词",
          "content": "发言内容（200-400字）",
          "evidence": ["引用的案例或数据"],
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
          "expert": "{topic.expert1}",
          "target": "{topic.expert2}",
          "attack_type": "质疑类型",
          "content": "质疑内容（300-700字）",
          "evidence": ["反驳证据"]
        }},
        {{
          "expert": "{topic.expert2}",
          "target": "{topic.expert1}",
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
          "expert": "{topic.expert1}",
          "content": "辩护内容（200-400字）",
          "defense_success_rate": 70
        }},
        {{
          "expert": "{topic.expert2}",
          "content": "辩护内容（200-400字）",
          "defense_success_rate": 65
        }}
      ]
    }},
    {{
      "round_number": 4,
      "round_name": "认知升级",
      "synthesis": {{
        "summary": "最终综合答案",
        "consensus": ["最终共识点"],
        "disagreements": ["未解分歧"]
      }},
      "speeches": [
        {{
          "expert": "{topic.expert1}",
          "old_view": "旧观点",
          "new_view": "新认知",
          "trigger": "触发因素",
          "content": "认知升级描述（100-200字）"
        }},
        {{
          "expert": "{topic.expert2}",
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
      "attacker": "{topic.expert1}",
      "target": "{topic.expert2}",
      "attack_type": "攻击类型",
      "attack_content": "攻击内容",
      "counter_attack": "反击内容"
    }}
  ],
  "key_quotes": [
    {{"expert": "{topic.expert1}", "quote": "金句内容", "impact": "high"}},
    {{"expert": "{topic.expert2}", "quote": "金句内容", "impact": "high"}}
  ]
}}

请生成完整的、有深度的辩论内容。每次发言都必须有具体论据，不能空泛。"""

    print(f"  💬 LLM: 生成4轮辩论...")
    result = call_llm_json(
        prompt,
        "你是圆桌讨论主持人，生成真实、有深度、有引用的辩论。每位专家的发言必须体现其独特风格和核心信念。",
        max_tokens=8000,
        temperature=0.8,
    )

    if result['success'] and result.get('data'):
        print(f"  💬 LLM: 成功 ({result['elapsed']:.1f}s)")
        return result['data']
    else:
        print(f"  💬 LLM: 失败 — {result.get('error', '未知错误')[:100]}")
        return None


# ═══ Phase 4: 评分 + 提取策略 ═══════════════════════════════

def score_and_extract(debate_json: Dict, temp_path: str) -> Dict:
    """评分 + 提取策略"""
    result = {'score': {}, 'extraction': {}}

    # 保存为临时文件（scorer需要文件路径）
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(debate_json, f, ensure_ascii=False, indent=2)

    # 评分
    print(f"  ⚖️ 评分: scorer_v2 7维度评估...")
    try:
        score_result = score_v2(temp_path)
        result['score'] = score_result
        total = score_result.get('total', 0)
        grade = score_result.get('grade', 'F')
        print(f"  ⚖️ 评分: {total:.1f} ({grade})")
    except Exception as e:
        print(f"  ⚖️ 评分: 失败 ({e})")

    # 提取策略
    print(f"  ⚔️ 提取: llm_extractor 策略分析...")
    try:
        extractor = LLMStrategyExtractor()
        extraction = extractor.extract(temp_path)
        result['extraction'] = extraction
        expert_count = len(extraction.get('experts', {}))
        print(f"  ⚔️ 提取: {expert_count} 位专家策略")
    except Exception as e:
        print(f"  ⚔️ 提取: 失败 ({e})")

    return result


# ═══ Phase 5: 升级专家 ═══════════════════════════════════════

def upgrade_experts(extraction: Dict, score_total: float) -> Dict:
    """融合增强式升级专家"""
    upgrades = {}
    engine = FusionEngine(EXPERT_LIBRARY)

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
            print(f"  📈 {expert_name}: 未找到档案")
            continue

        print(f"  📈 {expert_name}: 融合增强中...")
        try:
            engine.upgrade_expert(md_path, strategy, score_total)
            upgrades[expert_name] = True
            print(f"  📈 {expert_name}: 完成")
        except Exception as e:
            print(f"  📈 {expert_name}: 失败 ({e})")

    return upgrades


# ═══ 同质化检查 ═══════════════════════════════════════════════

def check_homogeneity() -> list:
    """检查专家库同质化问题"""
    issues = []
    experts_dir = os.path.join(EXPERT_LIBRARY, 'experts')
    categories = ['philosophy', 'psychology', 'sociology', 'literature', 'economics']

    for cat in categories:
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
    """输出同质化报告"""
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


# ═══ 主流程 ══════════════════════════════════════════════════

def run_deep_training(rounds: int, experts: List[str] = None,
                      skip_search: bool = False):
    """运行深度训练（完整流程）"""
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"  深度训练引擎 V8.0")
    print(f"  轮次: {rounds} | 跳过搜索: {skip_search}")
    print(f"{'='*60}")

    # 初始化模块
    arena = DebateArena(EXPERT_LIBRARY)
    print(f"\n  专家库: {len(arena.profiles)} 位专家")
    print(f"  冲突点: {len(arena.get_all_conflicts())} 个")

    # Phase 1: 生成话题
    print(f"\n{'─'*60}")
    print(f"  Phase 1: 生成话题")
    print(f"{'─'*60}")
    topics = generate_topics(arena, rounds, experts)
    for i, t in enumerate(topics, 1):
        print(f"  [{i}] {t.expert1} vs {t.expert2}")
        print(f"      {t.topic[:60]}...")

    # 逐轮训练
    session = {
        'version': 'V8.0',
        'start_time': datetime.now().isoformat(),
        'rounds': rounds,
        'results': [],
        'total_upgrades': 0,
    }

    for round_num, topic in enumerate(topics, 1):
        print(f"\n{'━'*60}")
        print(f"  深度训练 #{round_num}/{len(topics)} | {topic.expert1} vs {topic.expert2}")
        print(f"{'━'*60}")

        # Phase 2: 内容采集
        print(f"\n  Phase 2: 内容采集")
        material = collect_material(topic, skip_search=skip_search)

        # Phase 3: 生成辩论
        print(f"\n  Phase 3: 生成辩论")
        debate_json = generate_debate(topic, arena, material)
        if not debate_json:
            print(f"  ❌ 辩论生成失败，跳过")
            continue

        # Phase 4: 评分 + 提取
        print(f"\n  Phase 4: 评分 + 提取策略")
        temp_path = os.path.join(MEMORY_DIR, f'temp_debate_{round_num}.json')
        os.makedirs(MEMORY_DIR, exist_ok=True)
        score_extract = score_and_extract(debate_json, temp_path)

        score_total = score_extract['score'].get('total', 0)

        # Phase 5: 升级专家
        if score_total >= 60:
            print(f"\n  Phase 5: 升级专家")
            upgrades = upgrade_experts(score_extract['extraction'], score_total)
            session['total_upgrades'] += len(upgrades)
        else:
            print(f"\n  Phase 5: 跳过（评分 {score_total:.0f} < 60）")
            upgrades = {}

        # 保存辩论结果
        debate_path = os.path.join(MEMORY_DIR,
            f'deep_training_round{round_num}_{topic.expert1}_{topic.expert2}.json')
        debate_record = {
            '训练轮次': f'第{round_num}轮',
            '话题': topic.topic,
            '专家': [topic.expert1, topic.expert2],
            '核心冲突': f'{topic.belief1} ↔ {topic.belief2}',
            '搜索来源': {
                '知乎MCP结果数': len(material.get('zhihu', [])),
                'WebSearch结果数': len(material.get('web_search', [])),
            },
            '辩论': debate_json,
            '评分': score_extract['score'],
            '策略提取': score_extract['extraction'],
            '专家升级': upgrades,
        }
        with open(debate_path, 'w', encoding='utf-8') as f:
            json.dump(debate_record, f, ensure_ascii=False, indent=2)
        print(f"\n  📄 保存: {os.path.basename(debate_path)}")

        session['results'].append({
            'round': round_num,
            'topic': topic.topic,
            'experts': [topic.expert1, topic.expert2],
            'score': score_total,
            'grade': score_extract['score'].get('grade', 'F'),
            'upgrades': list(upgrades.keys()),
        })

        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 最终报告
    session['end_time'] = datetime.now().isoformat()
    session['duration'] = time.time() - start_time

    log_path = os.path.join(MEMORY_DIR,
        f'auto_train_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"  深度训练完成")
    print(f"{'='*60}")
    print(f"  轮次: {len(session['results'])}/{rounds}")
    print(f"  专家升级: {session['total_upgrades']} 位")
    print(f"  耗时: {session['duration']:.1f}s")
    print(f"  日志: {os.path.basename(log_path)}")

    for r in session['results']:
        experts_str = '+'.join(r['experts'])
        print(f"    Round {r['round']}: {experts_str} → {r['score']:.0f} ({r['grade']})")

    print(f"{'='*60}")


# ═══ CLI ═════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='深度训练引擎 V8.0')
    parser.add_argument('--rounds', type=int, default=5, help='训练轮次（默认5）')
    parser.add_argument('--experts', type=str, default=None, help='指定专家对（逗号分隔）')
    parser.add_argument('--check', action='store_true', help='仅检查同质化')
    parser.add_argument('--skip-search', action='store_true', help='跳过搜索（调试用）')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    if args.check:
        issues = check_homogeneity()
        print_homogeneity_report(issues)
        return

    experts = args.experts.split(',') if args.experts else None
    run_deep_training(args.rounds, experts, args.skip_search)


if __name__ == '__main__':
    main()
