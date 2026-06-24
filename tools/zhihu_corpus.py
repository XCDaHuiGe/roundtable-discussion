#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎搜索集成模块 - 圆桌讨论项目
用于在生成书籍讨论前检索书评和讨论内容作为语料库
"""

import json
import os
import sys
import time
from pathlib import Path

# 知乎搜索脚本路径
ZHIHU_SEARCH_SCRIPT = Path(__file__).parent.parent / "zhihu_search_skills" / "zhihu-search" / "scripts" / "zhihu-search.py"

# 环境变量
ZHIHU_ACCESS_SECRET = "d48b49056c4b6ed7d157695b7e10aa2e10cbff4f"

def search_zhihu(query: str, count: int = 5) -> dict:
    """
    调用知乎搜索API
    
    Args:
        query: 搜索关键词
        count: 返回数量 (1-10)
    
    Returns:
        搜索结果字典
    """
    import subprocess
    
    # 设置环境变量
    env = os.environ.copy()
    env["ZHIHU_ACCESS_SECRET"] = ZHIHU_ACCESS_SECRET
    env["HTTP_PROXY"] = "http://127.0.0.1:65532"
    env["HTTPS_PROXY"] = "http://127.0.0.1:65532"
    
    # 构建命令
    payload = json.dumps({"query": query, "count": count}, ensure_ascii=False)
    cmd = [sys.executable, str(ZHIHU_SEARCH_SCRIPT), payload]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=15
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr, "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "Search timeout", "exit_code": 1}
    except Exception as e:
        return {"error": str(e), "exit_code": 1}


def search_book_reviews(book_title: str, author: str = "", count: int = 10) -> dict:
    """
    搜索书籍相关书评和讨论
    
    Args:
        book_title: 书名
        author: 作者（可选）
        count: 返回数量
    
    Returns:
        搜索结果
    """
    # 构建搜索关键词
    queries = [
        f"{book_title} 书评",
        f"{book_title} {author} 评价",
        f"{book_title} 读后感",
        f"{book_title} 讨论"
    ]
    
    all_items = []
    seen_urls = set()
    
    for query in queries[:2]:  # 只搜索前2个关键词，避免过多请求
        result = search_zhihu(query, count=count)
        if result.get("code") == 0:
            for item in result.get("items", []):
                url = item.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_items.append(item)
        time.sleep(0.5)  # 避免请求过快
    
    return {
        "code": 0,
        "message": "success",
        "item_count": len(all_items),
        "items": all_items[:count]
    }


def search_topic_discussions(topic: str, count: int = 10) -> dict:
    """
    搜索话题相关讨论
    
    Args:
        topic: 话题关键词
        count: 返回数量
    
    Returns:
        搜索结果
    """
    queries = [
        f"{topic} 讨论",
        f"{topic} 观点",
        f"{topic} 分析"
    ]
    
    all_items = []
    seen_urls = set()
    
    for query in queries[:2]:
        result = search_zhihu(query, count=count)
        if result.get("code") == 0:
            for item in result.get("items", []):
                url = item.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_items.append(item)
        time.sleep(0.5)
    
    return {
        "code": 0,
        "message": "success",
        "item_count": len(all_items),
        "items": all_items[:count]
    }


def save_corpus(data: dict, output_path: str):
    """
    保存语料库到JSON文件
    
    Args:
        data: 语料数据
        output_path: 输出路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Corpus saved to: {output_path}")


def extract_key_points(items: list) -> list:
    """
    从搜索结果中提取关键观点
    
    Args:
        items: 搜索结果列表
    
    Returns:
        关键观点列表
    """
    key_points = []
    for item in items:
        summary = item.get("summary", "")
        if len(summary) > 50:  # 只保留有意义的摘要
            key_points.append({
                "title": item.get("title", ""),
                "author": item.get("author_name", ""),
                "key_point": summary[:300],  # 截取前300字
                "votes": item.get("vote_up_count", 0),
                "url": item.get("url", "")
            })
    return key_points


# 示例用法
if __name__ == "__main__":
    # 测试搜索
    print("Testing Zhihu Search...")
    result = search_zhihu("真需求 梁宁", count=3)
    print(json.dumps(result, ensure_ascii=False, indent=2))
