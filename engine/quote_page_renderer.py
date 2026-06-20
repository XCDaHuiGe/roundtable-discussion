# -*- coding: utf-8 -*-
"""
金句页渲染模块
为HTML-PPT添加专门的金句页视觉设计
"""
from __future__ import annotations

from html import escape
from typing import Dict, List, Optional


# ─── 金句页CSS ──────────────────────────────────────────────

QUOTE_PAGE_CSS = """
/* ═══════════════════════════════════════════════════════════════
   金句页样式
   ═══════════════════════════════════════════════════════════════ */

.quote-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 100vh;
  padding: 48px 72px;
  position: relative;
  background: var(--paper);
  overflow: hidden;
}

/* 装饰引号 */
.quote-page::before {
  content: "\u201C";
  font-size: clamp(120px, 15vw, 200px);
  color: var(--accent);
  opacity: 0.15;
  position: absolute;
  left: 10%;
  top: 15%;
  font-family: Georgia, serif;
  line-height: 1;
  z-index: 0;
}

.quote-page::after {
  content: "\u201D";
  font-size: clamp(120px, 15vw, 200px);
  color: var(--accent);
  opacity: 0.15;
  position: absolute;
  right: 10%;
  bottom: 15%;
  font-family: Georgia, serif;
  line-height: 1;
  z-index: 0;
}

/* 金句文字 */
.quote-text {
  font-size: clamp(36px, 5vw, 72px);
  font-weight: 900;
  line-height: 1.3;
  max-width: 85%;
  font-family: var(--serif);
  position: relative;
  z-index: 1;
  color: var(--ink);
  margin-bottom: 32px;
}

/* 作者署名 */
.quote-author {
  font-size: 18px;
  color: var(--muted);
  margin-top: 8px;
  font-family: var(--mono);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  position: relative;
  z-index: 1;
}

/* 作者头像 */
.quote-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}

/* 上下文说明 */
.quote-context {
  font-size: 14px;
  color: var(--muted);
  margin-top: 12px;
  max-width: 600px;
  line-height: 1.6;
  position: relative;
  z-index: 1;
}

/* 底部标签 */
.quote-tag {
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--accent);
  margin-top: 24px;
  padding: 6px 16px;
  border: 1px solid var(--accent);
  position: relative;
  z-index: 1;
}

/* ═══════════════════════════════════════════════════════════════
   金句页变体
   ═══════════════════════════════════════════════════════════════ */

/* 深色背景变体 */
.quote-page[data-tone="dark"] {
  background: var(--ink);
  color: var(--paper);
}

.quote-page[data-tone="dark"] .quote-text {
  color: var(--paper);
}

.quote-page[data-tone="dark"] .quote-author {
  color: rgba(var(--paper-rgb), 0.7);
}

.quote-page[data-tone="dark"] .quote-context {
  color: rgba(var(--paper-rgb), 0.6);
}

/* 强调变体 */
.quote-page.emphasis .quote-text {
  font-size: clamp(48px, 6vw, 96px);
  color: var(--accent);
}

/* 双人对比变体 */
.quote-versus {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  width: 100%;
  max-width: 1200px;
}

.quote-versus-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.quote-versus-item .quote-text {
  font-size: clamp(24px, 3vw, 42px);
  max-width: 90%;
}

.quote-versus-divider {
  width: 2px;
  background: var(--accent);
  opacity: 0.3;
}

/* ═══════════════════════════════════════════════════════════════
   金句页动画
   ═══════════════════════════════════════════════════════════════ */

@keyframes quoteFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes quoteScale {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}

.quote-page .quote-text {
  animation: quoteFadeIn 0.8s ease-out;
}

.quote-page .quote-author {
  animation: quoteFadeIn 0.8s ease-out 0.2s both;
}

.quote-page .quote-context {
  animation: quoteFadeIn 0.8s ease-out 0.4s both;
}

/* 深色页特殊背景 */
.quote-page[data-tone="dark"]::before {
  background:
    radial-gradient(circle at 30% 30%, rgba(var(--accent-rgb), 0.15), transparent 50%),
    radial-gradient(circle at 70% 70%, rgba(var(--accent-rgb), 0.1), transparent 50%);
}
"""


# ─── 金句页HTML生成 ──────────────────────────────────────────────

def render_quote_page(
    quote: str,
    author: str,
    context: Optional[str] = None,
    avatar_color: Optional[str] = None,
    tone: str = "light",
    emphasis: bool = False,
    tag: Optional[str] = None,
) -> str:
    """
    渲染单个金句页
    
    Args:
        quote: 金句内容
        author: 作者姓名
        context: 上下文说明（可选）
        avatar_color: 头像背景色（可选）
        tone: 色调（light/dark）
        emphasis: 是否强调模式
        tag: 底部标签（可选）
    
    Returns:
        HTML字符串
    """
    classes = ["quote-page"]
    if emphasis:
        classes.append("emphasis")
    
    data_attrs = f'data-tone="{tone}"' if tone == "dark" else ""
    
    avatar_html = ""
    if author:
        initial = author[0] if author else "?"
        color = avatar_color or "var(--accent)"
        avatar_html = f'<div class="quote-avatar" style="background:{color}">{escape(initial)}</div>'
    
    context_html = ""
    if context:
        context_html = f'<div class="quote-context">{escape(context)}</div>'
    
    tag_html = ""
    if tag:
        tag_html = f'<div class="quote-tag">{escape(tag)}</div>'
    
    return f"""
<section class="{' '.join(classes)}" {data_attrs}>
  {avatar_html}
  <div class="quote-text">{escape(quote)}</div>
  <div class="quote-author">— {escape(author)}</div>
  {context_html}
  {tag_html}
</section>
"""


def render_quote_versus_page(
    quote1: str,
    author1: str,
    quote2: str,
    author2: str,
    topic: Optional[str] = None,
) -> str:
    """
    渲染双人对比金句页
    
    Args:
        quote1: 第一个金句
        author1: 第一个作者
        quote2: 第二个金句
        author2: 第二个作者
        topic: 话题（可选）
    
    Returns:
        HTML字符串
    """
    topic_html = ""
    if topic:
        topic_html = f'<div class="reading-kicker">{escape(topic)}</div>'
    
    return f"""
<section class="quote-page" data-tone="dark">
  {topic_html}
  <div class="quote-versus">
    <div class="quote-versus-item">
      <div class="quote-avatar" style="background:var(--accent)">{escape(author1[0])}</div>
      <div class="quote-text">{escape(quote1)}</div>
      <div class="quote-author">— {escape(author1)}</div>
    </div>
    <div class="quote-versus-divider"></div>
    <div class="quote-versus-item">
      <div class="quote-avatar" style="background:var(--accent-2)">{escape(author2[0])}</div>
      <div class="quote-text">{escape(quote2)}</div>
      <div class="quote-author">— {escape(author2)}</div>
    </div>
  </div>
</section>
"""


def extract_quotes_from_debate(content: Dict) -> List[Dict]:
    """
    从辩论内容中提取金句
    
    Returns:
        [{"quote": str, "author": str, "context": str, "round": int}]
    """
    quotes = []
    
    for round_data in content.get("rounds", []):
        round_num = round_data.get("round_number", 0)
        
        # 从立场阐述中提取
        for stance in round_data.get("stances", []):
            text = stance.get("stance", "")
            author = stance.get("expert", "")
            # 提取最后的金句（通常是总结性语句）
            sentences = text.split("。")
            if len(sentences) > 1:
                # 取最后一句作为金句候选
                candidate = sentences[-1].strip()
                if len(candidate) > 10 and len(candidate) < 50:
                    quotes.append({
                        "quote": candidate,
                        "author": author,
                        "context": f"轮次{round_num} - 立场阐述",
                        "round": round_num,
                    })
        
        # 从交锋中提取
        for clash in round_data.get("clash_rounds", []):
            # 攻击方金句
            attack = clash.get("attack_content", "")
            attacker = clash.get("attacker", "")
            sentences = attack.split("。")
            if len(sentences) > 1:
                candidate = sentences[-1].strip()
                if len(candidate) > 10 and len(candidate) < 50:
                    quotes.append({
                        "quote": candidate,
                        "author": attacker,
                        "context": f"轮次{round_num} - 交锋",
                        "round": round_num,
                    })
            
            # 反驳方金句
            counter = clash.get("counter_attack", "")
            target = clash.get("target", "")
            sentences = counter.split("。")
            if len(sentences) > 1:
                candidate = sentences[-1].strip()
                if len(candidate) > 10 and len(candidate) < 50:
                    quotes.append({
                        "quote": candidate,
                        "author": target,
                        "context": f"轮次{round_num} - 反驳",
                        "round": round_num,
                    })
    
    return quotes


# 测试
if __name__ == "__main__":
    # 测试1：单人金句页
    html1 = render_quote_page(
        quote="避免愚蠢比追求聪明更重要",
        author="芒格",
        context="多元思维模型的核心智慧",
        tone="light",
        tag="核心洞见",
    )
    print("测试1 - 单人金句页:")
    print(html1[:300])
    print("...")
    
    # 测试2：双人对比金句页
    html2 = render_quote_versus_page(
        quote1="道法自然，无为而治",
        author1="老子",
        quote2="仁义礼智信，君子之道",
        author2="孔子",
        topic="道 vs 仁",
    )
    print("\n测试2 - 双人对比金句页:")
    print(html2[:300])
    print("...")
