# ASR Error Taxonomy Reference Guide

## Overview

This is a **multi-label taxonomy** system. Annotators may assign **multiple categories** to the same error. Use all categories that apply.

---

## Error Categories

### 1. 💊 Medication
**Errors affecting medication-related information:**

- Drug name
- Dose
- Unit
- Route (IV/PO/etc.)
- Frequency
- Duration

**Examples:**
- "amLODIPine" → "amitriptyline"
- "5 mg" → "50 mg"
- "once daily" → "twice daily"

---

### 2. 🏥 Clinical Concepts
**Errors altering clinical information:**

- Diagnosis
- Symptom
- Procedure
- Anatomy
- Laterality
- Laboratory value (including units)

**Examples:**
- "abdominal pain" → "back pain"
- "left knee" → "right knee"
- "potassium 3.5" → "potassium 5.5"

---

### 3. ⏱️ Temporal
**Errors affecting time-related information:**

- Date
- Time
- Duration
- Event sequence (before / after)

**Examples:**
- "two days ago" → "today"
- "follow-up in 2 weeks" → "2 months"

---

### 4. 🚫 Negation / Uncertainty
**Errors involving negation or uncertainty:**

- Loss of negation
- Added negation
- Removal of hedging / uncertainty

**Examples:**
- "no chest pain" → "chest pain"
- "possibly pregnant" → "pregnant"

---

### 5. 🔢 Numerics
**Errors involving numerical values:**

- Vital signs
- Measurements
- Decimals
- Ranges
- Comparators ("greater than", "less than")

**Examples:**
- "BP 120/80" → "200/80"
- "O₂ sat 98%" → "88%"

---

### 6. 💬 Speaker & Attribution
**Errors regarding who said what (patient vs clinician):**

**Examples:**
- Patient fear attributed to clinician
- Clinician instruction labeled as patient dialogue

---

### 7. 📋 Pragmatics (Plan–History–Instruction)
**Errors mixing different clinical contexts:**

- Assessment
- Plan
- Past history
- Instructions

**Examples:**
- "start metformin" → "stop metformin"
- "we will order labs" → "ordered labs previously"

---

### 8. 👤 Identity (Patient / Location)
**Errors affecting identification information:**

- Patient name
- Key personal identifiers
- Important location (clinic, hospital, city)

**Examples:**
- "Johnson" → "Jordan"
- "Los Angeles" → "loss angles"

---

### 9. 🩺 Specialty Category
**Optional secondary tag indicating clinical domain:**

- Cardiology
- Oncology
- Psychiatry
- Neurology
- etc.

**Use when helpful for downstream stratification.**

---

### 10. 📄 Formatting / Structure
**Errors affecting document structure:**

- Section headers
- Bullet points
- Structured lists (AST-specific)

**Examples:**
- "Plan:" header missing
- ROS list collapsed into a paragraph

---

### 11. 🔤 Generic ASR
**Use when the error is primarily:**

- Substitution
- Insertion
- Deletion
- without a clear clinical category

**This functions as a fallback category.**

---

## Multi-Label Guidelines

### When to Use Multiple Categories

An error may belong to **multiple categories simultaneously**. For example:

**Example 1:**
- Error: "metformin 500mg" → "metformin"
- Categories: ✅ **Medication** (drug info) + ✅ **Numerics** (dose value)

**Example 2:**
- Error: "no history of diabetes" → "history of diabetes"
- Categories: ✅ **Negation / Uncertainty** + ✅ **Clinical Concepts** (diagnosis)

**Example 3:**
- Error: "left atrium" → "right atrium"
- Categories: ✅ **Clinical Concepts** (anatomy + laterality)

**Example 4:**
- Error: "potassium 3.5 mmol/L" → "potassium 5.5 mmol/L"
- Categories: ✅ **Clinical Concepts** (lab value) + ✅ **Numerics** (measurement)

### Priority Guidelines

1. **Always tag all applicable categories** - don't limit yourself to one
2. **Use Generic ASR as fallback** - only when no clinical categories apply
3. **Specialty Category is optional** - use for domain-specific analysis
4. **Be specific first** - prefer specific categories (Medication, Temporal) over generic

---

## Decision Tree

```
Start: Is this error clinically significant?
│
├─ YES → Choose all specific categories that apply:
│   ├─ Drug info? → Medication
│   ├─ Clinical term? → Clinical Concepts
│   ├─ Time/date? → Temporal
│   ├─ Negation changed? → Negation / Uncertainty
│   ├─ Number changed? → Numerics
│   ├─ Speaker confused? → Speaker & Attribution
│   ├─ Context mixed? → Pragmatics
│   ├─ Name/location? → Identity
│   ├─ Format issue? → Formatting / Structure
│   └─ Medical domain? → Specialty Category (optional)
│
└─ NO → Generic ASR
```

---

## Common Combinations

### Frequently Co-occurring Categories

| Primary | Often With | Example |
|---------|-----------|---------|
| Medication | Numerics | "aspirin 81mg" → "aspirin 80mg" |
| Clinical Concepts | Negation / Uncertainty | "no fever" → "fever" |
| Clinical Concepts | Numerics | "glucose 120" → "glucose 220" |
| Temporal | Pragmatics | "start tomorrow" → "started yesterday" |
| Identity | Clinical Concepts | "Dr. Smith's patient" → "Dr. Jones's patient" |

---

## Annotation Workflow

1. **Read the error carefully** - understand what changed
2. **Identify primary impact** - what's the main clinical concern?
3. **Check all categories** - does it fit multiple?
4. **Select all that apply** - don't limit to one
5. **Assign severity** - based on combined impact
6. **Add specialty tag** - if relevant for your analysis

---

## Quality Checks

### Before Submitting Each Annotation:

✅ Did I check all 11 categories?
✅ Did I select **all** that apply (not just one)?
✅ Is Generic ASR only used when nothing else fits?
✅ Does the severity reflect the combined impact?
✅ Are medication errors tagged appropriately?
✅ Are negation changes captured?

---

## Examples by Severity

### Severity 5 (Critical) - Multi-Label

**Error:** "no allergy to penicillin" → "allergy to penicillin"
- Categories: 🚫 Negation / Uncertainty + 💊 Medication
- Impact: Could cause withholding necessary antibiotic

**Error:** "metformin 500mg" → "metformin 5000mg"
- Categories: 💊 Medication + 🔢 Numerics
- Impact: 10x overdose

### Severity 3 (Medium) - Multi-Label

**Error:** "follow up in 2 weeks" → "follow up in 2 months"
- Categories: ⏱️ Temporal + 📋 Pragmatics
- Impact: Delayed follow-up could miss condition changes

**Error:** "potassium 3.5" → "potassium 5.5"
- Categories: 🏥 Clinical Concepts + 🔢 Numerics
- Impact: Changes interpretation from normal to high

### Severity 1 (Minor) - Single Label

**Error:** "um" → "and"
- Categories: 🔤 Generic ASR
- Impact: Filler word, no clinical meaning

---

## Tips for Annotators

### Maximize Accuracy
- Take your time with each error
- Consider the full clinical context
- When in doubt, select multiple categories
- Don't overthink - if it fits, tag it

### Speed Tips
- Start with the most obvious category
- Then quickly scan remaining categories
- Use keyboard for navigation
- Batch similar errors together

### Common Mistakes to Avoid
- ❌ Selecting only one category when multiple apply
- ❌ Using Generic ASR for medication/temporal errors
- ❌ Ignoring negation changes
- ❌ Missing numerical changes in clinical values
- ❌ Forgetting speaker attribution errors

---

## Contact & Questions

If you're unsure about a category assignment:
1. Check the examples above
2. Consider the clinical impact
3. When in doubt, tag multiple categories
4. Document unclear cases for team review

Remember: **It's better to over-tag than under-tag!**

---

**Last Updated:** December 22, 2024
**Version:** 2.0 - Full 11-Category Taxonomy
