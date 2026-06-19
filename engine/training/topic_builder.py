# -*- coding: utf-8 -*-
"""
训练话题构建器：从互联网素材包中提取争议点，匹配专家对，生成训练话题。

用法：
    python engine/training/topic_builder.py content/穷查理宝典_素材.md --library expert-library
    python engine/training/topic_builder.py content/穷查理宝典_素材.md --library expert-library --count 5

与 topic_generator.py 的区别：
    - topic_generator.py：纯从专家信念差异生成（无外部数据）
    - topic_builder.py：从互联网素材中提取争议点 + 匹配专家（有真实素材支撑）
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from training.topic_generator import load_experts, find_belief_conflicts


# ─── 素材解析 ──────────────────────────────────────────────

def parse_material(path: str) -> Dict:
    """解析素材包 .md 文件"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取主题
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ''
    # 去掉书名号
    title = title.replace('《', '').replace('》', '').replace('互联网素材包', '').strip()

    # 提取各观点
    sections = {}
    current_section = ''
    current_content = []

    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content)

    # 提取观点列表
    opinions = []
    opinion_blocks = re.split(r'### 观点 \d+:', content)
    for block in opinion_blocks[1:]:  # 跳过第一个（标题前）
        title_end = block.find('\n')
        opinion_title = block[:title_end].strip() if title_end > 0 else ''
        # 提取引用内容
        quote_match = re.search(r'> (.*?)(?:\n\n|\n—)', block, re.DOTALL)
        quote = quote_match.group(1).strip() if quote_match else ''
        # 提取来源
        source_match = re.search(r'— \[来源: (https?://[^\]]+)\]', block)
        source = source_match.group(1) if source_match else ''

        if quote:
            opinions.append({
                'title': opinion_title[:100],
                'content': quote[:500],
                'source': source,
            })

    return {
        'title': title,
        'sections': sections,
        'opinions': opinions,
        'raw': content,
    }


# ─── 争议点提取 ──────────────────────────────────────────────

def extract_controversies(material: Dict) -> List[Dict]:
    """从素材中提取争议点/矛盾点"""
    controversies = []

    # 1. 从素材的"争议点"章节提取
    raw = material.get('raw', '')
    controversy_section = ''
    in_section = False
    for line in raw.split('\n'):
        if '争议' in line and line.startswith('## '):
            in_section = True
            continue
        if in_section and line.startswith('## '):
            break
        if in_section:
            controversy_section += line + '\n'

    # 解析争议点
    if controversy_section.strip() and '待补充' not in controversy_section:
        points = re.findall(r'\d+\.\s*\*\*(.+?)\*\*', controversy_section)
        for p in points:
            controversies.append({
                'point': p.strip()[:200],
                'source': '素材争议点章节',
                'type': 'explicit',
            })

    # 2. 从观点内容中提取对立观点
    opinions = material.get('opinions', [])
    for i, op1 in enumerate(opinions):
        for op2 in opinions[i+1:]:
            conflict = detect_opinion_conflict(op1['content'], op2['content'])
            if conflict:
                controversies.append({
                    'point': f"{op1['title'][:50]} vs {op2['title'][:50]}",
                    'opinion_a': op1,
                    'opinion_b': op2,
                    'conflict_keywords': conflict,
                    'source': f"{op1.get('source', '')} vs {op2.get('source', '')}",
                    'type': 'detected',
                })

    # 3. 从内容中提取带转折词的争议句
    keywords = ['但是', '然而', '争议', '批评', '反对', '反驳', '质疑',
                '不同看法', '对立', '矛盾', '未必', '并非', '误区']
    for op in opinions:
        content = op.get('content', '')
        sentences = re.split(r'[。！？\n]', content)
        for sent in sentences:
            for kw in keywords:
                if kw in sent and 15 < len(sent) < 150:
                    controversies.append({
                        'point': sent.strip(),
                        'source': op.get('source', ''),
                        'keyword': kw,
                        'type': 'keyword',
                    })
                    break

    # 去重
    seen = set()
    unique = []
    for c in controversies:
        key = c['point'][:50]
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique[:10]


def detect_opinion_conflict(text1: str, text2: str) -> str:
    """检测两段文字是否存在观点冲突"""
    opposites = [
        ('支持', '反对'), ('乐观', '悲观'), ('肯定', '否定'),
        ('成功', '失败'), ('有效', '无效'), ('应该', '不应该'),
        ('必要', '不必要'), ('重要', '不重要'), ('正确', '错误'),
        ('短期', '长期'), ('风险', '安全'), ('创新', '保守'),
        ('个体', '集体'), ('理性', '感性'), ('自由', '秩序'),
    ]

    for a, b in opposites:
        if (a in text1 and b in text2) or (b in text1 and a in text2):
            return f"{a}vs{b}"

    # 否定词检测
    negations = ['不', '非', '无', '未必', '并非', '未必']
    for neg in negations:
        if neg in text1 and neg not in text2:
            return f"否定({neg})"
        if neg in text2 and neg not in text1:
            return f"否定({neg})"

    return ''


# ─── 专家匹配 ──────────────────────────────────────────────

def match_experts_to_controversy(
    controversy: Dict,
    experts: List[Dict],
    conflicts: List[Dict],
) -> Optional[Tuple[str, str]]:
    """
    为争议点匹配最合适的专家对。

    策略：
    1. 如果有素材中的对立观点(opinion_a/b)，根据观点内容匹配专家信念
    2. 如果有冲突关键词，找信念中包含相关词的专家
    3. 兜底：使用已有的专家信念冲突
    """
    point = controversy.get('point', '')

    # 策略1：从素材对立观点匹配
    if controversy.get('opinion_a') and controversy.get('opinion_b'):
        op_a = controversy['opinion_a']['content']
        op_b = controversy['opinion_b']['content']
        best_pair = _match_by_content(op_a, op_b, experts)
        if best_pair:
            return best_pair

    # 策略2：从冲突关键词匹配
    kw = controversy.get('conflict_keywords', '') or controversy.get('keyword', '')
    if kw:
        # 清理关键词
        clean_kw = kw.replace('vs', '').replace('否定(', '').replace(')', '')
        parts = [clean_kw] if clean_kw else []
        if 'vs' in kw:
            parts = kw.split('vs')

        matching_experts = []
        for expert in experts:
            beliefs_text = ' '.join(expert.get('beliefs', []))
            values_text = ' '.join(expert.get('values', []))
            all_text = beliefs_text + values_text
            for part in parts:
                if part and part in all_text:
                    matching_experts.append(expert['name'])
                    break

        if len(matching_experts) >= 2:
            return (matching_experts[0], matching_experts[1])

    # 策略3：使用已有的专家信念冲突
    if conflicts:
        # 随机选一个冲突（可以改进为更智能的匹配）
        import random
        c = random.choice(conflicts)
        return (c['expert1'], c['expert2'])

    # 策略4：随机配对
    if len(experts) >= 2:
        import random
        pair = random.sample(experts, 2)
        return (pair[0]['name'], pair[1]['name'])

    return None


def _match_by_content(opinion_a: str, opinion_b: str,
                       experts: List[Dict]) -> Optional[Tuple[str, str]]:
    """根据观点内容匹配专家"""
    scores = []
    for expert in experts:
        beliefs = expert.get('beliefs', [])
        values = expert.get('values', [])
        all_text = ' '.join(beliefs + values)

        # 计算与 opinion_a 和 opinion_b 的匹配度
        score_a = _text_similarity(opinion_a, all_text)
        score_b = _text_similarity(opinion_b, all_text)
        scores.append({
            'name': expert['name'],
            'score_a': score_a,
            'score_b': score_b,
        })

    if not scores:
        return None

    # 找最匹配 opinion_a 的专家
    scores.sort(key=lambda x: x['score_a'], reverse=True)
    expert_a = scores[0]['name']

    # 找最匹配 opinion_b 的专家（排除 expert_a）
    candidates = [s for s in scores if s['name'] != expert_a]
    if not candidates:
        return None
    candidates.sort(key=lambda x: x['score_b'], reverse=True)
    expert_b = candidates[0]['name']

    if scores[0]['score_a'] > 0 or candidates[0]['score_b'] > 0:
        return (expert_a, expert_b)

    return None


def _text_similarity(text1: str, text2: str) -> float:
    """简单的文本相似度（共享词数）"""
    # 提取有意义的词（2个字以上）
    words1 = set(re.findall(r'[\u4e00-\u9fff]{2,}', text1))
    words2 = set(re.findall(r'[\u4e00-\u9fff]{2,}', text2))
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / max(len(words1), len(words2))


# ─── 话题生成 ──────────────────────────────────────────────

def generate_topic_from_material(
    controversy: Dict,
    expert1: str,
    expert2: str,
    material_title: str,
) -> Dict:
    """从素材争议点 + 专家对生成讨论话题"""
    point = controversy.get('point', '')

    templates = [
        '{e1}和{e2}就"{point}"展开辩论。{e1}的立场是什么？{e2}如何反驳？谁的论据更硬？',
        '关于"{point}"，{e1}和{e2}的根本分歧在哪里？这个分歧在现实中有什么代价？',
        '{e1}认为...，{e2}反驳...——围绕"{point}"的争论，最终谁对？',
        '"{point}"——{e1}和{e2}各执一词。你能从他们的论辩中提炼出什么可验证的判断？',
    ]

    import random
    template = random.choice(templates)
    topic = template.format(e1=expert1, e2=expert2, point=point[:80])

    return {
        'topic': topic,
        'experts': [expert1, expert2],
        'controversy': controversy,
        'material_title': material_title,
        'has_material': True,
    }


# ─── 主入口 ──────────────────────────────────────────────

def build_topics_from_material(
    material_path: str,
    library_dir: str,
    count: int = 3,
) -> List[Dict]:
    """
    主入口：从素材包构建训练话题。

    Args:
        material_path: 素材包 .md 文件路径
        library_dir: 专家库目录
        count: 生成话题数量

    Returns:
        话题列表
    """
    # 1. 解析素材
    material = parse_material(material_path)
    if not material.get('opinions'):
        print(f"  WARNING: 素材中没有提取到观点，无法构建话题")
        return []

    # 2. 提取争议点
    controversies = extract_controversies(material)
    if not controversies:
        print(f"  WARNING: 素材中没有找到争议点")
        # 尝试用观点列表构建简单话题
        controversies = [
            {'point': op['title'][:80], 'source': op.get('source', ''), 'type': 'fallback'}
            for op in material['opinions'][:count]
        ]

    # 3. 加载专家
    experts = load_experts(library_dir)
    if len(experts) < 2:
        print(f"  ERROR: 专家库不足2位专家")
        return []

    # 4. 加载专家冲突
    conflicts = find_belief_conflicts(experts)

    # 5. 为每个争议点匹配专家并生成话题
    topics = []
    used_pairs = set()

    for controversy in controversies[:count * 2]:  # 多取一些，去重后取 count 个
        pair = match_experts_to_controversy(controversy, experts, conflicts)
        if not pair:
            continue

        pair_key = tuple(sorted(pair))
        if pair_key in used_pairs:
            continue
        used_pairs.add(pair_key)

        topic = generate_topic_from_material(
            controversy, pair[0], pair[1], material['title']
        )
        topics.append(topic)

        if len(topics) >= count:
            break

    # 如果不够，补充随机配对
    if len(topics) < count:
        import random
        remaining = [c for c in controversies if c not in [t['controversy'] for t in topics]]
        for c in remaining[:count - len(topics)]:
            pair = random.sample(experts, 2)
            topic = generate_topic_from_material(
                c, pair[0]['name'], pair[1]['name'], material['title']
            )
            topics.append(topic)

    return topics[:count]


# ─── CLI ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='训练话题构建器')
    parser.add_argument('material', help='素材包 .md 文件路径')
    parser.add_argument('--library', default='expert-library', help='专家库目录')
    parser.add_argument('--count', type=int, default=3, help='生成话题数量')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    if not os.path.exists(args.material):
        print(f"Error: 素材文件不存在: {args.material}")
        sys.exit(1)

    topics = build_topics_from_material(args.material, args.library, args.count)

    if not topics:
        print("未生成任何话题")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  从素材构建了 {len(topics)} 个训练话题")
    print(f"  素材: {args.material}")
    print(f"{'='*60}\n")

    for i, t in enumerate(topics, 1):
        print(f"话题 {i}: {t['topic']}")
        print(f"  专家: {', '.join(t['experts'])}")
        c = t.get('controversy', {})
        if c.get('source'):
            print(f"  来源: {c['source'][:60]}")
        print()

    # 保存到文件
    output_path = args.material.replace('_素材.md', '_topics.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"话题已保存: {output_path}")


if __name__ == '__main__':
    main()
