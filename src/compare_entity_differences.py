
import json
from pathlib import Path

review_path = Path("data/annotations/second_article_review.json")
main_path = Path("data/annotations/annotated.jsonl")
output_path = Path("data/annotations/second_article_entity_diff.txt")

review = json.loads(review_path.read_text(encoding="utf-8"))

main_article = None
with main_path.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        item = json.loads(line)
        if item.get("original_id") == review["original_id"]:
            main_article = item
            break

if main_article is None:
    raise SystemExit("Artikel tidak ditemukan di dataset utama.")

def entity_key(entity):
    return (
        entity["start"],
        entity["end"],
        entity["label"]
    )

main_entities = main_article.get("entities", [])
review_entities = review.get("entities", [])

main_keys = {entity_key(e) for e in main_entities}
review_keys = {entity_key(e) for e in review_entities}

only_main = sorted(main_keys - review_keys)
only_review = sorted(review_keys - main_keys)

def show_entity(key, text):
    start, end, label = key
    span = text[start:end]
    return (
        f"{start}:{end} | {label:6} | "
        f"{span!r} | valid_span={bool(span)}"
    )

lines = [
    "PERBANDINGAN ANOTASI ARTIKEL KEDUA",
    f"Judul: {review['title']}",
    f"Jumlah anotasi utama: {len(main_entities)}",
    f"Jumlah anotasi review: {len(review_entities)}",
    f"Hanya di dataset utama: {len(only_main)}",
    f"Hanya di file review: {len(only_review)}",
    "",
    "=== HANYA DI DATASET UTAMA ===",
]

lines.extend(
    show_entity(key, main_article["text"])
    for key in only_main
)

lines.extend(["", "=== HANYA DI FILE REVIEW ==="])

lines.extend(
    show_entity(key, review["text"])
    for key in only_review
)

output_path.write_text("\n".join(lines), encoding="utf-8")

print("\n".join(lines))
print(f"\nLaporan disimpan di: {output_path}")
print("\nDataset utama tidak diubah.")
