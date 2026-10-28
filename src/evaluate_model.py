from pathlib import Path
import argparse, json
import spacy
from metrics import detailed_metrics

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
REPORTS = ROOT / "reports"
MODEL = ROOT / "models" / "trained"


def load_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def predict(nlp, rows):
    gold_docs, pred_docs, errors = [], [], []
    for row in rows:
        text = row["text"]
        gold = [(int(e["start"]), int(e["end"]), str(e["label"])) for e in row.get("entities", [])]
        doc = nlp(text)
        pred = [(e.start_char, e.end_char, e.label_) for e in doc.ents]
        gold_docs.append(gold); pred_docs.append(pred)
        gold_set, pred_set = set(gold), set(pred)
        for start, end, label in sorted(pred_set - gold_set):
            errors.append({"original_id": row.get("original_id"), "kind": "false_positive", "text": text[start:end], "label": label, "start": start, "end": end})
        for start, end, label in sorted(gold_set - pred_set):
            errors.append({"original_id": row.get("original_id"), "kind": "false_negative", "text": text[start:end], "label": label, "start": start, "end": end})
    overall, per_label = detailed_metrics(gold_docs, pred_docs)
    return {"overall": overall, "per_label": per_label}, errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--split", choices=["validation", "test"], default="test")
    args = p.parse_args()
    data_path = SPLITS / f"{args.split}.jsonl"
    if not data_path.exists():
        raise SystemExit(f"Split tidak ditemukan: {data_path}")
    rows = load_rows(data_path)
    if not rows:
        raise SystemExit("Split kosong.")
    try:
        baseline = spacy.load("en_core_web_sm")
    except OSError:
        raise SystemExit("Model baseline belum terpasang.")
    if not MODEL.exists():
        raise SystemExit("Model terlatih belum ditemukan. Jalankan train_model.py dahulu.")
    trained = spacy.load(MODEL)
    baseline_metrics, baseline_errors = predict(baseline, rows)
    trained_metrics, trained_errors = predict(trained, rows)
    report = {
        "split": args.split,
        "documents": len(rows),
        "gold_spans": sum(len(r.get("entities", [])) for r in rows),
        "matching": "exact-span: start, end, and label must all match",
        "baseline_model": "en_core_web_sm",
        "baseline": baseline_metrics,
        "trained_model": str(MODEL),
        "trained": trained_metrics,
        "trained_errors_first_30": trained_errors[:30],
        "baseline_errors_first_30": baseline_errors[:30],
        "warning": "If this is the test split, do not use these results to tune the model. Human-reviewed gold labels are required."
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"evaluation_{args.split}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"split": args.split, "documents": len(rows), "baseline": baseline_metrics, "trained": trained_metrics, "report": str(out)}, indent=2, ensure_ascii=False))
    print("\nContoh kesalahan model terlatih (maksimal 10):")
    for e in trained_errors[:10]:
        print(e)

if __name__ == "__main__":
    main()
