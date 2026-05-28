# -*- coding: utf-8 -*-
"""Fix round 113 key typo and verify plan."""
import json

with open('content/deep_training/20_rounds_plan.json', 'r', encoding='utf-8') as f:
    plan = json.load(f)

# Fix round 113: dreams2 -> belief2
r113 = plan[2]
if 'dreams2' in r113:
    r113['belief2'] = r113.pop('dreams2')
    print(f"Fixed round 113: dreams2 -> belief2")

# Verify all
for r in plan:
    assert 'belief1' in r, f"Round {r['round']} missing belief1"
    assert 'belief2' in r, f"Round {r['round']} missing belief2"
    print(f"  R{r['round']:3d} {r['expert1']:10s} vs {r['expert2']:10s} OK")

# Re-save fixed version
with open('content/deep_training/20_rounds_plan.json', 'w', encoding='utf-8') as f:
    json.dump(plan, f, ensure_ascii=False, indent=2)

# Create 4 batches of 5
for i in range(4):
    batch = {
        "batch": i + 1,
        "rounds": plan[i*5:(i+1)*5]
    }
    with open(f'content/deep_training/batch20_{i+1}.json', 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    r = batch['rounds']
    print(f"\n  Batch {batch['batch']}: R{r[0]['round']}-R{r[-1]['round']} saved")

print("\n✅ Ready! 20 rounds, 4 batches of 5.")
