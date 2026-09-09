#!/usr/bin/env python3
"""Build annotation JSON for Qwen3, Nemotron 3.5, and Gemma 3n outputs."""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

import jiwer
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluate_new_models_wer import remove_timestamps

REFERENCE_CSV = ROOT / "data" / "final_120_sampled_medical_datasets.csv"
NER_WORKBOOK = ROOT / "results" / "all_result_processed_normalized_with_ner_tagged.xlsx"
OUTPUT_DIR = ROOT / "annotation_webapp" / "data" / "annotation_data"

MODELS = {
    "qwen3": (ROOT / "results" / "qwen3_asr_results.csv", "Qwen3-ASR"),
    "nemotron35": (ROOT / "results" / "nemotron35_asr_results.csv", "Nemotron3.5-ASR"),
    "gemma3n": (ROOT / "results" / "gemma3n_e4b_asr_results.csv", "Gemma3n-E4B-ASR"),
    "whisper": (ROOT / "results" / "whisper_phi4_asr_results_all.csv", "Whisper-ASR"),
    "phi4": (ROOT / "results" / "whisper_phi4_asr_results_all.csv", "Phi-4-ASR"),
}

NER_TAG = re.compile(r"\[([A-Z_]+):\s*([^\]]+)\]")


def flatten_reference(value, source):
    if source == "UK-Dataset":
        try:
            turns = ast.literal_eval(value) if isinstance(value, str) else value
        except (ValueError, SyntaxError):
            return ""
        return " ".join(
            str(turn.get("text", ""))
            for turn in turns
            if isinstance(turn, dict) and turn.get("speaker", "").upper() in {"DOCTOR", "PATIENT"}
        )
    return str(value) if pd.notna(value) else ""


def medical_vocab(tagged_text):
    words = set()
    for match in NER_TAG.finditer(str(tagged_text or "")):
        words.update(re.findall(r"[a-zA-Z']+", match.group(2).lower()))
    return words


def overlaps(words, vocab):
    for word in words:
        if word in vocab:
            return True
        if len(word) >= 4 and any(
            len(vocab_word) >= 4 and word[:5] == vocab_word[:5] for vocab_word in vocab
        ):
            return True
    return False


def error_is_medical(error_type, reference_words, hypothesis_words, vocab):
    if error_type == "insert":
        words = hypothesis_words
    elif error_type == "delete":
        words = reference_words
    else:
        words = reference_words + hypothesis_words
    return overlaps([re.sub(r"[^a-zA-Z']", "", word).lower() for word in words], vocab)


def reconstruct(reference_words, hypothesis_words, alignment, vocab):
    output = []
    errors = []
    cursor = 0
    for chunk in alignment:
        ref_start, ref_end = chunk.ref_start_idx, chunk.ref_end_idx
        hyp_start, hyp_end = chunk.hyp_start_idx, chunk.hyp_end_idx
        if chunk.type == "equal":
            output.extend(reference_words[ref_start:ref_end])
            continue
        if chunk.type == "insert":
            content = " ".join(hypothesis_words[hyp_start:hyp_end])
            marker = f"[INS:{content}]"
        elif chunk.type == "delete":
            content = " ".join(reference_words[ref_start:ref_end])
            marker = f"[DEL:{content}]"
        else:
            before = " ".join(reference_words[ref_start:ref_end])
            after = " ".join(hypothesis_words[hyp_start:hyp_end])
            content = f"{before}->{after}"
            marker = f"[SUB:{content}]"
        is_medical = error_is_medical(
            chunk.type,
            reference_words[ref_start:ref_end],
            hypothesis_words[hyp_start:hyp_end],
            vocab,
        )
        start_idx = len(" ".join(output)) + (1 if output else 0)
        output.append(marker)
        end_idx = start_idx + len(marker)
        errors.append(
            {
                "error_id": f"{chunk.type}_{len(errors)}",
                "error_type": {"insert": "INS", "delete": "DEL", "substitute": "SUB"}[chunk.type],
                "error_match": marker,
                "error_text": content,
                "position": len(errors),
                "start_idx": start_idx,
                "end_idx": end_idx,
                "is_medical": is_medical,
            }
        )
        cursor = hyp_end
    return " ".join(output), errors


def prepare_model(model_name, result_path, output_column, reference, ner_by_id, output_path):
    results = pd.read_csv(result_path)
    if len(results) != len(reference) or set(results.utterance_id) != set(reference.utterance_id):
        raise ValueError(f"{model_name}: result/reference IDs do not match")
    entries = []
    for row in results.to_dict("records"):
        ref_row = reference.loc[reference.utterance_id == row["utterance_id"]].iloc[0]
        reference_text = remove_timestamps(flatten_reference(ref_row.transcript, ref_row.source))
        hypothesis_text = remove_timestamps(row[output_column])
        ref_words = reference_text.split()
        hyp_words = hypothesis_text.split()
        alignment = jiwer.process_words(reference_text, hypothesis_text).alignments[0]
        tagged_human = ner_by_id.get(str(row["utterance_id"]), "")
        reconstructed, errors = reconstruct(ref_words, hyp_words, alignment, medical_vocab(tagged_human))
        wer_value = row.get(f"{output_column}_WER")
        entries.append(
            {
                "utterance_id": str(row["utterance_id"]),
                "human_transcript": reference_text,
                "human_transcript_ner": tagged_human,
                "asr_transcript": hypothesis_text,
                "asr_reconstructed": reconstructed,
                "audio_file": str(row["audio_file"]),
                "model": model_name,
                "wer": float(wer_value) if pd.notna(wer_value) else None,
                "errors": errors,
                "error_count": len(errors),
                "index": len(entries),
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{model_name}: wrote {len(entries)} entries, {sum(len(e['errors']) for e in entries)} errors -> {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["all", *MODELS], default="all")
    parser.add_argument("--reference-csv", type=Path, default=REFERENCE_CSV)
    parser.add_argument("--ner-workbook", type=Path, default=NER_WORKBOOK)
    args = parser.parse_args()

    reference = pd.read_csv(args.reference_csv)
    ner_df = pd.read_excel(args.ner_workbook, usecols=["utterance_id", "norm_human_transcript_ner"])
    ner_by_id = dict(zip(ner_df.utterance_id.astype(str), ner_df.norm_human_transcript_ner.fillna("")))
    if len(reference) != 120 or len(ner_by_id) != 120:
        raise ValueError("Expected exactly 120 reference and NER rows")
    selected = MODELS if args.model == "all" else {args.model: MODELS[args.model]}
    for name, (path, column) in selected.items():
        prepare_model(
            name,
            path,
            column,
            reference,
            ner_by_id,
            OUTPUT_DIR / f"{name}_annotation_data.json",
        )


if __name__ == "__main__":
    main()
