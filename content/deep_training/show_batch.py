import json
data = json.load(open('content/deep_training/batch1.json', 'r', encoding='utf-8'))
for r in data[:5]:
    print(f'R{r["round"]}: {r["expert1"]} vs {r["expert2"]} [{r["strength"]}]')
print(f'... total {len(data)} rounds')
