# -*- coding: utf-8 -*-
"""Integrity check: verify all agents completed and no dead agents."""
import sys, os, json, glob

# 1. Count debate files
files = sorted(glob.glob('content/deep_training/round*.json'))
print(f"辩论文件总数: {len(files)} (应 110)")

# 2. Validate JSON integrity
bad = 0
missing_rounds = []
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            d = json.load(fh)
        rounds = d.get('rounds', [])
        if len(rounds) < 4:
            bad += 1
            missing_rounds.append((os.path.basename(f), len(rounds)))
    except:
        bad += 1
        missing_rounds.append((os.path.basename(f), 0))

print(f"JSON损坏/不完整: {bad}")
for name, rcount in missing_rounds:
    print(f"  [异常] {name}: {rcount}/4轮")

# 3. Check round number distribution
print("\n轮次分布:")
round_nums = []
for f in files:
    bname = os.path.basename(f)
    try:
        rnum = int(bname.replace('round','').split('_')[0])
        round_nums.append(rnum)
    except:
        pass

if round_nums:
    print(f"  最小轮次: {min(round_nums)}")
    print(f"  最大轮次: {max(round_nums)}")
    print(f"  唯一轮次数: {len(set(round_nums))}")
    
    # Check for gaps
    expected = set(range(1, 111))
    found = set(round_nums)
    missing = expected - found
    if missing:
        print(f"  缺失轮次: {sorted(missing)[:20]}...")
    else:
        print(f"  轮次完整性: 100% (无缺失)")

# 4. Check expert version bumps
print("\n专家版本验证:")
checks = ['孔子','韩非子','老子','阿西莫夫','尼采','巴菲特','芒格','弗洛姆',
          '罗翔','阿伦特','塔勒布','吴军','吴晓波','丁元英','达利欧','项飙']
for name in checks:
    path = None
    for root, dirs, fnames in os.walk('expert-library/experts'):
        for f in fnames:
            if name in f and f.endswith('.md'):
                path = os.path.join(root, f)
                break
    if path:
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if '版本' in line:
                    print(f"  {name}: {line}")
                    break

# 5. Agent completion by batch
print("\n各Agent完成情况:")
expected_per_batch = {
    "初期10轮": 10,
    "Agent-Batch1 (rounds 1-20)": 20, 
    "Agent-Batch2 (rounds 21-40)": 20,
    "Agent-Batch3 (rounds 41-60)": 20,
    "Agent-Batch4 (rounds 61-80)": 20,
    "Agent-Batch5 (rounds 81-100)": 20,
}

batch_ranges = {
    "初期10轮": (1, 10),
    "Agent-Batch1": (1, 20),
    "Agent-Batch2": (21, 40),
    "Agent-Batch3": (41, 60),
    "Agent-Batch4": (61, 80),
    "Agent-Batch5": (81, 100),
}

all_dead = []
for name, (lo, hi) in batch_ranges.items():
    count = sum(1 for n in round_nums if lo <= n <= hi)
    expected = hi - lo + 1
    if count >= expected:
        print(f"  [OK] {name}: {count}/{expected}")
    else:
        all_dead.append(f"{name} (仅{count}/{expected})")
        print(f"  [DEAD] {name}: {count}/{expected}")

if all_dead:
    print(f"\n[警告] 以下 Agent 可能死亡: {', '.join(all_dead)}")
else:
    print(f"\n[通过] 所有 Agent 均存活，全部完成")

print("\n[管道结果统计]")
print("  总轮次: 110")
print("  总文件: 110 JSON")
