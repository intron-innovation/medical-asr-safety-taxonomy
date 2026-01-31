# Taxonomy Update - January 30, 2026

## Changes Made

### Modified Taxonomy Categories

**File Modified:** `templates/annotate.html`

#### Removed:
- ❌ `generic_asr` → "Generic ASR"

#### Added/Changed:
1. ✅ `disfluency_hesitation` → "Disfluency/Hesitation"
   - Replaces "Generic ASR"
   - Captures hesitations, filled pauses, speech disfluencies
   - Examples: "um", "uh", "er", stammering

2. ✅ `contraction` → "Contraction"
   - New category for shortened/contracted word forms
   - Examples: "don't" (do not), "can't" (cannot), "I'm" (I am)
   - Captures both correct and incorrect contractions

## Updated Taxonomy List

The complete taxonomy categories are now:

1. Medical Terminology
2. Medication
3. Numerics
4. Temporal
5. Demographics
6. Negation
7. Meaning
8. Fluency
9. Proper Names
10. Redundancy
11. **Disfluency/Hesitation** (NEW - replaced Generic ASR)
12. **Contraction** (NEW)

## Implementation Details

### Value Mapping

```python
"disfluency_hesitation"  # Internal value (database)
"Disfluency/Hesitation"  # Display label (UI)

"contraction"            # Internal value (database)
"Contraction"            # Display label (UI)
```

### HTML Changes
```html
<!-- Before -->
<input type="checkbox" name="taxonomy" value="generic_asr" id="tax-generic">
<label for="tax-generic">Generic ASR</label>

<!-- After -->
<input type="checkbox" name="taxonomy" value="disfluency_hesitation" id="tax-disfluency">
<label for="tax-disfluency">Disfluency/Hesitation</label>

<input type="checkbox" name="taxonomy" value="contraction" id="tax-contraction">
<label for="tax-contraction">Contraction</label>
```

## Impact

- ✅ Existing annotations with `generic_asr` will continue to work
- ✅ New annotations will use updated taxonomy
- ✅ Frontend automatically displays new categories on next page load
- ✅ No database migration needed (taxonomy is stored as JSON)

## Notes

- The internal value uses underscores (`disfluency_hesitation`)
- The display label uses hyphens and spaces (`Disfluency/Hesitation`)
- All taxonomy values are case-sensitive in the backend
- Export/analytics queries should use the internal value format

## Testing

To verify changes:
1. Load the annotation interface
2. Click on any error to open the annotation modal
3. Confirm that "Generic ASR" is gone
4. Confirm that "Disfluency/Hesitation" and "Contraction" appear in the category list
