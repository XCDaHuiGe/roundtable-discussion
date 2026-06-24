# -*- coding: utf-8 -*-
"""
测试8认知函数模块

测试范围：
1. 数据结构正确性
2. 各认知函数的prompt构建
3. CognitiveAnalyzer的协调功能
4. 分析报告的生成
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from engine.cognitive_functions import (
    CognitiveType,
    CognitiveResult,
    CognitiveAnalysisReport,
    CognitiveFunction,
    ContrarianFunction,
    RiskFunction,
    HistoricalFunction,
    MechanismFunction,
    SystemsFunction,
    IncentiveFunction,
    CompressionFunction,
    MetaCognitionFunction,
    CognitiveAnalyzer,
    quick_analyze,
)


# ─── 数据结构测试 ──────────────────────────────────────────

class TestCognitiveType:
    """测试CognitiveType枚举"""

    def test_all_types_exist(self):
        assert len(CognitiveType) == 8
        assert CognitiveType.CONTRARIAN.value == "contrarian"
        assert CognitiveType.RISK.value == "risk"
        assert CognitiveType.HISTORICAL.value == "historical"
        assert CognitiveType.MECHANISM.value == "mechanism"
        assert CognitiveType.SYSTEMS.value == "systems"
        assert CognitiveType.INCENTIVE.value == "incentive"
        assert CognitiveType.COMPRESSION.value == "compression"
        assert CognitiveType.META_COGNITION.value == "meta_cognition"


class TestCognitiveResult:
    """测试CognitiveResult数据类"""

    def test_create_result(self):
        result = CognitiveResult(
            cognitive_type=CognitiveType.CONTRARIAN,
            analysis="测试分析",
            confidence=0.85,
            key_insights=["洞见1", "洞见2"],
            challenges=["挑战1"],
            evidence_quality="strong",
            actionability="high",
        )
        assert result.cognitive_type == CognitiveType.CONTRARIAN
        assert result.confidence == 0.85
        assert len(result.key_insights) == 2

    def test_to_dict(self):
        result = CognitiveResult(
            cognitive_type=CognitiveType.RISK,
            analysis="风险分析",
            confidence=0.7,
            key_insights=["风险1"],
            challenges=["挑战1"],
            evidence_quality="moderate",
            actionability="medium",
        )
        d = result.to_dict()
        assert d["cognitive_type"] == "risk"
        assert d["confidence"] == 0.7
        assert isinstance(d["key_insights"], list)


class TestCognitiveAnalysisReport:
    """测试CognitiveAnalysisReport"""

    def test_create_report(self):
        results = [
            CognitiveResult(
                cognitive_type=CognitiveType.CONTRARIAN,
                analysis="分析1",
                confidence=0.8,
                key_insights=["洞见1"],
                challenges=["挑战1"],
                evidence_quality="strong",
                actionability="high",
            )
        ]
        report = CognitiveAnalysisReport(
            topic="测试话题",
            experts=["专家A", "专家B"],
            results=results,
            synthesis="综合洞见",
        )
        assert report.topic == "测试话题"
        assert len(report.results) == 1

    def test_get_high_confidence_insights(self):
        results = [
            CognitiveResult(
                cognitive_type=CognitiveType.CONTRARIAN,
                analysis="分析1",
                confidence=0.9,
                key_insights=["高置信洞见"],
                challenges=[],
                evidence_quality="strong",
                actionability="high",
            ),
            CognitiveResult(
                cognitive_type=CognitiveType.RISK,
                analysis="分析2",
                confidence=0.3,
                key_insights=["低置信洞见"],
                challenges=[],
                evidence_quality="weak",
                actionability="low",
            ),
        ]
        report = CognitiveAnalysisReport(
            topic="测试",
            experts=[],
            results=results,
            synthesis="",
        )
        high = report.get_high_confidence_insights(threshold=0.7)
        assert "高置信洞见" in high
        assert "低置信洞见" not in high

    def test_get_prompt_injection(self):
        results = [
            CognitiveResult(
                cognitive_type=CognitiveType.CONTRARIAN,
                analysis="反对分析",
                confidence=0.8,
                key_insights=["洞见"],
                challenges=["挑战"],
                evidence_quality="strong",
                actionability="high",
            )
        ]
        report = CognitiveAnalysisReport(
            topic="测试话题",
            experts=["A"],
            results=results,
            synthesis="综合分析",
        )
        injection = report.get_prompt_injection()
        assert "认知函数深度分析" in injection
        assert "CONTRARIAN" in injection
        assert "反对分析" in injection
        assert "综合分析" in injection


# ─── 认知函数类测试 ────────────────────────────────────────

class TestCognitiveFunctions:
    """测试各认知函数类"""

    def test_all_function_classes_exist(self):
        """验证所有8个函数类都存在"""
        classes = [
            ContrarianFunction, RiskFunction, HistoricalFunction,
            MechanismFunction, SystemsFunction, IncentiveFunction,
            CompressionFunction, MetaCognitionFunction,
        ]
        assert len(classes) == 8

    def test_function_attributes(self):
        """验证每个函数类都有必要属性"""
        functions = [
            ContrarianFunction(),
            RiskFunction(),
            HistoricalFunction(),
            MechanismFunction(),
            SystemsFunction(),
            IncentiveFunction(),
            CompressionFunction(),
            MetaCognitionFunction(),
        ]
        for func in functions:
            assert hasattr(func, "cognitive_type")
            assert hasattr(func, "display_name")
            assert hasattr(func, "description")
            assert hasattr(func, "focus_question")
            assert isinstance(func.cognitive_type, CognitiveType)

    def test_prompt_generation(self):
        """验证prompt生成"""
        topic = "AI会取代人类工作吗"
        experts = ["芒格", "赫拉利", "卡尼曼"]
        previous_args = [
            {"expert": "芒格", "stance": "support", "content": "AI将重塑工作"}
        ]

        func = ContrarianFunction()
        prompt = func._build_prompt(topic, experts, previous_args)
        assert topic in prompt
        assert "芒格" in prompt
        assert "反对者" in prompt

    def test_system_prompt(self):
        """验证系统提示词生成"""
        func = RiskFunction()
        system = func._get_system_prompt()
        assert "风险分析师" in system
        assert "JSON" in system

    def test_fallback_analysis(self):
        """验证回退分析"""
        func = MechanismFunction()
        result = func._fallback_analysis("测试", ["A"])
        assert result.confidence == 0.0
        assert result.evidence_quality == "weak"


# ─── CognitiveAnalyzer测试 ─────────────────────────────────

class TestCognitiveAnalyzer:
    """测试CognitiveAnalyzer协调器"""

    def test_init_all(self):
        """测试默认初始化（全部8个函数）"""
        analyzer = CognitiveAnalyzer()
        types = analyzer.get_cognitive_types()
        assert len(types) == 8

    def test_init_subset(self):
        """测试子集初始化"""
        types = [CognitiveType.CONTRARIAN, CognitiveType.RISK]
        analyzer = CognitiveAnalyzer(types)
        result_types = analyzer.get_cognitive_types()
        assert len(result_types) == 2
        assert CognitiveType.CONTRARIAN in result_types
        assert CognitiveType.RISK in result_types

    @patch("engine.cognitive_functions.call_llm_json")
    def test_analyze_single(self, mock_llm):
        """测试单个认知函数分析"""
        mock_llm.return_value = {
            "success": True,
            "data": {
                "analysis": "测试分析",
                "confidence": 0.8,
                "key_insights": ["洞见1"],
                "challenges": ["挑战1"],
                "evidence_quality": "moderate",
                "actionability": "medium",
            }
        }

        analyzer = CognitiveAnalyzer([CognitiveType.CONTRARIAN])
        result = analyzer.analyze(
            CognitiveType.CONTRARIAN,
            "测试话题",
            ["专家A"],
            [{"expert": "专家A", "stance": "support", "content": "测试"}],
        )
        assert result.confidence == 0.8
        assert "洞见1" in result.key_insights
        mock_llm.assert_called_once()

    @patch("engine.cognitive_functions.call_llm_json")
    def test_analyze_all(self, mock_llm):
        """测试全部认知函数分析"""
        mock_llm.return_value = {
            "success": True,
            "data": {
                "analysis": "测试分析",
                "confidence": 0.7,
                "key_insights": ["洞见1"],
                "challenges": ["挑战1"],
                "evidence_quality": "moderate",
                "actionability": "medium",
            }
        }

        analyzer = CognitiveAnalyzer([CognitiveType.CONTRARIAN, CognitiveType.RISK])
        report = analyzer.analyze_all("测试话题", ["专家A"])
        assert report.topic == "测试话题"
        assert len(report.results) == 2
        assert report.synthesis  # 综合洞见非空

    @patch("engine.cognitive_functions.call_llm_json")
    def test_llm_failure_fallback(self, mock_llm):
        """测试LLM调用失败时的回退"""
        mock_llm.return_value = {
            "success": False,
            "data": None,
            "error": "API调用失败",
        }

        analyzer = CognitiveAnalyzer([CognitiveType.CONTRARIAN])
        result = analyzer.analyze(
            CognitiveType.CONTRARIAN,
            "测试话题",
            ["专家A"],
            [],
        )
        assert result.confidence == 0.0
        assert "自动分析失败" in result.challenges[0]


# ─── 快捷函数测试 ──────────────────────────────────────────

class TestQuickAnalyze:
    """测试quick_analyze快捷函数"""

    @patch("engine.cognitive_functions.call_llm_json")
    def test_quick_analyze(self, mock_llm):
        """测试快捷分析函数"""
        mock_llm.return_value = {
            "success": True,
            "data": {
                "analysis": "快速分析",
                "confidence": 0.6,
                "key_insights": ["快速洞见"],
                "challenges": [],
                "evidence_quality": "moderate",
                "actionability": "medium",
            }
        }

        report = quick_analyze("测试话题", ["A", "B"])
        assert isinstance(report, CognitiveAnalysisReport)
        assert report.topic == "测试话题"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
