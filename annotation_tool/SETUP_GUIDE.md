# ASR Error Annotation Tool - Complete Setup Guide

## What You've Got

I've created a complete annotation pipeline for you with three main components:

### 1. **annotation_interface.html** 🎨
A professional web-based interface for human annotation featuring:
- **Side-by-side transcript view** (human vs ASR output)
- **Color-coded error highlighting**:
  - 🔴 **Deletions** (red) - words ASR missed
  - 🟡 **Substitutions** (orange) - words ASR got wrong
  - 🔵 **Insertions** (cyan) - extra words ASR added
- **Error annotation modal** with:
  - Multiple taxonomy selection (Medication, Clinical Concepts, Temporal, Numerics, Identity)
  - Severity slider (0-5 scale with labels)
- **Statistics dashboard** with charts
- **Local browser storage** for annotations
- **Export functionality** to JSON

### 2. **prepare_annotations.py** 📊
Converts your Excel results into JSON format for the web tool:
```bash
# Whisper model (default)
python prepare_annotations.py --input all_result_processed.xlsx --model whisper

# Other models
python prepare_annotations.py --input all_result_processed.xlsx --model phi4
python prepare_annotations.py --input all_result_processed.xlsx --model parakeet
python prepare_annotations.py --input all_result_processed.xlsx --model granite

# Primock data
python prepare_annotations.py --primock primock_result_separate_sheets.xlsx
```

### 3. **process_annotations.py** 📈
Merges your annotations back into pandas DataFrames:
```bash
python process_annotations.py --annotations asr_annotations_TIMESTAMP.json --original all_result_processed.xlsx --report
```

Creates:
- `results_with_annotations.xlsx` - Your data with annotation columns
- `annotation_report.csv` (optional) - Detailed annotation report

## Your Workflow

### Phase 1: Preparation (1 minute)
```bash
python prepare_annotations.py --input all_result_processed.xlsx --model whisper
```
Creates: `whisper_annotation_data.json`

### Phase 2: Annotation (depends on your data)
1. Open `annotation_interface.html` in your browser
2. Load the JSON file
3. Click through utterances and annotate errors
4. Click **💾 Export Annotations** to save: `asr_annotations_TIMESTAMP.json`

### Phase 3: Processing (1 minute)
```bash
python process_annotations.py --annotations asr_annotations_1234567890.json --original all_result_processed.xlsx --report
```
Creates: 
- `results_with_annotations.xlsx` - Ready for analysis!
- `annotation_report.csv` - Summary statistics

## Key Features

### Error Classification
Each error gets TWO labels:
1. **Taxonomy** (select one or more):
   - 💊 Medication (drug names, dosages, interactions)
   - 🏥 Clinical Concepts (medical terms, conditions)
   - ⏱️ Temporal (dates, times, durations)
   - 🔢 Numerics (numbers, measurements)
   - 👤 Identity (names, identifiers)

2. **Severity Score** (0-5):
   - 0: No impact on understanding
   - 1: Minor - easily overlooked
   - 2: Low - some impact but context preserved
   - 3: Medium - notable impact on meaning
   - 4: High - significant impact on clinical info
   - 5: Critical - severe, patient safety concerns

### Smart Interface
- **Visual feedback**: Green dot = annotated, orange dot = needs annotation
- **Progress tracking**: See % completion at a glance
- **Quick navigation**: Dropdown to jump between utterances
- **Statistics**: Charts showing error patterns across your dataset

## File Structure

```
/home/kelechi/bio_ramp_asr/
├── annotation_interface.html      ← Open in browser
├── prepare_annotations.py          ← Step 1: Convert Excel → JSON
├── process_annotations.py          ← Step 3: Convert annotations → Excel
├── quickstart.sh                   ← Automated setup script
├── ANNOTATION_TOOL_README.md       ← Detailed documentation
└── SETUP_GUIDE.md                  ← This file
```

## Quick Commands

### One-liner quick start (Whisper):
```bash
python prepare_annotations.py --input all_result_processed.xlsx --model whisper && \
open annotation_interface.html  # or just open the HTML file manually
```

### Process all 4 models:
```bash
for model in whisper phi4 parakeet granite; do
    python prepare_annotations.py --input all_result_processed.xlsx --model $model
done
```

### Create final results with report:
```bash
python process_annotations.py \
  --annotations asr_annotations_1234567890.json \
  --original all_result_processed.xlsx \
  --report \
  --report-output detailed_error_analysis.csv
```

## Annotation Best Practices

### For Annotators:
1. **Read the human transcript first** - understand the correct information
2. **Examine the error carefully** - what exactly is wrong?
3. **Consider the impact** - would this confuse a doctor? Harm patient safety?
4. **Use all taxonomy tags** - one error might affect multiple categories (e.g., "metformin 500mg" affects both Medication and Numerics)
5. **Be consistent** - try to use similar severity scores for similar errors
6. **Take breaks** - annotation is cognitively demanding

### Example Scenarios:

**"metformin" → "metaform" [SUB]**
- Taxonomy: Medication
- Severity: 4 (High) - wrong drug name is critical

**"three days" → "tree days" [SUB]**
- Taxonomy: Temporal
- Severity: 2 (Low) - clear from context what was meant

**"fever of 38.7°C" → "fever of [DEL: 38.7°C]" [DEL]**
- Taxonomy: Numerics, Clinical Concepts
- Severity: 4 (High) - specific vital sign value is important

**"and the pain is" → "and [INS: the pain is the pain is]"**
- Taxonomy: Clinical Concepts
- Severity: 1 (Minor) - redundant but doesn't change meaning

## Output Data Format

After processing, your Excel file will have new columns:

| Column | Content | Example |
|--------|---------|---------|
| `error_taxonomy_annotations` | Full annotation objects | JSON array |
| `error_annotation_summary` | Total errors, avg severity, tags | `{'total_errors': 3, 'average_severity': 2.67, 'taxonomy_tags': ['Medication', 'Numerics']}` |
| `deletion_annotations` | Del-specific annotations | List of deletion errors with taxonomy/severity |
| `substitution_annotations` | Sub-specific annotations | List of substitution errors |
| `insertion_annotations` | Ins-specific annotations | List of insertion errors |

## Tips & Tricks

### Speed up annotation:
- Use keyboard shortcuts (arrow keys to navigate)
- Click error list items instead of hovering over text
- Batch similar errors (all medication errors together)

### Track your progress:
- The progress bar shows overall completion percentage
- Statistics update in real-time
- Export frequently to ensure no data loss

### Validate annotations:
- Export the JSON and inspect manually for patterns
- Use the Summary tab to review statistics
- Cross-check a sample of your annotations

## Troubleshooting

**Q: Browser says "JSON failed to load"**
- Ensure the JSON file is in the same directory or provide full path
- Check that Python script completed successfully

**Q: Some columns missing from Excel output**
- Ensure original file is `all_result_processed.xlsx`
- Run prepare_annotations.py with correct --model parameter

**Q: Annotations disappeared after closing browser**
- Always use **💾 Export Annotations** button to save!
- The tool stores in browser's local storage, which can be cleared

**Q: Charts not showing in Summary tab**
- Check internet connection (Chart.js is CDN-hosted)
- Try a different browser
- Ensure JavaScript is enabled

## Next Steps

1. ✅ You have the tool - ready to use!
2. 📋 Prepare your data: `python prepare_annotations.py ...`
3. 🎯 Open HTML file and start annotating
4. 📊 Export annotations when done
5. 🔄 Process results: `python process_annotations.py ...`
6. 📈 Analyze results in your notebook!

## Support & Questions

For issues:
1. Check [ANNOTATION_TOOL_README.md](ANNOTATION_TOOL_README.md) for detailed docs
2. Review the file format examples in that README
3. Check your input files have the required columns
4. Ensure all Python dependencies installed: `pip install pandas openpyxl`

---

**Ready to annotate?** 🚀

Just run:
```bash
python prepare_annotations.py --input all_result_processed.xlsx --model whisper
```

Then open `annotation_interface.html` in your browser!
