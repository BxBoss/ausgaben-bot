"""Ausgaben-Bot Dashboard: PDF-Kontoauszug per Drag&Drop -> KI-Kategorisierung
-> Kontrolle -> Google Sheets.

Start:
    python app.py
Dann im Browser: http://127.0.0.1:5000
"""
from __future__ import annotations

import os
import uuid

from flask import Flask, jsonify, render_template, request

import ai_processor
import config
import dedupe
import pdf_extractor
import sheets_client

app = Flask(__name__)
os.makedirs(config.UPLOAD_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html", categories=config.CATEGORIES)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "Keine Datei erhalten."}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Nur PDF-Dateien werden unterstuetzt."}), 400

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(config.UPLOAD_DIR, filename)
    file.save(path)

    try:
        raw_text = pdf_extractor.extract_text(path)
        transactions = ai_processor.process_statement(raw_text)
    except Exception as exc:  # dem Nutzer die konkrete Ursache zeigen
        return jsonify({"error": str(exc)}), 422

    for tx in transactions:
        tx["quelle"] = file.filename

    sheets_warning = None
    try:
        hashes = sheets_client.existing_hashes()
        dedupe.mark_duplicates(transactions, hashes)
    except Exception as exc:  # Sheets evtl. noch nicht konfiguriert (SETUP.md)
        sheets_warning = (
            f"Google Sheets nicht erreichbar ({exc}). "
            "Duplikat-Pruefung uebersprungen -- SETUP.md pruefen."
        )
        for tx in transactions:
            tx["_hash"] = dedupe.row_hash(tx)
            tx["bereits_importiert"] = False

    return jsonify(
        {
            "transactions": transactions,
            "categories": config.CATEGORIES,
            "sheets_warning": sheets_warning,
        }
    )


@app.route("/commit", methods=["POST"])
def commit():
    payload = request.get_json(silent=True) or {}
    transactions = payload.get("transactions", [])
    if not transactions:
        return jsonify({"error": "Keine Transaktionen zum Eintragen."}), 400

    try:
        count = sheets_client.append_transactions(transactions)
    except Exception as exc:
        return jsonify({"error": f"Eintragen ins Sheet fehlgeschlagen: {exc}"}), 502

    return jsonify({"inserted": count})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
