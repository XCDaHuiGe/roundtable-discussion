# -*- coding: utf-8 -*-
"""Process 20 new rounds (111-130) with per-round detailed feedback."""
import sys, os, glob, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'engine', 'training'))
from extractor import extract
from evolution_engine import EvolutionEngine

training_dir = os.path.dirname(__file__)
library_dir = os.path.join(training_dir, '..', '..', 'expert-library')
engine = EvolutionEngine(library_dir)

# Get the new rounds (111-130) sorted
all_files = sorted(glob.glob(os.path.join(training_dir, 'round1*.json')))
# Filter rounds > 110
new_files = [f for f in all_files if int(os.path.basename(f).replace('round','').split('_')[0]) >= 111]
new_files = sorted(new_files, key=lambda f: int(os.path.basename(f).replace('round','').split('_')[0]))

print(f"{'='*60}")
print(f"  20 轮深度训练 —— 详细反馈报告")
print(f"{'='*60}\n")

all_upgrades = {}
processed = 0
failed = 0

for fpath in new_files:
    fname = os.path.basename(fpath)
    try:
        ext_result = extract(fpath)
    except Exception as e:
        print(f"  [FAIL] {fname}: extract error - {e}")
        failed += 1
        continue

    processed += 1
    round_name = ext_result.get('title', fname)[:50]
    
    print(f"\n{'─'*50}")
    print(f"  Round: {round_name}")
    print(f"{'─'*50}")
    
    for expert_name, expert_data in ext_result.get('experts', {}).items():
        strategy = {
            'attack_strategy': expert_data.get('attack_strategy', {}),
            'defense_weakness': expert_data.get('defense_weakness', {}),
            'style_fingerprint': expert_data.get('style_fingerprint', {}),
            'evidence_preference': expert_data.get('evidence_preference', {}),
            'interaction_pattern': expert_data.get('interaction_pattern', {}),
        }
        try:
            evo_result = engine.evolve(expert_name, strategy, topic=fname, score=65.0)
            if evo_result:
                if expert_name not in all_upgrades:
                    all_upgrades[expert_name] = {'merges': 0, 'repl': 0, 'old_v': evo_result.old_version, 'new_v': evo_result.new_version, 'count': 0}
                all_upgrades[expert_name]['count'] += 1
                all_upgrades[expert_name]['new_v'] = evo_result.new_version
                if evo_result.strategy_merges or evo_result.material_replacements:
                    all_upgrades[expert_name]['merges'] += len(evo_result.strategy_merges)
                    all_upgrades[expert_name]['repl'] += len(evo_result.material_replacements)
                    print(f"    [{expert_name}] V{evo_result.old_version} -> V{evo_result.new_version}")
                    for m in evo_result.strategy_merges:
                        print(f"      + {m[:50]}")
                    for r in evo_result.material_replacements:
                        print(f"      ~ {r[:50]}")
                else:
                    print(f"    [{expert_name}] 无变化 (V{evo_result.old_version})")
        except Exception as e:
            print(f"    [{expert_name}] evolve error: {e}")

print(f"\n{'='*60}")
print(f"  总结")
print(f"{'='*60}")
print(f"\nProcessed: {processed}, Failed: {failed}")
print(f"Experts upgraded: {len(all_upgrades)}")
total_m = sum(v['merges'] for v in all_upgrades.values())
total_r = sum(v['repl'] for v in all_upgrades.values())
print(f"Total strategy merges: {total_m}")
print(f"Total material replacements: {total_r}")

print(f"\n{'─'*60}")
print(f"  {'Expert':<16} {'Rounds':<8} {'V':<12} {'Merges':<8} {'Repl':<8}")
print(f"{'─'*60}")
for name, v in sorted(all_upgrades.items(), key=lambda x: -x[1]['merges']):
    v_str = f"V{v['old_v']}->V{v['new_v']}"
    print(f"  {name:<14} {v['count']:<8} {v_str:<12} {v['merges']:<8} {v['repl']:<8}")

# Overall evaluation
print(f"\n{'='*60}")
print(f"  评价")
print(f"{'='*60}")

upgraded = [n for n, v in all_upgrades.items() if v['merges'] > 0]
print(f"\n  获得升级的专家 ({len(upgraded)}人):")
for n in upgraded:
    v = all_upgrades[n]
    print(f"    {n} (V{v['old_v']}->V{v['new_v']}, +{v['merges']}策略/{v['repl']}素材)")

stagnant = [n for n, v in all_upgrades.items() if v['merges'] == 0]
if stagnant:
    print(f"\n  未获得升级的专家 ({len(stagnant)}人):")
    for n in stagnant:
        v = all_upgrades[n]
        print(f"    {n} (V{v['old_v']}, {v['count']}轮训练)")
