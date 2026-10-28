import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[1]
ANNOTATIONS_DIR = BASE_DIR / "data" / "annotations"

MAIN_PATH = ANNOTATIONS_DIR / "annotated.jsonl"
TEMPLATE_PATH = ANNOTATIONS_DIR / "annotation_template.jsonl"
OUTPUT_PATH = ANNOTATIONS_DIR / "all_annotations_diff.txt"


def load_jsonl(path):
    records = {}

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            item = json.loads(line)
            article_id = item.get("original_id")

            if not article_id:
                raise ValueError(
                    f"original_id tidak ditemukan di {path.name}, "
                    f"baris {line_number}"
                )

            if article_id in records:
                raise ValueError(
                    f"ID duplikat {article_id} di {path.name}"
                )

            records[article_id] = item

    return records


def entity_key(entity):
    return (
        entity["start"],
        entity["end"],
        entity["label"],
    )


def format_entity(key, text):
    start, end, label = key
    span = text[start:end]

    return (
        f"{start}:{end} | {label:6} | "
        f"{span!r}"
    )


def main():
    main_data = load_jsonl(MAIN_PATH)
    template_data = load_jsonl(TEMPLATE_PATH)

    all_ids = sorted(set(main_data) | set(template_data))

    only_main_ids = set(main_data) - set(template_data)
    only_template_ids = set(template_data) - set(main_data)

    lines = [
        "LAPORAN PERBANDINGAN ANOTASI SELURUH DATASET",
        "Catatan: laporan ini hanya membaca data dan tidak "
        "mengubah dataset utama.",
        "",
        f"Jumlah artikel dataset utama: {len(main_data)}",
        f"Jumlah artikel template: {len(template_data)}",
        f"Artikel hanya di dataset utama: {len(only_main_ids)}",
        f"Artikel hanya di template: {len(only_template_ids)}",
        "",
    ]

    total_only_main = 0
    total_only_template = 0
    total_common = 0
    articles_with_diff = 0
    label_changes = 0
    boundary_changes = 0

    for article_id in all_ids:
        main_article = main_data.get(article_id)
        template_article = template_data.get(article_id)

        if main_article is None or template_article is None:
            continue

        main_entities = main_article.get("entities", [])
        template_entities = template_article.get("entities", [])

        main_keys = {entity_key(e) for e in main_entities}
        template_keys = {entity_key(e) for e in template_entities}

        only_main = sorted(main_keys - template_keys)
        only_template = sorted(template_keys - main_keys)
        common = main_keys & template_keys

        if not only_main and not only_template:
            continue

        articles_with_diff += 1
        total_only_main += len(only_main)
        total_only_template += len(only_template)
        total_common += len(common)

        # Periksa rentang sama tetapi label berbeda.
        template_by_span = {}
        for start, end, label in template_keys:
            template_by_span.setdefault((start, end), set()).add(label)

        main_by_span = {}
        for start, end, label in main_keys:
            main_by_span.setdefault((start, end), set()).add(label)

        article_label_changes = []
        for span in set(main_by_span) & set(template_by_span):
            main_labels = main_by_span[span]
            template_labels = template_by_span[span]

            if main_labels != template_labels:
                article_label_changes.append(
                    (span, main_labels, template_labels)
                )

        label_changes += len(article_label_changes)

        # Periksa entitas dengan label sama tetapi batas berbeda.
        main_by_label_text = {}
        template_by_label_text = {}

        for start, end, label in main_keys:
            text = main_article["text"][start:end]
            main_by_label_text.setdefault((label, text), set()).add(
                (start, end)
            )

        for start, end, label in template_keys:
            text = template_article["text"][start:end]
            template_by_label_text.setdefault((label, text), set()).add(
                (start, end)
            )

        article_boundary_changes = []
        for key in set(main_by_label_text) & set(template_by_label_text):
            main_spans = main_by_label_text[key]
            template_spans = template_by_label_text[key]

            if main_spans != template_spans:
                article_boundary_changes.append(
                    (key, main_spans, template_spans)
                )

        boundary_changes += len(article_boundary_changes)

        title = main_article.get("title", "(judul tidak tersedia)")

        lines.extend([
            "=" * 78,
            f"ID: {article_id}",
            f"Judul: {title}",
            f"Jumlah entitas utama: {len(main_entities)}",
            f"Jumlah entitas template: {len(template_entities)}",
            f"Hanya di dataset utama: {len(only_main)}",
            f"Hanya di template: {len(only_template)}",
            "",
            "--- HANYA DI DATASET UTAMA ---",
        ])

        if only_main:
            lines.extend(
                format_entity(key, main_article["text"])
                for key in only_main
            )
        else:
            lines.append("(tidak ada)")

        lines.extend(["", "--- HANYA DI TEMPLATE ---"])

        if only_template:
            lines.extend(
                format_entity(key, template_article["text"])
                for key in only_template
            )
        else:
            lines.append("(tidak ada)")

        lines.extend(["", "--- RENTANG SAMA, LABEL BERBEDA ---"])

        if article_label_changes:
            for span, main_labels, template_labels in article_label_changes:
                start, end = span
                text = main_article["text"][start:end]
                lines.append(
                    f"{start}:{end} | {text!r} | "
                    f"utama={sorted(main_labels)} | "
                    f"template={sorted(template_labels)}"
                )
        else:
            lines.append("(tidak terdeteksi)")

        lines.extend(["", "--- TEKS SAMA, BATAS BERBEDA ---"])

        if article_boundary_changes:
            for key, main_spans, template_spans in article_boundary_changes:
                label, text = key
                lines.append(
                    f"{label} | {text!r} | "
                    f"batas_utama={sorted(main_spans)} | "
                    f"batas_template={sorted(template_spans)}"
                )
        else:
            lines.append("(tidak terdeteksi)")

        lines.append("")

    lines.extend([
        "=" * 78,
        "RINGKASAN",
        f"Artikel dengan perbedaan anotasi: {articles_with_diff}",
        f"Entitas hanya di dataset utama: {total_only_main}",
        f"Entitas hanya di template: {total_only_template}",
        f"Rentang sama dengan perbedaan label: {label_changes}",
        f"Teks dan label sama dengan perbedaan batas: {boundary_changes}",
        "",
        "PERHATIAN:",
        "Perbedaan tidak otomatis berarti kesalahan.",
        "Template belum tentu merupakan anotasi final yang benar.",
        "Periksa konteks dan pedoman anotasi sebelum memperbaiki data.",
        "Dataset utama tidak diubah oleh skrip ini.",
    ])

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines[-12:]))
    print(f"\nLaporan lengkap disimpan di: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
