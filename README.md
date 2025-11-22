
# BioRAMP ASR — data collection, inference and results

This folder contains the cleaned data collection, model inference, and result processing notebooks used for the BioRAMP medical ASR experiments.

Files of interest
- `data_collections_clean.ipynb` — download/load Primock, Afrispeech and US medical datasets, compute durations and produce `all_datasets_merged.csv`.
- `model_inference.ipynb` — runs ASR inference (Phi‑4 example + Whisper example) over `all_datasets_merged.csv`.
- `result_process.ipynb` — postprocesses ASR outputs and computes WERs.
- `all_result_processed.xlsx` — final per-utterance results and WER columns for each model (primary source for the results table).
- `phi_env.yml` — Conda environment specification (see notes below).

Quick start

1. Prepare environment

   - Recommended: create the conda environment from `phi_env.yml` and then install an appropriate PyTorch build for your CUDA version.

     ```sh
     conda env create -f phi_env.yml -n phi_env
     conda activate phi_env
     # then install CUDA-aware pytorch per https://pytorch.org/get-started/locally
     ```

   - Alternative: export pip reqs via `pip freeze > requirements.txt` then `pip install -r requirements.txt`.

2. Run data collection

   - Open `data_collections_clean.ipynb` in Jupyter or VS Code and run the cells in order.
   - The notebook will attempt to:
     - Download `Primock-57` from Hugging Face (via `snapshot_download`) if not present locally.
     - Download and extract the US dataset ZIP and gather transcripts matched to audio files.
     - Load `afrispeech-dialog` via `datasets.load_dataset` and select the `medical` domain subset.
     - Compute durations and merge datasets into `all_datasets_merged.csv`.

   - Output: `bio_ramp_asr/all_datasets_merged.csv`

3. Run model inference

   - Open `model_inference.ipynb`.
   - Ensure you have the right hardware and a PyTorch build matching your CUDA driver.
   - The notebook demonstrates two paths:
     - Phi‑4 multimodal transcription (device: CUDA if available)
     - Whisper-based ASR pipeline using `transformers` pipeline for `openai/whisper-large-v3`.
   - The notebook reads `all_datasets_merged.csv`, runs inference and writes raw ASR outputs.

4. Postprocess results and compute WER

   - Run `result_process.ipynb` (or the archived `archieved/phi_4_inference.ipynb`) to compute per-utterance WERs and aggregate results.
   - Final sheet is written to `bio_ramp_asr/all_result_processed.xlsx` which contains columns `utterance_id`, `source` and one or more `*_wer` columns (one per model).

Practical notes
- Large files and git: audio or dataset files often exceed GitHub's 100MB limit. Use Git LFS for audio files or exclude them from the repository and keep only metadata/paths.
- Hugging Face: some downloads require authentication or bandwidth; ensure `huggingface_hub` is configured if you hit rate limits.
- Reproducible environment: after `conda env create`, pin any additional pip-only packages with `pip freeze > pip-requirements.txt` and commit.

Generating the per-utterance WER table (preview)

The full results table is available in `bio_ramp_asr/all_result_processed.xlsx`. To extract a preview (utterance_id, source, and all `*_wer` columns) and save a CSV, run this small script from the `bio_ramp_asr` folder:

```py
import pandas as pd
df = pd.read_excel('all_result_processed.xlsx')
wer_cols = [c for c in df.columns if c.lower().endswith('_wer') or 'wer' in c.lower()]
cols = ['utterance_id','source'] + wer_cols
cols = [c for c in cols if c in df.columns]
df[cols].to_csv('results_utterance_wers_preview.csv', index=False)
print('Wrote results_utterance_wers_preview.csv')
```

If you prefer a markdown preview in the README, run this to print a markdown table of the first N rows:

```py
print('| ' + ' | '.join(cols) + ' |')
print('| ' + ' | '.join(['---']*len(cols)) + ' |')
for _,r in df[cols].head(40).iterrows():
    vals = [str(r[c]).replace('|','\\|') for c in cols]
    print('| ' + ' | '.join(vals) + ' |')
```

Results (preview)

Below is a short preview of the per-utterance WERs (first 40 rows). For the complete table open `all_result_processed.xlsx` or generate `results_utterance_wers_preview.csv` as shown above.

<!-- Results preview inserted here by script if desired. -->

Contact / next steps
- If you want me to embed the full per-utterance WER table into this README, tell me whether you want the entire table included or just aggregates (per-model average WER). Large tables (>100 rows) can make the README heavy — I recommend keeping the full table as a separate CSV and embedding a small sample here.
- I can also:
  - Replace `data_collections.ipynb` with the cleaned notebook permanently.
  - Run the notebooks here to generate `all_datasets_merged.csv` and `all_result_processed.xlsx` if you give permission to execute.

---
Generated on the local machine; paths in this README assume the repository root is `bio_ramp_asr`.
