# Calibration session

**15 minutes, both annotators, before anyone works alone.**

## How the session runs

**Session `RES0051` is the live one.** It sits first in both models on
`/annotate_subset` — 3 errors on Qwen3, 8 on Gemma 3n, 11 in total. Annotate it
**together, out loud**: both commit to an answer, then compare, then discuss.

The ten worked items further down are the reference sheet. Use them when you hit a
disagreement on `RES0051` — each one is a real error the two of you labelled differently
in an earlier round, with the settled answer.

Afterwards each of you finishes the **other two sessions alone**, 75 errors each.

---

## Reference sheet: ten errors you previously disagreed on

---

## What went wrong last time, in one paragraph

You were answering different questions. One of you started from **the sound** ("that's a
mispronunciation") and reached for Annunciation or Spelling. The other started from
**the word** ("that's a drug name") and reached for Dictionary. Nine of our 47
complete disagreements were exactly that. Neither reading was wrong — the guide allowed
both. It no longer does: **always start from the damaged word.**

---

## The ten

| # | Error | Answer | Why |
|---|---|---|---|
| 1 | `[SUB:hypertensive->paternity]` | **Dictionary**, sev 3 | *hypertensive* is a condition. Start from the word, not the sound. |
| 2 | `[SUB:atenolol->low]` | **Dictionary**, sev 3 | A drug name. One word, so one label — not Dictionary + Homonym. |
| 3 | `[INS:alcohol]` — patient said it twice, transcript has it once | **Human transcription error**, sev 1 | The speaker *did* say it. The reference is incomplete, not the model wrong. |
| 4 | `[INS:for you]` — nobody said it | **Words added**, sev 1 | Same shape as #3, opposite answer. The question is always *did the speaker say this?* |
| 5 | `[SUB:lose->loose]` in "loose clothes" | **Human transcription error**, sev 1 | The ASR is right; the human typed the wrong word. |
| 6 | `[SUB:heartbeat shake->beating cheek]` | **Dictionary + Annunciation/Homonym**, sev 3 | Two damaged words, two causes. *heartbeat→beating* is Dictionary, *shake→cheek* is sound. The only case where two labels are allowed. |
| 7 | `[SUB:irregularities->regularities]` | **Annunciation/Homonym**, sev 3 | An ordinary word, so sound-based. Severity 3 because the negation flips. |
| 8 | `[SUB:complaint->complaints]` | **Suffix**, sev 1 | Same stem, wrong ending. |
| 9 | `[SUB:palpitations->palpitation]` | **Suffix**, sev 2 | Also a suffix, even though it sounds like mishearing. Suffix sits above Annunciation in the order, so it wins. |
| 10 | `[DEL:the]` | **Stop words**, sev 1 | No clinical content. |

---

## Three rules these items are testing

**Start from the word.** Items 1, 2, 7. If the damaged word is a drug, condition,
anatomy term, procedure or a name → Dictionary. If it is an ordinary English word →
Annunciation/Homonym. Pronunciation explains nearly every ASR error, so it is a useless
label unless the word was ordinary.

**One word, one label.** Items 2, 9. The form now blocks a second label on a
single-word tag. Item 6 is the exception: two damaged words, two different causes.

**Insertions: did the speaker say it?** Items 3 and 4. Yes → Human transcription error,
the reference is incomplete. No → Words added, the model invented it. Last round one of
you called `[INS:alcohol]` a transcription error and the other called it Words added;
both appear 11 times in the data.

---

## Severity in one line

**3** touches a diagnosis, symptom, medication, procedure, or a negation.
**1** a clinician reading the transcript would not be misled.
**2** genuinely uncertain — not "somewhere in between".

Last round one of you rated 28% of errors severity 3 and the other 18%. Items 1, 2, 6
and 7 are all 3; items 3, 4, 5, 8 and 10 are all 1. Check you both agree before moving on.

---

## Note: some answers changed

Items 2 and 9 were settled differently in the earlier reconciliation, under the old
rules. The taxonomy has changed since — single-word tags now take one label, and Suffix
now sits above Annunciation. Where this document and the old sheet disagree, **this
document is correct.**

---

## After the session

Each of you finishes the other two sessions alone. Do not compare notes once `RES0051`
is done — the whole point is to measure whether the shared understanding holds.

If you hit something the guide does not cover, note the error ID and keep going. Do not
invent a convention mid-session; that is how the last two rounds diverged.
