from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import regex as re

@dataclass
class Candidate:
    field: str
    value: str
    page_index: int
    chunk_id: str
    start: int
    end: int
    matched_text: str
    rule_id: str
    priority: int
    score: float

def _window_boost(text: str, start: int, end: int) -> float:
    # small boost if match is near typical keywords
    left = max(0, start - 120)
    right = min(len(text), end + 120)
    window = text[left:right].lower()
    keywords = ["dop", "treated", "solvent", "spin", "cast", "immers", "vapor", "anneal", "film"]
    hits = sum(1 for k in keywords if k in window)
    return min(0.4, 0.08 * hits)

def extract_with_rules(field: str, chunk_id: str, page_index: int, text: str, rules: Dict[str, Any]) -> List[Candidate]:
    cands: List[Candidate] = []
    for p in rules.get("patterns", []):
        rid = p.get("id", "rule")
        label = p.get("label", "")
        rgx = p.get("regex", "")
        prio = int(p.get("priority", 0))
        if not rgx:
            continue

        for m in re.finditer(rgx, text, flags=re.IGNORECASE | re.MULTILINE):
            start, end = m.span()
            matched = text[start:end]
            score = float(prio) / 100.0 + _window_boost(text, start, end)
            cands.append(
                Candidate(
                    field=field,
                    value=label,
                    page_index=page_index,
                    chunk_id=chunk_id,
                    start=start,
                    end=end,
                    matched_text=matched,
                    rule_id=rid,
                    priority=prio,
                    score=score,
                )
            )
    cands.sort(key=lambda x: (x.score, x.priority), reverse=True)
    return cands

def pick_best(cands: List[Candidate]) -> Candidate | None:
    return cands[0] if cands else None
