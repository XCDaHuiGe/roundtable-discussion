# -*- coding: utf-8 -*-
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = os.path.dirname(__file__)
for bidx in range(1, 6):
    path = os.path.join(base, f'batch{bidx}.json')
    data = json.load(open(path, 'r', encoding='utf-8'))
    experts = set()
    for r in data:
        experts.add(r['expert1'])
        experts.add(r['expert2'])
    
    pairs = [(r['expert1'], r['expert2'], r['strength']) for r in data[:5]]
    print(f'\nBatch {bidx}: ({len(data)} rounds, {len(experts)} experts)')
    for e1, e2, s in pairs:
        print(f'  {e1} vs {e2} [{s}]')
    print(f'  ... +{len(data)-5} more')
    print(f'  Experts: {", ".join(sorted(experts)[:6])}...')
