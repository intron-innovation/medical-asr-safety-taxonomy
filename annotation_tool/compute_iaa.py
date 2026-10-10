"""Inter-rater agreement for the BioRAMP annotation subset.

Two annotators, two models, three sessions, the same error set for both raters.
Reports severity agreement (ordinal) and taxonomy agreement (multi-label).

    python compute_iaa.py
"""

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np

DATA = Path(__file__).parent / "completed_annotation" / "inter_rater_datasets"
PAIRS = [("qwen3_iaa", "ANN009_qwen.json", "ANN010_qwen.json"),
         ("gemma3n_iaa", "ANN009_gemma.json", "ANN010_gemma.json")]

CLASSES = ["annunciation_errors", "homonym_errors_rhyming_words", "dictionary_errors",
           "stop_words", "suffix_errors", "spelling_errors", "critical_errors",
           "nonsense_errors", "words_added", "words_deleted", "not_an_error"]


def load(fname):
    d = json.loads((DATA / fname).read_text())
    recs = d["annotations"] if isinstance(d, dict) and "annotations" in d else d
    return {r["errorId"]: r for r in recs}


def cohen_kappa(a, b, weights=None):
    """Cohen's kappa. weights=None|'linear'|'quadratic'."""
    cats = sorted(set(a) | set(b))
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    if k < 2:
        return float("nan")
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[idx[x], idx[y]] += 1
    O /= O.sum()
    E = np.outer(O.sum(1), O.sum(0))
    if weights is None:
        W = 1 - np.eye(k)
    else:
        d = np.abs(np.subtract.outer(np.arange(k), np.arange(k))).astype(float)
        W = d / (k - 1) if weights == "linear" else (d / (k - 1)) ** 2
    denom = (W * E).sum()
    return float("nan") if denom == 0 else 1 - (W * O).sum() / denom


def krippendorff_alpha(a, b, level="nominal"):
    """Krippendorff's alpha for 2 coders, complete data."""
    vals = sorted(set(a) | set(b))
    idx = {v: i for i, v in enumerate(vals)}
    k = len(vals)
    if k < 2:
        return float("nan")
    o = np.zeros((k, k))
    for x, y in zip(a, b):
        o[idx[x], idx[y]] += 1
        o[idx[y], idx[x]] += 1
    n_c = o.sum(1)
    n = n_c.sum()
    if level == "ordinal":
        d2 = np.zeros((k, k))
        for i in range(k):
            for j in range(k):
                lo, hi = min(i, j), max(i, j)
                d2[i, j] = (n_c[lo:hi + 1].sum() - (n_c[i] + n_c[j]) / 2) ** 2
    else:
        d2 = 1 - np.eye(k)
    Do = (o * d2).sum() / n
    De = (np.outer(n_c, n_c) * d2).sum() - (n_c * np.diag(d2) * n_c).sum()
    De = De / (n * (n - 1))
    return float("nan") if De == 0 else 1 - Do / De


def label(k):
    if np.isnan(k):
        return "n/a"
    for lim, name in [(0.0, "poor"), (0.20, "slight"), (0.40, "fair"),
                      (0.60, "moderate"), (0.80, "substantial")]:
        if k <= lim:
            return name
    return "almost perfect"


def severity_block(pairs, tag):
    a = [x["severity"] for x, _ in pairs]
    b = [y["severity"] for _, y in pairs]
    exact = np.mean([i == j for i, j in zip(a, b)])
    within1 = np.mean([abs(i - j) <= 1 for i, j in zip(a, b)])
    kq = cohen_kappa(a, b, "quadratic")
    print(f"\n  {tag:14} n={len(pairs):3}  exact {exact:5.1%}  within-1 {within1:5.1%}"
          f"  kappa {cohen_kappa(a, b):5.2f}  wkappa(quad) {kq:5.2f} ({label(kq)})"
          f"  alpha(ord) {krippendorff_alpha(a, b, 'ordinal'):5.2f}")
    return a, b


def main():
    allpairs = []
    print("=" * 92)
    print("SEVERITY AGREEMENT  (ordinal 1-3)")
    print("=" * 92)
    for model, fa, fb in PAIRS:
        A, B = load(fa), load(fb)
        pairs = [(A[i], B[i]) for i in A if i in B]
        allpairs += pairs
        severity_block(pairs, model)
    a, b = severity_block(allpairs, "POOLED")

    print("\n  confusion (rows = ANN009, cols = ANN010)")
    lv = sorted(set(a) | set(b))
    print("        " + "".join(f"{v:>7}" for v in lv) + "    total")
    for i in lv:
        row = [sum(1 for x, y in zip(a, b) if x == i and y == j) for j in lv]
        print(f"   sev{i}" + "".join(f"{c:>7}" for c in row) + f"{sum(row):>9}")
    print("   total" + "".join(f"{sum(1 for y in b if y == j):>7}" for j in lv))

    print("\n" + "=" * 92)
    print("TAXONOMY AGREEMENT  (multi-label, per category present/absent)")
    print("=" * 92)
    print(f"\n  {'category':30}{'ANN009':>8}{'ANN010':>8}{'both':>7}{'agree%':>9}{'kappa':>8}  interpretation")
    rows = []
    for c in CLASSES:
        x = [1 if c in r["errorClass"] else 0 for r, _ in allpairs]
        y = [1 if c in r["errorClass"] else 0 for _, r in allpairs]
        if sum(x) + sum(y) == 0:
            continue
        both = sum(1 for i, j in zip(x, y) if i and j)
        agree = np.mean([i == j for i, j in zip(x, y)])
        k = cohen_kappa(x, y)
        rows.append((c, sum(x), sum(y), both, agree, k))
        print(f"  {c:30}{sum(x):>8}{sum(y):>8}{both:>7}{agree:>8.1%}{k:>8.2f}  {label(k)}")

    ks = [r[5] for r in rows if not np.isnan(r[5])]
    print(f"\n  mean kappa across {len(ks)} categories: {np.mean(ks):.2f}")

    exact_set = np.mean([set(x["errorClass"]) == set(y["errorClass"]) for x, y in allpairs])
    jac = np.mean([len(set(x["errorClass"]) & set(y["errorClass"])) /
                   max(len(set(x["errorClass"]) | set(y["errorClass"])), 1)
                   for x, y in allpairs])
    anyov = np.mean([bool(set(x["errorClass"]) & set(y["errorClass"])) for x, y in allpairs])
    print(f"  identical label set: {exact_set:.1%}   mean Jaccard: {jac:.2f}   "
          f"at least one shared label: {anyov:.1%}")

    nl9 = Counter(len(x["errorClass"]) for x, _ in allpairs)
    nl10 = Counter(len(y["errorClass"]) for _, y in allpairs)
    print(f"  labels per error  ANN009 mean {np.mean([len(x['errorClass']) for x, _ in allpairs]):.2f} {dict(sorted(nl9.items()))}")
    print(f"                    ANN010 mean {np.mean([len(y['errorClass']) for _, y in allpairs]):.2f} {dict(sorted(nl10.items()))}")

    print("\n" + "=" * 92)
    print("WHERE THEY DIVERGE  (most common disagreeing label pairs)")
    print("=" * 92)
    swaps = Counter()
    for x, y in allpairs:
        sx, sy = set(x["errorClass"]), set(y["errorClass"])
        for only9 in sx - sy:
            for only10 in sy - sx:
                swaps[tuple(sorted((only9, only10)))] += 1
    for (p, q), n in swaps.most_common(8):
        print(f"  {n:>3}x  {p}  <->  {q}")


if __name__ == "__main__":
    main()
