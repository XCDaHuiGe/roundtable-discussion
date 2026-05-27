# -*- coding: utf-8 -*-
"""
多轮训练编排器：设定训练轮数、心跳输出、轮次总结、最终总结。

用法：
    # 自动模式（轮转使用 V8 JSON）
    python engine/training/orchestrator.py --rounds 5 --mode auto --library expert-library

    # 人给话题模式
    python engine/training/orchestrator.py --rounds 3 --mode human --json content/段永平_v8.json --library expert-library

    # 带目标分数
    python engine/training/orchestrator.py --rounds 10 --mode auto --library expert-library --target-score 85
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
from training.upgrader import upgrade_expert, parse_version
from training.trainer import TrainingSession
from training.miner import MaterialReader
from training.topic_builder import build_topics_from_material
from training.topic_generator import generate_topics, load_experts


# ─── 数据结构 ────────────────────────────────────────────

@dataclass
class RoundResult:
    round_num: int
    discussion_file: str
    book_title: str
    score_result: Dict
    expert_upgrades: Dict[str, Dict] = field(default_factory=dict)
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
    experts_upgraded: Dict[str, Dict] = field(default_factory=dict)
    target_score: float = 85.0
    target_reached: bool = False
    duration_seconds: float = 0.0


# ─── 编排器 ──────────────────────────────────────────────

class TrainingOrchestrator:

    def __init__(self, library_dir: str, content_dir: str = 'content',
                 log_dir: str = 'memory', target_score: float = 85.0,
                 use_material: bool = False):
        self.library_dir = library_dir
        self.content_dir = content_dir
        self.log_dir = log_dir
        self.target_score = target_score
        self.use_material = use_material
        self.session = TrainingSession(library_dir, log_dir)
        self.material_reader = MaterialReader(content_dir) if use_material else None
        os.makedirs(log_dir, exist_ok=True)

    def run(self, rounds: int, mode: str, json_path: str = None,
            expert_name: str = None) -> FinalSummary:
        """主入口：运行 N 轮训练。"""
        start_time = time.time()
        all_rounds: List[RoundResult] = []
        self._emit_header(rounds, mode)

        # 素材模式：预先生成话题计划
        material_topics = []
        if self.use_material and mode == 'auto':
            material_topics = self._prepare_material_topics(rounds)

        for round_num in range(1, rounds + 1):
            # 心跳：轮次开始
            self._emit_heartbeat(round_num, rounds, "START")

            # 素材模式：尝试从本地素材构建话题
            mined_topic = None
            if self.use_material and mode == 'auto':
                mined_topic = self._try_build_topic_from_material(round_num, rounds, material_topics)

            # 选择讨论文件
            discussion = self._select_discussion_file(round_num, mode, json_path, expert_name)
            if not discussion:
                self._emit_heartbeat(round_num, rounds, "SKIP", "无可用讨论文件")
                continue

            # 执行单轮
            result = self._run_round(round_num, rounds, discussion)
            if mined_topic:
                result.book_title = f"{result.book_title} [话题: {mined_topic[:40]}]"
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

    def _run_round(self, round_num: int, total: int, discussion: str) -> RoundResult:
        """执行单轮训练：评分→提取→升级。"""
        book_title = os.path.basename(discussion).replace('_v8.json', '').replace('_V8.json', '')

        # 评分
        self._emit_heartbeat(round_num, total, "SCORING", os.path.basename(discussion))
        try:
            score_result = score_discussion(discussion)
        except Exception as e:
            self._emit_heartbeat(round_num, total, "ERROR", f"评分失败: {e}")
            return RoundResult(
                round_num=round_num, discussion_file=discussion,
                book_title=book_title, score_result={'total': 0, 'grade': 'F', 'dimensions': {}}
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
            extraction = extract(discussion)
        except Exception as e:
            self._emit_heartbeat(round_num, total, "ERROR", f"提取失败: {e}")
            return RoundResult(
                round_num=round_num, discussion_file=discussion,
                book_title=book_title, score_result=score_result
            )

        # 升级专家
        attack_eff = dims.get('attack_efficiency', {}).get('score', 0.0)
        defense_rate_val = dims.get('defense_rate', {}).get('score', 0.0)
        upgrades = {}

        upgrade_parts = []
        for expert_name, expert_data in extraction.get('experts', {}).items():
            expert_md = self.session.find_expert_md(expert_name)
            if not expert_md:
                continue

            old_version = 0
            try:
                with open(expert_md, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                old_version = parse_version(old_content)
            except Exception:
                pass

            strategy = self.session._build_strategy_template(expert_data, dims)

            try:
                new_content = upgrade_expert(
                    expert_md, strategy,
                    topic=book_title,
                    score=score_total,
                    attack_eff=attack_eff,
                    defense_rate=defense_rate_val,
                )
                new_version = parse_version(new_content)
                speech_count = expert_data.get('speech_count', 0)
                attack_count = len([s for s in expert_data.get('speeches', []) if s.get('type') == 'attack'])

                upgrades[expert_name] = {
                    'file': expert_md,
                    'old_version': old_version,
                    'new_version': new_version,
                    'speech_count': speech_count,
                    'attack_count': attack_count,
                }
                upgrade_parts.append(f"{expert_name} V{old_version}→V{new_version}")
            except Exception as e:
                upgrade_parts.append(f"{expert_name} ERR:{e}")

        if upgrade_parts:
            self._emit_heartbeat(round_num, total, "UPGRADE", " | ".join(upgrade_parts))
        else:
            self._emit_heartbeat(round_num, total, "UPGRADE", "无专家升级")

        elapsed = time.time()
        self._emit_heartbeat(round_num, total, "COMPLETE", f"Round {round_num} done")

        return RoundResult(
            round_num=round_num,
            discussion_file=discussion,
            book_title=book_title,
            score_result=score_result,
            expert_upgrades=upgrades,
        )

    def _prepare_material_topics(self, total_rounds: int) -> List[Dict]:
        """预先生成话题计划（基于已有素材 + 专家信念差异）"""
        topics = []

        # 获取已有 V8 文件的书名
        v8_files = sorted(glob.glob(os.path.join(self.content_dir, '*_v8.json')))
        book_names = []
        for f in v8_files:
            name = os.path.basename(f).replace('_v8.json', '').replace('_V8.json', '')
            book_names.append(name)

        if not book_names:
            return topics

        # 获取已有素材的书名
        available_materials = self.material_reader.list_available()

        # 交替：奇数轮=有素材的书，偶数轮=专家信念差异
        for i in range(total_rounds):
            if i % 2 == 0:
                # 优先选有素材的书
                book = book_names[i % len(book_names)]
                has_material = book in available_materials
                topics.append({
                    'type': 'book',
                    'keyword': book,
                    'has_material': has_material,
                })
            else:
                # 通用模式：从专家信念差异获取关键词
                expert_topics = generate_topics(self.library_dir, 1)
                if expert_topics:
                    kw = expert_topics[0].get('topic', '')[:30]
                    topics.append({'type': 'topic', 'keyword': kw})
                else:
                    topics.append({'type': 'topic', 'keyword': book_names[0] if book_names else '投资'})

        return topics

    def _try_build_topic_from_material(self, round_num: int, total: int,
                                        material_topics: List[Dict]) -> Optional[str]:
        """尝试从本地素材构建话题（不进行网络请求）"""
        idx = (round_num - 1) % len(material_topics) if material_topics else 0
        if idx >= len(material_topics):
            return None

        topic_info = material_topics[idx]
        keyword = topic_info['keyword']

        # 检查是否有本地素材
        if not self.material_reader.exists(keyword):
            self._emit_heartbeat(round_num, total, "NO_MATERIAL",
                                 f"{keyword[:30]} — 无素材，用已有V8")
            return None

        self._emit_heartbeat(round_num, total, "MATERIAL", f"{keyword[:30]}")

        try:
            # 从素材构建话题
            material_path = self.material_reader._find_material(keyword)
            if material_path:
                built_topics = build_topics_from_material(
                    material_path, self.library_dir, count=1
                )
                if built_topics:
                    topic_text = built_topics[0]['topic']
                    self._emit_heartbeat(round_num, total, "TOPIC",
                                         topic_text[:50])
                    return topic_text
        except Exception as e:
            self._emit_heartbeat(round_num, total, "TOPIC_ERR", str(e)[:50])

        return None

    def _select_discussion_file(self, round_num: int, mode: str,
                                 json_path: str = None,
                                 expert_name: str = None) -> Optional[str]:
        """选择讨论文件。"""
        if mode == 'human':
            return json_path

        if mode == 'auto':
            v8_files = sorted(glob.glob(os.path.join(self.content_dir, '*_v8.json')))
            if not v8_files:
                return None
            idx = (round_num - 1) % len(v8_files)
            return v8_files[idx]

        if mode == 'replay':
            v8_files = sorted(glob.glob(os.path.join(self.content_dir, '*_v8.json')))
            # 找包含目标专家的文件
            matching = []
            for f in v8_files:
                try:
                    with open(f, 'r', encoding='utf-8-sig') as fh:
                        d = json.load(fh)
                    names = [e['name'] for e in d.get('experts', [])]
                    if expert_name in names:
                        matching.append(f)
                except Exception:
                    continue
            if not matching:
                return v8_files[0] if v8_files else None
            idx = (round_num - 1) % len(matching)
            return matching[idx]

        return None

    # ─── 输出格式 ─────────────────────────────────────────

    def _emit_header(self, rounds: int, mode: str):
        """输出训练头信息。"""
        print(f"\n{'='*60}")
        print(f"  圆桌会议训练引擎")
        print(f"  模式: {mode} | 轮次: {rounds} | 目标: {self.target_score}")
        print(f"{'='*60}\n")

    def _emit_heartbeat(self, round_num: int, total: int, phase: str, detail: str = ''):
        """输出心跳行。"""
        tag = f"[{round_num}/{total}]"
        phase_str = f"{phase:<10}"
        line = f"  {tag} {phase_str}"
        if detail:
            line += f" {detail}"
        print(line)

    def _emit_round_summary(self, round_num: int, total: int, result: RoundResult):
        """输出轮次总结。"""
        dims = result.score_result.get('dimensions', {})
        score_total = result.score_result.get('total', 0)
        grade = result.score_result.get('grade', 'F')

        print(f"\n  {'─'*56}")
        print(f"  ROUND {round_num}/{total} SUMMARY")
        print(f"  {'─'*56}")
        print(f"  Discussion: {os.path.basename(result.discussion_file)}")
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

        # 专家升级
        if result.expert_upgrades:
            print()
            print(f"  Expert Upgrades:")
            for name, info in result.expert_upgrades.items():
                old_v = info.get('old_version', 0)
                new_v = info.get('new_version', 0)
                sp = info.get('speech_count', 0)
                atk = info.get('attack_count', 0)
                print(f"    {name:<12} V{old_v}→V{new_v}  ({sp} speeches, {atk} attacks)")

        print(f"  {'─'*56}\n")

    def _emit_final_summary(self, summary: FinalSummary):
        """输出最终总结。"""
        print(f"\n{'='*60}")
        print(f"  TRAINING COMPLETE")
        print(f"{'='*60}")
        print(f"  Mode: {summary.mode} | Rounds: {summary.total_rounds} | Duration: {summary.duration_seconds:.1f}s")
        print(f"  Target: {summary.target_score} | Reached: {'YES' if summary.target_reached else 'NO'}")

        # 分数趋势
        if summary.score_progression:
            print()
            print(f"  SCORE PROGRESSION")
            max_score = max(summary.score_progression) if summary.score_progression else 100
            for i, s in enumerate(summary.score_progression, 1):
                bar_len = int(s / max_score * 30) if max_score > 0 else 0
                bar = '\u2588' * bar_len + '\u2591' * (30 - bar_len)
                print(f"  Round {i}: {s:>5.1f}  {bar}")
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

        # 专家进化
        if summary.experts_upgraded:
            print()
            print(f"  EXPERT EVOLUTION")
            for name, info in sorted(summary.experts_upgraded.items()):
                first_v = info.get('first_version', 1)
                last_v = info.get('last_version', 1)
                trained_rounds = info.get('rounds', [])
                v_str = f"V{first_v}→V{last_v}"
                r_str = ','.join(str(r) for r in trained_rounds)
                print(f"    {name:<12} {v_str}  (rounds: {r_str})")

        print(f"\n{'='*60}\n")

    def _format_dims_short(self, dims: Dict) -> str:
        """格式化维度分数为简短字符串。"""
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
        """构建最终总结。"""
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

        # 专家进化
        for r in all_rounds:
            for name, info in r.expert_upgrades.items():
                if name not in summary.experts_upgraded:
                    summary.experts_upgraded[name] = {
                        'first_version': info.get('old_version', 1),
                        'last_version': info.get('new_version', 1),
                        'rounds': [],
                        'final_score': 0,
                    }
                entry = summary.experts_upgraded[name]
                entry['last_version'] = info.get('new_version', entry['last_version'])
                entry['rounds'].append(r.round_num)
                entry['final_score'] = r.score_result.get('total', 0)

        # 是否达标
        if summary.score_progression:
            summary.target_reached = max(summary.score_progression) >= self.target_score

        return summary

    def _save_log(self, all_rounds: List[RoundResult], summary: FinalSummary):
        """保存训练日志。"""
        log = {
            'start_time': all_rounds[0].timestamp if all_rounds else '',
            'end_time': datetime.now().isoformat(),
            'mode': summary.mode,
            'total_rounds': summary.total_rounds,
            'target_score': summary.target_score,
            'target_reached': summary.target_reached,
            'duration_seconds': summary.duration_seconds,
            'score_progression': summary.score_progression,
            'rounds': [
                {
                    'round': r.round_num,
                    'discussion': os.path.basename(r.discussion_file),
                    'book_title': r.book_title,
                    'score': r.score_result.get('total', 0),
                    'grade': r.score_result.get('grade', 'F'),
                    'expert_upgrades': {
                        name: {
                            'old_version': info.get('old_version', 0),
                            'new_version': info.get('new_version', 0),
                        }
                        for name, info in r.expert_upgrades.items()
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
    parser = argparse.ArgumentParser(description='圆桌会议多轮训练编排器')
    parser.add_argument('--rounds', type=int, default=3, help='训练轮次')
    parser.add_argument('--mode', choices=['auto', 'human', 'replay'], default='auto',
                        help='训练模式')
    parser.add_argument('--json', help='讨论 JSON 路径（human 模式）')
    parser.add_argument('--library', default='expert-library', help='专家库目录')
    parser.add_argument('--content', default='content', help='讨论内容目录')
    parser.add_argument('--expert', help='目标专家名（replay 模式）')
    parser.add_argument('--target-score', type=float, default=85.0, help='目标分数')
    parser.add_argument('--log-dir', default='memory', help='日志目录')
    parser.add_argument('--use-material', action='store_true',
                        help='使用本地素材构建话题（需先用 SKILL Phase 0 采风）')

    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    orchestrator = TrainingOrchestrator(
        library_dir=args.library,
        content_dir=args.content,
        log_dir=args.log_dir,
        target_score=args.target_score,
        use_material=args.use_material,
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
