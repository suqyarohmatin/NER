
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "annotations" / "second_article_review.json"

ALLOWED_LABELS = {
    "PERSON", "ORG", "GPE", "LOC", "DATE", "EVENT"
}


def main():
    with FILE.open("r", encoding="utf-8") as f:
        article = json.load(f)

    text = article["text"]
    entities = article["entities"]

    print("=" * 60)
    print("PEMERIKSAAN ANOTASI ARTIKEL KEDUA")
    print("=" * 60)

    print("Judul:", article["title"])
    print("Panjang teks:", len(text))
    print(
        "Panjang title + body:",
        len(article["title"] + "\n" + article["body"])
    )
    print(
        "Teks konsisten:",
        text == article["title"] + "\n" + article["body"]
    )
    print("Status review:", article["reviewed"])

    errors = []
    seen = set()
    ordered = sorted(
        entities,
        key=lambda e: (e["start"], e["end"])
    )

    for i, entity in enumerate(entities, 1):
        start = entity.get("start")
        end = entity.get("end")
        label = entity.get("label")

        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"Entitas {i}: posisi bukan bilangan bulat")
            continue

        if start < 0 or end <= start or end > len(text):
            errors.append(f"Entitas {i}: posisi tidak valid")
            continue

        if label not in ALLOWED_LABELS:
            errors.append(f"Entitas {i}: label tidak dikenal")

        key = (start, end, label)
        if key in seen:
            errors.append(f"Entitas {i}: duplikat")
        seen.add(key)

    for previous, current in zip(ordered, ordered[1:]):
        if current["start"] < previous["end"]:
            errors.append(
                "Tumpang tindih: "
                f"{text[previous['start']:previous['end']]!r} "
                "dan "
                f"{text[current['start']:current['end']]!r}"
            )

    print("\n--- Pemeriksaan struktur ---")
    if errors:
        for error in errors:
            print("PERLU DIPERBAIKI:", error)
    else:
        print("Struktur anotasi: OK")

    print("\n--- Daftar anotasi ---")
    for i, entity in enumerate(ordered, 1):
        value = text[entity["start"]:entity["end"]]
        print(
            f"{i:02}. {entity['label']:6} "
            f"{entity['start']}:{entity['end']} | {value!r}"
        )

    print("\n--- Jumlah per label ---")
    counts = Counter(e["label"] for e in entities)
    for label in sorted(ALLOWED_LABELS):
        print(f"{label:6}: {counts[label]}")

    print("\n--- Pemeriksaan frasa penting ---")
    review_phrases = [
        "Malaysia Overnight Rate",
        "MYOR",
        "KLIBOR",
        "UOB Malayia",
        "UOB Malaysia",
        "RHB Banking",
        "Malayan Banking",
        "Maybank",
        "Christina Cheah",
        "Nurjesmi Mohd Nashir",
        "Farid Kairi",
        "Bank Negara Malaysia",
        "September 2021",
        "Singapore",
        "Japan",
        "Switzerland",
        "the United States",
        "the United Kingdom",
    ]

    for phrase in review_phrases:
        start = 0
        found = False

        while True:
            start = text.find(phrase, start)
            if start == -1:
                break

            found = True
            end = start + len(phrase)

            exact = [
                e for e in entities
                if e["start"] == start
                and e["end"] == end
            ]

            if exact:
                status = ", ".join(e["label"] for e in exact)
                print(f"{phrase!r} {start}:{end} -> ADA ({status})")
            else:
                print(f"{phrase!r} {start}:{end} -> PERLU DITINJAU")

            start = end

        if not found:
            print(f"{phrase!r} -> Tidak ditemukan dalam teks")

    print("\nStatus review tetap:", article["reviewed"])
    print("Dataset utama tidak diubah.")


if __name__ == "__main__":
    main()
