# Setup

Kostenloser, regelbasierter Ausgaben-Bot: liest Kontoauszug-PDFs, kategorisiert
Buchungen per Keyword-Regeln (keine KI-API, kein Server), trägt sie in eine
Excel-Datei mit Dashboard, Monatsübersichten und Diagrammen ein.

## 1. Voraussetzungen

- Python 3.11 oder neuer ([python.org](https://www.python.org/downloads/))
- Git (optional, nur falls per `git clone` geholt)

## 2. Projekt holen

Per Git:
```bash
git clone <repo-url>
cd ausgaben-bot
```

Oder: ZIP entpacken und in den Ordner wechseln.

## 3. Python-Umgebung einrichten

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

(macOS/Linux: `source venv/bin/activate` statt `venv\Scripts\activate`)

## 4. Eigene Finanzen.xlsx anlegen

```bash
venv\Scripts\python.exe create_template.py Finanzen.xlsx
```

Erzeugt eine leere Vorlage (Dashboard + 12 Monatsblätter + eine
"Transaktionen"-Tabelle) -- noch ohne Buchungen, aber mit allen Formeln
und Diagrammen fertig eingerichtet. Lege sie ab, wo du sie behalten willst
(z.B. `Dokumente\Finanzen.xlsx`).

## 5. Ersten Import machen

Kontoauszug als PDF exportieren (Online-Banking -> "Umsätze"/Kontoauszug,
Zeitraum wählen, als PDF herunterladen), dann:

```bash
venv\Scripts\python.exe import_kontoauszug.py "<Pfad zur PDF>" --xlsx "<Pfad zu deiner Finanzen.xlsx>"
```

Das Skript zeigt dir alle erkannten Buchungen inkl. Kategorie zur Kontrolle
im Terminal und fragt vor dem Eintragen nach Bestätigung.

Danach: [WORKFLOW.md](WORKFLOW.md) für den laufenden monatlichen Ablauf.

## Wichtig: PDF-Format

`pdf_transaction_parser.py` ist kalibriert auf die Kontoauszug-Formate einer
VR-Bank (Girokonto-Umsätze-Export, Kreditkartenkonto-Umsätze-Export,
klassische Kreditkarten-Umsatzaufstellung). Andere Banken formatieren ihre
PDFs anders -- bricht der Import mit "Keine Buchungszeilen erkannt" ab, muss
das Regex in `pdf_transaction_parser.py` an das eigene Bank-Format angepasst
werden. Am einfachsten: PDF-Rohtext ansehen (`pdf_extractor.extract_text(...)`
in einer Python-Shell) und ein neues Format-Modul nach dem Vorbild der
bestehenden drei ergänzen.

## Kategorien anpassen

`categorizer_rules.py` enthält die Keyword-Listen pro Kategorie
(`EXPENSE_KEYWORDS`/`INCOME_KEYWORDS`). Frei erweiterbar -- ein neues
Stichwort wirkt sofort beim nächsten Import, und `create_template.py` liest
die Kategorienliste automatisch von dort, falls die Vorlage neu erzeugt wird.
