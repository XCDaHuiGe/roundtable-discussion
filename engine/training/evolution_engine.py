# -*- coding: utf-8 -*-
"""
⚠️ DEPRECATED (V11.0 起废弃) — 进化式升级引擎 V3.1

此模块已被 FusionEngine (fusion_engine.py V5.0) 取代。
auto_train.py V11.0 只使用 FusionEngine + Coach Review 闭环。
保留此文件仅供历史参考，不要在新代码中导入。

进化式升级引擎 V3.1

核心原则：
- 灵魂层：永不改变（基因）
- 策略层：融合升级（旧+新 → 更强版本）
- 素材层：质量判别（有必要增加才增加，不机械淘汰）

与 V2.0 的区别：
- V2.0 追加式：更多素材 = 更强（错误假设）
- V3.0 进化式：更密策略 = 更强
- V3.1 判别式：质量判别驱动，有必要增加才增加

用法：
    from engine.training.evolution_engine import EvolutionEngine
    engine = EvolutionEngine('expert-library')
    result = engine.evolve('孔子', strategy_data, topic='某话题', score=75.0)
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ─── 容量常量（质量判别驱动，有必要增加才增加）────────────

MAX_SPEECHES = 7
MAX_CASES = 6
MAX_QUOTES = 8
MAX_ATTACK_MODES = 4
MAX_DEFENSE_MODES = 4
MAX_TRAINING_HISTORY = 15


@dataclass
class EvolutionResult:
    """一次进化操作的结果"""
    expert_name: str
    file_path: str
    old_version: int
    new_version: int
    strategy_merges: List[str] = field(default_factory=list)
    material_replacements: List[str] = field(default_factory=list)
    density_delta: float = 0.0
    word_count_before: int = 0
    word_count_after: int = 0


class ExpertParser:
    """三层解析器：将 .md 拆分为灵魂/策略/素材"""

    def __init__(self, content: str):
        self.content = content
        self.sections = self._split_sections()

    def _split_sections(self) -> Dict[str, str]:
        """按三级标题拆分"""
        sections = {}
        current_key = ''
        current_lines = []

        for line in self.content.split('\n'):
            if line.startswith('## 第') and '层' in line:
                if current_key:
                    sections[current_key] = '\n'.join(current_lines)
                current_key = line.strip()
                current_lines = [line]
            elif line.startswith('## ') and '第' not in line:
                if current_key:
                    sections[current_key] = '\n'.join(current_lines)
                current_key = line.strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_key:
            sections[current_key] = '\n'.join(current_lines)

        return sections

    def get_meta(self) -> Dict:
        """提取元信息"""
        meta = {}
        for line in self.content.split('\n'):
            m = re.match(r'- \*\*(.+?)\*\*:\s*(.+)', line)
            if m:
                meta[m.group(1).strip()] = m.group(2).strip()
        return meta

    def get_soul(self) -> str:
        """获取灵魂层内容"""
        for key in self.sections:
            if '第一层' in key or '灵魂层' in key:
                return self.sections[key]
        return ''

    def get_strategy(self) -> str:
        """获取策略层内容"""
        for key in self.sections:
            if '第二层' in key or '策略层' in key:
                return self.sections[key]
        return ''

    def get_material(self) -> str:
        """获取素材层内容"""
        for key in self.sections:
            if '第三层' in key or '素材层' in key:
                return self.sections[key]
        return ''

    def get_training_history(self) -> str:
        """获取训练历史"""
        for key in self.sections:
            if '训练历史' in key:
                return self.sections[key]
        return ''

    def parse_attack_table(self) -> List[Dict]:
        """解析攻击模式表格"""
        strategy = self.get_strategy()
        rows = []
        pattern = r'### 攻击模式.*?\n\n>.*?\n\n(?:\|.*?\n)*((?:\|.*?\n)+)'
        m = re.search(pattern, strategy, re.DOTALL)
        if not m:
            return rows
        for line in m.group(1).strip().split('\n'):
            if '|' in line and '优先级' not in line and '---' not in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) >= 3:
                    rows.append({
                        'priority': cells[0],
                        'angle': cells[1],
                        'scenario': cells[2],
                        'rating': cells[3] if len(cells) > 3 else '中',
                    })
        return rows

    def parse_defense_table(self) -> List[Dict]:
        """解析防御模式表格"""
        strategy = self.get_strategy()
        rows = []
        pattern = r'### 防御模式.*?\n\n>.*?\n\n(?:\|.*?\n)*((?:\|.*?\n)+)'
        m = re.search(pattern, strategy, re.DOTALL)
        if not m:
            return rows
        for line in m.group(1).strip().split('\n'):
            if '|' in line and '被攻击' not in line and '---' not in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) >= 2:
                    rate_str = cells[2] if len(cells) > 2 else '0%'
                    rate_num = 0
                    rm = re.search(r'(\d+)', rate_str)
                    if rm:
                        rate_num = int(rm.group(1))
                    rows.append({
                        'type': cells[0],
                        'strategy': cells[1],
                        'rate_str': rate_str,
                        'rate_num': rate_num,
                    })
        return rows

    def parse_speeches(self) -> List[Dict]:
        """解析精选发言"""
        material = self.get_material()
        speeches = []
        pattern = r'#### 发言 (\d+)\n\n(.*?)(?=#### 发言 \d+|\n### |\Z)'
        for m in re.finditer(pattern, material, re.DOTALL):
            block = m.group(2)
            speech = {'num': int(m.group(1))}
            for field in ['场景', '对手', '内容', '效果', '杀伤力']:
                fm = re.search(rf'- \*\*{field}\*\*:\s*(.+?)(?=\n- \*\*|\Z)', block, re.DOTALL)
                if fm:
                    speech[field] = fm.group(1).strip()
            speeches.append(speech)
        return speeches

    def parse_quotes(self) -> List[Dict]:
        """解析金句库"""
        material = self.get_material()
        quotes = []
        pattern = r'### 金句库.*?\n\n>.*?\n\n((?:\d+\..*\n?)+)'
        m = re.search(pattern, material, re.DOTALL)
        if not m:
            return quotes
        for line in m.group(1).strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            qm = re.match(r'\d+\.\s*"(.+?)"\s*—\s*杀伤力:\s*(\S+)', line)
            if qm:
                quotes.append({'text': qm.group(1), 'rating': qm.group(2)})
            elif re.match(r'\d+\.', line):
                text = re.sub(r'^\d+\.\s*', '', line)
                quotes.append({'text': text, 'rating': '中'})
        return quotes

    def parse_cases(self) -> List[Dict]:
        """解析核心案例"""
        material = self.get_material()
        cases = []
        pattern = r'#### 案例 (\d+)\n\n(.*?)(?=#### 案例 \d+|\n### |\Z)'
        for m in re.finditer(pattern, material, re.DOTALL):
            block = m.group(2)
            case = {'num': int(m.group(1))}
            for field in ['标题', '来源', '内容', '用于', '被引用次数']:
                fm = re.search(rf'- \*\*{field}\*\*:\s*(.+?)(?=\n- \*\*|\Z)', block, re.DOTALL)
                if fm:
                    case[field] = fm.group(1).strip()
            cases.append(case)
        return cases


class ContentScorer:
    """内容质量评分器：决定什么保留、什么淘汰"""

    @staticmethod
    def score_speech(speech: Dict) -> float:
        """评分一条发言的质量"""
        content = speech.get('内容', '')
        if not content:
            return 0.0

        score = 0.0

        # 长度分（适中最好，太短没内容，太长可能是模板化）
        length = len(content)
        if 100 <= length <= 600:
            score += 30
        elif length > 600:
            score += 20
        elif length >= 50:
            score += 10

        # 证据密度
        evidence_patterns = [
            r'\d+%', r'\d+万', r'\d+亿', r'第.{1,3}章', r'情节',
            r'案例', r'事实上', r'现实中', r'数据', r'原文', r'书中',
            r'「.*?」', r'".*?"', r'比如', r'例如',
        ]
        for p in evidence_patterns:
            if re.search(p, content):
                score += 5

        # 逻辑密度
        logic_words = ['但是', '然而', '问题是', '矛盾', '如果', '因为',
                       '所以', '本质上', '实际上', '换句话说', '关键在于']
        for w in logic_words:
            if w in content:
                score += 3

        # 修辞手法
        rhetoric = ['就像', '好比', '说白了', '坦白说', '不是.*而是',
                     '一方面.*另一方面', '与其.*不如']
        for r in rhetoric:
            if re.search(r, content):
                score += 5

        # 杀伤力加成
        rating = speech.get('杀伤力', '中')
        if rating == '高':
            score += 15
        elif rating == '中':
            score += 8

        # 重复内容惩罚（检查是否有重复片段）
        if content.count('我创儒家') > 1 or content.count('我批判儒释道') > 1:
            score -= 20

        return max(0, score)

    @staticmethod
    def score_quote(quote: Dict) -> float:
        """评分一条金句的质量"""
        text = quote.get('text', '')
        if not text:
            return 0.0

        score = 0.0
        length = len(text)

        # 长度：15-100字最佳
        if 15 <= length <= 100:
            score += 20
        elif length <= 150:
            score += 10
        else:
            score -= 5  # 太长不像金句

        # 杀伤力
        rating = quote.get('rating', '中')
        if rating == '高':
            score += 15
        elif rating == '中':
            score += 8

        # 修辞加分
        if re.search(r'不是.*而是|就像|好比|本质上', text):
            score += 10

        # 反问加分
        if '？' in text or '?' in text:
            score += 5

        # 完整句子加分
        if text.endswith(('。', '！', '？', '"', '"')):
            score += 5

        # 重复内容惩罚
        if len(set(text)) < len(text) * 0.3:
            score -= 10

        return max(0, score)

    @staticmethod
    def score_case(case: Dict) -> float:
        """评分一个案例的质量"""
        content = case.get('内容', '')
        if not content:
            return 0.0

        score = 0.0
        length = len(content)

        # 长度
        if 50 <= length <= 400:
            score += 20
        elif length > 400:
            score += 15
        elif length >= 20:
            score += 5

        # 数据密度
        if re.search(r'\d+%', content):
            score += 5
        if re.search(r'\d+万|\d+亿|\d+美元', content):
            score += 5

        # 来源可信度
        source = case.get('来源', '')
        if source and source != '待训练':
            score += 10

        # "待训练"惩罚
        if '待训练' in content or '待训练' in case.get('标题', ''):
            score -= 30

        return max(0, score)


class EvolutionEngine:
    """进化式升级引擎"""

    def __init__(self, library_dir: str):
        self.library_dir = library_dir
        self.scorer = ContentScorer()

    def find_expert_md(self, expert_name: str) -> Optional[str]:
        """查找专家 .md 文件"""
        experts_dir = os.path.join(self.library_dir, 'experts')
        if not os.path.exists(experts_dir):
            return None
        for category in os.listdir(experts_dir):
            cat_dir = os.path.join(experts_dir, category)
            if not os.path.isdir(cat_dir):
                continue
            for fname in os.listdir(cat_dir):
                if not fname.endswith('.md'):
                    continue
                path = os.path.join(cat_dir, fname)
                with open(path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                if expert_name in first_line:
                    return path
        return None

    def evolve(self, expert_name: str, strategy_data: Dict,
               topic: str = '', score: float = 0.0,
               attack_eff: float = 0.0, defense_rate: float = 0.0) -> Optional[EvolutionResult]:
        """
        主进化函数：对一位专家执行一次进化。

        Args:
            expert_name: 专家姓名
            strategy_data: 本轮提取的策略数据
            topic: 本轮讨论话题
            score: 本轮总分
            attack_eff: 攻击效率
            defense_rate: 防御率

        Returns:
            EvolutionResult 或 None
        """
        md_path = self.find_expert_md(expert_name)
        if not md_path:
            return None

        with open(md_path, 'r', encoding='utf-8') as f:
            original = f.read()

        parser = ExpertParser(original)
        meta = parser.get_meta()
        old_version = int(re.search(r'V(\d+)', meta.get('版本', 'V1')).group(1)) if meta.get('版本') else 1
        old_training_count = int(meta.get('训练次数', '0') or '0')

        result = EvolutionResult(
            expert_name=expert_name,
            file_path=md_path,
            old_version=old_version,
            new_version=old_version + 1,
            word_count_before=len(original),
        )

        # === 层1：灵魂层 — 不碰 ===

        # === 层2：策略层 — 融合升级 ===
        content = original
        content, merges = self._evolve_strategy_layer(content, strategy_data, topic)
        result.strategy_merges = merges

        # === 层3：素材层 — 精选替换 ===
        content, replacements = self._evolve_material_layer(content, strategy_data, topic)
        result.material_replacements = replacements

        # === 判别：是否有实际变化 ===
        has_changes = bool(merges or replacements)

        # === 更新元信息（仅在有实际变化时递增版本）===
        new_training_count = old_training_count + 1
        if has_changes:
            new_version = old_version + 1
            result.new_version = new_version
            content = re.sub(r'\*\*版本\*\*:.*', f'**版本**: V{new_version}', content)
        else:
            result.new_version = old_version
        content = re.sub(r'\*\*训练次数\*\*:.*', f'**训练次数**: {new_training_count}', content)
        content = re.sub(r'\*\*最后训练\*\*:.*', f'**最后训练**: {topic or "进化训练"}', content)
        if score:
            content = re.sub(r'\*\*当前评分\*\*:.*', f'**当前评分**: {score:.1f}', content)

        # === 更新训练历史（保留最近 N 条）===
        content = self._update_training_history(
            content, new_training_count, topic, attack_eff, defense_rate,
            strategy_data
        )

        # === 写回 ===
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)

        result.word_count_after = len(content)
        result.density_delta = (
            (result.word_count_after - result.word_count_before) / max(result.word_count_before, 1) * 100
        )

        return result

    def _evolve_strategy_layer(self, content: str, strategy: Dict,
                                topic: str) -> Tuple[str, List[str]]:
        """策略层进化：融合升级"""
        merges = []

        # 攻击模式升级
        new_attack = strategy.get('attack_strategy', {})
        if new_attack and new_attack.get('best_angle'):
            content, merged = self._merge_attack_patterns(content, new_attack)
            if merged:
                merges.append(f"攻击模式: {new_attack['best_angle'][:30]}")

        # 防御模式升级
        new_defense = strategy.get('defense_weakness', {})
        if new_defense and new_defense.get('broken_by'):
            content, merged = self._merge_defense_patterns(content, new_defense)
            if merged:
                merges.append(f"防御模式: {new_defense['broken_by'][:30]}")

        # 分析框架升级（仅当有明显升级时）
        framework_upgrade = strategy.get('framework_upgrade', '')
        if framework_upgrade and len(framework_upgrade) > 50:
            content, merged = self._merge_framework(content, framework_upgrade)
            if merged:
                merges.append("分析框架升级")

        return content, merges

    def _merge_attack_patterns(self, content: str, new_attack: Dict) -> Tuple[str, bool]:
        """融合攻击模式：新 + 旧 → 保留最强的 N 个"""
        pattern = r'(\| 优先级 \| 攻击角度.*?\n\|.*?\|.*?\|.*?\|.*?\|\n(?:\|.*?\|.*?\|.*?\|.*?\|\n)*)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content, False

        table_text = m.group(1)
        rows = []
        for line in table_text.strip().split('\n'):
            if '|' in line and '优先级' not in line and '---' not in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) >= 4:
                    rows.append(cells)

        # 新攻击角度
        new_angle = new_attack.get('best_angle', '')
        new_scenario = new_attack.get('applicable_when', '对手立场偏激时')
        new_rating = new_attack.get('kill_rating', '中')

        # 检查是否已有相同角度（避免重复）
        for row in rows:
            if row[1] == new_angle:
                return content, False

        # 添加新角度
        rows.append(['', new_angle, new_scenario, new_rating])

        # 按杀伤力排序，保留前 MAX_ATTACK_MODES 个
        rating_order = {'高': 3, '中': 2, '低': 1}
        rows.sort(key=lambda r: rating_order.get(r[3] if len(r) > 3 else '中', 0), reverse=True)
        rows = rows[:MAX_ATTACK_MODES]

        # 重建表格
        new_table = "| 优先级 | 攻击角度 | 适用场景 | 杀伤力评级 |\n"
        new_table += "|--------|---------|---------|-----------|\n"
        for i, row in enumerate(rows, 1):
            row[0] = str(i)
            new_table += f"| {' | '.join(row)} |\n"

        content = content[:m.start()] + new_table + content[m.end():]
        return content, True

    def _merge_defense_patterns(self, content: str, new_defense: Dict) -> Tuple[str, bool]:
        """融合防御模式：修复弱点，提升成功率"""
        pattern = r'(\| 被攻击类型 \| 化解策略.*?\n\|.*?\|.*?\|.*?\|\n(?:\|.*?\|.*?\|.*?\|\n)*)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content, False

        table_text = m.group(1)
        rows = []
        for line in table_text.strip().split('\n'):
            if '|' in line and '被攻击' not in line and '---' not in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) >= 3:
                    rows.append(cells)

        broken_by = new_defense.get('broken_by', '')
        fix = new_defense.get('fix_strategy', '')
        changed = False

        # 尝试匹配并修复已有弱点
        for i, row in enumerate(rows):
            if broken_by and broken_by in row[0]:
                old_rate = re.search(r'(\d+)', row[2])
                old_val = int(old_rate.group(1)) if old_rate else 0
                new_val = min(100, old_val + 15)
                rows[i][1] = fix if fix else row[1]
                rows[i][2] = f'{new_val}%'
                changed = True
                break

        # 如果没匹配，添加新防御
        if not changed and broken_by:
            rows.append([broken_by, fix or '综合回应', '15%'])
            if len(rows) > MAX_DEFENSE_MODES:
                # 移除成功率最高的（已经够强了），保留弱点
                rate_vals = []
                for r in rows:
                    rm = re.search(r'(\d+)', r[2])
                    rate_vals.append(int(rm.group(1)) if rm else 0)
                # 移除成功率最高且不是"待训练"的
                max_idx = rate_vals.index(max(rate_vals))
                if rate_vals[max_idx] > 50:
                    rows.pop(max_idx)
                else:
                    rows = rows[:MAX_DEFENSE_MODES]
            changed = True

        if not changed:
            return content, False

        new_table = "| 被攻击类型 | 化解策略 | 成功率 |\n"
        new_table += "|-----------|---------|--------|\n"
        for row in rows:
            new_table += f"| {' | '.join(row)} |\n"

        content = content[:m.start()] + new_table + content[m.end():]
        return content, True

    def _merge_framework(self, content: str, upgrade: str) -> Tuple[str, bool]:
        """融合分析框架升级"""
        pattern = r'(### 分析框架\n\n>.*?\n\n```\n)(.*?)(```)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content, False

        old_framework = m.group(2).strip()
        # 仅当新框架明显更复杂时才升级
        if len(upgrade) <= len(old_framework):
            return content, False

        new_content = content[:m.start(2)] + upgrade + '\n' + content[m.start(3):]
        return new_content, True

    def _evolve_material_layer(self, content: str, strategy: Dict,
                                topic: str) -> Tuple[str, List[str]]:
        """素材层进化：质量判别驱动

        逻辑：
        - 新内容带来新角度且质量达标 → 增加（不淘汰）
        - 新内容与已有重复 → 替换最弱的
        - 已有内容过多且质量参差 → 淘汰最弱的
        """
        changes = []

        # 精选发言进化
        new_speech = strategy.get('style_fingerprint', {}).get('most_authentic_line', '')
        if new_speech and len(new_speech) > 50:
            content, changed = self._evolve_speeches(content, new_speech, topic, strategy)
            if changed:
                changes.append(changed)

        # 金句进化
        new_quote = strategy.get('style_fingerprint', {}).get('most_authentic_line', '')
        if new_quote and len(new_quote) > 15:
            content, changed = self._evolve_quotes(content, new_quote)
            if changed:
                changes.append(changed)

        # 去重处理
        content = self._deduplicate_speeches(content)
        content = self._deduplicate_quotes(content)

        return content, changes

    def _evolve_speeches(self, content: str, new_speech: str,
                         topic: str, strategy: Dict) -> Tuple[str, str]:
        """质量判别驱动的发言进化

        判别逻辑：
        1. 新发言与已有重复 → 不操作
        2. 新发言质量 > 已有最弱 且带来新角度 → 增加（不淘汰）
        3. 新发言质量 > 已有最弱 且角度重复 → 替换最弱
        4. 新发言质量 <= 已有最弱 → 不操作
        """
        pattern = r'#### 发言 (\d+)\n\n(.*?)(?=#### 发言 \d+|\n### |\Z)'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if not matches:
            return content, ''

        # 评分每条发言
        scores = []
        contents = []
        for m in matches:
            block = m.group(0)
            cm = re.search(r'- \*\*内容\*\*:\s*(.+?)(?=\n- \*\*|\Z)', block, re.DOTALL)
            content_text = cm.group(1).strip() if cm else ''
            km = re.search(r'- \*\*杀伤力\*\*:\s*(\S+)', block)
            rating = km.group(1) if km else '中'
            scores.append(self.scorer.score_speech({'内容': content_text, '杀伤力': rating}))
            contents.append(content_text)

        # 检查是否重复
        for existing in contents:
            if new_speech[:60] in existing or existing[:60] in new_speech:
                return content, ''

        # 新发言评分
        new_score = self.scorer.score_speech({'内容': new_speech, '杀伤力': '中'})
        weakest_idx = scores.index(min(scores))
        weakest_score = scores[weakest_idx]

        if new_score <= weakest_score:
            return content, ''

        # 判断是否带来新角度（长度差异大 = 可能是新角度）
        is_new_angle = True
        for existing in contents:
            if existing and len(set(new_speech[:100]) & set(existing[:100])) > len(new_speech[:100]) * 0.6:
                is_new_angle = False
                break

        # 有效发言数（排除"待训练"）
        real_count = sum(1 for c in contents if c and '待训练' not in c and len(c) > 30)

        if is_new_angle and real_count < MAX_SPEECHES:
            # 增加新发言
            new_num = len(matches) + 1
            new_block = f"""#### 发言 {new_num}

- **场景**: {topic or '进化训练'}
- **对手**: 训练讨论
- **内容**: {new_speech[:500]}
- **效果**: 新角度补充
- **杀伤力**: 中"""
            # 插入到最后一个发言之后
            last_match = matches[-1]
            content = content[:last_match.end()] + '\n' + new_block + content[last_match.end():]
            return content, f'新增发言（新角度，共{new_num}条）'
        else:
            # 替换最弱的（角度重复或已达上限）
            old_block = matches[weakest_idx].group(0)
            num_match = re.search(r'发言 (\d+)', old_block)
            num = num_match.group(1) if num_match else '1'
            new_block = f"""#### 发言 {num}

- **场景**: {topic or '进化训练'}
- **对手**: 训练讨论
- **内容**: {new_speech[:500]}
- **效果**: 质量升级替换
- **杀伤力**: 中"""
            content = content[:matches[weakest_idx].start()] + new_block + content[matches[weakest_idx].end():]
            return content, f'替换最弱发言（质量升级）'

    def _evolve_quotes(self, content: str, new_quote: str) -> Tuple[str, str]:
        """质量判别驱动的金句进化"""
        pattern = r'(### 金句库.*?\n\n>.*?\n\n)((?:\d+\..*\n?)+)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content, ''

        quotes_text = m.group(2)
        quotes = []
        for line in quotes_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            qm = re.match(r'\d+\.\s*"?(.+?)"?\s*—\s*杀伤力:\s*(\S+)', line)
            if qm:
                quotes.append({'text': qm.group(1), 'rating': qm.group(2), 'raw': line})
            elif re.match(r'\d+\.', line):
                quotes.append({'text': line, 'rating': '中', 'raw': line})

        if not quotes:
            return content, ''

        # 检查重复
        for q in quotes:
            if new_quote[:30] in q.get('text', ''):
                return content, ''

        scores = [self.scorer.score_quote(q) for q in quotes]
        new_q = {'text': new_quote, 'rating': '中'}
        new_score = self.scorer.score_quote(new_q)

        weakest_idx = scores.index(min(scores))
        if new_score <= scores[weakest_idx]:
            return content, ''

        real_count = sum(1 for q in quotes if q.get('text') and '待训练' not in q.get('text', ''))

        if real_count < MAX_QUOTES:
            # 增加
            quotes.append({'text': new_quote, 'rating': '中'})
        else:
            # 替换最弱
            quotes[weakest_idx] = {'text': new_quote, 'rating': '中'}

        # 重建
        new_quotes_block = ''
        for i, q in enumerate(quotes[:MAX_QUOTES], 1):
            text = q.get('text', q.get('raw', ''))
            rating = q.get('rating', '中')
            text = re.sub(r'^\d+\.\s*', '', text)
            text = text.strip('"').strip('"').strip('"')
            new_quotes_block += f'{i}. "{text}" — 杀伤力: {rating}\n'

        content = content[:m.start(2)] + new_quotes_block + content[m.end(2):]
        action = '新增金句' if real_count < MAX_QUOTES else '替换最弱金句'
        return content, action

    def _replace_weakest_speech(self, content: str, new_speech: str,
                                 topic: str, strategy: Dict) -> Tuple[str, bool]:
        """替换最弱的发言"""
        pattern = r'#### 发言 \d+\n\n.*?(?=#### 发言 \d+|\n### |\Z)'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if not matches:
            return content, False

        # 评分每条发言
        scores = []
        for m in matches:
            block = m.group(0)
            # 提取内容
            cm = re.search(r'- \*\*内容\*\*:\s*(.+?)(?=\n- \*\*|\Z)', block, re.DOTALL)
            content_text = cm.group(1).strip() if cm else ''
            km = re.search(r'- \*\*杀伤力\*\*:\s*(\S+)', block)
            rating = km.group(1) if km else '中'
            speech = {'内容': content_text, '杀伤力': rating}
            scores.append(self.scorer.score_speech(speech))

        # 新发言评分
        new_speech_data = {'内容': new_speech, '杀伤力': '中'}
        new_score = self.scorer.score_speech(new_speech_data)

        # 找到最弱的
        weakest_idx = scores.index(min(scores))

        # 仅当新发言更强时才替换
        if new_score <= scores[weakest_idx]:
            return content, False

        # 构建新发言块
        old_block = matches[weakest_idx].group(0)
        num_match = re.search(r'发言 (\d+)', old_block)
        num = num_match.group(1) if num_match else '1'

        new_block = f"""#### 发言 {num}

- **场景**: {topic or '进化训练'}
- **对手**: 训练讨论
- **内容**: {new_speech[:500]}
- **效果**: 策略进化升级
- **杀伤力**: 中"""

        content = content[:matches[weakest_idx].start()] + new_block + content[matches[weakest_idx].end():]
        return content, True

    def _replace_weakest_quote(self, content: str, new_quote: str) -> Tuple[str, bool]:
        """替换最弱的金句"""
        pattern = r'(### 金句库.*?\n\n>.*?\n\n)((?:\d+\..*\n?)+)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content, False

        quotes_text = m.group(2)
        quotes = []
        for line in quotes_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            qm = re.match(r'\d+\.\s*"?(.+?)"?\s*—\s*杀伤力:\s*(\S+)', line)
            if qm:
                quotes.append({'text': qm.group(1), 'rating': qm.group(2), 'raw': line})
            elif re.match(r'\d+\.', line):
                quotes.append({'text': line, 'rating': '中', 'raw': line})

        if not quotes:
            return content, False

        # 检查是否已存在
        for q in quotes:
            if new_quote[:30] in q.get('text', ''):
                return content, False

        # 评分
        scores = [self.scorer.score_quote(q) for q in quotes]
        new_q = {'text': new_quote, 'rating': '中'}
        new_score = self.scorer.score_quote(new_q)

        weakest_idx = scores.index(min(scores))
        if new_score <= scores[weakest_idx]:
            return content, False

        # 替换
        quotes[weakest_idx] = {'text': new_quote, 'rating': '中'}

        # 重建
        new_quotes_block = ''
        for i, q in enumerate(quotes[:MAX_QUOTES], 1):
            text = q.get('text', q.get('raw', ''))
            rating = q.get('rating', '中')
            # 清理旧格式
            text = re.sub(r'^\d+\.\s*', '', text)
            text = text.strip('"').strip('"').strip('"')
            new_quotes_block += f'{i}. "{text}" — 杀伤力: {rating}\n'

        content = content[:m.start(2)] + new_quotes_block + content[m.end(2):]
        return content, True

    def _deduplicate_speeches(self, content: str) -> str:
        """去重精选发言：如果内容相同，保留质量更高的那条"""
        pattern = r'#### 发言 (\d+)\n\n(.*?)(?=#### 发言 \d+|\n### |\Z)'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if len(matches) <= 1:
            return content

        seen_contents: Dict[str, int] = {}  # key -> index of first occurrence
        to_remove = []
        for idx, m in enumerate(matches):
            block = m.group(2)
            cm = re.search(r'- \*\*内容\*\*:\s*(.+?)(?=\n- \*\*|\Z)', block, re.DOTALL)
            if cm:
                content_key = cm.group(1).strip()[:100]
                if content_key in seen_contents:
                    # 保留内容更长的那条（质量更高）
                    prev_idx = seen_contents[content_key]
                    prev_block = matches[prev_idx].group(2)
                    prev_cm = re.search(r'- \*\*内容\*\*:\s*(.+?)(?=\n- \*\*|\Z)', prev_block, re.DOTALL)
                    prev_len = len(prev_cm.group(1).strip()) if prev_cm else 0
                    curr_len = len(cm.group(1).strip())
                    if curr_len > prev_len:
                        to_remove.append(matches[prev_idx])
                        seen_contents[content_key] = idx
                    else:
                        to_remove.append(m)
                else:
                    seen_contents[content_key] = idx

        # 从后往前删除（保持索引正确）
        for m in reversed(to_remove):
            content = content[:m.start()] + content[m.end():]

        # 重新编号
        counter = [0]
        def renumber(match):
            counter[0] += 1
            return f'#### 发言 {counter[0]}'
        content = re.sub(r'#### 发言 \d+', renumber, content)

        return content

    def _deduplicate_quotes(self, content: str) -> str:
        """去重金句库：移除重复的金句"""
        pattern = r'(### 金句库.*?\n\n>.*?\n\n)((?:\d+\..*\n?)+)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content

        quotes_text = m.group(2)
        seen = set()
        unique_lines = []
        for line in quotes_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            # 提取核心文本
            key = re.sub(r'^\d+\.\s*', '', line)
            key = key[:60]
            if key not in seen:
                seen.add(key)
                unique_lines.append(line)

        # 重新编号
        renumbered = []
        for i, line in enumerate(unique_lines[:MAX_QUOTES], 1):
            text = re.sub(r'^\d+\.\s*', '', line)
            renumbered.append(f'{i}. {text}')

        new_quotes = '\n'.join(renumbered) + '\n'
        content = content[:m.start(2)] + new_quotes + content[m.end(2):]
        return content

    def _update_training_history(self, content: str, round_num: int,
                                  topic: str, attack_eff: float,
                                  defense_rate: float,
                                  strategy: Dict) -> str:
        """更新训练历史（保留最近 N 条）"""
        pattern = r'(## 训练历史摘要\n\n>.*?\n\n\| 轮次.*?\n\|.*?\n)((?:\|.*?\n)*)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content

        existing_rows = m.group(2)
        rows = []
        for line in existing_rows.strip().split('\n'):
            line = line.strip()
            if line and '— | —' not in line:
                rows.append(line)

        # 新行
        date = datetime.now().strftime('%Y-%m-%d')
        upgrade = strategy.get('attack_strategy', {}).get('best_angle', '进化升级')[:20]
        new_row = f"| {round_num} | {date} | {topic[:20]} | {attack_eff:.0f}% | {defense_rate:.0f}% | {upgrade} |"
        rows.insert(0, new_row)

        # 保留最近 N 条
        rows = rows[:MAX_TRAINING_HISTORY]

        new_history = '\n'.join(rows) + '\n'
        content = content[:m.start(2)] + new_history + content[m.end(2):]
        return content


def evolve_expert(library_dir: str, expert_name: str, strategy_data: Dict,
                  topic: str = '', score: float = 0.0,
                  attack_eff: float = 0.0, defense_rate: float = 0.0) -> Optional[EvolutionResult]:
    """便捷入口"""
    engine = EvolutionEngine(library_dir)
    return engine.evolve(expert_name, strategy_data, topic, score, attack_eff, defense_rate)
