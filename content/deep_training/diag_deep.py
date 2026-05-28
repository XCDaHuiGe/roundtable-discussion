# -*- coding: utf-8 -*-
"""Deep diagnostic for remaining broken files."""
import json, glob

files = [
    'content/deep_training/round026_塔勒布_罗翔.json',
    'content/deep_training/round092_李诞_许知远.json',
    'content/deep_training/round095_尼克·博斯特罗姆_尼克·博斯特罗姆.json',
]

for path in files:
    try:
        fi = glob.glob(path)
        if not fi:
            fi = [f for f in glob.glob('content/deep_training/round*.json') if '026' in f or '092' in f or '095' in f]
        if not fi:
            print(f"Not found: {path}")
            continue
        path = fi[0]
    except:
        pass
    
    raw = open(path, 'r', encoding='utf-8-sig').read()
    name = path.split('\\')[-1]
    
    err = None
    try:
        json.loads(raw)
        print(f"[OK] {name}")
        continue
    except json.JSONDecodeError as e:
        err = e
        print(f"[ERR] {name}: line {e.lineno}, col {e.colno}, pos {e.pos}")
    
    if err:
        # Show the problematic area in hex
        start = max(0, err.pos - 5)
        end = min(len(raw), err.pos + 15)
        chunk = raw[start:end]
        print(f"  Chars around error: {repr(chunk)}")
        print(f"  Hex: {' '.join(f'{ord(c):04x}' for c in chunk)}")
        
        # Also show the line
        lines = raw.split('\n')
        if err.lineno <= len(lines):
            line = lines[err.lineno - 1]
            print(f"  Line {err.lineno} (full): {repr(line[:200])}")
        print()
