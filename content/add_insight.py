# -*- coding: utf-8 -*-
"""Add final_insight to JSON"""
import json

with open('d:/vibe_coding/zhengliu/圆桌会议/content/无用阶级_工作意义_讨论.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['final_insight'] = '意义不在工作之中，意义在附近。重建人与真实世界的连接，才是应对无用时代的唯一出路'

with open('d:/vibe_coding/zhengliu/圆桌会议/content/无用阶级_工作意义_讨论.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Added final_insight")
