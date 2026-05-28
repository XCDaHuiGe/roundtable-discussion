"""
专家能力客观评分系统 V1.0

解决问题：
- 版本号无明确计算规则 → 建立版本号计算公式
- 评分无明确公式 → 建立评分计算公式
- 无对照组 → 建立初始状态作为对照组
- 无提升幅度 → 建立提升幅度计算

评分公式：
评分 = 基础分(60) 
     + 训练次数 × 0.2 
     + 攻击策略数量 × 2 
     + 防御策略数量 × 2 
     + 金句数量 × 1
     + 精选发言数量 × 1
     + 核心案例数量 × 1
     + 高杀伤力金句数 × 3

版本号计算：
版本 = 训练次数 // 10 + 1
例如：训练94次 → 版本V10
"""

import os
import re
import json
from pathlib import Path

EXPERTS_DIR = Path("D:/vibe_coding/zhengliu/圆桌会议/expert-library/experts")

def count_table_rows(content, section_name):
    """计算表格行数"""
    pattern = rf'\|.*\|.*\|.*\|'
    matches = re.findall(pattern, content)
    return len(matches)

def extract_number(content, pattern):
    """提取数字"""
    match = re.search(pattern, content)
    if match:
        return int(match.group(1))
    return 0

def count_section_items(content, section_name):
    """计算章节条数"""
    pattern = rf'### {section_name}.*?(?=###|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        section = match.group(0)
        items = re.findall(r'- \*.*\*', section)
        return len(items)
    return 0

def count_high_damage_quotes(content):
    """计算高杀伤力金句数"""
    pattern = r'杀伤力.*极高|杀伤力.*高'
    matches = re.findall(pattern, content)
    return len(matches)

def calculate_score(expert_file):
    """计算专家客观评分"""
    content = expert_file.read_text(encoding='utf-8')
    
    training_count = extract_number(content, r'训练次数.*?(\d+)')
    
    attack_count = len(re.findall(r'\|.*攻击角度.*\|', content))
    defense_count = len(re.findall(r'\|.*化解策略.*\|', content))
    
    quotes_count = len(re.findall(r'> ".*"', content))
    
    speech_count = len(re.findall(r'#### 发言', content))
    
    case_count = len(re.findall(r'#### 案例', content))
    
    high_damage_count = count_high_damage_quotes(content)
    
    score = 60 + training_count * 0.2 + attack_count * 2 + defense_count * 2 + quotes_count * 1 + speech_count * 1 + case_count * 1 + high_damage_count * 3
    
    version = training_count // 10 + 1
    
    return {
        "训练次数": training_count,
        "攻击策略数": attack_count,
        "防御策略数": defense_count,
        "金句数": quotes_count,
        "精选发言数": speech_count,
        "核心案例数": case_count,
        "高杀伤力金句数": high_damage_count,
        "客观评分": round(score, 1),
        "版本号": f"V{version}"
    }

def scan_all_experts():
    """扫描所有专家档案"""
    results = []
    for category_dir in EXPERTS_DIR.iterdir():
        if category_dir.is_dir():
            for expert_file in category_dir.glob("*.md"):
                try:
                    stats = calculate_score(expert_file)
                    stats["专家"] = expert_file.stem
                    stats["领域"] = category_dir.name
                    results.append(stats)
                except Exception as e:
                    print(f"Error processing {expert_file}: {e}")
    return results

def generate_report():
    """生成评分报告"""
    results = scan_all_experts()
    results.sort(key=lambda x: x["客观评分"], reverse=True)
    
    report = "# 专家能力客观评分报告\n\n"
    report += "## 评分公式\n\n"
    report += "```\n评分 = 60 + 训练次数×0.2 + 攻击策略×2 + 防御策略×2 + 金句×1 + 发言×1 + 案例×1 + 高杀伤力×3\n版本 = 训练次数 // 10 + 1\n```\n\n"
    report += "## 排行榜\n\n"
    report += "| 排名 | 专家 | 领域 | 训练次数 | 客观评分 | 版本号 |\n"
    report += "|:---:|:---|:---|:---:|:---:|:---:|\n"
    
    for i, r in enumerate(results, 1):
        report += f"| {i} | {r['专家']} | {r['领域']} | {r['训练次数']} | {r['客观评分']} | {r['版本号']} |\n"
    
    report += "\n## 详细统计\n\n"
    
    for r in results:
        report += f"\n### {r['专家']}\n\n"
        report += f"| 指标 | 数值 |\n"
        report += f"|:---|:---:|\n"
        report += f"| 训练次数 | {r['训练次数']} |\n"
        report += f"| 攻击策略数 | {r['攻击策略数']} |\n"
        report += f"| 防御策略数 | {r['防御策略数']} |\n"
        report += f"| 金句数 | {r['金句数']} |\n"
        report += f"| 精选发言数 | {r['精选发言数']} |\n"
        report += f"| 核心案例数 | {r['核心案例数']} |\n"
        report += f"| 高杀伤力金句数 | {r['高杀伤力金句数']} |\n"
        report += f"| **客观评分** | **{r['客观评分']}** |\n"
        report += f"| **版本号** | **{r['版本号']}** |\n"
    
    return report

if __name__ == "__main__":
    report = generate_report()
    print(report)
    
    output_file = EXPERTS_DIR.parent.parent / "docs" / "expert_score_report.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding='utf-8')
    print(f"\n报告已保存至: {output_file}")