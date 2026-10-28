from pathlib import Path
import argparse, json, random, time
import spacy
from spacy.training import Example
from metrics import detailed_metrics

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
MODEL_OUT = ROOT / "models" / "trained"


def load_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_examples(nlp, rows):
    examples = []
    for row in rows:
        text = row["text"]
        entities = [(int(e["start"]), int(e["end"]), str(e["label"])) for e in row.get("entities", [])]
        doc = nlp.make_doc(text)
        # Reject offsets that do not align to token boundaries rather than silently corrupting labels.
        for start, end, label in entities:
            if doc.char_span(start, end, label=label, alignment_mode="strict") is None:
                raise ValueError(f"Span tidak sejajar token pada original_id={row.get('original_id')}: {start}:{end} {label} -> {text[start:end]!r}")
        examples.append(Example.from_dict(doc, {"entities": entities}))
    return examples


def evaluate(nlp, rows):
    gold_docs, pred_docs = [], []
    for row in rows:
        doc = nlp(row["text"])
        gold_docs.append([(int(e["start"]), int(e["end"]), str(e["label"])) for e in row.get("entities", [])])
        pred_docs.append([(e.start_char, e.end_char, e.label_) for e in doc.ents])
    return detailed_metrics(gold_docs, pred_docs)[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dropout", type=float, default=0.2)
    args = p.parse_args()
    train_path, val_path = SPLITS / "train.jsonl", SPLITS / "validation.jsonl"
    if not train_path.exists() or not val_path.exists():
        raise SystemExit("Split belum ada. Jalankan validate_annotations.py dan split_data.py terlebih dahulu.")
    train_rows, val_rows = load_rows(train_path), load_rows(val_path)
    if not train_rows or not val_rows:
        raise SystemExit("Train/validation kosong.")
    random.seed(args.seed)
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise SystemExit("Model baseline belum ada. Jalankan python -m spacy download en_core_web_sm")
    if "ner" not in nlp.pipe_names:
        raise SystemExit("Model dasar tidak memiliki komponen ner.")
    ner = nlp.get_pipe("ner")
    for row in train_rows:
        for ent in row.get("entities", []):
            ner.add_label(str(ent["label"]))
    train_examples = make_examples(nlp, train_rows)
    best_f1, best_epoch = -1.0, 0
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    if MODEL_OUT.exists():
        import shutil; shutil.rmtree(MODEL_OUT)
    start_time = time.time()
    optimizer = nlp.resume_training()
    rng = random.Random(args.seed)
    for epoch in range(1, args.epochs + 1):
        rng.shuffle(train_examples)
        losses = {}
        with nlp.select_pipes(enable=["ner"]):
            for batch_start in range(0, len(train_examples), 8):
                batch = train_examples[batch_start:batch_start + 8]
                nlp.update(batch, sgd=optimizer, drop=args.dropout, losses=losses)
        val_score = evaluate(nlp, val_rows)
        print(f"Epoch {epoch:02d}/{args.epochs} | loss={losses.get('ner', 0):.4f} | val P={val_score['precision']:.4f} R={val_score['recall']:.4f} F1={val_score['f1']:.4f}")
        if val_score["f1"] > best_f1:
            best_f1, best_epoch = val_score["f1"], epoch
            if MODEL_OUT.exists():
                import shutil; shutil.rmtree(MODEL_OUT)
            nlp.to_disk(MODEL_OUT)
    elapsed = time.time() - start_time
    meta = {"base_model": "en_core_web_sm", "trained_model_path": str(MODEL_OUT), "epochs_requested": args.epochs, "best_epoch": best_epoch, "best_validation_exact_span_f1": best_f1, "seed": args.seed, "dropout": args.dropout, "train_documents": len(train_rows), "train_spans": sum(len(r.get("entities", [])) for r in train_rows), "validation_documents": len(val_rows), "validation_spans": sum(len(r.get("entities", [])) for r in val_rows), "training_seconds": round(elapsed, 2), "matching": "exact start/end/label"}
    (MODEL_OUT / "training_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Model terbaik disimpan di:", MODEL_OUT)
    print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
