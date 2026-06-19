import re
import os
from pathlib import Path

EXPERTS_DIR = Path(r"D:\vibe_coding\zhengliu\圆桌会议\expert-library\experts")
TODO_COMMENT = "<!-- TODO: 需要补充金句 -->"

PATTERN_1_PHRASES = [
    "我们再深一层。你说",
    "但让我告诉你为什么这是错的",
    "我举个反例:历史上所有伟大的进步",
]

PATTERN_2_PHRASES = [
    "那我问你一个最直接的问题:如果现实中你的观点被证伪了一次又一次,你还要坚持吗?",
    "你的理论听起来很完美,但世界不是按理论运行的",
]


def is_template_quote(text: str) -> bool:
    if all(p in text for p in PATTERN_1_PHRASES):
        return True
    if all(p in text for p in PATTERN_2_PHRASES):
        return True
    return False


def process_file(filepath: Path) -> dict:
    result = {"modified": False, "removed": 0, "remaining": 0, "needs_more": False}
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("### 金句库"):
            start_idx = i
            break

    if start_idx is None:
        return result

    quote_start = None
    for i in range(start_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped == "" or stripped.startswith(">"):
            continue
        if re.match(r"^\d+\.\s", stripped):
            quote_start = i
            break
        elif stripped.startswith("###") or stripped.startswith("---"):
            return result
        else:
            continue

    if quote_start is None:
        return result

    quote_end = quote_start
    for i in range(quote_start, len(lines)):
        stripped = lines[i].strip()
        if re.match(r"^\d+\.\s", stripped):
            quote_end = i
        elif stripped.startswith("###") or stripped == "---":
            break
        elif stripped == "":
            continue
        else:
            break

    quotes_block = lines[quote_start:quote_end + 1]
    parsed_quotes = []
    current_quote = None

    for line in quotes_block:
        m = re.match(r"^(\d+)\.\s+(.*)", line.strip())
        if m:
            if current_quote is not None:
                parsed_quotes.append(current_quote)
            current_quote = {"num": int(m.group(1)), "text": m.group(2), "raw": line}
        elif current_quote is not None:
            current_quote["text"] += line.strip()
            current_quote["raw"] += "\n" + line

    if current_quote is not None:
        parsed_quotes.append(current_quote)

    original_count = len(parsed_quotes)
    kept = [q for q in parsed_quotes if not is_template_quote(q["text"])]
    removed_count = original_count - len(kept)

    if removed_count == 0:
        result["remaining"] = original_count
        return result

    result["removed"] = removed_count
    result["remaining"] = len(kept)
    result["modified"] = True
    result["needs_more"] = len(kept) < 3

    new_quote_lines = []
    for idx, q in enumerate(kept, 1):
        m = re.match(r"^(\d+)\.\s+(.*)", q["raw"].strip())
        if m:
            new_text = q["raw"].strip()
            new_text = re.sub(r"^(\d+)\.", f"{idx}.", new_text, count=1)
            new_quote_lines.append(new_text)

    header_line = lines[start_idx]
    count_match = re.search(r"（(\d+)条）", header_line)
    if count_match:
        new_header = re.sub(r"（(\d+)条）", f"（{len(kept)}条）", header_line)
    else:
        new_header = header_line

    desc_line_idx = start_idx + 1
    while desc_line_idx < len(lines) and lines[desc_line_idx].strip() == "":
        desc_line_idx += 1

    after_quotes_idx = quote_end + 1

    new_lines = lines[:start_idx]
    new_lines.append(new_header)
    new_lines.append("")
    new_lines.append("> 最犀利、最像这个人会说的话。")
    new_lines.append("")

    if result["needs_more"]:
        new_lines.append(TODO_COMMENT)
        new_lines.append("")

    new_lines.extend(new_quote_lines)

    if after_quotes_idx < len(lines):
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.extend(lines[after_quotes_idx:])

    filepath.write_text("\n".join(new_lines), encoding="utf-8")
    return result


def main():
    md_files = sorted(EXPERTS_DIR.rglob("*.md"))
    print(f"扫描目录: {EXPERTS_DIR}")
    print(f"找到 {len(md_files)} 个专家文件\n")
    print("=" * 70)

    total_modified = 0
    total_removed = 0
    total_remaining = 0
    needs_more_files = []

    for filepath in md_files:
        result = process_file(filepath)
        expert_name = filepath.stem
        rel_path = filepath.relative_to(EXPERTS_DIR)

        if result["removed"] > 0:
            total_modified += 1
            total_removed += result["removed"]
            print(f"  ✂️  {rel_path}: 删除 {result['removed']} 条模板引文, 剩余 {result['remaining']} 条")
            if result["needs_more"]:
                needs_more_files.append(str(rel_path))
        elif result["remaining"] > 0:
            print(f"  ✅  {rel_path}: 无模板引文 ({result['remaining']} 条)")
        else:
            print(f"  ⚠️  {rel_path}: 未找到金句库")

        total_remaining += result["remaining"]

    print("=" * 70)
    print(f"\n📊 清理报告:")
    print(f"  修改文件数:       {total_modified}")
    print(f"  删除模板引文总数: {total_removed}")
    print(f"  保留引文总数:     {total_remaining}")

    if needs_more_files:
        print(f"\n⚠️  需要补充金句的文件 ({len(needs_more_files)} 个):")
        for f in needs_more_files:
            print(f"    - {f}")
    else:
        print(f"\n✅ 所有文件金句数量充足（≥3条）")


if __name__ == "__main__":
    main()
