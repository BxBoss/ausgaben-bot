"""Regex-basierte Extraktion von Buchungszeilen aus Kontoauszug-Rohtext.

Unterstuetzt zwei kalibrierte Formate einer VR-Bank:

1. Kreditkarten-Umsatzaufstellung (eine Zeile pro Buchung):
    DD.MM. DD.MM. <Umsatzinformationen> <Betrag>,<Cent>[+-]
    Mobil bezahlter Umsatz          <- Rauschzeile, wird ignoriert

2. Girokonto-Umsaetze-Export (mehrzeiliger Block pro Buchung):
    <Name/Auftraggeber> <Betrag>,<Cent> EUR
    <IBAN> DD.MM.YYYY
    <Verwendungszweck-Details, 0-3 Zeilen>

`parse_transactions()` erkennt das Format automatisch anhand von
Kopfzeilen-Merkmalen und ruft den passenden Parser auf.

Andere Banken/Kontoauszug-Formate koennen abweichen -- bei Bedarf hier
weitere Formate ergaenzen."""
from __future__ import annotations

import re
from datetime import date
from typing import Any

# ---------------------------------------------------------------------
# Format 1: Kreditkarten-Umsatzaufstellung
# ---------------------------------------------------------------------

_CC_YEAR_RE = re.compile(r"Umsatzaufstellung vom \d{2}\.\d{2}\.(\d{4})")
_CC_YEAR_FALLBACK_RE = re.compile(r"Abrechnungsdatum:\s*\d{2}\.\d{2}\.(\d{4})")

_CC_LINE_RE = re.compile(
    r"^(?P<buchungsdatum>\d{2}\.\d{2})\.\s+"
    r"(?P<belegdatum>\d{2}\.\d{2})\.\s+"
    r"(?P<desc>.+?)\s+"
    r"(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})(?P<sign>[+-])$"
)

_CC_IGNORE_DESC_SUBSTRINGS = (
    "ausgleich kreditkartensaldo",
    "saldo vormonat",
)


def _parse_amount(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", "."))


def parse_creditcard_transactions(raw_text: str) -> list[dict[str, Any]]:
    m = _CC_YEAR_RE.search(raw_text) or _CC_YEAR_FALLBACK_RE.search(raw_text)
    if not m:
        raise ValueError(
            "Abrechnungsjahr nicht im PDF-Text gefunden -- Format weicht ab, "
            "Regex in pdf_transaction_parser.py muss angepasst werden."
        )
    year = int(m.group(1))
    transactions = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _CC_LINE_RE.match(line)
        if not m:
            continue

        desc = m.group("desc").strip()
        if any(s in desc.lower() for s in _CC_IGNORE_DESC_SUBSTRINGS):
            continue

        day, month = m.group("buchungsdatum").split(".")
        datum = date(year, int(month), int(day)).isoformat()

        betrag = _parse_amount(m.group("amount"))
        betrag = -abs(betrag) if m.group("sign") == "-" else abs(betrag)

        transactions.append(
            {
                "datum": datum,
                "betrag": betrag,
                "verwendungszweck": desc,
                "match_text": desc,
                "unsicher": False,
            }
        )
    return transactions


# ---------------------------------------------------------------------
# Format 2: Girokonto-Umsaetze-Export
# ---------------------------------------------------------------------

_GK_TX_START_RE = re.compile(
    r"^(?P<name>.+)\s(?P<sign>[+-])(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR$"
)
_GK_DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4})\s*$")
_GK_PAYPAL_MERCHANT_RE = re.compile(r"[Ii]hr Einkauf bei\s+(.+?)(?:\s+EREF|,|$)")
_GK_NOISE_PREFIXES = ("Seite ", "Wir machen den Weg frei")

# Sammelbuchungen der Kreditkarten-Abrechnung -- keine Einzelkategorie,
# sondern die Gesamtsumme einer Kartenabrechnung. Fuer Monate, die schon
# per Kreditkarten-Umsatzaufstellung einzeln importiert wurden, muss die
# passende Zeile hier explizit ausgeschlossen werden (sonst Doppelzaehlung).
# Format: (Buchungsdatum als YYYY-MM-DD, Betrag als negative Zahl)
GK_EXCLUDE_VISA_SETTLEMENTS: set[tuple[str, float]] = set()


def parse_girokonto_transactions(raw_text: str) -> list[dict[str, Any]]:
    lines = raw_text.splitlines()
    n = len(lines)
    transactions = []
    i = 0
    while i < n:
        line = lines[i].strip()
        m = _GK_TX_START_RE.match(line)
        if not m:
            i += 1
            continue

        name = m.group("name").strip()
        amount = _parse_amount(m.group("amount"))
        betrag = amount if m.group("sign") == "+" else -amount

        datum = None
        if i + 1 < n:
            dm = _GK_DATE_RE.search(lines[i + 1].strip())
            if dm:
                d, mo, y = dm.group(1).split(".")
                datum = date(int(y), int(mo), int(d)).isoformat()

        continuation = []
        j = i + 2
        while j < n:
            l2 = lines[j].strip()
            if not l2:
                j += 1
                continue
            if _GK_TX_START_RE.match(l2):
                break
            if l2.startswith(_GK_NOISE_PREFIXES):
                j += 1
                continue
            continuation.append(l2)
            j += 1
        cont_text = " ".join(continuation)

        if datum is not None:
            verwendungszweck = name
            if "paypal" in name.lower():
                pm = _GK_PAYPAL_MERCHANT_RE.search(cont_text)
                if pm:
                    merchant = pm.group(1).strip().rstrip(",")
                    # Manche PayPal-Buchungen haben nach "Ihr Einkauf bei"
                    # keinen echten Namen (direkt "EREF:...") -- die Regex
                    # faengt dann faelschlich den ganzen Referenz-Bloedsinn.
                    if merchant and not re.search(r"EREF|MREF|CRED:|IBAN:", merchant):
                        verwendungszweck = merchant

            if (datum, round(betrag, 2)) not in GK_EXCLUDE_VISA_SETTLEMENTS:
                transactions.append(
                    {
                        "datum": datum,
                        "betrag": betrag,
                        "verwendungszweck": verwendungszweck,
                        "match_text": f"{name} {cont_text}",
                        "unsicher": False,
                    }
                )
        i = j
    return transactions


# ---------------------------------------------------------------------
# Format-Erkennung
# ---------------------------------------------------------------------

def parse_transactions(raw_text: str) -> list[dict[str, Any]]:
    if "Filterparameter" in raw_text and "Umsätze" in raw_text:
        return parse_girokonto_transactions(raw_text)
    return parse_creditcard_transactions(raw_text)
