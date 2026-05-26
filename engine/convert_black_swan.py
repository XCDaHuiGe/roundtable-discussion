# -*- coding: utf-8 -*-
"""V8 JSON 转换器：将黑天鹅讨论 JSON 转换为渲染器格式"""

import json
import os
import re

EXPERT_COLORS = {
    "塔勒布": "#8a2a4a",
    "纳西姆·塔勒布": "#8a2a4a",
    "巴菲特": "#1a5f2a",
    "沃伦·巴菲特": "#1a5f2a",
    "芒格": "#2d5a8e",
    "查理·芒格": "#2d5a8e",
    "吴军": "#2a6a6a",
    "李诞": "#FFC107",
    "柯林斯": "#4a2d8a",
    "吉姆·柯林斯": "#4a2d8a",
}

EXPERT_PROFILES = {
    "塔勒布": {
        "core_belief": "世界由不可预测的极端事件主导，智慧在于构建能从混乱中获益的反脆弱系统",
        "interest": "算法时代的黑天鹅是否更频繁？量化模型在极端情况下的失效是系统性缺陷",
        "fear": "当所有人使用相同的模型时，一个小波动就能引发相关性共振的雪崩",
        "bias": "倾向于认为任何预测模型在极端斯坦都会失效，但可能低估了进化的可能性"
    },
    "巴菲特": {
        "core_belief": "买股票就是买公司，用合理价格买优秀企业，让复利创造奇迹",
        "interest": "量化时代，价值投资是否还有生存空间？能力圈原则在AI时代是否更加重要",
        "fear": "算法让市场更有效，但这不意味着真正的风险消失了，只是换了形式",
        "bias": "倾向于认为人类判断力在投资中的核心地位不可替代，但可能低估AI的演进速度"
    },
    "芒格": {
        "core_belief": "多元思维模型+逆向思维+长期视角=卓越决策；人类误判心理学是投资核心",
        "interest": "AI能否真正理解'软信息'——语气、留白、不说的话？",
        "fear": "量化算法本质上是高级版'铁锤人综合征'，在极端情况下必然失效",
        "bias": "倾向于认为人类的直觉判断不可替代，但承认AI在特定任务上的效率优势"
    },
    "吴军": {
        "core_belief": "科技发展以浪潮形式推进，简单即是美；顺势者昌逆势者亡",
        "interest": "AI和人类直觉是分工协作还是替代竞争？技术进步的边界在哪",
        "fear": "信息差的缩小可能只是表面，更深的结构性不平等依然存在",
        "bias": "技术乐观主义者，但承认'软信息'处理是当前AI的局限"
    },
    "李诞": {
        "core_belief": "人间不值得，但你已经来了，那就凑合过吧——承认虚无但不虚无",
        "interest": "散户与精英博弈的真相是什么？普通人在AI时代如何自处",
        "fear": "精英们讨论的'算法胜负'与普通人关心的'退休金安全'是两个世界",
        "bias": "倾向于解构宏大叙事，强调普通人的视角和生存困境"
    },
    "柯林斯": {
        "core_belief": "卓越是持续推动飞轮的结果；第五级经理人+刺猬理念=伟大企业",
        "interest": "量化算法把金融市场当成静态系统，但市场是由真实的人驱动的动态飞轮",
        "fear": "飞轮效应被误解为'找到就能躺赢'，但真正的飞轮需要持续维护",
        "bias": "实证主义者，质疑幸存者偏差和数据选择的科学性"
    }
}


def normalize_name(name: str) -> str:
    """统一专家名字"""
    mapping = {
        "沃伦·巴菲特": "巴菲特",
        "查理·芒格": "芒格",
        "纳西姆·塔勒布": "塔勒布",
        "吉姆·柯林斯": "柯林斯",
    }
    return mapping.get(name, name)


def build_experts(data: dict) -> list:
    """构建专家档案"""
    experts_list = []
    for e in data["participants"]:
        name = normalize_name(e["name"])
        profile = EXPERT_PROFILES.get(name, {
            "core_belief": "待填充",
            "interest": "待填充",
            "fear": "待填充",
            "bias": "待填充"
        })
        color = e.get("color", "#333333")
        experts_list.append({
            "name": name,
            "title": e.get("role", ""),
            "avatar_color": color,
            **profile
        })
    return experts_list


def build_stances(round_data: dict, data: dict) -> list:
    """构建立场"""
    stances = []
    for s in round_data.get("discussion", []):
        if s.get("type") in ["opening", "synthesis"]:
            stances.append({
                "expert": normalize_name(next((p["name"] for p in data["participants"] if p["id"] == s["speaker"]), s["speaker"])),
                "stance": s["content"],
                "emotion": "serious"
            })
    return stances


def build_clash_rounds(round_data: dict, data: dict) -> list:
    """构建碰撞轮次"""
    clashes = []
    for s in round_data.get("discussion", []):
        if s.get("type") in ["attack", "counter"]:
            targets = s.get("targets", [])
            if targets:
                target_id = targets[0] if isinstance(targets[0], str) else targets[0].get("id", "unknown")
                target_name = normalize_name(next((p["name"] for p in data["participants"] if p["id"] == target_id), target_id))
                clashes.append({
                    "attacker": normalize_name(next((p["name"] for p in data["participants"] if p["id"] == s["speaker"]), s["speaker"])),
                    "target": target_name,
                    "attack_type": "逻辑漏洞",
                    "attack_content": s["content"],
                    "emotion": "serious",
                    "counter_attack": None
                })
    return clashes


def build_rounds(data: dict) -> list:
    """构建完整的轮次数据"""
    rounds = []
    
    for i, r in enumerate(data["rounds"]):
        round_number = r["round"]
        topic = r["title"]
        core_question = r["theme"]
        
        stances = []
        clashes = []
        
        for s in r.get("discussion", []):
            speaker_id = s["speaker"]
            speaker_name = normalize_name(next((p["name"] for p in data["participants"] if p["id"] == speaker_id), speaker_id))
            
            if s.get("type") in ["opening"]:
                stances.append({
                    "expert": speaker_name,
                    "stance": s["content"],
                    "emotion": "serious"
                })
            elif s.get("type") in ["attack", "counter"]:
                targets = s.get("targets", [])
                if targets:
                    if isinstance(targets[0], str):
                        target_name = normalize_name(next((p["name"] for p in data["participants"] if p["id"] == targets[0]), targets[0]))
                    else:
                        target_name = normalize_name(targets[0].get("name", "unknown"))
                else:
                    target_name = "未知"
                
                clashes.append({
                    "attacker": speaker_name,
                    "target": target_name,
                    "attack_type": "逻辑漏洞",
                    "attack_content": s["content"],
                    "emotion": "serious",
                    "counter_attack": None
                })
        
        rounds.append({
            "round_number": round_number,
            "topic": topic,
            "core_question": core_question,
            "stances": stances,
            "clash_rounds": clashes if round_number == 2 else [],
            "reality_cases": [],
            "cost_discussion": {},
            "human_nature": {},
            "cognitive_upgrade": {}
        })
    
    # Round 3 需要合成数据
    if len(rounds) >= 3:
        # 使用Round 3的synthesis构建
        r3 = data["rounds"][2]
        syntheses = [s for s in r3.get("discussion", []) if s.get("type") == "synthesis"]
        
        # 构建现实案例
        reality_cases = []
        case_templates = [
            {
                "case_name": "GameStop事件（2021）",
                "case_source": "[来源：WSB论坛与金融媒体报道]",
                "case_content": "2021年1月，Reddit论坛WallStreetBets的散户投资者协同买入GameStop股票，成功猎杀Melvin Capital等做空机构。股价从20美元飙升至483美元，引发史上最大的'轧空'事件之一。",
                "case_outcome": "机构亏损数十亿美元，但散户最终也被Robinhood等平台限制交易",
                "case_lesson": "散户协同确实能打破机构假设，但这是否证明算法时代的黑天鹅更可控？"
            },
            {
                "case_name": "量化踩踏事件",
                "case_source": "[来源：1987年股灾与2010年闪崩研究]",
                "case_content": "1987年10月19日'黑色星期一'，道琼斯指数暴跌22.6%。程序化交易策略的'投资组合保险'加剧了抛售压力，Quant策略让整个华尔街陷入踩踏。2010年5月6日道指'闪崩'，也是算法共振的典型案例。",
                "case_outcome": "市场在几分钟内暴跌近千点，随后迅速反弹，监管机构至今无法确定原因",
                "case_lesson": "当所有算法都在执行相同的止损逻辑时，小波动会引发雪崩式下跌"
            },
            {
                "case_name": "AI投研能力边界",
                "case_source": "[来源：中信建投2025年AI投研报告]",
                "case_content": "中信建投研究显示：AI投研L3已能承担独立分析师级工作，能处理海量数据、识别财务异常、生成研究报告。但L4/L5仍处于展望阶段——需要深度理解商业逻辑、管理层意图和行业趋势的判断性工作。",
                "case_outcome": "AI在L3任务上效率远超人类，但'软信息'处理仍是瓶颈",
                "case_lesson": "财新报道指出：'真正有信息含量的往往不在字面，而在语气、留白和不说的话里'"
            }
        ]
        
        for i, syn in enumerate(syntheses[:3]):
            speaker_id = syn["speaker"]
            speaker_name = normalize_name(next((p["name"] for p in data["participants"] if p["id"] == speaker_id), speaker_id))
            case = case_templates[i]
            reality_cases.append({
                **case,
                "case_content": case["case_content"] + f"\n\n【{speaker_name}洞见】{syn['content']}"
            })
        
        rounds[2]["reality_cases"] = reality_cases
        
        # 构建代价讨论
        rounds[2]["cost_discussion"] = {
            "scenario": "如果普通人试图在算法时代'战胜市场'，会发生什么？",
            "cost_analysis": [
                {
                    "cost": "信息差的结构性不平等",
                    "analysis": "算法让市场更有效，但高效的市场对散户更加残酷——当机构用AI处理信息时，散户用什么？表面上的信息平权掩盖了更深的能力差距。"
                },
                {
                    "cost": "散户的'软信息'劣势",
                    "analysis": "财新指出AI的局限在于'语气、留白和不说的话'——这些软信息恰恰是人类最擅长的，但普通散户有渠道获取这些信息吗？"
                },
                {
                    "cost": "GameStop式胜利的幻象",
                    "analysis": "散户协同确实赢了机构一次，但Robinhood随即限制了交易。这种'胜利'创造了什么真实价值？机构会总结经验教训，散户只是在社交媒体上欢呼。"
                }
            ],
            "worst_case": "普通人在算法时代试图'主动博弈'，结果被高频交易、量化策略和信息差收割得更彻底。",
            "survivor_bias": "你只看到GameStop的散户胜利，看不到同期有多少散户在协同失败后被机构反向收割。"
        }
        
        # 构建人性层
        rounds[2]["human_nature"] = {
            "question": "为什么人类总是高估自己的判断力，同时低估系统的脆弱性？",
            "psychological_analysis": "投资中最大的敌人不是市场，而是我们自己。人类天生倾向于：1）过度自信——认为自己的模型比别人的更准确；2）线性外推——用过去预测未来；3）群体思维——当算法都使用相似模型时，它们都在犯同样的错误。塔勒布的核心洞见：脆弱的不是个体，而是系统。",
            "real_examples": [
                "1987年股灾：所有Quant策略都在执行'投资组合保险'的止损逻辑，然后市场崩了——没有人停下来问'如果所有人都这样做会怎样？'",
                "GameStop事件：机构做空假设散户不会协同，但Reddit证明了群体行为可以打破模型假设——问题是，下次还会有效吗？",
                "2025年金融AI市场362亿美元，每个机构都在投资——当所有人都用AI时，AI的优势还存在吗？"
            ],
            "conclusion": "人类的判断力在AI时代并未失效，但需要进化：不是与AI竞争数据处理，而是专注于AI无法处理的'软信息'和'极端情况预判'。"
        }
        
        # 构建认知升级
        rounds[2]["cognitive_upgrade"] = {
            "old_thinking": "AI会取代人类判断，所以散户没有机会了。",
            "new_thinking": "AI会淘汰'可量化的判断'，但'不可量化的判断'——软信息、极端情况、人性洞察——是人类最后的护城河。",
            "complexity": "李诞的视角提醒我们：精英们讨论的'算法胜负'与普通人关心的'退休金安全'是两个世界。对普通人来说，不是'战胜算法'，而是'利用算法'——买指数基金，好好睡觉。",
            "actionable_insight": "1）不要试图战胜AI，而是利用AI工具提升效率；2）专注于AI无法处理的'软信息'能力建设；3）对普通人来说，低成本指数基金+持续学习=最理性的生存策略。"
        }
    
    return rounds


def build_final_insight(data: dict) -> str:
    """构建最终洞见"""
    insights = data.get("final_insights", [])
    if insights:
        return insights[0].get("title", "") + "：" + insights[0].get("insight", "")
    return "算法的'正常'与'极端'不对称性是人类判断的最后护城河"


def build_open_questions(data: dict) -> list:
    """构建开放问题"""
    return [
        "量化算法是否会让黑天鹅事件更频繁？当所有人使用相同的模型时，'轧空'和'踩踏'是否会变成常态？",
        "GameStop事件是散户觉醒的开始，还是一次不可复制的偶然？普通人在算法时代如何找到自己的生存策略？",
        "AI能否最终学会处理'软信息'？当AI发展到L5阶段，人类直觉还剩什么价值？"
    ]


def convert(input_path: str, output_path: str):
    """转换讨论 JSON 为 V8 渲染器格式"""
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    output = {
        "title": data["title"],
        "subtitle": f"《{data['book_title']}》· 6位专家 · 3轮碰撞 · 基于2025年互联网真实素材",
        "experts": build_experts(data),
        "rounds": build_rounds(data),
        "final_insight": build_final_insight(data),
        "open_questions": build_open_questions(data)
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Converted: {output_path}")
    return output


if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "content/黑天鹅_量化博弈_讨论.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "content/黑天鹅_量化博弈_v8.json"
    convert(input_path, output_path)
