# -*- coding: utf-8 -*-
"""Add open_questions to JSON"""
import json

with open('d:/vibe_coding/zhengliu/圆桌会议/content/无用阶级_工作意义_讨论.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['open_questions'] = [
    "当大部分工作被AI接管后，人类如何重新定义自己的价值？",
    "基本收入保障（UBI）是否能够解决无用阶级带来的社会问题？",
    "效率崇拜时代，如何保护那些无法被量化的价值和追求？"
]

with open('d:/vibe_coding/zhengliu/圆桌会议/content/无用阶级_工作意义_讨论.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Added open_questions")
