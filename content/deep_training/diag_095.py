import json
f = 'content/deep_training/round095_尼克·博斯特罗姆_塔勒布.json'
raw = open(f, 'r', encoding='utf-8-sig').read()
try:
    json.loads(raw)
    print("VALID JSON")
except json.JSONDecodeError as e:
    print(f"Error: line {e.lineno}, col {e.colno}")
    lines = raw.split('\n')
    start_l = max(0, e.lineno - 2)
    end_l = min(len(lines), e.lineno + 1)
    for i in range(start_l, end_l):
        marker = ">>>" if i == e.lineno - 1 else "   "
        print(f"{marker} L{i+1}: {lines[i][:150]}")
