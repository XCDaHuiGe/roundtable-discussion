# -*- coding: utf-8 -*-
"""
Auto Scorer — 自动评分器（零LLM依赖）

从辩论JSON中提取客观信号，自动计算6维度分数。
不依赖Agent主观判断，纯Python启发式规则。

评分信号：
  reality_grounding:    证据数量 × 类型多样性 × 引用密度
  contradiction_handling: 回应链完整性 × 碰撞轮次 × 反驳深度
  strategic_depth:      发言长度 × 逻辑连接词密度 × 论证层次
  cross_domain_transfer: 跨域引用数 × 类比使用
  novelty:              与专家已有素材的差异度
  personality_consistency: 知识边界合规 × 高频词使用 × 时代一致性

用法：
  from engine.auto_scorer import auto_score_debate
  scores = auto_score_debate(debate_json, expert_names=['老子', '孔子'])
  # → {'reality_grounding': 72, 'contradiction_handling': 65, ...}
"""

import re
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
#  信号提取器
# ═══════════════════════════════════════════════════════════════

# 证据类型关键词
EVIDENCE_PATTERNS = {
    'book_ref': re.compile(r'[《》]|一书中|作者|书中|写道|指出|认为|说过'),
    'data': re.compile(r'\d+%|\d+万|\d+亿|\d+\.\d+|数据|统计|调查|研究显示|报告'),
    'case': re.compile(r'案例|例如|比如|就像|譬如|试想|想象一下|有一个'),
    'expert_ref': re.compile(r'学者|教授|专家|先生|博士|大师'),
    'theory': re.compile(r'理论|假说|模型|框架|范式|原理|法则|定律'),
    'history': re.compile(r'年代|时期|朝代|世纪|历史|当年|古[代今]|昔'),
}

# 逻辑连接词
LOGIC_CONNECTORS = [
    '因此', '所以', '然而', '但是', '不过', '虽然', '尽管',
    '如果', '假设', '换言之', '换句话说', '进一步', '更深一层',
    '反过来说', '相反', '另一方面', '不仅如此', '更重要的是',
    '由此可见', '综上所述', '归根结底', '本质上',
]

# 跨域引用词
CROSS_DOMAIN_MARKERS = [
    '物理学', '生物学', '心理学', '经济学', '哲学', '数学',
    '进化', '量子', '热力学', '熵', '博弈论', '混沌',
    '神经科学', '社会学', '人类学', '考古学', '天文学',
    '医学', '法律', '政治', '艺术', '音乐', '文学',
]


def _count_evidence(text: str) -> Dict[str, int]:
    """统计文本中各类证据的数量"""
    counts = {}
    for etype, pattern in EVIDENCE_PATTERNS.items():
        counts[etype] = len(pattern.findall(text))
    return counts


def _count_logic_connectors(text: str) -> int:
    """统计逻辑连接词数量"""
    return sum(text.count(c) for c in LOGIC_CONNECTORS)


def _count_cross_domain(text: str) -> int:
    """统计跨域引用数量"""
    return sum(text.count(m) for m in CROSS_DOMAIN_MARKERS)


def _calc_text_complexity(text: str) -> float:
    """计算文本复杂度（0-100）

    基于：平均句长、逻辑连接词密度、词汇多样性
    """
    if not text:
        return 0

    # 平均句长
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_len = sum(len(s) for s in sentences) / max(len(sentences), 1)

    # 逻辑连接词密度（每100字）
    connector_count = _count_logic_connectors(text)
    connector_density = connector_count / max(len(text) / 100, 1)

    # 组合得分
    len_score = min(avg_len / 80 * 100, 100)  # 80字以上的句子算满分
    density_score = min(connector_density / 3 * 100, 100)  # 每100字3个以上算满分

    return len_score * 0.6 + density_score * 0.4


def _check_response_chain(debate_json: Dict) -> float:
    """检查回应链完整性（0-100）

    检查：每条发言是否回应了前一条
    """
    rounds = debate_json.get('rounds', [])
    if not rounds:
        return 0

    total_speeches = 0
    responded_speeches = 0

    for i, round_data in enumerate(rounds):
        speeches = round_data.get('speeches', [])
        for j, speech in enumerate(speeches):
            total_speeches += 1
            content = speech.get('content', '')

            # 第一轮不需要回应前文
            if i == 0 and j == 0:
                responded_speeches += 1
                continue

            # 检查是否有回应标记
            if speech.get('responds_to') or speech.get('target'):
                responded_speeches += 1
                continue

            # 启发式：内容中是否提到了对方的观点
            if i > 0:
                prev_round = rounds[i - 1]
                prev_experts = [s.get('expert', '') for s in prev_round.get('speeches', [])]
                if any(exp in content for exp in prev_experts if exp):
                    responded_speeches += 1
                    continue

            # 同一轮中回应前一条
            if j > 0:
                prev_expert = speeches[j - 1].get('expert', '')
                if prev_expert and prev_expert in content:
                    responded_speeches += 1

    return (responded_speeches / max(total_speeches, 1)) * 100


def _check_personality(text: str, expert_name: str) -> float:
    """检查人格一致性（0-100）

    基于：知识边界合规 + 高频词使用
    """
    try:
        from knowledge_boundary_checker import check_knowledge_boundary, get_metaphor_guide
        result = check_knowledge_boundary(text, expert_name)

        score = 100

        # 禁用词扣分（每个扣15分）
        forbidden_count = len(result.get('forbidden_words', []))
        score -= forbidden_count * 15

        # 警告扣分（每个扣5分）
        warning_count = len(result.get('warnings', []))
        score -= warning_count * 5

        # 高频词加分（使用了专家的高频词）
        guide = get_metaphor_guide(expert_name)
        if guide:
            freq_words = guide.get('high_freq_words', [])
            used = sum(1 for w in freq_words if w in text)
            score += min(used * 3, 15)  # 最多加15分

        return max(0, min(100, score))
    except Exception:
        return 60  # 无法检查时给默认分


def _calc_novelty(text: str, existing_quotes: List[str] = None) -> float:
    """计算新颖性（0-100）

    与专家已有素材对比，差异越大越新颖
    """
    if not existing_quotes:
        return 60  # 无对比素材时给默认分

    # 简单的Jaccard相似度
    text_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', text))
    if not text_words:
        return 50

    max_sim = 0
    for quote in existing_quotes:
        quote_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', quote))
        if not quote_words:
            continue
        intersection = text_words & quote_words
        union = text_words | quote_words
        sim = len(intersection) / max(len(union), 1)
        max_sim = max(max_sim, sim)

    # 相似度越低越新颖
    novelty = (1 - max_sim) * 100
    return max(30, min(100, novelty))


# ═══════════════════════════════════════════════════════════════
#  主评分函数
# ═══════════════════════════════════════════════════════════════

def auto_score_debate(
    debate_json: Dict,
    expert_names: List[str] = None,
    existing_quotes: Dict[str, List[str]] = None,
) -> Dict[str, float]:
    """自动评分辩论（零LLM依赖）

    Args:
        debate_json: 辩论JSON
        expert_names: 参与辩论的专家名列表
        existing_quotes: 专家已有的金句库 {专家名: [金句列表]}

    Returns:
        6维度分数 dict，可直接传入 score_discussion()
    """
    rounds = debate_json.get('rounds', [])
    clash_rounds = debate_json.get('clash_rounds', [])
    key_quotes = debate_json.get('key_quotes', [])

    # 合并所有发言文本
    all_speeches = []
    expert_speeches = {}
    for round_data in rounds:
        for speech in round_data.get('speeches', []):
            content = speech.get('content', '')
            all_speeches.append(content)
            expert = speech.get('expert', '')
            if expert:
                expert_speeches.setdefault(expert, []).append(content)

    all_text = '\n'.join(all_speeches)
    total_chars = len(all_text)

    # ── 1. reality_grounding (25%) ──
    # 证据数量 + 类型多样性 + 引用密度
    evidence_counts = _count_evidence(all_text)
    total_evidence = sum(evidence_counts.values())
    evidence_types = sum(1 for v in evidence_counts.values() if v > 0)

    evidence_density = total_evidence / max(total_chars / 500, 1)  # 每500字证据数
    evidence_score = min(evidence_density * 20, 60)  # 基础分（密度）
    evidence_score += evidence_types * 6  # 类型多样性加分（最多6种×6=36）
    evidence_score += min(len(key_quotes) * 3, 10)  # 金句加分
    reality_grounding = max(30, min(100, evidence_score))

    # ── 2. contradiction_handling (20%) ──
    # 回应链完整性 + 碰撞轮次 + 反驳深度
    response_chain = _check_response_chain(debate_json)
    clash_score = min(len(clash_rounds) * 25, 75)  # 每个碰撞轮25分，最多75

    # 反驳深度：检查是否有"但是"、"然而"等反驳标记
    rebuttal_markers = sum(all_text.count(m) for m in ['但是', '然而', '不过', '恰恰相反', '问题在于'])
    rebuttal_score = min(rebuttal_markers * 5, 25)

    contradiction_handling = response_chain * 0.4 + clash_score * 0.35 + rebuttal_score * 0.25
    contradiction_handling = max(30, min(100, contradiction_handling))

    # ── 3. strategic_depth (20%) ──
    # 文本复杂度 + 逻辑连接词 + 论证层次
    complexity = _calc_text_complexity(all_text)
    connector_count = _count_logic_connectors(all_text)
    connector_score = min(connector_count * 3, 60)

    # 论证层次：是否有"首先...其次...最后"结构
    layer_markers = sum(all_text.count(m) for m in ['首先', '其次', '最后', '第一', '第二', '第三'])
    layer_score = min(layer_markers * 8, 40)

    strategic_depth = complexity * 0.4 + connector_score * 0.3 + layer_score * 0.3
    strategic_depth = max(30, min(100, strategic_depth))

    # ── 4. cross_domain_transfer (15%) ──
    cross_count = _count_cross_domain(all_text)
    cross_score = min(cross_count * 15, 100)
    # 类比使用
    analogy_count = sum(all_text.count(m) for m in ['就像', '好比', '犹如', '宛如', '类比', '类似于'])
    analogy_score = min(analogy_count * 10, 40)
    cross_domain_transfer = cross_score * 0.6 + analogy_score * 0.4 + 20  # 基础分20
    cross_domain_transfer = max(30, min(100, cross_domain_transfer))

    # ── 5. novelty (10%) ──
    # 与已有素材的差异度
    if existing_quotes and expert_names:
        all_existing = []
        for name in expert_names:
            all_existing.extend(existing_quotes.get(name, []))
        novelty = _calc_novelty(all_text, all_existing)
    else:
        # 无对比素材时，用反问句/极端案例作为新颖性信号
        novelty_markers = sum(all_text.count(m) for m in ['如果...呢', '试想', '极端情况', '反过来说', '你有没有想过'])
        novelty = 50 + min(novelty_markers * 8, 40)

    # ── 6. personality_consistency (10%) ──
    if expert_names:
        personality_scores = []
        for name in expert_names:
            expert_text = '\n'.join(expert_speeches.get(name, []))
            if expert_text:
                personality_scores.append(_check_personality(expert_text, name))
        personality_consistency = sum(personality_scores) / max(len(personality_scores), 1) if personality_scores else 60
    else:
        personality_consistency = 60

    return {
        'reality_grounding': round(reality_grounding),
        'contradiction_handling': round(contradiction_handling),
        'strategic_depth': round(strategic_depth),
        'cross_domain_transfer': round(cross_domain_transfer),
        'novelty': round(novelty),
        'personality_consistency': round(personality_consistency),
    }


def blend_scores(auto_scores: Dict[str, float],
                 agent_scores: Dict[str, float] = None,
                 auto_weight: float = 0.6) -> Dict[str, float]:
    """混合自动评分和Agent评分

    默认自动评分占60%，Agent评分占40%。
    如果没有Agent评分，直接使用自动评分。

    Args:
        auto_scores: 自动评分结果
        agent_scores: Agent传入的评分（可选）
        auto_weight: 自动评分权重（0-1）
    """
    if not agent_scores:
        return auto_scores

    blended = {}
    for dim in auto_scores:
        auto_val = auto_scores.get(dim, 50)
        agent_val = agent_scores.get(dim, 50)
        blended[dim] = round(auto_val * auto_weight + agent_val * (1 - auto_weight))

    return blended


# ═══════════════════════════════════════════════════════════════
#  CLI 测试
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import json

    # 构造测试辩论
    test_debate = {
        'topic': 'AI时代，人类的价值在哪里？',
        'rounds': [
            {
                'round_number': 1,
                'round_name': '立场阐述',
                'speeches': [
                    {
                        'expert': '老子',
                        'content': '道可道，非常道。AI虽精巧，终是器物。上善若水，水善利万物而不争。人类的价值不在于与机器比拼计算速度，而在于无为的智慧。数据表明，90%的AI应用仍需人类判断。正如《道德经》所言：知人者智，自知者明。'
                    },
                    {
                        'expert': '芒格',
                        'content': '用多元思维模型来分析这个问题。首先，从心理学角度看，人类有系统1和系统2的思维能力，AI目前只有系统2的一部分。其次，从经济学角度看，人类的比较优势在于创造性思维。但是，如果人类不持续学习，这些优势会被侵蚀。'
                    }
                ]
            },
            {
                'round_number': 2,
                'round_name': '相互质疑',
                'speeches': [
                    {
                        'expert': '老子',
                        'target': '芒格',
                        'content': '你的多元思维模型虽好，但过度依赖分析恰恰是问题所在。反者道之动，越是追求精确，越可能偏离本质。历史上无数案例证明，最伟大的发现往往来自直觉而非分析。'
                    },
                    {
                        'expert': '芒格',
                        'target': '老子',
                        'content': '老子的无为思想有其智慧，但不能泛化。数据显示，在投资领域，系统化分析的回报率远高于直觉判断。不过，我承认，在某些复杂系统中，道家的直觉思维确实有独特价值。'
                    }
                ]
            }
        ],
        'clash_rounds': [
            {
                'attacker': '老子',
                'target': '芒格',
                'attack_type': '哲学攻击',
                'attack_content': '过度依赖分析是现代人的通病'
            }
        ],
        'key_quotes': [
            {'expert': '老子', 'quote': '反者道之动，越是追求精确，越可能偏离本质'},
            {'expert': '芒格', 'quote': '人类的比较优势在于创造性思维'},
        ]
    }

    scores = auto_score_debate(test_debate, expert_names=['老子', '芒格'])
    print('=== 自动评分结果 ===')
    for dim, val in scores.items():
        print(f'  {dim}: {val}')

    # 混合评分测试
    agent_scores = {
        'reality_grounding': 80,
        'contradiction_handling': 70,
        'strategic_depth': 75,
        'cross_domain_transfer': 60,
        'novelty': 70,
        'personality_consistency': 85,
    }
    blended = blend_scores(scores, agent_scores)
    print('\n=== 混合评分（自动60% + Agent40%） ===')
    for dim, val in blended.items():
        print(f'  {dim}: {val} (auto={scores[dim]}, agent={agent_scores[dim]})')

    from scorer import score_discussion
    result = score_discussion(blended)
    print(f'\n=== 最终评分 ===')
    print(f'  总分: {result["total"]} ({result["grade"]})')
