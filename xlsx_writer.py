"""Schreibt bestaetigte Transaktionen in die Finanzen.xlsx -- neue Struktur
(Stand: komplettes Rebuild) ist EINE Excel-Tabelle "Transaktionen" auf dem
gleichnamigen Blatt, kein Pro-Monat-Zeilenlimit mehr. Neue Zeilen werden
einfach unten an die Tabelle angehaengt, die Tabelle waechst automatisch mit."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.formatting.rule import CellIsRule

SHEET_NAME = "Transaktionen"
TABLE_NAME = "Transaktionen"
DATE_NUMBER_FORMAT = "dd.mm.yyyy"
BETRAG_NUMBER_FORMAT = '#,##0.00" €"'

MONTHS_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni",
             "Juli", "August", "September", "Oktober", "November", "Dezember"]

GRUEN = "1E7B34"
ROT = "C62828"
KK_FILL = PatternFill("solid", fgColor="DCE6F5")


def _as_date(value: Any) -> date:
    if isinstance(value, (date, datetime)):
        return value if isinstance(value, date) and not isinstance(value, datetime) else value.date()
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def write_transactions(xlsx_path: str, transactions: list[dict[str, Any]]) -> dict[str, int]:
    """transactions: Liste von Dicts mit Keys datum, betrag (signiert: negativ
    = Ausgabe, positiv = Einnahme), kategorie, verwendungszweck, optional quelle
    ("Girokonto"/"Kreditkarte", Default "Girokonto")."""
    if not transactions:
        return {"geschrieben": 0}

    wb = openpyxl.load_workbook(xlsx_path, data_only=False)
    ws = wb[SHEET_NAME]
    table = ws.tables[TABLE_NAME]

    start_cell, end_cell = table.ref.split(":")
    end_col_letters = "".join(c for c in end_cell if c.isalpha())
    end_row = int("".join(c for c in end_cell if c.isdigit()))
    start_col_letters = "".join(c for c in start_cell if c.isalpha())

    row = end_row + 1
    for tx in transactions:
        d = _as_date(tx["datum"])
        betrag = round(float(tx["betrag"]), 2)

        ws.cell(row=row, column=1, value=d).number_format = DATE_NUMBER_FORMAT
        ws.cell(row=row, column=2, value=MONTHS_DE[d.month - 1])
        ws.cell(row=row, column=3, value="Einnahme" if betrag > 0 else "Ausgabe")
        ws.cell(row=row, column=4, value=tx["kategorie"])
        bcell = ws.cell(row=row, column=5, value=betrag)
        bcell.number_format = BETRAG_NUMBER_FORMAT
        ws.cell(row=row, column=6, value=tx.get("verwendungszweck", ""))
        quelle = tx.get("quelle", "Girokonto")
        qcell = ws.cell(row=row, column=7, value=quelle)
        if quelle == "Kreditkarte":
            for c in range(1, 8):
                ws.cell(row=row, column=c).fill = KK_FILL
        row += 1

    new_end_row = row - 1
    table.ref = f"{start_col_letters}{start_cell[len(start_col_letters):]}:{end_col_letters}{new_end_row}"

    # Bedingte Formatierung (+ gruen, - rot) auf den neuen Bereich mit ausdehnen
    green_rule = CellIsRule(operator="greaterThan", formula=["0"], font=Font(color=GRUEN, bold=True))
    red_rule = CellIsRule(operator="lessThan", formula=["0"], font=Font(color=ROT, bold=True))
    full_range = f"E2:E{new_end_row}"
    ws.conditional_formatting.add(full_range, green_rule)
    ws.conditional_formatting.add(full_range, red_rule)

    wb.save(xlsx_path)
    return {"geschrieben": len(transactions)}
