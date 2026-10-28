from collections import defaultdict


def span_set(entities):
    return {(int(e["start"]), int(e["end"]), str(e["label"])) for e in entities}


def score_sets(gold, pred):
    tp = len(gold & pred)
    fp = len(pred - gold)
    fn = len(gold - pred)
    precision = tp / (tp + fp) if tp + fp else (1.0 if not gold and not pred else 0.0)
    recall = tp / (tp + fn) if tp + fn else (1.0 if not gold and not pred else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def detailed_metrics(gold_docs, pred_docs):
    gold_all, pred_all = set(), set()
    labels = set()
    for i, (gold, pred) in enumerate(zip(gold_docs, pred_docs)):
        gold = {(s,e,l) for s,e,l in gold}
        pred = {(s,e,l) for s,e,l in pred}
        gold_all |= {(i,s,e,l) for s,e,l in gold}
        pred_all |= {(i,s,e,l) for s,e,l in pred}
        labels |= {l for _,_,l in gold | pred}
    g = {(i,s,e,l) for i,s,e,l in gold_all}
    p = {(i,s,e,l) for i,s,e,l in pred_all}
    overall = score_sets(g, p)
    per_label = {}
    for label in sorted(labels):
        gl = {x for x in g if x[3] == label}
        pl = {x for x in p if x[3] == label}
        per_label[label] = score_sets(gl, pl)
    return overall, per_label
