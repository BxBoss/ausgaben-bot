# Ausgaben-Bot

Kontoauszug-PDF per Drag & Drop hochladen -> Claude extrahiert und kategorisiert
die Transaktionen -> Ergebnis im Dashboard prüfen/korrigieren -> per Klick ins
Google Sheet eintragen.

## Setup

Siehe [SETUP.md](SETUP.md) für die vollständige Schritt-für-Schritt-Anleitung
(Anthropic API-Key, Google Cloud Service Account, Sheet-Freigabe).

## Start

```bash
python app.py
```

Dann im Browser: http://127.0.0.1:5000

## Funktionsweise

1. **Upload**: PDF wird per `pdfplumber` in Rohtext umgewandelt (bankunabhängig).
2. **KI-Extraktion + Kategorisierung**: Claude zerlegt den Text in einzelne
   Buchungen (Datum, Empfänger, Verwendungszweck, Betrag, Typ) und ordnet jeder
   eine Kategorie aus `config.py` zu — in einem Aufruf, strukturierter JSON-Output.
3. **Dedupe**: Bereits im Sheet vorhandene Buchungen werden per Hash erkannt und
   im Dashboard vorab abgewählt (verhindert doppelte Einträge bei überlappenden
   Auszugs-Zeiträumen).
4. **Kontrolle**: Alle Felder sind im Dashboard editierbar, bevor etwas ins
   Sheet geschrieben wird.
5. **Sheets-Eintrag**: Bestätigte Zeilen werden über die Sheets API angehängt.

## Konfiguration

- `config.py` — Kategorienliste (`CATEGORIES`) und Spalten-Mapping (`SHEET_COLUMNS`)
- `.env` — API-Keys, Sheet-ID (siehe `.env.example`)
