"""What would round-1 agreement have been under the rules agreed at reconciliation?

A post-hoc re-scoring of the round-1 pairs, applied as a cascade so each rule's
contribution is visible. This ESTIMATES the effect of the rules; it is not a new
measurement of annotator reliability. Rule B is flagged because adopting one
rater's label for the other manufactures agreement rather than observing it.

    python simulate_rules_on_round1.py
"""

import json
from pathlib import Path

import numpy as np

DATA = Path(__file__).parent / "completed_annotation" / "inter_rater_datasets"
CLASSES = ["annunciation_errors", "homonym_errors_rhyming_words", "dictionary_errors",
           "stop_words", "suffix_errors", "spelling_errors", "nonsense_errors",
           "words_added", "words_deleted"]
TYPE_RULE = {"words_added": "INS", "words_deleted": "DEL"}


def load(fname):
    d = json.loads((DATA / fname).read_text())
    recs = d["annotations"] if isinstance(d, dict) and "annotations" in d else d
    return {r["errorId"]: r for r in recs}


def kappa(x, y, quadratic=False):
    cats = sorted(set(x) | set(y))
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    if k < 2:
        return float("nan")
    O = np.zeros((k, k))
    for a, b in zip(x, y):
        O[idx[a], idx[b]] += 1
    O /= O.sum()
    E = np.outer(O.sum(1), O.sum(0))
    if quadratic:
        d = np.abs(np.subtract.outer(np.arange(k), np.arange(k))).astype(float)
        W = (d / (k - 1)) ** 2
    else:
        W = 1 - np.eye(k)
    den = (W * E).sum()
    return float("nan") if den == 0 else 1 - (W * O).sum() / den


def score(rows, tag, note=""):
    """rows: list of (labels_a, sev_a, labels_b, sev_b)."""
    if not rows:
        print(f"  {tag:34}  (empty)")
        return
    la = [r[0] for r in rows]
    lb = [r[2] for r in rows]
    sa = [r[1] for r in rows]
    sb = [r[3] for r in rows]
    ks = []
    for c in CLASSES:
        x = [1 if c in s else 0 for s in la]
        y = [1 if c in s else 0 for s in lb]
        if sum(x) + sum(y) == 0:
            continue
        k = kappa(x, y)
        if not np.isnan(k):
            ks.append(k)
    exact_set = np.mean([p == q for p, q in zip(la, lb)])
    sev_exact = np.mean([i == j for i, j in zip(sa, sb)])
    print(f"  {tag:34} n={len(rows):3}  tax kappa {np.mean(ks):5.2f}  "
          f"same labels {exact_set:5.1%}  sev exact {sev_exact:5.1%}  "
          f"sev wkappa {kappa(sa, sb, True):5.2f}  {note}")


def main():
    pairs = []
    for m in ["qwen", "gemma"]:
        A, B = load(f"ANN009_{m}.json"), load(f"ANN010_{m}.json")
        pairs += [(A[i], B[i]) for i in A if i in B]

    base = [(set(a["errorClass"]), a["severity"], set(b["errorClass"]), b["severity"],
             a["errorType"]) for a, b in pairs]

    print("=" * 112)
    print("ROUND 1 RE-SCORED UNDER THE AGREED RULES  (estimate, not a new measurement)")
    print("=" * 112)
    score([r[:4] for r in base], "0. as annotated")

    # Rule A as proposed - read critical_errors as meaning severity 3 - is REJECTED.
    # When a rater used the tag they picked severity 2 62% of the time and 3 only
    # 29%, so it marked "clinically meaningful", not "severe". Forcing the mapping
    # breaks 6 of the 7 pairs that already agreed on severity. The label is simply
    # dropped and each rater's own severity kept.
    a_rows = [(la - {"critical_errors"}, sa, lb - {"critical_errors"}, sb, et)
              for la, sa, lb, sb, et in base]
    a_rows = [r for r in a_rows if r[0] and r[2]]
    score([r[:4] for r in a_rows], "A. critical_errors label dropped",
          f"({len(base) - len(a_rows)} lost all labels)")

    # Rule B, honest form - not_an_error means that rater declined to classify, so
    # the item carries no comparable judgement. Drop it from the comparison.
    b_keep = [r for r in a_rows if "not_an_error" not in r[0] and "not_an_error" not in r[2]]
    score([r[:4] for r in b_keep], "B. not_an_error items excluded",
          f"({len(a_rows) - len(b_keep)} dropped)")

    # Rule C - the operation rule, applied independently to each rater.
    c_rows = []
    n_c = 0
    for la, sa, lb, sb, et in b_keep:
        for s in (la, lb):
            for lab, req in TYPE_RULE.items():
                if lab in s and et != req:
                    s.discard(lab)
                    n_c += 1
        c_rows.append((la, sa, lb, sb, et))
    c_rows = [r for r in c_rows if r[0] and r[2]]
    score([r[:4] for r in c_rows], "C. + operation rule enforced",
          f"({n_c} invalid labels removed)")

    # Rule B, circular form - shown only to mark the ceiling, never to report.
    d_rows = []
    for la, sa, lb, sb, et in a_rows:
        if "not_an_error" in la and "not_an_error" not in lb:
            la, sa = set(lb), sb
        elif "not_an_error" in lb and "not_an_error" not in la:
            lb, sb = set(la), sa
        d_rows.append((la - {"not_an_error"}, sa, lb - {"not_an_error"}, sb, et))
    d_rows = [r for r in d_rows if r[0] and r[2]]
    print()
    score([r[:4] for r in d_rows], "X. not_an_error -> adopt other rater",
          "<-- CIRCULAR, do not report")
    print("\n  X imposes agreement rather than observing it: one rater's labels are copied")
    print("  onto the other, so those items agree by construction. Use B, not X.")


if __name__ == "__main__":
    main()
