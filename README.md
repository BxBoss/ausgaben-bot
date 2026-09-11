# Ausgaben-Bot

Kostenloser, regelbasierter Import von Kontoauszug-PDFs (Girokonto +
Kreditkarte) in eine Finanzen.xlsx mit Dashboard. Kein API-Key, kein Server.

**Aktueller Workflow: siehe [WORKFLOW.md](WORKFLOW.md).**

Kurzfassung:
```bash
venv\Scripts\python.exe import_kontoauszug.py "<Pfad zur PDF>"
```

## Funktionsweise

1. **PDF-Extraktion**: `pdf_extractor.py` (pdfplumber) liest den Rohtext.
2. **Parsing**: `pdf_transaction_parser.py` erkennt automatisch eines von drei
   kalibrierten VR-Bank-Formaten (Girokonto-Umsätze, Kreditkartenkonto-Umsätze,
   klassische Kreditkarten-Umsatzaufstellung) und extrahiert Datum/Betrag/
   Verwendungszweck.
3. **Kategorisierung**: `categorizer_rules.py` -- Keyword-Liste pro Kategorie,
   gegen Zahlungsempfänger + vollständigen Verwendungszweck geprüft.
4. **Kontrolle**: Terminal zeigt alle erkannten Buchungen inkl. Duplikat-
   Warnung, fragt vor dem Schreiben nach Bestätigung.
5. **Eintrag**: `xlsx_writer.py` hängt bestätigte Zeilen an die
   "Transaktionen"-Tabelle in Finanzen.xlsx an (ein Blatt, eine Excel-Tabelle,
   kein Zeilenlimit). Das "Dashboard"-Blatt rechnet per Tabellen-Referenz
   automatisch mit.

## Konfiguration

- `categorizer_rules.py` — Kategorisierungs-Keywords, hier erweitern wenn ein
  Anbieter falsch/gar nicht erkannt wird
- `pdf_transaction_parser.py` — Format-Parser, hier anpassen bei neuen
  Kontoauszug-Layouts

## Legacy: Flask-Dashboard mit KI-Kategorisierung (Google Sheets)

Ursprünglicher Ansatz (`app.py`, `ai_processor.py`, `sheets_client.py`) nutzt
Claude-API + Google Sheets statt der kostenlosen xlsx-Variante. Funktioniert
weiterhin, ist aber nicht der aktive Workflow -- siehe [SETUP.md](SETUP.md)
falls doch gebraucht.
