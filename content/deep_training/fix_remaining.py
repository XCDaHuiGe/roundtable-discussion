# -*- coding: utf-8 -*-
"""Manual fix for 3 remaining broken JSON files."""
import glob, json, re

# File 1: round026 - unescaped quotes in text
f1 = glob.glob('content/deep_training/round026_*.json')[0]
raw = open(f1, 'r', encoding='utf-8-sig').read()

# Replace the problematic Chinese double quotes with Chinese-style quotes
fixed = raw[:286] + '\u201c' + raw[287:]  # "真" -> left quote
# Find the closing quote position
pos = raw.find('"', 290)
if pos > 0:
    fixed = fixed[:pos] + '\u201d' + fixed[pos+1:]

# Also find the second pair
pos2 = fixed.find('\u201c', pos+1)
if pos2 > 0:
    pos3 = fixed.find('"', pos2+1)
    if pos3 > 0 and fixed[pos3-1] != '\\':
        # Check if this is a closing quote for Chinese text
        ch = fixed[pos3-1]
        if ord(ch) > 127:
            fixed = fixed[:pos3] + '\u201d' + fixed[pos3+1:]

try:
    json.loads(fixed)
    open(f1, 'w', encoding='utf-8').write(fixed)
    print(f"Fixed: {f1.split(chr(92))[-1]}")
except json.JSONDecodeError as e:
    print(f"Still broken: {f1.split(chr(92))[-1]}: {e.msg}")

# File 2: round092 - check the issue
f2 = glob.glob('content/deep_training/round092_*.json')[0]
raw = open(f2, 'r', encoding='utf-8-sig').read()
# Line 39 issue - might be a single quote used as string delimiter
fixed2 = raw.replace("'", "\u2019")  # Replace ASCII single quotes with typographic
fixed2 = fixed2.replace('\u2019\u2019', "''")  # but don't affect inside JSON structure
try:
    json.loads(fixed2)
except json.JSONDecodeError:
    # More targeted: look for the specific issue
    lines = raw.split('\n')
    line38 = lines[37]  # 0-indexed
    # Find unescaped quote
    print(f"round092 line 38: ...{line38[100:200]}...")

# File 3: round095
f3 = glob.glob('content/deep_training/round095_*.json')[0]
raw3 = open(f3, 'r', encoding='utf-8-sig').read()
# Position 4251 has unescaped quote
fixed3 = raw3[:4240] + '\u201c' + raw3[4241:]  # Replace " with left quote
# Find matching closing quote
for i in range(4242, len(fixed3)):
    if fixed3[i] == '"' and fixed3[i-1] != '\\':
        # Check if content is Chinese text
        prev_ch = fixed3[i-1]
        if ord(prev_ch) > 127:
            fixed3 = fixed3[:i] + '\u201d' + fixed3[i+1:]
            break

try:
    json.loads(fixed3)
    open(f3, 'w', encoding='utf-8').write(fixed3)
    print(f"Fixed: {f3.split(chr(92))[-1]}")
except json.JSONDecodeError as e:
    print(f"Still broken: {f3.split(chr(92))[-1]}: {e.msg}")
