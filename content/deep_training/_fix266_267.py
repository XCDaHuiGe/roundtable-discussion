import glob, re

for fname in [
    'content/deep_training/round266_项飙_弗洛伊德.json',
    'content/deep_training/round267_吴晓波_尼克_博斯特罗姆.json',
]:
    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()

    # Strategy: find all stance/attack/counter_attack value strings,
    # and replace inner bare " with \"
    lines = text.split('\n')
    out_lines = []
    
    for line in lines:
        # Match lines of the form:  "key": "value",
        m = re.match(r'^(\s*"(stance|attack_content|counter_attack|title|topic)"\s*:\s*")(.*)("\s*,?\s*)$', line, re.DOTALL)
        if not m:
            out_lines.append(line)
            continue
        
        key = m.group(2)
        prefix = m.group(1)
        content = m.group(3)
        suffix = m.group(4) + '\n'  # add back the newline
        
        # Escape all bare " in content, but preserve existing \"
        fixed_content = []
        i = 0
        while i < len(content):
            c = content[i]
            if c == '\\' and i + 1 < len(content) and content[i+1] == '"':
                fixed_content.append('\\"')
                i += 2
            elif c == '"':
                fixed_content.append('\\"')
                i += 1
            else:
                fixed_content.append(c)
                i += 1
        
        new_line = prefix + ''.join(fixed_content) + suffix.rstrip('\n')
        out_lines.append(new_line)
    
    result = '\n'.join(out_lines)
    
    # Verify JSON validity
    import json
    try:
        json.loads(result)
        print('VALID JSON:', fname)
    except json.JSONDecodeError as e:
        print('INVALID:', fname, e)
        # Show the problematic area
        print('  Around error:', repr(result[max(0,e.pos-50):e.pos+50]))
    
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(result)
        print('  Wrote:', fname)
