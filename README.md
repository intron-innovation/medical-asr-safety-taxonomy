
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

Generating the per-utterance WER table

The full results table is available in `all_result_processed.xlsx`. To extract per-utterance WERs and save as CSV:

```python
import pandas as pd
df = pd.read_excel('all_result_processed.xlsx')
wer_cols = [c for c in df.columns if c.lower().endswith('_wer') or 'wer' in c.lower()]
cols = ['utterance_id', 'source'] + wer_cols
cols = [c for c in cols if c in df.columns]
df[cols].to_csv('results_utterance_wers.csv', index=False)
print(f'Saved {len(df)} utterance results')
```

Results summary

Per-model aggregate Word Error Rate (WER) statistics computed from `all_result_processed.xlsx`:

| Model | Avg WER | Min WER | Max WER | Count |
| --- | --- | --- | --- | --- |
| IBM-Granite | 0.8834 | 0.5982 | 1.0000 | 39 |
| Nvidia-Parakeet | 0.1288 | 0.0580 | 0.2902 | 39 |
| Phi-4-ASR | 0.8565 | 0.3214 | 1.1233 | 39 |
| Whisper-ASR | 0.2342 | 0.103 | 0.5026 | 39 |

<!-- To compute or update WER statistics for all four models with your current data:

```python
import pandas as pd
df = pd.read_excel('all_result_processed.xlsx')
wer_cols = [c for c in df.columns if c.lower().endswith('_wer')]

print("| Model | Avg WER | Min WER | Max WER | Count |")
print("| --- | --- | --- | --- | --- |")

for col in wer_cols:
    model_name = col.replace('_wer', '').replace('_', ' ').title()
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(vals) > 0:
        avg = vals.mean()
        min_val = vals.min()
        max_val = vals.max()
        count = len(vals)
        print(f"| {model_name} | {avg:.4f} | {min_val:.4f} | {max_val:.4f} | {count} |")
```

Run this script to generate the complete results table for all four models (IBM-Granite, Nvidia-Parakeet, Phi-4-ASR, Whisper-ASR) and copy the output to the table above. -->

Data sources and attribution

The notebooks use the following publicly available datasets:

- **Primock-57** (UK medical consultations): Available via Hugging Face at `sdialog/Primock-57`. See the [original repository](https://github.com/sdialog/Primock) for details.
- **Afrispeech-dialog** (African medical conversations): Available via Hugging Face at `intronhealth/afrispeech-dialog`. Covers multiple African languages and medical scenarios.
- **US medical dataset** (anonymized medical consultations): Downloaded from Springer Nature Figshare (DOI: 10.6084/m9.figshare.14861698.v1).

Please respect the licenses and usage terms of each dataset when using or publishing results based on this data.

Environment and dependencies

- **Python**: 3.10+ recommended.
- **PyTorch**: Install the CUDA-enabled version matching your GPU and CUDA toolkit. See [pytorch.org/get-started](https://pytorch.org/get-started/locally).
- **Key packages**: transformers (4.30.0+), datasets (2.0.0+), jiwer, soundfile, pandas, huggingface_hub.
- **Optional**: openpyxl (for Excel I/O), librosa (for audio processing).

All base dependencies are listed in `phi_env.yml`.

Troubleshooting

**GPU out of memory during inference**
- Reduce `chunk_seconds` parameter in `model_inference.ipynb` (default 300) to process shorter audio segments.
- Reduce `max_new_tokens` for the model to limit output length.
- Ensure no other GPU processes are running: `nvidia-smi`.

**ModuleNotFoundError: No module named 'torch'**
- Install PyTorch: `conda install pytorch pytorch-cuda=11.8 -c pytorch -c nvidia` (adjust CUDA version as needed).

**Hugging Face API errors**
- Authenticate: `huggingface-cli login` and provide your access token.
- Check rate limits and network connectivity.

**`all_result_processed.xlsx` is missing**
- Run `result_process.ipynb` to regenerate from raw ASR outputs.

**Dataset download fails**
- Verify your internet connection and Hugging Face API access.
- For the US dataset, check that the Figshare URL is still valid or download manually.

Project structure

```
bio_ramp_asr/
├── data_collections_clean.ipynb        # Data download and merging
├── model_inference.ipynb               # ASR inference (Phi-4, Whisper)
├── result_process.ipynb                # WER computation and aggregation
├── all_datasets_merged.csv             # Merged dataset (output of step 2)
├── all_result_processed.xlsx           # Final results with WERs (output of step 4)
├── phi_env.yml                         # Conda environment specification
├── README.md                           # This file
├── data/                               # Downloaded datasets (Primock, US, Afrispeech)
├── results/                            # Intermediate ASR results (CSVs)
└── archieved/                          # Previous notebook versions
```



Contributing

For bug reports, feature requests, or improvements:
- Open an issue on the repository.
- Submit a pull request with your changes.
- Ensure notebooks are properly formatted and runnable.
- Update `phi_env.yml` if adding new dependencies.
- Document any changes to the workflow.

License

This code is provided as-is for research purposes. The datasets have their own licenses. See Data sources above and respect each dataset's terms of use before publication.

---



