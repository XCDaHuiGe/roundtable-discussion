# -*- coding: utf-8 -*-
"""
深度训练引擎 V11.0 — Agent=LLM，Python=机械操作 + Coach审阅 + 门控验证

核心设计：
  - Agent（你）本身就是LLM，负责搜索、阅读、生成辩论、反思
  - Python模块只做机械操作：评分、提取、Coach审阅、门控验证、升级、保存
  - 不依赖任何外部LLM API

进化闭环（借鉴 SkillOpt）：
  1. Agent调用 step1_generate_topics() → 获取话题列表
  2. Agent自己用WebSearch/AnySearch搜索 → 采集素材
  3. Agent自己阅读专家档案 → 理解专家风格
  4. Agent自己生成辩论JSON → 传入step4评分
  5. Agent调用 step4_score_and_extract() → 机械评分+提取
  6. Agent生成 coach_review.json → Coach审阅（监督角色）
  7. Agent调用 step5_upgrade_experts() → 门控验证 + 快照 + 升级/回退
     - Coach: 结构化审阅，决定哪些升级值得执行
     - Gate: 新分 > 历史平均？通过才升级
     - Snapshot: 升级前保存快照
     - Rollback: 门控拒绝时回退
  8. Agent调用 step6_record_tracking() → 记录训练数据到追踪系统
  9. Agent调用 save_training_result() → 机械保存

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
from scorer import score_discussion, default_scores
from training.llm_extractor import LLMStrategyExtractor
from training.reflection_schema import (
    load_reflection, validate_reflection, gate_upgrade,
    save_to_history, snapshot_expert, rollback_expert, cleanup_snapshots,
    REFLECTION_PROMPT,
)
from training.coach import (
    validate_coach_review, load_coach_review, coach_review_to_dict,
    extract_strategies_from_coach_review, CoachReview,
    COACH_REVIEW_PROMPT,
)
from training.tracker import TrainingTracker
from auto_scorer import auto_score_debate, blend_scores

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
    """获取专家档案信息（包含策略层，形成进化闭环）

    Agent读取策略层后，可以：
    - 根据attack_modes选择攻击角度
    - 根据defense_modes识别对手弱点
    - 根据weaknesses避免被攻击
    """
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
        'attack_modes': profile.attack_modes[:3],
        'defense_modes': profile.defense_modes[:3],
        'weaknesses': profile.weaknesses[:2],
    }


# ═══════════════════════════════════════════════════════════════
#  Phase 4: 评分 + 提取（机械操作）
# ═══════════════════════════════════════════════════════════════

def step4_score_and_extract(debate_json: Dict, scores: Dict = None,
                             expert_names: List[str] = None) -> Dict:
    """评分和策略提取（机械操作）

    自动评分 + Agent评分混合，消除主观偏差。

    Args:
        debate_json: 辩论JSON
        scores: Agent传入的6维度分数（可选）
        expert_names: 参与辩论的专家名列表（用于自动评分）

    Returns:
        {"score": {"total": 68.5, "grade": "C"}, "extraction": {...}}
    """
    result = {'score': {}, 'extraction': {}}

    temp_path = os.path.join(MEMORY_DIR, '_temp_debate.json')
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(debate_json, f, ensure_ascii=False, indent=2)

    try:
        # 自动评分（零LLM依赖）
        auto_scores = auto_score_debate(debate_json, expert_names=expert_names)

        if scores and any(v != 50 for v in scores.values()):
            # Agent提供了有效评分 → 混合（自动60% + Agent40%）
            final_scores = blend_scores(auto_scores, scores, auto_weight=0.6)
        else:
            # Agent未评分 → 纯自动评分
            final_scores = auto_scores

        result['score'] = score_discussion(final_scores)
        result['score']['auto_scores'] = auto_scores  # 保留自动评分细节
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
#  Phase 4b: Coach 审阅（机械操作）
# ═══════════════════════════════════════════════════════════════

def step4b_coach_review(coach_review_json: Dict = None,
                        coach_review_path: str = None) -> CoachReview:
    """加载并验证 Coach 审阅结果（机械操作）

    Agent 生成 coach_review.json 后传入此函数。
    Python 做验证、过滤低信心、应用 Edit Budget。

    Args:
        coach_review_json: Agent 传入的 Coach Review JSON dict
        coach_review_path: 或者从文件路径加载

    Returns:
        验证后的 CoachReview 对象
    """
    if coach_review_json:
        return validate_coach_review(coach_review_json)
    elif coach_review_path:
        review = load_coach_review(coach_review_path)
        if review:
            return review

    # 无 Coach Review 时返回空对象（不影响流程，但跳过 Coach 优化）
    return CoachReview()


# ═══════════════════════════════════════════════════════════════
#  Phase 5: 门控验证 + 快照 + 升级/回退（机械操作）
# ═══════════════════════════════════════════════════════════════

def step5_upgrade_experts(
    extraction: Dict,
    score_total: float,
    coach_review: CoachReview = None,
    topic: Dict = None,
) -> Dict:
    """门控验证 + 快照 + 融合升级 + 回退（机械操作）

    流程：
    1. 门控验证：新分 > 历史平均？拒绝则跳过
    2. 快照：升级前保存专家档案快照
    3. 融合升级：使用 FusionEngine
    4. 记录：保存分数到历史

    Args:
        extraction: step4 的策略提取结果
        score_total: 本轮辩论总分
        coach_review: Coach 审阅结果（可选，提供更精准的升级策略）
        topic: 话题信息（用于追踪）
    """
    # ── 门控验证 ──
    gate_result = gate_upgrade(
        {"debate_quality": score_total, "expert_upgrades": []},
        history_path=None,
    )
    if not gate_result["passed"]:
        return {
            "upgrades": {},
            "gate": gate_result,
            "reason": f"门控拒绝: {gate_result['reason']}",
        }

    # ── 确定升级策略来源：Coach > 原始 extraction ──
    if coach_review and coach_review.upgrade_recommendations:
        expert_strategies = extract_strategies_from_coach_review(coach_review)
    else:
        expert_strategies = {}
        for expert_name, expert_data in extraction.get("experts", {}).items():
            expert_strategies[expert_name] = {
                "attack_strategy": expert_data.get("attack_strategy", {}),
                "defense_weakness": expert_data.get("defense_weakness", {}),
                "style_fingerprint": expert_data.get("style_fingerprint", {}),
                "evidence_preference": expert_data.get("evidence_preference", {}),
                "interaction_pattern": expert_data.get("interaction_pattern", {}),
            }

    # ── 快照 + 融合升级 ──
    engine = FusionEngine(EXPERT_LIBRARY)
    upgrades = {}
    snapshots = {}

    for expert_name, strategy in expert_strategies.items():
        md_path = engine.find_expert_md(expert_name)
        if not md_path:
            continue
        try:
            # 快照（升级前）
            snap_path = snapshot_expert(md_path)
            snapshots[expert_name] = snap_path

            # 融合升级
            engine.upgrade_expert(md_path, strategy, score_total)
            upgrades[expert_name] = True

            # 清理旧快照（保留最近3个）
            cleanup_snapshots(md_path, keep_latest=3)
        except Exception as e:
            # 升级失败，回退到快照
            if expert_name in snapshots and snapshots[expert_name]:
                rollback_expert(md_path, snapshots[expert_name])
            upgrades[expert_name] = False

    # ── 保存分数到历史（供下次门控对比） ──
    reflection_data = coach_review_to_dict(coach_review) if coach_review else {}
    save_to_history(score_total, reflection_data)

    return {
        "upgrades": upgrades,
        "gate": gate_result,
        "snapshots": snapshots,
        "coach_used": coach_review is not None and len(coach_review.upgrade_recommendations) > 0,
    }


# ═══════════════════════════════════════════════════════════════
#  Phase 6: 记录追踪（机械操作）
# ═══════════════════════════════════════════════════════════════

def step6_record_tracking(
    topic: Dict,
    score_total: float,
    extraction: Dict,
    upgrade_result: Dict,
    coach_review: CoachReview = None,
) -> None:
    """记录训练数据到追踪系统（机械操作）

    数据写入：
    - memory/training_history.jsonl （全局追加日志）
    - memory/expert_evolution/{专家名}.json （每位专家的进化数据）
    """
    tracker = TrainingTracker(EXPERT_LIBRARY, MEMORY_DIR)

    experts_data = {}
    for expert_name in extraction.get("experts", {}):
        expert_extraction = extraction["experts"][expert_name]
        experts_data[expert_name] = {
            "old_version": expert_extraction.get("version", 1),
            "new_version": expert_extraction.get("version", 1) + (1 if upgrade_result.get("upgrades", {}).get(expert_name) else 0),
            "score": score_total,
            "attack_eff": 0.0,
            "defense_rate": 0.0,
            "operations": [],
            "capability_delta": {},
            "quality_matrix": coach_review.dimensions if coach_review else {},
        }

    session_data = {
        "book_title": topic.get("topic", "未知话题"),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "experts": experts_data,
    }
    tracker.record_training(session_data)


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
#  评估函数
# ═══════════════════════════════════════════════════════════════

def validate_content(debate_json: Dict) -> Dict:
    """验证内容质量（机械操作）

    检查项：
    - 引用数量 ≥ 2
    - 每轮发言长度 ≥ 100字
    - 碰撞轮次 ≥ 1

    Returns:
        {"passed": True, "quote_count": 3, "issues": []}
    """
    issues = []
    total_quotes = 0
    total_speeches = 0
    short_speeches = 0

    for round_data in debate_json.get('rounds', []):
        for speech in round_data.get('speeches', []):
            total_speeches += 1
            content = speech.get('content', '')
            if len(content) < 100:
                short_speeches += 1
                issues.append(f"发言过短: {speech.get('expert', '未知')} ({len(content)}字)")

            if speech.get('quote'):
                total_quotes += 1

    if total_quotes < 2:
        issues.append(f"引用不足: 仅{total_quotes}个引用，需要≥2")

    clash_count = len(debate_json.get('clash_rounds', []))
    if clash_count < 1:
        issues.append("缺少碰撞轮次")

    return {
        'passed': len(issues) == 0,
        'quote_count': total_quotes,
        'speech_count': total_speeches,
        'short_speeches': short_speeches,
        'clash_count': clash_count,
        'issues': issues,
    }


def compare_performance(
    expert_name: str,
    topic: Dict,
    old_score: float,
    new_score: float,
    old_extraction: Dict = None,
    new_extraction: Dict = None,
) -> Dict:
    """对比训练前后表现（机械操作）

    Agent传入：
    - 旧版本辩论评分
    - 新版本辩论评分
    - 策略提取结果（可选）

    Returns:
        {"improved": True, "delta": 15.5, "analysis": "..."}
    """
    delta = new_score - old_score
    improved = delta > 0

    analysis = []
    if improved:
        analysis.append(f"评分提升: {old_score:.1f} → {new_score:.1f} (+{delta:.1f})")
    else:
        analysis.append(f"评分下降: {old_score:.1f} → {new_score:.1f} (-{abs(delta):.1f})")

    if old_extraction and new_extraction:
        old_attack_count = len(old_extraction.get('experts', {}).get(expert_name, {}).get('attack_strategy', {}))
        new_attack_count = len(new_extraction.get('experts', {}).get(expert_name, {}).get('attack_strategy', {}))
        if new_attack_count > old_attack_count:
            analysis.append(f"攻击模式增加: {old_attack_count} → {new_attack_count}")

    return {
        'expert': expert_name,
        'topic': topic.get('topic', ''),
        'old_score': old_score,
        'new_score': new_score,
        'delta': round(delta, 1),
        'improved': improved,
        'analysis': analysis,
    }


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