#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify

try:
    # Enable permissive CORS for local file:// origins
    from flask_cors import CORS
    CORS_AVAILABLE = True
except Exception:
    CORS_AVAILABLE = False

APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "annotations_store.json"

app = Flask(__name__)
if CORS_AVAILABLE:
    CORS(app, resources={r"/*": {"origins": "*"}})


def _init_store() -> Dict[str, Any]:
    return {
        "version": "1.0",
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "annotators": {}
    }


def load_store() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        store = _init_store()
        DATA_FILE.write_text(json.dumps(store, indent=2))
        return store
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If corrupted, back up and start fresh
        backup = DATA_FILE.with_suffix(".bak")
        try:
            os.replace(DATA_FILE, backup)
        except Exception:
            pass
        store = _init_store()
        DATA_FILE.write_text(json.dumps(store, indent=2))
        return store


def save_store(store: Dict[str, Any]) -> None:
    store["updatedAt"] = datetime.utcnow().isoformat() + "Z"
    DATA_FILE.write_text(json.dumps(store, indent=2))


@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok", "dataFile": str(DATA_FILE), "exists": DATA_FILE.exists()})


@app.route("/annotations", methods=["POST"])
def save_annotation() -> Any:
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON"}), 400

    required = [
        "annotatorId", "annotatorName", "annotatorEmail",
        "utteranceId", "errorType", "errorMatch",
        "taxonomy", "severity", "timestamp"
    ]
    missing = [k for k in required if k not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    store = load_store()
    annotators = store.setdefault("annotators", {})

    ann_id = payload["annotatorId"]
    ann_entry = annotators.setdefault(ann_id, {
        "name": payload["annotatorName"],
        "email": payload["annotatorEmail"],
        "affiliation": payload.get("affiliation"),
        "annotations": []
    })

    # upsert logic: match on tuple key
    key = (
        payload["utteranceId"], payload["errorType"], payload["errorMatch"]
    )

    def match(entry: Dict[str, Any]) -> bool:
        return (
            entry.get("utteranceId") == key[0]
            and entry.get("errorType") == key[1]
            and entry.get("errorMatch") == key[2]
        )

    existing_idx = next((i for i, e in enumerate(ann_entry["annotations"]) if match(e)), None)

    record = {
        "utteranceId": payload["utteranceId"],
        "errorType": payload["errorType"],
        "errorMatch": payload["errorMatch"],
        "taxonomy": payload["taxonomy"],
        "severity": payload["severity"],
        "timestamp": payload["timestamp"],
        "context": {
            "humanTranscript": payload.get("humanTranscript"),
            "asrReconstructed": payload.get("asrReconstructed"),
            "utteranceIndex": payload.get("utteranceIndex"),
        }
    }

    if existing_idx is None:
        ann_entry["annotations"].append(record)
        action = "inserted"
    else:
        ann_entry["annotations"][existing_idx] = record
        action = "updated"

    save_store(store)
    return jsonify({"status": "ok", "action": action, "count": len(ann_entry["annotations"])})


if __name__ == "__main__":
    port = int(os.environ.get("ANNOTATION_SERVER_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
