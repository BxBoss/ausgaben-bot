"""Claude extrahiert Transaktionen aus rohem Kontoauszug-Text und
kategorisiert sie in einem Aufruf (strukturierter Output via Tool Use)."""
from __future__ import annotations

from typing import Any

import anthropic

import config

_TRANSACTIONS_TOOL = {
    "name": "record_transactions",
    "description": (
        "Speichert die aus dem Kontoauszug extrahierten Transaktionen, "
        "jede bereits einer Kategorie zugeordnet."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "transactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "datum": {
                            "type": "string",
                            "description": "Buchungsdatum im Format YYYY-MM-DD",
                        },
                        "zahlungsempfaenger": {
                            "type": "string",
                            "description": "Name des Empfaengers bzw. Auftraggebers, bereinigt/normalisiert",
                        },
                        "verwendungszweck": {
                            "type": "string",
                            "description": "Buchungstext / Verwendungszweck, so wie im Auszug vermerkt",
                        },
                        "betrag": {
                            "type": "number",
                            "description": "Betrag mit Vorzeichen: negativ = Ausgabe, positiv = Einnahme",
                        },
                        "typ": {
                            "type": "string",
                            "enum": ["Ausgabe", "Einnahme"],
                        },
                        "kategorie": {
                            "type": "string",
                            "enum": config.CATEGORIES,
                        },
                    },
                    "required": [
                        "datum",
                        "zahlungsempfaenger",
                        "verwendungszweck",
                        "betrag",
                        "typ",
                        "kategorie",
                    ],
                },
            }
        },
        "required": ["transactions"],
    },
}

_SYSTEM_PROMPT = f"""Du extrahierst Buchungen aus dem Rohtext eines deutschen Bank-Kontoauszugs (PDF-Text, Layout je nach Bank unterschiedlich).

Regeln:
- Erkenne jede einzelne Buchungszeile (nicht Kontostand/Saldo-Zeilen, nicht Kopf-/Fusszeilen, nicht Seitenzahlen).
- Zahlungsempfaenger: der tatsaechliche Name des Empfaengers/Auftraggebers, ohne technische Zusaetze wie IBAN/BIC-Wiederholungen.
- Verwendungszweck: der Buchungstext/Referenztext, so wie er im Auszug steht (gekuerzt falls sehr lang).
- Betrag: als Zahl mit Punkt als Dezimaltrennzeichen, Vorzeichen negativ fuer Ausgaben, positiv fuer Einnahmen.
- Kategorie: waehle die passendste aus der vorgegebenen Liste anhand von Empfaenger und Verwendungszweck. Gehaltszahlungen/Ueberweisungseingaenge -> "Einkommen".
- Gib ausschliesslich ueber das Tool "record_transactions" strukturierte Daten zurueck, keinen Fliesstext.
"""


def process_statement(raw_text: str) -> list[dict[str, Any]]:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY ist nicht gesetzt (.env pruefen).")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=8192,
        system=_SYSTEM_PROMPT,
        tools=[_TRANSACTIONS_TOOL],
        tool_choice={"type": "tool", "name": "record_transactions"},
        messages=[
            {"role": "user", "content": f"Kontoauszug-Rohtext:\n\n{raw_text}"}
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "record_transactions":
            return block.input.get("transactions", [])

    raise RuntimeError("Claude hat keine strukturierten Transaktionen zurueckgegeben.")
