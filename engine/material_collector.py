# -*- coding: utf-8 -*-
"""
素材收集器 — 从多种来源聚合讨论素材

素材来源：
  1. Agent 通过 WebSearch 搜索的结果（传入文本）
  2. Agent 通过知乎 MCP 搜索的结果（传入文本）
  3. content_injector.py 的话题→书单映射
  4. 本地 content/ 目录下的已有素材文件

用法：
  from engine.material_collector import collect_material
  material = collect_material("AI会取代人类工作吗", web_text=..., zhihu_text=...)
"""

import os
import re
from typing import Dict, List, Optional

CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content')


def collect_material(
    topic: str,
    web_text: str = '',
    zhihu_text: str = '',
    max_chars: int = 8000,
) -> str:
    """聚合多来源素材为一段结构化文本

    Args:
        topic: 话题
        web_text: Agent 通过 WebSearch 搜索的结果
        zhihu_text: Agent 通过知乎 MCP 搜索的结果
        max_chars: 最大字符数

    Returns:
        结构化素材文本
    """
    parts = []

    # 1. 话题→书单映射
    book_material = _get_book_material(topic)
    if book_material:
        parts.append(f"=== 相关书籍素材 ===\n{book_material}")

    # 2. WebSearch 素材
    if web_text:
        parts.append(f"=== 互联网讨论素材 ===\n{web_text[:3000]}")

    # 3. 知乎素材
    if zhihu_text:
        parts.append(f"=== 知乎讨论素材 ===\n{zhihu_text[:2000]}")

    # 4. 本地已有素材
    local = _find_local_material(topic)
    if local:
        parts.append(f"=== 本地素材 ===\n{local[:2000]}")

    combined = '\n\n'.join(parts)
    return combined[:max_chars] if combined else f"话题：{topic}\n（暂无外部素材，请基于专家知识体系生成讨论）"


def _get_book_material(topic: str) -> str:
    """从 content_injector 获取话题相关书单"""
    try:
        from content_injector import TOPIC_BOOK_MAPPING

        # 简单关键词匹配
        topic_lower = topic.lower()
        matched_books = []

        for key, books in TOPIC_BOOK_MAPPING.items():
            if key in topic or any(k in topic for k in key.split('/')):
                matched_books.extend(books)

        if not matched_books:
            # 模糊匹配
            for key, books in TOPIC_BOOK_MAPPING.items():
                for char in key:
                    if char in topic and len(char) > 1:
                        matched_books.extend(books)
                        break

        if not matched_books:
            return ''

        lines = []
        for book in matched_books[:4]:  # 最多4本
            lines.append(f"《{book['name']}》- {book['author']}")
            if book.get('key_chapters'):
                lines.append(f"  关键章节: {', '.join(book['key_chapters'][:3])}")
            if book.get('quotes'):
                lines.append(f"  金句: {book['quotes'][0]}")

        return '\n'.join(lines)
    except Exception:
        return ''


def _find_local_material(topic: str) -> str:
    """在 content/ 目录下查找相关素材文件"""
    if not os.path.isdir(CONTENT_DIR):
        return ''

    # 从话题提取关键词
    keywords = re.findall(r'[\u4e00-\u9fff]{2,}', topic)
    if not keywords:
        return ''

    # 搜索素材文件
    for fname in os.listdir(CONTENT_DIR):
        if not fname.endswith('.md') and not fname.endswith('.json'):
            continue
        if fname.startswith('_') or fname.startswith('.'):
            continue

        fname_lower = fname.lower()
        if any(kw in fname_lower for kw in keywords):
            fpath = os.path.join(CONTENT_DIR, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 只返回前2000字
                return f"[来源: {fname}]\n{content[:2000]}"
            except Exception:
                continue

    return ''


def format_search_results(results: List[Dict]) -> str:
    """格式化搜索结果为素材文本

    Args:
        results: [{title, url, snippet}] 或 [{title, content}]

    Returns:
        格式化文本
    """
    lines = []
    for i, r in enumerate(results[:8], 1):
        title = r.get('title', f'结果{i}')
        content = r.get('snippet', r.get('content', ''))
        url = r.get('url', '')
        if content:
            lines.append(f"[{i}] {title}")
            if url:
                lines.append(f"    来源: {url}")
            lines.append(f"    {content[:300]}")
            lines.append('')
    return '\n'.join(lines)


if __name__ == '__main__':
    # 测试
    material = collect_material("AI会取代人类工作吗")
    print(f"素材长度: {len(material)} 字符")
    print(material[:500])
