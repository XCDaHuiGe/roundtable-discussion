# -*- coding: utf-8 -*-
"""
V15 JSON Schema - 认知研究架构

升级自V8格式，新增：
1. cognitive_dimensions: 10轴认知展开
2. tension_pairs: 核心张力对
3. hypothesis_evolution: 假设演化追踪
4. insight_delta: 认知增量评估
5. uncertainty: 不确定性管理
6. world_state: 世界状态模拟
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CognitiveDimension(BaseModel):
    """10轴认知展开"""
    concept: str = Field(default="", description="概念轴")
    causality: str = Field(default="", description="因果轴")
    contradiction: str = Field(default="", description="矛盾轴")
    boundary: str = Field(default="", description="边界轴")
    analogy: str = Field(default="", description="类比轴")
    historical: str = Field(default="", description="历史轴")
    future: str = Field(default="", description="未来轴")
    system: str = Field(default="", description="系统轴")
    incentive: str = Field(default="", description="激励轴")
    mechanism: str = Field(default="", description="机制轴")


class TensionPair(BaseModel):
    """核心张力对"""
    tension_id: str = Field(..., description="张力ID")
    pole_a: str = Field(..., description="张力极A")
    pole_b: str = Field(..., description="张力极B")
    description: str = Field(default="", description="张力描述")
    extreme_a: str = Field(default="", description="极值推演A")
    extreme_b: str = Field(default="", description="极值推演B")


class HypothesisEvolution(BaseModel):
    """假设演化追踪"""
    hypothesis_id: str = Field(..., description="假设ID")
    initial_form: str = Field(..., description="初始假设")
    evolution: List[Dict[str, Any]] = Field(default=[], description="演化记录")
    final_hypothesis: str = Field(default="", description="最终假设")
    evolution_quality: str = Field(default="low", description="演化质量")


class InsightDelta(BaseModel):
    """认知增量评估"""
    round_number: int = Field(..., description="轮次")
    new_insight: str = Field(default="", description="本轮新认知")
    dismissed_assumptions: List[str] = Field(default=[], description="被推翻的假设")
    gain_score: float = Field(default=0.0, description="增量分数 0.0-1.0")
    is_pseudo_depth: bool = Field(default=False, description="是否伪深度")


class Uncertainty(BaseModel):
    """不确定性管理"""
    claim: str = Field(..., description="核心观点")
    confidence: float = Field(default=0.5, description="置信度 0.0-1.0")
    certainty_grade: str = Field(default="medium", description="确定等级")
    uncertainty_sources: List[str] = Field(default=[], description="不确定来源")
    if_wrong_what_happens: str = Field(default="", description="如果错了的后果")


class WorldState(BaseModel):
    """世界状态模拟"""
    world_id: str = Field(default="default", description="世界ID")
    economic_state: Dict[str, Any] = Field(default={}, description="经济状态")
    technological_state: Dict[str, Any] = Field(default={}, description="技术状态")
    social_state: Dict[str, Any] = Field(default={}, description="社会状态")
    cultural_state: Dict[str, Any] = Field(default={}, description="文化状态")


class RoundtableV15(BaseModel):
    """圆桌会议V15 - 认知研究架构"""
    title: str = Field(..., min_length=1, max_length=100)
    subtitle: str = Field(default="")
    books: List[Dict[str, Any]] = Field(default=[], description="引用书籍")
    experts: List[Dict[str, Any]] = Field(..., min_length=4, max_length=8)
    rounds: List[Dict[str, Any]] = Field(..., min_length=3, max_length=7)
    final_insight: str = Field(default="")
    open_questions: List[str] = Field(default=[])
    
    # V15 新增字段
    cognitive_dimensions: Optional[CognitiveDimension] = Field(default=None, description="10轴认知展开")
    tension_pairs: List[TensionPair] = Field(default=[], description="核心张力对")
    hypothesis_evolution: List[HypothesisEvolution] = Field(default=[], description="假设演化追踪")
    insight_delta: List[InsightDelta] = Field(default=[], description="认知增量评估")
    uncertainty: List[Uncertainty] = Field(default=[], description="不确定性管理")
    world_state: Optional[WorldState] = Field(default=None, description="世界状态模拟")
    
    version: str = Field(default="v15", description="版本号")
    cognitive_architecture: str = Field(default="v7.2", description="认知架构版本")


def v8_to_v15(v8_data: Dict[str, Any]) -> RoundtableV15:
    """将V8格式转换为V15格式"""
    return RoundtableV15(
        title=v8_data.get("title", ""),
        subtitle=v8_data.get("subtitle", ""),
        books=v8_data.get("books", []),
        experts=v8_data.get("experts", []),
        rounds=v8_data.get("rounds", []),
        final_insight=v8_data.get("final_insight", ""),
        open_questions=v8_data.get("open_questions", []),
        version="v15",
        cognitive_architecture="v7.2"
    )


def v15_to_v8(v15_data: RoundtableV15) -> Dict[str, Any]:
    """将V15格式转换为V8格式（兼容）"""
    return {
        "title": v15_data.title,
        "subtitle": v15_data.subtitle,
        "books": v15_data.books,
        "experts": v15_data.experts,
        "rounds": v15_data.rounds,
        "final_insight": v15_data.final_insight,
        "open_questions": v15_data.open_questions
    }
