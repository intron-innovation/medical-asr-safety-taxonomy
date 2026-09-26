"""Re-run Qwen3-ASR with a max_new_tokens cap that does not truncate.

The original run used chunk_seconds=300 with max_new_tokens=512. At the corpus's
~2.26 words/sec, a 300 s chunk holds ~679 words ~= 917 tokens, so 119 of 120
sessions hit the cap mid-chunk. Observed output length was 0.68 of reference and
the predicted-vs-observed correlation for that cap is r=0.95.

Writes to a NEW csv; the original results are left untouched.
"""

import os
import sys
from functools import partial

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import model_inference_qwen3_nemotron_gemma as base

MAX_NEW_TOKENS = 2048
CHUNK_SECONDS = 300
OUT_CSV = os.path.join(base.RESULTS_DIR, "qwen3_asr_results_fixed.csv")


def main():
    df = base.load_dataframe(False)
    print(f"sessions: {len(df)}  chunk={CHUNK_SECONDS}s  max_new_tokens={MAX_NEW_TOKENS}")

    processor, model = base.load_qwen3_asr()
    outputs = []
    for path in tqdm(df["audio_file"].tolist(), desc="qwen3 (fixed)"):
        outputs.append(
            base.transcribe_qwen3_asr(
                path, processor, model,
                chunk_seconds=CHUNK_SECONDS, max_new_tokens=MAX_NEW_TOKENS,
            )
        )

    out = df.copy()
    out["Qwen3-ASR"] = outputs
    os.makedirs(base.RESULTS_DIR, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    bad = sum(1 for t in outputs if str(t).startswith(("ERROR", "FILE_NOT_FOUND")))
    print(f"saved -> {OUT_CSV}")
    print(f"{len(outputs) - bad}/{len(outputs)} succeeded")

    ref = df["transcript"].fillna("").str.split().str.len()
    hyp = pd.Series(outputs).astype(str).str.split().str.len()
    print(f"median output/reference length ratio: {(hyp / ref.clip(lower=1)).median():.3f}  (was 0.680)")


if __name__ == "__main__":
    main()
