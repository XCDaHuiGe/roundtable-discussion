# -*- coding: utf-8 -*-
"""
策略提取器：从讨论 JSON 中提取每位专家的战斗策略数据。

用法：
    python engine/training/extractor.py <json_path> [--output <output_path>]

提取5类策略数据：
    1. 攻击策略 - 最有效的攻击角度
    2. 防御弱点 - 被什么角度击穿
    3. 证据偏好 - 什么类型证据最有说服力
    4. 交互模式 - 和谁碰撞最有效
    5. 风格指纹 - 最像这个人会说的话
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def load_discussion(json_path: str) -> Dict:
    """加载讨论 JSON，兼容 utf-8-sig 编码"""
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'title' in data:
        data['title'] = data['title'].lstrip('\ufeff')
    return data


def extract_experts(data: Dict) -> List[Dict]:
    """提取专家列表"""
    experts = data.get('experts', [])
    if not experts:
        # 尝试从 rounds 中提取
        for r in data.get('rounds', []):
            for s in r.get('stances', []):
                name = s.get('expert', '')
                if name and not any(e.get('name') == name for e in experts):
                    experts.append({'name': name, 'role': ''})
    return experts


def extract_expert_speeches(data: Dict, expert_name: str) -> List[Dict]:
    """提取某位专家的所有发言"""
    speeches = []
    for r in data.get('rounds', []):
        # 从 stances 中提取
        for s in r.get('stances', []):
            if s.get('expert') == expert_name:
                speeches.append({
                    'type': 'stance',
                    'round': r.get('round_number', 0),
                    'topic': r.get('topic', ''),
                    'content': s.get('stance', ''),
                    'emotion': s.get('emotion', 'serious')
                })
        # 从 clash_rounds 中提取（作为攻击方或防守方）
        for c in r.get('clash_rounds', []):
            if c.get('attacker') == expert_name:
                speeches.append({
                    'type': 'attack',
                    'round': r.get('round_number', 0),
                    'topic': r.get('topic', ''),
                    'target': c.get('target', ''),
                    'attack_type': c.get('attack_type', ''),
                    'content': c.get('attack_content', ''),
                    'emotion': c.get('emotion', 'serious')
                })
            if c.get('target') == expert_name and c.get('counter_attack'):
                speeches.append({
                    'type': 'defense',
                    'round': r.get('round_number', 0),
                    'topic': r.get('topic', ''),
                    'attacker': c.get('attacker', ''),
                    'content': c.get('counter_attack', ''),
                    'emotion': c.get('counter_emotion', 'serious')
                })
    return speeches


def extract_all_interactions(data: Dict) -> List[Dict]:
    """提取所有碰撞交互（用于分析交互模式）"""
    interactions = []
    for r in data.get('rounds', []):
        for c in r.get('clash_rounds', []):
            interactions.append({
                'round': r.get('round_number', 0),
                'topic': r.get('topic', ''),
                'attacker': c.get('attacker', ''),
                'target': c.get('target', ''),
                'attack_type': c.get('attack_type', ''),
                'attack_content': c.get('attack_content', ''),
                'counter_attack': c.get('counter_attack', ''),
                'has_counter': bool(c.get('counter_attack'))
            })
    return interactions


def build_extraction_prompt(expert_name: str, speeches: List[Dict],
                            interactions: List[Dict], book_title: str) -> str:
    """构建策略提取的 AI 提示词"""
    # 分类发言
    stances = [s for s in speeches if s['type'] == 'stance']
    attacks = [s for s in speeches if s['type'] == 'attack']
    defenses = [s for s in speeches if s['type'] == 'defense']

    # 找到该专家参与的交互
    expert_interactions = [
        i for i in interactions
        if i['attacker'] == expert_name or i['target'] == expert_name
    ]

    prompt = f"""分析专家「{expert_name}」在《{book_title}》圆桌讨论中的表现，提取5类战斗策略数据。

## 本轮发言数据

### 立场发言（{len(stances)}条）
"""
    for s in stances:
        prompt += f"- Round {s['round']} [{s['topic']}]: {s['content'][:200]}...\n"

    prompt += f"\n### 攻击发言（{len(attacks)}条）\n"
    for a in attacks:
        prompt += f"- Round {a['round']} → {a['target']} [{a['attack_type']}]: {a['content'][:200]}...\n"

    prompt += f"\n### 防御发言（{len(defenses)}条）\n"
    for d in defenses:
        prompt += f"- Round {d['round']} ← {d['attacker']}: {d['content'][:200]}...\n"

    prompt += f"\n### 碰撞交互（{len(expert_interactions)}条）\n"
    for i in expert_interactions:
        role = '攻击方' if i['attacker'] == expert_name else '防守方'
        prompt += f"- {i['attacker']} → {i['target']} [{i['attack_type']}] ({role})\n"

    prompt += """
## 请提取以下5类策略数据（JSON格式）

```json
{
  "attack_strategy": {
    "best_angle": "本轮最有效的攻击角度是什么",
    "why_effective": "为什么这个角度有效",
    "applicable_when": "对手说什么时用这个角度",
    "kill_rating": "高/中/低"
  },
  "defense_weakness": {
    "broken_by": "本轮被什么角度击穿了",
    "why_vulnerable": "为什么在这个角度上脆弱",
    "fix_strategy": "下次如何防御这个角度"
  },
  "evidence_preference": {
    "most_effective_type": "什么类型的证据最有说服力",
    "ranking": ["类型1", "类型2", "类型3"],
    "best_example": "本轮最好的证据引用是什么"
  },
  "interaction_pattern": {
    "best_opponent": "和谁的碰撞最有效",
    "why_effective": "为什么和这个人碰撞最有效",
    "worst_opponent": "和谁的碰撞最无效",
    "why_weak": "为什么和这个人碰撞效果差"
  },
  "style_fingerprint": {
    "most_authentic_line": "本轮最像这个人会说的话",
    "why_authentic": "为什么这句话最像他",
    "weakest_line": "本轮最不像这个人会说的话",
    "why_weak": "为什么这句话不像他"
  }
}
```

要求：
1. 每个字段必须基于实际发言内容，不能编造
2. 引用发言时保留原文
3. 评估要客观，不好也不坏的就说"中等"
4. 风格指纹要能区分"这个人说的"和"任何人可能说的"
"""
    return prompt


def extract(json_path: str, output_path: str = None) -> Dict:
    """主提取函数"""
    data = load_discussion(json_path)
    book_title = data.get('title', '未知')
    experts = extract_experts(data)
    interactions = extract_all_interactions(data)

    result = {
        'book_title': book_title,
        'source_file': json_path,
        'experts': {}
    }

    for expert in experts:
        name = expert.get('name', '')
        if not name:
            continue
        speeches = extract_expert_speeches(data, name)
        prompt = build_extraction_prompt(name, speeches, interactions, book_title)
        result['experts'][name] = {
            'expert_info': expert,
            'speech_count': len(speeches),
            'speeches': speeches,
            'extraction_prompt': prompt
        }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Extraction prompts saved: {output_path}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <json_path> [--output <output_path>]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = None
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    if not output_path:
        base = Path(json_path).stem
        output_path = f"content/{base}_extraction.json"

    extract(json_path, output_path)


if __name__ == '__main__':
    main()
