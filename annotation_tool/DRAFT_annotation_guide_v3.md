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
    S([Highlighted error]) --> Q1{Play the audio. Does it match what the ASR wrote,<br/>not what the reference says?<br/>i.e. is the reference wrong and the ASR right?}
    Q1 -- yes --> H[Human transcription error]
    Q1 -- no --> QA{Is there a fault in the recording at this spot?<br/>a dropout, click, cut-off, distortion or noise<br/>Play the audio}
    QA -- yes --> AG[Audio glitch]
    QA -- no --> Q2{Is the damaged word a medical term or a name?<br/>a drug, condition, symptom, body part, test, person or place}
    Q2 -- yes --> D[Dictionary error]
    Q2 -- no --> Q3{Is it the same word with only the ending changed?<br/>plural, tense or -ing}
    Q3 -- yes --> SU[Suffix error]
    Q3 -- no --> Q4{Is it only a short function word?<br/>a, an, the, of, to, is}
    Q4 -- yes --> SW[Stop words]
    Q4 -- no --> Q5{Was an ordinary word swapped for another real word?<br/>usually a sound-alike. Play the audio}
    Q5 -- yes --> A[Annunciation / Homonym]
    Q5 -- no --> Q6{Is the output not a real word at all?}
    Q6 -- yes --> N[Nonsense error]
    Q6 -- no --> O[ASR omission / insertion<br/>ordinary words dropped or invented]
```

Three things to remember:

- **Start from the word, not the sound.**
- **A medical term is always Dictionary**, even if only the ending changed
  (`abdominal→abdomen`).
- **One word, one label.** Two labels only when two words failed for different reasons.

**Audio glitch:** A fault in the recording at this spot. This includes a dropout, distortion, a click or pop, a cut-off, or a burst of noise over the speech. An accent, or fast, slurred or mumbled speech, is not a glitch. If a glitch hides a medical term, it is still Audio glitch. *e.g. a word cut off mid-syllable; a click or dropout where a word should be.*

---

## Step 2 — The severity

**Does the word carry clinical content?** (diagnosis, symptom, medication, procedure,
number, negation)

- **No** → **1 Minor**
- **Yes, and the transcript now says something false** → **3 Severe**
- **Yes, and the fact is just missing or garbled** → **2 Moderate**

**3 = misleading. 2 = missing. 1 = no clinical content.**

| Example | Severity |
|---|---|
| `[SUB:gastrings->gallstones]` | 3 — a different diagnosis that reads as true |
| `[SUB:worse->yeah]` | 2 — the course of the symptom is lost, nothing false |

---

## Before you submit

- Did I follow the chart from the top?
- Did I play the audio for Human transcription error, Audio glitch and Annunciation / Homonym?
- Is my severity wrong (3), missing (2), or no clinical content (1)?
