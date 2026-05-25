import os
import zipfile
import re
from bs4 import BeautifulSoup
import sys
import glob

def extract_epub_text(epub_path, max_chars=80000):
    """从 EPUB 文件提取文本"""
    text_parts = []

    try:
        with zipfile.ZipFile(epub_path, 'r') as zf:
            # 找到所有 HTML 文件
            html_files = [f for f in zf.namelist() if f.endswith('.html') or f.endswith('.xhtml') or f.endswith('.htm')]

            # 按文件名排序以保持顺序
            html_files.sort()

            for html_file in html_files:
                try:
                    content = zf.read(html_file).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(content, 'html.parser')

                    # 移除脚本和样式
                    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()

                    # 提取文本
                    text = soup.get_text(separator=' ', strip=True)
                    text = re.sub(r'\s+', ' ', text)

                    if len(text) > 50:  # 忽略太短的片段
                        text_parts.append(text)

                    if sum(len(t) for t in text_parts) > max_chars:
                        break

                except Exception as e:
                    continue

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return ""

    full_text = ' '.join(text_parts)
    return full_text[:max_chars]

if __name__ == "__main__":
    # 找到穷查理宝典 EPUB 文件
    book_dir = r"C:\Users\gai\Downloads\书"
    epub_files = glob.glob(os.path.join(book_dir, "*.epub"))

    for f in epub_files:
        if "穷查理" in f:
            print(f"Found: {f}", file=sys.stderr)
            text = extract_epub_text(f)
            print(text)
            break
