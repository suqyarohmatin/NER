from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
REQUIRED = ["original_id", "source_name", "title", "body", "language", "entities"]


def clean_cell(value):
    if pd.isna(value):
        return value
    value = str(value).strip()
    # CSV export in this dataset may prefix values with a literal apostrophe.
    if value.startswith("'"):
        value = value[1:]
    return value.strip()


def main():
    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        raise SystemExit(f"Tidak ada CSV ditemukan di {RAW_DIR}. Masukkan file CSV ke folder itu.")

    frames, file_audit = [], []
    for path in files:
        try:
            frame = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str, on_bad_lines="warn")
        except UnicodeDecodeError:
            frame = pd.read_csv(path, sep=";", encoding="latin-1", dtype=str, on_bad_lines="warn")
        frame.columns = [str(c).strip().strip('"').replace("\ufeff", "") for c in frame.columns]
        missing_cols = [c for c in REQUIRED if c not in frame.columns]
        if missing_cols:
            print(f"PERINGATAN {path.name}: kolom tidak ditemukan: {missing_cols}")
            for col in missing_cols:
                frame[col] = pd.NA
        frame["file_sumber"] = path.name
        file_audit.append({"file": path.name, "rows_loaded": int(len(frame)), "columns": list(frame.columns)})
        frames.append(frame)
        print(f"Dibaca: {path.name}: {len(frame)} baris")

    all_df = pd.concat(frames, ignore_index=True, sort=False)
    for col in all_df.select_dtypes(include="object").columns:
        all_df[col] = all_df[col].map(clean_cell)

    initial_rows = len(all_df)
    exact_duplicate_rows = int(all_df.duplicated().sum())
    missing_title_before = int((all_df["title"].isna() | all_df["title"].fillna("").str.strip().eq("")).sum())
    missing_body_before = int((all_df["body"].isna() | all_df["body"].fillna("").str.strip().eq("")).sum())
    missing_id = int((all_df["original_id"].isna() | all_df["original_id"].fillna("").str.strip().eq("")).sum())

    # Remove exact duplicate rows first, then duplicate article identities.
    all_df = all_df.drop_duplicates().copy()
    exact_rows_removed = initial_rows - len(all_df)
    duplicate_ids = int(all_df["original_id"].notna().sum() - all_df.loc[all_df["original_id"].notna(), "original_id"].nunique())
    with_id = all_df[all_df["original_id"].notna() & all_df["original_id"].astype(str).str.strip().ne("")].copy()
    without_id = all_df[~(all_df["original_id"].notna() & all_df["original_id"].astype(str).str.strip().ne(""))].copy()
    with_id = with_id.drop_duplicates(subset=["original_id"], keep="first")
    all_df = pd.concat([with_id, without_id], ignore_index=True, sort=False)

    # Rows without title/body are excluded from modeling but their counts are recorded.
    valid = all_df["title"].fillna("").str.strip().ne("") & all_df["body"].fillna("").str.strip().ne("")
    invalid_rows_removed = int((~valid).sum())
    clean_df = all_df.loc[valid].copy().reset_index(drop=True)
    clean_df["language_norm"] = clean_df["language"].fillna("").str.lower().str.strip()
    clean_df["text"] = clean_df["title"].fillna("").astype(str) + "\n" + clean_df["body"].fillna("").astype(str)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "articles_clean.csv"
    clean_df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    language_counts = clean_df["language_norm"].replace("", "(kosong)").value_counts(dropna=False).to_dict()
    audit = {
        "files": file_audit,
        "files_found": len(files),
        "rows_loaded_total": int(initial_rows),
        "exact_duplicate_rows_detected": exact_duplicate_rows,
        "exact_duplicate_rows_removed": int(exact_rows_removed),
        "duplicate_original_id_rows_detected_after_exact_dedup": int(duplicate_ids),
        "missing_title_rows_before_dedup": int(missing_title_before),
        "missing_body_rows_before_dedup": int(missing_body_before),
        "missing_original_id_rows_before_dedup": int(missing_id),
        "rows_removed_missing_title_or_body": int(invalid_rows_removed),
        "clean_rows_for_modeling": int(len(clean_df)),
        "language_distribution": {str(k): int(v) for k, v in language_counts.items()},
        "output_csv": str(out_csv),
        "deduplication_policy": "exact duplicate rows removed, then keep first row for each non-empty original_id; rows without original_id retained unless exact duplicate",
        "apostrophe_policy": "remove one leading apostrophe from string values if present"
    }
    (REPORT_DIR / "data_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== RINGKASAN AUDIT ===")
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    print("\nCatatan: cek manual kebijakan deduplikasi dan laporan bahasa sebelum membuat anotasi.")

if __name__ == "__main__":
    main()
