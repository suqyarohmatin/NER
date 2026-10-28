
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotations" / "annotated.jsonl"
REVIEW = ROOT / "data" / "annotations" / "first_article_review.json"
BACKUP = ROOT / "data" / "annotations" / "annotated.backup.jsonl"


def main():
    with REVIEW.open("r", encoding="utf-8") as f:
        reviewed_article = json.load(f)

    print("Artikel:", reviewed_article["title"])
    print("Jumlah entitas:", len(reviewed_article["entities"]))
    print("Status saat ini:", reviewed_article["reviewed"])

    answer = input(
        "\nApakah semua entitas dan posisinya sudah kamu periksa? (ya/tidak): "
    ).strip().lower()

    if answer != "ya":
        print("Dibatalkan. Dataset utama tidak diubah.")
        return

    with ANN.open("r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    if not rows or rows[0].get("original_id") != reviewed_article.get("original_id"):
        print("ID artikel pertama tidak cocok. Dataset tidak diubah.")
        return

    # Pastikan teks artikel sama persis sebelum mengganti anotasinya.
    if rows[0].get("text") != reviewed_article.get("text"):
        print("Teks artikel berbeda. Dataset tidak diubah.")
        return

    # Buat cadangan sebelum memperbarui dataset utama.
    if not BACKUP.exists():
        shutil.copy2(ANN, BACKUP)

    # Status True hanya ditetapkan setelah pengguna mengonfirmasi review.
    reviewed_article["reviewed"] = True
    rows[0] = reviewed_article

    with ANN.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("\nArtikel pertama berhasil diperbarui.")
    print("Cadangan:", BACKUP)
    print("Artikel lain tetap dipertahankan.")


if __name__ == "__main__":
    main()
