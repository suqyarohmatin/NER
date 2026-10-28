
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ANN = ROOT / "data" / "annotations" / "annotated.all.jsonl"
REVIEW = ROOT / "data" / "annotations" / "second_article_review.json"
BACKUP = ROOT / "data" / "annotations" / "annotated.all.backup.jsonl"


def main():
    if not REVIEW.exists():
        print("File second_article_review.json tidak ditemukan.")
        return

    with REVIEW.open("r", encoding="utf-8") as f:
        reviewed_article = json.load(f)

    print("Judul:", reviewed_article.get("title"))
    print("Jumlah entitas:", len(reviewed_article.get("entities", [])))
    print("Status:", reviewed_article.get("reviewed"))

    if not ANN.exists():
        print("Dataset annotated.all.jsonl tidak ditemukan.")
        return

    with ANN.open("r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    matches = [
        i for i, row in enumerate(rows)
        if row.get("original_id") == reviewed_article.get("original_id")
    ]

    if len(matches) != 1:
        print("ID artikel tidak ditemukan atau tidak unik.")
        print("Dataset tidak diubah.")
        return

    index = matches[0]
    original = rows[index]

    if original.get("text") != reviewed_article.get("text"):
        print("Teks artikel berbeda dari dataset utama.")
        print("Dataset tidak diubah.")
        return

    print("\nPastikan seluruh entitas dan posisi sudah diperiksa.")
    answer = input("Simpan artikel yang sudah direview? (ya/tidak): ")
    if answer.strip().lower() != "ya":
        print("Dibatalkan. Dataset tidak diubah.")
        return

    confirm = input(
        "Apakah anotasi benar-benar sudah diperiksa manusia? (ya/tidak): "
    )
    if confirm.strip().lower() != "ya":
        print("Dibatalkan. Status review tidak diubah.")
        return

    if not BACKUP.exists():
        shutil.copy2(ANN, BACKUP)

    reviewed_article["reviewed"] = True
    rows[index] = reviewed_article

    with ANN.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("\nArtikel kedua berhasil disimpan.")
    print("Cadangan:", BACKUP)


if __name__ == "__main__":
    main()
