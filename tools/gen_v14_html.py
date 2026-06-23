#!/usr/bin/env python3
import json, base64

with open("content/真需求_完整v8.json", "r", encoding="utf-8") as f:
    data = json.load(f)

imgs = {}
for name in ["cover", "expert_grid", "question", "stances", "clash", "case", "cost", "human_nature", "cognitive_upgrade", "final_insight", "open_questions"]:
    path = f"output/assets/{name}.png"
    try:
        with open(path, "rb") as f:
            imgs[name] = base64.b64encode(f.read()).decode()
    except:
        imgs[name] = ""

html = ""
with open("output/zhenxuqiu_v14.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Done")
