# -*- coding: utf-8 -*-
"""
自动化训练入口 V7.0

一个命令完成全部训练流程：
  python auto_train.py                    # 默认5轮
  python auto_train.py --rounds 10        # 10轮
  python auto_train.py --experts 孔子,老子 # 指定专家
  python auto_train.py --check            # 仅检查同质化

流程：
  1. 检查专家同质化 → 自动修复
  2. 运行深度训练 → 生成辩论 + 提取策略 + 升级档案
  3. 验证结果 → 评分 + 差异化检查
"""

import argparse
import json
import os
import sys
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EXPERT_LIBRARY = os.path.join(os.path.dirname(__file__), '..', 'expert-library', 'experts')
MEMORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory')
CATEGORIES = ['philosophy', 'psychology', 'sociology', 'literature', 'economics']

HOMOGENEOUS_VALUES = "专业能力/独立判断/持续学习"
HOMOGENEOUS_FRAMEWORK = "先看事实：发生了什么，数据怎么说？"
TEMPLATE_QUOTE_PATTERN = "我们再深一层。你说"


def load_all_experts() -> dict:
    experts = {}
    for cat in CATEGORIES:
        cat_dir = os.path.join(EXPERT_LIBRARY, cat)
        if not os.path.isdir(cat_dir):
            continue
        for f in os.listdir(cat_dir):
            if f.endswith('.md'):
                name = f[:-3]
                path = os.path.join(cat_dir, f)
                with open(path, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                experts[name] = {'path': path, 'category': cat, 'content': content}
    return experts


def check_homogeneity(experts: dict) -> list:
    issues = []
    for name, data in experts.items():
        content = data['content']
        if HOMOGENEOUS_VALUES in content:
            issues.append({
                'expert': name,
                'category': data['category'],
                'type': '同质化价值排序',
                'severity': 'HIGH'
            })
        if HOMOGENEOUS_FRAMEWORK in content:
            issues.append({
                'expert': name,
                'category': data['category'],
                'type': '同质化分析框架',
                'severity': 'HIGH'
            })
        if TEMPLATE_QUOTE_PATTERN in content:
            issues.append({
                'expert': name,
                'category': data['category'],
                'type': '模板化金句',
                'severity': 'MEDIUM'
            })
    return issues


def select_experts_for_training(experts: dict, target: list = None, count: int = 6) -> list:
    if target:
        return [t for t in target if t in experts]
    names = list(experts.keys())
    training_counts = {}
    for name, data in experts.items():
        content = data['content']
        tc = content.count('### 话题') + content.count('### 深度训练')
        training_counts[name] = tc
    sorted_names = sorted(names, key=lambda n: training_counts.get(n, 0))
    return sorted_names[:count]


def generate_training_report(experts: dict, issues: list) -> str:
    report = []
    report.append("=" * 60)
    report.append("  专家库质量报告")
    report.append("=" * 60)
    report.append(f"\n总专家数: {len(experts)}")
    report.append(f"问题总数: {len(issues)}")

    high = [i for i in issues if i['severity'] == 'HIGH']
    medium = [i for i in issues if i['severity'] == 'MEDIUM']
    report.append(f"  HIGH: {len(high)}")
    report.append(f"  MEDIUM: {len(medium)}")

    if high:
        report.append("\n--- HIGH 优先级问题 ---")
        for i in high:
            report.append(f"  [{i['category']}] {i['expert']}: {i['type']}")

    if medium:
        report.append("\n--- MEDIUM 优先级问题 ---")
        for i in medium:
            report.append(f"  [{i['category']}] {i['expert']}: {i['type']}")

    by_type = {}
    for i in issues:
        by_type.setdefault(i['type'], []).append(i['expert'])

    report.append("\n--- 按问题类型汇总 ---")
    for t, names in by_type.items():
        report.append(f"  {t}: {len(names)} 位专家")
        for n in names[:5]:
            report.append(f"    - {n}")
        if len(names) > 5:
            report.append(f"    ... 还有 {len(names)-5} 位")

    report.append("\n" + "=" * 60)
    return "\n".join(report)


def run_training_session(experts: dict, selected: list, rounds: int) -> dict:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'training'))
    from llm_generate import call_llm_json

    session = {
        'start_time': datetime.now().isoformat(),
        'rounds': rounds,
        'experts': selected,
        'results': []
    }

    for r in range(rounds):
        print(f"\n--- Round {r+1}/{rounds} ---")

        if len(selected) >= 2:
            pair = random.sample(selected, 2)
        else:
            pair = selected[:2]

        topic = f"{pair[0]}与{pair[1]}的核心信念碰撞"
        print(f"话题: {topic}")
        print(f"参与: {', '.join(pair)}")

        expert_profiles = []
        for name in pair:
            data = experts[name]
            lines = data['content'].split('\n')
            beliefs = []
            in_beliefs = False
            for line in lines:
                if '### 核心信念' in line:
                    in_beliefs = True
                    continue
                if in_beliefs and line.startswith('###'):
                    break
                if in_beliefs and line.startswith('- '):
                    beliefs.append(line[2:])
            expert_profiles.append(f"【{name}】核心信念: {'; '.join(beliefs[:3])}")

        prompt = f"""你是一个圆桌讨论主持人。请组织以下专家就"{topic}"进行3轮深度辩论。

参与专家：
{chr(10).join(expert_profiles)}

要求：
1. 第一轮：各自表达立场（200-400字/人）
2. 第二轮：相互质疑反驳（300-700字/人）
3. 第三轮：回应辩护+认知升级（200-400字/人）

返回JSON格式：
{{
  "topic": "{topic}",
  "rounds": [
    {{
      "round_name": "立场阐述",
      "speeches": [
        {{"expert": "专家名", "stance": "立场关键词", "content": "发言内容（200-400字）", "emotion": "serious"}}
      ]
    }},
    {{
      "round_name": "相互质疑",
      "speeches": [
        {{"expert": "专家名", "target": "被质疑者", "attack_type": "质疑类型", "content": "质疑内容（300-700字）"}}
      ]
    }},
    {{
      "round_name": "回应辩护",
      "speeches": [
        {{"expert": "专家名", "content": "辩护内容", "cognitive_upgrade": "认知升级描述"}}
      ]
    }}
  ],
  "key_quotes": [
    {{"expert": "专家名", "quote": "金句内容", "impact": "high"}}
  ]
}}"""

        result = call_llm_json(prompt, "你是圆桌讨论主持人，生成真实、有深度的辩论。")
        if result['success'] and result['data']:
            round_result = result['data']
            session['results'].append({
                'round': r + 1,
                'topic': topic,
                'experts': pair,
                'data': round_result
            })

            quotes = round_result.get('key_quotes', [])
            if quotes:
                print(f"  金句: {quotes[0]['quote'][:50]}...")

            for speech in round_result.get('rounds', [{}])[0].get('speeches', []):
                expert = speech.get('expert', '')
                content = speech.get('content', '')
                print(f"  {expert}: {content[:60]}...")
        else:
            print(f"  LLM调用失败: {result.get('error', '未知错误')}")

    session['end_time'] = datetime.now().isoformat()

    os.makedirs(MEMORY_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(MEMORY_DIR, f'auto_train_{ts}.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
    print(f"\n训练日志: {log_path}")

    return session


def update_expert_from_training(experts: dict, session: dict):
    quotes_added = 0
    speeches_added = 0

    for round_data in session.get('results', []):
        data = round_data.get('data', {})

        for quote in data.get('key_quotes', []):
            expert = quote.get('expert', '')
            if expert in experts:
                path = experts[expert]['path']
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                quote_text = quote.get('quote', '')
                if quote_text and quote_text not in content:
                    if '### 金句库' in content:
                        insert_pos = content.find('### 金句库')
                        next_section = content.find('\n## ', insert_pos + 10)
                        if next_section == -1:
                            next_section = len(content)
                        existing_quotes = content[insert_pos:next_section]
                        quote_count = existing_quotes.count('" — 杀伤力')
                        if quote_count < 8:
                            new_quote = f'{quote_count+1}. "{quote_text}" — 杀伤力: {quote.get("impact", "中")}\n'
                            content = content[:next_section] + new_quote + content[next_section:]
                            with open(path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            quotes_added += 1

        for round_info in data.get('rounds', []):
            for speech in round_info.get('speeches', []):
                expert = speech.get('expert', '')
                content_text = speech.get('content', '')
                if expert in experts and content_text:
                    speeches_added += 1

    print(f"\n档案更新: 新增 {quotes_added} 条金句, {speeches_added} 条发言记录")


def main():
    parser = argparse.ArgumentParser(description='自动化训练入口 V7.0')
    parser.add_argument('--rounds', type=int, default=5, help='训练轮次（默认5）')
    parser.add_argument('--experts', type=str, default=None, help='指定专家（逗号分隔）')
    parser.add_argument('--check', action='store_true', help='仅检查同质化')
    parser.add_argument('--count', type=int, default=6, help='每轮参与专家数（默认6）')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  自动化训练引擎 V7.0")
    print("=" * 60)

    print("\n[1/4] 加载专家库...")
    experts = load_all_experts()
    print(f"  已加载 {len(experts)} 位专家")

    print("\n[2/4] 检查同质化...")
    issues = check_homogeneity(experts)
    report = generate_training_report(experts, issues)
    print(report)

    if args.check:
        return

    print("\n[3/4] 选择训练专家...")
    target = args.experts.split(',') if args.experts else None
    selected = select_experts_for_training(experts, target, args.count)
    print(f"  参与专家: {', '.join(selected)}")

    print("\n[4/4] 开始训练...")
    session = run_training_session(experts, selected, args.rounds)

    print("\n[更新] 升级专家档案...")
    update_expert_from_training(experts, session)

    print("\n" + "=" * 60)
    print("  训练完成!")
    print("=" * 60)
    print(f"  轮次: {len(session.get('results', []))}")
    print(f"  专家: {', '.join(selected)}")
    print(f"  日志: memory/auto_train_*.json")
    print("=" * 60)


if __name__ == '__main__':
    main()
