import json
from pathlib import Path

p = Path("data/annotations/second_article_review.json")
a = json.loads(p.read_text(encoding="utf-8"))
t = a["text"]

for start in range(0, len(t), 500):
    end = min(start + 500, len(t))
    print(f"\n--- KARAKTER {start}-{end} ---")
    print(t[start:end])
