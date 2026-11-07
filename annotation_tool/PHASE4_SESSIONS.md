# Phase 4 sessions

Open **Annotate Subset** and pick a model. Both models hold the same five sessions.
Built by `build_phase4_subset.py` (`qwen3_iaa4`, `gemma3n_iaa4`).

Sessions appear in a different order for each annotator, so use the IDs below.

## Joint: all three annotators, together

| Session | Source | Medical errors (both models) |
|---|---|---|
| `day1_consultation10` | UK | 24 |
| `63e6abb7-2d8e-4df3-a52e-8e09aea762c6_0d2e6ebf48e7196f5ab076e05d590ad9_5epxs3QR` | AfriSpeech (African) | 25 |
| `3_MyocardialInfarction` | Nigerian conversation (African) | 22 |

## Independent: each annotator alone

| Session | Source | Medical errors (both models) |
|---|---|---|
| `day2_consultation03` | UK | 35 |
| `4fc2c19e-de60-4be0-91b5-7870f60f2d99_4f72189a5c5e29dd6caa06214423b231_N96VXtHf` | AfriSpeech (African) | 37 |

143 medical errors per annotator in total (71 joint, 72 independent).

Joint sessions: do not score them as independent agreement. Report agreement on the two
independent sessions only.

## How they were chosen

From the 112 sessions not used in rounds 1 to 3. The UK sessions are at the harder end of the
UK pool (highest WER) within the size limit. The African sessions mix the two African sources.
To swap a session, edit `SESSIONS` in `build_phase4_subset.py` and run it again.
