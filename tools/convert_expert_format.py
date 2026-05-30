# -*- coding: utf-8 -*-
"""
专家档案格式转换器

将 expert-library 项目的百科格式转换为圆桌会议项目的三层架构格式。

用法：
  python tools/convert_expert_format.py --source D:\vibe_coding\zhengliu\expert-library\experts --target expert-library\experts
"""

import os
import re
import argparse
from typing import Dict, List, Optional


def parse_source_format(content: str) -> Dict:
    """解析 expert-library 的百科格式"""
    result = {
        'name': '',
        'domain': '',
        'mbti': '',
        'era': '',
        'nationality': '',
        'identity': '',
        'stance': '',
        'beliefs': [],
        'values': [],
        'thinking_style': '',
        'argument_style': '',
        'key_quotes': [],
        'classic_cases': [],
    }

    # 姓名
    name_match = re.search(r'^# (.+?)（[^）]+）专家档案', content)
    if name_match:
        result['name'] = name_match.group(1).strip()
    else:
        name_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if name_match:
            result['name'] = name_match.group(1).strip()

    # 基本信息
    domain_match = re.search(r'\*\*领域\*\*\s*\|\s*([^|]+)', content)
    if domain_match:
        result['domain'] = domain_match.group(1).strip()

    mbti_match = re.search(r'\*\*MBTI\*\*\s*\|\s*([^|]+)', content)
    if mbti_match:
        result['mbti'] = mbti_match.group(1).strip()

    era_match = re.search(r'\*\*时代\*\*\s*\|\s*([^|]+)', content)
    if era_match:
        result['era'] = era_match.group(1).strip()

    nationality_match = re.search(r'\*\*国籍\*\*\s*\|\s*([^|]+)', content)
    if nationality_match:
        result['nationality'] = nationality_match.group(1).strip()

    identity_match = re.search(r'\*\*主要身份\*\*\s*\|\s*([^|]+)', content)
    if identity_match:
        result['identity'] = identity_match.group(1).strip()

    # 核心立场
    stance_match = re.search(r'\*\*"(.+?)"\*\*', content)
    if stance_match:
        result['stance'] = stance_match.group(1).strip()

    # 核心理论/观点中的关键概念
    theories = re.findall(r'### \d+\. (.+?)——(.+?)\n', content)
    for theory_name, theory_desc in theories[:3]:
        result['beliefs'].append(f"{theory_name}: {theory_desc}")

    # 如果没有提取到信念，从核心立场提取
    if not result['beliefs'] and result['stance']:
        result['beliefs'] = [result['stance'][:100]]

    # 价值排序（从领域和身份推断）
    if result['domain']:
        domains = result['domain'].split('、')
        result['values'] = domains[:3]

    # 思维风格（从MBTI推断）
    if result['mbti']:
        mbti_style = result['mbti']
        if '直觉' in mbti_style or 'N' in mbti_style:
            result['thinking_style'] = '概念抽象'
        elif '感觉' in mbti_style or 'S' in mbti_style:
            result['thinking_style'] = '实证分析'
        elif '思考' in mbti_style or 'T' in mbti_style:
            result['thinking_style'] = '逻辑推理'
        elif '情感' in mbti_style or 'F' in mbti_style:
            result['thinking_style'] = '人文关怀'

    # 论证风格（从身份推断）
    if result['identity']:
        if '思想家' in result['identity'] or '哲学家' in result['identity']:
            result['argument_style'] = '哲学思辨'
        elif '科学家' in result['identity']:
            result['argument_style'] = '数据实证'
        elif '作家' in result['identity'] or '文学' in result['identity']:
            result['argument_style'] = '叙事隐喻'
        elif '企业家' in result['identity'] or '商业' in result['identity']:
            result['argument_style'] = '案例实战'
        else:
            result['argument_style'] = '综合论证'

    # 经典案例
    cases = re.findall(r'\*\*经典案例\*\*：\n(.+?)(?:\n\*\*来源|\n---|\n###)', content, re.DOTALL)
    for case in cases[:3]:
        case_clean = case.strip()[:200]
        if case_clean:
            result['classic_cases'].append(case_clean)

    return result


def generate_target_format(data: Dict, category: str) -> str:
    """生成圆桌会议项目的三层架构格式"""
    name = data['name']
    beliefs = data['beliefs'] if data['beliefs'] else ['待填充']
    values = data['values'] if data['values'] else ['待填充']
    thinking_style = data['thinking_style'] if data['thinking_style'] else '综合分析'
    argument_style = data['argument_style'] if data['argument_style'] else '综合论证'

    template = f"""# {name}

## 元信息

- **分类**: {category}
- **版本**: V1
- **训练次数**: 0
- **最后训练**: 未训练
- **当前评分**: 0

---

## 第一层：灵魂层（永不改变）

> 训练不碰这一层。这是专家的"基因"。

### 核心信念

{chr(10).join(f'- {b}' for b in beliefs[:3])}

### 价值排序

{chr(10).join(f'{i+1}. {v}' for i, v in enumerate(values[:3]))}

### 思维底色

- **思维风格**: {thinking_style}
- **表达风格**: 待填充
- **论证偏好**: {argument_style}

### 代表身份

- **姓名**: {name}
- **身份**: {data.get('identity', '待填充')}
- **时代**: {data.get('era', '待填充')}
- **标签**: 待填充

---

## 第二层：策略层（训练升级的核心）

> 每次训练替换升级，保持恒定大小。这是专家的"武器库"。

### 分析框架

> 面对任何议题时的分析路径。

待填充

### 攻击模式

> 攻击对手论点的具体角度。

| 优先级 | 攻击角度 | 适用场景 | 杀伤力 |
|:---:|:---|:---|:---:|
| 1 | 待填充 | 待填充 | 待评估 |
| 2 | 待填充 | 待填充 | 待评估 |
| 3 | 待填充 | 待填充 | 待评估 |

### 防御模式

> 被攻击时的防御策略。

| 被攻击类型 | 防御策略 | 成功率 |
|:---|:---|:---:|
| 待填充 | 待填充 | 0% (待训练) |
| 待填充 | 待填充 | 0% (待训练) |

---

## 第三层：素材层（实战积累）

> 每次训练增量添加，不删除。这是专家的"弹药库"。

### 金句库（6条）

> 最犀利、最像这个人会说的话。

1. 待填充
2. 待填充
3. 待填充
4. 待填充
5. 待填充
6. 待填充

### 核心案例（3个）

> 能证明自己观点的真实案例。

1. 待填充
2. 待填充
3. 待填充

### 反例库（3个）

> 能反驳对手观点的真实案例。

1. 待填充
2. 待填充
3. 待填充

---

## 来源信息

- **原始档案**: expert-library 项目
- **转换时间**: 自动转换
- **原始格式**: 百科格式
"""
    return template


def convert_file(source_path: str, target_path: str, category: str):
    """转换单个文件"""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ 读取失败: {source_path} ({e})")
        return False

    data = parse_source_format(content)
    if not data['name']:
        print(f"  ❌ 无法提取姓名: {source_path}")
        return False

    target_content = generate_target_format(data, category)

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(target_content)

    print(f"  ✅ {data['name']} → {category}")
    return True


def convert_all(source_dir: str, target_dir: str):
    """批量转换所有专家"""
    count = 0

    # 分类映射
    category_map = {
        'business': 'economics',
        'chinese-intellectuals': 'literature',
        'cross-domain': 'philosophy',
        'economics': 'economics',
        'history': 'sociology',
        'philosophy': 'philosophy',
        'psychology': 'psychology',
        'science': 'philosophy',
        'self-help': 'psychology',
        'technology': 'literature',
    }

    for source_cat in os.listdir(source_dir):
        source_cat_dir = os.path.join(source_dir, source_cat)
        if not os.path.isdir(source_cat_dir):
            continue
        if source_cat in ['evaluation', 'templates']:
            continue

        target_cat = category_map.get(source_cat, source_cat)
        target_cat_dir = os.path.join(target_dir, target_cat)

        print(f"\n转换 [{source_cat}] → [{target_cat}]")

        for filename in os.listdir(source_cat_dir):
            if not filename.endswith('.md'):
                continue

            source_path = os.path.join(source_cat_dir, filename)
            target_path = os.path.join(target_cat_dir, filename)

            if convert_file(source_path, target_path, target_cat):
                count += 1

    print(f"\n总计转换: {count} 位专家")
    return count


def main():
    parser = argparse.ArgumentParser(description='专家档案格式转换器')
    parser.add_argument('--source', type=str, required=True, help='源目录（expert-library/experts）')
    parser.add_argument('--target', type=str, required=True, help='目标目录（圆桌项目expert-library/experts）')
    args = parser.parse_args()

    convert_all(args.source, args.target)


if __name__ == '__main__':
    main()