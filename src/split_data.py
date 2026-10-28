from pathlib import Path
import argparse, json, random

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotations" / "annotated.jsonl"
OUT = ROOT / "data" / "splits"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train", type=float, default=0.70)
    p.add_argument("--val", type=float, default=0.15)
    p.add_argument("--test", type=float, default=0.15)
    args = p.parse_args()
    if abs(args.train + args.val + args.test - 1.0) > 1e-6:
        raise SystemExit("Proporsi train + val + test harus sama dengan 1.0")
    if not ANN.exists():
        raise SystemExit("File annotated.jsonl belum ada.")
    rows = [json.loads(line) for line in ANN.read_text(encoding="utf-8").splitlines() if line.strip()]
    if any(r.get("reviewed") is not True for r in rows):
        raise SystemExit("Semua artikel yang dipakai harus reviewed=true.")
    ids = [str(r.get("original_id", "")).strip() for r in rows]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        raise SystemExit("original_id harus ada dan unik sebelum split.")
    if len(rows) < 20:
        raise SystemExit("Anotasi terlalu sedikit untuk split yang masuk akal. Anotasi setidaknya 20 artikel; disarankan 70+ agar test mendekati 10 artikel.")
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    n = len(rows)
    n_train = int(n * args.train)
    n_val = int(n * args.val)
    train = rows[:n_train]
    val = rows[n_train:n_train+n_val]
    test = rows[n_train+n_val:]
    OUT.mkdir(parents=True, exist_ok=True)
    for name, subset in [("train", train), ("validation", val), ("test", test)]:
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for row in subset:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {"seed": args.seed, "ratios": {"train": args.train, "validation": args.val, "test": args.test}, "documents": {"train": len(train), "validation": len(val), "test": len(test)}, "spans": {"train": sum(len(r.get("entities", [])) for r in train), "validation": sum(len(r.get("entities", [])) for r in val), "test": sum(len(r.get("entities", [])) for r in test)}}
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "split_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if len(test) < 10:
        print("PERINGATAN: test set kurang dari 10 artikel; anotasi lebih banyak artikel jika tugas mensyaratkan minimal 10 artikel evaluasi.")

if __name__ == "__main__":
    main()
