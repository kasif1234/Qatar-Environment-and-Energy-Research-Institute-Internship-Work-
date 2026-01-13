from __future__ import annotations
from typing import Dict, Any, List
from ..scoring import extract_with_rules, Candidate

def extract(chunk_id: str, page_index: int, text: str, rules: Dict[str, Any]) -> List[Candidate]:
    return extract_with_rules("doping_method", chunk_id, page_index, text, rules)
