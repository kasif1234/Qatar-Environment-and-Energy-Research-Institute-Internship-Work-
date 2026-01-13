from __future__ import annotations
from typing import Dict, Any, List

def is_not_specified(v: str) -> bool:
    if v is None:
        return True
    x = v.strip().lower()
    return x in {"not specified", "not reported", "n/a", ""}

def row_has_all_fields(row: Dict[str, Any], required: List[str]) -> bool:
    for f in required:
        if f not in row or is_not_specified(str(row[f] or "")):
            return False
    return True
