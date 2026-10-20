# DRAFT — Annotation guide v2 (not deployed)

For review. Replaces the current `/instructions` page if approved.

Written for the annotators. Deliberately short: v1 was long and the round-1/round-2
results show the two readers absorbed it differently.

---

## What you are deciding

For every highlighted error, two things:

1. **Why did the ASR get this wrong?** — the cause
2. **How bad is it clinically?** — one severity

You are **not** deciding whether the error is clinically relevant. The system already
filtered for that before showing it to you.

---

## Rule 1 — Start from the WORD, not the sound

This is the change that matters most. Last round one annotator was asking *"what kind of
sound problem is this?"* and the other *"what kind of word was hit?"* They picked
different labels on the same error nine times out of ten.

**Always start from the word that was damaged.**

> `[SUB:amlodipine->pain]`
> Wrong: "that's a mispronunciation" → Annunciation
> Right: "amlodipine is a drug name" → **Dictionary error**

Pronunciation explains *why* nearly every ASR error happens, which is exactly why it is
a poor label — it fits everything. Use it only when the damaged word is an **ordinary
English word**.

---

## Rule 2 — The categories, in order

Work down and take the **first** that fits.

| # | Category | The single test |
|---|---|---|
| 1 | **Human transcription error** | Is the **reference** at fault and the ASR right? Stop here if yes. |
| 2 | **Dictionary error** | Was the damaged word a drug, condition, anatomy term, procedure, or a proper noun / place / name? Also when a medical word becomes non-medical, or the reverse. |
| 3 | **Suffix error** | Same stem, wrong ending. (*vomit → vomits*) |
| 4 | **Annunciation / Homonym error** | An **ordinary** word was misheard as another word that sounds like it. **You must have played the audio.** (*pus → pulse*, *fainting → painting*) |
| 5 | **Nonsense error** | The output is not a real word at all. (*wisdom teeth → visimteeth*) |
| 6 | **Stop words** | Only a short function word changed — *a, an, the, is, has, if*. |
| 7 | **Words added** | `[INS:…]` only. A word nobody said. |
| 8 | **Words deleted** | `[DEL:…]` only. Spoken content missing. |

7 and 8 grey out automatically when they don't apply.

---

## Rule 3 — One tag, one label (unless two words were damaged)

**If the tag covers a single word, pick exactly one label.** The form will not let you
pick a second.

Only when the tag spans **two or more damaged words** may you pick more than one, and
only then because the words failed for *different* reasons:

> `[SUB:heartbeat shake->beating cheek]`
> *heartbeat → beating* is a **Dictionary** error
> *shake → cheek* is an **Annunciation / Homonym** error
> Tick both.

Do not add a second label "to be safe". Do not use one label as shorthand for
"something is wrong here".

---

## Human transcription error — the two cases

Use it when the **transcript is at fault, not the model**. The ASR was right.

**(a) The human typed it wrong**
> reference *"catherization"* → ASR *"catheterization"*
> reference *"lose"* → ASR *"loose"*

**(b) The human missed speech the speaker actually said**
> `[INS:alcohol]` — the patient said it twice, the transcript has it once
> `[INS:is there any drug]` — a whole question the transcript omits

Case (b) looks like an insertion but it is **not a hallucination**. Ask yourself: *did
the speaker actually say this?* If yes, the reference is incomplete and this is the
label. If no one said it, it is **Words added**.

Judge these from the text, not the audio.

---

## Severity

One level per error, for the whole error.

| | |
|---|---|
| **1 Minor** | A clinician reading the transcript would not be misled. |
| **2 Moderate** | Meaning is obscured or uncertain, but not clearly wrong. |
| **3 Severe** | Touches a **diagnosis, symptom, medication, procedure, or a negation**. |

**The test:** *if this went uncorrected and you could only read the transcript, would it
change your understanding of the patient's condition?*

### Anchors — calibrate against these

| Error | Severity | Why |
|---|---|---|
| `[SUB:amlodipine->pain]` | 3 | Medication lost |
| `[SUB:ulcer->asthma]` | 3 | One diagnosis becomes another |
| `[SUB:irregularities->regularities]` | 3 | Negation flips |
| `[SUB:urethra->ureteral]` | 2 | Anatomy blurred, meaning recoverable |
| `[SUB:dripples->dribbles]` | 2 | Symptom wording changed, sense intact |
| `[DEL:the]`, `[INS:in]` | 1 | No clinical content |

Severity 2 is for *genuinely uncertain* cases, not "somewhere in between". If you can
name the diagnosis, symptom, medication, procedure or negation affected, it is 3.

---

## Before you submit

- Did I start from the **damaged word**, not the sound?
- Did I play the audio? (required for Annunciation / Homonym)
- One word in the tag → one label?
- Is my severity 3 justified by a diagnosis, symptom, medication, procedure or negation?

---

## Changes from v1

- **Annunciation and Homonym are now one category.** Separately they had negative
  agreement (κ −0.09 and −0.02); merged they reach 0.37.
- **Spelling error is renamed Human transcription error** and now explicitly covers
  speech the human failed to transcribe. 53 of its 98 past uses were this case.
- **Multi-label is restricted to multi-word tags** and enforced by the form. 77% of tags
  are a single word; on those, one annotator used two labels 22 times and the other 3.
- **Critical errors and Not an error** were retired after round 1 — neither reached any
  agreement. Severity carries criticality.
