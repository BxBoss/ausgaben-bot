"""PDF -> Rohtext. Bank-unabhaengig: die eigentliche Struktur-Erkennung
(welche Zeile welche Transaktion ist) macht ai_processor.py."""
from __future__ import annotations

import pdfplumber


def extract_text(pdf_path: str) -> str:
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
    full_text = "\n".join(pages_text).strip()
    if not full_text:
        raise ValueError(
            "Kein Text im PDF gefunden. Vermutlich ein gescanntes/Bild-PDF "
            "ohne OCR-Textebene."
        )
    return full_text
