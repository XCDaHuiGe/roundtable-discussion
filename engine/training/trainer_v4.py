# -*- coding: utf-8 -*-
"""
训练编排器 V4.0 — AI-Native Training Pipeline

核心升级：
1. AI驱动的策略提取（llm_extractor）替代启发式提取
2. 融合增强式升级（fusion_engine）替代替换式升级
3. 训练效果追踪（tracker）实时监控评分提升
4. 智能诊断（为什么评分不提升）

用法：
    # 人给话题模式
    python engine/training/trainer_v4.py --mode human --json <讨论JSON> --library <专家库>

    # 查看训练效果报告
    python engine/training/trainer_v4.py --report

    # 绘制趋势图
    python engine/training/trainer_v4.py --plot
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from training.llm_extractor import LLMStrategyExtractor
from training.fusion_engine import FusionEngine
from training.scorer import score_discussion
from training.tracker import TrainingTracker


class TrainingSessionV4:
    """V4.0 训练会话 — AI-Native Pipeline"""

    def __init__(self, library_dir: str, log_dir: str = 'memory'):
        self.library_dir = library_dir
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # 初始化新模块
        self.extractor = LLMStrategyExtractor()
        self.fusion_engine = FusionEngine(library_dir)
        self.tracker = TrainingTracker(library_dir, log_dir)

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
        人给话题模式（V4.0 完整流程）：
        1. 评分（scorer）
        2. AI策略提取（llm_extractor）
        3. 融合增强升级（fusion_engine）
        4. 记录训练效果（tracker）
        """
        print(f"\n{'='*70}")
        print(f"训练模式：人给话题 (V4.0 AI-Native Pipeline)")
        print(f"讨论文件：{json_path}")
        print(f"{'='*70}\n")

        # Step 1: 评分
        print("[1/4] 评分中...")
        score_result = score_discussion(json_path)
        print(f"  总分: {score_result['total']:.1f} ({score_result['grade']})")
        for dim_name, dim in score_result['dimensions'].items():
            print(f"  - {dim_name}: {dim['score']:.1f}% (权重 {dim['weight']*100:.0f}%)")

        # Step 2: AI策略提取（核心升级）
        print("\n[2/4] AI策略提取中...")
        print("  调用LLM进行5维度质量评分...")
        extraction = self.extractor.extract(json_path)

        if not book_title:
            book_title = extraction.get('book_title', '未知')

        # 提取分数维度
        score_breakdown = score_result.get('dimensions', {})
        attack_eff = score_breakdown.get('attack_efficiency', {}).get('score', 0.0)
        defense_rate = score_breakdown.get('defense_rate', {}).get('score', 0.0)

        # 显示AI质量分析摘要
        print("\n  AI质量分析摘要:")
        for name, data in extraction.get('experts', {}).items():
            cg = data.get('cognitive_growth', {})
            print(f"    {name}: 平均质量 {cg.get('avg_score', 0):.1f}/10 | "
                  f"最强维度: {cg.get('strongest_dimension', 'N/A')} | "
                  f"趋势: {cg.get('trend', 'N/A')}")

        # Step 3: 融合增强升级（核心升级）
        print("\n[3/4] 融合增强升级中...")
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

        # 收集训练数据用于追踪
        tracking_data = {
            'timestamp': datetime.now().isoformat(),
            'book_title': book_title,
            'experts': {},
        }

        for expert_name, expert_data in extraction.get('experts', {}).items():
            expert_md = self.find_expert_md(expert_name)
            if not expert_md:
                print(f"  SKIP: {expert_name} (未找到专家档案)")
                continue

            # 获取旧版本
            with open(expert_md, 'r', encoding='utf-8') as f:
                old_content = f.read()
            old_version = self._parse_version(old_content)

            # 融合增强升级（替代替换式升级）
            print(f"  融合 {expert_name}...")
            result = self.fusion_engine.fuse(
                expert_name,
                expert_data,
                topic=book_title,
                score=score_result['total'],
                attack_eff=attack_eff,
                defense_rate=defense_rate,
                quality_data=extraction.get('quality_matrix', {}).get(expert_name, {}),
            )

            if result:
                print(f"  ✓ {expert_name}: V{result.old_version} → V{result.new_version}")
                if result.fusion_operations:
                    for op in result.fusion_operations:
                        print(f"    - {op}")
                if result.capability_delta:
                    print(f"    能力增量: {result.capability_delta}")

                round_log['expert_upgrades'][expert_name] = {
                    'file': expert_md,
                    'old_version': result.old_version,
                    'new_version': result.new_version,
                    'operations': result.fusion_operations,
                    'capability_delta': result.capability_delta,
                }

                # 准备追踪数据
                tracking_data['experts'][expert_name] = {
                    'old_version': result.old_version,
                    'new_version': result.new_version,
                    'score': score_result['total'],
                    'attack_eff': attack_eff,
                    'defense_rate': defense_rate,
                    'operations': result.fusion_operations,
                    'capability_delta': result.capability_delta,
                    'quality_matrix': extraction.get('quality_matrix', {}).get(expert_name, {}),
                }
            else:
                print(f"  ✗ {expert_name}: 融合失败")

        # Step 4: 记录训练效果
        print("\n[4/4] 记录训练效果...")
        self.tracker.record_training(tracking_data)

        # 显示训练效果摘要
        analysis = self.tracker.analyze_training_effectiveness()
        if analysis.get('status') != 'no_data':
            print(f"  整体趋势: {analysis.get('overall_trend', 'N/A')}")
            print(f"  平均提升: {analysis.get('avg_improvement_per_training', 0):.2f} 分/次")

        self.session_log['rounds'].append(round_log)
        round_log['score_result'] = score_result
        return round_log

    def run_auto_mode(self, topic_count: int = 3) -> List[Dict]:
        """
        互搏模式（V4.0）：
        1. 从专家信念差异生成话题
        2. 对每个话题生成讨论
        3. 评分 + AI提取 + 融合升级 + 追踪
        """
        print(f"\n{'='*70}")
        print(f"训练模式：专家互搏 (V4.0)")
        print(f"{'='*70}\n")

        # 复用原有的topic_generator
        from training.topic_generator import generate_topics, load_experts

        print("[1/2] 从专家信念差异生成话题...")
        topics = generate_topics(self.library_dir, topic_count)

        if not topics:
            print("Error: 无法生成话题。检查专家库是否至少有2位专家。")
            return []

        results = []
        for i, topic in enumerate(topics, 1):
            print(f"\n  Topic {i}: {topic['topic']}")
            print(f"  Experts: {', '.join(topic['experts'])}")

            results.append({
                'topic': topic['topic'],
                'experts': topic['experts'],
                'conflict': topic.get('conflict'),
                'status': 'pending_discussion',
                'note': '需要调用主 SKILL.md 生成讨论 JSON，然后用 --mode human 训练',
            })

        topics_path = os.path.join(
            self.log_dir,
            f'auto_topics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(topics_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[2/2] 话题已保存: {topics_path}")

        return results

    def generate_report(self) -> str:
        """生成训练效果报告"""
        return self.tracker.generate_report()

    def plot_trends(self) -> List[str]:
        """绘制训练趋势图"""
        return self.tracker.plot_trends()

    def save_session_log(self):
        """保存训练会话日志"""
        self.session_log['end_time'] = datetime.now().isoformat()
        log_path = os.path.join(
            self.log_dir,
            f'training_v4_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.session_log, f, ensure_ascii=False, indent=2)
        print(f"\nSession log saved: {log_path}")

    @staticmethod
    def _parse_version(content: str) -> int:
        """提取当前版本号"""
        m = re.search(r'\*\*版本\*\*:\s*V(\d+)', content)
        return int(m.group(1)) if m else 1


def main():
    parser = argparse.ArgumentParser(description='圆桌会议训练引擎 V4.0')
    parser.add_argument('--mode', choices=['human', 'auto', 'report', 'plot'],
                        default='human', help='训练模式')
    parser.add_argument('--json', help='讨论 JSON 路径（human 模式）')
    parser.add_argument('--library', default='expert-library',
                        help='专家库目录路径')
    parser.add_argument('--rounds', type=int, default=3,
                        help='互搏轮次（auto 模式）')
    parser.add_argument('--topic', help='话题名（human 模式可选）')

    args = parser.parse_args()

    session = TrainingSessionV4(args.library)

    if args.mode == 'human':
        if not args.json:
            print("Error: --json required for human mode")
            sys.exit(1)
        session.run_human_mode(args.json, args.topic)
        session.save_session_log()

    elif args.mode == 'auto':
        session.run_auto_mode(args.rounds)

    elif args.mode == 'report':
        report = session.generate_report()
        print(report)
        report_path = os.path.join(session.log_dir, 'training_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存: {report_path}")

    elif args.mode == 'plot':
        paths = session.plot_trends()
        if paths:
            print("趋势图已生成:")
            for p in paths:
                print(f"  - {p}")


if __name__ == '__main__':
    main()
