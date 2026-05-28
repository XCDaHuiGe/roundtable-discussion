# -*- coding: utf-8 -*-
"""验证升级：所有adapter内容完整性 + 版本一致性"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from render_adapter import adapt, ADAPTERS

TEST_DATA = {
    "title": "升级验证测试",
    "subtitle": "V7.0全模板内容完整性验证",
    "experts": [
        {"name": "达利欧", "title": "投资大师", "avatar_color": "#1a5f2a", "core_belief": "原则驱动"},
        {"name": "芒格", "title": "投资思想家", "avatar_color": "#8a2a4a", "core_belief": "多元思维模型"},
    ],
    "rounds": [
        {
            "round_number": 1,
            "topic": "如何面对职场倦怠",
            "core_question": "当工作严重消耗精力，应该改变自己还是离开？",
            "stances": [
                {"expert": "达利欧", "stance": "痛苦+反思=进步。职场倦怠是一个信号。", "emotion": "serious"},
                {"expert": "芒格", "stance": "反过来想。如果一份工作让你痛苦到极点，你需要问的不是如何坚持。", "emotion": "serious"}
            ],
            "clash_rounds": [
                {
                    "attacker": "芒格",
                    "target": "达利欧",
                    "attack_type": "逻辑漏洞",
                    "attack_content": "你说痛苦+反思=进步，但有些痛苦不是用来反思的。",
                    "emotion": "serious",
                    "counter_attack": "你说得对，但关键是要先反思再决定。"
                }
            ],
            "reality_cases": [
                {"case_name": "某科技公司员工", "case_source": "真实案例", "case_content": "连续加班两年后 burnout", "case_outcome": "离职后恢复", "case_lesson": "及时止损"}
            ],
            "cost_discussion": {
                "scenario": "如果盲目忍耐",
                "cost_analysis": [{"cost": "健康代价", "analysis": "长期压力导致免疫力下降"}],
                "worst_case": "身心崩溃",
                "survivor_bias": "成功者往往忽略了那些倒下的人"
            },
            "human_nature": {
                "question": "为什么大多数人选择忍耐？",
                "psychological_analysis": "损失厌恶让人们害怕失去现有的稳定",
                "real_examples": ["沉没成本谬误", "现状偏差"],
                "conclusion": "人性使然，但可以被觉察和克服"
            },
            "cognitive_upgrade": {
                "old_thinking": "忍耐就是美德",
                "new_thinking": "有策略地选择战场",
                "complexity": "需要区分'成长的痛苦'和'消耗的痛苦'",
                "actionable_insight": "建立个人健康仪表盘，设定红线"
            },
            "synthesis": {
                "answer": "面对职场倦怠，核心在于区分'成长型痛苦'和'消耗型痛苦'。前者值得忍耐，后者必须逃离。",
                "consensus": ["盲目忍耐不是美德", "决定前需理解痛苦根源"],
                "disagreements": ["反思深度存在分歧", "离开时机存在分歧"]
            }
        }
    ],
    "final_insight": "最重要的不是选择忍耐还是逃离，而是建立清晰的决策框架。",
    "open_questions": ["如何判断环境是否可改变？", "离开前应做好哪些准备？"],
    "final_consensus": ["盲目忍耐不可取", "决策需基于深入理解"],
    "final_disagreements": ["反思深度存在分歧"]
}

REQUIRED_SECTIONS = [
    "现实案例", "代价讨论", "人性层", "认知升级", "综合答案",
    "共识点", "分歧点", "最终洞见", "最终共识", "未解分歧"
]

def verify():
    results = {}
    for template_id in ADAPTERS:
        html = adapt(TEST_DATA, template_id)
        found = []
        missing = []
        for section in REQUIRED_SECTIONS:
            if section in html:
                found.append(section)
            else:
                missing.append(section)
        results[template_id] = {"found": found, "missing": missing, "total": len(html)}
    
    print("=" * 60)
    print("V7.0 全模板内容完整性验证")
    print("=" * 60)
    
    all_pass = True
    for tid, r in results.items():
        status = "PASS" if not r["missing"] else "FAIL"
        if r["missing"]:
            all_pass = False
        print(f"\n[{status}] {tid} ({r['total']} chars)")
        print(f"  ✓ 包含: {', '.join(r['found'])}")
        if r["missing"]:
            print(f"  ✗ 缺失: {', '.join(r['missing'])}")
    
    print("\n" + "=" * 60)
    
    # 版本一致性检查
    version_files = {
        "SKILL.md": None,
        "AGENTS.md": None,
        "README.md": None,
    }
    for fname in version_files:
        fpath = os.path.join(os.path.dirname(__file__), "..", fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                if "V7.0" in content:
                    version_files[fname] = "V7.0"
                else:
                    for v in ["V5.0", "V5.1", "V6.0"]:
                        if v in content:
                            version_files[fname] = v
                            break
    
    print("\n版本一致性检查:")
    versions = set(version_files.values())
    for fname, ver in version_files.items():
        status = "✓" if ver == "V7.0" else "✗"
        print(f"  {status} {fname}: {ver or '未找到版本号'}")
    
    if len(versions) == 1 and "V7.0" in versions:
        print("\n✓ 版本号统一: V7.0")
    else:
        all_pass = False
        print(f"\n✗ 版本号不一致: {versions}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("全部通过! ✓")
    else:
        print("部分检查未通过! ✗")
    
    return all_pass

if __name__ == "__main__":
    verify()
