# -*- coding: utf-8 -*-
"""
训练编排器：串联提取→升级→评分的完整训练循环。

用法：
    # 人给话题模式
    python engine/training/trainer.py --mode human --json <讨论JSON> --library <专家库>

    # 互搏模式（自动生成话题）
    python engine/training/trainer.py --mode auto --library <专家库> [--rounds 3]

    # 回放训练模式（修补弱点）
    python engine/training/trainer.py --mode replay --library <专家库> --expert <专家名>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from training.extractor import extract
from training.upgrader import upgrade_expert, parse_version
from training.scorer import score_discussion
from training.topic_generator import generate_topics, load_experts


class TrainingSession:
    """一次训练会话"""

    def __init__(self, library_dir: str, log_dir: str = 'memory'):
        self.library_dir = library_dir
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.session_log = {
            'start_time': datetime.now().isoformat(),
            'rounds': [],
            'expert_upgrades': {},
        }

    def find_expert_md(self, expert_name: str) -> str:
        """在专家库中查找专家 .md 文件"""
        experts_dir = os.path.join(self.library_dir, 'experts')
        for category in os.listdir(experts_dir):
            cat_dir = os.path.join(experts_dir, category)
            if not os.path.isdir(cat_dir):
                continue
            for fname in os.listdir(cat_dir):
                if not fname.endswith('.md') or fname == 'expert_template.md':
                    continue
                path = os.path.join(cat_dir, fname)
                with open(path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                if expert_name in first_line:
                    return path
        return ''

    def run_human_mode(self, json_path: str, book_title: str = None) -> Dict:
        """
        人给话题模式：
        1. 从讨论 JSON 提取策略
        2. 评分
        3. 升级专家
        """
        print(f"\n{'='*60}")
        print(f"训练模式：人给话题")
        print(f"讨论文件：{json_path}")
        print(f"{'='*60}\n")

        # Step 1: 评分
        print("[1/3] 评分中...")
        score_result = score_discussion(json_path)
        print(f"  总分: {score_result['total']:.1f} ({score_result['grade']})")

        # Step 2: 提取策略
        print("[2/3] 提取策略数据...")
        extraction_path = json_path.replace('.json', '_extraction.json')
        extraction = extract(json_path, extraction_path)

        if not book_title:
            book_title = extraction.get('book_title', '未知')

        # 提取分数维度
        score_breakdown = score_result.get('dimensions', {})
        attack_eff = score_breakdown.get('attack_efficiency', {}).get('score', 0.0)
        defense_rate = score_breakdown.get('defense_rate', {}).get('score', 0.0)

        # Step 3: 升级每位专家
        print("[3/3] 升级专家...")
        round_num = len(self.session_log['rounds']) + 1
        round_log = {
            'round': round_num,
            'mode': 'human',
            'topic': book_title,
            'json_path': json_path,
            'score': score_result['total'],
            'grade': score_result['grade'],
            'expert_upgrades': {},
        }

        for expert_name, expert_data in extraction.get('experts', {}).items():
            expert_md = self.find_expert_md(expert_name)
            if not expert_md:
                print(f"  SKIP: {expert_name} (未找到专家档案)")
                continue

            # 启发式提取策略数据
            strategy = self._build_strategy_template(expert_data, score_breakdown)

            # 升级专家（传真实分数）
            new_content = upgrade_expert(
                expert_md, strategy,
                topic=book_title,
                score=score_result['total'],
                attack_eff=attack_eff,
                defense_rate=defense_rate,
            )
            new_version = parse_version(new_content)

            print(f"  UP: {expert_name} → V{new_version}")
            round_log['expert_upgrades'][expert_name] = {
                'file': expert_md,
                'new_version': new_version,
                'speech_count': expert_data.get('speech_count', 0),
            }

        self.session_log['rounds'].append(round_log)
        round_log['score_result'] = score_result
        return round_log

    def run_auto_mode(self, topic_count: int = 3) -> List[Dict]:
        """
        互搏模式：
        1. 从专家信念差异生成话题
        2. 对每个话题生成讨论（需要外部调用 render_v8）
        3. 评分 + 升级
        """
        print(f"\n{'='*60}")
        print(f"训练模式：专家互搏（自动生成话题）")
        print(f"{'='*60}\n")

        # Step 1: 生成话题
        print("[1/2] 从专家信念差异生成话题...")
        topics = generate_topics(self.library_dir, topic_count)

        if not topics:
            print("Error: 无法生成话题。检查专家库是否至少有2位专家。")
            return []

        results = []
        for i, topic in enumerate(topics, 1):
            print(f"\n  Topic {i}: {topic['topic']}")
            print(f"  Experts: {', '.join(topic['experts'])}")
            print(f"  Conflict: {topic.get('conflict', {}).get('belief1', 'N/A')} vs {topic.get('conflict', {}).get('belief2', 'N/A')}")

            results.append({
                'topic': topic['topic'],
                'experts': topic['experts'],
                'conflict': topic.get('conflict'),
                'status': 'pending_discussion',
                'note': '需要调用主 SKILL.md 生成讨论 JSON，然后用 --mode human 训练',
            })

        # 保存话题到文件
        topics_path = os.path.join(self.log_dir, f'auto_topics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(topics_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[2/2] 话题已保存: {topics_path}")
        print("下一步：用主 SKILL.md 为每个话题生成讨论，然后用 --mode human 训练")

        return results

    def run_replay_mode(self, expert_name: str) -> Dict:
        """
        回放训练模式：
        1. 分析专家历史训练日志
        2. 找到反复暴露的弱点
        3. 构造针对性话题
        """
        print(f"\n{'='*60}")
        print(f"训练模式：回放训练（修补弱点）")
        print(f"目标专家：{expert_name}")
        print(f"{'='*60}\n")

        expert_md = self.find_expert_md(expert_name)
        if not expert_md:
            print(f"Error: 未找到专家 {expert_name} 的档案")
            return {}

        # 读取专家档案
        with open(expert_md, 'r', encoding='utf-8') as f:
            content = f.read()

        # 分析防御模式中的弱点
        weaknesses = []
        import re
        defense_pattern = r'\| (.+?) \| (.+?) \| (\d+)% \|'
        for m in re.finditer(defense_pattern, content):
            attack_type = m.group(1)
            strategy = m.group(2)
            rate = int(m.group(3))
            if rate < 50:
                weaknesses.append({
                    'attack_type': attack_type,
                    'current_strategy': strategy,
                    'success_rate': rate,
                })

        if not weaknesses:
            print(f"  {expert_name} 没有明显弱点（所有防御成功率 >= 50%）")
            return {'status': 'no_weaknesses'}

        print(f"  发现 {len(weaknesses)} 个弱点:")
        for w in weaknesses:
            print(f"    - {w['attack_type']}: 成功率 {w['success_rate']}%")

        # 构造针对性话题
        topics = []
        for w in weaknesses:
            topic = f"针对「{w['attack_type']}」的专项训练：如何在面对{w['attack_type']}时保持立场？"
            topics.append({
                'topic': topic,
                'target_expert': expert_name,
                'weakness': w,
                'status': 'pending',
            })

        # 保存
        replay_path = os.path.join(self.log_dir, f'replay_{expert_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(replay_path, 'w', encoding='utf-8') as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
        print(f"\n  回放话题已保存: {replay_path}")
        print(f"  下一步：为这些话题生成讨论，然后用 --mode human 训练 {expert_name}")

        return {'weaknesses': weaknesses, 'topics': topics}

    def save_session_log(self):
        """保存训练会话日志"""
        self.session_log['end_time'] = datetime.now().isoformat()
        log_path = os.path.join(
            self.log_dir,
            f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.session_log, f, ensure_ascii=False, indent=2)
        print(f"\nSession log saved: {log_path}")

    def _build_strategy_template(self, expert_data: Dict, score_breakdown: Dict = None) -> Dict:
        """从发言内容启发式提取策略数据（无需 AI）。"""
        import re
        speeches = expert_data.get('speeches', [])
        attacks = [s for s in speeches if s.get('type') == 'attack']
        defenses = [s for s in speeches if s.get('type') == 'defense']
        stances = [s for s in speeches if s.get('type') == 'stance']

        # 攻击策略：取最长攻击
        best_attack = max(attacks, key=lambda a: len(a.get('content', '')), default={})
        # 防御弱点：取最短防御（最弱的）
        worst_defense = min(defenses, key=lambda d: len(d.get('content', '')), default={})
        # 风格指纹：取修辞手法最多的立场发言
        best_stance = max(stances, key=lambda s: self._style_score(s.get('content', '')), default={})
        # 最弱发言：取最短立场
        weakest_stance = min(stances, key=lambda s: len(s.get('content', '')), default={})

        return {
            'attack_strategy': {
                'best_angle': best_attack.get('attack_type', '逻辑漏洞'),
                'why_effective': f"针对{best_attack.get('target', '对手')}的{best_attack.get('attack_type', '')}攻击",
                'applicable_when': f"对手持{best_attack.get('target', '')}立场时",
                'kill_rating': '高' if len(best_attack.get('content', '')) > 200 else '中',
            },
            'defense_weakness': {
                'broken_by': worst_defense.get('attacker', '逻辑漏洞攻击'),
                'why_vulnerable': '回应简短，缺乏证据支撑',
                'fix_strategy': '增加具体证据和逻辑链',
            },
            'evidence_preference': {
                'most_effective_type': '逻辑推演',
                'ranking': ['逻辑推演', '案例归纳', '数据实证'],
                'best_example': best_stance.get('content', '')[:100] if best_stance else '',
            },
            'interaction_pattern': {
                'best_opponent': best_attack.get('target', ''),
                'why_effective': f"在{best_attack.get('topic', '讨论')}中成功攻击",
                'worst_opponent': worst_defense.get('attacker', ''),
                'why_weak': f"在{worst_defense.get('topic', '讨论')}中防御不足",
            },
            'style_fingerprint': {
                'most_authentic_line': best_stance.get('content', '')[:200],
                'why_authentic': '风格鲜明，有修辞手法',
                'weakest_line': weakest_stance.get('content', '')[:100] if weakest_stance else '',
                'why_weak': '表达平淡，缺乏特色',
            },
        }

    @staticmethod
    def _style_score(content: str) -> int:
        """评估发言的修辞手法得分。"""
        if not content:
            return 0
        score = len(content)
        # 修辞手法加分
        devices = ['就像', '好比', '本质上', '说白了', '坦白说', '不是.*而是',
                    '如果.*那么', '一方面.*另一方面', '与其.*不如']
        for d in devices:
            if re.search(d, content):
                score += 30
        # 反问句加分
        score += content.count('？') * 10
        return score


def main():
    parser = argparse.ArgumentParser(description='圆桌会议训练引擎')
    parser.add_argument('--mode', choices=['human', 'auto', 'replay'],
                        default='human', help='训练模式')
    parser.add_argument('--json', help='讨论 JSON 路径（human 模式）')
    parser.add_argument('--library', default='expert-library',
                        help='专家库目录路径')
    parser.add_argument('--rounds', type=int, default=3,
                        help='互搏轮次（auto 模式）')
    parser.add_argument('--expert', help='目标专家名（replay 模式）')
    parser.add_argument('--topic', help='话题名（human 模式可选）')

    args = parser.parse_args()

    session = TrainingSession(args.library)

    if args.mode == 'human':
        if not args.json:
            print("Error: --json required for human mode")
            sys.exit(1)
        session.run_human_mode(args.json, args.topic)

    elif args.mode == 'auto':
        session.run_auto_mode(args.rounds)

    elif args.mode == 'replay':
        if not args.expert:
            print("Error: --expert required for replay mode")
            sys.exit(1)
        session.run_replay_mode(args.expert)

    session.save_session_log()


if __name__ == '__main__':
    main()
