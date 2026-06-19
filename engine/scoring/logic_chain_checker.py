"""
逻辑牵引验证系统 V1.0

核心问题：专家讨论"太碎了"，没有内在逻辑牵引

最小设计：
- 检查每轮发言是否包含"@引用"
- 检查引用是否指向上一轮的具体观点
- 计算逻辑牵引度

成功标准：
逻辑牵引度 = 引用链条完整度
"""

import json
import re
from pathlib import Path
from collections import defaultdict

MEMORY_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/memory")
CONTENT_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/content")

def check_reference_chain(debate_json):
    """检查引用链条"""
    results = {
        "话题": debate_json.get("话题", debate_json.get("title", "")),
        "专家": debate_json.get("专家", []),
        "轮次分析": [],
        "逻辑牵引度": 0
    }
    
    if "辩论" in debate_json:
        debate = debate_json["辩论"]
        rounds = ["第1轮_立场阐述", "第2轮_相互质疑", "第3轮_回应辩护", "第4轮_认知升级"]
        
        total_expected_refs = 0
        actual_refs = 0
        
        for i, round_name in enumerate(rounds):
            if round_name in debate:
                round_data = debate[round_name]
                round_analysis = {
                    "轮次": round_name,
                    "发言数": 0,
                    "引用数": 0,
                    "预期引用数": 0,
                    "引用率": 0
                }
                
                for speaker_key, speaker_data in round_data.items():
                    round_analysis["发言数"] += 1
                    
                    if i == 0:
                        round_analysis["预期引用数"] += 1
                        total_expected_refs += 1
                        if "核心冲突" in debate_json:
                            actual_refs += 1
                            round_analysis["引用数"] += 1
                    else:
                        round_analysis["预期引用数"] += 1
                        total_expected_refs += 1
                        
                        content = ""
                        if isinstance(speaker_data, dict):
                            content = speaker_data.get("论证", speaker_data.get("回应", speaker_data.get("质疑点", "")))
                        elif isinstance(speaker_data, str):
                            content = speaker_data
                        
                        if "@" in content or "引用" in content or "你说" in content:
                            actual_refs += 1
                            round_analysis["引用数"] += 1
                
                if round_analysis["预期引用数"] > 0:
                    round_analysis["引用率"] = round_analysis["引用数"] / round_analysis["预期引用数"]
                
                results["轮次分析"].append(round_analysis)
        
        if total_expected_refs > 0:
            results["逻辑牵引度"] = actual_refs / total_expected_refs
    
    if "rounds" in debate_json:
        rounds = debate_json["rounds"]
        total_refs = 0
        total_content = 0
        
        for round_data in rounds:
            if "stances" in round_data:
                for stance in round_data["stances"]:
                    content = stance.get("content", "")
                    total_content += 1
                    if "@" in content:
                        total_refs += 1
        
        results["逻辑牵引度"] = total_refs / total_content if total_content > 0 else 0
    
    return results

def scan_all_debates():
    """扫描所有辩论"""
    all_results = []
    
    for json_file in MEMORY_DIR.glob("*.json"):
        try:
            content = json_file.read_text(encoding='utf-8-sig')
            data = json.loads(content)
            result = check_reference_chain(data)
            result["来源"] = json_file.name
            all_results.append(result)
        except Exception as e:
            print(f"Error: {json_file}: {e}")
    
    for json_file in CONTENT_DIR.glob("*.json"):
        try:
            content = json_file.read_text(encoding='utf-8-sig')
            data = json.loads(content)
            result = check_reference_chain(data)
            result["来源"] = json_file.name
            all_results.append(result)
        except Exception as e:
            print(f"Error: {json_file}: {e}")
    
    return all_results

def generate_report():
    """生成逻辑牵引报告"""
    all_results = scan_all_debates()
    
    report = "# 逻辑牵引验证报告\n\n"
    report += "## 成功标准\n\n"
    report += "```\n逻辑牵引度 = 引用链条完整度\n\n验证方式：\n- 检查每轮发言是否包含\"@引用\"\n- 检查引用是否指向上一轮的具体观点\n- 计算引用率 = 实际引用数 / 预期引用数\n```\n\n"
    
    report += "## 总体统计\n\n"
    
    avg牵引度 = sum(r["逻辑牵引度"] for r in all_results) / len(all_results) if all_results else 0
    report += f"| 指标 | 数值 |\n|:---|:---:|\n| 辩论总数 | {len(all_results)} |\n| 平均逻辑牵引度 | {avg牵引度:.1%} |\n\n"
    
    report += "## 详细分析\n\n"
    
    for r in all_results:
        report += f"### {r['话题']}\n\n"
        report += f"| 来源 | {r['来源']} |\n|:---|:---|\n"
        report += f"| 专家 | {', '.join(r['专家']) if r['专家'] else '未知'} |\n"
        report += f"| **逻辑牵引度** | **{r['逻辑牵引度']:.1%}** |\n\n"
        
        if r["轮次分析"]:
            report += "| 轮次 | 发言数 | 引用数 | 预期引用 | 引用率 |\n"
            report += "|:---|:---:|:---:|:---:|:---:|\n"
            for ra in r["轮次分析"]:
                report += f"| {ra['轮次']} | {ra['发言数']} | {ra['引用数']} | {ra['预期引用数']} | {ra['引用率']:.1%} |\n"
            report += "\n"
    
    report += "## 问题诊断\n\n"
    
    low牵引 = [r for r in all_results if r["逻辑牵引度"] < 0.5]
    if low牵引:
        report += "### 🔴 逻辑牵引度低于50%的辩论\n\n"
        for r in low牵引:
            report += f"- **{r['话题']}**：{r['逻辑牵引度']:.1%}\n"
        report += "\n"
    
    report += "## 改进建议\n\n"
    report += "1. **第1轮**：发言应引用\"核心冲突\"（话题定义）\n"
    report += "2. **第2轮**：质疑应引用第1轮的\"金句\"或\"推理\"\n"
    report += "3. **第3轮**：回应应引用第2轮的\"质疑点\"\n"
    report += "4. **第4轮**：认知升级应引用第3轮的\"回应\"并形成共识\n"
    
    return report

if __name__ == "__main__":
    report = generate_report()
    print(report)
    
    output_file = Path("D:/vibe_coding/zhengliu/圆桌会议/docs/logic_chain_report.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding='utf-8')
    print(f"\n报告已保存至: {output_file}")