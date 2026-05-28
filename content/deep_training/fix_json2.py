# -*- coding: utf-8 -*-
"""Fix all JSON files with unescaped quotes or syntax errors."""
import json, glob, os, re

fs = sorted(glob.glob('content/deep_training/round*.json'))

for f in fs:
    try:
        json.loads(open(f, 'r', encoding='utf-8-sig').read())
    except json.JSONDecodeError:
        pass
    else:
        continue  # already valid
    
    raw = open(f, 'r', encoding='utf-8-sig').read()
    name = os.path.basename(f)
    
    # Strategy: replace ASCII double quotes inside Chinese text with Chinese quotes
    # Asian text context: 前一个字是中文, 后一个字也是中文
    import unicodedata
    
    def is_cjk(ch):
        try:
            return 'CJK' in unicodedata.name(ch, '') or 'FULLWIDTH' in unicodedata.name(ch, '')
        except:
            return False
    
    chars = list(raw)
    in_string = False
    escape = False
    fix_count = 0
    
    i = 0
    while i < len(chars):
        ch = chars[i]
        
        if escape:
            escape = False
            i += 1
            continue
        
        if ch == '\\':
            escape = True
            i += 1
            continue
        
        if ch == '"':
            # Toggle in_string (simple but effective for well-formed JSON structure)
            # Count preceding backslashes
            bs_count = 0
            j = i - 1
            while j >= 0 and chars[j] == '\\':
                bs_count += 1
                j -= 1
            
            if bs_count % 2 == 0:  # not escaped
                if not in_string:
                    in_string = True
                else:
                    # We're closing a string - check if next non-space char is valid
                    # If there's a quote that shouldn't close (e.g., inside text), flag it
                    pass
        i += 1
    
    # Simple approach: just try to repair common patterns
    # Replace unescaped quotes inside string values
    fixed = re.sub(r'(?<=[^\s,:{\[])"(?=[^\s,\]:}\]])', '\u201c', raw)
    fixed = re.sub(r'(?<=[^\s,:{\[])"(?=\s*[^\s,:{\[:])', '\u201d', fixed)
    
    # Reset in_string state tracking
    # Try to find the exact fix
    try:
        json.loads(fixed)
        open(f, 'w', encoding='utf-8').write(fixed)
        print(f"  [FIXED] {name}")
        continue
    except:
        pass
    
    # More targeted: read the error message, find the problematic line
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        lineno = e.lineno
        lines = raw.split('\n')
        if lineno <= len(lines):
            line = lines[lineno - 1]
            # Find unescaped quotes in this line
            # Simple heuristic: replace quotes inside stance/attack_content/counter_attack values
            fixed_line = line
            # Replace ASCII " that appear between CJK characters with Chinese quotes
            new_chars = list(fixed_line)
            for ci in range(len(new_chars)):
                if new_chars[ci] == '"':
                    prev_char = new_chars[ci-1] if ci > 0 else ' '
                    next_char = new_chars[ci+1] if ci < len(new_chars)-1 else ' '
                    if is_cjk(prev_char) and is_cjk(next_char):
                        # This is likely a quote inside Chinese text, not a JSON delimiter
                        new_chars[ci] = '\u201c'  # use left double quotation mark
            fixed_line = ''.join(new_chars)
            lines[lineno - 1] = fixed_line
            fixed = '\n'.join(lines)
            try:
                json.loads(fixed)
                open(f, 'w', encoding='utf-8').write(fixed)
                print(f"  [FIXED-line] {name}")
                continue
            except:
                pass
    
    print(f"  [FAIL] {name}")

print("\nFinal recheck:")
for f in fs:
    try:
        json.loads(open(f, 'r', encoding='utf-8-sig').read())
    except:
        print(f"  [BROKEN] {os.path.basename(f)}")
