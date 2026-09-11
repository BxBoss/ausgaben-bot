# Monatlicher Workflow: Kontoauszug -> Finanzen.xlsx

Stand: komplett neu aufgebaute Datei (ein Blatt "Transaktionen" mit einer
Excel-Tabelle statt 12 separaten Monatsblättern). Kein Zeilen-Limit mehr --
neue Buchungen werden einfach unten angehängt, alle Formeln/Diagramme im
"Dashboard"-Blatt beziehen sich per Tabellen-Referenz automatisch mit.

## 1. Unterlagen holen

Sobald verfügbar, als PDF exportieren ("Umsätze" in der Bank-Onlinebanking-
Oberfläche, Zeitraum wählen):
- Girokonto-Umsätze
- Kreditkartenkonto-Umsätze (eigenes Konto für die Karte -- gleicher
  Export-Mechanismus, andere IBAN)

Speicherort egal (z.B. Desktop).

## 2. Import laufen lassen

```bash
cd "E:\_VAULT_\Claude\Projekte\Finanzen\ausgaben-bot"
venv\Scripts\python.exe import_kontoauszug.py "<Pfad zur PDF>"
```

Format (Girokonto / Kreditkartenkonto / alte Einzel-Kreditkartenabrechnung)
wird automatisch erkannt, ebenso ob es sich um Girokonto- oder
Kreditkarten-Buchungen handelt (steuert die blaue "Kreditkarte"-Markierung
in der Tabelle). Bei mehreren PDFs für denselben Zeitraum: Skript einfach
mehrfach aufrufen, einmal pro Datei.

Das Skript:
1. liest den PDF-Text, erkennt Buchungszeilen
2. kategorisiert regelbasiert (siehe `categorizer_rules.py`)
3. zeigt alle erkannten Buchungen zur Kontrolle im Terminal, inkl. Duplikat-Warnung
4. fragt vor dem Schreiben nach Bestätigung (`j`/N)
5. hängt bestätigte Zeilen unten an die "Transaktionen"-Tabelle an

## 3. Wichtig: Kartenabrechnungs-Sammelbuchungen ausschließen

Wenn du **beide** PDFs (Girokonto + Kreditkartenkonto) für denselben Monat
importierst, muss die Sammelbuchung im Girokonto ("Visa-Sonstiges" bzw. die
Zeile mit "Kartenabrechnung"/"Überweisung" im Kreditkartenkonto-Export, die
Geld vom einen aufs andere Konto schiebt) ausgeschlossen werden -- sonst
zählt der Kartenumsatz doppelt (einmal als Sammelbuchung, einmal itemisiert).

`pdf_transaction_parser.py` filtert "Überweisung"-Zeilen im
Kreditkartenkonto-Export sowie Buchungen zur Kreditkarten-IBAN im Girokonto
automatisch (`GK_EXCLUDE_IBANS`). Nur die **exakte** "Visa-Sonstiges"-Zeile
im Girokonto (Betrag + Datum) muss weiterhin manuell in
`GK_EXCLUDE_VISA_SETTLEMENTS` eingetragen werden, siehe Beispiele im
Skript-Kopf bzw. frühere Importe.

## 4. Kategorien prüfen/korrigieren

Zeilen mit Kategorie "Sonstiges" sind unbekannte Verkäufer/Zahlungsempfänger,
für die keine Regel greift. Direkt in Excel in der `Kategorie`-Spalte
korrigieren -- ganz normale Zellen, keine Formel dahinter, keine Nebenwirkung.

**Wiederkehrender Laden/Anbieter falsch/gar nicht erkannt?** Dauerhaft fixen
statt jeden Monat neu zu korrigieren: in `categorizer_rules.py`
(`EXPENSE_KEYWORDS` bzw. `INCOME_KEYWORDS`) ein Stichwort zur passenden
Kategorie hinzufügen (kleingeschrieben, Teilstring-Suche gegen Name +
vollständigen Verwendungszweck). Wirkt sofort beim nächsten Import.

## 5. Datei öffnen & prüfen

Beim ersten Öffnen in Excel rechnet Excel automatisch neu -- alle Kacheln,
die Monatsübersicht, die Kategorie-Tabelle und beide Diagramme im Dashboard
aktualisieren sich dann von selbst, da sie per Tabellen-Referenz
(`Transaktionen[Spalte]`) rechnen statt auf feste Zeilenbereiche.

## Struktur der Datei

- **Dashboard**: Kennzahlen-Kacheln (Einnahmen/Ausgaben/Netto/Sparquote),
  Monatsübersicht-Tabelle, Trend-Diagramm (Einnahmen/Ausgaben + Sparquote),
  Kreisdiagramm Ausgaben-Kategorien
- **Transaktionen**: eine Zeile pro Buchung -- Datum, Monat, Typ
  (Ausgabe/Einnahme), Kategorie, Betrag (negativ=Ausgabe/rot,
  positiv=Einnahme/grün), Verwendungszweck, Quelle (Girokonto/Kreditkarte,
  Kreditkarte zusätzlich blau markiert)

## Konventionen

- Sparen/Invest zählt: Trade-Republic-Buchungen, Bitget, + die eigene
  Überweisung aufs andere Konto (Kategorie "Sparen/Invest")
- Fixkosten-Konzept aus der alten Datei entfällt -- Kategorien sprechen für
  sich, keine separate Fixkosten/Variable-Kosten-Aufteilung mehr nötig
