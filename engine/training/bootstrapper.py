# -*- coding: utf-8 -*-
"""
专家初始化器：从 V8 JSON 中提取专家数据，创建初始专家 .md 文件。

用法：
    python engine/training/bootstrapper.py --content-dir content --library expert-library
    python engine/training/bootstrapper.py --content-dir content --library expert-library --expert 巴菲特
    python engine/training/bootstrapper.py --content-dir content --library expert-library --dry-run
"""

import argparse
import glob
import json
import os
import re
import sys
from typing import Dict, List, Optional

# 名字归一化映射
NAME_NORMALIZE = {
    '纳西姆·塔勒布': '塔勒布',
    '沃伦·巴菲特': '巴菲特',
    '查理·芒格': '芒格',
    '吉姆·柯林斯': '柯林斯',
    '瑞·达利欧': '达利欧',
    '赫拉利': '尤瓦尔·赫拉利',
    '卡尼曼': '丹尼尔·卡尼曼',
    '戈尔曼': '丹尼尔·戈尔曼',
    '波伏娃': '西蒙娜·德·波伏娃',
}

# 分类映射
CATEGORY_MAP = {
    '巴菲特': 'economics', '芒格': 'economics', '达利欧': 'economics',
    '塔勒布': 'economics', '柯林斯': 'economics', '刘润': 'economics',
    '吴晓波': 'economics', '吴军': 'economics', '段永平': 'economics',
    '孔子': 'philosophy', '老子': 'philosophy', '韩非子': 'philosophy',
    '尼采': 'philosophy', '阿伦特': 'philosophy',
    '西蒙娜·德·波伏娃': 'philosophy', '尼克·博斯特罗姆': 'philosophy',
    '罗翔': 'philosophy',
    '丹尼尔·卡尼曼': 'psychology', '丹尼尔·戈尔曼': 'psychology',
    '弗洛伊德': 'psychology', '弗洛姆': 'psychology',
    '菲利普·津巴多': 'psychology',
    '项飙': 'sociology', '马克思': 'sociology', '许知远': 'sociology',
    '尤瓦尔·赫拉利': 'sociology',
    '李诞': 'literature', '凯文·凯利': 'literature',
    '阿西莫夫': 'literature', '冯唐': 'literature',
    '万维钢': 'literature', '丁元英': 'literature', '芮小丹': 'literature',
}


def normalize_name(name: str) -> str:
    return NAME_NORMALIZE.get(name, name)


class ExpertBootstrapper:

    def __init__(self, content_dir: str, library_dir: str):
        self.content_dir = content_dir
        self.library_dir = library_dir
        self.template_path = os.path.join(library_dir, 'templates', 'expert_template.md')

    def scan_all(self) -> Dict[str, Dict]:
        """扫描所有 JSON（V8 + 讨论），聚合专家数据。"""
        experts = {}

        # 扫描 V8 文件
        for fpath in sorted(glob.glob(os.path.join(self.content_dir, '*_v8.json'))):
            try:
                with open(fpath, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            self._process_file(data, fpath, experts)

        # 扫描讨论文件（补充 V8 中没有的专家）
        for fpath in sorted(glob.glob(os.path.join(self.content_dir, '*_讨论.json'))):
            try:
                with open(fpath, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
                continue
            self._process_discussion_file(data, fpath, experts)

        return experts

    def _process_file(self, data: Dict, fpath: str, experts: Dict):
        """处理单个 V8 文件。"""
        book_title = data.get('title', os.path.basename(fpath))
        for e in data.get('experts', []):
            name = normalize_name(e['name'])
            if name not in experts:
                experts[name] = self._empty_expert(name)
            info = experts[name]
            info['files'].append(fpath)
            for field in ['title', 'core_belief', 'interest', 'fear', 'bias', 'speaking_style', 'experience']:
                new_val = e.get(field, '')
                if new_val and len(new_val) > len(info.get(field, '')):
                    info[field] = new_val
            self._extract_round_data(data, name, info, book_title)

    def _process_discussion_file(self, data: Dict, fpath: str, experts: Dict):
        """处理讨论文件（补充专家数据）。"""
        book_title = data.get('title', os.path.basename(fpath))

        # 从 experts 列表提取
        for e in data.get('experts', []):
            if isinstance(e, str):
                name = normalize_name(e)
            elif isinstance(e, dict):
                name = normalize_name(e.get('name', ''))
            else:
                continue
            if not name:
                continue
            if name not in experts:
                experts[name] = self._empty_expert(name)
                if isinstance(e, dict):
                    experts[name]['title'] = e.get('role', '')
            info = experts[name]
            if fpath not in info['files']:
                info['files'].append(fpath)

        # 从 rounds.speakers 提取（有些文件 experts 列表为空）
        for r in data.get('rounds', []):
            for s in r.get('speakers', []):
                if isinstance(s, dict) and 'expert' in s:
                    name = normalize_name(s['expert'])
                    if name and name not in experts:
                        experts[name] = self._empty_expert(name)
                        experts[name]['files'].append(fpath)

        # 提取发言数据
        for name in list(experts.keys()):
            if any(fpath in experts[name].get('files', []) for _ in [1]):
                self._extract_discussion_speeches(data, name, experts[name], book_title)

    def _extract_discussion_speeches(self, data: Dict, expert_name: str, info: Dict, book_title: str):
        """从讨论格式提取发言。"""
        for r in data.get('rounds', []):
            topic = r.get('theme', r.get('topic', ''))
            round_num = r.get('round_number', 0)

            # Round 1: speakers
            for s in r.get('speakers', []):
                if s.get('expert', '') == expert_name:
                    content = s.get('content', '')
                    if content and len(content) > 30:
                        info['speeches'].append({
                            'type': 'stance',
                            'content': content,
                            'topic': topic,
                            'round': round_num,
                            'book': book_title,
                        })

            # Round 2: attacks
            for a in r.get('attacks', []):
                if a.get('from', '') == expert_name:
                    content = a.get('content', '')
                    if content:
                        info['attacks'].append({
                            'type': 'attack',
                            'content': content,
                            'target': a.get('to', ''),
                            'attack_type': '逻辑漏洞',
                            'topic': topic,
                            'round': round_num,
                            'book': book_title,
                        })

            # Round 3: synthesis
            for s in r.get('synthesis', []):
                if s.get('expert', '') == expert_name:
                    content = s.get('content', '')
                    if content and len(content) > 30:
                        info['speeches'].append({
                            'type': 'stance',
                            'content': content,
                            'topic': topic,
                            'round': round_num,
                            'book': book_title,
                        })

    @staticmethod
    def _empty_expert(name: str) -> Dict:
        return {
            'name': name,
            'title': '',
            'core_belief': '',
            'interest': '',
            'fear': '',
            'bias': '',
            'speaking_style': '',
            'experience': '',
            'stance': '',
            'files': [],
            'speeches': [],
            'attacks': [],
            'defenses': [],
            'cases': [],
        }

    def _extract_round_data(self, data: Dict, expert_name: str, info: Dict, book_title: str):
        """从讨论轮次中提取该专家的所有发言。"""
        for r in data.get('rounds', []):
            topic = r.get('topic', '')
            round_num = r.get('round_number', 0)

            # 立场发言
            for s in r.get('stances', []):
                if normalize_name(s.get('expert', '')) == expert_name:
                    content = s.get('stance', '')
                    if content and len(content) > 30:
                        info['speeches'].append({
                            'type': 'stance',
                            'content': content,
                            'topic': topic,
                            'round': round_num,
                            'book': book_title,
                            'emotion': s.get('emotion', ''),
                        })

            # 攻击
            for c in r.get('clash_rounds', []):
                atk_content = c.get('attack_content', '') or ''
                counter = c.get('counter_attack')

                if normalize_name(c.get('attacker', '')) == expert_name and atk_content:
                    info['attacks'].append({
                        'type': 'attack',
                        'content': atk_content,
                        'target': c.get('target', ''),
                        'attack_type': c.get('attack_type', ''),
                        'topic': topic,
                        'round': round_num,
                        'book': book_title,
                    })

                # 防御（显式反击）
                if normalize_name(c.get('target', '')) == expert_name and counter:
                    info['defenses'].append({
                        'type': 'defense',
                        'content': counter,
                        'attacker': c.get('attacker', ''),
                        'attack_type': c.get('attack_type', ''),
                        'topic': topic,
                        'round': round_num,
                        'book': book_title,
                    })

            # 案例
            for rc in r.get('reality_cases', []):
                if rc.get('case_content'):
                    info['cases'].append({
                        'case_name': rc.get('case_name', ''),
                        'case_source': rc.get('case_source', ''),
                        'case_content': rc.get('case_content', ''),
                        'case_outcome': rc.get('case_outcome', ''),
                        'case_lesson': rc.get('case_lesson', ''),
                        'topic': topic,
                    })

    def bootstrap_all(self, dry_run: bool = False) -> Dict[str, str]:
        """创建所有专家 .md 文件。"""
        experts = self.scan_all()
        created = {}

        for name, info in sorted(experts.items()):
            category = self._classify_expert(name, info.get('title', ''))
            if not category:
                print(f"  SKIP: {name} (无法分类)")
                continue

            content = self._fill_template(info, category)

            # 确定文件路径
            cat_dir = os.path.join(self.library_dir, 'experts', category)
            safe_name = name.replace('·', '_').replace('/', '_')
            fpath = os.path.join(cat_dir, f"{safe_name}.md")

            if dry_run:
                print(f"  DRY-RUN: {name} -> {fpath}")
                print(f"    Soul: {info.get('core_belief', '')[:50]}...")
                print(f"    Speeches: {len(info['speeches'])}, Attacks: {len(info['attacks'])}, Cases: {len(info['cases'])}")
                created[name] = fpath
                continue

            os.makedirs(cat_dir, exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  CREATED: {name} -> {fpath}")
            created[name] = fpath

        return created

    def _classify_expert(self, name: str, title: str) -> str:
        """确定专家分类。"""
        if name in CATEGORY_MAP:
            return CATEGORY_MAP[name]
        # 从 title 推断
        title_lower = title.lower()
        if any(w in title_lower for w in ['投资', '经济', '商业', '管理', '财经', '企业家']):
            return 'economics'
        if any(w in title_lower for w in ['哲学', '思想家', '伦理']):
            return 'philosophy'
        if any(w in title_lower for w in ['心理', '行为', '精神']):
            return 'psychology'
        if any(w in title_lower for w in ['社会', '人类学', '政治']):
            return 'sociology'
        if any(w in title_lower for w in ['作家', '文学', '编剧', '科幻', '喜剧']):
            return 'literature'
        return 'sociology'  # 默认

    def _fill_template(self, info: Dict, category: str) -> str:
        """填充三层模板。"""
        name = info['name']
        title = info.get('title', '')
        core_belief = info.get('core_belief', '')
        interest = info.get('interest', '')
        fear = info.get('fear', '')
        bias = info.get('bias', '')
        speaking_style = info.get('speaking_style', '') or self._infer_speaking_style(info)
        experience = info.get('experience', '') or title

        # 策略层：从实际数据提取
        attack_modes = self._extract_attack_modes(info)
        defense_modes = self._extract_defense_modes(info)
        evidence_prefs = self._extract_evidence_prefs(info)
        interaction_strategies = self._extract_interaction_strategies(info)
        analysis_framework = self._build_analysis_framework(info)

        # 素材层：选最佳
        best_speeches = self._select_best_speeches(info, 5)
        best_cases = self._select_best_cases(info, 4)
        best_quotes = self._extract_quotes(info, 6)

        # 构建核心信念（3条）
        beliefs = self._build_beliefs(core_belief, interest, fear, bias)

        # 构建价值排序
        values = self._build_values(info)

        # 构建标签
        tags = self._build_tags(info)

        # 组装
        lines = []
        lines.append(f"# {name}")
        lines.append("")
        lines.append("## 元信息")
        lines.append("")
        lines.append(f"- **分类**: {category}")
        lines.append("- **版本**: V1")
        lines.append("- **训练次数**: 0")
        lines.append("- **最后训练**: 未训练")
        lines.append("- **当前评分**: 未评分")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 第一层：灵魂层（永不改变）")
        lines.append("")
        lines.append('> 训练不碰这一层。这是专家的\u201c基因\u201d。')
        lines.append("")
        lines.append("### 核心信念")
        lines.append("")
        for b in beliefs:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("### 价值排序")
        lines.append("")
        for i, v in enumerate(values, 1):
            lines.append(f"{i}. {v}")
        lines.append("")
        lines.append("### 思维底色")
        lines.append("")
        lines.append(f"- **思维风格**: {self._infer_thinking_style(info)}")
        lines.append(f"- **表达风格**: {speaking_style}")
        lines.append(f"- **论证偏好**: {self._infer_argument_style(info)}")
        lines.append("")
        lines.append("### 代表身份")
        lines.append("")
        lines.append(f"- **姓名**: {name}")
        lines.append(f"- **身份**: {title}")
        lines.append(f"- **时代**: {self._infer_era(info)}")
        lines.append(f"- **标签**: {', '.join(tags)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 第二层：策略层（训练升级的核心）")
        lines.append("")
        lines.append('> 每次训练替换升级，保持恒定大小。这是专家的\u201c武器库\u201d。')
        lines.append("")
        lines.append("### 分析框架")
        lines.append("")
        lines.append("> 面对任何议题时的分析路径。")
        lines.append("")
        lines.append("```")
        lines.append(analysis_framework)
        lines.append("```")
        lines.append("")
        lines.append("### 攻击模式")
        lines.append("")
        lines.append("> 当我要反驳别人时，优先使用这些角度（按优先级排序）。")
        lines.append("")
        lines.append("| 优先级 | 攻击角度 | 适用场景 | 杀伤力评级 |")
        lines.append("|--------|---------|---------|-----------|")
        for i, am in enumerate(attack_modes, 1):
            lines.append(f"| {i} | {am['angle']} | {am['scenario']} | {am['rating']} |")
        lines.append("")
        lines.append("### 防御模式")
        lines.append("")
        lines.append("> 当我被攻击时，用这些方式化解。")
        lines.append("")
        lines.append("| 被攻击类型 | 化解策略 | 成功率 |")
        lines.append("|-----------|---------|--------|")
        for dm in defense_modes:
            lines.append(f"| {dm['type']} | {dm['strategy']} | {dm['rate']} |")
        lines.append("")
        lines.append("### 证据偏好")
        lines.append("")
        lines.append("> 什么类型的证据我最常用、用得最好。")
        lines.append("")
        lines.append("| 证据类型 | 使用优先级 | 命中率 |")
        lines.append("|---------|-----------|--------|")
        for ep in evidence_prefs:
            lines.append(f"| {ep['type']} | {ep['priority']} | {ep['rate']} |")
        lines.append("")
        lines.append("### 交互策略")
        lines.append("")
        lines.append("> 面对不同风格的对手，我的应对策略。")
        lines.append("")
        lines.append("| 对手风格 | 我的策略 | 原因 |")
        lines.append("|---------|---------|------|")
        for ist in interaction_strategies:
            lines.append(f"| {ist['style']} | {ist['strategy']} | {ist['reason']} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 第三层：素材层（精选替换）")
        lines.append("")
        lines.append("> 每次训练：新增强的 → 淘汰弱的 → 总数不变。")
        lines.append("> 精选发言保持 5 条，核心案例保持 4 个，金句保持 6 条。")
        lines.append("")
        lines.append("### 精选发言（5条）")
        lines.append("")
        lines.append("> 最能代表这位专家风格和深度的发言片段。来自实战讨论。")
        lines.append("")
        for i, sp in enumerate(best_speeches, 1):
            lines.append(f"#### 发言 {i}")
            lines.append("")
            lines.append(f"- **场景**: {sp.get('topic', '讨论')}")
            lines.append(f"- **对手**: {sp.get('opponent', '训练讨论')}")
            lines.append(f"- **内容**: {sp.get('content', '')}")
            lines.append(f"- **效果**: {sp.get('effect', '风格鲜明')}")
            lines.append(f"- **杀伤力**: {sp.get('rating', '中')}")
            lines.append("")
        lines.append("### 核心案例（4个）")
        lines.append("")
        lines.append("> 最有说服力的案例。来自实战讨论或互联网素材。")
        lines.append("")
        for i, cs in enumerate(best_cases, 1):
            lines.append(f"#### 案例 {i}")
            lines.append("")
            lines.append(f"- **标题**: {cs.get('case_name', '案例')}")
            lines.append(f"- **来源**: {cs.get('case_source', '现实案例')}")
            lines.append(f"- **内容**: {cs.get('case_content', '')}")
            lines.append(f"- **用于**: {cs.get('topic', '讨论')}")
            lines.append(f"- **被引用次数**: 0")
            lines.append("")
        lines.append("### 金句库（6条）")
        lines.append("")
        lines.append("> 最犀利、最像这个人会说的话。")
        lines.append("")
        for i, q in enumerate(best_quotes, 1):
            lines.append(f"{i}. \"{q}\" — 杀伤力: 中")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 训练历史摘要")
        lines.append("")
        lines.append("> 自动记录每次训练的关键变化。最多保留最近 10 次。")
        lines.append("")
        lines.append("| 轮次 | 日期 | 话题 | 攻击效率 | 防御率 | 主要升级 |")
        lines.append("|------|------|------|---------|--------|---------|")
        lines.append("| — | — | — | — | — | — |")
        lines.append("")

        return '\n'.join(lines)

    def _build_beliefs(self, core_belief: str, interest: str, fear: str, bias: str) -> List[str]:
        """构建 3 条核心信念。"""
        beliefs = []
        if core_belief:
            beliefs.append(core_belief)
        if interest:
            beliefs.append(interest)
        if fear:
            beliefs.append(fear)
        # 确保至少 3 条
        while len(beliefs) < 3:
            if bias and bias not in beliefs:
                beliefs.append(bias)
            else:
                beliefs.append("待训练补充")
        return beliefs[:3]

    def _build_values(self, info: Dict) -> List[str]:
        """构建价值排序。"""
        values = []
        title = info.get('title', '')
        belief = info.get('core_belief', '')
        # 从 title 和 core_belief 推断
        if '投资' in title or '经济' in title:
            values = ['理性决策', '长期价值', '风险控制']
        elif '哲学' in title or '思想家' in title:
            values = ['真理追求', '独立思考', '人文关怀']
        elif '心理' in title or '行为' in title:
            values = ['实证研究', '人性理解', '科学方法']
        elif '社会' in title or '人类' in title:
            values = ['社会公正', '个体尊严', '批判思维']
        elif '作家' in title or '文学' in title:
            values = ['表达自由', '审美追求', '社会洞察']
        else:
            values = ['专业能力', '独立判断', '持续学习']
        return values

    def _infer_thinking_style(self, info: Dict) -> str:
        """推断思维风格。"""
        title = info.get('title', '')
        if any(w in title for w in ['投资', '经济', '商业', '管理']):
            return '实用主义'
        if any(w in title for w in ['哲学', '思想家']):
            return '理想主义'
        if any(w in title for w in ['心理', '行为']):
            return '怀疑主义'
        if any(w in title for w in ['社会', '人类']):
            return '批判主义'
        if any(w in title for w in ['作家', '文学', '喜剧']):
            return '解构主义'
        return '现实主义'

    def _infer_speaking_style(self, info: Dict) -> str:
        """从发言模式推断表达风格。"""
        speeches = info.get('speeches', [])
        if not speeches:
            return '冷静分析'
        total = ''.join([s.get('content', '') for s in speeches[:5]])
        excl = total.count('！') + total.count('!')
        ques = total.count('？') + total.count('?')
        if excl > 5:
            return '激情宣导'
        if ques > 5:
            return '追问式'
        if len(total) > 1000 and total.count('，') > 20:
            return '温和说理'
        return '冷静分析'

    def _infer_argument_style(self, info: Dict) -> str:
        """推断论证偏好。"""
        title = info.get('title', '')
        if any(w in title for w in ['投资', '经济', '数据']):
            return '数据实证'
        if any(w in title for w in ['哲学', '思想']):
            return '逻辑推演'
        if any(w in title for w in ['心理', '行为']):
            return '案例归纳'
        if any(w in title for w in ['作家', '文学']):
            return '类比隐喻'
        return '逻辑推演'

    def _infer_era(self, info: Dict) -> str:
        """推断活跃时代。"""
        title = info.get('title', '')
        era_map = {
            '孔子': '春秋时期', '老子': '春秋时期', '韩非子': '战国时期',
            '尼采': '19世纪', '弗洛伊德': '20世纪初',
            '马克思': '19世纪', '阿伦特': '20世纪',
        }
        name = info.get('name', '')
        if name in era_map:
            return era_map[name]
        if any(w in title for w in ['创始人', '代表']):
            return '历史人物'
        return '当代'

    def _build_tags(self, info: Dict) -> List[str]:
        """构建标签。"""
        tags = []
        title = info.get('title', '')
        name = info.get('name', '')
        # 从 title 提取关键词
        for word in ['投资', '哲学', '心理', '社会', '文学', '商业', '科学', '法律', '经济', '管理']:
            if word in title:
                tags.append(word)
        if not tags:
            tags = ['思想者']
        return tags[:5]

    def _extract_attack_modes(self, info: Dict) -> List[Dict]:
        """从实际攻击数据提取攻击模式。"""
        attacks = info.get('attacks', [])
        if not attacks:
            return [
                {'angle': '逻辑漏洞攻击', 'scenario': '对手论证不严密时', 'rating': '中'},
                {'angle': '现实矛盾攻击', 'scenario': '对手观点与事实矛盾时', 'rating': '中'},
                {'angle': '利益冲突攻击', 'scenario': '对手存在利益关联时', 'rating': '中'},
            ]
        # 按 attack_type 分组，取最常见的 3 种
        type_counts = {}
        for a in attacks:
            atype = a.get('attack_type', '逻辑漏洞')
            if atype not in type_counts:
                type_counts[atype] = []
            type_counts[atype].append(a)
        modes = []
        for atype, items in sorted(type_counts.items(), key=lambda x: -len(x[1])):
            best = max(items, key=lambda x: len(x.get('content', '')))
            modes.append({
                'angle': atype,
                'scenario': f"针对{best.get('target', '对手')}的{atype}观点",
                'rating': '高' if len(best.get('content', '')) > 200 else '中',
            })
            if len(modes) >= 3:
                break
        # 补齐到 3 个
        while len(modes) < 3:
            modes.append({'angle': '观点质疑', 'scenario': '对手立场偏激时', 'rating': '中'})
        return modes

    def _extract_defense_modes(self, info: Dict) -> List[Dict]:
        """从防御数据提取防御模式。"""
        defenses = info.get('defenses', [])
        if not defenses:
            return [
                {'type': '被指逻辑漏洞', 'strategy': '用事实和逻辑链重新论证', 'rate': '0% (待训练)'},
                {'type': '被要求举证', 'strategy': '补充具体案例和数据', 'rate': '0% (待训练)'},
                {'type': '被反问立场', 'strategy': '承认复杂性，坚持核心判断', 'rate': '0% (待训练)'},
            ]
        modes = []
        for d in defenses[:3]:
            modes.append({
                'type': f"被{d.get('attacker', '对手')}{d.get('attack_type', '攻击')}",
                'strategy': d.get('content', '')[:50],
                'rate': '0% (待训练)',
            })
        while len(modes) < 3:
            modes.append({'type': '被指理想化', 'strategy': '用现实案例回应', 'rate': '0% (待训练)'})
        return modes[:3]

    def _extract_evidence_prefs(self, info: Dict) -> List[Dict]:
        """从发言内容推断证据偏好。"""
        speeches = info.get('speeches', []) + info.get('attacks', [])
        all_text = ' '.join([s.get('content', '') for s in speeches])

        prefs = []
        # 检测各类证据使用
        if re.search(r'\d+%|\d+万|\d+亿', all_text):
            prefs.append({'type': '具体数字/数据', 'priority': '高', 'rate': '0% (待训练)'})
        if re.search(r'第.{1,3}章|情节|故事|书中', all_text):
            prefs.append({'type': '书中案例', 'priority': '高', 'rate': '0% (待训练)'})
        if re.search(r'历史上|现实中|案例|事件', all_text):
            prefs.append({'type': '历史案例', 'priority': '中', 'rate': '0% (待训练)'})
        if re.search(r'我认为|我的经验|我见过', all_text):
            prefs.append({'type': '个人经历', 'priority': '中', 'rate': '0% (待训练)'})
        if re.search(r'逻辑|推理|因为|所以|如果', all_text):
            prefs.append({'type': '逻辑推演', 'priority': '中', 'rate': '0% (待训练)'})

        # 补齐到 5 个
        defaults = [
            {'type': '哲学引用', 'priority': '低', 'rate': '0% (待训练)'},
            {'type': '类比隐喻', 'priority': '低', 'rate': '0% (待训练)'},
            {'type': '权威引用', 'priority': '低', 'rate': '0% (待训练)'},
        ]
        for d in defaults:
            if len(prefs) >= 5:
                break
            if not any(p['type'] == d['type'] for p in prefs):
                prefs.append(d)
        return prefs[:5]

    def _extract_interaction_strategies(self, info: Dict) -> List[Dict]:
        """推断交互策略。"""
        return [
            {'style': '犀利讽刺型', 'strategy': '保持冷静，用事实回应', 'reason': '避免情绪化导致失分'},
            {'style': '数据实证型', 'strategy': '承认数据，指出解读差异', 'reason': '尊重事实但坚持立场'},
            {'style': '哲学思辨型', 'strategy': '用具体案例回应抽象论证', 'reason': '把讨论拉回现实'},
        ]

    def _build_analysis_framework(self, info: Dict) -> str:
        """构建分析框架。"""
        title = info.get('title', '')
        name = info.get('name', '')
        belief = info.get('core_belief', '')

        if '投资' in title or '经济' in title:
            return f"""面对议题X，我的分析路径是：
1. 先看基本面：这个事物的内在价值是什么？
2. 再看市场定价：当前价格与价值的偏离程度
3. 评估风险收益比：最坏情况能否承受？
4. 得出结论：是否有足够的安全边际？"""
        if '哲学' in title or '思想' in title:
            return f"""面对议题X，我的分析路径是：
1. 先问本质：这个问题的根本假设是什么？
2. 再看历史：过去的思想家如何看待这个问题？
3. 检验逻辑：论证链条是否自洽？
4. 得出结论：我的立场是什么，为什么？"""
        if '心理' in title:
            return f"""面对议题X，我的分析路径是：
1. 先看行为：人们实际上是怎么做的？
2. 再看动机：背后的心理机制是什么？
3. 对比理论：现有理论能否解释这个现象？
4. 得出结论：如何利用这个洞察？"""
        return f"""面对议题X，我的分析路径是：
1. 先看事实：发生了什么，数据怎么说？
2. 再看结构：背后的利益关系和权力结构
3. 检验假设：主流叙事是否站得住脚？
4. 得出结论：我的判断是什么？"""

    def _select_best_speeches(self, info: Dict, count: int) -> List[Dict]:
        """选择最佳发言。"""
        speeches = info.get('speeches', [])
        # 按长度+修辞手法排序
        scored = []
        for s in speeches:
            content = s.get('content', '')
            score = len(content)
            # 加分：有证据标记
            if re.search(r'\d+%|\d+万|第.{1,3}章|案例|数据|事实上', content):
                score += 100
            # 加分：有修辞手法
            if re.search(r'就像|好比|本质上|说白了|坦白说', content):
                score += 50
            scored.append((score, s))

        scored.sort(key=lambda x: -x[0])
        result = []
        for _, s in scored[:count]:
            result.append({
                'topic': s.get('topic', '讨论'),
                'opponent': s.get('opponent', '训练讨论'),
                'content': s.get('content', '')[:500],
                'effect': '观点鲜明',
                'rating': '高' if len(s.get('content', '')) > 200 else '中',
            })
        # 补齐
        while len(result) < count:
            result.append({
                'topic': '待训练',
                'opponent': '待训练',
                'content': '(初始素材，待训练升级)',
                'effect': '待训练',
                'rating': '低',
            })
        return result

    def _select_best_cases(self, info: Dict, count: int) -> List[Dict]:
        """选择最佳案例。"""
        cases = info.get('cases', [])
        # 按内容长度排序
        scored = [(len(c.get('case_content', '')), c) for c in cases]
        scored.sort(key=lambda x: -x[0])
        result = [c for _, c in scored[:count]]
        # 补齐
        while len(result) < count:
            result.append({
                'case_name': '(待训练补充)',
                'case_source': '待训练',
                'case_content': '(初始素材，待训练升级)',
                'case_outcome': '',
                'case_lesson': '',
                'topic': '',
            })
        return result

    def _extract_quotes(self, info: Dict, count: int) -> List[str]:
        """提取金句。"""
        speeches = info.get('speeches', []) + info.get('attacks', [])
        quotes = []
        for s in speeches:
            content = s.get('content', '')
            # 按句号分割，找短而有力的句子
            sentences = re.split(r'[。！？]', content)
            for sent in sentences:
                sent = sent.strip()
                if 20 < len(sent) < 80:
                    # 加分：有修辞
                    if re.search(r'就像|好比|本质上|说白了|不是.*而是', sent):
                        quotes.append(sent)
                    elif len(sent) > 30:
                        quotes.append(sent)
        # 去重
        seen = set()
        unique = []
        for q in quotes:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        result = unique[:count]
        # 补齐
        while len(result) < count:
            result.append("(金句待训练补充)")
        return result


def main():
    parser = argparse.ArgumentParser(description='专家初始化器')
    parser.add_argument('--content-dir', default='content', help='V8 JSON 目录')
    parser.add_argument('--library', default='expert-library', help='专家库目录')
    parser.add_argument('--expert', help='只创建指定专家')
    parser.add_argument('--dry-run', action='store_true', help='只预览不写入')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    bootstrapper = ExpertBootstrapper(args.content_dir, args.library)

    if args.expert:
        # 创建单个专家
        experts = bootstrapper.scan_all()
        target = None
        for name, info in experts.items():
            if args.expert in name:
                target = (name, info)
                break
        if not target:
            print(f"Error: 未找到专家 '{args.expert}'")
            sys.exit(1)
        name, info = target
        category = bootstrapper._classify_expert(name, info.get('title', ''))
        if args.dry_run:
            content = bootstrapper._fill_template(info, category)
            print(content)
        else:
            cat_dir = os.path.join(args.library, 'experts', category)
            os.makedirs(cat_dir, exist_ok=True)
            safe_name = name.replace('·', '_').replace('/', '_')
            fpath = os.path.join(cat_dir, f"{safe_name}.md")
            content = bootstrapper._fill_template(info, category)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"CREATED: {name} -> {fpath}")
    else:
        print(f"\n{'='*60}")
        print(f"专家初始化器")
        print(f"{'='*60}\n")
        created = bootstrapper.bootstrap_all(dry_run=args.dry_run)
        print(f"\n总计: {len(created)} 位专家")


if __name__ == '__main__':
    main()
