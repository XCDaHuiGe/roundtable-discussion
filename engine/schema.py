# -*- coding: utf-8 -*-
"""圆桌会议内容Schema定义 - 使用Pydantic验证AI输出"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class Speaker(BaseModel):
    """发言者"""
    name: str = Field(..., min_length=1, max_length=50, description="专家姓名")
    role: str = Field(..., min_length=1, max_length=100, description="专家角色")
    avatar_color: str = Field(default="#c23b22", description="头像背景色")
    content: str = Field(..., min_length=10, description="发言内容")


class Clash(BaseModel):
    """碰撞交锋"""
    type: str = Field(..., description="碰撞类型：情节反驳/细节挑战/逻辑追问/框架质疑/反例引入")
    expert: str = Field(..., description="专家姓名")
    content: str = Field(..., min_length=10, description="碰撞内容")


class Insight(BaseModel):
    """核心洞见"""
    statement: str = Field(..., min_length=10, description="洞见句")
    explanation: str = Field(..., min_length=10, description="洞见展开说明")


class Round(BaseModel):
    """讨论轮次"""
    round_number: int = Field(..., ge=1, le=10, description="轮次编号")
    topic: str = Field(..., min_length=2, description="讨论主题")
    question: str = Field(..., min_length=10, description="核心问题")
    speakers: List[Speaker] = Field(..., min_items=1, max_items=6, description="发言者列表")
    clashes: List[Clash] = Field(default=[], description="碰撞交锋")
    insight: Optional[Insight] = Field(default=None, description="本轮洞见")


class Dashboard(BaseModel):
    """讨论仪表盘"""
    total_experts: int = Field(..., ge=1, le=10)
    total_rounds: int = Field(..., ge=1, le=10)
    total_clashes: int = Field(default=0)
    total_insights: int = Field(default=0)
    experts: List[str] = Field(..., description="专家名单")


class TensionPoint(BaseModel):
    """张力点"""
    axis: str = Field(..., description="张力轴名称")
    description: str = Field(..., description="张力描述")


class OpenQuestion(BaseModel):
    """开放问题"""
    question: str = Field(..., min_length=10)


class RoundtablePPT(BaseModel):
    """圆桌会议PPT完整结构"""
    title: str = Field(..., min_length=1, max_length=100, description="书名/主题")
    subtitle: str = Field(default="", description="副标题")
    style: str = Field(default="严肃", description="风格：严肃/接地气/人物原有")
    dashboard: Dashboard
    rounds: List[Round] = Field(..., min_items=1, max_items=10)
    tensions: List[TensionPoint] = Field(default=[])
    open_questions: List[OpenQuestion] = Field(default=[])
    conclusion: str = Field(default="", description="结语")
    
    @validator('rounds')
    def validate_rounds(cls, v):
        """验证轮次编号连续"""
        for i, round in enumerate(v):
            if round.round_number != i + 1:
                raise ValueError(f'轮次编号不连续：期望{i+1}，实际{round.round_number}')
        return v


# Schema验证函数
def validate_content(data: dict) -> RoundtablePPT:
    """验证AI输出的内容是否符合Schema"""
    try:
        ppt = RoundtablePPT(**data)
        return ppt
    except Exception as e:
        raise ValueError(f"内容验证失败: {e}")