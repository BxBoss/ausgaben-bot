"""Wrapper um die Google Sheets API: bestehende Zeilen lesen (fuer Dedupe)
und neue, bestaetigte Transaktionen anhaengen."""
from __future__ import annotations

from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config
import dedupe

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _service():
    creds = service_account.Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=_SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def _range(a1_suffix: str) -> str:
    return f"{config.GOOGLE_SHEET_NAME}!{a1_suffix}"


def ensure_header(service=None) -> None:
    """Schreibt die Kopfzeile, falls das Sheet noch leer ist."""
    service = service or _service()
    n_cols = len(config.SHEET_COLUMNS)
    end_col = chr(ord("A") + n_cols - 1)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=config.GOOGLE_SHEET_ID, range=_range(f"A1:{end_col}1"))
        .execute()
    )
    if not result.get("values"):
        service.spreadsheets().values().update(
            spreadsheetId=config.GOOGLE_SHEET_ID,
            range=_range("A1"),
            valueInputOption="USER_ENTERED",
            body={"values": [list(config.SHEET_COLUMNS.keys())]},
        ).execute()


def existing_hashes() -> set[str]:
    """Liest alle bisherigen Datenzeilen und berechnet daraus Dedupe-Hashes."""
    service = _service()
    ensure_header(service)
    n_cols = len(config.SHEET_COLUMNS)
    end_col = chr(ord("A") + n_cols - 1)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=config.GOOGLE_SHEET_ID, range=_range(f"A2:{end_col}"))
        .execute()
    )
    field_keys = list(config.SHEET_COLUMNS.values())
    hashes = set()
    for row in result.get("values", []):
        padded = row + [""] * (n_cols - len(row))
        record = dict(zip(field_keys, padded))
        hashes.add(dedupe.row_hash(record))
    return hashes


def append_transactions(transactions: list[dict[str, Any]]) -> int:
    """Haengt bestaetigte Transaktionen als neue Zeilen an. Gibt Anzahl zurueck."""
    if not transactions:
        return 0

    service = _service()
    ensure_header(service)

    field_keys = list(config.SHEET_COLUMNS.values())
    values = [[tx.get(key, "") for key in field_keys] for tx in transactions]

    service.spreadsheets().values().append(
        spreadsheetId=config.GOOGLE_SHEET_ID,
        range=_range("A1"),
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()
    return len(values)
