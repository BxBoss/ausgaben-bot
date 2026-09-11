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

# IBANs, die auf das Kreditkartenkonto selbst zeigen -- jede Girokonto-Buchung
# mit einer dieser IBANs ist eine Ein-/Auszahlung auf die Kreditkarte (manuelle
# Kartenbegleichung per SecureGo, inkl. fehlgeschlagener/rueckgebuchter
# Versuche), keine eigenstaendige Ausgabe. Wuerde sonst mit den itemisierten
# Kreditkartenkonto-Buchungen doppelt zaehlen.
GK_EXCLUDE_IBANS: set[str] = set()


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

            is_visa_settlement = (datum, round(betrag, 2)) in GK_EXCLUDE_VISA_SETTLEMENTS
            is_card_account_transfer = any(iban in cont_text for iban in GK_EXCLUDE_IBANS)
            if not is_visa_settlement and not is_card_account_transfer:
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
# Format 3: Kreditkartenkonto-Umsaetze-Export (eigenes Konto fuer die Karte,
# gleicher Umsaetze-Export-Mechanismus wie Format 2, aber andere Zeilenform)
# ---------------------------------------------------------------------

_KKU_TX_START_RE = re.compile(
    r"^(?P<label>.+?)\s(?P<sign>[+-])(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR$"
)
_KKU_DATE_RE = re.compile(r"Umsatz vom\s+(\d{2}\.\d{2}\.\d{4})")
_KKU_VALUTA_YEAR_RE = re.compile(r"Valuta\s+\d{2}\.\d{2}\.(\d{4})")
_KKU_MERCHANT_STOP_RE = re.compile(r"\s+EUR\b|\s+Valuta\b|Umsatz vom")
_KKU_NOISE_PREFIXES = ("Seite ", "Wir machen den Weg frei")

# "Ueberweisung" = eingehende Zahlung der Kartenabrechnung vom Girokonto --
# keine Kartenbuchung, sondern die interne Ausgleichsbuchung. Wird immer
# ausgeschlossen (entspricht der "Visa-Sonstiges"-Sammelbuchung im Girokonto,
# die dafuer ebenfalls ausgeschlossen werden muss um Doppelzaehlung zu vermeiden).


def parse_kreditkartenkonto_transactions(raw_text: str) -> list[dict[str, Any]]:
    lines = raw_text.splitlines()
    n = len(lines)
    transactions = []
    i = 0
    while i < n:
        line = lines[i].strip()
        m = _KKU_TX_START_RE.match(line)
        if not m:
            i += 1
            continue

        label = m.group("label").strip()
        amount = _parse_amount(m.group("amount"))
        betrag = amount if m.group("sign") == "+" else -amount

        continuation = []
        j = i + 1
        while j < n:
            l2 = lines[j].strip()
            if not l2:
                j += 1
                continue
            if _KKU_TX_START_RE.match(l2):
                break
            if l2.startswith(_KKU_NOISE_PREFIXES):
                j += 1
                continue
            continuation.append(l2)
            j += 1
        cont_text = " ".join(continuation)

        if "überweisung" in label.lower():
            i = j
            continue  # Kartenabrechnung-Ausgleich, keine Buchung

        dm = _KKU_DATE_RE.search(cont_text)
        if not dm:
            i = j
            continue
        d, mo, y = dm.group(1).split(".")
        # Einzelne "Umsatz vom"-Jahresangaben im Export sind fehlerhaft
        # (beobachtet: 2025 statt 2026) -- die Valuta-Zeile im selben Block
        # gilt als verlaesslicher und korrigiert das Jahr im Zweifel.
        vy = _KKU_VALUTA_YEAR_RE.search(cont_text)
        if vy and vy.group(1) != y:
            y = vy.group(1)
        datum = date(int(y), int(mo), int(d)).isoformat()

        stop = _KKU_MERCHANT_STOP_RE.search(cont_text)
        merchant = cont_text[: stop.start()].strip() if stop else cont_text.strip()
        if not merchant:
            merchant = label

        transactions.append(
            {
                "datum": datum,
                "betrag": betrag,
                "verwendungszweck": merchant,
                "match_text": f"{merchant} {cont_text}",
                "unsicher": False,
                "quelle": "Kreditkarte",
            }
        )
        i = j
    return transactions


# ---------------------------------------------------------------------
# Format-Erkennung
# ---------------------------------------------------------------------

def parse_transactions(raw_text: str) -> list[dict[str, Any]]:
    if "Kreditkartenkonto" in raw_text:
        return parse_kreditkartenkonto_transactions(raw_text)
    if "Filterparameter" in raw_text and "Umsätze" in raw_text:
        return parse_girokonto_transactions(raw_text)
    return parse_creditcard_transactions(raw_text)
