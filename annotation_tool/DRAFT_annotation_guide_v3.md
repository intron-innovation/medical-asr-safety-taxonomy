# DRAFT — Quick guide v3 (for the instruction page)

Short on purpose. Fuller reasoning and examples are in the companion document.
Not deployed.

---

## For each error, pick two things

1. **Why did it go wrong?** One label.
2. **How bad is it clinically?** One severity.

---

## Step 1 — The label. Follow the chart, stop at the first "yes".

```mermaid
flowchart TD
    S([Highlighted error]) --> Q1{Is it the same word with only the ending changed?<br/>plural, tense or -ing/-ed. Medical words too}
    Q1 -- yes --> SU[Suffix error]
    Q1 -- no --> Q2{Is the damaged word a medical term or a name?<br/>a drug, condition, symptom, body part, test, person or place<br/>Informal patient words count}
    Q2 -- yes --> D[Dictionary error]
    Q2 -- no --> Q3{Is it only a short function word?<br/>a, an, the, of, to, is}
    Q3 -- yes --> SW[Stop words]
    Q3 -- no --> Q4{Is the output not a real word at all?}
    Q4 -- yes --> N[Nonsense error]
    Q4 -- no --> AU[/Still no label? Now play the audio/]
    AU --> Q5{Is the reference clearly wrong and the ASR right?<br/>If the audio is unclear, answer no}
    Q5 -- yes --> H[Human transcription error]
    Q5 -- no --> Q6{Is there a fault in the recording at this spot?<br/>a dropout, click, cut-off, distortion or noise}
    Q6 -- yes --> AG[Audio glitch]
    Q6 -- no --> Q7{Was an ordinary word swapped for another real word?<br/>usually a sound-alike}
    Q7 -- yes --> A[Annunciation / Homonym]
    Q7 -- no --> O[ASR omission / insertion<br/>ordinary words dropped or invented]
```

Three things to remember:

- **Text first, audio last.** Steps 1 to 4 need no audio. Play it only when none fits.
- **Unclear audio is not evidence that the reference is wrong.**
- **Same word, only the ending changed → Suffix**, medical or not. **Otherwise a medical term is Dictionary**, even if the audio is glitchy or the reference looks wrong
  (`abdominal→abdomen`).
- **One word, one label.** Two labels only when two words failed for different reasons.

**Audio glitch:** A fault in the recording at this spot. This includes a dropout, distortion, a click or pop, a cut-off, or a burst of noise over the speech. An accent, or fast, slurred or mumbled speech, is not a glitch. If a glitch hides a medical term, label it Dictionary error instead. *e.g. a word cut off mid-syllable; a click or dropout where a word should be.*

---

## Step 2 — The severity

**Does the word carry clinical content?** (diagnosis, symptom, medication, procedure,
number, negation)

- **No** → **1 Minor**
- **Yes, and the transcript now says something false** → **3 Severe**
- **Yes, and the fact is just missing or garbled** → **2 Moderate**

**3 = misleading. 2 = missing. 1 = no clinical content.**

A run of **5+ words dropped or invented by the ASR** that carries clinical content is **3**. Fillers only is **1**.

| Example | Severity |
|---|---|
| `[SUB:gastrings->gallstones]` | 3 — a different diagnosis that reads as true |
| `[SUB:worse->yeah]` | 2 — the course of the symptom is lost, nothing false |

---

## Before you submit

- Did I follow the chart from the top, text first?
- Did I play the audio only for the last four labels (Human transcription error, Audio glitch, Annunciation / Homonym, ASR omission / insertion)?
- Is my severity wrong (3), missing (2), or no clinical content (1)?
