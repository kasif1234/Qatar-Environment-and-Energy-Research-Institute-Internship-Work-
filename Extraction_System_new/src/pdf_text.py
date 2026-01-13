from __future__ import annotations
from dataclasses import dataclass
from typing import List
import fitz  # PyMuPDF
import re

@dataclass
class PageText:
    page_index: int
    text: str

def clean_text(s: str) -> str:
    s = s.replace("\u00ad", "")  # soft hyphen
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def pdf_to_pages(pdf_path: str) -> List[PageText]:
    doc = fitz.open(pdf_path)
    pages: List[PageText] = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        text = page.get_text("text") or ""
        pages.append(PageText(page_index=i, text=clean_text(text)))
    doc.close()
    return pages
