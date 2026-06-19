# -*- coding: utf-8 -*-
from engine.distillation.rank import extract_root_rank


def test_extract_root_rank_full_input():
    """All fields present at top level → correct extraction."""
    data = {
        "phenomena": ["现象A", "现象B"],
        "candidate_generators": ["候选1", "候选2"],
        "root_generators": ["根1"],
        "regeneration_matrix": [
            {"phenomenon": "现象A", "generator": "候选1"},
        ],
        "domain_assumptions": ["假设X"],
        "prediction_tests": ["测试1"],
    }

    result = extract_root_rank(data)

    assert result["phenomena"] == ["现象A", "现象B"]
    assert result["candidate_generators"] == ["候选1", "候选2"]
    assert result["root_generators"] == ["根1"]
    assert result["regeneration_matrix"] == [
        {"phenomenon": "现象A", "generator": "候选1"},
    ]
    assert result["domain_assumptions"] == ["假设X"]
    assert result["prediction_tests"] == ["测试1"]


def test_extract_root_rank_missing_fields_return_empty_lists():
    """Empty dict → every field is an empty list."""
    result = extract_root_rank({})

    assert result["phenomena"] == []
    assert result["candidate_generators"] == []
    assert result["root_generators"] == []
    assert result["regeneration_matrix"] == []
    assert result["domain_assumptions"] == []
    assert result["prediction_tests"] == []


def test_extract_root_rank_phenomena_from_rounds_reality_cases():
    """When top-level phenomena is absent, extract from rounds[*].reality_cases."""
    data = {
        "rounds": [
            {"reality_cases": ["案例1", "案例2"]},
            {"reality_cases": ["案例3"]},
            {"other_field": "no_cases_here"},
        ],
    }

    result = extract_root_rank(data)

    assert result["phenomena"] == ["案例1", "案例2", "案例3"]


def test_extract_root_rank_reality_cases_alias():
    """Top-level ``reality_cases`` key works as alias for ``phenomena``."""
    data = {"reality_cases": ["别名A"]}

    result = extract_root_rank(data)

    assert result["phenomena"] == ["别名A"]


def test_extract_root_rank_phenomena_takes_priority_over_rounds():
    """Top-level phenomena wins over rounds reality_cases."""
    data = {
        "phenomena": ["顶层"],
        "rounds": [{"reality_cases": ["轮次"]}],
    }

    result = extract_root_rank(data)

    assert result["phenomena"] == ["顶层"]


def test_extract_root_rank_matrix_missing_keys_filled():
    """Matrix items missing phenomenon/generator get empty-string defaults."""
    data = {
        "regeneration_matrix": [
            {"phenomenon": "P1"},
            {"generator": "G2"},
            {"phenomenon": "P3", "generator": "G3"},
            "not_a_dict",
        ],
    }

    result = extract_root_rank(data)

    assert result["regeneration_matrix"] == [
        {"phenomenon": "P1", "generator": ""},
        {"phenomenon": "", "generator": "G2"},
        {"phenomenon": "P3", "generator": "G3"},
    ]
