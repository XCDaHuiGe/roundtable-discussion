# -*- coding: utf-8 -*-
"""圆桌会议V8级内容Schema - 从知识讨论升级为生存博弈"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator
from enum import Enum


class StanceType(str, Enum):
    """立场类型"""
    SUPPORT = "support"  # 支持
    OPPOSE = "oppose"  # 反对
    NEUTRAL = "neutral"  # 中立
    COMPLEX = "complex"  # 复杂


class EmotionType(str, Enum):
    """情绪类型"""
    SARCASM = "sarcasm"  # 嘲讽
    HELPLESSNESS = "helplessness"  # 无奈
    ANGER = "anger"  # 愤怒
    HESITATION = "hesitation"  # 犹豫
    SELF_DEPRECATION = "self_deprecation"  # 自嘲
    COLD_LAUGH = "cold_laugh"  # 冷笑
    SILENCE = "silence"  # 沉默
    SERIOUS = "serious"  # 严肃


class ExpertProfile(BaseModel):
    """专家档案 - 包含立场、利益、恐惧、偏见"""
    name: str = Field(..., description="专家姓名")
    title: str = Field(..., description="头衔/身份")
    avatar_color: str = Field(default="#c9a227", description="头像颜色")
    
    # 核心立场
    stance: StanceType = Field(..., description="对主题的立场")
    core_belief: str = Field(..., min_length=10, description="核心信念（一句话）")
    
    # 利益相关
    interest: str = Field(..., min_length=10, description="利益相关（他从这个观点中获得什么）")
    fear: str = Field(..., min_length=10, description="恐惧（他最怕什么）")
    bias: str = Field(..., min_length=10, description="偏见（他的认知盲区）")
    
    # 经历
    experience: str = Field(..., min_length=20, description="关键经历（塑造他观点的事件）")
    trauma: Optional[str] = Field(default=None, description="创伤（如果有）")
    
    # 表达风格
    speaking_style: str = Field(..., description="说话风格")
    default_emotion: EmotionType = Field(default=EmotionType.SERIOUS, description="默认情绪")


class ClashRound(BaseModel):
    """碰撞轮次 - 支持多轮攻击"""
    round_num: int = Field(..., ge=1, le=5, description="碰撞轮次")
    attacker: str = Field(..., description="攻击者")
    target: str = Field(..., description="被攻击者")
    attack_type: str = Field(..., description="攻击类型：逻辑漏洞/利益冲突/现实矛盾/人性弱点/失败案例")
    attack_content: str = Field(..., min_length=30, description="攻击内容")
    emotion: EmotionType = Field(default=EmotionType.SERIOUS, description="攻击时的情绪")
    
    # 反击
    counter_attack: Optional[str] = Field(default=None, description="反击内容")
    counter_emotion: Optional[EmotionType] = Field(default=None, description="反击情绪")


class RealityCase(BaseModel):
    """现实案例 - 必须有代价"""
    case_name: str = Field(..., min_length=5, description="案例名称")
    case_source: str = Field(..., description="来源：个人经历/商业事件/社会现象/历史案例")
    case_content: str = Field(..., min_length=50, description="案例内容")
    case_outcome: str = Field(..., min_length=20, description="结果（必须有代价）")
    case_lesson: str = Field(..., min_length=20, description="教训")


class CostDiscussion(BaseModel):
    """代价讨论 - 如果这样做，会死在哪里"""
    scenario: str = Field(..., min_length=20, description="假设场景")
    cost_analysis: List[Dict[str, str]] = Field(..., min_items=2, description="代价分析")
    worst_case: str = Field(..., min_length=20, description="最坏情况")
    survivor_bias: Optional[str] = Field(default=None, description="幸存者偏差分析")


class HumanNatureLayer(BaseModel):
    """人性层 - 为什么人明知道对，还是做不到"""
    question: str = Field(..., min_length=20, description="人性问题")
    psychological_analysis: str = Field(..., min_length=50, description="心理分析")
    real_examples: List[str] = Field(..., min_items=2, description="现实例子")
    conclusion: str = Field(..., min_length=20, description="结论")


class CognitiveUpgrade(BaseModel):
    """认知升级 - 更复杂、更真实的结论"""
    old_thinking: str = Field(..., min_length=20, description="旧思维")
    new_thinking: str = Field(..., min_length=20, description="新思维")
    complexity: str = Field(..., min_length=30, description="复杂性说明")
    actionable_insight: str = Field(..., min_length=20, description="可执行洞见")


class DiscussionRound(BaseModel):
    """讨论轮次 - V8级结构"""
    round_number: int = Field(..., ge=1, le=10)
    topic: str = Field(..., min_length=5)
    core_question: str = Field(..., min_length=10)
    
    # Round1: 立场表达
    stances: List[Dict[str, str]] = Field(..., min_items=3, description="各专家立场")
    
    # Round2: 互相反驳
    clash_rounds: List[ClashRound] = Field(..., min_items=2, description="碰撞轮次")
    
    # Round3: 现实案例
    reality_cases: List[RealityCase] = Field(..., min_items=1, description="现实案例")
    
    # Round4: 代价讨论
    cost_discussion: CostDiscussion
    
    # Round5: 人性层
    human_nature: HumanNatureLayer
    
    # Round6: 认知升级
    cognitive_upgrade: CognitiveUpgrade
    
    # 情绪标记
    emotions: List[Dict[str, str]] = Field(default=[], description="情绪标记")


class RoundtableV8(BaseModel):
    """圆桌会议V8级内容"""
    title: str = Field(..., min_length=1, max_length=100)
    subtitle: str = Field(default="")
    
    # 专家档案
    experts: List[ExpertProfile] = Field(..., min_items=4, max_items=8)
    
    # 讨论轮次
    rounds: List[DiscussionRound] = Field(..., min_items=3, max_items=7)
    
    # 总结
    final_insight: str = Field(..., min_length=50, description="最终洞见")
    open_questions: List[str] = Field(..., min_items=2, description="开放问题")
    
    @validator('experts')
    def validate_experts(cls, v):
        """验证专家立场多样性"""
        stances = [e.stance for e in v]
        if len(set(stances)) < 2:
            raise ValueError('专家立场必须多样化，至少2种不同立场')
        return v


def validate_v8_content(data: dict) -> RoundtableV8:
    """验证V8级内容"""
    try:
        return RoundtableV8(**data)
    except Exception as e:
        raise ValueError(f"内容验证失败: {e}")