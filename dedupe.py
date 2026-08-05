"""Duplikat-Erkennung: Hash aus den inhaltlichen Kernfeldern einer Transaktion,
damit dieselbe Buchung nicht zweimal ins Sheet geschrieben wird (z.B. bei
ueberlappenden Kontoauszug-Zeitraeumen oder versehentlichem Doppel-Upload)."""
from __future__ import annotations

import hashlib
from typing import Any

_KEY_FIELDS = ("datum", "betrag", "zahlungsempfaenger", "verwendungszweck")


def row_hash(transaction: dict[str, Any]) -> str:
    key = "|".join(str(transaction.get(field, "")).strip().lower() for field in _KEY_FIELDS)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def mark_duplicates(
    transactions: list[dict[str, Any]], existing_hashes: set[str]
) -> list[dict[str, Any]]:
    for tx in transactions:
        tx["_hash"] = row_hash(tx)
        tx["bereits_importiert"] = tx["_hash"] in existing_hashes
    return transactions
