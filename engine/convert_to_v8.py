# -*- coding: utf-8 -*-
"""V8 JSON 转换器：将讨论 JSON 转换为渲染器格式"""

import json
import os

EXPERT_COLORS = {
    "巴菲特": "#1a5f2a",
    "芒格": "#2d5a8e",
    "塔勒布": "#8a2a4a",
    "柯林斯": "#4a2d8a",
    "达利欧": "#8a6a2a",
    "吴军": "#2a6a6a",
    "沃伦·巴菲特": "#1a5f2a",
    "查理·芒格": "#2d5a8e",
    "纳西姆·塔勒布": "#8a2a4a",
    "吉姆·柯林斯": "#4a2d8a",
    "瑞·达利欧": "#8a6a2a",
    "吴军": "#2a6a6a",
}

EXPERT_PROFILES = {
    "巴菲特": {
        "core_belief": "买股票就是买公司，用合理价格买优秀企业比用便宜价格买普通企业好得多",
        "interest": "段永平是价值投资在中国最忠实的实践者，验证了巴菲特体系的跨文化可行性",
        "fear": "段永平的体系被机械模仿而非真正理解，最终在市场考验中失败",
        "bias": "倾向于认为段永平的成功是'认知胜利'而非'时代红利'"
    },
    "芒格": {
        "core_belief": "多元思维模型+逆向思维+长期视角=卓越投资决策",
        "interest": "段永平的'本分'哲学与芒格的伦理投资理念高度一致",
        "fear": "段永平的投资体系被过度简化为核心持仓清单，失去了哲学内核",
        "bias": "认为段永平的实业经验是其最大优势，容易忽视宏观环境的贡献"
    },
    "塔勒布": {
        "core_belief": "反脆弱性：有些事物能从冲击、不确定性和波动中获益",
        "interest": "段永平的集中持仓+长期持有策略在尾部风险面前极为脆弱",
        "fear": "段永平的成功建立在一系列不可能预测的'正面黑天鹅'之上",
        "bias": "系统性低估个体认知能力，倾向于认为'懂企业'是一种幻觉"
    },
    "柯林斯": {
        "core_belief": "卓越企业的共同特征是'第五级经理人'+飞轮效应+知道不做什么",
        "interest": "段永平用实证证明：知道自己不做什么，是比知道自己做什么更强大的竞争优势",
        "fear": "段永平的体系无法被普通人真正复制，因为它依赖特定的个人能力和资本条件",
        "bias": "倾向于用实证数据说话，但可能低估了'洞见'和'直觉'的价值"
    },
    "达利欧": {
        "core_belief": "经济是一台机器，理解债务周期和信贷机制是做出好决策的前提",
        "interest": "段永平的成功部分是'顺势而为'——美元强势、美国科技霸权、全球化的宏观背景",
        "fear": "未来20年宏观环境的剧变可能让过去30年的投资逻辑面临根本性挑战",
        "bias": "宏观视角可能导致低估个体企业家的能动性"
    },
    "吴军": {
        "core_belief": "科技发展以浪潮形式推进，顺势者昌逆势者亡；简单即是美",
        "interest": "段永平是中国第一个用实业思维做投资的实践者，具有划时代意义",
        "fear": "段永平的实业经验既是他的护城河，也是他的认知边界",
        "bias": "对中国市场的独特性可能过于乐观"
    }
}


def normalize_name(name: str) -> str:
    """统一专家名字"""
    mapping = {
        "沃伦·巴菲特": "巴菲特",
        "查理·芒格": "芒格",
        "纳西姆·塔勒布": "塔勒布",
        "吉姆·柯林斯": "柯林斯",
        "瑞·达利欧": "达利欧",
    }
    return mapping.get(name, name)


def build_experts(data: dict) -> list:
    """构建专家档案"""
    experts_list = []
    for e in data["experts"]:
        name = normalize_name(e["name"])
        profile = EXPERT_PROFILES.get(name, {
            "core_belief": "待填充",
            "interest": "待填充",
            "fear": "待填充",
            "bias": "待填充"
        })
        color = EXPERT_COLORS.get(name, "#333333")
        experts_list.append({
            "name": name,
            "title": e["role"],
            "avatar_color": color,
            **profile
        })
    return experts_list


def build_stances(round_data: dict) -> list:
    """构建立场"""
    return [
        {
            "expert": normalize_name(s["expert"]),
            "stance": s["content"],
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
            "attack_type": "逻辑漏洞",
            "attack_content": a["content"],
            "emotion": "serious",
            "counter_attack": None
        })
    return clashes


def build_reality_cases(syntheses: list) -> list:
    """从 Round 3 的 synthesis 构建案例"""
    cases = []
    case_map = {
        "段永平投资网易": {
            "case_name": "网易投资（2001-2009）",
            "case_source": "[来源：雪球投资分析](https://xueqiu.com/4136606186/361411928)",
            "case_content": "2001年互联网泡沫破裂，网易濒临退市，股价跌至0.25-1美元。段永平以0.8美元大举买入，最终获利超100倍，约20亿美元。",
            "case_outcome": "百倍回报，但过程极为痛苦——股价长期在1美元以下，多次濒临退市",
            "case_lesson": "逆向投资需要对自己判断的极度自信，以及足够深的'安全垫'——段永平懂游戏、懂管理层、懂商业模式"
        },
        "苹果持仓74%": {
            "case_name": "苹果持仓集中（2011至今）",
            "case_source": "[来源：阿怪分析](https://xueqiu.com/9081465327/361663212)",
            "case_content": "段永平在苹果持仓占组合74.33%，持仓市值超122亿美元。这是极度集中的投资，也是他最大的一次'押注'。",
            "case_outcome": "回报超20倍，但一旦苹果出现根本性危机，整个资产面临灭顶之灾",
            "case_lesson": "集中持仓的前提是'真懂'——段永平懂消费电子、懂乔布斯、懂生态系统"
        },
        "做空百度亏损2亿": {
            "case_name": "做空百度（教训）",
            "case_source": "[来源：阿怪分析](https://xueqiu.com/9081465327/361663212)",
            "case_content": "段永平曾做空百度，亏损约2亿美元。他坦言：'这是失去平常心的愚蠢行为。'这次教训让他定下'永远不做空'的铁律。",
            "case_outcome": "2亿美元亏损，但换来了一条价值连城的投资铁律",
            "case_lesson": "'不做空'不是因为胆小，而是因为理解了做空的非线性风险"
        }
    }
    for i, syn in enumerate(syntheses[:3]):
        case_name = list(case_map.keys())[i % len(case_map)]
        case = case_map[case_name]
        cases.append({**case, "case_content": case["case_content"] + f"\n\n{syn}"})
    return cases


def build_cost_discussion(round_data: dict) -> dict:
    """构建代价讨论"""
    return {
        "scenario": "如果普通人模仿段永平的集中持仓策略，会发生什么？",
        "cost_analysis": [
            {
                "cost": "资本不足导致无法加仓",
                "analysis": "段永平可以在股价下跌时持续加仓——他有足够的资本。普通人可能在第一个低点就用光了子弹，然后在下一次暴跌中被迫割肉。"
            },
            {
                "cost": "实业经验无法复制",
                "analysis": "段永平懂网易，是因为他做了20年游戏；懂苹果，是因为他在消费电子行业摸爬滚打。这种经验不是读几本书能学到的。"
            },
            {
                "cost": "心理承受能力不同",
                "analysis": "段永平说过：'为什么我能拿网易那么久，赚了那么多钱还不卖？因为那些钱对我来讲并不多。'当你亏的是孩子的学费、房子的首付，你的'理性'会瞬间崩溃。"
            }
        ],
        "worst_case": "普通人用杠杆或借来的钱'集中持仓'，在一次市场暴跌中爆仓——这不是价值投资，这是赌博。",
        "survivor_bias": "你只看到段永平的网易百倍回报，看不到同期有无数人用同样的方法重仓了雅虎、朗讯、WorldCom，血本无归。"
    }


def build_human_nature(syntheses: list) -> dict:
    """构建人性层"""
    return {
        "question": "为什么大多数人无法真正执行段永平的投资体系？",
        "psychological_analysis": "投资最大的敌人不是市场，而是我们自己。段永平的体系要求：1）极度理性；2）极度耐心；3）极度自知。这三件事，每一件都是反人性的。我们天生倾向于过度自信、频繁交易、追涨杀跌。更深层的问题是：'懂'是一种幻觉——我们以为我们懂了，但其实是认知偏误在起作用。",
        "real_examples": [
            "段永平在2001年买入网易时，市场上99%的人认为他是疯子——股价从70美元跌到0.25美元，你真的能拿住吗？",
            "巴菲特说过：'在别人恐惧时贪婪，在别人贪婪时恐惧'——这句话人人都知道，但执行起来需要的是对自己判断的绝对信心，而这种信心需要深刻的理解来支撑",
            "达利欧说'如果你不觉得一年前的自己是个蠢货，那说明你这年没学到什么东西'——但大多数人不愿意承认自己曾经愚蠢"
        ],
        "conclusion": "段永平的体系本质上是一套'认知-行为'系统：深度理解→坚定信念→持续行动。大多数人缺的不是知识，而是把知识转化为行动的认知深度。"
    }


def build_cognitive_upgrade(round_data: dict) -> dict:
    """构建认知升级"""
    return {
        "old_thinking": "段永平的方法很简单：买好公司，长期持有。普通人学他买苹果茅台就行。",
        "new_thinking": "段永平的方法极难复制：他用几十年实业经验建立了对特定行业的深度理解，然后在理解范围内极度专注。普通人需要找到自己的'实业经验'领域，而不是照抄持仓。",
        "complexity": "段永平的'简单'是几十年积累之后的返璞归真。对于刚起步的投资者，'简单'意味着先去积累实业经验、行业认知，而不是急着买股票。",
        "actionable_insight": "不要抄段永平的持仓，要学段永平的'不为清单'。把他不做什么列出来，然后问自己：我能做到吗？如果不能，就用指数基金。"
    }


def build_rounds(data: dict) -> list:
    """构建完整的轮次数据"""
    rounds = []

    # Round 1
    r1 = data["rounds"][0]
    rounds.append({
        "round_number": 1,
        "topic": "段永平投资哲学的底层逻辑是否站得住脚？",
        "core_question": "买股票就是买公司——这句话有1%的人真懂就了不起，做到就更难",
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
        "topic": "段永平投资体系的局限在哪里？",
        "core_question": "成功是认知的胜利还是时代的红利？实业经验是优势还是局限？",
        "stances": [],
        "clash_rounds": build_clash_rounds(r2),
        "reality_cases": [],
        "cost_discussion": {},
        "human_nature": {},
        "cognitive_upgrade": {}
    })

    # Round 3
    r3 = data["rounds"][2]
    syntheses = [s["content"] for s in r3.get("synthesis", [])]

    rounds.append({
        "round_number": 3,
        "topic": "段永平投资哲学对普通人的启示与局限",
        "core_question": "如何从段永平的成功中提取可执行的洞见，而不是机械模仿",
        "stances": [],
        "clash_rounds": [],
        "reality_cases": build_reality_cases(syntheses),
        "cost_discussion": build_cost_discussion(r3),
        "human_nature": build_human_nature(syntheses),
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
            "段永平能在泡泡玛特上复制他的成功吗？还是说他的实业经验边界到了消费娱乐领域就失效了？",
            "如果茅台的营收利润双降持续5年，段永平还会坚持'懂'茅台吗？还是说他的'懂'会变成'固执'？",
            "普通人能否找到一条介于'完全模仿段永平'和'全部买指数基金'之间的中间路径？"
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Converted: {output_path}")


if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "content/段永平投资问答语录_讨论.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "content/段永平投资问答语录_v8.json"
    convert(input_path, output_path)
