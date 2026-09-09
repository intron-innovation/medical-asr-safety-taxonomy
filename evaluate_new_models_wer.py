#!/usr/bin/env python3
"""
Compute per-session WER for the three new ASR models (Qwen3-ASR, Nemotron 3.5 ASR,
Gemma 3n E4B) against the human reference transcript, using the same text
normalization as result_process.ipynb (see remove_timestamps / extract_utterances).

Usage:
    python evaluate_new_models_wer.py [--smoke-test]

Writes results/new_models_wer.csv (per-session) and prints an aggregate summary.
"""

import argparse
import ast
import re

import contractions
import jiwer
import pandas as pd
from num2words import num2words

DATA_FULL = "data/final_120_sampled_medical_datasets.csv"
DATA_SMOKE = "results/selected_session_for_test_2.xlsx.csv"

MODEL_RESULTS = {
    "Qwen3-ASR": "results/qwen3_asr_results.csv",
    "Nemotron3.5-ASR": "results/nemotron35_asr_results.csv",
    "Gemma3n-E4B-ASR": "results/gemma3n_e4b_asr_results.csv",
    "Whisper-ASR": "results/whisper_phi4_asr_results_all.csv",
    "Phi-4-ASR": "results/whisper_phi4_asr_results_all.csv",
}


def extract_utterances(turns):
    """Flatten the UK-Dataset's [{'speaker':..,'text':..}, ...] transcript format to plain text."""
    if isinstance(turns, str):
        try:
            turns = ast.literal_eval(turns)
        except (ValueError, SyntaxError):
            return ""
    if not turns or not hasattr(turns, "__iter__"):
        return ""
    formatted = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        speaker = turn.get("speaker", "").upper()
        text = turn.get("text", "")
        if "DOCTOR" in speaker:
            formatted.append(f"DOCTOR: {text}")
        elif "PATIENT" in speaker:
            formatted.append(f"PATIENT: {text}")
    return " ".join(formatted)


def remove_timestamps(text: str) -> str:
    """Same normalization used in result_process.ipynb, so WERs are comparable to the older models."""
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r"\b\d{1,2}:\d{1,2}:\d{1,3}\b", "", text)
    cleaned = cleaned.replace("\n", " ").replace("\r", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\[?[Ss]peaker\s*\d+\]?:", "", cleaned)
    cleaned = re.sub(r"\b[Dd]:", "", cleaned)
    cleaned = re.sub(r"\b[Pp]:", "", cleaned)
    cleaned = re.sub(r"\bDOCTOR:\s*", "", cleaned)
    cleaned = re.sub(r"\bPATIENT:\s*", "", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = contractions.fix(cleaned)
    cleaned = re.sub(r"\d+", lambda x: num2words(int(x.group())), cleaned)
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", cleaned)
    cleaned = cleaned.lower()
    cleaned = re.sub(r"\bok\b", "okay", cleaned)
    cleaned = re.sub(r"\bohh\b", "oh", cleaned)
    cleaned = re.sub(r"\bdr\b", "doctor", cleaned)
    cleaned = re.sub(r"\bpt\b", "patient", cleaned)
    cleaned = re.sub(r"\b(um|uh|erm|uhm|mmhmm|ah|umm)\b", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def load_reference(smoke_test: bool) -> pd.DataFrame:
    if smoke_test:
        df = pd.read_csv(DATA_SMOKE)
        df = df.rename(columns={"human-transcript": "transcript"})
        return df[["utterance_id", "transcript", "duration", "source"]] if "source" in df.columns else df
    df = pd.read_csv(DATA_FULL)
    uk_mask = df["source"] == "UK-Dataset"
    df.loc[uk_mask, "transcript"] = df.loc[uk_mask, "transcript"].apply(extract_utterances)
    return df


def wer_for(ref: str, hyp: str):
    ref, hyp = ref.strip(), hyp.strip()
    if not ref:
        return None
    if not hyp:
        return 1.0
    return jiwer.process_words(ref, hyp).wer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    ref_df = load_reference(args.smoke_test)
    ref_df["norm_reference"] = ref_df["transcript"].apply(remove_timestamps)

    eval_df = ref_df[["utterance_id", "duration", "source", "norm_reference"]].copy()

    for col, path in MODEL_RESULTS.items():
        try:
            model_df = pd.read_csv(path)
        except FileNotFoundError:
            print(f"Skipping {col}: {path} not found")
            continue
        model_df = model_df[["utterance_id", col]]
        eval_df = eval_df.merge(model_df, on="utterance_id", how="left")
        norm_col = f"norm_{col}"
        eval_df[norm_col] = eval_df[col].apply(remove_timestamps)
        eval_df[f"{col}_wer"] = eval_df.apply(
            lambda row: wer_for(row["norm_reference"], row[norm_col]), axis=1
        )
        eval_df[f"{col}_error"] = eval_df[col].astype(str).str.startswith(("ERROR", "FILE_NOT_FOUND"))
        model_df[f"{col}_WER"] = model_df["utterance_id"].map(
            eval_df.set_index("utterance_id")[f"{col}_wer"]
        )
        full_model_df = pd.read_csv(path)
        full_model_df[f"{col}_WER"] = full_model_df["utterance_id"].map(
            model_df.set_index("utterance_id")[f"{col}_WER"]
        )
        full_model_df.to_csv(path, index=False)
        print(f"Updated {path} with {col}_WER")

    wer_cols = [f"{c}_wer" for c in MODEL_RESULTS if f"{c}_wer" in eval_df.columns]
    eval_df["best_wer"] = eval_df[wer_cols].min(axis=1)
    eval_df["best_models"] = eval_df.apply(
        lambda row: ", ".join(
            col.removesuffix("_wer") for col in wer_cols if row[col] == row["best_wer"]
        ),
        axis=1,
    )
    print("=== Aggregate WER (mean over sessions with a valid WER) ===")
    for col in MODEL_RESULTS:
        wer_col = f"{col}_wer"
        if wer_col not in eval_df.columns:
            continue
        err_col = f"{col}_error"
        n_errors = int(eval_df[err_col].sum()) if err_col in eval_df.columns else 0
        vals = eval_df[wer_col].dropna()
        if len(vals) == 0:
            print(f"{col}: no valid rows")
            continue
        print(
            f"{col}: mean={vals.mean():.4f} median={vals.median():.4f} "
            f"min={vals.min():.4f} max={vals.max():.4f} n={len(vals)} errors={n_errors}"
        )

    print("\n=== Best model per session (ties retained) ===")
    print(eval_df["best_models"].value_counts().to_string())

    print("\n=== Per-session WER ===")
    print(eval_df[["utterance_id", "duration", "source"] + wer_cols + ["best_wer", "best_models"]].to_string(index=False))


if __name__ == "__main__":
    main()
