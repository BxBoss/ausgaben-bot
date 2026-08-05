# Setup

## 1. Python-Umgebung

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Anthropic API-Key

1. https://console.anthropic.com/settings/keys öffnen, Key erstellen.
2. `.env.example` nach `.env` kopieren und `ANTHROPIC_API_KEY` eintragen.

## 3. Google Cloud Projekt + Sheets API

1. https://console.cloud.google.com/ öffnen, neues Projekt anlegen (z.B. "ausgaben-bot").
2. Im Projekt: **APIs & Services -> Library** -> "Google Sheets API" suchen -> **Enable**.

## 4. Service Account anlegen

1. **APIs & Services -> Credentials -> Create Credentials -> Service Account**.
2. Name z.B. `ausgaben-bot`, Rolle kann übersprungen werden (nicht nötig).
3. Nach dem Anlegen: Service Account öffnen -> Tab **Keys** -> **Add Key -> Create new key -> JSON**.
4. Die heruntergeladene JSON-Datei umbenennen in `credentials.json` und in den Projektordner legen
   (`ausgaben-bot/credentials.json`). Diese Datei ist in `.gitignore` und wird **nie** committet.
5. Die E-Mail-Adresse des Service Accounts notieren (steht in der JSON-Datei als `client_email`,
   sieht aus wie `ausgaben-bot@<projekt>.iam.gserviceaccount.com`).

## 5. Ziel-Google-Sheet freigeben

1. Das gewünschte Google Sheet öffnen (oder neu anlegen).
2. **Freigeben** -> die Service-Account-E-Mail aus Schritt 4.5 als **Editor** hinzufügen.
3. Die Sheet-ID aus der URL kopieren:
   `https://docs.google.com/spreadsheets/d/`**`<SHEET_ID>`**`/edit`
4. In `.env`: `GOOGLE_SHEET_ID=<SHEET_ID>` eintragen.
5. Optional: `GOOGLE_SHEET_NAME` auf den Namen des Tabellenblatts (Reiter) setzen, in das
   geschrieben werden soll (Default: `Ausgaben`). Der Bot legt die Kopfzeile automatisch an,
   falls das Blatt leer ist.

## 6. Starten

```bash
python app.py
```

Dashboard öffnet sich unter http://127.0.0.1:5000 — PDF reinziehen, Ergebnis prüfen/korrigieren,
"Ins Google Sheet eintragen" klicken.

## Spalten anpassen

Falls dein Sheet eine andere Spaltenreihenfolge/-benennung hat als der Default
(`Datum | Zahlungsempfaenger | Kategorie | Betrag | Verwendungszweck | Typ | Quelle`),
einfach `SHEET_COLUMNS` in `config.py` anpassen — Reihenfolge im Dict = Reihenfolge im Sheet.

## Kategorien anpassen

Die Kategorienliste steht in `config.py` (`CATEGORIES`). Frei erweiterbar/umbenennbar,
wirkt sich direkt auf die KI-Klassifizierung und das Dropdown im Dashboard aus.
