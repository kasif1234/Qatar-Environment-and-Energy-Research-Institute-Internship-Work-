from __future__ import annotations
from typing import Dict, Any, List
import json

REQUIRED_FIELDS = ["polymer", "dopant", "doping_method", "solvent", "film_prep"]

def load_gold(jsonl_path: str) -> Dict[str, List[Dict[str, Any]]]:
    # jsonl format: one entry per row:
    # {"pdf_id":"paper1", "fields":{"polymer":"...", ...}, "evidence":{"polymer":{"page":0,"chunk_id":"p0_c1","span":[10,30]}}}
    out: Dict[str, List[Dict[str, Any]]] = {}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            pdf_id = obj["pdf_id"]
            out.setdefault(pdf_id, []).append(obj)
    return out

def exact_match(pred: Dict[str, Any], gold_fields: Dict[str, Any]) -> float:
    # per-field exact match average
    scores = []
    for k in REQUIRED_FIELDS:
        pv = (pred.get(k) or "").strip()
        gv = (gold_fields.get(k) or "").strip()
        scores.append(1.0 if pv == gv else 0.0)
    return sum(scores) / len(scores)

def evaluate_pdf(pred_rows: List[Dict[str, Any]], gold_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    # simple matching: if counts differ, evaluate best pairings by greedy EM
    used = set()
    per_row = []
    for pr in pred_rows:
        best_j = None
        best_s = -1.0
        for j, gr in enumerate(gold_rows):
            if j in used:
                continue
            s = exact_match(pr, gr["fields"])
            if s > best_s:
                best_s = s
                best_j = j
        if best_j is not None:
            used.add(best_j)
            per_row.append(best_s)
        else:
            per_row.append(0.0)

    avg = sum(per_row) / max(1, len(per_row))
    return {"row_count_pred": len(pred_rows), "row_count_gold": len(gold_rows), "avg_field_em": avg}
