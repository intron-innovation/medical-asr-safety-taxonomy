# Post-correction and fine-tuning

Workstream for improving clinical ASR output using the severity-annotated error corpus produced by
the annotation tool. Everything in this folder is downstream of `../annotation_tool/` — it consumes
annotations, it does not produce them.

**Status: design and toy-demo stage. No model has been trained yet.**

---

## What we are trying to do

Standard WER treats every error as equal. In a clinical transcript it is not: mishearing a drug name
or dropping a negation can change care, while a dropped article cannot. 

<!-- The goal is a system that
spends its capacity on the errors that could hurt a patient, and an evaluation that can show it did. -->

Three arms, to be compared against each other and against no correction at all:

| Arm | What is trained | Input → output | What it tests |
|---|---|---|---|
| **A. SFT on text** | An LLM corrector downstream of the ASR | ASR hypothesis → corrected transcript | Can a text-only model learn this corpus's failure modes? |
| **B. SFT on utterance** | The ASR model itself | audio → transcript | Is it better to fix the recogniser than to patch its output? |
| **C. RL** | The Arm A corrector, continued | ASR hypothesis → corrected transcript | Does a severity-weighted reward beat a WER-weighted one? |

<!-- Arm C is the contribution. Arms A and B are the baselines that make it interpretable — without them
there is no way to attribute a gain to the severity weighting rather than to fine-tuning in general. -->

<!-- ### Why RL after SFT, not instead of it

SFT can only imitate the single reference answer, and its loss weights every token equally — there
is no way to express "the drug name matters more than the article." RL scores whatever the model
produces, so the reward can encode that preference. But RL from an un-tuned model is unstable:
most sampled candidates are junk, every one scores badly, and there is no gradient signal. SFT
first puts the model in the right output distribution; RL then shifts its priorities within it.
This is the InstructGPT ordering (Ouyang et al., 2022, arXiv:2203.02155).

---

## The reward

```
R = −Σᵢ wᵢ · 1[errorᵢ left uncorrected]
    − λ · Σⱼ wⱼ · 1[errorⱼ newly introduced]
    + μ · acoustic_consistency(edit, audio)
```

- `w` is exponential in annotated severity, so one severe error outweighs many trivial ones.
- `λ > 1`: introducing a clinical error must cost more than failing to fix one.
- The acoustic term is **not optional**. A severity-weighted reward pays the model most for editing
  drug names, doses and negations — exactly where a fluent but ungrounded guess is most dangerous.
  Without a grounding term the reward actively rewards confabulation. See arXiv:2609.14455.

`postcorrection_demo.py` shows this scoring three candidate corrections of a real error, including
a fluent confabulation that only the second term catches.

---

## Data this consumes

| Source | What it gives |
|---|---|
| `../annotation_tool/completed_annotation/*.json` | Human severity + taxonomy labels per error |
| `../annotation_webapp/data/annotation_data/*.json` | Aligned reference/hypothesis pairs for all 120 sessions, 5 models |
| `../data/final_audio/` (GCS in production) | Audio, for Arm B and the acoustic reward term |

**Corpus:** 120 sessions, balanced 40 African / 40 UK / 40 USA, across whisper, phi4, gemma3n,
nemotron35 and qwen3 — roughly 960 (reference, hypothesis) pairs available.

**Annotation to date (test sample):** 154 errors over 8 sessions by 2 annotators. Dropping
`not_an_error` and `spelling_errors` leaves **96 usable**, at severity 1/2/3 = 63/23/10. This is
enough to *validate* a reward function, not to train a policy. More annotation is in progress.

### Known data issues, unresolved

1. **No inter-annotator agreement.** Each model was labelled by exactly one annotator, so there is
   no κ on severity. A reviewer will ask.
2. **References contain errors.** Cases like `catherization → catheterization` are the *reference*
   being wrong. Training toward those teaches the model to reintroduce typos. The `spelling_errors`
   category now captures these, but the 9 records carrying that slug predate the definition fix and
   need re-review.
3. **The severity scale is 1–3 in the deployed tool** even though source documents describe a 0–5
   scale. The reward weights depend on the number of levels, so this must be settled before training.

---

## Held-out design

Split by **session**, never by utterance. Two consultations the model has never seen stand in for
the patients it will meet at deployment; splitting by utterance puts the same speaker, accent and
clinic on both sides and inflates the numbers.

What exists at each stage:

| | reference | annotations | reward | what runs |
|---|---|---|---|---|
| Train (Arms A, B) | yes | no | no | the model |
| Train (Arm C) | yes | yes | yes | model + reward |
| Evaluate | yes | yes | yes | the model |
| **Deploy** | **no** | **no** | **no** | **the model alone** |

References and annotators are scaffolding. They build the system, then they are discarded:
`audio → ASR → corrector → transcript`.

---

## Evaluation

Report all three, always together:

- **Severity-weighted error rate** — the headline.
- **Plain WER** — to show it did not degrade.
- **Harm-introduction rate** — new severity-4/5 errors the corrector *created*. A system that
  fixes more than it breaks is the whole claim; this is the number that proves it.

Stratify by severity and by dataset group (African / UK / USA). African sessions carry 2–3× the
error load of US sessions on every model, so a pooled number hides the case that matters most.

If plain WER and severity-weighted error move together, the severity weighting did nothing and the
result is just "fine-tuning helps."

---

## Contents

| Path | |
|---|---|
| `postcorrection_demo.py` | Illustrative end-to-end walkthrough on the 96 annotated errors — data shapes, the SFT prompt, the reward scoring three candidates, and the WER-vs-severity contrast. No model is trained. Run with `python postcorrection_demo.py`. |
| `results/` | Training and evaluation outputs. |

**Overview deck:** https://claude.ai/artifact/LgrSQmdvN7V9H8VKGtXpS4 — six slides covering the
prompting/SFT/RL distinction, the reward, and the evaluation design. Private; share from the page's
Share menu if others need it.

---

## Environment

Not yet provisioned. Target stack: `transformers` + `peft` + `trl` + `bitsandbytes`, using TRL's
`SFTTrainer` then `GRPOTrainer`.

Hardware constraint: a single RTX 4090 (24 GB), driver 535 capped at CUDA 12.2 — **pin torch to a
cu121 build**, newer wheels want 12.8+. A 7–8B corrector fits for SFT with QLoRA; GRPO samples
several candidates per prompt, so expect to drop to 3–4B there if memory bites. Transcripts run
over 1,000 tokens, so correction is windowed rather than whole-consultation — a memory necessity,
not just a design choice.

Pick a corrector base that is **not** one of the ASR systems under evaluation, or a reviewer will
ask whether the model is just cleaning up its own output.

---

## Reading

| | |
|---|---|
| SFT-then-RL, the template | Ouyang et al. 2022, [arXiv:2203.02155](https://arxiv.org/abs/2203.02155) |
| LLM post-correction of ASR | Chen et al., HyPoradise, NeurIPS 2023 D&B, [arXiv:2309.15701](https://arxiv.org/abs/2309.15701) |
| RL for ASR | Shivakumar et al., ASRU 2025, [arXiv:2509.01939](https://arxiv.org/abs/2509.01939) |
| GRPO | Shao et al., DeepSeekMath 2024, [arXiv:2402.03300](https://arxiv.org/abs/2402.03300) |
| Nearest prior work — clinician-rated ASR harm | Ellis et al., "WER is Unaware", IWSDS 2026, arXiv:2511.16544 |
| The error taxonomy | Zafar et al. 2004, [PMID 15325329](https://pubmed.ncbi.nlm.nih.gov/15325329/) |

The Ellis et al. entry is the one to position against: it establishes that WER correlates poorly
with clinician risk judgements and that an LLM judge tracks experts — but stops at measurement.
Novelty here must be stated narrowly as *the first RL reward for ASR post-correction derived from
human per-error clinical-harm severity annotations*. -->
