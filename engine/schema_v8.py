# -*- coding: utf-8 -*-
"""
圆桌会议V8级内容Schema - 新增books字段支持多书讨论

核心升级：
1. 新增books字段：支持基于多本书的讨论
2. 每本书包含name/author/key_chapters/key_quotes
3. 兼容原有单书讨论模式（books可为空）
4. 验证函数支持新旧两种模式

使用场景：
- 单书讨论：books留空或填1本书
- 话题讨论：books填3-5本相关书籍
- 对比讨论：books填2本对比书籍
"""

from typing import List, Optional, Dict, Tuple, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ========== 枚举类型 ==========
class StanceType(str, Enum):
    """立场类型"""
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    COMPLEX = "complex"


class EmotionType(str, Enum):
    """情绪类型"""
    SARCASM = "sarcasm"
    HELPLESSNESS = "helplessness"
    ANGER = "anger"
    HESITATION = "hesitation"
    SELF_DEPRECATION = "self_deprecation"
    COLD_LAUGH = "cold_laugh"
    SILENCE = "silence"
    SERIOUS = "serious"


# ========== 新增：书籍模型 ==========
class BookReference(BaseModel):
    """
    引用书籍信息

    用于话题讨论模式，一本书对应一组可引用素材
    """
    name: str = Field(..., min_length=1, description="书名")
    author: str = Field(..., min_length=1, description="作者")
    key_chapters: List[str] = Field(
        default=[],
        description="关键章节列表，如['第3章', '第5章']"
    )
    key_quotes: List[str] = Field(
        default=[],
        description="关键金句列表，可直接引用"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "倦怠社会",
                "author": "韩炳哲",
                "key_chapters": ["第3章：超越规训社会", "第5章：倦怠社会"],
                "key_quotes": [
                    "功绩社会下的自我剥削比外部剥削更高效",
                    "我们生活在一种过度的积极之中"
                ]
            }
        }
    }


# ========== 专家模型 ==========
class ExpertProfile(BaseModel):
    """专家档案 - 包含立场、利益、恐惧、偏见"""
    name: str = Field(..., description="专家姓名")
    title: str = Field(..., description="头衔/身份")
    avatar_color: str = Field(default="#c9a227", description="头像颜色")

    # 核心立场
    stance: StanceType = Field(..., description="对主题的立场")
    core_belief: str = Field(..., min_length=1, description="核心信念（一句话）")

    # 利益相关
    interest: str = Field(..., min_length=1, description="利益相关")
    fear: str = Field(..., min_length=1, description="恐惧")
    bias: str = Field(..., min_length=1, description="偏见")

    # 经历
    experience: str = Field(..., min_length=1, description="关键经历")
    trauma: Optional[str] = Field(default=None, description="创伤")

    # 表达风格
    speaking_style: str = Field(..., description="说话风格")
    default_emotion: EmotionType = Field(default=EmotionType.SERIOUS, description="默认情绪")


# ========== 碰撞轮次 ==========
class ClashRound(BaseModel):
    """碰撞轮次 - 支持多轮攻击"""
    round_num: int = Field(..., ge=1, le=5, description="碰撞轮次")
    attacker: str = Field(..., description="攻击者")
    target: str = Field(..., description="被攻击者")
    attack_type: str = Field(..., description="攻击类型")
    attack_content: str = Field(..., min_length=1, description="攻击内容")
    emotion: EmotionType = Field(default=EmotionType.SERIOUS, description="攻击时的情绪")

    # 反击
    counter_attack: Optional[str] = Field(default=None, description="反击内容")
    counter_emotion: Optional[EmotionType] = Field(default=None, description="反击情绪")


# ========== 现实案例 ==========
class RealityCase(BaseModel):
    """现实案例 - 必须有代价"""
    case_name: str = Field(..., min_length=1, description="案例名称")
    case_source: str = Field(..., description="来源")
    case_content: str = Field(..., min_length=1, description="案例内容")
    case_outcome: str = Field(..., min_length=1, description="结果")
    case_lesson: str = Field(..., min_length=1, description="教训")


# ========== 代价讨论 ==========
class CostDiscussion(BaseModel):
    """代价讨论"""
    scenario: str = Field(..., min_length=1, description="假设场景")
    cost_analysis: List[Dict[str, str]] = Field(..., min_length=2, description="代价分析")
    worst_case: str = Field(..., min_length=1, description="最坏情况")
    survivor_bias: Optional[str] = Field(default=None, description="幸存者偏差分析")


# ========== 人性层 ==========
class HumanNatureLayer(BaseModel):
    """人性层"""
    question: str = Field(..., min_length=1, description="人性问题")
    psychological_analysis: str = Field(..., min_length=1, description="心理分析")
    real_examples: List[str] = Field(..., min_length=2, description="现实例子")
    conclusion: str = Field(..., min_length=1, description="结论")


# ========== 认知升级 ==========
class CognitiveUpgrade(BaseModel):
    """认知升级"""
    old_thinking: str = Field(..., min_length=1, description="旧思维")
    new_thinking: str = Field(..., min_length=1, description="新思维")
    complexity: str = Field(..., min_length=1, description="复杂性说明")
    actionable_insight: str = Field(..., min_length=1, description="可执行洞见")


# ========== 讨论轮次 ==========
class DiscussionRound(BaseModel):
    """讨论轮次 - V8级结构"""
    round_number: int = Field(..., ge=1, le=10)
    topic: str = Field(..., min_length=1)
    core_question: str = Field(..., min_length=1)

    # Round1: 立场表达
    stances: List[Dict[str, str]] = Field(..., min_length=3, description="各专家立场")

    # Round2: 互相反驳
    clash_rounds: List[ClashRound] = Field(..., min_length=2, description="碰撞轮次")

    # Round3: 现实案例
    reality_cases: List[RealityCase] = Field(..., min_length=1, description="现实案例")

    # Round4: 代价讨论
    cost_discussion: CostDiscussion

    # Round5: 人性层
    human_nature: HumanNatureLayer

    # Round6: 认知升级
    cognitive_upgrade: CognitiveUpgrade

    # 情绪标记
    emotions: List[Dict[str, str]] = Field(default=[], description="情绪标记")


# ========== V8 Schema定义（字典形式，用于运行时验证） ==========
V8_SCHEMA = {
    "title": str,
    "subtitle": str,
    "books": [  # 新增字段
        {
            "name": str,
            "author": str,
            "key_chapters": List[str],
            "key_quotes": List[str],
        }
    ],
    "experts": [
        {
            "name": str,
            "title": str,
            "avatar_color": str,
            "stance": str,
            "core_belief": str,
            "interest": str,
            "fear": str,
            "bias": str,
            "experience": str,
            "trauma": Optional[str],
            "speaking_style": str,
            "default_emotion": str,
        }
    ],
    "rounds": [
        {
            "round_number": int,
            "topic": str,
            "core_question": str,
            "stances": List[Dict[str, str]],
            "clash_rounds": List[Dict],
            "reality_cases": List[Dict],
            "cost_discussion": Dict,
            "human_nature": Dict,
            "cognitive_upgrade": Dict,
            "emotions": List[Dict[str, str]],
        }
    ],
    "final_insight": str,
    "open_questions": List[str],
}


# ========== 主模型 ==========
class RoundtableV8(BaseModel):
    """
    圆桌会议V8级内容

    升级点：
    - 新增books字段，支持多书讨论
    - 兼容单书模式（books可为空列表）
    """
    title: str = Field(..., min_length=1, max_length=100)
    subtitle: str = Field(default="")

    # 新增：引用书籍列表
    books: List[BookReference] = Field(
        default=[],
        description="讨论涉及的书籍列表。单书讨论可留空或填1本，话题讨论填3-5本"
    )

    # 专家档案
    experts: List[ExpertProfile] = Field(..., min_length=4, max_length=8)

    # 讨论轮次
    rounds: List[DiscussionRound] = Field(..., min_length=3, max_length=7)

    # 总结
    final_insight: str = Field(..., min_length=1, description="最终洞见")
    open_questions: List[str] = Field(..., min_length=2, description="开放问题")

    @field_validator('experts')
    def validate_experts(cls, v):
        """验证专家立场多样性"""
        stances = [e.stance for e in v]
        if len(set(stances)) < 2:
            raise ValueError('专家立场必须多样化，至少2种不同立场')
        return v

    @field_validator('books')
    def validate_books(cls, v):
        """验证书籍信息完整性"""
        for book in v:
            if not book.name or not book.author:
                raise ValueError('书籍必须包含书名和作者')
        return v


# ========== 验证函数 ==========
def validate_v8(data: Dict) -> Tuple[bool, List[str]]:
    """
    验证V8 JSON是否符合Schema

    Args:
        data: 待验证的字典数据

    Returns:
        (是否通过, 错误信息列表)
    """
    errors = []

    # 检查必填字段
    required_fields = ["title", "experts", "rounds", "final_insight", "open_questions"]
    for field in required_fields:
        if field not in data:
            errors.append(f"缺少必填字段: {field}")

    # 检查books字段（新增，可选但推荐）
    if "books" in data:
        books = data["books"]
        if not isinstance(books, list):
            errors.append("books必须是列表")
        else:
            for i, book in enumerate(books):
                if not isinstance(book, dict):
                    errors.append(f"books[{i}]必须是字典")
                    continue
                if "name" not in book or not book["name"]:
                    errors.append(f"books[{i}]缺少name字段")
                if "author" not in book or not book["author"]:
                    errors.append(f"books[{i}]缺少author字段")

    # 检查experts
    if "experts" in data:
        experts = data["experts"]
        if not isinstance(experts, list):
            errors.append("experts必须是列表")
        elif len(experts) < 4:
            errors.append(f"专家数量不足: {len(experts)}，至少需要4位")
        elif len(experts) > 8:
            errors.append(f"专家数量过多: {len(experts)}，最多8位")
        else:
            # 检查立场多样性
            stances = set()
            for i, expert in enumerate(experts):
                if not isinstance(expert, dict):
                    errors.append(f"experts[{i}]必须是字典")
                    continue
                if "name" not in expert:
                    errors.append(f"experts[{i}]缺少name字段")
                if "stance" in expert:
                    stances.add(expert["stance"])
            if len(stances) < 2:
                errors.append("专家立场必须多样化，至少2种不同立场")

    # 检查rounds
    if "rounds" in data:
        rounds = data["rounds"]
        if not isinstance(rounds, list):
            errors.append("rounds必须是列表")
        elif len(rounds) < 3:
            errors.append(f"讨论轮次不足: {len(rounds)}，至少需要3轮")
        else:
            for i, round_data in enumerate(rounds):
                if not isinstance(round_data, dict):
                    errors.append(f"rounds[{i}]必须是字典")
                    continue

                # 检查stances
                stances = round_data.get("stances", [])
                if not isinstance(stances, list) or len(stances) < 3:
                    errors.append(f"rounds[{i}].stances至少需要3条发言")

                # 检查clash_rounds
                clashes = round_data.get("clash_rounds", [])
                if not isinstance(clashes, list) or len(clashes) < 2:
                    errors.append(f"rounds[{i}].clash_rounds至少需要2次碰撞")

                # 检查reality_cases
                cases = round_data.get("reality_cases", [])
                if not isinstance(cases, list) or len(cases) < 1:
                    errors.append(f"rounds[{i}].reality_cases至少需要1个案例")

    # 检查final_insight
    if "final_insight" in data and (not data["final_insight"] or len(data["final_insight"]) < 10):
        errors.append("final_insight过短，需要至少10个字符")

    # 检查open_questions
    if "open_questions" in data:
        oq = data["open_questions"]
        if not isinstance(oq, list) or len(oq) < 2:
            errors.append("open_questions至少需要2个问题")

    return len(errors) == 0, errors


def validate_v8_content(data: dict) -> RoundtableV8:
    """
    使用Pydantic验证V8级内容

    Args:
        data: 待验证的字典数据

    Returns:
        验证后的RoundtableV8对象

    Raises:
        ValueError: 验证失败时抛出
    """
    try:
        return RoundtableV8(**data)
    except Exception as e:
        raise ValueError(f"内容验证失败: {e}")


def get_discussion_mode(data: Dict) -> str:
    """
    判断讨论模式

    Args:
        data: V8 JSON数据

    Returns:
        "single_book" - 单书讨论
        "multi_book" - 多书讨论
        "topic_based" - 纯话题讨论（无书籍）
    """
    books = data.get("books", [])

    if not books:
        return "topic_based"
    elif len(books) == 1:
        return "single_book"
    else:
        return "multi_book"


def create_topic_based_v8(
    title: str,
    topic: str,
    books: List[Dict[str, Any]],
    experts: List[Dict],
    rounds: List[Dict],
    final_insight: str,
    open_questions: List[str]
) -> Dict:
    """
    创建基于话题的V8内容

    Args:
        title: 讨论标题
        topic: 话题名称
        books: 书籍列表，每本包含name/author/key_chapters/key_quotes
        experts: 专家列表
        rounds: 讨论轮次
        final_insight: 最终洞见
        open_questions: 开放问题

    Returns:
        符合V8 Schema的字典
    """
    return {
        "title": title,
        "subtitle": f"基于{len(books)}本书的深度讨论",
        "books": books,
        "experts": experts,
        "rounds": rounds,
        "final_insight": final_insight,
        "open_questions": open_questions
    }


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("🧪 运行V8 Schema测试...\n")

    # 测试1: 单书讨论（兼容旧模式）
    print("=" * 60)
    print("测试1: 单书讨论（兼容旧模式）")
    print("=" * 60)

    single_book_data = {
        "title": "《倦怠社会》中的自我剥削",
        "subtitle": "",
        "books": [
            {
                "name": "倦怠社会",
                "author": "韩炳哲",
                "key_chapters": ["第3章", "第5章"],
                "key_quotes": ["功绩社会下的自我剥削比外部剥削更高效"]
            }
        ],
        "experts": [
            {
                "name": "哲学家A",
                "title": "哲学教授",
                "stance": "support",
                "core_belief": "自我剥削是现代社会的主要矛盾",
                "interest": "理论影响力",
                "fear": "被边缘化",
                "bias": "过度理论化",
                "experience": "研究法兰克福学派20年",
                "speaking_style": "严谨学术"
            },
            {
                "name": "社会学家B",
                "title": "社会学研究员",
                "stance": "oppose",
                "core_belief": "外部剥削依然存在",
                "interest": "社会公平",
                "fear": "忽视结构性问题",
                "bias": "偏向底层视角",
                "experience": "长期调研工厂劳工",
                "speaking_style": "数据驱动"
            },
            {
                "name": "心理学家C",
                "title": "临床心理学家",
                "stance": "complex",
                "core_belief": "内外剥削并存",
                "interest": "患者康复",
                "fear": "简化复杂问题",
                "bias": "临床视角局限",
                "experience": "治疗 burnout 患者10年",
                "speaking_style": "温和分析"
            },
            {
                "name": "企业家D",
                "title": "科技公司CEO",
                "stance": "neutral",
                "core_belief": "效率与福祉需要平衡",
                "interest": "企业利润",
                "fear": "监管加强",
                "bias": "技术乐观主义",
                "experience": "管理千人团队",
                "speaking_style": "务实直接"
            }
        ],
        "rounds": [
            {
                "round_number": 1,
                "topic": "自我剥削的本质",
                "core_question": "自我剥削是否比外部剥削更危险？",
                "stances": [
                    {"expert": "哲学家A", "content": "韩炳哲在《倦怠社会》第3章指出..."},
                    {"expert": "社会学家B", "content": "但数据显示，2023年劳工权益侵害案件增长了15%..."},
                    {"expert": "心理学家C", "content": "从临床角度看，两者都导致 burnout..."},
                    {"expert": "企业家D", "content": "关键是找到平衡点..."}
                ],
                "clash_rounds": [
                    {
                        "round_num": 1,
                        "attacker": "社会学家B",
                        "target": "哲学家A",
                        "attack_type": "现实矛盾",
                        "attack_content": "你忽视了外卖骑手被算法压榨的事实...",
                        "emotion": "serious"
                    },
                    {
                        "round_num": 2,
                        "attacker": "哲学家A",
                        "target": "社会学家B",
                        "attack_type": "逻辑漏洞",
                        "attack_content": "你混淆了剥削的形式和本质...",
                        "emotion": "serious"
                    }
                ],
                "reality_cases": [
                    {
                        "case_name": "某大厂员工猝死事件",
                        "case_source": "社会新闻",
                        "case_content": "2023年某互联网公司员工因过度加班猝死...",
                        "case_outcome": "引发社会对996的讨论",
                        "case_lesson": "自我剥削和外部剥削往往同时存在"
                    }
                ],
                "cost_discussion": {
                    "scenario": "如果完全接受韩炳哲的理论",
                    "cost_analysis": [
                        {"cost": "忽视结构性不平等"},
                        {"cost": "个体化社会问题的风险"}
                    ],
                    "worst_case": "社会改革动力被消解",
                    "survivor_bias": "能发声的人往往是自我剥削的受害者"
                },
                "human_nature": {
                    "question": "为什么人明知道过度工作有害还是停不下来？",
                    "psychological_analysis": "多巴胺驱动的成就感和恐惧驱动的焦虑形成双重束缚",
                    "real_examples": ["刷短视频停不下来", "不断检查工作邮件"],
                    "conclusion": "需要外部约束来打破自我剥削的循环"
                },
                "cognitive_upgrade": {
                    "old_thinking": "剥削是别人强加的",
                    "new_thinking": "剥削可以是自我施加的，且更难察觉",
                    "complexity": "两种剥削相互强化，不能简单对立",
                    "actionable_insight": "建立个人边界，识别自我剥削的信号"
                },
                "emotions": []
            },
            {
                "round_number": 2,
                "topic": "自我剥削的边界",
                "core_question": "如何区分自我驱动和自我剥削？",
                "stances": [
                    {"expert": "哲学家A", "content": "关键在于自主性的程度..."},
                    {"expert": "社会学家B", "content": "结构性压力让'自主选择'成为幻觉..."},
                    {"expert": "心理学家C", "content": "内在动机和外在动机的平衡..."},
                    {"expert": "企业家D", "content": "市场机制自然会调节..."}
                ],
                "clash_rounds": [
                    {
                        "round_num": 1,
                        "attacker": "心理学家C",
                        "target": "企业家D",
                        "attack_type": "利益冲突",
                        "attack_content": "你的立场受到利益影响...",
                        "emotion": "serious"
                    },
                    {
                        "round_num": 2,
                        "attacker": "企业家D",
                        "target": "心理学家C",
                        "attack_type": "现实矛盾",
                        "attack_content": "但数据显示弹性工作制提升了满意度...",
                        "emotion": "serious"
                    }
                ],
                "reality_cases": [
                    {
                        "case_name": "远程工作实验",
                        "case_source": "商业实验",
                        "case_content": "某公司在疫情期间实行远程办公...",
                        "case_outcome": "生产力提升但工作时间延长",
                        "case_lesson": "自由可能掩盖剥削"
                    }
                ],
                "cost_discussion": {
                    "scenario": "如果完全禁止加班",
                    "cost_analysis": [
                        {"cost": "经济竞争力下降"},
                        {"cost": "个人发展受限"}
                    ],
                    "worst_case": "人才流失到更宽松的市场",
                    "survivor_bias": "反对加班的人往往是高薪群体"
                },
                "human_nature": {
                    "question": "为什么人会选择自我剥削？",
                    "psychological_analysis": "成就感和安全感的双重需求...",
                    "real_examples": ["自愿加班求晋升", "过度准备考试"],
                    "conclusion": "需要重新定义成功"
                },
                "cognitive_upgrade": {
                    "old_thinking": "努力就有回报",
                    "new_thinking": "努力的方向和边界同样重要",
                    "complexity": "个人责任和社会结构的交互",
                    "actionable_insight": "设定清晰的工作边界"
                },
                "emotions": []
            },
            {
                "round_number": 3,
                "topic": "出路在哪里",
                "core_question": "如何在功绩社会中保持身心健康？",
                "stances": [
                    {"expert": "哲学家A", "content": "需要重新思考'善'的定义..."},
                    {"expert": "社会学家B", "content": "制度性保障比个人修养更根本..."},
                    {"expert": "心理学家C", "content": "建立健康的自我认知..."},
                    {"expert": "企业家D", "content": "技术可以帮助实现工作生活平衡..."}
                ],
                "clash_rounds": [
                    {
                        "round_num": 1,
                        "attacker": "社会学家B",
                        "target": "企业家D",
                        "attack_type": "利益冲突",
                        "attack_content": "技术解决方案是另一种商业机会...",
                        "emotion": "serious"
                    },
                    {
                        "round_num": 2,
                        "attacker": "哲学家A",
                        "target": "社会学家B",
                        "attack_type": "逻辑漏洞",
                        "attack_content": "制度变革需要文化基础...",
                        "emotion": "serious"
                    }
                ],
                "reality_cases": [
                    {
                        "case_name": "四天工作制试点",
                        "case_source": "政策实验",
                        "case_content": "冰岛试行四天工作制...",
                        "case_outcome": "生产力未下降，幸福感提升",
                        "case_lesson": "减少工作时间未必损害效率"
                    }
                ],
                "cost_discussion": {
                    "scenario": "如果全面推行四天工作制",
                    "cost_analysis": [
                        {"cost": "服务业覆盖不足"},
                        {"cost": "国际竞争力下降"}
                    ],
                    "worst_case": "经济停滞",
                    "survivor_bias": "试点成功的案例被过度宣传"
                },
                "human_nature": {
                    "question": "为什么人需要工作来定义自己？",
                    "psychological_analysis": "工作伦理已经内化为身份认同...",
                    "real_examples": ["退休后的失落感", "失业后的自我怀疑"],
                    "conclusion": "需要多元化的自我价值来源"
                },
                "cognitive_upgrade": {
                    "old_thinking": "工作是人生意义的主要来源",
                    "new_thinking": "意义可以在工作之外找到",
                    "complexity": "工作、休闲、关系的平衡",
                    "actionable_insight": "培养工作之外的兴趣和社群"
                },
                "emotions": []
            }
        ],
        "final_insight": "自我剥削和外部剥削是同一枚硬币的两面...",
        "open_questions": [
            "如何在现代社会中建立健康的劳动伦理？",
            "技术是中立的还是自带剥削逻辑？"
        ]
    }

    # 使用字典验证
    is_valid, errors = validate_v8(single_book_data)
    print(f"字典验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    if errors:
        for e in errors:
            print(f"  - {e}")

    # 使用Pydantic验证
    try:
        v8_obj = validate_v8_content(single_book_data)
        print(f"✅ Pydantic验证通过")
        print(f"  讨论模式: {get_discussion_mode(single_book_data)}")
        print(f"  书籍数量: {len(v8_obj.books)}")
        print(f"  专家数量: {len(v8_obj.experts)}")
        print(f"  轮次数量: {len(v8_obj.rounds)}")
    except ValueError as e:
        print(f"❌ Pydantic验证失败: {e}")

    # 测试2: 多书话题讨论（新模式）
    print("\n" + "=" * 60)
    print("测试2: 多书话题讨论（新模式）")
    print("=" * 60)

    # 复用相同的轮次结构，只修改内容
    def make_round(round_num, topic, question, stances, attacker1, target1, attack1, attacker2, target2, attack2, case_name, case_content, case_outcome, case_lesson):
        return {
            "round_number": round_num,
            "topic": topic,
            "core_question": question,
            "stances": stances,
            "clash_rounds": [
                {
                    "round_num": 1,
                    "attacker": attacker1,
                    "target": target1,
                    "attack_type": "利益冲突",
                    "attack_content": attack1,
                    "emotion": "serious"
                },
                {
                    "round_num": 2,
                    "attacker": attacker2,
                    "target": target2,
                    "attack_type": "逻辑漏洞",
                    "attack_content": attack2,
                    "emotion": "serious"
                }
            ],
            "reality_cases": [
                {
                    "case_name": case_name,
                    "case_source": "商业分析",
                    "case_content": case_content,
                    "case_outcome": case_outcome,
                    "case_lesson": case_lesson
                }
            ],
            "cost_discussion": {
                "scenario": f"如果{topic}",
                "cost_analysis": [{"cost": "成本A"}, {"cost": "成本B"}],
                "worst_case": "最坏情况",
                "survivor_bias": "幸存者偏差"
            },
            "human_nature": {
                "question": "人性问题？",
                "psychological_analysis": "心理分析...",
                "real_examples": ["例子1", "例子2"],
                "conclusion": "结论"
            },
            "cognitive_upgrade": {
                "old_thinking": "旧思维",
                "new_thinking": "新思维",
                "complexity": "复杂性",
                "actionable_insight": "可执行洞见"
            },
            "emotions": []
        }

    multi_book_data = {
        "title": "算法推荐如何重塑我们的注意力",
        "subtitle": "",
        "books": [
            {
                "name": "倦怠社会",
                "author": "韩炳哲",
                "key_chapters": ["第3章", "第5章"],
                "key_quotes": ["功绩社会下的自我剥削比外部剥削更高效"]
            },
            {
                "name": "娱乐至死",
                "author": "尼尔·波兹曼",
                "key_chapters": ["第1章", "第10章"],
                "key_quotes": ["我们将毁于我们所热爱的东西"]
            },
            {
                "name": "浅薄",
                "author": "尼古拉斯·卡尔",
                "key_chapters": ["第3章", "第6章"],
                "key_quotes": ["互联网正在重塑我们的大脑"]
            }
        ],
        "experts": [
            {
                "name": "技术哲学家",
                "title": "哲学教授",
                "stance": "oppose",
                "core_belief": "算法推荐是技术异化的最新形式",
                "interest": "理论影响力",
                "fear": "被边缘化",
                "bias": "技术悲观主义",
                "experience": "研究技术哲学15年",
                "speaking_style": "批判性分析"
            },
            {
                "name": "认知科学家",
                "title": "脑科学研究员",
                "stance": "support",
                "core_belief": "算法只是工具，问题在于使用方式",
                "interest": "科研成果转化",
                "fear": "研究被误用",
                "bias": "科学主义",
                "experience": "研究注意力机制10年",
                "speaking_style": "数据驱动"
            },
            {
                "name": "产品经理",
                "title": "大厂推荐算法负责人",
                "stance": "complex",
                "core_belief": "算法可以设计得更好",
                "interest": "产品成功",
                "fear": "监管风险",
                "bias": "技术乐观主义",
                "experience": "设计推荐系统8年",
                "speaking_style": "务实直接"
            },
            {
                "name": "社会学家",
                "title": "数字社会研究员",
                "stance": "neutral",
                "core_belief": "需要系统性解决方案",
                "interest": "社会影响力",
                "fear": "简化复杂问题",
                "bias": "结构决定论",
                "experience": "研究数字鸿沟12年",
                "speaking_style": "宏观分析"
            }
        ],
        "rounds": [
            make_round(1, "算法推荐的本质", "算法推荐是服务用户还是剥削用户？",
                [
                    {"expert": "技术哲学家", "content": "波兹曼在《娱乐至死》中警告..."},
                    {"expert": "认知科学家", "content": "数据显示，用户主动选择算法推荐的比例达到70%..."},
                    {"expert": "产品经理", "content": "我们的目标是提升用户体验..."},
                    {"expert": "社会学家", "content": "需要看到结构性不平等..."}
                ],
                "技术哲学家", "产品经理", "你的利益与用户利益并不一致...",
                "认知科学家", "技术哲学家", "你把所有技术都等同于电视...",
                "TikTok注意力经济", "TikTok通过算法最大化用户停留时间...", "用户日均使用时长超过90分钟", "注意力成为被争夺的资源"),
            make_round(2, "注意力经济", "注意力是否应该被商品化？",
                [
                    {"expert": "技术哲学家", "content": "韩炳哲指出注意力是功绩社会的货币..."},
                    {"expert": "认知科学家", "content": "注意力机制是大脑的自然功能..."},
                    {"expert": "产品经理", "content": "广告模式是免费内容的基石..."},
                    {"expert": "社会学家", "content": "注意力不平等加剧了信息鸿沟..."}
                ],
                "社会学家", "产品经理", "你们从注意力经济中获利...",
                "产品经理", "社会学家", "但免费内容让信息更普惠...",
                "Facebook数据门", "Cambridge Analytica利用用户数据...", "引发全球数据隐私讨论", "注意力数据是敏感资产"),
            make_round(3, "未来方向", "如何构建更健康的注意力生态？",
                [
                    {"expert": "技术哲学家", "content": "需要回归波兹曼的媒介素养..."},
                    {"expert": "认知科学家", "content": "数字素养教育是关键..."},
                    {"expert": "产品经理", "content": "产品设计应该考虑长期价值..."},
                    {"expert": "社会学家", "content": "需要政策干预..."}
                ],
                "技术哲学家", "产品经理", "你们的'长期价值'还是商业利益...",
                "认知科学家", "技术哲学家", "但教育需要时间和资源...",
                "欧盟数字服务法", "欧盟通过DSA规范平台责任...", "平台算法需要接受审计", "监管可以推动变革")
        ],
        "final_insight": "算法推荐不是技术问题，而是社会契约问题...",
        "open_questions": [
            "如何设计更公平的推荐算法？",
            "个人如何在算法时代保持自主性？"
        ]
    }

    is_valid2, errors2 = validate_v8(multi_book_data)
    print(f"字典验证结果: {'✅ 通过' if is_valid2 else '❌ 失败'}")
    if errors2:
        for e in errors2:
            print(f"  - {e}")

    try:
        v8_obj2 = validate_v8_content(multi_book_data)
        print(f"✅ Pydantic验证通过")
        print(f"  讨论模式: {get_discussion_mode(multi_book_data)}")
        print(f"  书籍数量: {len(v8_obj2.books)}")
        for b in v8_obj2.books:
            print(f"    - 《{b.name}》({b.author})")
        print(f"  轮次数量: {len(v8_obj2.rounds)}")
    except ValueError as e:
        print(f"❌ Pydantic验证失败: {e}")

    # 测试3: 纯话题讨论（无书籍）
    print("\n" + "=" * 60)
    print("测试3: 纯话题讨论（无书籍，兼容旧模式）")
    print("=" * 60)

    topic_only_data = {
        "title": "现代社会的孤独感",
        "experts": [
            {
                "name": "社会学家",
                "title": "研究员",
                "stance": "support",
                "core_belief": "现代社会必然导致孤独",
                "interest": "学术声誉",
                "fear": "被忽视",
                "bias": "宏观视角",
                "experience": "研究城市化20年",
                "speaking_style": "学术"
            },
            {
                "name": "心理学家",
                "title": "治疗师",
                "stance": "oppose",
                "core_belief": "孤独是个体选择",
                "interest": "患者康复",
                "fear": "社会污名化",
                "bias": "个体视角",
                "experience": "治疗社交焦虑15年",
                "speaking_style": "温和"
            },
            {
                "name": "城市规划师",
                "title": "设计师",
                "stance": "neutral",
                "core_belief": "空间设计影响社交",
                "interest": "项目成功",
                "fear": "设计失误",
                "bias": "环境决定论",
                "experience": "设计社区空间10年",
                "speaking_style": "务实"
            },
            {
                "name": "作家",
                "title": "小说家",
                "stance": "complex",
                "core_belief": "孤独是创作的代价",
                "interest": "作品影响力",
                "fear": "失去灵感",
                "bias": "浪漫化孤独",
                "experience": "独居写作20年",
                "speaking_style": "感性"
            }
        ],
        "rounds": [
            make_round(1, "孤独的根源", "现代社会的孤独是结构性问题还是个体选择？",
                [
                    {"expert": "社会学家", "content": "城市化进程导致传统社群解体..."},
                    {"expert": "心理学家", "content": "研究表明孤独感与个体认知模式更相关..."},
                    {"expert": "城市规划师", "content": "公共空间设计影响人际互动..."},
                    {"expert": "作家", "content": "孤独是现代人精神独立的标志..."}
                ],
                "心理学家", "社会学家", "你把所有问题都归因于社会结构...",
                "社会学家", "心理学家", "但数据显示独居率与抑郁症发病率正相关...",
                "日本蛰居族现象", "日本超过100万年轻人长期闭门不出...", "成为严重的社会问题", "孤独可能演变为社会隔离"),
            make_round(2, "孤独与连接", "数字连接能否替代面对面交流？",
                [
                    {"expert": "社会学家", "content": "线上社群创造了新的连接方式..."},
                    {"expert": "心理学家", "content": "但缺乏非语言线索的深度..."},
                    {"expert": "城市规划师", "content": "混合空间可能是未来..."},
                    {"expert": "作家", "content": "真正的理解需要身体的在场..."}
                ],
                "心理学家", "城市规划师", "物理空间不是万能的...",
                "作家", "心理学家", "但你说的是理想状态...",
                "Zoom疲劳症", "视频会议导致新型疲劳...", "影响远程工作体验", "数字连接有生理代价"),
            make_round(3, "解决方案", "如何在不牺牲独立的情况下减少孤独？",
                [
                    {"expert": "社会学家", "content": "重建社区组织和公共生活..."},
                    {"expert": "心理学家", "content": "提升个体的社交技能..."},
                    {"expert": "城市规划师", "content": "设计促进偶遇的空间..."},
                    {"expert": "作家", "content": "接受孤独作为存在的一部分..."}
                ],
                "城市规划师", "作家", "设计不能解决所有问题...",
                "社会学家", "城市规划师", "但环境确实影响行为...",
                "丹麦共居社区", "丹麦的co-living社区实验...", "居民满意度较高", "新型社区模式值得探索")
        ],
        "final_insight": "孤独不是现代社会的bug，而是feature...",
        "open_questions": [
            "如何在保持独立的同时建立深度连接？",
            "技术应该促进连接还是保护独处？"
        ]
    }

    is_valid3, errors3 = validate_v8(topic_only_data)
    print(f"字典验证结果: {'✅ 通过' if is_valid3 else '❌ 失败'}")
    if errors3:
        for e in errors3:
            print(f"  - {e}")

    try:
        v8_obj3 = validate_v8_content(topic_only_data)
        print(f"✅ Pydantic验证通过")
        print(f"  讨论模式: {get_discussion_mode(topic_only_data)}")
        print(f"  书籍数量: {len(v8_obj3.books)} (纯话题讨论)")
    except ValueError as e:
        print(f"❌ Pydantic验证失败: {e}")

    # 测试4: 错误数据检测
    print("\n" + "=" * 60)
    print("测试4: 错误数据检测")
    print("=" * 60)

    bad_data = {
        "title": "测试",
        "experts": [
            {
                "name": "专家A",
                "stance": "support",
                "core_belief": "测试",
                "interest": "测试",
                "fear": "测试",
                "bias": "测试",
                "experience": "测试",
                "speaking_style": "测试"
            }
            # 只有1个专家，立场单一
        ],
        "rounds": [],
        "final_insight": "短",
        "open_questions": ["一个问题"]  # 不足2个
    }

    is_valid4, errors4 = validate_v8(bad_data)
    print(f"字典验证结果: {'✅ 通过' if is_valid4 else '❌ 失败'}")
    print("检测到的错误:")
    for e in errors4:
        print(f"  - {e}")

    assert not is_valid4, "错误数据应该验证失败"
    assert len(errors4) >= 4, f"应该检测到至少4个错误，实际{len(errors4)}"
    print("✅ 错误检测功能正常")

    print("\n" + "=" * 60)
    print("🎉 所有Schema测试通过！")
    print("=" * 60)
