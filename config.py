"""
Zentrale Konfiguration: Secrets aus .env, Kategorienliste, Sheet-Spalten.

Sobald die echte Ziel-Google-Sheets-Datei bekannt ist, hier nur
SHEET_COLUMNS anpassen (Reihenfolge/Namen) -- der Rest der App
bleibt unveraendert.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "Ausgaben")
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json"
)

# Reihenfolge = Reihenfolge der Spalten im Google Sheet (Anzeigename -> interner Feldname).
# Muss zur ersten Zeile (Header) im Ziel-Sheet passen. Beim Anpassen an die
# echte Sheet-Struktur hier Eintraege umordnen/umbenennen -- der interne
# Feldname (rechts) muss zu den Keys aus ai_processor.py passen.
SHEET_COLUMNS: dict[str, str] = {
    "Datum": "datum",
    "Zahlungsempfaenger": "zahlungsempfaenger",
    "Kategorie": "kategorie",
    "Betrag": "betrag",
    "Verwendungszweck": "verwendungszweck",
    "Typ": "typ",
    "Quelle": "quelle",
}

# Default-Kategorien fuer die KI-Klassifizierung. Frei erweiterbar/aenderbar.
CATEGORIES = [
    "Lebensmittel",
    "Miete & Wohnen",
    "Transport & Mobilitaet",
    "Freizeit & Hobby",
    "Abos & Streaming",
    "Versicherung",
    "Gesundheit",
    "Shopping",
    "Restaurants & Cafe",
    "Reisen",
    "Bildung",
    "Spenden",
    "Einkommen",
    "Sonstiges",
]

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
DEDUPE_LOG_PATH = os.path.join(os.path.dirname(__file__), "dedupe_log.json")
