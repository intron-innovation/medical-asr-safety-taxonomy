#!/usr/bin/env python3
"""Explode completed annotations into one CSV row per taxonomy assignment."""

import argparse
import json
from pathlib import Path

import pandas as pd


def load_annotations(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("annotations"), list):
        return data["annotations"]
    if isinstance(data, dict) and isinstance(data.get("annotators"), dict):
        rows = []
        for annotator_id, annotator in data["annotators"].items():
            for annotation in annotator.get("annotations", []):
                row = dict(annotation)
                row.setdefault("annotatorId", annotator_id)
                rows.append(row)
        return rows
    raise ValueError(f"Unsupported annotation JSON shape: {path}")


def taxonomy_values(annotation):
    values = annotation.get("errorClass") or annotation.get("taxonomy") or []
    if isinstance(values, str):
        values = [values]
    return [str(value).strip() for value in values if str(value).strip()]


def annotation_rows(paths):
    rows = []
    for path in paths:
        for annotation in load_annotations(path):
            context = annotation.get("context") or {}
            taxonomies = taxonomy_values(annotation)
            if not taxonomies:
                continue
            example = annotation.get("errorMatch") or annotation.get("errorText") or ""
            for taxonomy in taxonomies:
                rows.append(
                    {
                        "taxonomy": taxonomy,
                        "annotated_example": example,
                        "severity": annotation.get("severity"),
                        "session_annotated": annotation.get("utteranceId", ""),
                        "model_used": annotation.get("modelName") or annotation.get("model", ""),
                        "annotator_id": annotation.get("annotatorId", ""),
                        "error_type": annotation.get("errorType", ""),
                        "error_id": annotation.get("errorId", annotation.get("id", "")),
                        "source_file": path.name,
                        "human_transcript": context.get("humanTranscript", ""),
                        "asr_reconstructed": context.get("asrReconstructed", ""),
                    }
                )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Completed annotation JSON exports")
    parser.add_argument("--output", type=Path, default=Path("results/taxonomy_annotation_examples.csv"))
    args = parser.parse_args()

    rows = annotation_rows(args.inputs)
    if not rows:
        raise SystemExit("No annotations with taxonomy/errorClass values were found.")

    output = pd.DataFrame(rows)
    output = output.sort_values(["taxonomy", "session_annotated", "model_used", "annotator_id"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)

    print(f"Wrote {len(output)} taxonomy-assignment rows from {len(set(output.error_id))} unique annotations")
    print(f"Taxonomies: {', '.join(sorted(output.taxonomy.unique()))}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
