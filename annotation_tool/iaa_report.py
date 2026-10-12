"""Final IAA report: per-label kappa, overall kappa, severity per level and overall.

    python iaa_report.py [round]

Two taxonomy columns are reported.

  strict  - a category counts as agreed only if both raters ticked it. The standard
            multi-label IAA computation.
  union   - under the union rule, where one rater's label set is a strict subset of
            the other's, the extra labels are credited to both: the subset rater is
            read as having left them unmarked rather than having rejected them.
            Generous, and must be declared as such when reported.

Severity takes a single value per error, so no union applies; those figures are
measured directly.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

DATA = Path(__file__).parent / "completed_annotation" / "inter_rater_datasets"
ROUNDS = {1: "", 2: "_round2"}
CLASSES = ["annunciation_errors", "homonym_errors_rhyming_words", "dictionary_errors",
           "stop_words", "suffix_errors", "spelling_errors", "nonsense_errors",
           "words_added", "words_deleted", "critical_errors", "not_an_error"]
SEV_NAME = {0: "0 None", 1: "1 Minor", 2: "2 Moderate", 3: "3 Severe"}


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


def alpha_ordinal(x, y):
    vals = sorted(set(x) | set(y))
    idx = {v: i for i, v in enumerate(vals)}
    k = len(vals)
    if k < 2:
        return float("nan")
    o = np.zeros((k, k))
    for a, b in zip(x, y):
        o[idx[a], idx[b]] += 1
        o[idx[b], idx[a]] += 1
    n_c = o.sum(1)
    n = n_c.sum()
    d2 = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            lo, hi = min(i, j), max(i, j)
            d2[i, j] = (n_c[lo:hi + 1].sum() - (n_c[i] + n_c[j]) / 2) ** 2
    Do = (o * d2).sum() / n
    De = ((np.outer(n_c, n_c) * d2).sum() - (n_c * np.diag(d2) * n_c).sum()) / (n * (n - 1))
    return float("nan") if De == 0 else 1 - Do / De


def band(k):
    if np.isnan(k):
        return "n/a"
    for lim, name in [(0.0, "poor"), (0.20, "slight"), (0.40, "fair"),
                      (0.60, "moderate"), (0.80, "substantial")]:
        if k <= lim:
            return name
    return "almost perfect"


def main():
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    sfx = ROUNDS[rnd]
    pairs = []
    for m in ["qwen", "gemma"]:
        A, B = load(f"ANN009_{m}{sfx}.json"), load(f"ANN010_{m}{sfx}.json")
        pairs += [(A[i], B[i]) for i in A if i in B]

    la = [set(a["errorClass"]) for a, _ in pairs]
    lb = [set(b["errorClass"]) for _, b in pairs]
    # union crediting: only where one set strictly contains the other
    ua, ub = [], []
    n_credited = 0
    for x, y in zip(la, lb):
        if x < y or y < x:
            ua.append(x | y)
            ub.append(x | y)
            n_credited += 1
        else:
            ua.append(x)
            ub.append(y)

    print("=" * 96)
    print(f"IAA REPORT - ROUND {rnd}   ANN009 vs ANN010   n = {len(pairs)} paired errors")
    print("=" * 96)

    print("\nTAXONOMY - kappa per label\n")
    print(f"  {'category':30}{'ANN009':>8}{'ANN010':>8}{'both':>6}{'strict k':>10}{'union k':>9}   interpretation (union)")
    strict, union = [], []
    for c in CLASSES:
        x = [1 if c in s else 0 for s in la]
        y = [1 if c in s else 0 for s in lb]
        if sum(x) + sum(y) == 0:
            continue
        xs = [1 if c in s else 0 for s in ua]
        ys = [1 if c in s else 0 for s in ub]
        ks, ku = kappa(x, y), kappa(xs, ys)
        both = sum(1 for i, j in zip(x, y) if i and j)
        if not np.isnan(ks):
            strict.append(ks)
        if not np.isnan(ku):
            union.append(ku)
        print(f"  {c:30}{sum(x):>8}{sum(y):>8}{both:>6}{ks:>10.2f}{ku:>9.2f}   {band(ku)}")

    print(f"\n  {'OVERALL (mean of per-label kappa)':30}{'':22}{np.mean(strict):>10.2f}{np.mean(union):>9.2f}"
          f"   {band(np.mean(union))}")
    ex_s = np.mean([p == q for p, q in zip(la, lb)])
    ex_u = np.mean([p == q for p, q in zip(ua, ub)])
    ja_s = np.mean([len(p & q) / max(len(p | q), 1) for p, q in zip(la, lb)])
    print(f"  {'identical label set':30}{'':22}{ex_s:>10.1%}{ex_u:>9.1%}")
    print(f"  {'mean Jaccard':30}{'':22}{ja_s:>10.2f}{1.0 if False else np.mean([len(p & q) / max(len(p | q), 1) for p, q in zip(ua, ub)]):>9.2f}")
    print(f"\n  union crediting applied to {n_credited} of {len(pairs)} pairs "
          f"({n_credited / len(pairs):.1%}) where one label set strictly contained the other")

    sa = [a["severity"] for a, _ in pairs]
    sb = [b["severity"] for _, b in pairs]
    print("\n" + "=" * 96)
    print("SEVERITY - per level (one vs rest)\n")
    print(f"  {'level':14}{'ANN009':>8}{'ANN010':>8}{'both':>6}{'either':>8}{'Jaccard':>9}{'kappa':>8}   interpretation")
    for L in sorted(set(sa) | set(sb)):
        x = [1 if v == L else 0 for v in sa]
        y = [1 if v == L else 0 for v in sb]
        both = sum(1 for i, j in zip(x, y) if i and j)
        either = sum(1 for i, j in zip(x, y) if i or j)
        k = kappa(x, y)
        print(f"  {SEV_NAME.get(L, L):14}{sum(x):>8}{sum(y):>8}{both:>6}{either:>8}"
              f"{both / max(either, 1):>9.2f}{k:>8.2f}   {band(k)}")

    print("\n  OVERALL SEVERITY")
    print(f"    exact agreement      {np.mean([i == j for i, j in zip(sa, sb)]):.1%}")
    print(f"    within one level     {np.mean([abs(i - j) <= 1 for i, j in zip(sa, sb)]):.1%}")
    print(f"    Cohen kappa          {kappa(sa, sb):.2f}   {band(kappa(sa, sb))}")
    print(f"    quadratic weighted   {kappa(sa, sb, True):.2f}   {band(kappa(sa, sb, True))}   <- report this one")
    print(f"    Krippendorff alpha   {alpha_ordinal(sa, sb):.2f}")

    print("\n  confusion (rows ANN009, cols ANN010)")
    lv = sorted(set(sa) | set(sb))
    print("        " + "".join(f"{v:>7}" for v in lv) + "    total")
    for i in lv:
        r = [sum(1 for a, b in zip(sa, sb) if a == i and b == j) for j in lv]
        print(f"   sev{i}" + "".join(f"{c:>7}" for c in r) + f"{sum(r):>9}")
    print("   total" + "".join(f"{sum(1 for b in sb if b == j):>7}" for j in lv))


if __name__ == "__main__":
    main()
