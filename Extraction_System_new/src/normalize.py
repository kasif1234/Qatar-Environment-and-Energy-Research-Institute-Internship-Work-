from __future__ import annotations
from typing import Dict
import re
from rapidfuzz import fuzz

def basic_norm(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s

def load_synonyms(yaml_obj) -> Dict[str, str]:
    # yaml: {canonical: {variant: canonical}}
    canon = yaml_obj.get("canonical", {}) if isinstance(yaml_obj, dict) else {}
    out = {}
    for k, v in canon.items():
        out[basic_norm(k.lower())] = basic_norm(v)
    return out

def apply_synonyms(value: str, syn_map: Dict[str, str]) -> str:
    v = basic_norm(value)
    key = v.lower()
    if key in syn_map:
        return syn_map[key]
    # soft match for common formatting differences (optional)
    best = None
    best_score = 0
    for k, canon in syn_map.items():
        score = fuzz.ratio(key, k)
        if score > best_score:
            best_score = score
            best = canon
    if best is not None and best_score >= 93:
        return best
    return v
