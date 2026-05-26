# -*- coding: utf-8 -*-
"""V8 JSON 转换器：AI生成叙事_金融定价"""

import json
import os

EXPERT_COLORS = {
    "纳西姆·塔勒布": "#8a2a4a",
    "塔勒布": "#8a2a4a",
    "吴军": "#2a6a6a",
    "李诞": "#4a6a2a",
    "刘润": "#6a4a2a",
    "罗翔": "#2a4a6a",
    "凯文·凯利": "#4a2a6a",
    "KK": "#4a2a6a"
}

EXPERT_PROFILES = {
    "纳西姆·塔勒布": {
        "core_belief": "世界由极端事件主导，智慧在于知道自己不知道什么，并构建能从混乱中获益的系统",
        "interest": "AI叙事革命是否会放大金融市场的\"相关性崩溃\"风险——当所有人都依赖同一套AI系统时",
        "fear": "AI生成的\"完美同质化\"信息会让市场在黑天鹅来临时加速崩溃，而非分散风险",
        "bias": "系统性低估AI在\"已知未知\"领域的效率，低估相关性崩溃的概率"
    },
    "吴军": {
        "core_belief": "科技发展以浪潮形式推进，顺势者昌；简单即是美，AI是人类认知的扩展而非替代",
        "interest": "中信建投、招商证券的AI应用案例——中国市场的AI落地速度和应用方式",
        "fear": "从业者只关注\"被替代\"的恐惧，而忽视了\"驾驭AI\"的机会",
        "bias": "对中国市场的独特性可能过于乐观，忽视监管和散户非理性因素的影响"
    },
    "李诞": {
        "core_belief": "人间不值得，但活着本身就是意义——解构一切宏大叙事，揭示\"表演\"背后的真实",
        "interest": "那些被替代的\"报告写作\"工作，有多少是真正有价值的？有多少只是\"流程要求\"？",
        "fear": "AI只是加速了\"假戏\"的完成，但人们会用\"AI焦虑\"来掩盖真实的无力感",
        "bias": "倾向于认为\"努力无用\"，可能低估了主动拥抱变化的人的价值"
    },
    "刘润": {
        "core_belief": "商业的本质是交易，所有问题都是交易成本问题；AI重构了什么值得定价",
        "interest": "当信息成本趋近于零，什么交易成本反而上升？——\"信任\"和\"判断力\"的价值重估",
        "fear": "大家只关注AI的效率，而忽视AI带来的\"信任重构\"问题",
        "bias": "过度强调商业逻辑，可能忽视法律、伦理等非商业维度"
    },
    "罗翔": {
        "core_belief": "法治的要义是对权力的限制；技术可以是中立的，但掌握技术的人不是",
        "interest": "当70%分析师被替代，剩下30%拥有更大定价权——这是不是一种\"合法的权力集中\"？",
        "fear": "AI让追问变得不可能——当\"完美报告\"的生产者是一个黑箱时，谁来为误判负责？",
        "bias": "倾向于关注\"弱势群体\"的处境，可能低估AI对信息民主化的贡献"
    },
    "凯文·凯利": {
        "core_belief": "AI是\"异类智能\"，与人类智能平行存在；学会与异类共生，而非与它竞争",
        "interest": "金融市场的\"人机协作新形态\"——不是取代，而是扩展能力边界",
        "fear": "大家把AI当作\"竞争对手\"而非\"合作伙伴\"，错失共生红利",
        "bias": "对\"进托邦\"的乐观可能低估了转型期的阵痛和不平等"
    }
}


def normalize_name(name: str) -> str:
    """统一专家名字"""
    mapping = {
        "凯文·凯利": "凯文·凯利",
        "KK": "凯文·凯利"
    }
    return mapping.get(name, name)


def build_experts(data: dict) -> list:
    """构建专家档案"""
    experts_list = []
    for e in data["rounds"][0]["speakers"]:
        name = e["expert"]
        profile = EXPERT_PROFILES.get(name, {
            "core_belief": "待填充",
            "interest": "待填充",
            "fear": "待填充",
            "bias": "待填充"
        })
        color = EXPERT_COLORS.get(name, "#333333")
        
        titles = {
            "纳西姆·塔勒布": "不确定性思想家 · 《黑天鹅》作者",
            "吴军": "科技投资观察者 · 《浪潮之巅》作者",
            "李诞": "喜剧人/解构者 · 《笑场》作者",
            "刘润": "商业结构化视角 · 润米咨询创始人",
            "罗翔": "法律与人性视角 · 中国政法大学教授",
            "凯文·凯利": "科技趋势观察者 · 《连线》创始主编"
        }
        
        experts_list.append({
            "name": name,
            "title": titles.get(name, "专家"),
            "avatar_color": color,
            **profile
        })
    return experts_list


def build_stances(round_data: dict) -> list:
    """构建立场"""
    return [
        {
            "expert": normalize_name(s["expert"]),
            "stance": s["position"] + "\n\n" + s["content"],
            "emotion": "serious"
        }
        for s in round_data["speakers"]
    ]


def build_clash_rounds(round_data: dict) -> list:
    """构建碰撞轮次"""
    clashes = []
    for a in round_data.get("attacks", []):
        clashes.append({
            "attacker": normalize_name(a["from"]),
            "target": normalize_name(a["to"]),
            "attack_type": "认知碰撞",
            "attack_content": a["content"],
            "emotion": "serious",
            "counter_attack": None
        })
    return clashes


def build_insights(r3_data: dict) -> list:
    """从 Round 3 的 insights 构建"""
    cases = []
    case_map = [
        {
            "case_name": "中信建投AI投研L3",
            "case_source": "[来源：新华财经]",
            "case_content": "中信建投AI投研L3框架：2-5分钟自动生成研报级HTML/Word报告。\n\n" + r3_data["insights"][0]["statement"],
            "case_outcome": "效率提升：人类分析师需要3-5天，AI仅需2-5分钟",
            "case_lesson": r3_data["insights"][2]["statement"]
        },
        {
            "case_name": "招商证券香港AI Agent",
            "case_source": "[来源：招商证券香港]",
            "case_content": "5个AI Agent并行工作，2.5小时完成人类分析师一周工作量。\n\n" + r3_data["insights"][1]["statement"],
            "case_outcome": "产能跃升：周级别工作量压缩至小时级别",
            "case_lesson": r3_data["insights"][3]["statement"]
        },
        {
            "case_name": "分析师替代率70%",
            "case_source": "[来源：新浪财经2025年8月一线券商测算]",
            "case_content": "一线券商内部测算：初级和中级分析师岗位替代率可能高达70%。\n\n" + r3_data["insights"][4]["statement"],
            "case_outcome": "行业地震：七成分析师面临转型或失业压力",
            "case_lesson": r3_data["insights"][5]["statement"]
        }
    ]
    return case_map


def build_synthesis() -> dict:
    """构建综合洞察"""
    return {
        "scenario": "谁真正从AI叙事革命中获益？",
        "cost_analysis": [
            {
                "cost": "塔勒布：杠铃策略",
                "analysis": "真正获益的不是拥抱AI最快的人，而是\"知道AI什么时候会失败\"的人。AI降低了\"已知\"的成本，但\"未知\"的价值反而上升。"
            },
            {
                "cost": "吴军：见识决定命运",
                "analysis": "获益的是\"知道AI边界在哪里\"的人。见识决定命运，在AI时代，见识就是\"知道自己不擅长什么\"。"
            },
            {
                "cost": "李诞：要么更快，要么更慢",
                "analysis": "卡在中间做\"中等效率\"的事情，是AI时代最糟糕的策略。要么用AI跑得更快，要么专注AI永远做不了的事。"
            },
            {
                "cost": "刘润：信任差",
                "analysis": "当信息差消失，\"信任差\"反而成为新的稀缺资源。商业的本质是交易，AI让交易更容易，但\"建立信任\"这件事AI帮不了你。"
            },
            {
                "cost": "罗翔：警惕权力集中",
                "analysis": "真正有价值的，是那些能帮助\"弱者\"使用AI的力量。技术本身是中立的，但技术+资本的结合会放大既有的不平等。"
            },
            {
                "cost": "KK：学会共生",
                "analysis": "获益最大的是那些学会与\"异类智能\"协作的人。未来最成功的金融机构，是那些学会与AI\"共生\"的机构。"
            }
        ],
        "worst_case": "当所有人都在用同一套AI系统做决策，\"人类的选择\"还存在吗？或者说，它还有意义吗？",
        "survivor_bias": "我们只看到\"被AI替代\"的恐惧，看不到那些\"因为AI而释放出来\"去做更有价值事情的人。"
    }


def build_human_nature() -> dict:
    """构建人性层"""
    return {
        "question": "为什么金融市场的定价从来不只是信息处理？",
        "psychological_analysis": "金融市场的定价，表面上是数字的博弈，深层是人性预期的博弈——欲望、恐惧、信任、偏见。AI擅长的是\"字面\"，是\"逻辑推理\"，但它无法复制人类的\"情绪波动\"。当一份研报不再有\"分析师的犹豫\"、\"语气中的暗示\"，市场反而失去了一个重要的信号来源。真正有信息含量的，恰恰是\"没说出口的话\"。AI可以生成完美的字面，但无法生成\"人性\"。",
        "real_examples": [
            "财新指出：真正有信息含量的往往不在字面，而在语气、留白和不说的话里——这恰恰是AI的弱势",
            "2025年9月，某大型公募基金使用AI研报后反而加大人类分析师投入——因为AI研报引发大量\"追责\"问题",
            "当\"完美报告\"的生产者是一个黑箱时，谁来为误判负责？这个责任问题，AI无法回答"
        ],
        "conclusion": "AI生成叙事颠覆的不是信息本身，而是\"信息的稀缺性\"——当信息不再稀缺，判断力和信任成为新的稀缺资源。"
    }


def build_cognitive_upgrade(r3_data: dict) -> dict:
    """构建认知升级"""
    return {
        "old_thinking": "AI会取代分析师，市场不再需要那么多\"写报告的人\"",
        "new_thinking": "AI会重塑分析师的价值——从\"信息整理者\"转向\"判断力提供者\"，那些能读懂\"语气、留白和不说的话\"的人，正在变得前所未有地值钱",
        "complexity": "AI叙事革命不是\"取代\"，而是\"分工重构\"。AI接管了\"50-90分的区间\"，人类的艺术在100分那里等着。问题是：你能达到100分吗？",
        "actionable_insight": "不要问\"AI能不能替代我\"，要问\"AI能让我的判断力扩展多少倍\"。或者，更根本的问题是：在AI生成海量同质化内容的时代，你的\"不可替代性\"在哪里？"
    }


def build_rounds(data: dict) -> list:
    """构建完整的轮次数据"""
    rounds = []

    # Round 1
    r1 = data["rounds"][0]
    rounds.append({
        "round_number": 1,
        "topic": r1["theme"],
        "core_question": "AI叙事是否真正颠覆了金融定价？",
        "stances": build_stances(r1),
        "clash_rounds": [],
        "reality_cases": [],
        "cost_discussion": {},
        "human_nature": {},
        "cognitive_upgrade": {}
    })

    # Round 2
    r2 = data["rounds"][1]
    rounds.append({
        "round_number": 2,
        "topic": r2["theme"],
        "core_question": "AI叙事的天花板在哪里？",
        "stances": [],
        "clash_rounds": build_clash_rounds(r2),
        "reality_cases": [],
        "cost_discussion": {},
        "human_nature": {},
        "cognitive_upgrade": {}
    })

    # Round 3
    r3 = data["rounds"][2]
    rounds.append({
        "round_number": 3,
        "topic": r3["theme"],
        "core_question": "谁真正从AI叙事革命中获益？",
        "stances": [],
        "clash_rounds": [],
        "reality_cases": build_insights(r3),
        "cost_discussion": build_synthesis(),
        "human_nature": build_human_nature(),
        "cognitive_upgrade": build_cognitive_upgrade(r3)
    })

    return rounds


def convert(input_path: str, output_path: str):
    """转换讨论 JSON 为 V8 渲染器格式"""
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    output = {
        "title": data["title"],
        "subtitle": f"《{data['book_info']['title']}》· 6位专家 · 3轮碰撞 · 基于互联网真实素材",
        "experts": build_experts(data),
        "rounds": build_rounds(data),
        "final_insight": data["rounds"][2]["insights"][0]["statement"],
        "open_questions": [
            "当\"完美报告\"的生产者是一个黑箱时，谁来为误判负责？这个责任问题，AI能否回答？",
            "金融市场的定价，表面上是数字的博弈——当AI接管了数字处理，谁来负责\"人性博弈\"的部分？",
            "那些能读懂\"语气、留白和不说的话\"的人，是否会成为AI时代最稀缺的人才？"
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Converted: {output_path}")


if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "content/AI生成叙事_金融定价_讨论.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "content/AI生成叙事_金融定价_v8.json"
    convert(input_path, output_path)
