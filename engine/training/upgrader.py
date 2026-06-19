# -*- coding: utf-8 -*-
"""
替换式升级器：用提取的策略数据升级专家 .md 文件。

核心原则：
- 策略层：融合升级（旧+新 → 更强的版本）
- 素材层：精选替换（新增强的 → 淘汰弱的 → 总数不变）
- 灵魂层：不碰

用法：
    python engine/training/upgrader.py <expert_md> <strategy_json>
"""

import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional


# === 素材层容量限制 ===
MAX_SPEECHES = 5
MAX_CASES = 4
MAX_QUOTES = 6


def read_expert_md(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_expert_md(path: str, content: str):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def parse_version(content: str) -> int:
    """提取当前版本号"""
    m = re.search(r'\*\*版本\*\*:\s*V(\d+)', content)
    return int(m.group(1)) if m else 1


def parse_training_count(content: str) -> int:
    """提取训练次数"""
    m = re.search(r'\*\*训练次数\*\*:\s*(\d+)', content)
    return int(m.group(1)) if m else 0


def update_meta(content: str, version: int, training_count: int,
                score: float = None, topic: str = None) -> str:
    """更新元信息"""
    content = re.sub(
        r'\*\*版本\*\*:.*',
        f'**版本**: V{version}',
        content
    )
    content = re.sub(
        r'\*\*训练次数\*\*:.*',
        f'**训练次数**: {training_count}',
        content
    )
    content = re.sub(
        r'\*\*最后训练\*\*:.*',
        f'**最后训练**: {topic or "刚完成"}',
        content
    )
    if score is not None:
        content = re.sub(
            r'\*\*当前评分\*\*:.*',
            f'**当前评分**: {score:.1f}',
            content
        )
    return content


def upgrade_attack_patterns(content: str, strategy: Dict) -> str:
    """升级攻击模式表"""
    new_angle = strategy.get('attack_strategy', {})
    if not new_angle:
        return content

    # 找到攻击模式表格
    pattern = r'(\| 优先级 \| 攻击角度.*?\n(?:\|.*?\n)*)'
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return content

    table = m.group(1)
    # 解析现有行
    rows = [l for l in table.strip().split('\n') if l.startswith('|') and '优先级' not in l and '---' not in l]

    # 添加新角度
    new_row = f"| 新 | {new_angle.get('best_angle', '')} | {new_angle.get('applicable_when', '')} | {new_angle.get('kill_rating', '中')} |"

    if len(rows) >= 3:
        # 替换杀伤力最低的一行
        ratings = {'高': 3, '中': 2, '低': 1}
        weakest_idx = min(range(len(rows)),
                          key=lambda i: ratings.get(rows[i].split('|')[4].strip().rstrip(), 0))
        rows[weakest_idx] = new_row
    else:
        rows.append(new_row)

    # 重建表格
    new_table = "| 优先级 | 攻击角度 | 适用场景 | 杀伤力评级 |\n"
    new_table += "|--------|---------|---------|-----------|\n"
    for i, row in enumerate(rows):
        # 重新编号
        cells = [c.strip() for c in row.split('|') if c.strip()]
        if cells:
            cells[0] = str(i + 1)
            new_table += f"| {' | '.join(cells)} |\n"

    content = content[:m.start()] + new_table + content[m.end():]
    return content


def upgrade_defense_patterns(content: str, strategy: Dict) -> str:
    """升级防御模式表"""
    weakness = strategy.get('defense_weakness', {})
    if not weakness:
        return content

    broken_by = weakness.get('broken_by', '')
    fix = weakness.get('fix_strategy', '')

    if not broken_by:
        return content

    # 找到防御模式表格
    pattern = r'(\| 被攻击类型 \| 化解策略.*?\n(?:\|.*?\n)*)'
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return content

    table = m.group(1)
    rows = [l for l in table.strip().split('\n') if l.startswith('|') and '被攻击' not in l and '---' not in l]

    # 检查是否已有同类防御
    found = False
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.split('|') if c.strip()]
        if len(cells) >= 2 and broken_by in cells[0]:
            # 更新成功率
            old_rate = cells[2] if len(cells) > 2 else '0%'
            old_num = int(re.search(r'(\d+)', old_rate).group(1)) if re.search(r'(\d+)', old_rate) else 0
            new_rate = min(100, old_num + 20)  # 每次训练+20%
            cells[1] = fix
            cells[2] = f'{new_rate}%'
            rows[i] = '| ' + ' | '.join(cells) + ' |'
            found = True
            break

    if not found:
        new_row = f"| {broken_by} | {fix} | 20% |"
        if len(rows) >= 3:
            # 替换成功率最低的
            rates = []
            for row in rows:
                cells = [c.strip() for c in row.split('|') if c.strip()]
                rate = int(re.search(r'(\d+)', cells[2]).group(1)) if len(cells) > 2 and re.search(r'(\d+)', cells[2]) else 0
                rates.append(rate)
            weakest = rates.index(min(rates))
            rows[weakest] = new_row
        else:
            rows.append(new_row)

    # 重建表格
    new_table = "| 被攻击类型 | 化解策略 | 成功率 |\n"
    new_table += "|-----------|---------|--------|\n"
    for row in rows:
        new_table += row + '\n'

    content = content[:m.start()] + new_table + content[m.end():]
    return content


def upgrade_speeches(content: str, strategy: Dict) -> str:
    """升级精选发言（替换式）"""
    style = strategy.get('style_fingerprint', {})
    new_line = style.get('most_authentic_line', '')
    if not new_line:
        return content

    # 找到所有发言块
    pattern = r'#### 发言 (\d)\n\n- \*\*场景\*\*:.*?(?=#### 发言 \d|\n### )'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    if not matches:
        return content

    # 找到杀伤力最低的发言
    weakest_idx = 0
    weakest_kill = 999
    kill_map = {'高': 3, '中': 2, '低': 1}

    for i, m in enumerate(matches):
        block = m.group(0)
        kill_match = re.search(r'\*\*杀伤力\*\*:\s*(高|中|低)', block)
        kill_val = kill_map.get(kill_match.group(1), 0) if kill_match else 0
        if kill_val < weakest_kill:
            weakest_kill = kill_val
            weakest_idx = i

    # 用新发言替换最弱的
    old_block = matches[weakest_idx].group(0)
    num = re.search(r'发言 (\d)', old_block).group(1)
    topic = strategy.get('_topic', '训练讨论')
    opponent = style.get('weakest_line', '对手')  # placeholder

    new_block = f"""#### 发言 {num}

- **场景**: {topic}
- **对手**: 训练讨论
- **内容**: {new_line}
- **效果**: {style.get('why_authentic', '风格鲜明')}
- **杀伤力**: 中"""

    content = content[:matches[weakest_idx].start()] + new_block + content[matches[weakest_idx].end():]
    return content


def upgrade_quotes(content: str, strategy: Dict) -> str:
    """升级金句库（替换式）"""
    style = strategy.get('style_fingerprint', {})
    new_quote = style.get('most_authentic_line', '')
    if not new_quote:
        return content

    # 找到金句库
    pattern = r'### 金句库.*?\n\n((?:\d+\..*\n)+)'
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return content

    quotes_block = m.group(1)
    quotes = [l.strip() for l in quotes_block.strip().split('\n') if l.strip()]

    # 找到杀伤力最低的
    kill_map = {'高': 3, '中': 2, '低': 1}
    weakest_idx = 0
    weakest_kill = 999

    for i, q in enumerate(quotes):
        kill_match = re.search(r'杀伤力:\s*(高|中|低)', q)
        kill_val = kill_map.get(kill_match.group(1), 0) if kill_match else 0
        if kill_val < weakest_kill:
            weakest_kill = kill_val
            weakest_idx = i

    # 替换
    quotes[weakest_idx] = f'{weakest_idx + 1}. "{new_quote}" — 杀伤力: 中'

    # 重建
    new_quotes = '\n'.join(quotes)
    content = content[:m.start(1)] + new_quotes + content[m.end(1):]
    return content


def append_training_history(content: str, round_num: int, topic: str,
                            attack_eff: float, defense_rate: float, upgrades: str) -> str:
    """追加训练历史记录"""
    # 找到训练历史表格
    pattern = r'(\| 轮次 \| 日期 \|.*?\n(?:\|.*?\n)*)'
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return content

    from datetime import datetime
    date = datetime.now().strftime('%Y-%m-%d')

    new_row = f"| {round_num} | {date} | {topic} | {attack_eff:.0f}% | {defense_rate:.0f}% | {upgrades} |"

    table = m.group(1).rstrip('\n')
    # 替换占位行或追加
    if '| — | — |' in table:
        table = table.replace('| — | — | — | — | — | — |', new_row)
    else:
        table += '\n' + new_row

    content = content[:m.start()] + table + '\n' + content[m.end():]
    return content


def upgrade_expert(expert_md_path: str, strategy: Dict, topic: str = '训练',
                   score: float = None, attack_eff: float = None,
                   defense_rate: float = None) -> str:
    """
    主升级函数：替换式升级专家 .md

    Args:
        expert_md_path: 专家 .md 文件路径
        strategy: 提取的策略数据（来自 extractor）
        topic: 本轮讨论话题
        score: 本轮评分

    Returns:
        升级后的 .md 内容
    """
    content = read_expert_md(expert_md_path)

    # 1. 更新元信息
    version = parse_version(content) + 1
    training_count = parse_training_count(content) + 1
    content = update_meta(content, version, training_count, score, topic)

    # 2. 升级策略层
    content = upgrade_attack_patterns(content, strategy)
    content = upgrade_defense_patterns(content, strategy)

    # 3. 升级素材层（精选替换）
    strategy['_topic'] = topic
    content = upgrade_speeches(content, strategy)
    content = upgrade_quotes(content, strategy)

    # 4. 追加训练历史
    if attack_eff is None:
        attack_eff = 0.0
    if defense_rate is None:
        defense_rate = 0.0
    upgrades = strategy.get('attack_strategy', {}).get('best_angle', '策略优化')
    content = append_training_history(content, training_count, topic,
                                      attack_eff, defense_rate, upgrades)

    # 5. 写回文件
    write_expert_md(expert_md_path, content)

    return content


def main():
    if len(sys.argv) < 3:
        print("Usage: python upgrader.py <expert_md> <strategy_json>")
        sys.exit(1)

    expert_md = sys.argv[1]
    strategy_json = sys.argv[2]

    with open(strategy_json, 'r', encoding='utf-8') as f:
        strategy = json.load(f)

    result = upgrade_expert(expert_md, strategy)
    print(f"Upgraded: {expert_md}")
    print(f"New version: V{parse_version(result)}")


if __name__ == '__main__':
    main()
