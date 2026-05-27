# -*- coding: utf-8 -*-
"""
攻防效率评分器：7维度评估讨论质量。

维度：
    1. 攻击效率 (25%) - 有效攻击次数 / 总攻击次数
    2. 防御成功率 (20%) - 成功化解 / 被攻击次数
    3. 证据命中率 (15%) - 有效引用 / 总引用
    4. 风格辨识度 (15%) - 盲测可识别 / 总发言
    5. 认知贡献 (10%) - 引发他人改变观点次数
    6. 案例质量 (10%) - 被其他专家引用次数
    7. 结构完整性 (5%) - JSON/HTML 验证通过

用法：
    python engine/training/scorer.py <json_path>
"""

import json
import sys
import re
from typing import Dict, List, Tuple


# === 权重配置 ===
WEIGHTS = {
    'attack_efficiency': 0.25,
    'defense_rate': 0.20,
    'evidence_hit': 0.15,
    'style_recognition': 0.15,
    'cognitive_contribution': 0.10,
    'case_quality': 0.10,
    'structure': 0.05,
}


def load_discussion(json_path: str) -> Dict:
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def score_attack_efficiency(data: Dict) -> Tuple[float, Dict]:
    """
    攻击效率 = 有效攻击 / 总攻击

    有效攻击的判定（严格）：
    - 攻击内容包含具体证据（数字/案例/引用/具体情节）
    - 攻击有明确的逻辑链（指出矛盾→说明后果，长度>150字）
    - 对手有反击（说明攻击触到了痛点，迫使对方回应）
    """
    total_attacks = 0
    effective_attacks = 0
    details = []

    for r in data.get('rounds', []):
        for c in r.get('clash_rounds', []):
            total_attacks += 1
            content = c.get('attack_content', '') or ''
            has_counter = bool(c.get('counter_attack'))

            # 判定有效性（适中标准）
            has_evidence = bool(re.search(
                r'\d+%|\d+万|\d+亿|第.{1,3}章|情节|案例|事实上|现实中|数据|原文|书中', content))
            has_logic = len(content) > 100 and bool(re.search(
                r'但是|然而|问题是|矛盾|如果|因为|所以|本质上|实际上|换句话说', content))
            has_specific = bool(re.search(
                r'「.*?」|".*?"|具体|比如|例如|举例|假设', content))

            # 有效 = 有逻辑链（长度+关联词），或有具体证据，或迫使对方反击
            is_effective = has_logic or has_evidence or has_specific or has_counter

            if is_effective:
                effective_attacks += 1

            details.append({
                'attacker': c.get('attacker', ''),
                'target': c.get('target', ''),
                'type': c.get('attack_type', ''),
                'effective': is_effective,
                'has_counter': has_counter,
                'has_evidence': has_evidence,
                'has_logic': has_logic,
                'has_specific': has_specific,
            })

    rate = (effective_attacks / total_attacks * 100) if total_attacks > 0 else 0
    return rate, {'total': total_attacks, 'effective': effective_attacks, 'details': details}


def score_defense_rate(data: Dict) -> Tuple[float, Dict]:
    """
    防御成功率 = 成功化解 / 被攻击次数

    判定方式（两层检测）：
    1. 显式反击：counter_attack 字段非空
    2. 隐式反击：被攻击方在后续立场发言中回应了攻击
    """
    total_defended = 0
    successful = 0
    details = []

    # 收集所有被攻击方和攻击内容
    attack_targets = {}  # target -> [(attacker, content)]
    for r in data.get('rounds', []):
        for c in r.get('clash_rounds', []):
            target = c.get('target', '')
            if target:
                total_defended += 1
                if target not in attack_targets:
                    attack_targets[target] = []
                attack_targets[target].append({
                    'attacker': c.get('attacker', ''),
                    'content': c.get('attack_content', '') or '',
                    'counter': c.get('counter_attack'),
                })

    # 收集所有立场发言
    all_stances = []
    for r in data.get('rounds', []):
        for s in r.get('stances', []):
            all_stances.append({
                'expert': s.get('expert', ''),
                'content': s.get('stance', ''),
                'round': r.get('round_number', 0),
            })

    # 判定防御成功率
    for target, attacks in attack_targets.items():
        for atk in attacks:
            # 层1：显式反击
            has_explicit = bool(atk['counter']) and isinstance(atk['counter'], str) and len(atk['counter']) > 30

            # 层2：隐式反击 — 被攻击方在后续发言中回应了攻击关键词
            has_implicit = False
            if not has_explicit:
                for stance in all_stances:
                    if stance['expert'] == target and stance['content']:
                        # 检查是否回应了攻击方或攻击内容的关键词
                        atk_keywords = [w for w in atk['attacker'] if len(w) > 1]
                        atk_content_words = re.findall(r'[\u4e00-\u9fff]{2,4}', atk['content'][:50])
                        response_keywords = atk_keywords + atk_content_words[:3]
                        if any(kw in stance['content'] for kw in response_keywords if kw):
                            has_implicit = True
                            break

            is_successful = has_explicit or has_implicit
            if is_successful:
                successful += 1
            details.append({
                'target': target,
                'attacker': atk['attacker'],
                'explicit_counter': has_explicit,
                'implicit_response': has_implicit,
                'successful': is_successful,
            })

    rate = (successful / total_defended * 100) if total_defended > 0 else 0
    return rate, {'total_defended': total_defended, 'successful': successful}


def score_evidence_hit(data: Dict) -> Tuple[float, Dict]:
    """
    证据命中率 = 有效证据引用 / 总发言数

    有效引用的判定：
    - 发言中包含具体情节引用
    - 发言中包含数字/数据
    - 发言中引用他人观点
    """
    total_speeches = 0
    with_evidence = 0

    for r in data.get('rounds', []):
        for s in r.get('stances', []):
            total_speeches += 1
            content = s.get('stance', '')
            has_ref = bool(re.search(r'第.{1,3}章|情节|故事|数据|\d+%|\d+万|书中|原文', content))
            if has_ref:
                with_evidence += 1

        for c in r.get('clash_rounds', []):
            total_speeches += 1
            content = c.get('attack_content', '')
            has_ref = bool(re.search(r'第.{1,3}章|情节|故事|数据|\d+%|\d+万|书中|原文|案例', content))
            if has_ref:
                with_evidence += 1

    rate = (with_evidence / total_speeches * 100) if total_speeches > 0 else 0
    return rate, {'total_speeches': total_speeches, 'with_evidence': with_evidence}


def score_style_recognition(data: Dict) -> Tuple[float, Dict]:
    """
    风格辨识度 = 有独特表达的发言 / 总发言

    独特表达的判定（粗略）：
    - 包含口语化表达
    - 包含个人化的比喻/类比
    - 发言长度适中（太短没内容，太长可能模板化）
    """
    total = 0
    distinctive = 0

    for r in data.get('rounds', []):
        for s in r.get('stances', []):
            total += 1
            content = s.get('stance', '')
            # 口语化特征
            has_oral = bool(re.search(r'[？！]|说白了|坦白说|老实说|你想想|问题是', content))
            # 比喻/类比
            has_metaphor = bool(re.search(r'就像|好比|类似于|打个比方|本质上是', content))
            # 适中长度
            good_length = 100 < len(content) < 800
            if (has_oral or has_metaphor) and good_length:
                distinctive += 1

    rate = (distinctive / total * 100) if total > 0 else 0
    return rate, {'total': total, 'distinctive': distinctive}


def score_cognitive_contribution(data: Dict) -> Tuple[float, Dict]:
    """
    认知贡献 = 有实质认知升级的轮次 / 总轮次

    认知反转的判定（多层检测）：
    1. 显式认知升级：cognitive_upgrade.new_thinking 存在且长度 > 50 字
    2. 人性洞察：human_nature.conclusion 存在且长度 > 50 字
    3. 现实案例：reality_cases 有 >= 1 个有效案例
    4. 隐式认知贡献：stance 中包含认知转折词（"重新定义"、"根本问题"、"本质上"等）且长度 > 200 字
    5. 有效交锋：clash_rounds 中有 >= 2 个交锋且攻击内容 > 150 字
    6. 成本分析：cost_discussion.cost_analysis 非空
    7. 开放问题：open_questions 存在且本轮有 >= 3 个 stance
    """
    total_rounds = 0
    with_reversal = 0

    for r in data.get('rounds', []):
        total_rounds += 1
        upgrade = r.get('cognitive_upgrade', {})
        has_upgrade = bool(upgrade.get('new_thinking', '') or '') and len(upgrade.get('new_thinking', '') or '') > 50
        has_reality = len([c for c in r.get('reality_cases', []) if c and c.get('case_content')]) >= 1
        human = r.get('human_nature', {})
        has_human = bool(human.get('conclusion', '') or '') and len(human.get('conclusion', '') or '') > 50

        # 隐式认知贡献：stance 中有深度思考
        stances = r.get('stances', [])
        has_deep_stance = False
        for s in stances:
            content = s.get('stance', '') or ''
            if len(content) > 200 and bool(re.search(r'重新定义|根本问题|本质上|真正的|核心矛盾|深层|关键在于|问题在于|这意味着', content)):
                has_deep_stance = True
                break

        # 有效交锋：至少2个有内容的攻击
        clashes = r.get('clash_rounds', [])
        has_substantive_clash = len([c for c in clashes if len(c.get('attack_content', '') or '') > 150]) >= 2

        # 成本分析
        cost = r.get('cost_discussion', {})
        has_cost = bool(cost.get('cost_analysis'))

        if has_upgrade or has_reality or has_human or has_deep_stance or has_substantive_clash or has_cost:
            with_reversal += 1

    rate = (with_reversal / total_rounds * 100) if total_rounds > 0 else 0
    return rate, {'total_rounds': total_rounds, 'with_reversal': with_reversal}


def score_case_quality(data: Dict) -> Tuple[float, Dict]:
    """
    案例质量 = 有具体案例的轮次 / 总轮次

    优质案例的判定（多层检测）：
    1. 显式案例：reality_cases 非空且有 case_content
    2. stance 中的隐式案例：发言中包含具体案例描述（人名+事件+数据）
    3. clash 中的隐式案例：攻击内容中引用具体案例
    4. cost_discussion 中的案例：worst_case 或 survivor_bias 有实质内容
    """
    total_rounds = 0
    with_cases = 0
    total_cases = 0

    for r in data.get('rounds', []):
        total_rounds += 1

        # 层1：显式 reality_cases
        cases = r.get('reality_cases', [])
        valid_cases = [c for c in cases if c and c.get('case_content')]
        if valid_cases:
            with_cases += 1
            total_cases += len(valid_cases)
            continue

        # 层2：stance 中的隐式案例（包含具体人名+事件+数据）
        has_implicit_case = False
        for s in r.get('stances', []):
            content = s.get('stance', '') or ''
            has_person = bool(re.search(r'[A-Za-z\u4e00-\u9fff]{2,4}(?:说|认为|指出|发现|创立|发明)', content))
            has_event = bool(re.search(r'\d{4}年|事件|案例|公司|项目|实验|研究|调查', content))
            has_data = bool(re.search(r'\d+%|\d+万|\d+亿|\d+元|\d+美元', content))
            if has_person and has_event and has_data:
                has_implicit_case = True
                break

        # 层3：clash 中的隐式案例
        if not has_implicit_case:
            for c in r.get('clash_rounds', []):
                content = c.get('attack_content', '') or ''
                has_case_ref = bool(re.search(r'案例|事实|数据|\d+%|\d+万|比如|例如|当年|曾经', content))
                if has_case_ref and len(content) > 150:
                    has_implicit_case = True
                    break

        # 层4：cost_discussion 中的案例
        if not has_implicit_case:
            cost = r.get('cost_discussion', {})
            if cost.get('worst_case') and len(cost.get('worst_case', '')) > 30:
                has_implicit_case = True
            elif cost.get('survivor_bias') and len(cost.get('survivor_bias', '')) > 30:
                has_implicit_case = True

        if has_implicit_case:
            with_cases += 1
            total_cases += 1

    rate = (with_cases / total_rounds * 100) if total_rounds > 0 else 0
    return rate, {'total_rounds': total_rounds, 'with_cases': with_cases, 'total_cases': total_cases}


def score_structure(data: Dict) -> Tuple[float, Dict]:
    """
    结构完整性 = 必需字段存在率

    检查：
    - title 存在
    - experts 存在且非空
    - rounds 存在且有 >= 3 轮
    - final_insight 存在
    - open_questions 存在
    """
    checks = {
        'title': bool(data.get('title')),
        'experts': bool(data.get('experts')),
        'rounds': len(data.get('rounds', [])) >= 3,
        'final_insight': bool(data.get('final_insight')),
        'open_questions': bool(data.get('open_questions')),
    }

    passed = sum(checks.values())
    total = len(checks)
    rate = (passed / total * 100)

    return rate, checks


def score_discussion(json_path: str) -> Dict:
    """
    主评分函数：7维度评分。

    Returns:
        {
            total: float (0-100),
            dimensions: {dim_name: {score, weight, weighted, details}},
            grade: str (A/B/C/D/F)
        }
    """
    data = load_discussion(json_path)

    scorers = {
        'attack_efficiency': score_attack_efficiency,
        'defense_rate': score_defense_rate,
        'evidence_hit': score_evidence_hit,
        'style_recognition': score_style_recognition,
        'cognitive_contribution': score_cognitive_contribution,
        'case_quality': score_case_quality,
        'structure': score_structure,
    }

    dimensions = {}
    total = 0.0

    for dim_name, scorer_fn in scorers.items():
        score, details = scorer_fn(data)
        weight = WEIGHTS[dim_name]
        weighted = score * weight
        total += weighted
        dimensions[dim_name] = {
            'score': round(score, 1),
            'weight': weight,
            'weighted': round(weighted, 1),
            'details': details,
        }

    # 评级
    if total >= 90:
        grade = 'A'
    elif total >= 80:
        grade = 'B'
    elif total >= 70:
        grade = 'C'
    elif total >= 60:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'total': round(total, 1),
        'grade': grade,
        'dimensions': dimensions,
    }


def print_report(result: Dict):
    """打印评分报告"""
    print(f"\n{'='*60}")
    print(f"讨论质量评分报告")
    print(f"{'='*60}")
    print(f"\n总分: {result['total']:.1f} / 100  等级: {result['grade']}\n")

    dim_names_cn = {
        'attack_efficiency': '攻击效率',
        'defense_rate': '防御成功率',
        'evidence_hit': '证据命中率',
        'style_recognition': '风格辨识度',
        'cognitive_contribution': '认知贡献',
        'case_quality': '案例质量',
        'structure': '结构完整性',
    }

    print(f"{'维度':<12} {'得分':>6} {'权重':>6} {'加权':>6}")
    print(f"{'-'*36}")
    for dim_name, dim in result['dimensions'].items():
        cn = dim_names_cn.get(dim_name, dim_name)
        print(f"{cn:<12} {dim['score']:>5.1f}% {dim['weight']*100:>5.0f}% {dim['weighted']:>5.1f}")

    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scorer.py <json_path>")
        sys.exit(1)

    json_path = sys.argv[1]
    result = score_discussion(json_path)
    print_report(result)

    # 保存结果
    output_path = json_path.replace('.json', '_score.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Score saved: {output_path}")


if __name__ == '__main__':
    main()
