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
    S([Highlighted error]) --> Q1{Is the reference wrong<br/>and the ASR right?}
    Q1 -- yes --> H[Human transcription error]
    Q1 -- no --> QA{Is there a fault in the audio here?<br/>dropout, click, cut-off. Play the audio}
    QA -- yes --> AG[Audio glitch]
    QA -- no --> Q2{Is the damaged word a<br/>medical term or a name?}
    Q2 -- yes --> D[Dictionary error]
    Q2 -- no --> Q3{Same stem, only the<br/>inflection changed?}
    Q3 -- yes --> SU[Suffix error]
    Q3 -- no --> Q4{Only a short<br/>function word?}
    Q4 -- yes --> SW[Stop word]
    Q4 -- no --> Q5{An ordinary word swapped for<br/>another real word<br/>(usually a sound-alike)? play the audio}
    Q5 -- yes --> A[Annunciation / Homonym]
    Q5 -- no --> Q6{Not a real word?}
    Q6 -- yes --> N[Nonsense error]
    Q6 -- no --> O[ASR omission / insertion]
```

Three things to remember:

- **Start from the word, not the sound.**
- **A medical term is always Dictionary**, even if only the ending changed
  (`abdominal→abdomen`).
- **One word, one label.** Two labels only when two words failed for different reasons.

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
- Did I play the audio for Annunciation / Homonym?
- Is my severity wrong (3), missing (2), or no clinical content (1)?
