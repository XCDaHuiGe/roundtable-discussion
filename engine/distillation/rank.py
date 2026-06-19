# -*- coding: utf-8 -*-
"""Root-rank extractor: pull rank fields from a material dict."""
from __future__ import annotations


def extract_root_rank(data: dict) -> dict:
    """Extract root-rank fields from *data*.

    Parameters
    ----------
    data : dict
        Material dictionary that may contain:
        - ``phenomena`` or ``reality_cases``: list of phenomena
        - ``candidate_generators``: list of candidate generators
        - ``root_generators``: list of root generators
        - ``regeneration_matrix``: list of dicts with *phenomenon* and *generator*
        - ``domain_assumptions``: list of domain assumptions
        - ``prediction_tests``: list of prediction tests
        - ``rounds``: list of round dicts, each may have ``reality_cases``

    Returns
    -------
    dict
        A dictionary with keys: ``domain_assumptions``, ``phenomena``,
        ``candidate_generators``, ``root_generators``, ``regeneration_matrix``,
        ``prediction_tests``.  Missing fields are returned as empty lists.
    """
    phenomena = data.get("phenomena") or data.get("reality_cases") or []
    if not phenomena:
        phenomena = _phenomena_from_rounds(data.get("rounds", []))

    return {
        "domain_assumptions": list(data.get("domain_assumptions") or []),
        "phenomena": list(phenomena),
        "candidate_generators": list(data.get("candidate_generators") or []),
        "root_generators": list(data.get("root_generators") or []),
        "regeneration_matrix": _sanitize_matrix(data.get("regeneration_matrix")),
        "prediction_tests": list(data.get("prediction_tests") or []),
    }


def _phenomena_from_rounds(rounds: list) -> list[str]:
    """Collect phenomena from ``rounds[*].reality_cases``."""
    phenomena: list[str] = []
    for r in rounds:
        for case in r.get("reality_cases", []):
            if isinstance(case, str):
                phenomena.append(case)
    return phenomena


def _sanitize_matrix(raw) -> list[dict]:
    """Ensure every matrix item has *phenomenon* and *generator* keys."""
    if not raw:
        return []
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        result.append({
            "phenomenon": item.get("phenomenon", ""),
            "generator": item.get("generator", ""),
        })
    return result
