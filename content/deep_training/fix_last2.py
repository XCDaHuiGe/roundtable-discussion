# -*- coding: utf-8 -*-
"""Final manual fix for remaining 2 files."""
import json, glob

# round026: show ALL content around error
f1 = glob.glob('content/deep_training/round026_*.json')[0]
raw = open(f1, 'r', encoding='utf-8-sig').read()
lines = raw.split('\n')
print(f"round026: {len(lines)} lines")
print(f"Line 11: {repr(lines[10][:300])}")
print(f"Line 12: {repr(lines[11][:300])}")

# Find ALL ASCII double quotes in lines 10-13
for i in range(9, 14):
    if i < len(lines):
        for j, c in enumerate(lines[i]):
            if c == '"':
                print(f"  Quote at line {i+1}, col {j}")

# The error says line 11, col 54, pos 290
# Let me look at the hex at position 290
print(f"\nRaw chars 280-310: {repr(raw[280:310])}")
print(f"Hex: {' '.join(f'{ord(c):04x}' for c in raw[280:310])}")
