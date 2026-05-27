#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证HTML圆桌洞见文件的脚本"""

import re
import os
from pathlib import Path

# 需要验证的文件列表
HTML_FILES = [
    "output/算法凝视下的情感套利_圆桌洞见.html",
    "output/算法多巴胺与叙事贫民窟_圆桌洞见.html",
    "output/生命资产的负债表_圆桌洞见.html",
    "output/赛博朋克的自我实现预言_圆桌洞见.html",
    "output/赛博亲密关系的经济学_圆桌洞见.html",
    "output/无用阶级_工作意义_圆桌洞见.html",
    "output/算法信用_人性异化_圆桌洞见.html",
    "output/人机协同_投研重构_圆桌洞见.html",
    "output/影视模因_散户狂潮_圆桌洞见.html",
    "output/经典文学_AI创作_圆桌洞见.html",
    "output/科幻叙事_投资泡沫_圆桌洞见.html",
    "output/虚构世界_资产化_圆桌洞见.html",
    "output/黑天鹅_量化博弈_圆桌洞见.html",
    "output/创意边际成本_内容投资_圆桌洞见.html",
    "output/AI生成叙事_金融定价_圆桌洞见.html",
    "output/段永平投资问答语录_圆桌洞见.html",
    "output/儒释道批判性分析_圆桌洞见.html",
    "output/穷查理宝典_圆桌洞见.html",
    "output/布鲁克林有棵树_圆桌洞见.html",
    "output/天道_圆桌洞见.html"
]

# 段永平相关的关键词
DUANYONGPING_KEYWORDS = ["段永平", "步步高", "OPPO", "vivo", "本分"]

def check_overflow(css_content):
    """检查CSS中是否有overflow-y: auto或scroll"""
    issues = []
    pattern = r'overflow-y\s*:\s*(auto|scroll)'
    matches = re.findall(pattern, css_content, re.IGNORECASE)
    if matches:
        issues.append(f"发现overflow-y: {', '.join(matches)}")
    return issues

def check_speech_length(html_content):
    """检查专家发言是否少于100字"""
    issues = []
    # 匹配发言内容块（假设在speech-content或speech-text类中）
    speech_pattern = r'<(?:div|p)[^>]*class="[^"]*(?:speech-content|speech-text)[^"]*"[^>]*>(.*?)</(?:div|p)>'
    speeches = re.findall(speech_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    for i, speech in enumerate(speeches):
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', speech).strip()
        # 移除多余空白
        clean_text = re.sub(r'\s+', '', clean_text)
        if len(clean_text) < 100:
            issues.append(f"发言{i+1}只有{len(clean_text)}字: {clean_text[:50]}...")
    return issues

def check_content_mixing(html_content, filename):
    """检查段永平内容是否串入非段永平话题"""
    issues = []
    is_duanyongping_file = "段永平" in filename
    
    # 如果不是段永平相关文件，检查是否包含段永平关键词
    if not is_duanyongping_file:
        for keyword in DUANYONGPING_KEYWORDS:
            if keyword in html_content:
                # 提取上下文
                idx = html_content.find(keyword)
                context_start = max(0, idx - 50)
                context_end = min(len(html_content), idx + len(keyword) + 50)
                context = html_content[context_start:context_end]
                issues.append(f"发现段永平相关内容'{keyword}': ...{context}...")
    
    return issues

def check_section_height(html_content):
    """检查section样式是否有100vh和overflow: hidden"""
    issues = []
    
    # 检查是否有section样式
    section_pattern = r'\.section\s*\{([^}]+)\}'
    sections = re.findall(section_pattern, html_content)
    
    if not sections:
        issues.append("未找到.section样式定义")
        return issues
    
    for i, section in enumerate(sections):
        if '100vh' not in section:
            issues.append(f"section样式{i+1}缺少100vh高度")
        if 'overflow: hidden' not in section and 'overflow:hidden' not in section:
            issues.append(f"section样式{i+1}缺少overflow: hidden")
    
    return issues

def validate_file(filepath):
    """验证单个HTML文件"""
    results = {
        "file": filepath,
        "overflow_issues": [],
        "speech_issues": [],
        "content_mixing_issues": [],
        "section_height_issues": []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取CSS部分
        css_pattern = r'<style[^>]*>(.*?)</style>'
        css_content = re.findall(css_pattern, content, re.DOTALL | re.IGNORECASE)
        css_text = '\n'.join(css_content)
        
        # 执行检查
        results["overflow_issues"] = check_overflow(css_text)
        results["speech_issues"] = check_speech_length(content)
        results["content_mixing_issues"] = check_content_mixing(content, filepath)
        results["section_height_issues"] = check_section_height(css_text)
        
    except FileNotFoundError:
        results["overflow_issues"].append(f"文件不存在: {filepath}")
    except Exception as e:
        results["overflow_issues"].append(f"读取错误: {str(e)}")
    
    return results

def main():
    """主函数"""
    print("=" * 60)
    print("HTML圆桌洞见文件验证报告")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    all_results = []
    
    for html_file in HTML_FILES:
        filepath = base_path / html_file
        print(f"\n验证: {html_file}")
        results = validate_file(str(filepath))
        all_results.append(results)
        
        # 输出结果
        issues = []
        issues.extend(results["overflow_issues"])
        issues.extend(results["speech_issues"])
        issues.extend(results["content_mixing_issues"])
        issues.extend(results["section_height_issues"])
        
        if issues:
            print(f"  ❌ 发现 {len(issues)} 个问题:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  ✅ 通过")
    
    # 汇总
    print("\n" + "=" * 60)
    print("验证汇总")
    print("=" * 60)
    
    passed = sum(1 for r in all_results if not any([
        r["overflow_issues"],
        r["speech_issues"],
        r["content_mixing_issues"],
        r["section_height_issues"]
    ]))
    failed = len(all_results) - passed
    
    print(f"总数: {len(all_results)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if failed > 0:
        print("\n需要修复的文件:")
        for r in all_results:
            issues = []
            issues.extend(r["overflow_issues"])
            issues.extend(r["speech_issues"])
            issues.extend(r["content_mixing_issues"])
            issues.extend(r["section_height_issues"])
            if issues:
                print(f"\n  {r['file']}:")
                for issue in issues:
                    print(f"    - {issue}")

if __name__ == "__main__":
    main()