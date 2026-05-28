# -*- coding: utf-8 -*-
"""Precise fix for remaining 2 files - replace unescaped quotes in stance text."""
import json, glob

def fix_unescaped_quotes(raw):
    """Replace ASCII " inside Chinese-text JSON string values with Chinese quotation marks."""
    result = list(raw)
    in_string = False
    escape = False
    i = 0
    while i < len(result):
        c = result[i]
        
        if c == '\\' and not escape:
            escape = True
            i += 1
            continue
        
        if c == '"' and not escape:
            prev = result[i-1] if i > 0 else ' '
            next_c = result[i+1] if i < len(result)-1 else ' '
            
            if not in_string:
                # Opening a JSON string
                in_string = True
            else:
                # Could be closing a JSON string or an unescaped quote in text
                # If next non-space char is : or , or ] or }, it's a closing quote
                # If surrounded by CJK characters, it's an unescaped internal quote
                
                # Find next non-space character
                lookahead = ''
                for j in range(i+1, min(i+10, len(result))):
                    if result[j] not in ' \n\r\t':
                        lookahead = result[j]
                        break
                
                if lookahead in ':],}':
                    # Valid closing quote
                    in_string = False
                elif (ord(prev) > 0x2e80 or prev in '.,!?。，！？、；：') and (ord(next_c) > 0x2e80 or next_c in '.,!?。，！？、；：'):
                    # Quote surrounded by CJK or punctuation - needs fixing
                    pass  # We'll handle below
        
        if c == '"' and in_string and not escape:
            prev = result[i-1] if i > 0 else ' '
            next_c = result[i+1] if i < len(result)-1 else ' '
            lookahead = ''
            for j in range(i+1, min(i+10, len(result))):
                if result[j] not in ' \n\r\t':
                    lookahead = result[j]
                    break
            
            if lookahead not in ':],}':
                # Not a valid closing quote - likely unescaped quote inside text
                if ord(prev) > 0x2e80 or prev in '。，！？、；：' or ord(next_c) > 0x2e80:
                    result[i] = '\u201c'  # Replace with Chinese left quote
        
        if c == '\\' and escape:
            escape = False
        
        i += 1
    
    return ''.join(result)

# Fix both files
for pattern in ['round026', 'round095']:
    files = glob.glob(f'content/deep_training/{pattern}_*.json')
    if not files:
        continue
    f = files[0]
    raw = open(f, 'r', encoding='utf-8-sig').read()
    
    fixed = fix_unescaped_quotes(raw)
    try:
        json.loads(fixed)
        open(f, 'w', encoding='utf-8').write(fixed)
        print(f"[FIXED] {f.split(chr(92))[-1]}")
    except json.JSONDecodeError as e:
        print(f"[FAIL] {f.split(chr(92))[-1]}: {e.msg}")
        # Show what's still wrong
        lines = fixed.split('\n')
        if e.lineno <= len(lines):
            print(f"  Line {e.lineno}: ...{lines[e.lineno-1][max(0,e.colno-20):e.colno+30]}...")

print("\nFinal verification:")
for f in glob.glob('content/deep_training/round*.json'):
    try:
        json.loads(open(f, 'r', encoding='utf-8-sig').read())
    except:
        print(f"  [BROKEN] {f.split(chr(92))[-1]}")
