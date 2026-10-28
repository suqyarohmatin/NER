import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotations" / "annotated.jsonl"
OUT = ROOT / "data" / "annotations" / "second_article_review.json"

# Format: (posisi_awal, posisi_akhir, label, teks_yang_diharapkan)
ENTITIES = [
    (0, 12, "ORG", "UOB Malaysia"),
    (14, 25, "ORG", "RHB Banking"),
    (30, 37, "ORG", "Maybank"),
    (78, 91, "GPE", "PETALING JAYA"),
    (93, 105, "ORG", "UOB Malaysia"),
    (107, 124, "ORG", "RHB Banking Group"),
    (129, 144, "ORG", "Malayan Banking"),
    (146, 153, "ORG", "Maybank"),
    (183, 191, "GPE", "Malaysia"),
    (415, 427, "ORG", "UOB Malaysia"),
    (446, 449, "ORG", "RHB"),
    (454, 461, "ORG", "Maybank"),
    (515, 523, "GPE", "Malaysia"),
    (932, 940, "GPE", "Malaysia"),
    (1202, 1213, "ORG", "UOB Malayia"),
    (1260, 1275, "PERSON", "Christina Cheah"),
    (1383, 1395, "ORG", "UOB Malaysia"),
    (1397, 1400, "ORG", "RHB"),
    (1405, 1412, "ORG", "Maybank"),
    (1710, 1722, "ORG", "UOB Malaysia"),
    (2139, 2156, "ORG", "RHB Banking Group"),
    (2193, 2213, "PERSON", "Nurjesmi Mohd Nashir"),
    (2378, 2386, "GPE", "Malaysia"),
    (2590, 2593, "ORG", "RHB"),
    (2621, 2641, "ORG", "Bank Negara Malaysia"),
    (2766, 2774, "GPE", "Malaysia"),
    (2797, 2808, "PERSON", "Farid Kairi"),
    (2892, 2899, "ORG", "Maybank"),
    (3307, 3327, "ORG", "Bank Negara Malaysia"),
    (3345, 3353, "GPE", "Malaysia"),
    (3390, 3410, "ORG", "Bank Negara Malaysia"),
    (3430, 3444, "DATE", "September 2021"),
    (3448, 3456, "GPE", "Malaysia"),
    (3729, 3737, "GPE", "Malaysia"),
    (3827, 3836, "GPE", "Singapore"),
    (3838, 3843, "GPE", "Japan"),
    (3845, 3856, "GPE", "Switzerland"),
    (3858, 3875, "GPE", "the United States"),
    (3880, 3898, "GPE", "the United Kingdom"),
]


def main():
    with ANN.open("r", encoding="utf-8") as file:
        rows = [json.loads(line) for line in file if line.strip()]

    if len(rows) < 2:
        raise ValueError("Dataset tidak memiliki artikel kedua.")

    article = rows[1]
    text = article["text"]

    if not text.startswith(
        "UOB Malaysia, RHB Banking and Maybank execute landmark MYOR-based transaction"
    ):
        raise ValueError(
            "Artikel kedua tidak sesuai dengan artikel Maybank yang diharapkan. "
            "File keluaran tidak dibuat."
        )

    corrected = []

    for start, end, label, expected_text in ENTITIES:
        actual_text = text[start:end]

        if actual_text != expected_text:
            raise ValueError(
                f"Validasi gagal pada posisi {start}:{end}. "
                f"Teks yang diharapkan: {expected_text!r}; "
                f"teks aktual: {actual_text!r}. "
                "File keluaran tidak diperbarui."
            )

        corrected.append({
            "start": start,
            "end": end,
            "label": label
        })

    # Pastikan tidak ada anotasi yang bertumpuk.
    corrected.sort(key=lambda item: (item["start"], item["end"]))

    for previous, current in zip(corrected, corrected[1:]):
        if current["start"] < previous["end"]:
            raise ValueError(
                f"Anotasi bertumpuk: {previous} dan {current}. "
                "File keluaran tidak diperbarui."
            )

    result = dict(article)
    result["reviewed"] = False
    result["entities"] = corrected

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("Calon anotasi artikel kedua berhasil dibuat.")
    print("File:", OUT)
    print("Jumlah entitas:", len(corrected))
    print("Status reviewed:", result["reviewed"])
    print("Dataset utama belum diubah.")


if __name__ == "__main__":
    main()