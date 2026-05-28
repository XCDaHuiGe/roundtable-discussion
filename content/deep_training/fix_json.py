# -*- coding: utf-8 -*-
"""Fix JSON syntax errors in round files."""
import json, glob, os, re

fs = sorted(glob.glob('content/deep_training/round*.json'))
err_files = []
for f in fs:
    try:
        json.loads(open(f, 'r', encoding='utf-8-sig').read())
    except:
        err_files.append(f)

print(f"Fixing {len(err_files)} files...")
fixed_count = 0

for f in err_files:
    content = open(f, 'r', encoding='utf-8-sig').read()
    name = os.path.basename(f)
    
    lines = content.split('\n')
    
    # Read the error message to find the line/col
    try:
        json.loads(content)
        print(f"  [OK] Already valid: {name}")
        continue
    except json.JSONDecodeError as e:
        lineno = e.lineno
        colno = e.colno
        msg = str(e)
    
    # Common fixes:
    # 1. Missing comma between array elements
    # 2. Trailing comma in last element
    
    # Fix: missing comma before new object in array
    fixed = re.sub(r'\}\s*\n\s*\{', '},\n{', content)
    
    # Fix: missing comma between string values in an array
    fixed = re.sub(r'"\s*\n\s*"', '",\n"', fixed)
    
    if fixed != content:
        try:
            json.loads(fixed)
            open(f, 'w', encoding='utf-8').write(fixed)
            print(f"  [FIXED] {name}")
            fixed_count += 1
            continue
        except:
            pass
    
    # More targeted fix: look at the exact error location
    try:
        lines_before = lines[:lineno-1]
        problem_line = lines[lineno-1]
        fixed_line = problem_line[:colno-1] + ',' + problem_line[colno-1:]
        fixed_content = '\n'.join(lines_before + [fixed_line] + lines[lineno:])
        json.loads(fixed_content)
        open(f, 'w', encoding='utf-8').write(fixed_content)
        print(f"  [FIXED-exact] {name}")
        fixed_count += 1
        continue
    except:
        pass
    
    print(f"  [FAIL] {name}: {msg[:60]}")

print(f"\nFixed: {fixed_count}, Remaining: {len(err_files) - fixed_count}")
