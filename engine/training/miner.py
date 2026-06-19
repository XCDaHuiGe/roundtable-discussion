# -*- coding: utf-8 -*-
"""
素材读取器：检查和读取本地已有的互联网素材包。

注意：互联网采风（知乎 MCP + WebSearch）由 SKILL/Agent 完成，
本模块只负责读取已采集的素材文件。

采风流程（由 SKILL.md Phase 0 定义）：
    1. SKILL/Agent 使用知乎 MCP search_content 搜索
    2. SKILL/Agent 使用 get_feed_detail 获取详情
    3. SKILL/Agent 使用 WebSearch 补充
    4. 输出到 content/{书名}_素材.md

本模块职责：
    - 检查素材文件是否存在
    - 读取并解析素材文件
    - 为 topic_builder 提供素材数据

用法：
    from training.miner import MaterialReader
    reader = MaterialReader('content')
    material = reader.read('穷查理宝典')
"""

import os
import re
from typing import Dict, List, Optional
from datetime import datetime


class MaterialReader:
    """素材文件读取器"""

    def __init__(self, content_dir: str = 'content'):
        self.content_dir = content_dir

    def exists(self, topic: str) -> bool:
        """检查素材文件是否存在"""
        path = self._find_material(topic)
        return path is not None

    def read(self, topic: str) -> Optional[Dict]:
        """
        读取素材文件并解析为结构化数据。

        Args:
            topic: 书名或主题关键词

        Returns:
            解析后的素材数据字典，或 None
        """
        path = self._find_material(topic)
        if not path:
            return None

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self._parse(content, topic)

    def list_available(self) -> List[str]:
        """列出所有可用的素材文件"""
        if not os.path.exists(self.content_dir):
            return []

        materials = []
        for f in os.listdir(self.content_dir):
            if f.endswith('_素材.md'):
                name = f.replace('_素材.md', '')
                materials.append(name)
        return materials

    def _find_material(self, topic: str) -> Optional[str]:
        """查找素材文件（支持模糊匹配）"""
        if not os.path.exists(self.content_dir):
            return None

        # 精确匹配
        exact = os.path.join(self.content_dir, f'{topic}_素材.md')
        if os.path.exists(exact):
            return exact

        # 模糊匹配
        safe_topic = re.sub(r'[<>:"/\\|?*]', '', topic)
        for f in os.listdir(self.content_dir):
            if f.endswith('_素材.md'):
                name = f.replace('_素材.md', '')
                if safe_topic in name or name in safe_topic:
                    return os.path.join(self.content_dir, f)

        return None

    def _parse(self, content: str, topic: str) -> Dict:
        """解析素材 .md 文件为结构化数据"""
        # 提取来源数
        source_match = re.search(r'\*\*来源数\*\*:\s*(\d+)', content)
        source_count = int(source_match.group(1)) if source_match else 0

        # 提取各观点
        opinions = []
        blocks = re.split(r'### 观点 \d+:', content)
        for block in blocks[1:]:
            title_end = block.find('\n')
            op_title = block[:title_end].strip() if title_end > 0 else ''

            quote_match = re.search(r'> (.*?)(?:\n\n|\n—)', block, re.DOTALL)
            quote = quote_match.group(1).strip() if quote_match else ''

            source_match = re.search(r'— \[来源: (https?://[^\]]+)\]', block)
            source = source_match.group(1) if source_match else ''

            if quote:
                opinions.append({
                    'title': op_title[:100],
                    'content': quote[:500],
                    'source': source,
                })

        # 提取争议点
        controversies = []
        controversy_section = ''
        in_section = False
        for line in content.split('\n'):
            if '争议' in line and line.startswith('## '):
                in_section = True
                continue
            if in_section and line.startswith('## '):
                break
            if in_section:
                controversy_section += line + '\n'

        if controversy_section.strip() and '待补充' not in controversy_section:
            points = re.findall(r'\d+\.\s*\*\*(.+?)\*\*', controversy_section)
            for p in points:
                controversies.append({
                    'point': p.strip()[:200],
                    'source': '素材争议点章节',
                })

        # 提取金句
        quotes = []
        quotes_section = ''
        in_section = False
        for line in content.split('\n'):
            if '金句' in line and line.startswith('## '):
                in_section = True
                continue
            if in_section and line.startswith('## '):
                break
            if in_section:
                quotes_section += line + '\n'

        quote_matches = re.findall(r'\d+\.\s*"(.+?)"', quotes_section)
        quotes = [q.strip() for q in quote_matches if len(q.strip()) > 5]

        return {
            'title': topic,
            'source_count': source_count,
            'opinions': opinions,
            'controversies': controversies,
            'quotes': quotes,
            'raw': content,
            'has_content': len(opinions) > 0,
        }


def main():
    """CLI: 列出可用素材"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    reader = MaterialReader('content')
    materials = reader.list_available()

    if not materials:
        print("没有找到素材文件。")
        print("请先使用 SKILL.md Phase 0 进行互联网采风：")
        print("  按照 SKILL.md 为《书名》进行互联网内容挖掘")
        return

    print(f"\n可用素材 ({len(materials)} 个):\n")
    for name in materials:
        data = reader.read(name)
        if data:
            status = f"{len(data['opinions'])} 个观点, {len(data['controversies'])} 个争议点"
            print(f"  {name} — {status}")


if __name__ == '__main__':
    main()
