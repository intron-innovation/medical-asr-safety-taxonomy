# medical-asr-safety-taxonomy (push of local isatasr workspace)

This repository contains data collection and model inference notebooks for medical ASR experiments.

Contents added from the local `isatasr` workspace:

- `bio_ramp_asr/data_collections_clean.ipynb` — cleaned notebook that downloads/loads Primock, Afrispeech and a US medical dataset, computes audio durations, and merges into `all_datasets_merged.csv`.
- `bio_ramp_asr/all_datasets_merged.csv` — merged dataset produced by the notebook (if present locally).
- `bio_ramp_asr/model_inference.ipynb` — model inference notebook (Phi‑4 and Whisper examples) that reads `all_datasets_merged.csv` and runs ASR.

How to reproduce locally
- Create and activate the conda environment (see `phi_env.yml`) or install the pip requirements.

  Conda (recommended):

  ```sh
  conda env create -f phi_env.yml
  conda activate phi_env
  ```

- Notes about PyTorch/CUDA: install the appropriate `pytorch` and `torchaudio` build for your CUDA version. If you have CUDA installed, follow the instructions at https://pytorch.org/get-started/locally to select the right command and then install the rest of the pip packages (or update `phi_env.yml` accordingly).

Running the notebooks
- Open the notebooks in JupyterLab/VS Code and run the cells in order.
- `data_collections_clean.ipynb` will attempt to download datasets via Hugging Face `snapshot_download` and via direct URL for the US dataset. It writes `bio_ramp_asr/all_datasets_merged.csv`.
- `model_inference.ipynb` reads `bio_ramp_asr/all_datasets_merged.csv` and demonstrates using Phi‑4 and Whisper models to transcribe audio files.

Environment and package requirements
- See `phi_env.yml` for a reproducible conda environment specification. When installing PyTorch, prefer the official instructions for your platform and CUDA version.

License and data
- The notebooks reference datasets that may have their own license and usage terms. Make sure you have the right to download and use those datasets for your purposes.

Contact
- If you want me to make further adjustments (split notebooks, add CI, or push only specific folders), tell me which parts to change.
