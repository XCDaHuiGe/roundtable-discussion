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
import re
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


def compute_strategy_data(speeches: List[Dict], interactions: List[Dict],
                          expert_name: str) -> Dict:
    """从原始发言和碰撞数据中计算结构化策略数据。

    这是进化引擎需要的输入格式：attack_strategy / defense_weakness / style_fingerprint
    
    升级：即使没有counter_attack，也能从stance发言中提取策略
    """
    attacks = [s for s in speeches if s['type'] == 'attack']
    defenses = [s for s in speeches if s['type'] == 'defense']
    stances = [s for s in speeches if s['type'] == 'stance']

    # === 攻击策略：从攻击发言或stance发言中提取 ===
    attack_strategy = {'best_angle': '', 'applicable_when': '', 'kill_rating': '中'}
    
    # 如果有攻击发言，从中提取
    if attacks:
        best_attack = max(attacks, key=lambda a: len(a.get('content', '')))
        content = best_attack.get('content', '')
        attack_type = best_attack.get('attack_type', '')
        target = best_attack.get('target', '')
        angle = attack_type if attack_type else content[:80].replace('\n', ' ')
        rating = '高' if len(content) > 300 else '中' if len(content) > 100 else '低'
        attack_strategy = {
            'best_angle': angle,
            'applicable_when': f'对手({target})立场偏激时' if target else '对手立场偏激时',
            'kill_rating': rating,
        }
    # 如果没有攻击发言，从stance中寻找反驳内容
    elif stances:
        for s in stances:
            content = s.get('content', '')
            # 检查是否包含反驳关键词
            if any(kw in content for kw in ['但是', '然而', '问题是', '你说的', '我不认同', '不同意']):
                angle = content[:80].replace('\n', ' ')
                rating = '高' if len(content) > 300 else '中'
                attack_strategy = {
                    'best_angle': angle,
                    'applicable_when': '对手观点有明显漏洞时',
                    'kill_rating': rating,
                }
                break

    # === 阿御弱点：从防御发言或被攻击的stance中提取 ===
    defense_weakness = {'broken_by': '', 'fix_strategy': ''}
    
    # 如果有防御发言，从中提取
    if defenses:
        weakest_defense = min(defenses, key=lambda d: len(d.get('content', '')))
        attacker = weakest_defense.get('attacker', '')
        defense_weakness = {
            'broken_by': attacker if attacker else '逻辑漏洞',
            'fix_strategy': weakest_defense.get('content', '')[:100] if weakest_defense.get('content') else '需要更充分的论据',
        }
    # 如果没有防御发言，从交互中找被攻击的记录
    elif interactions:
        # 找到该专家作为target的交互
        as_target = [i for i in interactions if i.get('target') == expert_name]
        if as_target:
            # 被攻击但没有反击，说明防御失败
            attack = as_target[0]
            attack_type = attack.get('attack_type', '逻辑漏洞')
            defense_weakness = {
                'broken_by': attack_type,
                'fix_strategy': '需要准备针对此类攻击的回应',
            }

    # === 风格指纹：最像这个人会说的话 ===
    style_fingerprint = {'most_authentic_line': '', 'weakest_line': ''}
    all_contents = [s.get('content', '') for s in speeches if s.get('content')]
    if all_contents:
        # 最有深度的发言 = 最长的
        best_line = max(all_contents, key=len)
        # 最弱的发言 = 最短的（排除空的）
        non_empty = [c for c in all_contents if len(c) > 20]
        worst_line = min(non_empty, key=len) if non_empty else ''
        style_fingerprint = {
            'most_authentic_line': best_line,
            'weakest_line': worst_line,
        }

    # === 证据偏好 ===
    evidence_preference = {'most_effective_type': '', 'ranking': []}
    evidence_types = []
    for s in speeches:
        content = s.get('content', '')
        if re.search(r'\d+%|\d+万|\d+亿|\d+美元', content):
            evidence_types.append('数据')
        if re.search(r'第.{1,3}章|情节|原文|书中', content):
            evidence_types.append('文本引用')
        if re.search(r'案例|比如|例如|事实上', content):
            evidence_types.append('案例')
        if re.search(r'就像|好比|本质上|说白了', content):
            evidence_types.append('类比隐喻')
    if evidence_types:
        from collections import Counter
        counts = Counter(evidence_types)
        ranking = [t for t, _ in counts.most_common()]
        evidence_preference = {
            'most_effective_type': ranking[0] if ranking else '',
            'ranking': ranking,
        }

    # === 交互模式 ===
    interaction_pattern = {'best_opponent': '', 'worst_opponent': ''}
    expert_interactions = [
        i for i in interactions
        if i['attacker'] == expert_name or i['target'] == expert_name
    ]
    if expert_interactions:
        # 有counter_attack的交互 = 成功防御 = 好对手
        successful = [i for i in expert_interactions if i.get('has_counter')]
        failed = [i for i in expert_interactions if not i.get('has_counter')]
        if successful:
            best_opp = successful[0]
            interaction_pattern['best_opponent'] = (
                best_opp['target'] if best_opp['attacker'] == expert_name else best_opp['attacker']
            )
        if failed:
            worst_opp = failed[0]
            interaction_pattern['worst_opponent'] = (
                worst_opp['target'] if worst_opp['attacker'] == expert_name else worst_opp['attacker']
            )

    return {
        'attack_modes': [{'angle': attack_strategy['best_angle'],
                          'scenario': attack_strategy['applicable_when'],
                          'rating': attack_strategy['kill_rating']}] if attack_strategy['best_angle'] else [],
        'attack_strategy': attack_strategy,
        'defense_weakness': defense_weakness,
        'style_fingerprint': style_fingerprint,
        'evidence_preference': evidence_preference,
        'interaction_pattern': interaction_pattern,
        'speeches': all_contents,
    }


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
        strategy_data = compute_strategy_data(speeches, interactions, name)
        prompt = build_extraction_prompt(name, speeches, interactions, book_title)
        result['experts'][name] = {
            'expert_info': expert,
            'speech_count': len(speeches),
            'speeches': speeches,
            'extraction_prompt': prompt,
            'attack_modes': strategy_data['attack_modes'],
            'attack_strategy': strategy_data['attack_strategy'],
            'defense_weakness': strategy_data['defense_weakness'],
            'style_fingerprint': strategy_data['style_fingerprint'],
            'evidence_preference': strategy_data['evidence_preference'],
            'interaction_pattern': strategy_data['interaction_pattern'],
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
