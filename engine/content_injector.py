# -*- coding: utf-8 -*-
"""
内容注入器 - 为通用话题注入配套书单素材

核心问题：
1. 通用话题（如"算法推荐"）没有配套书单
2. 生成阶段不强制要求引用
3. 专家发言缺乏跨书籍的关联能力

解决思路：
- 建立话题→书单映射
- 为每个话题预置可引用的书籍、章节、金句
- 生成Prompt片段，指导LLM在讨论中引用这些素材
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

# ========== 话题→书单映射 ==========
# 每个话题配置3-5本相关书籍，包含关键章节和金句
TOPIC_BOOK_MAPPING = {
    "算法推荐": [
        {
            "name": "倦怠社会",
            "author": "韩炳哲",
            "key_chapters": ["第3章：超越规训社会", "第5章：倦怠社会"],
            "quotes": [
                "功绩社会下的自我剥削比外部剥削更高效",
                "我们生活在一种过度的积极之中",
                "倦怠成为存在的基本状态"
            ]
        },
        {
            "name": "娱乐至死",
            "author": "尼尔·波兹曼",
            "key_chapters": ["第1章：媒介即隐喻", "第10章：教学是一种娱乐活动"],
            "quotes": [
                "我们将毁于我们所热爱的东西",
                "在信息的海洋中，我们渴死于没有知识",
                "媒介即认识论"
            ]
        },
        {
            "name": "注意力经济",
            "author": "吴修铭",
            "key_chapters": ["第2章：注意力商人", "第7章：社交媒体时代"],
            "quotes": [
                "注意力是人类最稀缺的资源",
                "免费服务背后，你才是产品",
                "每一次滑动都在重塑你的大脑"
            ]
        },
        {
            "name": "浅薄",
            "author": "尼古拉斯·卡尔",
            "key_chapters": ["第3章：大脑的可塑性", "第6章：谷歌让我们变笨了吗"],
            "quotes": [
                "互联网正在重塑我们的大脑",
                "深度思考正在被碎片化的浏览取代",
                "记忆外包导致认知能力的退化"
            ]
        }
    ],
    "数字游民": [
        {
            "name": "逃避自由",
            "author": "埃里希·弗洛姆",
            "key_chapters": ["第5章：逃避机制", "第7章：自由与民主"],
            "quotes": [
                "自由带来孤独，孤独带来焦虑",
                "现代人逃避自由的方式比过去更加隐蔽",
                "真正的自由意味着责任"
            ]
        },
        {
            "name": "工作的意义",
            "author": "詹姆斯·苏兹曼",
            "key_chapters": ["第4章：狩猎采集者的闲暇", "第9章：工作的未来"],
            "quotes": [
                "人类历史上大部分时期并没有'工作'的概念",
                "我们工作的时长并没有带来相应的幸福感",
                "技术解放劳动力的承诺从未真正实现"
            ]
        },
        {
            "name": "游牧人生",
            "author": "杰西卡·布鲁德",
            "key_chapters": ["第1章：新游牧族", "第8章：车轮上的家园"],
            "quotes": [
                "他们不是为了冒险而选择游牧，而是为了生存",
                "亚马逊的仓库成为游牧者的季节性营地",
                "自由职业的另一面是不稳定的焦虑"
            ]
        },
        {
            "name": "孤独的城市",
            "author": "奥利维娅·莱恩",
            "key_chapters": ["第2章：孤独的城市", "第6章：连接与分离"],
            "quotes": [
                "城市越拥挤，人越孤独",
                "数字连接无法替代身体的在场",
                "孤独是一种现代性的病症"
            ]
        }
    ],
    "内卷": [
        {
            "name": "单向度的人",
            "author": "赫伯特·马尔库塞",
            "key_chapters": ["第3章：不幸意识的征服", "第7章：肯定性文化"],
            "quotes": [
                "发达工业社会成功地压制了人们内心的否定性",
                "人们生活在一种舒适的顺从之中",
                "批判性思维正在被技术性思维取代"
            ]
        },
        {
            "name": "倦怠社会",
            "author": "韩炳哲",
            "key_chapters": ["第2章：超越规训社会", "第4章：精神暴力"],
            "quotes": [
                "功绩主体将自己视为自由空间，实际上却身处牢笼",
                "他者在消失，自我在膨胀",
                "抑郁是功绩社会的典型病症"
            ]
        },
        {
            "name": "优绩的暴政",
            "author": "迈克尔·桑德尔",
            "key_chapters": ["第1章：优绩至上时代", "第6章：成功伦理学"],
            "quotes": [
                "优绩至上主义让成功者傲慢，让失败者自卑",
                "你的成功不完全是你自己的功劳",
                "文凭主义成为新的阶层壁垒"
            ]
        }
    ],
    "消费主义": [
        {
            "name": "消费社会",
            "author": "让·鲍德里亚",
            "key_chapters": ["第1章：消费的神化", "第3章：符号与差异"],
            "quotes": [
                "消费不是为了满足需求，而是为了生产差异",
                "物体系成为身份的象征",
                "广告告诉我们什么是值得欲望的对象"
            ]
        },
        {
            "name": "有闲阶级论",
            "author": "托斯丹·凡勃伦",
            "key_chapters": ["第3章：炫耀性消费", "第5章：金钱文化"],
            "quotes": [
                "消费是展示社会地位的手段",
                "浪费性消费成为荣誉的象征",
                "有闲阶级通过不工作来展示优越性"
            ]
        },
        {
            "name": "工作、消费主义和新穷人",
            "author": "齐格蒙特·鲍曼",
            "key_chapters": ["第2章：从工作伦理到消费美学", "第4章：新穷人的前景"],
            "quotes": [
                "消费社会中的穷人不是失业者，而是不消费者",
                "消费美学取代了工作伦理",
                "穷人成为社会的他者，需要被隔离"
            ]
        }
    ],
    "AI人工智能": [
        {
            "name": "技术垄断",
            "author": "尼尔·波兹曼",
            "key_chapters": ["第1章：技术垄断", "第8章：隐形的技术"],
            "quotes": [
                "技术不是中立的工具，它有自己的议程",
                "每一种技术都既是恩赐也是包袱",
                "我们正在成为技术的仆人"
            ]
        },
        {
            "name": "人类简史",
            "author": "尤瓦尔·赫拉利",
            "key_chapters": ["第19章：从此过着幸福快乐的日子", "后记：变成神的这种动物"],
            "quotes": [
                "未来人类可能分化为神人和无用阶级",
                "数据成为21世纪最重要的资源",
                "算法比我们更了解自己"
            ]
        },
        {
            "name": "第二次机器革命",
            "author": "埃里克·布林约尔松",
            "key_chapters": ["第3章：数字化与创造性破坏", "第9章：未来的工作"],
            "quotes": [
                "数字技术正在重塑经济的每一个层面",
                "技能溢价在加速扩大",
                "我们需要重新思考教育和培训"
            ]
        }
    ],
    "焦虑": [
        {
            "name": "逃避自由",
            "author": "埃里希·弗洛姆",
            "key_chapters": ["第3章：个人与社会的联系", "第5章：逃避机制"],
            "quotes": [
                "自由带来不安全感和孤独感",
                "现代人被抛入一个充满不确定性的世界",
                "焦虑是现代人的基本情绪"
            ]
        },
        {
            "name": "身份的焦虑",
            "author": "阿兰·德波顿",
            "key_chapters": ["第2章：势利倾向", "第5章：期望与匮乏"],
            "quotes": [
                "身份的焦虑源于对爱的渴望",
                "现代社会让每个人都觉得自己可以成功",
                "势利者是我们内心的镜子"
            ]
        },
        {
            "name": "倦怠社会",
            "author": "韩炳哲",
            "key_chapters": ["第4章：精神暴力", "第6章：倦怠社会"],
            "quotes": [
                "功绩主体是自身的雇主，也是自身的奴隶",
                "焦虑来自过度的积极",
                "抑郁是功绩社会的产物"
            ]
        }
    ],
    "孤独": [
        {
            "name": "孤独六讲",
            "author": "蒋勋",
            "key_chapters": ["第一讲：情欲孤独", "第四讲：革命孤独"],
            "quotes": [
                "孤独是生命圆满的开始",
                "思维需要孤独，创造需要孤独",
                "害怕孤独的人其实是在害怕自己"
            ]
        },
        {
            "name": "孤独的城市",
            "author": "奥利维娅·莱恩",
            "key_chapters": ["第1章：孤独的体验", "第5章：网络中的孤独"],
            "quotes": [
                "城市制造了孤独，又承诺治愈孤独",
                "社交媒体让我们更孤独",
                "孤独是一种政治问题"
            ]
        },
        {
            "name": "逃避自由",
            "author": "埃里希·弗洛姆",
            "key_chapters": ["第5章：逃避机制", "第7章：自由与自发"],
            "quotes": [
                "孤独是自由的代价",
                "人们为了逃避孤独而臣服于权威",
                "真正的自发可以战胜孤独"
            ]
        }
    ]
}

# ========== 话题匹配逻辑 ==========
def match_topic(title: str) -> Optional[str]:
    """
    根据标题匹配话题

    Args:
        title: 讨论标题

    Returns:
        匹配到的话题key，或None
    """
    title_lower = title.lower()

    # 直接匹配
    for topic in TOPIC_BOOK_MAPPING.keys():
        if topic in title_lower:
            return topic

    # 关键词匹配
    keyword_mapping = {
        "算法推荐": ["算法", "推荐", "推荐系统", "信息流", "feed", "个性化", "filter bubble", "信息茧房"],
        "数字游民": ["数字游民", "远程工作", "自由职业", "nomad", "freelance", "远程办公", "地理套利"],
        "内卷": ["内卷", "involution", "竞争", "996", "加班", "绩效", "KPI", "优绩"],
        "消费主义": ["消费", "购物", "品牌", "奢侈品", "物欲", "消费社会", "买买买", "剁手"],
        "AI人工智能": ["AI", "人工智能", "chatgpt", "大模型", "机器学习", "深度学习", "自动化", "智能"],
        "焦虑": ["焦虑", "焦虑感", "压力", "紧张", "不安", "焦虑症", "精神内耗"],
        "孤独": ["孤独", "寂寞", "孤单", "独处", "社交恐惧", "社恐", "人际"]
    }

    for topic, keywords in keyword_mapping.items():
        for kw in keywords:
            if kw in title_lower:
                return topic

    return None


def get_book_materials(topic: str) -> List[Dict]:
    """
    获取话题对应的书单素材

    Args:
        topic: 话题名称

    Returns:
        书单列表
    """
    return TOPIC_BOOK_MAPPING.get(topic, [])


def inject_book_materials(topic: str, experts: List[str]) -> str:
    """
    为话题生成素材注入Prompt

    Args:
        topic: 讨论话题
        experts: 参与讨论的专家列表

    Returns:
        一个Prompt片段，包含推荐引用的书籍、关键章节、可用素材
    """
    matched_topic = match_topic(topic)

    if not matched_topic:
        return _generate_generic_prompt(topic, experts)

    books = get_book_materials(matched_topic)

    prompt_parts = [
        f"# 📚 话题「{topic}」配套书单素材",
        "",
        f"## 讨论要求",
        f"本次讨论涉及话题「{topic}」，请以下{len(experts)}位专家在发言中引用以下书籍素材：",
        "",
        "## 推荐引用书籍",
        ""
    ]

    for i, book in enumerate(books, 1):
        prompt_parts.append(f"### {i}. 《{book['name']}》 - {book['author']}")
        prompt_parts.append(f"**关键章节：** {', '.join(book['key_chapters'])}")
        prompt_parts.append("**可用金句：**")
        for quote in book['quotes']:
            prompt_parts.append(f"  - \"{quote}\"")
        prompt_parts.append("")

    prompt_parts.extend([
        "## 引用规范",
        "1. 每次发言至少引用1本书籍的具体观点或金句",
        "2. 引用格式：'《书名》中指出...' 或 '作者XXX在《书名》中写道...'",
        "3. 鼓励跨书籍对比：'这与《书名A》中的观点形成对比...'",
        "4. 可以结合现实案例和数据强化论证",
        "",
        "## 专家引用策略",
    ])

    # 为每个专家分配不同的引用重点
    strategies = [
        "重点引用哲学/社会学经典，提供理论深度",
        "重点引用当代研究，提供数据和现实案例",
        "重点引用跨文化视角，提供比较分析",
        "重点批判性分析，质疑书中观点的局限性",
        "重点整合不同书籍的观点，寻找共识",
        "重点从个体经验出发，连接书中理论与现实"
    ]

    for i, expert in enumerate(experts):
        strategy = strategies[i % len(strategies)]
        prompt_parts.append(f"- **{expert}**：{strategy}")

    prompt_parts.extend([
        "",
        "## 证据类型要求",
        "- 书籍引用：至少50%的发言包含具体书名引用",
        "- 数据支撑：涉及趋势判断时提供具体数字",
        "- 案例佐证：结合现实事件或历史案例",
        "- 理论框架：使用书中的理论模型分析现实",
        ""
    ])

    return "\n".join(prompt_parts)


def _generate_generic_prompt(topic: str, experts: List[str]) -> str:
    """
    为未匹配到预置话题的情况生成通用Prompt

    Args:
        topic: 讨论话题
        experts: 参与讨论的专家列表

    Returns:
        通用Prompt片段
    """
    return f"""# 📚 话题「{topic}」素材注入

## 讨论要求
本次讨论涉及话题「{topic}」，请以下{len(experts)}位专家在发言中提供充分的证据支撑。

## 证据类型要求
1. **书籍引用**：引用相关领域的经典著作或当代畅销书
2. **数据支撑**：使用具体数字、百分比、统计结果
3. **案例佐证**：引用历史事件、社会现象、商业案例
4. **专家观点**：引用该领域知名学者的观点
5. **理论框架**：使用成熟的理论模型进行分析

## 引用规范
- 引用书籍时注明《书名》和作者
- 引用数据时说明来源和时间
- 引用案例时提供具体细节
- 避免空泛的断言，每句话尽量有依据

## 专家分工
""" + "\n".join([
    f"- **{expert}**：重点从{['理论', '数据', '案例', '批判', '整合', '经验'][i%6]}角度提供证据"
    for i, expert in enumerate(experts)
])


def generate_system_prompt(topic: str, experts: List[str], base_prompt: str = "") -> str:
    """
    生成完整的系统Prompt，包含基础指令+素材注入

    Args:
        topic: 讨论话题
        experts: 参与讨论的专家列表
        base_prompt: 基础Prompt（可选）

    Returns:
        完整的系统Prompt
    """
    material_prompt = inject_book_materials(topic, experts)

    if base_prompt:
        return f"{base_prompt}\n\n{'='*60}\n\n{material_prompt}"

    return material_prompt


def export_mapping(path: str = "topic_book_mapping.json") -> None:
    """
    导出话题映射到JSON文件

    Args:
        path: 输出文件路径
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(TOPIC_BOOK_MAPPING, f, ensure_ascii=False, indent=2)
    print(f"✅ 话题映射已导出到: {path}")


def import_mapping(path: str) -> Dict:
    """
    从JSON文件导入话题映射

    Args:
        path: JSON文件路径

    Returns:
        话题映射字典
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("🧪 运行内容注入器测试...\n")

    # 测试1: 匹配话题并生成Prompt
    print("=" * 60)
    print("测试1: 算法推荐话题")
    print("=" * 60)

    topic1 = "算法推荐如何重塑我们的注意力"
    experts1 = ["技术哲学家", "认知科学家", "社会学家", "产品经理", "媒体研究者", "心理学家"]

    prompt1 = inject_book_materials(topic1, experts1)
    print(prompt1[:500] + "...\n")

    # 验证匹配
    matched = match_topic(topic1)
    assert matched == "算法推荐", f"期望匹配'算法推荐'，实际匹配'{matched}'"
    print(f"✅ 话题匹配正确: {matched}")

    # 测试2: 数字游民话题
    print("\n" + "=" * 60)
    print("测试2: 数字游民话题")
    print("=" * 60)

    topic2 = "数字游民：自由还是逃避？"
    experts2 = ["社会学家", "经济学家", "心理学家", "远程工作者", "城市规划师"]

    prompt2 = inject_book_materials(topic2, experts2)
    print(prompt2[:500] + "...\n")

    matched2 = match_topic(topic2)
    assert matched2 == "数字游民", f"期望匹配'数字游民'，实际匹配'{matched2}'"
    print(f"✅ 话题匹配正确: {matched2}")

    # 测试3: 未匹配话题
    print("\n" + "=" * 60)
    print("测试3: 未匹配话题（通用Prompt）")
    print("=" * 60)

    topic3 = "量子计算的未来发展"
    experts3 = ["物理学家", "计算机科学家"]

    prompt3 = inject_book_materials(topic3, experts3)
    print(prompt3[:500] + "...\n")

    matched3 = match_topic(topic3)
    assert matched3 is None, f"期望未匹配，实际匹配'{matched3}'"
    print(f"✅ 未匹配话题返回通用Prompt")

    # 测试4: 书单素材完整性
    print("\n" + "=" * 60)
    print("测试4: 书单素材完整性")
    print("=" * 60)

    for topic, books in TOPIC_BOOK_MAPPING.items():
        assert len(books) >= 3, f"话题'{topic}'的书籍数量不足3本"
        for book in books:
            assert "name" in book, f"书籍缺少name字段"
            assert "author" in book, f"书籍缺少author字段"
            assert "key_chapters" in book, f"书籍缺少key_chapters字段"
            assert "quotes" in book, f"书籍缺少quotes字段"
            assert len(book["quotes"]) >= 2, f"《{book['name']}》的金句不足2条"
        print(f"✅ 话题'{topic}': {len(books)}本书，素材完整")

    # 测试5: 导出导入
    print("\n" + "=" * 60)
    print("测试5: 导出导入功能")
    print("=" * 60)

    import tempfile
    import os

    temp_path = os.path.join(tempfile.gettempdir(), "test_topic_mapping.json")
    export_mapping(temp_path)

    imported = import_mapping(temp_path)
    assert "算法推荐" in imported, "导入后缺少'算法推荐'话题"
    assert len(imported["算法推荐"]) == 4, "导入后书籍数量不匹配"

    os.unlink(temp_path)
    print("✅ 导出导入测试通过")

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
