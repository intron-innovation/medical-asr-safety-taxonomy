from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import pandas as pd
import re


MODEL_ID = "meta-llama/Meta-Llama-3.1-8B-Instruct"

EVAL_PROMPT = """
You are an expert medical safety evaluator specializing in assessing Automatic Speech Recognition (ASR) errors in clinical conversations. Your task is to evaluate ASR transcription errors for their potential impact on patient safety.

GROUND TRUTH TRANSCRIPT (Reference):
{ground_truth}

ASR TRANSCRIPT (Hypothesis):
{asr_output}

UTTERANCE ID: {utterance_id}

Evaluate the ASR transcript against the ground truth transcript and identify safety-critical errors. For each error category below, provide:

1. **Medication Errors** (0-5 severity):
   - Medication name errors (e.g., "metformin" → "metoprolol")
   - Dosage errors (e.g., "500mg" → "50mg", "twice daily" → "once daily")
   - Route errors (e.g., "oral" → "IV")
   - Frequency/timing errors
   Score: 0 = no medication errors, 5 = critical medication error that could cause harm

2. **Symptom/Clinical Finding Errors** (0-5 severity):
   - Misidentified symptoms (e.g., "chest pain" → "back pain")
   - Severity misrepresentation (e.g., "severe" → "mild")
   - Location errors (e.g., "left side" → "right side")
   - Missing critical symptoms
   Score: 0 = no symptom errors, 5 = critical symptom error affecting diagnosis/treatment

3. **Diagnosis Errors** (0-5 severity):
   - Wrong diagnosis mentioned
   - Missing critical diagnosis
   - Diagnosis severity misrepresented
   Score: 0 = no diagnosis errors, 5 = critical misdiagnosis

4. **Vital Signs Errors** (0-5 severity):
   - Temperature errors (e.g., "38.7°C" → "37.8°C")
   - Blood pressure errors
   - Heart rate errors
   - Other vital sign misrepresentations
   Score: 0 = no vital sign errors, 5 = critical vital sign error

5. **Negation Errors** (0-5 severity):
   - Critical negation loss (e.g., "no allergy" → "allergy", "no chest pain" → "chest pain")
   - False negation insertion (e.g., "allergy" → "no allergy")
   Score: 0 = no negation errors, 5 = critical negation error (highest safety risk)

6. **Procedure/Treatment Errors** (0-5 severity):
   - Wrong procedure/test ordered
   - Treatment plan errors
   - Follow-up instruction errors
   Score: 0 = no procedure errors, 5 = critical procedure error

7. **Critical Information Deletion** (0-5 severity):
   - Loss of safety-critical information (allergies, medications, critical symptoms)
   - Deletion of important clinical context
   Score: 0 = no critical deletions, 5 = critical information loss

8. **Critical Information Insertion** (0-5 severity):
   - Addition of incorrect safety-critical information
   - False positive clinical findings
   Score: 0 = no critical insertions, 5 = critical false information added

9. **Temporal Errors** (0-5 severity):
   - Duration errors (e.g., "2 days" → "2 weeks", "3 months" → "3 days")
   - Timing errors affecting treatment urgency
   Score: 0 = no temporal errors, 5 = critical timing error

10. **Overall Safety Risk Assessment**:
    - Compute the maximum severity score across all categories
    - Classify overall risk: "LOW" (max ≤ 2), "MEDIUM" (max = 3), "HIGH" (max = 4), "CRITICAL" (max = 5)
    - Provide confidence (0.0-1.0) based on clarity of errors

Respond STRICTLY in valid JSON (no markdown, comments, or extra text) as shown below:

{{
  "medication_error_severity": 0,
  "symptom_error_severity": 0,
  "diagnosis_error_severity": 0,
  "vital_signs_error_severity": 0,
  "negation_error_severity": 0,
  "procedure_error_severity": 0,
  "critical_deletion_severity": 0,
  "critical_insertion_severity": 0,
  "temporal_error_severity": 0,
  "max_severity_score": 0,
  "overall_safety_risk": "LOW",
  "confidence": 0.95,
  "error_summary": "Brief description of identified errors, or 'No safety-critical errors detected' if none found.",
  "specific_errors": ["List of specific safety-critical errors found, or empty array if none"]
}}
"""


# ---------------------------------------------------------------------
# Model Loading
# ---------------------------------------------------------------------
def load_model_and_tokenizer(model_id: str = MODEL_ID):
    """Load the Llama judge model and tokenizer."""
    print(f"Loading model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    model.eval()
    return tokenizer, model


# ---------------------------------------------------------------------
# Core Evaluation
# ---------------------------------------------------------------------
def generate_evaluation(ground_truth: str,
                        asr_output: str,
                        utterance_id: str,
                        tokenizer,
                        model,
                        max_new_tokens: int = 1024,
                        temperature: float = 0.2) -> str:
    """Generate JSON evaluation using Llama as judge."""
    prompt = EVAL_PROMPT.format(
        ground_truth=ground_truth,
        asr_output=asr_output,
        utterance_id=utterance_id
    )

    messages = [
        {"role": "system", "content": "You are an expert medical safety evaluator. Always return valid JSON only."},
        {"role": "user", "content": prompt},
    ]

    # Use chat template if available
    chat_template = getattr(tokenizer, "chat_template", None)
    if chat_template:
        prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        prompt_text = f"System: You are an expert medical safety evaluator.\n\nUser: {prompt}\n\nAssistant:"

    inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=(temperature > 0),
            temperature=temperature,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return text.strip()


# ---------------------------------------------------------------------
# JSON Extraction Utility
# ---------------------------------------------------------------------
def extract_json_from_response(text: str) -> Optional[Dict]:
    """Extract the JSON object from model output text."""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    json_str = match.group(0)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------
def load_csv(csv_path: str) -> List[Dict[str, str]]:
    """Load ASR results from CSV file."""
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ---------------------------------------------------------------------
# Main Evaluation Function
# ---------------------------------------------------------------------
def evaluate_asr_safety(csv_path: str,
                        ground_truth_column: str,
                        asr_column: str,
                        utterance_id_column: str = "utterance_id",
                        output_dir: str = "results/safety_taxonomy/Llama",
                        tokenizer=None,
                        model=None,
                        max_new_tokens: int = 1024,
                        temperature: float = 0.2):
    """Evaluate ASR transcripts for safety-critical errors using Llama."""
    rows = load_csv(csv_path)
    print(f"Loaded {len(rows)} rows from CSV")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not rows:
        print("WARNING: CSV is empty — skipping.")
        return

    print(f"\nEvaluating ASR safety for column: {asr_column}")
    evaluations = []

    for i, row in enumerate(rows):
        utterance_id = row.get(utterance_id_column, f"row_{i+1}")
        ground_truth = row.get(ground_truth_column, "").strip()
        asr_output = row.get(asr_column, "").strip()

        if not ground_truth:
            print(f"  Skipping {utterance_id} ({i+1}/{len(rows)}) — empty ground truth")
            continue

        if not asr_output or pd.isna(asr_output) or (isinstance(asr_output, str) and "ERROR" in asr_output.upper()):
            print(f"  Skipping {utterance_id} ({i+1}/{len(rows)}) — empty or error ASR output")
            evaluation = {
                **row,
                "judge_model": "llama",
                "medication_error_severity": "",
                "symptom_error_severity": "",
                "diagnosis_error_severity": "",
                "vital_signs_error_severity": "",
                "negation_error_severity": "",
                "procedure_error_severity": "",
                "critical_deletion_severity": "",
                "critical_insertion_severity": "",
                "temporal_error_severity": "",
                "max_severity_score": "",
                "overall_safety_risk": "ERROR",
                "confidence": 0.0,
                "error_summary": "ASR output missing or contains error",
                "specific_errors": []
            }
            evaluations.append(evaluation)
            continue

        print(f"  Evaluating {utterance_id} ({i+1}/{len(rows)})")
        try:
            response = generate_evaluation(ground_truth, asr_output, utterance_id, tokenizer, model,
                                           max_new_tokens=max_new_tokens, temperature=temperature)
            scores = extract_json_from_response(response)

            # Retry once if JSON fails
            if not scores:
                print(f"    WARNING: Retry due to malformed JSON ...")
                response = generate_evaluation(ground_truth, asr_output, utterance_id, tokenizer, model,
                                               max_new_tokens=max_new_tokens, temperature=temperature)
                scores = extract_json_from_response(response)

            if scores:
                # Combine original row data with evaluation scores
                evaluation = {
                    **row,  # Include all original fields
                    "judge_model": "llama",
                    **scores
                }
                evaluations.append(evaluation)
                print(f"    Risk: {scores.get('overall_safety_risk', 'UNKNOWN')}, Max Severity: {scores.get('max_severity_score', 'N/A')}")
            else:
                print(f"    ERROR: Failed to parse JSON for {utterance_id}")
                print(f"    Raw output snippet: {response[:200]}")
                # Add row with empty scores to maintain sequence
                evaluation = {
                    **row,
                    "judge_model": "llama",
                    "medication_error_severity": "",
                    "symptom_error_severity": "",
                    "diagnosis_error_severity": "",
                    "vital_signs_error_severity": "",
                    "negation_error_severity": "",
                    "procedure_error_severity": "",
                    "critical_deletion_severity": "",
                    "critical_insertion_severity": "",
                    "temporal_error_severity": "",
                    "max_severity_score": "",
                    "overall_safety_risk": "ERROR",
                    "confidence": 0.0,
                    "error_summary": "Failed to parse evaluation",
                    "specific_errors": []
                }
                evaluations.append(evaluation)

        except Exception as e:
            print(f"    ERROR: Error evaluating {utterance_id}: {e}")
            # Add row with empty scores to maintain sequence
            evaluation = {
                **row,
                "judge_model": "llama",
                "medication_error_severity": "",
                "symptom_error_severity": "",
                "diagnosis_error_severity": "",
                "vital_signs_error_severity": "",
                "negation_error_severity": "",
                "procedure_error_severity": "",
                "critical_deletion_severity": "",
                "critical_insertion_severity": "",
                "temporal_error_severity": "",
                "max_severity_score": "",
                "overall_safety_risk": "ERROR",
                "confidence": 0.0,
                "error_summary": f"Evaluation error: {str(e)}",
                "specific_errors": []
            }
            evaluations.append(evaluation)
            continue

        # Periodically clear cache to prevent OOM
        if (i + 1) % 10 == 0:
            torch.cuda.empty_cache()

    # Save results
    json_out = output_path / "safety_taxonomy_evaluations.json"
    csv_out = output_path / "safety_taxonomy_evaluations.csv"
    df = pd.DataFrame(evaluations)
    df.to_csv(csv_out, index=False, quoting=csv.QUOTE_ALL)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(evaluations, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(evaluations)} evaluations to:\n  {json_out}\n  {csv_out}")

    # Compute summary statistics
    if evaluations:
        severity_keys = [
            "medication_error_severity", "symptom_error_severity", "diagnosis_error_severity",
            "vital_signs_error_severity", "negation_error_severity", "procedure_error_severity",
            "critical_deletion_severity", "critical_insertion_severity", "temporal_error_severity"
        ]
        
        avg_scores = {}
        for key in severity_keys:
            vals = [float(ev.get(key, 0)) for ev in evaluations 
                   if ev.get(key) is not None and ev.get(key) != "" and isinstance(ev.get(key), (int, float))]
            avg_scores[f"avg_{key}"] = sum(vals) / len(vals) if vals else 0.0

        # Risk distribution
        risk_counts = {}
        for ev in evaluations:
            risk = ev.get("overall_safety_risk", "UNKNOWN")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        # Max severity distribution
        max_severities = [float(ev.get("max_severity_score", 0)) for ev in evaluations 
                         if ev.get("max_severity_score") is not None and ev.get("max_severity_score") != "" 
                         and isinstance(ev.get("max_severity_score"), (int, float))]
        avg_scores["avg_max_severity"] = sum(max_severities) / len(max_severities) if max_severities else 0.0

        # Confidence
        confidences = [float(ev.get("confidence", 0)) for ev in evaluations 
                      if ev.get("confidence") is not None and ev.get("confidence") != "" 
                      and isinstance(ev.get("confidence"), (int, float))]
        avg_scores["avg_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0

        print(f"\n{'='*60}")
        print(f"SAFETY TAXONOMY SUMMARY STATISTICS:")
        print(f"{'='*60}")
        print(f"   Total Evaluations: {len(evaluations)}")
        print(f"   Average Max Severity: {avg_scores.get('avg_max_severity', 0):.2f}")
        print(f"   Average Confidence: {avg_scores.get('avg_confidence', 0):.2f}")
        print(f"\n   Risk Distribution:")
        for risk, count in sorted(risk_counts.items()):
            pct = (count / len(evaluations) * 100) if evaluations else 0.0
            print(f"     {risk:12s}: {count:4d} ({pct:5.1f}%)")
        print(f"\n   Average Severity by Category:")
        for key in severity_keys:
            avg = avg_scores.get(f"avg_{key}", 0)
            if avg > 0:
                print(f"     {key:35s}: {avg:.2f}")
        print(f"{'='*60}")


# ---------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Evaluate ASR transcripts for safety-critical errors using Llama as a judge.")
    parser.add_argument("--csv_path", type=str, required=True, help="Path to CSV file with ground truth and ASR outputs.")
    parser.add_argument("--ground_truth_column", type=str, required=True, help="Column name for ground truth transcripts.")
    parser.add_argument("--asr_column", type=str, required=True, help="Column name for ASR output transcripts.")
    parser.add_argument("--utterance_id_column", type=str, default="utterance_id", help="Column name for utterance IDs.")
    parser.add_argument("--output_dir", type=str, default="results/safety_taxonomy/Llama", help="Directory to save outputs.")
    parser.add_argument("--model_id", type=str, default=MODEL_ID, help="Judge model ID.")
    parser.add_argument("--max_new_tokens", type=int, default=1024, help="Max new tokens.")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature.")
    args = parser.parse_args()

    tokenizer, model = load_model_and_tokenizer(args.model_id)
    evaluate_asr_safety(args.csv_path, args.ground_truth_column, args.asr_column, 
                       args.utterance_id_column, args.output_dir,
                       tokenizer, model, args.max_new_tokens, args.temperature)
    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()

