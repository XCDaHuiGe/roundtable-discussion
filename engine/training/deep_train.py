# -*- coding: utf-8 -*-
"""
⚠️ DEPRECATED (V11.0 起废弃) — 深度训练引擎 V1.0

此模块已被 auto_train.py V11.0 取代（含 Coach + 门控 + 追踪闭环）。
存在字段名不匹配 bug（expert1 vs expert_a）和类型错误。
保留此文件仅供历史参考，不要在新代码中导入。

深度训练引擎 V1.0

核心流程：
1. LLM自主生成话题（基于专家信念冲突）
2. WebSearch搜索话题相关内容
3. 知乎MCP采集深度内容
4. LLM生成多轮专家辩论对话
5. 从辩论中提取策略，更新专家档案

用法：
    python engine/training/deep_train.py --rounds 10
    python engine/training/deep_train.py --experts 孔子,老子,韩非子
"""

import argparse
import json
import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.orchestrator import TrainingOrchestrator
from training.debate_arena import DebateArena
from training.evolution_engine import EvolutionEngine
from training.extractor import extract


class DeepTrainer:
    def __init__(self, library_dir: str = 'expert-library', log_dir: str = 'memory'):
        self.library_dir = library_dir
        self.log_dir = log_dir
        self.arena = DebateArena(library_dir)
        self.evolution_engine = EvolutionEngine(library_dir)
        os.makedirs(log_dir, exist_ok=True)
        
    def generate_topic_from_conflict(self) -> Dict:
        """从专家信念冲突中生成话题"""
        conflicts = self.arena.get_all_conflicts()
        if not conflicts:
            return self._generate_default_topic()
        
        conflict = random.choice(conflicts)
        expert_a = conflict.get('expert_a', '')
        expert_b = conflict.get('expert_b', '')
        belief_a = conflict.get('belief_a', '')
        belief_b = conflict.get('belief_b', '')
        
        topic = {
            'title': f"{expert_a}的'{belief_a}'与{expert_b}的'{belief_b}'冲突",
            'description': f"当{expert_a}最看重'{belief_a}'，{expert_b}最看重'{belief_b}'时，在真实决策中如何选择？",
            'conflict_experts': [expert_a, expert_b],
            'belief_conflict': {'a': belief_a, 'b': belief_b},
        }
        return topic
    
    def _generate_default_topic(self) -> Dict:
        """默认话题生成"""
        default_topics = [
            {'title': 'AI时代的职业选择', 'description': '人工智能会取代哪些工作？人类应该如何应对？'},
            {'title': '数字游民的生活方式', 'description': '远程工作是否真的自由？有什么隐藏的代价？'},
            {'title': '消费主义的陷阱', 'description': '消费如何塑造我们的身份？如何逃离消费陷阱？'},
            {'title': '内卷与躺平的选择', 'description': '竞争压力下，应该继续奋斗还是选择躺平？'},
            {'title': '社交媒体的注意力殖民', 'description': '算法如何控制我们的注意力？如何夺回自主权？'},
        ]
        return random.choice(default_topics)
    
    def generate_debate_prompt(self, topic: Dict, experts: List[str]) -> str:
        """生成辩论Prompt"""
        expert_profiles = []
        for name in experts:
            profile = self._load_expert_profile(name)
            if profile:
                expert_profiles.append(f"【{name}】\n核心立场：{profile.get('stance', '')}\n发言风格：{profile.get('style', '')}")
        
        prompt = f"""
你是一个圆桌讨论主持人，请组织以下专家就话题进行深度辩论。

## 话题
{topic['title']}
{topic['description']}

## 参与专家
{chr(10).join(expert_profiles)}

## 辩论规则
1. 每位专家必须表达自己的立场（第一轮）
2. 专家之间必须相互质疑和反驳（第二轮）
3. 专家必须回应他人的质疑（第三轮）
4. 每次发言必须包含：观点+论据+推理
5. 发言风格必须符合专家特征

## 输出格式（JSON）
{
  "rounds": [
    {
      "round_name": "立场阐述",
      "speeches": [
        {"expert": "专家名", "stance": "立场", "content": "发言内容", "style_markers": ["风格标记"]}
      ]
    },
    {
      "round_name": "相互质疑",
      "speeches": [
        {"expert": "专家名", "target": "质疑对象", "attack_type": "质疑类型", "content": "质疑内容"}
      ]
    },
    {
      "round_name": "回应辩护",
      "speeches": [
        {"expert": "专家名", "defense_type": "辩护类型", "content": "辩护内容"}
      ]
    }
  ],
  "clash_rounds": [
    {
      "attacker": "攻击者", "target": "被攻击者", "attack_type": "攻击类型",
      "attack_content": "攻击内容", "counter_attack": "反击内容"
    }
  ]
}

请生成完整的辩论内容。
"""
        return prompt
    
    def _load_expert_profile(self, name: str) -> Optional[Dict]:
        """加载专家档案"""
        categories = ['philosophy', 'business', 'psychology', 'science', 'economics', 'literature', 'history']
        for cat in categories:
            path = os.path.join(self.library_dir, 'experts', cat, f'{name}.md')
            if os.path.exists(path):
                return self._parse_expert_md(path)
        return None
    
    def _parse_expert_md(self, path: str) -> Dict:
        """解析专家MD档案"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        stance = ''
        style = ''
        
        if '## 核心立场' in content:
            start = content.find('## 核心立场')
            end = content.find('##', start + 10)
            stance = content[start:end].replace('## 核心立场', '').strip()[:200]
        
        if '## 发言风格' in content:
            start = content.find('## 发言风格')
            end = content.find('##', start + 10)
            style = content[start:end].replace('## 发言风格', '').strip()[:200]
        
        return {'stance': stance, 'style': style}
    
    def select_experts_for_topic(self, topic: Dict) -> List[str]:
        """为话题选择专家"""
        if 'conflict_experts' in topic:
            base_experts = topic['conflict_experts']
        else:
            profiles = self.arena.profiles
            if len(profiles) >= 6:
                base_experts = random.sample(list(profiles.keys()), 6)
            else:
                base_experts = list(profiles.keys())[:6]
        return base_experts
    
    def run_deep_training(self, rounds: int = 10) -> Dict:
        """运行深度训练"""
        print(f"\n{'='*60}")
        print(f"  深度训练引擎 V1.0")
        print(f"  轮次: {rounds} | 专家库: {len(self.arena.profiles)} 位")
        print(f"{'='*60}\n")
        
        results = {
            'rounds': rounds,
            'topics_generated': [],
            'debates_generated': [],
            'expert_upgrades': {},
            'start_time': datetime.now().isoformat(),
        }
        
        total_strategy_merges = 0
        total_material_replacements = 0
        
        for i in range(rounds):
            print(f"\n[{i+1}/{rounds}] 深度训练轮次")
            
            topic = self.generate_topic_from_conflict()
            print(f"  话题: {topic['title']}")
            results['topics_generated'].append(topic['title'])
            
            experts = self.select_experts_for_topic(topic)
            print(f"  专家: {', '.join(experts)}")
            
            debate_json = self._generate_debate_json(topic, experts)
            if debate_json:
                results['debates_generated'].append(debate_json)
                
                temp_path = self._save_temp_debate(debate_json, i)
                
                extraction = extract(temp_path)
                
                score = 70.0
                
                for expert_name, expert_data in extraction.get('experts', {}).items():
                    strategy = {
                        'attack_strategy': expert_data.get('attack_strategy', {}),
                        'defense_weakness': expert_data.get('defense_weakness', {}),
                        'style_fingerprint': expert_data.get('style_fingerprint', {}),
                    }
                    
                    evo_result = self.evolution_engine.evolve(
                        expert_name, strategy,
                        topic=topic['title'],
                        score=score,
                    )
                    
                    if evo_result:
                        if expert_name not in results['expert_upgrades']:
                            results['expert_upgrades'][expert_name] = []
                        results['expert_upgrades'][expert_name].append({
                            'old_version': evo_result.old_version,
                            'new_version': evo_result.new_version,
                            'strategy_merges': len(evo_result.strategy_merges),
                        })
                        total_strategy_merges += len(evo_result.strategy_merges)
                        total_material_replacements += len(evo_result.material_replacements)
                        print(f"    {expert_name}: V{evo_result.old_version}→V{evo_result.new_version}")
                
                os.remove(temp_path)
        
        results['total_strategy_merges'] = total_strategy_merges
        results['total_material_replacements'] = total_material_replacements
        results['end_time'] = datetime.now().isoformat()
        
        log_path = os.path.join(self.log_dir, f'deep_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"  深度训练完成")
        print(f"  话题生成: {len(results['topics_generated'])}")
        print(f"  辩论生成: {len(results['debates_generated'])}")
        print(f"  策略融合: {total_strategy_merges}")
        print(f"  素材替换: {total_material_replacements}")
        print(f"  专家升级: {len(results['expert_upgrades'])} 位")
        print(f"{'='*60}\n")
        
        return results
    
    def _generate_debate_json(self, topic: Dict, experts: List[str]) -> Optional[Dict]:
        """生成辩论JSON（模拟版，实际需要调用LLM）"""
        debate = {
            'title': topic['title'],
            'experts': experts,
            'rounds': [
                {
                    'round_name': '立场阐述',
                    'speeches': []
                },
                {
                    'round_name': '相互质疑',
                    'speeches': []
                },
                {
                    'round_name': '回应辩护',
                    'speeches': []
                }
            ],
            'clash_rounds': []
        }
        
        for expert in experts:
            profile = self._load_expert_profile(expert)
            stance = profile.get('stance', '保持理性分析') if profile else '保持理性分析'
            
            debate['rounds'][0]['speeches'].append({
                'expert': expert,
                'stance': stance[:50],
                'content': f"我认为{topic['title']}的核心在于{stance[:100]}。这需要我们从多个角度来审视。",
                'style_markers': ['理性', '数据驱动']
            })
        
        for i, attacker in enumerate(experts):
            target = experts[(i + 1) % len(experts)]
            debate['clash_rounds'].append({
                'attacker': attacker,
                'target': target,
                'attack_type': '逻辑漏洞',
                'attack_content': f"{attacker}质疑{target}的观点存在逻辑跳跃，缺乏实证支撑。",
                'counter_attack': f"{target}回应：我的观点基于长期观察，逻辑链条完整。"
            })
        
        return debate
    
    def _save_temp_debate(self, debate: Dict, round_num: int) -> str:
        """保存临时辩论文件"""
        temp_path = os.path.join(self.log_dir, f'temp_debate_{round_num}.json')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(debate, f, ensure_ascii=False, indent=2)
        return temp_path


def main():
    parser = argparse.ArgumentParser(description='深度训练引擎 V1.0')
    parser.add_argument('--rounds', type=int, default=10, help='训练轮次')
    parser.add_argument('--library', default='expert-library', help='专家库目录')
    parser.add_argument('--log-dir', default='memory', help='日志目录')
    
    args = parser.parse_args()
    
    trainer = DeepTrainer(
        library_dir=args.library,
        log_dir=args.log_dir,
    )
    
    trainer.run_deep_training(rounds=args.rounds)


if __name__ == '__main__':
    main()