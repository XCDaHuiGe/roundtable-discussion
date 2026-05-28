"""
专家能力验证系统 V2.0 (Karpathy Guidelines版)

核心原则：
1. 明确假设：能力提升 = 辩论胜率提升
2. 最小设计：只保留可验证指标
3. 验证闭环：每次辩论后记录胜率

成功标准：
- 辩论胜率 = 被共识采纳的观点数 / 总发言数
- 能力提升 = 当前胜率 - 基线胜率
"""

import json
import re
from pathlib import Path

CONTENT_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/content")
OUTPUT_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/output")
MEMORY_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/memory")

def extract_consensus_adopted_views(roundtable_json):
    """从圆桌洞见JSON中提取被共识采纳的观点"""
    adopted = {}
    
    if "rounds" in roundtable_json:
        for round_data in roundtable_json["rounds"]:
            if "stance_evolution" in round_data:
                for expert, evolution in round_data["stance_evolution"].items():
                    if expert not in adopted:
                        adopted[expert] = {"采纳": 0, "总发言": 0}
                    adopted[expert]["总发言"] += 1
                    if evolution.get("change_reason"):
                        adopted[expert]["采纳"] += 1
    
    if "dynamic_consensus_state" in roundtable_json:
        if "emerging_frameworks" in roundtable_json["dynamic_consensus_state"]:
            for framework in roundtable_json["dynamic_consensus_state"]["emerging_frameworks"]:
                pass
    
    return adopted

def calculate_win_rate(adopted_stats):
    """计算辩论胜率"""
    if adopted_stats["总发言"] == 0:
        return 0
    return adopted_stats["采纳"] / adopted_stats["总发言"]

def scan_all_roundtables():
    """扫描所有圆桌洞见，计算每位专家的累计胜率"""
    expert_stats = {}
    
    for json_file in CONTENT_DIR.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding='utf-8'))
            adopted = extract_consensus_adopted_views(data)
            for expert, stats in adopted.items():
                if expert not in expert_stats:
                    expert_stats[expert] = {"采纳": 0, "总发言": 0}
                expert_stats[expert]["采纳"] += stats["采纳"]
                expert_stats[expert]["总发言"] += stats["总发言"]
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    for json_file in MEMORY_DIR.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding='utf-8'))
            if "策略提取" in data:
                for expert_key in data["策略提取"]:
                    expert_name = expert_key.split("_")[0]
                    if expert_name not in expert_stats:
                        expert_stats[expert_name] = {"采纳": 0, "总发言": 0, "训练": 0}
                    expert_stats[expert_name]["训练"] += 1
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    return expert_stats

def generate_win_rate_report():
    """生成辩论胜率报告"""
    expert_stats = scan_all_roundtables()
    
    results = []
    for expert, stats in expert_stats.items():
        win_rate = calculate_win_rate(stats)
        results.append({
            "专家": expert,
            "采纳": stats["采纳"],
            "总发言": stats["总发言"],
            "辩论胜率": round(win_rate * 100, 1),
            "训练次数": stats.get("训练", 0)
        })
    
    results.sort(key=lambda x: x["辩论胜率"], reverse=True)
    
    report = "# 专家辩论胜率报告（可验证版）\n\n"
    report += "## 成功标准\n\n"
    report += "```\n辩论胜率 = 被共识采纳的观点数 / 总发言数\n能力提升 = 当前胜率 - 基线胜率\n```\n\n"
    report += "## 排行榜\n\n"
    report += "| 排名 | 专家 | 训练次数 | 总发言 | 被采纳 | 辩论胜率 |\n"
    report += "|:---:|:---|:---:|:---:|:---:|:---:|\n"
    
    for i, r in enumerate(results, 1):
        report += f"| {i} | {r['专家']} | {r['训练次数']} | {r['总发言']} | {r['采纳']} | {r['辩论胜率']}% |\n"
    
    report += "\n## 说明\n\n"
    report += "- **辩论胜率**：专家观点被共识采纳的比例（可验证）\n"
    report += "- **训练次数**：参与深度训练的轮次（客观计数）\n"
    report += "- **能力提升**：需要基线胜率作为对照（待建立）\n"
    
    return report

if __name__ == "__main__":
    report = generate_win_rate_report()
    print(report)
    
    output_file = Path("D:/vibe_coding/zhengliu/圆桌会议/docs/expert_win_rate_report.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding='utf-8')
    print(f"\n报告已保存至: {output_file}")