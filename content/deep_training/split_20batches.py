# -*- coding: utf-8 -*-
"""Verify and fix the 20-round plan JSON."""
import json

with open('content/deep_training/20_rounds_plan.json', 'r', encoding='utf-8') as f:
    plan = json.load(f)

for r in plan:
    assert 'belief1' in r, f"Round {r.get('round', '?')} missing belief1"
    assert 'belief2' in r, f"Round {r.get('round', '?')} missing belief2"
    print(f"  Round {r['round']:3d}: {r['expert1']:10s} vs {r['expert2']:10s} ✅")

# Save as 4 batches of 5
batches = []
for i in range(4):
    batch = {
        "batch": i + 1,
        "rounds": plan[i*5:(i+1)*5]
    }
    batches.append(batch)
    with open(f'content/deep_training/batch20_{i+1}.json', 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    print(f"  Batch {batch['batch']}: rounds {batch['rounds'][0]['round']}-{batch['rounds'][-1]['round']} saved")

print("\n✅ All checks passed. Ready to generate.")
