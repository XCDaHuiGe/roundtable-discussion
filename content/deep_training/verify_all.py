# -*- coding: utf-8 -*-
import json, glob, os

# Check round095_塔勒布
f1 = 'content/deep_training/round095_尼克·博斯特罗姆_塔勒布.json'
d = json.loads(open(f1, 'r', encoding='utf-8-sig').read())
print(f"round095_塔勒布: title={d['title']}, rounds={len(d['rounds'])}")

# Plan says round095 should be 博斯特罗姆 vs 津巴多
# Let's just rename the file name to match its actual content
# Since this file has 塔勒布, keep the name

# Final check all files
files = sorted(glob.glob('content/deep_training/round*.json'))
good = 0
bad = []
for f in files:
    try:
        d = json.loads(open(f, 'r', encoding='utf-8-sig').read())
        if len(d.get('rounds', [])) >= 4:
            good += 1
        else:
            bad.append((os.path.basename(f), f'only {len(d["rounds"])} rounds'))
    except Exception as e:
        bad.append((os.path.basename(f), str(e)[:80]))

print(f"\nTotal: {len(files)}")
print(f"Valid: {good}")
print(f"Broken: {len(bad)}")
if bad:
    for n, e in bad:
        print(f"  {n}: {e}")
else:
    print("[OK] All files healthy!")
