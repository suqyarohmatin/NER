from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotations" / "annotated.jsonl"


def read_jsonl(path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON tidak valid pada baris {line_no}: {e}")
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def main():
    if not ANN.exists():
        raise SystemExit(f"File tidak ditemukan: {ANN}. Tinjau annotation_template.jsonl lalu simpan sebagai annotated.jsonl.")
    rows = read_jsonl(ANN)
    errors, ids = [], set()
    for row in rows:
        line = row["_line_no"]
        text = row.get("text")
        if not isinstance(text, str) or not text:
            errors.append(f"baris {line}: text kosong/bukan string")
            continue
        if row.get("reviewed") is not True:
            errors.append(f"baris {line}: reviewed harus true setelah anotasi diperiksa manusia")
        oid = str(row.get("original_id", "")).strip()
        if not oid:
            errors.append(f"baris {line}: original_id kosong")
        elif oid in ids:
            errors.append(f"baris {line}: original_id duplikat {oid!r}")
        ids.add(oid)
        entities = row.get("entities", [])
        if not isinstance(entities, list):
            errors.append(f"baris {line}: entities harus berupa list")
            continue
        spans = []
        for ent in entities:
            try:
                start, end, label = int(ent["start"]), int(ent["end"]), str(ent["label"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"baris {line}: entitas harus memiliki start, end, label")
                continue
            if start < 0 or end <= start or end > len(text):
                errors.append(f"baris {line}: offset tidak valid {start}:{end} untuk teks panjang {len(text)}")
                continue
            if not text[start:end].strip():
                errors.append(f"baris {line}: span hanya spasi")
            if label not in {"PERSON", "ORG", "GPE", "LOC", "DATE", "EVENT"}:
                errors.append(f"baris {line}: label tidak dikenal {label!r}")
            if (start, end) in spans:
                errors.append(f"baris {line}: span duplikat {start}:{end}")
            spans.append((start, end))
    if errors:
        print("VALIDASI GAGAL:")
        for error in errors[:100]:
            print("-", error)
        raise SystemExit(f"Total kesalahan: {len(errors)}. Perbaiki file anotasi.")
    print(f"Validasi berhasil: {len(rows)} artikel, semua reviewed=true, offset valid.")
    print("Jumlah span:", sum(len(r.get("entities", [])) for r in rows))

if __name__ == "__main__":
    main()
