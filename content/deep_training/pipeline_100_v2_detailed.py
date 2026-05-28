# -*- coding: utf-8 -*-
"""Pipeline for rounds 131-230 with per-round detailed feedback, 20-round progress."""
import sys, os, glob, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'engine', 'training'))
from extractor import extract
from evolution_engine import EvolutionEngine

training_dir = os.path.dirname(__file__)
library_dir = os.path.join(training_dir, '..', '..', 'expert-library')
engine = EvolutionEngine(library_dir)

# Get rounds 131-230 only
all_files = sorted(glob.glob(os.path.join(training_dir, 'round1*.json')) + glob.glob(os.path.join(training_dir, 'round2*.json')))
new_files = []
for f in all_files:
    try:
        rn = int(os.path.basename(f).replace('round','').split('_')[0])
        if 131 <= rn <= 230:
            new_files.append(f)
    except:
        pass
new_files = sorted(new_files, key=lambda f: int(os.path.basename(f).replace('round','').split('_')[0]))

print(f"Found {len(new_files)} rounds (131-230)\n")

all_upgrades = {}
processed = 0
failed = 0
total_files = len(new_files)

for idx, fpath in enumerate(new_files):
    fname = os.path.basename(fpath)
    
    try:
        ext_result = extract(fpath)
    except Exception as e:
        failed += 1
        rn = os.path.basename(fpath).split('_')[0].replace('round','')
        print(f"  [{rn}] FAIL extract: {str(e)[:60]}")
        continue

    processed += 1
    rn = ext_result.get('title', fname)[:5].replace('Round ','')
    
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
                    all_upgrades[expert_name] = {'merges': 0, 'repl': 0, 'old_v': [], 'new_v': 0, 'count': 0}
                all_upgrades[expert_name]['count'] += 1
                all_upgrades[expert_name]['old_v'].append(evo_result.old_version)
                if evo_result.strategy_merges or evo_result.material_replacements:
                    all_upgrades[expert_name]['merges'] += len(evo_result.strategy_merges)
                    all_upgrades[expert_name]['repl'] += len(evo_result.material_replacements)
                    all_upgrades[expert_name]['new_v'] = evo_result.new_version
        except:
            pass
    
    # Progress every 20
    if (idx + 1) % 20 == 0:
        print(f"  [{idx+1}/{total_files}] Processed 20...")

print(f"\n{'='*60}")
print(f"  RESULT: {processed} processed, {failed} failed")
print(f"{'='*60}")

total_m = sum(v['merges'] for v in all_upgrades.values())
total_r = sum(v['repl'] for v in all_upgrades.values())
print(f"  Upgraded: {len(all_upgrades)} experts")
print(f"  Merges: {total_m}, Replacements: {total_r}")

print(f"\n{'─'*70}")
print(f"  {'Expert':<16} {'Rounds':<8} {'Version':<14} {'Merges':<8} {'Repl':<8}")
print(f"{'─'*70}")
for name, v in sorted(all_upgrades.items(), key=lambda x: -x[1]['merges']):
    old_vs = v['old_v']
    v_str = f"V{min(old_vs)}->V{v['new_v']}" if v['new_v'] != min(old_vs) else f"V{min(old_vs)}"
    print(f"  {name:<14} {v['count']:<8} {v_str:<14} {v['merges']:<8} {v['repl']:<8}")

# ─── Evaluation ───
print(f"\n{'='*60}")
print(f"  评价")
print(f"{'='*60}")

top = sorted(all_upgrades.items(), key=lambda x: -x[1]['merges'])[:5]
print(f"\n  最佳提升 (Top 5):")
for n, v in top:
    old_vs = v['old_v']
    v_str = f"V{min(old_vs)} -> V{v['new_v']}"
    print(f"    {n}: {v_str}, +{v['merges']}策略/{v['repl']}素材, {v['count']}轮")

stagnant = [(n, v) for n, v in all_upgrades.items() if v['merges'] == 0]
if stagnant:
    print(f"\n  零提升 ({len(stagnant)}人):")
    for n, v in stagnant:
        print(f"    {n}: V{v['old_v'][0]}, {v['count']}轮训练无变化")

print(f"\n{'─'*60}")
print(f"  Score gap (旧版本 -> 新版本):")
rising = [(n, v) for n, v in all_upgrades.items() if v['merges'] > 0]
for n, v in sorted(rising, key=lambda x: min(x[1]['old_v'])):
    old_min = min(v['old_v'])
    delta = v['new_v'] - old_min
    print(f"    {n:<14}: V{old_min} -> V{v['new_v']} (+{delta})")
