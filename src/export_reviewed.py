import json
from pathlib import Path

ANN = Path(__file__).resolve().parents[1] / "data" / "annotations"
rows = [json.loads(l) for l in (ANN / "annotated.all.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
done = [r for r in rows if r.get("reviewed") is True]
(ANN / "annotated.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done), encoding="utf-8")
print(f"{len(done)} dari {len(rows)} artikel reviewed -> annotated.jsonl")