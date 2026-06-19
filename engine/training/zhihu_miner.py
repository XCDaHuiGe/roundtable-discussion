# -*- coding: utf-8 -*-
"""
知乎 MCP 采风器：调用知乎 MCP 服务采集素材。

用法：
    python engine/training/zhihu_miner.py "AI创意边际成本归零"
    python engine/training/zhihu_miner.py --topics topics.txt
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

MCP_URL = "http://127.0.0.1:18061/mcp"


def mcp_call(tool_name: str, arguments: Dict) -> Optional[Dict]:
    """调用 MCP 工具"""
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/call',
        'params': {
            'name': tool_name,
            'arguments': arguments,
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(MCP_URL, data=data, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = resp.read().decode('utf-8')
        # Parse SSE response
        for line in result.split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        return json.loads(result)
    except Exception as e:
        print(f"  MCP 调用失败: {e}")
        return None


def search_zhihu(keyword: str, limit: int = 10) -> List[Dict]:
    """搜索知乎内容"""
    result = mcp_call('search_content', {
        'keyword': keyword,
        'search_type': '综合',
        'limit': limit,
    })
    if not result:
        return []

    # Extract search results from MCP response
    content = result.get('result', {}).get('content', [])
    if not content:
        return []

    # Parse the text content
    text = content[0].get('text', '') if content else ''
    # The MCP server saves results to files, return the path
    return text


def get_feed_detail(url: str) -> Optional[str]:
    """获取知乎内容详情"""
    result = mcp_call('get_feed_detail', {'url': url})
    if not result:
        return None
    content = result.get('result', {}).get('content', [])
    return content[0].get('text', '') if content else None


def mine_topic(topic: str, topic_short: str, content_dir: str = 'content') -> str:
    """为一个话题采风"""
    print(f"\n{'='*60}")
    print(f"  采风: {topic[:50]}...")
    print(f"{'='*60}")

    # 多角度搜索
    queries = [
        f"{topic_short} 观点 争议",
        f"{topic_short} 案例 现实",
        f"{topic_short} 批评 反对",
    ]

    all_results = []
    for i, q in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] 搜索: {q[:40]}...")
        search_result = search_zhihu(q, limit=10)
        if search_result:
            print(f"    搜索完成")
            all_results.append(search_result)
        else:
            print(f"    无结果")

    # 整合素材
    material = build_material(topic, topic_short, all_results)

    # 保存
    safe_name = topic_short.replace('"', '').replace('"', '').replace(':', '').replace('？', '')
    safe_name = safe_name[:30]
    path = os.path.join(content_dir, f'{safe_name}_素材.md')
    os.makedirs(content_dir, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(material)

    print(f"\n  素材已保存: {path}")
    return path


def build_material(topic: str, topic_short: str, search_results: List[str]) -> str:
    """整合素材包"""
    lines = []
    lines.append(f"# 《{topic_short}》互联网素材包")
    lines.append("")
    lines.append(f"> 采集时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 来源：知乎 MCP 搜索")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 一、主题概述")
    lines.append("")
    lines.append(f"- **主题**: {topic}")
    lines.append(f"- **来源数**: {len(search_results)}")
    lines.append("")

    lines.append("## 二、核心观点（来自互联网）")
    lines.append("")
    for i, result in enumerate(search_results[:10], 1):
        lines.append(f"### 观点 {i}")
        lines.append("")
        # Truncate long results
        text = result[:500] if isinstance(result, str) else str(result)[:500]
        lines.append(f"> {text}")
        lines.append("")

    lines.append("## 三、争议点/矛盾点")
    lines.append("")
    lines.append("(待 AI 从搜索结果中提取)")
    lines.append("")

    lines.append("## 四、现实案例")
    lines.append("")
    lines.append("(待 AI 从搜索结果中提取)")
    lines.append("")

    return '\n'.join(lines)


# 9 个话题
TOPICS = [
    ("\u521b\u610f\u8fb9\u9645\u6210\u672c\u5f52\u96f6\u7684\u8d44\u672c\u6697\u9762\uff1a\u5f53AI\u51fb\u7a7f\u6587\u5b66\u4e0e\u7535\u5f71\u7684\u751f\u4ea7\u58c1\u5792\uff0c\u6295\u8d44\u903b\u8f91\u5c06\u62bc\u6ce8\u7b97\u529b\u9738\u6743\u8fd8\u662f\u4eba\u7c7b\u539f\u751f\u7a00\u7f3a\u6027\uff1f", "AI\u521b\u610f\u8fb9\u9645\u6210\u672c\u5f52\u96f6"),
    ("\u9690\u5f62\u7b97\u6cd5\u76d1\u5de5\u4e0e\u5fc3\u7406\u5f02\u5316\uff1a\u5f53AI\u6210\u4e3a\u804c\u573a\u8d44\u6e90\u7684\u5206\u914d\u8005\uff0c\u5de5\u4f5c\u793e\u4f1a\u5b66\u4e2d\u7684\u4eba\u5982\u4f55\u9000\u5316\u4e3a\u91d1\u878d\u6548\u7387\u6a21\u578b\u4e2d\u7684\u8fb9\u9645\u53d8\u91cf\uff1f", "\u9690\u5f62\u7b97\u6cd5\u76d1\u5de5"),
    ("\u94f6\u5e55\u5e7b\u89c9\u4e0e\u6563\u6237\u72c2\u70ed\uff1a\u5f71\u89c6\u53d9\u4e8b\u5982\u4f55\u91cd\u5851\u5927\u4f17\u5bf9\u91d1\u878d\u6760\u6746\u7684\u6d6a\u6f2b\u5316\u60f3\u8c61\uff0c\u79d1\u6280\u5e73\u53f0\u53c8\u5982\u4f55\u5229\u7528\u6b64\u60c5\u7eea\u8fdb\u884c\u91cf\u5316\u5957\u5229\uff1f", "\u94f6\u5e55\u5e7b\u89c9\u4e0e\u6563\u6237\u72c2\u70ed"),
    ("\u6570\u5b57\u6c38\u751f\u7684\u60bc\u5ff5\u7ecf\u6d4e\u5b66\uff1aAI\u91cd\u5851\u901d\u8005\u5f71\u50cf\u4e0e\u6587\u5b66\u8bb0\u5fc6\uff0c\u662f\u5fc3\u7406\u521b\u4f24\u7684\u7597\u6108\uff0c\u8fd8\u662f\u5bf9\u6b7b\u4ea7\u7981\u5fcc\u4e0e\u60c5\u611f\u7f81\u7eca\u7684\u5546\u4e1a\u900f\u652f\uff1f", "\u6570\u5b57\u6c38\u751f\u7684\u60bc\u5ff5\u7ecf\u6d4e\u5b66"),
    ("\u65e0\u7528\u9636\u7ea7\u7684\u610f\u4e49\u91cd\u6784\uff1a\u5f53\u79d1\u6280\u5265\u593a\u4e86\u4f20\u7edf\u5de5\u4f5c\u7684\u751f\u5b58\u4ef7\u503c\uff0c\u5fc3\u7406\u5b66\u4e0e\u6587\u5b66\u5982\u4f55\u4e3a\u4e0d\u52b3\u52a8\u7684\u5168\u65b0\u751f\u6d3b\u63d0\u4f9b\u7cbe\u795e\u5408\u6cd5\u6027\uff1f", "\u65e0\u7528\u9636\u7ea7\u7684\u610f\u4e49\u91cd\u6784"),
    ("\u9ed1\u5929\u9e45\u65f6\u523b\u7684\u76f4\u89c9\u4fe1\u4ef0\uff1a\u5728AI\u7edf\u6cbb\u7684\u91cf\u5316\u91d1\u878d\u4e2d\uff0c\u4eba\u7c7b\u6295\u8d44\u8005\u57fa\u4e8e\u751f\u6d3b\u7ecf\u9a8c\u4e0e\u5fc3\u7406\u76f4\u89c9\u7684\u975e\u7406\u6027\uff0c\u662f\u98ce\u9669\u6e90\u6cc9\u8fd8\u662f\u6700\u540e\u62a4\u57ce\u6cb3\uff1f", "\u9ed1\u5929\u9e45\u65f6\u523b\u7684\u76f4\u89c9\u4fe1\u4ef0"),
    ("\u4e2d\u4ea7\u751f\u6d3b\u7684\u53d9\u4e8b\u6027\u7834\u4ea7\uff1a\u4ece\u6587\u5b66\u5e7b\u68a6\u5230\u6d88\u8d39\u4fe1\u8d37\uff0c\u91d1\u878d\u7cfb\u7edf\u5982\u4f55\u5229\u7528\u5fc3\u7406\u5b66\u9677\u9631\u5c06\u7406\u60f3\u751f\u6d3b\u5f02\u5316\u4e3a\u6c38\u4e0d\u6b47\u606f\u7684\u503a\u52a1\u67b7\u9501\uff1f", "\u4e2d\u4ea7\u751f\u6d3b\u7684\u53d9\u4e8b\u6027\u7834\u4ea7"),
    ("\u865a\u62df\u7a7a\u95f4\u7684\u5927\u8fc1\u5f99\u4e0e\u8d44\u4ea7\u91cd\u4f30\uff1a\u5f53\u7535\u5f71\u7ea7\u7684\u6c89\u6d78\u79d1\u6280\u5c06\u751f\u6d3b\u4e0e\u5de5\u4f5c\u5168\u9762\u8fc1\u5165\u865a\u62df\uff0c\u73b0\u5b9e\u4e16\u754c\u7684\u91d1\u878d\u8d44\u4ea7\u4f30\u503c\u903b\u8f91\u662f\u5426\u4f1a\u5f7b\u5e95\u5d29\u6e83\uff1f", "\u865a\u62df\u7a7a\u95f4\u7684\u5927\u8fc1\u5f99\u4e0e\u8d44\u4ea7\u91cd\u4f30"),
    ("\u60c5\u7eea\u52b3\u52a8\u7684\u7ec8\u6781\u5916\u5305\uff1a\u5f53AI\u63a5\u7ba1\u5de5\u4f5c\u573a\u666f\u4e2d\u7684\u60c5\u611f\u629a\u6170\uff0c\u4eba\u7c7b\u662f\u83b7\u5f97\u4e86\u5fc3\u7406\u89e3\u653e\uff0c\u8fd8\u662f\u4e27\u5931\u4e86\u751f\u53d1\u6587\u5b66\u4e0e\u5171\u60c5\u7684\u751f\u6d3b\u571f\u58e4\uff1f", "\u60c5\u7eea\u52b3\u52a8\u7684\u7ec8\u6781\u5916\u5305"),
]


def main():
    parser = argparse.ArgumentParser(description='知乎 MCP 采风器')
    parser.add_argument('--topic', help='单个话题')
    parser.add_argument('--all', action='store_true', help='采集所有 9 个话题')
    parser.add_argument('--content-dir', default='content', help='输出目录')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    if args.all:
        for topic_full, topic_short in TOPICS:
            mine_topic(topic_full, topic_short, args.content_dir)
    elif args.topic:
        # Find matching topic
        for topic_full, topic_short in TOPICS:
            if args.topic in topic_full or args.topic in topic_short:
                mine_topic(topic_full, topic_short, args.content_dir)
                break
        else:
            mine_topic(args.topic, args.topic[:20], args.content_dir)
    else:
        print("Usage: python zhihu_miner.py --all")
        print("       python zhihu_miner.py --topic 'AI创意'")


if __name__ == '__main__':
    main()
