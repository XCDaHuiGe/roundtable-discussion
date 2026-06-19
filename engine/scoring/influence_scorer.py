"""
专家能力验证系统 V2.1 (Karpathy Guidelines版)

最小设计：
1. 金句胜率 = 被记录在key_quotes的金句数
2. 认知影响 = 观点被stance_evolution.change_reason引用的次数

验证闭环：
- 每次圆桌洞见后，统计每位专家的影响力
"""

import json
from pathlib import Path
from collections import defaultdict

CONTENT_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/content")
MEMORY_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/memory")

def extract_expert_influence(roundtable_json):
    """提取专家影响力数据"""
    influence = defaultdict(lambda: {"金句": 0, "影响他人": 0, "被影响": 0, "训练": 0})
    
    if "key_quotes" in roundtable_json:
        for quote in roundtable_json["key_quotes"]:
            expert = quote.get("expert", "")
            if expert:
                influence[expert]["金句"] += 1
    
    if "rounds" in roundtable_json:
        for round_data in roundtable_json["rounds"]:
            if "stance_evolution" in round_data:
                for expert, evolution in round_data["stance_evolution"].items():
                    change_reason = evolution.get("change_reason", "")
                    if change_reason:
                        influence[expert]["被影响"] += 1
                        mentioned = extract_mentioned_experts(change_reason)
                        for m in mentioned:
                            influence[m]["影响他人"] += 1
    
    return dict(influence)

def extract_mentioned_experts(text):
    """从文本中提取被提及的专家名"""
    experts = ["老子", "尼采", "孔子", "韩非子", "卡尼曼", "弗洛姆", "津巴多", 
               "达利欧", "芒格", "塔勒布", "项飙", "赫拉利", "凯文凯利", "博斯特罗姆",
               "李诞", "冯唐", "吴军", "刘润", "罗翔", "阿伦特", "波伏娃", "阿西莫夫",
               "丁元英", "芮小丹", "万维钢", "许知远", "吴晓波", "柯林斯", "马克思", "戈尔曼"]
    mentioned = []
    for expert in experts:
        if expert in text:
            mentioned.append(expert)
    return mentioned

def scan_all_sources():
    """扫描所有来源，计算影响力"""
    all_influence = defaultdict(lambda: {"金句": 0, "影响他人": 0, "被影响": 0, "训练": 0})
    
    for json_file in CONTENT_DIR.glob("*.json"):
        try:
            content = json_file.read_text(encoding='utf-8-sig')
            data = json.loads(content)
            influence = extract_expert_influence(data)
            for expert, stats in influence.items():
                for key, value in stats.items():
                    all_influence[expert][key] += value
        except Exception as e:
            print(f"Error: {json_file}: {e}")
    
    for json_file in MEMORY_DIR.glob("*.json"):
        try:
            content = json_file.read_text(encoding='utf-8-sig')
            data = json.loads(content)
            if "专家" in data:
                for expert in data["专家"]:
                    all_influence[expert]["训练"] += 1
        except Exception as e:
            print(f"Error: {json_file}: {e}")
    
    return dict(all_influence)

def calculate_influence_score(stats):
    """计算影响力分数（简单加权）"""
    return stats["金句"] * 3 + stats["影响他人"] * 2 - stats["被影响"] * 1

def generate_report():
    """生成影响力报告"""
    all_influence = scan_all_sources()
    
    results = []
    for expert, stats in all_influence.items():
        score = calculate_influence_score(stats)
        results.append({
            "专家": expert,
            "训练": stats["训练"],
            "金句": stats["金句"],
            "影响他人": stats["影响他人"],
            "被影响": stats["被影响"],
            "影响力分数": score
        })
    
    results.sort(key=lambda x: x["影响力分数"], reverse=True)
    
    report = "# 专家影响力报告（可验证版 V2.1）\n\n"
    report += "## 成功标准（最小设计）\n\n"
    report += "```\n影响力分数 = 金句×3 + 影响他人×2 - 被影响×1\n\n验证方式：\n- 金句：被记录在key_quotes的金句数\n- 影响他人：观点被stance_evolution.change_reason引用的次数\n- 被影响：自己的立场被他人观点改变的次数\n```\n\n"
    report += "## 排行榜\n\n"
    report += "| 排名 | 专家 | 训练 | 金句 | 影响他人 | 被影响 | 影响力分数 |\n"
    report += "|:---:|:---|:---:|:---:|:---:|:---:|:---:|\n"
    
    for i, r in enumerate(results, 1):
        report += f"| {i} | {r['专家']} | {r['训练']} | {r['金句']} | {r['影响他人']} | {r['被影响']} | {r['影响力分数']} |\n"
    
    report += "\n## 说明\n\n"
    report += "- **金句**：被记录在圆桌洞见key_quotes中的金句数（可验证）\n"
    report += "- **影响他人**：观点被其他专家引用并改变立场的次数（可验证）\n"
    report += "- **被影响**：自己的立场被他人观点改变的次数（可验证）\n"
    report += "- **影响力分数**：金句×3 + 影响他人×2 - 被影响×1（简单加权）\n"
    
    return report

if __name__ == "__main__":
    report = generate_report()
    print(report)
    
    output_file = Path("D:/vibe_coding/zhengliu/圆桌会议/docs/expert_influence_report.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding='utf-8')
    print(f"\n报告已保存至: {output_file}")