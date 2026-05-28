# -*- coding: utf-8 -*-
"""Process all 10 debate JSONs through extraction + evolution pipeline."""
import sys, os, json, glob, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'engine', 'training'))

from extractor import extract
from evolution_engine import EvolutionEngine
from tracker import TrainingTracker

training_dir = os.path.join(os.path.dirname(__file__))
library_dir = os.path.join(training_dir, '..', '..', 'expert-library')
log_dir = os.path.join(training_dir, '..', '..', 'memory')

engine = EvolutionEngine(library_dir)
tracker = TrainingTracker(library_dir, log_dir)

files = sorted(glob.glob(os.path.join(training_dir, 'round*.json')))
print(f"\n{'='*60}")
print(f"  深度训练管道: {len(files)} 轮辩论")
print(f"{'='*60}\n")

all_expert_upgrades = {}
all_scores = []

for fpath in files:
    fname = os.path.basename(fpath)
    print(f"\n  [{fname}]")
    
    # Step 1: Extract strategies
    try:
        ext_result = extract(fpath)
    except Exception as e:
        print(f"    EXTRACT FAILED: {e}")
        continue
    
    book_title = ext_result.get('book_title', fname)
    print(f"    Book: {book_title}")
    print(f"    Experts analyzed: {len(ext_result.get('experts', {}))}")
    
    # Step 2: Evolve each expert
    for expert_name, expert_data in ext_result.get('experts', {}).items():
        strategy = {
            'attack_strategy': expert_data.get('attack_strategy', {}),
            'defense_weakness': expert_data.get('defense_weakness', {}),
            'style_fingerprint': expert_data.get('style_fingerprint', {}),
            'evidence_preference': expert_data.get('evidence_preference', {}),
            'interaction_pattern': expert_data.get('interaction_pattern', {}),
        }
        
        try:
            evo_result = engine.evolve(
                expert_name, strategy,
                topic=book_title,
                score=65.0,
                attack_eff=0.8,
                defense_rate=0.6,
            )
            if evo_result:
                expert_key = f"{expert_name}"
                if expert_key not in all_expert_upgrades:
                    all_expert_upgrades[expert_key] = []
                all_expert_upgrades[expert_key].append({
                    'old_version': evo_result.old_version,
                    'new_version': evo_result.new_version,
                    'strategy_merges': len(evo_result.strategy_merges),
                    'material_replacements': len(evo_result.material_replacements),
                    'density_delta': evo_result.density_delta,
                })
                delta = evo_result.density_delta
                print(f"    {expert_name}: V{evo_result.old_version}->V{evo_result.new_version} "
                      f"(merges:{len(evo_result.strategy_merges)}, "
                      f"repl:{len(evo_result.material_replacements)}, "
                      f"density:{delta:+.1f}%)")
        except Exception as e:
            print(f"    {expert_name} EVOLVE FAILED: {e}")

# Summary
print(f"\n{'='*60}")
print(f"  训练完成汇总")
print(f"{'='*60}")
print(f"  总辩论数: {len(files)}")
print(f"  升级专家数: {len(all_expert_upgrades)}")
total_merges = sum(sum(u['strategy_merges'] for u in upgrades) for upgrades in all_expert_upgrades.values())
total_repl = sum(sum(u['material_replacements'] for u in upgrades) for upgrades in all_expert_upgrades.values())
print(f"  策略融合: {total_merges}")
print(f"  素材替换: {total_repl}")

print(f"\n  专家升级详情:")
for name, upgrades in sorted(all_expert_upgrades.items()):
    first_v = upgrades[0]['old_version']
    last_v = upgrades[-1]['new_version']
    m = sum(u['strategy_merges'] for u in upgrades)
    r = sum(u['material_replacements'] for u in upgrades)
    d = sum(u['density_delta'] for u in upgrades)
    print(f"    {name}: V{first_v}->V{last_v} ({m} merges, {r} repl, density {d:+.1f}%)")
