# -*- coding: utf-8 -*-
"""人机协同投研重构圆桌洞见 - V8级渲染器"""

import json
import re
import os

def escape_html(text):
    """转义HTML特殊字符"""
    if not text:
        return ""
    text = str(text)
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def parse_content(text):
    """解析富文本标记"""
    if not text:
        return ""
    text = escape_html(text)
    text = text.replace('[br]', '<br>')
    text = re.sub(r'\[strong\](.*?)\[/strong\]', r'<strong>\1</strong>', text)
    text = re.sub(r'\[em\](.*?)\[/em\]', r'<em>\1</em>', text)
    return text

def render_sp_content(content_list):
    """渲染发言内容"""
    html = ""
    for item in content_list:
        if isinstance(item, dict):
            item_type = item.get('type', 'text')
            if item_type == 'br':
                html += '<br>'
            elif item_type == 'strong':
                html += f'<strong>{escape_html(item.get("text", ""))}</strong>'
            elif item_type == 'em':
                html += f'<em>{escape_html(item.get("text", ""))}</em>'
        else:
            html += escape_html(str(item))
    return html

def render_slide(slide):
    """渲染单个幻灯片"""
    slide_type = slide.get('type', 'content')
    elements = slide.get('elements', [])
    
    html = '<div class="slide-content">\n'
    
    for elem in elements:
        elem_type = elem.get('type')
        
        if elem_type == 'div':
            cls = elem.get('class', '')
            content = elem.get('text', '') or elem.get('content', '')
            
            if isinstance(content, list):
                if cls == 'grid-2':
                    grid_items = ''
                    for item in content:
                        item_html = ''
                        if isinstance(item, dict):
                            item_cls = item.get('class', '')
                            item_content = item.get('content', [])
                            inner = ''
                            for ic in item_content:
                                if isinstance(ic, dict):
                                    ic_type = ic.get('type')
                                    if ic_type == 'div':
                                        ic_cls = ic.get('class', '')
                                        ic_text = ic.get('text', '')
                                        if ic_cls == 'speaker-avatar':
                                            inner += f'<div class="speaker-avatar">{escape_html(ic_text)}</div>'
                                        elif ic_cls == 'speaker-name':
                                            inner += f'<div class="speaker-name">{escape_html(ic_text)}</div>'
                                        elif ic_cls == 'speaker-role':
                                            inner += f'<div class="speaker-role">{escape_html(ic_text)}</div>'
                                        elif 'card-' in ic_cls:
                                            inner += f'<div class="{ic_cls}">{escape_html(ic_text)}</div>'
                                        elif ic_cls == 'speaker-header':
                                            inner += f'<div class="speaker-header">{ic_text}</div>'
                                        elif ic_cls == 'profile-item':
                                            inner += f'<div class="profile-item">{ic_text}</div>'
                                        elif 'card-body' in ic_cls:
                                            inner += f'<div class="{ic_cls}">{ic_text}</div>'
                                        elif 'quote' in ic_cls:
                                            inner += f'<div class="{ic_cls}">{ic_text}</div>'
                                        elif 'card-num' in ic_cls:
                                            inner += f'<div class="{ic_cls}">{escape_html(ic_text)}</div>'
                                        elif 'card-title' in ic_cls:
                                            inner += f'<div class="{ic_cls}">{ic_text}</div>'
                                        else:
                                            inner += f'<div class="{ic_cls}">{ic_text}</div>'
                                    elif isinstance(ic, str):
                                        inner += escape_html(ic)
                                elif isinstance(ic, str):
                                    inner += escape_html(ic)
                            item_html = f'<div class="{item_cls}">{inner}</div>'
                        elif isinstance(item, str):
                            item_html = f'<div>{escape_html(item)}</div>'
                        if item_html:
                            grid_items += item_html
                    html += f'<div class="{cls}">{grid_items}</div>\n'
                elif cls == 'card-rise':
                    inner = ''
                    for ic in content:
                        if isinstance(ic, dict):
                            ic_content = ic.get('content', [])
                            inner_content = ''
                            for iic in ic_content:
                                if isinstance(iic, dict):
                                    iic_cls = iic.get('class', '')
                                    iic_text = iic.get('text', '')
                                    if iic_cls == 'speaker-avatar':
                                        inner_content += f'<div class="speaker-avatar">{escape_html(iic_text)}</div>'
                                    elif iic_cls == 'speaker-name':
                                        inner_content += f'<div class="speaker-name">{escape_html(iic_text)}</div>'
                                    elif iic_cls == 'speaker-role':
                                        inner_content += f'<div class="speaker-role">{escape_html(iic_text)}</div>'
                                    elif iic_cls == 'speaker-header':
                                        ih = ''
                                        for iii in iic.get('content', []):
                                            if isinstance(iii, dict):
                                                iii_cls = iii.get('class', '')
                                                iii_text = iii.get('text', '')
                                                ih += f'<div class="{iii_cls}">{escape_html(iii_text)}</div>'
                                        inner_content += f'<div class="speaker-header">{ih}</div>'
                                    elif 'profile-item' in iic_cls:
                                        inner_content += f'<div class="{iic_cls}">{iic_text}</div>'
                                    else:
                                        inner_content += f'<div class="{iic_cls}">{iic_text}</div>'
                                elif isinstance(iic, str):
                                    inner_content += escape_html(iic)
                            inner += f'<div class="{iic_cls}">{inner_content}</div>'
                        elif isinstance(ic, str):
                            inner += escape_html(ic)
                    html += f'<div class="{cls}">{inner}</div>\n'
                elif 'card' in cls:
                    inner = ''
                    for ic in content:
                        if isinstance(ic, dict):
                            ic_text = ic.get('text', '')
                            ic_cls = ic.get('class', 'card-body')
                            inner += f'<div class="{ic_cls}">{ic_text}</div>'
                        elif isinstance(ic, str):
                            inner += escape_html(ic)
                    html += f'<div class="{cls}">{inner}</div>\n'
                elif 'clash-round' in cls:
                    inner = ''
                    for ic in content:
                        if isinstance(ic, dict):
                            ic_cls = ic.get('class', '')
                            ic_text = ic.get('text', '')
                            ic_content = ic.get('content', [])
                            if ic_cls == 'clash-header':
                                ih = ''
                                for iii in ic_content:
                                    if isinstance(iii, dict):
                                        iii_cls = iii.get('class', '')
                                        iii_text = iii.get('text', '')
                                        ih += f'<span class="{iii_cls}">{escape_html(iii_text)}</span>'
                                inner += f'<div class="{ic_cls}">{ih}</div>'
                            elif 'clash-type' in ic_cls:
                                inner += f'<div class="{ic_cls}">{escape_html(ic_text)}</div>'
                            elif 'clash-content' in ic_cls:
                                inner += f'<div class="{ic_cls}">{ic_text}</div>'
                            elif 'counter-attack' in ic_cls:
                                inner += f'<div class="{ic_cls}"></div>'
                            elif 'counter-label' in ic_cls:
                                inner += f'<div class="{ic_cls}">{escape_html(ic_text)}</div>'
                            elif 'counter-content' in ic_cls:
                                inner += f'<div class="{ic_cls}">{ic_text}</div>'
                            else:
                                inner += f'<div class="{ic_cls}">{ic_text}</div>'
                        elif isinstance(ic, str):
                            inner += escape_html(ic)
                    html += f'<div class="{cls}">{inner}</div>\n'
                elif 'cb' in cls:
                    inner = ''
                    for ic in content:
                        if isinstance(ic, dict):
                            ic_cls = ic.get('class', '')
                            ic_text = ic.get('text', '')
                            inner += f'<div class="{ic_cls}">{escape_html(ic_text)}</div>'
                        elif isinstance(ic, str):
                            inner += escape_html(ic)
                    html += f'<div class="{cls}">{inner}</div>\n'
                elif 'speaker-header' in cls:
                    ih = ''
                    for ic in content:
                        if isinstance(ic, dict):
                            ic_cls = ic.get('class', '')
                            ic_text = ic.get('text', '')
                            ih += f'<div class="{ic_cls}">{escape_html(ic_text)}</div>'
                    html += f'<div class="{cls}">{ih}</div>\n'
                elif 'speaker-avatar' in cls:
                    html += f'<div class="{cls}">{escape_html(content)}</div>\n'
                elif 'speaker-name' in cls:
                    html += f'<div class="{cls}">{escape_html(content)}</div>\n'
                elif 'speaker-role' in cls:
                    html += f'<div class="{cls}">{escape_html(content)}</div>\n'
                elif 'insight-c' in cls:
                    inner = ''
                    for ic in content:
                        if isinstance(ic, dict):
                            ic_cls = ic.get('class', '')
                            ic_text = ic.get('text', '')
                            inner += f'<div class="{ic_cls}">{ic_text}</div>'
                        elif isinstance(ic, str):
                            inner += escape_html(ic)
                    html += f'<div class="{cls}">{inner}</div>\n'
                else:
                    html += f'<div class="{cls}">{content}</div>\n'
            else:
                html += f'<div class="{cls}">{content}</div>\n'
        elif elem_type == 'rule':
            html += '<div class="rule"></div>\n'
    
    html += '</div>\n'
    return html

def render_discussion_slide(slide):
    """渲染讨论幻灯片"""
    data_title = slide.get('data_title', '')
    slide_class = slide.get('class', '')
    elements = slide.get('elements', [])
    
    content_html = render_slide(slide)
    
    return f'''<section class="slide {slide_class}" data-title="{data_title}">
{content_html}
</section>'''

def render_discussion(json_path, output_path, template_path):
    """渲染圆桌洞见HTML"""
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        content = json.load(f)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    slides_html = []
    for slide in content['discussions']:
        slide_html = render_discussion_slide(slide)
        slides_html.append(slide_html)
    
    slides_content = '\n'.join(slides_html)
    
    html = template.replace('<!-- SLIDES_HERE -->', slides_content)
    html = html.replace('__BOOK_TITLE__', content['metadata']['title'])
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ 渲染完成: {output_path}")
    print(f"  幻灯片数: {len(content['discussions'])}")
    print(f"  文件大小: {os.path.getsize(output_path):,} bytes")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "content", "人机协同_投研重构_讨论.json")
    output_path = os.path.join(base_dir, "output", "人机协同_投研重构_圆桌洞见.html")
    template_path = os.path.join(base_dir, "assets", "roundtable-template.html")
    
    render_discussion(json_path, output_path, template_path)
