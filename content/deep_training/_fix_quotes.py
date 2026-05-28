import re, glob, json

for fname in glob.glob('content/deep_training/round266*.json') + glob.glob('content/deep_training/round267*.json'):
    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\n')
    new_lines = []
    for line in lines:
        # Only process lines that contain stance/attack/counter JSON values
        if re.search(r'"(stance|attack_content|counter_attack)"', line):
            m = re.match(r'^(\s*"(?:stance|attack_content|counter_attack)"\s*:\s*")(.*)(")\s*,?\s*$', line, re.DOTALL)
            if m:
                prefix = m.group(1)
                content = m.group(2)
                suffix = m.group(3)
                # Replace inner unescaped ASCII double quotes with Chinese quotation marks
                # Pattern: "ChineseText" -> \u201cChineseText\u201d
                LQ = chr(0x201c)
                RQ = chr(0x201d)
                content = re.sub(
                    '\x22([\u4e00-\u9fff][\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\w\s.,;:\u2014\u2013\xb7\u2022\u2026\xd7a-zA-Z0-9]{0,100}?[\u4e00-\u9fff])\x22',
                    LQ + r'\1' + RQ,
                    content
                )
                line = prefix + content + suffix
        new_lines.append(line)

    result = '\n'.join(new_lines)
    
    # Verify it's valid JSON
    try:
        json.loads(result)
        print('VALID:', fname)
    except json.JSONDecodeError as e:
        print('STILL INVALID:', fname, e)
    
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(result)
