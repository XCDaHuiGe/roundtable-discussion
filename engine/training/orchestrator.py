# -*- coding: utf-8 -*-
"""
多轮训练编排器 V4.0：融合增强式训练 + AI策略提取 + 严格评分

核心升级（V4.0 vs V3.0）：
- 用 scorer_v2 替代 scorer（严格评分，解决评分虚高问题）
- 用 llm_extractor 替代 extractor（AI深度分析策略质量）
- 用 fusion_engine 替代 evolution_engine（融合增强式升级）
- 支持 --engine v3/v4 参数选择新旧引擎
- 保持向后兼容（默认使用V3引擎）

核心升级（V3.0 vs V2.0）：
- 用 EvolutionEngine 替代旧的 upgrader（策略融合+素材精选替换）
- 集成 DebateArena（对抗自训练，无需人给话题）
- 增强心跳输出（每轮开始/进行中/结束）
- 增强轮次总结（进化指标、密度变化）
- 增强最终总结（维度趋势、专家进化路径、策略密度变化）

用法：
    # V4引擎（推荐，融合增强式训练）
    python engine/training/orchestrator.py --rounds 5 --mode evolution --library expert-library --engine v4

    # V3引擎（向后兼容）
    python engine/training/orchestrator.py --rounds 5 --mode evolution --library expert-library --engine v3

    # 人给话题模式
    python engine/training/orchestrator.py --rounds 3 --mode human --json content/段永平_v8.json --engine v4

    # 自动模式（轮转使用已有 V8 JSON）
    python engine/training/orchestrator.py --rounds 5 --mode auto --library expert-library

    # 带目标分数
    python engine/training/orchestrator.py --rounds 10 --mode auto --library expert-library --target-score 85 --engine v4
"""

import argparse
import glob
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from training.scorer import score_discussion
from training.extractor import extract
from training.trainer import TrainingSession
from training.topic_generator import generate_topics, load_experts

# V3.0 新模块
from training.evolution_engine import EvolutionEngine, EvolutionResult
from training.debate_arena import DebateArena, DebateTopic

# V4.0 新模块
from training.scorer_v2 import score_discussion as score_discussion_v2
from training.llm_extractor import LLMStrategyExtractor
from training.fusion_engine import FusionEngine, FusionResult as FusionResultV4


# ─── 数据结构 ────────────────────────────────────────────

@dataclass
class RoundResult:
    round_num: int
    discussion_file: str
    book_title: str
    score_result: Dict
    expert_evolutions: Dict[str, EvolutionResult] = field(default_factory=dict)
    topic_source: str = ''  # 'human' | 'auto' | 'evolution'
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class FinalSummary:
    total_rounds: int
    mode: str
    score_progression: List[float] = field(default_factory=list)
    dimension_trends: Dict[str, List[float]] = field(default_factory=dict)
    expert_evolution_paths: Dict[str, Dict] = field(default_factory=dict)
    density_changes: Dict[str, List[float]] = field(default_factory=dict)
    target_score: float = 85.0
    target_reached: bool = False
    duration_seconds: float = 0.0
    total_strategy_merges: int = 0
    total_material_replacements: int = 0


# ─── 编排器 ──────────────────────────────────────────────

class TrainingOrchestrator:

    def __init__(self, library_dir: str, content_dir: str = 'content',
                 log_dir: str = 'memory', target_score: float = 85.0,
                 engine_version: str = 'v3'):
        self.library_dir = library_dir
        self.content_dir = content_dir
        self.log_dir = log_dir
        self.target_score = target_score
        self.engine_version = engine_version
        self.session = TrainingSession(library_dir, log_dir)
        self.evolution_engine = EvolutionEngine(library_dir)
        self.debate_arena = DebateArena(library_dir)
        self.fusion_engine = FusionEngine(library_dir) if engine_version == 'v4' else None
        self.llm_extractor = LLMStrategyExtractor() if engine_version == 'v4' else None
        os.makedirs(log_dir, exist_ok=True)

    def run(self, rounds: int, mode: str, json_path: str = None,
            expert_name: str = None) -> FinalSummary:
        """主入口：运行 N 轮训练。"""
        start_time = time.time()
        all_rounds: List[RoundResult] = []
        self._emit_header(rounds, mode)

        # 进化模式：预先生成对抗话题
        evolution_topics = []
        if mode == 'evolution':
            evolution_topics = self.debate_arena.generate_training_plan(rounds)
            self._emit_evolution_plan(evolution_topics)

        for round_num in range(1, rounds + 1):
            # 心跳：轮次开始
            self._emit_heartbeat(round_num, rounds, "START")

            # 根据模式选择讨论文件
            if mode == 'evolution':
                topic_idx = (round_num - 1) % len(evolution_topics) if evolution_topics else 0
                debate_topic = evolution_topics[topic_idx] if topic_idx < len(evolution_topics) else None
                discussion = self._select_evolution_discussion(round_num, debate_topic)
                result = self._run_round(round_num, rounds, discussion,
                                         topic_source='evolution',
                                         debate_topic=debate_topic)
            elif mode == 'human':
                result = self._run_round(round_num, rounds, json_path,
                                         topic_source='human')
            else:  # auto
                discussion = self._select_auto_discussion(round_num)
                if not discussion:
                    self._emit_heartbeat(round_num, rounds, "SKIP", "无可用讨论文件")
                    continue
                result = self._run_round(round_num, rounds, discussion,
                                         topic_source='auto')

            all_rounds.append(result)

            # 轮次总结
            self._emit_round_summary(round_num, rounds, result)

            # 提前终止
            if result.score_result.get('total', 0) >= self.target_score:
                self._emit_heartbeat(round_num, rounds, "TARGET",
                                     f"已达目标 {self.target_score}")
                break

        # 最终总结
        duration = time.time() - start_time
        summary = self._build_final_summary(all_rounds, mode, duration)
        self._emit_final_summary(summary)

        # 保存日志
        self._save_log(all_rounds, summary)

        return summary

    def _run_round(self, round_num: int, total: int, discussion: str,
                   topic_source: str = 'auto',
                   debate_topic: DebateTopic = None) -> RoundResult:
        """执行单轮训练：评分→提取→进化升级。"""
        book_title = os.path.basename(discussion).replace('_v8.json', '').replace('_V8.json', '') if discussion else ''
        if debate_topic:
            book_title = debate_topic.topic[:50]

        # 心跳：评分中
        self._emit_heartbeat(round_num, total, "SCORING", os.path.basename(discussion) if discussion else book_title)
        try:
            if self.engine_version == 'v4':
                score_result = score_discussion_v2(discussion)
            else:
                score_result = score_discussion(discussion)
        except Exception as e:
            self._emit_heartbeat(round_num, total, "ERROR", f"评分失败: {e}")
            return RoundResult(
                round_num=round_num, discussion_file=discussion or '',
                book_title=book_title, score_result={'total': 0, 'grade': 'F', 'dimensions': {}},
                topic_source=topic_source
            )

        score_total = score_result.get('total', 0)
        grade = score_result.get('grade', 'F')
        dims = score_result.get('dimensions', {})
        dim_short = self._format_dims_short(dims)
        self._emit_heartbeat(round_num, total, "SCORE",
                             f"{score_total:.1f} ({grade})  {dim_short}")

        # 提取策略
        self._emit_heartbeat(round_num, total, "EXTRACT", book_title)
        try:
            if self.engine_version == 'v4' and self.llm_extractor:
                extraction = self.llm_extractor.extract(discussion)
            else:
                extraction = extract(discussion)
        except Exception as e:
            self._emit_heartbeat(round_num, total, "ERROR", f"提取失败: {e}")
            return RoundResult(
                round_num=round_num, discussion_file=discussion or '',
                book_title=book_title, score_result=score_result,
                topic_source=topic_source
            )

        # 评分阈值：统一使用60分（让更多讨论能触发进化）
        MIN_EVOLVE_SCORE = 60.0
        if score_total < MIN_EVOLVE_SCORE:
            self._emit_heartbeat(round_num, total, "SKIP",
                                 f"评分 {score_total:.1f} < {MIN_EVOLVE_SCORE}，跳过进化")
            return RoundResult(
                round_num=round_num,
                discussion_file=discussion or '',
                book_title=book_title,
                score_result=score_result,
                topic_source=topic_source,
            )

        # 进化升级专家
        attack_eff = dims.get('attack_efficiency', {}).get('score', 0.0)
        defense_rate_val = dims.get('defense_rate', {}).get('score', 0.0)
        evolutions = {}

        self._emit_heartbeat(round_num, total, "EVOLVE", book_title)
        for expert_name, expert_data in extraction.get('experts', {}).items():
            strategy = {
                'attack_strategy': expert_data.get('attack_strategy', {}),
                'defense_weakness': expert_data.get('defense_weakness', {}),
                'style_fingerprint': expert_data.get('style_fingerprint', {}),
                'evidence_preference': expert_data.get('evidence_preference', {}),
                'interaction_pattern': expert_data.get('interaction_pattern', {}),
            }
            try:
                if self.engine_version == 'v4' and self.fusion_engine:
                    md_path = self.fusion_engine.find_expert_md(expert_name)
                    if md_path:
                        self.fusion_engine.upgrade_expert(md_path, strategy, score_total)
                        self._emit_heartbeat(round_num, total, "FUSED",
                                             f"{expert_name} 融合增强完成")
                else:
                    evo_result = self.evolution_engine.evolve(
                        expert_name, strategy,
                        topic=book_title,
                        score=score_total,
                        attack_eff=attack_eff,
                        defense_rate=defense_rate_val,
                    )
                    if evo_result:
                        evolutions[expert_name] = evo_result
                        v_str = f"V{evo_result.old_version}→V{evo_result.new_version}"
                        m_str = f"{len(evo_result.strategy_merges)}策略"
                        r_str = f"{len(evo_result.material_replacements)}替换"
                        self._emit_heartbeat(round_num, total, "EVOLVED",
                                             f"{expert_name} {v_str} ({m_str}, {r_str})")
            except Exception as e:
                self._emit_heartbeat(round_num, total, "EVO_ERR",
                                     f"{expert_name}: {e}")

        if not evolutions and self.engine_version != 'v4':
            self._emit_heartbeat(round_num, total, "EVOLVE", "无专家进化")

        return RoundResult(
            round_num=round_num,
            discussion_file=discussion or '',
            book_title=book_title,
            score_result=score_result,
            expert_evolutions=evolutions,
            topic_source=topic_source,
        )

    def _select_evolution_discussion(self, round_num: int,
                                      debate_topic: DebateTopic = None) -> str:
        """进化模式选择讨论文件"""
        if debate_topic:
            # 尝试找包含这两个专家的已有讨论
            v8_files = sorted(glob.glob(os.path.join(self.content_dir, '*_v8.json')))
            for f in v8_files:
                try:
                    with open(f, 'r', encoding='utf-8-sig') as fh:
                        d = json.load(fh)
                    names = [e['name'] for e in d.get('experts', [])]
                    if debate_topic.expert1 in names or debate_topic.expert2 in names:
                        return f
                except Exception:
                    continue

        # 回退到轮转
        return self._select_auto_discussion(round_num)

    def _select_auto_discussion(self, round_num: int) -> Optional[str]:
        """自动模式选择讨论文件"""
        v8_files = sorted(glob.glob(os.path.join(self.content_dir, '*_v8.json')))
        if not v8_files:
            return None
        idx = (round_num - 1) % len(v8_files)
        return v8_files[idx]

    # ─── 输出格式 ─────────────────────────────────────────

    def _emit_header(self, rounds: int, mode: str):
        """输出训练头信息"""
        expert_count = len(self.debate_arena.profiles)
        conflict_count = len(self.debate_arena.get_all_conflicts())
        engine_name = 'V4.0 融合增强式' if self.engine_version == 'v4' else 'V3.0 进化式'
        print(f"\n{'='*60}")
        print(f"  圆桌会议训练引擎 {engine_name}")
        print(f"  模式: {mode} | 轮次: {rounds} | 目标: {self.target_score}")
        print(f"  专家库: {expert_count} 位专家 | {conflict_count} 个信念冲突点")
        print(f"{'='*60}\n")

    def _emit_evolution_plan(self, topics: List[DebateTopic]):
        """输出进化训练计划"""
        print(f"  EVOLUTION PLAN")
        print(f"  {'─'*56}")
        for t in topics:
            print(f"  Round {t.round_num}: {t.expert1} vs {t.expert2}")
            print(f"  话题: {t.topic[:55]}...")
            print(f"  信念: {t.belief1[:25]} ↔ {t.belief2[:25]}")
            print()
        print(f"  {'─'*56}\n")

    def _emit_heartbeat(self, round_num: int, total: int, phase: str, detail: str = ''):
        """输出心跳行"""
        tag = f"[{round_num}/{total}]"
        phase_str = f"{phase:<10}"
        line = f"  {tag} {phase_str}"
        if detail:
            line += f" {detail}"
        print(line)

    def _emit_round_summary(self, round_num: int, total: int, result: RoundResult):
        """输出轮次总结"""
        dims = result.score_result.get('dimensions', {})
        score_total = result.score_result.get('total', 0)
        grade = result.score_result.get('grade', 'F')

        print(f"\n  {'─'*56}")
        print(f"  ROUND {round_num}/{total} SUMMARY")
        print(f"  {'─'*56}")
        print(f"  Source: {result.topic_source} | Topic: {result.book_title[:40]}")
        print(f"  Score: {score_total:.1f} ({grade})")
        print()

        # 维度表
        dim_names_cn = {
            'attack_efficiency': '攻击效率',
            'defense_rate': '防御成功率',
            'evidence_hit': '证据命中率',
            'style_recognition': '风格辨识度',
            'cognitive_contribution': '认知贡献',
            'case_quality': '案例质量',
            'structure': '结构完整性',
        }
        print(f"  {'维度':<12} {'得分':>6} {'权重':>6} {'加权':>6}")
        print(f"  {'-'*36}")
        for dim_name, dim in dims.items():
            cn = dim_names_cn.get(dim_name, dim_name)
            print(f"  {cn:<12} {dim.get('score', 0):>5.1f}% {dim.get('weight', 0)*100:>5.0f}% {dim.get('weighted', 0):>5.1f}")

        # 专家进化详情
        if result.expert_evolutions:
            print()
            print(f"  EXPERT EVOLUTIONS:")
            for name, evo in result.expert_evolutions.items():
                print(f"    {name}: V{evo.old_version}→V{evo.new_version}")
                if evo.strategy_merges:
                    for m in evo.strategy_merges:
                        print(f"      + 策略融合: {m}")
                if evo.material_replacements:
                    for r in evo.material_replacements:
                        print(f"      ~ 素材替换: {r}")
                delta = evo.density_delta
                sign = '+' if delta > 0 else ''
                print(f"      密度变化: {sign}{delta:.1f}%")

        print(f"  {'─'*56}\n")

    def _emit_final_summary(self, summary: FinalSummary):
        """输出最终总结"""
        engine_name = 'V4.0 FUSION' if self.engine_version == 'v4' else 'V3.0 EVOLUTION'
        print(f"\n{'='*60}")
        print(f"  TRAINING COMPLETE — {engine_name} REPORT")
        print(f"{'='*60}")
        print(f"  Mode: {summary.mode} | Rounds: {summary.total_rounds}")
        print(f"  Duration: {summary.duration_seconds:.1f}s")
        print(f"  Target: {summary.target_score} | Reached: {'YES' if summary.target_reached else 'NO'}")
        if self.engine_version == 'v3':
            print(f"  Total Strategy Merges: {summary.total_strategy_merges}")
            print(f"  Total Material Replacements: {summary.total_material_replacements}")

        # 分数趋势
        if summary.score_progression:
            print()
            print(f"  SCORE PROGRESSION")
            max_score = max(summary.score_progression) if summary.score_progression else 100
            for i, s in enumerate(summary.score_progression, 1):
                bar_len = int(s / max_score * 30) if max_score > 0 else 0
                bar = '\u2588' * bar_len + '\u2591' * (30 - bar_len)
                print(f"  Round {i}: {s:>5.1f}  {bar}")
            if len(summary.score_progression) > 1:
                delta = summary.score_progression[-1] - summary.score_progression[0]
                print(f"  Delta:   {delta:+.1f} points")

        # 维度趋势
        if summary.dimension_trends:
            print()
            print(f"  DIMENSION TRENDS")
            dim_names_cn = {
                'attack_efficiency': '攻击效率',
                'defense_rate': '防御成功率',
                'evidence_hit': '证据命中率',
                'style_recognition': '风格辨识度',
                'cognitive_contribution': '认知贡献',
                'case_quality': '案例质量',
                'structure': '结构完整性',
            }
            print(f"  {'维度':<12} {'起始':>6} {'最终':>6} {'变化':>6}")
            print(f"  {'-'*36}")
            for dim_name, scores in summary.dimension_trends.items():
                if scores:
                    cn = dim_names_cn.get(dim_name, dim_name)
                    start = scores[0]
                    end = scores[-1]
                    delta = end - start
                    print(f"  {cn:<12} {start:>5.1f}% {end:>5.1f}% {delta:>+5.1f}")

        # 专家进化路径
        if summary.expert_evolution_paths:
            print()
            print(f"  EXPERT EVOLUTION PATHS")
            for name, info in sorted(summary.expert_evolution_paths.items()):
                first_v = info.get('first_version', 1)
                last_v = info.get('last_version', 1)
                merges = info.get('total_merges', 0)
                replacements = info.get('total_replacements', 0)
                rounds_trained = info.get('rounds', [])
                print(f"    {name}: V{first_v}→V{last_v} "
                      f"({merges}策略融合, {replacements}素材替换, "
                      f"轮次: {','.join(str(r) for r in rounds_trained)})")

        # 密度变化
        if summary.density_changes:
            print()
            print(f"  DENSITY EVOLUTION (Alloy Model)")
            for name, densities in summary.density_changes.items():
                if len(densities) > 1:
                    start_d = densities[0]
                    end_d = densities[-1]
                    change = end_d - start_d
                    sign = '+' if change > 0 else ''
                    print(f"    {name}: {start_d:.1f}% → {end_d:.1f}% ({sign}{change:.1f}%)")
                elif densities:
                    print(f"    {name}: {densities[0]:.1f}%")

        print(f"\n{'='*60}\n")

    def _format_dims_short(self, dims: Dict) -> str:
        """格式化维度分数为简短字符串"""
        short_names = {
            'attack_efficiency': 'atk',
            'defense_rate': 'def',
            'evidence_hit': 'evi',
            'style_recognition': 'sty',
            'cognitive_contribution': 'cog',
            'case_quality': 'cas',
            'structure': 'str',
        }
        parts = []
        for dim_name, dim in dims.items():
            short = short_names.get(dim_name, dim_name[:3])
            parts.append(f"{short}:{dim.get('score', 0):.0f}")
        return "[" + " ".join(parts) + "]"

    def _build_final_summary(self, all_rounds: List[RoundResult],
                              mode: str, duration: float) -> FinalSummary:
        """构建最终总结"""
        summary = FinalSummary(
            total_rounds=len(all_rounds),
            mode=mode,
            target_score=self.target_score,
            duration_seconds=duration,
        )

        # 分数趋势
        for r in all_rounds:
            summary.score_progression.append(r.score_result.get('total', 0))

        # 维度趋势
        dim_names = ['attack_efficiency', 'defense_rate', 'evidence_hit',
                     'style_recognition', 'cognitive_contribution', 'case_quality', 'structure']
        for dim in dim_names:
            scores = []
            for r in all_rounds:
                dim_data = r.score_result.get('dimensions', {}).get(dim, {})
                scores.append(dim_data.get('score', 0))
            summary.dimension_trends[dim] = scores

        # 专家进化路径
        for r in all_rounds:
            for name, evo in r.expert_evolutions.items():
                if name not in summary.expert_evolution_paths:
                    summary.expert_evolution_paths[name] = {
                        'first_version': evo.old_version,
                        'last_version': evo.new_version,
                        'rounds': [],
                        'total_merges': 0,
                        'total_replacements': 0,
                    }
                entry = summary.expert_evolution_paths[name]
                entry['last_version'] = evo.new_version
                entry['rounds'].append(r.round_num)
                entry['total_merges'] += len(evo.strategy_merges)
                entry['total_replacements'] += len(evo.material_replacements)
                summary.total_strategy_merges += len(evo.strategy_merges)
                summary.total_material_replacements += len(evo.material_replacements)

                # 密度变化
                if name not in summary.density_changes:
                    summary.density_changes[name] = []
                summary.density_changes[name].append(evo.density_delta)

        # 是否达标
        if summary.score_progression:
            summary.target_reached = max(summary.score_progression) >= self.target_score

        return summary

    def _save_log(self, all_rounds: List[RoundResult], summary: FinalSummary):
        """保存训练日志"""
        log = {
            'version': 'V3.0',
            'start_time': all_rounds[0].timestamp if all_rounds else '',
            'end_time': datetime.now().isoformat(),
            'mode': summary.mode,
            'total_rounds': summary.total_rounds,
            'target_score': summary.target_score,
            'target_reached': summary.target_reached,
            'duration_seconds': summary.duration_seconds,
            'score_progression': summary.score_progression,
            'total_strategy_merges': summary.total_strategy_merges,
            'total_material_replacements': summary.total_material_replacements,
            'rounds': [
                {
                    'round': r.round_num,
                    'discussion': os.path.basename(r.discussion_file),
                    'book_title': r.book_title,
                    'score': r.score_result.get('total', 0),
                    'grade': r.score_result.get('grade', 'F'),
                    'topic_source': r.topic_source,
                    'evolutions': {
                        name: {
                            'old_version': evo.old_version,
                            'new_version': evo.new_version,
                            'strategy_merges': evo.strategy_merges,
                            'material_replacements': evo.material_replacements,
                            'density_delta': evo.density_delta,
                        }
                        for name, evo in r.expert_evolutions.items()
                    },
                }
                for r in all_rounds
            ],
        }

        log_path = os.path.join(
            self.log_dir,
            f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"  Session log: {log_path}")


# ─── CLI ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='圆桌会议训练编排器 V4.0')
    parser.add_argument('--rounds', type=int, default=3, help='训练轮次')
    parser.add_argument('--mode', choices=['auto', 'human', 'evolution', 'replay'],
                        default='evolution', help='训练模式')
    parser.add_argument('--json', help='讨论 JSON 路径（human 模式）')
    parser.add_argument('--library', default='expert-library', help='专家库目录')
    parser.add_argument('--content', default='content', help='讨论内容目录')
    parser.add_argument('--expert', help='目标专家名（replay 模式）')
    parser.add_argument('--target-score', type=float, default=85.0, help='目标分数')
    parser.add_argument('--log-dir', default='memory', help='日志目录')
    parser.add_argument('--engine', choices=['v3', 'v4'], default='v3',
                        help='引擎版本: v3(进化式) / v4(融合增强式)')

    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    orchestrator = TrainingOrchestrator(
        library_dir=args.library,
        content_dir=args.content,
        log_dir=args.log_dir,
        target_score=args.target_score,
        engine_version=args.engine,
    )

    if args.mode == 'human' and not args.json:
        print("Error: --json required for human mode")
        sys.exit(1)

    if args.mode == 'replay' and not args.expert:
        print("Error: --expert required for replay mode")
        sys.exit(1)

    orchestrator.run(
        rounds=args.rounds,
        mode=args.mode,
        json_path=args.json,
        expert_name=args.expert,
    )


if __name__ == '__main__':
    main()
