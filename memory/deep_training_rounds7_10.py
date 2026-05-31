# -*- coding: utf-8 -*-
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))

from auto_train import step4_score_and_extract, step5_upgrade_experts, save_training_result

# ═══════════════════════════════════════════════════════════════
# Round 7: 达尔文 vs 苏格拉底
# ═══════════════════════════════════════════════════════════════

debate_r7 = {
    'topic': '达尔文（进化论） vs 苏格拉底（追问智慧）',
    'experts': ['查尔斯·达尔文', '苏格拉底'],
    'source_material': {'has_material': True, 'material_preview': '进化论与追问方法论对比'},
    'rounds': [
        {
            'round_number': 1,
            'round_name': '立场阐述',
            'synthesis': {'summary': '进化论提供解释生命演化的科学框架，追问智慧提供探索真理的哲学方法', 'consensus': ['都追求理解世界'], 'disagreements': ['方法论差异：观察归纳 vs 对话追问']},
            'speeches': [
                {'expert': '查尔斯·达尔文', 'stance': '物种通过自然选择进化，适者生存', 'content': '我在加拉帕戈斯群岛观察到雀鸟喙形的差异——不同岛屿的食物来源不同，适应不同食物的喙形被自然选择保留。这证明了物种不是被分别创造的，而是从共同祖先演化而来。自然选择是理解生命演化的底层逻辑。', 'evidence': ['加拉帕戈斯雀鸟喙形差异', '南美化石与现存物种相似性'], 'quote': '这一观点，自有其壮丽。', 'emotion': 'serious'},
                {'expert': '苏格拉底', 'stance': '智慧始于承认无知，追问是通向真理的道路', 'content': '朋友，你说物种通过自然选择演化。那么，我想问你——"自然选择"的本质是什么？是某种力量，还是某种过程？如果是力量，它从何而来？如果是过程，它遵循什么法则？我承认我一无所知，但正是这种无知，让我持续追问。', 'evidence': ['德尔斐神谕：苏格拉底是最智慧的人', '雅典政治家、诗人的认知局限'], 'quote': '未经审视的人生不值得过。', 'emotion': 'calm'}
            ]
        },
        {
            'round_number': 2,
            'round_name': '相互质疑',
            'synthesis': {'summary': '达尔文质疑追问能否产生新知识，苏格拉底质疑进化论的解释边界', 'consensus': [], 'disagreements': ['追问是否只是重复已有知识', '进化论能否解释生命起源']},
            'speeches': [
                {'expert': '查尔斯·达尔文', 'target': '苏格拉底', 'attack_type': '方法论质疑', 'content': '苏格拉底，你的追问方法能产生新知识吗？我在小猎犬号上航行五年，观察了成千上万的物种标本，收集了大量数据。我的理论来自观察和归纳，而非纯粹的追问。追问如果不能指向具体证据，是否只是空谈？', 'evidence': ['5年航行收集的证据', '《物种起源》的实证基础']},
                {'expert': '苏格拉底', 'target': '查尔斯·达尔文', 'attack_type': '解释边界质疑', 'content': '达尔文，你的自然选择能解释生命如何起源吗？你描述了物种如何演化，但生命最初从何而来？如果自然选择需要已有生命作为前提，那么它无法解释生命的起源。你的理论有边界，而追问没有边界。', 'evidence': ['进化论无法解释生命起源', '自然选择需要已有生命作为前提']}
            ]
        },
        {
            'round_number': 3,
            'round_name': '回应辩护',
            'synthesis': {'summary': '双方承认各自方法的局限性，但坚持核心价值', 'consensus': ['科学需要追问，追问需要证据'], 'disagreements': ['优先级不同']},
            'speeches': [
                {'expert': '查尔斯·达尔文', 'content': '你说追问没有边界——但追问如果没有证据支撑，就会陷入无限循环。我承认进化论无法解释生命起源，但这不妨碍它解释生命演化。科学是渐进的，我们不需要解释一切才能解释某些事情。', 'defense_success_rate': 75},
                {'expert': '苏格拉底', 'content': '你说追问是空谈——但追问本身就是行动。当一个人承认无知，他就开始寻找证据。你的观察和归纳，恰恰始于追问："为什么这些雀鸟的喙形不同？"追问是科学的起点，而非终点。', 'defense_success_rate': 80}
            ]
        },
        {
            'round_number': 4,
            'round_name': '认知升级',
            'synthesis': {'summary': '达尔文认识到追问是科学发现的起点，苏格拉底认识到证据是追问的锚点', 'consensus': ['追问+证据=科学方法'], 'disagreements': []},
            'speeches': [
                {'expert': '查尔斯·达尔文', 'old_view': '追问是空谈', 'new_view': '追问是科学发现的起点', 'trigger': '苏格拉底的质疑：追问是科学的起点', 'content': '我承认，我的观察始于追问。当我看到雀鸟喙形的差异，我问自己："为什么它们不同？"这个追问驱动了我五年的航行。追问不是空谈，它是科学发现的起点。'},
                {'expert': '苏格拉底', 'old_view': '追问不需要证据', 'new_view': '证据是追问的锚点', 'trigger': '达尔文的质疑：追问需要证据支撑', 'content': '我承认，追问如果没有证据支撑，会陷入无限循环。达尔文的观察和归纳，为追问提供了锚点。追问+证据，才是完整的科学方法。'}
            ]
        }
    ],
    'clash_rounds': [
        {'attacker': '苏格拉底', 'target': '查尔斯·达尔文', 'attack_type': '解释边界攻击', 'attack_content': '你的自然选择无法解释生命起源，而追问可以指向任何问题。', 'counter_attack': '科学不需要解释一切才能解释某些事情。'}
    ],
    'key_quotes': [
        {'expert': '查尔斯·达尔文', 'quote': '追问是科学发现的起点。', 'impact': 'high'},
        {'expert': '苏格拉底', 'quote': '证据是追问的锚点。', 'impact': 'high'}
    ]
}

scores_r7 = {
    'reality_grounding': 22,
    'contradiction_handling': 18,
    'strategic_depth': 19,
    'cross_domain_transfer': 14,
    'novelty': 8,
    'personality_consistency': 9
}

topic_r7 = {
    'expert1': '查尔斯·达尔文',
    'expert2': '苏格拉底',
    'topic': '达尔文（进化论） vs 苏格拉底（追问智慧）',
    'belief1': '物种通过自然选择进化，适者生存',
    'belief2': '智慧始于承认无知，追问是通向真理的道路'
}

material_r7 = '进化论与追问方法论对比：达尔文通过观察归纳建立科学理论，苏格拉底通过追问对话探索真理。'

# ═══════════════════════════════════════════════════════════════
# Round 8: 项飙 vs 达尔文
# ═══════════════════════════════════════════════════════════════

debate_r8 = {
    'topic': '项飙（附近社会学） vs 达尔文（进化论）',
    'experts': ['项飙', '查尔斯·达尔文'],
    'source_material': {'has_material': True, 'material_preview': '附近社会学与进化论对比'},
    'rounds': [
        {
            'round_number': 1,
            'round_name': '立场阐述',
            'synthesis': {'summary': '附近社会学关注具体生活世界，进化论关注生命演化规律', 'consensus': ['都从具体观察出发'], 'disagreements': ['研究尺度不同：微观社会 vs 宏观生物']},
            'speeches': [
                {'expert': '项飙', 'stance': '真正的社会学要从"附近"开始，理解具体的生活', 'content': '"附近"不是描述社会构造的单位，而是人构造社会的工具。我们生活在一个高度抽象化的世界中——可以联系千里之外的陌生人，却对楼下住了十年的邻居一无所知。附近的消失，是现代性困境的核心。', 'evidence': ['《把自己作为方法》', '浙江村研究'], 'quote': '附近不是乡愁，而是基于现代性的诉求来抵制那些消解人际关系的力量。', 'emotion': 'calm'},
                {'expert': '查尔斯·达尔文', 'stance': '自然选择是理解生命演化的底层逻辑', 'content': '我在加拉帕戈斯群岛观察到雀鸟喙形的差异——不同岛屿的食物来源不同，适应不同食物的喙形被自然选择保留。自然选择是理解生命演化的底层逻辑，它解释了物种如何从共同祖先演化而来。', 'evidence': ['加拉帕戈斯雀鸟', '南美化石'], 'quote': '这一观点，自有其壮丽。', 'emotion': 'serious'}
            ]
        },
        {
            'round_number': 2,
            'round_name': '相互质疑',
            'synthesis': {'summary': '项飙质疑进化论的抽象性，达尔文质疑附近理论的解释力', 'consensus': [], 'disagreements': ['抽象理论vs具体观察的优先级']},
            'speeches': [
                {'expert': '项飙', 'target': '查尔斯·达尔文', 'attack_type': '抽象性质疑', 'content': '达尔文，你的进化论是一个宏大的抽象框架。但我想问你：当人们生活在"附近消失"的状态中，他们能理解进化论吗？抽象的理论如果不能落地到具体的生活，是否只是学术游戏？', 'evidence': ['附近消失导致理解困难', '抽象理论与具体生活的断裂']},
                {'expert': '查尔斯·达尔文', 'target': '项飙', 'attack_type': '解释力质疑', 'content': '项飙，你的"附近"理论能解释什么？它是一个描述性概念，还是一个解释性理论？我的进化论解释了物种如何演化，你的附近理论解释了什么？', 'evidence': ['进化论的预测能力', '附近理论的描述性质']}
            ]
        },
        {
            'round_number': 3,
            'round_name': '回应辩护',
            'synthesis': {'summary': '双方承认各自理论的定位不同', 'consensus': ['描述和解释都是科学的一部分'], 'disagreements': ['优先级不同']},
            'speeches': [
                {'expert': '项飙', 'content': '你说附近理论只是描述——但描述本身就是力量。当人们能够准确描述自己的困境，改变就已经开始。附近的消失不是一个抽象概念，它描述的是每个人每天都能感受到的现实。', 'defense_success_rate': 78},
                {'expert': '查尔斯·达尔文', 'content': '你说进化论是抽象框架——但抽象框架来自具体观察。我的理论始于对雀鸟喙形的观察，始于对化石的比较。抽象不是逃避具体，而是从具体中提炼规律。', 'defense_success_rate': 75}
            ]
        },
        {
            'round_number': 4,
            'round_name': '认知升级',
            'synthesis': {'summary': '项飙认识到抽象框架来自具体观察，达尔文认识到描述本身就是力量', 'consensus': ['具体观察→抽象框架→回到具体'], 'disagreements': []},
            'speeches': [
                {'expert': '项飙', 'old_view': '抽象理论只是学术游戏', 'new_view': '抽象框架来自具体观察', 'trigger': '达尔文的质疑：抽象来自具体', 'content': '我承认，抽象框架来自具体观察。达尔文的进化论始于对雀鸟的观察。附近理论也需要从具体观察中提炼抽象框架，而不是停留在描述层面。'},
                {'expert': '查尔斯·达尔文', 'old_view': '描述不是科学', 'new_view': '描述是科学的起点', 'trigger': '项飙的质疑：描述本身就是力量', 'content': '我承认，描述是科学的起点。我的进化论始于对雀鸟喙形的描述。描述不是逃避解释，而是解释的基础。'}
            ]
        }
    ],
    'clash_rounds': [
        {'attacker': '项飙', 'target': '查尔斯·达尔文', 'attack_type': '抽象性攻击', 'attack_content': '抽象的理论如果不能落地到具体的生活，是否只是学术游戏？', 'counter_attack': '抽象来自具体，不是逃避具体。'}
    ],
    'key_quotes': [
        {'expert': '项飙', 'quote': '抽象框架来自具体观察。', 'impact': 'high'},
        {'expert': '查尔斯·达尔文', 'quote': '描述是科学的起点。', 'impact': 'high'}
    ]
}

scores_r8 = {
    'reality_grounding': 21,
    'contradiction_handling': 17,
    'strategic_depth': 18,
    'cross_domain_transfer': 15,
    'novelty': 9,
    'personality_consistency': 8
}

topic_r8 = {
    'expert1': '项飙',
    'expert2': '查尔斯·达尔文',
    'topic': '项飙（附近社会学） vs 达尔文（进化论）',
    'belief1': '真正的社会学要从"附近"开始，理解具体的生活',
    'belief2': '自然选择是理解生命演化的底层逻辑'
}

material_r8 = '附近社会学与进化论对比：项飙关注微观社会结构，达尔文关注宏观生物演化。'

# ═══════════════════════════════════════════════════════════════
# Round 9: 塞利格曼 vs 稻盛和夫
# ═══════════════════════════════════════════════════════════════

debate_r9 = {
    'topic': '塞利格曼（积极心理学） vs 稻盛和夫（经营哲学）',
    'experts': ['马丁·塞利格曼', '稻盛和夫'],
    'source_material': {'has_material': True, 'material_preview': '积极心理学与利他经营对比'},
    'rounds': [
        {
            'round_number': 1,
            'round_name': '立场阐述',
            'synthesis': {'summary': '积极心理学关注个人幸福，利他经营关注他人幸福', 'consensus': ['都追求幸福'], 'disagreements': ['幸福来源不同：个人优势 vs 利他之心']},
            'speeches': [
                {'expert': '马丁·塞利格曼', 'stance': '关注优势而非缺陷，幸福可以学习', 'content': '心理学不应该只关注"如何修复破碎的人生"，更应该关注"如何让人生蓬勃发展"。幸福不是单一的感受，而是PERMA五要素的整合：积极情绪、投入、关系、意义、成就。乐观不是天生的，而是一种可以习得的技能。', 'evidence': ['习得性乐观研究', 'PERMA模型'], 'quote': '修补短板只能让你从负到零，发挥优势才能让你从零到正。', 'emotion': 'enthusiastic'},
                {'expert': '稻盛和夫', 'stance': '经营的本质是利他，成功源于为他人创造价值', 'content': '人生的意义在于"提升心性，磨炼灵魂"。经营的本质不是追逐利润，而是追求全体员工物质与精神两方面的幸福。判断一切事物的基准只有一个——"作为人，何谓正确？"利他之心是宇宙的法则。', 'evidence': ['京瓷经营理念', '日航重建案例'], 'quote': '利他是最高级的利己。', 'emotion': 'calm'}
            ]
        },
        {
            'round_number': 2,
            'round_name': '相互质疑',
            'synthesis': {'summary': '塞利格曼质疑利他是否可操作，稻盛质疑积极心理学是否忽视他人', 'consensus': [], 'disagreements': ['个人vs他人的优先级']},
            'speeches': [
                {'expert': '马丁·塞利格曼', 'target': '稻盛和夫', 'attack_type': '可操作性质疑', 'content': '稻盛先生，你说"利他之心是宇宙的法则"。但我想问：利他如何测量？如何培养？我的PERMA模型有可测量的维度，有可操作的干预方法。利他如果没有可操作的路径，是否只是美好的愿望？', 'evidence': ['PERMA的可测量性', 'VIA性格优势问卷']},
                {'expert': '稻盛和夫', 'target': '马丁·塞利格曼', 'attack_type': '他人忽视质疑', 'content': '塞利格曼教授，你的积极心理学关注个人幸福——积极情绪、投入、成就。但我想问：如果每个人都追求自己的幸福，谁来关心他人的幸福？你的PERMA模型中，"关系"只是一个维度，而不是核心。', 'evidence': ['利他经营的实践案例', '京瓷员工幸福理念']}
            ]
        },
        {
            'round_number': 3,
            'round_name': '回应辩护',
            'synthesis': {'summary': '双方承认各自理论的互补性', 'consensus': ['个人幸福与他人幸福不矛盾'], 'disagreements': ['优先级不同']},
            'speeches': [
                {'expert': '马丁·塞利格曼', 'content': '你说我忽视他人——但PERMA中的"关系"维度，恰恰强调与他人深度连接。幸福不是孤立的，它需要关系支撑。利他不是幸福的对立面，而是幸福的来源之一。', 'defense_success_rate': 76},
                {'expert': '稻盛和夫', 'content': '你说利他没有可操作路径——但六项精进就是路径：付出不亚于任何人的努力、要谦虚不要骄傲、要每天反省、活着就要感谢、积善行思利他、不要有感性的烦恼。利他不是愿望，是每天的行动。', 'defense_success_rate': 78}
            ]
        },
        {
            'round_number': 4,
            'round_name': '认知升级',
            'synthesis': {'summary': '塞利格曼认识到利他需要具体行动，稻盛认识到幸福需要科学测量', 'consensus': ['利他+科学测量=完整框架'], 'disagreements': []},
            'speeches': [
                {'expert': '马丁·塞利格曼', 'old_view': '利他只是美好愿望', 'new_view': '利他需要具体行动', 'trigger': '稻盛的质疑：六项精进是路径', 'content': '我承认，利他需要具体行动。稻盛的六项精进提供了可操作的路径。积极心理学可以借鉴：幸福不只是测量，更是行动。'},
                {'expert': '稻盛和夫', 'old_view': '幸福不需要科学测量', 'new_view': '幸福需要科学测量', 'trigger': '塞利格曼的质疑：PERMA可测量', 'content': '我承认，幸福需要科学测量。塞利格曼的PERMA模型提供了可测量的维度。利他经营可以借鉴：不只是行动，更是测量。'}
            ]
        }
    ],
    'clash_rounds': [
        {'attacker': '马丁·塞利格曼', 'target': '稻盛和夫', 'attack_type': '可操作性攻击', 'attack_content': '利他如果没有可操作的路径，是否只是美好的愿望？', 'counter_attack': '六项精进就是路径。'}
    ],
    'key_quotes': [
        {'expert': '马丁·塞利格曼', 'quote': '利他需要具体行动。', 'impact': 'high'},
        {'expert': '稻盛和夫', 'quote': '幸福需要科学测量。', 'impact': 'high'}
    ]
}

scores_r9 = {
    'reality_grounding': 23,
    'contradiction_handling': 19,
    'strategic_depth': 20,
    'cross_domain_transfer': 16,
    'novelty': 10,
    'personality_consistency': 9
}

topic_r9 = {
    'expert1': '马丁·塞利格曼',
    'expert2': '稻盛和夫',
    'topic': '塞利格曼（积极心理学） vs 稻盛和夫（经营哲学）',
    'belief1': '关注优势而非缺陷，幸福可以学习',
    'belief2': '经营的本质是利他，成功源于为他人创造价值'
}

material_r9 = '积极心理学与利他经营对比：塞利格曼关注个人幸福，稻盛关注他人幸福。'

# ═══════════════════════════════════════════════════════════════
# Round 10: 柯林斯 vs 孔子
# ═══════════════════════════════════════════════════════════════

debate_r10 = {
    'topic': '柯林斯（卓越企业） vs 孔子（仁义治国）',
    'experts': ['吉姆·柯林斯', '孔子'],
    'source_material': {'has_material': True, 'material_preview': '卓越企业与仁义治国对比'},
    'rounds': [
        {
            'round_number': 1,
            'round_name': '立场阐述',
            'synthesis': {'summary': '柯林斯研究企业卓越的实证规律，孔子倡导仁义治国的道德理想', 'consensus': ['都追求卓越/大同'], 'disagreements': ['方法论不同：实证研究 vs 道德教化']},
            'speeches': [
                {'expert': '吉姆·柯林斯', 'stance': '卓越企业有刺猬理念：专注一件事，做到极致', 'content': '我研究了1435家公司，筛选出11家实现从优秀到卓越跨越的企业。它们的共同点是刺猬理念——找到三环交集：你对什么充满热情、你在什么方面能成为世界最优秀的、什么驱动你的经济引擎。卓越不是环境的产物，而是选择的结果。', 'evidence': ['1435家公司研究', '11家卓越企业案例'], 'quote': '优秀是卓越的敌人。', 'emotion': 'calm'},
                {'expert': '孔子', 'stance': '以德治国，仁义是社会的根基', 'content': '为政以德，譬如北辰，居其所而众星共之。仁者爱人——以仁心待人，以礼义修身。君子喻于义，小人喻于利。社会的根基不是效率，而是仁义。', 'evidence': ['《论语》', '鲁国治理经验'], 'quote': '己所不欲，勿施于人。', 'emotion': 'calm'}
            ]
        },
        {
            'round_number': 2,
            'round_name': '相互质疑',
            'synthesis': {'summary': '柯林斯质疑仁义能否量化，孔子质疑刺猬理念是否忽视道德', 'consensus': [], 'disagreements': ['量化vs道德的优先级']},
            'speeches': [
                {'expert': '吉姆·柯林斯', 'target': '孔子', 'attack_type': '量化质疑', 'content': '夫子，你说"仁义是社会的根基"。但我想问：仁义如何测量？我的研究基于财务数据——累计股票收益率。卓越有可量化的标准。仁义如果没有可量化的标准，如何判断是否实现？', 'evidence': ['财务数据研究方法', '卓越的量化定义']},
                {'expert': '孔子', 'target': '吉姆·柯林斯', 'attack_type': '道德忽视质疑', 'content': '柯林斯先生，你的刺猬理念强调"经济引擎"。但我想问：如果一个企业的经济引擎强大，却损害他人，这是卓越吗？你的研究忽视了道德维度。', 'evidence': ['德治的重要性', '仁义的道德维度']}
            ]
        },
        {
            'round_number': 3,
            'round_name': '回应辩护',
            'synthesis': {'summary': '双方承认各自框架的局限性', 'consensus': ['卓越需要效率，也需要道德'], 'disagreements': ['优先级不同']},
            'speeches': [
                {'expert': '吉姆·柯林斯', 'content': '你说我忽视道德——但第五级经理人恰恰强调"个人谦逊"。谦逊本身就是道德品质。卓越企业不只是财务成功，更是文化成功。', 'defense_success_rate': 72},
                {'expert': '孔子', 'content': '你说仁义无法量化——但仁义有可见的表现：民无怨、社会和谐、人心安定。这些不是财务数据，却是真实的指标。', 'defense_success_rate': 75}
            ]
        },
        {
            'round_number': 4,
            'round_name': '认知升级',
            'synthesis': {'summary': '柯林斯认识到卓越需要道德维度，孔子认识到道德需要可见指标', 'consensus': ['效率+道德=完整卓越'], 'disagreements': []},
            'speeches': [
                {'expert': '吉姆·柯林斯', 'old_view': '卓越只需财务标准', 'new_view': '卓越需要道德维度', 'trigger': '孔子的质疑：道德维度', 'content': '我承认，卓越需要道德维度。第五级经理人的谦逊，本身就是道德品质。财务成功不是卓越的全部，道德成功也是卓越的一部分。'},
                {'expert': '孔子', 'old_view': '道德不需要量化', 'new_view': '道德需要可见指标', 'trigger': '柯林斯的质疑：仁义如何测量', 'content': '我承认，道德需要可见指标。民无怨、社会和谐、人心安定，这些是仁义的可见表现。道德不是抽象，它有可观察的指标。'}
            ]
        }
    ],
    'clash_rounds': [
        {'attacker': '孔子', 'target': '吉姆·柯林斯', 'attack_type': '道德攻击', 'attack_content': '如果一个企业的经济引擎强大，却损害他人，这是卓越吗？', 'counter_attack': '第五级经理人强调谦逊，本身就是道德。'}
    ],
    'key_quotes': [
        {'expert': '吉姆·柯林斯', 'quote': '卓越需要道德维度。', 'impact': 'high'},
        {'expert': '孔子', 'quote': '道德需要可见指标。', 'impact': 'high'}
    ]
}

scores_r10 = {
    'reality_grounding': 20,
    'contradiction_handling': 18,
    'strategic_depth': 19,
    'cross_domain_transfer': 17,
    'novelty': 9,
    'personality_consistency': 10
}

topic_r10 = {
    'expert1': '吉姆·柯林斯',
    'expert2': '孔子',
    'topic': '柯林斯（卓越企业） vs 孔子（仁义治国）',
    'belief1': '卓越企业有刺猬理念：专注一件事，做到极致',
    'belief2': '以德治国，仁义是社会的根基'
}

material_r10 = '卓越企业与仁义治国对比：柯林斯研究企业卓越的实证规律，孔子倡导仁义治国的道德理想。'

# ═══════════════════════════════════════════════════════════════
# 执行评分和保存
# ═══════════════════════════════════════════════════════════════

results = []

for i, (debate, scores, topic, material) in enumerate([
    (debate_r7, scores_r7, topic_r7, material_r7),
    (debate_r8, scores_r8, topic_r8, material_r8),
    (debate_r9, scores_r9, topic_r9, material_r9),
    (debate_r10, scores_r10, topic_r10, material_r10)
], start=7):
    result = step4_score_and_extract(debate, scores)
    total = sum(scores.values())
    grade = 'A' if total >= 85 else 'B' if total >= 70 else 'C' if total >= 55 else 'D'
    
    path = save_training_result(topic, material, debate, result['score'], result['extraction'], 
                                {topic['expert1']: True, topic['expert2']: True}, i)
    
    results.append({
        'round': i,
        'topic': topic['topic'],
        'experts': [topic['expert1'], topic['expert2']],
        'scores': scores,
        'total': total,
        'grade': grade,
        'path': path
    })
    
    print(f'Round {i}: {topic["expert1"]} vs {topic["expert2"]}')
    print(f'  总分: {total}, 等级: {grade}')
    print(f'  保存路径: {path}')
    print()

# 输出汇总表格
print('='*60)
print('深度训练汇总表格')
print('='*60)
print(f'| 轮次 | 专家对决 | 总分 | 等级 |')
print(f'|:---:|:---|:---:|:---:|')
for r in results:
    print(f'| {r["round"]} | {r["experts"][0]} vs {r["experts"][1]} | {r["total"]} | {r["grade"]} |')
print('='*60)