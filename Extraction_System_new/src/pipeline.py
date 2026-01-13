from __future__ import annotations
import os
import json
import yaml
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List

from .pdf_text import pdf_to_pages
from .chunking import simple_chunks
from .scoring import pick_best
from .normalize import load_synonyms, apply_synonyms
from .validate import row_has_all_fields
from .evaluate import load_gold, evaluate_pdf, REQUIRED_FIELDS

from .extractors import polymer as ex_poly
from .extractors import dopant as ex_dop
from .extractors import solvent as ex_sol
from .extractors import doping_method as ex_method
from .extractors import film_prep as ex_film

def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def setup_logger(run_dir: str) -> logging.Logger:
    os.makedirs(run_dir, exist_ok=True)
    logger = logging.getLogger("extract")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fh = logging.FileHandler(os.path.join(run_dir, "run.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def extract_one_pdf(pdf_path: str, rules_dir: str, syn_map: Dict[str, str]) -> Dict[str, Any]:
    # load rules
    rules = {
        "polymer": _load_yaml(os.path.join(rules_dir, "polymer_patterns.yml")),
        "dopant": _load_yaml(os.path.join(rules_dir, "dopant_patterns.yml")),
        "solvent": _load_yaml(os.path.join(rules_dir, "solvent_patterns.yml")),
        "doping_method": _load_yaml(os.path.join(rules_dir, "method_patterns.yml")),
        "film_prep": _load_yaml(os.path.join(rules_dir, "film_prep_patterns.yml")),
    }

    pages = pdf_to_pages(pdf_path)
    chunks = simple_chunks(pages, max_chars=2500)

    # collect best candidate per field across all chunks
    best = {k: None for k in REQUIRED_FIELDS}

    for c in chunks:
        text = c.text

        c_poly = pick_best(ex_poly.extract(c.chunk_id, c.page_index, text, rules["polymer"]))
        c_dop  = pick_best(ex_dop.extract(c.chunk_id, c.page_index, text, rules["dopant"]))
        c_sol  = pick_best(ex_sol.extract(c.chunk_id, c.page_index, text, rules["solvent"]))
        c_met  = pick_best(ex_method.extract(c.chunk_id, c.page_index, text, rules["doping_method"]))
        c_film = pick_best(ex_film.extract(c.chunk_id, c.page_index, text, rules["film_prep"]))

        for field, cand in [("polymer", c_poly), ("dopant", c_dop), ("solvent", c_sol), ("doping_method", c_met), ("film_prep", c_film)]:
            if cand is None:
                continue
            # global best by score
            if best[field] is None or cand.score > best[field].score:
                best[field] = cand

    # finalize row
    row = {}
    evidence = {}
    for field in REQUIRED_FIELDS:
        cand = best[field]
        if cand is None:
            row[field] = "Not specified"
            continue
        val = apply_synonyms(cand.value, syn_map)
        row[field] = val
        evidence[field] = {
            "page": cand.page_index,
            "chunk_id": cand.chunk_id,
            "span": [cand.start, cand.end],
            "matched_text": cand.matched_text,
            "rule_id": cand.rule_id,
            "score": cand.score,
        }

    return {"row": row, "evidence": evidence}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", required=True, help="Folder containing PDFs")
    ap.add_argument("--rules_dir", required=True, help="rules/v001 folder")
    ap.add_argument("--gold", default="", help="data/gold/annotations.jsonl (optional)")
    ap.add_argument("--run_dir", default="", help="runs/run_YYYY-MM-DD_vXXX")
    args = ap.parse_args()

    run_dir = args.run_dir.strip()
    if not run_dir:
        run_dir = os.path.join("runs", f"run_{datetime.now().strftime('%Y-%m-%d')}_v001")

    logger = setup_logger(run_dir)
    logger.info(f"Run dir: {run_dir}")

    syn = _load_yaml(os.path.join(args.rules_dir, "synonym_map.yml"))
    syn_map = load_synonyms(syn)

    pdf_files = [f for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")]
    pdf_files.sort()

    outputs = []
    for f in pdf_files:
        pdf_path = os.path.join(args.pdf_dir, f)
        pdf_id = os.path.splitext(f)[0]
        logger.info(f"Extracting: {f}")

        res = extract_one_pdf(pdf_path, args.rules_dir, syn_map)

        # For now, we produce ONE row per PDF.
        # Later, you can extend to multi-row by detecting multiple polymers/dopants.
        out = {"pdf_id": pdf_id, "fields": res["row"], "evidence": res["evidence"]}
        outputs.append(out)

        with open(os.path.join(run_dir, f"{pdf_id}.json"), "w", encoding="utf-8") as w:
            json.dump(out, w, ensure_ascii=False, indent=2)

    # save summary
    with open(os.path.join(run_dir, "predictions.jsonl"), "w", encoding="utf-8") as w:
        for o in outputs:
            w.write(json.dumps(o, ensure_ascii=False) + "\n")

    # optional evaluation
    if args.gold:
        gold = load_gold(args.gold)
        scores = []
        for o in outputs:
            pdf_id = o["pdf_id"]
            if pdf_id not in gold:
                continue
            # pred_rows = [o["fields"]] because 1 row per pdf baseline
            report = evaluate_pdf([o["fields"]], gold[pdf_id])
            scores.append(report["avg_field_em"])
            logger.info(f"Eval {pdf_id}: avg_field_em={report['avg_field_em']:.3f}")

        overall = sum(scores) / max(1, len(scores))
        logger.info(f"Overall avg_field_em on gold PDFs present in run: {overall:.3f}")

        with open(os.path.join(run_dir, "eval_summary.json"), "w", encoding="utf-8") as w:
            json.dump({"overall_avg_field_em": overall, "n": len(scores)}, w, indent=2)

if __name__ == "__main__":
    main()
