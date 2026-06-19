# -*- coding: utf-8 -*-
"""
一键训练脚本 - 最简单的训练入口

用法：
    python train.py              # 默认训练5轮
    python train.py 10           # 训练10轮
    python train.py 100          # 训练100轮（持续学习）
    python train.py --quick      # 快速训练3轮（使用现有讨论）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.training.orchestrator import TrainingOrchestrator


def main():
    rounds = 5
    quick_mode = False
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--quick':
            rounds = 3
            quick_mode = True
        elif arg.isdigit():
            rounds = int(arg)
    
    print("\n" + "="*50)
    print("  圆桌会议一键训练")
    print("  轮次: {} | 模式: {}".format(rounds, "快速" if quick_mode else "持续学习"))
    print("="*50 + "\n")
    
    orchestrator = TrainingOrchestrator(
        library_dir='expert-library',
        content_dir='content',
        log_dir='memory',
        target_score=100.0,
        engine_version='v3',
    )
    
    mode = 'auto' if quick_mode else 'evolution'
    
    summary = orchestrator.run(
        rounds=rounds,
        mode=mode,
    )
    
    print("\n训练完成！")
    print("  总轮次: {}".format(summary.total_rounds))
    print("  最高分数: {:.1f}".format(max(summary.score_progression) if summary.score_progression else 0))
    print("  策略融合: {}".format(summary.total_strategy_merges))
    print("  素材替换: {}".format(summary.total_material_replacements))
    print("  日志: memory/training_*.json")


if __name__ == '__main__':
    main()