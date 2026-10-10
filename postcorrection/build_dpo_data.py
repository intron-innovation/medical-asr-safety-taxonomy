"""Build the JSONL the DPO notebook expects, from our completed annotations.

One record per (session, ASR model) pair that has human severity labels.
Schema is dictated by the notebook's REQUIRED_FIELDS check.
"""

import collections
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent / "data" / "sample_data.jsonl"

ANN_FILES = [
    "PHI4_annotations.json",
    "qwen3_annotation.json",
    "Nemotron_annotation.json",
    "gemma3n_e4b_annotation.json",
]

# The qwen3 annotations were made against the original (truncated) run, so that is
# the hypothesis they describe. That file was retired from the webapp; read the copy.
EXTRA_STORE = Path(
    "/tmp/claude-1011/-home-kelechi/b07fd7d7-f0e2-49d9-b504-57b02cf1813c"
    "/scratchpad/qwen3_annotation_data.json.bak"
)

REGION = {
    "UK-Dataset": "UK primary care",
    "us_medical": "North American OSCE",
    "med-convo-nig": "Nigerian clinical",
    "afrispeech_medical": "African clinical",
}


def main():
    meta = pd.read_csv(ROOT / "data" / "final_120_sampled_medical_datasets.csv")
    domain = dict(zip(meta.utterance_id.astype(str), meta.source.map(REGION)))

    annotations = []
    for name in ANN_FILES:
        annotations += json.loads(
            (ROOT / "annotation_tool" / "completed_annotation" / name).read_text()
        )["annotations"]

    by_pair = collections.defaultdict(list)
    for record in annotations:
        by_pair[(record["utteranceId"], record["modelName"])].append(record)

    store = {}
    data_dir = ROOT / "annotation_webapp" / "data" / "annotation_data"
    for path in list(data_dir.glob("*_annotation_data.json")) + [EXTRA_STORE]:
        if not path.exists():
            continue
        model = path.name.replace("_annotation_data.json", "").replace(".bak", "")
        for item in json.loads(path.read_text()):
            store[(item["utterance_id"], item["model"])] = item

    rows = []
    for (session, model), errors in sorted(by_pair.items()):
        item = store.get((session, model))
        if item is None:
            print(f"  skipped {session}/{model}: no aligned data")
            continue

        rated = [
            {
                "error_id": e["errorId"],
                "error_type": e["errorType"],
                "error_match": e["errorMatch"],
                "error_class": e["errorClass"],
                "severity": e["severity"],
            }
            for e in errors
        ]
        parsed = len(item["errors"])
        severities = [e["severity"] for e in rated if e["severity"] is not None]

        rows.append({
            "id": f"{session}__{model}",
            "session_id": session,
            "source_model": model,
            "domain": domain.get(session, "clinical"),
            "hypothesis": item["asr_transcript"],
            "reference": item["human_transcript"],
            # Deliberately empty: our records are whole consultations, so there is no
            # surrounding dialogue. Putting the reference here would leak the answer.
            "context": [],
            "errors": rated,
            "annotation_summary": {
                "parsed_edits": parsed,
                "annotated_edits": len(rated),
                "coverage": round(len(rated) / parsed, 4) if parsed else 0.0,
                "max_rated_severity": max(severities) if severities else None,
            },
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nwrote {len(rows)} records -> {OUT}")
    df = pd.DataFrame([{
        "id": r["id"], "session": r["session_id"], "model": r["source_model"],
        "domain": r["domain"],
        "hyp_words": len(r["hypothesis"].split()),
        "ref_words": len(r["reference"].split()),
        "parsed": r["annotation_summary"]["parsed_edits"],
        "annotated": r["annotation_summary"]["annotated_edits"],
        "coverage": r["annotation_summary"]["coverage"],
        "max_sev": r["annotation_summary"]["max_rated_severity"],
    } for r in rows])
    print(df.to_string(index=False))
    print(f"\nunique sessions: {df.session.nunique()}  (notebook needs >= 3)")


if __name__ == "__main__":
    main()
