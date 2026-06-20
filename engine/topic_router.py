# -*- coding: utf-8 -*-
"""
话题路由器：根据用户话题自动选择最佳 6 位专家。

选择策略：
1. 解析话题，提取关键词并映射到领域
2. 对每位专家计算 关键词重叠 + 领域相关度 评分
3. 确保领域多样性：至少 2 个不同领域、至多 3 个同领域、至少 1 个挑战者

用法：
    from engine.topic_router import select_experts, load_all_experts
    experts = select_experts("AI会取代人类的工作吗")
    experts = select_experts("人生的意义是什么", count=4)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional


# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────

EXPERT_DOMAINS = ["philosophy", "economics", "psychology", "sociology", "literature"]

# 每个领域的已知"挑战者"——其信念通常与主流对立，能制造张力
CHALLENGER_NAMES = {
    "philosophy": {"尼采", "叔本华", "萨特", "Nietzsche", "Schopenhauer", "Sartre",
                   "尼克_博斯特罗姆", "Nick Bostrom"},
    "economics":  {"塔勒布", "Taleb", "芒格", "Munger"},
    "psychology": {"弗洛伊德", "Freud", "丹尼尔_卡尼曼", "Kahneman"},
    "sociology":  {"马克思", "Marx", "项飙", "Xiang Biao"},
    "literature": {"丁元英", "李诞", "许知远"},
}

# ──────────────────────────────────────────────
# 关键词 → 领域映射（双向：话题词 → 领域，领域 → 相关话题词）
# ──────────────────────────────────────────────

KEYWORD_DOMAIN_MAP: Dict[str, List[str]] = {
    # --- philosophy ---
    "AI": ["philosophy", "economics", "literature"],
    "人工智能": ["philosophy", "economics", "literature"],
    "意义": ["philosophy"],
    "存在": ["philosophy"],
    "生死": ["philosophy", "psychology"],
    "自由": ["philosophy", "sociology"],
    "正义": ["philosophy", "sociology", "literature"],
    "道德": ["philosophy"],
    "伦理": ["philosophy", "sociology"],
    "人生": ["philosophy", "psychology"],
    "灵魂": ["philosophy"],
    "意识": ["philosophy", "psychology"],
    "信仰": ["philosophy"],
    "虚无": ["philosophy"],
    "死亡": ["philosophy", "psychology"],
    "哲学": ["philosophy"],
    "真理": ["philosophy"],
    "幸福": ["philosophy", "psychology"],
    "目的": ["philosophy"],
    "价值": ["philosophy", "economics"],
    "存在主义": ["philosophy"],
    "自我": ["philosophy", "psychology"],
    "超人": ["philosophy"],
    "无为": ["philosophy"],
    "道": ["philosophy"],
    "nature": ["philosophy"],
    "consciousness": ["philosophy", "psychology"],
    "freedom": ["philosophy"],
    "death": ["philosophy", "psychology"],
    "meaning": ["philosophy"],
    "morality": ["philosophy"],
    "ethics": ["philosophy", "sociology"],
    "truth": ["philosophy"],
    "philosophy": ["philosophy"],

    # --- economics ---
    "工作": ["economics", "sociology"],
    "经济": ["economics"],
    "市场": ["economics"],
    "投资": ["economics"],
    "创业": ["economics"],
    "金钱": ["economics"],
    "财富": ["economics"],
    "金融": ["economics"],
    "股票": ["economics"],
    "资本": ["economics", "sociology"],
    "商业": ["economics"],
    "职业": ["economics", "sociology"],
    "失业": ["economics", "sociology"],
    "消费": ["economics"],
    "通胀": ["economics"],
    "管理": ["economics"],
    "竞争": ["economics"],
    "效率": ["economics"],
    "风险": ["economics"],
    "不确定性": ["economics", "philosophy"],
    "内卷": ["economics", "sociology"],
    "躺平": ["economics", "sociology"],
    "996": ["economics", "sociology"],
    "裁员": ["economics"],
    "工资": ["economics"],
    "房价": ["economics"],
    "work": ["economics", "sociology"],
    "economy": ["economics"],
    "market": ["economics"],
    "investment": ["economics"],
    "business": ["economics"],
    "capital": ["economics", "sociology"],
    "money": ["economics"],
    "career": ["economics"],

    # --- psychology ---
    "情绪": ["psychology"],
    "焦虑": ["psychology"],
    "抑郁": ["psychology"],
    "心理": ["psychology"],
    "爱情": ["psychology", "literature"],
    "关系": ["psychology", "sociology"],
    "童年": ["psychology"],
    "创伤": ["psychology"],
    "欲望": ["psychology", "philosophy"],
    "潜意识": ["psychology"],
    "性格": ["psychology"],
    "幸福": ["psychology", "philosophy"],
    "恐惧": ["psychology"],
    "孤独": ["psychology", "philosophy"],
    "教育": ["psychology", "philosophy"],
    "习惯": ["psychology"],
    "动机": ["psychology"],
    "认知": ["psychology", "philosophy"],
    "思维": ["psychology", "philosophy"],
    "决策": ["psychology", "economics"],
    "behavior": ["psychology"],
    "emotion": ["psychology"],
    "anxiety": ["psychology"],
    "mind": ["psychology", "philosophy"],
    "love": ["psychology", "literature"],
    "psychology": ["psychology"],

    # --- sociology ---
    "社会": ["sociology"],
    "文化": ["sociology", "literature"],
    "权力": ["sociology", "philosophy"],
    "阶级": ["sociology"],
    "平等": ["sociology", "philosophy"],
    "民主": ["sociology", "philosophy"],
    "历史": ["sociology", "philosophy"],
    "文明": ["sociology", "philosophy"],
    "民族": ["sociology"],
    "全球化": ["sociology", "economics"],
    "技术": ["sociology", "economics", "literature"],
    "互联网": ["sociology", "economics", "literature"],
    "虚拟": ["sociology", "philosophy"],
    "媒体": ["sociology", "literature"],
    "算法": ["sociology", "economics"],
    "制度": ["sociology", "philosophy"],
    "异化": ["sociology", "philosophy"],
    "消费主义": ["sociology", "economics"],
    "社交媒体": ["sociology", "psychology"],
    "不平等": ["sociology"],
    "极权": ["sociology", "philosophy"],
    "humanity": ["sociology", "philosophy"],
    "society": ["sociology"],
    "culture": ["sociology", "literature"],
    "power": ["sociology"],
    "history": ["sociology"],
    "inequality": ["sociology"],
    "technology": ["sociology", "economics", "literature"],

    # --- literature ---
    "文学": ["literature"],
    "写作": ["literature"],
    "故事": ["literature"],
    "电影": ["literature"],
    "艺术": ["literature", "philosophy"],
    "美": ["literature", "philosophy"],
    "创作": ["literature"],
    "语言": ["literature", "philosophy"],
    "叙事": ["literature", "sociology"],
    "讽刺": ["literature"],
    "戏剧": ["literature"],
    "诗歌": ["literature"],
    "小说": ["literature"],
    "科幻": ["literature", "philosophy"],
    "反乌托邦": ["literature", "sociology"],
    "人性": ["literature", "philosophy", "psychology"],
    "生命": ["literature", "philosophy"],
    "命运": ["literature", "philosophy"],
    "天道": ["literature", "philosophy"],
    "literature": ["literature"],
    "writing": ["literature"],
    "art": ["literature", "philosophy"],
    "story": ["literature"],
    "fiction": ["literature"],
}

# 领域相关主题的补充触发词（当话题含有这些词时，额外加分）
DOMAIN_BOOST: Dict[str, List[str]] = {
    "philosophy": ["意义", "存在", "价值", "真理", "善", "美", "自由意志",
                    "虚无", "目的", "本质", "终极", "为什么", "是什么",
                    "meaning", "existence", "purpose", "essence", "why"],
    "economics":  ["效率", "增长", "利润", "成本", "供需", "贸易", "税",
                    "GDP", "就业", "物价", "收入", "分配",
                    "growth", "profit", "cost", "trade", "GDP", "income"],
    "psychology": ["感受", "情绪", "压力", "行为", "习惯", "自控", "幸福",
                    "焦虑", "恐惧", "上瘾", "偏见", "直觉",
                    "feeling", "stress", "behavior", "habit", "bias"],
    "sociology":  ["群体", "制度", "阶层", "权力", "文化", "传统", "变革",
                    "体制", "舆论", "共识", "冲突",
                    "group", "institution", "power", "culture", "change"],
    "literature": ["隐喻", "表达", "叙事", "风格", "审美", "悲剧", "荒诞",
                    "对话", "象征", "意象",
                    "metaphor", "narrative", "style", "aesthetic", "tragedy"],
}


# ──────────────────────────────────────────────
# 专家加载
# ──────────────────────────────────────────────

def load_all_experts(base_dir: Optional[str] = None) -> Dict:
    """
    加载所有专家 profile（*.md，排除 _知识边界.md 和 .snapshots）。

    Args:
        base_dir: expert-library 根目录，默认为项目根下的 expert-library

    Returns:
        dict: {name: {name, domain, core_beliefs, values, thinking_style,
                       identity, tags, file_path}}
    """
    if base_dir is None:
        # 推断项目根目录：engine/ 的上一级
        base_dir = str(Path(__file__).resolve().parent.parent / "expert-library")

    experts_dir = os.path.join(base_dir, "experts")
    if not os.path.isdir(experts_dir):
        raise FileNotFoundError(f"专家库目录不存在: {experts_dir}")

    experts = {}
    for domain in os.listdir(experts_dir):
        domain_path = os.path.join(experts_dir, domain)
        if not os.path.isdir(domain_path):
            continue

        for fname in os.listdir(domain_path):
            # 只加载 .md profile，跳过 知识边界 和快照
            if not fname.endswith(".md"):
                continue
            if "_知识边界" in fname:
                continue
            if fname.startswith("."):
                continue

            fpath = os.path.join(domain_path, fname)
            expert = _parse_expert_md(fpath, domain)
            if expert and expert["name"]:
                # 去重：如果同名已存在，训练次数更高的优先
                existing = experts.get(expert["name"])
                if existing is None or expert.get("version", "") > existing.get("version", ""):
                    experts[expert["name"]] = expert

    return experts


def _parse_expert_md(file_path: str, domain: str) -> Optional[Dict]:
    """
    解析单个专家 .md 文件，提取：姓名、核心信念、价值排序、思维风格、身份、标签。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    # 姓名：第一个 # 标题
    name = ""
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        name = m.group(1).strip()

    # 元信息中的分类（覆盖传入的 domain）
    cat_m = re.search(r"\*\*分类\*\*:\s*(\S+)", content)
    if cat_m:
        domain = cat_m.group(1).strip()

    # 版本号（用于去重）
    version = ""
    ver_m = re.search(r"\*\*版本\*\*:\s*(\S+)", content)
    if ver_m:
        version = ver_m.group(1).strip()

    # 核心信念
    core_beliefs = []
    bm = re.search(r"### 核心信念\n\n((?:- .+\n?)+)", content)
    if bm:
        for line in bm.group(1).strip().split("\n"):
            line = line.strip().lstrip("- ").strip()
            if line and line != "待填充":
                core_beliefs.append(line)

    # 价值排序
    values = []
    vm = re.search(r"### 价值排序\n\n((?:\d+\.\s*.+\n?)+)", content)
    if vm:
        for line in vm.group(1).strip().split("\n"):
            line = re.sub(r"^\d+\.\s*", "", line.strip())
            if line and line != "待填充":
                values.append(line)

    # 思维风格
    thinking_style = ""
    tm = re.search(r"\*\*思维风格\*\*:\s*(.+)", content)
    if tm:
        thinking_style = tm.group(1).strip()
        if thinking_style == "待填充":
            thinking_style = ""

    # 论证偏好
    argument_pref = ""
    am = re.search(r"\*\*论证偏好\*\*:\s*(.+)", content)
    if am:
        argument_pref = am.group(1).strip()
        if argument_pref == "待填充":
            argument_pref = ""

    # 身份
    identity = ""
    im = re.search(r"\*\*身份\*\*:\s*(.+)", content)
    if im:
        identity = im.group(1).strip()
        if identity == "待填充":
            identity = ""

    # 标签
    tags = []
    tgm = re.search(r"\*\*标签\*\*:\s*(.+)", content)
    if tgm:
        raw = tgm.group(1).strip()
        if raw and raw != "待填充":
            tags = [t.strip() for t in raw.split(",") if t.strip()]

    return {
        "name": name,
        "domain": domain,
        "core_beliefs": core_beliefs,
        "values": values,
        "thinking_style": thinking_style,
        "argument_pref": argument_pref,
        "identity": identity,
        "tags": tags,
        "version": version,
        "file_path": file_path,
    }


# ──────────────────────────────────────────────
# 话题解析
# ──────────────────────────────────────────────

def _extract_topic_keywords(topic: str) -> List[str]:
    """
    从话题字符串中提取关键词（中英文混合）。
    策略：最长匹配优先，逐步从话题中切出已知关键词。
    """
    found = []
    remaining = topic

    # 按长度降序匹配，避免短词误切长词的一部分
    sorted_kw = sorted(KEYWORD_DOMAIN_MAP.keys(), key=len, reverse=True)
    for kw in sorted_kw:
        if kw.lower() in remaining.lower():
            found.append(kw)
            # 从 remaining 中移除（忽略大小写）
            remaining = re.sub(re.escape(kw), "", remaining, flags=re.IGNORECASE)

    # 如果没匹配到任何已知关键词，用 jieba 风格的简单拆分（按空格/标点切）
    if not found:
        tokens = re.split(r"[\s,，。？！、；：""''（）\(\)\[\]【】]+", topic)
        found = [t for t in tokens if len(t) >= 2]

    return found


def _topic_to_domains(topic: str) -> Dict[str, float]:
    """
    根据话题关键词，计算各领域的相关度分数。

    Returns:
        dict: {domain: score}，分数越高表示话题越相关
    """
    keywords = _extract_topic_keywords(topic)
    domain_scores: Dict[str, float] = {d: 0.0 for d in EXPERT_DOMAINS}

    # 1) 关键词 → 领域 映射
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in KEYWORD_DOMAIN_MAP:
            for domain in KEYWORD_DOMAIN_MAP[kw_lower]:
                domain_scores[domain] += 1.0
        # 也尝试原始大小写
        if kw in KEYWORD_DOMAIN_MAP:
            for domain in KEYWORD_DOMAIN_MAP[kw]:
                domain_scores[domain] += 1.0

    # 2) 领域 boost：如果话题中出现领域相关触发词
    topic_lower = topic.lower()
    for domain, triggers in DOMAIN_BOOST.items():
        for trigger in triggers:
            if trigger.lower() in topic_lower:
                domain_scores[domain] += 0.5

    return domain_scores


# ──────────────────────────────────────────────
# 专家评分
# ──────────────────────────────────────────────

def _score_expert(expert: Dict, topic: str, topic_keywords: List[str],
                  domain_scores: Dict[str, float]) -> Dict:
    """
    为单个专家计算综合评分。

    Returns:
        dict: {name, domain, score, reason, is_challenger}
    """
    score = 0.0
    reasons = []

    # --- 1. 关键词重叠（在信念、价值、身份中出现话题关键词） ---
    searchable = " ".join(
        expert["core_beliefs"] + expert["values"]
        + [expert.get("identity", ""), expert.get("thinking_style", "")]
    ).lower()

    keyword_hits = 0
    for kw in topic_keywords:
        if kw.lower() in searchable:
            keyword_hits += 1
    if keyword_hits:
        kw_score = keyword_hits * 2.0
        score += kw_score
        reasons.append(f"关键词命中×{keyword_hits}")

    # --- 2. 领域相关度 ---
    expert_domain = expert.get("domain", "")
    domain_bonus = domain_scores.get(expert_domain, 0.0)
    if domain_bonus > 0:
        score += domain_bonus
        if domain_bonus >= 2.0:
            reasons.append(f"领域高度相关({expert_domain})")
        else:
            reasons.append(f"领域相关({expert_domain})")

    # --- 3. 信念丰富度加分（有内容的专家比空模板更有用） ---
    if expert["core_beliefs"]:
        belief_len = sum(len(b) for b in expert["core_beliefs"])
        richness = min(belief_len / 30.0, 2.0)  # 最多 +2
        score += richness
        if richness >= 1.0:
            reasons.append("信念丰富")

    # --- 4. 挑战者加分 ---
    is_challenger = expert["name"] in CHALLENGER_NAMES.get(expert_domain, set())
    if is_challenger:
        score += 1.5
        reasons.append("挑战者视角")

    # --- 5. 话题直接提及专家名字 ---
    if expert["name"] in topic:
        score += 10.0
        reasons.append("话题直接提及")

    return {
        "name": expert["name"],
        "domain": expert_domain,
        "score": round(score, 2),
        "reason": "、".join(reasons) if reasons else "无明显匹配",
        "is_challenger": is_challenger,
    }


# ──────────────────────────────────────────────
# 选择算法（多样性约束）
# ──────────────────────────────────────────────

def select_experts(topic: str, count: int = 6,
                   base_dir: Optional[str] = None) -> list:
    """
    为给定话题选择最佳专家组合。

    保证：
      - 至少 2 个不同领域
      - 至少 1 个挑战者
      - 至多 3 个同领域

    Args:
        topic: 用户话题字符串
        count: 选择专家数量（默认 6）
        base_dir: expert-library 根目录（可选）

    Returns:
        list of dict: [{name, domain, score, reason}, ...]
    """
    # 加载所有专家
    all_experts = load_all_experts(base_dir)
    if not all_experts:
        return []

    # 话题分析
    topic_keywords = _extract_topic_keywords(topic)
    domain_scores = _topic_to_domains(topic)

    # 为每位专家打分
    scored = []
    for expert in all_experts.values():
        result = _score_expert(expert, topic, topic_keywords, domain_scores)
        scored.append(result)

    # 按分数降序排列
    scored.sort(key=lambda x: x["score"], reverse=True)

    # 贪心选择 + 多样性约束
    selected = _select_with_constraints(scored, count)

    return selected


def _select_with_constraints(scored: list, count: int) -> list:
    """
    贪心选择，同时满足多样性约束。

    约束：
      1. 每个领域至多 3 人
      2. 最终至少 2 个不同领域
      3. 最终至少 1 个挑战者
    """
    MAX_PER_DOMAIN = 3

    selected: List[Dict] = []
    domain_count: Dict[str, int] = {}
    has_challenger = False

    # 第一轮：贪心按分选择，遵守每领域上限
    for expert in scored:
        if len(selected) >= count:
            break

        domain = expert["domain"]
        current = domain_count.get(domain, 0)

        if current >= MAX_PER_DOMAIN:
            continue

        selected.append(expert)
        domain_count[domain] = current + 1
        if expert["is_challenger"]:
            has_challenger = True

    # 后处理：检查多样性约束
    # 约束 1：至少 2 个不同领域
    unique_domains = set(e["domain"] for e in selected)
    if len(unique_domains) < 2 and len(selected) < count:
        # 找一个不同领域的高分专家加入
        for expert in scored:
            if expert["name"] in {e["name"] for e in selected}:
                continue
            if expert["domain"] not in unique_domains:
                selected.append(expert)
                domain_count[expert["domain"]] = 1
                unique_domains.add(expert["domain"])
                if expert["is_challenger"]:
                    has_challenger = True
                break

    # 约束 2：至少 1 个挑战者
    if not has_challenger:
        # 尝试用挑战者替换最低分的非挑战者
        challenger_candidates = [
            e for e in scored
            if e["is_challenger"] and e["name"] not in {s["name"] for s in selected}
        ]
        if challenger_candidates:
            # 替换最低分
            lowest_idx = len(selected) - 1
            if lowest_idx >= 0:
                removed = selected[lowest_idx]
                replacement = challenger_candidates[0]
                selected[lowest_idx] = replacement
                domain_count[removed["domain"]] = max(
                    0, domain_count.get(removed["domain"], 1) - 1
                )
                domain_count[replacement["domain"]] = (
                    domain_count.get(replacement["domain"], 0) + 1
                )

    # 按分数重新排序
    selected.sort(key=lambda x: x["score"], reverse=True)

    # 移除内部字段
    for e in selected:
        e.pop("is_challenger", None)

    return selected[:count]


# ──────────────────────────────────────────────
# 辅助：调试输出
# ──────────────────────────────────────────────

def explain_selection(topic: str, count: int = 6,
                      base_dir: Optional[str] = None) -> str:
    """
    返回人类可读的选择解释，用于调试。

    Returns:
        str: 格式化的解释文本
    """
    topic_keywords = _extract_topic_keywords(topic)
    domain_scores = _topic_to_domains(topic)
    selected = select_experts(topic, count, base_dir)

    lines = [
        f"话题: {topic}",
        f"提取关键词: {', '.join(topic_keywords)}",
        f"领域相关度: {domain_scores}",
        f"",
        f"选中专家 ({len(selected)}):",
    ]
    for i, e in enumerate(selected, 1):
        lines.append(
            f"  {i}. {e['name']} ({e['domain']}) "
            f"[分数: {e['score']}] {e['reason']}"
        )

    return "\n".join(lines)


# ──────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python engine/topic_router.py '你的话题'")
        print("示例: python engine/topic_router.py 'AI会取代人类的工作吗'")
        sys.exit(1)

    test_topic = sys.argv[1]
    test_count = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    print(explain_selection(test_topic, test_count))
