# -*- coding: utf-8 -*-
"""
训练效果追踪系统 V4.0

核心功能：
- 跨轮次评分追踪（看评分是否随训练提升）
- 专家能力进化曲线（每个维度的成长轨迹）
- 训练ROI分析（投入多少训练→产出多少提升）
- 自动诊断训练瓶颈（为什么评分不提升）

数据存储：
- memory/training_history.jsonl  # 所有训练记录的追加日志
- memory/expert_evolution/       # 每位专家的进化数据

用法：
    from engine.training.tracker import TrainingTracker
    tracker = TrainingTracker('expert-library')
    tracker.record_training(session_data)
    report = tracker.generate_report()
    tracker.plot_trends()
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class TrainingRecord:
    """单次训练记录"""
    timestamp: str
    book_title: str
    expert_name: str
    old_version: int
    new_version: int
    score_before: float = 0.0
    score_after: float = 0.0
    attack_eff: float = 0.0
    defense_rate: float = 0.0
    operations: List[str] = field(default_factory=list)
    capability_delta: Dict = field(default_factory=dict)
    quality_matrix: Dict = field(default_factory=dict)


@dataclass
class ExpertEvolution:
    """一位专家的完整进化轨迹"""
    expert_name: str
    training_records: List[TrainingRecord] = field(default_factory=list)
    score_trend: List[float] = field(default_factory=list)
    capability_timeline: List[Dict] = field(default_factory=list)


class TrainingTracker:
    """训练效果追踪系统"""

    def __init__(self, library_dir: str, memory_dir: str = 'memory'):
        self.library_dir = library_dir
        self.memory_dir = memory_dir
        self.history_file = os.path.join(memory_dir, 'training_history.jsonl')
        self.evolution_dir = os.path.join(memory_dir, 'expert_evolution')

        os.makedirs(memory_dir, exist_ok=True)
        os.makedirs(self.evolution_dir, exist_ok=True)

    def record_training(self, session_data: Dict) -> None:
        """
        记录一次训练会话

        Args:
            session_data: {
                'book_title': str,
                'timestamp': str,
                'experts': {
                    name: {
                        'old_version': int,
                        'new_version': int,
                        'score': float,
                        'attack_eff': float,
                        'defense_rate': float,
                        'operations': List[str],
                        'capability_delta': Dict,
                        'quality_matrix': Dict,
                    }
                }
            }
        """
        timestamp = session_data.get('timestamp', datetime.now().isoformat())
        book_title = session_data.get('book_title', '未知')

        # 追加到全局历史
        with open(self.history_file, 'a', encoding='utf-8') as f:
            record = {
                'timestamp': timestamp,
                'book_title': book_title,
                'experts': session_data.get('experts', {}),
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

        # 更新每位专家的进化数据
        for expert_name, data in session_data.get('experts', {}).items():
            self._update_expert_evolution(expert_name, {
                'timestamp': timestamp,
                'book_title': book_title,
                **data,
            })

    def _update_expert_evolution(self, expert_name: str, data: Dict) -> None:
        """更新单个专家的进化数据"""
        safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', expert_name)
        evo_file = os.path.join(self.evolution_dir, f'{safe_name}.json')

        evolution = {'expert_name': expert_name, 'records': []}
        if os.path.exists(evo_file):
            with open(evo_file, 'r', encoding='utf-8') as f:
                evolution = json.load(f)

        record = {
            'timestamp': data.get('timestamp'),
            'book_title': data.get('book_title'),
            'old_version': data.get('old_version', 1),
            'new_version': data.get('new_version', 1),
            'score': data.get('score', 0.0),
            'attack_eff': data.get('attack_eff', 0.0),
            'defense_rate': data.get('defense_rate', 0.0),
            'operations': data.get('operations', []),
            'capability_delta': data.get('capability_delta', {}),
            'quality_matrix': data.get('quality_matrix', {}),
        }

        evolution['records'].append(record)

        # 计算趋势
        scores = [r['score'] for r in evolution['records'] if r['score'] > 0]
        evolution['score_trend'] = scores
        evolution['avg_score'] = sum(scores) / len(scores) if scores else 0
        evolution['best_score'] = max(scores) if scores else 0
        evolution['training_count'] = len(evolution['records'])

        # 计算能力提升
        if len(evolution['records']) >= 2:
            first = evolution['records'][0]
            latest = evolution['records'][-1]
            evolution['score_delta'] = latest['score'] - first['score']
            evolution['version_delta'] = latest['new_version'] - first['old_version']
        else:
            evolution['score_delta'] = 0
            evolution['version_delta'] = 0

        with open(evo_file, 'w', encoding='utf-8') as f:
            json.dump(evolution, f, ensure_ascii=False, indent=2)

    def get_expert_evolution(self, expert_name: str) -> Optional[Dict]:
        """获取一位专家的进化数据"""
        safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', expert_name)
        evo_file = os.path.join(self.evolution_dir, f'{safe_name}.json')

        if not os.path.exists(evo_file):
            return None

        with open(evo_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_all_evolution(self) -> Dict[str, Dict]:
        """获取所有专家的进化数据"""
        result = {}
        if not os.path.exists(self.evolution_dir):
            return result

        for fname in os.listdir(self.evolution_dir):
            if fname.endswith('.json'):
                with open(os.path.join(self.evolution_dir, fname), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result[data.get('expert_name', fname)] = data
        return result

    def analyze_training_effectiveness(self) -> Dict:
        """
        分析训练效果：训练是否真的提升了评分？

        Returns:
            {
                'overall_trend': 'up' | 'down' | 'flat',
                'avg_improvement_per_training': float,
                'experts_with_positive_trend': List[str],
                'experts_with_negative_trend': List[str],
                'bottleneck_analysis': Dict,
            }
        """
        all_evo = self.get_all_evolution()

        if not all_evo:
            return {'status': 'no_data'}

        # 统计所有专家的训练效果
        positive_trend = []
        negative_trend = []
        flat_trend = []
        total_improvement = 0
        total_trainings = 0

        for name, evo in all_evo.items():
            records = evo.get('records', [])
            if len(records) < 2:
                continue

            scores = [r['score'] for r in records if r['score'] > 0]
            if len(scores) < 2:
                continue

            # 线性回归判断趋势
            trend = self._calc_linear_trend(scores)

            if trend > 0.5:
                positive_trend.append(name)
            elif trend < -0.5:
                negative_trend.append(name)
            else:
                flat_trend.append(name)

            total_improvement += scores[-1] - scores[0]
            total_trainings += len(records)

        avg_improvement = total_improvement / total_trainings if total_trainings > 0 else 0

        # 瓶颈分析
        bottleneck = self._analyze_bottleneck(all_evo)

        return {
            'overall_trend': 'up' if len(positive_trend) > len(negative_trend) else 'down' if len(negative_trend) > len(positive_trend) else 'flat',
            'positive_count': len(positive_trend),
            'negative_count': len(negative_trend),
            'flat_count': len(flat_trend),
            'experts_with_positive_trend': positive_trend,
            'experts_with_negative_trend': negative_trend,
            'avg_improvement_per_training': round(avg_improvement, 2),
            'bottleneck_analysis': bottleneck,
        }

    def _calc_linear_trend(self, scores: List[float]) -> float:
        """计算线性趋势（简化版）"""
        if len(scores) < 2:
            return 0.0
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n

        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        # 归一化：每轮训练的评分变化
        return slope

    def _analyze_bottleneck(self, all_evo: Dict) -> Dict:
        """分析训练瓶颈"""
        # 收集所有训练记录中的维度分数
        dimension_scores = {
            'depth': [],
            'logic': [],
            'evidence': [],
            'style': [],
        }

        for evo in all_evo.values():
            for record in evo.get('records', []):
                qm = record.get('quality_matrix', {})
                for dim in dimension_scores:
                    if dim in qm:
                        dimension_scores[dim].append(qm[dim])

        # 找出最弱的维度
        avg_dims = {}
        for dim, scores in dimension_scores.items():
            if scores:
                avg_dims[dim] = sum(scores) / len(scores)

        weakest_dim = min(avg_dims, key=avg_dims.get) if avg_dims else 'unknown'

        # 分析为什么评分不提升
        reasons = []

        # 检查1：训练次数是否足够
        total_records = sum(len(evo.get('records', [])) for evo in all_evo.values())
        if total_records < 10:
            reasons.append("训练次数不足（<10次），需要更多数据")

        # 检查2：是否有专家评分持续下降
        declining_experts = []
        for name, evo in all_evo.items():
            records = evo.get('records', [])
            if len(records) >= 3:
                recent_scores = [r['score'] for r in records[-3:] if r['score'] > 0]
                if len(recent_scores) >= 3 and recent_scores[-1] < recent_scores[0]:
                    declining_experts.append(name)
        if declining_experts:
            reasons.append(f"专家评分下降: {', '.join(declining_experts)}")

        # 检查3：能力增量是否太小
        small_deltas = []
        for name, evo in all_evo.items():
            for record in evo.get('records', []):
                delta = record.get('capability_delta', {})
                total_delta = sum(delta.values())
                if total_delta < 0.5:
                    small_deltas.append(name)
        if small_deltas:
            reasons.append(f"能力增量过小（可能是融合失败）")

        return {
            'weakest_dimension': weakest_dim,
            'dimension_averages': avg_dims,
            'possible_reasons': reasons,
            'recommendation': self._generate_recommendation(weakest_dim, reasons),
        }

    def _generate_recommendation(self, weakest_dim: str, reasons: List[str]) -> str:
        """生成改进建议"""
        recommendations = []

        dim_map = {
            'depth': '认知深度不足，建议增加对问题本质的挖掘',
            'logic': '逻辑严密性不足，建议强化论证链条',
            'evidence': '证据质量不足，建议增加具体情节引用',
            'style': '风格辨识度不足，建议强化个人化表达',
        }

        if weakest_dim in dim_map:
            recommendations.append(dim_map[weakest_dim])

        if '训练次数不足' in str(reasons):
            recommendations.append('增加训练轮次，至少完成20次训练再评估效果')

        if '评分下降' in str(reasons):
            recommendations.append('检查融合引擎是否过度替换，考虑降低替换阈值')

        return ' | '.join(recommendations) if recommendations else '继续观察'

    def generate_report(self) -> str:
        """生成训练效果报告（Markdown格式）"""
        analysis = self.analyze_training_effectiveness()
        all_evo = self.get_all_evolution()

        report = f"""# 训练效果追踪报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 总体趋势

"""
        if analysis.get('status') == 'no_data':
            report += "暂无训练数据。请先执行训练。\n"
            return report

        trend_emoji = {'up': '📈', 'down': '📉', 'flat': '➡️'}
        trend = analysis.get('overall_trend', 'flat')
        report += f"- 整体趋势: {trend_emoji.get(trend, '')} {trend.upper()}\n"
        report += f"- 平均每次训练提升: {analysis.get('avg_improvement_per_training', 0):.2f} 分\n"
        report += f"- 正向趋势专家: {analysis.get('positive_count', 0)} 位\n"
        report += f"- 负向趋势专家: {analysis.get('negative_count', 0)} 位\n"
        report += f"- 平稳趋势专家: {analysis.get('flat_count', 0)} 位\n"

        report += "\n## 专家进化详情\n\n"
        report += "| 专家 | 训练次数 | 最新评分 | 评分变化 | 版本 |\n"
        report += "|------|---------|---------|---------|------|\n"

        for name, evo in sorted(all_evo.items()):
            records = evo.get('records', [])
            if not records:
                continue
            latest = records[-1]
            first = records[0]
            score_delta = latest.get('score', 0) - first.get('score', 0)
            delta_str = f"+{score_delta:.1f}" if score_delta >= 0 else f"{score_delta:.1f}"

            report += f"| {name} | {len(records)} | {latest.get('score', 0):.1f} | {delta_str} | V{latest.get('new_version', 1)} |\n"

        report += "\n## 瓶颈分析\n\n"
        bottleneck = analysis.get('bottleneck_analysis', {})
        report += f"- 最弱维度: **{bottleneck.get('weakest_dimension', 'N/A')}**\n"
        report += f"- 维度平均分: {bottleneck.get('dimension_averages', {})}\n"

        if bottleneck.get('possible_reasons'):
            report += "\n### 可能原因\n\n"
            for reason in bottleneck['possible_reasons']:
                report += f"- {reason}\n"

        report += f"\n### 改进建议\n\n{bottleneck.get('recommendation', '继续观察')}\n"

        return report

    def plot_trends(self, output_dir: str = 'memory/charts') -> List[str]:
        """
        绘制趋势图（返回生成的图片路径列表）

        需要 matplotlib，如果未安装则跳过
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
        except ImportError:
            print("[WARN] matplotlib 未安装，跳过绘图")
            return []

        os.makedirs(output_dir, exist_ok=True)
        all_evo = self.get_all_evolution()
        generated = []

        # 1. 总体评分趋势图
        fig, ax = plt.subplots(figsize=(10, 6))

        for name, evo in all_evo.items():
            records = evo.get('records', [])
            scores = [r['score'] for r in records if r['score'] > 0]
            if len(scores) >= 2:
                ax.plot(range(1, len(scores) + 1), scores, marker='o', label=name)

        ax.set_xlabel('Training Round')
        ax.set_ylabel('Score')
        ax.set_title('Expert Score Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)

        path = os.path.join(output_dir, 'score_trends.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        generated.append(path)

        # 2. 能力增量分布图
        fig, ax = plt.subplots(figsize=(8, 6))

        deltas = []
        for evo in all_evo.values():
            for record in evo.get('records', []):
                delta = record.get('capability_delta', {})
                total = sum(delta.values())
                if total > 0:
                    deltas.append(total)

        if deltas:
            ax.hist(deltas, bins=20, edgecolor='black')
            ax.set_xlabel('Capability Delta')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Capability Improvements')

            path = os.path.join(output_dir, 'capability_deltas.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            generated.append(path)

        return generated

    def export_training_data(self, output_path: str = None) -> str:
        """导出所有训练数据为CSV（便于外部分析）"""
        if output_path is None:
            output_path = os.path.join(self.memory_dir, 'training_data.csv')

        import csv

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'expert_name', 'book_title', 'old_version',
                'new_version', 'score', 'attack_eff', 'defense_rate',
                'capability_delta_total', 'operations_count',
            ])

            all_evo = self.get_all_evolution()
            for name, evo in all_evo.items():
                for record in evo.get('records', []):
                    delta = record.get('capability_delta', {})
                    writer.writerow([
                        record.get('timestamp', ''),
                        name,
                        record.get('book_title', ''),
                        record.get('old_version', ''),
                        record.get('new_version', ''),
                        record.get('score', 0),
                        record.get('attack_eff', 0),
                        record.get('defense_rate', 0),
                        sum(delta.values()),
                        len(record.get('operations', [])),
                    ])

        return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='训练效果追踪系统')
    parser.add_argument('--library', default='expert-library', help='专家库目录')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--plot', action='store_true', help='绘制趋势图')
    parser.add_argument('--export', action='store_true', help='导出CSV')
    args = parser.parse_args()

    tracker = TrainingTracker(args.library)

    if args.report:
        report = tracker.generate_report()
        print(report)

        # 保存报告
        report_path = os.path.join(tracker.memory_dir, 'training_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存: {report_path}")

    if args.plot:
        paths = tracker.plot_trends()
        if paths:
            print(f"\n图表已生成:")
            for p in paths:
                print(f"  - {p}")

    if args.export:
        csv_path = tracker.export_training_data()
        print(f"\nCSV已导出: {csv_path}")

    if not any([args.report, args.plot, args.export]):
        # 默认显示摘要
        analysis = tracker.analyze_training_effectiveness()
        if analysis.get('status') == 'no_data':
            print("暂无训练数据")
        else:
            print(f"\n训练效果摘要:")
            print(f"  整体趋势: {analysis.get('overall_trend', 'N/A')}")
            print(f"  平均提升: {analysis.get('avg_improvement_per_training', 0):.2f} 分/次")
            print(f"  正向趋势: {analysis.get('positive_count', 0)} 位专家")
            print(f"  负向趋势: {analysis.get('negative_count', 0)} 位专家")


if __name__ == '__main__':
    main()
