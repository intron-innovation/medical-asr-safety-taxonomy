# DRAFT — Annotation companion v3 (reference, not on the instruction page)

For when the quick guide is not enough. Read it once before annotating, or look things up
as you go. Based on what went wrong in round 3.

---

## Label rules in more detail

**Start from the word, not the sound.** Pronunciation explains nearly every ASR error, so
it is only a label when the damaged word is an ordinary English word.

**A medical term beats Suffix.** If the damaged word is a drug, condition, symptom,
anatomy term, procedure or test, it is Dictionary even when only the ending changed.
`abdominal→abdomen`, `feverish→fever`, `palpitations→palpitation` are all Dictionary.
Suffix is only for ordinary words, inflection only: `complaint→complaints`, `walked→walk`.

**Real word for real word is still Annunciation / Homonym.** `worst→worse` and
`drinks→does` are ordinary words. Dictionary is about the kind of word that was damaged,
not about the output being a word.

**One word, one label.** The form blocks a second label on a single-word tag. A tag over
two or more words may take two labels only when the words failed for different reasons:
`[SUB:heartbeat shake->beating cheek]` is Dictionary + Annunciation / Homonym.

**Words added and Words deleted are now one label: ASR omission / insertion.** It is the
last stop in the chart: the reference is right, the damaged words are ordinary, and the
ASR dropped or invented them. The colour of the tag already tells you whether it was an
insertion or a deletion.

### Insertions and deletions: whose mistake is it?

Ask: *did the speaker actually say it?* Judge from the text first; play the audio only if
the text does not settle it.

| Tag | Speaker said it? | Label |
|---|---|---|
| INS | Yes, the reference left it out | Human transcription error |
| INS | No, nobody said it | ASR omission / insertion |
| DEL | Yes, the ASR dropped it | ASR omission / insertion (or Stop word / Dictionary by the chart) |
| DEL | No, the reference has words the speaker never said | Human transcription error |

---

## Fragments: one event, several tags

The system compares the reference with the ASR word by word. When the same words are in a
different place in each, it cannot say "moved". It reports one insertion, one deletion
and sometimes a substitution. You then see three separate tags for what is really one
event.

**A real example from round 3 (`day5_consultation04`).**

- Both models heard "...have you opened your bowels normally, **you have been to the
  toilet**, I had problems last week, but this week it seems to be..."
- The reference has the same sentence in a different place, after "it seems to be".
- If the audio confirms the speaker said it early, the human typed the words out of order.

The comparison produced three tags:

- `[INS:you have been]` near the start
- `[SUB:yeah last week->to the yeah]` next to it
- `[DEL:to be you have been to the toilet]` later

Last round the annotators labelled these three tags differently: Annunciation / Homonym,
Human transcription error, and Words deleted. All three tags are one event, the reference
placing a sentence in the wrong spot. If the audio confirms it, the right answer is
**Human transcription error, severity 1, on all three.**

**How to spot a fragment.**

- The same words appear in an INS and a DEL (or a SUB) close together.
- The tags are only a few words apart.
- The stretch has repetition, an interruption, or "pardon".

**What to do.**

1. Read the stretch in the reference and decide what actually happened to the speech.
2. Give every tag in that event the same label and the same severity.
3. Do not choose Human transcription error just because the stretch looks messy. Choose it
   only if the reference really is wrong.

---

## Severity in more detail

**Q1. Does the damaged word carry clinical content?** A diagnosis, a symptom, a
medication, a procedure or test, a number (dose, duration, frequency), or a negation.
If no → **1 Minor**.

**Q2. If yes, what does the transcript now say?**

| | What the reader gets | Severity |
|---|---|---|
| Wrong | A plausible but different clinical fact. A reader would act on it. | **3 Severe** |
| Missing | The fact is gone or garbled. A reader would notice and have to ask. | **2 Moderate** |

**Always 3:** a medication replaced or lost, a diagnosis replaced, a negation flipped, a
dose or number changed.

A symptom replaced by a different symptom is 3. A symptom *modifier* lost (worse, mild,
sudden) is 2 unless it flips the meaning.

If you are stuck between 2 and 3, ask: *would a clinician reading only this transcript
believe something false?* Yes → 3. No, they would just be missing something → 2.

### Severity anchors (real errors from round 3, proposed answers)

| Error | Severity | Why |
|---|---|---|
| `[SUB:amlodipine->pain]` | 3 | Medication replaced |
| `[SUB:gastrings->gallstones]` | 3 | One diagnosis becomes another, reads as true |
| `[SUB:pain->bleeding]` | 3 | A different symptom, reads as true |
| `[SUB:irregularities->regularities]` | 3 | Negation flips |
| `[SUB:worse->yeah]` | 2 | Course of the symptom lost, nothing false stated |
| `[SUB:urethra->ureteral]` | 2 | Anatomy blurred, meaning recoverable |
| `[SUB:drinks->does]` | 1 | No clinical content |
| `[DEL:the]`, `[INS:of]` | 1 | No clinical content |

---

## Label answers to round-3 disagreements (proposed, to confirm)

| Error | Label | Why |
|---|---|---|
| `[SUB:abdominal->abdomen]` | Dictionary | Anatomy term, beats Suffix |
| `[SUB:feverish->fever]` | Dictionary | Symptom term, beats Suffix |
| `[SUB:worst->worse]` | Annunciation / Homonym | Ordinary word |
| `[SUB:drinks->does]` | Annunciation / Homonym | Ordinary word |
| `[SUB:the air->a year]` | Annunciation / Homonym | Sound-alike phrase; messy audio does not make it a reference error |
| `[SUB:prescribe medication->prescribed medications]` | Dictionary | Medical term; endings changed |
| `[SUB:complaint->complaints]` | Suffix | Ordinary word, plural only |

---

## What went wrong in round 3

- Dictionary versus Annunciation / Homonym (7 errors): a real word swapped for a real word
  was read as Dictionary by one annotator.
- Annunciation / Homonym versus Human transcription error (7): repeated or interrupted speech.
- Insertions and deletions labelled Human transcription error (7): no rule for when the
  reference is at fault on a deletion.
- Suffix versus other (6): "same stem" was undefined; medical terms were not separated.
- Severity 3: one annotator rated diagnosis and symptom swaps as 2.

---

## Changes from v2

- Flowchart for the label order.
- A medical term beats Suffix; Dictionary is about the word, not the output.
- Words added and Words deleted merged into ASR omission / insertion.
- Deletions added to the Human transcription rule.
- A rule for fragments and messy speech.
- Severity is now wrong vs missing.
- The error's NER type (for example PROBLEM, MEDICINE) is shown instead of INS / DEL / SUB,
  because the tag colour already shows that. Insertions show none.
