# -*- coding: utf-8 -*-
"""
证据引用验证器 - 解决圆桌会议证据命中率低的问题

核心问题：
1. 证据命中率极低（4.5-7.4%）
2. 标准太窄：只认"第X章"、"情节"、"书中"
3. 通用话题（如"算法推荐"）没有配套书单
4. 生成阶段不强制要求引用

解决思路：
- 扩展证据类型判定（书籍引用、数据、案例、专家观点、理论、历史）
- 支持通用话题的特殊标准
- 提供详细的缺失证据报告
"""

import json
import re
from typing import Dict, List, Tuple
from pathlib import Path

# ========== 证据类型正则模式 ==========
EVIDENCE_PATTERNS = {
    "book_reference": r"第[一二三四五六七八九十\d]+章|书中提到|原文|页码|章节|写道|记载|描述",
    "data": r"\d+%|\d+万|\d+亿|\d+元|\d+美元|\d+人|\d+年|\d+次|\d+倍|\d+个",
    "case": r"案例|事件|丑闻|诉讼|调查|实验|研究|报告|分析|现象",
    "expert_quote": r"[\u4e00-\u9fff]{2,4}(?:说|认为|指出|发现|创立|发明|提出|强调|警告)",
    "theory": r"理论|模型|框架|假说|定律|原则|效应|机制|范式",
    "historical": r"\d{4}年|历史上|曾经|过去|早期|近年来|年代|时期|阶段",
}

# 编译正则以提高性能
_COMPILED_PATTERNS = {k: re.compile(v) for k, v in EVIDENCE_PATTERNS.items()}

# 话题类型关键词
BOOK_BASED_KEYWORDS = [
    "《", "书", "小说", "作者", "主人公", "主角", "情节", "故事", "叙事",
    "读后感", "书评", "文学", "作品", "著作", "文本"
]

TOPIC_BASED_KEYWORDS = [
    "算法", "推荐", "数字", "游民", "AI", "人工智能", "资本", "消费",
    "内卷", "躺平", "焦虑", "抑郁", "孤独", "社交", "媒体", "信息",
    "工作", "职场", "生活", "方式", "主义", "时代", "社会", "文化",
    "心理", "认知", "思维", "决策", "行为", "习惯", "效率", "生产力"
]


def get_topic_type(title: str) -> str:
    """
    判断话题类型：book_based / topic_based / hybrid

    Args:
        title: 讨论标题

    Returns:
        "book_based" - 基于具体书籍的讨论
        "topic_based" - 通用概念/话题讨论
        "hybrid" - 混合类型
    """
    title_lower = title.lower()

    has_book = any(kw in title_lower for kw in BOOK_BASED_KEYWORDS)
    has_topic = any(kw in title_lower for kw in TOPIC_BASED_KEYWORDS)

    # 有书名号《》直接判定为 book_based
    if "《" in title and "》" in title:
        return "book_based"

    if has_book and not has_topic:
        return "book_based"
    elif has_topic and not has_book:
        return "topic_based"
    elif has_book and has_topic:
        return "hybrid"
    else:
        # 默认保守策略：如果无法判断，视为 topic_based（标准更宽松）
        return "topic_based"


def detect_evidence_types(text: str) -> Dict[str, bool]:
    """
    检测文本中包含的证据类型

    Args:
        text: 发言内容

    Returns:
        Dict[str, bool] - 各证据类型是否存在
    """
    return {
        name: bool(pattern.search(text))
        for name, pattern in _COMPILED_PATTERNS.items()
    }


def has_evidence(text: str, topic_type: str = "book_based") -> Tuple[bool, List[str]]:
    """
    判断发言是否包含有效证据

    Args:
        text: 发言内容
        topic_type: 话题类型，影响判定标准

    Returns:
        (是否有证据, 证据类型列表)
    """
    evidence_types = detect_evidence_types(text)
    found_types = [k for k, v in evidence_types.items() if v]

    if topic_type == "book_based":
        # 书籍讨论：至少要有书籍引用，或其他2种证据
        has_book = evidence_types.get("book_reference", False)
        other_count = len(found_types) - (1 if has_book else 0)
        if has_book or other_count >= 2:
            return True, found_types
        return False, found_types

    elif topic_type == "topic_based":
        # 通用话题：至少1种证据即可（标准放宽）
        if len(found_types) >= 1:
            return True, found_types
        return False, found_types

    else:  # hybrid
        # 混合类型：至少1种证据，有书籍引用更好
        if len(found_types) >= 1:
            return True, found_types
        return False, found_types


def extract_speeches(data: Dict) -> List[Dict]:
    """
    从V8 JSON中提取所有发言

    V8结构：
    - rounds: List[DiscussionRound]
      - stances: List[Dict] (round 1)
      - clash_rounds: List[ClashRound] (round 2)
      - reality_cases: List[RealityCase] (round 3)
      - cost_discussion: CostDiscussion (round 4)
      - human_nature: HumanNatureLayer (round 5)
      - cognitive_upgrade: CognitiveUpgrade (round 6)
    """
    speeches = []

    for round_data in data.get("rounds", []):
        round_num = round_data.get("round_number", 0)

        # Round 1: 立场表达
        for stance in round_data.get("stances", []):
            speeches.append({
                "round": round_num,
                "type": "stance",
                "expert": stance.get("expert", "未知"),
                "content": stance.get("content", ""),
            })

        # Round 2: 碰撞轮次
        for clash in round_data.get("clash_rounds", []):
            speeches.append({
                "round": round_num,
                "type": "attack",
                "expert": clash.get("attacker", "未知"),
                "content": clash.get("attack_content", ""),
            })
            if clash.get("counter_attack"):
                speeches.append({
                    "round": round_num,
                    "type": "counter",
                    "expert": clash.get("target", "未知"),
                    "content": clash["counter_attack"],
                })

        # Round 3: 现实案例
        for case in round_data.get("reality_cases", []):
            speeches.append({
                "round": round_num,
                "type": "case",
                "expert": "案例",
                "content": case.get("case_content", ""),
            })

        # Round 4: 代价讨论
        cost = round_data.get("cost_discussion", {})
        if cost:
            speeches.append({
                "round": round_num,
                "type": "cost",
                "expert": "代价分析",
                "content": cost.get("scenario", "") + " " + str(cost.get("cost_analysis", "")),
            })

        # Round 5: 人性层
        human = round_data.get("human_nature", {})
        if human:
            speeches.append({
                "round": round_num,
                "type": "human_nature",
                "expert": "人性分析",
                "content": human.get("psychological_analysis", "") + " " + " ".join(human.get("real_examples", [])),
            })

        # Round 6: 认知升级
        cognitive = round_data.get("cognitive_upgrade", {})
        if cognitive:
            speeches.append({
                "round": round_num,
                "type": "cognitive",
                "expert": "认知升级",
                "content": cognitive.get("new_thinking", "") + " " + cognitive.get("actionable_insight", ""),
            })

    return speeches


def validate_evidence(json_path: str) -> Dict:
    """
    验证讨论JSON中的证据引用质量

    Args:
        json_path: V8 JSON文件路径

    Returns:
        {
            "total_speeches": int,
            "with_evidence": int,
            "evidence_hit_rate": float,
            "missing_evidence": List[Dict],
            "evidence_types": Dict[str, int],
            "grade": str,  # A/B/C/D/F
        }
    """
    # 读取JSON
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {json_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 判断话题类型
    title = data.get("title", "")
    topic_type = get_topic_type(title)

    # 提取所有发言
    speeches = extract_speeches(data)

    total = len(speeches)
    with_evidence_count = 0
    missing_evidence = []
    evidence_type_counts = {k: 0 for k in EVIDENCE_PATTERNS.keys()}

    for speech in speeches:
        has_evi, found_types = has_evidence(speech["content"], topic_type)

        if has_evi:
            with_evidence_count += 1
            for t in found_types:
                evidence_type_counts[t] += 1
        else:
            missing_evidence.append({
                "round": speech["round"],
                "type": speech["type"],
                "expert": speech["expert"],
                "content_preview": speech["content"][:100] + "..." if len(speech["content"]) > 100 else speech["content"],
            })

    # 计算命中率
    hit_rate = (with_evidence_count / total * 100) if total > 0 else 0.0

    # 评级
    if hit_rate >= 80:
        grade = "A"
    elif hit_rate >= 60:
        grade = "B"
    elif hit_rate >= 40:
        grade = "C"
    elif hit_rate >= 20:
        grade = "D"
    else:
        grade = "F"

    return {
        "title": title,
        "topic_type": topic_type,
        "total_speeches": total,
        "with_evidence": with_evidence_count,
        "evidence_hit_rate": round(hit_rate, 2),
        "missing_evidence": missing_evidence,
        "evidence_types": evidence_type_counts,
        "grade": grade,
    }


def batch_validate(directory: str) -> List[Dict]:
    """
    批量验证目录下所有V8 JSON文件

    Args:
        directory: 包含JSON文件的目录

    Returns:
        List[Dict] - 每个文件的验证结果
    """
    results = []
    dir_path = Path(directory)

    for json_file in dir_path.glob("*.json"):
        try:
            result = validate_evidence(str(json_file))
            results.append(result)
        except Exception as e:
            results.append({
                "file": str(json_file),
                "error": str(e),
            })

    return results


def print_report(result: Dict) -> None:
    """打印验证报告"""
    print("=" * 60)
    print(f"📊 证据引用验证报告")
    print("=" * 60)
    print(f"标题: {result.get('title', 'N/A')}")
    print(f"话题类型: {result.get('topic_type', 'N/A')}")
    print(f"总发言数: {result['total_speeches']}")
    print(f"含证据发言: {result['with_evidence']}")
    print(f"证据命中率: {result['evidence_hit_rate']}%")
    print(f"评级: {result['grade']}")
    print("-" * 60)
    print("证据类型分布:")
    for etype, count in result["evidence_types"].items():
        print(f"  - {etype}: {count}")
    print("-" * 60)

    if result["missing_evidence"]:
        print(f"⚠️ 缺少证据的发言 ({len(result['missing_evidence'])}条):")
        for i, miss in enumerate(result["missing_evidence"][:5], 1):
            print(f"  {i}. [{miss['type']}] {miss['expert']} (Round {miss['round']})")
            print(f"     预览: {miss['content_preview']}")
        if len(result["missing_evidence"]) > 5:
            print(f"     ... 还有 {len(result['missing_evidence']) - 5} 条")
    else:
        print("✅ 所有发言都包含证据！")
    print("=" * 60)


# ========== 测试代码 ==========
if __name__ == "__main__":
    # 测试1: 使用模拟数据测试
    print("🧪 运行证据验证器测试...\n")

    # 模拟V8 JSON数据
    mock_data = {
        "title": "《倦怠社会》中的算法推荐困境",
        "experts": [{"name": "专家A"}, {"name": "专家B"}],
        "rounds": [
            {
                "round_number": 1,
                "stances": [
                    {
                        "expert": "专家A",
                        "content": "韩炳哲在《倦怠社会》第3章中指出，功绩社会下的自我剥削比外部剥削更高效。"
                    },
                    {
                        "expert": "专家B",
                        "content": "我认为这个问题需要从另一个角度来看。"  # 无证据
                    }
                ],
                "clash_rounds": [
                    {
                        "attacker": "专家A",
                        "target": "专家B",
                        "attack_content": "2023年的数据显示，超过70%的Z世代每天使用推荐算法超过3小时。"
                    }
                ],
                "reality_cases": [
                    {
                        "case_content": "TikTok算法推荐导致的注意力碎片化案例已经被广泛研究。"
                    }
                ],
                "cost_discussion": {
                    "scenario": "如果完全依赖算法推荐",
                    "cost_analysis": [{"cost": "认知能力下降"}, {"cost": "信息茧房固化"}]
                },
                "human_nature": {
                    "psychological_analysis": "多巴胺驱动的即时满足机制让人难以抗拒算法推荐。",
                    "real_examples": ["刷短视频停不下来", "不断刷新信息流"]
                },
                "cognitive_upgrade": {
                    "new_thinking": "我们需要建立主动的信息筛选机制。",
                    "actionable_insight": "每天设定30分钟的无算法阅读时间。"
                }
            }
        ],
        "final_insight": "算法推荐是工具，关键在于使用者的自觉。",
        "open_questions": ["如何平衡效率与多样性？"]
    }

    # 写入临时文件进行测试
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    try:
        result = validate_evidence(temp_path)
        print_report(result)

        # 断言验证
        assert result["total_speeches"] == 7, f"期望7条发言，实际{result['total_speeches']}"
        assert result["with_evidence"] >= 2, f"期望至少2条有证据，实际{result['with_evidence']}"
        assert result["topic_type"] == "book_based", f"期望book_based，实际{result['topic_type']}"
        assert result["evidence_hit_rate"] > 0, "命中率应大于0"

        print("\n✅ 所有测试通过！")

    finally:
        import os
        os.unlink(temp_path)

    # 测试2: 通用话题
    print("\n🧪 测试通用话题...")
    mock_topic_data = {
        "title": "数字游民的生活方式",
        "experts": [{"name": "专家A"}],
        "rounds": [
            {
                "round_number": 1,
                "stances": [
                    {
                        "expert": "专家A",
                        "content": "2024年调查显示，全球数字游民已超过4000万人。"
                    }
                ],
                "clash_rounds": [],
                "reality_cases": [],
                "cost_discussion": {},
                "human_nature": {},
                "cognitive_upgrade": {}
            }
        ],
        "final_insight": "",
        "open_questions": []
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(mock_topic_data, f, ensure_ascii=False, indent=2)
        temp_path2 = f.name

    try:
        result2 = validate_evidence(temp_path2)
        print_report(result2)
        assert result2["topic_type"] == "topic_based", f"期望topic_based，实际{result2['topic_type']}"
        print("\n✅ 通用话题测试通过！")
    finally:
        os.unlink(temp_path2)
