# -*- coding: utf-8 -*-
"""Process batch1 only (R111-R115) with detailed feedback."""
import sys, os, glob, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'engine', 'training'))
from extractor import extract
from evolution_engine import EvolutionEngine

training_dir = os.path.dirname(__file__)
library_dir = os.path.join(training_dir, '..', '..', 'expert-library')
engine = EvolutionEngine(library_dir)

all_files = sorted(glob.glob(os.path.join(training_dir, 'round1*.json')))
new_files = [f for f in all_files if 111 <= int(os.path.basename(f).replace('round','').split('_')[0]) <= 115]
new_files = sorted(new_files, key=lambda f: int(os.path.basename(f).replace('round','').split('_')[0]))

print("Processing batch1 (R111-R115)...\n")

all_upgrades = {}
for fpath in new_files:
    fname = os.path.basename(fpath)
    ext_result = extract(fpath)
    round_name = ext_result.get('title', fname)[:50]
    print(f"--- {round_name} ---")
    
    for expert_name, expert_data in ext_result.get('experts', {}).items():
        strategy = {
            'attack_strategy': expert_data.get('attack_strategy', {}),
            'defense_weakness': expert_data.get('defense_weakness', {}),
            'style_fingerprint': expert_data.get('style_fingerprint', {}),
            'evidence_preference': expert_data.get('evidence_preference', {}),
            'interaction_pattern': expert_data.get('interaction_pattern', {}),
        }
        evo_result = engine.evolve(expert_name, strategy, topic=fname, score=65.0)
        if evo_result:
            if expert_name not in all_upgrades:
                all_upgrades[expert_name] = {'merges': 0, 'repl': 0, 'old_v': evo_result.old_version, 'new_v': evo_result.new_version, 'count': 0}
            all_upgrades[expert_name]['count'] += 1
            all_upgrades[expert_name]['new_v'] = evo_result.new_version
            if evo_result.strategy_merges or evo_result.material_replacements:
                all_upgrades[expert_name]['merges'] += len(evo_result.strategy_merges)
                all_upgrades[expert_name]['repl'] += len(evo_result.material_replacements)
                print(f"  [{expert_name}] V{evo_result.old_version}->V{evo_result.new_version}")
                for m in evo_result.strategy_merges:
                    print(f"    + {m[:50]}")
                for r in evo_result.material_replacements:
                    print(f"    ~ {r[:50]}")
            else:
                print(f"  [{expert_name}] 无变化 (V{evo_result.old_version})")

print(f"\nBatch1 done. Upgrades:")
for n, v in sorted(all_upgrades.items(), key=lambda x: -x[1]['merges']):
    print(f"  {n}: V{v['old_v']}->V{v['new_v']}, +{v['merges']}策略/{v['repl']}素材")
