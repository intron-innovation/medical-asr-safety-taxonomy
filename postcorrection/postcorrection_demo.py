"""Toy end-to-end demo of severity-weighted ASR post-correction (SFT + RL).

Runs on the 8 annotated sessions. Everything here is illustrative -- no model is
trained. The point is to show the data shapes, the prompts, and the reward.

    python postcorrection_demo.py
"""

import json
import re
from collections import Counter
from pathlib import Path

ANN_DIR = Path(__file__).parent.parent / "annotation_tool" / "completed_annotation"
FILES = [
    "PHI4_annotations.json",
    "qwen3_annotation.json",
    "Nemotron_annotation.json",
    "gemma3n_e4b_annotation.json",
]

# Labels that mark a bad reference or a non-error, not a bad hypothesis.
EXCLUDED_CLASSES = {"not_an_error", "spelling_errors"}

# Reward weight per severity level. Exponential so one severe error outweighs
# many trivial ones.
SEVERITY_WEIGHT = {0: 0, 1: 1, 2: 4, 3: 16}

# Penalty multiplier for errors the corrector *introduces*, relative to errors
# it fails to fix. >1 because confabulating clinical text is worse than leaving
# a known error in place.
LAMBDA_INTRODUCED = 2.0

TAG_RE = re.compile(r"\[(INS|DEL|SUB):(.*?)\]")


def render(tagged, side):
    """Collapse an inline-tagged alignment into one side of the pair.

    Tag convention: [SUB:reference->hypothesis], [INS:x] present only in the
    hypothesis, [DEL:x] present only in the reference.
    """

    def sub(m):
        kind, body = m.group(1), m.group(2)
        if kind == "SUB":
            ref, _, hyp = body.partition("->")
            return ref if side == "reference" else hyp
        if kind == "INS":
            return "" if side == "reference" else body
        return body if side == "reference" else ""

    return re.sub(r"\s+", " ", TAG_RE.sub(sub, tagged)).strip()


def load_annotations():
    recs = []
    for fn in FILES:
        recs += json.loads((ANN_DIR / fn).read_text())["annotations"]
    kept = [r for r in recs if not (set(r["errorClass"]) & EXCLUDED_CLASSES)]
    return recs, kept


def window(tagged, start, end, pad=220):
    return tagged[max(0, start - pad) : min(len(tagged), end + pad)]


def error_pair(error_match):
    """Return (reference_form, hypothesis_form) for one inline tag."""
    m = TAG_RE.fullmatch(error_match.strip())
    kind, body = m.group(1), m.group(2)
    if kind == "SUB":
        ref, _, hyp = body.partition("->")
        return ref.strip(), hyp.strip()
    if kind == "INS":
        return "", body.strip()
    return body.strip(), ""


def reward(candidate, errors, reference):
    """Severity-weighted reward for one candidate correction.

    Negative is bad. Two terms:
      - unfixed: annotated errors whose wrong form survives in the candidate
      - introduced: content words in the candidate absent from the reference
    """
    cand_l = candidate.lower()
    ref_words = set(re.findall(r"[a-z]+", reference.lower()))

    unfixed, fixed = [], []
    for e in errors:
        ref_form, hyp_form = error_pair(e["errorMatch"])
        w = SEVERITY_WEIGHT[e["severity"]]
        if ref_form and ref_form.lower() in cand_l:
            fixed.append((e, w))
        elif hyp_form and hyp_form.lower() in cand_l:
            unfixed.append((e, w))
        elif not ref_form:  # insertion: fixed iff the spurious word is gone
            fixed.append((e, w))
        else:
            unfixed.append((e, w))

    introduced = [w for w in re.findall(r"[a-z]+", cand_l) if w not in ref_words]
    penalty_unfixed = sum(w for _, w in unfixed)
    penalty_new = LAMBDA_INTRODUCED * len(introduced)

    return {
        "reward": -(penalty_unfixed + penalty_new),
        "fixed": len(fixed),
        "unfixed": len(unfixed),
        "weight_unfixed": penalty_unfixed,
        "introduced": introduced,
    }


SFT_PROMPT = """You are correcting the output of a speech recognition system that \
transcribed a clinical consultation. The audio was accented and the recogniser makes \
predictable mistakes: it mangles drug names and proper nouns, mishears clinical terms \
for similar-sounding everyday words, drops function words, and sometimes omits whole \
passages.

Rewrite the transcript so it says what the speakers actually said.

Rules:
- Change only what is wrong. If a span is already correct, copy it verbatim.
- Never invent clinical content. If you cannot tell what a garbled span should be, \
leave it unchanged rather than guessing a plausible drug, dose, or diagnosis.
- Preserve the speakers' own words and register. This is not a summary or a cleanup.

Transcript:
{hypothesis}

Corrected transcript:"""


def main():
    all_recs, kept = load_annotations()
    sessions = sorted({r["utteranceId"] for r in kept})

    print("=" * 78)
    print("STAGE 0 — WHAT THE ANNOTATION GIVES US")
    print("=" * 78)
    print(f"annotated errors          {len(all_recs)}")
    print(f"dropped ({'/'.join(sorted(EXCLUDED_CLASSES))})  {len(all_recs) - len(kept)}")
    print(f"usable                    {len(kept)}")
    sev = Counter(r["severity"] for r in kept)
    print("severity                  " + "  ".join(f"sev{k}={v}" for k, v in sorted(sev.items())))
    print(f"sessions                  {len(sessions)}")

    # Split on SESSION, never on utterance: the same consultation must not appear
    # on both sides or the model memorises the speakers.
    test_sessions = set(sessions[:2])
    train_sessions = set(sessions[2:])
    tr = [r for r in kept if r["utteranceId"] in train_sessions]
    te = [r for r in kept if r["utteranceId"] in test_sessions]
    print(f"\nsplit (by session)        train={len(train_sessions)} sessions / {len(tr)} errors"
          f"   test={len(test_sessions)} sessions / {len(te)} errors")

    print()
    print("=" * 78)
    print("STAGE 3 — ONE SFT TRAINING EXAMPLE")
    print("=" * 78)
    # A short, high-severity substitution reads far better than a block deletion.
    ex = min((r for r in kept if r["severity"] == 3 and r["errorType"] == "SUB"),
             key=lambda r: len(r["errorMatch"]))
    tagged = window(ex["context"]["asrReconstructed"], ex["startIdx"], ex["endIdx"], pad=150)
    hyp, ref = render(tagged, "hypothesis"), render(tagged, "reference")
    ref_form, hyp_form = error_pair(ex["errorMatch"])
    print(f"\n[session {ex['utteranceId']}  model {ex['modelName']}  "
          f"sev {ex['severity']}  {ex['errorClass']}]")
    print(f"the error: heard '{hyp_form}' where the patient said '{ref_form}'\n")
    print("--- PROMPT (what the model sees at training AND at deployment) ---")
    print(SFT_PROMPT.format(hypothesis=hyp))
    print("\n--- TARGET (only available at training) ---")
    print(ref)

    print()
    print("=" * 78)
    print("STAGE 4 — THE REWARD, SCORING THREE CANDIDATE CORRECTIONS")
    print("=" * 78)
    errs = [e for e in kept if e["utteranceId"] == ex["utteranceId"]
            and ex["startIdx"] - 150 <= e["startIdx"] <= ex["endIdx"] + 150]

    # C keeps the sentence fluent and clinically plausible but swaps in a drug
    # the patient never named -- the failure mode a severity reward can invite.
    confabulated = ref.replace(ref_form, "azithromycin", 1)
    candidates = {
        "A. do nothing (copy the ASR output)": hyp,
        "B. correct it properly": ref,
        f"C. fluent confabulation ('{ref_form}' -> 'azithromycin')": confabulated,
    }
    print(f"\nscoring against {len(errs)} annotated error(s) in this window\n")
    for name, cand in candidates.items():
        r = reward(cand, errs, ref)
        print(f"{name}")
        print(f"    reward {r['reward']:8.1f}   fixed {r['fixed']}/{len(errs)}   "
              f"unfixed weight {r['weight_unfixed']}   invented {len(r['introduced'])} word(s)")
        if r["introduced"][:6]:
            print(f"    invented: {r['introduced'][:6]}")
    print("\n  R = -[ severity-weighted unfixed errors ]"
          f"  -  {LAMBDA_INTRODUCED} x [ words not in reference ]")
    print(f"  severity weights: {SEVERITY_WEIGHT}")
    print("\n  B beats C: both are fluent, but C invented a drug. Without the second")
    print("  term, a severity-weighted reward actively encourages C.")

    print()
    print("=" * 78)
    print("STAGE 5 — WHY WER IS NOT THE METRIC")
    print("=" * 78)
    total_errors = len(kept)
    total_weight = sum(SEVERITY_WEIGHT[r["severity"]] for r in kept)
    sev3 = [r for r in kept if r["severity"] == 3]
    print(f"\n{'':22} {'count':>8} {'share':>8} {'weight':>8} {'share':>8}")
    for s in sorted(sev):
        c = sev[s]
        w = c * SEVERITY_WEIGHT[s]
        print(f"severity {s:<13} {c:>8} {c/total_errors:>7.0%} {w:>8} {w/total_weight:>7.0%}")
    print(f"\nWER treats all {total_errors} equally. The reward puts "
          f"{sum(SEVERITY_WEIGHT[r['severity']] for r in sev3)/total_weight:.0%} "
          f"of its weight on the {len(sev3)} severe errors.")
    print("\nThe severe ones in this sample:")
    for r in sev3:
        print(f"  {r['modelName']:11} {r['errorMatch'][:80]}")

    print()
    print("=" * 78)
    print("DEPLOYMENT — WHAT IS AVAILABLE WHEN, AND WHAT IS NOT")
    print("=" * 78)
    print("""
                            reference?  annotations?  reward?   what runs
  train SFT                    yes          no          no      corrector
  train RL                     yes          yes         yes     corrector + reward
  evaluate (held-out)          yes          yes         yes     corrector
  DEPLOY (new consultation)    NO           NO          NO      corrector only

  On a new consultation the pipeline is just:

      audio  ->  ASR  ->  corrector (trained weights)  ->  transcript

  No reference, no annotators, no reward -- those exist only to build and score
  the corrector. This is why the held-out split must be by SESSION: the test
  sessions stand in for consultations the model will never have seen.
""")


if __name__ == "__main__":
    main()
