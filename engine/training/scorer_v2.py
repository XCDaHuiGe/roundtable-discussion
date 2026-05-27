# -*- coding: utf-8 -*-
"""
攻防效率评分器 V2：7维度评估讨论质量（严格版）。

相比V1的核心改进：
    1. 攻击有效性：从"四选一"改为"基础条件+强条件"两层验证
    2. 证据命中：从窄关键词白名单改为三层标准（BOOK_BASED/TOPIC_BASED/HYBRID）
    3. 风格辨识：从通用口语化检测改为四项同时满足的严格标准
    4. 认知贡献：从字段存在检查改为内容深度评估（行动建议/矛盾分析）
    5. 案例质量：从"有案例"改为"四要素完整性"检查
    6. 防御判定：从字符级匹配改为语义关键词回应检测（>=2个关键词）
    7. 结构检查：增加全员参与检查（每轮6位专家都有发言）

维度：
    1. 攻击效率 (25%) - 有效攻击次数 / 总攻击次数
    2. 防御成功率 (20%) - 成功化解 / 被攻击次数
    3. 证据命中率 (15%) - 有效引用 / 总发言
    4. 风格辨识度 (15%) - 符合严格标准的发言 / 总发言
    5. 认知贡献 (10%) - 有深度认知升级的轮次 / 总轮次
    6. 案例质量 (10%) - 完整案例轮次 / 总轮次
    7. 结构完整性 (5%) - 必需字段+全员参与验证

用法：
    python engine/training/scorer_v2.py <json_path>
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

# === 攻击效率：逻辑链关联词 ===
LOGIC_KEYWORDS = [
    '但是', '然而', '问题是', '矛盾', '如果', '因为', '所以',
    '本质上', '实际上', '那么', '因此', '导致', '意味着',
    '换句话说', '由此可见', '问题在于', '根源在于',
]

# === 攻击效率：具体证据模式 ===
SPECIFIC_EVIDENCE_PATTERNS = [
    re.compile(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?%'),  # 百分比
    re.compile(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:万|亿|元|美元|人|次|只|件|个|条)'),  # 数字+单位
    re.compile(r'(?:案例|例子|事例|实例|典故)[:：]'),  # 案例名称标记
    re.compile(r'[《「"“][^》」"”]{2,20}[》」"”]'),  # 书名号/引号内内容
    re.compile(r'(?:第[一二三四五六七八九十\d]{1,3}[章回节卷]|第\d{1,3}页)'),  # 章节/页码
]

# === 证据命中率：BOOK_BASED 模式 ===
BOOK_BASED_PATTERNS = [
    re.compile(r'第[一二三四五六七八九十\d]{1,3}[章回节卷]'),  # 章节引用
    re.compile(r'第\d{1,3}页'),  # 页码
    re.compile(r'(?:书中|小说里|故事里|原文|作者写到|描写道|写道|提到|写道)'),  # 书中场景
    re.compile(r'[《「"“][^》」"”]{3,30}[》」"”]'),  # 原文引用
    re.compile(r'(?:情节|桥段|片段|场景|细节)'),  # 情节引用
]

# === 证据命中率：TOPIC_BASED 模式 ===
TOPIC_BASED_PATTERNS = [
    re.compile(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:万|亿|元|美元|%|倍|年|人|次|只|件|个|条)'),  # 具体数字
    re.compile(r'(?:案例|例子|事例|实例|典故)[:：]?'),  # 案例
    re.compile(r'(?:理论|模型|框架|学说|定律|效应)'),  # 理论
    re.compile(r'(?:专家指出|研究表明|数据显示|调查发现|报告指出|统计显示|学者认为)'),  # 专家观点
    re.compile(r'\d{4}年|20\d{2}年|19\d{2}年'),  # 年份
]

# === 风格辨识度：口语化表达 ===
ORAL_EXPRESSIONS = [
    '说白了', '坦白说', '老实说', '你想想', '问题是', '不是', '而是',
    '要知道', '说到底', '讲真', '实话说', '不瞒你说', '你得明白',
]

# === 风格辨识度：比喻/类比 ===
METAPHOR_PATTERNS = [
    re.compile(r'就像[^，。]{2,20}'),  # 就像...
    re.compile(r'好比[^，。]{2,20}'),  # 好比...
    re.compile(r'类似于[^，。]{2,20}'),  # 类似于...
    re.compile(r'打个比方[^，。]{2,20}'),  # 打个比方...
    re.compile(r'本质上是[^，。]{2,20}'),  # 本质上是...
    re.compile(r'相当于[^，。]{2,20}'),  # 相当于...
    re.compile(r'如同[^，。]{2,20}'),  # 如同...
    re.compile(r'仿佛[^，。]{2,20}'),  # 仿佛...
]

# === 风格辨识度：模板化总结词（禁止出现） ===
TEMPLATE_WORDS = [
    '综上所述', '总而言之', '一言以蔽之', '总的来说', '归纳起来',
    '最后总结', '总结来说', '概括而言', '综上所述',
]

# === 认知贡献：行动建议标记 ===
ACTION_MARKERS = [
    '作为个人', '作为社会', '作为政策', '作为企业', '作为政府',
    '我们应该', '社会应该', '政策应该', '需要建立', '需要完善',
    '建议', '应当', '必须', '有必要', '关键在于',
]

# === 认知贡献：矛盾分析标记 ===
CONTRAST_MARKERS = [
    re.compile(r'表面上.{2,30}实际上'),  # 表面上...实际上
    re.compile(r'看似.{2,30}实则'),  # 看似...实则
    re.compile(r'一方面.{2,30}另一方面'),  # 一方面...另一方面
    re.compile(r'虽然.{2,30}但是'),  # 虽然...但是
    re.compile(r'尽管.{2,30}然而'),  # 尽管...然而
]


def load_discussion(json_path: str) -> Dict:
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def _extract_keywords(text: str, max_words: int = 5) -> List[str]:
    """从文本中提取关键词（2-4字中文短语）"""
    if not text:
        return []
    words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
    seen = set()
    result = []
    for w in words:
        if w not in seen and len(w) >= 2:
            seen.add(w)
            result.append(w)
            if len(result) >= max_words:
                break
    return result


def _count_evidence_patterns(content: str, patterns: List[re.Pattern]) -> int:
    """统计内容中匹配的证据模式数量"""
    count = 0
    for pattern in patterns:
        if pattern.search(content):
            count += 1
    return count


# ==================== 维度1：攻击效率 (25%) ====================

def score_attack_efficiency(data: Dict) -> Tuple[float, Dict]:
    """
    攻击效率 = 有效攻击 / 总攻击

    有效攻击判定（严格两层）：
    - 基础条件（必须）：攻击内容 > 60字
    - 强条件（满足任一）：
        * 有逻辑链：包含逻辑关联词且长度 > 150字
        * 有具体证据：包含数字/百分比/案例名称/具体情节
        * 迫使对手深度反击：counter_attack 长度 > 100字

    只有基础条件 = 50% 有效（计为0.5个有效攻击）
    满足强条件 = 100% 有效（计为1个有效攻击）
    """
    total_attacks = 0
    effective_attacks = 0.0
    details = []

    for r in data.get('rounds', []):
        for c in r.get('clash_rounds', []):
            total_attacks += 1
            content = c.get('attack_content', '') or ''
            counter = c.get('counter_attack', '') or ''

            # 基础条件：长度 > 60字
            base_pass = len(content) > 60

            # 强条件1：有逻辑链（关联词 + 长度>150）
            has_logic_keywords = any(kw in content for kw in LOGIC_KEYWORDS)
            has_logic = has_logic_keywords and len(content) > 150

            # 强条件2：有具体证据
            has_specific = any(p.search(content) for p in SPECIFIC_EVIDENCE_PATTERNS)

            # 强条件3：迫使对手深度反击
            has_deep_counter = isinstance(counter, str) and len(counter) > 100

            # 判定
            if not base_pass:
                # 不满足基础条件 = 完全无效
                is_effective = False
                effectiveness = 0.0
            elif has_logic or has_specific or has_deep_counter:
                # 基础 + 任一强条件 = 100%有效
                is_effective = True
                effectiveness = 1.0
            else:
                # 只有基础条件 = 50%有效
                is_effective = True
                effectiveness = 0.5

            effective_attacks += effectiveness

            details.append({
                'attacker': c.get('attacker', ''),
                'target': c.get('target', ''),
                'type': c.get('attack_type', ''),
                'effective': is_effective,
                'effectiveness': effectiveness,
                'base_pass': base_pass,
                'has_logic': has_logic,
                'has_specific': has_specific,
                'has_deep_counter': has_deep_counter,
                'content_length': len(content),
                'counter_length': len(counter) if isinstance(counter, str) else 0,
            })

    rate = (effective_attacks / total_attacks * 100) if total_attacks > 0 else 0
    return rate, {
        'total': total_attacks,
        'effective': effective_attacks,
        'details': details,
    }


# ==================== 维度2：防御成功率 (20%) ====================

def score_defense_rate(data: Dict) -> Tuple[float, Dict]:
    """
    防御成功率 = 成功化解 / 被攻击次数

    判定方式（两层检测）：
    1. 显式反击：counter_attack 字段非空且长度 > 50字
    2. 隐式反击：被攻击方在后续发言中回应了攻击关键词（>=2个关键词匹配）
    """
    total_defended = 0
    successful = 0
    details = []

    # 收集所有被攻击记录
    attack_records = []
    for r in data.get('rounds', []):
        for c in r.get('clash_rounds', []):
            target = c.get('target', '')
            if target:
                total_defended += 1
                attack_records.append({
                    'target': target,
                    'attacker': c.get('attacker', ''),
                    'content': c.get('attack_content', '') or '',
                    'counter': c.get('counter_attack', ''),
                    'round': r.get('round_number', 0),
                })

    # 收集所有 stance 发言（按轮次排序）
    all_stances = []
    for r in data.get('rounds', []):
        for s in r.get('stances', []):
            all_stances.append({
                'expert': s.get('expert', ''),
                'content': s.get('stance', '') or '',
                'round': r.get('round_number', 0),
            })

    # 判定防御成功率
    for atk in attack_records:
        target = atk['target']

        # 层1：显式反击
        counter = atk['counter']
        has_explicit = bool(counter) and isinstance(counter, str) and len(counter) > 50

        # 层2：隐式反击 — 被攻击方在后续发言中回应攻击关键词
        has_implicit = False
        matched_keywords = []
        if not has_explicit:
            # 提取攻击内容中的核心关键词（排除常见虚词）
            atk_keywords = _extract_keywords(atk['content'][:100], max_words=8)
            stop_words = {
                '什么', '这个', '那个', '问题', '观点', '认为', '觉得',
                '我们', '你们', '他们', '一个', '可以', '就是',
            }
            atk_keywords = [w for w in atk_keywords if w not in stop_words]

            # 查找被攻击方在后续轮次的 stance
            for stance in all_stances:
                if (stance['expert'] == target and
                    stance['round'] >= atk['round'] and
                    stance['content']):
                    # 检查是否回应了至少2个攻击关键词
                    matched = [kw for kw in atk_keywords if kw in stance['content']]
                    if len(matched) >= 2:
                        has_implicit = True
                        matched_keywords = matched
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
            'matched_keywords': matched_keywords,
        })

    rate = (successful / total_defended * 100) if total_defended > 0 else 0
    return rate, {
        'total_defended': total_defended,
        'successful': successful,
        'details': details,
    }


# ==================== 维度3：证据命中率 (15%) ====================

def score_evidence_hit(data: Dict) -> Tuple[float, Dict]:
    """
    证据命中率 = 有效引用的发言 / 总发言数

    三层标准：
    - BOOK_BASED（书籍讨论）：章节/原文/情节/页码/书中提到
    - TOPIC_BASED（通用话题）：案例/数据/理论/专家观点/具体数字/百分比/年份
    - HYBRID（混合）：合并两类

    每次发言至少满足2种证据模式才算"有证据"
    """
    total_speeches = 0
    with_evidence = 0
    pattern_counts = {
        'book_based': 0,
        'topic_based': 0,
        'hybrid': 0,
    }

    for r in data.get('rounds', []):
        for s in r.get('stances', []):
            total_speeches += 1
            content = s.get('stance', '') or ''

            book_count = _count_evidence_patterns(content, BOOK_BASED_PATTERNS)
            topic_count = _count_evidence_patterns(content, TOPIC_BASED_PATTERNS)

            if book_count > 0:
                pattern_counts['book_based'] += 1
            if topic_count > 0:
                pattern_counts['topic_based'] += 1
            if book_count > 0 and topic_count > 0:
                pattern_counts['hybrid'] += 1

            # 至少满足2种模式才算有效
            total_patterns = book_count + topic_count
            if total_patterns >= 2:
                with_evidence += 1

        for c in r.get('clash_rounds', []):
            total_speeches += 1
            content = c.get('attack_content', '') or ''

            book_count = _count_evidence_patterns(content, BOOK_BASED_PATTERNS)
            topic_count = _count_evidence_patterns(content, TOPIC_BASED_PATTERNS)

            if book_count > 0:
                pattern_counts['book_based'] += 1
            if topic_count > 0:
                pattern_counts['topic_based'] += 1
            if book_count > 0 and topic_count > 0:
                pattern_counts['hybrid'] += 1

            total_patterns = book_count + topic_count
            if total_patterns >= 2:
                with_evidence += 1

    rate = (with_evidence / total_speeches * 100) if total_speeches > 0 else 0
    return rate, {
        'total_speeches': total_speeches,
        'with_evidence': with_evidence,
        'pattern_distribution': pattern_counts,
    }


# ==================== 维度4：风格辨识度 (15%) ====================

def score_style_recognition(data: Dict) -> Tuple[float, Dict]:
    """
    风格辨识度 = 符合严格标准的发言 / 总发言

    需要同时满足四项：
    1. 有口语化表达（"说白了/坦白说/老实说/你想想/问题是/不是...而是"）
    2. 有比喻/类比（"就像/好比/类似于/打个比方/本质上是"）
    3. 长度适中（100-800字）
    4. 不是模板化内容（不包含"综上所述/总而言之/一言以蔽之"等总结词）
    """
    total = 0
    distinctive = 0
    details = []

    for r in data.get('rounds', []):
        for s in r.get('stances', []):
            total += 1
            content = s.get('stance', '') or ''

            # 条件1：口语化表达
            has_oral = any(expr in content for expr in ORAL_EXPRESSIONS)

            # 条件2：比喻/类比
            has_metaphor = any(p.search(content) for p in METAPHOR_PATTERNS)

            # 条件3：长度适中
            good_length = 100 < len(content) < 800

            # 条件4：非模板化
            has_template = any(tw in content for tw in TEMPLATE_WORDS)

            # 四项同时满足
            is_distinctive = has_oral and has_metaphor and good_length and not has_template

            if is_distinctive:
                distinctive += 1

            details.append({
                'expert': s.get('expert', ''),
                'has_oral': has_oral,
                'has_metaphor': has_metaphor,
                'good_length': good_length,
                'has_template': has_template,
                'length': len(content),
                'distinctive': is_distinctive,
            })

    rate = (distinctive / total * 100) if total > 0 else 0
    return rate, {
        'total': total,
        'distinctive': distinctive,
        'details': details,
    }


# ==================== 维度5：认知贡献 (10%) ====================

def score_cognitive_contribution(data: Dict) -> Tuple[float, Dict]:
    """
    认知贡献 = 有深度认知升级的轮次 / 总轮次

    需要同时满足：
    1. cognitive_upgrade.new_thinking 存在且长度 > 50字
    2. 包含行动建议（"作为个人/作为社会/作为政策" 或 "应该/需要/建议"）
    3. 或包含矛盾分析（"表面上...实际上..."）
    """
    total_rounds = 0
    with_upgrade = 0
    details = []

    for r in data.get('rounds', []):
        total_rounds += 1
        upgrade = r.get('cognitive_upgrade', {})

        # 条件1：new_thinking 存在且长度 > 50字
        new_thinking = upgrade.get('new_thinking', '') or ''
        has_new_thinking = len(new_thinking) > 50

        # 条件2：包含行动建议
        has_action = any(marker in new_thinking for marker in ACTION_MARKERS)

        # 条件3：包含矛盾分析
        has_contrast = any(p.search(new_thinking) for p in CONTRAST_MARKERS)

        # 必须同时满足：条件1 + (条件2 或 条件3)
        is_quality = has_new_thinking and (has_action or has_contrast)

        if is_quality:
            with_upgrade += 1

        details.append({
            'round': r.get('round_number', 0),
            'has_new_thinking': has_new_thinking,
            'has_action': has_action,
            'has_contrast': has_contrast,
            'is_quality': is_quality,
            'new_thinking_length': len(new_thinking),
        })

    rate = (with_upgrade / total_rounds * 100) if total_rounds > 0 else 0
    return rate, {
        'total_rounds': total_rounds,
        'with_upgrade': with_upgrade,
        'details': details,
    }


# ==================== 维度6：案例质量 (10%) ====================

def score_case_quality(data: Dict) -> Tuple[float, Dict]:
    """
    案例质量 = 有完整案例的轮次 / 总轮次

    优质案例需要四要素缺一不可：
    1. 案例名称（case_name 非空）
    2. 来源（case_source 非空）
    3. 具体内容（case_content > 30字）
    4. 结果/教训（case_outcome 或 case_lesson 非空）
    """
    total_rounds = 0
    with_cases = 0
    case_details = []

    for r in data.get('rounds', []):
        total_rounds += 1
        has_quality_case = False
        round_cases = []

        # 检查 reality_cases 中的案例
        cases = r.get('reality_cases', [])
        for c in cases:
            if not isinstance(c, dict):
                continue

            name = c.get('case_name', '') or ''
            source = c.get('case_source', '') or ''
            content = c.get('case_content', '') or ''
            outcome = c.get('case_outcome', '') or ''
            lesson = c.get('case_lesson', '') or ''

            # 四要素检查
            has_name = len(name) > 0
            has_source = len(source) > 0
            has_content = len(content) > 30
            has_result = len(outcome) > 0 or len(lesson) > 0

            is_complete = has_name and has_source and has_content and has_result

            round_cases.append({
                'name': name,
                'complete': is_complete,
                'checks': {
                    'has_name': has_name,
                    'has_source': has_source,
                    'has_content': has_content,
                    'has_result': has_result,
                }
            })

            if is_complete:
                has_quality_case = True

        if has_quality_case:
            with_cases += 1

        case_details.append({
            'round': r.get('round_number', 0),
            'has_case': has_quality_case,
            'cases': round_cases,
        })

    rate = (with_cases / total_rounds * 100) if total_rounds > 0 else 0
    return rate, {
        'total_rounds': total_rounds,
        'with_cases': with_cases,
        'round_details': case_details,
    }


# ==================== 维度7：结构完整性 (5%) ====================

def score_structure(data: Dict) -> Tuple[float, Dict]:
    """
    结构完整性 = 必需字段存在率 + 全员参与检查

    检查：
    - title 存在
    - experts 存在且 >= 6人
    - rounds 存在且 >= 3轮
    - final_insight 存在
    - open_questions 存在
    - 每轮 stance 数量 >= 6（全员参与）
    """
    checks = {
        'title': bool(data.get('title')),
        'experts': len(data.get('experts', [])) >= 6,
        'rounds': len(data.get('rounds', [])) >= 3,
        'final_insight': bool(data.get('final_insight')),
        'open_questions': bool(data.get('open_questions')),
    }

    # 全员参与检查
    full_participation = True
    participation_details = []

    for r in data.get('rounds', []):
        stances = r.get('stances', [])
        expert_names = set(s.get('expert', '') for s in stances if s.get('expert'))
        round_num = r.get('round_number', 0)

        # 检查是否有6位不同专家发言
        has_six = len(expert_names) >= 6
        checks[f'round_{round_num}_full_participation'] = has_six

        if not has_six:
            full_participation = False

        participation_details.append({
            'round': round_num,
            'expert_count': len(expert_names),
            'experts': sorted(list(expert_names)),
        })

    passed = sum(1 for v in checks.values() if v is True)
    total = len(checks)
    rate = (passed / total * 100)

    return rate, {
        'checks': checks,
        'full_participation': full_participation,
        'participation_details': participation_details,
    }


# ==================== 主评分函数 ====================

def score_discussion(json_path: str) -> Dict:
    """
    主评分函数：7维度评分 V2。

    Returns:
        {
            total: float (0-100),
            dimensions: {dim_name: {score, weight, weighted, details}},
            grade: str (A/B/C/D/F),
            version: str
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

    # 评级（更严格）
    if total >= 92:
        grade = 'A'
    elif total >= 82:
        grade = 'B'
    elif total >= 70:
        grade = 'C'
    elif total >= 55:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'total': round(total, 1),
        'grade': grade,
        'version': '2.0',
        'dimensions': dimensions,
    }


def print_report(result: Dict):
    """打印评分报告"""
    print(f"\n{'='*70}")
    print(f"讨论质量评分报告 V{result.get('version', '2.0')}")
    print(f"{'='*70}")
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

    print(f"{'维度':<12} {'得分':>6} {'权重':>6} {'加权':>6}  {'诊断'}")
    print(f"{'-'*60}")

    diagnostics = {
        'attack_efficiency': '基础>60字 + 强条件(逻辑/证据/反击)',
        'defense_rate': '显式反击>50字 或 隐式回应>=2关键词',
        'evidence_hit': '至少2种证据模式(书籍/通用)',
        'style_recognition': '口语+比喻+长度适中+非模板',
        'cognitive_contribution': 'new_thinking>50字 + 行动/矛盾',
        'case_quality': '四要素完整(名+源+内容+结果)',
        'structure': '6人全员参与 + 基础字段',
    }

    for dim_name, dim in result['dimensions'].items():
        cn = dim_names_cn.get(dim_name, dim_name)
        diag = diagnostics.get(dim_name, '')
        print(f"{cn:<12} {dim['score']:>5.1f}% {dim['weight']*100:>5.0f}% {dim['weighted']:>5.1f}  {diag}")

    print()

    # 详细诊断
    print("详细诊断:")
    print("-" * 60)

    # 攻击效率详情
    atk = result['dimensions']['attack_efficiency']['details']
    if atk.get('total', 0) > 0:
        print(f"  攻击: {atk['effective']:.1f}/{atk['total']} 有效")
        for d in atk.get('details', [])[:3]:
            status = "✓" if d['effective'] else "✗"
            print(f"    {status} {d['attacker']}→{d['target']}: "
                  f"长度{d['content_length']} 逻辑{d['has_logic']} 证据{d['has_specific']} 反击{d['has_deep_counter']}")

    # 证据命中详情
    evd = result['dimensions']['evidence_hit']['details']
    print(f"  证据: {evd['with_evidence']}/{evd['total_speeches']} 发言含有效引用")
    pd = evd.get('pattern_distribution', {})
    if pd:
        print(f"    书籍类: {pd.get('book_based', 0)}, 通用类: {pd.get('topic_based', 0)}, 混合: {pd.get('hybrid', 0)}")

    # 风格详情
    sty = result['dimensions']['style_recognition']['details']
    print(f"  风格: {sty['distinctive']}/{sty['total']} 发言匹配严格标准")

    # 结构详情
    struct = result['dimensions']['structure']['details']
    print(f"  结构: 全员参与={struct.get('full_participation', False)}")
    for pd in struct.get('participation_details', []):
        print(f"    第{pd['round']}轮: {pd['expert_count']}人参与 {pd['experts']}")

    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scorer_v2.py <json_path>")
        sys.exit(1)

    json_path = sys.argv[1]
    result = score_discussion(json_path)
    print_report(result)

    # 保存结果
    output_path = json_path.replace('.json', '_score_v2.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Score saved: {output_path}")


# ==================== 测试代码 ====================

def _create_test_data() -> Dict:
    """创建测试数据"""
    return {
        "title": "测试书籍圆桌讨论",
        "experts": [
            {"name": "专家A", "speaking_style": "冷静克制"},
            {"name": "专家B", "speaking_style": "直接果断"},
            {"name": "专家C", "speaking_style": "尖锐直接"},
            {"name": "专家D", "speaking_style": "深刻冷静"},
            {"name": "专家E", "speaking_style": "幽默智慧"},
            {"name": "专家F", "speaking_style": "理性客观"},
        ],
        "rounds": [
            {
                "round_number": 1,
                "stances": [
                    {
                        "expert": "专家A",
                        "stance": "说白了，这本书的核心问题就在于作者试图用经济学的框架去解释一切社会现象，但问题是社会远比经济模型复杂。就像试图用一把尺子去丈量大海的深度，本质上是不可能的。书中第3章提到的那个案例，2023年的数据显示有85%的参与者都受到了影响，这恰恰证明了我的观点。"
                    },
                    {
                        "expert": "专家B",
                        "stance": "我不同意专家A的看法。坦率说，作者的理论框架虽然不完美，但是提供了一个全新的视角。数据显示，在应用了这个模型之后，效率提升了23%。这就好比给盲人一副眼镜，虽然不能完全恢复视力，但至少能看到轮廓。"
                    },
                    {
                        "expert": "专家C",
                        "stance": "你们两个都错了。这本书的问题根本不在于框架本身，而在于作者忽视了权力结构的影响。第5章中描写道，那些所谓的'自愿交易'实际上充满了胁迫。表面上看起来是自由选择，实际上是没有选择的选择。"
                    },
                    {
                        "expert": "专家D",
                        "stance": "我想从另一个角度来分析。书中提到的那个实验，2019年发表在《自然》杂志上，样本量达到5000人。结果显示，干预组的满意度比对照组高出15个百分点。这个数据表明，作者的结论是有实证基础的。"
                    },
                    {
                        "expert": "专家E",
                        "stance": "各位，我们不妨打个比方。这本书就像是一道精致的法国菜，摆盘很漂亮，但味道却不敢恭维。作者用了大量的学术术语来包装一个简单的道理：人们总是追求自身利益最大化。问题是，这还用你说吗？"
                    },
                    {
                        "expert": "专家F",
                        "stance": "作为理性的观察者，我认为需要区分两个层面。从规范层面看，作者的论证存在漏洞；但从描述层面看，他的观察是准确的。根据皮尤研究中心2024年的调查，67%的受访者认同书中的核心论点。这个案例说明，理论与实践之间存在鸿沟。"
                    },
                ],
                "clash_rounds": [
                    {
                        "attacker": "专家B",
                        "target": "专家A",
                        "attack_type": "证据质疑",
                        "attack_content": "专家A，你刚才说社会远比经济模型复杂，但是你的论证有一个根本性的漏洞。你引用的那个2023年的数据，来源是哪里？书中第3章确实提到了一个案例，但那个案例的样本量只有120人，而且是在特定文化背景下进行的。如果把这个结果推广到整个社会，那就是以偏概全。因为小样本的结论不能代表整体，这是统计学最基本的常识。",
                        "counter_attack": "专家B，你质疑我的数据来源，这很好。但问题是，你自己引用的那个'效率提升23%'的数据，书中根本没有给出原始出处。我翻遍了全书，没有找到任何关于这个实验的详细描述。如果这是你自己的臆测，那我们就不是在讨论同一本书了。"
                    },
                    {
                        "attacker": "专家C",
                        "target": "专家B",
                        "attack_type": "逻辑攻击",
                        "attack_content": "专家B，你的类比是有问题的。你说'给盲人一副眼镜'，但问题是这本书的读者并不是盲人，他们需要的是更深刻的洞察，而不是表面的轮廓。如果作者只是提供了'轮廓'，那他为什么要写300页？这本质上是一种 intellectual laziness。",
                        "counter_attack": ""
                    },
                ],
                "cognitive_upgrade": {
                    "new_thinking": "经过这一轮讨论，我意识到这本书的价值不在于它的结论是否正确，而在于它提出的问题本身。作为个人，我们应该培养批判性思维，不轻信任何单一的理论框架；作为社会，我们需要建立更多元的声音平台；作为政策制定者，应该警惕用简单模型解决复杂问题的倾向。表面上作者在讨论经济学，实际上他在探讨人类理性的边界。",
                    "complexity": "这个问题存在内在矛盾：一方面我们需要简化模型来理解世界，另一方面简化必然导致失真。"
                },
                "reality_cases": [
                    {
                        "case_name": "2008年金融危机",
                        "case_source": "《大空头》迈克尔·刘易斯",
                        "case_content": "雷曼兄弟在2008年9月15日申请破产保护，标志着全球金融危机的全面爆发。此前，该公司的杠杆率达到了30:1，持有大量次级抵押贷款支持证券。",
                        "case_outcome": "导致全球股市蒸发超过30万亿美元",
                        "case_lesson": "复杂金融模型的风险被严重低估"
                    }
                ],
            },
            {
                "round_number": 2,
                "stances": [
                    {"expert": "专家A", "stance": "短。"},
                    {"expert": "专家B", "stance": "我坚持我的观点。"},
                    {"expert": "专家C", "stance": "同上。"},
                    {"expert": "专家D", "stance": "综上所述，我们需要更深入地思考这个问题。"},
                    {"expert": "专家E", "stance": "哈哈，你们太认真了。"},
                    {"expert": "专家F", "stance": "数据表明，结论是不确定的。"},
                ],
                "clash_rounds": [],
                "cognitive_upgrade": {
                    "new_thinking": "",
                    "complexity": ""
                },
                "reality_cases": [],
            },
        ],
        "final_insight": "测试总结",
        "open_questions": ["问题1", "问题2"],
    }


def _create_edge_case_data() -> Dict:
    """创建边界情况测试数据"""
    return {
        "title": "边界测试",
        "experts": [{"name": f"专家{i}"} for i in range(6)],
        "rounds": [
            {
                "round_number": 1,
                "stances": [
                    {"expert": "专家A", "stance": "a" * 50},  # 太短，不满足风格
                    {"expert": "专家B", "stance": "a" * 150},  # 无口语化
                    {"expert": "专家C", "stance": "说白了，这就像一场游戏。" * 20},  # 有口语+比喻，但太短重复
                    {"expert": "专家D", "stance": "a" * 900},  # 太长
                    {"expert": "专家E", "stance": "综上所述，一言以蔽之。" + "a" * 200},  # 有模板词
                    {"expert": "专家F", "stance": "老实说，这个问题本质上是复杂的。就好比一座冰山，我们只能看到水面上的部分。书中第2章详细描写了这一现象，数据显示有78%的案例符合这一模式。"},
                ],
                "clash_rounds": [
                    {
                        "attacker": "专家A",
                        "target": "专家B",
                        "attack_content": "短攻击。",
                        "counter_attack": "",
                    },
                    {
                        "attacker": "专家C",
                        "target": "专家D",
                        "attack_content": "你的观点有问题，因为数据不支持。书中第3章提到的案例显示，2024年有65%的参与者改变了态度。如果这是真的，那么你的理论就站不住脚。本质上，你混淆了相关性和因果性。",
                        "counter_attack": "你说我混淆了相关性和因果性，但问题是你的解读过于狭隘。那个案例的样本只有200人，而且是在特定文化背景下进行的，不能推广到一般情况。",
                    },
                ],
                "cognitive_upgrade": {
                    "new_thinking": "我们应该重新审视这个问题。作为个人，需要保持开放心态；作为社会，需要包容不同声音。",
                },
                "reality_cases": [
                    {
                        "case_name": "",
                        "case_source": "某书",
                        "case_content": "一些内容",
                        "case_outcome": "",
                    }
                ],
            }
        ],
        "final_insight": "测试",
        "open_questions": ["Q1"],
    }


def run_tests():
    """运行测试"""
    import tempfile
    import os

    print("=" * 70)
    print("scorer_v2.py 测试开始")
    print("=" * 70)

    # 测试1：正常数据
    print("\n【测试1】正常数据评分")
    test_data = _create_test_data()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    try:
        result = score_discussion(temp_path)
        print_report(result)

        # 验证关键指标
        atk = result['dimensions']['attack_efficiency']
        assert atk['details']['total'] == 2, f"攻击总数应为2，实际{atk['details']['total']}"
        assert atk['details']['effective'] == 1.5, f"有效攻击应为1.5，实际{atk['details']['effective']}"
        print("  ✓ 攻击效率测试通过")

        defense = result['dimensions']['defense_rate']
        assert defense['details']['total_defended'] == 2, f"被攻击数应为2"
        # 专家A被专家B攻击，专家A的counter_attack > 50字（显式反击）
        # 专家B被专家C攻击，专家B的counter_attack为空
        # 但专家B在第1轮有stance发言，可能匹配隐式反击条件
        # 实际结果取决于关键词匹配，这里只验证总数
        assert defense['details']['successful'] >= 1, f"成功防御应至少1"
        print(f"  ✓ 防御成功率测试通过（成功{defense['details']['successful']}/2）")

        evd = result['dimensions']['evidence_hit']
        assert evd['details']['total_speeches'] == 14, f"总发言数应为14，实际{evd['details']['total_speeches']}"
        print("  ✓ 证据命中率测试通过")

        style = result['dimensions']['style_recognition']
        assert style['details']['total'] == 12, f"总发言数应为12，实际{style['details']['total']}"
        print("  ✓ 风格辨识度测试通过")

        struct = result['dimensions']['structure']
        assert struct['details']['full_participation'] == True, "应全员参与"
        print("  ✓ 结构完整性测试通过")

    finally:
        os.unlink(temp_path)

    # 测试2：边界数据
    print("\n【测试2】边界数据评分")
    edge_data = _create_edge_case_data()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(edge_data, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    try:
        result = score_discussion(temp_path)
        print_report(result)

        # 验证边界情况
        style = result['dimensions']['style_recognition']
        assert style['details']['distinctive'] == 1, f"风格匹配应为1（只有专家F满足全部条件），实际{style['details']['distinctive']}"
        print("  ✓ 边界风格测试通过")

        case = result['dimensions']['case_quality']
        assert case['details']['with_cases'] == 0, f"案例质量应为0（缺少case_name和outcome），实际{case['details']['with_cases']}"
        print("  ✓ 边界案例测试通过")

        atk = result['dimensions']['attack_efficiency']
        # 专家A→专家B: 长度4，不满足基础条件(>60)，完全无效
        # 专家C→专家D: 长度83，满足基础条件但无强条件，50%有效
        # 但专家C的攻击中有"65%"和"书中第3章"，满足具体证据条件，所以是100%有效
        # 因此有效攻击 = 0 + 1.0 = 1.0
        assert atk['details']['effective'] == 1.0, f"有效攻击应为1.0（一个完全无效，一个100%有效因为有具体证据），实际{atk['details']['effective']}"
        print("  ✓ 边界攻击测试通过")

    finally:
        os.unlink(temp_path)

    print("\n" + "=" * 70)
    print("所有测试通过！")
    print("=" * 70)


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == '--test':
        run_tests()
    else:
        main()
