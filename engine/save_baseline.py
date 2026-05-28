import os, subprocess, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_COMMIT = '4fbf43d'
BASELINE_DIR = os.path.join(REPO, 'expert-library', 'experts-baseline')

def decode_git_path(raw: str) -> str:
    """Decode git octal-escaped path to proper UTF-8"""
    # Remove surrounding quotes if present
    raw = raw.strip().strip('"')
    # Replace octal escapes like \345\210\230 with actual bytes
    def repl(m):
        octals = m.group(0).split('\\')[1:]
        bytes_arr = bytes([int(o, 8) for o in octals])
        return bytes_arr.decode('utf-8')
    result = re.sub(r'(?:\\\d{3})+', repl, raw)
    return result

# Get raw binary output
result = subprocess.run(
    ['git', 'ls-tree', '-r', '--name-only', '-z', BASELINE_COMMIT, 'expert-library/experts/'],
    capture_output=True, cwd=REPO
)
# Split by null byte
raw_lines = result.stdout.split(b'\0')
files = []
for raw in raw_lines:
    raw_str = raw.decode('utf-8', errors='replace').strip()
    if raw_str and raw_str.endswith('.md'):
        decoded = decode_git_path(raw_str)
        files.append(decoded)

print(f"Found {len(files)} expert files in commit {BASELINE_COMMIT}")

count = 0
for f in files:
    content = subprocess.run(
        ['git', 'show', f'{BASELINE_COMMIT}:{f}'],
        capture_output=True, cwd=REPO
    )
    if content.returncode != 0 or not content.stdout.strip():
        print(f"  FAIL: {f}")
        continue

    rel_path = f.replace('expert-library/experts/', '', 1)
    target = os.path.join(BASELINE_DIR, rel_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'w', encoding='utf-8') as fh:
        fh.write(content.stdout.decode('utf-8', errors='replace'))
    count += 1

print(f"Saved {count} baseline expert files to: {BASELINE_DIR}")
