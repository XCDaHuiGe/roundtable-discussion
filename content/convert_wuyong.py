# -*- coding: utf-8 -*-
"""Simple converter for 无用阶级 discussion"""
import json

# Read the existing JSON
with open('d:/vibe_coding/zhengliu/圆桌会议/content/无用阶级_工作意义_讨论.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Build experts from dashboard
expert_names = data.get('dashboard', {}).get('experts', [])
expert_colors = {
    '赫拉利': '#9B59B6',
    '项飙': '#E74C3C',
    '许知远': '#3498DB',
    '余华': '#F39C12',
    '罗翔': '#27AE60',
    '李诞': '#1ABC9C'
}
expert_titles = {
    '赫拉利': '历史学家 · 《未来简史》作者',
    '项飙': '人类学家',
    '许知远': '知识分子 · 《十三邀》主持人',
    '余华': '作家 · 《活着》作者',
    '罗翔': '法学家',
    '李诞': '脱口秀演员'
}
expert_beliefs = {
    '赫拉利': '人类统治地球的秘密不是智力，而是虚构故事的能力。AI时代，这个能力正在被算法接管',
    '项飙': '附近不是乡愁，是基于现代性的诉求来抵制消解人际关系的力量',
    '许知远': '理想主义不是浪漫，是看清了之后还选择相信',
    '余华': '活着本身就是意义',
    '罗翔': '法治的要义是对权力的限制；人必须接受自己的有限性',
    '李诞': '人间不值得，但你已经来了，那就凑合过吧'
}

# Create experts list
data['experts'] = []
for name in expert_names:
    data['experts'].append({
        'name': name,
        'title': expert_titles.get(name, ''),
        'avatar_color': expert_colors.get(name, '#333333'),
        'core_belief': expert_beliefs.get(name, ''),
        'interest': '',
        'fear': '',
        'bias': ''
    })

# Update rounds to match V8 format
for round_data in data['rounds']:
    # Add 'core_question'
    round_data['core_question'] = round_data.get('question', '')

    # Convert 'speakers' to 'stances'
    if 'speakers' in round_data:
        round_data['stances'] = [
            {
                'expert': s['name'],
                'stance': s['content'],
                'emotion': 'serious'
            }
            for s in round_data['speakers']
        ]

    # Add empty clash_rounds
    if 'clashes' in round_data:
        round_data['clash_rounds'] = round_data.pop('clashes')
        for c in round_data['clash_rounds']:
            c['attack_type'] = c.get('type', '认知碰撞')
            c['attack_content'] = c['content']
            c['counter_attack'] = None
            c['target'] = c.get('target', '')
    else:
        round_data['clash_rounds'] = []

    # Add empty sections
    round_data['reality_cases'] = []
    round_data['cost_discussion'] = {}
    round_data['human_nature'] = {}
    round_data['cognitive_upgrade'] = {}

# Write back
with open('d:/vibe_coding/zhengliu/圆桌会议/content/无用阶级_工作意义_讨论.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("JSON updated successfully")
