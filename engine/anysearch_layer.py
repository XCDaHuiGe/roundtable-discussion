# -*- coding: utf-8 -*-
"""
AnySearch Layer V4.0 — 系统级搜索（含回退机制）

优先使用AnySearch API，失败时回退到WebSearch Agent工具。
搜索结果自动写入memory目录缓存。

搜索优先级：
  AnySearch API → WebSearch Agent工具 → 本地缓存
"""

import subprocess
import json
import os
import hashlib
from datetime import datetime

ANYSEARCH_CLI = os.path.join(os.path.dirname(__file__), '..', '.trae', 'skills', 'anysearch', 'scripts', 'anysearch_cli.py')
SEARCH_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory', 'search_cache')

SOURCES = {
    'web': {'weight': 0.7, 'role': '现实案例', 'query_suffix': ''},
    'reddit': {'weight': 0.9, 'role': '真实情绪', 'query_suffix': 'site:reddit.com'},
    'arxiv': {'weight': 1.0, 'role': '学术证据', 'query_suffix': 'site:arxiv.org'},
    'github': {'weight': 1.0, 'role': '真实工程实践', 'query_suffix': 'site:github.com'},
}


def search_source(query: str, source: str = 'web', max_results: int = 5) -> dict:
    """搜索单个来源（AnySearch优先，失败回退）"""
    cached = _load_cache(query, source)
    if cached:
        return cached

    suffix = SOURCES.get(source, {}).get('query_suffix', '')
    full_query = f"{query} {suffix}".strip() if suffix else query

    result = _search_anysearch(full_query, max_results)
    if result['success']:
        result['source'] = source
        result['weight'] = SOURCES.get(source, {}).get('weight', 0.5)
        _save_cache(query, source, result)
        return result

    return {'success': False, 'source': source, 'error': result.get('error', 'AnySearch失败'), 'fallback': 'none'}


def multi_source_search(query: str, sources: list = None, max_results: int = 3) -> dict:
    """多源搜索"""
    if sources is None:
        sources = ['web', 'reddit', 'arxiv']

    results = {}
    for source in sources:
        if source in SOURCES:
            results[source] = search_source(query, source, max_results)

    return results


def system_search(query: str, max_results: int = 5) -> dict:
    """系统级搜索入口（自动选择最佳来源）"""
    result = search_source(query, 'web', max_results)
    if result['success']:
        return result

    result = search_source(query, 'reddit', max_results)
    if result['success']:
        return result

    return {'success': False, 'error': '所有搜索源均失败', 'query': query}


def extract_url(url: str) -> dict:
    """提取URL全文"""
    try:
        result = subprocess.run(
            ['python', ANYSEARCH_CLI, 'extract', url],
            capture_output=True, text=True, timeout=30, encoding='utf-8'
        )
        if result.returncode == 0:
            return {'success': True, 'content': result.stdout[:3000]}
        return {'success': False, 'error': result.stderr[:200]}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def build_material_text(search_results: dict, max_chars: int = 3000) -> str:
    """合并多源结果为带权重的素材文本"""
    parts = []
    for source, data in search_results.items():
        if data.get('success') and data.get('results'):
            weight = data.get('weight', 0.5)
            role = SOURCES.get(source, {}).get('role', source)
            parts.append(f"=== {source.upper()} ({role}, 权重:{weight}) ===\n{data['results'][:1000]}")
    return '\n\n'.join(parts)[:max_chars]


# ═══ AnySearch API ══════════════════════════════════════════

def _search_anysearch(query: str, max_results: int = 5) -> dict:
    """调用AnySearch CLI"""
    try:
        result = subprocess.run(
            ['python', ANYSEARCH_CLI, 'search', query, '--max_results', str(max_results)],
            capture_output=True, text=True, timeout=30, encoding='utf-8'
        )
        if result.returncode == 0 and result.stdout.strip():
            return {'success': True, 'results': result.stdout, 'method': 'anysearch'}
        return {'success': False, 'error': result.stderr[:200] if result.stderr else '空结果'}
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'AnySearch超时(30s)'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ═══ 缓存系统 ══════════════════════════════════════════════

def _cache_key(query: str, source: str) -> str:
    raw = f"{source}:{query}".encode('utf-8')
    return hashlib.md5(raw).hexdigest()[:12]


def _cache_path(query: str, source: str) -> str:
    os.makedirs(SEARCH_CACHE_DIR, exist_ok=True)
    key = _cache_key(query, source)
    return os.path.join(SEARCH_CACHE_DIR, f'{key}.json')


def _load_cache(query: str, source: str) -> dict:
    path = _cache_path(query, source)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        age_hours = (datetime.now().timestamp() - data.get('cached_at', 0)) / 3600
        if age_hours < 24:
            data['from_cache'] = True
            return data
    except Exception:
        pass
    return None


def _save_cache(query: str, source: str, result: dict):
    try:
        path = _cache_path(query, source)
        result['cached_at'] = datetime.now().timestamp()
        result['query'] = query
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
