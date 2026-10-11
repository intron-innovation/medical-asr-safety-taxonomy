"""Score the zero-shot LLM severity judge against the round-1 gold standard.

The fair benchmark is human-vs-human, not human-vs-gold: the two annotators
adjudicated the gold, so their own answers are embedded in it and their scores
against it are inflated. The judge had no such advantage.

    python score_llm_judge.py
"""

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

BASE = Path(__file__).parent / "completed_annotation"
LLM = BASE / "llm_severity_ratings"
RUNS = {"A": "ANN009_zero_shot_gpt-5.5.json", "B": "ANN010_zero_shot_gpt-5.5.json"}


def load(path):
    d = json.loads(path.read_text())
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


def row(tag, x, y, note=""):
    exact = np.mean([a == b for a, b in zip(x, y)])
    within = np.mean([abs(a - b) <= 1 for a, b in zip(x, y)])
    print(f"  {tag:34} exact {exact:5.1%}  within1 {within:6.1%}  "
          f"kappa {kappa(x, y):5.2f}  wkappa {kappa(x, y, True):5.2f}  {note}")


def main():
    A, B = load(LLM / RUNS["A"]), load(LLM / RUNS["B"])
    gold = {r["error_id"]: r for r in csv.DictReader((BASE / "gold_standard_round1.csv").open())
            if r["gold_severity"]}
    ids = [i for i in A if i in B and i in gold]

    g = [int(gold[i]["gold_severity"]) for i in ids]
    h9 = [A[i]["severity"] for i in ids]
    h10 = [B[i]["severity"] for i in ids]
    l9 = [A[i]["llm_severity"] for i in ids]
    l10 = [B[i]["llm_severity"] for i in ids]
    lm = [int(round((a + b) / 2)) for a, b in zip(l9, l10)]

    print(f"n = {len(ids)} errors with an LLM rating and a gold severity "
          f"(gemma subset only; qwen is not covered)\n")
    print("=== against the gold standard ===")
    row("human ANN009", h9, g, "<- inflated, helped set the gold")
    row("human ANN010", h10, g, "<- inflated, helped set the gold")
    row("LLM run A", l9, g)
    row("LLM run B", l10, g)
    row("LLM mean of runs", lm, g)
    print("\n=== the fair benchmark ===")
    row("human vs human", h9, h10, "<- the bar the judge must clear")
    row("LLM vs itself", l9, l10, "<- the judge's own ceiling")

    print("\n=== gold (rows) against LLM mean (cols) ===")
    lv = [1, 2, 3]
    print("        " + "".join(f"{v:>7}" for v in lv))
    for i in lv:
        print(f"   gold{i}" + "".join(
            f"{sum(1 for a, b in zip(g, lm) if a == i and b == j):>7}" for j in lv))
    over = sum(1 for a, b in zip(g, lm) if b > a)
    under = sum(1 for a, b in zip(g, lm) if b < a)
    print(f"\n  judge rates higher than gold {over}x, lower {under}x "
          f"-> {'harsher' if over > under else 'softer'} than the consensus")
    print(f"  severity-3 recall: {sum(1 for a, b in zip(g, lm) if a == 3 and b == 3)}"
          f"/{g.count(3)} of the gold's severe errors were called severe")


if __name__ == "__main__":
    main()
