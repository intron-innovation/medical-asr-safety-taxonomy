# BioRAMP ASR Error Taxonomy — Annotator Reference

This file mirrors the annotator-facing guide served at `/instructions`
(`annotation_webapp/templates/instructions.html`) and the hover descriptions on the annotation
screen (`annotation_webapp/templates/annotate.html`). **If you change one, change all three.**

## Scope

This project evaluates errors in ASR transcripts of medical conversations. Errors are filtered
before annotation: medical NER identifies the clinically relevant terms in the reference
transcript — problems, medications, anatomical structures, procedures and laboratory information —
and only errors touching those terms are kept. Everything shown to an annotator has already passed
that filter, so annotators are not asked to judge clinical relevance, only **what led to the
error** and **how severe** it is.

Each error is tagged by the aligner with its type (`DEL`, `SUB`, `INS`) and presented inline as
`[DEL:word]`, `[SUB:reference->hypothesis]`, `[INS:word]`.

## Source

Adapted from **Zafar A, Mamlin B, Perkins S, Belsito AM, Overhage JM, McDonald CJ (2004), "A simple
error classification system for understanding sources of error in automatic speech recognition and
human transcription"**, Int J Med Inform 73:719–730
([PMID 15325329](https://pubmed.ncbi.nlm.nih.gov/15325329/)).

## Multi-class rule

A single error may belong to more than one category — select every category that applies rather
than choosing only the best fit.

- *swampy region → iswampimidio* is both an **annunciation** error and a **nonsense** error: the
  misrecognition involves both pronunciation and a nonsensical transformation.
- *urethra → ureteral* is both a **dictionary** error and an **annunciation** error: it involves
  both medical vocabulary and pronunciation.

**Not an Error** is the exception — it is mutually exclusive with the other ten.

Assign **one** severity level per error, reflecting the combined impact of everything selected.

---

## The 11 Categories

Order matches the annotator guide.

### 1. Annunciation errors
Errors caused by how the speaker pronounced the word — accented speech, pausing in the middle of a
sentence, speaking too fast, slurring words, or disfluencies. Listen to the audio before selecting
this.

> large intestine → large intensity · nausea → nuisance · abdominal pain → abnormal pain ·
> cigarette pack → cigarette back · recreational drugs → nutritional drugs · night sweats → night sets

### 2. Homonym errors / rhyming words
Errors where the misrecognised word or phrase **sounds similar** to the intended one but is spelled
differently. Covers both identical-sounding words and near-sounding or rhyming words.

> pus → pulse · middle ear effusion → middle ear fusion · exertion → extortion · fainting → painting ·
> weight loss → waste loss · stool → stew

### 3. Dictionary errors
Phrases recognised in place of a word missing from the dictionary. These are typically a medical
drug entity or a proper noun that is not in the ASR system's dictionary. The result sounds very
similar to, but not always exactly like, the intended word.

> naproxen → proxen · metformin → bombetformin · lisinopril → lesetapril · amlodipine → amelodipine ·
> Chidinma → Chidima · Igbo → evil · Ekiti → Nkita

### 4. Stop words (added / deleted / substituted)
An error involving a short function word such as *a, an, the, has* or *if*, whether added, deleted
or substituted.

> `[SUB:a->the]` · `[DEL:a]` · `[SUB:or->so]` · `[INS:in]` · `[INS:the]` · `[DEL:a bit]`

### 5. Suffix errors
Errors caused by substituting an incorrect ending on the intended word. The stem is right; the
ending is wrong.

> breathless → breathlessness · `[SUB:vomit->vomits]` · `[SUB:nauseated->nauseous]` ·
> `[SUB:problem->problems]`

### 6. Human spelling errors
Errors that occur only in the **human transcription** and not in the ASR output — the speech
recogniser is correct in this case and the human transcriber is wrong. Use this when the reference
transcript contains the mistake.

> reference "catherization" → ASR "catheterization" · reference "urinal" → ASR "urinary" ·
> podagra → podegra

### 7. Critical errors
Errors that could change the meaning of the intended utterance. Most result when a positive is
changed to a negative (or vice versa), or when a number is misrecognised. This can also occur when
the ASR deletes a large chunk of the transcript.

> `[SUB:dripples->bubbles]` · `[SUB:urethra->ureteral]` · `[DEL:recreational]` ·
> `[DEL:okay and do you take any medications i had a a drug history of thyroxine]`

### 8. Nonsense errors
A recognised word or phrase that does not make grammatical or lexical sense, even after a possible
correction has been hypothesised from context.

> wisdom teeth → visimteeth · swampy region → iswampimidio · feverish → beverish

### 9. Words added
A word is inserted that was not spoken (cases of insertion). This may also be a repeated insertion.

> `[INS:for you]` · `[INS:one thousand nine]` · `[INS:of july]`

### 10. Words deleted
A word that was spoken is omitted (cases of deletion). This may also be a chunk of a sentence being
deleted.

> `[DEL:urine]` · `[DEL:recreational]` · `[DEL:in]` ·
> `[DEL:okay and do you take any medications i had a a drug history of thyroxine]`

### 11. Not an error
The flagged difference is acceptable and should not be counted as an ASR error: fillers, plural
variants and alternate spellings where neither transcript is wrong. Mutually exclusive with the
other categories.

> uh · like

---

## Severity

| Level | Label | Meaning |
|---|---|---|
| 1 | Minor | Little or no chance of impacting the health practitioner's understanding of the conversation and/or line of management for the patient. |
| 2 | Moderate | Some chance of impacting the health practitioner's understanding of the conversation and/or line of management for the patient. |
| 3 | Severe | Likely to lead to an egregious clinical error — possibly omission or inclusion of a key life-impacting detail in the conversation. |

**Practical test:** *"If this went uncorrected, and if you could only read the transcript alone,
would it have changed your understanding of the patient's clinical condition?"*

Ratings are inherently subjective. Annotators should use clinical judgment and be internally
consistent.

---

## Storage Schema

Written by the annotation interface to `completed_annotation/*.json` under `annotations`, one
record per error:

| Field | Meaning |
|---|---|
| `errorClass` | **List of category slugs — this is the label field.** |
| `taxonomy` | Unused; empty on all records to date. Do not read. |
| `severity` | Integer 1–3 |
| `errorType` | `INS` / `DEL` / `SUB`, from the aligner |
| `errorMatch` | The inline edit tag, e.g. `[SUB:dripples->bubbles]` |
| `startIdx`, `endIdx` | Character offsets into `context.asrReconstructed` |
| `annotatorId`, `modelName`, `utteranceId`, `errorId` | Provenance |
| `context.humanTranscript` | Reference, speaker-diarized |
| `context.asrReconstructed` | ASR hypothesis with inline edit tags |
| `context.humanTranscriptNER` | Reference with clinical entity spans tagged |

Category slugs (unchanged — renaming a label does **not** change its slug):
`annunciation_errors`, `homonym_errors_rhyming_words`, `dictionary_errors`, `stop_words`,
`suffix_errors`, `spelling_errors` *(displayed as "Human Spelling Errors")*, `critical_errors`,
`nonsense_errors`, `words_added`, `words_deleted`, `not_an_error`.

---

## Re-annotation note

The `spelling_errors` label previously read as an ASR-side misspelling. It now means the **reference**
is wrong and the recogniser is right. All 9 records carrying this slug in the first annotation batch
were assigned under the old reading and need re-review; conversely, reference errors such as
`[SUB:catherization->catheterization]` were filed under `not_an_error` and should move here.

---

**Version:** 3.1 — mirrors the live annotator guide. Replaces the earlier clinical-domain scheme
(medication / clinical concepts / temporal / negation / numerics / …), which was never used by
annotators and is retired.
