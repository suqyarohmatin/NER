
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotations" / "annotated.all.jsonl"


def main():
    with ANN.open("r", encoding="utf-8") as file:
        rows = [json.loads(line) for line in file if line.strip()]

    pending = [row for row in rows if row.get("reviewed") is not True]

    if not pending:
        print("Semua artikel sudah ditinjau.")
        return

    print(f"Jumlah artikel yang belum ditinjau: {len(pending)}")

    try:
        number = int(input("Pilih nomor artikel yang ingin diperiksa (1 = artikel pertama yang belum ditinjau): "))
        if number < 1 or number > len(pending):
            print("Nomor artikel tidak tersedia.")
            return
    except ValueError:
        print("Masukkan nomor berupa angka.")
        return

    article = pending[number - 1]
    text = article["text"]

    print("\n" + "=" * 60)
    print("PEMERIKSAAN ARTIKEL")
    print("=" * 60)
    print("Judul:", article.get("title", "(judul tidak tersedia)"))
    print("ID:", article.get("original_id"))
    print("Status review:", article.get("reviewed"))
    print("\nDaftar entitas:\n")

    for i, entity in enumerate(article.get("entities", []), start=1):
        start = entity["start"]
        end = entity["end"]
        label = entity["label"]
        print(f"{i:03}. {label:8} | {text[start:end]!r} (start={start}, end={end})")


if __name__ == "__main__":
    main()
