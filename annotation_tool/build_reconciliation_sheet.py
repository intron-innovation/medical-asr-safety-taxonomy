"""Build the reconciliation sheet for the IAA round.

Pairs every error the two annotators both labelled, classifies the disagreement,
and writes a CSV sorted so the call starts with what matters. Blank columns at
the end are for the agreed decision.

    python build_reconciliation_sheet.py
"""

import csv
import json
from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent / "completed_annotation" / "inter_rater_datasets"
OUT = Path(__file__).parent / "completed_annotation" / "reconciliation_sheet.csv"
PAIRS = [("qwen3_iaa", "ANN009_qwen.json", "ANN010_qwen.json"),
         ("gemma3n_iaa", "ANN009_gemma.json", "ANN010_gemma.json")]

# Categories that the IAA showed are structurally broken, not just miscalibrated:
# both never agreed on either, and both overlap another axis.
STRUCTURAL = {"critical_errors", "not_an_error"}


def load(fname):
    d = json.loads((DATA / fname).read_text())
    recs = d["annotations"] if isinstance(d, dict) and "annotations" in d else d
    return {r["errorId"]: r for r in recs}


def classify(a, b):
    """Return (priority, kind). Lower priority number = discuss first."""
    la, lb = set(a["errorClass"]), set(b["errorClass"])
    sa, sb = a["severity"], b["severity"]
    same_label, same_sev = la == lb, sa == sb

    if same_label and same_sev:
        return 5, "agreed"
    if max(sa, sb) >= 3 or abs(sa - sb) >= 2:
        return 1, "severity gap, clinical risk"
    if (la | lb) & STRUCTURAL:
        return 2, "structural category"
    if not same_label and not same_sev:
        return 3, "label + severity"
    if not same_label:
        return 3, "label only"
    return 4, "severity +/-1"


def main():
    rows = []
    for model, fa, fb in PAIRS:
        A, B = load(fa), load(fb)
        for eid in A:
            if eid not in B:
                continue
            a, b = A[eid], B[eid]
            prio, kind = classify(a, b)
            la, lb = set(a["errorClass"]), set(b["errorClass"])
            rows.append({
                "priority": prio,
                "disagreement": kind,
                "model": model,
                "session": a["utteranceId"],
                "error_type": a["errorType"],
                "error": a["errorMatch"][:160],
                "ANN009_labels": "; ".join(sorted(la)),
                "ANN009_severity": a["severity"],
                "ANN010_labels": "; ".join(sorted(lb)),
                "ANN010_severity": b["severity"],
                "shared_labels": "; ".join(sorted(la & lb)),
                "AGREED_LABELS": "",
                "AGREED_SEVERITY": "",
                "NOTES": "",
                "error_id": eid,
            })

    rows.sort(key=lambda r: (r["priority"], r["model"], r["session"]))
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    print(f"wrote {n} rows -> {OUT}\n")
    counts = Counter((r["priority"], r["disagreement"]) for r in rows)
    print(f"{'prio':>5}  {'kind':28}{'n':>5}{'share':>8}")
    for (p, k), c in sorted(counts.items()):
        print(f"{p:>5}  {k:28}{c:>5}{c / n:>8.1%}")
    dis = sum(c for (p, _), c in counts.items() if p < 5)
    print(f"\n  {n - dis} fully agreed, {dis} to reconcile ({dis / n:.0%})")


if __name__ == "__main__":
    main()
