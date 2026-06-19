# -*- coding: utf-8 -*-
"""
V13 模板批量修复脚本 - 将旧模板修复为符合 V13 规范

修复项：
1. body/html 锁滚动
2. 去重导航脚本（保留最后一套）
3. 统一选择器（确保 .slide 有 100vh 和 overflow:hidden）
4. 修复 slide_selector_consistent
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ENGINE_DIR = Path(__file__).parent


def fix_body_html_lock(content: str) -> str:
    """确保 body 和 html 都锁滚动"""
    # 检查 html 是否有 overflow:hidden
    if not re.search(r"html\s*\{[^}]*overflow\s*:\s*hidden", content):
        # 在 <style> 标签内添加 html 锁滚动
        if "html {" in content:
            content = content.replace("html {", "html { overflow: hidden;", 1)
        elif "html{" in content:
            content = content.replace("html{", "html{overflow:hidden;", 1)
        else:
            # 在 body 之前添加
            content = content.replace("<style>", "<style>\nhtml { overflow: hidden; }\n", 1)

    # 确保 body 有 overflow:hidden
    if not re.search(r"body\s*\{[^}]*overflow\s*:\s*hidden", content):
        if "body {" in content:
            # 在 body { 后添加 overflow:hidden
            content = re.sub(r"(body\s*\{)", r"\1\n  overflow: hidden;", content, count=1)
        elif "body{" in content:
            content = re.sub(r"(body\{)", r"\1overflow:hidden;", content, count=1)

    return content


def fix_slide_height(content: str) -> str:
    """确保 .slide 有 height:100vh"""
    if not re.search(r"\.slide\s*\{[^}]*height\s*:\s*100vh", content):
        # 在 .slide 定义中添加 height:100vh
        content = re.sub(
            r"(\.slide\s*\{)",
            r"\1\n  height: 100vh;",
            content,
            count=1
        )
    return content


def fix_slide_overflow(content: str) -> str:
    """确保 .slide 有 overflow:hidden"""
    if not re.search(r"\.slide\s*\{[^}]*overflow\s*:\s*hidden", content):
        content = re.sub(
            r"(\.slide\s*\{)",
            r"\1\n  overflow: hidden;",
            content,
            count=1
        )
    return content


def fix_duplicate_scripts(content: str) -> str:
    """删除重复的导航脚本，保留最后一套"""
    # 找到所有 <script>...</script> 块
    script_pattern = r'<script[^>]*>\s*\(function\(\)\s*\{.*?\}\)\(\);\s*</script>'
    scripts = list(re.finditer(script_pattern, content, re.DOTALL))

    if len(scripts) <= 1:
        return content

    # 保留最后一个脚本（通常是最完整的）
    last_script = scripts[-1]
    scripts_to_remove = scripts[:-1]

    # 从后往前删除，避免偏移问题
    for script in reversed(scripts_to_remove):
        content = content[:script.start()] + content[script.end():]

    return content


def fix_selector_consistency(content: str) -> str:
    """统一选择器：如果混用 .slide 和 .section，统一为 .slide"""
    # 检查是否混用
    uses_slide = bool(re.search(r"querySelectorAll\s*\(\s*['\"]\.slide['\"]", content))
    uses_section = bool(re.search(r"querySelectorAll\s*\(\s*['\"]\.section['\"]", content))

    if uses_slide and uses_section:
        # 统一为 .slide
        content = re.sub(
            r"querySelectorAll\s*\(\s*['\"]\.section['\"]",
            "querySelectorAll('.slide'",
            content
        )

    return content


def fix_template(template_path: Path) -> bool:
    """修复单个模板，返回是否修改"""
    original = template_path.read_text(encoding="utf-8")
    content = original

    # 应用修复
    content = fix_body_html_lock(content)
    content = fix_slide_height(content)
    content = fix_slide_overflow(content)
    content = fix_duplicate_scripts(content)
    content = fix_selector_consistency(content)

    if content != original:
        template_path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    """修复所有 B 级模板"""
    config_path = ENGINE_DIR / "templates.json"
    if not config_path.exists():
        print("templates.json not found")
        return

    config = json.loads(config_path.read_text(encoding="utf-8"))
    fixed_count = 0

    for t in config.get("templates", []):
        template_path = ENGINE_DIR / t["file"]
        if not template_path.exists():
            print(f"SKIP {t['id']}: file not found")
            continue

        # 跳过 Handlebars legacy
        content = template_path.read_text(encoding="utf-8")
        if re.search(r"\{\{#each|\{\{add", content):
            print(f"SKIP {t['id']}: Handlebars legacy")
            continue

        if fix_template(template_path):
            print(f"FIXED {t['id']}")
            fixed_count += 1
        else:
            print(f"OK {t['id']}: no changes needed")

    print(f"\nFixed {fixed_count} templates")


if __name__ == "__main__":
    main()
