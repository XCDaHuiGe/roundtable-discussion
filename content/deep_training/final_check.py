# -*- coding: utf-8 -*-
"""Final validation of all 110 round JSONs."""
import json, glob, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = sorted(glob.glob('content/deep_training/round*.json'))
good = 0
bad_files = []
for f in files:
    try:
        d = json.loads(open(f, 'r', encoding='utf-8-sig').read())
        rounds = len(d.get('rounds', []))
        if rounds >= 4:
            good += 1
        else:
            bad_files.append((f.split('\\')[-1], f'only {rounds} rounds'))
    except Exception as e:
        bad_files.append((f.split('\\')[-1], str(e)[:60]))

print(f"Total: {len(files)}")
print(f"Valid: {good}")
print(f"Broken: {len(bad_files)}")
if bad_files:
    print("\nBroken files:")
    for name, err in bad_files:
        print(f"  {name}: {err}")
else:
    print("\n[OK] All 110 files are valid JSON with 4+ rounds!")
    
# Count rounds distribution
expert_rounds = {}
for f in files:
    try:
        d = json.loads(open(f, 'r', encoding='utf-8-sig').read())
        for e in d.get('experts', []):
            name = e.get('name', '')
            if name:
                expert_rounds[name] = expert_rounds.get(name, 0) + 1
    except:
        pass

print(f"\nUnique experts covered: {len(expert_rounds)}")
print(f"Total debates: {len(files)}")
