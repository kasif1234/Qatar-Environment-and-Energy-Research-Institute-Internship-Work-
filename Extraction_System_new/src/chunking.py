from __future__ import annotations
from dataclasses import dataclass
from typing import List
import re

@dataclass
class Chunk:
    chunk_id: str
    page_index: int
    text: str

def simple_chunks(pages, max_chars: int = 2500) -> List[Chunk]:
    chunks: List[Chunk] = []
    for p in pages:
        t = p.text
        if not t:
            continue
        # split on blank lines first
        parts = re.split(r"\n\s*\n", t)
        buf = ""
        k = 0
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(buf) + len(part) + 2 <= max_chars:
                buf = (buf + "\n\n" + part).strip()
            else:
                if buf:
                    chunks.append(Chunk(chunk_id=f"p{p.page_index}_c{k}", page_index=p.page_index, text=buf))
                    k += 1
                buf = part
        if buf:
            chunks.append(Chunk(chunk_id=f"p{p.page_index}_c{k}", page_index=p.page_index, text=buf))
    return chunks
