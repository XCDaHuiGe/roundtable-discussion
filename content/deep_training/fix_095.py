# -*- coding: utf-8 -*-
"""Fix round095_菲利普·津巴多 JSON."""
import json, glob

f = 'content/deep_training/round095_尼克·博斯特罗姆_菲利普·津巴多.json'
if not glob.glob(f):
    print("File not found, looking for alternatives...")
    files = glob.glob('content/deep_training/round095_*.json')
    print(f"Found: {files}")
    f = files[0]

raw = open(f, 'r', encoding='utf-8-sig').read()

try:
    json.loads(raw)
    print("Already valid!")
except json.JSONDecodeError as e:
    print(f"Error at line {e.lineno}, col {e.colno}")
    
    # Simple approach: use json repair - try to find the exact issue
    # Show the line
    lines = raw.split('\n')
    if e.lineno <= len(lines):
        line = lines[e.lineno - 1]
        # Replace unescaped quotes in the problematic area
        # Strategy: find the problem and fix it character by character
        chars = list(line)
        for ci in range(len(chars)):
            if chars[ci] == '"':
                prev_char = chars[ci-1] if ci > 0 else ' '
                next_char = chars[ci+1] if ci < len(chars)-1 else ' '
                # If this quote is surrounded by non-ASCII (Chinese) on both sides
                # it's likely an unescaped quote inside text
                if ord(prev_char) > 0x2e80 and ord(next_char) > 0x2e80:
                    chars[ci] = '\u201c'
        lines[e.lineno - 1] = ''.join(chars)
        raw2 = '\n'.join(lines)
        try:
            json.loads(raw2)
            open(f, 'w', encoding='utf-8').write(raw2)
            print("Fixed!")
        except json.JSONDecodeError as e2:
            print(f"Still broken: {e2.msg}")
            print(f"Line {e2.lineno}: {lines[e2.lineno-1][:200]}")
    else:
        print("Line number out of range")
