"""Regex-basierte Extraktion von Buchungszeilen aus Kontoauszug-Rohtext.

Kalibriert an einer echten VR-Bank Kreditkarten-Umsatzaufstellung. Format:
    DD.MM. DD.MM. <Umsatzinformationen> <Betrag>,<Cent>[+-]
    Mobil bezahlter Umsatz          <- Rauschzeile, wird ignoriert

Datum hat KEIN Jahr auf der Buchungszeile selbst -- das Jahr steht im
Kopf ("Umsatzaufstellung vom DD.MM.YYYY bis DD.MM.YYYY" bzw.
"Abrechnungsdatum: DD.MM.YYYY") und wird von dort uebernommen.

"Saldo Vormonat", "Ausgleich Kreditkartensaldo", "Zwischensaldo" und
"Uebertrag" sind keine echten Buchungen (Salden/Kartenausgleich),
sondern werden explizit rausgefiltert.

Andere Banken/Kontoauszug-Formate koennen abweichen -- bei Bedarf hier
weitere Formate ergaenzen."""
from __future__ import annotations

import re
from datetime import date
from typing import Any

_YEAR_RE = re.compile(r"Umsatzaufstellung vom \d{2}\.\d{2}\.(\d{4})")
_YEAR_FALLBACK_RE = re.compile(r"Abrechnungsdatum:\s*\d{2}\.\d{2}\.(\d{4})")

_LINE_RE = re.compile(
    r"^(?P<buchungsdatum>\d{2}\.\d{2})\.\s+"
    r"(?P<belegdatum>\d{2}\.\d{2})\.\s+"
    r"(?P<desc>.+?)\s+"
    r"(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})(?P<sign>[+-])$"
)

_IGNORE_DESC_SUBSTRINGS = (
    "ausgleich kreditkartensaldo",
    "saldo vormonat",
)


def _find_statement_year(raw_text: str) -> int:
    m = _YEAR_RE.search(raw_text) or _YEAR_FALLBACK_RE.search(raw_text)
    if not m:
        raise ValueError(
            "Abrechnungsjahr nicht im PDF-Text gefunden -- Format weicht ab, "
            "Regex in pdf_transaction_parser.py muss angepasst werden."
        )
    return int(m.group(1))


def _parse_amount(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", "."))


def parse_transactions(raw_text: str) -> list[dict[str, Any]]:
    year = _find_statement_year(raw_text)
    transactions = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue

        desc = m.group("desc").strip()
        if any(s in desc.lower() for s in _IGNORE_DESC_SUBSTRINGS):
            continue

        day, month = m.group("buchungsdatum").split(".")
        datum = date(year, int(month), int(day)).isoformat()

        betrag = _parse_amount(m.group("amount"))
        if m.group("sign") == "-":
            betrag = -abs(betrag)
        else:
            betrag = abs(betrag)

        transactions.append(
            {
                "datum": datum,
                "betrag": betrag,
                "verwendungszweck": desc,
                "unsicher": False,
            }
        )
    return transactions
