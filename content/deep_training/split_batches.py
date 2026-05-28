# -*- coding: utf-8 -*-
"""Split 100 rounds into 5 batches of 20 and show expert coverage per batch."""
import sys, os, json

with open(os.path.join(os.path.dirname(__file__), '100_rounds_plan.json'), 'r', encoding='utf-8') as f:
    plan = json.load(f)

batch_size = 20
for batch_idx in range(5):
    start = batch_idx * batch_size
    end = start + batch_size
    batch = plan[start:end]
    
    experts_needed = set()
    for r in batch:
        experts_needed.add(r['expert1'])
        experts_needed.add(r['expert2'])
    
    experts_sorted = sorted(experts_needed)
    
    out = os.path.join(os.path.dirname(__file__), f'batch{batch_idx+1}.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    
    print(f"Batch {batch_idx+1}: rounds {start+1}-{end}, {len(experts_needed)} unique experts")
    print(f"  Experts: {', '.join(experts_sorted[:8])}{'...' if len(experts_sorted) > 8 else ''}")
    print()
