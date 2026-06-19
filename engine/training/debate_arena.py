# -*- coding: utf-8 -*-
"""
对抗自训练竞技场 V3.0

核心原理：专家之间的信念差异 = 天然的训练话题。不需要外部输入。

训练循环：
1. 从每位专家的"核心信念"中提取矛盾点
   → 孔子相信"人性本善" vs 尼采相信"权力意志"
2. 两位专家就这个话题进行深度碰撞
3. 提取表现数据，进化升级专家
4. 从升级后的专家中提取新的矛盾点
5. 重复

三种对抗模式：
- 信念碰撞：直接对立的信念对撞
- 价值排序冲突：最看重的东西不同
- 方法论分歧：分析路径不同

用法：
    python engine/training/debate_arena.py --library expert-library --rounds 5
"""

import os
import re
import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ─── 对立词对库 ──────────────────────────────────────

OPPOSITE_PAIRS = [
    ('善', '恶'), ('乐观', '悲观'), ('理想', '现实'),
    ('自由', '秩序'), ('个体', '集体'), ('理性', '感性'),
    ('变革', '保守'), ('平等', '等级'), ('人性', '制度'),
    ('短期', '长期'), ('风险', '安全'), ('创新', '传统'),
    ('物质', '精神'), ('竞争', '合作'), ('效率', '公平'),
    ('决定', '选择'), ('宿命', '自由意志'), ('本能', '教化'),
    ('自然', '人为'), ('无为', '有为'), ('克制', '放纵'),
    ('市场', '计划'), ('民主', '专制'), ('科学', '信仰'),
    ('解构', '建构'), ('怀疑', '信任'), ('极简', '繁复'),
]


@dataclass
class BeliefProfile:
    """专家信念档案"""
    name: str
    path: str
    beliefs: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    thinking_style: str = ''
    argument_style: str = ''
    attack_modes: List[Dict] = field(default_factory=list)
    defense_modes: List[Dict] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class DebateTopic:
    """一个对抗话题"""
    topic: str
    expert1: str
    expert2: str
    belief1: str
    belief2: str
    conflict_type: str
    strength: str
    round_num: int = 0


@dataclass
class ArenaRoundResult:
    """一轮竞技场结果"""
    round_num: int
    topic: DebateTopic
    winner: str = ''
    key_insight: str = ''
    expert1_performance: Dict = field(default_factory=dict)
    expert2_performance: Dict = field(default_factory=dict)


class BeliefExtractor:
    """信念提取器：从专家 .md 中提取信念档案"""

    @staticmethod
    def extract(path: str) -> Optional[BeliefProfile]:
        """从 .md 文件提取信念档案"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        # 姓名
        name_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else ''

        # 核心信念
        beliefs = []
        beliefs_match = re.search(r'### 核心信念\n\n((?:- .+\n?)+)', content)
        if beliefs_match:
            beliefs = [
                l.strip('- ').strip()
                for l in beliefs_match.group(1).strip().split('\n')
                if l.strip() and '待填充' not in l
            ]

        # 价值排序
        values = []
        values_match = re.search(r'### 价值排序\n\n((?:\d+\. .+\n?)+)', content)
        if values_match:
            values = [
                re.sub(r'^\d+\.\s*', '', l.strip())
                for l in values_match.group(1).strip().split('\n')
            ]

        # 思维风格
        style_match = re.search(r'\*\*思维风格\*\*:\s*(.+)', content)
        thinking_style = style_match.group(1).strip() if style_match else ''

        # 论证偏好
        arg_match = re.search(r'\*\*论证偏好\*\*:\s*(.+)', content)
        argument_style = arg_match.group(1).strip() if arg_match else ''

        # 攻击模式
        attack_modes = []
        attack_section = re.search(
            r'### 攻击模式\n\n>.*?\n\n(?:\|.*?\n)*((?:\|.*?\n)+)', content, re.DOTALL
        )
        if attack_section:
            for line in attack_section.group(1).strip().split('\n'):
                if '|' in line and '优先级' not in line and '---' not in line:
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if len(cells) >= 3:
                        attack_modes.append({
                            'angle': cells[1],
                            'scenario': cells[2],
                            'rating': cells[3] if len(cells) > 3 else '中',
                        })

        # 防御模式
        defense_modes = []
        defense_section = re.search(
            r'### 防御模式\n\n>.*?\n\n(?:\|.*?\n)*((?:\|.*?\n)+)', content, re.DOTALL
        )
        if defense_section:
            for line in defense_section.group(1).strip().split('\n'):
                if '|' in line and '被攻击' not in line and '---' not in line:
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if len(cells) >= 3:
                        rate_m = re.search(r'(\d+)', cells[2])
                        rate = int(rate_m.group(1)) if rate_m else 0
                        defense_modes.append({
                            'type': cells[0],
                            'strategy': cells[1],
                            'rate': rate,
                        })

        # 弱点提取：防御成功率 < 50% 的
        weaknesses = [
            d['type'] for d in defense_modes if d['rate'] < 50
        ]

        return BeliefProfile(
            name=name,
            path=path,
            beliefs=beliefs,
            values=values,
            thinking_style=thinking_style,
            argument_style=argument_style,
            attack_modes=attack_modes,
            defense_modes=defense_modes,
            weaknesses=weaknesses,
        )


class ConflictDetector:
    """冲突检测器：找到专家之间的信念矛盾"""

    @staticmethod
    def detect_direct_conflicts(profiles: List[BeliefProfile]) -> List[Dict]:
        """检测直接对立的信念"""
        conflicts = []
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                p1, p2 = profiles[i], profiles[j]
                for b1 in p1.beliefs:
                    for b2 in p2.beliefs:
                        for a, b in OPPOSITE_PAIRS:
                            if (a in b1 and b in b2) or (b in b1 and a in b2):
                                conflicts.append({
                                    'expert1': p1.name,
                                    'expert2': p2.name,
                                    'belief1': b1,
                                    'belief2': b2,
                                    'conflict_type': 'direct',
                                    'strength': 'strong',
                                    'opposite_pair': (a, b),
                                })
                                break
        return conflicts

    @staticmethod
    def detect_value_conflicts(profiles: List[BeliefProfile]) -> List[Dict]:
        """检测价值排序冲突"""
        conflicts = []
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                p1, p2 = profiles[i], profiles[j]
                if p1.values and p2.values and p1.values[0] != p2.values[0]:
                    conflicts.append({
                        'expert1': p1.name,
                        'expert2': p2.name,
                        'belief1': f'最看重：{p1.values[0]}',
                        'belief2': f'最看重：{p2.values[0]}',
                        'conflict_type': 'value_priority',
                        'strength': 'moderate',
                    })
        return conflicts

    @staticmethod
    def detect_method_conflicts(profiles: List[BeliefProfile]) -> List[Dict]:
        """检测方法论冲突（论证偏好不同）"""
        conflicts = []
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                p1, p2 = profiles[i], profiles[j]
                if (p1.argument_style and p2.argument_style
                        and p1.argument_style != p2.argument_style):
                    conflicts.append({
                        'expert1': p1.name,
                        'expert2': p2.name,
                        'belief1': f'论证方式：{p1.argument_style}',
                        'belief2': f'论证方式：{p2.argument_style}',
                        'conflict_type': 'method',
                        'strength': 'moderate',
                    })
        return conflicts

    @staticmethod
    def detect_weakness_exploits(profiles: List[BeliefProfile]) -> List[Dict]:
        """检测弱点利用机会：A 的攻击角度恰好是 B 的弱点"""
        exploits = []
        for p1 in profiles:
            for p2 in profiles:
                if p1.name == p2.name:
                    continue
                for attack in p1.attack_modes:
                    for weakness in p2.weaknesses:
                        if attack['angle'] in weakness or weakness in attack['angle']:
                            exploits.append({
                                'expert1': p1.name,
                                'expert2': p2.name,
                                'belief1': f"擅长攻击：{attack['angle']}",
                                'belief2': f"弱点：{weakness}",
                                'conflict_type': 'weakness_exploit',
                                'strength': 'strong',
                            })
        return exploits


class TopicComposer:
    """话题作曲家：从冲突生成讨论话题"""

    TEMPLATES = {
        'direct': [
            '{e1}坚信"{b1}"，{e2}坚持"{b2}"——谁更接近真相？这个判断如何影响我们的行动？',
            '"{b1}"vs"{b2}"：{e1}和{e2}的根本分歧。现实中，选错边的代价是什么？',
            '如果{e1}是对的（{b1}），{e2}的世界观就要崩塌。反之亦然。谁的证据更硬？',
            '面对"{b1}"和"{b2}"的对立，一个没有预设立场的观察者会怎么看？',
        ],
        'value_priority': [
            '{e1}最看重"{b1}"，{e2}最看重"{b2}"——如果资源有限只能保一个，选哪个？',
            '在真实决策中，"{b1}"和"{b2}"冲突时，人们实际上怎么选？理想和现实差多远？',
        ],
        'method': [
            '{e1}用{b1}，{e2}用{b2}——同一个问题，两种方法得出的结论会差多远？',
            '如果强制{e2}用{b1}来论证自己的观点，会发生什么？方法论的边界在哪里？',
        ],
        'weakness_exploit': [
            '{e1}的{b1}正好对上{e2}的{b2}——这是一场不对等的战斗。{e2}如何自救？',
            '训练场景：{e1}专门攻击{e2}的{b2}。{e2}需要在5分钟内构建防御。怎么防？',
        ],
    }

    @classmethod
    def compose(cls, conflict: Dict) -> str:
        """从冲突生成话题文本"""
        c_type = conflict.get('conflict_type', 'direct')
        templates = cls.TEMPLATES.get(c_type, cls.TEMPLATES['direct'])
        template = random.choice(templates)
        return template.format(
            e1=conflict['expert1'],
            e2=conflict['expert2'],
            b1=conflict.get('belief1', ''),
            b2=conflict.get('belief2', ''),
        )


class DebateArena:
    """对抗自训练竞技场"""

    def __init__(self, library_dir: str):
        self.library_dir = library_dir
        self.profiles: List[BeliefProfile] = []
        self._load_profiles()

    def _load_profiles(self):
        """加载所有专家信念档案"""
        experts_dir = os.path.join(self.library_dir, 'experts')
        if not os.path.exists(experts_dir):
            return

        for category in os.listdir(experts_dir):
            cat_dir = os.path.join(experts_dir, category)
            if not os.path.isdir(cat_dir):
                continue
            for fname in os.listdir(cat_dir):
                if not fname.endswith('.md'):
                    continue
                path = os.path.join(cat_dir, fname)
                profile = BeliefExtractor.extract(path)
                if profile and profile.name:
                    self.profiles.append(profile)

    def get_all_conflicts(self) -> List[Dict]:
        """获取所有类型的冲突"""
        detector = ConflictDetector()
        conflicts = []
        conflicts.extend(detector.detect_direct_conflicts(self.profiles))
        conflicts.extend(detector.detect_value_conflicts(self.profiles))
        conflicts.extend(detector.detect_method_conflicts(self.profiles))
        conflicts.extend(detector.detect_weakness_exploits(self.profiles))
        return conflicts

    def generate_topics(self, count: int = 5,
                        prefer_strong: bool = True) -> List[DebateTopic]:
        """生成对抗训练话题"""
        conflicts = self.get_all_conflicts()
        if not conflicts:
            return self._generate_random_topics(count)

        # 按强度排序
        if prefer_strong:
            strong = [c for c in conflicts if c['strength'] == 'strong']
            moderate = [c for c in conflicts if c['strength'] == 'moderate']
            random.shuffle(strong)
            random.shuffle(moderate)
            ordered = strong + moderate
        else:
            random.shuffle(conflicts)
            ordered = conflicts

        topics = []
        seen_pairs = set()
        for conflict in ordered:
            if len(topics) >= count:
                break
            pair_key = tuple(sorted([conflict['expert1'], conflict['expert2']]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            topic_text = TopicComposer.compose(conflict)
            topics.append(DebateTopic(
                topic=topic_text,
                expert1=conflict['expert1'],
                expert2=conflict['expert2'],
                belief1=conflict.get('belief1', ''),
                belief2=conflict.get('belief2', ''),
                conflict_type=conflict['conflict_type'],
                strength=conflict['strength'],
            ))

        # 补齐
        while len(topics) < count:
            random_topics = self._generate_random_topics(1)
            if random_topics:
                topics.extend(random_topics)
            else:
                break

        return topics[:count]

    def _generate_random_topics(self, count: int) -> List[DebateTopic]:
        """随机配对生成话题（当没有冲突时的后备方案）"""
        if len(self.profiles) < 2:
            return []

        pairs = []
        for i in range(len(self.profiles)):
            for j in range(i + 1, len(self.profiles)):
                pairs.append((self.profiles[i], self.profiles[j]))

        random.shuffle(pairs)
        topics = []
        for p1, p2 in pairs[:count]:
            topic = (
                f'{p1.name}和{p2.name}的核心世界观差异是什么？'
                f'这个差异在现实决策中意味着什么？'
            )
            topics.append(DebateTopic(
                topic=topic,
                expert1=p1.name,
                expert2=p2.name,
                belief1=p1.beliefs[0] if p1.beliefs else '',
                belief2=p2.beliefs[0] if p2.beliefs else '',
                conflict_type='random_pair',
                strength='moderate',
            ))
        return topics

    def get_expert_profile(self, name: str) -> Optional[BeliefProfile]:
        """获取指定专家的信念档案"""
        for p in self.profiles:
            if p.name == name:
                return p
        return None

    def get_training_recommendations(self) -> Dict[str, List[str]]:
        """
        为每位专家生成训练建议：
        - 谁应该和谁对抗（信念碰撞）
        - 谁需要修补弱点
        - 谁的方法论需要扩展
        """
        recommendations = {}
        for profile in self.profiles:
            recs = []

            # 弱点训练建议
            if profile.weaknesses:
                for w in profile.weaknesses[:2]:
                    recs.append(f"弱点修补：{w}")

            # 信念碰撞建议
            for other in self.profiles:
                if other.name == profile.name:
                    continue
                for b1 in profile.beliefs:
                    for b2 in other.beliefs:
                        for a, b in OPPOSITE_PAIRS:
                            if (a in b1 and b in b2) or (b in b1 and a in b2):
                                recs.append(f"信念碰撞 vs {other.name}：{a}↔{b}")
                                break

            if recs:
                recommendations[profile.name] = recs[:5]

        return recommendations

    def generate_training_plan(self, rounds: int = 5) -> List[DebateTopic]:
        """
        生成完整的训练计划：
        - 奇数轮：强冲突碰撞
        - 偶数轮：弱点修补
        """
        topics = self.generate_topics(count=rounds, prefer_strong=True)

        # 标记轮次
        for i, topic in enumerate(topics, 1):
            topic.round_num = i

        return topics


def main():
    import argparse
    parser = argparse.ArgumentParser(description='对抗自训练竞技场')
    parser.add_argument('--library', default='expert-library', help='专家库目录')
    parser.add_argument('--rounds', type=int, default=5, help='训练轮次')
    parser.add_argument('--show-conflicts', action='store_true', help='显示所有冲突')
    parser.add_argument('--show-recommendations', action='store_true', help='显示训练建议')
    args = parser.parse_args()

    arena = DebateArena(args.library)

    print(f"\n{'='*60}")
    print(f"  对抗自训练竞技场")
    print(f"  专家数: {len(arena.profiles)}")
    print(f"{'='*60}\n")

    if args.show_conflicts:
        conflicts = arena.get_all_conflicts()
        print(f"发现 {len(conflicts)} 个冲突点：\n")
        for i, c in enumerate(conflicts, 1):
            print(f"  {i}. [{c['conflict_type']}] {c['expert1']} vs {c['expert2']}")
            print(f"     {c['belief1'][:40]} ↔ {c['belief2'][:40]}")
            print(f"     强度: {c['strength']}")
        print()

    if args.show_recommendations:
        recs = arena.get_training_recommendations()
        print("训练建议：\n")
        for name, items in recs.items():
            print(f"  {name}:")
            for item in items:
                print(f"    - {item}")
        print()

    # 生成训练计划
    topics = arena.generate_training_plan(args.rounds)
    print(f"生成 {len(topics)} 个训练话题：\n")
    for t in topics:
        print(f"  Round {t.round_num}: {t.expert1} vs {t.expert2} [{t.conflict_type}]")
        print(f"  话题: {t.topic[:60]}...")
        print(f"  信念: {t.belief1[:30]} ↔ {t.belief2[:30]}")
        print()


if __name__ == '__main__':
    main()
