
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotations" / "annotated.jsonl"
OUTPUT = ROOT / "data" / "annotations" / "first_article_review.json"


def main():
    with ANN.open("r", encoding="utf-8") as file:
        rows = [json.loads(line) for line in file if line.strip()]

    if not rows:
        print("File anotasi kosong.")
        return

    article = rows[0]
    text = article["text"]

    # Hapus entitas yang jelas bukan entitas bernama.
    remove_spans = {
        (1116, 1121),  # daily
        (1139, 1145),  # weekly
        (1340, 1355),  # Aliran - Become
        (1373, 1378),  # Based
        (2251, 2259),  # each day
        (3890, 3893),  # NGO
    }

    corrected = []

    for ent in article["entities"]:
        start, end = ent["start"], ent["end"]
        label = ent["label"]
        entity_text = text[start:end]

        if (start, end) in remove_spans:
            continue

        # Perbaiki label yang jelas salah.
        if entity_text == "CIMB":
            label = "ORG"
        elif entity_text == "Aliran" and label == "GPE":
            label = "ORG"

        # Kasus hukum bukan nama orang secara keseluruhan.
        if entity_text == (
            "Ahmad Zahri bin Mirza Abdul Hamid v AIMS Cyberjaya Sdn Bhd"
        ):
            continue

        # Nama undang-undang dan perjanjian tidak dipaksakan
        # menjadi ORG dalam skema label proyek ini.
        if entity_text in {
            "the Industrial Relations Act 1967",
            "the International Covenant on Economic, Social and Cultural Rights",
            "the Convention on the Elimination of All Forms of Discrimination Against Women",
        }:
            continue

        corrected.append({
            "start": start,
            "end": end,
            "label": label
        })

    # Perbaiki nama organisasi yang terpecah atau terlalu panjang.
    replacements = [
        ("Persatuan Aliran Kesedaran Negara", "ORG"),
        ("Maybank", "ORG"),
    ]

    for phrase, label in replacements:
        start = text.find(phrase)
        if start == -1:
            print("Peringatan: teks tidak ditemukan:", phrase)
            continue

        end = start + len(phrase)

        # Hapus span lama yang bertumpang tindih dengan nama yang benar.
        corrected = [
            ent for ent in corrected
            if ent["end"] <= start or ent["start"] >= end
        ]

        corrected.append({
            "start": start,
            "end": end,
            "label": label
        })

    # Urutkan entitas berdasarkan posisi teks.
    corrected.sort(key=lambda ent: (ent["start"], ent["end"]))

    # Simpan hasil tinjauan secara terpisah.
    article["entities"] = corrected
    article["reviewed"] = False

    with OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False, indent=2)

    print("Hasil tinjauan tersimpan di:", OUTPUT)
    print("Jumlah entitas setelah perbaikan awal:", len(corrected))
    print("Status review tetap False.")
    print("File annotated.jsonl asli tidak diubah.")

def show_review():
    with OUTPUT.open("r", encoding="utf-8") as file:
        article = json.load(file)

    print("\nDAFTAR ENTITAS HASIL PERBAIKAN")
    print("=" * 50)

    for i, entity in enumerate(article["entities"], start=1):
        start = entity["start"]
        end = entity["end"]
        label = entity["label"]
        entity_text = article["text"][start:end]

        print(f"{i:02}. {label:6} | {entity_text!r}")


if __name__ == "__main__":
    main()
    show_review()