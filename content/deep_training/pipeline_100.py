# -*- coding: utf-8 -*-
"""Process all round files through extraction + evolution pipeline."""
import sys, os, glob, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'engine', 'training'))
from extractor import extract
from evolution_engine import EvolutionEngine

training_dir = os.path.dirname(__file__)
library_dir = os.path.join(training_dir, '..', '..', 'expert-library')
engine = EvolutionEngine(library_dir)

files = sorted(glob.glob(os.path.join(training_dir, 'round*.json')))
print(f"Found {len(files)} round files")

all_upgrades = {}
processed = 0
failed = 0

for fpath in files:
    fname = os.path.basename(fpath)
    try:
        ext_result = extract(fpath)
    except Exception as e:
        failed += 1
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
            evo_result = engine.evolve(expert_name, strategy, topic=fname, score=65.0)
            if evo_result:
                if expert_name not in all_upgrades:
                    all_upgrades[expert_name] = {'merges': 0, 'repl': 0, 'old_v': evo_result.old_version, 'new_v': evo_result.new_version, 'count': 0}
                all_upgrades[expert_name]['merges'] += len(evo_result.strategy_merges)
                all_upgrades[expert_name]['repl'] += len(evo_result.material_replacements)
                all_upgrades[expert_name]['new_v'] = evo_result.new_version
                all_upgrades[expert_name]['count'] += 1
        except:
            pass
    
    if processed % 20 == 0:
        print(f"  Processed {processed}/{len(files)}...")

print(f"\nProcessed: {processed}, Failed: {failed}")
print(f"Upgraded experts: {len(all_upgrades)}")
total_m = sum(v['merges'] for v in all_upgrades.values())
total_r = sum(v['repl'] for v in all_upgrades.values())
print(f"Total merges: {total_m}, Total replacements: {total_r}")

print(f"\n{'Expert':<16} {'Rounds':<8} {'V':<10} {'Merges':<8} {'Repl':<8}")
for name, v in sorted(all_upgrades.items(), key=lambda x: -x[1]['merges']):
    print(f"  {name:<14} {v['count']:<8} V{v['old_v']}->V{v['new_v']:<3} {v['merges']:<8} {v['repl']:<8}")
