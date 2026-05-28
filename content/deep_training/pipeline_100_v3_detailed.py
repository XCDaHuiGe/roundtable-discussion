# -*- coding: utf-8 -*-
"""Pipeline for rounds 231-330 with per-round detail + 20-round summary."""
import sys, os, glob, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'engine', 'training'))
from extractor import extract
from evolution_engine import EvolutionEngine

training_dir = os.path.dirname(__file__)
library_dir = os.path.join(training_dir, '..', '..', 'expert-library')
engine = EvolutionEngine(library_dir)

# Find rounds 231-330
all_files = glob.glob(os.path.join(training_dir, 'round2*.json')) + glob.glob(os.path.join(training_dir, 'round3*.json'))
new_files = []
for f in all_files:
    try:
        rn = int(os.path.basename(f).replace('round','').split('_')[0])
        if 231 <= rn <= 330:
            new_files.append(f)
    except: pass
new_files.sort(key=lambda f: int(os.path.basename(f).replace('round','').split('_')[0]))

print(f"Found {len(new_files)} rounds (231-330)\n")

all_upgrades = {}
processed = failed = 0

for idx, fpath in enumerate(new_files):
    try:
        ext_result = extract(fpath)
    except Exception as e:
        failed += 1
        print(f"  [{os.path.basename(fpath).split('_')[0].replace('round','')}] FAIL: {str(e)[:60]}")
        continue
    processed += 1
    
    for expert_name, expert_data in ext_result.get('experts', {}).items():
        strategy = {
            'attack_strategy': expert_data.get('attack_strategy', {}),
            'defense_weakness': expert_data.get('defense_weakness', {}),
            'style_fingerprint': expert_data.get('style_fingerprint', {}),
            'evidence_preference': expert_data.get('evidence_preference', {}),
            'interaction_pattern': expert_data.get('interaction_pattern', {}),
        }
        try:
            evo_result = engine.evolve(expert_name, strategy, topic=os.path.basename(fpath), score=65.0)
            if evo_result:
                if expert_name not in all_upgrades:
                    all_upgrades[expert_name] = {'merges': 0, 'repl': 0, 'old_v': [], 'new_v': 0, 'count': 0}
                all_upgrades[expert_name]['count'] += 1
                all_upgrades[expert_name]['old_v'].append(evo_result.old_version)
                if evo_result.strategy_merges or evo_result.material_replacements:
                    all_upgrades[expert_name]['merges'] += len(evo_result.strategy_merges)
                    all_upgrades[expert_name]['repl'] += len(evo_result.material_replacements)
                    all_upgrades[expert_name]['new_v'] = evo_result.new_version
        except: pass
    
    if (idx + 1) % 20 == 0:
        print(f"  [{idx+1}/{len(new_files)}] ...")

print(f"\n{'='*60}")
print(f"  RESULT: {processed} processed, {failed} failed")
print(f"{'='*60}")
print(f"  Experts: {len(all_upgrades)}")
total_m = sum(v['merges'] for v in all_upgrades.values())
total_r = sum(v['repl'] for v in all_upgrades.values())
print(f"  Merges: {total_m}, Repl: {total_r}")

print(f"\n{'─'*70}")
print(f"  {'Expert':<16} {'Rounds':<8} {'Jump':<14} {'Merges':<8} {'Repl':<8} {'Rate':<8}")
print(f"{'─'*70}")
for name, v in sorted(all_upgrades.items(), key=lambda x: -x[1]['merges']):
    old_vs = v['old_v']
    mn = min(old_vs)
    jump = v['new_v'] - mn if v['new_v'] > 0 else 0
    v_str = f"V{mn}->V{v['new_v']}" if jump > 0 else f"V{mn}"
    rate = f"{v['merges']/max(v['count'],1):.1f}/轮"
    print(f"  {name:<14} {v['count']:<8} {v_str:<14} {v['merges']:<8} {v['repl']:<8} {rate:<8}")

# ─── 评价 ───
print(f"\n{'='*60}")
print(f"  评价")
print(f"{'='*60}")

print(f"\n  最佳提升 (Top 5 融合量):")
for n, v in sorted(all_upgrades.items(), key=lambda x: -x[1]['merges'])[:5]:
    mn = min(v['old_v'])
    print(f"    {n}: V{mn}->V{v['new_v']}, +{v['merges']}策略/{v['repl']}素材, {v['count']}轮")

stagnant = [(n, v) for n, v in all_upgrades.items() if v['merges'] == 0]
if stagnant:
    print(f"\n  零提升 ({len(stagnant)}人):")
    for n, v in stagnant:
        print(f"    {n}: V{v['old_v'][0]}, {v['count']}轮不变")

print(f"\n  版本跨度 (旧→新):")
rising = [(n, v) for n, v in all_upgrades.items() if v['new_v'] > min(v['old_v'])]
for n, v in sorted(rising, key=lambda x: min(x[1]['old_v'])):
    mn = min(v['old_v'])
    jump_v = v['new_v'] - mn
    bar = '█' * max(1, jump_v)
    if jump_v > 0:
        print(f"    {n:<14}: V{mn:<2}->V{v['new_v']:<2} +{jump_v} {bar}")
