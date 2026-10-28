import json
from pathlib import Path

review_path = Path("data/annotations/second_article_review.json")
main_path = Path("data/annotations/annotated.jsonl")

review = json.loads(review_path.read_text(encoding="utf-8"))

print("ID artikel review:", review["original_id"])
print("Status review:", review["reviewed"])

if not main_path.exists():
    print("\nFile annotated.jsonl belum ditemukan.")
else:
    found = False

    with main_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue

            item = json.loads(line)

            if item.get("original_id") == review["original_id"]:
                found = True
                print("\nArtikel ditemukan di dataset utama.")
                print("Nomor baris:", line_no)
                print("Judul sama:", item.get("title") == review.get("title"))
                print("Teks sama:", item.get("text") == review.get("text"))
                print("Jumlah entitas utama:", len(item.get("entities", [])))
                print("Jumlah entitas review:", len(review.get("entities", [])))
                print("Status reviewed utama:", item.get("reviewed"))
                break

    if not found:
        print("\nArtikel ini belum ditemukan di dataset utama.")
