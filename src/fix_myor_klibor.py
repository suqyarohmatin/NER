import json
import shutil
from datetime import datetime
from pathlib import Path

path = Path("data/annotations/annotated.all.jsonl")
target_title = "UOB Malaysia, RHB Banking and Maybank execute landmark MYOR-based transaction - Newswav"

targets = {
    (55, 59), (967, 971), (1118, 1122), (1531, 1535),
    (1974, 1978), (2310, 2314), (2469, 2475), (2479, 2483),
    (2701, 2705), (2971, 2975), (3153, 3157), (3432, 3436),
    (3503, 3507), (3727, 3731),
}

with path.open("r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

matches = [a for a in records if a.get("title", "").strip() == target_title]

if len(matches) != 1:
    raise SystemExit(
        f"DIBATALKAN: artikel dengan judul persis ditemukan {len(matches)}."
    )

article = matches[0]
text = article.get("text", "")
found = []

for entity in article.get("entities", []):
    span = (entity.get("start"), entity.get("end"))
    if span in targets:
        mention = text[span[0]:span[1]].upper()
        if mention not in {"MYOR", "KLIBOR"}:
            raise SystemExit(f"DIBATALKAN: teks tidak cocok pada {span}.")
        if entity.get("label") not in {"GPE", "ORG"}:
            raise SystemExit(f"DIBATALKAN: label tidak sesuai pada {span}.")
        found.append(entity)

if len(found) != 14 or {(e["start"], e["end"]) for e in found} != targets:
    raise SystemExit(f"DIBATALKAN: hanya cocok {len(found)} dari 14 target.")

backup = path.with_name(
    f"annotated.all.backup_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
)
shutil.copy2(path, backup)

article["entities"] = [
    e for e in article["entities"]
    if (e.get("start"), e.get("end")) not in targets
]
article["reviewed"] = False

temp = path.with_suffix(".tmp")
with temp.open("w", encoding="utf-8", newline="\n") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

temp.replace(path)

print("BERHASIL")
print("Anotasi dihapus: 14")
print("Status reviewed:", article["reviewed"])
print("Cadangan:", backup)
print("Anotasi tersisa:", len(article["entities"]))
