"""Cut the phase 4 annotation sessions out of the full Qwen3 and Gemma 3n data.

Writes qwen3_iaa4 and gemma3n_iaa4 into annotation_webapp/data/annotation_data/, the same
way the round 3 pair (qwen3_iaa3, gemma3n_iaa3) was made: whole sessions, copied as they are,
under a separate model name so phase 4 is keyed apart from the full 120-session models.

    python build_phase4_subset.py

Joint sessions (all three annotators, together): 2 African + 1 UK.
Independent sessions (each annotator alone):     1 African + 1 UK.

Chosen from the 112 sessions not used in rounds 1-3. UK sessions are the harder end of the
UK pool (highest WER) within the size limit; African sessions mix the two African sources.
Medical errors are the ones annotators must label (is_medical), summed over both models.
"""

import json
from pathlib import Path

DATA = Path(__file__).parent.parent / "annotation_webapp" / "data" / "annotation_data"

SESSIONS = [  # (utterance_id, how it is annotated)
    ("day1_consultation10", "joint"),                # UK, 24 medical errors, WER 0.166
    ("63e6abb7-2d8e-4df3-a52e-8e09aea762c6_0d2e6ebf48e7196f5ab076e05d590ad9_5epxs3QR", "joint"),  # AfriSpeech, 25, WER 0.167
    ("3_MyocardialInfarction", "joint"),             # Nigerian, 22, WER 0.239
    ("day2_consultation03", "independent"),          # UK, 35, WER 0.177
    ("4fc2c19e-de60-4be0-91b5-7870f60f2d99_4f72189a5c5e29dd6caa06214423b231_N96VXtHf", "independent"),  # AfriSpeech, 37, WER 0.132
]

SOURCES = [("qwen3_fixed", "qwen3_iaa4"), ("gemma3n", "gemma3n_iaa4")]


def main():
    ids = [u for u, _ in SESSIONS]
    for source, target in SOURCES:
        full = {d["utterance_id"]: d for d in json.loads((DATA / f"{source}_annotation_data.json").read_text())}
        missing = [u for u in ids if u not in full]
        if missing:
            raise SystemExit(f"{source}: missing {missing}")
        rows = []
        for i, u in enumerate(ids):
            row = dict(full[u])
            row["model"] = target
            row["index"] = i
            rows.append(row)
        (DATA / f"{target}_annotation_data.json").write_text(json.dumps(rows, indent=2))
        print(f"{target}: {len(rows)} sessions")


if __name__ == "__main__":
    main()
