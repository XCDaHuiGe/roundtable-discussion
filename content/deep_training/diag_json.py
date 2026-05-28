# -*- coding: utf-8 -*-
"""Diagnose JSON error in a specific file."""
import json

f = 'content/deep_training/round021_丹尼尔·戈尔曼_弗洛姆.json'
raw = open(f, 'r', encoding='utf-8-sig').read()

try:
    json.loads(raw)
    print("File is valid!")
except json.JSONDecodeError as e:
    print(f"Error at line {e.lineno}, col {e.colno}, pos {e.pos}")
    # Show surrounding context
    start = max(0, e.pos - 30)
    end = min(len(raw), e.pos + 30)
    ctx = raw[start:end]
    print(f"Context: ...{ctx}...")
    
    # Check for problematic characters
    for ch in ['"', "'", '\n', '\t', '\\']:
        if ch in ctx:
            idx = ctx.index(ch)
            print(f"  Found '{ch}' at offset {start + idx} in context")
    
    lines = raw.split('\n')
    lineno = e.lineno - 1
    if lineno < len(lines):
        print(f"\nLine {e.lineno}:")
        print(f"  {lines[lineno][:200]}")
