# -*- coding: utf-8 -*-
"""Generate 100-round training plan from belief conflicts."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'engine', 'training'))
from debate_arena import DebateArena

arena = DebateArena(os.path.join(os.path.dirname(__file__), '..', '..', 'expert-library'))
topics = arena.generate_topics(count=100, prefer_strong=True)

data = []
for i, t in enumerate(topics, 1):
    data.append({
        'round': i,
        'expert1': t.expert1,
        'expert2': t.expert2,
        'belief1': t.belief1,
        'belief2': t.belief2,
        'topic': t.topic,
        'conflict_type': t.conflict_type,
        'strength': t.strength,
    })

out = os.path.join(os.path.dirname(__file__), '100_rounds_plan.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total topics: {len(topics)}")
print(f"Strong: {sum(1 for t in topics if t.strength == 'strong')}")
print(f"Moderate: {sum(1 for t in topics if t.strength == 'moderate')}")

expert_counts = {}
for t in topics:
    for e in [t.expert1, t.expert2]:
        expert_counts[e] = expert_counts.get(e, 0) + 1

print("\nTop experts:")
for name, cnt in sorted(expert_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {name}: {cnt}")

print("\nFirst 10 rounds:")
for t in data[:10]:
    print(f"  R{t['round']}: {t['expert1']} vs {t['expert2']} [{t['conflict_type']}]")
