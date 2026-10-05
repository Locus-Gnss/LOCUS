import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Emoji detection regex covering standard emoji ranges
emoji_regex = re.compile(
    "[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]"
)

print("=== AUDITING EMOJIS IN SRC AND ROOT ===")
total_found = 0
for root, _, files in os.walk('src'):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                for idx, line in enumerate(fh, 1):
                    matches = emoji_regex.findall(line)
                    if matches:
                        total_found += len(matches)
                        repr_matches = [repr(m) for m in matches]
                        print(f"{p}:{idx}: {line.strip()[:100]} | Matches: {repr_matches}")

for f in ['dashboard.py']:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as fh:
            for idx, line in enumerate(fh, 1):
                matches = emoji_regex.findall(line)
                if matches:
                    total_found += len(matches)
                    print(f"{f}:{idx}: {line.strip()[:100]} | Matches: {[repr(m) for m in matches]}")

print(f"\nTotal emoji instances found: {total_found}")
