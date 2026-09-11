"""CLI: Kontoauszug-PDF -> regelbasierte Kategorisierung -> Kontrolle ->
Eintrag in Finanzen.xlsx. Kein API-Key, kein Server, keine Kosten.

Nutzung:
    python import_kontoauszug.py <pfad_zur_pdf> <monat>

Beispiel:
    python import_kontoauszug.py Abrechnung_Juli.pdf Juli
"""
from __future__ import annotations

import argparse
import sys

import openpyxl

import categorizer_rules
import pdf_extractor
import pdf_transaction_parser
import xlsx_writer

DEFAULT_XLSX = r"C:\Users\Nils\Downloads\Finanzen.xlsx"


def existing_keys(xlsx_path: str, month: str) -> set[tuple]:
    """(datum, betrag, verwendungszweck) bereits vorhandener Zeilen fuer
    einfache Duplikat-Erkennung."""
    sheet_name = xlsx_writer.resolve_sheet_name(month)
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[sheet_name]
    keys = set()
    for row in range(xlsx_writer.DATA_START_ROW, xlsx_writer.AUSGABEN_MAX_ROW + 1):
        datum, betrag, _, zweck = (ws.cell(row=row, column=c).value for c in range(1, 5))
        if datum is not None:
            keys.add((str(datum), betrag, str(zweck or "")))
    for row in range(xlsx_writer.DATA_START_ROW, xlsx_writer.EINNAHMEN_MAX_ROW + 1):
        datum, betrag, _, zweck = (ws.cell(row=row, column=c).value for c in range(6, 10))
        if datum is not None:
            keys.add((str(datum), betrag, str(zweck or "")))
    return keys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path")
    parser.add_argument("monat")
    parser.add_argument("--xlsx", default=DEFAULT_XLSX)
    parser.add_argument("--yes", action="store_true", help="ohne Rueckfrage eintragen")
    args = parser.parse_args()

    raw_text = pdf_extractor.extract_text(args.pdf_path)
    parsed = pdf_transaction_parser.parse_transactions(raw_text)

    if not parsed:
        print("Keine Buchungszeilen erkannt. Regex in pdf_transaction_parser.py "
              "muss vermutlich an dieses Bank-Format angepasst werden.")
        sys.exit(1)

    for tx in parsed:
        is_income = tx["betrag"] > 0
        tx["kategorie"] = categorizer_rules.categorize(tx["verwendungszweck"], is_income)

    dupes = existing_keys(args.xlsx, args.monat)

    print(f"\n{len(parsed)} Buchungen erkannt:\n")
    print(f"{'Datum':<12} {'Betrag':>10}  {'Kategorie':<15} {'Verwendungszweck':<35} Hinweis")
    print("-" * 100)
    for tx in parsed:
        key = (tx["datum"], abs(tx["betrag"]), tx["verwendungszweck"])
        hinweise = []
        if key in dupes:
            hinweise.append("DUPLIKAT?")
        if tx["unsicher"]:
            hinweise.append("Vorzeichen unsicher")
        print(f"{tx['datum']:<12} {tx['betrag']:>10.2f}  {tx['kategorie']:<15} "
              f"{tx['verwendungszweck'][:35]:<35} {', '.join(hinweise)}")

    if not args.yes:
        antwort = input("\nDiese Zeilen in Finanzen.xlsx eintragen? [j/N] ").strip().lower()
        if antwort != "j":
            print("Abgebrochen, nichts geschrieben.")
            return

    ausgaben = [
        {"datum": tx["datum"], "betrag": abs(tx["betrag"]), "kategorie": tx["kategorie"],
         "verwendungszweck": tx["verwendungszweck"]}
        for tx in parsed if tx["betrag"] < 0
    ]
    einnahmen = [
        {"datum": tx["datum"], "betrag": abs(tx["betrag"]), "kategorie": tx["kategorie"],
         "verwendungszweck": tx["verwendungszweck"]}
        for tx in parsed if tx["betrag"] > 0
    ]

    result = xlsx_writer.write_transactions(args.xlsx, args.monat, ausgaben, einnahmen)
    print(f"\nFertig: {result['ausgaben_geschrieben']} Ausgaben, "
          f"{result['einnahmen_geschrieben']} Einnahmen in '{args.monat}' eingetragen.")


if __name__ == "__main__":
    main()
