"""Regex-basierte Extraktion von Buchungszeilen aus Kontoauszug-Rohtext.

Bestes-Wissen-Startpunkt fuer ein generisches deutsches Kontoauszug-Format
(Datum [Datum] Verwendungszweck Betrag). Bank-Layouts variieren stark --
sobald ein echtes Beispiel-PDF vorliegt, muss dieses Regex ggf. kalibriert
werden. Deshalb markiert der Parser jede Zeile mit niedriger Sicherheit
(kein eindeutiges Vorzeichen erkannt) statt sie stillschweigend falsch
einzuordnen."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

_LINE_RE = re.compile(
    r"^(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?:\d{2}\.\d{2}\.\d{4}\s+)?"
    r"(?P<desc>.+?)\s+"
    r"(?P<sign>[+-])?\s*(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})\s*(?:EUR)?$"
)


def _parse_amount(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", "."))


def parse_transactions(raw_text: str) -> list[dict[str, Any]]:
    transactions = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue

        datum = datetime.strptime(m.group("date"), "%d.%m.%Y").date().isoformat()
        betrag = _parse_amount(m.group("amount"))
        sign = m.group("sign")
        if sign == "-":
            betrag = -abs(betrag)
            unsicher = False
        elif sign == "+":
            betrag = abs(betrag)
            unsicher = False
        else:
            # Kein explizites Vorzeichen im Text gefunden -- als Ausgabe
            # angenommen (haeufigster Fall), aber zur Kontrolle markiert.
            betrag = -abs(betrag)
            unsicher = True

        transactions.append(
            {
                "datum": datum,
                "betrag": betrag,
                "verwendungszweck": m.group("desc").strip(),
                "unsicher": unsicher,
            }
        )
    return transactions
