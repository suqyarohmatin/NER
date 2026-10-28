from pathlib import Path
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_DIR = ROOT / "data" / "annotations"
MAIN_FILE = ANNOTATION_DIR / "annotated.jsonl"
TEMPLATE_FILE = ANNOTATION_DIR / "annotation_template.jsonl"
OUTPUT_FILE = ANNOTATION_DIR / "audit_report.txt"
ALLOWED_LABELS = {"PERSON", "ORG", "GPE", "LOC", "DATE", "EVENT"}


def read_jsonl(path):
    rows = []
    errors = []
    if not path.exists():
        return rows, [f"File tidak ditemukan: {path}"]

    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            if not raw_line.strip():
                errors.append(f"Baris {line_no}: baris kosong")
                continue
            try:
                row = json.loads(raw_line)
                if not isinstance(row, dict):
                    errors.append(f"Baris {line_no}: satu baris JSON harus berupa object")
                    continue
                row["_audit_line"] = line_no
                rows.append(row)
            except json.JSONDecodeError as exc:
                errors.append(f"Baris {line_no}: JSON tidak valid: {exc}")
    return rows, errors


def audit_file(path):
    rows, errors = read_jsonl(path)
    issues = []
    ids = []
    label_counts = Counter()
    reviewed_counts = Counter()
    total_entities = 0
    articles_with_entities = 0
    articles_missing_entities = 0
    offset_issues = 0
    unknown_label_issues = 0
    duplicate_span_issues = 0
    text_consistency_issues = 0

    for row in rows:
        line = row.get("_audit_line", "?")
        text = row.get("text")
        title = row.get("title")
        body = row.get("body")
        reviewed = row.get("reviewed", None)
        reviewed_counts[str(reviewed)] += 1

        oid = str(row.get("original_id", "")).strip()
        if not oid:
            issues.append(f"Baris {line}: original_id kosong")
        else:
            ids.append(oid)

        if not isinstance(text, str) or not text:
            issues.append(f"Baris {line}: text kosong atau bukan string")
            text = ""
        if isinstance(title, str) and isinstance(body, str):
            expected = title + "\n" + body
            if text != expected:
                text_consistency_issues += 1
                issues.append(f"Baris {line}: text tidak sama dengan title + newline + body")

        entities = row.get("entities", [])
        if not isinstance(entities, list):
            issues.append(f"Baris {line}: entities bukan list")
            continue
        if entities:
            articles_with_entities += 1
        else:
            articles_missing_entities += 1

        seen_spans = set()
        for index, ent in enumerate(entities, start=1):
            total_entities += 1
            if not isinstance(ent, dict):
                issues.append(f"Baris {line}, entitas {index}: format bukan object")
                continue
            try:
                start = int(ent["start"])
                end = int(ent["end"])
                label = str(ent["label"])
            except (KeyError, TypeError, ValueError):
                issues.append(f"Baris {line}, entitas {index}: harus memiliki start, end, label")
                continue

            label_counts[label] += 1
            if start < 0 or end <= start or end > len(text):
                offset_issues += 1
                issues.append(
                    f"Baris {line}, entitas {index}: offset tidak valid {start}:{end} "
                    f"(panjang teks {len(text)})"
                )
                continue

            span = text[start:end]
            if not span.strip():
                offset_issues += 1
                issues.append(f"Baris {line}, entitas {index}: span hanya berisi spasi")
            if label not in ALLOWED_LABELS:
                unknown_label_issues += 1
                issues.append(
                    f"Baris {line}, entitas {index}: label tidak dikenal {label!r}; "
                    f"span={span!r}"
                )
            key = (start, end)
            if key in seen_spans:
                duplicate_span_issues += 1
                issues.append(
                    f"Baris {line}, entitas {index}: span duplikat {start}:{end} "
                    f"({span!r})"
                )
            seen_spans.add(key)

    duplicate_ids = [oid for oid, count in Counter(ids).items() if count > 1]
    for oid in duplicate_ids:
        issues.append(f"original_id duplikat: {oid}")

    summary = {
        "file": str(path.relative_to(ROOT)),
        "rows": len(rows),
        "json_errors": len(errors),
        "unique_ids": len(set(ids)),
        "duplicate_ids": len(duplicate_ids),
        "reviewed_true": reviewed_counts.get("True", 0),
        "reviewed_false": reviewed_counts.get("False", 0),
        "reviewed_missing_or_other": len(rows) - reviewed_counts.get("True", 0) - reviewed_counts.get("False", 0),
        "total_entities": total_entities,
        "articles_with_entities": articles_with_entities,
        "articles_without_entities": articles_missing_entities,
        "offset_issues": offset_issues,
        "unknown_label_issues": unknown_label_issues,
        "duplicate_span_issues": duplicate_span_issues,
        "text_consistency_issues": text_consistency_issues,
        "label_counts": label_counts,
        "issues": issues,
        "read_errors": errors,
    }
    return summary


def render_summary(summary):
    lines = [
        f"FILE: {summary['file']}",
        f"Jumlah baris/artikel terbaca: {summary['rows']}",
        f"Kesalahan JSON/baris kosong: {summary['json_errors']}",
        f"ID unik: {summary['unique_ids']}",
        f"ID duplikat: {summary['duplicate_ids']}",
        f"reviewed=True: {summary['reviewed_true']}",
        f"reviewed=False: {summary['reviewed_false']}",
        f"reviewed hilang/nilai lain: {summary['reviewed_missing_or_other']}",
        f"Total entitas: {summary['total_entities']}",
        f"Artikel dengan entitas: {summary['articles_with_entities']}",
        f"Artikel tanpa entitas: {summary['articles_without_entities']}",
        f"Masalah offset/span: {summary['offset_issues']}",
        f"Label tidak dikenal: {summary['unknown_label_issues']}",
        f"Span duplikat: {summary['duplicate_span_issues']}",
        f"Ketidaksesuaian text vs title + newline + body: {summary['text_consistency_issues']}",
        "Jumlah per label:",
    ]
    if summary["label_counts"]:
        for label, count in sorted(summary["label_counts"].items()):
            lines.append(f"  - {label}: {count}")
    else:
        lines.append("  - (belum ada entitas)")

    all_issues = summary["read_errors"] + summary["issues"]
    lines.append(f"Total temuan pemeriksaan teknis: {len(all_issues)}")
    if all_issues:
        lines.append("Rincian temuan (maksimal 300):")
        lines.extend(f"  - {item}" for item in all_issues[:300])
        if len(all_issues) > 300:
            lines.append(f"  ... {len(all_issues) - 300} temuan lain tidak ditampilkan.")
    else:
        lines.append("Tidak ada masalah teknis yang ditemukan pada pemeriksaan ini.")
    return "\n".join(lines)


def main():
    if not MAIN_FILE.exists():
        print(f"File utama tidak ditemukan: {MAIN_FILE}")
        print("Pastikan script disimpan di folder src proyek, lalu jalankan lagi.")
        raise SystemExit(1)

    main_summary = audit_file(MAIN_FILE)
    report_parts = [
        "LAPORAN AUDIT READ-ONLY — MAYBANK NER SERVICE",
        "Catatan: script ini hanya membaca file; tidak mengubah anotasi atau status reviewed.",
        "",
        render_summary(main_summary),
    ]

    if TEMPLATE_FILE.exists():
        template_summary = audit_file(TEMPLATE_FILE)
        report_parts += [
            "",
            "=" * 70,
            "PERBANDINGAN RINGKAS DENGAN TEMPLATE",
            render_summary(template_summary),
        ]
        if main_summary["rows"] != template_summary["rows"]:
            report_parts.append(
                f"PERINGATAN: jumlah baris berbeda "
                f"(annotated={main_summary['rows']}, template={template_summary['rows']})."
            )
        if main_summary["unique_ids"] != template_summary["unique_ids"]:
            report_parts.append(
                f"CATATAN: jumlah ID unik berbeda "
                f"(annotated={main_summary['unique_ids']}, template={template_summary['unique_ids']})."
            )

    report = "\n".join(report_parts) + "\n"
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nLaporan disimpan di: {OUTPUT_FILE}")
    print("Dataset utama tidak diubah. Laporan audit ditulis ke file terpisah.")


if __name__ == "__main__":
    main()
