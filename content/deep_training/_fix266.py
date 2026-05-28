# Fix unescaped double quotes in JSON string values
import re

def fix_quotes(text):
    """Replace inner ASCII double quotes with Chinese quotation marks."""
    # Match Chinese text that appears inside " stance " or other JSON string values
    # Strategy: find pairs of ASCII quotes that enclose Chinese text
    result = []
    i = 0
    in_string = False
    string_start = -1
    chars = list(text)
    
    while i < len(chars):
        c = chars[i]
        if c == '"' and (i == 0 or chars[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_start = i
            else:
                # Check if this quote ends a JSON value or is inside content
                # Look ahead - if followed by punctuation or end of line, it's closer
                # If followed by Chinese chars, it's an inner quote
                if i + 1 < len(chars):
                    next_char = chars[i+1]
                    # Check if next non-space char is , or ] or } or : or \n
                    j = i + 1
                    while j < len(chars) and chars[j] in ' \t\r\n':
                        j += 1
                    if j < len(chars) and chars[j] in ',]}:\n':
                        # This is a closing JSON quote
                        in_string = False
                        string_start = -1
                    else:
                        # Inner quote - replace with Chinese quote U+201D
                        chars[i] = '\u201d'
                else:
                    in_string = False
                    string_start = -1
        i += 1
    
    # Now fix opening inner quotes too
    # Find " that were not changed and are inside strings
    result = []
    i = 0
    in_string = False
    skip_next = False
    while i < len(chars):
        if skip_next:
            skip_next = False
            i += 1
            continue
        c = chars[i]
        if c == '"' and (i == 0 or chars[i-1] != '\\'):
            if not in_string:
                in_string = True
            else:
                # Check if it's still ASCII "
                j = i + 1
                while j < len(chars) and chars[j] in ' \t\r\n':
                    j += 1
                if j < len(chars) and chars[j] in ',]}:\n':
                    in_string = False
                # else: keep as Chinese quote (already converted)
        # Also fix opening inner quotes - they would be " followed by Chinese
        elif c == '"' and in_string and (i == 0 or chars[i-1] != '\\'):
            # This is an inner " that wasn't caught - it should be opening Chinese
            if i+1 < len(chars) and ord(chars[i+1]) > 127:
                chars[i] = '\u201c'
        i += 1
    
    return ''.join(chars)

import glob
for fname in glob.glob('content/deep_training/round26[67]*.json'):
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    fixed = fix_quotes(content)
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print('Fixed:', fname)
