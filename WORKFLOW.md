# Monatlicher Workflow: Kontoauszug -> Finanzen.xlsx

## 1. Unterlagen holen

Am Monatsende bzw. sobald verfuegbar:
- Kontoauszug(-PDF) vom Girokonto
- Kreditkarten-Umsatzaufstellung(-PDF), falls vorhanden

Beide als PDF herunterladen (Bank-Login -> Postfach/Dokumente), Speicherort egal
(z.B. Desktop oder Downloads).

## 2. Import laufen lassen

```bash
cd "E:\_VAULT_\Claude\Projekte\Finanzen\ausgaben-bot"
venv\Scripts\python.exe import_kontoauszug.py "<Pfad zur PDF>" <Monat>
```

Beispiel:
```bash
venv\Scripts\python.exe import_kontoauszug.py "C:\Users\Nils\Desktop\Kontoauszug_August.pdf" August
```

Das Skript:
1. liest den PDF-Text
2. erkennt Buchungszeilen (Datum, Betrag, Verwendungszweck)
3. kategorisiert regelbasiert (siehe `categorizer_rules.py`)
4. zeigt alle erkannten Buchungen zur Kontrolle im Terminal, inkl. Duplikat-Warnung
5. fragt vor dem Schreiben nach Bestaetigung (`j`/N)
6. traegt bestaetigte Zeilen in die passende Monats-Tabelle von `Finanzen.xlsx` ein

Bei mehreren Konten/Karten fuer denselben Monat: Skript einfach mehrfach mit
demselben Monat aufrufen, einmal pro PDF.

## 3. Kategorien pruefen/korrigieren

Zeilen mit Kategorie "Sonstiges" sind unbekannte Verkaeufer/Zahlungsempfaenger,
fuer die keine Regel greift. Direkt in Excel in der `Kategorie`-Spalte
korrigieren -- ganz normale Zellen, keine Formel dahinter, keine Nebenwirkung.

**Wiederkehrender Laden/Anbieter falsch/gar nicht erkannt?** Dauerhaft fixen
statt jeden Monat neu zu korrigieren: in `categorizer_rules.py` (`EXPENSE_KEYWORDS`
bzw. `INCOME_KEYWORDS`) ein Stichwort zur passenden Kategorie hinzufuegen
(kleingeschrieben, Teilstring-Suche). Wirkt sofort beim naechsten Import.

## 4. Datei oeffnen & pruefen

Beim ersten Oeffnen in Excel rechnet Excel automatisch neu -- Diagramme und
Summen in Monats-Blaettern sowie im "Bilanz"-Dashboard aktualisieren sich
dann von selbst.

## Format-Hinweise fuer den Parser

`pdf_transaction_parser.py` ist auf das Format einer VR-Bank
Kreditkarten-Umsatzaufstellung kalibriert (Datum ohne Jahr, Vorzeichen hinter
dem Betrag). Ein normaler Girokonto-Kontoauszug kann anders aussehen. Falls
`import_kontoauszug.py` mit "Keine Buchungszeilen erkannt" abbricht oder das
Jahr nicht findet: PDF-Rohtext pruefen (`pdf_extractor.extract_text(...)` in
einer Python-Shell) und das Regex in `pdf_transaction_parser.py` anpassen.

## Kapazitaets-Hinweis

Jede Monats-Tabelle hat Platz fuer bis zu 258 Ausgaben-Zeilen (Zeile 42-300)
und 58 Einnahmen-Zeilen (Zeile 42-100) -- die SUMIFS-Formeln in den
Kategorie-Summen decken genau diesen Bereich ab. Reicht das mal nicht (sehr
viele Kleinstbuchungen in einem Monat), meldet `xlsx_writer.py` das mit einer
klaren Fehlermeldung statt still Zeilen zu verlieren -- dann muesste der
Bereich in `config.py`/`xlsx_writer.py` UND die SUMIFS-Formeln im
betroffenen Monatsblatt weiter vergroessert werden.

## Einmalig eingerichtete Konventionen

- Sparen/Invest zaehlt: Trade-Republic-Buchungen + die monatliche
  Ueberweisung aufs andere Konto (Kategorie "Sparen/Invest" im Log,
  Summe wird per SUMIFS automatisch gezogen)
- Fixkosten = Tank + Selfcare + Abos (Sparbetrag zaehlt bewusst NICHT mehr mit)
- Monatsblatt-Namen haben ein Leerzeichen am Ende ("Juli ", nicht "Juli") --
  Altlast aus der urspruenglichen Datei, `xlsx_writer.py` beruecksichtigt das
