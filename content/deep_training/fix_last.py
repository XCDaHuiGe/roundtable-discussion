# -*- coding: utf-8 -*-
"""Final targeted fixes for 3 broken files."""
import json, glob

fixes = []

# File 1: round026 - unescaped " inside stance text
f1 = glob.glob('content/deep_training/round026_*.json')[0]
raw = open(f1, 'r', encoding='utf-8-sig').read()
# Replace ASCII " inside Chinese stance with Chinese quotation marks
# Target: 因为它"更好用"，而不是
old = '\u56e0\u4e3a\u5b83"'
new = '\u56e0\u4e3a\u5b83\u201c'
raw = raw.replace(old, new, 1)
old2 = '\u66f4\u597d\u7528"\uff0c'
new2 = '\u66f4\u597d\u7528\u201d\uff0c'
raw = raw.replace(old2, new2, 1)
# Also fix the second pair: "把复杂装得更好看"
old3 = '"' + '\u628a\u590d\u6742'
new3 = '\u201c' + '\u628a\u590d\u6742'
if old3 in raw:
    raw = raw.replace(old3, new3, 1)
    # Find matching closing quote
    idx = raw.find(new3) + len(new3)
    for i in range(idx, len(raw)):
        if raw[i] == '"':
            raw = raw[:i] + '\u201d' + raw[i+1:]
            break
try:
    json.loads(raw)
    open(f1, 'w', encoding='utf-8').write(raw)
    fixes.append(f1)
    print(f"[FIXED] round026")
except json.JSONDecodeError as e:
    print(f"[FAIL] round026: {e.msg}")

# File 2: round092 - single quote instead of double quote
f2 = glob.glob('content/deep_training/round092_*.json')[0]
raw = open(f2, 'r', encoding='utf-8-sig').read()
# Fix: replace \', with \", 
raw = raw.replace("\u3002', \"emotion\"", "\u3002\", \"emotion\"")
try:
    json.loads(raw)
    open(f2, 'w', encoding='utf-8').write(raw)
    fixes.append(f2)
    print(f"[FIXED] round092")
except json.JSONDecodeError as e:
    print(f"[FAIL] round092: {e.msg}")
    # More aggressive: find all unescaped single quotes in the last stance
    lines = raw.split('\n')
    line38 = lines[37]
    print(f"  Trying more targeted fix...")
    # Replace ' before , with "
    fixed_line = line38.replace("\u2018", '"').replace("\u2019", '"')
    # Find the problematic single quote
    import re
    fixed_line = re.sub(r"([\u4e00-\u9fff])'([\",\s])", r'\1"\2', fixed_line)
    lines[37] = fixed_line
    raw2 = '\n'.join(lines)
    try:
        json.loads(raw2)
        open(f2, 'w', encoding='utf-8').write(raw2)
        fixes.append(f2)
        print(f"[FIXED] round092 (2nd try)")
    except json.JSONDecodeError as e2:
        print(f"[FAIL] round092 (2nd): {e2.msg}")
        print(f"  Problem line 38: {repr(fixed_line)}")

# File 3: round095 - unescaped quotes
f3 = glob.glob('content/deep_training/round095_*.json')[0]
raw = open(f3, 'r', encoding='utf-8-sig').read()
lines = raw.split('\n')
# Find lines with unescaped quotes in Chinese text
import re
fixed_lines = []
for line in lines:
    # Replace ASCII " that appears between CJK characters with Chinese quotes
    new_chars = list(line)
    for ci in range(len(new_chars)):
        if new_chars[ci] == '"':
            prev_char = new_chars[ci-1] if ci > 0 else ' '
            next_char = new_chars[ci+1] if ci < len(new_chars)-1 else ' '
            prev_ok = ord(prev_char) > 0x2e80
            next_ok = ord(next_char) > 0x2e80
            if prev_ok and next_ok:
                new_chars[ci] = '\u201c'
    fixed_lines.append(''.join(new_chars))
raw3 = '\n'.join(fixed_lines)
try:
    json.loads(raw3)
    open(f3, 'w', encoding='utf-8').write(raw3)
    fixes.append(f3)
    print(f"[FIXED] round095")
except json.JSONDecodeError as e:
    print(f"[FAIL] round095: {e.msg}")

print(f"\nFixed {len(fixes)}/3 files")

# Final verification
print("\nFinal status:")
for f in [f1, f2, f3]:
    try:
        json.loads(open(f, 'r', encoding='utf-8-sig').read())
        print(f"  [OK] {f.split(chr(92))[-1]}")
    except json.JSONDecodeError as e:
        print(f"  [BROKEN] {f.split(chr(92))[-1]}: {e.msg}")
