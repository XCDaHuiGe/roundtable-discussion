# -*- coding: utf-8 -*-
"""
融合增强式升级引擎 V5.0

核心升级：
- 从"替换"升级为"融合增强"：旧能力 + 新能力 → 更强的复合能力
- 引入"能力图谱"概念：专家的能力是可叠加的，不是可替换的
- 保留历史能力轨迹，形成"能力进化链"
- 支持 MERGE / ENHANCE / BRANCH / FUSE 四种操作

与替换式的本质区别：
- 替换式：找到最弱项 → 删除 → 插入新项（能力总量不变）
- 融合式：分析旧能力 → 识别互补点 → 生成融合版本（能力总量增加）

用法：
    from engine.training.fusion_engine import FusionEngine, CapabilityGraph
    engine = FusionEngine('expert-library')
    result = engine.upgrade_expert('孔子', strategies, score=82.0)
"""

import os
import re
import json
import copy
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ─── 容量常量 ──────────────────────────────────────────────

MAX_SPEECHES = 8
MAX_CASES = 6
MAX_QUOTES = 10
MAX_ATTACK_MODES = 5
MAX_DEFENSE_MODES = 5
MAX_TRAINING_HISTORY = 20


# ─── 数据模型 ──────────────────────────────────────────────

@dataclass
class FusionResult:
    """一次融合操作的结果"""
    expert_name: str
    file_path: str
    old_version: int
    new_version: int
    fusion_operations: List[str] = field(default_factory=list)
    capability_delta: Dict = field(default_factory=dict)
    word_count_before: int = 0
    word_count_after: int = 0


class CapabilityGraph:
    """
    能力图谱：追踪专家能力的进化历史

    每个能力是一个节点，训练是节点间的边（融合操作）
    """

    def __init__(self, expert_name: str):
        self.expert_name = expert_name
        self.nodes: List[Dict] = []
        self.edges: List[Dict] = []

    def add_node(self, capability_type: str, content: str,
                 quality_score: float, source: str) -> str:
        """添加能力节点，返回节点ID"""
        node_id = f"{capability_type}_{len(self.nodes)}"
        self.nodes.append({
            "id": node_id,
            "type": capability_type,
            "content": content[:200],
            "quality_score": quality_score,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "active": True,
        })
        return node_id

    def add_edge(self, from_node: str, to_node: str,
                 operation: str, reason: str):
        """添加进化边（MERGE/ENHANCE/BRANCH）"""
        self.edges.append({
            "from": from_node,
            "to": to_node,
            "operation": operation,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def get_evolution_path(self, capability_type: str) -> List[Dict]:
        """获取某类能力的进化路径"""
        nodes = [n for n in self.nodes if n["type"] == capability_type]
        if not nodes:
            return []

        # 按时间排序
        nodes.sort(key=lambda n: n["created_at"])

        # 构建路径
        path = []
        for i, node in enumerate(nodes):
            entry = {
                "version": i + 1,
                "content": node["content"],
                "quality_score": node["quality_score"],
                "source": node["source"],
            }
            # 查找导致这个节点的边
            incoming = [e for e in self.edges if e["to"] == node["id"]]
            if incoming:
                entry["evolved_from"] = incoming[0]["from"]
                entry["operation"] = incoming[0]["operation"]
            path.append(entry)
        return path

    def find_weak_capabilities(self, threshold: float = 5.0) -> List[Dict]:
        """找出质量低于阈值的能力"""
        return [
            n for n in self.nodes
            if n["active"] and n["quality_score"] < threshold
        ]

    def to_dict(self) -> Dict:
        return {
            "expert_name": self.expert_name,
            "nodes": self.nodes,
            "edges": self.edges,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CapabilityGraph":
        """从字典恢复能力图谱"""
        graph = cls(data.get("expert_name", "未知"))
        graph.nodes = data.get("nodes", [])
        graph.edges = data.get("edges", [])
        return graph


# ─── 专家文件解析器 ────────────────────────────────────────

class ExpertFusionParser:
    """三层解析器：解析专家 .md 文件的结构"""

    def __init__(self, content: str):
        self.content = content
        self.sections = self._split_sections()
        self.capability_graph = self._load_capability_graph()

    def _split_sections(self) -> Dict[str, str]:
        """按二级标题拆分"""
        sections = {}
        current_key = ""
        current_lines = []

        for line in self.content.split("\n"):
            if line.startswith("## "):
                if current_key:
                    sections[current_key] = "\n".join(current_lines)
                current_key = line.strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_key:
            sections[current_key] = "\n".join(current_lines)

        return sections

    def _load_capability_graph(self) -> CapabilityGraph:
        """从内容中加载能力图谱"""
        pattern = r"## 能力图谱\n\n```json\n(.*?)```"
        m = re.search(pattern, self.content, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                return CapabilityGraph.from_dict(data)
            except json.JSONDecodeError:
                pass

        name = self.get_meta().get("姓名", "未知")
        return CapabilityGraph(name)

    def get_meta(self) -> Dict:
        """提取元信息"""
        meta = {}
        for line in self.content.split("\n"):
            m = re.match(r"- \*\*(.+?)\*\*:\s*(.+)", line)
            if m:
                meta[m.group(1).strip()] = m.group(2).strip()
        return meta

    def get_soul(self) -> str:
        for key in self.sections:
            if "第一层" in key or "灵魂层" in key:
                return self.sections[key]
        return ""

    def get_strategy(self) -> str:
        for key in self.sections:
            if "第二层" in key or "策略层" in key:
                return self.sections[key]
        return ""

    def get_material(self) -> str:
        for key in self.sections:
            if "第三层" in key or "素材层" in key:
                return self.sections[key]
        return ""

    def parse_attack_table(self) -> List[Dict]:
        """解析攻击模式表格"""
        strategy = self.get_strategy()
        rows = []
        pattern = r"### 攻击模式.*?(?:\|.*\n)*((?:\|.*\n)+)"
        m = re.search(pattern, strategy, re.DOTALL)
        if m:
            for line in m.group(1).strip().split("\n"):
                if "|" in line and "优先级" not in line and "---" not in line:
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                    if len(cells) >= 3:
                        rows.append({
                            "priority": cells[0],
                            "angle": cells[1],
                            "scenario": cells[2] if len(cells) > 2 else "",
                            "rating": cells[3] if len(cells) > 3 else "中",
                            "technique": cells[4] if len(cells) > 4 else "",
                        })
        return rows

    def parse_defense_table(self) -> List[Dict]:
        """解析防御模式表格"""
        strategy = self.get_strategy()
        rows = []
        pattern = r"### 防御模式.*?(?:\|.*\n)*((?:\|.*\n)+)"
        m = re.search(pattern, strategy, re.DOTALL)
        if m:
            for line in m.group(1).strip().split("\n"):
                if "|" in line and "被攻击" not in line and "---" not in line:
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                    if len(cells) >= 3:
                        rate_str = cells[2] if len(cells) > 2 else "0%"
                        rate_num = 0
                        rm = re.search(r"(\d+)", rate_str)
                        if rm:
                            rate_num = int(rm.group(1))
                        rows.append({
                            "type": cells[0],
                            "strategy": cells[1],
                            "rate_str": rate_str,
                            "rate_num": rate_num,
                        })
        return rows

    def parse_speeches(self) -> List[Dict]:
        """解析精选发言"""
        material = self.get_material()
        speeches = []
        pattern = r"#### 发言 (\d+)\n\n(.*?)\n(?=#### 发言 \d+|\n### |\Z)"
        for m in re.finditer(pattern, material, re.DOTALL):
            block = m.group(2)
            speech = {"num": int(m.group(1))}
            for field in ["场景", "对手", "内容", "效果", "杀伤力"]:
                fm = re.search(rf"- \*\*{field}\*\*:\s*(.+?)(?=\n- \*\*|\Z)", block, re.DOTALL)
                if fm:
                    speech[field] = fm.group(1).strip()
            speeches.append(speech)
        return speeches

    def parse_quotes(self) -> List[Dict]:
        """解析金句库"""
        material = self.get_material()
        quotes = []
        pattern = r"### 金句库.*?(?:\d+\..*\n?)+"
        m = re.search(pattern, material, re.DOTALL)
        if m:
            for line in m.group(0).strip().split("\n"):
                line = line.strip()
                if not line or "金句库" in line or ">" in line:
                    continue
                qm = re.match(r'\d+\.\s*"(.+?)"\s*—\s*杀伤力:\s*(\S+)', line)
                if qm:
                    quotes.append({"text": qm.group(1), "rating": qm.group(2)})
                elif re.match(r"\d+\.", line):
                    text = re.sub(r"^\d+\.\s*", "", line)
                    quotes.append({"text": text, "rating": "中"})
        return quotes


# ─── 融合引擎 ──────────────────────────────────────────────

class FusionEngine:
    """
    融合增强引擎

    核心操作：
    1. MERGE: 旧策略 + 新策略 → 融合版本（保留两者优点）
    2. ENHANCE: 旧策略 + 质量洞察 → 增强版本（针对弱点补强）
    3. BRANCH: 旧策略 + 新角度 → 新增分支（能力扩展）
    4. FUSE: 旧发言 + 新发言 → 融合发言（保留框架，注入新证据）
    """

    def __init__(self, library_dir: str):
        self.library_dir = library_dir

    def find_expert_md(self, expert_name: str) -> Optional[str]:
        """查找专家 .md 文件"""
        experts_dir = os.path.join(self.library_dir, "experts")
        if not os.path.exists(experts_dir):
            return None
        for category in os.listdir(experts_dir):
            cat_dir = os.path.join(experts_dir, category)
            if not os.path.isdir(cat_dir):
                continue
            for fname in os.listdir(cat_dir):
                if not fname.endswith(".md"):
                    continue
                path = os.path.join(cat_dir, fname)
                with open(path, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                if expert_name in first_line:
                    return path
        return None

    def merge_attack_patterns(self, old_pattern: Dict, new_pattern: Dict) -> Dict:
        """
        MERGE操作：合并两个攻击角度
        例如："逻辑漏洞" + "证据矛盾" → "逻辑漏洞+证据矛盾"复合攻击
        """
        old_angle = old_pattern.get("angle", "")
        new_angle = new_pattern.get("angle", "")

        # 如果一方包含另一方，返回较长的
        if old_angle in new_angle:
            merged_angle = new_angle
        elif new_angle in old_angle:
            merged_angle = old_angle
        else:
            # 检查是否有共同关键词
            old_words = set(old_angle.split())
            new_words = set(new_angle.split())
            common = old_words & new_words

            if len(common) >= len(old_words) * 0.5:
                # 高度相似，取较长的
                merged_angle = old_angle if len(old_angle) > len(new_angle) else new_angle
            else:
                # 互补角度，合并为复合攻击
                merged_angle = f"{old_angle}+{new_angle}"

        # 评级取高
        rating_order = {"高": 3, "中": 2, "低": 1}
        old_r = rating_order.get(old_pattern.get("rating", "中"), 1)
        new_r = rating_order.get(new_pattern.get("rating", "中"), 1)
        merged_rating = "高" if max(old_r, new_r) == 3 else "中" if max(old_r, new_r) == 2 else "低"

        # 场景合并
        old_scenario = old_pattern.get("scenario", "")
        new_scenario = new_pattern.get("scenario", "")
        merged_scenario = old_scenario
        if new_scenario and new_scenario not in old_scenario:
            merged_scenario = f"{old_scenario}；{new_scenario}"

        # 技术合并
        old_tech = old_pattern.get("technique", "")
        new_tech = new_pattern.get("technique", "")
        merged_tech = old_tech
        if new_tech and new_tech not in old_tech:
            merged_tech = f"{old_tech}/{new_tech}" if old_tech else new_tech

        return {
            "priority": old_pattern.get("priority", "1"),
            "angle": merged_angle,
            "scenario": merged_scenario,
            "rating": merged_rating,
            "technique": merged_tech,
        }

    def enhance_defense(self, old_defense: Dict, new_insight: Dict) -> Dict:
        """
        ENHANCE操作：增强防御能力
        例如："数据质疑"(40%) + "增加反例储备" → "数据质疑"(55%)
        """
        old_rate = old_defense.get("rate_num", 0)
        old_strategy = old_defense.get("strategy", "")
        new_fix = new_insight.get("fix_strategy", "")

        # 合并策略描述
        merged_strategy = old_strategy
        if new_fix and new_fix not in old_strategy:
            merged_strategy = f"{old_strategy}；{new_fix}"

        # 提升成功率
        priority = new_insight.get("priority", "中")
        boost = {"高": 25, "中": 15, "低": 10}.get(priority, 15)
        new_rate = min(100, old_rate + boost)

        return {
            "type": old_defense.get("type", ""),
            "strategy": merged_strategy,
            "rate_str": f"{new_rate}%",
            "rate_num": new_rate,
        }

    def branch_capability(self, new_capability: Dict) -> Dict:
        """
        BRANCH操作：新增能力分支
        例如：新增"归谬法"攻击角度
        """
        return {
            "priority": str(new_capability.get("priority", "1")),
            "angle": new_capability.get("angle", ""),
            "scenario": new_capability.get("scenario", ""),
            "rating": new_capability.get("rating", "中"),
            "technique": new_capability.get("technique", ""),
        }

    def fuse_speech(self, old_speech: str, new_speech: str, topic: str = "") -> str:
        """
        FUSE操作：融合两段发言
        保留旧框架，注入新证据/观点
        """
        import re

        # 提取旧的核心论点（前80字通常包含核心观点）
        old_core = old_speech[:80] if len(old_speech) > 80 else old_speech

        # 提取新的证据和洞察
        new_evidence = ""
        evidence_match = re.search(r"[^。]*(?:第.{1,3}章|情节|原文|书中|数据|案例|\d+%)[^。]*。", new_speech)
        if evidence_match:
            new_evidence = evidence_match.group(0)

        # 提取新的角度（与旧发言差异最大的部分）
        new_angle = ""
        if len(new_speech) > 100:
            new_words = set(new_speech.split())
            old_words = set(old_speech.split())
            unique_words = new_words - old_words
            if unique_words:
                sentences = re.split(r"[。！？]", new_speech)
                best_sentence = ""
                best_unique_count = 0
                for sent in sentences:
                    unique_count = sum(1 for w in sent.split() if w in unique_words)
                    if unique_count > best_unique_count:
                        best_unique_count = unique_count
                        best_sentence = sent
                new_angle = best_sentence

        # 组合融合版本
        fused = old_core
        if new_evidence and new_evidence not in old_speech:
            fused += f"\n\n进一步来看，{new_evidence}"
        if new_angle and new_angle not in old_speech and new_angle != new_evidence:
            fused += f"\n\n这实际上揭示了{new_angle}。"

        # 如果融合后太长，截断
        if len(fused) > 600:
            fused = fused[:600] + "..."

        return fused

    def upgrade_expert(
        self,
        expert_md_path: str,
        strategies: Dict,
        score: float
    ) -> str:
        """
        主升级函数

        流程：
        1. 读取专家档案
        2. 分析现有能力图谱
        3. 根据新策略决定操作类型（MERGE/ENHANCE/BRANCH）
        4. 执行融合
        5. 更新版本号和训练历史
        6. 写回文件

        Returns: 升级后的内容
        """
        with open(expert_md_path, "r", encoding="utf-8") as f:
            original = f.read()

        parser = ExpertFusionParser(original)
        meta = parser.get_meta()
        old_version = int(re.search(r"V(\d+)", meta.get("版本", "V1")).group(1)) if meta.get("版本") else 1
        old_training_count = int(meta.get("训练次数", "0") or "0")

        result = FusionResult(
            expert_name=meta.get("姓名", "未知"),
            file_path=expert_md_path,
            old_version=old_version,
            new_version=old_version,
            word_count_before=len(original),
        )

        content = original

        # === 层1：灵魂层 — 不碰 ===

        # === 层2：策略层 — 融合增强 ===
        content, operations, cap_delta = self._fuse_strategy_layer(
            content, strategies, parser
        )
        result.fusion_operations = operations
        result.capability_delta = cap_delta

        # === 层3：素材层 — 融合增强 ===
        content, material_ops = self._fuse_material_layer(
            content, strategies, parser
        )
        result.fusion_operations.extend(material_ops)

        # === 判别：是否有实际能力增量 ===
        has_changes = bool(operations or material_ops)

        # === 更新元信息 ===
        new_training_count = old_training_count + 1
        if has_changes:
            new_version = old_version + 1
            result.new_version = new_version
            content = re.sub(r"\*\*版本\*\*:.*", f"**版本**: V{new_version}", content)
        content = re.sub(r"\*\*训练次数\*\*:.*", f"**训练次数**: {new_training_count}", content)
        content = re.sub(r"\*\*最后训练\*\*:.*", f"**最后训练**: 融合训练", content)
        if score:
            content = re.sub(r"\*\*当前评分\*\*:.*", f"**当前评分**: {score:.1f}", content)

        # === 更新能力图谱 ===
        content = self._update_capability_graph(content, parser.capability_graph)

        # === 更新训练历史 ===
        content = self._update_training_history(
            content, new_training_count, score, result.fusion_operations
        )

        # === 写回 ===
        with open(expert_md_path, "w", encoding="utf-8") as f:
            f.write(content)

        result.word_count_after = len(content)
        return content

    def _fuse_strategy_layer(self, content: str, strategy: Dict,
                              parser: ExpertFusionParser) -> Tuple[str, List[str], Dict]:
        """策略层融合增强"""
        operations = []
        cap_delta = {"attack": 0, "defense": 0, "style": 0}

        # 攻击模式融合
        new_attack = strategy.get("attack_strategy", {})
        if new_attack and new_attack.get("best_angle"):
            content, op, delta = self._fuse_attack_patterns(
                content, new_attack, parser
            )
            if op:
                operations.append(f"攻击融合: {op}")
                cap_delta["attack"] += delta

        # 防御模式融合
        new_defense = strategy.get("defense_weakness", {})
        if new_defense and new_defense.get("broken_by"):
            content, op, delta = self._fuse_defense_patterns(
                content, new_defense, parser
            )
            if op:
                operations.append(f"防御融合: {op}")
                cap_delta["defense"] += delta

        # 风格指纹融合
        new_style = strategy.get("style_fingerprint", {})
        if new_style and new_style.get("most_authentic_line"):
            content, op, delta = self._fuse_style_fingerprint(
                content, new_style, parser
            )
            if op:
                operations.append(f"风格融合: {op}")
                cap_delta["style"] += delta

        return content, operations, cap_delta

    def _fuse_attack_patterns(self, content: str, new_attack: Dict,
                               parser: ExpertFusionParser) -> Tuple[str, str, float]:
        """攻击模式融合：MERGE / BRANCH"""
        old_attacks = parser.parse_attack_table()
        new_angle = new_attack.get("best_angle", "")
        new_scenario = new_attack.get("applicable_when", "")
        new_rating = new_attack.get("kill_rating", "中")
        new_technique = new_attack.get("key_technique", "")
        quality_score = new_attack.get("quality_score", 5.0)

        if not new_angle:
            return content, "", 0.0

        # 检查是否已有相同/相似角度
        similar_idx = -1
        for i, old in enumerate(old_attacks):
            if self._text_similarity(old.get("angle", ""), new_angle) > 0.6:
                similar_idx = i
                break

        if similar_idx >= 0:
            # === MERGE: 合并新旧角度 ===
            old = old_attacks[similar_idx]
            merged = self.merge_attack_patterns(
                old,
                {
                    "angle": new_angle,
                    "scenario": new_scenario,
                    "rating": new_rating,
                    "technique": new_technique,
                }
            )
            old_attacks[similar_idx] = merged

            operation = f"MERGE '{old['angle'][:20]}' + '{new_angle[:20]}' → '{merged['angle'][:30]}'"
            delta = 1.5

            # 记录能力图谱
            old_node = parser.capability_graph.add_node(
                "attack", old["angle"], old.get("quality_score", 5.0), "原始"
            )
            new_node = parser.capability_graph.add_node(
                "attack", merged["angle"], quality_score, "MERGE"
            )
            parser.capability_graph.add_edge(
                old_node, new_node, "MERGE",
                f"合并 '{old['angle'][:20]}' 和 '{new_angle[:20]}'"
            )

        else:
            # === BRANCH: 新增角度 ===
            if len(old_attacks) >= MAX_ATTACK_MODES:
                weakest_idx = min(range(len(old_attacks)),
                                  key=lambda i: {"高": 3, "中": 2, "低": 1}.get(old_attacks[i]["rating"], 0))
                old_gem = old_attacks[weakest_idx]["angle"]
                content = self._archive_to_quotes(content, old_gem)
                old_attacks[weakest_idx] = {
                    "priority": str(weakest_idx + 1),
                    "angle": new_angle,
                    "scenario": new_scenario,
                    "rating": new_rating,
                    "technique": new_technique,
                }
                operation = f"BRANCH 替换最弱角度，旧角度归档: '{old_gem[:20]}'"
                delta = 1.0

                # 记录能力图谱
                old_node = parser.capability_graph.add_node(
                    "attack", old_gem, 3.0, "被替换"
                )
                new_node = parser.capability_graph.add_node(
                    "attack", new_angle, quality_score, "BRANCH"
                )
                parser.capability_graph.add_edge(
                    old_node, new_node, "BRANCH",
                    f"替换最弱角度 '{old_gem[:20]}'"
                )
            else:
                old_attacks.append({
                    "priority": str(len(old_attacks) + 1),
                    "angle": new_angle,
                    "scenario": new_scenario,
                    "rating": new_rating,
                    "technique": new_technique,
                })
                operation = f"BRANCH 新增角度: '{new_angle[:30]}'"
                delta = 1.0

                # 记录能力图谱
                new_node = parser.capability_graph.add_node(
                    "attack", new_angle, quality_score, "BRANCH"
                )

        content = self._rebuild_attack_table(content, old_attacks)
        return content, operation, delta

    def _fuse_defense_patterns(self, content: str, new_defense: Dict,
                                parser: ExpertFusionParser) -> Tuple[str, str, float]:
        """防御模式融合：ENHANCE / BRANCH"""
        old_defenses = parser.parse_defense_table()
        broken_by = new_defense.get("broken_by", "")
        fix = new_defense.get("fix_strategy", "")
        priority = new_defense.get("priority", "中")
        success_rate = new_defense.get("success_rate", 20.0)

        if not broken_by:
            return content, "", 0.0

        # 检查是否已有同类防御
        matched_idx = -1
        for i, old in enumerate(old_defenses):
            if broken_by in old["type"] or old["type"] in broken_by:
                matched_idx = i
                break

        if matched_idx >= 0:
            # === ENHANCE: 升级现有防御 ===
            old = old_defenses[matched_idx]
            enhanced = self.enhance_defense(
                old,
                {"fix_strategy": fix, "priority": priority}
            )
            old_defenses[matched_idx] = enhanced

            operation = f"ENHANCE '{old['type'][:20]}': {old['rate_num']}% → {enhanced['rate_num']}%"
            delta = (enhanced["rate_num"] - old["rate_num"]) / 100 * 2

            # 记录能力图谱
            old_node = parser.capability_graph.add_node(
                "defense", old["type"], old["rate_num"] / 10, "原始"
            )
            new_node = parser.capability_graph.add_node(
                "defense", enhanced["type"], enhanced["rate_num"] / 10, "ENHANCE"
            )
            parser.capability_graph.add_edge(
                old_node, new_node, "ENHANCE",
                f"成功率 {old['rate_num']}% → {enhanced['rate_num']}%"
            )

        else:
            # === BRANCH: 新增防御模式 ===
            if len(old_defenses) >= MAX_DEFENSE_MODES:
                weakest_idx = min(range(len(old_defenses)),
                                  key=lambda i: old_defenses[i]["rate_num"])
                old_gem = old_defenses[weakest_idx]["type"]
                content = self._archive_to_quotes(content, old_gem)
                old_defenses[weakest_idx] = {
                    "type": broken_by,
                    "strategy": fix or "综合回应",
                    "rate_str": f"{int(success_rate)}%",
                    "rate_num": int(success_rate),
                }
                operation = f"BRANCH 新增防御，归档旧模式: '{old_gem[:20]}'"

                # 记录能力图谱
                old_node = parser.capability_graph.add_node(
                    "defense", old_gem, 2.0, "被替换"
                )
                new_node = parser.capability_graph.add_node(
                    "defense", broken_by, success_rate / 10, "BRANCH"
                )
                parser.capability_graph.add_edge(
                    old_node, new_node, "BRANCH",
                    f"替换最弱防御 '{old_gem[:20]}'"
                )
            else:
                old_defenses.append({
                    "type": broken_by,
                    "strategy": fix or "综合回应",
                    "rate_str": f"{int(success_rate)}%",
                    "rate_num": int(success_rate),
                })
                operation = f"BRANCH 新增防御: '{broken_by[:30]}'"

                # 记录能力图谱
                new_node = parser.capability_graph.add_node(
                    "defense", broken_by, success_rate / 10, "BRANCH"
                )
            delta = 0.8

        content = self._rebuild_defense_table(content, old_defenses)
        return content, operation, delta

    def _fuse_style_fingerprint(self, content: str, new_style: Dict,
                                 parser: ExpertFusionParser) -> Tuple[str, str, float]:
        """风格指纹融合：增强风格辨识度"""
        authentic_line = new_style.get("most_authentic_line", "")
        signature = new_style.get("signature_pattern", "")
        avoid = new_style.get("avoid_pattern", "")

        if not authentic_line:
            return content, "", 0.0

        # 找到风格指纹区域
        pattern = r"(### 风格指纹.*?)\n\n(?=### |\n## )"
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content, "", 0.0

        old_block = m.group(1)

        # 检查是否已有相似风格标记
        if authentic_line[:50] in old_block:
            return content, "", 0.0

        # 追加新的风格标记
        new_entry = f"\n- **训练认证**: \"{authentic_line[:100]}\" — {new_style.get('why_authentic', '风格鲜明')[:50]}"
        if signature:
            new_entry += f"\n- **标志性模式**: {signature[:80]}"
        if avoid:
            new_entry += f"\n- **避免模式**: {avoid[:80]}"

        new_block = old_block + new_entry
        content = content[:m.start()] + new_block + content[m.end():]

        operation = f"ENHANCE 风格指纹: +'{authentic_line[:30]}...'"
        delta = 0.5

        # 记录能力图谱
        parser.capability_graph.add_node(
            "style", authentic_line, 7.0, "ENHANCE"
        )

        return content, operation, delta

    def _fuse_material_layer(self, content: str, strategy: Dict,
                              parser: ExpertFusionParser) -> Tuple[str, List[str]]:
        """素材层融合增强"""
        operations = []

        # 精选发言融合
        new_speech = strategy.get("style_fingerprint", {}).get("most_authentic_line", "")
        if new_speech and len(new_speech) > 50:
            content, op = self._fuse_speeches(content, new_speech, strategy, parser)
            if op:
                operations.append(op)

        # 金句融合
        new_quote = strategy.get("style_fingerprint", {}).get("most_authentic_line", "")
        if new_quote and len(new_quote) > 15:
            content, op = self._fuse_quotes(content, new_quote, parser)
            if op:
                operations.append(op)

        return content, operations

    def _fuse_speeches(self, content: str, new_speech: str,
                        strategy: Dict, parser: ExpertFusionParser) -> Tuple[str, str]:
        """发言融合：找到最互补的旧发言，生成融合版本"""
        old_speeches = parser.parse_speeches()
        if not old_speeches:
            return content, ""

        # 找到与新发言最互补的旧发言
        best_fusion_idx = -1
        best_fusion_score = -1

        for i, old in enumerate(old_speeches):
            complement = self._calc_complement(old.get("内容", ""), new_speech)
            if complement > best_fusion_score:
                best_fusion_score = complement
                best_fusion_idx = i

        if best_fusion_idx < 0 or best_fusion_score < 0.3:
            # 互补度不够，直接新增
            real_count = sum(1 for s in old_speeches
                           if s.get("内容") and "待训练" not in s.get("内容", ""))
            if real_count < MAX_SPEECHES:
                new_num = len(old_speeches) + 1
                new_block = self._build_speech_block(new_num, new_speech, strategy)
                pattern = r"(#### 发言 \d+\n\n.*?)(?=\n## |\Z)"
                matches = list(re.finditer(pattern, content, re.DOTALL))
                if matches:
                    last = matches[-1]
                    content = content[:last.end()] + "\n" + new_block + content[last.end():]
                return content, f"BRANCH 新增发言（互补度{best_fusion_score:.2f}不足）"
            else:
                weakest_idx = min(range(len(old_speeches)),
                                  key=lambda i: self._score_speech_simple(old_speeches[i]))
                return self._replace_speech(content, weakest_idx, new_speech, strategy, old_speeches)

        # === 融合：互补的旧发言 + 新发言 ===
        old = old_speeches[best_fusion_idx]
        old_content = old.get("内容", "")

        fused_content = self.fuse_speech(old_content, new_speech)

        return self._replace_speech(content, best_fusion_idx, fused_content, strategy, old_speeches,
                                     fused=True)

    def _fuse_quotes(self, content: str, new_quote: str,
                      parser: ExpertFusionParser) -> Tuple[str, str]:
        """金句融合"""
        old_quotes = parser.parse_quotes()
        if not old_quotes:
            return content, ""

        # 检查是否已有相似金句
        for q in old_quotes:
            if new_quote[:30] in q.get("text", ""):
                return content, ""

        # 评分新旧金句
        new_score = self._score_quote_simple(new_quote)
        old_scores = [self._score_quote_simple(q.get("text", "")) for q in old_quotes]
        weakest_idx = old_scores.index(min(old_scores))

        if new_score <= old_scores[weakest_idx]:
            return content, ""

        # 替换最弱的
        old_quotes[weakest_idx] = {"text": new_quote, "rating": "中"}

        # 重建金句库
        content = self._rebuild_quotes(content, old_quotes)
        return content, f"ENHANCE 金句: 替换第{weakest_idx+1}条"

    def _archive_to_quotes(self, content: str, text: str) -> str:
        """将淘汰的策略归档到金句库"""
        if len(text) < 10:
            return content

        pattern = r"(### 金句库.*?)\n\n(?=### |\n## )"
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content

        old_block = m.group(1)

        if text[:30] in old_block:
            return content

        quotes = []
        for line in old_block.split("\n"):
            qm = re.match(r"(\d+)\.\s*", line.strip())
            if qm:
                quotes.append(int(qm.group(1)))

        next_num = max(quotes) + 1 if quotes else 1
        archive_entry = f"\n{next_num}. \"{text[:100]}\" — 杀伤力: 低 [历史归档]"
        new_block = old_block + archive_entry

        content = content[:m.start()] + new_block + content[m.end():]
        return content

    def _text_similarity(self, a: str, b: str) -> float:
        """计算两段文本的相似度"""
        if not a or not b:
            return 0.0
        a_words = set(a.split())
        b_words = set(b.split())
        if not a_words or not b_words:
            return 0.0
        intersection = len(a_words & b_words)
        union = len(a_words | b_words)
        return intersection / union if union > 0 else 0.0

    def _calc_complement(self, old: str, new: str) -> float:
        """计算内容互补度 (0-1)"""
        old_words = set(old[:100].split())
        new_words = set(new[:100].split())
        if not old_words or not new_words:
            return 0.0
        intersection = len(old_words & new_words)
        union = len(old_words | new_words)
        if union == 0:
            return 0.0
        difference = 1 - (intersection / union)
        return min(1.0, difference)

    def _score_speech_simple(self, speech: Dict) -> float:
        """简单评分发言"""
        content = speech.get("内容", "")
        score = len(content) / 10
        if "待训练" in content:
            score -= 50
        return score

    def _score_quote_simple(self, text: str) -> float:
        """简单评分金句"""
        if not text:
            return 0.0
        score = len(text)
        if 15 <= len(text) <= 100:
            score += 20
        return score

    def _build_speech_block(self, num: int, content: str, strategy: Dict) -> str:
        """构建发言块"""
        topic = strategy.get("_topic", "融合训练")
        return f"""#### 发言 {num}

- **场景**: {topic}
- **对手**: 训练讨论
- **内容**: {content[:500]}
- **效果**: 融合增强
- **杀伤力**: 中

"""

    def _replace_speech(self, content: str, idx: int, new_content: str,
                        strategy: Dict, old_speeches: List[Dict],
                        fused: bool = False) -> Tuple[str, str]:
        """替换指定位置的发言"""
        pattern = r"#### 发言 \d+\n\n.*?\n(?=#### 发言 \d+|\n### |\Z)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if idx >= len(matches):
            return content, ""

        old_block = matches[idx].group(0)
        num_match = re.search(r"发言 (\d+)", old_block)
        num = num_match.group(1) if num_match else str(idx + 1)

        label = "融合增强" if fused else "质量升级替换"
        new_block = self._build_speech_block(int(num), new_content, strategy)

        content = content[:matches[idx].start()] + new_block + content[matches[idx].end():]

        action = f"{'FUSE' if fused else 'REPLACE'} 发言{num}: {label}"
        return content, action

    def _rebuild_attack_table(self, content: str, rows: List[Dict]) -> str:
        """重建攻击模式表格"""
        pattern = r"(### 攻击模式.*?)\n\n(?=### |\n## )"
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content

        old_block = m.group(1)
        desc_match = re.search(r"(### 攻击模式\n\n>.*?\n\n)", old_block, re.DOTALL)
        desc = desc_match.group(1) if desc_match else "### 攻击模式\n\n"

        new_table = desc
        new_table += "| 优先级 | 攻击角度 | 适用场景 | 杀伤力评级 | 核心技术 |\n"
        new_table += "|--------|---------|---------|-----------|----------|\n"
        for i, row in enumerate(rows[:MAX_ATTACK_MODES], 1):
            new_table += f"| {i} | {row['angle']} | {row['scenario']} | {row['rating']} | {row.get('technique', '')} |\n"

        content = content[:m.start()] + new_table + content[m.end():]
        return content

    def _rebuild_defense_table(self, content: str, rows: List[Dict]) -> str:
        """重建防御模式表格"""
        pattern = r"(### 防御模式.*?)\n\n(?=### |\n## )"
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content

        old_block = m.group(1)
        desc_match = re.search(r"(### 防御模式\n\n>.*?\n\n)", old_block, re.DOTALL)
        desc = desc_match.group(1) if desc_match else "### 防御模式\n\n"

        new_table = desc
        new_table += "| 被攻击类型 | 化解策略 | 成功率 |\n"
        new_table += "|-----------|---------|--------|\n"
        for row in rows[:MAX_DEFENSE_MODES]:
            new_table += f"| {row['type']} | {row['strategy']} | {row['rate_str']} |\n"

        content = content[:m.start()] + new_table + content[m.end():]
        return content

    def _rebuild_quotes(self, content: str, quotes: List[Dict]) -> str:
        """重建金句库"""
        pattern = r"(### 金句库.*?)\n\n(?=### |\n## )"
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content

        old_block = m.group(1)
        desc_match = re.search(r"(### 金句库\n\n>.*?\n\n)", old_block, re.DOTALL)
        desc = desc_match.group(1) if desc_match else "### 金句库\n\n"

        new_block = desc
        for i, q in enumerate(quotes[:MAX_QUOTES], 1):
            text = q.get("text", "").strip('"').strip('"')
            rating = q.get("rating", "中")
            new_block += f'{i}. "{text}" — 杀伤力: {rating}\n'

        content = content[:m.start()] + new_block + content[m.end():]
        return content

    def _update_capability_graph(self, content: str, graph: CapabilityGraph) -> str:
        """更新能力图谱到专家文件"""
        graph_data = json.dumps(graph.to_dict(), ensure_ascii=False, indent=2)

        pattern = r"## 能力图谱\n\n```json\n.*?```"
        if re.search(pattern, content, re.DOTALL):
            new_block = f"## 能力图谱\n\n```json\n{graph_data}\n```"
            content = re.sub(pattern, new_block, content, flags=re.DOTALL)
        else:
            new_block = f"\n\n---\n\n## 能力图谱\n\n```json\n{graph_data}\n```"
            content = content.rstrip() + new_block

        return content

    def _update_training_history(self, content: str, round_num: int,
                                  score: float, operations: List[str]) -> str:
        """更新训练历史"""
        pattern = r"(## 训练历史摘要\n\n>.*?\n\n\| 轮次.*?\n\|.*\n)((?:\|.*\n)*)"
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return content

        existing_rows = m.group(2)
        rows = []
        for line in existing_rows.strip().split("\n"):
            line = line.strip()
            if line and "— | —" not in line:
                rows.append(line)

        date = datetime.now().strftime("%Y-%m-%d")
        ops_summary = " / ".join(operations)[:30] if operations else "无变化"
        new_row = f"| {round_num} | {date} | 融合训练 | {score:.0f} | {ops_summary} |"
        rows.insert(0, new_row)
        rows = rows[:MAX_TRAINING_HISTORY]

        header = m.group(1)
        if "融合操作" not in header:
            header = header.replace("| 升级内容 |", "| 融合操作 |")
            header = re.sub(r"\|[-\s|]+\|", "|--------|--------|---------|--------|------------|", header)

        new_history = header + "\n".join(rows) + "\n"
        content = content[:m.start()] + new_history + content[m.end():]
        return content


# ─── 便捷入口 ──────────────────────────────────────────────

def fuse_expert(library_dir: str, expert_name: str, strategy_data: Dict,
                score: float = 0.0) -> Optional[FusionResult]:
    """便捷入口"""
    engine = FusionEngine(library_dir)
    md_path = engine.find_expert_md(expert_name)
    if not md_path:
        return None

    content = engine.upgrade_expert(md_path, strategy_data, score)

    # 构建结果
    parser = ExpertFusionParser(content)
    meta = parser.get_meta()
    new_version = int(re.search(r"V(\d+)", meta.get("版本", "V1")).group(1)) if meta.get("版本") else 1

    return FusionResult(
        expert_name=expert_name,
        file_path=md_path,
        old_version=new_version - 1,
        new_version=new_version,
        word_count_after=len(content),
    )


# ─── 测试代码 ──────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile
    import shutil

    print("=" * 60)
    print("测试 fusion_engine.py")
    print("=" * 60)

    # 创建测试用的专家文件
    test_expert_content = """# 孔子

## 元信息

- **分类**: philosophy
- **版本**: V1
- **训练次数**: 0
- **最后训练**: 未训练
- **当前评分**: 未评分
- **姓名**: 孔子

---

## 第一层：灵魂层（永不改变）

### 核心信念

- 人性本善，通过教育和修身可以达到仁的境界

---

## 第二层：策略层（训练升级的核心）

### 攻击模式

> 当我要反驳别人时，优先使用这些角度。

| 优先级 | 攻击角度 | 适用场景 | 杀伤力评级 | 核心技术 |
|--------|---------|---------|-----------|----------|
| 1 | 人性假设漏洞 | 对手持性恶论立场时 | 高 | 类比论证 |
| 2 | 逻辑漏洞 | 对手持尼采立场时 | 高 | 归谬法 |
| 3 | 忽视教育力量 | 对手认为人性不可改变时 | 中 | 历史案例 |
| 4 | 功利主义短视 | 对手只看短期利益时 | 中 | 长远视角 |

### 防御模式

> 当我被攻击时，用这些方式化解。

| 被攻击类型 | 化解策略 | 成功率 |
|-----------|---------|--------|
| 被指理想化 | 用历史案例证明可行性 | 0% (待训练) |
| 被要求举证 | 引用《论语》中的具体教导 | 0% (待训练) |
| 被质疑等级观念 | 区分"礼"与"等级压迫"的本质差异 | 0% (待训练) |
| 逻辑漏洞攻击 | 增加具体证据和逻辑链 | 15% |

### 风格指纹

> 这个人的标志性表达特征。

- **标志性开头**: "吾以为..."
- **口头禅**: "君子"

---

## 第三层：素材层（精选替换）

### 精选发言（5条）

#### 发言 1

- **场景**: 儒家思想是否为专制服务？
- **对手**: 训练讨论
- **内容**: 我创儒家，不是为帝王服务，而是为天下苍生。
- **效果**: 观点鲜明
- **杀伤力**: 高

#### 发言 2

- **场景**: 待训练
- **对手**: 待训练
- **内容**: (待训练升级)
- **效果**: 待训练
- **杀伤力**: 低

### 金句库（6条）

> 最犀利、最像这个人会说的话。

1. "己所不欲，勿施于人" — 杀伤力: 高
2. "君君臣臣父父子子，我说的是各安其位、各尽其责" — 杀伤力: 中
3. "以道事君，不可则止——这不是盲从，是有原则的合作" — 杀伤力: 中
4. "民为贵，社稷次之，君为轻——这是民本思想的先声" — 杀伤力: 中
5. "修身齐家治国平天下——一切从修身开始" — 杀伤力: 中
6. "(待训练补充)" — 杀伤力: 低

---

## 训练历史摘要

> 每次训练后的能力变化记录。

| 轮次 | 日期 | 训练主题 | 当前评分 | 升级内容 |
|------|------|---------|---------|----------|
"""

    # 创建临时目录结构
    test_dir = tempfile.mkdtemp()
    test_experts_dir = os.path.join(test_dir, "experts", "philosophy")
    os.makedirs(test_experts_dir, exist_ok=True)

    test_md_path = os.path.join(test_experts_dir, "孔子.md")
    with open(test_md_path, "w", encoding="utf-8") as f:
        f.write(test_expert_content)

    engine = FusionEngine(test_dir)

    # 测试1: merge_attack_patterns
    print("\n[测试1] merge_attack_patterns")
    old_pat = {"angle": "逻辑漏洞", "scenario": "对手逻辑错误时", "rating": "中", "technique": "归谬法"}
    new_pat = {"angle": "证据矛盾", "scenario": "对手证据冲突时", "rating": "高", "technique": "对比法"}
    merged = engine.merge_attack_patterns(old_pat, new_pat)
    print(f"  旧: {old_pat['angle']}")
    print(f"  新: {new_pat['angle']}")
    print(f"  合并: {merged['angle']}")
    print(f"  评级: {merged['rating']}")
    print(f"  技术: {merged['technique']}")

    # 测试2: enhance_defense
    print("\n[测试2] enhance_defense")
    old_def = {"type": "数据质疑", "strategy": "补充数据", "rate_str": "40%", "rate_num": 40}
    new_ins = {"fix_strategy": "增加反例储备", "priority": "高"}
    enhanced = engine.enhance_defense(old_def, new_ins)
    print(f"  旧成功率: {old_def['rate_num']}%")
    print(f"  新成功率: {enhanced['rate_num']}%")
    print(f"  策略: {enhanced['strategy']}")

    # 测试3: branch_capability
    print("\n[测试3] branch_capability")
    new_cap = {"angle": "归谬法", "scenario": "对手自相矛盾时", "rating": "高", "technique": "反证"}
    branched = engine.branch_capability(new_cap)
    print(f"  新增角度: {branched['angle']}")
    print(f"  场景: {branched['scenario']}")

    # 测试4: fuse_speech
    print("\n[测试4] fuse_speech")
    old_s = "人性本善，这是不争的事实。"
    new_s = "孟子说'人皆有不忍人之心'，这在第三章有详细论述。数据显示90%的人在紧急情况下会优先帮助他人。"
    fused = engine.fuse_speech(old_s, new_s)
    print(f"  旧: {old_s}")
    print(f"  新: {new_s[:50]}...")
    print(f"  融合: {fused[:100]}...")

    # 测试5: upgrade_expert (完整流程)
    print("\n[测试5] upgrade_expert (完整流程)")
    strategies = {
        "attack_strategy": {
            "best_angle": "历史案例对比",
            "why_effective": "用具体历史事实证明观点",
            "applicable_when": "对手缺乏历史依据时",
            "kill_rating": "高",
            "key_technique": "证据碾压",
            "quality_score": 8.5,
        },
        "defense_weakness": {
            "broken_by": "被指理想化",
            "why_vulnerable": "缺乏具体历史案例支撑",
            "fix_strategy": "引用周公制礼的具体历史背景",
            "priority": "高",
            "success_rate": 65.0,
        },
        "style_fingerprint": {
            "most_authentic_line": "吾以为，仁政之本在于爱人",
            "why_authentic": "使用'吾以为'标志性开头，符合孔子温和说理的表达风格",
            "weakest_line": "从数据角度看",
            "why_weak": "孔子不会用现代数据语言",
        },
        "evidence_preference": {
            "most_effective_type": "历史案例",
            "ranking": ["历史案例", "经典引用", "类比隐喻"],
        },
        "interaction_pattern": {
            "best_opponent": "韩非子",
            "worst_opponent": "尼采",
        },
    }

    upgraded_content = engine.upgrade_expert(test_md_path, strategies, score=82.0)

    # 验证升级结果
    parser = ExpertFusionParser(upgraded_content)
    meta = parser.get_meta()
    print(f"  版本: {meta.get('版本', 'N/A')}")
    print(f"  训练次数: {meta.get('训练次数', 'N/A')}")
    print(f"  当前评分: {meta.get('当前评分', 'N/A')}")

    attacks = parser.parse_attack_table()
    print(f"  攻击模式数: {len(attacks)}")
    for a in attacks:
        print(f"    - {a['angle']} ({a['rating']})")

    defenses = parser.parse_defense_table()
    print(f"  防御模式数: {len(defenses)}")
    for d in defenses:
        print(f"    - {d['type']}: {d['rate_str']}")

    # 验证能力图谱
    graph = parser.capability_graph
    print(f"  能力节点数: {len(graph.nodes)}")
    print(f"  进化边数: {len(graph.edges)}")

    # 测试6: CapabilityGraph
    print("\n[测试6] CapabilityGraph")
    cg = CapabilityGraph("测试专家")
    node1 = cg.add_node("attack", "逻辑攻击", 6.0, "初始")
    node2 = cg.add_node("attack", "逻辑+证据复合攻击", 8.5, "MERGE")
    cg.add_edge(node1, node2, "MERGE", "合并逻辑和证据攻击")
    path = cg.get_evolution_path("attack")
    print(f"  进化路径长度: {len(path)}")
    for p in path:
        print(f"    v{p['version']}: {p['content'][:30]}... (评分: {p['quality_score']})")

    weak = cg.find_weak_capabilities(threshold=7.0)
    print(f"  弱能力数: {len(weak)}")

    # 清理
    shutil.rmtree(test_dir)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
