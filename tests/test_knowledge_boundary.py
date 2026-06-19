# -*- coding: utf-8 -*-
"""
测试知识边界检查器和Prompt模板
"""
import pytest

from engine.knowledge_boundary_checker import (
    check_forbidden_words,
    check_knowledge_boundary,
    get_boundary,
    get_metaphor_guide,
    generate_expert_prompt_context,
)
from engine.prompts.expert_speak_v2 import (
    build_expert_speak_prompt,
    translate_to_era,
)


class TestKnowledgeBoundary:
    """知识边界检查器测试"""

    def test_get_boundary_laozi(self):
        """测试获取老子知识边界"""
        boundary = get_boundary("老子")
        assert boundary is not None
        assert boundary.name == "老子"
        assert boundary.era == "春秋时期"
        assert "道" in boundary.core_knowledge
        assert "AI" in boundary.forbidden_words

    def test_get_boundary_munger(self):
        """测试获取芒格知识边界"""
        boundary = get_boundary("芒格")
        assert boundary is not None
        assert "多元思维模型" in boundary.core_knowledge
        assert "量子" in boundary.forbidden_words

    def test_get_boundary_unknown(self):
        """测试获取未知专家"""
        boundary = get_boundary("未知专家")
        assert boundary is None

    def test_check_forbidden_words_pass(self):
        """测试通过禁用词检查"""
        text = "用多元思维模型来分析，首先要反过来想"
        result = check_forbidden_words(text, "芒格")
        assert result == []

    def test_check_forbidden_words_fail(self):
        """测试失败禁用词检查"""
        text = "AI是道的自我展开，算法的进化就像水的流动"
        result = check_forbidden_words(text, "老子")
        assert "AI" in result
        assert "算法" in result

    def test_check_forbidden_words_nietzsche(self):
        """测试尼采禁用词"""
        text = "量子力学证明了永恒轮回的可能性"
        result = check_forbidden_words(text, "尼采")
        assert "量子" in result

    def test_check_knowledge_boundary_pass(self):
        """测试通过知识边界检查"""
        text = "用多元思维模型来分析，首先要反过来想，避免愚蠢比追求聪明更重要"
        result = check_knowledge_boundary(text, "芒格")
        assert result["passed"] is True
        assert result["forbidden_words"] == []

    def test_check_knowledge_boundary_fail(self):
        """测试失败知识边界检查"""
        text = "AI是道的自我展开，算法的进化就像水的流动"
        result = check_knowledge_boundary(text, "老子")
        assert result["passed"] is False
        assert len(result["forbidden_words"]) > 0

    def test_check_knowledge_boundary_warnings(self):
        """测试知识边界警告"""
        # 孔子使用老子的核心概念"道法自然"
        text = "道法自然，仁义礼智信"
        result = check_knowledge_boundary(text, "孔子")
        assert len(result["warnings"]) > 0

    def test_check_knowledge_boundary_modern_words(self):
        """测试现代词汇警告"""
        text = "老子认为AI算法很好"
        result = check_knowledge_boundary(text, "老子")
        assert len(result["warnings"]) > 0


class TestMetaphorGuide:
    """比喻指南测试"""

    def test_get_metaphor_guide_laozi(self):
        """测试老子比喻指南"""
        guide = get_metaphor_guide("老子")
        assert "水" in guide["high_freq_words"]
        assert "水" in guide["metaphor_sources"]

    def test_get_metaphor_guide_munger(self):
        """测试芒格比喻指南"""
        guide = get_metaphor_guide("芒格")
        assert "棒球" in guide["metaphor_sources"]

    def test_get_metaphor_guide_unknown(self):
        """测试未知专家比喻指南"""
        guide = get_metaphor_guide("未知专家")
        assert guide == {}


class TestPromptContext:
    """Prompt上下文测试"""

    def test_generate_expert_prompt_context_laozi(self):
        """测试老子Prompt上下文"""
        context = generate_expert_prompt_context("老子")
        assert "老子" in context
        assert "春秋时期" in context
        assert "道" in context
        assert "AI" in context  # 禁用词列表中

    def test_generate_expert_prompt_context_munger(self):
        """测试芒格Prompt上下文"""
        context = generate_expert_prompt_context("芒格")
        assert "芒格" in context
        assert "当代" in context
        assert "多元思维模型" in context

    def test_generate_expert_prompt_context_unknown(self):
        """测试未知专家Prompt上下文"""
        context = generate_expert_prompt_context("未知专家")
        assert context == ""


class TestExpertSpeakPrompt:
    """专家发言Prompt测试"""

    def test_build_stance_prompt_laozi(self):
        """测试老子立场阐述Prompt"""
        prompt = build_expert_speak_prompt(
            expert_name="老子",
            topic="AI时代的工作替代",
            round_type="stance",
            emotion="calm",
        )
        assert "老子" in prompt
        assert "春秋时期" in prompt
        assert "AI时代的工作替代" in prompt
        assert "禁用词" in prompt

    def test_build_rebuttal_prompt_munger(self):
        """测试芒格反驳Prompt"""
        prompt = build_expert_speak_prompt(
            expert_name="芒格",
            topic="道德与能力哪个更重要",
            round_type="rebuttal",
            opponent_statement="道德是门槛，能力是加分项",
            emotion="serious",
        )
        assert "芒格" in prompt
        assert "道德是门槛" in prompt
        assert "反驳" in prompt

    def test_build_question_prompt_confucius(self):
        """测试孔子提问Prompt"""
        prompt = build_expert_speak_prompt(
            expert_name="孔子",
            topic="专业能力vs道德",
            round_type="question",
            emotion="calm",
        )
        assert "孔子" in prompt
        assert "问题" in prompt

    def test_build_synthesis_prompt_nietzsche(self):
        """测试尼采综合Prompt"""
        prompt = build_expert_speak_prompt(
            expert_name="尼采",
            topic="生命的意义",
            round_type="synthesis",
            emotion="enlightened",
        )
        assert "尼采" in prompt
        assert "升华" in prompt

    def test_build_prompt_unknown_expert(self):
        """测试未知专家Prompt"""
        prompt = build_expert_speak_prompt(
            expert_name="未知专家",
            topic="测试话题",
            round_type="stance",
        )
        assert "未知专家" in prompt


class TestEraTranslation:
    """时代翻译测试"""

    def test_translate_to_era_spring_autumn(self):
        """测试翻译到春秋时期"""
        text = "AI的算法效率很高"
        result = translate_to_era(text, "春秋时期")
        assert "巧器" in result
        assert "术" in result
        assert "AI" not in result

    def test_translate_to_era_19th_century(self):
        """测试翻译到19世纪"""
        text = "AI的算法效率很高"
        result = translate_to_era(text, "19世纪")
        assert "机械智能" in result
        assert "AI" not in result

    def test_translate_to_era_modern(self):
        """测试翻译到现代（无翻译）"""
        text = "AI的算法效率很高"
        result = translate_to_era(text, "当代")
        assert result == text

    def test_translate_to_era_no_match(self):
        """测试无匹配翻译"""
        text = "今天天气很好"
        result = translate_to_era(text, "春秋时期")
        assert result == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
