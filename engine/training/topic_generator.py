# -*- coding: utf-8 -*-
"""
互搏模式话题生成器：从专家核心信念差异中自动生成训练话题。

用法：
    python engine/training/topic_generator.py <expert_library_dir> [--count 3]

原理：
    专家之间的信念差异 = 天然的训练话题
    不需要外部输入，专家互搏即可自训练
"""

import os
import sys
import re
import random
from pathlib import Path
from typing import Dict, List, Tuple


def load_experts(library_dir: str) -> List[Dict]:
    """加载所有专家 .md 文件"""
    experts = []
    experts_dir = os.path.join(library_dir, 'experts')
    if not os.path.exists(experts_dir):
        return experts

    for category in os.listdir(experts_dir):
        cat_dir = os.path.join(experts_dir, category)
        if not os.path.isdir(cat_dir):
            continue
        for fname in os.listdir(cat_dir):
            if not fname.endswith('.md'):
                continue
            path = os.path.join(cat_dir, fname)
            expert = parse_expert_md(path)
            if expert:
                experts.append(expert)
    return experts


def parse_expert_md(path: str) -> Dict:
    """解析专家 .md 文件，提取核心信息"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取姓名
    name_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else ''

    # 提取核心信念
    beliefs = []
    beliefs_match = re.search(r'### 核心信念\n\n((?:- .+\n)+)', content)
    if beliefs_match:
        beliefs = [l.strip('- ').strip()
                   for l in beliefs_match.group(1).strip().split('\n')]

    # 提取价值排序
    values = []
    values_match = re.search(r'### 价值排序\n\n((?:\d+\. .+\n?)+)', content)
    if values_match:
        values = [re.sub(r'^\d+\.\s*', '', l.strip())
                  for l in values_match.group(1).strip().split('\n')]

    # 提取思维底色
    thinking_style = ''
    style_match = re.search(r'\*\*思维风格\*\*:\s*(.+)', content)
    if style_match:
        thinking_style = style_match.group(1).strip()

    # 提取分析框架
    framework = ''
    fw_match = re.search(r'### 分析框架\n\n>.*?\n\n```\n(.*?)```', content, re.DOTALL)
    if fw_match:
        framework = fw_match.group(1).strip()

    # 提取攻击模式
    attack_modes = []
    attack_match = re.search(r'### 攻击模式\n\n>.*?\n\n(?:\|.*?\n)*((?:\|.*?\n)+)', content)
    if attack_match:
        for line in attack_match.group(1).strip().split('\n'):
            if '|' in line and '优先级' not in line and '---' not in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) >= 3:
                    attack_modes.append({
                        'angle': cells[1],
                        'scenario': cells[2],
                        'rating': cells[3] if len(cells) > 3 else '中'
                    })

    return {
        'name': name,
        'path': path,
        'beliefs': beliefs,
        'values': values,
        'thinking_style': thinking_style,
        'framework': framework,
        'attack_modes': attack_modes
    }


def find_belief_conflicts(experts: List[Dict]) -> List[Dict]:
    """找到专家之间的信念冲突点"""
    conflicts = []

    for i in range(len(experts)):
        for j in range(i + 1, len(experts)):
            e1 = experts[i]
            e2 = experts[j]

            # 比较核心信念
            for b1 in e1['beliefs']:
                for b2 in e2['beliefs']:
                    # 检查是否存在对立关键词
                    conflict = detect_conflict(b1, b2)
                    if conflict:
                        conflicts.append({
                            'expert1': e1['name'],
                            'expert2': e2['name'],
                            'belief1': b1,
                            'belief2': b2,
                            'conflict_type': conflict,
                            'strength': 'strong' if conflict == 'direct' else 'moderate'
                        })

            # 比较价值排序
            if e1['values'] and e2['values']:
                v1 = e1['values'][0]  # 最看重的
                v2 = e2['values'][0]
                if v1 != v2:
                    conflicts.append({
                        'expert1': e1['name'],
                        'expert2': e2['name'],
                        'belief1': f'最看重：{v1}',
                        'belief2': f'最看重：{v2}',
                        'conflict_type': 'value_priority',
                        'strength': 'moderate'
                    })

    return conflicts


def detect_conflict(belief1: str, belief2: str) -> str:
    """检测两个信念之间是否存在冲突"""
    # 直接对立词对
    opposites = [
        ('善', '恶'), ('乐观', '悲观'), ('理想', '现实'),
        ('自由', '秩序'), ('个体', '集体'), ('理性', '感性'),
        ('变革', '保守'), ('平等', '等级'), ('人性', '制度'),
        ('短期', '长期'), ('风险', '安全'), ('创新', '传统'),
        ('物质', '精神'), ('竞争', '合作'), ('效率', '公平'),
        ('决定', '选择'), ('宿命', '自由意志'), ('本能', '教化'),
    ]

    for a, b in opposites:
        if (a in belief1 and b in belief2) or (b in belief1 and a in belief2):
            return 'direct'

    # 否定词检测
    negations = ['不', '非', '无', '未必', '并非']
    for neg in negations:
        if neg in belief1 and neg not in belief2:
            # belief1 否定，belief2 肯定
            base1 = belief1.replace(neg, '')
            if any(w in belief2 for w in base1 if len(w) > 1):
                return 'negation'
        if neg in belief2 and neg not in belief1:
            base2 = belief2.replace(neg, '')
            if any(w in belief1 for w in base2 if len(w) > 1):
                return 'negation'

    return ''


def generate_topic_from_conflict(conflict: Dict) -> str:
    """从信念冲突生成讨论话题"""
    templates = {
        'direct': [
            '{e1}认为"{b1}"，{e2}认为"{b2}"——谁更接近真相？这个判断如何影响我们的行动？',
            '"{b1}"vs"{b2}"：{e1}和{e2}的根本分歧。这个分歧在现实中有什么代价？',
            '如果{e1}是对的（{b1}），{e2}的世界观就要崩塌。反之亦然。谁的证据更硬？',
        ],
        'negation': [
            '{e1}说"{b1}"，{e2}反驳"{b2}"——这是一个可以验证的事实问题，还是一个价值选择？',
            '"{b1}"和"{b2}"能共存吗？{e1}和{e2}的矛盾是表面的还是根本的？',
        ],
        'value_priority': [
            '{e1}最看重"{b1}"，{e2}最看重"{b2}"——如果资源有限只能保一个，选哪个？',
            '在真实决策中，"{b1}"和"{b2}"冲突时，人们实际上怎么选？理想和现实差多远？',
        ]
    }

    template_list = templates.get(conflict['conflict_type'], templates['direct'])
    template = random.choice(template_list)

    topic = template.format(
        e1=conflict['expert1'],
        e2=conflict['expert2'],
        b1=conflict['belief1'],
        b2=conflict['belief2']
    )
    return topic


def generate_topics(library_dir: str, count: int = 3) -> List[Dict]:
    """
    主生成函数：从专家库中自动生成训练话题。

    Args:
        library_dir: 专家库目录路径
        count: 生成话题数量

    Returns:
        话题列表，每个话题包含：topic, experts, conflict
    """
    experts = load_experts(library_dir)
    if len(experts) < 2:
        print(f"Error: Need at least 2 experts, found {len(experts)}")
        return []

    conflicts = find_belief_conflicts(experts)
    if not conflicts:
        # 没有找到冲突，随机配对生成通用话题
        pairs = []
        for i in range(len(experts)):
            for j in range(i + 1, len(experts)):
                pairs.append((experts[i], experts[j]))

        random.shuffle(pairs)
        topics = []
        for e1, e2 in pairs[:count]:
            topic = f'{e1["name"]}和{e2["name"]}的核心世界观差异是什么？这个差异在实践中意味着什么？'
            topics.append({
                'topic': topic,
                'experts': [e1['name'], e2['name']],
                'conflict': None,
                'type': 'random_pair'
            })
        return topics

    # 按冲突强度排序
    strong = [c for c in conflicts if c['strength'] == 'strong']
    moderate = [c for c in conflicts if c['strength'] == 'moderate']

    selected = strong[:count]
    if len(selected) < count:
        random.shuffle(moderate)
        selected.extend(moderate[:count - len(selected)])

    topics = []
    for conflict in selected[:count]:
        topic_text = generate_topic_from_conflict(conflict)
        topics.append({
            'topic': topic_text,
            'experts': [conflict['expert1'], conflict['expert2']],
            'conflict': conflict,
            'type': conflict['conflict_type']
        })

    return topics


def main():
    if len(sys.argv) < 2:
        print("Usage: python topic_generator.py <expert_library_dir> [--count 3]")
        sys.exit(1)

    library_dir = sys.argv[1]
    count = 3
    if '--count' in sys.argv:
        idx = sys.argv.index('--count')
        if idx + 1 < len(sys.argv):
            count = int(sys.argv[idx + 1])

    topics = generate_topics(library_dir, count)

    if not topics:
        print("No topics generated. Check expert library.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Generated {len(topics)} training topics")
    print(f"{'='*60}\n")

    for i, t in enumerate(topics, 1):
        print(f"Topic {i}: {t['topic']}")
        print(f"  Experts: {', '.join(t['experts'])}")
        print(f"  Type: {t['type']}")
        if t['conflict']:
            print(f"  Conflict: {t['conflict']['belief1']} vs {t['conflict']['belief2']}")
        print()


if __name__ == '__main__':
    main()
