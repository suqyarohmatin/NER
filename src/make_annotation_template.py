from pathlib import Path
import argparse
import json
import re

import pandas as pd
import spacy

ROOT = Path(__file__).resolve().parents[1]
CLEAN_CSV = ROOT / "data" / "processed" / "articles_clean.csv"
OUT = ROOT / "data" / "annotations" / "annotation_template.jsonl"

SUPPORTED_LANGUAGES = {"en", "eng", "english", "en-us", "en-gb"}
MAX_BODY_LENGTH = 10000


def normalize_text(value):
    """Menormalkan teks untuk membantu mendeteksi duplikasi."""
    value = str(value or "").lower().strip()
    return re.sub(r"\s+", " ", value)


def main():
    parser = argparse.ArgumentParser(
        description="Buat template anotasi NER dengan saran entitas dari spaCy."
    )
    parser.add_argument(
        "--n",
        type=int,
        default=100,
        help="Jumlah maksimal artikel untuk template."
    )
    args = parser.parse_args()

    if args.n < 1:
        raise SystemExit("Jumlah artikel (--n) harus minimal 1.")

    if not CLEAN_CSV.exists():
        raise SystemExit(
            "File data bersih tidak ditemukan. "
            "Jalankan python .\\src\\prepare_data.py terlebih dahulu."
        )

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise SystemExit(
            "Model spaCy belum terpasang. Jalankan: "
            "python -m spacy download en_core_web_sm"
        )

    df = pd.read_csv(
        CLEAN_CSV,
        dtype=str,
        keep_default_na=False
    )

    required_columns = {"language_norm", "title", "body", "original_id"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise SystemExit(
            f"Kolom wajib tidak ditemukan: {', '.join(sorted(missing_columns))}. "
            "Periksa kembali hasil prepare_data.py."
        )

    # 1. Pilih artikel berbahasa Inggris.
    english = df[
        df["language_norm"].str.strip().str.lower().isin(SUPPORTED_LANGUAGES)
    ].copy()

    # 2. Bersihkan spasi pada judul dan isi.
    english["title"] = english["title"].fillna("").astype(str).str.strip()
    english["body"] = english["body"].fillna("").astype(str).str.strip()

    # 3. Hitung panjang isi artikel.
    english["body_length"] = english["body"].str.len()

    # 4. Keluarkan artikel yang tidak mempunyai judul/isi
    #    atau isi lebih dari 10.000 karakter.
    eligible = english[
        (english["title"] != "")
        & (english["body_length"] > 0)
        & (english["body_length"] <= MAX_BODY_LENGTH)
    ].copy()

    # 5. Hilangkan duplikasi berdasarkan original_id yang tidak kosong.
    has_id = eligible["original_id"].str.strip() != ""
    with_id = eligible[has_id].drop_duplicates(
        subset=["original_id"],
        keep="first"
    )
    without_id = eligible[~has_id]

    eligible = pd.concat(
        [with_id, without_id],
        ignore_index=True
    )

    # 6. Hilangkan duplikasi berdasarkan gabungan judul dan isi.
    #    Artikel dengan judul sama tetapi isi berbeda tetap dipertahankan.
    eligible["_normalized_title"] = eligible["title"].map(normalize_text)
    eligible["_normalized_body"] = eligible["body"].map(normalize_text)

    eligible = eligible.drop_duplicates(
        subset=["_normalized_title", "_normalized_body"],
        keep="first"
    ).copy()

    # Pertahankan urutan awal dataset.
    # Ambil maksimal sebanyak yang diminta.
    selected = eligible.head(args.n)

    if selected.empty:
        raise SystemExit(
            "Tidak ditemukan artikel yang memenuhi kriteria. "
            "Periksa bahasa, judul, isi, dan batas panjang artikel."
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    # 7. Buat saran entitas spaCy dan simpan ke JSONL.
    with OUT.open("w", encoding="utf-8") as f:
        for _, row in selected.iterrows():
            title = row["title"]
            body = row["body"]
            text = f"{title}\n{body}"

            suggestions = []

            # spaCy memiliki batas panjang teks. Untuk data yang melebihi
            # batas model, proses per bagian agar tidak terjadi error.
            max_chunk_length = nlp.max_length - 100

            for chunk_start in range(0, len(text), max_chunk_length):
                chunk = text[
                    chunk_start:chunk_start + max_chunk_length
                ]

                doc = nlp(chunk)

                
                allowed_labels = {"PERSON", "ORG", "GPE", "LOC", "DATE", "EVENT"}

                for ent in doc.ents:
                    if ent.label_ not in allowed_labels:
                        continue

                    suggestions.append({
                        "start": chunk_start + ent.start_char,
                        "end": chunk_start + ent.end_char,
                        "label": ent.label_
                    })
            obj = {
                "original_id": str(row.get("original_id", "")),
                "source_name": str(row.get("source_name", "")),
                "file_sumber": str(row.get("file_sumber", "")),
                "language": str(row.get("language_norm", "")),
                "title": title,
                "body": body,
                "text": text,
                "entities": suggestions,
                "reviewed": False
            }

            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count += 1

    print("Template anotasi berhasil dibuat.")
    print(f"Jumlah artikel bahasa Inggris awal: {len(english)}")
    print(f"Artikel setelah filter panjang: {len(eligible)}")
    print(f"Jumlah artikel dalam template: {count}")
    print(f"Lokasi file: {OUT}")
    print(
        "PENTING: entitas dari spaCy hanya saran awal. "
        "Periksa label, offset, entitas yang terlewat, dan entitas yang keliru "
        "sebelum mengubah reviewed menjadi true."
    )


if __name__ == "__main__":
    main()
