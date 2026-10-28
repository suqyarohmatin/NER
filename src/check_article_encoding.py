import json
from pathlib import Path

p = Path("data/annotations/second_article_review.json")
a = json.loads(p.read_text(encoding="utf-8"))

print("Panjang teks:", len(a["text"]))
print("Jumlah entitas:", len(a["entities"]))
print("Status review:", a["reviewed"])

print("\n--- 500 karakter terakhir ---")
print(repr(a["text"][-500:]))

print("\n--- Pemeriksaan kecocokan teks ---")
print("text = title + newline + body:",
      a["text"] == a["title"] + "\n" + a["body"])

print("\n--- Pemeriksaan karakter mencurigakan ---")
for s in ("â€™", "â€œ", "â€", "�"):
    print(repr(s), ":", a["text"].count(s))
